# Sprint 1 Data Specification: `v1.0` (s1-data-v1.0-spec)

| Attribute | Value |
|-----------|-------|
| **Data Version** | `v1.0` |
| **Document Version** | 1.4 |
| **Status** | Frozen (recipe + local snapshot rules); **Custom seed 500 explicitly skipped** (see §1, §2, §4.5.2) |
| **Aligned with shaping** | [_docs/shaping/7_data_EN.md](../shaping/7_data_EN.md) §7.3.1 |
| **Pipeline Code** | Repository `data_pipeline/` (generation scripts); this spec describes **content and traceability**, not implementation details |
| **Code Snapshot (Reproducible)** | Git `HEAD` = `23bd3f6e2eee153e38ed60c3d8cc35639d21d915` (repository commit at time of recording; for replay, fix to this commit or equivalent tag; **update this line with your local `git rev-parse HEAD`**) |

---

## 1. What `v1.0` Means (Frozen Granularity)

**Frozen:**

1. **Recipe Table**: Subset names, target counts, and proportions (consistent with §2).
2. **Source Datasets**: Hub `repo_id`, local disk paths, shard counts / sampling parameters recorded in `download_meta.json`.
3. **Training Subset Construction Rules**: How to extract **5k + 5k + 3k (general training block)** from full `train` and translation outputs (see §4); rules are deterministic algorithms, not "verbal agreements".
4. **General Mixed (Train + Validation)**: `download` defaults to sampling **2000 EN + 2000 ZH** (`seed=42`), then tail-splitting by language into **1000** for **`general_mixed_validation.jsonl`**, and the remaining **3000** for **`general_mixed_train.jsonl`** (see §3.3). `GENERAL_VAL_N=0` falls back to single `general_mixed.jsonl` (not recommended, legacy compatibility only).
5. **Brainstorm Validation Export**: After §4.1 training head, take **3000** valid `train.jsonl` rows (disjoint from **\(S\)**), and write aligned validation set from `brainstorm_vicuna_10k_zh.jsonl` by **`id`** (see §3.5, §4.4); **not merged** into 13k training recipe.

**Not Frozen / To Be Completed (Does not block Week2 PoC from reading spec, but recommended before Gate1):**

- **Custom Seed 500**: Not yet persisted; §4.5.1 provides creation guide. **Current decision: no data, skip this phase** (see §4.5.2); does not block PoC / Stage1 mainline, only note **`data_profile=v1.0-skip-seed`** (or equivalent field) in experiments and reports to distinguish from "full 13.5k" shaping ideal recipe.
- **HF `revision`**: `brainstorm` currently `null` (default branch snapshot); on next full download, recommend writing specific `revision` to `download_meta.json` for long-term bitwise reproducibility.

---

## 2. Recipe Summary Table (Consistent with shaping 7.3.1)

| Subset | Target Count | Proportion | Description |
|--------|--------------|------------|-------------|
| brainstorm_vicuna_10k (English original) | 5,000 | 35% | Core brainstorming (English) |
| brainstorm_vicuna_10k (Qwen translated Chinese) | 5,000 | 35% | Parallel Chinese with **same `id` alignment** as English subset |
| Alpaca / ShareGPT (EN-ZH mixed general, **train**) | 3,000 | 25% | Written by `download` to `general_mixed_train.jsonl` (disjoint IDs from validation block) |
| Custom seed data (personal creative cases) | 500 (shaping target) | 5% | **Currently skipped: 0**; once available, persist to `data/raw/seed_v1.0/` per §4.5.1 |
| **Total (shaping target)** | **13,500** | **100%** | Design total target |
| **Total (currently trainable subsets)** | **13,000** | ≈96.3% | **5k EN + 5k ZH + 3k general**, no seed; consistent with "skip seed" decision |

**Validation Sets (Default, not counted in "trainable 13k" above)**

| Name | Target Count | Generation Method | Description |
|------|--------------|-------------------|-------------|
| General mixed validation | 1,000 | `python -m data_pipeline download` (`GENERAL_VAL_N>0`) | `general_mixed_validation.jsonl`, disjoint IDs from `general_mixed_train`, §3.4 |
| Brainstorm validation (EN+ZH aligned) | 3,000 (English window) | `python -m data_pipeline export-brainstorm-val` | `validation_en.jsonl` + `brainstorm_vicuna_10k_zh_validation.jsonl`, disjoint from training set **S**, §3.5, §4.4; when translations incomplete `written_zh` may be less than `written_en`, see `brainstorm_validation_meta.json` |

`GENERAL_VAL_N=0` produces no "general validation" file, only legacy single `general_mixed.jsonl` (not recommended).

**Naming Recommendation**: In training experiment `META.json` / README, specify `data_version=v1.0` and `seed_block=skipped` (or `data_profile=v1.0-skip-seed`) to avoid confusion with "seed-inclusive" runs later.

---

## 3. Local Artifacts and Traceability Pointers

Default **`DATA_ROOT=./data`** (relative to repository root). If you use a different root, adjust paths below accordingly.

### 3.1 Brainstorm Main Set (HF Export)

| Item | Value |
|------|-------|
| Hub `repo_id` | `DevQuasar/brainstorm_vicuna_10k` |
| `revision` (at recording) | `null` (see `data/raw/brainstorm_vicuna_10k/download_meta.json`) |
| `train` rows | 10,000 |
| `test` rows | 1,000 (**not included in v1.0 training recipe by default**; reserved for evaluation or other split strategies) |
| Local path | `data/raw/brainstorm_vicuna_10k/train.jsonl`, `test.jsonl` |
| Metadata | `data/raw/brainstorm_vicuna_10k/download_meta.json` |

**Note (optional artifact):** **`validation_en.jsonl`** is produced by **`export-brainstorm-val`**, **not** by **`download`**; default path and rules see §3.5, §4.4.

### 3.2 Brainstorm Chinese Translation (Cloud Qwen)

| Item | Value |
|------|-------|
| Pipeline | `python -m data_pipeline translate` (see [data_pipeline/README.md](../../data_pipeline/README.md)) |
| Local path | `data/processed/brainstorm_vicuna_10k_zh.jsonl` |
| Row structure | Each row contains `id`, `conversations_zh`, `conversations_en`, etc.; **training uses Chinese turns from `conversations_zh`**; `from` already aligned with English (see `conversation_format.apply_original_speaker_roles_to_translated_turns`) |
| API / Model | Configured in `.env` via `DASHSCOPE_*`, `TRANSLATE_MODEL` (**do not commit keys to repository**); experiment records should separately note "model name + date" |

**Note:** Translation file row count may be ≥ 5,000 (e.g., nearly full `train` translated); **v1.0 training Chinese 5k still only takes 5,000 rows with same `id` as §4.1 English subset**, does not require exact 5k rows in file.

### 3.3 General Mixed (Alpaca + Chinese Instructions)

| Item | Value |
|------|-------|
| English Hub | `tatsu-lab/alpaca`, `split=train`, default sample **2,000** (`GENERAL_EN_SAMPLE_N`) |
| Chinese Hub | `FreedomIntelligence/evol-instruct-chinese`, `split=train`, default sample **2,000** (`GENERAL_ZH_SAMPLE_N`) |
| Random seed | `42` (`GENERAL_SEED`) |
| Validation hold-out | Default **`GENERAL_VAL_N=1000`**: English tail **500** + Chinese tail **500** (`split_mode=train_val_by_language_tail`), written to **`general_mixed_validation.jsonl`** |
| Training subset path | `data/raw/general_mixed/general_mixed_train.jsonl` (**3,000** rows) |
| Validation subset path | `data/raw/general_mixed/general_mixed_validation.jsonl` (**1,000** rows) |
| Compatibility mode | `GENERAL_VAL_N=0` produces only **`general_mixed.jsonl`** (full text = sum of both language samples), no train/val split |
| Metadata | `data/raw/general_mixed/download_meta.json` (contains `*_n_obtained`, `written_train_rows`, `written_val_rows` or `written_rows`, `split_mode`) |
| Row structure | After normalization contains `id`, `lang`, `source_repo`, `schema`, `messages`, etc. (see `general_normalize.py`) |

### 3.4 General Mixed Validation Set (1,000, Default)

This block **not merged** into §4's **13k training recipe**; used for **early stopping / coarse hyperparameter tuning** or when framework requires `validation` split. Disjoint ID set from `general_mixed_train.jsonl`; split rules see §3.3 "validation hold-out".

### 3.5 Brainstorm Validation Export (Disjoint from §4.1 Training Head)

| Item | Value |
|------|-------|
| Command | `python -m data_pipeline export-brainstorm-val` (requires existing `train.jsonl` and `brainstorm_vicuna_10k_zh.jsonl`) |
| English path (default) | `data/raw/brainstorm_vicuna_10k/validation_en.jsonl` (`BRAINSTORM_VAL_EN_JSONL` can override) |
| Chinese path (default) | `data/processed/brainstorm_vicuna_10k_zh_validation.jsonl` (`BRAINSTORM_VAL_ZH_JSONL` can override) |
| Metadata | `data/processed/brainstorm_validation_meta.json` (`written_en` / `written_zh` / `missing_zh_ids_sample`, etc.) |
| Default count | Skip training head **5,000** valid rows, then take **3,000** (`BRAINSTORM_TRAIN_HEAD_N` / `BRAINSTORM_VAL_EXPORT_N`) |
| Strict alignment | `BRAINSTORM_VAL_REQUIRE_FULL_ZH=1`: exit with error if any `id` in validation window lacks translation, forcing re-translation |

Construction rule details see §4.4.

---

## 4. v1.0 Training Subset Construction Rules (Deterministic)

The following rules construct **shaping-consistent count** training slices from "full downloaded / translated" materials.

### 4.1 English Brainstorm (5,000)

- **Source file**: `data/raw/brainstorm_vicuna_10k/train.jsonl`
- **Rule**: Take **first 5,000 valid samples** in **top-to-bottom physical order**: skip blank-only lines; remaining lines must be **`json.loads` parseable as objects** to count toward index (consistent with `export-brainstorm-val` training head counting; if any line is invalid JSON, fix source file or record in this spec errata before replay).
- **Primary key**: `id` field per JSON row; denote set **\(S\) = { `id` of these 5000 rows }**.

### 4.2 Chinese Brainstorm (5,000)

- **Source file**: `data/processed/brainstorm_vicuna_10k_zh.jsonl`
- **Rule**: Filter rows where **`id` ∈ \(S\)**; if any `id` missing, **temporarily exclude that `id` from v1.0 Chinese block** (log in merge script); target **exactly 5,000** rows; if insufficient, drive re-translation via "missing translation list" or tighten §4.1 subset until aligned.
- **Current assumption**: Translation already covers `train` first 5k corresponding `id` (consistent with current pipeline practice); if actually insufficient, record difference set in `v1.0.1` or errata section.

### 4.3 General Mixed (3,000, Training Block)

- **Source file**: `data/raw/general_mixed/general_mixed_train.jsonl` **full text** (default **3,000** rows; validate `written_train_rows` from `download_meta.json`).
- **No secondary sampling**, avoid inconsistency with published `download_meta`.
- **Validation 1,000** rows see §3.4, **do not merge** into this training block.

### 4.4 Brainstorm Validation (Default 3,000)

- **Purpose**: Hold-out with same distribution as **§4.1–4.2 training brainstorm**, for training process validation; **not merged** into 13k training recipe.
- **English**: `data/raw/brainstorm_vicuna_10k/train.jsonl`, after counting **5,000** valid JSON rows (same as §4.1), sequentially take **3,000** more valid rows, write to **`validation_en.jsonl`** (default path see §3.5).
- **Chinese**: `data/processed/brainstorm_vicuna_10k_zh.jsonl`, keep only translation rows where **`id`** falls in above English validation window **and order matches**, write to **`brainstorm_vicuna_10k_zh_validation.jsonl`**. If any `id` not yet translated: default **skip** that Chinese row, record `missing_zh_*` in `brainstorm_validation_meta.json`; set `BRAINSTORM_VAL_REQUIRE_FULL_ZH=1` to force command failure and require re-translation.
- **Primary key**: Validation English window `id` set denoted **\(V\)**, satisfying **\(V \cap S = \emptyset\)** (**\(S\)** see §4.1).

### 4.5 Custom Seed (500)

- **Status**: **Not included in current disk snapshot**; suggested target path `data/raw/seed_v1.0/` (to be created).
- **Format**: To be aligned with downstream training scripts (suggest same `messages` structure as `general_mixed` for unified loader).

#### 4.5.1 Creation Steps (Operational Guide)

**1. Clarify Purpose (consistent with shaping)**  
[_docs/shaping/7_data_EN.md](../shaping/7_data_EN.md) §7.3.1 positions this block at **5%**, as **"personal creative cases" + personalization style placeholder**: supplementing public brainstorm data with **product-scene closer** writing (e.g., your domain terminology, preferred follow-up style, short flow from "quick capture" to "card completion"). It's not the main capability source, but **prevents model from only generalizing brainstorms without sounding like your product**.

**2. Content Sources**

| Source | Suggestion |
|--------|------------|
| Write yourself | 1~multi-turn dialogues per entry, using real user language you would say + desired assistant style (can be half-draft then polished) |
| De-sensitized real conversations | If historical conversations exist, remove **PII** like names, phones, internal project codes before writing |
| Light rewriting | Inspired by `brainstorm` entries, **change scenario and wording**, avoid verbatim repetition from HF rows (reduce copyright/repetition concerns) |

**3. Count and Pace**
- Target **500** rows; can start with **50–100** to establish template and quality standards, then batch to 500.
- **Week2 PoC** if time-constrained: temporarily **0 or few rows** (note `v1.0-a` in spec / experiment records), **before Gate1** fill or accept 12.5k main recipe training (consistent with shaping "conservative", but note in report).

**4. Recommended Disk Structure**

```text
data/raw/seed_v1.0/
  README.md          # Author, date, purpose, de-sensitization notes
  seed_v1.0.jsonl    # One JSON per line
  seed_meta.json     # Optional: count, version, checksum plan aligned with v1.0 recipe
```

**5. Suggested JSON Fields per Row (aligned with `general_mixed`)**

Each row at minimum contains:

- `id`: Stable unique key, e.g., `seed-v1.0-00001` (avoid conflict with HF `id`).
- `lang`: `zh` / `en` / `mixed` (mark by main content language).
- `source_repo`: Fixed as `local/seed_v1.0` or `user/yichao1991/seed_v1.0` or other recognizable string.
- `schema`: Suggest `sharegpt_conversations` or `conversations` consistent with brainstorm (`human`/`gpt` alternation); if using OpenAI-style unified loader, use **`messages`** (same as `general_mixed_train.jsonl`), e.g.:

```json
{
  "id": "seed-v1.0-00001",
  "lang": "zh",
  "source_repo": "local/seed_v1.0",
  "schema": "messages_turns",
  "messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

Multi-turn: continue appending `user` / `assistant` alternation.

**6. Quality Self-Check (Minimum Bar)**

- No empty `content`, no single-turn with only one party.
- Chinese fluent, no heavy template repetition.
- Related to "brainstorm + product scenario"; pure encyclopedia Q&A acceptable in small amounts, **not majority** (otherwise duplicates Alpaca block).
- Recommend maintaining a **simple table** (CSV works): `id`, topic tag, whether manually reviewed, for future Stage2 filtering.

**7. Merge into v1.0 Training Pack**
When merging training JSONL, mix `seed_v1.0.jsonl` with §4.1–4.3 training block outputs **by recipe proportion or shuffled**; mark `source_block=seed_v1.0` in **manifest** for traceability and exclusion.

**8. No Need for `data_pipeline download`**
Seed is **locally authored**, not from HF auto-download; if later writing small scripts to validate JSONL row counts and fields, place in `data_pipeline/` or `scripts/` with separate documentation.

#### 4.5.2 Current Decision: Skip Seed (0 rows)

- **Reason**: No personal creative case material currently available.
- **Impact**: Training recipe executes with **13,000 rows** (5k+5k+3k), 500 short of shaping ideal **13,500**, **acceptable**; personalization style mainly relies on subsequent Stage2 or re-training after seed supplement.
- **Recording Obligation**: Note `seed_block=skipped` or `data_profile=v1.0-skip-seed` in every training experiment.
- **Recovery Condition**: Once ≥50 usable drafts available, recommend initiating §4.5.1; after reaching 500, update this spec status line and remove `skip-seed` marker.

---

## 5. Handoff to Week2 PoC

| Input | Description |
|-------|-------------|
| PoC data volume (shaping) | Typically **1k** subset; can take first **1,000** rows / corresponding `id` from §4.1 |
| Merge script | Not yet mandatory in this repository; recommend outputting **manifest** in v1.0 merge script (per row: `global_id`, `source_block`, `source_id`, `split`) |

---

## 6. Gaps, Risks, and Remedies

| Item | Risk | Remedy |
|------|------|--------|
| HF `revision` is `null` | Future Hub updates may cause bitwise inconsistency | On next full download, fix `BRAINSTORM_DATASET_REVISION` and update this spec |
| Chinese 5k and English `id` misaligned | Missing translations or duplicates | Filter per §4.2 rules + re-translate missing `id` |
| Seed 500 skipped | 500 row gap from shaping 13.5k ideal | **Approved skip for current phase** (§4.5.2); reassess before Gate1 or Stage2 |
| Translation model drift | Different dates yield different Qwen translations | Record `TRANSLATE_MODEL` and run date in experiment `META.json` |
| Brainstorm validation window missing translations | `written_zh` less than `written_en`, awkward aligned validation subset | Re-run `translate` to cover §4.4 window `id`, or accept `missing_zh_*` in meta; set `BRAINSTORM_VAL_REQUIRE_FULL_ZH=1` to force alignment check |
| Only `general_mixed.jsonl` exists | Old `.env` (`GENERAL_VAL_N=0`) or old script, no general validation split | Align `GENERAL_*` / `GENERAL_VAL_N` in `.env.example`, re-execute `download` |

---

## 7. Related Documents and Commands

- Shaping: [_docs/shaping/7_data_CN.md](../shaping/7_data_CN.md) · [_docs/shaping/7_data_EN.md](../shaping/7_data_EN.md)
- Sprint 1 Memo (Data Prep Long-form): [_docs/sprints/Sprint1-dataset_download_processing_CN.md](../sprints/Sprint1-dataset_download_processing_CN.md) · [_docs/sprints/Sprint1-dataset_download_processing_EN.md](../sprints/Sprint1-dataset_download_processing_EN.md)
- Sprint 1 Execution: [_docs/execution/sprint-1-train.md](sprint-1-train.md)
- Data Directory: [data/README.md](../../data/README.md)
- Pipeline: [data_pipeline/README.md](../../data_pipeline/README.md) · [data_pipeline/README_EN.md](../../data_pipeline/README_EN.md) (includes `download` / `translate` / `export-brainstorm-val`)

---

## 8. Revision History

| Date | Revision |
|------|----------|
| 2026-05-12 | Initial: Aligned with landed `data_pipeline` + `data/raw` + `data/processed` snapshots and `download_meta` |
| 2026-05-12 | §4.5.1 (then §4.4.1): Added custom seed 500 creation steps and JSON field suggestions |
| 2026-05-14 | "General Mixed" default sample 4k then split to `general_mixed_train` / `general_mixed_validation`; brainstorm validation `export-brainstorm-val`, §3.5, §4.4; custom seed deferred to §4.5; document version **1.2** |
| 2026-05-17 | No training data recipe change: cross-reference—Layer 2 **evaluation** baseline artifacts see [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) (`v1.0` training subsets and manifest definitions unchanged). |
