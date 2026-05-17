# 用 AutoDL 租赁 GPU 进行大模型 Gemma-4-E2B-IT 微调

> **用途**：在 AutoDL 云端 GPU 实例上配置训练环境  
> **适用显卡**：RTX 5090 / 4090 / A100 / H100 等 NVIDIA GPU  
> **日期**：2026-05-17

---

## 0. 背景

### 0.1 项目背景

本项目尝试用 **Vibe Coding** 在 3～4 个月内从零推进一个端侧大模型微调项目，最终落地为一款安卓端的 **AI 思维助手** App。

**痛点**：灵感来时随手记，但传统笔记只能「存」不能「想」——不会追问、不会发散、更不会帮你收敛成可行动的洞察。

**方案**：让「随手记的一句话」经过端侧大模型**追问-发散-收敛**，最终收成结构化的「灵感卡片」。选型上用 **Gemma-4-E2B-IT**（4B 级）做基座，**LoRA 微调**对齐「头脑风暴」节奏，再量化塞进手机，兼顾隐私与成本。

> 详细任务总览见 [Sprint1-00_tasks_intro_CN.md](Sprint1-00_tasks_intro_CN.md)

### 0.2 本文定位：Week 2 PoC 训练环境

**Sprint 1 进度**：
- Week 1 已完成：数据冻结（v1.0 配方）+ 基线评测（Layer 2 500条）
- **Week 2 目标**：PoC 快速闭环——用 1k 条数据完成一次端到端 LoRA 微调，验证「数据+训练+评估」链路可跑通

**PoC 的核心目的**（不是产出完美模型）：
1. 验证训练脚本能正常跑通（不崩溃、不 OOM、loss 正常下降）
2. 验证 LoRA 权重可导出、可加载、可推理
3. 验证微调后的模型能在 Layer 2 上产出可评估的结果
4. 为 Week 3 Stage 1 保守训练积累配置经验

> 详细 PoC 规划见 [Sprint1-05_week2_poc_plan_CN.md](Sprint1-05_week2_poc_plan_CN.md)

---

## 1. 创建 AutoDL 实例

### 1.1 autodl 配置

登录 [autodl](https://www.autodl.com/login) 后，账户里面冲一点钱，然后进入 `算力市场`，选择适合项目的GPU。

<img src="./img/autodl_1.png" style="margin-left: 0px" width=800px>

创建虚拟机后，可以在 `容器实例` 中看到类似下面截图：

<img src="./img/autodl_2.png" style="margin-left: 0px" width=800px>

需要注意，虚拟机不用的时候需要关闭，否则会一直扣钱。

我们可以点击 `JupyterLab` 打开后端，进行和我们本地代码编写一样的操作：

<img src="./img/autodl_3.png" style="margin-left: 0px" width=600px>

如何在 VSCode 中进行 SSH 远程连接：

VSCode中提供了 `Remote-SSH` 插件，可以让我们连接远程服务器进行操作。

首先，我们需要在 VSCode 的扩展中安装 `Remote-SSH` 插件。然后，我们在 VScode 左边栏 `Remote Explorer` 中就可以找到 `SSH` 栏。我们点击 `+`，输入 SSH 登录指令（复制AutoDL容器实例中的ssh登录指令，并在VSCode“输入SSH连接命令”窗口中输入ssh并按Enter）：

<img src="./img/autodl_7.png" style="margin-left: 0px" width=600px>

在弹出的窗口中点击“C:\User\[UserName]\.sshconfig”文件，然后在右下角弹出的窗口中选择`打开配置` (`Open Config`)。编辑config文件：host后为主机名，可以自定义；HostName后为主机ip；Port后为端口号；User为用户名。

<img src="./img/autodl_8.png" style="margin-left: 0px" width=600px>

如果我们对于Port没有特定要求的话，也可以这里面的参数都不做修改。

接下来，我们在 VScode 左边栏 `Remote Explorer` 找到新建的 SSH 远程接口，点击 `Connect in Current Window`：

<img src="./img/autodl_9.png" style="margin-left: 0px" width=600px>

会跳出一个新的页面。我们需要输入 AutoDL 容器实例中的ssh密码，然后 Enter：

<img src="./img/autodl_10.png" style="margin-left: 0px" width=600px>

- [reference](https://zhuanlan.zhihu.com/p/688746108#:~:text=VSCode%E4%B8%AD%E6%8F%90%E4%BE%9B%E4%BA%86%20Remote-SSH%20%E6%8F%92%E4%BB%B6%EF%BC%8C%E5%8F%AF%E4%BB%A5%E8%AE%A9%E6%88%91%E4%BB%AC%E8%BF%9E%E6%8E%A5%E8%BF%9C%E7%A8%8B%E6%9C%8D%E5%8A%A1%E5%99%A8%E8%BF%9B%E8%A1%8C%E6%93%8D%E4%BD%9C%E3%80%82%201.%20%E5%AE%89%E8%A3%85Remote-SSH%E6%8F%92%E4%BB%B6%20%E6%89%93%E5%BC%80%E6%89%A9%E5%B1%95%EF%BC%8C%E6%90%9C%E7%B4%A2Remote-SSH%EF%BC%8C%E5%B9%B6%E7%82%B9%E5%87%BB%E5%AE%89%E8%A3%85%E3%80%82%202.,%E9%85%8D%E7%BD%AE%20SSH%20config%E6%96%87%E4%BB%B6%20%EF%BC%881%EF%BC%89%E6%96%B0%E5%BB%BA%E8%BF%9C%E7%A8%8B%20%EF%BC%882%EF%BC%89%E5%A4%8D%E5%88%B6%20AutoDL%20%E5%AE%B9%E5%99%A8%E5%AE%9E%E4%BE%8B%E4%B8%AD%E7%9A%84ssh%E7%99%BB%E5%BD%95%E6%8C%87%E4%BB%A4%EF%BC%8C%E5%B9%B6%E5%9C%A8VSCode%E2%80%9C%E8%BE%93%E5%85%A5SSH%E8%BF%9E%E6%8E%A5%E5%91%BD%E4%BB%A4%E2%80%9D%E7%AA%97%E5%8F%A3%E4%B8%AD%E8%BE%93%E5%85%A5ssh%E5%B9%B6%E6%8C%89Enter%E3%80%82)

另，如何在autodl开启学术加速：`source /etc/network_turbo`。

### 1.2 开机后检查环境

1. 我们选择 **"算法镜像"** 或 **"基础镜像"**：`PyTorch 2.7.0 + Python 3.11 + CUDA 12.4`

2. **GPU 选择**：- RTX 5090 (32GB)

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
```

相关代码：

```sh
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
    if [ -n "$USE_MODELSCOPE" ]; then
        echo "  USE_MODELSCOPE: $USE_MODELSCOPE (将使用魔搭下载)"
    fi
else
    echo "⚠️ 警告: 未找到 .env 文件，可能需要手动设置环境变量"
    echo "  选项 1: export USE_MODELSCOPE=1 (使用 ModelScope 魔搭)"
    echo "  选项 2: export HF_TOKEN=your_token (使用 Hugging Face)"
fi
```

GPU 环境检查: 

```                              
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
```           

相关代码：

```sh
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
```

Python 虚拟环境: 

```           
┌─────────────────────────────────────────────────────────────┐
│  3. Python 虚拟环境                                           │
│     ├── 检查 venv-train 目录是否存在                           │
│     │   ├── 不存在 → 创建: python3 -m venv venv-train        │
│     │   └── 存在 → 复用现有环境                               │
│     └── 激活虚拟环境: source venv-train/bin/activate          │
└─────────────────────────────────────────────────────────────┘
                              ↓
```   

相关代码：

```sh
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
```

安装依赖：

```   
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
```   

```sh  
# 升级 pip
echo ""
echo "升级 pip..."
pip install --upgrade pip

# 安装依赖
echo ""
echo "安装训练依赖..."
pip install -r requirements-train.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
# 4-bit 量化依赖（requirements-train.txt 已包含，此处确保已装）
pip show bitsandbytes >/dev/null 2>&1 || pip install bitsandbytes -i https://pypi.tuna.tsinghua.edu.cn/simple
```  

数据检查和处理：

```   
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
```   

相关代码：

```sh
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
```   

这里需要简单解释一下 `prepare_poc_data.py` 的逻辑：

该脚本负责从 v1.0 数据配方中抽取 **1,000 条** PoC 子集，配比与数据来源如下：

| 数据源 | 条数 | 来源文件 | 格式转换 |
|--------|------|----------|----------|
| brainstorm_en | 400 | `data/raw/brainstorm_vicuna_10k/train.jsonl` | ShareGPT → messages |
| brainstorm_cn | 400 | `data/processed/brainstorm_vicuna_10k_zh.jsonl` | ShareGPT (中文) → messages |
| general | 200 | `data/raw/general_mixed/general_mixed_train.jsonl` | Alpaca/messages 格式保持 |
| **合计** | **1,000** | — | — |

**关键处理步骤：**

1. **格式统一**：将 ShareGPT 的 `conversations`（`from: human/gpt`）转换为标准 `messages` 格式（`role: user/assistant`），中文优先取 `conversations_zh` 字段
2. **随机抽样**：固定 `seed=42`，从各源中无放回抽取指定条数
3. **来源标记**：每条样本添加 `source` 字段（如 `brainstorm_vicuna_10k_zh`），便于后续追溯
4. **打乱混合**：合并后整体 `random.shuffle`，避免训练时数据分布偏斜

**输出产物：**
- `data/poc_v1.0_1k.jsonl` — 训练数据（1000 行，每行一条对话样本）
- `data/poc_v1.0_1k_meta.json` — 元数据（记录各源抽样数、seed、时间戳）

```   
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

（相关代码参见 `Sprint1-07_train_poc_explained_CN.md`）

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
