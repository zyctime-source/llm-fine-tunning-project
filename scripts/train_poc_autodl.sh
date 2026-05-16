#!/bin/bash
# AutoDL 快速启动脚本
# 用法: bash train_poc_autodl.sh

set -e  # 遇到错误立即退出

echo "=========================================="
echo "Sprint 1 Week 2 PoC 训练 - AutoDL"
echo "=========================================="

# 检查是否在正确的目录
if [ ! -f "requirements-train.txt" ]; then
    echo "错误: 请在仓库根目录运行此脚本"
    exit 1
fi

# 加载环境变量（HF_TOKEN 等）
if [ -f ".env" ]; then
    echo ""
    echo "加载环境变量 (.env)..."
    set -a
    source .env
    set +a
    echo "✓ 环境变量已加载"
    if [ -n "$HF_TOKEN" ]; then
        echo "  HF_TOKEN: 已设置"
    fi
    if [ -n "$HF_ENDPOINT" ]; then
        echo "  HF_ENDPOINT: $HF_ENDPOINT"
    fi
else
    echo "⚠️ 警告: 未找到 .env 文件，可能需要手动设置 HF_TOKEN"
fi

# 检查 GPU
if ! command -v nvidia-smi &> /dev/null; then
    echo "错误: 未检测到 nvidia-smi，请确认 GPU 环境"
    exit 1
fi

echo ""
echo "GPU 信息:"
nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader

echo ""
echo "CUDA 版本:"
nvcc --version 2>/dev/null || echo "nvcc 未找到，使用 PyTorch 内置 CUDA"

# 创建/激活虚拟环境（如果不存在）
VENV_NAME="venv-train"

if [ ! -d "$VENV_NAME" ]; then
    echo ""
    echo "创建虚拟环境: $VENV_NAME"
    python3 -m venv "$VENV_NAME"
fi

echo ""
echo "激活虚拟环境..."
source "$VENV_NAME/bin/activate"

# 升级 pip
echo ""
echo "升级 pip..."
pip install --upgrade pip

# 安装依赖
echo ""
echo "安装训练依赖..."
pip install -r requirements-train.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 验证安装
echo ""
echo "验证安装:"
python3 -c "
import torch
import transformers
import peft
import trl

print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'CUDA version: {torch.version.cuda}')
    print(f'GPU: {torch.cuda.get_device_name(0)}')
print(f'Transformers: {transformers.__version__}')
print(f'PEFT: {peft.__version__}')
print(f'TRL: {trl.__version__}')
"

# 检查数据文件
echo ""
echo "检查数据文件..."
if [ ! -f "data/poc_v1.0_1k.jsonl" ]; then
    echo "错误: data/poc_v1.0_1k.jsonl 不存在"
    echo "请先运行: python scripts/prepare_poc_data.py"
    exit 1
fi
echo "✓ 数据文件已准备好"

# 创建输出目录
mkdir -p experiment/s1-poc-e01/results

echo ""
echo "=========================================="
echo "开始训练"
echo "=========================================="

# 运行训练（使用 4-bit 量化节省显存，5090 24GB 应该足够）
echo ""
echo "启动训练..."
python3 scripts/train_poc.py \
    --data_path data/poc_v1.0_1k.jsonl \
    --output_dir experiment/s1-poc-e01 \
    --model_name google/gemma-4-2b-it \
    --load_in_4bit \
    --lora_r 8 \
    --lora_alpha 16 \
    --num_epochs 1 \
    --batch_size 1 \
    --gradient_accumulation_steps 4 \
    --learning_rate 2e-4 \
    --warmup_steps 50 \
    --max_seq_length 2048 \
    --seed 42

echo ""
echo "=========================================="
echo "训练完成!"
echo "=========================================="
echo "输出目录: experiment/s1-poc-e01/"
echo "LoRA 权重: experiment/s1-poc-e01/adapter_model.safetensors"
echo "训练日志: training.log"
