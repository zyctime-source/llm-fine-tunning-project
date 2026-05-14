# data_pipeline

**Chinese version:** [README.md](README.md)

## 1 Overview

Sprint 1 data pipeline: download **brainstorm_vicuna_10k** and a **bilingual general-mix** dataset from Hugging Face, then call **Qwen-Max / Qwen-Plus** through Alibaba Cloud DashScope (OpenAI-compatible API) to translate English brainstorm dialogues into Chinese, producing training-ready JSONL.

Product rationale: [_docs/shaping/7_data_EN.md](../_docs/shaping/7_data_EN.md) (translation strategy §7.2, mix §7.3.1). Chinese shaping doc: [_docs/shaping/7_data_CN.md](../_docs/shaping/7_data_CN.md).

## 2 Quick start

### Requirements

- Python 3.11+ (**minimum 3.10**; if you use 3.10, verify `datasets` and deps in your venv).
- Conda or venv (**dedicated environment recommended** to avoid global Anaconda issues with NumPy 2.x / old `numexpr` wheels).

### Setup

Replace the `cd` path below with your **repository root** (the folder that contains `data_pipeline/` and `requirements-data.txt`). On Windows, e.g. `D:\work\llm-fine-tunning-project`.

**Windows (conda):**

```shell
cd /path/to/llm-fine-tunning-project
conda create -n llm-data python=3.11 -y
conda activate llm-data
```

**Windows (venv):**

```shell
cd /path/to/llm-fine-tunning-project
python3.11 -m venv .venv
.\.venv\Scripts\activate
```

**macOS / Linux:** use `source .venv/bin/activate` instead of `.\.venv\Scripts\activate`; adjust `cd` to your path.

#### 1 Install dependencies

```shell
pip install -r requirements-data.txt
```

Optional China mirror:

```shell
pip install -r requirements-data.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

**Eval environment (separate venv recommended):** Layer 2 inference / baseline eval uses [requirements-eval.txt](../requirements-eval.txt) at the repo root (PyTorch, `transformers`, etc.). That stack differs from `requirements-data.txt` (including NumPy policy). Prefer a **second** venv (e.g. `.venv-eval` or conda `llm-eval`); see [experiment/README.md](../experiment/README.md), section “Layer 2 推理 / 冒烟”.

#### 2 Configure environment variables

Create `.env` in the **repository root** (next to [`.env.example`](../.env.example)), not inside `data_pipeline/`. Copy the template first:

**Windows:**

```shell
copy .env.example .env
```

**macOS / Linux:**

```shell
cp .env.example .env
```

`python-dotenv` discovers `.env` from the working directory; running commands from the repo root loads that file.

**Minimal example** (add `HF_TOKEN` if you hit gated datasets; translation requires DashScope):

```env
# Hugging Face (optional)
# HF_TOKEN=hf_xxx

# Alibaba DashScope (required for translate)
DASHSCOPE_API_KEY=sk-xxx
TRANSLATE_MODEL=qwen-max
```

Full variable list: [`.env.example`](../.env.example). Code entry point: `DataPipelineSettings.from_env()` in [settings.py](settings.py).

#### 3 Run the pipeline

```shell
python -m data_pipeline download
python -m data_pipeline translate
python -m data_pipeline export-brainstorm-val
```

For a dry run, set `TRANSLATE_MAX_ITEMS=5` in `.env`, validate output and cost, then remove the cap for the full run.

`export-brainstorm-val` writes English rows after the training head (see [s1-data-v1.0-spec_CN.md](../_docs/execution/s1-data-v1.0-spec_CN.md) §3.5 / §4.4) and aligns Chinese rows by `id`.

**Note:** `translate` progress lines printed to the terminal are in **English** (see `translate_qwen.py`).

## 3 CLI summary

| Subcommand | Purpose |
|------------|---------|
| `download` | Download `DevQuasar/brainstorm_vicuna_10k` splits to `train.jsonl` / `test.jsonl`; sample two HF datasets per `.env` and write `general_mixed_train.jsonl` + `general_mixed_validation.jsonl` by default (`general_mixed.jsonl` only if `GENERAL_VAL_N=0`) |
| `translate` | Read `BRAINSTORM_SOURCE_JSONL` (default train export), call the cloud model per row, append to `TRANSLATED_JSONL_PATH`; **existing `id`s are skipped** (resumable) |
| `export-brainstorm-val` | After the training head in `train.jsonl`, take `BRAINSTORM_VAL_EXPORT_N` English rows and align rows from `brainstorm_vicuna_10k_zh.jsonl` by `id`; write meta JSON |

## 4 Configuration (summary)

1. **Download:** set `HF_TOKEN` / `HF_HOME` when using gated datasets or higher Hub limits.
2. **Translate:** `DASHSCOPE_API_KEY` is required; common models are `qwen-max` or `qwen-plus`; `DASHSCOPE_OPENAI_BASE_URL` defaults to the DashScope compatible endpoint.
3. **Paths:** default `DATA_ROOT=./data` (override in `.env`); outputs are described below.

## 5 Output layout

Default `DATA_ROOT=./data` (configurable). Same as [data/README.md](../data/README.md):

| Path | Description |
|------|---------------|
| `raw/brainstorm_vicuna_10k/train.jsonl` | Train split, one HF row JSON per line (`id`, `conversations`, …) |
| `raw/brainstorm_vicuna_10k/test.jsonl` | Test split |
| `raw/brainstorm_vicuna_10k/download_meta.json` | Download metadata (repo, revision, row counts per split) |
| `raw/brainstorm_vicuna_10k/validation_en.jsonl` | English brainstorm validation (default 3000; **disjoint** from §4.1 training ids) |
| `raw/general_mixed/general_mixed_train.jsonl` | General mix **training** subset (default 3000 rows, `messages` layout) |
| `raw/general_mixed/general_mixed_validation.jsonl` | General mix **validation** subset (default 1000 rows; disjoint ids, tail split per language) |
| `raw/general_mixed/general_mixed.jsonl` | Written only when **`GENERAL_VAL_N=0`** (legacy single file) |
| `raw/general_mixed/download_meta.json` | Sample counts, seed, paths, `split_mode`, etc. |
| `processed/brainstorm_vicuna_10k_zh_validation.jsonl` | Aligned Chinese subset (same id order as `validation_en.jsonl`; missing translations omitted—see meta) |
| `processed/brainstorm_validation_meta.json` | Export summary (`written_en`, `written_zh`, `missing_zh_*`, …) |
| `processed/brainstorm_vicuna_10k_zh.jsonl` | Translation output (`id`, `conversations_zh`, `conversations_en`) |
| `processed/translation_checkpoint.json` | Last translation run summary JSON |

Override `BRAINSTORM_SOURCE_JSONL` if your source JSONL lives elsewhere (each line must include `id` and `conversations` like the HF export).

## 6 Package modules

| Module | Role |
|--------|------|
| [settings.py](settings.py) | Load paths and hyperparameters from the environment |
| [download_hf.py](download_hf.py) | `datasets.load_dataset` download + general mix sampling |
| [general_normalize.py](general_normalize.py) | Normalize Alpaca or ShareGPT-style rows for training |
| [conversation_format.py](conversation_format.py) | Dialogue text, model prompt, JSON parse/validate, role sync |
| [translate_qwen.py](translate_qwen.py) | DashScope via OpenAI-compatible client, retries, throttling, logs |
| [brainstorm_validation.py](brainstorm_validation.py) | `export-brainstorm-val`: post-head English window + zh alignment |
| [__main__.py](__main__.py) | CLI entry for `download` / `translate` / `export-brainstorm-val` |

## 7 General mix (Alpaca / ShareGPT)

**Where it lands:** The general mix is **not** loose files under `data/raw/` only. It lives in the sibling folder **`data/raw/general_mixed/`** (next to `brainstorm_vicuna_10k/`). Default outputs when `GENERAL_VAL_N>0`:

- `data/raw/general_mixed/general_mixed_train.jsonl`
- `data/raw/general_mixed/general_mixed_validation.jsonl`
- `data/raw/general_mixed/download_meta.json`

If **`GENERAL_VAL_N=0`** in `.env`, only `general_mixed.jsonl` is written.

Override with `GENERAL_RAW_DIR` in `.env` if needed.

**When it is created:** Only **`python -m data_pipeline download`** writes these files (same command: brainstorm first, then general mix). **`translate` alone does not** create the general mix.

If the folder is missing: run `download` again from the repo root and inspect the second JSON block in the terminal (`general_en_n_obtained`, `general_zh_n_obtained`, errors).

- Default English: `tatsu-lab/alpaca` (triplet fields → two-turn `messages`).
- Default Chinese: `FreedomIntelligence/evol-instruct-chinese` (must match parsers in [general_normalize.py](general_normalize.py): `conversations` or `instruction`/`output`, etc.).
- If `download_meta.json` shows `*_n_obtained` far below `*_n_requested`, check dataset columns or switch `GENERAL_*_DATASET_REPO`; multi-config datasets may need `GENERAL_EN_DATASET_CONFIG` / `GENERAL_ZH_DATASET_CONFIG`.

## 8 Troubleshooting

1. **`import datasets` / `pandas` errors with NumPy / `numexpr`**  
   Usually a binary mismatch with NumPy 2 in a global conda env. Create a fresh venv and install only `requirements-data.txt`.

2. **HF download 401 / 403**  
   Set `HF_TOKEN` in `.env` (same token as Hub login).

3. **Translate 401 / unknown model**  
   Verify `DASHSCOPE_API_KEY` and that `TRANSLATE_MODEL` is supported on the DashScope compatible API.

4. **Resume**  
   Re-run `translate` without deleting `processed/brainstorm_vicuna_10k_zh.jsonl`; lines with existing `id` are not re-requested.

## 9 Related docs

- [_docs/shaping/7_data_EN.md](../_docs/shaping/7_data_EN.md) — Data mix and translation (English shaping)
- [_docs/shaping/7_data_CN.md](../_docs/shaping/7_data_CN.md) — Same (Chinese shaping)
- [execution/sprint-1-train.md](../execution/sprint-1-train.md) — Sprint 1 goals and deliverables
- [data/README.md](../data/README.md) — Data directory notes
