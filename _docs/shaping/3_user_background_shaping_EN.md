# 3. Users and scenarios (Who / When)

> This document describes the project at the **shaping** stage: users, roles, account principles, usage contexts, and primary journeys. It **does not** lock the final client form factor (e.g. Kotlin Android app vs WeChat mini program—see a dedicated chapter). It **does not** commit to offline support, accessibility, or internationalization for the first version.

---

## 3.1 Users and scale (Who)

- **Primary user**: You—owning product definition, learning the full loop of **fine-tuning → evaluation → serving → iteration**, and day-to-day personal use.
- **Secondary users**: Friends invited to a private beta; **capacity assumption ~100 people** (small-team beta scale; this document does not specify performance targets).
- **Data isolation**: **One account maps to one isolated data space**; users only see their own inspiration cards, conversations, tags, links, and session-related assets. There is **no** default “shared inspiration wall for everyone” (unless scoped as a separate initiative later).

---

## 3.2 Roles: regular users and beta admins (Who · permission boundary)

### Regular users (beta testers)

- Use core product capabilities: quick capture, brainstorm, cards and links, history, etc. (subject to what is actually enabled).
- **By default** they **cannot** view other users’ content.

### Beta administrators (recommend at least one—typically you; optionally a few trusted co-admins)

- **Responsibilities (platform and beta governance)**: Grant or revoke **beta access** (invite codes, allowlists, account bans); handle **abuse and anomalies** (spam signups, attacks, policy violations); publish **beta announcements** (maintenance windows, rule updates); view **aggregate health signals** (e.g. signup counts, error rates, API availability—**without** reading user inspiration body text).
- **Principles (privacy and trust)**: Admins **do not**, by default, read users’ inspiration content, full chat logs, or brainstorm session summaries. If future **legal process** or **explicitly user-authorized** support workflows require access to content, that should be **a separate chapter**: scope, approval, and audit trails.
- **Relationship to regular users**: An admin account **may also** act as a normal user (using the product personally), but **platform administration** and **personal use** are conceptually separated to avoid the habit of “using admin rights to casually browse data.”

---

## 3.3 Account system (Who · identity and lifecycle)

> This section states **principles and lifecycle** only, not specific login vendors (WeChat, SMS OTP, email, etc.—see “Client form factor and account implementation choices”).

- **Signup and beta gating**: During beta, **an account is required**; new accounts should be tied to **invite code / allowlist / admin provisioning** to avoid open registration being abused.
- **Login and identity**: Users authenticate in a standard, auditable way; credentials and tokens follow common security practice (implementation is out of scope here).
- **Multi-device**: If the same account is used on multiple devices, **the server is the source of truth**; clients display synchronized results (sync details are defined at implementation time).
- **Account and data rights (baseline)**: Provide a path for **account deletion / erasure of personal data** (scope and cooling-off periods can be detailed in compliance docs); controls for “use my data for model improvement” should align with the privacy and data chapter.
- **Session and security narrative**: Re-authentication after long idle periods, second confirmation for sensitive actions, etc.—follow common industry practice at implementation time.

---

## 3.4 Scope of this section (vs client form factor)

- **Client form factor** (Kotlin Android app, WeChat mini program, or other) is **not locked here**; this section describes **who**, **in what situations**, performs **which inspiration-related behaviors**. Distribution channels and store policies are decided in a dedicated chapter.

---

## 3.5 Product scope (scenario-relevant)

- **Scope**: Focus on **“generating inspiration”** and **“connecting inspiration”**; a **clean inspiration editor**, not a general-purpose workbench.
- **Model capabilities (scenario level)**: Brainstorming, natural dialogue, summarization; room for **Tools / skills+Tools**; **optional multiple models** (stronger cloud vs smaller models) for **user choice** and **your learning comparisons**; **no** fixed list of model names or on-device deployment here.

---

## 3.6 Core scenarios and two primary modes (When / primary journeys)

Field-level rules and state semantics for inspiration cards (finalization, tags, links) are in **`shaping/4_object_rule_EN.md`**.

### Primary-screen information architecture (shaping)

- The home experience centers on **two primary actions**: **Quick capture** and **Brainstorm**.
- Everything else (history, search, settings, feedback, etc.) is **secondary** (small buttons, icons, overflow menus, or hidden tiers) to avoid cognitive overload.

### Mode A: Quick capture

- **Context**: Short moments to capture a thought quickly.
- **Behavior**: The user can stop after jotting down an idea.
- **Default**: **Save as draft**; no requirement to fill title, tags, links, or enter a dialogue on the spot.
- **Evolution**: The draft can be edited later or flow into a brainstorm and then be harvested into cards (an explicit “upgrade to brainstorm” control can be **Later**; v1 can also enter brainstorm only from a list entry).

### Mode B: Brainstorm

- **Context**: A contiguous block of time for exploratory dialogue and convergence.
- **Behavior**: Multi-turn brainstorm → harvest inspiration cards → **confirm and finalize snapshots** per `4_object_rule_EN.md`.
- **Provenance and process assets**: **Source summary** (short provenance) and **session / discussion summary** (substantive summary of the discussion) are **separate** display and storage concepts; cards **may link** to the session summary; multiple cards harvested from one session **may share** the same session summary.

### Tags and links (one sentence at scenario level)

- Tags support search and clustering; links support explicit reasons why “this card belongs with that”; the six link types and tag details are in Chapter 4.

### User value of “connecting inspiration” (narrative)

- Surface recurring themes, bridge weak ties, see how ideas evolve over time, rediscover forgotten half-finished notes and “islands” on the graph—this section keeps the narrative only, not algorithms.

---

## 3.7 Secondary scenarios

- **History**: Browse and retrieve saved content and related entry points.
- **Feedback**: Reserve a conceptual slot for **explicit feedback or gating** toward phase-two **training candidate pools / personalization** (triggers defined elsewhere).

---

## 3.8 Granularity of “When”

- This section **does not** set KPIs (frequency, session length, etc.).
- **Context** is carried by the two primary modes: **mobile fragmented time** vs **continuous focused time**.

---

## Document map

| File | Contents |
|------|----------|
| `shaping/3_user_background_shaping_EN.md` | Users, roles, accounts, scenarios, primary modes (this document) |
| `shaping/4_object_rule_EN.md` | Inspiration cards, tags, link semantics, finalization and snapshots |

Chinese counterparts: `shaping/3_user_background_shaping_CN.md`, `shaping/4_object_rule_CN.md`.
