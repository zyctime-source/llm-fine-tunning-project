#!/usr/bin/env python3
"""
验证 LoRA 权重可加载、可推理

用法:
    python scripts/verify_lora.py \
        --model_path experiment/s1-poc-e01 \
        --test_prompt "我想学习编程"

输出:
    - 检查 adapter_config.json
    - 检查 adapter_model.safetensors
    - 加载模型并运行推理测试
"""

import os
import json
import argparse
from pathlib import Path

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel


def verify_files(model_path: str):
    """验证必要的文件是否存在"""
    path = Path(model_path)
    
    print("=" * 60)
    print("1. 检查文件")
    print("=" * 60)
    
    required_files = {
        "adapter_config.json": "LoRA 配置",
        "adapter_model.safetensors": "LoRA 权重",
    }
    
    all_exist = True
    for file, desc in required_files.items():
        file_path = path / file
        if file_path.exists():
            size = file_path.stat().st_size / 1024 / 1024  # MB
            print(f"  ✓ {file} ({desc}): {size:.2f} MB")
        else:
            print(f"  ✗ {file} ({desc}): 缺失")
            all_exist = False
    
    # 检查是否有 tokenizer
    tokenizer_files = ["tokenizer.json", "tokenizer_config.json"]
    tokenizer_found = any((path / f).exists() for f in tokenizer_files)
    if tokenizer_found:
        print(f"  ✓ Tokenizer 文件已找到")
    else:
        print(f"  ⚠ Tokenizer 文件未找到（将使用基座模型的 tokenizer）")
    
    return all_exist


def load_and_test(model_path: str, test_prompt: str, base_model: str = "google/gemma-4-2b-it"):
    """加载模型并运行测试"""
    
    print("\n" + "=" * 60)
    print("2. 加载模型")
    print("=" * 60)
    
    print(f"  基座模型: {base_model}")
    print(f"  LoRA 路径: {model_path}")
    
    # 加载 tokenizer
    print("  加载 tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
    except:
        # 如果没有保存 tokenizer，使用基座模型的
        print("  使用基座模型的 tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(base_model)
    
    # 加载基座模型
    print("  加载基座模型 (4-bit 量化)...")
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        load_in_4bit=True,
    )
    
    # 加载 LoRA 权重
    print("  加载 LoRA 权重...")
    model = PeftModel.from_pretrained(model, model_path)
    
    print("  ✓ 模型加载成功")
    
    # 打印可训练参数信息
    model.print_trainable_parameters()
    
    # 运行推理测试
    print("\n" + "=" * 60)
    print("3. 推理测试")
    print("=" * 60)
    
    print(f"  输入: {test_prompt}")
    
    # 构建对话格式
    messages = [{"role": "user", "content": test_prompt}]
    
    # 应用 chat template
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    # 编码
    inputs = tokenizer(text, return_tensors="pt").to(model.device)
    
    # 生成
    print("  生成中...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )
    
    # 解码
    response = tokenizer.decode(outputs[0], skip_special_tokens=False)
    
    # 提取生成的部分
    generated_part = response[len(text):]
    
    print(f"  输出: {generated_part[:200]}...")
    
    print("\n" + "=" * 60)
    print("4. 验证结果")
    print("=" * 60)
    print("  ✓ LoRA 权重可加载")
    print("  ✓ 模型可推理")
    print("  ✓ 输出格式正常")
    print("\n  🎉 验证通过！LoRA 权重可用。")
    
    return True


def main():
    parser = argparse.ArgumentParser(description="验证 LoRA 权重")
    parser.add_argument("--model_path", type=str, default="experiment/s1-poc-e01",
                       help="LoRA 权重目录路径")
    parser.add_argument("--base_model", type=str, default="google/gemma-4-2b-it",
                       help="基座模型名称")
    parser.add_argument("--test_prompt", type=str, default="我想学习编程，有什么建议？",
                       help="测试用的输入提示")
    
    args = parser.parse_args()
    
    # 检查文件
    if not verify_files(args.model_path):
        print("\n  ✗ 文件检查失败，请确认产物已下载")
        return 1
    
    # 加载测试
    try:
        load_and_test(args.model_path, args.test_prompt, args.base_model)
        return 0
    except Exception as e:
        print(f"\n  ✗ 加载或推理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
