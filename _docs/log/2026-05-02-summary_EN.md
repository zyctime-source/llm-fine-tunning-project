# Session summary · 2026-05-02

This note captures the day’s discussion on **small-model fine-tuning + inspiration / brainstorm product shape**, for continuity in later work.

---

## 1. Background and goals

- Interest in **fine-tuning** large models; focus on **smaller-parameter** models (e.g. Gemma E2B/E4B, Qwen 3.4 0.8B/2B—subject to official cards and licenses).
- Long-term use in **on-device or lightweight** settings; training planned on **rented GPUs via AutoDL** for cloud fine-tuning.
- **Languages**: Chinese–English mix.
- One project goal: **learn the full fine-tuning loop end to end** (data → train → evaluate → deploy / iterate).

---

## 2. Product form evolution

### 2.1 Early idea (since revised)

- Considered a **Kotlin + Android Studio** native app for Android and Huawei HarmonyOS, with **on-device** small models; features: capture inspiration, tags, graph-like links between similar ideas, voice/text chat, local storage of chats and summaries.
- Conclusion: a **first “graph” version** is more realistic with **embedding similarity edges**, not a full GNN from day one.

### 2.2 Current consensus (shift of focus)

- **No longer center** on long-cycle native app development as the main bet.
- **Shape**: **WeChat mini program** for UX (inspiration, chat, display); **small model served via API** on the server, **mobile clients call over the network**, **full weights not shipped on phone**.
- **Pros**: less build effort, faster iteration, many device types inside WeChat; model updates without users downloading large weights; fits **periodic fine-tuning on server-stored dialogue**.
- **Tradeoffs**: data and inference in the cloud—**privacy story** moves from “all local” to “cloud + controllable personalization”; API cost, auth, weak networks; WeChat mini program **AI categories and review** need an explicit check against platform rules.
- **Stack note**: Kotlin native can remain an **extension** later, not the **main line** for this phase.

---

## 3. Fine-tuning strategy: two phases

### Phase 1 — Task-oriented: stronger brainstorming / distilling inspiration

- **Why**: Small base models are not strongly biased toward “help me brainstorm and distill”; **SFT/LoRA** on public data can sharpen that.
- **Data bias**: Use datasets like **`brainstorm_vicuna_10k`** (Hugging Face: `DevQuasar/brainstorm_vicuna_10k`) and similar **brainstorm / human–model dialogue** data; same family includes Markdown-summary variants (e.g. `brainstorm-v3.1_vicnua_1k`) closer to “post-dialogue tidy-up.”
- **Caveat**: Much of this is **English and synthetic**; if the product is mainly Chinese, plan **mixed Chinese–English or extra Chinese brainstorm/summary** data to avoid skewed skills.
- **Output shape**: Align early—mostly free chat, or a fixed **title / bullets / tags** structure so mini program persistence fields match.

### Phase 2 — User-oriented: personalization (“knows you better over time”)

- **Idea**: After real use, **high-quality records from the mini program** (chats, adopted inspiration summaries) feed **periodic fine-tuning** (e.g. every two weeks or after **N** accumulated items) to tune tone, follow-up habits, summary style, etc.
- **Engineering**: Keep **task LoRA** and **personal LoRA** **separate** so you can roll back the “personal layer” without losing the brainstorm base; **mix in general high-quality data** during training to reduce catastrophic forgetting.
- **Data quality**: Prefer **adopted summaries**, **user-marked “good” turns**, or **human-reviewed batches** for the training pool to cut noise.
- **vs RAG**: Long-lived facts and old inspirations fit **structured storage + retrieval**; fine-tuning focuses on **how to speak, ask, and summarize in your voice**.

### Product principles (confirmed that day)

- **Personalization first**: default is **allow user data to improve the model** (phase-two fine-tuning).
- **Engineering guardrails** (without changing “personalization first”):
  - **Informed and in control**: explain how data is used; offer **opt-out of training** or **delete training-related data**.
  - **Security**: HTTPS, encryption at rest, account and data isolation.
  - **Compliance and review**: WeChat mini program AI categories and content rules need a dedicated pass.

---

## 4. “Too little data” and public datasets

- **Issue**: Day-to-day use yields **limited high-quality paired** data; self-collection alone may not suffice for a strong SFT round.
- **Tactics**:
  - **Mixed training**: large general instruction base + a small amount of curated personal data.
  - **Synthetic data**: stronger models generate “fragment → follow-ups → structured inspiration” samples under fixed system prompts, then spot human review.
  - **Cadence**: avoid rigid “every two weeks”; prefer **train after N reviewed samples** accumulate.

### Hugging Face dataset links collected that day (excerpt—verify licenses yourself)

| Type | Dataset | URL |
|------|---------|-----|
| Dialogue summarization | DialogSum | https://huggingface.co/datasets/knkarthick/dialogsum |
| Dialogue summarization | SAMSum | https://huggingface.co/datasets/Samsung/samsum |
| Brainstorming | brainstorm_vicuna_10k | https://huggingface.co/datasets/DevQuasar/brainstorm_vicuna_10k |
| Brainstorm + summary | brainstorm-v3.1_vicnua_1k | https://huggingface.co/datasets/DevQuasar/brainstorm-v3.1_vicnua_1k |
| Brainstorming | brainstorm-v2.1_vicuna_1k | https://huggingface.co/datasets/DevQuasar/brainstorm-v2.1_vicuna_1k |
| Dolly brainstorm subset | dolly_brainstorming | https://huggingface.co/datasets/lionelchg/dolly_brainstorming |
| Chinese writing | COIG-Writer | https://huggingface.co/datasets/m-a-p/COIG-Writer |
| Chinese creative (small) | creative_writing | https://huggingface.co/datasets/telecomadm1145/creative_writing |
| English creative mix | ember-dataset | https://huggingface.co/datasets/sparrowaisolutions/ember-dataset |
| General instructions | Alpaca | https://huggingface.co/datasets/tatsu-lab/alpaca |

---

## 5. Concept check: why still fine-tune for “summary / rewrite / translate”?

- Base **Instruct/Chat** models + prompts often already do generic summary, rewrite, and translation.
- **Fine-tuning value** is more often: **fixed formats, brand voice, domain terms, Chinese–English habits, distilling a large model on a narrow task**—not “teaching summary from scratch.”
- For this project: **phase one** sharpens **brainstorm and inspiration distillation**; **phase two** sharpens **personal style and habits**.

---

## 6. What edge small models can do (for later choices)

- **Good at**: short summaries, rewrite, sentence-level translation, light dialogue, simple structured extraction, local processing when privacy matters (if you return to on-device later).
- **Not a sole solution for**: hard facts, live information (needs retrieval), long complex reasoning; multimodal needs separate modules.

---

## 7. Hugging Face plugins (summary of that day’s explanation)

- Use **`/`** or auto-matched **Skills**: `hf-cli`, dataset viewer/create, **Jobs** cloud runs, **TRL** fine-tuning (SFT/DPO, etc.), eval cards, **Trackio**, **Gradio**, etc.
- **HF token / auth** must be configured per environment before Hub/Jobs (per plugin and MCP docs).

---

## 8. Conversation logs and knowledge capture

- Agreed to capture conclusions in **project log files** (e.g. this `log/` folder) for cross-session continuity.
- You wanted daily chats saved; **this file** is the structured day summary, complementary to Cursor chat history.

---

## 9. Suggested next steps

1. Freeze **V1 data recipe**: share of `brainstorm_vicuna_10k` + whether to add Chinese / dialogue-summary subsets + general base mix.  
2. Define **minimal API** (e.g. brainstorm session, save inspiration, fetch history) and **must-have mini program screens**.  
3. Write down **triggers for “enter training candidate pool”** (saved inspiration, likes, explicit “help improve model,” etc.).  
4. Run **phase-one LoRA** once on AutoDL and lock in **a few Chinese and a few English eval cases**; log in the next day’s note.

---

*Generated under the project `log/` directory for personal learning and project continuity.*

Chinese counterpart: `log/2026-05-02-summary_CN.md`.
