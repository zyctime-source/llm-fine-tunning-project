#!/usr/bin/env python3
"""
Build Layer 2 regression manifest (v0) from local JSONL snapshots.

No Hugging Face `datasets` dependency — uses stdlib only so broken NumPy/pandas
stacks do not block manifest generation.

Outputs:
  data/eval/layer2/manifest_v0.jsonl
  data/eval/layer2/manifest_meta.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT_DIR = REPO_ROOT / "data" / "eval" / "layer2"
BRAINSTORM_PATH = REPO_ROOT / "data" / "processed" / "brainstorm_vicuna_10k_zh.jsonl"
GENERAL_MIXED_TRAIN_PATH = (
    REPO_ROOT / "data" / "raw" / "general_mixed" / "general_mixed_train.jsonl"
)
GENERAL_MIXED_LEGACY_PATH = (
    REPO_ROOT / "data" / "raw" / "general_mixed" / "general_mixed.jsonl"
)


def _resolve_general_mixed_path() -> Path:
    if GENERAL_MIXED_TRAIN_PATH.exists():
        return GENERAL_MIXED_TRAIN_PATH
    if GENERAL_MIXED_LEGACY_PATH.exists():
        return GENERAL_MIXED_LEGACY_PATH
    raise SystemExit(
        "Missing general mix JSONL: expected "
        f"{GENERAL_MIXED_TRAIN_PATH} (preferred) or legacy {GENERAL_MIXED_LEGACY_PATH}. "
        "Run: python -m data_pipeline download"
    )

CORE_N = 200
GENERAL_N = 200
ZH_N = 100


def _sharegpt_zh_to_messages(conversations_zh: list) -> list[dict]:
    out: list[dict] = []
    for turn in conversations_zh:
        role = "user" if turn.get("from") == "human" else "assistant"
        out.append({"role": role, "content": turn.get("value", "")})
    return out


def _read_jsonl(path: Path) -> list[tuple[int, dict]]:
    rows: list[tuple[int, dict]] = []
    with path.open(encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            rows.append((i, json.loads(line)))
    return rows


def _sha256_messages(messages: list) -> str:
    blob = json.dumps(messages, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def build_manifest(
    out_dir: Path,
    seed_core: int,
    seed_general: int,
    seed_zh: int,
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_jsonl = out_dir / "manifest_v0.jsonl"

    brainstorm = _read_jsonl(BRAINSTORM_PATH)
    if len(brainstorm) < CORE_N:
        raise SystemExit(f"Need at least {CORE_N} brainstorm rows, got {len(brainstorm)}")

    rng_c = random.Random(seed_core)
    core_line_nums = sorted(rng_c.sample([ln for ln, _ in brainstorm], CORE_N))

    general_path = _resolve_general_mixed_path()
    general_rows = _read_jsonl(general_path)
    en_indices = [ln for ln, r in general_rows if r.get("lang") == "en"]
    zh_indices = [ln for ln, r in general_rows if r.get("lang") == "zh"]
    if len(en_indices) < GENERAL_N:
        raise SystemExit(f"Need at least {GENERAL_N} en rows in {general_path}, got {len(en_indices)}")
    if len(zh_indices) < ZH_N:
        raise SystemExit(f"Need at least {ZH_N} zh rows in {general_path}, got {len(zh_indices)}")

    rng_g = random.Random(seed_general)
    general_line_nums = sorted(rng_g.sample(en_indices, GENERAL_N))

    rng_z = random.Random(seed_zh)
    zh_line_nums = sorted(rng_z.sample(zh_indices, ZH_N))

    line_to_row_b = {ln: r for ln, r in brainstorm}
    line_to_row_g = {ln: r for ln, r in general_rows}

    records: list[dict] = []
    counters = {"core": 0, "general": 0, "zh_guard": 0}

    for ln in core_line_nums:
        counters["core"] += 1
        r = line_to_row_b[ln]
        mid = f"L2-core-{counters['core']:05d}"
        msgs = _sharegpt_zh_to_messages(r["conversations_zh"])
        records.append(
            {
                "layer2_id": mid,
                "stratum": "core",
                "source_hub_repo": "DevQuasar/brainstorm_vicuna_10k",
                "source_local_path": str(BRAINSTORM_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
                "source_line_1based": ln,
                "source_sample_id": r.get("id") or r.get("source_id"),
                "messages": msgs,
                "content_sha256": _sha256_messages(msgs),
            }
        )

    for ln in general_line_nums:
        counters["general"] += 1
        r = line_to_row_g[ln]
        mid = f"L2-general-{counters['general']:05d}"
        msgs = r["messages"]
        records.append(
            {
                "layer2_id": mid,
                "stratum": "general",
                "source_hub_repo": r.get("source_repo", "tatsu-lab/alpaca"),
                "source_local_path": str(general_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "source_line_1based": ln,
                "source_sample_id": r.get("id"),
                "messages": msgs,
                "content_sha256": _sha256_messages(msgs),
            }
        )

    for ln in zh_line_nums:
        counters["zh_guard"] += 1
        r = line_to_row_g[ln]
        mid = f"L2-zh_guard-{counters['zh_guard']:05d}"
        msgs = r["messages"]
        records.append(
            {
                "layer2_id": mid,
                "stratum": "zh_guard",
                "source_hub_repo": r.get("source_repo", "FreedomIntelligence/evol-instruct-chinese"),
                "source_local_path": str(general_path.relative_to(REPO_ROOT)).replace("\\", "/"),
                "source_line_1based": ln,
                "source_sample_id": r.get("id"),
                "messages": msgs,
                "content_sha256": _sha256_messages(msgs),
            }
        )

    with out_jsonl.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    meta = {
        "manifest_version": "layer2-v0",
        "total_items": len(records),
        "strata": {"core": CORE_N, "general": GENERAL_N, "zh_guard": ZH_N},
        "seeds": {"core": seed_core, "general": seed_general, "zh_guard": seed_zh},
        "paths": {
            "manifest_jsonl": str(out_jsonl.relative_to(REPO_ROOT)).replace("\\", "/"),
            "brainstorm_source": str(BRAINSTORM_PATH.relative_to(REPO_ROOT)).replace("\\", "/"),
            "general_mixed_source": str(general_path.relative_to(REPO_ROOT)).replace("\\", "/"),
        },
        "shaping_ref": "_docs/shaping/9_eval_qa_CN.md §9.1.3",
        "proxy_notes": {
            "general": "Shaping Layer1 cites X-AlpacaEval for general instruction-following; v0 uses tatsu-lab/alpaca-style en rows from general_mixed until HF datasets load is stable.",
            "zh_guard": "Shaping cites CMT-Eval for Chinese scenes; v0 uses FreedomIntelligence/evol-instruct-chinese rows from general_mixed until CMT-Eval is wired.",
        },
    }
    (out_dir / "manifest_meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(records)} records -> {out_jsonl}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    p.add_argument("--seed-core", type=int, default=42)
    p.add_argument("--seed-general", type=int, default=43)
    p.add_argument("--seed-zh", type=int, default=44)
    args = p.parse_args()
    build_manifest(args.out_dir, args.seed_core, args.seed_general, args.seed_zh)


if __name__ == "__main__":
    main()
