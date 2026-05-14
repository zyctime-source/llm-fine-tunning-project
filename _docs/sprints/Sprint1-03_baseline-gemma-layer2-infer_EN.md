# Fine-tuning Edge-side LLM App Development Log: 2026-05-13, Base Model (Gemma) Selection, Download, and Layer 2 Inference

> **Type**: Personal Project Technical Memo  
> **Date**: 2026-05-13  
> **GitHub repo**: https://github.com/zyctime-source/llm-fine-tunning-project  
> **Chinese Version**: [Sprint1-03_baseline-gemma-layer2-infer_CN.md](Sprint1-03_baseline-gemma-layer2-infer_CN.md)

---

## 1. Background

I have always been deeply interested in LLM fine-tuning. Through vibe coding, I aim to push a project from scratch to a production-ready Android application centered on LLM fine-tuning within 3–4 months, documenting the entire journey.

### 1.1 Project Context: AI Thinking Assistant on Your Phone

**Pain Point**: Inspiration strikes randomly, but traditional note-taking apps can only "store" rather than "think," and fail to connect ideas. Three months later, revisiting those notes, the original thought process is long forgotten.

**Solution**: Build an Android app where a single "quick capture" sentence undergoes on-device LLM-driven **questioning-divergence-convergence**, ultimately yielding a structured "inspiration card." For model selection, use **Gemma-4-E2B-IT** (4B-class) as the base, apply **LoRA fine-tuning** to align with the "brainstorming" rhythm, then quantize to INT4/INT8 to fit on-device, balancing privacy and cost.

**Key Understanding**: This is not a general-purpose chatbot, but a **structured thinking aid**—it must know how to ask follow-up questions, how to converge, and how to transform scattered dialogue into actionable cards.

### 1.2 What This Document Covers

[Sprint1-layer2-manifest_EN.md](Sprint1-layer2-manifest_EN.md) has already explained **Layer 2 manifest** generation and versioning. This document continues the same timeline, recording:

- **Base model** positioning in shaping  
- **Why Sprint 1 selects Gemma-4-E2B-IT** as the baseline  
- **How to download models from Hugging Face Hub** to local  
- **Evaluation-specific environment** setup and smoke testing  
- **How to use `layer2_smoke_infer.py`** to run through the manifest item-by-item according to **`eval-protocol-v0`** (including full 500 items and resume-from-checkpoint mechanism)

Reference documents:
- Authoritative protocol and report skeleton: see [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md)  
- Experiment directory description: see [experiment/baseline-gemma4e2b-it-layer2-v0/README.md](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md)  
- Edge-side model candidates and licenses: see [_docs/shaping/6_model_strategy_EN.md](../shaping/6_model_strategy_EN.md)

---

## 2. Base Model Selection: Gemma-4-E2B-IT

### 2.1 Candidate Models in Shaping

[_docs/shaping/6_model_strategy_EN.md](../shaping/6_model_strategy_EN.md) §6.1 lists **Gemma-4-E2B-IT**, **Gemma-4-E4B-IT**, **Qwen3.5-2B**, etc. as P0 observation targets. The **2B-class showdown** (Gemma vs Qwen) is the core comparison focus during the PoC phase. Licenses and edge-cloud division are detailed in §6.1.3 and §6.3 of the same document.

### 2.2 Why Sprint 1 Baseline Selects Gemma-4-E2B-IT

The baseline experiment ID for **Sprint 1 Week 1** in this repository is **`baseline-gemma4e2b-it-layer2-v0`** (evaluation only, no training). Reasons for selecting Gemma-4-E2B-IT:

- **Product narrative consistency**: First establish a **Layer 2 regression baseline** on the **Gemma-IT** series, providing a fixed reference point for subsequent fine-tuning and PoC comparison.  
- **Evaluation protocol consistency**: [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) §2 and §4 specify the model under test as **`google/gemma-4-E2B-it`**, with decoding adopting **`eval-protocol-v0`** (greedy decoding, `max_new_tokens` and other parameters per §4.0).  
- **Manifest alignment**: `evaluation.manifest_version` in `META.json` is **`layer2-v0`**, and the inference script defaults to reading `data/eval/layer2/manifest_v0.jsonl`.

**About naming**: The Hub repository name is `gemma-4-E2B-it` (2B parameter instruction-tuned model). The "4B-class" mentioned in shaping documents refers to higher tiers like E4B in the product line, **not conflicting with this baseline repo_id**—use Hub `repo_id` and `META.json` as authoritative sources.

### 2.3 2B-Class Candidates: Why Prioritize Gemma (Instead of Qwen)

The shaping document explicitly lists **Gemma-4-E2B-IT** and **Qwen3.5-2B** as parallel **P0 observation targets**, noting that the **2B-class showdown** is the core comparison focus of the PoC phase. Given this, why does Sprint 1 baseline lock in Gemma first?

**Current Decision Logic (Sprint 1 Week 1)**:

| Factor | Gemma-4-E2B-IT | Qwen3.5-2B | Selection Rationale for This Run |
|--------|----------------|------------|----------------------------------|
| **Release Date** | 2026-04 | 2026-03 | Gemma is newer, validate new architecture first |
| **Edge Optimization** | Purpose-built for edge devices (Any-to-Any architecture) | General multimodal | Aligns with "edge-first" product narrative |
| **License** | Google custom license (✅ commercial use) | Apache 2.0 (most permissive) | Gemma license satisfies commercial use; Qwen license more permissive, reserved as PoC backup |
| **Chinese Capability** | Needs validation | Native optimization | Sprint 1 prioritizes full pipeline validation; Chinese protection sub-layer (zh_guard) provides initial assessment |
| **Tech Stack** | Transformers official examples comprehensive | Equally comprehensive | Both easily integrable; pick one to establish pipeline |

**Key Understanding**:
- **Not excluding Qwen**: Qwen3.5-2B remains a **core comparison target for the PoC phase**, to be established in parallel baselines or direct comparison experiments in subsequent Sprints.
- **Prioritize running through one**: Sprint 1's primary goal is establishing an **end-to-end reproducible evaluation pipeline** (manifest → download → smoke → full run → baseline report). Running through the full pipeline on one model is more valuable than partially running two simultaneously.
- **License tradeoff**: Gemma's Google custom license allows commercial use; though not as permissive as Apache 2.0, it satisfies current stage requirements. If stricter licensing requirements emerge later, switching to Qwen is always an option.

---

## 3. Model Download and Version Freezing

### 3.1 First-Time Model Weight Download

The script uses `from_pretrained("google/gemma-4-E2B-it")` from the `transformers` library. **First run** will download `safetensors` and other files from Hugging Face Hub to local cache (~**10GB+**), with duration depending on network bandwidth and disk speed.

Python code snippet:

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "google/gemma-4-E2B-it"

# First execution automatically downloads weights to ~/.cache/huggingface/hub/
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",      # Auto-assign GPU/CPU
    torch_dtype="auto",     # Auto-select BF16/FP32
)

print(f"Model loaded: {model_id}")
print(f"Parameter count: {sum(p.numel() for p in model.parameters()) / 1e9:.2f}B")
```

**Configuration recommendation**: Configure **`HF_TOKEN`** in the `.env` file at repository root (Read permission sufficient) to avoid anonymous download rate limits.

```bash
# .env
HF_TOKEN=hf_your_token_here
```

For domestic mirror configuration, see [experiment/README.md](../../experiment/README.md) "Hugging Face: Login and Domestic Download Acceleration" section.

### 3.2 Freezing `revision` (Git Commit)

Baseline report §2 requires long-term recording of **`revision` / `commit`** to prevent reproduction failure from Hub `main` branch drift. Use **`base_model.revision`** in experiment directory **[experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json)** as the **single source of truth** (current example value: `b324173c7d5721c2baba7f3b17b3b9b3d34ab1e9`, consistent with `snapshots/<revision>` directory name in local HF cache).

Windows users can read this directory name from the cache directory as revision. When finalizing the baseline report, populate the same string into **s1-baseline-report_CN.md §2** table.

---

## 4. Evaluation Environment (Separate from Data Pipeline)

- Data download/translation uses [requirements-data.txt](../../requirements-data.txt)  
- **Layer 2 inference and smoke testing** uses [requirements-eval.txt](../../requirements-eval.txt)

Recommend using an independent virtual environment (e.g., Conda `llm-eval`), reasons detailed in [experiment/README.md](../../experiment/README.md) "Layer 2 Inference / Smoke Testing" section: different dependency stacks, NumPy major version differences, and different upgrade cadence from the data side.

**Basic installation steps**:

```bash
cd /path/to/llm-fine-tunning-project
conda activate llm-eval   # or source .venv-eval/bin/activate
pip install -r requirements-eval.txt
```

---

## 5. Smoke Testing (Rapid Validation, Not Full Run)

Goal: Without loading all **500 items**, quickly validate:
- Manifest field format is correct  
- `apply_chat_template` works properly  
- Gemma model weights are loadable  
- GPU/CPU inference paths are functional

### 5.1 Prompt-Only Validation (No Model Load)

```bash
python scripts/layer2_smoke_infer.py --dry-run --limit 5
```

### 5.2 Small-Batch Actual Inference (Example: 3 items, short output)

```bash
python scripts/layer2_smoke_infer.py --limit 3 --max-new-tokens 128
```

Default output path is **`experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_<UTC timestamp>.jsonl`**. Populate **`results.raw_outputs_dir`** and **`results.smoke_infer_jsonl`** into `META.json` (see [baseline README](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md) "Recorded Smoke Deliverables").

**Script behavior key points** (consistent with s1-baseline-report §4):
- Uses **greedy decoding** (`do_sample=False`)  
- If manifest ends with reference **assistant** turn, it will be **stripped first** before generation, avoiding mixing ground truth into the prompt

Implementation details in [scripts/layer2_smoke_infer.py](../../scripts/layer2_smoke_infer.py) top description and `messages_for_generation` function.

---

## 6. Full Inference: Item-by-Item Through Manifest

### 6.1 Parameters Aligned with `eval-protocol-v0`

Full Layer 2 main run parameters should match **s1-baseline-report §4.0**:

- **`--limit 500`**: Consistent with total count in `manifest_v0.jsonl` (or adjust subset as needed)  
- **`--max-new-tokens 2048`**: Protocol main value; smoke testing can use smaller values to save time  
- **Decoding method**: Fixed to greedy decoding in script, **do not** modify `temperature` for sampling comparison (if modification needed, bump `eval-protocol` version)

### 6.2 Real-Time Write and Resume from Checkpoint

The script currently supports the following features:

- **Real-time write**: Each generation immediately appends to JSONL with `flush`, no data loss on interruption  
- **Resume from checkpoint (`--resume`)**: Automatically skips based on **`layer2_id`** already present in output file, suitable for splitting long tasks across multiple executions

**Usage example** (full run + resume requires explicit **`--out`** pointing to existing file):

```bash
# First run, specify fixed output file
python scripts/layer2_smoke_infer.py --limit 500 --max-new-tokens 2048 --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_infer_full.jsonl

# Resume after interruption, using same output path
python scripts/layer2_smoke_infer.py --limit 500 --max-new-tokens 2048 --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_infer_full.jsonl --resume
```

**Note**: Without `--out`, each run generates a **new** timestamped file; for resume functionality, **must** use fixed `--out` and `--resume` parameters together.

### 6.3 Post-Run Backfill

After completing full inference, perform the following steps:

1. Write full JSONL path into **`META.json`** `results` field (or extended convention fields), and populate "Raw Model Outputs" path in **s1-baseline-report §7**  
2. (Optional) Per §4.1, integrate **judge** `qwen3.6-plus` for scoring  
3. Populate layered summary and redline conclusions into **§5–§6**, and synchronize `status` in **`META.json`** with report status as part of finalization workflow (see baseline README "To-Do" section)

---

## 7. Related Document Index

| Document | Purpose |
|----------|---------|
| [_docs/shaping/6_model_strategy_EN.md](../shaping/6_model_strategy_EN.md) | Edge-side candidate models, licenses, fine-tuning phase concepts |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | Model under test table, Layer 2 definition, `eval-protocol-v0`, judges, and report structure |
| [experiment/baseline-gemma4e2b-it-layer2-v0/README.md](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md) | This experiment directory conventions, installation and smoke steps, to-do list |
| [experiment/README.md](../../experiment/README.md) | Evaluation venv, HF login and mirror configuration |
| [Sprint1-layer2-manifest_EN.md](Sprint1-layer2-manifest_EN.md) | Manifest generation, fields and layer meanings |
| [_docs/eval/layer2/README.md](../eval/layer2/README.md) | Manifest paths and proxy data source notes |

---

## 8. Revision History

| Date | Revision |
|------|----------|
| 2026-05-14 | Initial version: Connects shaping selection, Hub download and revision, `requirements-eval`, smoke and full manifest inference (including `--resume` / `--out`) |
| 2026-05-14 | Language optimization: Simplified long sentences, unified terminology, clarified naming relationships, optimized paragraph structure |
| 2026-05-14 | §2.3 Added "2B-Class Candidates: Why Prioritize Gemma (Instead of Qwen)", explaining selection logic and PoC phase comparison plan |
| 2026-05-14 | §3.1 Added model download code snippet (Python `from_pretrained` method) |
