# Sprint 1（第1个月）训练主线打通

## 目标

- 完成 `Gemma-4-E2B` 的 PoC 与 Stage 1 基础微调闭环。
- 建立最小可复现、可评估、可回滚的训练流程。

## 时间与投入

- 周期：4 周
- 预计投入：约 80 小时（每周 20 小时）
- 预算建议：120-180 GPU 小时中的 40-70 小时优先分配到本 Sprint

## Must / Should / Won't

- Must
  - 冻结数据版本 `v1.0`，并形成数据说明与追溯信息。
  - 至少完成 1 次 PoC + 1 次 Stage 1 训练。
  - 跑通 Layer 2 回归评估，形成首份对比报告。
  - 固化实验命名规则与 lineage 记录实践。
- Should
  - 补齐中文保护题的小样本观察，提前识别中文退化风险。
  - 输出 1 份失败样本分析清单，减少下个 Sprint 重复踩坑。
- Won't
  - 不做 Stage 2 个性化微调。
  - 不做多模型并行主线（Qwen 仅作为风险备选，不并行推进）。

## 每周拆分

### Week 1：数据与基线准备

- 冻结 `v1.0` 数据配方（对齐 `shaping/7_data_CN.md`）。
- 产出实验元数据模板（实验 ID、父实验、数据版本、结果摘要）。（模板与基线实例草稿见 [experiment/README.md](../../experiment/README.md)。）
- 跑基座模型基线评估（Layer 2）。

交付物：

- `s1-data-v1.0-spec`（文档）— 已定稿：[_docs/execution/s1-data-v1.0-spec_CN.md](s1-data-v1.0-spec_CN.md)
- `s1-baseline-report`（报告）— **已定稿（数值已填）**：[_docs/execution/s1-baseline-report_CN.md](s1-baseline-report_CN.md)（与 `baseline-gemma4e2b-it-layer2-v0/META.json` 对齐，2026-05-17）
- 实验元数据模板 + 基线实例（草稿）：[experiment/README.md](../../experiment/README.md)（`_template/` 与 `baseline-gemma4e2b-it-layer2-v0/`）

### Week 2：PoC 快速闭环

- 完成 1 次 PoC 训练并产出可加载 LoRA。
- 执行 PoC 后回归评估，输出 Accept / Iterate / Reject 决策。

交付物：
- `s1-poc-e01`（实验记录）
- `s1-poc-e01-eval`（评估结果）

### Week 3：Stage 1 保守训练

- 在 PoC 结论基础上完成 1 次 Stage 1 保守训练。
- 同步记录失败样本与异常输入行为。

交付物：
- `s1-train-e01`（实验记录）
- `s1-train-e01-error-cases`（问题清单）

### Week 4：收敛与 Gate1 评审

- 完成 Stage 1 对比报告（基线 vs 微调后）。
- 固化 lineage 树状记录与回滚点。
- 评审是否通过 Gate1。

交付物：
- `s1-gate1-review`（评审报告）
- `s1-retro`（Sprint 复盘）

## Gate1 通过标准

- 训练可复现：同一配置可重复得到可接受结果。
- 评估可复跑：Layer 2 能稳定运行并输出结构化结果。
- 模型可加载推理：LoRA 权重可被端侧/测试推理链路加载。
- 核心能力达到“可用不退化”：不触发 P0/P1 红线。

## 风险与止损

- 中文质量显著退化：连续两轮中文保护题不可用，触发 Qwen 备选评估。
- 训练不稳定：当周重复失败超过 2 次，优先缩小变量并停掉可选项。
- 成本超预期：GPU 小时逼近当月上限时，仅保留 Must 任务。

## Sprint 结束复盘模板

- 目标达成：达成 / 部分达成 / 未达成
- 关键指标：核心能力、中文保护题、训练稳定性
- 主要阻塞与根因
- 下 Sprint 保留项 / 删除项 / 新增项（各不超过 5 条）
