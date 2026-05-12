# Discussion Summary · 2026-05-12

This document summarizes the discussions and deliverables related to "confirming the three-month Sprint execution plan, landing it into the repository without editing the plan file, and archiving the conversation."

---

## 1. Phase Positioning

- The day moved from **aligning constraints and confirming the plan** to **materializing the agreed three-month Sprint plan as executable docs** in the repo (the plan file itself was not modified).
- Existing shaping (Chapters 3–10) remains the documentation baseline; shaping body text was not rewritten on this day.

---

## 2. Key Constraints Captured (from the user)

- **Time**: aim for ~20 hours per week.  
- **Budget**: uncertain; the assistant provided a rough GPU-hour cost range at ~2.88 CNY/hour (RTX 5090 32GB rental), plus a suggested total budget envelope split into training vs evaluation/API.  
- **Primary 3-month goal**: end-to-end pipeline + usable Android demo.  
- **Model spine**: `Gemma-4-E2B`; keep `Qwen3.5-2B` as a **risk-driven optional branch** for Chinese quality, not a default dual-spine.  
- **Parallelism**: month 1 training-focused; months 2–3 parallelize training and Android.  
- **Quality bar**: usable first, optimize later; **no mandatory** Stage 2 personalization within three months.  
- **Planning cadence**: one Sprint per month; allow slipping by 1–2 buffer Sprints; each Sprint must have crisp goals and deliverables.

---

## 3. Plan Gates (summary)

- **Sprint 1**: train the spine (PoC + Stage 1 baseline loop). **Gate1**: reproducible train/eval + loadable inference; no P0/P1 redlines; core capability at least "usable without regression."  
- **Sprint 2**: stabilize regression evaluation + Android minimal main path. **Gate2**: main path runs on a real device; no P0/P1 redlines.  
- **Sprint 3**: demo hardening + acceptance + milestone archive.  
- **Buffer Sprints**: BufferSprintA focuses on training/data/redline remediation; BufferSprintB focuses on demo stability and Chinese hardening; both forbid scope creep.

---

## 4. Repository Deliverables (created on this day)

| Path | Description |
|------|-------------|
| `execution/README_CN.md` | Execution overview, ordering, weekly rituals |
| `execution/sprint-1-train.md` | Sprint 1 weekly breakdown, Gate1, risks |
| `execution/sprint-2-demo.md` | Sprint 2 eval stabilization + Android path, Gate2 |
| `execution/sprint-3-acceptance.md` | Sprint 3 acceptance + milestone archive |
| `execution/buffer-sprint-policy.md` | Buffer sprint triggers, allowed/forbidden work, budget guardrails |

**Note**: Per instructions, `.cursor/plans/three-month_sprint_plan_f8c3b767.plan.md` was **not edited**.

---

## 5. Plan To-dos (session outcome)

These four items were driven to **completed** during the implementation pass:

- `sprint1-train`  
- `sprint2-demo`  
- `sprint3-acceptance`  
- `buffer-policy`  

---

## 6. Logs / Archives (this round)

- `log/2026-05-12-complete_CN.md`: full conversation archive (rounds + appendices).  
- `log/2026-05-12-summary_CN.md`: Chinese summary.  
- `log/2026-05-12-summary_EN.md`: this English summary.

---

## 7. Recommended Next Steps

1. Start **Week 1 of Sprint 1** from `execution/sprint-1-train.md`, and optionally keep a weekly note under `log/`.  
2. Cross-check `shaping/7_data_CN.md` `v1.0` freeze assumptions against Sprint 1; log any deltas in the next log entry.  
3. Run **Gate1** before leaving Sprint 1; if it fails, enter a buffer sprint per `execution/buffer-sprint-policy.md`.

---

*Document generated in project `log/` directory for personal learning and project advancement.*
