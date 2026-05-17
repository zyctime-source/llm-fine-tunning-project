# Sprint 1 Week 1 结案报告：数据与基线准备

> **类型**：个人项目技术备忘  
> **日期**：2026-05-16  
> **GitHub repo**：https://github.com/zyctime-source/llm-fine-tunning-project  
> **主线对照**：[_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) §「Week 1：数据与基线准备」  
> **总览索引**：[Sprint1-00_tasks_intro_CN.md](Sprint1-00_tasks_intro_CN.md) §4 Week 1

---

## 1. 背景与范围

### 1.1 项目背景

随手记录的灵感往往只被「存」下来，却无法被「想」透——传统笔记不会追问、不会发散、更不会帮你收敛成可行动的洞察。三个月后回看，当初的思路早已模糊。

本项目尝试用端侧 **Gemma-4-E2B-IT** 模型 + LoRA 微调，打造一款安卓端的「AI 思维助手」：让每一句随手记都经过「追问—发散—收敛」的结构化加工，最终沉淀为一张可执行的「灵感卡片」。

### 1.2 本文范围

Sprint 1 第 1 周的核心目标是：**让数据与评测基础设施就位，并验证基座模型能跑通 Layer 2 回归集**（详见 `sprint-1-train.md`）。

本文不涉及训练与 PoC（那是 Week 2 及以后的任务），仅对 Week 1 已落地的工件、路径与结论做一份「结案清单」，方便交接给 Week 2 并留档复盘。

---

## 2. 任务清单（与 sprint-1-train 对齐）

| 任务 | 简述 | 状态 | 详情与入口 |
|------|------|------|------------|
| 冻结 `v1.0` 数据配方 | 确定数据来源、配比和抽样规则，形成可追溯的数据配方文档 | **已完成** | 详见 [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md)；当前为 `v1.0-skip-seed` 版本（自建种子 500 条暂缺，不阻塞基线） |
| 产出实验元数据模板 | 建立实验目录结构、META.json 模板和字段规范，支撑追踪 | **已完成** | 见 [experiment/_template/](../../experiment/_template/)，含 `META.*.template.json`、`FIELDS.md` 等；评测类实验参考 `META.eval.template.json` |
| 跑通基座模型 Layer 2 基线 | 完成 500 条 Layer 2 评测，建立后续对比的基准分数 | **已完成** | 实验目录 [experiment/baseline-gemma4e2b-it-layer2-v0/](../../experiment/baseline-gemma4e2b-it-layer2-v0/)，`META.json` 状态为 `completed` |
| 构建 Layer 2 题单 | 生成 500 条固定测试题（core/general/zh_guard 三层），用于后续回归测试 | **已完成** | 题单位于 `data/eval/layer2/manifest_v0.jsonl`；构建过程见 [Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) 与 [_docs/eval/layer2/README.md](../eval/layer2/README.md) |

---

## 3. 关键交付物（路径均为仓库相对路径）

| 交付物 | 位置 | 说明 |
|--------|------|------|
| 数据配方 `s1-data-v1.0-spec` | [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | 已冻结定稿；文档版本随交叉索引已 bump（见该文档 §8） |
| 基线评测报告 `s1-baseline-report` | [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | 已定稿：含 §4 评测协议、§5 分层均值、§6 红线、§7 产物路径 |
| 实验元数据 `META.json` | [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) | 已回填完成；含推理产物路径、评委结果、汇总分数等 |
| 全量推理结果 | `experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl` | 500 条，贪心解码，`max_new_tokens=2048` |
| 评委打分（逐条） | `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl` | 评委模型 `qwen3.6-plus`；本次 500/500 条解析成功 |
| 评委打分（汇总） | `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json` | 由 [scripts/aggregate_layer2_judge_scores.py](../../scripts/aggregate_layer2_judge_scores.py) 生成 |
| 基线实验 README | [experiment/baseline-gemma4e2b-it-layer2-v0/README.md](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md) | 含运行命令、待办清单、产物说明 |
| 推理与评委执行备忘 | [Sprint1-03_baseline-gemma-layer2-infer_CN.md](Sprint1-03_baseline-gemma-layer2-infer_CN.md) | §7 摘录了与报告 §5–§6 对齐的数值与红线结论 |

---

## 4. 基线结论（供 Week 2 参考）

评委 `overall` 维度（1–100）的均值如下（数据来自 `layer2_judge_summary.json` 与 `s1-baseline-report_CN.md` §5）：

| 子层 | 样本数 | overall 均值 |
|------|--------|--------------|
| core | 200 | **93.35** |
| general | 200 | **81.85** |
| zh_guard | 100 | **77.94** |
| **全体** | **500** | **85.67** |

**红线结论**：P0（安全）、P1（功能）**未触发**；P2（体验）**已预警**——中文保护子层（zh_guard）显著低于 core 层，Week 2 的 PoC 需将 **zh_guard** 纳入验收指标。详见基线报告 §6 与 Sprint1-03 §7.2。

---

## 5. 数据与评测流水线（Week 1 已打通）

| 阶段 | 备忘文档 | 关键内容 |
|------|----------|----------|
| 数据下载 / 翻译 / 验证子集 | [Sprint1-01_dataset_download_processing_CN.md](Sprint1-01_dataset_download_processing_CN.md) | `download`、`translate`、`export-brainstorm-val`；与 `s1-data-v1.0-spec` 对齐 |
| Layer 2 题单构建 | [Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) | `build_layer2_manifest.py`；`manifest_meta.json` 记录数据源与 seed |
| 评测环境 / 推理 / 评委打分 | [Sprint1-03_baseline-gemma-layer2-infer_CN.md](Sprint1-03_baseline-gemma-layer2-infer_CN.md) | `requirements-eval.txt`；`layer2_smoke_infer.py` / `layer2_judge_scores.py` |

---

## 6. 未完成项（不阻塞 Week 1 结案）

| 项 | 说明 |
|----|------|
| **Should：失败样本清单** | 本次评委 500/500 解析成功；低分个案可从 `layer2_judge_scores.jsonl` 按需抽取，建议留到 **PoC 后评估** 或 Stage 1 误差分析时统一沉淀 |
| **Should：环境版本信息** | `s1-baseline-report_CN.md` §7 中的 OS / Python / pip 版本等字段，建议在实际评测机上补全，便于他人复现 |
| **整 Sprint 的 Must 项** | PoC 训练、Stage 1 训练、微调后 Layer 2 对比等，属于 **Week 2–4** 范畴，见 [Sprint1-00_tasks_intro_CN.md](Sprint1-00_tasks_intro_CN.md) §3 |

---

## 7. 相关文档索引

| 文档 | 用途 |
|------|------|
| [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) | Sprint 1 四周主线与交付物定义 |
| [Sprint1-00_tasks_intro_CN.md](Sprint1-00_tasks_intro_CN.md) | 任务总览、Must/Should、Gate1 标准 |
| [Sprint1-01_dataset_download_processing_CN.md](Sprint1-01_dataset_download_processing_CN.md) | Week 1 数据准备流水 |
| [Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) | Layer 2 题单生成与分层逻辑 |
| [Sprint1-03_baseline-gemma-layer2-infer_CN.md](Sprint1-03_baseline-gemma-layer2-infer_CN.md) | 基线推理、评委打分、结果摘录 |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | 数据配方冻结规格 |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | 评测协议与基线定稿报告 |
| [experiment/README.md](../../experiment/README.md) | 实验目录约定、评测环境、脚本索引 |

---

## 8. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-17 | 初版：Week 1 结案报告（对齐 `sprint-1-train.md` Week 1 与既有 Sprint 备忘） |
