"""
CLI entry: ``python -m data_pipeline <subcommand>``.

Subcommands:

- ``download``: run ``download_hf`` for brainstorm + general mix.
- ``translate``: run ``translate_qwen`` to append translated JSONL.
- ``export-brainstorm-val``: slice ``train.jsonl`` after the training head and align zh rows for validation.

Path handling:

- Inserts the repository root on ``sys.path`` so ``python -m data_pipeline`` from the repo root resolves the package.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
if str(_REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPOSITORY_ROOT))

from data_pipeline.brainstorm_validation import export_brainstorm_validation
from data_pipeline.download_hf import download_brainstorm_vicuna, download_general_mixed
from data_pipeline.settings import DataPipelineSettings
from data_pipeline.translate_qwen import translate_brainstorm_file


def run_download_command(_: argparse.Namespace) -> int:
    """
    Run ``download``: fetch brainstorm dataset then general mix; print JSON summaries to stdout.

    Args:
        _: Parsed ``argparse.Namespace`` (unused; reserved for future flags).

    Returns:
        Process exit code ``0`` on success.
    """
    settings = DataPipelineSettings.from_env()
    print("Downloading brainstorm_vicuna_10k ...")
    split_counts = download_brainstorm_vicuna(settings)
    print(json.dumps({"brainstorm_splits": split_counts}, ensure_ascii=False, indent=2))

    print("Downloading and mixing general data (GENERAL_* env) ...")
    general_meta = download_general_mixed(settings)
    print(json.dumps(general_meta, ensure_ascii=False, indent=2))
    return 0


def run_translate_command(_: argparse.Namespace) -> int:
    """
    Run ``translate``: append translations; print JSON summary to stdout.

    Args:
        _: Parsed namespace placeholder.

    Returns:
        Exit code ``0`` on success (exceptions propagate on per-sample failures).
    """
    settings = DataPipelineSettings.from_env()
    summary = translate_brainstorm_file(settings)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def run_export_brainstorm_val_command(_: argparse.Namespace) -> int:
    """
    Export English + aligned Chinese brainstorm validation JSONL; print JSON summary.

    Args:
        _: Parsed namespace placeholder.

    Returns:
        Exit code ``0`` on success.
    """
    settings = DataPipelineSettings.from_env()
    if settings.brainstorm_val_export_n <= 0:
        print(
            json.dumps(
                {
                    "skipped": True,
                    "reason": "BRAINSTORM_VAL_EXPORT_N <= 0",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    summary = export_brainstorm_validation(settings)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    """
    Parse CLI arguments and dispatch download / translate / export-brainstorm-val.

    Returns:
        Subcommand exit code as int.
    """
    parser = argparse.ArgumentParser(
        description="Sprint 1 data: Hugging Face download, Qwen translation, brainstorm val export"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    download_parser = subparsers.add_parser(
        "download",
        help="Download brainstorm + general mix to local JSONL",
    )
    download_parser.set_defaults(func=run_download_command)

    translate_parser = subparsers.add_parser(
        "translate",
        help="Translate brainstorm train.jsonl to Chinese (resumable)",
    )
    translate_parser.set_defaults(func=run_translate_command)

    export_val_parser = subparsers.add_parser(
        "export-brainstorm-val",
        help="Write validation_en.jsonl + zh_validation after train head (see .env)",
    )
    export_val_parser.set_defaults(func=run_export_brainstorm_val_command)

    parsed_args = parser.parse_args()
    command_handler = parsed_args.func
    return int(command_handler(parsed_args))


if __name__ == "__main__":
    raise SystemExit(main())
