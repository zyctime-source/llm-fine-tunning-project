# Layer 2 回归验证集（manifest）

与 [_docs/shaping/9_eval_qa_CN.md](../../shaping/9_eval_qa_CN.md) §9.1.3 对齐：**核心 ~200、通用 ~200、中文保护 ~100**，合计 **500** 条。

## 当前版本

| 项 | 值 |
|----|-----|
| **版本 ID** | `layer2-v0` |
| **清单文件** | `data/eval/layer2/manifest_v0.jsonl` |
| **元数据** | `data/eval/layer2/manifest_meta.json`（条数、随机种子、源路径） |
| **生成脚本** | `scripts/build_layer2_manifest.py` |

## 每条记录字段

- `layer2_id`：唯一 ID（`L2-core-*` / `L2-general-*` / `L2-zh_guard-*`）
- `stratum`：`core` | `general` | `zh_guard`
- `source_hub_repo`：与 shaping 对齐的 Hub 数据集名（便于对照 Layer 1）
- `source_local_path` / `source_line_1based` / `source_sample_id`：本地快照中的可追溯定位
- `messages`：OpenAI 风格 `role` / `content`，评测时直接送入 chat 模板
- `content_sha256`：对 `messages` 的规范 JSON 做 SHA-256，便于校验是否被篡改

## 抽样规则（v0）

**通用混合源（`general` 与 `zh_guard` 共用）：** `scripts/build_layer2_manifest.py` **优先**读取 `data/raw/general_mixed/general_mixed_train.jsonl`（与数据规格 `s1-data-v1.0` 中 **3k 训练块**一致，**不与** `general_mixed_validation.jsonl` 的 hold-out 相交）。若该文件不存在（例如仍使用 `GENERAL_VAL_N=0`、只落盘单一 `general_mixed.jsonl`），则 **回退**到 legacy `data/raw/general_mixed/general_mixed.jsonl`。`manifest_meta.json` 里的 `paths.general_mixed_source` 记录的是**生成当时**实际选用的路径。

**换源与复现：** 从 legacy 全文（约 4k 行）切换到仅训练子集（3k 行）会改变 en/zh 抽样池，**同一套种子也未必得到相同 `layer2_id` 题面**。若需与旧基线逐题对比，应 **继续沿用旧 manifest 文件**；若接受新题单，请 **bump** 版本（如 `layer2-v0.1`）并在实验报告与 `manifest_meta.json` 中写清。

| 子层 | 本地源 | 说明 |
|------|--------|------|
| **core** | `data/processed/brainstorm_vicuna_10k_zh.jsonl` | 从全文件行中 **无放回随机抽 200 行**，种子 **42**；对话取 `conversations_zh`，映射为 `user`/`assistant` |
| **general** | 上表「通用混合源」 | 仅 `lang=="en"` 行；**无放回随机抽 200 行**，种子 **43**。shaping 中 Layer 1 通用指令指向 **X-AlpacaEval**；v0 使用已入库的 **Alpaca 风格英文指令** 作为离线代理（说明见 `manifest_meta.json` 的 `proxy_notes.general`） |
| **zh_guard** | 同上 | 仅 `lang=="zh"`（`FreedomIntelligence/evol-instruct-chinese` 子集）；**无放回随机抽 100 行**，种子 **44**。shaping 指向 **CMT-Eval**；v0 用 **中文指令数据** 作代理（说明见 `proxy_notes.zh_guard`） |

重新生成（须固定种子以复现同一题单；**须保证上文「通用混合源」文件已存在**，否则脚本退出）：

```bash
python scripts/build_layer2_manifest.py
# 可选：python scripts/build_layer2_manifest.py --seed-core 42 --seed-general 43 --seed-zh 44
```

## 与「理想 Layer 2」的差异

- **通用子层**：理想来源为 Hub `zhihz0535/X-AlpacaEval`；当前环境若无法稳定加载 `datasets`，仍以本仓库 **通用混合训练子集**（优先 `general_mixed_train.jsonl`）中的 en/Alpaca 行为 **v0 代理**。升级到 X-AlpacaEval 时应 **bump manifest 版本**（如 `layer2-v1`）并重跑基线。
- **中文子层**：理想来源为 **CMT-Eval**；v0 使用 **evol-instruct-chinese** 混入行。若后续接入 CMT-Eval，同样应 bump 版本。

基线报告中的协议与数值应对齐 **manifest 版本**（见 `_docs/execution/s1-baseline-report_CN.md` §3）。
