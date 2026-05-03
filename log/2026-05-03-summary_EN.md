# Session summary · 2026-05-03

This note captures the day’s discussion and written outputs on **project shaping: users/scenarios (Ch. 3) and core objects/rules (Ch. 4)**. Use it for tomorrow’s review and for continuing other chapters.

---

## 1. Phase placement

- Work stayed in **shaping**: objects, boundaries, and semantics—**no** implementation detail (commands, schemas, specific framework versions).
- Plan: **review tomorrow**, then continue with further modules.

---

## 2. Chapter 3: Users and scenarios (Who / When) — locked points

### 2.1 Users and scale

- **Primary user**: You (learning + personal closed loop).
- **Secondary users**: Invited beta testers; **~100 people** assumed; **per-account data isolation**.

### 2.2 Roles and accounts (best-practice shaping)

- **Regular users**: Cannot browse others’ content by default.
- **Beta admins**: Grant/revoke access, handle abuse, announcements, aggregate health metrics; **by default do not read** user inspiration bodies, full chats, or session summaries; legal or explicitly authorized support flows need a **separate chapter**; separate admin acts from personal use conceptually.
- **Account system**: Beta gating (invite / allowlist / admin provisioning); **server is source of truth**; account deletion / personal data erasure path; align “use data for model improvement” with the privacy chapter; **no** specific login vendor in Ch. 3.

### 2.3 vs client form factor

- **Do not lock** Kotlin app vs WeChat mini program (etc.) in Chapter 3; choose in a dedicated chapter (you still want to compare options later).

### 2.4 Product scope and models (scenario level)

- Focus **“generate inspiration”** and **“connect inspiration”**; keep the editor clean.
- Small-model narrative: brainstorm, dialogue, summarization, Tools/skills+Tools; **optional multiple models** (cloud “large” vs smaller) for user choice and learning comparisons; **no** fixed model list or on-device decision here.

### 2.5 Two primary modes and home IA

- **Quick capture**: fragmented time, **default draft**, can stop immediately.
- **Brainstorm**: contiguous time, multi-turn dialogue, harvest cards and finalize per Chapter 4.
- **Home**: **two primary actions** (quick capture, brainstorm); everything else secondary or hidden.

### 2.6 Provenance and process assets (one line)

- **Source summary** (short) vs **session / brainstorm summary** (substantive)—**separate**; cards may link to session summary; multiple cards from one session may share one summary.

### 2.7 Secondary scenarios and “When” granularity

- History; feedback slot for phase-two training pools.
- **No KPIs** in this chapter; contexts map to fragmented vs focused time.

### 2.8 Explicitly out of scope (day’s agreement)

- **Offline, accessibility, internationalization** not first-version commitments in this section.

---

## 3. Chapter 4: Core objects and rules — locked points

### 3.1 Inspiration card fields (required)

- **Title, body, tags, links, source summary, status (draft / finalized)**.
- Body need not equal full chat; **finalization** means accepting the **distilled** card, not verbatim dialogue.

### 3.2 Link semantics (six types)

- **Related** (undirected), **Extends** (A→B), **Supports** (directed—pick **one** consistent direction before implementation), **Tension/contrast** (undirected), **Merge candidate** (undirected), **Derived from dialogue** (directed vs undirected TBD).
- User-drawn edges always allowed; system suggestions prefer cards under the **latest confirmed finalized snapshot**; persist after user confirmation; at finalize, only edges **still on screen** enter the snapshot.

### 3.3 Tag rules

- Short tags, soft caps, normalization at implementation; user tags authoritative; model suggestions enter snapshot only after adoption (including “unchanged at finalize counts as adoption”); clear division of labor vs links.

### 3.4 Finalization and snapshots

- **Finalized = state after explicit confirm**; confirm instant freezes **title, body, tags, links, source summary** as the **finalized snapshot**.
- Title non-empty at finalize (model may propose); empty tags → model may fill; links may be model-suggested—**set at confirm instant** wins.
- **Editable after finalize**; until **Confirm** again, edits are an **unconfirmed draft layer** vs the last snapshot; outward-stable behavior uses the **latest confirmed finalized snapshot**; re-confirm advances the snapshot.

### 3.5 Diagrams

- Chapter 4 includes Mermaid: **object relationships**, **dual-mode primary path**, **sample link graph**, **state machine**, **snapshot vs unconfirmed edits**.

---

## 4. Written artifacts (first drafts)

| Path | Note |
|------|------|
| `shaping/3_user_background_shaping_CN.md` | Chapter 3 CN |
| `shaping/3_user_background_shaping_EN.md` | Chapter 3 EN |
| `shaping/4_object_rule_CN.md` | Chapter 4 CN (+ Mermaid) |
| `shaping/4_object_rule_EN.md` | Chapter 4 EN (+ Mermaid) |

---

## 5. Relation to 2026-05-02 summary

- **2026-05-02** captured two-stage fine-tuning, dataset pointers, and an earlier product form bias (mini program + API). **2026-05-03** writes **users/scenarios** and **cards/tags/links/finalization** into shaping files and **does not lock the client** in Chapter 3. If older notes conflict, **prefer the latest shaping markdown**; reconcile “client form factor” in one dedicated chapter later.

---

## 6. Suggested next steps (tomorrow and after)

1. **Review** `3_user_background_shaping_CN.md` and `4_object_rule_CN.md` for inconsistencies, over/under-specification.  
2. **Cross-links**: if files are renamed, update in-doc links and the table above.  
3. **Next shaping module** (pick one): client form factor + account implementation, privacy + training candidate pool, or minimal API contract.

---

*Generated under the project `log/` directory for personal learning and project continuity.*
