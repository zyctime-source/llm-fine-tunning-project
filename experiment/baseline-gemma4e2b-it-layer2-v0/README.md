# baseline-gemma4e2b-it-layer2-v0

**类型**：仅评测（`eval_only`），无训练。  
**目的**：在 Layer 2 回归集 `layer2-v0` 上建立 **Gemma-4-E2B-IT** 基线，协议为 `eval-protocol-v0`，供 Week 2 PoC 与后续 Stage 1 对照。

## 关联文档

| 文档 | 路径 |
|------|------|
| 基线报告（主叙事与 §4 协议） | [_docs/execution/s1-baseline-report_CN.md](../../_docs/execution/s1-baseline-report_CN.md) |
| Layer 2 manifest 说明 | [_docs/eval/layer2/README.md](../../_docs/eval/layer2/README.md) |
| Sprint 备忘：基线 Gemma + Layer 2 推理 | [_docs/sprints/Sprint1-03_baseline-gemma-layer2-infer_CN.md](../../_docs/sprints/Sprint1-03_baseline-gemma-layer2-infer_CN.md) |

| 路径 | 用途 |
|------|------|
| `META.json` | 结构化元数据（跑完后回填 `base_model.revision`、`results.*`、`result_scores` 等） |
| `results/` | 原始推理输出、评委中间件、分层汇总表（路径写入 `META.json` 与基线报告 §7） |

## 快速开始

### 环境要求

- Python **3.11+**（**最低 3.10**；请在 venv 内验证 `torch` / `transformers` 可导入）
- Conda 或 venv（**推荐独立评测环境**，避免与系统 Anaconda 中 NumPy 2.x、旧版 SciPy 等冲突）

### 安装步骤（评测 venv）

评测与数据管线**分开**：使用仓库根目录 [requirements-eval.txt](../../requirements-eval.txt)，环境与 Hugging Face 加速说明见 [experiment/README.md](../README.md) §「Layer 2 推理 / 冒烟」。

```shell
cd /path/to/llm-fine-tunning-project
conda activate llm-eval
pip install -r requirements-eval.txt
```

## 环境冒烟（Gemma + Layer2 前 N 条）

1. 校验 manifest 与 prompt 构造（不加载模型）：
   ```bash
   python scripts/layer2_smoke_infer.py --dry-run --limit 5
   ```
2. **新建评测专用 venv**（勿与 `data_pipeline` 的 `requirements-data.txt` 混用同一环境），见 [experiment/README.md](../README.md)。
3. 小批量推理（贪心；与 `eval-protocol-v0` 一致；`max_new_tokens` 冒烟可调低）：
   ```bash
   python scripts/layer2_smoke_infer.py --limit 3 --max-new-tokens 128
   ```
4. 将生成的 `results/smoke_infer_*.jsonl` 路径记入 `META.json`（`results.raw_outputs_dir` + `results.smoke_infer_jsonl`）；**已在 2026-05-13 记入**。

**说明**：manifest 中带参考 `assistant` 的单轮题，脚本会在生成前**去掉末尾 assistant**，避免把标准答案拼进 prompt。

### 已记录的冒烟产物（相对仓库根）

| 字段（`META.json`） | 路径 |
|---------------------|------|
| `results.raw_outputs_dir` | `experiment/baseline-gemma4e2b-it-layer2-v0/results` |
| `results.smoke_infer_jsonl` | `experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260513T1556Z.jsonl` |

### 全量 Layer 2 基线（500 条 + 评委，相对仓库根）

| 字段（`META.json`） | 路径 |
|---------------------|------|
| `results.layer2_infer_jsonl` | `experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl` |
| `results.metrics_path` | `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl` |
| `results.judge_summary_json` | `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json` |

摘要指标见 **`META.json` → `result_scores`**（与 `layer2_judge_summary.json` 一致）；详细维度均值/中位数以汇总文件为准。

## 评委打分（可选，`eval-protocol-v0` §4.1）

在 **Gemma 推理 JSONL** 就绪后（可与全量 500 条并行准备环境），使用 DashScope **OpenAI 兼容**接口调用 **`qwen3.6-plus`** 打分：

```bash
pip install -r requirements-eval.txt   # 含 openai、tenacity
# .env：DASHSCOPE_API_KEY、DASHSCOPE_OPENAI_BASE_URL（与翻译流水线一致）

python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl

python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl --resume

python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl --limit 10
```

将 **`results` 下评委 JSONL 路径**记入 `META.json`（可沿用 `metrics_path` 或扩展字段），并在 [s1-baseline-report_CN.md](../../_docs/execution/s1-baseline-report_CN.md) §7 填写。

详见 [experiment/README.md](../README.md)「Layer 2 评委打分」与 [scripts/layer2_judge_scores.py](../../scripts/layer2_judge_scores.py) 顶部说明。

### 评委结果汇总（生成 `result_scores` 摘要）

评委 JSONL 跑完后，用 [scripts/aggregate_layer2_judge_scores.py](../../scripts/aggregate_layer2_judge_scores.py) 计算分层均值/中位数、解析成功条数等，便于填入 **`META.json` → `result_scores`**（详细表仍写在 `s1-baseline-report` 或自行分析）。

```bash
python scripts/aggregate_layer2_judge_scores.py --judge-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json
```

- **`--out`**：写入完整摘要 JSON（含 `by_stratum`、`all_parse_ok` 各维度 `mean` / `median`）。  
- **标准错误输出**：附一段可直接合并进 `META.json` 的 **`result_scores`** 占位结构（含 `judge_summary_file`、各层 `overall` 均值等）。  
- 默认对同一 **`layer2_id` 保留最后一行**（若曾重跑评委）；需要保留所有行时用 **`--no-dedupe`**。

## 待办（跑基线时勾选）

- [x] 冻结 `base_model.revision`（Hub commit：`b324173c7d5721c2baba7f3b17b3b9b3d34ab1e9`）
- [x] 环境冒烟：已跑通 `layer2_smoke_infer.py`（3 条，`max_new_tokens=128`），路径见 `META.json` → `results.smoke_infer_*`
- [x] 跑满 500 条 Layer 2 推理（`max_new_tokens=2048`，贪心；见 `META.json` → `results.layer2_infer_*`）
- [x] 评委打分：`layer2_judge_scores.jsonl` + 汇总 `layer2_judge_summary.json`（`qwen3.6-plus`）
- [x] 将 `META.json` 的 `status` 改为 `completed`，并与 `s1-baseline-report_CN.md` 数值与 §7 路径同步（2026-05-15）
