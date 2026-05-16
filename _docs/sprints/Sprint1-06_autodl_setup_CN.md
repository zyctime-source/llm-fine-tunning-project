# AutoDL 环境设置指南（RTX 5090）

> **用途**：在 AutoDL 云端 GPU 实例上配置训练环境  
> **适用显卡**：RTX 5090 / 4090 / A100 / H100 等 NVIDIA GPU  
> **日期**：2026-05-17

---

## 1. 创建 AutoDL 实例

### 1.1 选择镜像

登录 [AutoDL](https://www.autodl.com/) 控制台：

1. 选择 **"算法镜像"** 或 **"基础镜像"**
   - **推荐**：`PyTorch 2.7.0 + Python 3.11 + CUDA 12.4`
   - 或者选择 `PyTorch` 类别下的最新版本

2. **GPU 选择**：
   - RTX 5090 (32GB) - 推荐用于本实验
   - RTX 4090 (24GB) - 备选
   - A100 (40GB/80GB) - 预算充足时

### 1.2 开机后检查环境

```bash
# 检查 GPU
nvidia-smi

# 预期输出示例（AutoDL RTX 5090）：
# +-----------------------------------------------------------------------------------------+
# | NVIDIA-SMI 580.105.08             Driver Version: 580.105.08     CUDA Version: 13.0     |
# +-----------------------------------------+------------------------+----------------------+
# | GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
# |                                         |                        |               MIG M. |
# |=========================================+========================+======================|
# |   0  NVIDIA GeForce RTX 5090        On  |   00000000:A8:00.0 Off |                  N/A |
# | 41%   31C    P8             17W /  575W |       0MiB /  32607MiB |      0%      Default |
# |                                         |                        |                  N/A |
# +-----------------------------------------+------------------------+----------------------+
```

---

## 2. 快速启动（推荐）

### 2.1 上传代码到 AutoDL

```bash
# 在 AutoDL 实例内
git clone https://github.com/zyctime-source/llm-fine-tunning-project.git
cd llm-fine-tunning-project
```

### 2.2 一键启动训练

```bash
# 进入项目目录
cd /root/autodl-tmp/llm-fine-tunning-project

# 如果使用 ModelScope（推荐国内环境）
export USE_MODELSCOPE=1

# 运行自动启动脚本
bash scripts/train_poc_autodl.sh
```

脚本会自动：
1. 加载 `.env` 环境变量（HF_TOKEN、USE_MODELSCOPE 等）
2. 验证 GPU 可用性
3. 创建/激活 Python 虚拟环境
4. 安装训练依赖（PyTorch、Transformers、TRL、PEFT、ModelScope）
5. 验证安装
6. 检查数据文件
7. 启动训练

#### `train_poc_autodl.sh` 脚本详解

| 阶段 | 功能 | 说明 |
|------|------|------|
| **环境检查** | 检查目录、加载 `.env` | 确保在项目根目录，加载 HF_TOKEN 或 USE_MODELSCOPE |
| **GPU 验证** | `nvidia-smi` | 显示 GPU 型号、驱动版本、CUDA 版本、显存 |
| **虚拟环境** | `python3 -m venv venv-train` | 创建隔离环境，避免污染系统 Python |
| **依赖安装** | `pip install -r requirements-train.txt` | 从清华镜像安装，加速下载 |
| **安装验证** | 导入 torch、transformers 等 | 确认 GPU 可用、版本正确 |
| **数据检查** | 检查 `data/poc_v1.0_1k.jsonl` | 确保 PoC 数据已准备 |
| **训练启动** | 运行 `train_poc.py` | 使用 4-bit 量化、LoRA rank=8、epoch=1 |

**脚本特点：**
- ✅ **幂等性**：多次运行不会重复创建环境
- ✅ **错误处理**：使用 `set -e`，出错立即退出
- ✅ **国内加速**：使用清华 PyPI 镜像
- ✅ **自动适配**：支持 HF_TOKEN 或 USE_MODELSCOPE 两种认证方式

---

### 2.3 脚本执行流程详解

当你运行 `bash scripts/train_poc_autodl.sh` 时，实际发生了什么：

```
┌─────────────────────────────────────────────────────────────┐
│  1. 初始化                                                   │
│     ├── 显示欢迎信息                                          │
│     ├── 检查是否在正确目录 (存在 requirements-train.txt)      │
│     └── 加载 .env 文件中的环境变量                             │
│         ├── HF_TOKEN (Hugging Face 认证)                     │
│         ├── HF_ENDPOINT (镜像地址)                           │
│         └── USE_MODELSCOPE (使用魔搭下载)                     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  2. GPU 环境检查                                              │
│     ├── 检查 nvidia-smi 可用                                  │
│     └── 显示 GPU 信息：                                        │
│         ├── GPU 型号 (如 RTX 5090)                           │
│         ├── 驱动版本 (如 580.105.08)                         │
│         ├── CUDA 版本 (如 13.0)                              │
│         └── 显存容量 (如 32607MiB / 32GB)                    │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Python 虚拟环境                                           │
│     ├── 检查 venv-train 目录是否存在                           │
│     │   ├── 不存在 → 创建: python3 -m venv venv-train        │
│     │   └── 存在 → 复用现有环境                               │
│     └── 激活虚拟环境: source venv-train/bin/activate          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  4. 安装依赖                                                  │
│     ├── 升级 pip: pip install --upgrade pip                   │
│     └── 安装 requirements-train.txt 中的包：                 │
│         ├── torch>=2.6.0 (PyTorch)                           │
│         ├── transformers>=4.49.0 (模型加载)                   │
│         ├── peft>=0.14.0 (LoRA)                             │
│         ├── trl>=0.15.0 (SFTTrainer)                        │
│         └── modelscope>=1.20.0 (国内下载)                    │
│     使用清华镜像: -i https://pypi.tuna.tsinghua.edu.cn/simple │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  5. 验证安装                                                  │
│     ├── import torch → 检查 CUDA 可用                        │
│     ├── import transformers                                  │
│     ├── import peft                                          │
│     └── import trl                                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  6. 数据检查                                                  │
│     └── 检查 data/poc_v1.0_1k.jsonl 是否存在                  │
│         └── 不存在 → 报错退出                                 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  7. 启动训练                                                  │
│     └── python3 scripts/train_poc.py                         │
│         ├── 参数 --data_path data/poc_v1.0_1k.jsonl          │
│         ├── 参数 --model_name google/gemma-4-2b-it         │
│         ├── 参数 --load_in_4bit (4-bit 量化)                 │
│         ├── 参数 --lora_r 8 --lora_alpha 16                  │
│         ├── 参数 --num_epochs 1                              │
│         └── 参数 --batch_size 1                              │
└─────────────────────────────────────────────────────────────┘
```

**预期输出：**

```bash
==========================================
Sprint 1 Week 2 PoC 训练 - AutoDL
==========================================

加载环境变量 (.env)...
✓ 环境变量已加载
  USE_MODELSCOPE: 1 (将使用魔搭下载)

GPU 信息:
NVIDIA GeForce RTX 5090, 580.105.08, 32607 MiB

激活虚拟环境...
安装训练依赖...
... (安装过程)

✓ 数据文件已准备好

==========================================
开始训练
==========================================
2026-05-16 22:XX:XX,XXX - INFO - 加载数据: data/poc_v1.0_1k.jsonl
2026-05-16 22:XX:XX,XXX - INFO - 加载了 1000 条样本
2026-05-16 22:XX:XX,XXX - INFO - 从 ModelScope 加载: google/gemma-4-2b-it
... (训练过程)
```

---

## 3. 手动安装（备选）

如果自动脚本失败，可以手动执行：

### 3.1 创建虚拟环境

```bash
cd /root/autodl-tmp/llm-fine-tunning-project

# 创建虚拟环境
python3 -m venv venv-train

# 激活
source venv-train/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 3.2 安装依赖

```bash
# 使用清华镜像加速
pip install -r requirements-train.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3.3 验证安装

```bash
python3 -c "
import torch
print(f'PyTorch: {torch.__version__}')
print(f'CUDA available: {torch.cuda.is_available()}')
print(f'GPU: {torch.cuda.get_device_name(0)}')
"
```

预期输出：
```
PyTorch: 2.6.0+cu124
CUDA available: True
GPU: NVIDIA GeForce RTX 5090
```

### 3.4 运行训练

**使用 ModelScope（推荐，国内更快）：**

```bash
# 设置使用 ModelScope
export USE_MODELSCOPE=1

# 运行训练
python3 scripts/train_poc.py \
    --data_path data/poc_v1.0_1k.jsonl \
    --output_dir experiment/s1-poc-e01 \
    --model_name google/gemma-4-2b-it \
    --load_in_4bit \
    --num_epochs 1 \
    --batch_size 1 \
    --learning_rate 2e-4
```

**使用 Hugging Face（需要 Token）：**

```bash
# 基础训练（4-bit 量化，节省显存）
python3 scripts/train_poc.py \
    --data_path data/poc_v1.0_1k.jsonl \
    --output_dir experiment/s1-poc-e01 \
    --model_name google/gemma-4-E2B-it \
    --load_in_4bit \
    --num_epochs 1 \
    --batch_size 1 \
    --learning_rate 2e-4
```

---

## 4. 训练参数调整

### 4.1 根据显存调整

| GPU 显存 | 推荐配置 | 命令 |
|---------|---------|------|
| 24GB (4090) | 4-bit 量化, rank=8 | `--load_in_4bit --lora_r 8` |
| 32GB (5090) | 4-bit 量化或 bf16, rank=8-16 | `--load_in_4bit --lora_r 8` 或 `--lora_r 16` |
| 40GB (A100) | 4-bit 量化, rank=16 | `--load_in_4bit --lora_r 16` |
| 80GB (A100/H100) | bf16 全精度, rank=16 | `--lora_r 16` |

### 4.2 快速测试（用于调试）

```bash
# 仅用 50 条数据快速验证流程
python3 scripts/train_poc.py \
    --data_path data/poc_voc_v1.0_1k.jsonl \
    --max_samples 50 \
    --output_dir experiment/s1-poc-e01-test \
    --num_epochs 1 \
    --load_in_4bit
```

---

## 5. 常见问题

### Q1: CUDA out of memory

**解决**：启用 4-bit 量化或减小 batch_size / max_seq_length

```bash
python3 scripts/train_poc.py --load_in_4bit --batch_size 1 --max_seq_length 1024
```

### Q2: 下载模型很慢/失败

**解决**：使用 ModelScope（魔搭）或 HF 镜像

**方法 1：使用 ModelScope（推荐，国内更快）**

```bash
# 安装 modelscope
pip install modelscope

# 设置环境变量使用 modelscope
export USE_MODELSCOPE=1

# 训练脚本会自动使用 modelscope 下载
python3 scripts/train_poc.py ...
```

**方法 2：使用 HF 镜像**

```bash
# 设置环境变量
export HF_ENDPOINT=https://hf-mirror.com
export HF_TOKEN=your_token_here  # 如果需要

# 然后运行训练
python3 scripts/train_poc.py ...
```

### Q3: 训练后找不到 LoRA 权重

**检查**：
```bash
ls -la experiment/s1-poc-e01/
# 应该包含：
# - adapter_config.json
# - adapter_model.safetensors
# - training_meta.json
```

### Q4: 如何监控训练进度

**方法 1**：查看日志
```bash
tail -f training.log
```

**方法 2**：使用 wandb（推荐）
1. 注册 [wandb.ai](https://wandb.ai)
2. 登录：`wandb login`
3. 训练时添加 `--use_wandb` 参数

---

## 6. 训练后操作

### 6.1 下载结果到本地

```bash
# 在本地执行
scp -P <端口> -r root@<主机>:/root/autodl-tmp/llm-fine-tunning-project/experiment/s1-poc-e01 ./
```

### 6.2 在本地评估

将 `experiment/s1-poc-e01/` 目录下载到本地后：

```bash
# 切换到本地仓库
# 更新 experiment/s1-poc-e01/META.json 状态
# 运行 Layer 2 评估（见 Week 2 D3-D4 任务）
```

---

## 7. 成本估算

### AutoDL RTX 5090 价格参考（2026-05）

| 配置 | 显存 | 价格/小时 | 预估训练时间 | 预估成本 |
|------|------|----------|-------------|---------|
| RTX 5090 (32GB) | 32GB | ~2-3元 | 30-60分钟 | 1-3元 |
| RTX 4090 (24GB) | 24GB | ~1.5-2元 | 30-60分钟 | 1-2元 |

> 实际成本取决于训练参数（epochs、量化方式等）

---

## 8. 相关文档

| 文档 | 用途 |
|------|------|
| [Sprint1-05_week2_poc_plan_CN.md](Sprint1-05_week2_poc_plan_CN.md) | Week 2 完整规划 |
| [experiment/s1-poc-e01/README.md](../../experiment/s1-poc-e01/README.md) | 实验详情 |
| [requirements-train.txt](../../requirements-train.txt) | 依赖列表 |
| [scripts/train_poc.py](../../scripts/train_poc.py) | 训练脚本 |

---

## 9. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-17 | 初版：AutoDL RTX 5090 环境设置指南 |
