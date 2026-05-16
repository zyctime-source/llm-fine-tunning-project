# Sprint 1 Week 2 规划：PoC 快速闭环

> **类型**：个人项目技术备忘  
> **日期**：2026-05-17  
> **GitHub repo**：https://github.com/zyctime-source/llm-fine-tunning-project  
> **主线对照**：[_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) §「Week 2：PoC 快速闭环」  
> **总览索引**：[Sprint1-00_tasks_intro_CN.md](Sprint1-00_tasks_intro_CN.md) §4 Week 2

---

## 1. 背景与范围

### 1.1 为什么做 PoC？

Week 1 已完成数据冻结和基线评测，现在需要**用最短路径验证「数据 + 训练 + 评估」链路可跑通**。PoC（Proof of Concept）的目标不是产出完美模型，而是：

1. 验证训练脚本能正常跑通（不崩溃、不 OOM、loss 正常下降）
2. 验证 LoRA 权重可导出、可加载、可推理
3. 验证微调后的模型能在 Layer 2 上产出可评估的结果
4. 为 Week 3 Stage 1 保守训练积累配置经验

### 1.2 本文范围

**核心任务**：
- PoC 训练（小数据量、短轮数、快速验证）
- LoRA 权重导出与加载验证
- PoC 后 Layer 2 回归评估
- Accept/Iterate/Reject 决策

**不做**：
- 不使用完整 13k 数据（那是 Stage 1 的任务）
- 不追求最优性能（那是迭代目标）
- 不做 Stage 2 个性化

---

## 2. 本周目标（一句话）

**用 1k 条数据完成一次端到端 LoRA 微调，产出可加载的 LoRA 权重，并通过 Layer 2 快速评估验证训练链路可用。**

---

## 3. 时间预算（20h）

假定 **5 个工作日 × 4h**；若你一周只有 3 个学习日，可将「第 4–5 天」合并为两个 8h 块。

| 天 | 时长 | 焦点 | 关键产出 |
|----|------|------|----------|
| D1 | 4h | 准备 PoC 数据子集（1k 条）、搭建训练环境、确认训练脚本 | `data/poc_v1.0_1k.jsonl` |
| D2 | 4h | 执行 PoC 训练（1-3 epoch）、监控 loss 曲线、处理异常 | `s1-poc-e01/` 目录、训练日志 |
| D3 | 4h | 导出 LoRA 权重、验证可加载、跑 Layer 2 冒烟测试 | `adapter_model.safetensors`、冒烟结果 |
| D4 | 4h | 执行完整 Layer 2 评估（500 条）、评委打分 | `s1-poc-e01-eval.jsonl`、评委结果 |
| D5 | 4h | 对比基线分数、做出 Accept/Iterate/Reject 决策、撰写周复盘 | 决策结论、Week 3 输入清单 |

---

## 4. 任务清单

### 4.1 准备阶段（D1）

| 任务 | 说明 | 检查点 |
|------|------|--------|
| **准备 PoC 数据子集** | 从 `v1.0` 完整数据中抽取 1k 条，保持配比（brainstorm_en: 400, brainstorm_cn: 400, general: 200） | 数据文件可加载、格式正确 |
| **确认训练环境** | 安装/验证训练依赖（TRL、Transformers、PEFT 等） | `import trl` 无报错 |
| **创建实验目录** | 复制模板，建立 `experiment/s1-poc-e01/` | META.json 已初始化 |
| **确定训练配置** | 保守配置：LoRA rank=8, alpha=16, lr=2e-4, epochs=1-3, batch_size=1/2 | 配置写入 META.json |

**PoC 数据配比建议**：

| 子集 | 条数 | 来源 |
|------|------|------|
| brainstorm_en | 400 | `brainstorm_vicuna_10k` 抽样 |
| brainstorm_cn | 400 | 中文翻译子集抽样 |
| general | 200 | 通用能力数据抽样 |
| **合计** | **1000** | — |

### 4.2 训练阶段（D2）

| 任务 | 说明 | 检查点 |
|------|------|--------|
| **启动训练** | 运行 TRL SFTTrainer，固定 seed=42 | 训练正常启动 |
| **监控指标** | loss 曲线、学习率变化、显存占用 | loss 平稳下降，无 NaN |
| **异常处理** | OOM 时减小 batch_size，发散时降低 lr | 记录调整过程 |
| **保存 checkpoint** | 每 epoch 保存，最终保存 LoRA 权重 | 权重文件存在且可读 |

**关键配置参考**（保守策略）：

```json
{
  "method": "LoRA",
  "rank": 8,
  "lora_alpha": 16,
  "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
  "learning_rate": 2e-4,
  "epochs": 1,
  "batch_size": 1,
  "gradient_accumulation_steps": 4,
  "warmup_steps": 50,
  "seed": 42
}
```

### 4.3 验证阶段（D3）

| 任务 | 说明 | 检查点 |
|------|------|--------|
| **LoRA 权重导出** | 使用 PEFT 保存 adapter | `adapter_model.safetensors` 存在 |
| **加载验证** | 基座 + LoRA 合并，验证可推理 | `model.generate()` 正常输出 |
| **冒烟测试** | Layer 2 前 10 条快速测试 | 输出格式正确、无乱码 |
| **META.json 更新** | 填入训练参数、状态改为 `training_completed` | 字段完整 |

### 4.4 评估阶段（D4）

| 任务 | 说明 | 检查点 |
|------|------|--------|
| **Layer 2 全量推理** | 500 条回归集，贪心解码 | 结果写入 `results/` |
| **评委打分** | 使用 `qwen3.6-plus` 评委模型 | 解析成功率 > 95% |
| **结果汇总** | 分层统计 overall 均值 | 与基线对比 |

**评估命令参考**（沿用 Week 1 协议）：

```shell
# 推理
python scripts/layer2_smoke_infer.py \
  --model-path experiment/s1-poc-e01/ \
  --out experiment/s1-poc-e01/results/poc_infer_xxx.jsonl

# 评委打分
python scripts/layer2_judge_scores.py \
  --manifest data/eval/layer2/manifest_v0.jsonl \
  --infer-jsonl experiment/s1-poc-e01/results/poc_infer_xxx.jsonl \
  --out experiment/s1-poc-e01/results/poc_judge_scores.jsonl
```

### 4.5 决策阶段（D5）

| 任务 | 说明 | 产出 |
|------|------|------|
| **分数对比** | PoC vs Week 1 基线 | 对比表格 |
| **红线检查** | 是否触发 P0/P1 | 结论 |
| **做出决策** | Accept / Iterate / Reject | 决策文档 |
| **更新 META.json** | 填入结果分数、决策、父实验 | `status=completed` |
| **Week 3 输入** | 列出 Stage 1 所需依赖 | 输入清单 |

---

## 5. 交付物

### 5.1 必做（Must）

| 交付物 | 位置 | 说明 |
|--------|------|------|
| `s1-poc-e01` 实验目录 | `experiment/s1-poc-e01/` | 含 README.md、META.json、LoRA 权重 |
| `s1-poc-e01-eval` 评估结果 | `experiment/s1-poc-e01/results/` | 推理结果 + 评委打分 |
| 决策文档 | `experiment/s1-poc-e01/README.md` §结论 | Accept/Iterate/Reject 及理由 |

### 5.2 建议（Should）

| 交付物 | 说明 |
|--------|------|
| 训练过程截图/记录 | loss 曲线、学习率变化 |
| 失败样本清单 | 训练异常、评估异常、低分样本 |
| zh_guard 专项观察 | 中文保护子层与基线对比 |

---

## 6. 决策出口（Accept / Iterate / Reject）

### 6.1 Accept（通过，进入 Week 3）

**条件**（同时满足）：
- 训练成功完成，LoRA 权重可加载
- Layer 2 推理可跑通，评委可打分
- 核心能力（core 子层）与基线相比不退化（波动 < 10%）
- 未触发 P0/P1 红线

**动作**：标记为 `accept`，更新 `META.json`，进入 Week 3 Stage 1 保守训练。

### 6.2 Iterate（需迭代，本周内再跑一轮）

**触发条件**（任一）：
- 训练完成但 loss 曲线异常（波动大、 plateau 过早）
- 评估结果某子层明显退化（下降 > 15%）
- zh_guard 显著下降（下降 > 20%）
- 发现配置问题（如学习率过高/过低）

**动作**：
- 记录问题根因
- 调整配置（如 lr、epoch、数据配比）
- 开新实验 `s1-poc-e02`，父实验指向 `s1-poc-e01`
- 本周内完成迭代

### 6.3 Reject（拒绝，触发重大调整）

**触发条件**（任一）：
- 训练反复失败（OOM、NaN、崩溃无法解决）
- LoRA 权重无法加载或推理
- 全面退化（core 层下降 > 30%）
- 数据配方存在根本问题

**动作**：
- 记录失败原因
- 评估是否需要：换基座模型（启动 Qwen 备选）、改数据配方、改训练框架
- 与 Week 1 基线报告对比，分析问题根源

---

## 7. 红线与风险

### 7.1 本周红线

| 红线 | 含义 | 触发后动作 |
|------|------|------------|
| P0 | 训练无法完成（崩溃/NaN/OOM 无法解决） | Reject，评估换模型或框架 |
| P1 | LoRA 权重无法加载或推理 | Reject，检查导出与加载代码 |
| P2 | core 层显著退化（> 20%）或 zh_guard 严重退化（> 30%） | Iterate，调整数据配比或训练配置 |

### 7.2 风险与止损

| 风险场景 | 触发条件 | 止损动作 |
|---------|---------|---------|
| **训练反复失败** | 同一配置失败 > 2 次 | 缩小变量（减 rank、减 batch、冻更多层） |
| **GPU 时间超预期** | 当周 GPU 小时 > 20h | 减 epoch 到 1，减数据到 500 条，优先保评估 |
| **评估波动过大** | 同一模型两次评估差异 > 15% | 增加复跑次数，检查解码参数是否一致 |
| **zh_guard 退化严重** | 中文保护题均值 < 60 | 立即启动中文数据配比调整实验 |

---

## 8. 与 Week 1 的衔接

### 8.1 Week 1 输入（已就绪）

| 输入 | 位置 | 用途 |
|------|------|------|
| 数据配方 `v1.0` | `_docs/execution/s1-data-v1.0-spec_CN.md` | 按配比抽样 1k 条 |
| 基线评测报告 | `_docs/execution/s1-baseline-report_CN.md` | 对比基准 |
| Layer 2 题单 | `data/eval/layer2/manifest_v0.jsonl` | 回归评估 |
| 实验元数据模板 | `experiment/_template/` | 创建 s1-poc-e01 |
| 基线分数 | `baseline-gemma4e2b-it-layer2-v0/META.json` | 对比依据 |

**基线分数回顾**（供对比）：

| 子层 | overall 均值 |
|------|--------------|
| core | 93.35 |
| general | 81.85 |
| zh_guard | 77.94 |
| **全体** | **85.67** |

### 8.2 Week 3 输出（预留输入）

| 输出 | 用途 |
|------|------|
| PoC 决策结论 | Stage 1 是否启动、配置建议 |
| 训练配置经验 | lr、epoch、batch 等最优起始值 |
| 数据配比建议 | 是否需要调整中英文比例 |
| 失败样本类型 | Stage 1 需重点观察的问题 |

---

## 9. 相关文档索引

| 文档 | 用途 |
|------|------|
| [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) | Sprint 1 四周主线 |
| [Sprint1-00_tasks_intro_CN.md](Sprint1-00_tasks_intro_CN.md) | Sprint 1 任务总览 |
| [Sprint1-04_week1_done_summary_CN.md](Sprint1-04_week1_done_summary_CN.md) | Week 1 结案报告（含基线分数） |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | 数据配方规格 |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | 评测协议与基线分数 |
| [_docs/shaping/8_train_iterate_CN.md](../shaping/8_train_iterate_CN.md) | 训练策略、实验命名、可复现性 |
| [experiment/README.md](../../experiment/README.md) | 实验目录约定、训练/评测环境 |
| [experiment/_template/](../../experiment/_template/) | META.json 模板 |

---

## 10. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-17 | 初版：Sprint 1 Week 2 PoC 规划（对齐 sprint-1-train.md Week 2） |
