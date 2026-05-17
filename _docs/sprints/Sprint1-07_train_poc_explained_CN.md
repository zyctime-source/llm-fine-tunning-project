# `train_poc.py` 脚本详解，LoRA Fine-tuning 原理与结果记录

> **目标**：深入理解 PoC 训练脚本的工作原理和 LoRA 微调配置  
> **适用读者**：希望理解代码逻辑和训练原理的用户  
> **日期**：2026-05-17

---

## 0. 背景

### 0.1 项目背景

本项目尝试用 **Vibe Coding** 在 3～4 个月内从零推进一个端侧大模型微调项目，最终落地为一款安卓端的 **AI 思维助手** App。

**痛点**：灵感来时随手记，但传统笔记只能「存」不能「想」——不会追问、不会发散、更不会帮你收敛成可行动的洞察。

**方案**：让「随手记的一句话」经过端侧大模型**追问-发散-收敛**，最终收成结构化的「灵感卡片」。选型上用 **Gemma-4-E2B-IT**（4B 级）做基座，**LoRA 微调**对齐「头脑风暴」节奏，再量化塞进手机，兼顾隐私与成本。

> 详细任务总览见 [Sprint1-00_tasks_intro_CN.md](Sprint1-00_tasks_intro_CN.md)

### 0.2 本文定位：Week 2 PoC 训练脚本原理

**Sprint 1 进度**：
- Week 1 已完成：数据冻结（v1.0 配方）+ 基线评测（Layer 2 500条）
- **Week 2 目标**：PoC 快速闭环——用 1k 条数据完成一次端到端 LoRA 微调，验证「数据+训练+评估」链路可跑通

**本文核心内容**：
1. **LoRA 原理**：为什么用 LoRA、数学原理、优势与权衡
2. **脚本详解**：`train_poc.py` 逐段代码解读
3. **配置说明**：每个超参数的选择理由（rank、lr、epoch 等）
4. **实际结果**：PoC 实验的真实训练记录（loss=1.93，时间=385秒）

> 配套环境搭建指南见 [Sprint1-06_autodl_setup_CN.md](Sprint1-06_autodl_setup_CN.md)  
> 详细 PoC 规划见 [Sprint1-05_week2_poc_plan_CN.md](Sprint1-05_week2_poc_plan_CN.md)

---

## 1. 整体架构概览

```
┌─────────────────────────────────────────────────────────────────┐
│                        train_poc.py                              │
├─────────────────────────────────────────────────────────────────┤
│  1. 数据加载 (load_poc_data)                                     │
│     └── 从 JSONL 读取 → 转换为 HuggingFace Dataset              │
├─────────────────────────────────────────────────────────────────┤
│  2. 模型准备 (setup_model_and_tokenizer)                         │
│     ├── 下载/加载 Gemma-4-2b-it                                │
│     ├── 4-bit 量化 (节省显存)                                   │
│     └── 准备 Tokenizer                                         │
├─────────────────────────────────────────────────────────────────┤
│  3. LoRA 配置 (setup_lora_config)                                │
│     └── 配置低秩适配器 (rank=8, alpha=16)                       │
├─────────────────────────────────────────────────────────────────┤
│  4. 训练执行 (SFTTrainer)                                       │
│     ├── 监督微调 (SFT)                                         │
│     ├── 反向传播优化                                          │
│     └── 保存 LoRA 权重                                         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. LoRA Fine-tuning 原理

### 2.1 什么是 LoRA？

**LoRA** (Low-Rank Adaptation) 是一种**参数高效微调** (Parameter-Efficient Fine-Tuning, PEFT) 方法。

#### 核心思想

不直接训练大模型的全部参数（40亿参数），而是训练少量的"适配器"参数：

```
传统微调: 修改全部 40亿 参数 → 需要巨大算力
LoRA 微调: 冻结 40亿 参数，只训练 0.1% ~ 1% 的低秩矩阵 → 高效
```

#### 数学原理

对于原始模型的某一层权重矩阵 $W_0$，LoRA 学习一个**低秩更新**：

$$W = W_0 + \Delta W = W_0 + BA$$

其中：
- $W_0$: 原始权重矩阵 (d×d)，**冻结不训练**
- $B$: 低秩矩阵 (d×r)，**可训练**
- $A$: 低秩矩阵 (r×d)，**可训练**
- $r$: rank（秩），通常 r << d（如 r=8, d=2048）

```
原始权重 W0: [2048 × 2048] = 4,194,304 参数 (冻结)
LoRA A:       [8 × 2048]    = 16,384 参数 (训练)
LoRA B:       [2048 × 8]    = 16,384 参数 (训练)
────────────────────────────────────────────
总训练参数:    32,768 (仅占原始 0.78%)
```

### 2.2 为什么用 LoRA？

| 优势 | 说明 |
|------|------|
| **节省显存** | 只加载优化器状态到少量参数，显存占用大幅降低 |
| **训练更快** | 反向传播只更新少量参数，计算量减少 |
| **权重更小** | LoRA 权重通常只有几十 MB，便于传输和部署 |
| **可组合** | 多个 LoRA 可以叠加到同一个基座模型 |

---

## 3. 脚本逐段详解

### 3.1 数据加载 (`load_poc_data`)

```python
def load_poc_data(data_path: str, max_samples: Optional[int] = None) -> Dataset:
    """
    加载 PoC 数据并转换为 HuggingFace Dataset 格式
    
    输入格式: {"id": str, "messages": [{"role": "user/assistant", "content": str}]}
    输出格式: Dataset 对象，每条包含 "messages" 字段
    """
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            messages = item.get('messages', [])
            if not messages:
                continue
            
            # 保留对话格式，后续由 formatting_func 处理
            formatted = {"messages": messages, "id": item.get("id")}
            data.append(formatted)
    
    return Dataset.from_list(data)
```

**数据流**：

```
poc_v1.0_1k.jsonl
    ↓
JSON 解析 (json.loads)
    ↓
提取 messages 对话列表
    ↓
Dataset.from_list() → HuggingFace Dataset 对象
    ↓
传入 SFTTrainer
```

**为什么用 `messages` 格式？**

现代 LLM（如 Gemma、Qwen、Llama）使用对话格式训练，每条样本是一个对话列表：

```json
{
  "messages": [
    {"role": "user", "content": "我想学习编程"},
    {"role": "assistant", "content": "好的！你想学习哪种编程语言？"},
    {"role": "user", "content": "Python"}
  ]
}
```

这比传统的 "input/output" 格式更灵活，支持多轮对话。

---

### 3.2 模型加载 (`setup_model_and_tokenizer`)

```python
def setup_model_and_tokenizer(
    model_name: str = "google/gemma-4-2b-it",
    load_in_4bit: bool = False,
    load_in_8bit: bool = False,
):
    # 加载 tokenizer（词表编码器）
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    # 加载模型
    model_kwargs = {
        "torch_dtype": torch.bfloat16,  # 使用 bfloat16 精度
        "device_map": "auto",            # 自动分配层到 GPU/CPU
    }
    
    if load_in_4bit:
        model_kwargs["load_in_4bit"] = True  # 4-bit 量化
    
    model = AutoModelForCausalLM.from_pretrained(model_name, **model_kwargs)
    return model, tokenizer
```

**关键概念解释**：

#### 3.2.1 Tokenizer（分词器）

```
原始文本: "你好，世界！"
    ↓ Tokenizer 编码
Token IDs: [52386, 117, 51461, 235265]
    ↓ 模型处理
预测下一个 Token
```

Tokenizer 的作用：
- 将**文本**转换为模型能理解的**数字序列**（Token IDs）
- 将模型的**数字输出**转换回**可读文本**

#### 3.2.2 4-bit 量化 (QLoRA)

```
原始 FP32: 32 bits × 40亿参数 = 16 GB (仅权重)
BF16 精度: 16 bits × 40亿参数 = 8 GB
4-bit 量化: 4 bits × 40亿参数 = 2 GB
────────────────────────────────────────
节省显存: 75% ~ 87.5%
```

4-bit 量化使用 **NF4** (Normal Float 4) 格式，在保持性能的同时大幅减少显存占用。

**为什么 RTX 5090 需要量化？**

- 原始 BF16: 8 GB (权重) + 8 GB (优化器状态) + 其他 = 约 20 GB
- 4-bit: 2 GB (权重) + 少量 (LoRA 优化器) = 约 6-8 GB
- RTX 5090 32GB 显存足够，但量化后更安全，可以增大 batch_size

**NF4 量化的潜在缺陷：**

| 问题 | 说明 | 影响 |
|------|------|------|
| **精度损失** | 4-bit 表示范围远低于 16-bit，参数精度压缩 | 可能导致模型「遗忘」部分基座能力，或微调后效果不如 BF16 |
| **梯度噪声** | 低精度权重引入更多梯度噪声 | 需要更小的学习率或更长的收敛时间 |
| **特定层敏感** | 某些层（如嵌入层、输出层）对精度更敏感 | 如果量化这些层，可能产生异常输出 |
| **推理兼容性** | 量化格式与部分推理框架不完全兼容 | 导出到端侧（手机）时可能需要额外转换 |

**PoC 阶段的权衡：**

当前选择 **4-bit 量化 + LoRA** 组合，是基于 PoC 目标的务实决策：

1. **首要目标**：验证「数据 → 训练 → 评估」完整链路可跑通，而非追求最优模型质量
2. **时间优先**：4-bit 量化让 RTX 5090 可以安全运行，避免 OOM 调试浪费时间
3. **后续调整**：Stage 1 保守训练（Week 3）会对比 4-bit vs BF16 的效果差异，届时根据 Layer 2 评估数据决定是否改用全精度

> **一句话总结**：PoC 阶段先让链路跑起来，量化带来的精度损失暂时接受；等验证完流程，再回头优化训练配置。

---

### 3.3 LoRA 配置 (`setup_lora_config`)

```python
def setup_lora_config(
    r: int = 8,                    # rank：低秩矩阵的秩
    lora_alpha: int = 16,         # alpha：缩放因子
    target_modules: Optional[list] = None,
    lora_dropout: float = 0.05,  # dropout：防止过拟合
):
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
    return lora_config
```

#### 3.3.1 关键参数详解

| 参数 | 值 | 含义 | 影响 |
|------|-----|------|------|
| **r** (rank) | 8 | 低秩矩阵的秩 | 越大表达能力越强，但训练参数越多 |
| **alpha** | 16 | 缩放因子 | 实际缩放 = alpha / r = 2，控制 LoRA 权重的影响强度 |
| **target_modules** | q/k/v/o_proj | 应用 LoRA 的层 | 注意力层的投影矩阵 |
| **dropout** | 0.05 | 随机丢弃率 | 防止过拟合，训练时随机丢弃 5% 的神经元 |

#### 3.3.2 Target Modules 解释

Gemma 模型的注意力层结构：

```
输入嵌入
    ↓
┌─────────────────────────────────────┐
│  Self-Attention (自注意力层)         │
│  ├── q_proj: Query 投影 (输入→Q)     │  ← LoRA 注入
│  ├── k_proj: Key 投影 (输入→K)       │  ← LoRA 注入
│  ├── v_proj: Value 投影 (输入→V)    │  ← LoRA 注入
│  └── o_proj: Output 投影 (结果→输出)│  ← LoRA 注入
└─────────────────────────────────────┘
    ↓
Feed-Forward (前馈层)
    ↓
输出
```

**为什么只改注意力层？**

- 注意力层是模型的"思考核心"
- 研究发现微调注意力层足以适配新任务
- 前馈层通常是通用的"知识存储"，不需要改

#### 3.3.3 Rank (r) 的选择

```
r=4:   非常小的适配器，适合简单任务，训练参数少
r=8:   平衡选择，PoC 使用（推荐起始值）
r=16:  更强的表达能力，适合复杂任务
r=32+: 接近全量微调，但参数多，容易过拟合
```

**PoC 选择 r=8 的原因**：
- 数据量小（1000 条），r=8 足够表达
- 保守策略，避免过拟合
- 训练速度快，便于快速迭代

---

### 3.4 训练配置 (`SFTConfig`)

```python
training_args = SFTConfig(
    # 基本训练参数
    num_train_epochs=1,                    # 训练 1 轮
    per_device_train_batch_size=1,         # 每设备 batch size
    gradient_accumulation_steps=4,         # 梯度累积步数
    
    # 优化器参数
    learning_rate=2e-4,                    # 学习率 0.0002
    warmup_steps=50,                       # 预热步数
    weight_decay=0.01,                     # 权重衰减
    lr_scheduler_type="cosine",            # 余弦退火
    
    # 显存优化
    bf16=True,                             # bfloat16 精度
    fp16=False,
    
    # 日志和保存
    logging_steps=10,                      # 每 10 步打印日志
    save_steps=100,                        # 每 100 步保存
)
```

#### 3.4.1 关键训练参数详解

**Epoch (轮数)**

```
Epoch 1: 所有数据过一遍
Epoch 2: 再过一遍（可能过拟合）
Epoch 3+: 继续训练（通常没必要）

PoC 使用 epoch=1：
- 数据量小，多轮容易过拟合
- 快速验证流程，不需要最优性能
```

**Batch Size 和 Gradient Accumulation**

```
真实 batch size = per_device_batch_size × accumulation_steps × GPU数量
                = 1 × 4 × 1 = 4

为什么不用 batch_size=4 直接？
- batch_size=1 节省显存
- accumulation_steps=4 模拟 batch_size=4 的梯度效果
- 适合显存有限的场景
```

**Learning Rate (学习率)**

```
学习率 = 2e-4 = 0.0002

太大 (1e-3): 训练不稳定，loss 震荡
合适 (2e-4): 平稳下降
太小 (1e-5): 收敛太慢

LoRA 通常使用较大学习率：2e-4 ~ 1e-3
```

**Warmup Steps (预热)**

```
前 50 步：学习率从 0 线性增加到 2e-4
之后：正常余弦退火

目的：
- 避免训练初期大学习率破坏预训练权重
- 让优化器先"适应"一下
```

**BF16 vs FP16**

```
BF16 (Brain Float 16):
- 指数位 8 bits，尾数位 7 bits
- 动态范围大（和 FP32 相同）
- 适合深度学习，数值稳定性好

FP16 (Half Float 16):
- 指数位 5 bits，尾数位 10 bits
- 动态范围小，容易溢出

RTX 5090 原生支持 BF16，所以用 bf16=True
```

---

### 3.5 数据格式化 (`formatting_prompts_func`)

```python
def formatting_prompts_func(example, tokenizer, max_seq_length: int = 2048):
    """
    使用模型的 chat template 格式化对话
    """
    messages = example["messages"]
    
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,           # 不转为 token IDs，保留文本
        add_generation_prompt=False  # 不添加生成提示
    )
    
    return {"text": text}
```

**Chat Template 的作用**

现代 LLM 使用特定的对话格式进行训练，例如 Gemma 使用：

```
<start_of_turn>user
我想学习编程<end_of_turn>
<start_of_turn>model
你想学习哪种编程语言？<end_of_turn>
```

`apply_chat_template` 自动将 `messages` 列表转换为模型期望的格式。

**为什么 `tokenize=False`？**

- SFTTrainer 内部会再次进行 tokenize
- 这里只是将对话拼接成完整字符串
- 方便调试和查看训练数据长什么样

---

### 3.6 训练执行 (`SFTTrainer`)

```python
trainer = SFTTrainer(
    model=model,                # 带 LoRA 的模型
    tokenizer=tokenizer,        # 分词器
    train_dataset=dataset,      # 训练数据
    args=training_args,         # 训练参数
    formatting_func=formatting_func,  # 数据格式化函数
)

# 开始训练
train_result = trainer.train()
```

**SFTTrainer 内部发生了什么？**

```
1. 从 dataset 取一个 batch
        ↓
2. formatting_func: messages → 对话文本
        ↓
3. tokenizer: 文本 → token IDs
        ↓
4. 前向传播 (Forward)
   模型预测下一个 token 的概率
        ↓
5. 计算损失 (CrossEntropyLoss)
   对比预测和真实标签的差异
        ↓
6. 反向传播 (Backward)
   只计算 LoRA 参数的梯度
        ↓
7. 优化器更新 (AdamW)
   更新 LoRA A 和 B 矩阵
        ↓
8. 重复 1-7，直到所有数据训练完成
```

**监督微调 (SFT) vs 预训练**

| | 预训练 (Pre-training) | 监督微调 (SFT) |
|---|----------------------|----------------|
| **数据** | 海量无标注文本 | 有标注的对话数据 |
| **目标** | 学习语言规律 | 学习特定任务/对话风格 |
| **计算** | 需要数千 GPU 天 | 只需几个 GPU 小时 |
| **输出** | 基础模型 | 对话模型 |

我们做的是 **SFT**：在预训练好的 Gemma 基础上，用我们的对话数据教它"头脑风暴"风格。

---

### 3.7 模型保存

```python
# 保存 LoRA 权重
trainer.save_model(str(output_dir))

# 保存 tokenizer (包含 chat template)
tokenizer.save_pretrained(str(output_dir))

# 保存训练元数据
meta = {
    "experiment_id": "s1-poc-e01",
    "model_name": args.model_name,
    "lora_config": {...},
    "training_args": {...},
    "train_result": {
        "final_loss": train_result.training_loss,
        "train_runtime": ...,
    },
}
```

**保存了什么？**

```
experiment/s1-poc-e01/
├── adapter_config.json          # LoRA 配置 (r=8, alpha=16 等)
├── adapter_model.safetensors    # LoRA 权重 (A 和 B 矩阵)
├── tokenizer/                   # Tokenizer 文件
│   ├── tokenizer_config.json
│   ├── tokenizer.json
│   └── special_tokens_map.json
└── training_meta.json           # 训练元数据 (loss, 时间等)
```

**注意**：保存的是 LoRA 增量权重，不是完整模型！

完整模型 = 基座 Gemma (8GB) + LoRA 权重 (16MB)

---

## 4. 训练参数总览

### 4.1 PoC 保守配置

| 参数 | 值 | 选择理由 |
|------|-----|----------|
| **基座模型** | gemma-4-2b-it | 4B 参数，端侧友好 |
| **数据量** | 1000 条 | 快速验证，30-60分钟训练 |
| **LoRA rank** | 8 | 平衡性能和效率 |
| **LoRA alpha** | 16 | 缩放因子 = 2，适中 |
| **Epochs** | 1 | 小数据，防过拟合 |
| **Batch size** | 1 (×4 累积 = 4) | 节省显存 |
| **Learning rate** | 2e-4 | LoRA 常用范围 |
| **Warmup steps** | 50 | 占总步数约 10% |
| **Precision** | bf16 + 4-bit | 5090 支持，节省显存 |
| **Max seq length** | 2048 | 覆盖大多数对话 |
| **Seed** | 42 | 可复现 |

### 4.2 预估资源消耗 (RTX 5090 32GB)

| 项目 | 估算值 | 说明 |
|------|--------|------|
| **模型加载** | ~6 GB | 4-bit 量化后 |
| **优化器状态** | ~0.5 GB | 仅 LoRA 参数 |
| **激活值** | ~4 GB | 前向传播中间结果 |
| **梯度** | ~0.5 GB | 反向传播梯度 |
| **预留缓冲** | ~2 GB | 系统预留 |
| **总占用** | ~13-15 GB | 远低于 32GB 上限 |
| **训练时间** | 30-60 分钟 | 1000 条 × 1 epoch |

---

## 5. 常见问题 FAQ

### Q1: 为什么不用全量微调 (Full Fine-tuning)？

```
全量微调: 训练 40亿 参数 × 4 bytes = 16 GB (仅权重)
         + 优化器状态 × 2 = 32 GB
         + 梯度 × 2 = 32 GB
         = 约 80 GB 显存需求 ❌

LoRA 微调: 训练 0.03亿 参数 × 4 bytes = 120 MB
          + 优化器状态 ≈ 400 MB
          + 4-bit 基座模型 = 2 GB
          = 约 6-8 GB 显存 ✅
```

### Q2: 如何判断训练是否正常？

**正常的指标**：

```
1. Loss 曲线：
   Step 10: loss=2.5
   Step 50: loss=1.8  ← 明显下降
   Step 100: loss=1.2
   Step 250: loss=0.8 ← 趋于平稳

2. 学习率：
   前 50 步线性上升 (warmup)
   之后余弦下降

3. GPU 利用率：
   nvidia-smi 显示 GPU-Util 60-100%
```

**异常的信号**：

```
❌ Loss = NaN: 学习率过大，减小 lr
❌ Loss 不降: 数据问题或 lr 过小
❌ OOM: 减小 batch_size 或启用量化
❌ GPU-Util = 0%: 数据加载瓶颈，调整 num_workers
```

### Q3: 如何选择 LoRA rank？

```
经验法则：
- 任务简单 + 数据少 (1k以下): r=4~8
- 任务中等 + 数据中等 (1k-10k): r=8~16
- 任务复杂 + 数据多 (10k+): r=16~32

PoC 用 r=8：
- 快速验证训练流程
- 不追求最优性能
- Stage 1 可以再调
```

### Q4: 4-bit 量化会损失性能吗？

```
实验证明：
- 4-bit 量化本身几乎无损（NF4 格式优化过）
- LoRA 在 4-bit 基座上微调，效果接近 BF16
- 对于 PoC 验证完全足够

注意：
- 推理时可以合并 LoRA + 基座，转为 BF16
- 最终部署不需要保持 4-bit
```

---

## 6. 相关资源

| 资源 | 链接 | 说明 |
|------|------|------|
| LoRA 论文 | arXiv:2106.09685 | 原始论文 |
| PEFT 库 | huggingface/peft | LoRA 实现 |
| TRL 库 | huggingface/trl | SFTTrainer |
| Gemma 文档 | ai.google.dev/gemma | 官方文档 |

---

## 7. 实际训练结果记录

这是 Sprint 1 Week 2 PoC 实验的实际运行记录。

### 7.1 训练完成日志

```
2026-05-16 23:11:15,644 - INFO - 保存 LoRA 权重到: experiment/s1-poc-e01
2026-05-16 23:11:16,366 - INFO - ============================================================
2026-05-16 23:11:16,366 - INFO - 训练完成!
2026-05-16 23:11:16,366 - INFO - 最终 loss: 1.9343
2026-05-16 23:11:16,367 - INFO - 训练时间: 385.28 秒
2026-05-16 23:11:16,367 - INFO - ============================================================

==========================================
训练完成!
==========================================
输出目录: experiment/s1-poc-e01/
LoRA 权重: experiment/s1-poc-e01/adapter_model.safetensors
训练日志: training.log
```

### 7.2 训练结果摘要

| 指标 | 数值 | 评价 |
|------|------|------|
| **最终 Loss** | 1.9343 | ✅ 正常范围（从约 2.5 下降到 1.93） |
| **训练时间** | 385.28 秒 | ✅ 约 6.4 分钟，快速完成 |
| **训练环境** | AutoDL RTX 5090 32GB | ✅ 云端 GPU |
| **LoRA 权重** | 5.14 MB | ✅ 正常大小（rank=8） |
| **训练轮数** | 1 epoch | 按计划执行 |
| **数据量** | 1000 条 | 按计划执行 |

---

## 8. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-17 | 初版：train_poc.py 详解与 LoRA 原理说明 |
| 2026-05-17 | 添加：实际训练结果记录（PoC 实验） |
