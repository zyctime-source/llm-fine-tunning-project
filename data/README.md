# 本地数据目录（默认 `DATA_ROOT=./data`）

- `raw/brainstorm_vicuna_10k/`：`python -m data_pipeline download` 写入的 `train.jsonl`、`test.jsonl` 与元数据。
- `raw/general_mixed/`：通用中英混合抽样后的 `general_mixed.jsonl`。
- `processed/`：翻译输出 `brainstorm_vicuna_10k_zh.jsonl`（可断点续跑追加）。

详见仓库根目录 [.env.example](../.env.example) 与 [requirements-data.txt](../requirements-data.txt)。

## 建议环境

在**独立 venv**中安装依赖，避免与本机 Anaconda 全局包（如 NumPy 2.x 与旧版 `numexpr`/`bottleneck`）冲突：

```text
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements-data.txt
copy .env.example .env
```

在仓库根目录执行：

```text
python -m data_pipeline download
python -m data_pipeline translate
```

调试翻译时可设置 `TRANSLATE_MAX_ITEMS=5`。若需改用英文 ShareGPT 风格数据，在 `.env` 中调整 `GENERAL_EN_DATASET_REPO` / `GENERAL_EN_DATASET_CONFIG` 即可。
