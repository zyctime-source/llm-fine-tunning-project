# Fine-tuning Edge-side LLM App Development Log: 2026-05-13, Layer 2 Regression Validation Set Manifest

> **Type**: Personal Project Technical Memo  
> **Date**: 2026-05-13  
> **GitHub repo**: https://github.com/zyctime-source/llm-fine-tunning-project  
> **Chinese Version**: [Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md)

---

## 1. Background

I have always been deeply interested in LLM fine-tuning. Through vibe coding, I aim to push a project from scratch to a production-ready Android application centered on LLM fine-tuning within 3–4 months, documenting the entire journey.

### 1.1 Project Context: AI Thinking Assistant on Your Phone

**Pain Point**: Inspiration strikes randomly, but traditional note-taking apps can only "store" rather than "think," and fail to connect ideas. Three months later, revisiting those notes, the original thought process is long forgotten.

**Solution**: Build an Android app where a single "quick capture" sentence undergoes on-device LLM-driven **questioning-divergence-convergence**, ultimately yielding a structured "inspiration card." For model selection, use **Gemma-4-E2B-IT** (4B-class) as the base, apply **LoRA fine-tuning** to align with the "brainstorming" rhythm, then quantize to INT4/INT8 to fit on-device, balancing privacy and cost.

**Key Understanding**: This is not a general-purpose chatbot, but a **structured thinking aid**—it must know how to ask follow-up questions, how to converge, and how to transform scattered dialogue into actionable cards.

### 1.2 What This Document Covers

Data recipes and training validation sets (general 1k + brainstorm 3k, etc.) are documented in [Sprint1-dataset_download_processing_EN.md](Sprint1-dataset_download_processing_EN.md) and [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md).

This memo focuses on the **evaluation phase**: how to translate the "~500 items, three-tier" Layer 2 goal from the shaping document into a **version-controlled, reproducible manifest (question bank)** within the repository, and its alignment with deliverables registered in the **Sprint 1 Baseline Report**.

Design rationale: see [_docs/shaping/9_eval_qa_EN.md](../shaping/9_eval_qa_EN.md) §9.1.3; implementation details: see [_docs/eval/layer2/README.md](../eval/layer2/README.md); baseline protocol: see [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) §0/§3.

---

## 2. What Is a Manifest

**A manifest (question bank) is a fixed list of test questions.**

In an LLM fine-tuning project, we need to repeatedly test model performance. Without a fixed question bank, random sampling for each test makes it impossible to determine whether model improvements reflect genuine capability gains or simply easier questions.

The manifest discussed here specifically refers to the **Layer 2 Regression Validation Set**:
- **File format**: `data/eval/layer2/manifest_v0.jsonl`, one JSON record per line
- **Contents**: 500 fixed test questions, divided into three tiers (core 200 items, general 200 items, zh_guard 100 items)
- **Version**: Currently `layer2-v0`; version bumps required for changes

Analogy: Just as students need fixed exam papers rather than randomly selecting questions from textbooks each time, a manifest serves as the "exam paper" for fine-tuning calibration.

---

## 3. Why a Manifest Is Needed

Rather than using raw data files (raw JSONL) directly, we use a manifest for four core reasons:

### 3.1 Fixed Question Bank Ensures Comparability
The same `layer2_id` must remain consistent across different experiments and checkpoints. Random sampling introduces "question difficulty variance" noise, making it impossible to distinguish between model improvement and easier questions.

### 3.2 Traceability for Auditing
Each record retains `source_local_path`, `source_line_1based`, and `source_sample_id`, enabling precise location of the original data source from Hub or local snapshots. Issues can be traced back to their origin.

### 3.3 Alignment with Shaping Layering
The `stratum` field in the manifest marks core/general/zh_guard tiers, allowing baseline report §5 to group and summarize directly by sub-layer without re-filtering.

### 3.4 Distinction from Training Validation Sets
Training validation sets (`general_mixed_validation.jsonl` and brainstorm validation sets, ~4k items total) are **in-training hold-outs** for early stopping and hyperparameter tuning.

Layer 2 manifest (~500 items) is a **post-training regression test** for high-frequency, low-cost detection of "whether the model has been trained off-course." They serve different purposes and must not be conflated.

### 3.5 Three-Tier Evaluation Architecture (Layer 1/2/3)

Beyond the **Layer 2** focus of this document, the shaping document defines two additional evaluation tiers, forming a **pyramid structure**:

| Tier | Scale | Core Purpose | Usage Timing | Cost & Frequency |
|------|-------|--------------|--------------|------------------|
| **Layer 1**<br>Capability Probe | ~4,000+ items | Explore model capability boundaries<br>Comprehensive horizontal comparison | Baseline at PoC phase<br>Deep analysis after key Stage 1 experiments | High cost<br>Low frequency (stage milestones) |
| **Layer 2**<br>Regression Validation | ~500 items<br>(focus of this doc) | Detect capability degradation<br>Prevent "training off-course" | **After every experiment**<br>automatic run | Controllable cost<br>High frequency (experiment iteration) |
| **Layer 3**<br>Production Acceptance | ~100 items | Manual walkthrough confirmation<br>"Product usable" perception | Before Stage 1 ends<br>Final gate before launch | High manual cost<br>Very rare (milestones) |

**Analogy**:
- **Layer 1** is like a "comprehensive physical": full checkup at project launch to understand all body indicators
- **Layer 2** is like "daily temperature": quick self-test during training iterations, immediate stop and adjustment if anomalies detected
- **Layer 3** is like an "employment physical": manual review before launch to ensure product-level usability

The manifest in this document precisely supports the **Layer 2 "daily temperature"** mechanism—500 fixed questions, sufficient to cover core/general/Chinese three-tier capabilities, yet not so large as to prevent high-frequency execution.

---

## 4. Current Version and File Locations (layer2-v0)

| Item | Value |
|------|-------|
| **Manifest Version** | `layer2-v0` (written to `manifest_version` in `manifest_meta.json`) |
| **Question Bank File** | `data/eval/layer2/manifest_v0.jsonl` (total **500** lines, one JSON per line) |
| **Metadata File** | `data/eval/layer2/manifest_meta.json` (contains counts, per-sub-layer seeds, source paths, `proxy_notes`) |
| **Generation Script** | `scripts/build_layer2_manifest.py` (uses only stdlib, no Hugging Face `datasets` dependency) |

**Alignment with Baseline Report**: s1-baseline-report §0 table "Layer 2 question bank manifest" points to the above paths; §3 "Actually used in this report" table's version, path, count, and sampling rules align with this document.

---

## 5. Fields in the Manifest

See [_docs/eval/layer2/README.md](../eval/layer2/README.md) "Fields per record" for details. Core field summary:

| Field | Description |
|-------|-------------|
| `layer2_id` | Stable primary key, e.g., `L2-core-00001` |
| `stratum` | Sub-layer marker: `core` / `general` / `zh_guard` |
| `source_hub_repo` / `source_local_path` / `source_line_1based` / `source_sample_id` | Traceability info, locating original data source |
| `messages` | OpenAI-style multi-turn dialogue, directly fed to Gemma chat template during evaluation |
| `content_sha256` | Hash of normalized `messages`, preventing silent data tampering |

---

## 6. Sampling Rules (v0) and Gaps from Ideal Targets

| Sub-layer | Scale | Local Material (v0) | Random Seed (default) |
|-----------|-------|---------------------|----------------------|
| **core** | 200 | Sampling without replacement from full `brainstorm_vicuna_10k_zh.jsonl` | 42 |
| **general** | 200 | Sampling without replacement from general mixed JSONL where `lang=="en"` | 43 |
| **zh_guard** | 100 | Same as above, where `lang=="zh"` | 44 |

**General Mixed Source Path**: Script **prioritizes** reading `general_mixed_train.jsonl`, falls back to `general_mixed.jsonl` if not present. `paths.general_mixed_source` in `manifest_meta.json` records the **actually used file at generation time**.

**Note**: Switching from legacy full text (~4k lines) to train-only subset (3k lines) changes the sampling pool; even with the same seed, question content may differ. In such cases, retain the old manifest for comparison, or bump version (e.g., `layer2-v0.1`) and re-run baseline.

**Ideal vs. Reality Gaps**:
- Ideal general sub-layer source in shaping is **X-AlpacaEval**; v0 uses `tatsu-lab/alpaca` English lines as **proxy**
- Ideal Chinese sub-layer source in shaping is **CMT-Eval**; v0 uses `evol-instruct-chinese` lines as **proxy**

Proxy notes are written to `proxy_notes` in `manifest_meta.json`. Bump manifest version when upgrading to real data sources.

---

## 7. How to Generate or Replay

**Prerequisites**:
- `data/processed/brainstorm_vicuna_10k_zh.jsonl` must exist
- `general_mixed_train.jsonl` or `general_mixed.jsonl` must exist

If missing, the script will error and prompt to run `python -m data_pipeline download` first.

**Generation Command**:

```bash
python scripts/build_layer2_manifest.py

# Explicitly specify seeds for documentation and CI alignment:
python scripts/build_layer2_manifest.py --seed-core 42 --seed-general 43 --seed-zh 44
```

Output overwrites `data/eval/layer2/manifest_v0.jsonl` and `manifest_meta.json`.

**Version Bump Rules**:
- Copy-only changes, no question meaning or order changes: no bump, keep `layer2-v0`
- Source change (e.g., from `general_mixed.jsonl` to `general_mixed_train.jsonl`): recommend bump to `layer2-v0.1` or `layer2-v1`

---

## 8. When the Manifest Is Used

The manifest is used at multiple stages of the **evaluation pipeline**:

### 8.1 Smoke Testing (Development Phase)
`scripts/layer2_smoke_infer.py` reads a few records from the manifest (e.g., 3 items), verifying:
- Gemma model loads correctly
- Chat template correctly processes the `messages` field
- Manifest field format is correct

Deliverable paths are recorded in [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json).

### 8.2 Baseline Evaluation (Sprint 1)
Run all 500 items under fixed **eval-protocol-v0** (see s1-baseline-report §4):
1. Generate answers with Gemma (`temperature=0`, fixed seed)
2. Optional: scoring with judge model (e.g., `qwen3.6-plus`)
3. Summarize results by sub-layer, populate baseline report §5

### 8.3 Experiment Comparison (PoC / Stage 1)
After each fine-tuning experiment, run tests with the **same manifest version** and **same evaluation protocol**, comparing against baseline:
- Is core capability degraded?
- Is general capability maintained?
- Is Chinese expression normal?

**Key Principle**: When comparing experiments, only model weights and training-related variables may change; manifest and evaluation protocol must remain consistent, otherwise results are incomparable.

### 8.4 Experiment Record-Keeping
Recommend documenting in each experiment's `META.json`:
```json
{
  "manifest_version": "layer2-v0",
  "manifest_path": "data/eval/layer2/manifest_v0.jsonl",
  "eval_protocol": "eval-protocol-v0"
}
```

This prevents confusion when future experiments use `layer2-v1`.

---

## 9. Related Document Index

| Document | Purpose |
|----------|---------|
| [_docs/shaping/9_eval_qa_EN.md](../shaping/9_eval_qa_EN.md) | Layer 1/2/3 tiered design, redline types; §9.1.3 for Layer 2 target scale and principles |
| [_docs/eval/layer2/README.md](../eval/layer2/README.md) | Manifest field details, sampling logic, proxy data source notes, distinction from training validation sets |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | Baseline report skeleton; §3 binds manifest and evaluation protocol |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | Training data and training-oriented validation set specs (parallel to Layer 2, do not conflate) |
| [Sprint1-dataset_download_processing_EN.md](Sprint1-dataset_download_processing_EN.md) | Same-date data preparation memo (download, translation, export-brainstorm-val) |

---

## 10. Revision History

| Date | Revision |
|------|----------|
| 2026-05-14 | Initial version: aligned with `layer2-v0`, `s1-baseline-report` §0/§3, and eval README |
| 2026-05-14 | Optimization: Added standalone "What is a manifest" section, reorganized "Why needed" into 3.1-3.4 bullet points, expanded "When used" into 8.1-8.4 full-flow description |
