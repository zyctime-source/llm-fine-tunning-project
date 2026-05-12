# 沟通小结 · 2026-05-12

完成训练与实验策略（Train / Iterate），评测与质量（Eval / QA），基础设施与运维（Infra / Ops）的shaping文档。

「三个月 Sprint 执行计划确认、计划落地到仓库、对话与小结归档」相关的讨论与产出。

---

## 1. 阶段定位

- 当日工作从 **约束对齐与计划确认**，推进到 **将已确认的三个月 Sprint 计划落地为可执行文档**（不修改计划文件本身）。
- 延续既有 shaping（第 3–10 章）作为文档基线；当日未要求改写 shaping 正文。

---

## 2. 用户输入的关键约束（已纳入计划与落地文档）

- **时间**：尽量每周约 20 小时。  
- **预算**：不确定；助手给出 2B LoRA 微调在 RTX 5090 32GB、约 2.88 元/小时租机下的粗算区间与总预算建议（训练 + 评测/API 分列）。  
- **三个月首要目标**：跑通端到端流程 + Android 端可用 Demo。  
- **模型主线**：`Gemma-4-E2B`；中文场景保留 `Qwen3.5-2B` 作为风险备选评估路径，不默认双线并行。  
- **并行节奏**：第 1 个月偏训练；第 2–3 个月训练与 Android 并行。  
- **质量策略**：先可用再优化；三个月内**不强制** Stage 2 个性化微调。  
- **计划形态**：每月一个 Sprint，可整体后延 1–2 个缓冲 Sprint；每个 Sprint 目标与交付物需清晰。

---

## 3. 计划与门禁（摘要）

- 三个月拆为 **Sprint 1（训练主线打通）→ Sprint 2（评测稳定 + Android 最小主链路）→ Sprint 3（Demo 收敛与验收）**。  
- **Gate1**：可复现、可评估、可加载推理；核心能力「可用不退化」；不触发 P0/P1 红线。  
- **Gate2**：Android 主链路在真机可跑通；评测不触发 P0/P1 红线。  
- **里程碑**：可稳定演示端到端；结果可复盘、可继续迭代。  
- **缓冲 Sprint**：BufferSprintA 侧重训练/数据/红线修复；BufferSprintB 侧重 Demo 稳定与中文补强；均禁止范围膨胀。

---

## 4. 当日落地文件（仓库）

| 路径 | 说明 |
|------|------|
| `execution/README_CN.md` | 三个月执行总览、顺序、每周固定动作 |
| `execution/sprint-1-train.md` | Sprint 1：PoC + Stage 1、Gate1、周拆分 |
| `execution/sprint-2-demo.md` | Sprint 2：评测稳定化 + Android 主链路、Gate2 |
| `execution/sprint-3-acceptance.md` | Sprint 3：验收、归档、里程碑标准 |
| `execution/buffer-sprint-policy.md` | 缓冲 Sprint 触发矩阵与执行规则 |

**说明**：按用户要求，**未编辑** `.cursor/plans/three-month_sprint_plan_f8c3b767.plan.md` 计划文件本体。

---

## 5. 计划内待办状态（当日会话结论）

以下四项在当次「落地执行」对话中均已处理为 **completed**：

- `sprint1-train`：Sprint 1 文档与范围落地。  
- `sprint2-demo`：Sprint 2 文档与范围落地。  
- `sprint3-acceptance`：Sprint 3 文档与范围落地。  
- `buffer-policy`：缓冲 Sprint 政策文档落地。

---

## 6. 日志与存档（本轮）

- `log/2026-05-12-complete_CN.md`：当日会话完整存档（轮次 + 附录）。  
- `log/2026-05-12-summary_CN.md`：本文件。  
- `log/2026-05-12-summary_EN.md`：当日英文小结。

---

## 7. 建议的下一步

1. 从 `execution/sprint-1-train.md` 的 **Week 1** 开始执行，并同步在 `log/` 写周记或短记。  
2. 核对 `shaping/7_data_CN.md` 中数据版本 `v1.0` 与 Sprint 1 冻结项是否一致，必要时在下一篇日志记录变更。  
3. Sprint 1 结束前安排 **Gate1** 评审，未通过则按 `execution/buffer-sprint-policy.md` 进入缓冲 Sprint。

---

*文档生成于项目 `log/` 目录，供个人学习与项目推进使用。*
