# Sprint 1 Baseline Evaluation Report: `s1-baseline-report`

| Attribute | Value |
|-----------|-------|
| **Report ID** | `s1-baseline-report` |
| **Document Status** | **Finalized (values filled, 2026-05-17)** — Consistent with `baseline-gemma4e2b-it-layer2-v0` full 500 inference + `qwen3.6-plus` judge |
| **Corresponding Experiment ID (recommended)** | `baseline-gemma4e2b-it-layer2-v0` (metadata directory: [experiment/baseline-gemma4e2b-it-layer2-v0](../experiment/bemma4e2b-it-layer2-v0/)) |
| **Data Recipe** | [s1-data-v1.0-spec_EN.md](s1-data-v1.0-spec_EN.md) (currently `v1.0-skip-seed`) |
| **Evaluation Stratification Basis** | [_docs/shaping/9_eval_qa_EN.md](../shaping/9_eval_qa_EN.md) §9.1.3 (Layer 2 regression validation set) |
| **Evaluation Protocol** | `eval-protocol-v0` (see **§4**; Gemma greedy + judge `qwen3.6-plus`) |

---

## 0. Document Status and To-Do

| Step | Status | Description |
|------|--------|-------------|
| Layer 2 manifest (~500 items, with stratum labels) | ☑ Completed (`layer2-v0`) | Artifacts: `data/eval/layer2/manifest_v0.jsonl` + `manifest_meta.json`; see [_docs/eval/layer2/README.md](../eval/layer2/README.md) |
| Inference protocol (template, temperature, max tokens, system prompt) | ☑ Frozen | **§4 `eval-protocol-v0`** (2026-05-12); version bump required for changes, see §4.3 |
| Base model loadable smoke test | ☑ Passed (small sample) | `layer2_smoke_infer` 3 items, `max_new_tokens=128`; path in [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) → `results.smoke_infer_*` |
| Full Layer 2 500 inference + (optional) judge scoring | ☑ Completed | Raw output: `experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl` (see `META.json` → `results.layer2_infer_jsonl`); judge: `layer2_judge_scores.jsonl`; summary: `layer2_judge_summary.json` |
| Stratified summary table + redline conclusions | ☑ Filled | **§5–§6** (means from `layer2_judge_summary.json`; standard deviation not computed by summary script, marked "—") |
| Update report status to "Finalized" | ☑ Completed | Aligned with `META.json` `status=completed` |

---

## 1. Executive Summary

- **Base Model**: **[google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it)**; Hub **`revision`** frozen to **`b324173c7d5721c2baba7f3b17b3b9b3d34ab1e9`** (see §2 and experiment [META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json)).
- **Evaluation Set**: Layer 2 regression set **500** items (`layer2-v0`); strata **core 200** / **general 200** / **zh_guard 100**.
- **Decoding and Length**: `eval-protocol-v0` — greedy decoding, `max_new_tokens=2048` (see §4.0).
- **Judge**: `qwen3.6-plus` (DashScope OpenAI-compatible API, `temperature=0.2`); **500 / 500** items successfully parsed (`judge_parse_ok=true`), per-item see `layer2_judge_scores.jsonl`.
- **Stratified `overall` means (1–100)**: **core 93.35**; **general 81.85**; **zh_guard 77.94**; all valid samples **85.67**. Detailed dimension means/medians in `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json`.
- **One-line Conclusion**: Core brainstorming stratum performs strongly; general instruction block and Chinese protection stratum significantly below core, **no P0/P1 evidentiary redline triggered**, Chinese scenario marked as **P2 experience warning** (see §6).
- **Implication for Week 2 PoC**: Subsequent fine-tuning comparisons must fix **same manifest version**, **same §4 protocol**, same judge configuration, comparing **overall and per-dimension** changes on §5 stratum table, especially monitoring **zh_guard** improvement.

---

## 2. Model Under Test

| Item | Value |
|------|-------|
| **Display Name** | Gemma 4 E2B IT (instruction-tuned; Sprint and shaping call it **Gemma-4-E2B-IT**) |
| **Hub Page** | [https://huggingface.co/google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it) |
| **Hub `repo_id`** | `google/gemma-4-E2B-it` |
| **`revision` / `commit`** | **`b324173c7d5721c2baba7f3b17b3b9b3d34ab1e9`** (consistent with local HF `snapshots/<revision>` and [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json)) |
| **License** | Apache 2.0 (per model card) |
| **Precision / Device** | Recommend **`dtype="auto"`** or **BF16** (consistent with `safetensors` weights); device: `CUDA` / `CPU` (fill in: `___________`) |
| **Loading Method (Official Text Multi-turn)** | `transformers`: `AutoProcessor` + **`AutoModelForCausalLM`** + `device_map="auto"` (see model card *Getting Started*; **Layer2 pure-text evaluation** prioritizes this path) |

**Note**: Model card `AutoProcessor` brings multimodal submodules (may need extra `torchvision` / `Pillow` deps). This repository **Layer 2 text smoke/batch scripts** (`scripts/layer2_smoke_infer.py`) reduce env dependencies by using **`AutoTokenizer` + `AutoModelForCausalLM`** for pure-text manifest, aligned with same `chat_template`; if you switch to `AutoProcessor`, install deps as Transformers errors indicate.
| **Multimodal (Image/Audio/Video)** | If evaluation includes non-text modalities, switch to `AutoModelForMultimodalLM` (see same model card; **consistent with Layer2 manifest**) |
| **Tokenizer Consistent with Training** | Fine-tuning data and inference both use same **`google/gemma-4-E2B-it`** processor / chat template = **yes** |

**Note**: Model card *Best Practices* recommends `temperature=1.0` / `top_p=0.95` / `top_k=64` for general sampling; this report **evaluation baseline** adopts **§4 `eval-protocol-v0` greedy decoding**, distinguishing from "daily chat best experience" to avoid mixing two decoding schemes in PoC comparison.

---

## 3. Layer 2 Evaluation Set Definition

Consistent with design documents ([_docs/shaping/9_eval_qa_EN.md](../shaping/9_eval_qa_EN.md) §9.1.3):

| Stratum | Target Scale | Purpose |
|---------|--------------|---------|
| **Core Capability** (brainstorm + summary) | ~200 | Product main capability regression |
| **Fallback General** (instruction following) | ~200 | Prevent "only knows brainstorming" |
| **Chinese Protection** | ~100 | Chinese degradation sentinel |

**Actual Use in This Report:**

| Item | Value |
|------|-------|
| **Manifest Version** | `layer2-v0` |
| **Manifest Path** | `data/eval/layer2/manifest_v0.jsonl` (metadata: `data/eval/layer2/manifest_meta.json`) |
| **Total Items** | **500** (reached shaping target scale; strata are **v0 proxy data sources**, bump version and re-run baseline when upgrading to X-AlpacaEval / CMT-Eval, see [_docs/eval/layer2/README.md](../eval/layer2/README.md)) |
| **Sampling/Filtering Rules** | `scripts/build_layer2_manifest.py`: brainstorm Chinese multi-round sample 200 (seed 42); `general_mixed` `lang=en` sample 200 (seed 43); `lang=zh` sample 100 (seed 44). Proxy data source notes in `manifest_meta.json` `proxy_notes` and [_docs/eval/layer2/README.md](../eval/layer2/README.md) |

---

## 4. Inference and Evaluation Protocol (Must Be Fixed for Reproducibility)

**Principle**: Subsequent PoC / Stage1 comparison experiments should **only change model weights and training-related variables**; fields in this section require **protocol version bump** (e.g., `eval-protocol-v0` → `v1`) for any changes, no silent modifications allowed.

**This Report Freezes: `eval-protocol-v0` (recommended to write into experiment `META.json`)**

---

### 4.0 Model Under Test (Gemma Base) — Generation Parameters (Best Practice)

Goal: **Regression comparable, reproducible**; consistent with common public benchmark practices (evaluation side minimizes randomness).

| Item | Recommended | Description |
|------|-------------|-------------|
| **Decoding** | **Greedy** | `do_sample=false` (or equivalent: `temperature=0` with sampling disabled) |
| **`temperature`** | **0** | Baseline / regression main run fixed at 0; if individual items need slight diversity, limit to exploratory experiments with separate protocol version |
| **`top_p`** | **1.0** (or omit) | Consistent with greedy; if future `temperature>0`, can use `0.9` |
| **`max_new_tokens`** | **2048** | Covers Layer2 most multi-round and brainstorm lengths; if truncation rate high, raise to **4096** (must be consistent within same bump) |
| **`repetition_penalty`** | **1.0** (default) | Unless Gemma official recommends otherwise for evaluation |
| **`stop` sequences** | **None** | Natural end by `eos_token`; avoid custom stops that may mis-truncate |
| **Single-turn / Multi-turn** | **Consistent with manifest** | Manifest `messages` rounds sent to chat template as-is; **do not** add system prompts like "please answer in Chinese" that conflict with item text |
| **System Prompt** | **None** or **Minimal** | Recommend **empty system**; if Gemma-IT template requires placeholder, use fixed single English assistant setting (write to manifest side same source, don't vary per item) |
| **Batch Size** | **1** (baseline first run) | Prioritize correctness and OOM safety; if speeding up with higher batch, record in report without changing decoding params |
| **Random Seed** | **`42`** | Under `temperature=0` impact limited, still record `torch` / `numpy` / `random` seeds and `transformers` version |

**Not Recommended**: Baseline main run using `temperature≥0.7` or changing system prompt per item — significantly increases variance, weakens "degradation detection" judgment.

---

### 4.1 Judge Model — `qwen3.6-plus` (LLM-as-a-Judge)

You have selected **Qwen3.6-Plus** as judge; common patterns with DashScope **OpenAI-compatible** API below (**verify actual available model name in console**).

| Item | Recommended | Description |
|------|-------------|-------------|
| **Model name `model`** | **`qwen3.6-plus`** | Consistent with Qwen Cloud / compatible API docs; if call fails, check console list and update this line |
| **Base URL** | Consistent with data side: domestic common `https://dashscope.aliyuncs.com/compatible-mode/v1`; international see official `dashscope-intl` docs | Align with `DASHSCOPE_OPENAI_BASE_URL` in [data_pipeline](../../data_pipeline/README.md) |
| **`temperature`** | **0.2** | Judge with slightly lower randomness,保留极小方差；if need stronger reproducibility can use **0** |
| **`max_tokens` (judge output)** | **2048** | Must fit multi-dimension **1–100** integer scores + `rationale_zh` + JSON; if structured output very long can use **4096** |
| **`top_p`** | **0.9** | Common combo with `temperature=0.2`; if `temperature=0` then `top_p=1` |
| **Scoring Dimensions** | Consistent with `scripts/layer2_judge_scores.py` and this repository Sprint memos | **relevance / coherence / helpfulness / creativity / clarity / task_alignment / depth / chinese_quality** (each 1–100) + **overall** (1–100) + **`rationale_zh`** (Chinese sentence) |
| **Output Format** | **JSON preferred** | Require judge to output only `{"relevance":1-100,...,"overall":1-100,"rationale_zh":"..."}` fixed keys for parsing and audit |
| **Calls per item** | **1 judge call** | Do not default to self-consistency majority vote (high cost); disputed items manually arbitrated |
| **Aggregation** | Stratum **mean ± std** | Consistent with shaping "stratified report, no single total score" |
| **Recording** | Record **date, model name, API region** per batch run | **Do not** paste API Key in report body |

---

### 4.2 If Not Using Automatic Judge

**Not Applicable** (this baseline uses §4.1 `qwen3.6-plus` judge). If switching to pure manual sampling in future, must start new `eval-protocol-v*` and fully replace §4.

---

### 4.3 Protocol Change Rules

| Change Type | Must bump `eval-protocol` version? |
|-------------|-----------------------------------|
| Modify Gemma `temperature` / `max_new_tokens` / system template | **Yes** |
| Change judge model or judge temperature / JSON key design | **Yes** |
| Only fix manifest typos, don't change item meaning or order | No (manifest self-bumps version) |

---

## 5. Results: Stratified Summary (Core / General / Chinese)

The following **means** come from **`layer2_judge_summary.json`** (`scripts/aggregate_layer2_judge_scores.py` statistics for `judge_parse_ok=true` samples). **Standard deviation** column not computed by summary script, marked **—**; if σ needed, extend script or offline compute from `layer2_judge_scores.jsonl`.

### 5.1 Core Capability (~200)

| Dimension | Mean | Std Dev | Notes |
|-----------|------|---------|-------|
| Relevance | 95.60 | — | n=200 |
| Coherence | 95.26 | — | |
| Helpfulness | 93.22 | — | |
| Creativity | 87.08 | — | |
| **overall** | **93.35** | — | Holistic 1–100 |

### 5.2 Fallback General (~200)

| Dimension | Mean | Std Dev | Notes |
|-----------|------|---------|-------|
| Relevance | 94.50 | — | n=200; many English instructions, `chinese_quality` often **100** (N/A) |
| Coherence | 83.26 | — | |
| Helpfulness | 81.91 | — | |
| Creativity | 74.12 | — | |
| **overall** | **81.85** | — | |

### 5.3 Chinese Protection (~100)

| Dimension | Mean | Std Dev | Notes |
|-----------|------|---------|-------|
| Chinese Quality | 92.86 | — | n=100 |
| Relevance | 88.00 | — | |
| Coherence | 79.10 | — | |
| **overall** | **77.94** | — | Significantly below core, see §6 P2 |

### 5.4 Failure Cases (Should)

- This run: **500 / 500** judge parses succeeded; if `judge_parse_ok=false` appears later, inspect `judge_error` / `judge_raw_preview` in `layer2_judge_scores.jsonl`, then re-run or arbitrate. Optional: extract 5–10 low `layer2_id` items to failure list.

---

## 6. Redline Conclusions (P0 / P1 / P2)

Definitions see [_docs/shaping/9_eval_qa_EN.md](../shaping/9_eval_qa_EN.md) §9.3.

| Level | Triggered? | Evidence | Action |
|-------|------------|----------|--------|
| **P0** Safety | ☑ No | No dedicated security red team set; Layer 2 is proxy regression set | Update if future audit finds issues |
| **P1** Function | ☑ No | No "large-scale unavailable" or protocol-level failure; judge parse failure **0** | Per shaping: stop and roll back if triggered |
| **P2** Experience | ☑ Yes (Warning) | **zh_guard** `overall` mean **77.94**, below **core 93.35** and pooled mean **85.67** (see §5.3) | Monitor Chinese scenarios in PoC / data recipe; optional Qwen baseline per shaping |

**Note**: Baseline phase **P0 should not trigger**; current conclusion is **proceed to Week 2 PoC**, but must include **Chinese protection stratum** in iteration acceptance metrics.

---

## 7. Artifacts and Environment (Reproducible)

| Item | Path or Content |
|------|-----------------|
| **Raw Model Output** (per-item JSONL) | `experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl` (see [META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) `results.layer2_infer_jsonl`) |
| **Judge Raw Output** | `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl` (`results.metrics_path`) |
| **Summary Table JSON** | `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json` (`results.judge_summary_json`) |
| **This Report Git Commit** | `115d983975664b42cb9b09dd9b5102fca08d4eaa` (`git rev-parse HEAD` at finalization; replay based on your clone) |
| **Operating System** | (Fill in on evaluation machine) |
| **Python** | (Fill in on evaluation machine) |
| **PyTorch / CUDA** | (Fill in on evaluation machine) |
| **Key Package Versions** | `transformers==___`, `accelerate==___`, … (Fill in on evaluation machine) |

---

## 8. Limitations and Next Steps

- **Layer 2 reached 500 items**: This baseline completed; manifest upgrade (e.g., to X-AlpacaEval / CMT-Eval proxy source) requires version bump and re-run.
- **Base vs final Gemma-4-E2B naming inconsistency**: Note transition strategy and when to re-run baseline.
- **Align with Week2**: After PoC completes, generate `s1-poc-e01-eval` comparison table under **same manifest version + same §4 protocol**.

---

## 9. Revision History

| Date | Revision |
|------|----------|
| 2026-05-12 | Initial skeleton: Aligned with Week1 plan and shaping Layer2 / redline sections |
| 2026-05-12 | §4 frozen `eval-protocol-v0`: Gemma greedy + `max_new_tokens=2048`; judge `qwen3.6-plus` with JSON output suggestion |
| 2026-05-17 | **Finalized**: Full 500 inference + `qwen3.6-plus` judge; §0/§1/§5/§6/§7 filled; §4.1 aligned with implementation to **1–100** scoring; `revision` aligned with `META.json` |
