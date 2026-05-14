#!/usr/bin/env python3
"""
Layer 2 smoke inference: load Gemma-4-E2B-IT and run greedy generation on the first N
manifest items (eval-protocol-v0: do_sample=False, temperature=0).

Uses AutoTokenizer + AutoModelForCausalLM (text-only). We intentionally avoid AutoProcessor
here: Gemma-4's processor stack pulls Gemma4VideoProcessor, which requires torchvision even
when you only run text — unnecessary for this Layer 2 JSONL manifest.

Alpaca-style rows in the manifest may end with a reference assistant turn; for inference
we strip trailing assistant messages so the model is not conditioned on the gold answer.

Usage:
  python scripts/layer2_smoke_infer.py --dry-run
  pip install -r requirements-eval.txt
  python scripts/layer2_smoke_infer.py --limit 3 --max-new-tokens 128
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO_ROOT / "data" / "eval" / "layer2" / "manifest_v0.jsonl"
DEFAULT_MODEL = "google/gemma-4-E2B-it"


def load_repo_dotenv() -> None:
    """Load HF_TOKEN, HF_ENDPOINT, etc. from repo-root .env (optional python-dotenv)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    env_path = REPO_ROOT / ".env"
    if env_path.is_file():
        load_dotenv(env_path, override=False)


def messages_for_generation(messages: list[dict]) -> list[dict] | None:
    """Drop trailing assistant turns so the last message is from the user (or empty)."""
    out = list(messages)
    while out and out[-1].get("role") == "assistant":
        out.pop()
    if not out:
        return None
    if out[-1].get("role") != "user":
        return None
    return out


def load_manifest_rows(path: Path, limit: int) -> list[dict]:
    rows: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
            if len(rows) >= limit:
                break
    return rows


def ensure_eval_dependencies() -> None:
    """Fail fast with an actionable message if the eval venv is incomplete."""
    try:
        import torch  # noqa: F401
    except ModuleNotFoundError:
        sys.exit(
            "Missing package: torch. With llm-eval (or your eval venv) active, run:\n"
            "  pip install -r requirements-eval.txt\n"
            "See experiment/README.md (Layer 2 / smoke)."
        )
    try:
        import transformers  # noqa: F401
    except ModuleNotFoundError:
        sys.exit(
            "Missing package: transformers. Run:\n"
            "  pip install -r requirements-eval.txt"
        )


def run_inference(
    model_id: str,
    rows: list[dict],
    max_new_tokens: int,
    output_path: Path,
) -> None:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=dtype,
    )
    if not torch.cuda.is_available():
        model = model.to("cpu")

    out_lines: list[dict] = []
    for rec in rows:
        lid = rec["layer2_id"]
        msgs_in = messages_for_generation(rec["messages"])
        if msgs_in is None:
            print(f"SKIP {lid}: could not derive user-terminated prompt from messages", file=sys.stderr)
            continue

        tokenized = tokenizer.apply_chat_template(
            msgs_in,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        )

        input_ids = tokenized["input_ids"].to(model.device)
        attention_mask = tokenized.get("attention_mask")
        if attention_mask is not None:
            attention_mask = attention_mask.to(model.device)

        pad_id = tokenizer.pad_token_id
        if pad_id is None:
            pad_id = tokenizer.eos_token_id

        with torch.inference_mode():
            generated = model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                max_new_tokens=max_new_tokens,
                do_sample=False,
                temperature=None,
                top_p=None,
                pad_token_id=pad_id,
            )

        prompt_len = input_ids.shape[1]
        new_tokens = generated[0, prompt_len:]
        text = tokenizer.batch_decode([new_tokens], skip_special_tokens=True)[0]

        out_lines.append(
            {
                "layer2_id": lid,
                "stratum": rec.get("stratum"),
                "prompt_message_count": len(msgs_in),
                "max_new_tokens": max_new_tokens,
                "completion_preview": text[:2000],
            }
        )
        print(f"OK {lid} ({rec.get('stratum')}) preview_len={len(text)}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for obj in out_lines:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")
    print(f"Wrote {len(out_lines)} lines -> {output_path}")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    p.add_argument("--model", type=str, default=DEFAULT_MODEL)
    p.add_argument("--limit", type=int, default=3)
    p.add_argument("--max-new-tokens", type=int, default=128)
    p.add_argument(
        "--out",
        type=Path,
        default=None,
        help="Output JSONL (default: under experiment/baseline.../results/)",
    )
    p.add_argument("--dry-run", action="store_true", help="Validate manifest only; do not load the model.")
    args = p.parse_args()

    load_repo_dotenv()

    if not args.manifest.is_file():
        sys.exit(f"Manifest not found: {args.manifest}")

    rows = load_manifest_rows(args.manifest, args.limit)
    if not rows:
        sys.exit("No manifest rows loaded.")

    for rec in rows:
        lid = rec["layer2_id"]
        g = messages_for_generation(rec["messages"])
        if g is None:
            print(f"WARN {lid}: cannot build prompt from messages", file=sys.stderr)
        else:
            print(f"CHECK {lid} stratum={rec.get('stratum')} prompt_turns={len(g)}")

    if args.dry_run:
        print("Dry run OK (--dry-run); no model loaded.")
        return

    ensure_eval_dependencies()

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
    out = args.out
    if out is None:
        out = (
            REPO_ROOT
            / "experiment"
            / "baseline-gemma4e2b-it-layer2-v0"
            / "results"
            / f"smoke_infer_{ts}.jsonl"
        )

    run_inference(args.model, rows, args.max_new_tokens, out)


if __name__ == "__main__":
    main()
