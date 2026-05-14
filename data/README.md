# 本地数据目录（默认 `DATA_ROOT=./data`）

- `raw/brainstorm_vicuna_10k/`：`python -m data_pipeline download` 写入的 `train.jsonl`、`test.jsonl` 与元数据。可选：在翻译完成后执行 `python -m data_pipeline export-brainstorm-val`，生成 **`validation_en.jsonl`**（与 spec 训练 head **不交**）。
- `raw/general_mixed/`：**与上一目录并列**；默认由 **`download`** 写入 `general_mixed_train.jsonl`（3000 行）、`general_mixed_validation.jsonl`（1000 行）及 `download_meta.json`。若 `.env` 中 **`GENERAL_VAL_N=0`**，则只写单一 `general_mixed.jsonl`（兼容旧配置）。**`translate` 不会创建此目录。**
- `processed/`：`brainstorm_vicuna_10k_zh.jsonl`（`translate` 追加）；可选 **`brainstorm_vicuna_10k_zh_validation.jsonl`**、**`brainstorm_validation_meta.json`**（`export-brainstorm-val`）。

若在资源管理器里只看到 `raw/brainstorm_vicuna_10k/` 而没有 `raw/general_mixed/`，说明尚未成功跑完 `download` 的后半段，或该步曾失败；请在仓库根目录执行 `python -m data_pipeline download` 并查看终端第二段输出。

**训练数据 v1.0 配方与追溯（Sprint1 Week1 交付）**：[s1-data-v1.0-spec_CN.md](../_docs/execution/s1-data-v1.0-spec_CN.md)。

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
python -m data_pipeline export-brainstorm-val
```

调试翻译时可设置 `TRANSLATE_MAX_ITEMS=5`。若需改用英文 ShareGPT 风格数据，在 `.env` 中调整 `GENERAL_EN_DATASET_REPO` / `GENERAL_EN_DATASET_CONFIG` 即可。
