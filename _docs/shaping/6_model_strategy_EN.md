# 6. Model & Capability Strategy (Model)

> This document is part of the project **shaping** phase: defining model selection, edge-cloud division, capability extensions, and fine-tuning strategy. **Does not include** specific fine-tuning scripts, hyperparameter configurations, quantization format selection, or training timelines.

---

## 6.1 Small Model Candidates (Confirmed Observation List)

### 6.1.1 Candidate List

| Priority | Model | Parameters | Version | Characteristics |
|----------|-------|------------|---------|-----------------|
| P0 | **Gemma-4-E2B-IT** | 2B | Instruction-tuned | Released Apr 2026, ultra-small, Any-to-Any architecture, edge-optimized |
| P0 | **Gemma-4-E4B-IT** | 4B | Instruction-tuned | Released Apr 2026, more capable, suitable for primary scenarios |
| P0 | **Qwen3.5-2B** | 2B | Image-Text-to-Text | Released Mar 2026, strong Chinese, native multimodal, Apache 2.0 |
| P1 | Qwen3.5-4B | 5B | Image-Text-to-Text | More capable, Chinese scenario primary alternative |
| P1 | Qwen3.5-0.8B | 0.9B | Image-Text-to-Text | Ultra-lightweight, speed testing |

### 6.1.2 Selection Rationale

- **Gemma 4** (Apr 2026 release): Google's current small model series, E2B/E4B specifically edge-optimized, Any-to-Any architecture
- **Qwen3.5** (Mar 2026 release): Alibaba's current small model series, Chinese-native optimization, Image-Text-to-Text multimodal, Apache 2.0 license
- **2B-class showdown**: Gemma-4-E2B vs Qwen3.5-2B is the core comparison focus for PoC phase
- **IT/Chat versions**: Rapid dialogue capability validation; **Base versions**: Reserve custom fine-tuning space
- Final selection not finalized; to be decided after PoC phase testing

### 6.1.3 License Information

| Model | License Type | Commercial Use | Notes |
|-------|--------------|----------------|-------|
| Gemma 4 | Google custom license | ✅ Allowed | Must comply with Google terms; prohibited for specific harmful uses |
| Qwen3.5 | Apache 2.0 | ✅ Allowed | Most permissive, suitable for long-term projects |
| Qwen3 | Apache 2.0 | ✅ Allowed | Previous generation, same permissive license |

---

## 6.2 Large Model Cloud Alternatives

| Model | Purpose | Selection Rationale |
|-------|---------|---------------------|
| DeepSeek-V3 / R1 | Deep reasoning, comparison learning | Domestic, high cost-performance, strong reasoning |
| Qwen-Max / Plus | Chinese scenario deep generation | Alibaba official, well-optimized for Chinese |

**Shaping placeholder**: Specific API vendors and pricing schemes not finalized; "multiple model options" concept reserved.

**Boundary**: GPT series and other international models excluded from initial version; reassess independently if global expansion needed in the future.

---

## 6.3 Edge-Cloud Division Strategy

### 6.3.1 On-Device Inference (Primary)

- **Default enabled**: Out-of-box low-latency experience
- **Applicable scenarios**: Quick capture response, basic brainstorming dialogue, privacy-sensitive content, offline usage
- **Model size**: 2B-5B (Gemma-4-E2B/E4B or Qwen3.5-2B/4B)
- **Technical path**: GGUF via llama.cpp / ONNX Runtime (to be evaluated during implementation)

### 6.3.2 Cloud Inference (Alternative)

- **Explicit toggle**: User actively selects "deep mode"
- **Applicable scenarios**: Complex multi-angle expansion, long dialogue summarization, comparison learning "fine-tuned small model vs. default large model behavior"
- **Model size**: Large model APIs (DeepSeek/Qwen/GPT, etc.)

### 6.3.3 User Choice

- Initial shaping suggests "2-option" simplified interface:
  - Default: On-device small model (fast, private, offline)
  - Optional: Cloud large model (deep, comprehensive)
- Automatic switching or intelligent routing strategies not defined

---

## 6.4 Capability Extensions: Tools / skills+Tools / Multimodal

### 6.4.1 Initial Release Scope

- **Core capabilities**: Pure dialogue brainstorming + card harvesting
- **Not included**: Specific Tools invocation, third-party skill integration

### 6.4.2 Extension Placeholders

| Extension Direction | Current Status | Future Possibilities |
|---------------------|----------------|----------------------|
| **Tools invocation** | Shaping placeholder | Calendar, search, export, etc. |
| **Skills packages** | Shaping placeholder | Predefined domain capabilities (Notion export, mind maps, etc.) |
| **Multimodal** | Gemma-4 native Any-to-Any support | Image/audio input extension reserved |

### 6.4.3 Technical Path Shaping

- Specific implementation paths not defined (native function calling / prompt simulation)
- Gemma-4's Any-to-Any architecture reserves possibilities for future multimodal expansion

---

## 6.5 Fine-Tuning Strategy (Two-Stage Concept)

### 6.5.1 Stage 1: Foundation Fine-Tuning

- **Goal**: Teach model basic "brainstorming dialogue + summarization harvesting" capabilities
- **Data strategy**: Public datasets + small seed dataset
- **Output**: Usable small model foundation version

### 6.5.2 Stage 2: Personalization Fine-Tuning

- **Goal**: Learn user's personal style, common tags, association preferences
- **Data strategy**: User finalized cards (requires explicit privacy authorization)
- **Output**: Model version personalized for individual
- **Shaping placeholder**: Implementation timeline and technical details not defined

### 6.5.3 Boundaries

- Specific frameworks not defined (TRL / LLaMA-Factory / others)
- Hyperparameter grids and evaluation metric formulas not defined
- Training environment configuration (AutoDL / local / cloud) not defined

---

## 6.6 Relationship with Other Chapters

| Chapter | Related Content |
|---------|-----------------|
| `5_surface_EN.md` | Edge/cloud models deployed on this client form factor |
| `4_object_rule_EN.md` | Finalized cards can serve as Stage 2 fine-tuning data sources |
| `7_data_EN.md` (pending) | Public dataset recipes, user data training pool principles |

---

## 6.7 Boundaries and Non-Goals (This Section)

- **Not defined**: Specific model quantization format (GGUF Q4/Q8 / ONNX / TFLite) final selection
- **Not defined**: On-device inference framework (llama.cpp / ONNX Runtime / MediaPipe) final selection
- **Not defined**: Cloud API vendors and cost budgets
- **Not defined**: Fine-tuning specific tech stack, hyperparameters, evaluation metric formulas
- **Not defined**: Model version update strategy (Gemma 4 subsequent version tracking mechanism)
- **Not included**: Fine-tuning scripts, training pipelines, model evaluation code (Development phase deliverables)

---

## Document Relationships

| Document | Content |
|----------|---------|
| `shaping/5_surface_EN.md` | Client form factor, inference deployment pattern |
| `shaping/6_model_strategy_EN.md` | Model selection, edge-cloud division, fine-tuning strategy (this document) |
| `shaping/7_data_EN.md` (pending) | Dataset recipes, data flow and privacy |
