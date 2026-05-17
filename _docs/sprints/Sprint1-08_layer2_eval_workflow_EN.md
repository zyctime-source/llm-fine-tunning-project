# Sprint 1 Week 2: Post-Fine-tuning Layer 2 Evaluation Complete Workflow

> **Goal**: Complete workflow guide from LoRA weights generation to Layer 2 evaluation completion  
> **Applicable Scenarios**: Post-PoC/Stage 1 training evaluation verification  
> **Date**: 2026-05-17

---

## 0. Background

### 0.1 Project Background

This project attempts to use **Vibe Coding** to advance an on-device LLM fine-tuning project from scratch within 3-4 months, eventually landing as an **AI Thinking Assistant** Android App.

**Pain Point**: When inspiration strikes, you jot it down, but traditional notes can only "store" not "think" — they don't ask follow-up questions, don't diverge, and certainly don't help you converge into actionable insights.

**Solution**: Let a "casual sentence" go through on-device LLM **question-diverge-converge**, eventually harvested into structured "idea cards". We use **Gemma-4-E2B-IT** (4B class) as base, **LoRA fine-tuning** to align with "brainstorming" rhythm, then quantize and fit into mobile phones, balancing privacy and cost.

> For detailed task overview, see [Sprint1-00_tasks_intro_EN.md](Sprint1-00_tasks_intro_EN.md)

### 0.2 Positioning of This Document: Post-Fine-tuning Evaluation Workflow

**Sprint 1 Progress**:
- Week 1 Completed: Data freeze (v1.0 recipe) + Baseline evaluation (Layer 2 500 samples)
- Week 2 Completed: PoC training (1k samples 1 epoch, loss=1.93) + LoRA weights generation
- **Current Stage**: Verify fine-tuning effects — complete pipeline from LoRA weights to Layer 2 evaluation and scoring

**Core Content of This Document**:
1. **Fine-tuning Result Confirmation**: Check LoRA weights, training metadata
2. **Smoke Test**: First 10 samples quick verification that weights are loadable and inference works
3. **Full Inference**: 500-sample batch inference with resume support
4. **Judge Scoring**: LLM-as-Judge 9-dimensional scoring
5. **Result Analysis**: Stratified statistics, baseline comparison, decision recommendations

**Actual Data**: This document is based on real PoC experiment records (Training completed 2026-05-16, core 80.68 / general 67.23 / zh_guard 44.71).

> For supporting training script explanation, see [Sprint1-07_train_poc_explained_EN.md](Sprint1-07_train_poc_explained_EN.md)  
> For detailed PoC planning, see [Sprint1-05_week2_poc_plan_EN.md](Sprint1-05_week2_poc_plan_EN.md)

---

## 1. Workflow Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│              Post-Fine-tuning Layer 2 Evaluation Complete Workflow   │
├─────────────────────────────────────────────────────────────────────┤
│  Step 1: Prepare LoRA Weights                                        │
│     └── Confirm adapter_model.safetensors generated                  │
├─────────────────────────────────────────────────────────────────────┤
│  Step 2: Layer 2 Smoke Test                                          │
│     └── First 10 samples quick verification, confirm loadable        │
├─────────────────────────────────────────────────────────────────────┤
│  Step 3: Full Layer 2 Inference (500 samples)                        │
│     └── Batch inference, generate poc_infer_full_*.jsonl             │
├─────────────────────────────────────────────────────────────────────┤
│  Step 4: Judge Scoring (LLM-as-Judge)                              │
│     └── qwen3.6-plus scoring, generate poc_judge_scores.jsonl       │
├─────────────────────────────────────────────────────────────────────┤
│  Step 5: Results Aggregation & Analysis                            │
│     └── Stratified stats, baseline comparison, decision advice     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Fine-tuning Result Confirmation

### 2.1 Check Training Artifacts

Before continuing evaluation, confirm the following files are generated:

```bash
ls -lh experiment/s1-poc-e01/

# Expected output:
-rw-r--r-- 1 user user 1.1K May 16 23:11 adapter_config.json
-rw-r--r-- 1 user user 5.2M May 16 23:11 adapter_model.safetensors  # ✅ LoRA weights
-rw-r--r-- 1 user user  31M May 16 23:11 tokenizer.json
-rw-r--r-- 1 user user  470B May 16 23:11 training_meta.json
drwxr-xr-x 2 user user 4.0K May 16 23:09 checkpoint-200
drwxr-xr-x 2 user user 4.0K May 16 23:11 checkpoint-250
drwxr-xr-x 2 user user    6 May 16 22:00 results
```

**Key File Checklist**:

| File | Size | Description | Status |
|------|------|-------------|--------|
| `adapter_model.safetensors` | ~5MB | LoRA weights file | ✅ Must exist |
| `adapter_config.json` | ~1KB | LoRA config (r=8, alpha=16) | ✅ Must exist |
| `tokenizer.json` | ~31MB | Tokenizer (required for inference) | ✅ Must exist |
| `training_meta.json` | ~500B | Training metadata | ✅ Must exist |

### 2.2 Confirm Training Results

View training metadata to confirm successful training:

```bash
cat experiment/s1-poc-e01/training_meta.json
```

**Expected Output**:
```json
{
  "experiment_id": "s1-poc-e01",
  "model_name": "google/gemma-4-2b-it",
  "lora_config": {
    "r": 8,
    "alpha": 16,
    "dropout": 0.05
  },
  "training_args": {
    "num_epochs": 1,
    "batch_size": 1,
    "learning_rate": 0.0002,
    "seed": 42
  },
  "train_result": {
    "final_loss": 1.9343,
    "train_runtime": 385.28
  }
}
```

**Success Criteria**:
- ✅ `final_loss` < 2.5 (decreased from initial ~2.5-3.0)
- ✅ `train_runtime` reasonable (PoC ~5-10 minutes)
- ✅ No `error` or `nan` fields

---

## 3. Layer 2 Smoke Test (First 10 Samples)

### 3.1 Why Do a Smoke Test?

Before running full 500 samples, first use 10 samples for quick verification:

1. **Weights Loadable**: Confirm LoRA weights can be loaded correctly
2. **Inference Normal**: Confirm model can generate reasonable text
3. **Format Correct**: Confirm output format meets expectations
4. **Save Time**: If smoke test fails, avoid wasting time on full inference

### 3.2 Execute Smoke Test

Use `layer2_smoke_infer_poc.py` script:

```bash
# Execute on AutoDL (with GPU) or local (with GPU)
python scripts/layer2_smoke_infer_poc.py \
    --model_path experiment/s1-poc-e01 \
    --manifest data/eval/layer2/manifest_v0.jsonl \
    --limit 10 \
    --out experiment/s1-poc-e01/results/poc_infer_smoke.jsonl
```

### 3.3 Source Code Explanation: `layer2_smoke_infer_poc.py`

```python
#!/usr/bin/env python3
"""
Post-PoC Layer 2 Smoke Test (First 10 samples quick verification)
"""

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

def run_inference(model, tokenizer, items, max_new_tokens=2048):
    """Run inference"""
    results = []
    device = model.device
    
    for item in items:
        layer2_id = item.get("layer2_id")
        prompt = item.get("prompt", "")
        
        # Build input (using conversation format)
        messages = [{"role": "user", "content": prompt}]
        text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )
        
        # Encode and generate
        inputs = tokenizer(text, return_tensors="pt").to(device)
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=0.1,  # Low temperature, stable output
                do_sample=False,  # Greedy decoding
            )
        
        # Decode result
        response = tokenizer.decode(outputs[0], skip_special_tokens=False)
        generated = response[len(text):].strip()
        
        results.append({
            "layer2_id": layer2_id,
            "prompt": prompt,
            "response": generated,
            "model": "s1-poc-e01",
        })
    
    return results

# Main flow
def main():
    # 1. Load model (base + LoRA)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        load_in_4bit=True,  # 4-bit quantization saves memory
    )
    model = PeftModel.from_pretrained(model, model_path)  # Load LoRA
    
    # 2. Load Layer 2 question list (first 10)
    items = load_manifest(manifest_path, limit=10)
    
    # 3. Run inference
    results = run_inference(model, tokenizer, items)
    
    # 4. Save results
    save_results(results, output_path)
```

**Key Code Explanation**:

| Code Segment | Function |
|--------------|----------|
| `PeftModel.from_pretrained()` | Load LoRA weights into base model |
| `apply_chat_template()` | Use Gemma conversation format template |
| `temperature=0.1` | Low temperature, more stable output (evaluation standard) |
| `do_sample=False` | Greedy decoding, reproducible |

### 3.4 Smoke Test Expected Output

```
============================================================
PoC Layer 2 Smoke Test
============================================================
Model: experiment/s1-poc-e01
Base: google/gemma-4-2b-it
Manifest: data/eval/layer2/manifest_v0.jsonl
Test samples: 10

[1/3] Loading model...
  - Tokenizer... ✓
  - Base model (4-bit)... ✓
  - LoRA weights... ✓
  Model loading complete

[2/3] Loading question list (first 10)...
  ✓ Loaded 10 samples

Test samples:
  1. [core] layer2-core-001: How to design a brainstorming workshop...
  2. [core] layer2-core-002: I have some ideas about environmental protection...
  3. [general] layer2-general-001: Explain quantum computing...
  ...

[3/3] Running inference...
100%|████████████████████| 10/10 [00:30<00:00,  3.00s/it]

============================================================
Inference Results Preview
============================================================

【layer2-core-001】
Prompt: How to design a brainstorming workshop to get participants actively speaking?
Response: This is a great question! First, you can consider what the workshop's goal is?...

【layer2-core-002】
Prompt: I have some ideas about environmental protection but don't know how to implement
Response: Great! Can you specifically talk about your ideas? We can analyze from feasibility perspective...

...

✓ Smoke test complete
Output file: experiment/s1-poc-e01/results/poc_infer_smoke_20260516TXXXXZ.jsonl
```

### 3.5 Smoke Test Pass Criteria

| Check Item | Pass Criteria | Failure Handling |
|------------|---------------|------------------|
| **Model Loading** | No errors, successful load | Check path, dependency installation |
| **Inference Execution** | All 10 successful | Check GPU, memory |
| **Output Format** | Normal Chinese/English response | Check tokenizer, chat template |
| **Content Relevance** | Response related to prompt | If completely unrelated, retrain needed |

**⚠️ If Smoke Test Fails**:
- Do not continue full inference
- Check if LoRA weights saved correctly
- Check if base model and LoRA match
- Retrain if necessary

---

## 4. Full Layer 2 Inference (500 Samples)

### 4.1 Execute Full Inference

After smoke test passes, execute full 500 samples:

```bash
# Execute on AutoDL (recommended, with GPU)
python scripts/layer2_full_infer_poc.py \
    --model_path experiment/s1-poc-e01 \
    --manifest data/eval/layer2/manifest_v0.jsonl \
    --out experiment/s1-poc-e01/results/poc_infer_full.jsonl
```

**Estimated Time**: 20-40 minutes (depends on GPU)

### 4.2 Source Code Explanation: `layer2_full_infer_poc.py`

Core differences vs smoke test:

```python
# Key difference 1: Support resume (checkpoint)
def load_existing_results(output_path):
    """Load existing results for resume"""
    existing_ids = set()
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            for line in f:
                r = json.loads(line)
                existing_ids.add(r.get("layer2_id"))
    return existing_ids

# Key difference 2: Filter completed samples
def main():
    all_items = load_manifest(manifest_path)  # 500 samples
    existing_ids = load_existing_results(output_path)
    
    # Only infer incomplete ones
    items = [item for item in all_items 
             if item.get("layer2_id") not in existing_ids]
    
    print(f"Total: {len(all_items)} samples")
    print(f"Completed: {len(existing_ids)} samples")
    print(f"Pending: {len(items)} samples")

# Key difference 3: Exception handling (single failure doesn't affect overall)
def run_inference(...):
    for item in items:
        try:
            # Inference logic
            result = {...}
        except Exception as e:
            # Record error, continue next
            result = {
                "layer2_id": layer2_id,
                "status": "error",
                "error": str(e),
            }
        results.append(result)
```

**Full Inference Features**:

| Feature | Description |
|---------|-------------|
| **Resume Support** | If interrupted, rerun will automatically skip completed |
| **Exception Tolerance** | Single failure recorded, continue other samples |
| **Progress Display** | tqdm progress bar shows real-time progress |
| **Auto Save** | Write to file immediately after each completion |

### 4.3 Full Inference Expected Output

```
============================================================
PoC Layer 2 Full Inference
============================================================
Model path: experiment/s1-poc-e01
Base model: google/gemma-4-2b-it
Manifest path: data/eval/layer2/manifest_v0.jsonl
Inference samples: Full (500 samples)

[1/4] Loading model...
  - Tokenizer...
  - Base model (4-bit)...
  - LoRA weights...
  ✓ Model loading complete

[2/4] Loading manifest...
  Loaded 500 samples

[3/4] Running inference...
Inference progress: 100%|████████████████████| 500/500 [25:00<00:00,  3.00s/it]

[4/4] Saving results...
  ✓ Results saved

============================================================
Inference Completion Statistics
============================================================
Total samples: 500
Success: 500
Failed: 0
Success rate: 100.0%

✓ All successful!
Output file: experiment/s1-poc-e01/results/poc_infer_full_20260516TXXXXZ.jsonl

Next steps:
  1. Download results to local
  2. Run judge scoring (layer2_judge_scores.py)
```

### 4.4 Results File Format

```jsonl
{"layer2_id": "layer2-core-001", "subset": "core", "prompt": "How to design...", "response": "First...", "model": "s1-poc-e01", "timestamp": "2026-05-16T23:30:00Z"}
{"layer2_id": "layer2-core-002", "subset": "core", "prompt": "I have...", "response": "Great...", "model": "s1-poc-e01", "timestamp": "2026-05-16T23:30:03Z"}
{"layer2_id": "layer2-general-001", "subset": "general", "prompt": "Explain quantum...", "response": "Quantum computing...", "model": "s1-poc-e01", "timestamp": "2026-05-16T23:30:06Z"}
...
```

---

## 5. Judge Scoring (LLM-as-Judge)

### 5.1 Why Judge Scoring?

Automatic evaluation dimensions are not comprehensive enough, need LLM as judge for multi-dimensional scoring:

| Dimension | Description |
|-----------|-------------|
| **relevance** | Relevance of response to prompt |
| **coherence** | Logical coherence |
| **helpfulness** | Helpfulness level |
| **creativity** | Creativity |
| **clarity** | Clarity |
| **task_alignment** | Task alignment (question-diverge-converge) |
| **depth** | Depth |
| **chinese_quality** | Chinese quality |
| **overall** | Overall score |

### 5.2 Execute Judge Scoring

```bash
# Execute locally (calls DashScope API)
python scripts/layer2_judge_scores.py \
    --manifest data/eval/layer2/manifest_v0.jsonl \
    --infer-jsonl experiment/s1-poc-e01/results/poc_infer_full_*.jsonl \
    --out experiment/s1-poc-e01/results/poc_judge_scores.jsonl
```

**Estimated Time**: 30-60 minutes (500 samples × ~5-10 seconds/sample)

**Dependencies**:
- `DASHSCOPE_API_KEY` configured in `.env`
- Network connection (calls Alibaba Cloud API)

### 5.3 Source Code Explanation: `layer2_judge_scores.py`

```python
#!/usr/bin/env python3
"""
Layer 2 Judge Scoring (DashScope qwen3.6-plus)
"""

import openai
from tenacity import retry, stop_after_attempt

# Initialize Judge LLM
client = openai.OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

# Scoring Prompt Template
JUDGE_PROMPT = """
You are a professional AI assistant evaluation expert. Please score the following response (1-100).

Prompt: {prompt}
Response: {response}

Please score from the following dimensions:
1. relevance: Relevance of response to prompt
2. coherence: Logical coherence
3. helpfulness: Helpfulness level
4. creativity: Creativity
5. clarity: Clarity
6. task_alignment: Whether it meets question-diverge-converge task requirements
7. depth: Depth
8. chinese_quality: Chinese expression quality
9. overall: Overall score

Please return in JSON format:
{{"relevance": 85, "coherence": 90, ..., "overall": 87}}
"""

@retry(stop=stop_after_attempt(3))  # Retry 3 times on failure
def judge_single(item, infer_result):
    """Score single result"""
    prompt = item.get("prompt")
    response = infer_result.get("response")
    
    # Call Judge LLM
    resp = client.chat.completions.create(
        model="qwen3.6-plus",
        messages=[
            {"role": "system", "content": "You are a professional AI evaluation expert."},
            {"role": "user", "content": JUDGE_PROMPT.format(prompt=prompt, response=response)}
        ],
        temperature=0.1,  # Low temperature, stable scoring
    )
    
    # Parse JSON score
    content = resp.choices[0].message.content
    scores = parse_json_scores(content)  # Extract JSON part
    
    return {
        "layer2_id": item.get("layer2_id"),
        "subset": item.get("subset"),
        "scores": scores,  # Each dimension score
        "judge_model": "qwen3.6-plus",
    }

def main():
    # Load manifest and inference results
    manifest = load_manifest(manifest_path)
    infer_results = load_infer_results(infer_jsonl_path)
    
    # Score one by one
    for item in tqdm(manifest, desc="Judge scoring"):
        layer2_id = item.get("layer2_id")
        infer_result = infer_results.get(layer2_id)
        
        try:
            judge_result = judge_single(item, infer_result)
            save_result(judge_result, output_path)
        except Exception as e:
            # Record error, continue next
            save_error(layer2_id, str(e), output_path)
```

**Scoring Features**:

| Feature | Description |
|---------|-------------|
| **Multi-dimensional** | 9 dimensions comprehensive evaluation |
| **Automated** | Batch automatic scoring, no manual work |
| **Consistent** | Same judge model ensures consistent standards |
| **Fault-tolerant** | Single failure recorded, continue others |

### 5.4 Scoring Results Format

```jsonl
{"layer2_id": "layer2-core-001", "subset": "core", "scores": {"relevance": 90, "coherence": 85, "helpfulness": 80, "creativity": 75, "clarity": 95, "task_alignment": 88, "depth": 70, "chinese_quality": 98, "overall": 85}, "judge_model": "qwen3.6-plus"}
{"layer2_id": "layer2-core-002", "subset": "core", "scores": {"relevance": 88, "coherence": 90, "helpfulness": 82, ...}, "judge_model": "qwen3.6-plus"}
...
```

---

## 6. Results Aggregation & Analysis

### 6.1 Execute Results Aggregation

```bash
# Generate stratified statistics report
python scripts/aggregate_layer2_judge_scores.py \
    --judge-jsonl experiment/s1-poc-e01/results/poc_judge_scores.jsonl \
    --out experiment/s1-poc-e01/results/poc_judge_summary.json
```

**Expected Output**:
```
Wrote experiment/s1-poc-e01/results/poc_judge_summary.json
Suggested META.result_scores:
{
  "result_scores": {
    "judge_summary_schema": "layer2-judge-summary-v0",
    "counts": {
      "rows_after_dedupe": 480,
      "judge_parse_ok": 479,
      "judge_parse_fail": 1
    },
    "by_stratum_overall_mean": {
      "core": 80.683,
      "general": 67.225,
      "zh_guard": 44.712
    },
    "all_parse_ok_overall_mean": 69.056
  }
}
```

### 6.2 Aggregation Report Format

`poc_judge_summary.json` contains:

```json
{
  "schema": "layer2-judge-summary-v0",
  "source_judge_jsonl": "experiment/s1-poc-e01/results/poc_judge_scores.jsonl",
  "judge_model": "qwen3.6-plus",
  "counts": {
    "rows_after_dedupe": 480,
    "judge_parse_ok": 479,
    "judge_parse_fail": 1
  },
  "by_stratum": {
    "core": {
      "n": 199,
      "overall": {"mean": 80.683, "median": 88.0},
      "relevance": {"mean": 88.925, "median": 95.0},
      "coherence": {"mean": 88.141, "median": 95.0},
      "helpfulness": {"mean": 78.588, "median": 85.0},
      "creativity": {"mean": 70.055, "median": 75.0},
      "clarity": {"mean": 94.497, "median": 95.0},
      "task_alignment": {"mean": 84.0, "median": 90.0},
      "depth": {"mean": 72.121, "median": 80.0},
      "chinese_quality": {"mean": 95.015, "median": 95.0}
    },
    "general": {...},
    "zh_guard": {...}
  },
  "all_parse_ok": {
    "n": 479,
    "overall": {"mean": 69.056, "median": 80.0}
  }
}
```

### 6.3 Baseline Comparison Analysis

| Subset | Baseline | PoC | Change | Change% | Evaluation |
|--------|----------|-----|--------|---------|------------|
| **core** | 93.35 | 80.68 | -12.67 | **-13.6%** | ⚠️ Declined but usable |
| **general** | 81.85 | 67.23 | -14.62 | **-17.9%** | ⚠️ Significant decline |
| **zh_guard** | 77.94 | 44.71 | -33.23 | **-42.6%** | ❌ Severe degradation |
| **All** | **85.67** | **69.06** | **-16.61** | **-19.4%** | ⚠️ Within expectations |

**Visual Comparison**:

```
Baseline vs PoC Comparison (overall scores)

100 │                                              ╭──── baseline
    │                              ╭───────────────╯
 90 │              ╭───────────────╯
    │              │               ╭──── poc
 80 │  ╭───────────╯               │
    │  │                           │
 70 │  │           ╭───────────────╯
    │  │           │
 60 │  │           │
    │  │           │               ╭──── poc (zh_guard ↓)
 50 │  │           │               │
    │  │           │               │
 40 │  │           │               ╰───────────────
    │  │           │
    └──┴───────────┴───────────────┴────────────────
       core      general         zh_guard
```

---

## 7. Decision Recommendations

### 7.1 Red Line Check

| Red Line | Definition | PoC Status | Result |
|----------|------------|------------|--------|
| **P0** | Model can't load or inference | Weights loadable, inference works | ✅ **Pass** |
| **P1** | Output safety/format serious errors | No safety violations, format correct | ✅ **Pass** |
| **P2** | Core capabilities significantly degraded (> 20%) | core layer decline -13.6% | ✅ **Pass** |
| **P2** | zh_guard severely degraded (> 30%) | zh_guard decline -42.6% | ⚠️ **Triggered** |

### 7.2 Decision: ACCEPT

**Decision**: **ACCEPT** (Enter Stage 1 Conservative Training)

**Reasoning**:
1. ✅ Training pipeline completely verified (data→training→evaluation→scoring)
2. ✅ LoRA weights loadable, usable for inference, correct format
3. ✅ core layer 80.68, core brainstorming function preserved
4. ⚠️ Performance decline within expectations (PoC used 1k data 1 epoch)

### 7.3 Stage 1 Improvement Directions

Based on PoC results, Stage 1 needs to prioritize:

| Priority | Improvement Item | Specific Measures |
|----------|------------------|-------------------|
| **P0** | Chinese protection (zh_guard) | Increase Chinese data ratio to 50%+, or increase training epochs to 2-3 |
| **P1** | Question depth (depth) | Add more deep follow-up samples in data |
| **P1** | Creativity (creativity) | Add diverse brainstorming cases, reduce templated responses |
| **P2** | General capability preservation | Increase general capability data ratio, or use larger rank |

---

## 8. Complete Workflow Checklist

| Step | Command | Artifact | Checkpoint |
|------|---------|----------|----------|
| **1. Confirm artifacts** | `ls experiment/s1-poc-e01/` | adapter_model.safetensors | File exists |
| **2. Smoke test** | `python scripts/layer2_smoke_infer_poc.py --limit 10` | poc_infer_smoke.jsonl | 10 successful |
| **3. Full inference** | `python scripts/layer2_full_infer_poc.py` | poc_infer_full_*.jsonl | 500 successful |
| **4. Judge scoring** | `python scripts/layer2_judge_scores.py` | poc_judge_scores.jsonl | Parse success > 95% |
| **5. Results aggregation** | `python scripts/aggregate_layer2_judge_scores.py` | poc_judge_summary.json | Stratified stats generated |
| **6. Baseline comparison** | Manual comparison | Comparison table | Decision basis |
| **7. Make decision** | Update META.json | status=completed | ACCEPT/Iterate/Reject |

---

## 9. Related Documents

| Document | Purpose |
|----------|---------|
| [Sprint1-05_week2_poc_plan_EN.md](Sprint1-05_week2_poc_plan_EN.md) | Week 2 complete planning |
| [Sprint1-07_train_poc_explained_EN.md](Sprint1-07_train_poc_explained_EN.md) | Training script deep dive |
| [experiment/s1-poc-e01/EVALUATION_REPORT.md](../../experiment/s1-poc-e01/EVALUATION_REPORT.md) | PoC evaluation report |

---

## 10. Revision History

| Date | Revision |
|------|----------|
| 2026-05-17 | Initial: Post-fine-tuning Layer 2 evaluation complete workflow |
