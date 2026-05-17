# Sprint 1 数据规格报告

| 属性 | 值 |
|------|-----|
| **数据版本** | `v1.0` |
| **文档版本** | 1.4 |
| **状态** | 已冻结（配方 + 本地快照规则）；**自建种子 500 当前明确跳过**（见 §1、§2、§4.5.2） |
| **对齐 shaping** | [_docs/shaping/7_data_CN.md](../shaping/7_data_CN.md) §7.3.1 |
| **流水线代码** | 仓库 `data_pipeline/`（生成脚本）；本规格描述**内容与追溯**，不重复实现细节 |
| **代码快照（可复现）** | Git `HEAD` = `23bd3f6e2eee153e38ed60c3d8cc35639d21d915`（记录时仓库提交；重放时请固定此提交或等价 tag；**以你本机 `git rev-parse HEAD` 为准更新此行**） |

---

## 1. `v1.0` 含义（冻结粒度）

**已冻结：**

1. **配方表**：各子集名称、目标条数、占比（与 §2 一致）。
2. **来源数据集**：Hub `repo_id`、本地落盘路径、`download_meta.json` 中记录的分片条数 / 抽样参数。
3. **训练子集构造规则**：如何从全量 `train` 与翻译产物中取出 **5k + 5k + 3k（通用训练块）**（见 §4）；规则为确定性算法，不依赖「口头约定」。
4. **通用混合（训练 + 验证）**：`download` 默认各源抽样 **2000 EN + 2000 ZH**（`seed=42`），按语种尾部切出 **1000** 条作 **`general_mixed_validation.jsonl`**，其余 **3000** 条作 **`general_mixed_train.jsonl`**（见 §3.3）。`GENERAL_VAL_N=0` 时仍为单一 `general_mixed.jsonl`（不推荐，仅兼容旧配置）。
5. **脑暴验证导出**：在 §4.1 训练 head **之后**取 **3000** 条有效 `train.jsonl` 行（与 **\(S\)** 不交），并从 `brainstorm_vicuna_10k_zh.jsonl` 按 **`id`** 对齐写出验证集（见 §3.5、§4.4）；**不并入** 13k 训练配方。

**未冻结 / 待补（不阻塞 Week2 PoC 读 spec，但 Gate1 前建议补齐）：**

- **自建种子 500**：尚未落盘；§4.5.1 为建立指南。**当前决策：暂无数据，本阶段跳过**（见 §4.5.2）；不阻塞 PoC / Stage1 主线，仅在实验与报告中注明 **`data_profile=v1.0-skip-seed`**（或等价字段），以便与「满 13.5k」的 shaping 理想配方区分。
- **HF `revision`**：`brainstorm` 当前为 `null`（默认分支快照）；再次全量下载时建议在 `download_meta.json` 中写入具体 `revision` 以便长期 bitwise 复现。

---

## 2. 配方总表（与 shaping 7.3.1 一致）

| 子集 | 目标条数 | 占比 | 说明 |
|------|----------|------|------|
| brainstorm_vicuna_10k（英文原版） | 5,000 | 35% | 核心脑暴（英文） |
| brainstorm_vicuna_10k（Qwen 翻译中文版） | 5,000 | 35% | 与英文子集 **同 `id` 对齐** 的平行中文 |
| Alpaca / ShareGPT（中英混合通用，**训练**） | 3,000 | 25% | 由 `download` 写为 `general_mixed_train.jsonl`（与验证块 **id 不相交**） |
| 自建种子数据（个人创意案例） | 500（shaping 目标） | 5% | **当前跳过：0 条**；有数据后按 §4.5.1 落盘 `data/raw/seed_v1.0/` |
| **合计（shaping 目标）** | **13,500** | **100%** | 设计总目标 |
| **合计（当前可训子集）** | **13,000** | ≈96.3% | **5k EN + 5k ZH + 3k 通用**，不含种子；与「跳过种子」决策一致 |

**验证集（默认，不计入上表「可训 13k」）**

| 名称 | 目标条数 | 生成方式 | 说明 |
|------|----------|----------|------|
| 通用混合验证 | 1,000 | `python -m data_pipeline download`（`GENERAL_VAL_N>0`） | `general_mixed_validation.jsonl`，与 `general_mixed_train` 的 `id` 不交，§3.4 |
| 脑暴验证（英+中对齐） | 3,000（英文窗） | `python -m data_pipeline export-brainstorm-val` | `validation_en.jsonl` + `brainstorm_vicuna_10k_zh_validation.jsonl`，与训练集合 **S** 不交，§3.5、§4.4；译稿不全时 `written_zh` 可能小于 `written_en`，见 `brainstorm_validation_meta.json` |

`GENERAL_VAL_N=0` 时无「通用验证」文件，仅保留旧版单一 `general_mixed.jsonl`（不推荐）。

**命名建议：** 在训练实验的 `META.json` / README 中写明 `data_version=v1.0` 且 `seed_block=skipped`（或 `data_profile=v1.0-skip-seed`），避免日后与「含 500 种子」的跑法混淆。

---

## 3. 本地产物与追溯指针

默认 **`DATA_ROOT=./data`**（相对仓库根）。若你使用其他根目录，以下路径按 `DATA_ROOT` 类推。

### 3.1 brainstorm 主集（HF 导出）

| 项 | 值 |
|----|-----|
| Hub `repo_id` | `DevQuasar/brainstorm_vicuna_10k` |
| `revision`（记录时） | `null`（见 `data/raw/brainstorm_vicuna_10k/download_meta.json`） |
| `train` 行数 | 10,000 |
| `test` 行数 | 1,000（**默认不纳入 v1.0 训练配方**；保留作评测或其它 split 策略时引用） |
| 本地路径 | `data/raw/brainstorm_vicuna_10k/train.jsonl`、`test.jsonl` |
| 元数据 | `data/raw/brainstorm_vicuna_10k/download_meta.json` |

**说明（可选产物）：** **`validation_en.jsonl`** 由 **`export-brainstorm-val`** 写出，**不是** **`download`** 的产物；默认路径与规则见 §3.5、§4.4。

### 3.2 brainstorm 中文翻译（云端 Qwen）

| 项 | 值 |
|----|-----|
| 流水线 | `python -m data_pipeline translate`（见 [data_pipeline/README.md](../../data_pipeline/README.md)） |
| 本地路径 | `data/processed/brainstorm_vicuna_10k_zh.jsonl` |
| 行结构 | 每行含 `id`、`conversations_zh`、`conversations_en` 等；**训练用中文轮次以 `conversations_zh` 为准**；`from` 已与英文对齐（见 `conversation_format.apply_original_speaker_roles_to_translated_turns`） |
| API / 模型 | 由 `.env` 中 `DASHSCOPE_*`、`TRANSLATE_MODEL` 配置（**勿将密钥提交进仓库**）；实验记录中应另记「模型名 + 日期」 |

**说明：** 翻译文件行数可能 ≥ 5,000（例如接近全 `train` 译完）；**v1.0 训练用中文 5k 仍只取与 §4 英文子集同 `id` 的 5,000 行**，不要求整文件恰好 5k 行。

### 3.3 通用混合（Alpaca + 中文指令）

| 项 | 值 |
|----|-----|
| 英文 Hub | `tatsu-lab/alpaca`，`split=train`，默认抽样 **2,000**（`GENERAL_EN_SAMPLE_N`） |
| 中文 Hub | `FreedomIntelligence/evol-instruct-chinese`，`split=train`，默认抽样 **2,000**（`GENERAL_ZH_SAMPLE_N`） |
| 随机种子 | `42`（`GENERAL_SEED`） |
| 验证 hold-out | 默认 **`GENERAL_VAL_N=1000`**：英文尾 **500** + 中文尾 **500**（`split_mode=train_val_by_language_tail`），写入 **`general_mixed_validation.jsonl`** |
| 训练子集路径 | `data/raw/general_mixed/general_mixed_train.jsonl`（**3,000** 行） |
| 验证子集路径 | `data/raw/general_mixed/general_mixed_validation.jsonl`（**1,000** 行） |
| 兼容模式 | `GENERAL_VAL_N=0` 时只写 **`general_mixed.jsonl`**（全文 = 两语言抽样之和），不再拆 train/val |
| 元数据 | `data/raw/general_mixed/download_meta.json`（含 `*_n_obtained`、`written_train_rows`、`written_val_rows` 或 `written_rows`、`split_mode`） |
| 行结构 | 归一化后含 `id`、`lang`、`source_repo`、`schema`、`messages` 等（见 `general_normalize.py`） |

### 3.4 通用混合验证集（1,000，默认）

本块**不并入** §4 所述 **13k 训练配方**；供 **early stopping / 粗调超参** 或框架强制 `validation` 分片时使用。与 **`general_mixed_train.jsonl` 的 `id` 集合不相交**；切分规则见 §3.3「验证 hold-out」。

### 3.5 脑暴验证导出（与 §4.1 训练 head 不交）

| 项 | 值 |
|----|-----|
| 命令 | `python -m data_pipeline export-brainstorm-val`（须先有 `train.jsonl` 与 `brainstorm_vicuna_10k_zh.jsonl`） |
| 英文路径（默认） | `data/raw/brainstorm_vicuna_10k/validation_en.jsonl`（`BRAINSTORM_VAL_EN_JSONL` 可覆盖） |
| 中文路径（默认） | `data/processed/brainstorm_vicuna_10k_zh_validation.jsonl`（`BRAINSTORM_VAL_ZH_JSONL` 可覆盖） |
| 元数据 | `data/processed/brainstorm_validation_meta.json`（`written_en` / `written_zh` / `missing_zh_ids_sample` 等） |
| 默认条数 | 跳过训练 head **5,000** 条有效行后，再取 **3,000** 条（`BRAINSTORM_TRAIN_HEAD_N` / `BRAINSTORM_VAL_EXPORT_N`） |
| 严格对齐 | `BRAINSTORM_VAL_REQUIRE_FULL_ZH=1` 时：验证窗口内任一 `id` 无译稿则**报错**退出 |

构造规则细节见 §4.4。

---


## 4. v1.0 训练子集构造规则（确定性）

以下规则用于从「全量已下载 / 已翻译」材料中构造 **与 shaping 条数一致** 的训练切片。

### 4.1 英文 brainstorm（5,000）

- **来源文件**：`data/raw/brainstorm_vicuna_10k/train.jsonl`
- **规则**：按文件 **从上到下的物理顺序**，取 **前 5,000 条有效样本**：跳过仅空白行；其余行须能 **`json.loads` 解析为对象**后计入序号（与 **`export-brainstorm-val`** 对训练 head 的计数一致；若某行非法 JSON，应在重放前修复源文件或在本 spec 勘误中记录）。
- **主键**：每行 JSON 的 `id` 字段；记集合 **\(S\) = { 这 5000 行的 `id` }**。

### 4.2 中文 brainstorm（5,000）

- **来源文件**：`data/processed/brainstorm_vicuna_10k_zh.jsonl`
- **规则**：筛出 **`id` ∈ \(S\)** 的所有行；若某 `id` 缺失则 **该 `id` 暂不纳入 v1.0 中文块**（应在合并脚本中打日志）；目标为 **恰好 5,000** 行，若不足则以「缺译清单」驱动补译或收紧 §4.1 子集直至对齐。
- **当前假设**：翻译已覆盖 `train` 前 5k 对应 `id`（与当前流水线实践一致）；若实际不足，在 `v1.0.1` 或勘误段记录差集。

### 4.3 通用混合（3,000，训练块）

- **来源文件**：`data/raw/general_mixed/general_mixed_train.jsonl` **全文**（默认 **3,000** 行；由 `download_meta.json` 校验 `written_train_rows`）。
- **不再二次抽样**，避免与已发布 `download_meta` 不一致。
- **验证用 1,000** 条见 §3.4，**勿并入**本训练块。

### 4.4 brainstorm 验证（默认 3,000）

- **用途**：与 **§4.1–4.2 训练脑暴**同分布的 hold-out，供训练过程验证；**不并入** 13k 训练配方。
- **英文**：`data/raw/brainstorm_vicuna_10k/train.jsonl`，在数满 **5,000** 条有效 JSON 行（与 §4.1 相同计数）之后，再顺序取 **3,000** 条有效行，写入 **`validation_en.jsonl`**（默认路径见 §3.5）。
- **中文**：`data/processed/brainstorm_vicuna_10k_zh.jsonl`，仅保留 **`id`** 落在上述英文验证窗口**且顺序一致**的译稿行，写入 **`brainstorm_vicuna_10k_zh_validation.jsonl`**。若某 `id` 尚未翻译：默认**跳过**该条中文，并在 `brainstorm_validation_meta.json` 中记录 `missing_zh_*`；设 `BRAINSTORM_VAL_REQUIRE_FULL_ZH=1` 则命令失败以倒逼补译。
- **主键**：验证英文窗口内 `id` 集合记为 **\(V\)**，满足 **\(V \cap S = \emptyset\)**（**\(S\)** 见 §4.1）。

### 4.5 自建种子（500）

- **状态**：**未包含于当前磁盘快照**；目标路径建议 `data/raw/seed_v1.0/`（待创建）。
- **格式**：待与下游训练脚本对齐（建议与 `general_mixed` 相同 `messages` 结构，便于同一 loader）。

#### 4.5.1 建立步骤（操作指南）

**1. 明确用途（与 shaping 一致）**  
[_docs/shaping/7_data_CN.md](../shaping/7_data_CN.md) §7.3.1 中该块占 **5%**，定位为 **「个人创意案例」+ 个性化风格预留**：补充公开脑暴数据里没有的、**更贴近你产品场景** 的写法（例如：你的领域术语、常用追问方式、从「随手记」到「卡片收成」的短流程）。它不是主能力来源，而是 **防止模型只会泛化脑暴、却不像你的产品**。

**2. 内容从哪来**  

| 来源 | 建议 |
|------|------|
| 你自己写 | 每条 1～多轮对话，用你真实会说的用户话 + 你期望的助手风格（可半草稿后润色） |
| 脱敏后的真实对话 | 若有历史对话，去掉姓名、电话、内部项目代号等 **PII** 后再写入 |
| 少量改写 | 从 `brainstorm` 某条得到灵感，**改场景与措辞**，避免与 HF 行逐字重复（减少版权/重复感） |

**3. 条数与节奏**  
- 目标 **500** 条；可先凑 **50～100** 条定好模板与质检标准，再批量补到 500。  
- **Week2 PoC** 若时间紧：可暂时 **0 条或少量**（在 spec / 实验记录里注明 `v1.0-a`），**Gate1 前** 再补满或接受 12.5k 主配方训练（与 shaping 的「保守」一致，但要在报告里写明）。

**4. 推荐落盘结构**  

```text
data/raw/seed_v1.0/
  README.md          # 撰写人、日期、用途、是否含真实场景脱敏说明
  seed_v1.0.jsonl    # 每行一条 JSON
  seed_meta.json     # 可选：条数、版本、与 v1.0 配方对齐的 checksum 计划等
```

**5. 每行 JSON 建议字段（与 `general_mixed` 对齐）**  

每条至少包含：

- `id`：稳定唯一键，例如 `seed-v1.0-00001`（勿与 HF `id` 冲突）。  
- `lang`：`zh` / `en` / `mixed`（按正文主体标即可）。  
- `source_repo`：固定为 `local/seed_v1.0` 或 `user/yichao1991/seed_v1.0` 等可识别字符串。  
- `schema`：建议 `sharegpt_conversations` 或与脑暴一致的 `conversations`（`human`/`gpt` 交替）；若用 OpenAI 式统一 loader，则用 **`messages`**（与 `general_mixed_train.jsonl` 相同），例如：

```json
{
  "id": "seed-v1.0-00001",
  "lang": "zh",
  "source_repo": "local/seed_v1.0",
  "schema": "messages_turns",
  "messages": [
    {"role": "user", "content": "……"},
    {"role": "assistant", "content": "……"}
  ]
}
```

多轮则继续追加 `user` / `assistant` 交替即可。

**6. 质量自检（最低门槛）**  

- 无空 `content`、无单轮只有一方。  
- 中文通顺、无大量模板套话重复。  
- 与「脑暴+产品场景」相关；纯百科问答可少量，**不宜占大头**（否则与 Alpaca 块重复）。  
- 建议维护一张 **简单表格**（CSV 即可）：`id`、主题标签、是否已人工读过，便于以后 Stage2 再筛。

**7. 并入 v1.0 训练包**  
合并训练 JSONL 时，把 `seed_v1.0.jsonl` 与 §4.1–4.3 的训练块输出 **按配方比例或打乱后混合**；在 **manifest** 里标记 `source_block=seed_v1.0`，便于回溯与剔除。

**8. 不必用 `data_pipeline download`**  
种子是 **本地撰写**，不来自 HF 自动下载；若日后写 small 脚本校验 JSONL 行数与字段，可放在 `data_pipeline/` 或 `scripts/` 下单独说明即可。

#### 4.5.2 当前决策：跳过种子（0 条）

- **原因**：暂无个人创意案例素材。  
- **影响**：训练配方按 **13,000 条**（5k+5k+3k）执行，与 shaping 理想 **13,500** 相差 500，**可接受**；个性化风格主要靠后续 Stage2 或补种子后再训。  
- **记录义务**：每次训练实验注明 `seed_block=skipped` 或 `data_profile=v1.0-skip-seed`。  
- **恢复条件**：一旦具备 ≥50 条可用草稿，建议启动 §4.5.1；满 500 后更新本 spec 状态行并取消 `skip-seed` 标记。

---

## 5. 与 Week2 PoC 的衔接

| 输入 | 说明 |
|------|------|
| PoC 数据量（shaping） | 常为 **1k** 子集；可从 §4.1 的前 **1,000** 行 / 对应 `id` 取子集 |
| 合并脚本 | 尚未在本仓库强制要求；建议在 `v1.0` 合并脚本中输出 **manifest**（每行：`global_id`、`source_block`、`source_id`、`split`） |

---

## 6. 缺口、风险与补救

| 项 | 风险 | 补救 |
|----|------|------|
| HF `revision` 为 `null` | 未来 Hub 更新可能导致字节级不一致 | 下次全量下载时固定 `BRAINSTORM_DATASET_REVISION` 并更新本 spec |
| 中文 5k 与英文 `id` 不对齐 | 缺译或重复 | 以 §4.2 规则过滤 + 补译缺失 `id` |
| 种子 500 跳过 | 与 shaping 13.5k 理想有 500 条差距 | **已批准当前阶段跳过**（§4.5.2）；Gate1 或 Stage2 前再评估是否补种 |
| 翻译模型漂移 | 不同日期 Qwen 译文不同 | 在实验 `META.json` 中记录 `TRANSLATE_MODEL` 与运行日期 |
| 脑暴验证窗内缺译 | `written_zh` 少于 `written_en`，对齐验证子集尴尬 | 补跑 `translate` 覆盖 §4.4 窗口 `id`，或接受 meta 中的 `missing_zh_*`；必要时设 `BRAINSTORM_VAL_REQUIRE_FULL_ZH=1` 强制检齐 |
| 仅存在 `general_mixed.jsonl` | 旧 `.env`（`GENERAL_VAL_N=0`）或旧版脚本，无通用验证分片 | 对齐 `.env.example` 中 `GENERAL_*` / `GENERAL_VAL_N`，重新执行 `download` |

---

## 7. 相关文档与命令

- Shaping：[_docs/shaping/7_data_CN.md](../shaping/7_data_CN.md) · [_docs/shaping/7_data_EN.md](../shaping/7_data_EN.md)
- Sprint 1 备忘（数据准备长文）：[_docs/sprints/Sprint1-dataset_download_processing_CN.md](../sprints/Sprint1-dataset_download_processing_CN.md) · [_docs/sprints/Sprint1-dataset_download_processing_EN.md](../sprints/Sprint1-dataset_download_processing_EN.md)
- Sprint 1 执行：[_docs/execution/sprint-1-train.md](sprint-1-train.md)
- 数据目录说明：[data/README.md](../../data/README.md)
- 流水线：[data_pipeline/README.md](../../data_pipeline/README.md) · [data_pipeline/README_EN.md](../../data_pipeline/README_EN.md)（含 `download` / `translate` / `export-brainstorm-val`）

---

## 8. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-12 | 初版：对齐已落地的 `data_pipeline` + `data/raw` + `data/processed` 快照与 `download_meta` |
| 2026-05-12 | §4.5.1（彼时 §4.4.1）：补充自建种子 500 的建立步骤与 JSON 字段建议 |
| 2026-05-14 | 「通用混合」默认抽样 4k 后拆 `general_mixed_train` / `general_mixed_validation`；脑暴验证 `export-brainstorm-val`、§3.5、§4.4；自建种子顺延 §4.5；文档版本 **1.2** |
| 2026-05-17 | 无训练数据配方变更：交叉索引——Layer 2 **评测**基线产物见 [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json)（`v1.0` 训练子集与 manifest 定义不变）。 |
