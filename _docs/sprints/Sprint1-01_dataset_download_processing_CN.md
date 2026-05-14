# 微调端侧大模型 App 开发记录：2026-05-13，数据集准备

> **类型**：个人项目技术备忘  
> **日期**：2026-05-13
> github repo: https://github.com/zyctime-source/llm-fine-tunning-project

---

## 1. 背景

我一直对于大模型的微调很感兴趣。希望通过vibe coding 在3-4个月内从零推进一个以大模型微调为核心、最终落在安卓端应用的落地项目，并全程留档。

### 1.1 项目背景：手机里的 AI 思维助手

**痛点**：灵感来时随手记，但传统笔记只能「存」不能「想」，三个月后回看，早已忘了当时的思路。

**方案**：做一款安卓 App，让「随手记的一句话」经过端侧大模型**追问-发散-收敛**，最终收成结构化的「灵感卡片」。选型上，用 **Gemma-4-E2B-IT**（4B 级）做基座，**LoRA 微调**对齐「头脑风暴」节奏，再量化到 INT4/INT8 塞进手机，兼顾隐私与成本。

💡 **理解要点**：这不是通用聊天机器人，而是**结构化的思维辅助工具**——必须会追问、会收敛、能把散漫对话变成可行动的卡片。

### 1.2 本文聊什么

整个项目分四步走：**定数据配方 → 下载清洗 → PoC 验证 → 全量训练**。本文聚焦数据准备阶段——从 Hugging Face 选哪些数据集、怎么落到本地磁盘、又怎么译成中文变成「可训的 JSONL」，以及 **`download` 默认拆出的通用验证集**与 **`export-brainstorm-val` 导出的脑暴验证集**各落在哪。

截至 Sprint 1 Week 1，数据规格 `s1-data-v1.0-spec_CN.md` 已冻结（含跳过自建种子 500 的决策），`data_pipeline/` 提供 **`download`**（含 `general_mixed_train` / `general_mixed_validation`）、**`translate`**、**`export-brainstorm-val`** 三条 CLI。下面把「买菜洗菜」的流水账记下来，方便复盘。

---

## 2. 数据集选型

设计依据见 **`_docs/shaping/7_data_CN.md` §7.3.1** 与 **`_docs/execution/s1-data-v1.0-spec_CN.md` §2**。落到 Hugging Face `repo_id` 上，当前快照主要是这几块：

> 💡 Markdown 管道表（`| ... |`）里**无法**对长路径自动换行，预览时两列常被拉得很宽。下面用 **HTML 表格**并设 `word-break: break-all`，便于在浏览器 / Typora / 部分富文本里换行；若粘贴到**不支持内联样式的平台**，可复制下方「纯文本清单」备用。

<div markdown="0" style="overflow-x:auto">

<table style="table-layout:fixed;width:100%;max-width:720px;border-collapse:collapse;font-size:14px;">
<thead>
<tr>
<th style="width:18%;border:1px solid #ccc;padding:6px;text-align:left;">角色</th>
<th style="width:30%;border:1px solid #ccc;padding:6px;text-align:left;word-break:break-all;overflow-wrap:anywhere;">Hub <code>repo_id</code></th>
<th style="width:34%;border:1px solid #ccc;padding:6px;text-align:left;word-break:break-all;overflow-wrap:anywhere;">本地产物</th>
<th style="width:35%;border:1px solid #ccc;padding:6px;text-align:left;">条数（v1.0）</th>
</tr>
</thead>
<tbody>
<tr>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">头脑风暴·英文</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>DevQuasar/brainstorm_vicuna_10k</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>data/raw/brainstorm_vicuna_10k/train.jsonl</code><br /><code>data/raw/brainstorm_vicuna_10k/validation_en.jsonl</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">训练 <strong>5,000</strong>（<code>train</code> 前 5000 有效行，spec §4.1）；验证 <strong>3,000</strong> 见 <code>validation_en.jsonl</code>（<code>export-brainstorm-val</code>，与训练 <code>id</code> 不交）</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">头脑风暴·中文</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">同上 + 翻译流水线</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>data/processed/brainstorm_vicuna_10k_zh.jsonl</code><br /><code>data/processed/brainstorm_vicuna_10k_zh_validation.jsonl</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">训练与英文同 <code>id</code> <strong>5,000</strong>（§4.2）；验证译稿与 <code>validation_en.jsonl</code> 对齐（默认 <strong>3,000</strong>，缺译见 <code>brainstorm_validation_meta.json</code>）</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">通用保底</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>tatsu-lab/alpaca</code> + <code>FreedomIntelligence/evol-instruct-chinese</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>data/raw/general_mixed/general_mixed_train.jsonl</code><br /><code>data/raw/general_mixed/general_mixed_validation.jsonl</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">默认各源抽 <strong>2000+2000</strong>，再切 <strong>训练 3000 + 验证 1000</strong>（英/中尾各 500 进验证，<code>seed=42</code>，见 <code>download_meta.json</code>）</td>
</tr>
<tr>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">自建种子</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;">本地撰写，非 HF</td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;word-break:break-all;"><code>data/raw/seed_v1.0/</code></td>
<td style="border:1px solid #ccc;padding:6px;vertical-align:top;"><strong>0</strong> 条，跳过（<code>v1.0-skip-seed</code>）</td>
</tr>
</tbody>
</table>

</div>


💡 **理解要点**：「通用」块先从 Hub 各抽一批（默认英 2000 + 中 2000），归一后**按语种尾部**划出 **1000** 条作 **`general_mixed_validation.jsonl`**，其余 **3000** 进 **`general_mixed_train.jsonl`**，训练配方仍只吃后者；`GENERAL_VAL_N=0` 时才退回到单一 `general_mixed.jsonl`。

---

## 3. 数据下载和后处理

下面按三步写：**本机怎么跑**（3.1）、**只谈 `download`：代码路径与落盘**（3.2）、**只有头脑风暴英文要译成中文时的 `translate` 与代码**（3.3）。通用块 **`general_mixed_train`（3k）** 仍是英+中拼盘且**不经 `translate`**，与上表一致。

### 3.1 本地怎么跑

1. **目录与环境**：在**仓库根**（能看到 `data_pipeline/`、`requirements-data.txt`）建独立 venv，避免和本机全局 Anaconda 里 NumPy 等版本打架。  
   `python -m venv .venv` → 激活后 `pip install -r requirements-data.txt`（细节见 `data_pipeline/README.md`）。
2. **配置**：根目录 `copy .env.example .env`（macOS/Linux 用 `cp`）。按需填 **`HF_TOKEN`**（gated 数据集或限额）；**翻译**必须配 **`DASHSCOPE_API_KEY`**，常用 **`TRANSLATE_MODEL=qwen-max`**。其余路径、`GENERAL_*` 抽样等见 `.env.example` 与 **`DataPipelineSettings.from_env()`**（`data_pipeline/settings.py`）。
3. **命令**（始终在仓库根执行，**每条子命令单独跑一段**，便于看日志与排错）：

```shell
python -m data_pipeline download
python -m data_pipeline translate
python -m data_pipeline export-brainstorm-val
```

先 `download` 再 `translate`。**译完**且验证窗内的 `id` 已有译稿后，再跑 `export-brainstorm-val` 导出脑暴验证集（详见 spec §3.5）。调试翻译可在 `.env` 里设 `TRANSLATE_MAX_ITEMS=5`，确认无误后删掉限制再跑全量。

### 3.2 下载这条链路：代码在干什么、下载后结构

子命令注册在 **`data_pipeline/__main__.py`**：`download` 入口先 **`DataPipelineSettings.from_env()`**，再**顺序**调两段下载——对应终端里先后打印的两段 JSON 摘要。

```py
settings = DataPipelineSettings.from_env()
print("Downloading brainstorm_vicuna_10k ...")
split_counts = download_brainstorm_vicuna(settings)
print(json.dumps({"brainstorm_splits": split_counts}, ensure_ascii=False, indent=2))

print("Downloading and mixing general data (GENERAL_* env) ...")
general_meta = download_general_mixed(settings)
print(json.dumps(general_meta, ensure_ascii=False, indent=2))
```

- **`download_brainstorm_vicuna`**（`download_hf.py`）：把 HF 上 **`DevQuasar/brainstorm_vicuna_10k`** 的各 split 写成 `data/raw/brainstorm_vicuna_10k/*.jsonl`，并写 **`download_meta.json`**（revision、条数等）。  
- **`download_general_mixed`**（同上 + **`general_normalize.py`**）：按 `.env` 里 `GENERAL_*` 从 Alpaca / evol-instruct 各抽 **`GENERAL_EN_SAMPLE_N` / `GENERAL_ZH_SAMPLE_N` 条**（默认各 **2000**），归一成统一行结构；若 **`GENERAL_VAL_N` > 0**（默认 **1000**），再写出 **`general_mixed_train.jsonl`（3000）** 与 **`general_mixed_validation.jsonl`（1000）**；若 **`GENERAL_VAL_N=0`** 则只写 **`general_mixed.jsonl`**。

**下载完成后**资源管理器里应能看到（若曾用旧 `.env` 只生成过 `general_mixed.jsonl`，请按 `.env.example` 打开 `GENERAL_VAL_N` 后再跑 `download`，见上文「通用」理解要点）：

| 路径 | 来源 | 内容 |
|------|------|------|
| `data/raw/brainstorm_vicuna_10k/train.jsonl` | `download` | HF `train` 分片导出 |
| `data/raw/brainstorm_vicuna_10k/test.jsonl` | `download` | HF `test` 分片导出 |
| `data/raw/brainstorm_vicuna_10k/download_meta.json` | `download` | 行数、`revision` 等追溯信息 |
| `data/raw/brainstorm_vicuna_10k/validation_en.jsonl` | `export-brainstorm-val` | 脑暴英文验证（默认 3000；与 §4.1 训练 head 的 `id` 不交） |
| `data/processed/brainstorm_vicuna_10k_zh_validation.jsonl` | `export-brainstorm-val` | 与上一文件按 `id` 对齐的译稿（缺译见 `brainstorm_validation_meta.json`） |
| `data/raw/general_mixed/general_mixed_train.jsonl` | `download` | 通用混合**训练**子集（默认 3000） |
| `data/raw/general_mixed/general_mixed_validation.jsonl` | `download` | 通用混合**验证**子集（默认 1000，`id` 与 train 不交） |
| `data/raw/general_mixed/general_mixed.jsonl` | `download` | 仅当 **`GENERAL_VAL_N=0`** 时写入的「整包」混合 |
| `data/raw/general_mixed/download_meta.json` | `download` | 抽样条数、`seed`、`split_mode`、`written_train_rows` / `written_val_rows` 等 |

### 3.3 数据集哪部分要译成中文

**需要走翻译的只有头脑风暴英文主集**（默认那份 `train.jsonl` 里多轮 `conversations`）。**通用混合训练块**里已经含英/中指令，**不要**再对 **`general_mixed_train.jsonl`**（或整包 `general_mixed.jsonl`）跑 `translate`。

`translate` **不是从 Hub 再下一遍数据**，而是在本地**追加写一个新文件**（JSONL 一行一条、带相同 **`id`**，便于和英文对齐与断点续跑）。

```shell
python -m data_pipeline translate
```

- **输入**：**`BRAINSTORM_SOURCE_JSONL`**（默认指向 `data/raw/brainstorm_vicuna_10k/train.jsonl`，可在 `.env` 改成子集路径做试跑）。  
- **输出**：**`TRANSLATED_JSONL_PATH`**（默认 `data/processed/brainstorm_vicuna_10k_zh.jsonl`），**追加**模式；已出现在输出文件里的 **`id` 会跳过**，可反复跑续译。  
- **接口**：阿里云 **DashScope** 的 OpenAI 兼容 Chat Completions，模型由 **`TRANSLATE_MODEL`**（如 `qwen-max`）指定；`translate_qwen.py` 里用 `tenacity` 给单次调用做了重试。

核心批量逻辑在 **`translate_brainstorm_file`**：读源文件逐行、`id` 去重、整段英文转 plain text 后 **`translate_one`**，再把模型返回的 `conversations` 与英文轮次对齐校验，最后写入一行 JSON。角色名若被模型写歪（例如 `gtp`），用英文侧的 **`from`** 覆盖，避免脏标签进训练：

```py
plain_english_dialogue = conversations_to_plain_text(english_turns)
parsed_model_payload = translator.translate_one(plain_english_dialogue)
chinese_turns = parsed_model_payload.get("conversations")
if not isinstance(chinese_turns, list):
    raise ValueError("Model JSON missing 'conversations' array")

# Models may typo `from` (e.g. gtp); trust English roles, only translated `value`.
apply_original_speaker_roles_to_translated_turns(english_turns, chinese_turns)
validate_translated_conversations(english_turns, chinese_turns)

output_record = {
    "id": sample_id,
    "source_id": sample_id,
    "split": settings.translate_split,
    "conversations_zh": chinese_turns,
    "conversations_en": english_turns,
}
output_fp.write(json.dumps(output_record, ensure_ascii=False) + "\n")
```

💡 **理解要点**：译后文件**行数可以大于 5000**（例如几乎整份 `train` 都译完）；但 **v1.0 配方里的中文 5k** 仍按 spec 只取**与英文前 5k 行相同 `id` 集合**的行——别把「文件行数」和「训练吃进去的条数」混成一回事。摘要会落到 **`data/processed/translation_checkpoint.json`**（若与 `download_meta.json` 一起留档，追溯链更完整）。

---

## 4. 训练 / 验证 / 测试：在当前规格里分别指什么？

### 4.1 Hugging Face 自带的 split

- **`brainstorm_vicuna_10k`**：官方提供 **`train`（10k 行）**与**`test`（1k 行）**，下载后就是两个 JSONL
- **`general_mixed`**：流水线从两个 Hub  **`train` split** 各抽 **2000** 行（可配置），归并后默认拆成 **`general_mixed_train.jsonl`** 与 **`general_mixed_validation.jsonl`**

### 4.2 `s1-data-v1.0-spec` 里「训练用」的切片

- **英文脑暴 5k**：`train.jsonl` **按物理顺序前 5000 行**；主键集合记为 **S**
- **中文脑暴 5k**：在 `brainstorm_vicuna_10k_zh.jsonl` 里筛 **`id ∈ S`** 的行，目标对齐 5000
- **通用 3k（训练）**：`general_mixed_train.jsonl` **全文 3000 行**，不再二次抽样
- **自建种子 500**：当前**跳过（0 条）**，训练侧记 **`v1.0-skip-seed`** 以免和满 13.5k 混谈

### 4.3 那「验证集 validation」在哪？

**通用部分**：默认已由 `download` 写出 **`data/raw/general_mixed/general_mixed_validation.jsonl`（1000）**，与 **`general_mixed_train.jsonl` 的 `id` 不相交**，规则是「每种语言抽样序列的**尾部**各一半验证」，详见 **`download_meta.json`** 里的 `split_mode` 与 `val_en_tail` / `val_zh_tail`。

**头脑风暴部分**：仓库里用 **`python -m data_pipeline export-brainstorm-val`**（依赖已有 `train.jsonl` 与译稿）按 spec 默认在训练 head **5000** 条**有效行**之后，再取 **3000** 条英文写入 **`validation_en.jsonl`**，并从 **`brainstorm_vicuna_10k_zh.jsonl`** 按 **`id`** 对齐写出 **`brainstorm_vicuna_10k_zh_validation.jsonl`**，摘要见 **`brainstorm_validation_meta.json`**。与 **S** 不交；缺译的 `id` 默认跳过中文行，可用 **`BRAINSTORM_VAL_REQUIRE_FULL_ZH=1`** 强制检齐。

**和 `test.jsonl`（脑暴 1k）**：仍适合更强 hold-out / 基线探针；**early stopping** 可组合 **`general_mixed_validation`** + 上述脑暴 val。

💡 **理解要点**：训练侧仍是 **13k**；**通用 1k** 与**脑暴 3k（默认）**验证集均**不进**这 13k。PoC 小预算仍可从 spec 建议的「前 1000 行 / 对应 id」取子集。


---

## 六、参考与延伸阅读（仓库内链接）

| 文档 | 用途 |
|------|------|
| [_docs/shaping/0_整体方案_端到端微调与端侧部署_CN.md](../shaping/0_整体方案_端到端微调与端侧部署_CN.md) | 端到端步骤索引与路线图 |
| [_docs/shaping/7_data_CN.md](../shaping/7_data_CN.md) | 数据配方、翻译策略、评估基准列表（shaping 层） |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | **v1.0 冻结规格**：路径、条数、确定性切片、跳过种子 |
| [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) | Sprint 1 周拆分与交付物 |
| [data_pipeline/README.md](../../data_pipeline/README.md) | 安装、`.env`、`download` / `translate` / `export-brainstorm-val` |
| [data/README.md](../../data/README.md) | `data/` 目录约定与排查 |

---

*本文为个人学习与技术备忘；若发现与仓库最新文件不一致，以仓库与 `s1-data-v1.0-spec` 为准。*
