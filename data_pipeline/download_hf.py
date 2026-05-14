"""
Download Hugging Face datasets and write general-mix JSONL.

Functions:

- ``download_brainstorm_vicuna``: load ``brainstorm_vicuna_10k`` (all splits), one ``.jsonl`` per split, plus ``download_meta.json``.
- ``download_general_mixed``: sample from two HF datasets (EN + ZH), normalize via ``general_normalize``, merge to
  ``general_mixed_train.jsonl`` + ``general_mixed_validation.jsonl`` when ``general_val_n > 0``, else legacy single
  ``general_mixed.jsonl``.

Requires ``datasets`` / ``huggingface_hub``. Run from repo root in a venv; set ``HF_TOKEN`` when needed.
"""

from __future__ import annotations

import json
import os
import random
from pathlib import Path
from typing import Any, Iterable

from datasets import Dataset, load_dataset

from data_pipeline.general_normalize import dumps_jsonl_line, normalize_general_row
from data_pipeline.settings import DataPipelineSettings


def _ensure_hf_env(settings: DataPipelineSettings) -> None:
    """
    Copy HF-related fields from settings into ``os.environ`` for ``datasets`` / Hub.

    Args:
        settings: Pipeline settings; only non-empty ``hf_token`` / ``hf_home`` are applied.

    Returns:
        None
    """
    if settings.hf_token:
        os.environ.setdefault("HF_TOKEN", settings.hf_token)
        os.environ.setdefault("HUGGING_FACE_HUB_TOKEN", settings.hf_token)
    if settings.hf_home:
        os.environ.setdefault("HF_HOME", settings.hf_home)


def _write_jsonl_file(output_path: Path, records: Iterable[dict[str, Any]]) -> int:
    """
    Write records to a JSONL file (overwrite if the file exists).

    Args:
        output_path: Destination path; parent directories are created as needed.
        records: Iterable of dict rows.

    Returns:
        Number of lines written.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines_written = 0
    with output_path.open("w", encoding="utf-8") as output_fp:
        for record in records:
            output_fp.write(dumps_jsonl_line(record))
            lines_written += 1
    return lines_written


def download_brainstorm_vicuna(settings: DataPipelineSettings) -> dict[str, int]:
    """
    Download all splits of ``brainstorm_vicuna_10k`` to JSONL and write download metadata.

    Args:
        settings: Must include ``brainstorm_repo``, ``brainstorm_revision``, ``brainstorm_raw_dir``.

    Returns:
        Map split name to row count, e.g. ``{"train": 10000, "test": 1000}``.

    Raises:
        OSError: On disk write failure.
        Any exception raised by ``datasets.load_dataset`` (network, parsing, etc.).
    """
    _ensure_hf_env(settings)
    output_dir = Path(settings.brainstorm_raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    dataset_dict = load_dataset(
        settings.brainstorm_repo,
        revision=settings.brainstorm_revision,
        trust_remote_code=True,
    )
    split_name_to_row_count: dict[str, int] = {}
    for split_name in dataset_dict.keys():
        split_file_path = output_dir / f"{split_name}.jsonl"
        row_count = 0
        with split_file_path.open("w", encoding="utf-8") as split_fp:
            for row in dataset_dict[split_name]:
                split_fp.write(json.dumps(row, ensure_ascii=False) + "\n")
                row_count += 1
        split_name_to_row_count[split_name] = row_count

    download_meta = {
        "repo": settings.brainstorm_repo,
        "revision": settings.brainstorm_revision,
        "splits": split_name_to_row_count,
    }
    meta_path = output_dir / "download_meta.json"
    meta_path.write_text(
        json.dumps(download_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return split_name_to_row_count


def _load_split_as_dataset(
    repo_id: str,
    split_name: str,
    revision: str | None,
    config_name: str | None,
) -> Dataset:
    """
    Load one split of a Hub dataset, optionally pinned to a revision or builder config.

    Args:
        repo_id: Hugging Face dataset id, e.g. ``"tatsu-lab/alpaca"``.
        split_name: Split name, usually ``"train"``.
        revision: Git revision; ``None`` uses the default branch.
        config_name: Builder config for multi-config datasets; ``None`` for single-config datasets.

    Returns:
        A ``datasets.Dataset`` instance.

    Raises:
        Exceptions from ``load_dataset`` on load failures.
    """
    load_kwargs: dict[str, Any] = {"trust_remote_code": True}
    if revision:
        load_kwargs["revision"] = revision
    if config_name:
        return load_dataset(repo_id, config_name, split=split_name, **load_kwargs)
    return load_dataset(repo_id, split=split_name, **load_kwargs)


def _collect_normalized_samples(
    *,
    dataset: Dataset,
    repo_id: str,
    language_code: str,
    target_count: int,
    rng: random.Random,
) -> list[dict[str, Any]]:
    """
    Shuffle row indices and collect up to ``target_count`` rows that normalize successfully.

    Args:
        dataset: Loaded HF ``Dataset``.
        repo_id: Dataset id (used in stable ``id`` / ``source_repo``).
        language_code: ``"en"``, ``"zh"``, etc.
        target_count: Maximum desired rows; fewer if too many rows fail normalization.
        rng: Random generator (seeded via ``general_seed`` for reproducibility).

    Returns:
        List of normalized dict records.
    """
    row_indices = list(range(len(dataset)))
    rng.shuffle(row_indices)
    collected: list[dict[str, Any]] = []
    for row_index in row_indices:
        if len(collected) >= target_count:
            break
        hf_row = dataset[row_index]
        stable_row_id = f"{language_code}-{repo_id.replace('/', '__')}-{row_index}"
        normalized = normalize_general_row(
            source_repo=repo_id,
            language_code=language_code,
            stable_row_id=stable_row_id,
            hf_row=hf_row,
        )
        if normalized is not None:
            collected.append(normalized)
    return collected


def download_general_mixed(settings: DataPipelineSettings) -> dict[str, Any]:
    """
    Sample EN and ZH HF datasets separately, normalize, merge, and write JSONL.

    When ``general_val_n > 0``:

    - Split each language list: last ``general_val_n // 2`` English and remaining count on ZH side go to validation;
      earlier rows form the training pool (deterministic given sampled order).
    - Write ``general_mixed_train.jsonl`` then ``general_mixed_validation.jsonl``.

    When ``general_val_n == 0`` (legacy): write all rows to ``general_mixed.jsonl``.

    Args:
        settings: Includes ``general_en_*``, ``general_zh_*``, ``general_seed``, ``general_raw_dir``,
            ``general_val_n``.

    Returns:
        Metadata dict with paths, written row counts, ``seed``, etc.

    Raises:
        ValueError: If validation hold-out size exceeds available rows per language.
        OSError: On disk write failure.
        Exceptions from ``load_dataset`` or I/O.
    """
    _ensure_hf_env(settings)
    output_dir = Path(settings.general_raw_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    rng = random.Random(settings.general_seed)

    english_dataset = _load_split_as_dataset(
        settings.general_en_repo,
        settings.general_en_split,
        settings.general_en_revision,
        settings.general_en_config_name,
    )
    chinese_dataset = _load_split_as_dataset(
        settings.general_zh_repo,
        settings.general_zh_split,
        settings.general_zh_revision,
        settings.general_zh_config_name,
    )

    english_rows = _collect_normalized_samples(
        dataset=english_dataset,
        repo_id=settings.general_en_repo,
        language_code="en",
        target_count=settings.general_en_n,
        rng=rng,
    )
    chinese_rows = _collect_normalized_samples(
        dataset=chinese_dataset,
        repo_id=settings.general_zh_repo,
        language_code="zh",
        target_count=settings.general_zh_n,
        rng=rng,
    )

    val_n = settings.general_val_n
    download_meta: dict[str, Any] = {
        "general_total_n_config": settings.general_total_n,
        "general_en_repo": settings.general_en_repo,
        "general_en_n_requested": settings.general_en_n,
        "general_en_n_obtained": len(english_rows),
        "general_zh_repo": settings.general_zh_repo,
        "general_zh_n_requested": settings.general_zh_n,
        "general_zh_n_obtained": len(chinese_rows),
        "seed": settings.general_seed,
        "general_val_n": val_n,
    }

    if val_n <= 0:
        merged_rows = english_rows + chinese_rows
        mixed_output_path = output_dir / "general_mixed.jsonl"
        written_rows = _write_jsonl_file(mixed_output_path, merged_rows)
        download_meta.update(
            {
                "written_rows": written_rows,
                "output": str(mixed_output_path),
                "split_mode": "single_file",
            }
        )
    else:
        val_en = val_n // 2
        val_zh = val_n - val_en
        if len(english_rows) < val_en or len(chinese_rows) < val_zh:
            raise ValueError(
                f"general_val_n={val_n} requires at least en tail={val_en}, zh tail={val_zh} "
                f"but obtained en={len(english_rows)}, zh={len(chinese_rows)}"
            )
        en_split = len(english_rows) - val_en
        zh_split = len(chinese_rows) - val_zh
        train_rows = english_rows[:en_split] + chinese_rows[:zh_split]
        val_rows = english_rows[en_split:] + chinese_rows[zh_split:]

        train_path = output_dir / "general_mixed_train.jsonl"
        val_path = output_dir / "general_mixed_validation.jsonl"
        written_train = _write_jsonl_file(train_path, train_rows)
        written_val = _write_jsonl_file(val_path, val_rows)
        download_meta.update(
            {
                "written_train_rows": written_train,
                "written_val_rows": written_val,
                "train_output": str(train_path),
                "validation_output": str(val_path),
                "val_en_tail": val_en,
                "val_zh_tail": val_zh,
                "split_mode": "train_val_by_language_tail",
            }
        )

    meta_path = output_dir / "download_meta.json"
    meta_path.write_text(
        json.dumps(download_meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return download_meta
