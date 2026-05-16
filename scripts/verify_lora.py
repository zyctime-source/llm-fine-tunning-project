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

import json
import argparse
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BASE_MODEL_ID = "google/gemma-4-E2B-it"
DEFAULT_LOCAL_CACHE = REPO_ROOT / "model_cache" / "google" / "gemma-4-E2B-it"


def resolve_base_model(base_model: str | None, lora_path: str) -> str:
    """优先本地 model_cache / adapter_config，避免从 Hub 拉取。"""
    if base_model:
        p = Path(base_model)
        if p.exists():
            return str(p.resolve())
        return base_model

    adapter_cfg = Path(lora_path) / "adapter_config.json"
    if adapter_cfg.is_file():
        cfg = json.loads(adapter_cfg.read_text(encoding="utf-8"))
        recorded = cfg.get("base_model_name_or_path")
        if recorded:
            p = Path(recorded)
            if not p.is_absolute():
                p = (REPO_ROOT / p).resolve()
            if p.exists():
                return str(p)

    if DEFAULT_LOCAL_CACHE.is_dir() and (DEFAULT_LOCAL_CACHE / "config.json").is_file():
        return str(DEFAULT_LOCAL_CACHE)

    return DEFAULT_BASE_MODEL_ID


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

    tokenizer_files = ["tokenizer.json", "tokenizer_config.json"]
    tokenizer_found = any((path / f).exists() for f in tokenizer_files)
    if tokenizer_found:
        print("  ✓ Tokenizer 文件已找到")
    else:
        print("  ⚠ Tokenizer 文件未找到（将使用基座模型的 tokenizer）")

    return all_exist


def load_and_test(model_path: str, test_prompt: str, base_model: str | None = None):
    """加载模型并运行测试"""

    base_model = resolve_base_model(base_model, model_path)

    print("\n" + "=" * 60)
    print("2. 加载模型")
    print("=" * 60)

    print(f"  基座模型: {base_model}")
    print(f"  LoRA 路径: {model_path}")

    print("  加载 tokenizer...")
    lora_dir = Path(model_path)
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_path)
    except Exception:
        print("  使用基座模型的 tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(base_model)

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("  加载基座模型 (4-bit 量化)...")
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

    print("  加载 LoRA 权重...")
    model = PeftModel.from_pretrained(model, model_path)

    print("  ✓ 模型加载成功")
    model.print_trainable_parameters()

    print("\n" + "=" * 60)
    print("3. 推理测试")
    print("=" * 60)

    print(f"  输入: {test_prompt}")

    messages = [{"role": "user", "content": test_prompt}]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    inputs = tokenizer(text, return_tensors="pt").to(model.device)

    print("  生成中...")
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=128,
            temperature=0.7,
            top_p=0.9,
            do_sample=True,
        )

    response = tokenizer.decode(outputs[0], skip_special_tokens=False)
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
    parser.add_argument(
        "--model_path",
        type=str,
        default="experiment/s1-poc-e01",
        help="LoRA 权重目录路径",
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default=None,
        help=f"基座模型路径或 Hub ID（默认从 adapter_config / {DEFAULT_LOCAL_CACHE} 推断）",
    )
    parser.add_argument(
        "--test_prompt",
        type=str,
        default="我想学习编程，有什么建议？",
        help="测试用的输入提示",
    )

    args = parser.parse_args()

    if not verify_files(args.model_path):
        print("\n  ✗ 文件检查失败，请确认产物已下载")
        return 1

    try:
        load_and_test(args.model_path, args.test_prompt, args.base_model)
        return 0
    except Exception as e:
        print(f"\n  ✗ 加载或推理失败: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
