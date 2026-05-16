# `experiment/` 实验目录

与 [_docs/shaping/8_train_iterate_CN.md](../_docs/shaping/8_train_iterate_CN.md) §8.2.3 一致：每个实验子目录包含 **README.md**（叙事）+ **META.json**（结构化元数据），可选 **results/**。

## 模板（复制后改名）

| 路径 | 用途 |
|------|------|
| [_template/README.md](_template/README.md) | README 小节草稿 |
| [_template/META.template.json](_template/META.template.json) | 训练类实验 `META.json` 占位 |
| [_template/META.eval.template.json](_template/META.eval.template.json) | 仅评测类实验 `META.json` 占位 |
| [_template/FIELDS.md](_template/FIELDS.md) | 字段说明（`experiment-meta-v0`） |

## 已有实例

| 目录 | 说明 |
|------|------|
| [baseline-gemma4e2b-it-layer2-v0](baseline-gemma4e2b-it-layer2-v0/) | Sprint 1 Week 1 基线评测（Layer 2 + `eval-protocol-v0`），**已完成**（`META.json` `status=completed`；见 [s1-baseline-report_CN.md](../_docs/execution/s1-baseline-report_CN.md)）。 |

新建训练实验时：复制 `_template/`，重命名目录，将 `META.eval.template.json` 换为 `META.template.json` 并改名为 `META.json`，按需删改字段。

## Layer 2 推理 / 冒烟（评测环境）

### 是否需要单独 venv？

**建议新建一个与数据管线分开的 venv**（例如仓库根目录下 `.venv-eval`，或 Conda 环境名 `llm-eval`），原因与 `data_pipeline/README.md` 中「推荐独立环境」一致：

- **依赖不同**：数据侧使用 [requirements-data.txt](../requirements-data.txt)（`datasets` 等）；评测侧使用 [requirements-eval.txt](../requirements-eval.txt)（`torch`、`transformers`、`accelerate` 等）。
- **NumPy 栈**：评测依赖里将 **NumPy 限制在 2.0 以下**，以降低与旧版 SciPy / sklearn 组合导致 `import transformers` 失败的风险；与数据环境里常见的 NumPy 2.x 可能**不兼容**。
- **体积与升级节奏**：PyTorch 与数据脚本拆开后，升级或重装时互不影响。

若你坚持使用**同一个** venv，需自行解决版本冲突；本仓库文档以「数据 `.venv` / 评测 `.venv-eval`」两套为默认叙述。

### 环境要求

- Python **3.11+**（**最低 3.10**；若使用 3.10，请在目标 venv 内自行验证 `torch` / `transformers` 可导入且能加载 Gemma）
- Conda 或 venv（**推荐独立环境**，避免与系统 Anaconda 中 NumPy 2.x、旧版 SciPy 等冲突）

### 安装步骤

请将下方 `cd` 路径替换为你本机上的**仓库根目录**（该目录下应能看到 `experiment/`、`requirements-eval.txt`、`scripts/`）。Windows 下可写成例如 `D:\yichao\LLM\llm-fine-tunning-project`。

**Windows (conda)：**

```shell
cd /path/to/llm-fine-tunning-project
conda create -n llm-eval python=3.11 -y
conda activate llm-eval
```

**Windows (venv)：**

```shell
cd /path/to/llm-fine-tunning-project
python -m venv .venv-eval
.\.venv-eval\Scripts\activate
```

**macOS / Linux：** 将上述 `.\.venv-eval\Scripts\activate` 改为 `source .venv-eval/bin/activate`；`cd` 改为你的本机仓库路径。

#### 安装依赖

```shell
pip install -r requirements-eval.txt
```

可选国内镜像：

```shell
pip install -r requirements-eval.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

若仍出现 `import transformers` / NumPy 相关错误，可先按 [requirements-eval.txt](../requirements-eval.txt) 文件头注释强制重装 NumPy 1.x，再重装 `torch` / `transformers`。本仓库的 **Layer 2 文本冒烟脚本**使用 `AutoTokenizer`，**不需要** `torchvision` / `Pillow`；若你自行改用 `AutoProcessor` 做多模态评测，再按 Transformers 报错安装 `torchvision`、`pillow` 等。

### Hugging Face：登录与国内下载加速

**关于 `HF_TOKEN` 警告**：未设置 token 时仍可下载多数公开模型，但 Hub 会限制匿名请求并发与带宽，并打印该提示。建议：

1. 在 [Hugging Face Tokens](https://huggingface.co/settings/tokens) 创建 **Read** 权限 token。  
2. 在仓库根目录 `.env` 中取消注释并填写 `HF_TOKEN=hf_...`（与 `data_pipeline` 共用同一 `.env` 即可），或在当前终端设置环境变量后再跑脚本。

**中国大陆镜像（模型/权重下载走 Hub API）**：常用第三方镜像为 **[hf-mirror.com](https://hf-mirror.com/)**，与 `huggingface_hub` / `transformers` 兼容的方式是设置 **`HF_ENDPOINT`**（详见镜像站说明）：

**Windows PowerShell（仅当前会话）：**

```powershell
$env:HF_ENDPOINT = "https://hf-mirror.com"
# 可选：$env:HF_TOKEN = "hf_你的token"
python scripts/layer2_smoke_infer.py --limit 3 --max-new-tokens 128
```

**Windows CMD：**

```cmd
set HF_ENDPOINT=https://hf-mirror.com
python scripts/layer2_smoke_infer.py --limit 3 --max-new-tokens 128
```

**macOS / Linux：**

```bash
export HF_ENDPOINT=https://hf-mirror.com
python scripts/layer2_smoke_infer.py --limit 3 --max-new-tokens 128
```

也可把 `HF_ENDPOINT` 与 `HF_TOKEN` 写入根目录 `.env`（见 [.env.example](../.env.example) 中 Hugging Face 小节）；`layer2_smoke_infer.py` 会在启动时尝试加载该文件（需已 `pip install python-dotenv`，已列入 `requirements-eval.txt`）。镜像为**非官方**同步，偶有延迟或个别文件与官方不一致，以镜像站公告为准。若需完全官方源，删除或清空 `HF_ENDPOINT` 即可。

### 脚本与产物路径

| 资源 | 路径 |
|------|------|
| 依赖清单 | [requirements-eval.txt](../requirements-eval.txt) |
| 冒烟脚本（manifest 前 N 条 + 贪心解码） | [scripts/layer2_smoke_infer.py](../scripts/layer2_smoke_infer.py) |
| 评委打分（DashScope `qwen3.6-plus`，对齐 s1-baseline-report §4.1） | [scripts/layer2_judge_scores.py](../scripts/layer2_judge_scores.py) |
| 评委结果汇总（分层 mean/median → `layer2_judge_summary.json`） | [scripts/aggregate_layer2_judge_scores.py](../scripts/aggregate_layer2_judge_scores.py) |
| 默认推理输出目录 | `experiment/baseline-gemma4e2b-it-layer2-v0/results/`（见该目录 [README](baseline-gemma4e2b-it-layer2-v0/README.md)） |

```shell
python scripts/layer2_smoke_infer.py --dry-run --limit 5
python scripts/layer2_smoke_infer.py --limit 3 --max-new-tokens 128
```

### Layer 2 评委打分（可选）

依赖与数据侧翻译相同：根目录 `.env` 中配置 **`DASHSCOPE_API_KEY`**，以及 **`DASHSCOPE_OPENAI_BASE_URL`**（默认国内兼容模式 URL）。需已 `pip install -r requirements-eval.txt`（含 `openai`、`tenacity`）。

在 **Gemma 推理 JSONL** 跑出一批或全部后，对每条 `layer2_id` 调用评委模型（默认 **`qwen3.6-plus`**，可用环境变量 `LAYER2_JUDGE_MODEL` 或 `--judge-model` 覆盖）：

```shell
python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl

python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl --resume

python scripts/layer2_judge_scores.py --manifest data/eval/layer2/manifest_v0.jsonl --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl --limit 10
```

- **`--resume`**：`--out` 中已出现过的 `layer2_id` 会跳过；若要重评某条，先从输出文件中删除对应行。  
- 输出每行含 `scores`（解析成功时）或 `judge_error` / `judge_raw_preview`（解析失败时）；与 manifest 对齐的维度见 [_docs/execution/s1-baseline-report_CN.md](../_docs/execution/s1-baseline-report_CN.md) §4.1。

