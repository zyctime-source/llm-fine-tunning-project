"""
Export brainstorm validation JSONL aligned with v1.0 training head.

English: first ``brainstorm_val_export_n`` valid JSON lines **after** skipping
``brainstorm_train_head_n`` lines from ``train.jsonl`` (same counting rule as spec §4.1).

Chinese: lines from the translated JSONL whose ``id`` appears in that English window,
**in the same id order** as English. Missing translations are reported in metadata;
optional strict mode fails if any id is missing.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from data_pipeline.settings import DataPipelineSettings


def _iter_valid_train_records(train_path: Path) -> Any:
    with train_path.open("r", encoding="utf-8") as fp:
        for raw_line in fp:
            stripped = raw_line.strip()
            if not stripped:
                continue
            yield json.loads(stripped)


def _load_translated_by_id(translated_path: Path) -> dict[str, dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    with translated_path.open("r", encoding="utf-8") as fp:
        for raw_line in fp:
            stripped = raw_line.strip()
            if not stripped:
                continue
            record = json.loads(stripped)
            sid = str(record.get("id", "")).strip()
            if sid:
                by_id[sid] = record
    return by_id


def export_brainstorm_validation(settings: DataPipelineSettings) -> dict[str, Any]:
    """
    Write English validation slice and aligned Chinese rows from the translation file.

    Args:
        settings: Paths and ``brainstorm_train_head_n``, ``brainstorm_val_export_n``, etc.

    Returns:
        Summary dict written to ``brainstorm_validation_meta.json`` (also printed by CLI).

    Raises:
        FileNotFoundError: If ``train.jsonl`` or translated JSONL is missing.
        ValueError: If ``brainstorm_val_export_n`` <= 0 while export is requested.
        RuntimeError: If strict full-ZH is enabled and any validation id lacks a translation.
    """
    if settings.brainstorm_val_export_n <= 0:
        raise ValueError(
            "brainstorm_val_export_n must be > 0; set BRAINSTORM_VAL_EXPORT_N or skip this command"
        )

    train_path = Path(settings.brainstorm_raw_dir) / "train.jsonl"
    if not train_path.exists():
        raise FileNotFoundError(
            f"Missing {train_path}. Run: python -m data_pipeline download"
        )

    translated_path = Path(settings.translated_jsonl_path)
    if not translated_path.exists():
        raise FileNotFoundError(
            f"Missing {translated_path}. Run: python -m data_pipeline translate"
        )

    head_n = settings.brainstorm_train_head_n
    val_n = settings.brainstorm_val_export_n

    valid_index = 0
    val_en_rows: list[dict[str, Any]] = []
    for record in _iter_valid_train_records(train_path):
        valid_index += 1
        if valid_index <= head_n:
            continue
        val_en_rows.append(record)
        if len(val_en_rows) >= val_n:
            break

    val_ids = [str(r.get("id", "")).strip() for r in val_en_rows]
    val_ids = [i for i in val_ids if i]

    zh_by_id = _load_translated_by_id(translated_path)
    zh_rows_ordered: list[dict[str, Any]] = []
    missing_ids: list[str] = []
    for sid in val_ids:
        row = zh_by_id.get(sid)
        if row is None:
            missing_ids.append(sid)
        else:
            zh_rows_ordered.append(row)

    if settings.brainstorm_val_require_full_zh and missing_ids:
        raise RuntimeError(
            f"BRAINSTORM_VAL_REQUIRE_FULL_ZH=1 but {len(missing_ids)} ids lack translation, "
            f"e.g. {missing_ids[:5]!r}"
        )

    out_en = Path(settings.brainstorm_val_en_jsonl)
    out_zh = Path(settings.brainstorm_val_zh_jsonl)
    out_en.parent.mkdir(parents=True, exist_ok=True)
    out_zh.parent.mkdir(parents=True, exist_ok=True)

    with out_en.open("w", encoding="utf-8") as fp:
        for row in val_en_rows:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    with out_zh.open("w", encoding="utf-8") as fp:
        for row in zh_rows_ordered:
            fp.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta_path = Path(settings.brainstorm_validation_meta_json)
    summary: dict[str, Any] = {
        "train_source": str(train_path.resolve()),
        "translated_source": str(translated_path.resolve()),
        "train_head_valid_lines": head_n,
        "val_requested": val_n,
        "written_en": len(val_en_rows),
        "written_zh": len(zh_rows_ordered),
        "missing_zh_count": len(missing_ids),
        "missing_zh_ids_sample": missing_ids[:50],
        "output_en": str(out_en.resolve()),
        "output_zh": str(out_zh.resolve()),
        "strict_zh": settings.brainstorm_val_require_full_zh,
        "rule": "valid_lines_after_head_then_align_zh_by_id_order",
    }
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    meta_path.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summary["meta_written"] = str(meta_path.resolve())
    return summary
