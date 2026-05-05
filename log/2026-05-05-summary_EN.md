# Discussion Summary · 2026-05-05

This document summarizes the discussions and finalized outputs related to "Training & Experimentation, Evaluation & Quality, Infrastructure & Operations" from the day.

---

## 1. Phase Positioning

- The day's work was in the **shaping** phase: defining training stages, experiment protocols, evaluation systems, data flow, and operational strategies.
- **Does not include**: specific training commands, hyperparameter grids, metric formulas, database selection, or API implementations.
- Continued the shaping progress from 05-02 to 05-04, completing the first drafts of Chapters 8, 9, and 10.

---

## 2. Chapter 8: Training & Experimentation Strategy (Train / Iterate) · Finalized Points

### 2.1 Training Stage Division (Corresponding to Two-Stage Fine-tuning)

| Stage | Goal | Key Decision Point |
|-------|------|-------------------|
| **Stage 0 PoC** | Validate data recipe feasibility, establish baseline | Produce evaluable LoRA weights |
| **Stage 1-A Conservative** | Produce usable "brainstorming + summarization" base model | Gemma-4-E2B vs Qwen3.5-2B showdown |
| **Stage 1-B Aggressive** | Adjust recipe when 1-A results are suboptimal | Prevent overfitting, set stop-loss |
| **Stage 2 Personalization** | Learn user's personal style | Trigger after accumulating N finalized cards |

### 2.2 Version Naming Convention

- **Format**: `{stage}-{base-model}-{data-version}-{experiment-number}-{status}`
- **Examples**: `s1-qwen35-2b-v1.0-e03-done`, `poc-gemma4e2-v0.1-e01-wip`
- **Data Version**: `v{major}.{minor}`, major = significant recipe change, minor = proportion fine-tuning

### 2.3 Reproducibility Standards

- **Random Seed**: Exploration experiments fix seed at `42`; ablation studies run 3 seeds and report mean
- **Environment Snapshot**: Record framework version, CUDA version, hardware specs, dataset hash
- **Experiment Lineage**: Tree-shaped history, each experiment labeled with `parent_experiment`

### 2.4 Experiment Decision Types

| Decision | Meaning |
|----------|---------|
| **Accept** | Met expectations, proceed to next stage |
| **Iterate** | Improvement observed but needs fine-tuning; start new experiment based on this one |
| **Reject** | Significant regression; roll back to parent experiment |
| **Abandon** | Wrong direction; archive and discontinue |

---

## 3. Chapter 9: Evaluation & Quality (Eval / QA) · Finalized Points

### 3.1 Tiered Evaluation System (Three Layers)

| Layer | Scale | Purpose | Update Frequency |
|-------|-------|---------|------------------|
| **Layer 1 Capability Probes** | ~4,000+ items | Comprehensive capability exploration, horizontal comparison | As public benchmarks update |
| **Layer 2 Regression Validation** | ~500 items | Automatic evaluation after each experiment, detect degradation | Periodically add historical error cases |
| **Layer 3 Production Acceptance** | ~100 items | Final manual review, confirm product readiness | Rarely changed |

### 3.2 Evaluation Dimensions (Framework defined, formulas not defined)

- Relevance, Coherence, Helpfulness, Creativity, Structuring, Chinese Quality
- Different question sets can emphasize different dimensions
- Output "multi-dimensional radar chart," not a single aggregate score

### 3.3 Quality Redline Types

| Level | Type | Trigger Example | Decision |
|-------|------|-----------------|----------|
| **P0** | Safety Redline | Harmful output, privacy leak | **Stop immediately**, investigate and fix |
| **P1** | Functionality Redline | Core capability degradation > 20% | **Reject experiment**, roll back to base |
| **P2** | Experience Redline | Creativity decline 10-20% | **Warning**, iterate and optimize |

### 3.4 Judge Models

- **Qwen-Max**: Primary choice for Chinese evaluation
- **GPT-4**: English evaluation, cross-validation
- **DeepSeek-R1**: Fast batch evaluation
- **Human**: Layer 3 acceptance, dispute arbitration

---

## 4. Chapter 10: Infrastructure & Operations (Infra / Ops) · Finalized Points

### 4.1 Data Flow Architecture

- **Product Data Flow**: On-device inference (real-time) → Finalization confirmation → Cloud storage (persistence)
- **Training Data Flow**: Finalized cards → User authorization → Training candidate pool → Periodic training
- **Control Point**: User data entering training pool requires explicit authorization, which can be revoked

### 4.2 Data State Flow

```
Draft → Finalized → Product Database (all users)
                    ↓ User authorization
              Training Candidate Pool → Training Complete → New Model Version → Push Update
```

### 4.3 User Privacy Switch

| Design Principle | Description |
|----------------|-------------|
| Conservative by Default | New users default to "not participating in model improvement" |
| Explicit Authorization | Participation requires user actively enabling |
| Immediate Effect | Switch changes take effect immediately |
| Reversible & Deletable | Can turn off anytime, can request deletion of contributed data |

### 4.4 Platform Compliance Layers

| Layer | Type | Examples |
|-------|------|----------|
| **L1** | Laws & Regulations | GDPR, Personal Information Protection Law, Generative AI Management |
| **L2** | Platform Policies | Google Play policies, model licenses |
| **L3** | Product Self-discipline | Content safety guidelines, data usage boundaries |
| **L4** | Technical Implementation | Secure coding, encryption strategies, audit logs |

### 4.5 Operations Types

| Type | Scenarios | Response Time |
|------|-----------|---------------|
| Product Operations | Service availability, data sync | Hour-level |
| Training Operations | Training task management, resource scheduling | Day-level |
| Security Operations | Redline events, security vulnerabilities | Minute-level |
| Data Operations | Data cleanup, compliance audits | Week-level |

---

## 5. Deliverables (First Drafts)

| Path | Description |
|------|-------------|
| `shaping/8_train_iterate_CN.md` | Chapter 8 Chinese draft (Training & Experimentation) |
| `shaping/8_train_iterate_EN.md` | Chapter 8 English draft (created today) |
| `shaping/9_eval_qa_CN.md` | Chapter 9 Chinese draft (Evaluation & Quality) |
| `shaping/9_eval_qa_EN.md` | Chapter 9 English draft (created today) |
| `shaping/10_infra_ops_CN.md` | Chapter 10 Chinese draft (Infrastructure & Operations) |
| `shaping/10_infra_ops_EN.md` | Chapter 10 English draft (created today) |

---

## 6. Complete Shaping Document Map

```
shaping/
├── 3_user_background_shaping_CN.md  - User & Scenarios
├── 4_object_rule_CN.md              - Core Objects & Rules
├── 5_surface_CN.md                  - Product Surface
├── 6_model_strategy_CN.md           - Model & Capability Strategy
├── 7_data_CN.md                     - Data Strategy
├── 8_train_iterate_CN.md            - Training & Experimentation (today)
├── 9_eval_qa_CN.md                  - Evaluation & Quality (today)
└── 10_infra_ops_CN.md               - Infrastructure & Operations (today)
```

---

## 7. Relationship with Previous Summaries

- **05-02**: Established two-stage fine-tuning, dataset direction, product surface preferences
- **05-03**: User & scenarios, core objects & rules (cards/tags/associations/finalization)
- **05-04**: Product surface (Kotlin Android), model candidates, data recipes, evaluation benchmarks
- **05-05 (today)**: Training stage division, experiment naming, reproducibility, tiered question sets, redline types, data flow, privacy switches, operations types

---

## 8. Recommended Next Steps

1. **Review**: Read through `8_train_iterate_EN.md`, `9_eval_qa_EN.md`, `10_infra_ops_EN.md` to check consistency with previous chapters
2. **Data Preparation**: Download brainstorm_vicuna_10k and begin Chinese translation (planned on 05-04)
3. **PoC Launch**: Based on existing shaping, start the first experiment of Stage 0
4. **3-Month Project Planning**: Integrate all shaping chapters, create milestone timeline

---

*Document generated in project `log/` directory for personal learning and project advancement.*
