# 微调端侧大模型 App 开发记录：2026-05-13，基线模型（Gemma）选型、下载与 Layer 2 推理

> **类型**：个人项目技术备忘  
> **日期**：2026-05-13  
> **GitHub repo**：https://github.com/zyctime-source/llm-fine-tunning-project  
> **英文版**：[Sprint1-03_baseline-gemma-layer2-infer_EN.md](Sprint1-03_baseline-gemma-layer2-infer_EN.md)

---

## 1. 背景

我一直对大模型微调很感兴趣。希望通过 vibe coding 在 3～4 个月内从零推进一个以大模型微调为核心、最终落在安卓端应用的落地项目，并全程留档。

### 1.1 项目背景：手机里的 AI 思维助手

**痛点**：灵感来时随手记，但传统笔记只能「存」不能「想」，也不能和其他灵感关联，三个月后回看，早已忘了当时的思路。

**方案**：做一款安卓 App，让「随手记的一句话」经过端侧大模型**追问-发散-收敛**，最终收成结构化的「灵感卡片」。选型上，用 **Gemma-4-E2B-IT**（4B 级）做基座，**LoRA 微调**对齐「头脑风暴」节奏，再量化到 INT4/INT8 塞进手机，兼顾隐私与成本。

**理解要点**：这不是通用聊天机器人，而是**结构化的思维辅助工具**——必须会追问、会收敛、能把散漫对话变成可行动的卡片。

### 1.2 本文聊什么

[Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) 已经说明了 **Layer 2 manifest** 的生成与版本化管理。本文接续同一时间线，记录以下内容：

- **基座模型**在 shaping 中的定位  
- **为何 Sprint 1 选择 Gemma-4-E2B-IT** 作为基线  
- **如何从 Hugging Face Hub 下载模型**到本地  
- **评测专用环境**的搭建与冒烟测试  
- **如何使用 `layer2_smoke_infer.py`** 按照 **`eval-protocol-v0`** 协议逐条跑通 manifest（包括全量 500 条与断点续传机制）

参考文档：
- 权威协议与报告骨架见 [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md)  
- 实验目录说明见 [experiment/baseline-gemma4e2b-it-layer2-v0/README.md](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md)  
- 端侧模型候选与许可证见 [_docs/shaping/6_model_strategy_CN.md](../shaping/6_model_strategy_CN.md)

---

## 2. 基座模型选型：Gemma-4-E2B-IT

### 2.1 shaping 中的候选模型

[_docs/shaping/6_model_strategy_CN.md](../shaping/6_model_strategy_CN.md) §6.1 将 **Gemma-4-E2B-IT**、**Gemma-4-E4B-IT**、**Qwen3.5-2B** 等列为 P0 观察对象。其中 **2B 级对决**（Gemma vs Qwen）是 PoC 阶段的核心对比焦点。许可证与端云分工详见同文档 §6.1.3、§6.3。

### 2.2 为何 Sprint 1 基线选择 Gemma-4-E2B-IT

本仓库 **Sprint 1 Week 1** 的基线实验 ID 为 **`baseline-gemma4e2b-it-layer2-v0`**（仅评测、无训练）。选择 Gemma-4-E2B-IT 的原因：

- **产品叙事一致**：先在 **Gemma-IT** 系列上建立 **Layer 2 回归基线**，后续微调和 PoC 对比才有固定参照点。  
- **评测协议一致**：[_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) §2、§4 明确被测模型为 **`google/gemma-4-E2B-it`**，解码采用 **`eval-protocol-v0`**（贪心解码、`max_new_tokens` 等参数见 §4.0）。  
- **manifest 对齐**：`META.json` 中的 `evaluation.manifest_version` 为 **`layer2-v0`**，推理脚本默认读取 `data/eval/layer2/manifest_v0.jsonl`。

**关于命名**：Hub 仓库名为 `gemma-4-E2B-it`（2B 参数指令模型）。shaping 文档中提到的「4B 级」指的是产品线中的 E4B 等更高档位，**与本基线 repo_id 不冲突**——以 Hub `repo_id` 和 `META.json` 为准。

### 2.3 2B 级候选：为何先跑通 Gemma（而不是 Qwen）

shaping 文档明确将 **Gemma-4-E2B-IT** 与 **Qwen3.5-2B** 并列为 **P0 观察对象**，并指出两者的 **2B 级对决**是 PoC 阶段的核心对比焦点。既然如此，为何 Sprint 1 基线先锁定 Gemma？

**当前决策逻辑（Sprint 1 Week 1）**：

| 因素 | Gemma-4-E2B-IT | Qwen3.5-2B | 本次选择理由 |
|------|----------------|------------|-------------|
| **发布时间** | 2026-04 | 2026-03 | Gemma 更新，先验证新架构 |
| **边缘优化** | 专为边缘设备（Any-to-Any 架构） | 通用多模态 | 与「端侧优先」产品叙事对齐 |
| **许可证** | Google 自定义许可（✅ 可商用） | Apache 2.0（最宽松） | Gemma 许可已满足商业使用；Qwen 许可更宽松，留作 PoC 备选 |
| **中文能力** | 需验证 | 原生优化 | Sprint 1 先跑通全链路；中文保护子层（zh_guard）即可初步评估 |
| **技术栈** | Transformers 官方示例完善 | 同样完善 | 两者都易接入，先选一个跑通流程 |

**关键理解**：
- **不是排斥 Qwen**：Qwen3.5-2B 仍是 **PoC 阶段核心对比对象**，将在后续 Sprint 建立平行基线或直接对比实验。
- **先跑通一个**：Sprint 1 的首要目标是建立 **端到端可复现的评测链路**（manifest → 下载 → 冒烟 → 全量 → 基线报告）。先在一个模型上跑通全链路，比同时铺开两个但都不完整更有价值。
- **许可权衡**：Gemma 的 Google 自定义许可允许商业使用，虽不如 Apache 2.0 宽松，但已满足当前阶段需求；若后续有更严格的许可要求，可随时切换到 Qwen。

---

## 3. 模型下载与版本冻结

### 3.1 首次下载模型权重

脚本使用 `transformers` 库的 `from_pretrained("google/gemma-4-E2B-it")`。**首次运行**时，会从 Hugging Face Hub 下载 `safetensors` 等文件到本地缓存（约 **10GB+**），耗时取决于网络带宽和磁盘速度。

Python 代码片段如下：

```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "google/gemma-4-E2B-it"

# 首次执行会自动下载权重到 ~/.cache/huggingface/hub/
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",      # 自动分配 GPU/CPU
    torch_dtype="auto",     # 自动选择 BF16/FP32
)

print(f"模型已加载：{model_id}")
print(f"参数数量：{sum(p.numel() for p in model.parameters()) / 1e9:.2f}B")
```

**配置建议**：在仓库根目录的 `.env` 文件中配置 **`HF_TOKEN`**（Read 权限即可），以避免匿名下载的限速问题。

```bash
# .env
HF_TOKEN=hf_your_token_here
```

国内镜像配置详见 [experiment/README.md](../../experiment/README.md) 的「Hugging Face：登录与国内下载加速」章节。

### 3.2 冻结 `revision`（Git commit）

基线报告 §2 要求长期记录 **`revision` / `commit`**，防止 Hub `main` 分支漂移导致无法复现。以实验目录 **[experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json)** 中的 **`base_model.revision`** 为**唯一事实来源**（当前示例值：`b324173c7d5721c2baba7f3b17b3b9b3d34ab1e9`，与本地 HF cache 中的 `snapshots/<revision>` 目录名一致）。

Windows 用户可从缓存目录读取该目录名作为 revision。定稿基线报告时，需将同一字符串填入 **s1-baseline-report_CN.md §2** 表格。

---

## 4. 评测环境（与数据管线分离）

- 数据下载/翻译使用 [requirements-data.txt](../../requirements-data.txt)  
- **Layer 2 推理与冒烟**使用 [requirements-eval.txt](../../requirements-eval.txt)

建议使用独立的虚拟环境（如 Conda `llm-eval`），原因详见 [experiment/README.md](../../experiment/README.md)「Layer 2 推理 / 冒烟」章节：依赖栈不同、NumPy 大版本差异、升级节奏与数据侧不同。

**基础安装步骤**：

```bash
cd /path/to/llm-fine-tunning-project
conda activate llm-eval   # 或 source .venv-eval/bin/activate
pip install -r requirements-eval.txt
```

---

## 5. 冒烟测试（快速验证，不跑全量）

目标：在**不加载全部 500 条**的情况下，快速验证以下内容：
- manifest 字段格式正确  
- `apply_chat_template` 工作正常  
- Gemma 模型权重可加载  
- GPU/CPU 推理路径可用

### 5.1 仅校验 prompt（不加载模型）

```bash
python scripts/layer2_smoke_infer.py --dry-run --limit 5
```

### 5.2 小批量实际推理（示例：3 条、短输出）

```bash
python scripts/layer2_smoke_infer.py --limit 3 --max-new-tokens 128
```

默认输出路径为 **`experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_<UTC时间>.jsonl`**。需将 **`results.raw_outputs_dir`** 和 **`results.smoke_infer_jsonl`** 写入 `META.json`（参见 [baseline README](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md)「已记录的冒烟产物」）。

**脚本行为要点**（与 s1-baseline-report §4 一致）：
- 采用**贪心解码**（`do_sample=False`）  
- 如果 manifest 末尾带有参考 **assistant** 轮次，会**先剥离**再进行生成，避免将标准答案混入 prompt

实现细节见 [scripts/layer2_smoke_infer.py](../../scripts/layer2_smoke_infer.py) 顶部说明与 `messages_for_generation` 函数。

---

## 6. 全量推理：逐条跑通 manifest

### 6.1 与 `eval-protocol-v0` 对齐的参数

全量 Layer 2 主跑参数应与 **s1-baseline-report §4.0** 保持一致：

- **`--limit 500`**：与 `manifest_v0.jsonl` 总条数一致（或根据需求调整子集）  
- **`--max-new-tokens 2048`**：协议主值；冒烟测试可用更小值节省时间  
- **解码方式**：脚本内固定为贪心解码，**不要**修改 `temperature` 进行采样对比（如需修改须 bump `eval-protocol` 版本）

### 6.2 实时写入与断点续传

脚本当前支持以下特性：

- **实时写入**：每条生成后立即追加写入 JSONL 并执行 `flush`，中断不丢失已完成的数据  
- **断点续传（`--resume`）**：根据已有输出文件中已出现的 **`layer2_id`** 自动跳过，适合长时间任务分多次执行

**使用示例**（全量 + 续传需显式指定 **`--out`** 指向已有文件）：

```bash
# 首次运行，指定固定输出文件
python scripts/layer2_smoke_infer.py --limit 500 --max-new-tokens 2048 --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_infer_full.jsonl

# 中断后恢复，使用同一输出路径
python scripts/layer2_smoke_infer.py --limit 500 --max-new-tokens 2048 --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_infer_full.jsonl --resume
```

**注意**：不设置 `--out` 时，每次运行会生成**新的**带时间戳的文件；如需断点续传，**必须**同时使用固定的 `--out` 和 `--resume` 参数。

### 6.3 跑完后回填

完成全量推理后，需执行以下步骤：

1. 将全量 JSONL 路径写入 **`META.json`** 的 `results` 字段（或扩展约定字段），并在 **s1-baseline-report §7** 填写「原始模型输出」路径  
2. （可选）按 §4.1 接入 **评委** `qwen3.6-plus` 进行评分  
3. 分层汇总与红线结论填入 **§5–§6**，并将 **`META.json` `status`** 与报告状态同步为定稿流程（参见 baseline README「待办」章节）

---

## 7. 相关文档索引

| 文档 | 用途 |
|------|------|
| [_docs/shaping/6_model_strategy_CN.md](../shaping/6_model_strategy_CN.md) | 端侧候选模型、许可证、微调阶段概念 |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | 被测模型表、Layer 2 定义、`eval-protocol-v0`、评委与报告结构 |
| [experiment/baseline-gemma4e2b-it-layer2-v0/README.md](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md) | 本实验目录约定、安装与冒烟步骤、待办清单 |
| [experiment/README.md](../../experiment/README.md) | 评测 venv、HF 登录与镜像配置 |
| [Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) | manifest 生成、字段与分层含义 |
| [_docs/eval/layer2/README.md](../eval/layer2/README.md) | manifest 路径与代理数据源说明 |

---

## 8. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-14 | 初版：串联 shaping 选型、Hub 下载与 revision、`requirements-eval`、冒烟与全量 manifest 推理（含 `--resume` / `--out`） |
| 2026-05-14 | 语言优化：简化长句、统一术语、澄清命名关系、优化段落结构 |
| 2026-05-14 | §2.3 增加「2B 级候选：为何先跑通 Gemma（而不是 Qwen）」，解释选型逻辑与 PoC 阶段对比计划 |
| 2026-05-14 | §3.1 增加模型下载代码片段（Python `from_pretrained` 与 huggingface-cli 两种方式） |
