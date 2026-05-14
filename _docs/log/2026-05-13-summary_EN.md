# Discussion Summary · 2026-05-13

This entry covers **Sprint 1 Week 1** work: the Layer 2 **manifest**, clarifications on baseline-report wording, Week 1 completion status, experiment metadata templates, the **eval venv** and **smoke inference** script, Hugging Face **token / China mirror**, and recording smoke outputs into **`META.json`** plus updating the baseline experiment **README** checklist.

---

## 1. Phase Positioning

- Moved from “data + shaping docs” toward an **executable Layer 2 manifest**, **eval dependency stack**, **smoke runner**, and **experiment-folder metadata**.  
- A **full 500-item baseline run** and **`s1-baseline-report` sign-off** are still outstanding.

---

## 2. Q&A Highlights (condensed)

| Topic | Takeaway |
|------|-----------|
| What “Manifest” means | A versioned Layer 2 **item list** (JSONL): IDs, strata, `messages`, provenance — for reproducible eval. |
| Is Week 1 fully done? | **No.** Manifest + protocol skeleton are in place; full run + finalized report remain. |
| Metadata template | `experiment/_template` + `META.json` conventions; `baseline-gemma4e2b-it-layer2-v0` is a concrete eval-only example. |
| Script location | Keep **`scripts/layer2_smoke_infer.py`** at repo root; no need to nest it under a specific experiment folder. |
| Separate venv for eval? | **Yes, recommended** vs the data pipeline; `requirements-eval.txt` + `experiment/README.md` now mirror the `data_pipeline` install style. |
| Gemma loading errors | For **text-only** Layer 2, use **`AutoTokenizer`** (not `AutoProcessor`) to avoid pulling **torchvision / PIL** for unused multimodal processors. |
| HF warning & China mirror | Set **`HF_TOKEN`** for rate limits / gated assets; use **`HF_ENDPOINT=https://hf-mirror.com`** for faster downloads in mainland China; the smoke script loads repo-root **`.env`** via **python-dotenv**. |

---

## 3. Repository Deliverables (this day)

| Kind | Path (representative) |
|------|-------------------------|
| Manifest | `data/eval/layer2/manifest_v0.jsonl`, `manifest_meta.json` |
| Builder | `scripts/build_layer2_manifest.py` |
| Eval runner & deps | `scripts/layer2_smoke_infer.py`, `requirements-eval.txt` |
| Docs | `_docs/eval/layer2/README.md`; `experiment/README.md` (incl. HF); cross-links in `data_pipeline/README*.md` |
| Templates & instance | `experiment/_template/*`, `experiment/baseline-gemma4e2b-it-layer2-v0/*` |
| Smoke output (user machine) | `.../results/smoke_infer_20260513T1556Z.jsonl` (referenced from `META.json`) |

---

## 4. Plan / Todo Status (relevant items)

- `layer2-manifest`, `meta-template`, `env-smoke`: marked **completed** in-repo / in the sprint plan after manifest land + templates + successful small-batch smoke + `META.json` backfill.  
- `s1-baseline-report`: still **WIP**; §0 smoke row updated to **passed (small sample)**; full Layer 2 run + §5–§7 numbers + final status still TODO.  
- `baseline-full-report`, `week2-handoff`, etc.: remain follow-ups.

---

## 5. Recommended Next Steps

1. Keep the eval venv aligned with **`pip install -r requirements-eval.txt`**.  
2. Record **`base_model.revision`** (HF commit) in `META.json` and `s1-baseline-report_CN.md` §2.  
3. Run **all 500** manifest lines (`--limit 500`, `max_new_tokens=2048` per frozen §4), write outputs, and fill the baseline report.  
4. If you upgrade manifest sources to true X-AlpacaEval / CMT-Eval, **bump** manifest version (e.g. `layer2-v1`) and re-baseline.

---

## 6. Logs (this round)

- `_docs/log/2026-05-13-complete_CN.md`: **verbatim export** of the Cursor agent transcript for session `72573b9b-ab79-4d5f-b76b-489ac46bece4` (278 `user`/`assistant` messages in original order, including earlier Sprint 1 Week-1 checklist discussion and later manifest/smoke/HF work — **not** a hand-summarized digest).  
- `_docs/log/2026-05-13-summary_CN.md`: Chinese summary.  
- `_docs/log/2026-05-13-summary_EN.md`: this English summary.

---

*Document generated in project `_docs/log/` for personal learning and project advancement.*
