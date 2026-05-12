# 5. Surface (Product Form Factor)

> This document is part of the project **shaping** phase: defining client-side form factor, inference deployment patterns, and key decision rationale. **Does not include** specific technical implementation details, Android version compatibility matrix, or app store publishing timeline.

---

## 5.1 Client-Side Form Factor (Decision Finalized)

### 5.1.1 Primary Form Factor

- **Form**: Native Android application in Kotlin
- **Excluded options**: WeChat Mini Program, Pure Web, Kotlin Multiplatform

### 5.1.2 Decision Rationale

| Dimension | Kotlin Native Android | WeChat Mini Program | Pure Web / PWA |
|-----------|----------------------|---------------------|----------------|
| **On-device model deployment** | ✅ Fully controllable, local inference feasible | ❌ Nearly infeasible, primarily cloud API dependent | ⚠️ WebAssembly/WebGPU emerging, compatibility to be verified |
| **Privacy & offline** | ✅ Data can stay on-device, offline usage supported | ❌ Data must upload, network dependent | ⚠️ Limited offline capabilities |
| **System-level capabilities** | ✅ Notifications, quick input, background services | ❌ Restricted | ❌ Restricted |
| **Global distribution** | ✅ Google Play worldwide | ❌ WeChat ecosystem mainly Chinese users | ✅ Browser universally available |
| **Developer experience** | ✅ Existing Kotlin experience, gentle learning curve | ⚠️ Must learn Mini Program framework | ⚠️ Different on-device inference stack |
| **Performance** | ✅ Optimal | ⚠️ Limited by WeChat Runtime | ⚠️ Limited by browser performance |

**Core decision logic**:
- Local model deployment is the core goal of this fine-tuning project; Mini Programs / Pure Web cannot satisfy this
- Global availability via Google Play without single-ecosystem lock-in
- Developer has existing Kotlin experience, PoC risk is manageable

### 5.1.3 iOS Strategy

- **Scope for initial release**: iOS client excluded
- **Future evaluation**: If iOS version needed, independently evaluate:
  - **Option A**: Native Swift development (optimal experience, separate codebases)
  - **Option B**: Reassess Kotlin Multiplatform / Compose Multiplatform maturity for code sharing

---

## 5.2 Inference Deployment Pattern (Edge-Cloud Hybrid)

### 5.2.1 On-Device Inference (Primary)

- **Positioning**: Enabled by default, providing "out-of-box" low-latency experience
- **Applicable scenarios**: Quick response, basic brainstorming, privacy-sensitive, offline available
- **Model size**: Small-parameter models (0.5B - 3B)
- **Technical path**: GGUF via llama.cpp, or ONNX via ONNX Runtime, or TFLite (to be evaluated during implementation)

### 5.2.2 Cloud Inference (Alternative)

- **Positioning**: Explicit toggle entry point for deep generation and user learning comparison
- **Applicable scenarios**: Complex reasoning, long text summarization, multi-angle ideation
- **Candidate models**: DeepSeek, Qwen, or other large models via API
- **User value**: Satisfies the learning goal of "comparing fine-tuned small model vs. default large model behavior"

### 5.2.3 Hybrid Logic (Shaping Placeholder)

- Initial shaping **does not finalize** specific switching strategy (auto-fallback / manual toggle / intelligent routing)
- Conceptual placeholder reserved: users can perceive two modes — "edge fast response" and "cloud deep capability"

---

## 5.3 Relationship with Other Chapters

| Chapter | Related Content |
|---------|-----------------|
| `3_user_background_shaping_EN.md` | Dual primary modes (Quick capture, Brainstorming) implemented on this client form factor |
| `4_object_rule_EN.md` | Persistence and synchronization strategy for inspiration cards, finalization snapshots constrained by this form factor |
| `6_model_strategy_EN.md` (pending) | Edge/cloud model selection, Tools extension requirements landed within this form factor |

---

## 5.4 Boundaries and Non-Goals (This Section)

- **Not defined**: Specific Android version compatibility (suggest Android 8+ or 10+, to be defined during implementation)
- **Not defined**: App store review timeline and distribution strategy (planned separately)
- **Not defined**: Kotlin Multiplatform cross-platform roadmap (initial release focuses on Android single platform)
- **Not defined**: Final on-device inference framework selection (llama.cpp / ONNX Runtime / TFLite to be evaluated during implementation)
- **Not included**: UI design artifacts, interaction flow diagrams (produced during PoC / Development phase)

---

## Document Relationships

| Document | Content |
|----------|---------|
| `shaping/3_user_background_shaping_EN.md` | Users, scenarios, dual primary modes |
| `shaping/4_object_rule_EN.md` | Inspiration cards, tags, associations, finalization rules |
| `shaping/5_surface_EN.md` | Client form factor, inference deployment pattern (this document) |
| `shaping/6_model_strategy_EN.md` (pending) | Model selection, fine-tuning strategy, capability extensions |
