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

输出:
    - experiment/s1-poc-e01/results/poc_infer_full.jsonl
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
from tqdm import tqdm


def load_manifest(manifest_path: str, limit: Optional[int] = None) -> List[Dict]:
    """加载评测题单"""
    items = []
    with open(manifest_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if limit and i >= limit:
                break
            items.append(json.loads(line.strip()))
    return items


def run_inference(
    model,
    tokenizer,
    items: List[Dict],
    max_new_tokens: int = 2048,
    temperature: float = 0.1,
) -> List[Dict]:
    """运行推理"""
    results = []
    device = model.device
    
    for item in tqdm(items, desc="推理进度"):
        layer2_id = item.get("layer2_id")
        prompt = item.get("prompt", "")
        subset = item.get("subset", "unknown")
        
        try:
            # 构建输入
            messages = [{"role": "user", "content": prompt}]
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
                "subset": subset,
                "prompt": prompt,
                "response": generated,
                "model": "s1-poc-e01",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "success",
            }
        except Exception as e:
            result = {
                "layer2_id": layer2_id,
                "subset": subset,
                "prompt": prompt,
                "response": f"[ERROR: {str(e)}]",
                "model": "s1-poc-e01",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "status": "error",
                "error": str(e),
            }
        
        results.append(result)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="PoC Layer 2 全量推理")
    parser.add_argument("--model_path", type=str, default="experiment/s1-poc-e01",
                       help="微调后的模型目录")
    parser.add_argument("--base_model", type=str, default="google/gemma-4-2b-it",
                       help="基座模型名称或本地路径")
    parser.add_argument("--manifest", type=str, default="data/eval/layer2/manifest_v0.jsonl",
                       help="Layer 2 题单路径")
    parser.add_argument("--out", type=str, default=None,
                       help="输出 JSONL 路径（默认自动生成）")
    parser.add_argument("--limit", type=int, default=None,
                       help="限制条数（默认全量 500 条）")
    parser.add_argument("--max_new_tokens", type=int, default=2048,
                       help="最大生成 token 数")
    parser.add_argument("--resume", action="store_true",
                       help="断点续跑（跳过已存在的 layer2_id）")
    
    args = parser.parse_args()
    
    # 自动生成输出路径
    if args.out is None:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%MZ")
        limit_str = f"_n{args.limit}" if args.limit else ""
        args.out = f"experiment/s1-poc-e01/results/poc_infer_full{limit_str}_{timestamp}.jsonl"
    
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("PoC Layer 2 全量推理")
    print("=" * 70)
    print(f"模型路径: {args.model_path}")
    print(f"基座模型: {args.base_model}")
    print(f"题单路径: {args.manifest}")
    if args.limit:
        print(f"限制条数: {args.limit}")
    else:
        print("推理条数: 全量 (500 条)")
    print(f"输出文件: {args.out}")
    if args.resume:
        print("断点续跑: 是")
    print("=" * 70)
    
    # 检查模型路径
    if not (Path(args.model_path) / "adapter_model.safetensors").exists():
        print(f"\n✗ 错误: 未找到 LoRA 权重")
        return 1
    
    # 加载已存在的结果（断点续跑）
    existing_ids = set()
    if args.resume and out_path.exists():
        print("\n检查已存在的结果...")
        with open(out_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    r = json.loads(line.strip())
                    existing_ids.add(r.get("layer2_id"))
                except:
                    pass
        print(f"  已存在 {len(existing_ids)} 条结果，将跳过")
    
    # 加载模型
    print("\n[1/4] 加载模型...")
    print("  - Tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(args.model_path)
    except:
        print("  - 使用基座模型 Tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    
    print("  - 基座模型 (4-bit)...")
    # 检查本地缓存
    if Path(args.base_model).exists():
        print(f"    使用本地模型: {args.base_model}")
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            load_in_4bit=True,
        )
    else:
        print(f"    从 Hugging Face 下载: {args.base_model}")
        model = AutoModelForCausalLM.from_pretrained(
            args.base_model,
            torch_dtype=torch.bfloat16,
            device_map="auto",
            load_in_4bit=True,
        )
    
    print("  - LoRA 权重...")
    model = PeftModel.from_pretrained(model, args.model_path)
    print("  ✓ 模型加载完成")
    
    # 加载题单
    print("\n[2/4] 加载题单...")
    all_items = load_manifest(args.manifest, limit=args.limit)
    
    # 过滤已存在的（断点续跑）
    if existing_ids:
        items = [item for item in all_items if item.get("layer2_id") not in existing_ids]
        print(f"  全量: {len(all_items)} 条")
        print(f"  跳过: {len(existing_ids)} 条")
        print(f"  待推理: {len(items)} 条")
    else:
        items = all_items
        print(f"  加载了 {len(items)} 条")
    
    if not items:
        print("\n✓ 所有样本已完成！")
        return 0
    
    # 运行推理
    print(f"\n[3/4] 运行推理...")
    results = run_inference(model, tokenizer, items, max_new_tokens=args.max_new_tokens)
    
    # 保存结果
    print(f"\n[4/4] 保存结果...")
    
    # 断点续跑模式：追加写入
    mode = 'a' if args.resume and existing_ids else 'w'
    with open(args.out, mode, encoding='utf-8') as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    
    print(f"  ✓ 结果已保存: {args.out}")
    
    # 统计
    success_count = sum(1 for r in results if r.get("status") == "success")
    error_count = len(results) - success_count
    
    print("\n" + "=" * 70)
    print("推理完成统计")
    print("=" * 70)
    print(f"总样本: {len(results)}")
    print(f"成功: {success_count}")
    print(f"失败: {error_count}")
    print(f"成功率: {success_count / len(results) * 100:.1f}%")
    
    if success_count == len(results):
        print("\n✓ 全部成功！")
        print("\n下一步:")
        print("  1. 下载结果到本地")
        print("  2. 运行评委打分 (layer2_judge_scores.py)")
        return 0
    else:
        print(f"\n⚠ {error_count} 条失败，建议检查错误原因")
        return 1


if __name__ == "__main__":
    exit(main())
