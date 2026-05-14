# Sprint 1 Task Overview: End-to-End Fine-tuning Pipeline Delivery

> **Type**: Personal Project Technical Memo  
> **Date**: 2026-05-13  
> **GitHub repo**: https://github.com/zyctime-source/llm-fine-tunning-project  
> **Chinese Version**: [Sprint1-00_tasks_intro_CN.md](Sprint1-00_tasks_intro_CN.md)

---

## 1. Background

I have always been deeply interested in LLM fine-tuning. Through vibe coding, I aim to push a project from scratch to a production-ready Android application centered on LLM fine-tuning within 3–4 months, documenting the entire journey.

### 1.1 Project Context: AI Thinking Assistant on Your Phone

**Pain Point**: Inspiration strikes randomly, but traditional note-taking apps can only "store" rather than "think," and fail to connect ideas. Three months later, revisiting those notes, the original thought process is long forgotten.

**Solution**: Build an Android app where a single "quick capture" sentence undergoes on-device LLM-driven **questioning-divergence-convergence**, ultimately yielding a structured "inspiration card." For model selection, use **Gemma-4-E2B-IT** (4B-class) as the base, apply **LoRA fine-tuning** to align with the "brainstorming" rhythm, then quantize to INT4/INT8 to fit on-device, balancing privacy and cost.

**Key Understanding**: This is not a general-purpose chatbot, but a **structured thinking aid**—it must know how to ask follow-up questions, how to converge, and how to transform scattered dialogue into actionable cards.

### 1.2 What This Document Covers

[Sprint1-dataset_download_processing_EN.md](Sprint1-dataset_download_processing_EN.md) documents data preparation; [Sprint1-layer2-manifest_EN.md](Sprint1-layer2-manifest_EN.md) explains evaluation question bank generation; [Sprint1-03_baseline-gemma-layer2-infer_CN.md](Sprint1-03_baseline-gemma-layer2-infer_CN.md) covers baseline inference. This document organizes the complete **Sprint 1 (Month 1)** task list from a **project management perspective**: goal decomposition, four-week progress, deliverable definitions, pass criteria, and risk contingencies.

For the detailed training mainline, see [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md).

---

## 2. Sprint 1 Core Goals

Complete **Gemma-4-E2B** PoC validation and Stage 1 foundational fine-tuning closed-loop within 4 weeks, establishing a **minimum reproducible, evaluable, and rollback-capable** training workflow.

### 2.1 Time Investment

| Item | Value |
|------|-------|
| **Duration** | 4 weeks |
| **Estimated Effort** | ~80 hours (20 hours/week) |
| **Budget Recommendation** | Within 120-180 GPU hours, prioritize allocating 40-70 hours to this Sprint |

---

## 3. Task Priorities: Must / Should / Won't

### Must (Required)

- [ ] **Freeze Data Version `v1.0`**: Form data specification and traceability information  
  Deliverable: [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) (frozen ✓)
- [ ] **Complete 1 PoC + 1 Stage 1 Training**: Produce loadable LoRA weights
- [ ] **Run Layer 2 Regression Evaluation**: Form initial baseline vs. fine-tuning comparison report  
  Deliverable: [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md)
- [ ] **Solidify Experiment Naming and Lineage Recording**: Establish experiment ID rules (`s1-{type}-e{number}`) and parent-child血缘 tracking

### Should (Recommended)

- [ ] **Fill Chinese Protection Observation**: Early identification of Chinese degradation risk (zh_guard sub-layer small-sample validation)
- [ ] **Output Failure Case Inventory**: Reduce repeated pitfalls in next Sprint  
  Deliverable: `s1-train-e01-error-cases.jsonl` or similar structured inventory

### Won't (Explicitly Excluded)

- ❌ **Stage 2 Personalized Fine-tuning**: User personal style learning deferred to subsequent Sprints
- ❌ **Multi-model Parallel Mainlines**: Qwen only as risk backup, not parallel advancement in Sprint 1 (focus on single-point breakthrough with Gemma first)

---

## 4. Four-Week Progress Breakdown

### Week 1: Data and Baseline Preparation

**Goal**: Make data and evaluation infrastructure ready, base model can run Layer 2.

| Task | Deliverable/Reference |
|------|----------------------|
| Freeze `v1.0` data recipe | [s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) |
| Produce experiment metadata template | [experiment/README.md](../../experiment/README.md) `_template/` |
| Run base model baseline evaluation | [baseline-gemma4e2b-it-layer2-v0](../../experiment/baseline-gemma4e2b-it-layer2-v0/) |
| Layer 2 manifest generation | [Sprint1-layer2-manifest_EN.md](Sprint1-layer2-manifest_EN.md) |

**Key Deliverables**:
- `s1-data-v1.0-spec` (finalized)
- `s1-baseline-report` (skeleton established, fill with actual measurements after running 500 items)
- Experiment metadata template + baseline instance draft

---

### Week 2: PoC Rapid Closed-Loop

**Goal**: Verify the "data + training + evaluation" pipeline is runnable through the shortest path.

| Task | Description | Deliverable |
|------|-------------|-------------|
| PoC Training | Small data volume (e.g., 1k items), few epochs, rapid training script validation | `s1-poc-e01/` experiment directory |
| LoRA Weight Export | Ensure loadable, inferable | `adapter_model.safetensors` |
| Post-PoC Evaluation | Layer 2 comparison with baseline, output Accept/Iterate/Reject | `s1-poc-e01-eval.json` |

**Key Deliverables**:
- `s1-poc-e01` (experiment record)
- `s1-poc-e01-eval` (evaluation results and decision conclusion)

**Decision Exits**:
- **Accept**: PoC validation passed, enter Week 3 Stage 1 conservative training
- **Iterate**: Adjust data or configuration, re-run PoC within this week
- **Reject**: Trigger major rollback (e.g., switch model, change data recipe)

---

### Week 3: Stage 1 Conservative Training

**Goal**: Based on PoC conclusions, complete one conservative but full Stage 1 training.

| Task | Description | Checkpoint |
|------|-------------|------------|
| Conservative Training Main Run | Use `v1.0` full 13k data (or 12k skipping seeds), standard LoRA configuration | Loss curve stable, no NaN |
| Failure Case Recording | Simultaneously record abnormal inputs and model outputs | Structured per Sprint memo format |
| Chinese Protection Validation | zh_guard sub-layer rapid regression, confirm Chinese not degraded | Compare with baseline, fluctuation < 10% |

**Key Deliverables**:
- `s1-train-e01` (experiment record)
- `s1-train-e01-error-cases` (issue inventory)

---

### Week 4: Convergence and Gate1 Review

**Goal**: Solidify achievements, complete Sprint retrospective, pass Gate1.

| Task | Description | Deliverable |
|------|-------------|-------------|
| Stage 1 Comparison Report | Baseline vs. post-fine-tuning, layered summary + redline conclusions | Populate s1-baseline-report §5-§6 |
| Lineage Tree Record | Visualize experiment血缘: baseline → PoC → Stage 1 | `experiment/lineage-tree.md` or tool diagram |
| Gate1 Review | Self-check whether pass criteria are met | `s1-gate1-review.md` |
| Sprint Retrospective | Goal achievement, blocking root causes, next Sprint plan | `s1-retro.md` |

**Key Deliverables**:
- `s1-gate1-review` (review report)
- `s1-retro` (Sprint retrospective)

---

## 5. Gate1 Pass Criteria

Quality threshold at Sprint 1 conclusion; all four must be satisfied simultaneously:

| Criterion | Specific Meaning | Verification Method |
|-----------|----------------|---------------------|
| **Training Reproducible** | Same configuration repeated runs yield acceptably similar results | Fixed seed, same data, compare two training loss curves |
| **Evaluation Re-runnable** | Layer 2 can stably run and output structured results | Same manifest, same protocol, two inference result SHAs identical |
| **Model Loadable** | LoRA weights can be loaded by edge-side/test inference pipeline | `layer2_smoke_infer.py` load checkpoint validation |
| **Capability Not Degraded** | Core capability reaches "usable," not triggering P0/P1 redlines | See [9_eval_qa_EN.md](../shaping/9_eval_qa_EN.md) §9.3 |

---

## 6. Risks and Stop-Loss Contingencies

| Risk Scenario | Trigger Condition | Stop-Loss Action |
|---------------|-------------------|------------------|
| **Significant Chinese Quality Degradation** | Chinese protection questions unavailable for two consecutive rounds (zh_guard average < 2 or P1 triggered) | Immediately initiate Qwen backup assessment; pause Gemma training, evaluate switching cost |
| **Training Instability** | Repeated failures > 2 times that week (loss divergence, OOM, NaN) | Narrow variable scope (e.g., reduce data volume, reduce rank, freeze more layers); stop Should tasks, retain only Must |
| **Cost Over Expectation** | GPU hours approaching monthly ceiling of 70h | Retain only Must tasks; interrupt non-critical experiments; consider CPU inference validation alternative |
| **Data Gap** | Self-built seed 500 items never completed | Accept `v1.0-skip-seed` approach, assess seed supplementation necessity after Gate1 |

---

## 7. Sprint Retrospective Template

At Sprint 1 conclusion (last 1-2 days of Week 4), output retrospective per following structure:

```markdown
## Sprint 1 Retrospective (s1-retro)

### Goal Achievement
- Achieved / Partially Achieved / Not Achieved
- Notes: ________________________________

### Key Metrics
- Core Capability (brainstorm + summary): Baseline ____ → Post-fine-tuning ____ (Target: not degraded)
- Chinese Protection (zh_guard): Baseline ____ → Post-fine-tuning ____ (Target: not degraded)
- Training Stability: Success ____ times / Failure ____ times

### Major Blockers and Root Causes
1. ________________ (Root cause: ______________)
2. ________________ (Root cause: ______________)

### Next Sprint Adjustments
- Retain (Continue):
  - ________________
- Remove (No longer do):
  - ________________
- Add (New discoveries):
  - ________________
```

---

## 8. Related Document Index

| Document | Purpose |
|----------|---------|
| [Sprint1-dataset_download_processing_EN.md](Sprint1-dataset_download_processing_EN.md) | Week 1 data preparation details |
| [Sprint1-layer2-manifest_EN.md](Sprint1-layer2-manifest_EN.md) | Week 1 evaluation question bank generation |
| [Sprint1-03_baseline-gemma-layer2-infer_CN.md](Sprint1-03_baseline-gemma-layer2-infer_CN.md) | Week 1 baseline inference execution |
| [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) | Detailed training mainline description |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | Data recipe frozen specification |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | Evaluation protocol and report skeleton |
| [_docs/shaping/9_eval_qa_EN.md](../shaping/9_eval_qa_EN.md) | Redline types and evaluation dimensions |

---

## 9. Revision History

| Date | Revision |
|------|----------|
| 2026-05-14 | Initial version: Integrated sprint-1-train.md mainline, added task overview perspective, four-week progress table, risk contingencies, and retrospective template |
