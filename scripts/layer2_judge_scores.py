#!/usr/bin/env python3
"""
Layer 2 LLM-as-a-Judge: score Gemma completions with DashScope OpenAI-compatible API.

Aligned with _docs/execution/s1-baseline-report_CN.md §4.1 (judge qwen3.6-plus, temperature 0.2,
JSON output). Reads:
  - manifest JSONL (full messages + stratum)
  - infer JSONL from scripts/layer2_smoke_infer.py (layer2_id, completion_text or completion_preview)

Scores (1–100 integers): relevance, coherence, helpfulness, creativity, clarity, task_alignment, depth,
chinese_quality (always; use **100** if reply is almost all English = N/A). **overall** also 1–100.
Plus rationale_zh (Chinese).

Outputs one JSON object per line (append + flush for resume safety).

Usage:
  pip install -r requirements-eval.txt
  # DASHSCOPE_API_KEY and DASHSCOPE_OPENAI_BASE_URL in repo-root .env
  python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl
  python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl --resume
  python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl --limit 10
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_JUDGE_MODEL = "qwen3.6-plus"


def _resolve_existing_file(path: Path) -> Path | None:
    """Resolve path: cwd-relative first, then repo-root-relative (for running from any cwd)."""
    path = path.expanduser()
    if path.is_file():
        return path.resolve()
    alt = (REPO_ROOT / path).resolve()
    if alt.is_file():
        return alt
    return None


def _infer_missing_help(requested: Path) -> str:
    lines = [
        f"Infer JSONL not found: {requested}",
        f"Tried: {requested.resolve() if requested.exists() else requested} and {REPO_ROOT / requested}",
    ]
    results_dir = REPO_ROOT / "experiment" / "baseline-gemma4e2b-it-layer2-v0" / "results"
    if results_dir.is_dir():
        jsonls = sorted(results_dir.glob("*.jsonl"))
        if jsonls:
            lines.append("Existing JSONL under experiment/baseline-gemma4e2b-it-layer2-v0/results/:")
            for f in jsonls:
                rel = f.relative_to(REPO_ROOT)
                lines.append(f"  --infer-jsonl {rel.as_posix()}")
    lines.append(
        "If you did not pass --out to layer2_smoke_infer.py, the file is named smoke_infer_<UTC>.jsonl — use that path."
    )
    return "\n".join(lines)


def messages_for_judge_context(messages: list[dict]) -> list[dict] | None:
    """Same as layer2_smoke_infer.messages_for_generation: last turn must be user."""
    out = list(messages)
    while out and out[-1].get("role") == "assistant":
        out.pop()
    if not out:
        return None
    if out[-1].get("role") != "user":
        return None
    return out


def load_repo_dotenv() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    p = REPO_ROOT / ".env"
    if p.is_file():
        load_dotenv(p, override=False)


def _read_jsonl_objects(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _manifest_by_id(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for obj in _read_jsonl_objects(path):
        lid = str(obj.get("layer2_id", "")).strip()
        if lid:
            out[lid] = obj
    return out


def _done_judge_ids(path: Path) -> set[str]:
    """Any layer2_id already present in the judge output (resume skips to avoid duplicate lines)."""
    if not path.exists():
        return set()
    done: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            lid = str(obj.get("layer2_id", "")).strip()
            if lid:
                done.add(lid)
    return done


def _messages_to_dialogue_text(messages: list[dict[str, Any]], max_chars: int = 12000) -> str:
    parts: list[str] = []
    for m in messages:
        role = str(m.get("role", ""))
        content = str(m.get("content", ""))
        parts.append(f"[{role}]\n{content}")
    text = "\n\n".join(parts)
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n... [truncated for judge context length]"
    return text


def _extract_json_object(text: str) -> dict[str, Any] | None:
    """Best-effort: first {...} block or fenced ```json."""
    t = text.strip()
    m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", t, re.IGNORECASE)
    if m:
        t = m.group(1).strip()
    start = t.find("{")
    if start < 0:
        return None
    depth = 0
    for i in range(start, len(t)):
        if t[i] == "{":
            depth += 1
        elif t[i] == "}":
            depth -= 1
            if depth == 0:
                chunk = t[start : i + 1]
                try:
                    return json.loads(chunk)
                except json.JSONDecodeError:
                    return None
    return None


# All dimension scores and overall use integer 1–100.
SCORE_MIN = 1
SCORE_MAX = 100
SCORE_DIMENSION_KEYS: tuple[str, ...] = (
    "relevance",
    "coherence",
    "helpfulness",
    "creativity",
    "clarity",
    "task_alignment",
    "depth",
    "chinese_quality",
)
SCORE_KEY_OVERALL = "overall"


def _int_in_range(value: Any, lo: int, hi: int) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return lo <= value <= hi
    if isinstance(value, float) and value == int(value):
        iv = int(value)
        return lo <= iv <= hi
    return False


def _build_user_prompt(
    stratum: str,
    dialogue_text: str,
    model_response: str,
) -> str:
    return f"""You evaluate a single assistant turn in a multi-turn dialogue.

**Stratum**: {stratum}
Weight your judgment accordingly: **core** = brainstorming / follow-up depth; **general** = instruction following and usefulness; **zh_guard** = Chinese dialogue quality (all strata still fill every numeric field below).

**Conversation (up to the last user turn; the model reply is scored separately):**
---
{dialogue_text}
---

**Model-generated assistant continuation (to score):**
---
{model_response}
---

Return **only** one JSON object. Use **integer** scores:
- **1–100** for each of: relevance, coherence, helpfulness, creativity, clarity, task_alignment, depth, chinese_quality
- **1–100** for **overall** (holistic quality for this turn, comparable across items)

Field meanings (brief):
- **relevance**: stays on topic.
- **coherence**: multi-turn flow and consistency.
- **helpfulness**: actionable value (questions, suggestions, summaries as appropriate).
- **creativity**: useful novelty / angles (especially for core).
- **clarity**: clear, readable expression.
- **task_alignment**: fulfills the user’s last request / intent.
- **depth**: probing or elaboration depth (core); concreteness of execution (general).
- **chinese_quality**: **required for every item.** If the reply is almost entirely English, score **100** (not applicable / no penalty). If Chinese is present, score naturalness and adequacy (1–100).
- **overall**: single composite 1–100 reflecting how good this assistant turn is.
- **rationale_zh**: one short sentence in **Chinese** summarizing the judgment.

No markdown fences, no extra keys."""


def _validate_scores(obj: dict[str, Any], _stratum: str) -> tuple[bool, str]:
    need = set(SCORE_DIMENSION_KEYS) | {SCORE_KEY_OVERALL, "rationale_zh"}
    missing = need - set(obj.keys())
    if missing:
        return False, f"missing keys: {sorted(missing)}"
    for k in SCORE_DIMENSION_KEYS:
        if not _int_in_range(obj[k], SCORE_MIN, SCORE_MAX):
            return False, f"{k} must be integer {SCORE_MIN}-{SCORE_MAX}, got {obj[k]!r}"
    if not _int_in_range(obj[SCORE_KEY_OVERALL], SCORE_MIN, SCORE_MAX):
        return False, f"{SCORE_KEY_OVERALL} must be integer {SCORE_MIN}-{SCORE_MAX}, got {obj[SCORE_KEY_OVERALL]!r}"
    rz = obj["rationale_zh"]
    if not isinstance(rz, str) or not str(rz).strip():
        return False, "rationale_zh must be non-empty string"
    return True, ""


def main() -> None:
    load_repo_dotenv()
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, default=REPO_ROOT / "data/eval/layer2/manifest_v0.jsonl")
    p.add_argument("--infer-jsonl", type=Path, required=True, help="Output from layer2_smoke_infer.py")
    p.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT
        / "experiment"
        / "baseline-gemma4e2b-it-layer2-v0"
        / "results"
        / "layer2_judge_scores.jsonl",
    )
    p.add_argument("--judge-model", type=str, default=os.getenv("LAYER2_JUDGE_MODEL", DEFAULT_JUDGE_MODEL))
    p.add_argument("--base-url", type=str, default=os.getenv("DASHSCOPE_OPENAI_BASE_URL", DEFAULT_BASE_URL))
    p.add_argument("--temperature", type=float, default=0.2)
    p.add_argument("--max-tokens", type=int, default=2048)
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--sleep", type=float, default=0.35, help="Seconds between API calls (rate limit courtesy).")
    p.add_argument("--resume", action="store_true", help="Skip layer2_id already present in --out (delete lines to retry).")
    p.add_argument("--limit", type=int, default=0, help="Max new judge calls (0 = no limit).")
    args = p.parse_args()

    resolved_manifest = _resolve_existing_file(args.manifest)
    if resolved_manifest is None:
        sys.exit(
            f"Manifest not found: {args.manifest}\n"
            f"Tried cwd-relative and under repo root: {REPO_ROOT}"
        )
    args.manifest = resolved_manifest

    resolved_infer = _resolve_existing_file(args.infer_jsonl)
    if resolved_infer is None:
        sys.exit(_infer_missing_help(args.infer_jsonl))
    args.infer_jsonl = resolved_infer

    if not args.out.is_absolute():
        args.out = (REPO_ROOT / args.out).resolve()

    api_key = (os.getenv("DASHSCOPE_API_KEY") or "").strip()
    if not api_key:
        sys.exit("Missing DASHSCOPE_API_KEY in environment or .env")

    try:
        from openai import OpenAI
    except ImportError:
        sys.exit("Missing openai. Run: pip install -r requirements-eval.txt")

    from tenacity import retry, stop_after_attempt, wait_exponential

    manifest = _manifest_by_id(args.manifest)
    infer_rows = _read_jsonl_objects(args.infer_jsonl)
    done = _done_judge_ids(args.out) if args.resume else set()

    client = OpenAI(api_key=api_key, base_url=args.base_url.strip(), timeout=args.timeout)

    system_msg = (
        "You are an impartial dialogue-quality evaluator. "
        "You must reply with a single JSON object only, no markdown fences."
    )

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60), reraise=True)
    def _call_judge(user_content: str) -> str:
        resp = client.chat.completions.create(
            model=args.judge_model,
            temperature=args.temperature,
            top_p=0.9,
            max_tokens=args.max_tokens,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_content},
            ],
        )
        choice = resp.choices[0].message
        return (choice.content or "").strip()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    new_count = 0
    skip_done = 0
    skip_missing = 0

    import time

    with args.out.open("a", encoding="utf-8") as fout:
        for row in infer_rows:
            lid = str(row.get("layer2_id", "")).strip()
            if not lid:
                continue
            if lid in done:
                skip_done += 1
                continue
            if args.limit and new_count >= args.limit:
                break

            mrec = manifest.get(lid)
            if not mrec:
                print(f"WARN skip {lid}: not in manifest", file=sys.stderr)
                skip_missing += 1
                continue

            stratum = str(mrec.get("stratum", "") or row.get("stratum", ""))
            messages_raw = mrec.get("messages")
            if not isinstance(messages_raw, list):
                print(f"WARN skip {lid}: bad messages", file=sys.stderr)
                skip_missing += 1
                continue

            msgs_ctx = messages_for_judge_context(messages_raw)
            if msgs_ctx is None:
                print(f"WARN skip {lid}: cannot build user-terminated dialogue", file=sys.stderr)
                skip_missing += 1
                continue

            completion = row.get("completion_text") or row.get("completion_preview") or ""
            if not str(completion).strip():
                print(f"WARN skip {lid}: empty completion", file=sys.stderr)
                skip_missing += 1
                continue

            dialogue = _messages_to_dialogue_text(msgs_ctx)
            user_prompt = _build_user_prompt(stratum, dialogue, str(completion))

            raw = ""
            parsed: dict[str, Any] | None = None
            ok = False
            err = ""
            try:
                raw = _call_judge(user_prompt)
                parsed = _extract_json_object(raw)
                if parsed is None:
                    err = "no_json_object"
                else:
                    ok, err = _validate_scores(parsed, stratum)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"

            out_obj: dict[str, Any] = {
                "layer2_id": lid,
                "stratum": stratum,
                "judge_model": args.judge_model,
                "judge_parse_ok": ok,
                "scores": parsed if ok else None,
                "judge_error": err if not ok else None,
                "judge_raw_preview": (raw[:4000] + ("..." if len(raw) > 4000 else "")) if raw else None,
            }
            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            fout.flush()

            if args.sleep > 0:
                time.sleep(args.sleep)

            new_count += 1
            status = "OK" if ok else "FAIL"
            print(f"{status} {lid} ({stratum})")

    print(
        f"Done. new_judged={new_count} skip_already={skip_done} skip_missing={skip_missing} -> {args.out}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
