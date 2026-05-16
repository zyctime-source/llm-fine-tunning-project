#!/usr/bin/env python3
"""
PoC 后 Layer 2 冒烟测试（前 10 条快速验证）

用法:
    python scripts/layer2_smoke_infer_poc.py \
        --model_path experiment/s1-poc-e01 \
        --manifest data/eval/layer2/manifest_v0.jsonl \
        --out experiment/s1-poc-e01/results/poc_infer_smoke.jsonl

功能:
    - 加载微调后的 LoRA 模型
    - 跑 Layer 2 前 10 条作为冒烟测试
    - 对比基线观察差异
"""

import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any

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
    """去掉末尾 assistant，保证最后一条为 user（与基线脚本一致）。"""
    out = list(messages)
    while out and out[-1].get("role") == "assistant":
        out.pop()
    if not out or out[-1].get("role") != "user":
        return None
    return out


def load_manifest(manifest_path: str, limit: int = 10) -> List[Dict]:
    """加载评测题单"""
    items = []
    with open(manifest_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i >= limit:
                break
            items.append(json.loads(line.strip()))
    return items


def run_inference(
    model,
    tokenizer,
    items: List[Dict],
    max_new_tokens: int = 2048,
) -> List[Dict]:
    """运行推理（eval-protocol-v0：贪心解码）"""
    results = []
    device = model.device
    pad_id = tokenizer.pad_token_id or tokenizer.eos_token_id

    for item in tqdm(items, desc="推理"):
        layer2_id = item.get("layer2_id")
        msgs_in = messages_for_generation(item.get("messages", []))
        if msgs_in is None:
            print(f"SKIP {layer2_id}: 无法从 messages 构造 prompt", file=sys.stderr)
            continue

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

        results.append({
            "layer2_id": layer2_id,
            "stratum": item.get("stratum"),
            "prompt_message_count": len(msgs_in),
            "max_new_tokens": max_new_tokens,
            "completion_text": text,
            "completion_preview": text[:2000],
            "model": "s1-poc-e01",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="PoC Layer 2 冒烟测试")
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
    parser.add_argument("--limit", type=int, default=10, help="测试条数（默认前 10 条）")
    parser.add_argument("--max_new_tokens", type=int, default=2048, help="最大生成 token 数")

    args = parser.parse_args()

    base_model = resolve_base_model(args.base_model, args.model_path)

    if args.out is None:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%MZ")
        args.out = f"experiment/s1-poc-e01/results/poc_infer_smoke_{timestamp}.jsonl"

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("PoC Layer 2 冒烟测试")
    print("=" * 70)
    print(f"模型: {args.model_path}")
    print(f"基座: {base_model}")
    print(f"题单: {args.manifest}")
    print(f"测试条数: {args.limit}")
    print(f"输出: {args.out}")
    print("=" * 70)

    if not (Path(args.model_path) / "adapter_model.safetensors").exists():
        print(f"\n✗ 错误: 未找到 LoRA 权重: {args.model_path}/adapter_model.safetensors")
        return 1

    print("\n[1/3] 加载模型...")
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
    model.print_trainable_parameters()

    print(f"\n[2/3] 加载题单（前 {args.limit} 条）...")
    items = load_manifest(args.manifest, limit=args.limit)
    print(f"  ✓ 加载了 {len(items)} 条")

    print("\n测试样本:")
    for i, item in enumerate(items):
        layer2_id = item.get("layer2_id", "unknown")
        stratum = item.get("stratum", "unknown")
        msgs = messages_for_generation(item.get("messages", []))
        preview = msgs[-1]["content"][:50] + "..." if msgs else "(无 prompt)"
        print(f"  {i + 1}. [{stratum}] {layer2_id}: {preview}")

    print("\n[3/3] 运行推理...")
    results = run_inference(model, tokenizer, items, max_new_tokens=args.max_new_tokens)

    print(f"\n保存结果到: {args.out}")
    with open(args.out, "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n" + "=" * 70)
    print("推理结果预览")
    print("=" * 70)
    for r in results:
        print(f"\n【{r['layer2_id']}】")
        print(f"Response: {r['completion_preview'][:200]}...")
        print("-" * 70)

    print("\n" + "=" * 70)
    print("✓ 冒烟测试完成")
    print("=" * 70)
    print(f"输出文件: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
