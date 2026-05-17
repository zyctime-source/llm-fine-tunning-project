# Sprint 1 Week 2 Plan: PoC Quick Closure

> **Type**: Personal Project Technical Memo  
> **Date**: 2026-05-17  
> **GitHub repo**: https://github.com/zyctime-source/llm-fine-tunning-project  
> **Main Reference**: [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) § "Week 2: PoC Quick Closure"  
> **Overview Index**: [Sprint1-00_tasks_intro_EN.md](Sprint1-00_tasks_intro_EN.md) §4 Week 2

---

## 1. Background and Scope

### 1.1 Why PoC?

Week 1 completed data freeze and baseline evaluation. Now we need to **verify the "data + training + evaluation" pipeline works end-to-end with minimal effort**. PoC (Proof of Concept) goals are NOT to produce a perfect model, but to:

1. Verify training scripts run successfully (no crashes, no OOM, loss decreases normally)
2. Verify LoRA weights can be exported, loaded, and used for inference
3. Verify fine-tuned model produces evaluable results on Layer 2
4. Accumulate configuration experience for Week 3 Stage 1 conservative training

### 1.2 Scope of This Document

**Core Tasks**:
- PoC training (small data, short epochs, quick validation)
- LoRA weight export and loading verification
- Post-PoC Layer 2 regression evaluation
- Accept/Iterate/Reject decision

**Out of Scope**:
- Not using full 13k dataset (that's Stage 1's task)
- Not pursuing optimal performance (that's iteration goal)
- No Stage 2 personalization

---

## 2. This Week's Goal (One Sentence)

**Complete an end-to-end LoRA fine-tuning with 1k samples, produce loadable LoRA weights, and verify the training pipeline works through Layer 2 quick evaluation.**

---

## 3. Time Budget (20h)

Assuming **5 working days × 4h**; if you only have 3 study days per week, combine "Day 4-5" into two 8h blocks.

| Day | Duration | Focus | Key Deliverable |
|-----|----------|-------|-----------------|
| D1 | 4h | Prepare PoC data subset (1k samples), setup training environment, confirm training scripts | `data/poc_v1.0_1k.jsonl` |
| D2 | 4h | Execute PoC training (1-3 epochs), monitor loss curve, handle exceptions | `s1-poc-e01/` directory, training logs |
| D3 | 4h | Export LoRA weights, verify loadable, run Layer 2 smoke test | `adapter_model.safetensors`, smoke test results |
| D4 | 4h | Execute full Layer 2 evaluation (500 samples), judge scoring | `s1-poc-e01-eval.jsonl`, judge results |
| D5 | 4h | Compare baseline scores, make Accept/Iterate/Reject decision, write weekly review | Decision conclusion, Week 3 input list |

---

## 4. Task Checklist

### 4.1 Preparation Phase (D1)

| Task | Description | Checkpoints |
|------|-------------|-------------|
| **Prepare PoC data subset** | Extract 1k samples from `v1.0` full data, maintain ratio (brainstorm_en: 400, brainstorm_cn: 400, general: 200) | Data files loadable, format correct |
| **Confirm training environment** | Install/verify training dependencies (TRL, Transformers, PEFT, etc.) | `import trl` runs without errors |
| **Create experiment directory** | Copy template, create `experiment/s1-poc-e01/` | META.json initialized |
| **Determine training config** | Conservative config: LoRA rank=8, alpha=16, lr=2e-4, epochs=1-3, batch_size=1/2 | Config written to META.json |

**PoC Data Ratio Recommendation**:

| Subset | Count | Source |
|--------|-------|--------|
| brainstorm_en | 400 | Sample from `brainstorm_vicuna_10k` |
| brainstorm_cn | 400 | Sample from Chinese translated subset |
| general | 200 | Sample from general capability data |
| **Total** | **1000** | — |

### 4.2 Training Phase (D2)

| Task | Description | Checkpoints |
|------|-------------|-------------|
| **Start training** | Run TRL SFTTrainer, fixed seed=42 | Training starts normally |
| **Monitor metrics** | Loss curve, learning rate changes, GPU memory usage | Loss decreases steadily, no NaN |
| **Exception handling** | Reduce batch_size on OOM, reduce lr on divergence | Record adjustment process |
| **Save checkpoints** | Save per epoch, final save LoRA weights | Weight files exist and readable |

**Key Configuration Reference** (Conservative Strategy):

```json
{
  "method": "LoRA",
  "rank": 8,
  "lora_alpha": 16,
  "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
  "learning_rate": 2e-4,
  "epochs": 1,
  "batch_size": 1,
  "gradient_accumulation_steps": 4,
  "warmup_steps": 50,
  "seed": 42
}
```

### 4.3 Validation Phase (D3)

| Task | Description | Checkpoints |
|------|-------------|-------------|
| **LoRA weight export** | Save adapter using PEFT | `adapter_model.safetensors` exists |
| **Loading verification** | Merge base + LoRA, verify inference works | `model.generate()` outputs normally |
| **Smoke test** | Layer 2 first 10 samples quick test | Output format correct, no garbled text |
| **META.json update** | Fill in training params, change status to `training_completed` | Fields complete |

### 4.4 Evaluation Phase (D4)

| Task | Description | Checkpoints |
|------|-------------|-------------|
| **Layer 2 full inference** | 500-sample regression set, greedy decoding | Results written to `results/` |
| **Judge scoring** | Use `qwen3.6-plus` judge model | Parse success rate > 95% |
| **Results aggregation** | Stratified overall mean statistics | Compare with baseline |

**Evaluation Command Reference** (Follow Week 1 protocol):

```shell
# Inference
python scripts/layer2_smoke_infer.py \
  --model-path experiment/s1-poc-e01/ \
  --out experiment/s1-poc-e01/results/poc_infer_xxx.jsonl

# Judge scoring
python scripts/layer2_judge_scores.py \
  --manifest data/eval/layer2/manifest_v0.jsonl \
  --infer-jsonl experiment/s1-poc-e01/results/poc_infer_xxx.jsonl \
  --out experiment/s1-poc-e01/results/poc_judge_scores.jsonl
```

### 4.5 Decision Phase (D5)

| Task | Description | Deliverable |
|------|-------------|-------------|
| **Score comparison** | PoC vs Week 1 baseline | Comparison table |
| **Red line check** | Whether P0/P1 triggered | Conclusion |
| **Make decision** | Accept / Iterate / Reject | Decision document |
| **Update META.json** | Fill in result scores, decision, parent experiment | `status=completed` |
| **Week 3 input** | List Stage 1 required dependencies | Input list |

---

## 5. Deliverables

### 5.1 Must Have

| Deliverable | Location | Description |
|-------------|----------|-------------|
| `s1-poc-e01` experiment directory | `experiment/s1-poc-e01/` | Contains README.md, META.json, LoRA weights |
| `s1-poc-e01-eval` evaluation results | `experiment/s1-poc-e01/results/` | Inference results + judge scoring |
| Decision document | `experiment/s1-poc-e01/README.md` §Conclusion | Accept/Iterate/Reject and reasoning |

### 5.2 Should Have

| Deliverable | Description |
|-------------|-------------|
| Training process screenshots/logs | Loss curve, learning rate changes |
| Failure sample list | Training anomalies, evaluation anomalies, low-score samples |
| zh_guard专项观察 | Chinese protection subset comparison with baseline |

---

## 6. Decision Outcomes (Accept / Iterate / Reject)

### 6.1 Accept (Pass, enter Week 3)

**Conditions** (all must be met):
- Training completed successfully, LoRA weights loadable
- Layer 2 inference runs, judge can score
- Core capabilities (core subset) don't degrade compared to baseline (fluctuation < 10%)
- No P0/P1 red lines triggered

**Action**: Mark as `accept`, update `META.json`, enter Week 3 Stage 1 conservative training.

### 6.2 Iterate (Needs iteration, run another round this week)

**Trigger Conditions** (any one):
- Training completed but loss curve abnormal (high fluctuation, plateau too early)
- Evaluation results show obvious degradation in any subset (decline > 15%)
- zh_guard significantly degraded (decline > 20%)
- Configuration issues discovered (e.g., learning rate too high/low)

**Actions**:
- Record root cause of issues
- Adjust configuration (e.g., lr, epoch, data ratio)
- Open new experiment `s1-poc-e02`, parent experiment points to `s1-poc-e01`
- Complete iteration within this week

### 6.3 Reject (Reject, trigger major adjustments)

**Trigger Conditions** (any one):
- Training repeatedly fails (OOM, NaN, crashes can't be resolved)
- LoRA weights can't be loaded or used for inference
- Comprehensive degradation (core layer decline > 30%)
- Fundamental issues with data recipe

**Actions**:
- Record failure reasons
- Evaluate whether needed: switch base model (activate Qwen backup), change data recipe, change training framework
- Compare with Week 1 baseline report, analyze root causes

---

## 7. Red Lines and Risks

### 7.1 This Week's Red Lines

| Red Line | Meaning | Action When Triggered |
|----------|---------|----------------------|
| P0 | Training can't complete (crash/NaN/OOM can't be resolved) | Reject, evaluate switching model or framework |
| P1 | LoRA weights can't be loaded or used for inference | Reject, check export and loading code |
| P2 | Core capabilities significantly degraded (> 20%) or zh_guard severely degraded (> 30%) | Iterate, adjust data ratio or training config |

### 7.2 Risks and Mitigation

| Risk Scenario | Trigger Condition | Mitigation Action |
|---------------|-----------------|-------------------|
| **Training repeatedly fails** | Same config fails > 2 times | Reduce variables (lower rank, reduce batch, freeze more layers) |
| **GPU time exceeds expectation** | Weekly GPU hours > 20h | Reduce epoch to 1, reduce data to 500 samples, prioritize evaluation |
| **Evaluation fluctuation too large** | Same model two evaluations differ > 15% | Increase rerun count, check if decoding params consistent |
| **zh_guard severely degraded** | Chinese protection questions mean < 60 | Immediately start Chinese data ratio adjustment experiment |

---

## 8. Connection with Week 1

### 8.1 Week 1 Inputs (Ready)

| Input | Location | Purpose |
|-------|----------|---------|
| Data recipe `v1.0` | `_docs/execution/s1-data-v1.0-spec_CN.md` | Sample 1k by ratio |
| Baseline evaluation report | `_docs/execution/s1-baseline-report_CN.md` | Comparison benchmark |
| Layer 2 question list | `data/eval/layer2/manifest_v0.jsonl` | Regression evaluation |
| Experiment metadata template | `experiment/_template/` | Create s1-poc-e01 |
| Baseline scores | `baseline-gemma4e2b-it-layer2-v0/META.json` | Comparison basis |

**Baseline Score Review** (for comparison):

| Subset | Overall Mean |
|--------|--------------|
| core | 93.35 |
| general | 81.85 |
| zh_guard | 77.94 |
| **All** | **85.67** |

### 8.2 Week 3 Outputs (Reserved Inputs)

| Output | Purpose |
|--------|---------|
| PoC decision conclusion | Whether Stage 1 launches, configuration recommendations |
| Training configuration experience | Optimal starting values for lr, epoch, batch, etc. |
| Data ratio recommendations | Whether to adjust Chinese/English ratio |
| Failure sample types | Issues to focus on in Stage 1 |

---

## 9. Related Documents Index

| Document | Purpose |
|----------|---------|
| [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) | Sprint 1 four-week main line |
| [Sprint1-00_tasks_intro_EN.md](Sprint1-00_tasks_intro_EN.md) | Sprint 1 task overview |
| [Sprint1-04_week1_done_summary_EN.md](Sprint1-04_week1_done_summary_EN.md) | Week 1 closure report (includes baseline scores) |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | Data recipe specification |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | Evaluation protocol and baseline scores |
| [_docs/shaping/8_train_iterate_CN.md](../shaping/8_train_iterate_CN.md) | Training strategy, experiment naming, reproducibility |
| [experiment/README.md](../../experiment/README.md) | Experiment directory conventions, training/evaluation environment |
| [experiment/_template/](../../experiment/_template/) | META.json template |

---

## 10. Revision History

| Date | Revision |
|------|----------|
| 2026-05-17 | Initial: Sprint 1 Week 2 PoC Plan (aligned with sprint-1-train.md Week 2) |
