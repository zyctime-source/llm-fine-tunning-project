# Session summary · 2026-05-04

This note captures the day's discussion and written outputs on **project shaping: surface (product form factor), model & capability strategy, and data strategy**.

---

## 1. Phase placement

- Work stayed in **shaping**: defining product form factor, model selection, data recipes, and evaluation strategies—**no** training scripts, hyperparameters, or implementation details.
- Continued from 05-03 shaping progress, completed Chapter 5, 6, 7 first drafts.

---

## 2. Chapter 5: Surface (Product Form Factor) — locked points

### 2.1 Client-side form factor (decision finalized)

- **Primary form factor**: Native Android application in Kotlin
- **Excluded**: WeChat Mini Program, Pure Web, Kotlin Multiplatform
- **Rationale**: On-device model deployment is core goal; global availability via Google Play; developer has existing Kotlin experience
- **iOS strategy**: Excluded from initial version; reassess Swift or KMP later if needed

### 2.2 Inference deployment pattern

- **On-device inference (primary)**: Small-parameter models (2B-5B) running locally for fast response and privacy-sensitive scenarios
- **Cloud inference (alternative)**: DeepSeek/Qwen large models via API for deep generation and learning comparison
- **Hybrid logic**: On-device by default, explicit toggle to cloud; automatic routing strategy not defined in initial version

---

## 3. Chapter 6: Model & Capability Strategy — locked points

### 3.1 Small model candidate observation list

| Priority | Model | Parameters | Release | License |
|----------|-------|------------|---------|---------|
| P0 | Gemma-4-E2B-IT | 2B | Apr 2025 | Google custom |
| P0 | Gemma-4-E4B-IT | 4B | Apr 2025 | Google custom |
| P0 | Qwen3.5-2B | 2B | Mar 2025 | Apache 2.0 |
| P1 | Qwen3.5-4B | 5B | Mar 2025 | Apache 2.0 |
| P1 | Qwen3.5-0.8B | 0.9B | Mar 2025 | Apache 2.0 |

- **2B-class showdown**: Gemma-4-E2B vs Qwen3.5-2B is the core comparison focus for PoC phase
- **Final selection not finalized**; to be decided after PoC testing

### 3.2 Large model cloud alternatives

- **DeepSeek-V3 / R1**: Deep reasoning, comparison learning
- **Qwen-Max / Plus**: Chinese scenario deep generation
- **GPT series excluded from initial version**

### 3.3 Capability extensions (Tools / skills+Tools / multimodal)

- Initial version: Pure dialogue brainstorming + card harvesting
- Reserved: Gemma-4 Any-to-Any multimodal extension placeholder
- Not defined: Specific Tools implementation path

### 3.4 Fine-tuning strategy

- **Stage 1 (Foundation)**: Public data + small seed dataset, learn "brainstorm dialogue + summarization harvesting"
- **Stage 2 (Personalization)**: User finalized cards (with authorization), learn personal style
- Technique: LoRA priority, full-parameter fine-tuning as alternative

---

## 4. Chapter 7: Data Strategy — locked points

### 4.1 Core dataset

- **Primary dataset**: `DevQuasar/brainstorm_vicuna_10k` (10k train + 1k test, English)
- **Data augmentation**: Qwen-Max translation → bilingual parallel dataset

### 4.2 Fine-tuning data recipe (conservative)

| Dataset | Entries | Ratio |
|---------|---------|-------|
| brainstorm_vicuna_10k English original | 5,000 | 35% |
| brainstorm_vicuna_10k Qwen-translated Chinese | 5,000 | 35% |
| Alpaca/ShareGPT general | 3,000 | 25% |
| Self-built seed data | 500 | 5% |
| **Total** | **13,500** | **100%** |

### 4.3 Evaluation benchmark (Machine Evaluation)

**Machine evaluation scheme (LLM-as-a-Judge)**:
- Judge models: Qwen-Max (Chinese), GPT-4 (English / cross-validation)
- Scoring dimensions: Relevance, Coherence, Helpfulness, Creativity (1-5 scale)

**Public benchmark datasets**:

| Dataset | Size | Purpose |
|---------|------|---------|
| X-AlpacaEval | 805 entries | General instruction following (bilingual) |
| CMT-Eval | 596 dialogues | Chinese multi-turn dialogue |
| brainstorm_vicuna_10k test set | 1,000 entries | Brainstorming baseline |
| brainstorm-v3.1_vicnua_1k | 1,000 entries | Brainstorming + summary (summarization eval) |
| brainstorm-v2.1_vicuna_1k | 1,000 entries | Brainstorming deep questioning |
| MT-Bench | 80 entries | Multi-turn deep dialogue |

- **Public benchmark total**: ~4,500 entries
- **Self-built supplement**: ~250 entries (creative writing, card summarization, product scenarios)
- **Total evaluation scale**: ~**4,750 entries** (sufficient to detect > 3% capability changes)

### 4.4 Conservative fine-tuning principles

- **LoRA priority**: rank=8, freeze 95%+ of base model parameters
- **Learning rate control**: 1e-4, prefer underfitting
- **Epoch limit**: 3 epochs
- **Mixed baseline**: 25% general data to prevent forgetting

### 4.5 Stop-loss thresholds

| Condition | Statistical Standard | Decision |
|-----------|---------------------|----------|
| Any dimension significantly decreases | p < 0.05 and decrease > 10% | Warning, analyze cause |
| Any dimension substantially decreases | p < 0.01 and decrease > 20% | Rollback to base model |
| Brainstorming fails to improve | Increase < 5% or decrease | Adjust recipe and retrain |

---

## 5. Written artifacts (first drafts)

| Path | Note |
|------|------|
| `shaping/5_surface_CN.md` | Chapter 5 CN (surface) |
| `shaping/5_surface_EN.md` | Chapter 5 EN |
| `shaping/6_model_strategy_CN.md` | Chapter 6 CN (model strategy) |
| `shaping/6_model_strategy_EN.md` | Chapter 6 EN |
| `shaping/7_data_CN.md` | Chapter 7 CN (data strategy) |
| `shaping/7_data_EN.md` | Chapter 7 EN |

---

## 6. Key dataset links

| Dataset | URL | Purpose |
|---------|-----|---------|
| brainstorm_vicuna_10k | https://huggingface.co/datasets/DevQuasar/brainstorm_vicuna_10k | Train + test |
| brainstorm-v3.1_vicnua_1k | https://huggingface.co/datasets/DevQuasar/brainstorm-v3.1_vicnua_1k | Evaluation (with summary) |
| brainstorm-v2.1_vicuna_1k | https://huggingface.co/datasets/DevQuasar/brainstorm-v2.1_vicuna_1k | Evaluation (deep questioning) |
| X-AlpacaEval | https://huggingface.co/datasets/zhihz0535/X-AlpacaEval | Evaluation (general instructions) |
| MT-Bench | https://huggingface.co/datasets/yzygalaxy/mt_bench_human_judgments | Evaluation (multi-turn) |

---

## 7. Suggested next steps

1. **Review**: Read `5_surface_CN.md`, `6_model_strategy_CN.md`, `7_data_CN.md` for consistency.
2. **Data preparation**: Download brainstorm_vicuna_10k, begin Chinese translation.
3. **Benchmark construction**: Filter subsets from public benchmarks suitable for brainstorming scenarios.
4. **Next shaping module**: Training/experiment strategy (Train), evaluation/quality (Eval), or 3-month project planning.

---

*Generated under the project `log/` directory for personal learning and project continuity.*
