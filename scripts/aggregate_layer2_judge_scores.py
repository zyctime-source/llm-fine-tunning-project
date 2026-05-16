#!/usr/bin/env python3
"""
Aggregate layer2_judge_scores.jsonl into a small JSON summary (means/medians by stratum).

Use this to fill experiment META.json → result_scores (summary only; keep the JSONL as
the audit trail). Numeric keys must stay aligned with scripts/layer2_judge_scores.py.

Usage (from repo root):
  python scripts/aggregate_layer2_judge_scores.py \\
    --judge-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl \\
    --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json

  python scripts/aggregate_layer2_judge_scores.py --judge-jsonl path/to/layer2_judge_scores.jsonl
  # prints JSON to stdout if --out omitted
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from collections.abc import Iterable
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

# Keep in sync with layer2_judge_scores.py: SCORE_DIMENSION_KEYS + overall
AGG_NUMERIC_KEYS: tuple[str, ...] = (
    "relevance",
    "coherence",
    "helpfulness",
    "creativity",
    "clarity",
    "task_alignment",
    "depth",
    "chinese_quality",
    "overall",
)


def _resolve_existing_file(path: Path) -> Path | None:
    path = path.expanduser()
    if path.is_file():
        return path.resolve()
    alt = (REPO_ROOT / path).resolve()
    if alt.is_file():
        return alt
    return None


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError as e:
                print(f"WARN skip line {line_no}: JSON decode: {e}", file=sys.stderr)
    return rows


def _dedupe_last_per_id(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int, int]:
    """Same layer2_id: keep last row. Rows without layer2_id are appended unchanged."""
    with_id = [r for r in rows if str(r.get("layer2_id", "")).strip()]
    without_id = [r for r in rows if not str(r.get("layer2_id", "")).strip()]
    by_id: dict[str, dict[str, Any]] = {}
    for row in with_id:
        lid = str(row.get("layer2_id", "")).strip()
        by_id[lid] = row
    dup_collapsed = max(0, len(with_id) - len(by_id))
    merged = list(by_id.values()) + without_id
    return merged, dup_collapsed, len(without_id)


def _mean_median(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"mean": None, "median": None}
    return {
        "mean": round(statistics.mean(values), 3),
        "median": round(statistics.median(values), 3),
    }


def _aggregate_rows(rows: Iterable[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Group by stratum; only rows with judge_parse_ok and scores dict."""
    by_stratum: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not row.get("judge_parse_ok"):
            continue
        scores = row.get("scores")
        if not isinstance(scores, dict):
            continue
        st = str(row.get("stratum", "") or "unknown").strip() or "unknown"
        by_stratum.setdefault(st, []).append(scores)

    final: dict[str, dict[str, Any]] = {}
    for st, score_rows in sorted(by_stratum.items()):
        per: dict[str, Any] = {"n": len(score_rows)}
        for key in AGG_NUMERIC_KEYS:
            vals: list[float] = []
            for s in score_rows:
                v = s.get(key)
                if isinstance(v, bool):
                    continue
                if isinstance(v, int):
                    vals.append(float(v))
                elif isinstance(v, float) and v == int(v):
                    vals.append(float(int(v)))
            if vals:
                per[key] = _mean_median(vals)
        final[st] = per
    return final


def _aggregate_all_ok(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    ok_scores: list[dict[str, Any]] = []
    for row in rows:
        if not row.get("judge_parse_ok"):
            continue
        s = row.get("scores")
        if isinstance(s, dict):
            ok_scores.append(s)
    out: dict[str, Any] = {"n": len(ok_scores)}
    for key in AGG_NUMERIC_KEYS:
        vals: list[float] = []
        for s in ok_scores:
            v = s.get(key)
            if isinstance(v, bool):
                continue
            if isinstance(v, int):
                vals.append(float(v))
            elif isinstance(v, float) and v == int(v):
                vals.append(float(int(v)))
        if vals:
            out[key] = _mean_median(vals)
    return out


def _rel_to_repo(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def main() -> None:
    p = argparse.ArgumentParser(description="Summarize layer2_judge_scores.jsonl for META.result_scores.")
    p.add_argument(
        "--judge-jsonl",
        type=Path,
        default=REPO_ROOT
        / "experiment"
        / "baseline-gemma4e2b-it-layer2-v0"
        / "results"
        / "layer2_judge_scores.jsonl",
        help="Input JSONL from layer2_judge_scores.py",
    )
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Write summary JSON (default: print to stdout only)",
    )
    p.add_argument(
        "--no-dedupe",
        action="store_true",
        help="Do not collapse duplicate layer2_id (default: keep last row per id)",
    )
    args = p.parse_args()

    resolved = _resolve_existing_file(args.judge_jsonl)
    if resolved is None:
        sys.exit(
            f"Judge JSONL not found: {args.judge_jsonl}\n"
            f"Tried cwd-relative and under repo root: {REPO_ROOT}"
        )

    rows = _read_jsonl(resolved)
    rows_total = len(rows)
    if not args.no_dedupe:
        rows, duplicate_layer2_ids, rows_missing_layer2_id = _dedupe_last_per_id(rows)
    else:
        duplicate_layer2_ids = 0
        rows_missing_layer2_id = sum(1 for r in rows if not str(r.get("layer2_id", "")).strip())

    parse_ok = sum(1 for r in rows if r.get("judge_parse_ok") is True)
    parse_fail = sum(1 for r in rows if r.get("judge_parse_ok") is not True)

    judge_models = [str(r.get("judge_model", "")).strip() for r in rows if r.get("judge_model")]
    judge_model = Counter(judge_models).most_common(1)[0][0] if judge_models else None

    summary: dict[str, Any] = {
        "schema": "layer2-judge-summary-v0",
        "source_judge_jsonl": _rel_to_repo(resolved),
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "judge_model": judge_model,
        "counts": {
            "rows_after_dedupe": len(rows),
            "rows_total_before_dedupe": rows_total,
            "duplicate_layer2_ids_collapsed": duplicate_layer2_ids,
            "rows_missing_layer2_id": rows_missing_layer2_id,
            "judge_parse_ok": parse_ok,
            "judge_parse_fail": parse_fail,
        },
        "by_stratum": _aggregate_rows(rows),
        "all_parse_ok": _aggregate_all_ok(rows),
    }

    text = json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        out_path = args.out
        if not out_path.is_absolute():
            out_path = (REPO_ROOT / out_path).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text, encoding="utf-8")
        print(f"Wrote {out_path}", file=sys.stderr)
        print(f"Suggested META.result_scores (merge or nest as you prefer):", file=sys.stderr)
        snippet = {
            "judge_summary_schema": summary["schema"],
            "judge_summary_file": _rel_to_repo(out_path),
            "judge_model": judge_model,
            "counts": summary["counts"],
            "by_stratum_overall_mean": {
                st: (summary["by_stratum"].get(st) or {}).get("overall", {}).get("mean")
                for st in sorted(summary["by_stratum"].keys())
            },
            "all_parse_ok_overall_mean": (summary["all_parse_ok"].get("overall") or {}).get("mean"),
        }
        print(json.dumps({"result_scores": snippet}, ensure_ascii=False, indent=2), file=sys.stderr)
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
