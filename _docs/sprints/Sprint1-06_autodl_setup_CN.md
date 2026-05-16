# AutoDL 环境设置指南（RTX 5090）

> **用途**：在 AutoDL 云端 GPU 实例上配置训练环境  
> **适用显卡**：RTX 5090 / 4090 / A100 / H100 等 NVIDIA GPU  
> **日期**：2026-05-17

---

## 1. 创建 AutoDL 实例

### 1.1 选择镜像

登录 [AutoDL](https://www.autodl.com/) 控制台：

1. 选择 **"算法镜像"** 或 **"基础镜像"**
   - **推荐**：`PyTorch 2.6.0 + Python 3.11 + CUDA 12.4`
   - 或者选择 `PyTorch` 类别下的最新版本

2. **GPU 选择**：
   - RTX 5090 (24GB) - 推荐用于本实验
   - RTX 4090 (24GB) - 备选
   - A100 (40GB/80GB) - 预算充足时

### 1.2 开机后检查环境

```bash
# SSH 登录实例
ssh -p <端口> root@<主机地址>

# 检查 GPU
nvidia-smi

# 预期输出示例：
# +-----------------------------------------------------------------------------------------+
# | NVIDIA-SMI 550.XX                 Driver Version: 550.XX     CUDA Version: 12.4          |
# |-----------------------------------------+------------------------+----------------------+
# | GPU  Name                 Persistence-M | Bus-Id          Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |           Memory-Usage | GPU-Util  Compute M. |
# |                                         |                        |               MIG M. |
# |=========================================+========================+======================|
# |   0  NVIDIA GeForce RTX 5090          Off |   00000000:01:00.0 Off |                  N/A |
# |  0%   30C    P8             20W /  450W |      1MiB /  24576MiB |      0%      Default |
# +-----------------------------------------+------------------------+----------------------+
```

---

## 2. 快速启动（推荐）

### 2.1 上传代码到 AutoDL

**方法一：使用 AutoDL 文件存储（推荐）**

```bash
# 在本地，使用 AutoDL 提供的 scp 命令上传
scp -P <端口> -r /path/to/llm-fine-tunning-project root@<主机>:/root/autodl-tmp/
```

**方法二：使用 GitHub**

```bash
# 在 AutoDL 实例内
ssh -p <端口> root@<主机>
cd /root/autodl-tmp
git clone https://github.com/zyctime-source/llm-fine-tunning-project.git
cd llm-fine-tunning-project
```

### 2.2 一键启动训练

```bash
# 进入项目目录
cd /root/autodl-tmp/llm-fine-tunning-project

# 运行自动启动脚本
bash scripts/train_poc_autodl.sh
```

脚本会自动：
1. 创建虚拟环境
2. 安装依赖
3. 验证 GPU
4. 开始训练

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

```bash
# 基础训练（4-bit 量化，节省显存）
python3 scripts/train_poc.py \
    --data_path data/poc_v1.0_1k.jsonl \
    --output_dir experiment/s1-poc-e01 \
    --model_name google/gemma-4-2b-it \
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
| 24GB (5090/4090) | 4-bit 量化, rank=8 | `--load_in_4bit --lora_r 8` |
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

**解决**：设置 HF 镜像

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

| 配置 | 价格/小时 | 预估训练时间 | 预估成本 |
|------|----------|-------------|---------|
| RTX 5090 (24GB) | ~2-3元 | 30-60分钟 | 1-3元 |

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
