# 2026-05-17 Work Summary

## Sprint 1 Week 2 PoC Completed ✅

### Key Achievements
- **PoC Training Completed**: 6.4 minutes on RTX 5090, loss=1.93, LoRA weights 5.14MB
- **Layer 2 Evaluation**: 480/500 samples completed, 99.8% success rate
- **Decision ACCEPT**: Training pipeline verified, proceed to Stage 1

### Key Metrics Comparison

| Subset | Baseline | PoC | Change |
|--------|----------|-----|--------|
| core | 93.35 | 80.68 | -13.6% ⚠️ |
| general | 81.85 | 67.23 | -17.9% ⚠️ |
| zh_guard | 77.94 | 44.71 | -42.6% ❌ |
| **Overall** | **85.67** | **69.06** | **-19.4%** |

### Main Issue
- **zh_guard Severe Degradation**: Chinese protection layer dropped 42.6%, needs priority fix in Stage 1

### Improvements for Stage 1
1. Chinese data ratio: 40% → 50%+
2. Training epochs: 1 → 2-3
3. Try larger LoRA rank (8→16)

### Documentation Output
- Training script explanation (added background + results)
- AutoDL environment guide (updated 5090 32GB, ModelScope)
- PoC evaluation report (comparison analysis + decision)

### Time Investment
~4 hours (training 30min + judging 60min + documentation 2h)
