---
name: Sprint1 Week2 PoC
overview: Sprint 1 第二周：PoC 快速闭环。用 1k 条数据完成端到端 LoRA 微调，产出可加载权重，通过 Layer 2 评估验证训练链路，输出 Accept/Iterate/Reject 决策。
todos:
  - id: poc-day1
    content: D1：准备 PoC 数据子集（1k 条）、搭建训练环境、创建实验目录 s1-poc-e01
    status: pending
  - id: poc-day2
    content: D2：执行 PoC 训练（1-3 epoch），监控 loss 曲线，保存 LoRA 权重
    status: pending
  - id: poc-day3
    content: D3：导出 LoRA 权重，验证可加载，跑 Layer 2 冒烟测试
    status: pending
  - id: poc-day4
    content: D4：执行完整 Layer 2 评估（500条），评委打分，结果汇总
    status: pending
  - id: poc-day5
    content: D5：对比基线分数，做出 Accept/Iterate/Reject 决策，撰写复盘
    status: pending
isProject: false
---

# Sprint 1 Week 2 执行计划（追踪版）

## 快速导航

- **详细规划文档**：[_docs/sprints/Sprint1-05_week2_poc_plan_CN.md](../_docs/sprints/Sprint1-05_week2_poc_plan_CN.md)
- **Week 1 结案报告**：[_docs/sprints/Sprint1-04_week1_done_summary_CN.md](../_docs/sprints/Sprint1-04_week1_done_summary_CN.md)
- **Sprint 1 总览**：[_docs/sprints/Sprint1-00_tasks_intro_CN.md](../_docs/sprints/Sprint1-00_tasks_intro_CN.md)

## 实验目录结构（预期）

```
experiment/s1-poc-e01/
├── README.md              # 实验叙事、结论、决策
├── META.json              # 结构化元数据（复制 _template/META.template.json）
├── adapter_config.json    # LoRA 配置（PEFT 自动生成）
├── adapter_model.safetensors  # LoRA 权重（PEFT 自动生成）
├── training/              # 训练过程文件
│   ├── trainer_state.json
│   └── ...
└── results/               # 评估结果
    ├── poc_infer_*.jsonl
    ├── poc_judge_scores.jsonl
    └── poc_judge_summary.json
```

## 关键决策点

| 决策 | 条件 | 下一步 |
|------|------|--------|
| **Accept** | 训练成功、权重可加载、core 层不退化、无 P0/P1 红线 | 进入 Week 3 Stage 1 保守训练 |
| **Iterate** | 训练完成但需调优（loss 异常、某层退化 > 15%、zh_guard 退化 > 20%） | 本周内开 s1-poc-e02 迭代 |
| **Reject** | 训练反复失败、权重无法加载、全面退化（core > 30%） | 评估换模型/改配方 |

## 基线对比参考

| 子层 | Week 1 基线 overall | PoC 目标 |
|------|---------------------|----------|
| core | 93.35 | 不退化（> 84）|
| general | 81.85 | 不退化（> 74）|
| zh_guard | 77.94 | 不退化（> 70）|

## 风险 checklist

- [ ] GPU 时间监控（建议单次训练 < 4h）
- [ ] 定期保存 checkpoint（防止训练中断丢失进度）
- [ ] 训练日志记录（loss、lr、显存占用）
- [ ] zh_guard 专项观察（中文退化风险）
