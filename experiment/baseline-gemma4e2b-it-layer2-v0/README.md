# baseline-gemma4e2b-it-layer2-v0

**类型**：仅评测（`eval_only`），无训练。  
**目的**：在 Layer 2 回归集 `layer2-v0` 上建立 **Gemma-4-E2B-IT** 基线，协议为 `eval-protocol-v0`，供 Week 2 PoC 与后续 Stage 1 对照。

## 关联文档

| 文档 | 路径 |
|------|------|
| 基线报告（主叙事与 §4 协议） | [_docs/execution/s1-baseline-report_CN.md](../../_docs/execution/s1-baseline-report_CN.md) |
| Layer 2 manifest 说明 | [_docs/eval/layer2/README.md](../../_docs/eval/layer2/README.md) |
| 数据配方 | [_docs/execution/s1-data-v1.0-spec_CN.md](../../_docs/execution/s1-data-v1.0-spec_CN.md) |

## 目录约定

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

## 待办（跑基线时勾选）

- [x] 冻结 `base_model.revision`（Hub commit：`b324173c7d5721c2baba7f3b17b3b9b3d34ab1e9`）
- [x] 环境冒烟：已跑通 `layer2_smoke_infer.py`（3 条，`max_new_tokens=128`），路径见 `META.json` → `results`
- [ ] 跑满 500 条 Layer 2 推理
- [ ] （可选）评委打分
- [ ] 将 `META.json` 的 `status` 改为 `completed`，并与 `s1-baseline-report` 定稿同步
