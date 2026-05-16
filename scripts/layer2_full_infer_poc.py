#!/usr/bin/env python3
"""
PoC 后 Layer 2 全量推理（500 条）

用法:
    # 在 AutoDL 上运行（有 GPU）
    python scripts/layer2_full_infer_poc.py \
        --model_path experiment/s1-poc-e01 \
        --manifest data/eval/layer2/manifest_v0.jsonl \
        --out experiment/s1-poc-e01/results/poc_infer_full.jsonl

    # 限制条数测试
    python scripts/layer2_full_infer_poc.py --limit 50 ...

    # 断点续跑
    python scripts/layer2_full_infer_poc.py --resume --out experiment/s1-poc-e01/results/poc_infer_full.jsonl
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent))
from verify_lora import resolve_base_model


def messages_for_generation(messages: list[dict]) -> list[dict] | None:
    """去掉末尾 assistant，保证最后一条为 user。"""
    out = list(messages)
    while out and out[-1].get("role") == "assistant":
        out.pop()
    if not out or out[-1].get("role") != "user":
        return None
    return out


def load_manifest(manifest_path: str, limit: Optional[int] = None) -> List[Dict]:
    """加载评测题单"""
    items = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            items.append(json.loads(line.strip()))
    return items


def load_existing_ids(out_path: Path) -> set[str]:
    """读取已完成的 layer2_id（断点续跑）。"""
    if not out_path.is_file():
        return set()
    ids = set()
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
                if row.get("layer2_id"):
                    ids.add(row["layer2_id"])
            except json.JSONDecodeError:
                continue
    return ids


def run_inference_streaming(
    model,
    tokenizer,
    items: List[Dict],
    out_path: Path,
    max_new_tokens: int = 2048,
) -> tuple[int, int]:
    """流式推理并逐条写入 JSONL（eval-protocol-v0：贪心解码）。"""
    device = model.device
    pad_id = tokenizer.pad_token_id or tokenizer.eos_token_id
    success_count = 0
    error_count = 0

    with out_path.open("a", encoding="utf-8") as fout:
        for item in tqdm(items, desc="推理进度"):
            layer2_id = item.get("layer2_id")
            stratum = item.get("stratum", "unknown")

            try:
                msgs_in = messages_for_generation(item.get("messages", []))
                if msgs_in is None:
                    raise ValueError("无法从 messages 构造 user-terminated prompt")

                tokenized = tokenizer.apply_chat_template(
                    msgs_in,
                    add_generation_prompt=True,
                    return_tensors="pt",
                    return_dict=True,
                )
                input_ids = tokenized["input_ids"].to(device)
                attention_mask = tokenized.get("attention_mask")
                if attention_mask is not None:
                    attention_mask = attention_mask.to(device)

                with torch.inference_mode():
                    generated = model.generate(
                        input_ids=input_ids,
                        attention_mask=attention_mask,
                        max_new_tokens=max_new_tokens,
                        do_sample=False,
                        pad_token_id=pad_id,
                    )

                prompt_len = input_ids.shape[1]
                new_tokens = generated[0, prompt_len:]
                text = tokenizer.batch_decode([new_tokens], skip_special_tokens=True)[0]

                result = {
                    "layer2_id": layer2_id,
                    "stratum": stratum,
                    "prompt_message_count": len(msgs_in),
                    "max_new_tokens": max_new_tokens,
                    "completion_text": text,
                    "completion_preview": text[:2000],
                    "model": "s1-poc-e01",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "success",
                }
                success_count += 1
            except Exception as e:
                result = {
                    "layer2_id": layer2_id,
                    "stratum": stratum,
                    "completion_text": "",
                    "completion_preview": f"[ERROR: {e}]",
                    "model": "s1-poc-e01",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "status": "error",
                    "error": str(e),
                }
                error_count += 1

            fout.write(json.dumps(result, ensure_ascii=False) + "\n")
            fout.flush()

    return success_count, error_count


def main():
    parser = argparse.ArgumentParser(description="PoC Layer 2 全量推理")
    parser.add_argument(
        "--model_path",
        type=str,
        default="experiment/s1-poc-e01",
        help="微调后的模型目录",
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default=None,
        help="基座模型路径或 Hub ID（默认从 adapter_config / model_cache 推断）",
    )
    parser.add_argument(
        "--manifest",
        type=str,
        default="data/eval/layer2/manifest_v0.jsonl",
        help="Layer 2 题单路径",
    )
    parser.add_argument(
        "--out",
        type=str,
        default=None,
        help="输出 JSONL 路径（默认自动生成）",
    )
    parser.add_argument("--limit", type=int, default=None, help="限制条数（默认全量 500 条）")
    parser.add_argument("--max_new_tokens", type=int, default=2048, help="最大生成 token 数")
    parser.add_argument("--resume", action="store_true", help="断点续跑（跳过已存在的 layer2_id）")

    args = parser.parse_args()

    base_model = resolve_base_model(args.base_model, args.model_path)

    if args.out is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
        limit_str = f"_n{args.limit}" if args.limit else ""
        args.out = f"experiment/s1-poc-e01/results/poc_infer_full{limit_str}_{timestamp}.jsonl"

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PoC Layer 2 全量推理")
    print("=" * 70)
    print(f"模型路径: {args.model_path}")
    print(f"基座模型: {base_model}")
    print(f"题单路径: {args.manifest}")
    print(f"推理条数: {args.limit if args.limit else '全量 (500 条)'}")
    print(f"输出文件: {args.out}")
    print(f"断点续跑: {'是' if args.resume else '否'}")
    print("=" * 70)

    if not (Path(args.model_path) / "adapter_model.safetensors").exists():
        print("\n✗ 错误: 未找到 LoRA 权重")
        return 1

    existing_ids: set[str] = set()
    if args.resume:
        existing_ids = load_existing_ids(out_path)
        if existing_ids:
            print(f"\n已存在 {len(existing_ids)} 条结果，将跳过")

    print("\n[1/4] 加载模型...")
    print("  - Tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    except Exception:
        print("  - 使用基座模型 Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(base_model)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("  - 基座模型 (4-bit)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        quantization_config=bnb_config,
        device_map="auto",
    )

    print("  - LoRA 权重...")
    model = PeftModel.from_pretrained(model, args.model_path)
    print("  ✓ 模型加载完成")

    print("\n[2/4] 加载题单...")
    all_items = load_manifest(args.manifest, limit=args.limit)
    items = [it for it in all_items if it.get("layer2_id") not in existing_ids] if existing_ids else all_items
    print(f"  全量: {len(all_items)} 条")
    if existing_ids:
        print(f"  跳过: {len(existing_ids)} 条")
    print(f"  待推理: {len(items)} 条")

    if not items:
        print("\n✓ 所有样本已完成！")
        return 0

    if not args.resume or not existing_ids:
        out_path.write_text("", encoding="utf-8")

    print("\n[3/4] 运行推理...")
    success_count, error_count = run_inference_streaming(
        model, tokenizer, items, out_path, max_new_tokens=args.max_new_tokens
    )

    print(f"\n[4/4] 结果已保存: {args.out}")

    total = success_count + error_count
    print("\n" + "=" * 70)
    print("推理完成统计")
    print("=" * 70)
    print(f"本次推理: {total}")
    print(f"成功: {success_count}")
    print(f"失败: {error_count}")
    if total:
        print(f"成功率: {success_count / total * 100:.1f}%")

    if error_count == 0:
        print("\n✓ 全部成功！")
        print("\n下一步:")
        print("  1. 下载结果到本地")
        print("  2. 运行评委打分 (layer2_judge_scores.py)")
        return 0

    print(f"\n⚠ {error_count} 条失败，建议检查错误原因")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
