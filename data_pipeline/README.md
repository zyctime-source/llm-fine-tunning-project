# data_pipeline

**英文版 / English:** [README_EN.md](README_EN.md)

## 1 简介

Sprint 1 数据准备流水线：从 Hugging Face 拉取 **brainstorm_vicuna_10k** 与 **通用中英混合**数据，并用阿里云 DashScope（OpenAI 兼容接口）调用 **Qwen-Max / Qwen-Plus** 将英文头脑风暴多轮对话译为中文，产出可训练用的 JSONL。

方案依据见仓库内 [_docs/shaping/7_data_CN.md](../_docs/shaping/7_data_CN.md)（7.2 翻译策略、7.3.1 数据配比）。英文说明见 [_docs/shaping/7_data_EN.md](../_docs/shaping/7_data_EN.md)。

## 2 快速开始

### 环境要求

- Python 3.11+（**最低 3.10**；若使用 3.10，请在 venv 内自行验证 `datasets` 与依赖无告警即可）
- Conda 或 venv（**推荐独立环境**，避免与系统 Anaconda 中 NumPy 2.x、旧版 `numexpr` 等冲突）

### 安装步骤

请将下方 `cd` 路径替换为你本机上的**仓库根目录**（该目录下应能看到 `data_pipeline/` 与 `requirements-data.txt`）。Windows 下可写成例如 `D:\work\llm-fine-tunning-project`。

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

**macOS / Linux：** 将上述 `.\.venv\Scripts\activate` 改为 `source .venv/bin/activate`；`cd` 改为你的本机仓库路径。

#### 2. 安装依赖

```shell
pip install -r requirements-data.txt
```

可选国内镜像：

```shell
pip install -r requirements-data.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

#### 3. 配置 API 与环境变量

在**仓库根目录**（与 [`.env.example`](../.env.example) 同级）创建 `.env` 文件，不要放在 `data_pipeline/` 子目录内。可先复制模板再编辑：

**Windows:**

```shell
copy .env.example .env
```

**macOS / Linux:**

```shell
cp .env.example .env
```

`python-dotenv` 会从当前工作目录向上查找 `.env`；在根目录运行命令时，根目录下的 `.env` 即可被加载。

**最小示例**（下载若遇 gated 数据集再补 `HF_TOKEN`；翻译必须配置 DashScope）：

```env
# Hugging Face（可选）
# HF_TOKEN=hf_xxx

# 阿里云 DashScope（翻译必填）
DASHSCOPE_API_KEY=sk-xxx
TRANSLATE_MODEL=qwen-max
```

完整变量说明见根目录 [.env.example](../.env.example)；代码入口为 [settings.py](settings.py) 中的 `DataPipelineSettings.from_env()`。

#### 4. 运行流水线

```shell
python -m data_pipeline download
python -m data_pipeline translate
```

调试翻译时可在 `.env` 中设置 `TRANSLATE_MAX_ITEMS=5`，确认输出与费用后再删除该限制跑全量。

## 3 功能概览

| 子命令 | 作用 |
|--------|------|
| `download` | 下载 `DevQuasar/brainstorm_vicuna_10k` 各 split 为 `train.jsonl` / `test.jsonl`；从两个 HF 数据集按 `.env` 抽样并归一化为 `general_mixed.jsonl` |
| `translate` | 读取 `BRAINSTORM_SOURCE_JSONL`（默认 train 分片），逐条调用云端模型翻译，写入 `TRANSLATED_JSONL_PATH`；**已存在的 `id` 会跳过**，支持断点续跑 |

## 4 配置说明（摘要）

1. **下载**：按需填写 `HF_TOKEN` / `HF_HOME`（访问 gated 数据集或提高限额时）。
2. **翻译**：必须配置 `DASHSCOPE_API_KEY`；`TRANSLATE_MODEL` 常用 `qwen-max` 或 `qwen-plus`；`DASHSCOPE_OPENAI_BASE_URL` 默认即为 DashScope 兼容模式地址。
3. **路径**：默认 `DATA_ROOT=./data`，可在 `.env` 中修改；产物说明见下文「输出目录约定」。

## 5 输出目录约定

默认 `DATA_ROOT=./data`（可在 `.env` 修改）。与 [data/README.md](../data/README.md) 一致：

| 路径 | 说明 |
|------|------|
| `raw/brainstorm_vicuna_10k/train.jsonl` | 训练分片，原始 HF 行 JSON（含 `id`、`conversations`） |
| `raw/brainstorm_vicuna_10k/test.jsonl` | 测试分片 |
| `raw/brainstorm_vicuna_10k/download_meta.json` | 下载元信息（repo、revision、各 split 条数） |
| `raw/general_mixed/general_mixed.jsonl` | 通用混合抽样结果，统一为 `messages` 结构 |
| `raw/general_mixed/download_meta.json` | 抽样条数、种子、输出路径等 |
| `processed/brainstorm_vicuna_10k_zh.jsonl` | 中文翻译结果（每行含 `id`、`conversations_zh`、`conversations_en`） |
| `processed/translation_checkpoint.json` | 最近一次翻译任务摘要 |

若源文件不在默认路径，可设置 `BRAINSTORM_SOURCE_JSONL` 指向自定义 JSONL（每行需含与 HF 一致的 `id` 与 `conversations`）。

## 6 包内模块

| 模块 | 职责 |
|------|------|
| [settings.py](settings.py) | 从环境变量加载全部路径与超参 |
| [download_hf.py](download_hf.py) | `datasets.load_dataset` 下载与通用数据抽样 |
| [general_normalize.py](general_normalize.py) | 将 Alpaca 类或 ShareGPT 式 `conversations` 归一为训练友好结构 |
| [conversation_format.py](conversation_format.py) | 多轮对话拼 prompt、解析模型 JSON、校验 `from` 顺序 |
| [translate_qwen.py](translate_qwen.py) | OpenAI 兼容客户端调用 DashScope + 重试与节流 |
| [__main__.py](__main__.py) | `download` / `translate` 子命令入口 |

## 7 通用数据（Alpaca / ShareGPT）

- 默认英文：`tatsu-lab/alpaca`（Alpaca 三字段，归一为两轮 `messages`）。
- 默认中文：`FreedomIntelligence/evol-instruct-chinese`（需能被 [general_normalize.py](general_normalize.py) 识别为 `conversations` 或 `instruction`/`output` 等常见字段）。
- 若 `download_meta.json` 里 `*_n_obtained` 明显小于 `*_n_requested`，请检查 HF 数据集字段是否与归一化逻辑匹配，或更换 `GENERAL_*_DATASET_REPO`，多配置数据集可通过 `GENERAL_EN_DATASET_CONFIG` / `GENERAL_ZH_DATASET_CONFIG` 指定子配置名。

## 8 常见问题

1. **`import datasets` 或 `pandas` 报 NumPy / `numexpr` 相关错误**  
   多为本机全局环境与 NumPy 2 的二进制不兼容。请新建 venv，仅安装 `requirements-data.txt` 后再运行。

2. **HF 下载 401 / 403**  
   在 `.env` 中配置 `HF_TOKEN`（与 Hub 登录 token 一致）。

3. **翻译 401 / 模型不存在**  
   检查 `DASHSCOPE_API_KEY` 是否有效、`TRANSLATE_MODEL` 是否在 DashScope 兼容接口支持的模型列表中。

4. **续跑**  
   不删除 `processed/brainstorm_vicuna_10k_zh.jsonl` 再次执行 `translate`，已写入的 `id` 不会重复请求。

## 9 相关文档

- [_docs/shaping/7_data_CN.md](../_docs/shaping/7_data_CN.md) — 数据配方与翻译要求原文  
- [_docs/shaping/7_data_EN.md](../_docs/shaping/7_data_EN.md) — 同上（英文 shaping）  
- [execution/sprint-1-train.md](../execution/sprint-1-train.md) — Sprint 1 周目标与交付物  
- [data/README.md](../data/README.md) — 数据目录说明  
