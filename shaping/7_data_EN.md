# 7. Data Strategy (Data)

> This document is part of the project **shaping** phase: defining fine-tuning dataset recipes, benchmark construction, data translation and augmentation strategies. **Does not include** specific data preprocessing code, translation pipeline implementation, or evaluation scripts.

---

## 7.1 Core Dataset

### 7.1.1 Primary Dataset: brainstorm_vicuna_10k

| Attribute | Description |
|-----------|-------------|
| **Source** | Hugging Face `DevQuasar/brainstorm_vicuna_10k` |
| **Size** | 10k train + 1k test |
| **Format** | Multi-turn dialogue (human/gpt alternating), 6-24 turns |
| **Topics** | Creative ideas, planning, problem-solving |
| **Language** | English |
| **Quality** | Synthetic data, natural follow-ups, reasonable expansion |
| **Fit** | ⭐⭐⭐⭐⭐ Highly aligned with "brainstorming" scenario |

### 7.1.2 Dialogue Pattern Analysis

Typical conversation structure:
1. User proposes idea ("I want to..." / "I'm thinking of...")
2. Assistant asks clarifying questions ("What kind of..." / "What inspired you...")
3. Multi-turn deepening converges to concrete proposal

---

## 7.2 Data Augmentation: Bilingual Construction

### 7.2.1 Translation Strategy

Use cloud Qwen-Max / Qwen-Plus to translate brainstorm_vicuna_10k into Chinese, building parallel bilingual dataset.

**Translation Prompt**:
```text
Please translate the following English brainstorming dialogue into Chinese.
Requirements:
1. Maintain natural conversational flow
2. Preserve questioning and divergent tone
3. Names and places may be kept or transliterated
4. Output format consistent with original (human/gpt alternating)

Original:
[English dialogue]
```

### 7.2.2 Quality Control

| Step | Operation | Pass Criteria |
|------|-----------|---------------|
| Machine translation | Qwen-Max batch translation | Complete all 10k entries |
| Manual spot-check | Random sample 100 entries | Unnatural rate < 10% |
| Correction re-translation | Re-translate or manually fix poor quality | Pass after correction |

### 7.2.3 Risk Mitigation

- If translation quality poor (> 20% unnatural) → Switch to DeepSeek or GPT-4 for re-translation
- If Chinese/English tone differs significantly → Keep English original as primary, Chinese as supplement rather than 1:1

---

## 7.3 Fine-Tuning Data Recipe (Conservative Initial Version)

### 7.3.1 Data Mix

| Dataset | Entries | Ratio | Description |
|---------|---------|-------|-------------|
| brainstorm_vicuna_10k (English original) | 5,000 | 35% | Core brainstorming capability |
| brainstorm_vicuna_10k (Qwen translated Chinese) | 5,000 | 35% | Chinese brainstorming capability |
| Alpaca / ShareGPT (mixed bilingual general) | 3,000 | 25% | General capability baseline, prevent forgetting |
| Self-built seed data (personal creative cases) | 500 | 5% | Personalization style reserved |
| **Total** | **13,500** | **100%** | |

### 7.3.2 Conservative Principles

- **LoRA priority**: Only train 1-5% of parameters, freeze base model
- **Learning rate control**: 1e-4 (conservative), prefer underfitting over overfitting
- **Epoch limit**: 3 epochs, observe before deciding to increase
- **Mixed baseline**: General data accounts for 25%, prevent only learning brainstorming and forgetting normal dialogue

---

## 7.4 Evaluation Benchmark (Machine Evaluation)

### 7.4.1 Machine Evaluation Scheme (LLM-as-a-Judge)

Adopt automated machine evaluation to replace manual scoring, enabling evaluation of large-scale datasets (2000+ entries).

**Judge Model Selection**:

| Judge Model | Advantages | Cost | Recommended Scenario |
|-------------|------------|------|----------------------|
| **Qwen-Max** | Strong Chinese understanding, aligns with cloud selection | Alibaba Cloud per-token billing | Chinese evaluation首选 |
| **GPT-4** | Strong English, rich judging experience | OpenAI API | English evaluation, cross-validation |
| **DeepSeek-R1** | High cost-performance, visible reasoning process | Low cost | Fast batch evaluation |

**Scoring Dimensions (1-5 Scale)**:

| Dimension | Meaning | 5-point Standard |
|-----------|---------|------------------|
| **Relevance** | Response stays on topic | Fully understands intent, no off-topic |
| **Coherence** | Multi-turn dialogue flows smoothly | Context consistent, natural transitions |
| **Helpfulness** | Provides valuable questions/suggestions | Questions have depth, suggestions actionable |
| **Creativity** | Provides novel angles or perspectives | Brainstorming-specific, reasonable divergence |

### 7.4.2 Public Benchmark Datasets (Direct Usage)

Select validated evaluation benchmarks from Hugging Face:

| Dataset | Size | Language | Characteristics | Evaluation Content |
|---------|------|----------|-----------------|---------------------|
| **X-AlpacaEval** | 805 entries | 5 languages including EN/CN | AlpacaEval professional translation | General instruction following |
| **CMT-Eval** | 596 dialogues (4,431 turns) | Chinese | Speech Act framework | Chinese multi-turn dialogue |
| **brainstorm_vicuna_10k test set** | 1,000 entries | English | Original dataset test split | Brainstorming-specific |
| **brainstorm-v3.1_vicnua_1k** | 1,000 entries | English | With Markdown summary | Brainstorming + summarization |
| **brainstorm-v2.1_vicuna_1k** | 1,000 entries | English | Deep questioning version | Brainstorming depth |
| **MT-Bench** | 80 entries | English | Multi-turn deep dialogue | Multi-turn capability |

**Public Benchmark Total**: ~4,500 entries (statistically significant)

**Sources**:
- X-AlpacaEval: https://huggingface.co/datasets/zhihz0535/X-AlpacaEval
- CMT-Eval: https://aclanthology.org/2025.findings-emnlp.992/ (confirm Hugging Face release)
- brainstorm_vicuna_10k: Built-in test split 1k entries
- brainstorm-v3.1_vicnua_1k: https://huggingface.co/datasets/DevQuasar/brainstorm-v3.1_vicnua_1k (with summary, for summarization evaluation)
- brainstorm-v2.1_vicuna_1k: https://huggingface.co/datasets/DevQuasar/brainstorm-v2.1_vicuna_1k (deep questioning version)
- MT-Bench: https://huggingface.co/datasets/yzygalaxy/mt_bench_human_judgments

### 7.4.3 Self-Built Supplementary Evaluation Set

Fill gaps not covered by public benchmarks:

| Domain | Count | Source | Purpose |
|--------|-------|--------|---------|
| Creative writing | 100 entries | Sampled from creative_writing/ember-dataset | Creative generation evaluation |
| Inspiration card summarization | 50 entries | Self-built: Long dialogue → structured card | Core product function evaluation |
| Product-specific scenarios | 100 entries | Self-built: Designed for application scenarios | Product alignment evaluation |

**Self-Built Total**: 250 entries

**Total Evaluation Scale**: ~4,750 entries (sufficient to detect > 3% capability changes, highly statistically significant)

### 7.4.4 Execution Flow

```
Stage 1: Baseline Testing
    ↓
Load base model (Gemma-4-E2B-IT or Qwen3.5-2B)
    ↓
Run public benchmarks (2,500 entries) + self-built set (250 entries)
    ↓
LLM judge (Qwen-Max) automatic scoring
    ↓
Record baseline scores (mean, std, per-dimension)

Stage 2: Post-Fine-Tuning Testing
    ↓
Load fine-tuned LoRA model
    ↓
Run same evaluation dataset (2,750 entries)
    ↓
LLM judge automatic scoring
    ↓
Record new scores

Stage 3: Comparative Analysis
    ↓
Statistical comparison: mean difference, t-test significance
    ↓
Per-dimension report: Brainstorming/General/Chinese/English capability changes
    ↓
Stop-loss decision: Accept or rollback fine-tuning result
```

### 7.4.5 Evaluation Prompt Template (Example)

```text
You are a professional dialogue quality evaluation expert. Please evaluate the following AI assistant response.

【Evaluation Dimensions】(1-5 points)
1. Relevance: Does the response stay on topic and understand user intent?
2. Coherence: Is the dialogue fluent and natural, context consistent?
3. Helpfulness: Does it provide valuable questions, suggestions, or information?
4. Creativity: Does it provide novel angles or perspectives (brainstorming scenario)?

【Conversation History】
{conversation_history}

【Current Question】
{user_input}

【Assistant Response】
{assistant_output}

Please output JSON format scores:
{
  "relevance": 4,
  "coherence": 4,
  "helpfulness": 5,
  "creativity": 4,
  "comment": "Questions have depth, suggestions actionable, could diverge further"
}
```

### 7.4.6 Stop-Loss Thresholds and Decision Criteria

| Condition | Statistical Standard | Decision |
|-----------|---------------------|----------|
| Any dimension significantly decreases | p < 0.05 and decrease > 10% | Warning, analyze cause |
| Any dimension substantially decreases | p < 0.01 and decrease > 20% | Rollback to base model |
| Brainstorming fails to improve | Increase < 5% or decrease | Adjust recipe and retrain |
| Chinese capability significantly decreases | p < 0.05 and decrease > 15% | Increase Chinese data or switch to Qwen3.5 |

**Statistical Method**: Paired t-test comparing pre/post fine-tuning scores on same samples.

---

## 7.5 Stage 2 Data (Personalization Fine-Tuning)

### 7.5.1 Data Sources

- User **finalized cards** from application (high signal)
- Dialogue turns marked "useful" by user
- Enter training pool only after **explicit user authorization**

### 7.5.2 Trigger Conditions (Shaping Placeholder)

No specific numbers defined, conceptual layer reserves following options:
- Trigger after accumulating N finalized cards
- Periodic trigger every two weeks
- Trigger on user explicit "optimize my model" click

### 7.5.3 Data Quality Filtering

- **Draft status content defaults excluded** from training pool
- User deleted or retracted content **immediately removed** from training pool
- Regular manual spot-check of user data quality

---

## 7.6 Relationship with Other Chapters

| Chapter | Related Content |
|---------|-----------------|
| `6_model_strategy_EN.md` | Model selection determines data language mix (Gemma 4 needs more Chinese protection, Qwen3.5 has strong Chinese native) |
| `4_object_rule_EN.md` | Finalized cards are data source for Stage 2 fine-tuning |
| `8_train_eval_EN.md` (pending) | Training process, evaluation metric calculation |

---

## 7.7 Boundaries and Non-Goals (This Section)

- **Not defined**: Specific data preprocessing code (cleaning, deduplication, format conversion)
- **Not defined**: Batch translation pipeline implementation tools
- **Not defined**: Specific 80 evaluation prompts content (requires manual writing)
- **Not defined**: "Judge model" prompt design for automated evaluation
- **Not included**: Data annotation platforms, crowdsourcing annotation processes
- **Not included**: Specific legal opinions on privacy compliance review

---

## Document Relationships

| Document | Content |
|----------|---------|
| `shaping/6_model_strategy_EN.md` | Model selection, fine-tuning strategy |
| `shaping/7_data_EN.md` | Dataset recipes, evaluation benchmark (this document) |
| `shaping/8_train_eval_EN.md` (pending) | Training process, evaluation methodology |
