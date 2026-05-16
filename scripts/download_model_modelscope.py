#!/usr/bin/env python3
"""从 ModelScope 下载模型（国内高速），供 train_poc 使用本地路径加载。"""

import argparse
import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL_ID = "google/gemma-4-E2B-it"
DEFAULT_CACHE_DIR = REPO_ROOT / "model_cache"


def main() -> None:
    parser = argparse.ArgumentParser(description="从 ModelScope 下载基座模型")
    parser.add_argument(
        "--model_id",
        type=str,
        default=os.environ.get("MS_MODEL_ID", DEFAULT_MODEL_ID),
        help=f"ModelScope 模型 ID（默认 {DEFAULT_MODEL_ID}）",
    )
    parser.add_argument(
        "--cache_dir",
        type=str,
        default=os.environ.get("MODEL_CACHE_DIR", str(DEFAULT_CACHE_DIR)),
        help="下载缓存目录（默认 model_cache/）",
    )
    args = parser.parse_args()

    try:
        from modelscope import snapshot_download
    except ImportError:
        raise SystemExit(
            "请先安装 modelscope: pip install modelscope -i https://pypi.tuna.tsinghua.edu.cn/simple"
        )

    cache_dir = Path(args.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    print(f"从 ModelScope 下载: {args.model_id}")
    print(f"缓存目录: {cache_dir.resolve()}")
    print("（约 10GB，国内网络通常比 Hugging Face 直连快很多）\n")

    model_dir = snapshot_download(args.model_id, cache_dir=str(cache_dir))

    print(f"\n✓ 下载完成")
    print(f"本地路径: {model_dir}")
    print(f"\n训练时指定本地路径，例如:")
    print(f"  python scripts/train_poc.py --model_name {model_dir} ...")


if __name__ == "__main__":
    main()
