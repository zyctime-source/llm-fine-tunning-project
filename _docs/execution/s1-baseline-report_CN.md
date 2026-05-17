# Sprint 1 基线评测报告

| 属性 | 值 |
|------|-----|
| **报告 ID** | `s1-baseline-report` |
| **文档状态** | **已定稿（数值已填，2026-05-17）** — 与 `baseline-gemma4e2b-it-layer2-v0` 全量 500 条推理 + `qwen3.6-plus` 评委一致 |
| **对应实验 ID（建议）** | `baseline-gemma4e2b-it-layer2-v0`（元数据目录：[experiment/baseline-gemma4e2b-it-layer2-v0](../experiment/baseline-gemma4e2b-it-layer2-v0/)） |
| **数据配方** | [s1-data-v1.0-spec_CN.md](s1-data-v1.0-spec_CN.md)（当前可为 `v1.0-skip-seed`） |
| **评估分层依据** | [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.1.3（Layer 2 回归验证集） |
| **评测协议** | `eval-protocol-v0`（见 **§4**；Gemma 贪心 + 评委 `qwen3.6-plus`） |

## 0. 文档状态与待办

| 步骤 | 状态 | 说明 |
|------|------|------|
| Layer 2 题单 manifest（~500 条，含子层标签） | ☑ 已完成（`layer2-v0`） | 产物：`data/eval/layer2/manifest_v0.jsonl` + `manifest_meta.json`；说明见 [_docs/eval/layer2/README.md](../eval/layer2/README.md) |
| 推理协议（模板、温度、max tokens、系统提示） | ☑ 已冻结 | **§4 `eval-protocol-v0`**（2026-05-12）；变更须 bump 版本，见 §4.3 |
| 基座可加载冒烟 | ☑ 已通过（小样本） | `layer2_smoke_infer` 3 条、`max_new_tokens=128`；路径见 [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) → `results.smoke_infer_*` |
| 跑满 Layer 2 全量推理 +（可选）评委打分 | ☑ 已完成 | 原始输出：`experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl`（见 `META.json` → `results.layer2_infer_jsonl`）；评委：`layer2_judge_scores.jsonl`；汇总：`layer2_judge_summary.json` |
| 分层汇总表 + 红线结论 | ☑ 已填入 | **§5–§6**（均值来自 `layer2_judge_summary.json`；标准差未在汇总脚本中计算，标为「—」） |
| 更新本报告状态为「已定稿」 | ☑ 已完成 | 与 `META.json` `status=completed` 对齐 |

---

## 1. 摘要（Executive summary）

- **基座模型**：**[google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it)**；Hub **`revision`** 已冻结为 **`b324173c7d5721c2baba7f3b17b3b9b3d34ab1e9`**（见 §2 与实验 [META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json)）。
- **评估集**：Layer 2 回归集 **500** 条（`layer2-v0`）；子层 **core 200** / **general 200** / **zh_guard 100**。
- **解码与长度**：`eval-protocol-v0` — 贪心解码，`max_new_tokens=2048`（见 §4.0）。
- **评委**：`qwen3.6-plus`（DashScope OpenAI 兼容接口，`temperature=0.2`）；**500 / 500** 条解析成功（`judge_parse_ok=true`），逐条见 `layer2_judge_scores.jsonl`。
- **分层 `overall` 均值（1–100）**：**core 93.35**；**general 81.85**；**zh_guard 77.94**；全体有效样本 **85.67**。明细与各维度均值/中位数见 `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json`。
- **结论一句话**：核心脑暴子层表现强；通用指令块与中文保护子层明显低于 core，**未触发 P0/P1 举证红线**，中文场景列为 **P2 体验预警**（见 §6）。
- **对 Week 2 PoC 的含义**：后续微调对比须固定 **同一 manifest 版本**、**同一 §4 协议**、同一评委配置，在 §5 子层表上对照 **overall 与各维度** 变化，尤其关注 **zh_guard** 是否改善。

---

## 2. 被测模型（Model）

| 项 | 值 |
|----|-----|
| **显示名** | Gemma 4 E2B IT（指令微调；Sprint 与 shaping 称 **Gemma-4-E2B-IT**） |
| **Hub 页面** | [https://huggingface.co/google/gemma-4-E2B-it](https://huggingface.co/google/gemma-4-E2B-it) |
| **Hub `repo_id`** | `google/gemma-4-E2B-it` |
| **`revision` / `commit`** | **`b324173c7d5721c2baba7f3b17b3b9b3d34ab1e9`**（与本地 HF `snapshots/<revision>` 及 [experiment/baseline-gemma4e2b-it-layer2-v0/META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) 一致） |
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
| **`max_tokens`（评委输出）** | **2048** | 需容纳多维度 **1–100** 整数分 + `rationale_zh` + JSON；若结构化输出很长可 **4096** |
| **`top_p`** | **0.9** | 与 `temperature=0.2` 的常见组合；若 `temperature=0` 则 `top_p=1` |
| **评分维度** | 与 `scripts/layer2_judge_scores.py` 及本仓库 Sprint 备忘一致 | **relevance / coherence / helpfulness / creativity / clarity / task_alignment / depth / chinese_quality**（各 1–100）+ **overall**（1–100）+ **`rationale_zh`**（中文一句） |
| **输出格式** | **优先 JSON** | 要求评委只输出 `{"relevance":1-100,...,"overall":1-100,"rationale_zh":"..."}` 等固定键，便于解析与审计 |
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

下列 **均值** 来自 **`layer2_judge_summary.json`**（`scripts/aggregate_layer2_judge_scores.py` 对 `judge_parse_ok=true` 的样本统计）。**标准差**列当前未在汇总脚本中计算，标为 **—**；若需 σ，可在该脚本上扩展或从 `layer2_judge_scores.jsonl` 离线计算。

### 5.1 核心能力（~200）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| 相关性（relevance） | 95.60 | — | n=200 |
| 连贯性（coherence） | 95.26 | — | |
| 有用性（helpfulness） | 93.22 | — | |
| 创造性（creativity） | 87.08 | — | |
| **overall** | **93.35** | — | 综合 1–100 |

### 5.2 保底通用（~200）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| 相关性（relevance） | 94.50 | — | n=200；该子层大量英文指令，`chinese_quality` 评委侧多为 **100**（不适用） |
| 连贯性（coherence） | 83.26 | — | |
| 有用性（helpfulness） | 81.91 | — | |
| 创造性（creativity） | 74.12 | — | |
| **overall** | **81.85** | — | |

### 5.3 中文保护（~100）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| 中文质量（chinese_quality） | 92.86 | — | n=100 |
| 相关性（relevance） | 88.00 | — | |
| 连贯性（coherence） | 79.10 | — | |
| **overall** | **77.94** | — | 显著低于 core，见 §6 P2 |

### 5.4 失败样例（Should）

- 本次评委 **500 / 500** 解析成功；若后续出现 `judge_parse_ok=false`，在 `layer2_judge_scores.jsonl` 中按 `judge_error` / `judge_raw_preview` 排查后重跑或人工仲裁。可选：从低分 `layer2_id` 中抽 5～10 条写入失败清单。

---

## 6. 红线结论（P0 / P1 / P2）

定义见 [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.3。

| 级别 | 是否触发 | 证据（样本 id / 统计） | 处置 |
|------|----------|------------------------|------|
| **P0** 安全 | ☑ 否 | 本基线未做独立安全红队集；Layer 2 为代理回归集 | 若后续专项检出再更新 |
| **P1** 功能 | ☑ 否 | 未观察到「大面积不可用」或协议级失败；评委解析失败 **0** | 若触发须按 shaping 停试与回退 |
| **P2** 体验 | ☑ 是（预警） | **zh_guard** `overall` 均值 **77.94**，低于 **core 93.35** 与全体均值 **85.67**（见 §5.3） | PoC 与数据配方中优先监控中文场景；可与 Qwen 备选评估对照（见 shaping） |

**说明**：基线阶段 **P0 不应触发**；当前结论为 **可进入 Week 2 PoC**，但须把 **中文保护子层** 纳入迭代验收指标。

---

## 7. 产物与环境（可复现）

| 项 | 路径或内容 |
|----|------------|
| **原始模型输出**（逐条 JSONL） | `experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl`（见 [META.json](../../experiment/baseline-gemma4e2b-it-layer2-v0/META.json) `results.layer2_infer_jsonl`） |
| **评委原始输出** | `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl`（`results.metrics_path`） |
| **汇总表 JSON** | `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json`（`results.judge_summary_json`） |
| **本报告 Git 提交** | `115d983975664b42cb9b09dd9b5102fca08d4eaa`（定稿时 `git rev-parse HEAD`；重放以你克隆为准） |
| **操作系统** | （评测机本地填写） |
| **Python** | （评测机本地填写） |
| **PyTorch / CUDA** | （评测机本地填写） |
| **关键包版本** | `transformers==___`, `accelerate==___`, …（评测机本地填写） |

---

## 8. 局限与后续

- **Layer 2 已满 500 条**：本基线已完成；manifest 升级（如换 X-AlpacaEval / CMT-Eval 代理源）须 bump 版本并重跑。
- **基座与最终 Gemma-4-E2B 命名不一致**：说明过渡策略及何时重跑基线。
- **与 Week2 对齐**：PoC 完成后，在 **同一 manifest 版本 + 同一 §4 协议** 下生成 `s1-poc-e01-eval` 对比表。

---

## 9. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-12 | 初版骨架：对齐 Week1 计划与 shaping Layer2 / 红线章节 |
| 2026-05-12 | §4 冻结 `eval-protocol-v0`：Gemma 贪心 + `max_new_tokens=2048`；评委 `qwen3.6-plus` 与 JSON 输出建议 |
| 2026-05-17 | **定稿**：全量 500 推理 + `qwen3.6-plus` 评委；§0/§1/§5/§6/§7 填入；§4.1 与实现统一为 **1–100** 评分；`revision` 与 `META.json` 对齐 |
