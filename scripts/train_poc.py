#!/usr/bin/env python3
"""
Sprint 1 Week 2 PoC 训练脚本
用于 AutoDL / GPU 环境进行 LoRA 微调

用法:
    cd /path/to/repo
    conda create -n llm-train python=3.11 -y
    conda activate llm-train
    pip install -r requirements-train.txt
    
    # 运行训练
    python scripts/train_poc.py \
        --data_path data/poc_v1.0_1k.jsonl \
        --output_dir experiment/s1-poc-e01

特征:
- 使用 TRL SFTTrainer 进行监督微调
- 支持 LoRA (PEFT)
- 自动保存 LoRA 权重到实验目录
- 支持 wandb 日志 (可选)
"""

import os
import sys
import json
import argparse
import logging
from pathlib import Path
from typing import Optional

import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    TrainingArguments,
    DataCollatorForSeq2Seq,
)
from datasets import Dataset
from peft import LoraConfig, get_peft_model, TaskType, PeftModel
from trl import SFTTrainer, SFTConfig

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('training.log')
    ]
)
logger = logging.getLogger(__name__)


def load_poc_data(data_path: str, max_samples: Optional[int] = None) -> Dataset:
    """
    加载 PoC 数据并转换为 HuggingFace Dataset 格式
    
    输入格式: {"id": str, "source": str, "messages": [{"role": "user/assistant", "content": str}]}
    输出格式: {"text": str} (ShareGPT 风格格式化后的对话)
    """
    logger.info(f"加载数据: {data_path}")
    
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            
            # 将 messages 格式化为对话文本
            messages = item.get('messages', [])
            if not messages:
                continue
            
            # 使用 tokenizer.apply_chat_template 的标准格式
            formatted = {"messages": messages, "id": item.get("id")}
            data.append(formatted)
            
            if max_samples and len(data) >= max_samples:
                break
    
    logger.info(f"加载了 {len(data)} 条样本")
    return Dataset.from_list(data)


def setup_model_and_tokenizer(
    model_name: str = "google/gemma-4-2b-it",
    load_in_4bit: bool = False,
    load_in_8bit: bool = False,
):
    """加载基座模型和 tokenizer"""
    logger.info(f"加载基座模型: {model_name}")
    
    # 加载 tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # 加载模型
    model_kwargs = {
        "torch_dtype": torch.bfloat16,
        "device_map": "auto",
    }
    
    if load_in_4bit:
        model_kwargs["load_in_4bit"] = True
    elif load_in_8bit:
        model_kwargs["load_in_8bit"] = True
    
    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    
    logger.info(f"模型加载完成: {model_name}")
    logger.info(f"模型参数量: {sum(p.numel() for p in model.parameters()) / 1e9:.2f}B")
    
    return model, tokenizer


def setup_lora_config(
    r: int = 8,
    lora_alpha: int = 16,
    target_modules: Optional[list] = None,
    lora_dropout: float = 0.05,
):
    """配置 LoRA"""
    if target_modules is None:
        # Gemma 模型的注意力模块
        target_modules = ["q_proj", "k_proj", "v_proj", "o_proj"]
    
    lora_config = LoraConfig(
        r=r,
        lora_alpha=lora_alpha,
        target_modules=target_modules,
        lora_dropout=lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    
    logger.info(f"LoRA 配置: r={r}, alpha={lora_alpha}, target={target_modules}")
    return lora_config


def formatting_prompts_func(example, tokenizer, max_seq_length: int = 2048):
    """
    格式化样本为训练文本
    使用模型的 chat template
    """
    messages = example["messages"]
    
    # 使用 tokenizer 的 chat template 格式化对话
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=False
    )
    
    return {"text": text}


def main():
    parser = argparse.ArgumentParser(description="Sprint 1 Week 2 PoC 训练")
    
    # 数据参数
    parser.add_argument("--data_path", type=str, default="data/poc_v1.0_1k.jsonl",
                       help="训练数据路径")
    parser.add_argument("--max_samples", type=int, default=None,
                       help="最大使用样本数（用于快速测试）")
    
    # 模型参数
    parser.add_argument("--model_name", type=str, default="google/gemma-4-2b-it",
                       help="基座模型名称")
    parser.add_argument("--load_in_4bit", action="store_true",
                       help="使用 4-bit 量化（节省显存）")
    parser.add_argument("--load_in_8bit", action="store_true",
                       help="使用 8-bit 量化（节省显存）")
    
    # LoRA 参数
    parser.add_argument("--lora_r", type=int, default=8,
                       help="LoRA rank")
    parser.add_argument("--lora_alpha", type=int, default=16,
                       help="LoRA alpha")
    parser.add_argument("--lora_dropout", type=float, default=0.05,
                       help="LoRA dropout")
    
    # 训练参数
    parser.add_argument("--output_dir", type=str, default="experiment/s1-poc-e01",
                       help="输出目录")
    parser.add_argument("--num_epochs", type=int, default=1,
                       help="训练轮数")
    parser.add_argument("--batch_size", type=int, default=1,
                       help="批次大小")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4,
                       help="梯度累积步数")
    parser.add_argument("--learning_rate", type=float, default=2e-4,
                       help="学习率")
    parser.add_argument("--warmup_steps", type=int, default=50,
                       help="warmup 步数")
    parser.add_argument("--max_seq_length", type=int, default=2048,
                       help="最大序列长度")
    parser.add_argument("--seed", type=int, default=42,
                       help="随机种子")
    
    # 日志参数
    parser.add_argument("--use_wandb", action="store_true",
                       help="使用 wandb 记录日志")
    parser.add_argument("--wandb_project", type=str, default="llm-fine-tuning-poc",
                       help="wandb 项目名")
    
    args = parser.parse_args()
    
    # 设置随机种子
    torch.manual_seed(args.seed)
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 加载数据
    dataset = load_poc_data(args.data_path, max_samples=args.max_samples)
    
    # 加载模型和 tokenizer
    model, tokenizer = setup_model_and_tokenizer(
        model_name=args.model_name,
        load_in_4bit=args.load_in_4bit,
        load_in_8bit=args.load_in_8bit,
    )
    
    # 设置 LoRA
    lora_config = setup_lora_config(
        r=args.lora_r,
        lora_alpha=args.lora_alpha,
        lora_dropout=args.lora_dropout,
    )
    
    # 应用 LoRA 到模型
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()
    
    # 训练配置
    training_args = SFTConfig(
        output_dir=str(output_dir),
        num_train_epochs=args.num_epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        warmup_steps=args.warmup_steps,
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        max_seq_length=args.max_seq_length,
        seed=args.seed,
        report_to="wandb" if args.use_wandb else None,
        run_name=f"s1-poc-e01-r{args.lora_r}-lr{args.learning_rate}",
        # 优化器设置
        optim="adamw_torch",
        weight_decay=0.01,
        lr_scheduler_type="cosine",
        # 其他
        fp16=False,
        bf16=True,  # RTX 5090 支持 bfloat16
        dataloader_num_workers=0,
        remove_unused_columns=False,
    )
    
    # 数据格式化函数
    def formatting_func(example):
        return formatting_prompts_func(example, tokenizer, args.max_seq_length)
    
    # 创建训练器
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        args=training_args,
        formatting_func=formatting_func,
    )
    
    # 开始训练
    logger.info("=" * 60)
    logger.info("开始训练")
    logger.info("=" * 60)
    
    train_result = trainer.train()
    
    # 保存模型
    logger.info(f"保存 LoRA 权重到: {output_dir}")
    trainer.save_model(str(output_dir))
    
    # 保存 tokenizer
    tokenizer.save_pretrained(str(output_dir))
    
    # 保存训练元数据
    meta = {
        "experiment_id": "s1-poc-e01",
        "model_name": args.model_name,
        "lora_config": {
            "r": args.lora_r,
            "alpha": args.lora_alpha,
            "dropout": args.lora_dropout,
        },
        "training_args": {
            "num_epochs": args.num_epochs,
            "batch_size": args.batch_size,
            "gradient_accumulation_steps": args.gradient_accumulation_steps,
            "learning_rate": args.learning_rate,
            "warmup_steps": args.warmup_steps,
            "seed": args.seed,
        },
        "train_result": {
            "final_loss": train_result.training_loss,
            "train_runtime": train_result.metrics.get("train_runtime", 0),
        },
        "output_dir": str(output_dir),
    }
    
    with open(output_dir / "training_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    
    logger.info("=" * 60)
    logger.info("训练完成!")
    logger.info(f"最终 loss: {train_result.training_loss:.4f}")
    logger.info(f"训练时间: {train_result.metrics.get('train_runtime', 0):.2f} 秒")
    logger.info("=" * 60)
    
    return train_result


if __name__ == "__main__":
    main()
