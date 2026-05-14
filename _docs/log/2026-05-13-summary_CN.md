# 沟通小结 · 2026-05-13

围绕 **Sprint 1 Week 1**：Layer 2 回归题单（manifest）、基线报告用语澄清、Week 1 完成度、实验元数据模板、评测环境与小批量冒烟、HF 国内镜像与 token，以及将冒烟产物写入 `META.json` 与勾选 README。

---

## 1. 阶段定位

- 从「数据与 shaping 文档」推进到 **可执行的 Layer 2 manifest + 评测依赖栈 + 冒烟脚本 + 实验目录元数据**。  
- 尚未完成 **全量 500 条基线推理** 与 **`s1-baseline-report` 定稿**。

---

## 2. 主要结论（问答摘要）

| 主题 | 结论 |
|------|------|
| Manifest 含义 | 固定版 Layer 2 **题单**（JSONL），含 ID、子层、`messages` 与追溯字段，用于可复现评测。 |
| Week 1 是否做完 | **未全部完成**；manifest 与协议骨架已就绪，全量跑数与报告定稿仍待办。 |
| 元数据模板 | `experiment/_template` + `META.json` 字段约定；`baseline-gemma4e2b-it-layer2-v0` 为评测实例草稿。 |
| 脚本位置 | `layer2_smoke_infer.py` 保留在 **`scripts/`** 更合适，不必迁入某个实验子目录。 |
| 评测 venv | **建议与数据管线分环境**；`requirements-eval.txt` + `experiment/README.md` 已按 `data_pipeline` 风格补充安装步骤。 |
| Gemma 加载 | 纯文本评测用 **`AutoTokenizer`**，避免 `AutoProcessor` 触发 **torchvision / PIL** 硬依赖。 |
| HF 警告与加速 | **`HF_TOKEN`** 提升限额与门禁下载；国内可用 **`HF_ENDPOINT=https://hf-mirror.com`**；脚本支持加载根目录 `.env`（`python-dotenv`）。 |

---

## 3. 当日落地文件与产物

| 类型 | 路径（摘） |
|------|----------------|
| Manifest | `data/eval/layer2/manifest_v0.jsonl`、`manifest_meta.json` |
| 构建脚本 | `scripts/build_layer2_manifest.py` |
| 评测脚本与依赖 | `scripts/layer2_smoke_infer.py`、`requirements-eval.txt` |
| 文档 | `_docs/eval/layer2/README.md`；`experiment/README.md`（含 HF）；`data_pipeline/README*.md` 交叉引用 |
| 实验模板与实例 | `experiment/_template/*`、`experiment/baseline-gemma4e2b-it-layer2-v0/*` |
| 冒烟输出（用户本机） | `experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260513T1556Z.jsonl`（已写入 `META.json`） |

---

## 4. 计划 / 待办状态（当日相关）

- `layer2-manifest`、`meta-template`、`env-smoke`：在仓库与计划文件中已标为 **completed**（以你本机冒烟成功及 `META.json` 回填为准）。  
- `s1-baseline-report`：**仍为 WIP**；§0 中「基座可加载冒烟」已更新为**小样本通过**，全量推理与定稿仍待。  
- `baseline-full-report`、`week2-handoff` 等：仍为后续工作。

---

## 5. 建议的下一步

1. 在 `llm-eval`（或你的评测 venv）中 **`pip install -r requirements-eval.txt`** 保持与文档一致；若已安装 Pillow 仅历史遗留，可不必强求与文本路径一致。  
2. 将 **`base_model.revision`**（Hub commit）写入 `META.json` 与 `s1-baseline-report_CN.md` §2。  
3. 扩展或复用 `layer2_smoke_infer.py` **跑满 500 条**（`--limit 500`、`max_new_tokens=2048` 与 §4 对齐），产出全量 JSONL 并回填报告 §5–§7。  
4. 若 manifest 升级为 X-AlpacaEval / CMT-Eval 真源，**bump** `layer2-v1` 并重跑基线。

---

## 6. 日志文件（本轮）

- `_docs/log/2026-05-13-complete_CN.md`：**agent transcript 全量逐条导出**（同一会话 `72573b9b-ab79-4d5f-b76b-489ac46bece4`，共 278 条 user/assistant 消息；含 Sprint1 第一周清单与后续 manifest/冒烟等，**非人工缩写版**）。  
- `_docs/log/2026-05-13-summary_CN.md`：本文件（摘要）。  
- `_docs/log/2026-05-13-summary_EN.md`：英文摘要。

---

*文档生成于项目 `_docs/log/` 目录，供个人学习与项目推进使用。*
