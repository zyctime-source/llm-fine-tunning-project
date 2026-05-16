# 微调端侧大模型 App 开发记录：2026-05-15，基线模型（Gemma）选型、下载与打分

> **类型**：个人项目技术备忘  
> **日期**：2026-05-15  
> **GitHub repo**：https://github.com/zyctime-source/llm-fine-tunning-project  

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

### 6.3 跑完后：回填、评委打分与报告

全量（或分批）推理结束后，典型产物为 **`experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_<UTC>.jsonl`**（若未传 `--out` 则带时间戳；你当前示例为 `smoke_infer_20260514T1009Z.jsonl`）。之后需要三件事：**写入元数据**、**对每条模型回答跑评委**、**把汇总与红线写回基线报告**。

#### 6.3.1 推理产物与 `META.json`

1. 将**全量推理 JSONL** 的相对路径写入 **`META.json`** → `results`（例如扩展 `results.layer2_infer_jsonl` 或团队约定字段），并在 [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) **§7** 填写「原始模型输出」路径。  
2. 叙事与命令速查见 [experiment/baseline-gemma4e2b-it-layer2-v0/README.md](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md)。

下面是推理的输出例子：

```json
{"layer2_id": "L2-core-00001", "stratum": "core", "prompt_message_count": 9, "max_new_tokens": 2048, "completion_preview": "非常棒！明确的规则能为开放的沟通设定一个安全和尊重的框架。\n\n为了让这个“家庭会议”真正有效，你觉得在**会议的组织和氛围营造**方面，还需要考虑哪些具体的小细节呢？比如，如何确保每个人都感到安全和被重视？", "timestamp": "2026-05-14T10:15:36.665142+00:00"}
```

#### 6.3.2 评委打分：具体在做什么

**目的**：在 **`eval-protocol-v0`** 下，用 **DashScope OpenAI 兼容接口** 调用 **`qwen3.6-plus`**（与 [s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) **§4.1** 一致），对 **每一条** Gemma 生成的 `completion_*` 打分，便于后续按 **core / general / zh_guard** 分层汇总、对照红线。

**脚本**：[scripts/layer2_judge_scores.py](../../scripts/layer2_judge_scores.py)  
**实验目录说明**：[experiment/baseline-gemma4e2b-it-layer2-v0/README.md](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md)「评委打分」一节。

**评分维度（共 8 项分项 + 1 项综合 + 1 条中文理由）**：评委必须返回**一个 JSON 对象**，且键集合与脚本校验一致。其中 **8 个分项键名**与 **`overall`** 均为 **整数 1–100**；**`rationale_zh`** 为**非空字符串**（一句中文简评）。分项含义与英文 prompt 中的定义对齐，下表为中文释义（便于写报告时引用）：

| JSON 键 | 中文含义（评委应如何理解） |
|-----------|---------------------------|
| `relevance` | 是否紧扣话题、未跑题 |
| `coherence` | 多轮衔接与前后一致性 |
| `helpfulness` | 可执行价值（追问、建议、小结等是否到位） |
| `creativity` | 有用的新角度 / 新意（**core** 层尤其看重） |
| `clarity` | 表达是否清楚、易读 |
| `task_alignment` | 是否落实用户**最后一轮**的意图 / 请求 |
| `depth` | **core**：追问或展开深度；**general**：执行层面的具体程度（与脚本英文说明一致） |
| `chinese_quality` | **每条必填**。若回复**几乎全英文**，填 **100**（表示本维度不适用、不扣分）；若含中文，则评自然度与得体性（1–100） |
| `overall` | 该轮 assistant 续写的**综合质量**（1–100，便于跨题可比） |
| `rationale_zh` | 用**一句中文**概括上述判断（非数值） |

**按 `stratum` 的侧重点**（写入评委 user prompt，用于引导打分风格，**不是**后验数学加权公式）：**core** 侧重脑暴与追问深度；**general** 侧重指令遵循与有用性；**zh_guard** 侧重中文对话质量。**注意**：三层都要填满上表全部数值键（含 `chinese_quality`），脚本不做「某层可省略某键」的例外。

**代码侧如何固定这些维度**：分项键名与 `overall` 的取值范围如下：

```py
# All dimension scores and overall use integer 1–100.
SCORE_MIN = 1
SCORE_MAX = 100
SCORE_DIMENSION_KEYS: tuple[str, ...] = (
    "relevance",
    "coherence",
    "helpfulness",
    "creativity",
    "clarity",
    "task_alignment",
    "depth",
    "chinese_quality",
)
SCORE_KEY_OVERALL = "overall"
```

解析出 JSON 后，脚本要求 **上述 8 键 + `overall` + `rationale_zh` 齐全**，且分数为 **1–100 的整数**（`rationale_zh` 为非空字符串）：

```py
def _validate_scores(obj: dict[str, Any], _stratum: str) -> tuple[bool, str]:
    need = set(SCORE_DIMENSION_KEYS) | {SCORE_KEY_OVERALL, "rationale_zh"}
    missing = need - set(obj.keys())
    if missing:
        return False, f"missing keys: {sorted(missing)}"
    for k in SCORE_DIMENSION_KEYS:
        if not _int_in_range(obj[k], SCORE_MIN, SCORE_MAX):
            return False, f"{k} must be integer {SCORE_MIN}-{SCORE_MAX}, got {obj[k]!r}"
    if not _int_in_range(obj[SCORE_KEY_OVERALL], SCORE_MIN, SCORE_MAX):
        return False, f"{SCORE_KEY_OVERALL} must be integer {SCORE_MIN}-{SCORE_MAX}, got {obj[SCORE_KEY_OVERALL]!r}"
    rz = obj["rationale_zh"]
    if not isinstance(rz, str) or not str(rz).strip():
        return False, "rationale_zh must be non-empty string"
    return True, ""
```

评委 **user** 侧完整模板（含对话占位、`stratum` 权重说明、各维度英文定义与 `chinese_quality` 特例）由 `_build_user_prompt` 生成：

```py
def _build_user_prompt(
    stratum: str,
    dialogue_text: str,
    model_response: str,
) -> str:
    return f"""You evaluate a single assistant turn in a multi-turn dialogue.

**Stratum**: {stratum}
Weight your judgment accordingly: **core** = brainstorming / follow-up depth; **general** = instruction following and usefulness; **zh_guard** = Chinese dialogue quality (all strata still fill every numeric field below).

**Conversation (up to the last user turn; the model reply is scored separately):**
---
{dialogue_text}
---

**Model-generated assistant continuation (to score):**
---
{model_response}
---

Return **only** one JSON object. Use **integer** scores:
- **1–100** for each of: relevance, coherence, helpfulness, creativity, clarity, task_alignment, depth, chinese_quality
- **1–100** for **overall** (holistic quality for this turn, comparable across items)

Field meanings (brief):
- **relevance**: stays on topic.
- **coherence**: multi-turn flow and consistency.
- **helpfulness**: actionable value (questions, suggestions, summaries as appropriate).
- **creativity**: useful novelty / angles (especially for core).
- **clarity**: clear, readable expression.
- **task_alignment**: fulfills the user’s last request / intent.
- **depth**: probing or elaboration depth (core); concreteness of execution (general).
- **chinese_quality**: **required for every item.** If the reply is almost entirely English, score **100** (not applicable / no penalty). If Chinese is present, score naturalness and adequacy (1–100).
- **overall**: single composite 1–100 reflecting how good this assistant turn is.
- **rationale_zh**: one short sentence in **Chinese** summarizing the judgment.

No markdown fences, no extra keys."""
```

**主流程代码片段**：创建客户端、带重试的评委调用；对每条样本拼 `user_prompt`、解析 JSON、校验后 **追加一行并 `flush`**。

```py
    client = OpenAI(api_key=api_key, base_url=args.base_url.strip(), timeout=args.timeout)

    system_msg = (
        "You are an impartial dialogue-quality evaluator. "
        "You must reply with a single JSON object only, no markdown fences."
    )

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=2, max=60), reraise=True)
    def _call_judge(user_content: str) -> str:
        resp = client.chat.completions.create(
            model=args.judge_model,
            temperature=args.temperature,
            top_p=0.9,
            max_tokens=args.max_tokens,
            messages=[
                {"role": "system", "content": system_msg},
                {"role": "user", "content": user_content},
            ],
        )
        choice = resp.choices[0].message
        return (choice.content or "").strip()
```

```py
            dialogue = _messages_to_dialogue_text(msgs_ctx)
            user_prompt = _build_user_prompt(stratum, dialogue, str(completion))

            raw = ""
            parsed: dict[str, Any] | None = None
            ok = False
            err = ""
            try:
                raw = _call_judge(user_prompt)
                parsed = _extract_json_object(raw)
                if parsed is None:
                    err = "no_json_object"
                else:
                    ok, err = _validate_scores(parsed, stratum)
            except Exception as e:
                err = f"{type(e).__name__}: {e}"

            out_obj: dict[str, Any] = {
                "layer2_id": lid,
                "stratum": stratum,
                "judge_model": args.judge_model,
                "judge_parse_ok": ok,
                "scores": parsed if ok else None,
                "judge_error": err if not ok else None,
                "judge_raw_preview": (raw[:4000] + ("..." if len(raw) > 4000 else "")) if raw else None,
            }
            fout.write(json.dumps(out_obj, ensure_ascii=False) + "\n")
            fout.flush()
```

**输入**：

| 输入 | 作用 |
|------|------|
| `--manifest` | `manifest_v0.jsonl`：取 `messages`、`stratum`，并与推理侧一致地**去掉末尾参考 assistant**，再拼进评委 prompt |
| `--infer-jsonl` | 上一步推理产物，例如 `.../smoke_infer_20260514T1009Z.jsonl`；按 `layer2_id` 取 `completion_text`（若无则用 `completion_preview`） |

**环境**：仓库根 `.env` 中配置 **`DASHSCOPE_API_KEY`**、`DASHSCOPE_OPENAI_BASE_URL`（与数据流水线翻译相同）；`pip install -r requirements-eval.txt`（含 `openai`、`tenacity`）。

**运行示例**（路径按你本机实际推理文件名替换）：

```bash
# 断点续跑：已写入 --out 的 layer2_id 会跳过；若要重评某条，先从输出文件中删除该行
python scripts/layer2_judge_scores.py \
  --manifest data/eval/layer2/manifest_v0.jsonl \
  --infer-jsonl experiment/baseline-gemma4e2b-it-layer2-v0/results/smoke_infer_20260514T1009Z.jsonl \
  --out experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl \
  --resume
```

上文已给出 **`_build_user_prompt` / `_call_judge` / 校验与落盘** 的源码引用；流程概览：逐条对齐 `layer2_id` → 拼对话与 Gemma 续写 → 评委返回单 JSON → `_extract_json_object` → `_validate_scores`。

**输出文件与格式**：默认 **`experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_scores.jsonl`**，**每行一条 JSON**（UTF-8），与推理脚本一样采用**追加 + flush**，便于中断后续跑。

| 顶层字段 | 含义 |
|----------|------|
| `layer2_id` | 与 manifest / 推理 JSONL 对齐 |
| `stratum` | `core` / `general` / `zh_guard` |
| `judge_model` | 如 `qwen3.6-plus` |
| `judge_parse_ok` | 是否成功解析并通过校验 |
| `scores` | 成功时：含 **8 个分项 + `overall` + `rationale_zh`**（含义见本节「评分维度」表） |
| `judge_error` | 失败时错误说明 |
| `judge_raw_preview` | 评委原始返回片段（便于排错） |

**`scores` 字段**：与上表及脚本 `SCORE_DIMENSION_KEYS` 一致；**`chinese_quality`** 与 **`overall`** 规则见上文维度表与 `_build_user_prompt` 英文说明。

**成功样例一行**（为便于阅读已换行；实际文件多为单行）：

```json
{
  "layer2_id": "L2-core-00001",
  "stratum": "core",
  "judge_model": "qwen3.6-plus",
  "judge_parse_ok": true,
  "scores": {
    "relevance": 95,
    "coherence": 95,
    "helpfulness": 90,
    "creativity": 85,
    "clarity": 95,
    "task_alignment": 95,
    "depth": 90,
    "chinese_quality": 95,
    "overall": 92,
    "rationale_zh": "回复承接上文并引导后续思考，贴合脑暴场景。"
  },
  "judge_error": null,
  "judge_raw_preview": "{...评委原始 JSON 文本节选...}"
}
```

将 **`layer2_judge_scores.jsonl`** 路径记入 **`META.json`**（如 `results.metrics_path` 或团队约定字段），并在 **s1-baseline-report §7** 与 **§5–§6** 分层汇总、红线结论中引用（Sprint 备忘 **§7** 为定稿数值摘录，与报告对齐）。

#### 6.3.3 定稿与状态

- 分层汇总与红线结论填入 **s1-baseline-report §5–§6**（本备忘 **§7** 摘录关键表）。  
- 将 **`META.json` 的 `status`** 与报告状态同步为定稿流程（参见 [baseline README](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md)「待办」）。

---

## 7. 基线结果与红线（与 s1-baseline-report 同步）

> **权威叙事与表格全文**以 [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) **§5–§6** 为准；本节为 Sprint 备忘中的**定稿摘录**（数值来自 `experiment/baseline-gemma4e2b-it-layer2-v0/results/layer2_judge_summary.json`，`judge_parse_ok=true`）。

下列 **均值** 由 `scripts/aggregate_layer2_judge_scores.py` 汇总。**标准差**未在脚本中计算，标为 **—**。

### 7.1 按子层：评委维度均值（核心 / 通用 / 中文）

#### 核心能力（~200）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| 相关性（relevance） | 95.60 | — | n=200 |
| 连贯性（coherence） | 95.26 | — | |
| 有用性（helpfulness） | 93.22 | — | |
| 创造性（creativity） | 87.08 | — | |
| **overall** | **93.35** | — | 综合 1–100 |

#### 保底通用（~200）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| 相关性（relevance） | 94.50 | — | n=200；该子层大量英文指令，`chinese_quality` 评委侧多为 **100**（不适用） |
| 连贯性（coherence） | 83.26 | — | |
| 有用性（helpfulness） | 81.91 | — | |
| 创造性（creativity） | 74.12 | — | |
| **overall** | **81.85** | — | |

#### 中文保护（~100）

| 维度 | 均值 | 标准差 | 备注 |
|------|------|--------|------|
| 中文质量（chinese_quality） | 92.86 | — | n=100 |
| 相关性（relevance） | 88.00 | — | |
| 连贯性（coherence） | 79.10 | — | |
| **overall** | **77.94** | — | 显著低于 core，见下节 P2 |

#### 失败样例（Should）

- 本次评委 **500 / 500** 解析成功；若后续出现 `judge_parse_ok=false`，在 `layer2_judge_scores.jsonl` 中按 `judge_error` / `judge_raw_preview` 排查后重跑或人工仲裁。可选：从低分 `layer2_id` 中抽 5～10 条写入失败清单。

### 7.2 红线结论（P0 / P1 / P2）

定义见 [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.3。

| 级别 | 是否触发 | 证据（样本 id / 统计） | 处置 |
|------|----------|------------------------|------|
| **P0** 安全 | ☑ 否 | 本基线未做独立安全红队集；Layer 2 为代理回归集 | 若后续专项检出再更新 |
| **P1** 功能 | ☑ 否 | 未观察到「大面积不可用」或协议级失败；评委解析失败 **0** | 若触发须按 shaping 停试与回退 |
| **P2** 体验 | ☑ 是（预警） | **zh_guard** `overall` 均值 **77.94**，低于 **core 93.35** 与全体均值 **85.67**（见 §7.1 中文保护） | PoC 与数据配方中优先监控中文场景；可与 Qwen 备选评估对照（见 shaping） |

**说明**：当前结论为 **可进入 Week 2 PoC**，但须把 **中文保护子层** 纳入迭代验收指标。

---

## 8. 相关文档索引

| 文档 | 用途 |
|------|------|
| [_docs/shaping/6_model_strategy_CN.md](../shaping/6_model_strategy_CN.md) | 端侧候选模型、许可证、微调阶段概念 |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | 被测模型表、Layer 2 定义、`eval-protocol-v0`、评委与报告结构 |
| [experiment/baseline-gemma4e2b-it-layer2-v0/README.md](../../experiment/baseline-gemma4e2b-it-layer2-v0/README.md) | 本实验目录约定、安装与冒烟步骤、待办清单 |
| [experiment/README.md](../../experiment/README.md) | 评测 venv、HF 登录与镜像配置 |
| [scripts/layer2_judge_scores.py](../../scripts/layer2_judge_scores.py) | Layer 2 评委打分（DashScope + `qwen3.6-plus`，输出 `layer2_judge_scores.jsonl`） |
| [scripts/aggregate_layer2_judge_scores.py](../../scripts/aggregate_layer2_judge_scores.py) | 评委 JSONL 汇总为 `layer2_judge_summary.json`（分层 mean/median） |
| [Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) | manifest 生成、字段与分层含义 |
| [_docs/eval/layer2/README.md](../eval/layer2/README.md) | manifest 路径与代理数据源说明 |

---

## 9. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-14 | 初版：串联 shaping 选型、Hub 下载与 revision、`requirements-eval`、冒烟与全量 manifest 推理（含 `--resume` / `--out`） |
| 2026-05-14 | 语言优化：简化长句、统一术语、澄清命名关系、优化段落结构 |
| 2026-05-14 | §2.3 增加「2B 级候选：为何先跑通 Gemma（而不是 Qwen）」，解释选型逻辑与 PoC 阶段对比计划 |
| 2026-05-14 | §3.1 增加模型下载代码片段（Python `from_pretrained` 与 huggingface-cli 两种方式） |
| 2026-05-15 | §6.3 扩充：推理产物回填、`layer2_judge_scores.py` 评委流程、输出 JSONL 字段与示例 |
| 2026-05-16 | §6.3.2：分项维度中文表、`stratum` 说明、与仓库一致的代码引用；去重「脚本概念」片段 |
| 2026-05-17 | 500 条推理+评委+汇总完成（路径见 `META.json`）；**新增 §7**「基线结果与红线」摘录，与 `s1-baseline-report_CN.md` §5–§6 对齐；原 §7/§8 顺延为 §8/§9 |
