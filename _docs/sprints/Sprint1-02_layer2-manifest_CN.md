# 微调端侧大模型 App 开发记录：2026-05-13，Layer 2 回归验证集 manifest

> **类型**：个人项目技术备忘  
> **日期**：2026-05-13  
> **GitHub repo**：https://github.com/zyctime-source/llm-fine-tunning-project  
> **英文版**：[Sprint1-layer2-manifest_EN.md](Sprint1-layer2-manifest_EN.md)

---

## 1. 背景

我一直对大模型微调很感兴趣。希望通过 vibe coding 在 3～4 个月内从零推进一个以大模型微调为核心、最终落在安卓端应用的落地项目，并全程留档。

### 1.1 项目背景：手机里的 AI 思维助手

**痛点**：灵感来时随手记，但传统笔记只能「存」不能「想」，也不能和其他灵感关联，三个月后回看，早已忘了当时的思路。

**方案**：做一款安卓 App，让「随手记的一句话」经过端侧大模型**追问-发散-收敛**，最终收成结构化的「灵感卡片」。选型上，用 **Gemma-4-E2B-IT**（4B 级）做基座，**LoRA 微调**对齐「头脑风暴」节奏，再量化到 INT4/INT8 塞进手机，兼顾隐私与成本。

**理解要点**：这不是通用聊天机器人，而是**结构化的思维辅助工具**——必须会追问、会收敛、能把散漫对话变成可行动的卡片。

### 1.2 本文聊什么

数据配方与训练验证集已在 [Sprint1-dataset_download_processing_CN.md](Sprint1-dataset_download_processing_CN.md) 和 [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) 中说明。

本文聚焦**评测环节**：如何把 shaping 文档中「约 500 条、分三层」的 Layer 2 目标，落地为仓库里**可版本化、可复现的 manifest（题单）**，以及它与 **Sprint 1 基线报告**中登记产物的对齐关系。

设计依据见 [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.1.3；实现细节见 [_docs/eval/layer2/README.md](../eval/layer2/README.md)；基线协议见 [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) §0/§3。

---

## 2. 什么是 manifest

**manifest（题单）是一份固定的测试题目清单。**

在模型微调项目中，我们需要反复测试模型表现。如果没有固定题单，每次测试随机抽题，就无法判断模型改进是真的能力提升，还是抽到了更简单的题目。

本文档讨论的 manifest 具体指 **Layer 2 回归验证集**：
- **文件格式**：`data/eval/layer2/manifest_v0.jsonl`，每行一条 JSON 记录
- **内容**：500 条固定测试题目，分三层（core 200 条、general 200 条、zh_guard 100 条）
- **版本**：当前为 `layer2-v0`，变更需 bump 版本号

类比理解：就像学生考试要有固定考卷，不能每次考试随机从课本里抽题，否则成绩无法比较。manifest 就是微调校准的「考卷」。

---

## 3. 为什么需要 manifest

不直接用原始数据文件（raw JSONL），而要用 manifest，有四个核心原因：

### 3.1 固定题面，确保可比性
同一 `layer2_id` 在不同实验、不同 checkpoint 间必须保持一致。随机抽题会引入「题目难度不同」的噪声，无法判断是模型进步还是题目变简单了。

### 3.2 可追溯，便于审计
每条记录保留 `source_local_path`、`source_line_1based`、`source_sample_id`，能精确定位到原始 Hub 数据或本地快照的哪一行。出了问题可以回溯源头。

### 3.3 与 shaping 分层对齐
manifest 中的 `stratum` 字段标记了 core/general/zh_guard 三层，基线报告 §5 按子层汇总时可直接分组，无需重新筛选。

### 3.4 与训练验证集区分
训练用的 `general_mixed_validation.jsonl` 和脑暴验证集（共约 4k 条）是**训练过程中**的 hold-out，用于早停和调参。

Layer 2 manifest（约 500 条）是**训练结束后**的回归测试，用于高频、低成本地检测「模型是否训歪了」。两者用途不同，不能混为一谈。

### 3.5 评估体系的三层结构（Layer 1/2/3）

除了本文重点讨论的 **Layer 2**，shaping 文档还定义了另外两层评估集，三者形成**金字塔结构**：

| 层级 | 规模 | 核心目的 | 使用时机 | 成本与频率 |
|------|------|----------|----------|-----------|
| **Layer 1**<br>能力探针集 | ~4,000+ 条 | 探索模型能力边界<br>全面横向对比 | PoC 阶段建基线<br>Stage 1 关键实验后深度分析 | 成本高<br>低频（阶段节点） |
| **Layer 2**<br>回归验证集 | ~500 条<br>（本文重点） | 检测能力退化<br>防「训歪」 | **每次实验后**自动跑 | 成本可控<br>高频（实验迭代） |
| **Layer 3**<br>生产验收集 | ~100 条 | 人工走查确认<br>「产品可用」感知 | Stage 1 结束前<br>上线前最终把关 | 人工成本高<br>极少（里程碑） |

**类比理解**：
- **Layer 1** 像「全面体检」：项目启动时做一次全套检查，了解身体各方面指标
- **Layer 2** 像「每日体温」：训练迭代时快速自测，发现异常立即停训调整
- **Layer 3** 像「入职体检」：上线前人工复核，确保产品层面可用

本文的 manifest 正是为了支撑 **Layer 2 的「每日体温」**机制——固定 500 道题，既足够覆盖核心/通用/中文三层能力，又不会因规模太大而无法高频运行。

---

## 4. 当前版本与文件位置（layer2-v0）

| 项 | 值 |
|----|-----|
| **Manifest 版本** | `layer2-v0`（写入 `manifest_meta.json` 的 `manifest_version`） |
| **题单文件** | `data/eval/layer2/manifest_v0.jsonl`（共 **500** 行，每行一条 JSON） |
| **元数据文件** | `data/eval/layer2/manifest_meta.json`（含条数、各子层种子、源路径、`proxy_notes`） |
| **生成脚本** | `scripts/build_layer2_manifest.py`（仅用 stdlib，不依赖 Hugging Face `datasets`） |

**与基线报告的对齐**：s1-baseline-report §0 表中「Layer 2 题单 manifest」指向上述路径；§3「本报告实际使用」表中的版本、路径、条数、抽样规则与本文一致。

---

## 5. manifest 里有什么字段

详见 [_docs/eval/layer2/README.md](../eval/layer2/README.md)「每条记录字段」。核心字段摘要：

| 字段 | 说明 |
|------|------|
| `layer2_id` | 稳定主键，如 `L2-core-00001` |
| `stratum` | 子层标记：`core` / `general` / `zh_guard` |
| `source_hub_repo` / `source_local_path` / `source_line_1based` / `source_sample_id` | 追溯信息，定位原始数据来源 |
| `messages` | OpenAI 风格多轮对话，评测时直接送入 Gemma chat 模板 |
| `content_sha256` | 对规范化 `messages` 的哈希，防止数据被静默篡改 |

---

## 6. 抽样规则（v0）与理想目标的差距

| 子层 | 规模 | 本地材料（v0） | 随机种子（默认） |
|------|------|----------------|------------------|
| **core** | 200 | `brainstorm_vicuna_10k_zh.jsonl` 全文件无放回抽样 | 42 |
| **general** | 200 | 通用混合 JSONL 中 `lang=="en"` 行无放回抽样 | 43 |
| **zh_guard** | 100 | 同上，`lang=="zh"` 行 | 44 |

**通用混合源路径**：脚本**优先**读取 `general_mixed_train.jsonl`，不存在则回退到 `general_mixed.jsonl`。`manifest_meta.json` 中的 `paths.general_mixed_source` 记录的是**生成当时**实际使用的文件。

**注意**：如果从 legacy 全文（约 4k 行）切换到仅 train 子集（3k 行），抽样池会变化，即使种子相同，题面也可能不同。此时应保留旧 manifest 用于对比，或 bump 版本（如 `layer2-v0.1`）并重跑基线。

**理想 vs 现实的差距**：
- shaping 中通用子层理想来源是 **X-AlpacaEval**，v0 用 `tatsu-lab/alpaca` 英文行作**代理**
- shaping 中中文子层理想来源是 **CMT-Eval**，v0 用 `evol-instruct-chinese` 行作**代理**

代理说明写在 `manifest_meta.json` 的 `proxy_notes` 中。升级真实数据源时应 bump manifest 版本。

---

## 7. 如何生成或重放

**前置条件**：
- 已存在 `data/processed/brainstorm_vicuna_10k_zh.jsonl`
- 已存在 `general_mixed_train.jsonl` 或 `general_mixed.jsonl`

若缺失，脚本会报错并提示先运行 `python -m data_pipeline download`。

**生成命令**：

```bash
python scripts/build_layer2_manifest.py

# 显式指定种子，便于文档与 CI 对齐：
python scripts/build_layer2_manifest.py --seed-core 42 --seed-general 43 --seed-zh 44 
```

输出会覆盖 `data/eval/layer2/manifest_v0.jsonl` 和 `manifest_meta.json`。

---

核心代码（`scripts/build_layer2_manifest.py`）

```python
# ========== 1. 路径优先级：优先 train，回退 legacy ==========
GENERAL_MIXED_TRAIN_PATH = (
    REPO_ROOT / "data" / "raw" / "general_mixed" / "general_mixed_train.jsonl"
)
GENERAL_MIXED_LEGACY_PATH = (
    REPO_ROOT / "data" / "raw" / "general_mixed" / "general_mixed.jsonl"
)

def _resolve_general_mixed_path() -> Path:
    if GENERAL_MIXED_TRAIN_PATH.exists():      # 优先：3k 训练子集
        return GENERAL_MIXED_TRAIN_PATH
    if GENERAL_MIXED_LEGACY_PATH.exists():     # 回退：legacy 全文
        return GENERAL_MIXED_LEGACY_PATH
    raise SystemExit("Missing general mix JSONL...")

# ========== 2. 抽样逻辑：固定种子，无放回 ==========
CORE_N = 200
GENERAL_N = 200
ZH_N = 100

def build_manifest(out_dir: Path, seed_core: int, seed_general: int, seed_zh: int) -> None:
    # core：从 brainstorm 全文件抽 200 行，种子 42
    rng_c = random.Random(seed_core)
    core_line_nums = sorted(rng_c.sample([ln for ln, _ in brainstorm], CORE_N))
    
    # general：从 en 行抽 200 行，种子 43
    en_indices = [ln for ln, r in general_rows if r.get("lang") == "en"]
    rng_g = random.Random(seed_general)
    general_line_nums = sorted(rng_g.sample(en_indices, GENERAL_N))
    
    # zh_guard：从 zh 行抽 100 行，种子 44
    zh_indices = [ln for ln, r in general_rows if r.get("lang") == "zh"]
    rng_z = random.Random(seed_zh)
    zh_line_nums = sorted(rng_z.sample(zh_indices, ZH_N))

# ========== 3. 记录构建：三种子层不同处理 ==========
# core：ShareGPT 格式转 OpenAI messages
core_msgs = _sharegpt_zh_to_messages(r["conversations_zh"])

# general / zh_guard：直接使用 messages，标记不同 source_repo
general_repo = r.get("source_repo", "tatsu-lab/alpaca")
zh_guard_repo = r.get("source_repo", "FreedomIntelligence/evol-instruct-chinese")

# 每条记录包含：layer2_id, stratum, messages, content_sha256, 追溯信息
record = {
    "layer2_id": f"L2-core-{counter:05d}",    # 或 general/zh_guard
    "stratum": "core",                       # core | general | zh_guard
    "source_hub_repo": "...",
    "source_local_path": "...",
    "source_line_1based": ln,
    "source_sample_id": r.get("id"),
    "messages": msgs,                        # OpenAI 格式
    "content_sha256": _sha256_messages(msgs), # 防篡改哈希
}

# ========== 4. 输出产物 ==========
# manifest_v0.jsonl：500 条 JSONL 记录
# manifest_meta.json：元数据（版本、种子、源路径、proxy_notes）
```

**关键设计要点**：
- **纯 stdlib**：仅用 `json`, `random`, `hashlib`，不依赖 Hugging Face `datasets`，避免 NumPy/pandas 环境问题
- **确定性**：`random.Random(seed)`（非全局 `random`），确保跨机器复现同一题单
- **内容哈希**：`content_sha256` 基于规范化 JSON，防静默篡改

完整脚本见 [`scripts/build_layer2_manifest.py`](../../scripts/build_layer2_manifest.py)。

---

## 8. 什么时候用到 manifest

manifest 在**评测流水线**的多个阶段被使用：

### 8.1 冒烟测试（开发阶段）
`scripts/layer2_smoke_infer.py` 读取 manifest 的少量记录（如 3 条），验证：
- Gemma 模型能否正常加载
- chat 模板是否能正确处理 `messages` 字段
- manifest 字段格式是否正确

产物路径记录在 [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) 中。

### 8.2 基线评测（Sprint 1）
跑满 500 条，在固定的 **eval-protocol-v0**（见 s1-baseline-report §4）下：
1. 用 Gemma 生成回答（`temperature=0`，固定种子）
2. 可选：用评委模型（如 `qwen3.6-plus`）打分
3. 按子层汇总结果，填入基线报告 §5

### 8.3 实验对比（PoC / Stage 1）
每次微调实验后，用**同一 manifest 版本**和**同一评测协议**跑测试，与基线对比：
- 核心能力是否退化？
- 通用能力是否保持？
- 中文表达是否正常？

**关键原则**：对比实验时只能改模型权重和训练相关变量，manifest 和评测协议必须保持一致，否则结果不可比。

### 8.4 实验记录
建议在每次实验的 `META.json` 中写明：
```json
{
  "manifest_version": "layer2-v0",
  "manifest_path": "data/eval/layer2/manifest_v0.jsonl",
  "eval_protocol": "eval-protocol-v0"
}
```

这样未来看到 `layer2-v1` 时，不会与当前实验混淆。

---

## 9. 相关文档索引

| 文档 | 用途 |
|------|------|
| [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) | Layer 1/2/3 分层设计、红线类型；§9.1.3 为 Layer 2 目标规模与原则 |
| [_docs/eval/layer2/README.md](../eval/layer2/README.md) | manifest 字段详情、抽样逻辑、代理数据源说明、与训练验证集区分 |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | 基线报告骨架；§3 绑定 manifest 与评测协议 |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | 训练数据与训练向验证集规格（与 Layer 2 并行，勿混用） |
| [Sprint1-dataset_download_processing_CN.md](Sprint1-dataset_download_processing_CN.md) | 同日期数据准备备忘（下载、翻译、export-brainstorm-val） |
| [Sprint1-baseline-gemma-layer2-infer_CN.md](Sprint1-baseline-gemma-layer2-infer_CN.md) | 基线 Gemma 选型、Hub 下载与 revision、评测环境、冒烟与全量 manifest 推理 |

---

## 10. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-14 | 初版：对齐 `layer2-v0`、`s1-baseline-report` §0/§3 与 eval README |
| 2026-05-14 | 相关文档索引：增加 [Sprint1-baseline-gemma-layer2-infer_CN.md](Sprint1-baseline-gemma-layer2-infer_CN.md)（基线推理备忘） |
