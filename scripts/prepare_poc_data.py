#!/usr/bin/env python3
"""
准备 Sprint 1 Week 2 PoC 数据子集 (1k 条)

配比：
- brainstorm_en: 400 条
- brainstorm_cn: 400 条  
- general: 200 条
- 合计: 1000 条

用法：
    cd /path/to/repo
    python scripts/prepare_poc_data.py

输出：
    data/poc_v1.0_1k.jsonl - PoC 训练数据
    data/poc_v1.0_1k_meta.json - 元数据
"""

import json
import random
from pathlib import Path
from typing import List, Dict, Any


def load_jsonl(filepath: Path) -> List[Dict[str, Any]]:
    """加载 jsonl 文件"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))
    return data


def convert_sharegpt_format(item: Dict, use_zh: bool = False) -> Dict[str, Any]:
    """
    将 ShareGPT 格式转换为统一训练格式
    
    输入格式:
        {
            "id": "...",
            "conversations": [{"from": "human/gpt", "value": "..."}]
        }
    或中文格式:
        {
            "id": "...",
            "conversations_zh": [...],
            "conversations_en": [...]
        }
    
    输出格式:
        {
            "id": "...",
            "messages": [{"role": "user/assistant", "content": "..."}]
        }
    """
    result = {"id": item.get("id", "unknown")}
    
    if use_zh and "conversations_zh" in item:
        conversations = item["conversations_zh"]
    elif "conversations" in item:
        conversations = item["conversations"]
    else:
        conversations = []
    
    messages = []
    for conv in conversations:
        role = "user" if conv.get("from") == "human" else "assistant"
        content = conv.get("value", "")
        messages.append({"role": role, "content": content})
    
    result["messages"] = messages
    return result


def convert_alpaca_format(item: Dict) -> Dict[str, Any]:
    """
    将 Alpaca 格式转换为统一训练格式
    
    输入格式:
        {
            "id": "...",
            "messages": [{"role": "user/assistant", "content": "..."}]
        }
    
    输出格式相同，直接返回
    """
    return {
        "id": item.get("id", "unknown"),
        "messages": item.get("messages", [])
    }


def sample_data(data: List[Dict], n: int, seed: int = 42) -> List[Dict]:
    """随机抽样 n 条数据"""
    if n >= len(data):
        return data
    
    rng = random.Random(seed)
    return rng.sample(data, n)


def main():
    """主函数"""
    # 配置
    SEED = 42
    random.seed(SEED)
    
    # 数据源配置
    CONFIG = {
        "brainstorm_en": {
            "path": Path("data/raw/brainstorm_vicuna_10k/train.jsonl"),
            "count": 400,
            "converter": lambda x: convert_sharegpt_format(x, use_zh=False),
            "source": "brainstorm_vicuna_10k_en"
        },
        "brainstorm_cn": {
            "path": Path("data/processed/brainstorm_vicuna_10k_zh.jsonl"),
            "count": 400,
            "converter": lambda x: convert_sharegpt_format(x, use_zh=True),
            "source": "brainstorm_vicuna_10k_zh"
        },
        "general": {
            "path": Path("data/raw/general_mixed/general_mixed_train.jsonl"),
            "count": 200,
            "converter": convert_alpaca_format,
            "source": "general_mixed"
        }
    }
    
    # 输出路径
    output_dir = Path("data")
    output_file = output_dir / "poc_v1.0_1k.jsonl"
    meta_file = output_dir / "poc_v1.0_1k_meta.json"
    
    print("=" * 60)
    print("Sprint 1 Week 2 PoC 数据准备")
    print("=" * 60)
    
    all_samples = []
    meta_info = {
        "version": "v1.0-poc",
        "total_samples": 0,
        "seed": SEED,
        "sources": {},
        "created_at": "2026-05-17"
    }
    
    # 处理每个数据源
    for name, config in CONFIG.items():
        print(f"\n处理: {name}")
        print(f"  源文件: {config['path']}")
        
        if not config["path"].exists():
            print(f"  ⚠️  文件不存在，跳过")
            continue
        
        # 加载数据
        data = load_jsonl(config["path"])
        print(f"  总条数: {len(data)}")
        
        # 抽样
        n_samples = min(config["count"], len(data))
        samples = sample_data(data, n_samples, seed=SEED)
        print(f"  抽样数: {len(samples)}")
        
        # 转换格式
        converted = [config["converter"](s) for s in samples]
        
        # 添加来源标记
        for c in converted:
            c["source"] = config["source"]
        
        all_samples.extend(converted)
        
        # 记录元数据
        meta_info["sources"][name] = {
            "file": str(config["path"]),
            "total": len(data),
            "sampled": len(samples)
        }
    
    # 打乱顺序
    random.shuffle(all_samples)
    
    # 更新元数据
    meta_info["total_samples"] = len(all_samples)
    
    # 保存数据文件
    print(f"\n保存数据文件: {output_file}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for item in all_samples:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
    
    # 保存元数据
    print(f"保存元数据: {meta_file}")
    with open(meta_file, 'w', encoding='utf-8') as f:
        json.dump(meta_info, f, indent=2, ensure_ascii=False)
    
    # 输出统计
    print("\n" + "=" * 60)
    print("完成！")
    print("=" * 60)
    print(f"总样本数: {len(all_samples)}")
    print(f"数据文件: {output_file}")
    print(f"元数据文件: {meta_file}")
    print("\n数据配比:")
    for name, info in meta_info["sources"].items():
        print(f"  - {name}: {info['sampled']} 条")
    
    # 显示前 3 条样本
    print("\n前 3 条样本预览:")
    for i, sample in enumerate(all_samples[:3]):
        print(f"\n[{i+1}] ID: {sample['id']}, Source: {sample['source']}")
        print(f"    Messages: {len(sample['messages'])} turns")
        for j, msg in enumerate(sample['messages'][:2]):  # 只显示前 2 轮
            content = msg['content'][:50] + "..." if len(msg['content']) > 50 else msg['content']
            print(f"      {msg['role']}: {content}")


if __name__ == "__main__":
    main()
