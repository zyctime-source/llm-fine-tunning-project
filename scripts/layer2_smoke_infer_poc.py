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

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from tqdm import tqdm


def load_manifest(manifest_path: str, limit: int = 10) -> List[Dict]:
    """加载评测题单"""
    items = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
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
    temperature: float = 0.1,  # 评测用贪心/低温度
) -> List[Dict]:
    """运行推理"""
    results = []
    
    device = model.device
    
    for item in tqdm(items, desc="推理"):
        layer2_id = item.get("layer2_id")
        prompt = item.get("prompt", "")
        
        # 构建输入
        messages = [{"role": "user", "content": prompt}]
        
        # 应用 chat template
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # 编码
        inputs = tokenizer(text, return_tensors="pt").to(device)
        
        # 生成
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=1.0,
                do_sample=temperature > 0,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
        
        # 解码
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=False)
        generated = full_response[len(text):].strip()
        
        result = {
            "layer2_id": layer2_id,
            "prompt": prompt,
            "response": generated,
            "model": "s1-poc-e01",
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        results.append(result)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="PoC Layer 2 冒烟测试")
    parser.add_argument("--model_path", type=str, default="experiment/s1-poc-e01",
                       help="微调后的模型目录")
    parser.add_argument("--base_model", type=str, default="google/gemma-4-2b-it",
                       help="基座模型名称")
    parser.add_argument("--manifest", type=str, default="data/eval/layer2/manifest_v0.jsonl",
                       help="Layer 2 题单路径")
    parser.add_argument("--out", type=str, default=None,
                       help="输出 JSONL 路径（默认自动生成）")
    parser.add_argument("--limit", type=int, default=10,
                       help="测试条数（默认前 10 条）")
    parser.add_argument("--max_new_tokens", type=int, default=2048,
                       help="最大生成 token 数")
    
    args = parser.parse_args()
    
    # 自动生成输出路径
    if args.out is None:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%MZ")
        args.out = f"experiment/s1-poc-e01/results/poc_infer_smoke_{timestamp}.jsonl"
    
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("PoC Layer 2 冒烟测试")
    print("=" * 70)
    print(f"模型: {args.model_path}")
    print(f"基座: {args.base_model}")
    print(f"题单: {args.manifest}")
    print(f"测试条数: {args.limit}")
    print(f"输出: {args.out}")
    print("=" * 70)
    
    # 检查模型路径
    if not (Path(args.model_path) / "adapter_model.safetensors").exists():
        print(f"\n✗ 错误: 未找到 LoRA 权重: {args.model_path}/adapter_model.safetensors")
        print("  请确认产物已下载到本地")
        return 1
    
    # 加载模型
    print("\n[1/3] 加载模型...")
    print("  - Tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    except:
        print("  - 使用基座模型 Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    
    print("  - 基座模型 (4-bit)...")
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        load_in_4bit=True,
    )
    
    print("  - LoRA 权重...")
    model = PeftModel.from_pretrained(model, args.model_path)
    
    print("  ✓ 模型加载完成")
    model.print_trainable_parameters()
    
    # 加载题单
    print(f"\n[2/3] 加载题单（前 {args.limit} 条）...")
    items = load_manifest(args.manifest, limit=args.limit)
    print(f"  ✓ 加载了 {len(items)} 条")
    
    # 显示测试内容
    print("\n测试样本:")
    for i, item in enumerate(items):
        layer2_id = item.get("layer2_id", "unknown")
        subset = item.get("subset", "unknown")
        prompt_preview = item.get("prompt", "")[:50] + "..."
        print(f"  {i+1}. [{subset}] {layer2_id}: {prompt_preview}")
    
    # 运行推理
    print(f"\n[3/3] 运行推理...")
    results = run_inference(model, tokenizer, items, max_new_tokens=args.max_new_tokens)
    
    # 保存结果
    print(f"\n保存结果到: {args.out}")
    with open(args.out, 'w', encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    # 显示结果预览
    print("\n" + "=" * 70)
    print("推理结果预览")
    print("=" * 70)
    for r in results:
        print(f"\n【{r['layer2_id']}】")
        print(f"Prompt: {r['prompt'][:80]}...")
        print(f"Response: {r['response'][:200]}...")
        print("-" * 70)
    
    print("\n" + "=" * 70)
    print("✓ 冒烟测试完成")
    print("=" * 70)
    print(f"输出文件: {args.out}")
    print("\n下一步:")
    print("  1. 检查输出质量（是否相关、格式是否正确）")
    print("  2. 对比基线输出（experiment/baseline-gemma4e2b-it-layer2-v0/results/）")
    print("  3. 如果正常，进入 D4 全量评估")
    
    return 0


if __name__ == "__main__":
    exit(main())
