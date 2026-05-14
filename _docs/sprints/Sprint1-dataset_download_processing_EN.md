# Fine-tuning an on-device LLM app — dev log, 2026-05-13: dataset prep

> **Type:** Personal project notes  
> **Date:** 2026-05-13  
> **GitHub repo:** https://github.com/zyctime-source/llm-fine-tunning-project  
> **Chinese version:** [Sprint1-dataset_download_processing_CN.md](Sprint1-dataset_download_processing_CN.md)

---

## 1. Context

I want to get hands-on with LLM fine-tuning. Over about 3–4 months I plan to go from zero to an Android app whose core is fine-tuned models, using vibe coding, and keep a full paper trail.

### 1.1 Product sketch: an AI thinking assistant on the phone

**Pain point:** Ideas show up as quick notes, but plain notes only *store* — they don’t *think*. A few months later you reopen them and the thread is gone.

**Approach:** An Android app where a one-liner note goes through an on-device model **probe → branch → converge** and becomes a structured “idea card”. Base model **Gemma-4-E2B-IT** (~4B), **LoRA** to match a brainstorm-style rhythm, then INT4/INT8 quant for the phone — privacy and cost in balance.

**Takeaway:** This is not a generic chatbot; it’s a **structured thinking aid** — it must probe, converge, and turn messy dialogue into actionable cards.

### 1.2 What this article covers

The roadmap is four beats: **define the data recipe → download & clean → PoC → full training**. This post is about **data prep**: which Hugging Face datasets we pick, how they land on disk, how English becomes training-ready Chinese JSONL, and where the **default general validation** from `download` and the **brainstorm validation** from `export-brainstorm-val` end up.

As of Sprint 1 Week 1, **`s1-data-v1.0-spec_CN.md`** is frozen (including skipping the 500-row custom seed block), and **`data_pipeline/`** exposes three CLIs: **`download`** (writes `general_mixed_train` / `general_mixed_validation` when configured), **`translate`**, and **`export-brainstorm-val`**. The rest is a straight “groceries and prep” walkthrough for later review.

---

## 2. Dataset choices

Rationale is in **`_docs/shaping/7_data_CN.md` §7.3.1** and **`_docs/execution/s1-data-v1.0-spec_CN.md` §2** (spec is Chinese-only; English shaping context: [_docs/shaping/7_data_EN.md](../shaping/7_data_EN.md)). At the Hub `repo_id` level the snapshot looks like this:

> 💡 Pipe tables (`| ... |`) don’t wrap long paths well. Below is an **HTML table** with `word-break: break-all` for browsers / Typora / some rich-text renderers. If your site strips inline styles, copy a plain list from the Chinese companion doc or the spec.

<div markdown="0" style="overflow-x:auto">

<table style="table-layout:fixed;width:100%;max-width:720px;border-collapse:collapse;font-size:14px;">
<thead>
<tr>
<th style="width:18%;border:1px solid #ccc;padding:6px;text-align:left;">Role</th>
<th style="width:30%;border:1px solid #ccc;padding:6px;text-align:left;word-break:break-all;overflow-wrap:anywhere;">Hub <code>repo_id</code></th>
<th style="width:34%;border:1px solid #ccc;padding:6px;text-align:left;word-break:break-all;overflow-wrap:anywhere;">Local artifact</th>
<th style="width:35%;border:1px solid #ccc;padding:6px;text-align:left;">Count (v1.0)</th>
</tr>
</thead>
<tbody>
<tr>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">Brainstorm · English</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>DevQuasar/brainstorm_vicuna_10k</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>data/raw/brainstorm_vicuna_10k/train.jsonl</code><br /><code>data/raw/brainstorm_vicuna_10k/validation_en.jsonl</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">Train <strong>5,000</strong> (first 5,000 <strong>valid</strong> lines of <code>train</code>, spec §4.1); val <strong>3,000</strong> in <code>validation_en.jsonl</code> (<code>export-brainstorm-val</code>, <code>id</code>s disjoint from train)</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">Brainstorm · Chinese</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">Same source + translation pipeline</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>data/processed/brainstorm_vicuna_10k_zh.jsonl</code><br /><code>data/processed/brainstorm_vicuna_10k_zh_validation.jsonl</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">Train <strong>5,000</strong> aligned by <code>id</code> (§4.2); val translations aligned to <code>validation_en.jsonl</code> (default <strong>3,000</strong>; gaps → <code>brainstorm_validation_meta.json</code>)</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">General mix (fallback)</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>tatsu-lab/alpaca</code> + <code>FreedomIntelligence/evol-instruct-chinese</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>data/raw/general_mixed/general_mixed_train.jsonl</code><br /><code>data/raw/general_mixed/general_mixed_validation.jsonl</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">Default <strong>2000+2000</strong> from sources, then <strong>3,000 train + 1,000 val</strong> (500 EN + 500 ZH tails hold out, <code>seed=42</code>, see <code>download_meta.json</code>)</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">Custom seed</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">Local only, not from HF</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>data/raw/seed_v1.0/</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;"><strong>0</strong> rows skipped (<code>v1.0-skip-seed</code>)</td>
</tr>
</tbody>
</table>

</div>


**Takeaway:** The **general** block samples EN+ZH from the Hub (defaults 2000+2000), normalizes, then takes the **last 1,000** by language tail into **`general_mixed_validation.jsonl`** and the rest **3,000** into **`general_mixed_train.jsonl`**; the training recipe only consumes the train file. **`GENERAL_VAL_N=0`** falls back to a single **`general_mixed.jsonl`**.

---

## 3. Download and post-processing

Three beats: **how to run locally** (3.1), **`download` code path and layout** (3.2), **`translate` when only brainstorm English becomes Chinese** (3.3). The **`general_mixed_train`** slice is still an EN+ZH mix and **never** goes through **`translate`**, same as the table.

### 3.1 Running locally

1. **Environment:** From **repo root** (you should see `data_pipeline/`, `requirements-data.txt`), use a **dedicated venv** so you don’t fight global Anaconda NumPy stacks.  
   `python -m venv .venv` → activate → `pip install -r requirements-data.txt` (details: `data_pipeline/README.md`).
2. **Config:** `copy .env.example .env` (Windows) or `cp` (macOS/Linux). Add **`HF_TOKEN`** if needed (gated sets / rate limits); **translation** needs **`DASHSCOPE_API_KEY`**, commonly **`TRANSLATE_MODEL=qwen-max`**. Other paths and `GENERAL_*` knobs: `.env.example` and **`DataPipelineSettings.from_env()`** in `data_pipeline/settings.py`.
3. **Commands** (always from repo root; **run each subcommand on its own** for clearer logs):

```shell
python -m data_pipeline download
python -m data_pipeline translate
python -m data_pipeline export-brainstorm-val
```

Run **`download`** before **`translate`**. After translations cover the validation window `id`s, run **`export-brainstorm-val`** (see spec §3.5). For a cheap trial set **`TRANSLATE_MAX_ITEMS=5`** in `.env`, then remove it for the full run.

### 3.2 What `download` does and what appears on disk

CLI wiring is in **`data_pipeline/__main__.py`**: `download` loads **`DataPipelineSettings.from_env()`** then runs **two** downloads in order — the two JSON blobs printed to the terminal.

```py
settings = DataPipelineSettings.from_env()
print("Downloading brainstorm_vicuna_10k ...")
split_counts = download_brainstorm_vicuna(settings)
print(json.dumps({"brainstorm_splits": split_counts}, ensure_ascii=False, indent=2))

print("Downloading and mixing general data (GENERAL_* env) ...")
general_meta = download_general_mixed(settings)
print(json.dumps(general_meta, ensure_ascii=False, indent=2))
```

- **`download_brainstorm_vicuna`** (`download_hf.py`): pulls **`DevQuasar/brainstorm_vicuna_10k`** splits into `data/raw/brainstorm_vicuna_10k/*.jsonl` plus **`download_meta.json`** (revision, row counts, …).
- **`download_general_mixed`** (same module + **`general_normalize.py`**): samples **`GENERAL_EN_SAMPLE_N` / `GENERAL_ZH_SAMPLE_N`** from Alpaca / evol-instruct (defaults **2000** each), normalizes; if **`GENERAL_VAL_N` > 0** (default **1000**), writes **`general_mixed_train.jsonl` (3000)** and **`general_mixed_validation.jsonl` (1000)**; if **`GENERAL_VAL_N=0`**, writes only **`general_mixed.jsonl`**.

**After `download`** you should see (if an old `.env` only ever produced **`general_mixed.jsonl`**, align with `.env.example`, turn on **`GENERAL_VAL_N`**, and rerun **`download`** — see the general-mix takeaway above):

| Path | Produced by | Contents |
|------|------------|----------|
| `data/raw/brainstorm_vicuna_10k/train.jsonl` | `download` | HF `train` export |
| `data/raw/brainstorm_vicuna_10k/test.jsonl` | `download` | HF `test` export |
| `data/raw/brainstorm_vicuna_10k/download_meta.json` | `download` | Row counts, `revision`, trace fields |
| `data/raw/brainstorm_vicuna_10k/validation_en.jsonl` | `export-brainstorm-val` | EN brainstorm val (default 3000; `id`s disjoint from §4.1 train head) |
| `data/processed/brainstorm_vicuna_10k_zh_validation.jsonl` | `export-brainstorm-val` | ZH lines aligned by `id` (gaps → `brainstorm_validation_meta.json`) |
| `data/raw/general_mixed/general_mixed_train.jsonl` | `download` | General **train** subset (default 3000) |
| `data/raw/general_mixed/general_mixed_validation.jsonl` | `download` | General **val** subset (default 1000; `id`s disjoint from train) |
| `data/raw/general_mixed/general_mixed.jsonl` | `download` | Only when **`GENERAL_VAL_N=0`**: single combined file |
| `data/raw/general_mixed/download_meta.json` | `download` | Counts, `seed`, `split_mode`, `written_train_rows` / `written_val_rows`, … |

### 3.3 What gets translated to Chinese

**Only the brainstorm English corpus** (default `train.jsonl` **`conversations`**). The **general train** mix already contains EN and ZH instruction rows — **do not** run **`translate`** on **`general_mixed_train.jsonl`** (or the single **`general_mixed.jsonl`** legacy file).

**`translate`** does **not** re-download from the Hub; it **appends** a new local JSONL (one JSON per line, same **`id`**, resumable).

```shell
python -m data_pipeline translate
```

- **Input:** **`BRAINSTORM_SOURCE_JSONL`** (defaults to `data/raw/brainstorm_vicuna_10k/train.jsonl`; can point to a subset for trials).
- **Output:** **`TRANSLATED_JSONL_PATH`** (default `data/processed/brainstorm_vicuna_10k_zh.jsonl`), **append** mode; existing **`id`**s are **skipped**.
- **API:** Alibaba **DashScope** OpenAI-compatible Chat Completions; model from **`TRANSLATE_MODEL`** (e.g. `qwen-max`); retries via `tenacity` in `translate_qwen.py`.

Core batching is **`translate_brainstorm_file`**: read line-wise, dedupe `id`, flatten English to **`translate_one`**, validate turns, write one JSON row. If the model typos roles (`gtp`), **`apply_original_speaker_roles_to_translated_turns`** restores English **`from`**:

```py
plain_english_dialogue = conversations_to_plain_text(english_turns)
parsed_model_payload = translator.translate_one(plain_english_dialogue)
chinese_turns = parsed_model_payload.get("conversations")
if not isinstance(chinese_turns, list):
    raise ValueError("Model JSON missing 'conversations' array")

# Models may typo `from` (e.g. gtp); trust English roles, only translated `value`.
apply_original_speaker_roles_to_translated_turns(english_turns, chinese_turns)
validate_translated_conversations(english_turns, chinese_turns)

output_record = {
    "id": sample_id,
    "source_id": sample_id,
    "split": settings.translate_split,
    "conversations_zh": chinese_turns,
    "conversations_en": english_turns,
}
output_fp.write(json.dumps(output_record, ensure_ascii=False) + "\n")
```

**Takeaway:** The translation file **may have more than 5,000 lines** (e.g. almost full `train` translated). **v1.0** still takes only rows whose **`id`** is in the first-5k-English set — don’t confuse **file row count** with **recipe row count**. Summary JSON: **`data/processed/translation_checkpoint.json`** (keep next to `download_meta.json` for traceability).

---

## 4. Train / validation / test in the current spec

### 4.1 Hub-native splits

- **`brainstorm_vicuna_10k`:** **`train`** (~10k rows) and **`test`** (~1k) as two JSONLs after `download`.
- **`general_mixed`:** Pipeline samples **2000** per source by default, then splits into **`general_mixed_train.jsonl`** and **`general_mixed_validation.jsonl`**.

### 4.2 Training slices in `s1-data-v1.0-spec`

- **EN brainstorm 5k:** First **5,000** valid lines of `train.jsonl` in order; key set **S**.
- **ZH brainstorm 5k:** Rows in `brainstorm_vicuna_10k_zh.jsonl` with **`id` ∈ S**; target 5,000.
- **General 3k (train):** Full **`general_mixed_train.jsonl`** (3,000 lines); no second sampling.
- **Custom seed 500:** **Skipped (0 rows)**; training profile **`v1.0-skip-seed`** so it isn’t confused with a full 13.5k shaping target.

### 4.3 Where is the validation set?

**General:** By default **`data/raw/general_mixed/general_mixed_validation.jsonl` (1,000)** — **`id`s disjoint** from **`general_mixed_train.jsonl`**, tail split per language; see **`download_meta.json`** (`split_mode`, `val_en_tail`, `val_zh_tail`).

**Brainstorm:** **`python -m data_pipeline export-brainstorm-val`** (needs `train.jsonl` + translation file): after **5,000** valid train lines, take **3,000** EN rows → **`validation_en.jsonl`**, align **`id`s from **`brainstorm_vicuna_10k_zh.jsonl`** → **`brainstorm_vicuna_10k_zh_validation.jsonl`**, summary **`brainstorm_validation_meta.json`**. Disjoint from **S**; missing `id`s skip ZH lines unless **`BRAINSTORM_VAL_REQUIRE_FULL_ZH=1`**.

**`test.jsonl` (brainstorm 1k):** Still a stronger hold-out / baseline probe; **early stopping** can combine **`general_mixed_validation`** and the brainstorm val export.

**Takeaway:** Training stays **13k**; **1k general** and **3k brainstorm (default) val** are **not** in that 13k. PoC can still use the spec’s “first 1k lines / matching `id`s” subset.

---

## 5. References (in-repo)

| Doc | Purpose |
|-----|---------|
| [_docs/shaping/0_Overview_End-to-End_Finetuning_and_Edge_Deployment_EN.md](../shaping/0_Overview_End-to-End_Finetuning_and_Edge_Deployment_EN.md) | End-to-end index (EN) |
| [_docs/shaping/7_data_EN.md](../shaping/7_data_EN.md) | Data recipe, translation, eval list (shaping, EN) |
| [_docs/shaping/7_data_CN.md](../shaping/7_data_CN.md) | Same (Chinese) |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | **Frozen v1.0 spec** (paths, counts, deterministic splits, skip-seed) — authoritative; Chinese |
| [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) | Sprint 1 breakdown and deliverables |
| [data_pipeline/README_EN.md](../../data_pipeline/README_EN.md) | `.env`, `download` / `translate` / `export-brainstorm-val` |
| [data/README.md](../../data/README.md) | `data/` layout and troubleshooting |

---

*Personal learning notes. If anything disagrees with the repo, trust the repo and `s1-data-v1.0-spec`.*
