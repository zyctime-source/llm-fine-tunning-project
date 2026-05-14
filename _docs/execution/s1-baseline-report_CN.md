# Sprint 1 基线评测报告：`s1-baseline-report`

| 属性 | 值 |
|------|-----|
| **报告 ID** | `s1-baseline-report` |
| **文档状态** | **骨架（WIP）** — 结构与协议已写死；**分层数值待跑完 Layer 2 后填入** |
| **对应实验 ID（建议）** | `baseline-gemma4e2b-it-layer2-v0`（元数据目录：[experiment/baseline-gemma4e2b-it-layer2-v0](../experiment/baseline-gemma4e2b-it-layer2-v0/)） |
| **数据配方** | [s1-data-v1.0-spec_CN.md](s1-data-v1.0-spec_CN.md)（当前可为 `v1.0-skip-seed`） |
| **评估分层依据** | [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.1.3（Layer 2 回归验证集） |
| **评测协议** | `eval-protocol-v0`（见 **§4**；Gemma 贪心 + 评委 `qwen3.6-plus`） |

## 0. 文档状态与待办

| 步骤 | 状态 | 说明 |
|------|------|------|
| Layer 2 题单 manifest（~500 条，含子层标签） | ☑ 已完成（`layer2-v0`） | 产物：`data/eval/layer2/manifest_v0.jsonl` + `manifest_meta.json`；说明见 [_docs/eval/layer2/README.md](../eval/layer2/README.md) |
| 推理协议（模板、温度、max tokens、系统提示） | ☑ 已冻结 | **§4 `eval-protocol-v0`**（2026-05-12）；变更须 bump 版本，见 §4.3 |
| 基座可加载冒烟 | ☑ 已通过（小样本） | `layer2_smoke_infer` 3 条、`max_new_tokens=128`；产物路径见 [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) → `results`；全量 500 条前仍可保留本行「小样本」语义 |
| 跑满 Layer 2 全量推理 +（可选）评委打分 | ☐ 待运行 | 原始输出落盘路径填入 **§7** |
| 分层汇总表 + 红线结论 | ☐ 待填入 | **§5–§6** |
| 更新本报告状态为「已定稿」 | ☐ 待完成 | 定稿日期写入 §0 表 |

---

## 1. 摘要（Executive summary）

**（跑完评测后填写 5～10 句）**

- **基座模型**：**[google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it)**（Hub `repo_id` 见 §2；`revision` 在本地快照中冻结）。
- **评估集**：Layer 2 回归集，共 **500** 条（`layer2-v0`）；子层：核心 **200** / 通用 **200** / 中文保护 **100**。
- **结论一句话**：例如「基线可接受 / 存在 P2 预警 / 触发 P1 须停」— **TBD**。
- **对 Week2 PoC 的含义**：例如「PoC 后对比同一协议、同一 manifest 版本」— **TBD**。

---

## 2. 被测模型（Model）

| 项 | 值 |
|----|-----|
| **显示名** | Gemma 4 E2B IT（指令微调；Sprint 与 shaping 称 **Gemma-4-E2B-IT**） |
| **Hub 页面** | [https://huggingface.co/google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it) |
| **Hub `repo_id`** | `google/gemma-4-E2B-it` |
| **`revision` / `commit`** | **`____________`**（下载时在代码或 `download_meta` 中写入 **具体 Git revision**；勿长期留空以便 bitwise 复现） |
| **License** | Apache 2.0（以模型卡为准） |
| **精度 / 设备** | 推荐 **`dtype="auto"`** 或 **BF16**（与权重 `safetensors` 一致）；设备：`CUDA` / `CPU`（填写：`___________`） |
| **加载方式（官方文本多轮）** | `transformers`：`AutoProcessor` + **`AutoModelForCausalLM`** + `device_map="auto"`（见模型卡 *Getting Started*；**Layer2 纯文本评测**优先此路径） |

**说明**：模型卡上的 `AutoProcessor` 会带上多模态子模块（可能额外依赖 `torchvision` / `Pillow`）。本仓库 **Layer 2 文本冒烟/批跑脚本**（`scripts/layer2_smoke_infer.py`）为减少环境依赖，对纯文本 manifest 使用 **`AutoTokenizer` + `AutoModelForCausalLM`**，与同一 `chat_template` 对齐；若你自行改为 `AutoProcessor`，请按 Transformers 报错补齐依赖。
| **多模态（图/音/视频）** | 若评测含非文本模态，改用 `AutoModelForMultimodalLM`（见同一模型卡；**与 Layer2 manifest 一致**） |
| **Tokenizer 是否与训练一致** | 微调数据与推理均使用同一 **`google/gemma-4-E2B-it`** processor / chat template 即为 **是** |

**说明**：模型卡 *Best Practices* 中通用采样推荐 `temperature=1.0` / `top_p=0.95` / `top_k=64`；本报告 **评测基线** 采用 **§4 `eval-protocol-v0` 的贪心解码**，与「日常聊天最佳体验」区分开，避免与 PoC 对比时混用两套解码。

---

## 3. Layer 2 评估集定义

与设计文档一致（[_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.1.3）：

| 子层 | 目标规模 | 用途 |
|------|----------|------|
| **核心能力**（脑暴 + 总结） | ~200 | 产品主能力回归 |
| **保底通用**（指令遵循） | ~200 | 防「只会脑暴」 |
| **中文保护** | ~100 | 中文退化哨兵 |

**本报告实际使用：**

| 项 | 值 |
|----|-----|
| **Manifest 版本** | `layer2-v0` |
| **Manifest 路径** | `data/eval/layer2/manifest_v0.jsonl`（元数据：`data/eval/layer2/manifest_meta.json`） |
| **总条数** | **500**（已达 shaping 目标规模；子层为 **v0 代理数据源**，升级 X-AlpacaEval / CMT-Eval 时须 bump 版本并重跑基线，见 [_docs/eval/layer2/README.md](../eval/layer2/README.md)） |
| **抽样/筛选规则** | `scripts/build_layer2_manifest.py`：brainstorm 中文多轮抽 200（seed 42）；`general_mixed` 中 `lang=en` 抽 200（seed 43）；`lang=zh` 抽 100（seed 44）。代理数据源说明见 `manifest_meta.json` 的 `proxy_notes` 与 [_docs/eval/layer2/README.md](../eval/layer2/README.md) |

---

## 4. 推理与评估协议（必须固定，便于复跑）

**原则**：此后 PoC / Stage1 的对比实验应 **仅改模型权重与训练相关变量**，本节字段若无 **协议版本 bump**（如 `eval-protocol-v0` → `v1`）不得静默改动。

**本报告冻结：`eval-protocol-v0`（建议写入实验 `META.json`）**

---

### 4.0 被测模型（Gemma 基座）— 生成参数（Best practice）

目标：**回归可比、可复现**；与常见公开基准习惯一致（评测侧尽量降低随机性）。

| 项 | 推荐值 | 说明 |
|----|--------|------|
| **解码** | **贪心** | `do_sample=false`（或等价：`temperature=0` 且关闭采样） |
| **`temperature`** | **0** | 基线 / 回归主跑固定为 0；若个别题需轻微多样性，仅限探索实验另开协议版本 |
| **`top_p`** | **1.0**（或不传） | 与贪心一致；若未来改用 `temperature>0`，可改为 `0.9` |
| **`max_new_tokens`** | **2048** | 覆盖 Layer2 多数多轮与脑暴长度；若截断率偏高可升到 **4096**（须同一 bump 内全员一致） |
| **`repetition_penalty`** | **1.0**（默认） | 除非 Gemma 官方推荐评测用微调，否则不改 |
| **`stop` 序列** | **无** | 由 `eos_token` 自然结束；勿加易误截的自定义 stop |
| **单轮 / 多轮** | **与 manifest 一致** | manifest 为几轮 `messages` 即原样送入 chat 模板；**勿**在评测时额外加「请用中文回答」等与题面冲突的系统指令 |
| **系统提示（system）** | **无** 或 **极简** | 推荐 **空 system**；若 Gemma-IT 模板强制占位，使用固定一句英文助手设定（写入 manifest 侧同源，勿每题变） |
| **批大小** | **1**（基线首跑） | 先保证正确性与 OOM 安全；提速时提高 batch 须在报告中记录且不改解码参数 |
| **随机种子** | **`42`** | 在 `temperature=0` 下影响有限，仍记录 `torch` / `numpy` / `random` 种子与 `transformers` 版本 |

**不推荐**：基线主跑使用 `temperature≥0.7`、或每题更换 system prompt——会显著增加方差，削弱「是否退化」的判断力。

---

### 4.1 评委模型 — `qwen3.6-plus`（LLM-as-a-Judge）

你已选定 **Qwen3.6-Plus** 作为评委；与 DashScope **OpenAI 兼容**接口的常见写法如下（**以控制台实际可用模型名为准**）。

| 项 | 推荐值 | 说明 |
|----|--------|------|
| **模型名 `model`** | **`qwen3.6-plus`** | 与 Qwen Cloud / 兼容接口文档一致；若调用失败请在控制台核对列表后更新本行 |
| **Base URL** | 与数据侧一致：国内常用 `https://dashscope.aliyuncs.com/compatible-mode/v1`；国际站见官方 `dashscope-intl` 文档 | 与 [data_pipeline](../../data_pipeline/README.md) 中 `DASHSCOPE_OPENAI_BASE_URL` 对齐即可 |
| **`temperature`** | **0.2** | 评委略低随机性、保留极小方差；若需更强可重复性可改为 **0** |
| **`max_tokens`（评委输出）** | **2048** | 需容纳多维度 1–5 分 + 短理由 + 可选 JSON；若结构化输出很长可 **4096** |
| **`top_p`** | **0.9** | 与 `temperature=0.2` 的常见组合；若 `temperature=0` 则 `top_p=1` |
| **评分维度** | 与 [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.2.1 对齐 | 相关性、连贯性、有用性、创造性；中文子层加 **中文质量** |
| **输出格式** | **优先 JSON** | 要求评委只输出 `{"relevance":1-5,...,"rationale_zh":"..."}` 等固定键，便于解析与审计 |
| **每题调用** | **1 次评委** | 不默认做 self-consistency 多数票（成本高）；若争议题再人工仲裁 |
| **聚合** | 子层内 **均值 ± 标准差** | 与 shaping「分层报告、不追求单一总分」一致 |
| **记录** | 每次跑批记录 **日期、模型名、API 区域** | **勿**在报告正文贴 API Key |

---

### 4.2 若不使用自动评委

**不适用**（本基线采用 §4.1 `qwen3.6-plus` 评委）。若未来改为纯人工抽检，须新起 `eval-protocol-v*` 并全文替换 §4。

---

### 4.3 协议变更规则

| 变更类型 | 是否必须 bump `eval-protocol` 版本 |
|----------|--------------------------------------|
| 修改 Gemma `temperature` / `max_new_tokens` / system 模板 | **是** |
| 更换评委模型或评委温度 / JSON 键设计 | **是** |
| 仅修复 manifest 中个别错字、不改题意与题序 | 否（manifest 自增版本即可） |

---

## 5. 结果：按子层汇总（核心 / 通用 / 中文）

**（填入数字或「见附件 CSV」）**

### 5.1 核心能力（~200）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| 相关性 | | | |
| 连贯性 | | | |
| 有用性 | | | |
| 创造性 | | | |

### 5.2 保底通用（~200）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| （同上或简化） | | | |

### 5.3 中文保护（~100）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| 中文质量 | | | |
| … | | | |

### 5.4 失败样例（Should）

- 链接或路径：`________________`（可选；Sprint 建议至少列 5～10 条 `item_id` + 简短原因）

---

## 6. 红线结论（P0 / P1 / P2）

定义见 [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.3。

| 级别 | 是否触发 | 证据（样本 id / 统计） | 处置 |
|------|----------|------------------------|------|
| **P0** 安全 | ☐ 否 ☐ 是 | | |
| **P1** 功能 | ☐ 否 ☐ 是 | | 若触发须按 shaping 停试与回退 |
| **P2** 体验 | ☐ 否 ☐ 是（预警） | | |

**说明**：基线阶段通常 **不应** 出现 P0；若 P1 在基线即触发，须在摘要中强调并调整数据或评测集再训。

---

## 7. 产物与环境（可复现）

| 项 | 路径或内容 |
|----|------------|
| **原始模型输出**（逐条 JSONL/JSON） | `________________` |
| **评委原始输出**（若有） | `________________` |
| **汇总表 CSV/JSON** | `________________` |
| **本报告 Git 提交** | `________________`（填写时 `git rev-parse HEAD`） |
| **操作系统** | |
| **Python** | |
| **PyTorch / CUDA** | |
| **关键包版本** | `transformers==___`, `accelerate==___`, … |

---

## 8. 局限与后续

- **Layer 2 若未满 500**：说明原因与计划补全时间。
- **基座与最终 Gemma-4-E2B 命名不一致**：说明过渡策略及何时重跑基线。
- **与 Week2 对齐**：PoC 完成后，在 **同一 manifest 版本 + 同一 §4 协议** 下生成 `s1-poc-e01-eval` 对比表。

---

## 9. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-12 | 初版骨架：对齐 Week1 计划与 shaping Layer2 / 红线章节 |
| 2026-05-12 | §4 冻结 `eval-protocol-v0`：Gemma 贪心 + `max_new_tokens=2048`；评委 `qwen3.6-plus` 与 JSON 输出建议 |
| 2026-05-12 | §2：锁定被测模型为 `google/gemma-4-E2B-it`（HF 链接 + 加载方式说明；与模型卡通用采样区分） |
