# `train_poc.py` Script Deep Dive, LoRA Fine-tuning Principles and Results

> **Goal**: Deep understanding of PoC training script workings and LoRA fine-tuning configuration  
> **Target Audience**: Users wanting to understand code logic and training principles  
> **Date**: 2026-05-17

---

## 0. Background

### 0.1 Project Background

This project attempts to use **Vibe Coding** to advance an on-device LLM fine-tuning project from scratch within 3-4 months, eventually landing as an **AI Thinking Assistant** Android App.

**Pain Point**: When inspiration strikes, you jot it down, but traditional notes can only "store" not "think" — they don't ask follow-up questions, don't diverge, and certainly don't help you converge into actionable insights.

**Solution**: Let a "casual sentence" go through on-device LLM **question-diverge-converge**, eventually harvested into structured "idea cards". We use **Gemma-4-E2B-IT** (4B class) as base, **LoRA fine-tuning** to align with "brainstorming" rhythm, then quantize and fit into mobile phones, balancing privacy and cost.

> For detailed task overview, see [Sprint1-00_tasks_intro_EN.md](Sprint1-00_tasks_intro_EN.md)

### 0.2 Positioning of This Document: Week 2 PoC Training Script Principles

**Sprint 1 Progress**:
- Week 1 Completed: Data freeze (v1.0 recipe) + Baseline evaluation (Layer 2 500 samples)
- **Week 2 Goal**: PoC quick closure — Complete end-to-end LoRA fine-tuning with 1k samples to verify "data+training+evaluation" pipeline works

**Core Content of This Document**:
1. **LoRA Principles**: Why use LoRA, mathematical principles, advantages and trade-offs
2. **Script Deep Dive**: `train_poc.py` line-by-line code interpretation
3. **Configuration Explanation**: Rationale for each hyperparameter (rank, lr, epoch, etc.)
4. **Actual Results**: Real training records from PoC experiment (loss=1.93, time=385 seconds)

> For supporting environment setup guide, see [Sprint1-06_autodl_setup_EN.md](Sprint1-06_autodl_setup_EN.md)  
> For detailed PoC planning, see [Sprint1-05_week2_poc_plan_EN.md](Sprint1-05_week2_poc_plan_EN.md)

---

## 1. Overall Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        train_poc.py                              │
├─────────────────────────────────────────────────────────────────┤
│  1. Data Loading (load_poc_data)                                 │
│     └── Read from JSONL → Convert to HuggingFace Dataset        │
├─────────────────────────────────────────────────────────────────┤
│  2. Model Preparation (setup_model_and_tokenizer)                │
│     ├── Download/Load Gemma-4-2b-it                             │
│     ├── 4-bit Quantization (save memory)                        │
│     └── Prepare Tokenizer                                       │
├─────────────────────────────────────────────────────────────────┤
│  3. LoRA Configuration (setup_lora_config)                      │
│     └── Configure low-rank adapters (rank=8, alpha=16)           │
├─────────────────────────────────────────────────────────────────┤
│  4. Training Execution (SFTTrainer)                             │
│     ├── Supervised Fine-Tuning (SFT)                            │
│     ├── Backpropagation Optimization                           │
│     └── Save LoRA Weights                                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. LoRA Fine-tuning Principles

### 2.1 What is LoRA?

**LoRA** (Low-Rank Adaptation) is a **Parameter-Efficient Fine-Tuning (PEFT)** method.

#### Core Idea

Instead of training all parameters of the large model (4 billion), train a small number of "adapter" parameters:

```
Traditional Fine-tuning: Modify all 4B parameters → Requires massive compute
LoRA Fine-tuning: Freeze 4B parameters, only train 0.1% ~ 1% low-rank matrices → Efficient
```

#### Mathematical Principle

For a weight matrix $W_0$ in the original model, LoRA learns a **low-rank update**:

$$W = W_0 + \Delta W = W_0 + BA$$

Where:
- $W_0$: Original weight matrix (d×d), **frozen, not trained**
- $B$: Low-rank matrix (d×r), **trainable**
- $A$: Low-rank matrix (r×d), **trainable**
- $r$: rank, usually r << d (e.g., r=8, d=2048)

```
Original weights W0: [2048 × 2048] = 4,194,304 parameters (frozen)
LoRA A:              [8 × 2048]    = 16,384 parameters (trainable)
LoRA B:              [2048 × 8]    = 16,384 parameters (trainable)
─────────────────────────────────────────────────────────
Total trainable:     32,768 (only 0.78% of original)
```

### 2.2 Why Use LoRA?

| Advantage | Description |
|-----------|-------------|
| **Memory Efficient** | Only load optimizer states for few parameters, significantly reduces GPU memory |
| **Faster Training** | Backpropagation only updates few parameters, less computation |
| **Smaller Weights** | LoRA weights typically only tens of MB, easy to transfer and deploy |
| **Composable** | Multiple LoRAs can be stacked on same base model |

---

## 3. Script Section-by-Section Deep Dive

### 3.1 Data Loading (`load_poc_data`)

```python
def load_poc_data(data_path: str, max_samples: Optional[int] = None) -> Dataset:
    """
    Load PoC data and convert to HuggingFace Dataset format
    
    Input format: {"id": str, "messages": [{"role": "user/assistant", "content": str}]}
    Output format: Dataset object, each containing "messages" field
    """
    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            messages = item.get('messages', [])
            if not messages:
                continue
            
            # Keep conversation format, formatting_func handles later
            formatted = {"messages": messages, "id": item.get("id")}
            data.append(formatted)
    
    return Dataset.from_list(data)
```

**Why use `messages` format?**

Modern LLMs (Gemma, Qwen, Llama) use conversation format for training, where each sample is a conversation list:

```json
{
  "messages": [
    {"role": "user", "content": "I want to learn programming"},
    {"role": "assistant", "content": "Great! Which programming language?"},
    {"role": "user", "content": "Python"}
  ]
}
```

More flexible than traditional "input/output" format, supports multi-turn conversations.

### 3.2 Model Loading (`setup_model_and_tokenizer`)

Key concepts:

**Tokenizer**: Converts text to token IDs the model understands
**4-bit Quantization**: Reduces memory from 16GB (FP32) → 8GB (BF16) → 2GB (4-bit)

**NF4 Quantization Trade-offs**:

| Issue | Description | Impact |
|-------|-------------|--------|
| **Precision Loss** | 4-bit range much lower than 16-bit | May cause model to "forget" some base capabilities |
| **Gradient Noise** | Low precision introduces more noise | Need smaller learning rate or longer convergence |
| **Layer Sensitivity** | Some layers (embeddings, output) more sensitive | May produce abnormal outputs if quantized |
| **Inference Compatibility** | Quantized format not fully compatible with all frameworks | May need conversion for mobile deployment |

**PoC Trade-off**: Accept precision loss temporarily to get pipeline running; optimize in Stage 1 based on evaluation data.

### 3.3 LoRA Configuration (`setup_lora_config`)

| Parameter | Value | Meaning | Impact |
|-----------|-------|---------|--------|
| **r** (rank) | 8 | Low-rank matrix rank | Higher = stronger expression, more parameters |
| **alpha** | 16 | Scaling factor | Actual scale = alpha/r = 2, controls LoRA weight impact |
| **target_modules** | q/k/v/o_proj | Layers to apply LoRA | Attention layer projection matrices |
| **dropout** | 0.05 | Random dropout rate | Prevents overfitting, drops 5% neurons during training |

**Why only attention layers?**
- Attention is the "thinking core" of the model
- Research shows fine-tuning attention sufficient for task adaptation
- Feed-forward layers are general "knowledge storage", don't need changes

### 3.4 Training Configuration (`SFTConfig`)

**Epoch (Training Rounds)**

```
Epoch 1: Go through all data once
Epoch 2: Go through again (may overfit)
Epoch 3+: Continue (usually unnecessary)

PoC uses epoch=1:
- Small data, multiple rounds prone to overfitting
- Quick pipeline validation, don't need optimal performance
```

**Batch Size and Gradient Accumulation**

```
Effective batch size = per_device_batch_size × accumulation_steps × num_GPUs
                    = 1 × 4 × 1 = 4

Why not batch_size=4 directly?
- batch_size=1 saves memory
- accumulation_steps=4 simulates batch_size=4 gradient effect
- Good for memory-constrained scenarios
```

**Learning Rate**

```
Learning rate = 2e-4 = 0.0002

Too high (1e-3): Training unstable, loss oscillates
Good (2e-4): Steady decrease
Too low (1e-5): Converges too slowly

LoRA typically uses larger learning rates: 2e-4 ~ 1e-3
```

### 3.5 Training Execution (`SFTTrainer`)

**Internal Flow**:

```
1. Fetch batch from dataset
        ↓
2. formatting_func: messages → conversation text
        ↓
3. tokenizer: text → token IDs
        ↓
4. Forward pass
   Model predicts next token probabilities
        ↓
5. Compute loss (CrossEntropyLoss)
   Compare prediction with ground truth
        ↓
6. Backward pass
   Only compute gradients for LoRA parameters
        ↓
7. Optimizer update (AdamW)
   Update LoRA A and B matrices
        ↓
8. Repeat 1-7 until all data trained
```

---

## 4. Training Parameters Summary

### 4.1 PoC Conservative Configuration

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| **Base Model** | gemma-4-2b-it | 4B params, mobile-friendly |
| **Data Amount** | 1000 samples | Quick validation, 30-60min training |
| **LoRA rank** | 8 | Balance performance and efficiency |
| **LoRA alpha** | 16 | Scale factor = 2, moderate |
| **Epochs** | 1 | Small data, prevent overfitting |
| **Batch size** | 1 (×4 accumulation = 4) | Save memory |
| **Learning rate** | 2e-4 | Common LoRA range |
| **Warmup steps** | 50 | About 10% of total steps |
| **Precision** | bf16 + 4-bit | 5090 support, saves memory |
| **Max seq length** | 2048 | Covers most conversations |
| **Seed** | 42 | Reproducible |

---

## 5. FAQ

### Q1: Why not Full Fine-tuning?

```
Full Fine-tuning: Train 4B params × 4 bytes = 16 GB (weights only)
                 + Optimizer × 2 = 32 GB
                 + Gradients × 2 = 32 GB
                 = ~80 GB GPU memory needed ❌

LoRA Fine-tuning: Train 0.03B params × 4 bytes = 120 MB
                 + Optimizer ≈ 400 MB
                 + 4-bit base model = 2 GB
                 = ~6-8 GB GPU memory ✅
```

### Q2: How to judge if training is normal?

**Normal Indicators**:
```
1. Loss Curve:
   Step 10: loss=2.5
   Step 50: loss=1.8  ← obvious decrease
   Step 100: loss=1.2
   Step 250: loss=0.8 ← stabilizes

2. Learning Rate:
   First 50 steps linear rise (warmup)
   Then cosine decay

3. GPU Utilization:
   nvidia-smi shows GPU-Util 60-100%
```

**Abnormal Signals**:
```
❌ Loss = NaN: Learning rate too high, reduce lr
❌ Loss not decreasing: Data problem or lr too small
❌ OOM: Reduce batch_size or enable quantization
❌ GPU-Util = 0%: Data loading bottleneck, adjust num_workers
```

---

## 6. Actual Training Results Record

This is the actual run record from Sprint 1 Week 2 PoC experiment.

### 6.1 Training Completion Log

```
2026-05-16 23:11:15,644 - INFO - Saving LoRA weights to: experiment/s1-poc-e01
2026-05-16 23:11:16,366 - INFO - ============================================================
2026-05-16 23:11:16,366 - INFO - Training completed!
2026-05-16 23:11:16,366 - INFO - Final loss: 1.9343
2026-05-16 23:11:16,367 - INFO - Training time: 385.28 seconds
2026-05-16 23:11:16,367 - INFO - ============================================================

==========================================
Training completed!
==========================================
Output directory: experiment/s1-poc-e01/
LoRA weights: experiment/s1-poc-e01/adapter_model.safetensors
Training log: training.log
```

### 6.2 Training Results Summary

| Metric | Value | Evaluation |
|--------|-------|------------|
| **Final Loss** | 1.9343 | ✅ Normal range (decreased from ~2.5 to 1.93) |
| **Training Time** | 385.28 seconds | ✅ About 6.4 minutes, quick completion |
| **Environment** | AutoDL RTX 5090 32GB | ✅ Cloud GPU |
| **LoRA Weights** | 5.14 MB | ✅ Normal size (rank=8) |
| **Training Rounds** | 1 epoch | As planned |
| **Data Amount** | 1000 samples | As planned |

### 6.3 Evaluation Results Summary

| Subset | Samples | Overall Mean | vs Baseline | Evaluation |
|--------|---------|--------------|-------------|------------|
| **core** | 199 | 80.68 | -12.67 (-13.6%) | ⚠️ Available but needs optimization |
| **general** | 200 | 67.23 | -14.62 (-17.9%) | ⚠️ Significant decline |
| **zh_guard** | 80 | 44.71 | -33.23 (-42.6%) | ❌ Severe degradation |
| **All** | 479 | 69.06 | -16.61 (-19.4%) | ⚠️ Within PoC expectations |

### 6.4 Key Findings

1. **Training Successful**: Loss decreased smoothly from ~2.5 to 1.93, no NaN or crashes
2. **Fast**: 6.4 minutes on RTX 5090, validates 4-bit quantization efficiency
3. **Performance decline within expectations**: Conservative config with 1k data 1 epoch, -19.4% expected
4. **Biggest Issue**: zh_guard -42.6%, Stage 1 needs to prioritize Chinese capability

### 6.5 Decision Conclusion

**Decision: ACCEPT** (Enter Stage 1 Conservative Training)

**Reasoning**:
- ✅ Training pipeline completely verified (data→training→evaluation→scoring)
- ✅ LoRA weights loadable, usable for inference, correct format
- ✅ core layer 80.68, core brainstorming function preserved
- ⚠️ Performance decline within expectations (PoC goal is pipeline verification, not optimal performance)

**Stage 1 Improvement Directions**:
1. Increase Chinese data ratio to 50%+ (current 40%)
2. Training epochs 1 → 2-3
3. Try larger LoRA rank (8→16)
4. Complete self-built seed data 500 samples

---

## 7. Related Resources

| Resource | Link | Description |
|----------|------|-------------|
| LoRA Paper | arXiv:2106.09685 | Original paper |
| PEFT Library | huggingface/peft | LoRA implementation |
| TRL Library | huggingface/trl | SFTTrainer |
| Gemma Docs | ai.google.dev/gemma | Official documentation |

---

## 8. Revision History

| Date | Revision |
|------|----------|
| 2026-05-17 | Initial: train_poc.py deep dive and LoRA principles |
| 2026-05-17 | Added: Actual training results record (PoC experiment) |
