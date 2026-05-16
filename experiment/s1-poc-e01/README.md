# s1-poc-e01：PoC 快速闭环实验

## 实验概述

| 属性 | 值 |
|------|-----|
| **实验 ID** | s1-poc-e01 |
| **阶段** | PoC（概念验证） |
| **父实验** | baseline-gemma4e2b-it-layer2-v0（基线评测） |
| **目标** | 验证「数据 + 训练 + 评估」链路可跑通 |
| **创建日期** | 2026-05-17 |
| **状态** | draft（准备中） |

## 实验假设

1. 使用 1k 条小数据（400 en + 400 cn + 200 general）可快速验证训练链路
2. 保守 LoRA 配置（rank=8, lr=2e-4, epoch=1）能产出可加载的 LoRA 权重
3. 微调后的模型在 Layer 2 上能产出可评估结果，不退化到不可用的程度

## 配置详情

### 基座模型
- **模型**: google/gemma-4-2b-it
- **精度**: bfloat16

### LoRA 配置
- **方法**: LoRA
- **Rank**: 8
- **Alpha**: 16
- **目标模块**: q_proj, v_proj, k_proj, o_proj
- **学习率**: 2e-4
- **Epochs**: 1
- **Batch Size**: 1
- **Gradient Accumulation**: 4 steps
- **Warmup Steps**: 50
- **种子**: 42

### 数据配置
- **配方**: v1.0-poc
- **路径**: `data/poc_v1.0_1k.jsonl`
- **配比**:
  - brainstorm_en: 400 条
  - brainstorm_cn: 400 条
  - general: 200 条
  - **合计**: 1000 条

### 评估配置
- **评测集**: Layer 2（500 条）
- **评测协议**: eval-protocol-v0
- **评委模型**: qwen3.6-plus
- **基线分数**: baseline-gemma4e2b-it-layer2-v0
  - overall: 85.67
  - core: 93.35
  - general: 81.85
  - zh_guard: 77.94

## 实验步骤

### Day 1：准备（已完成 ✓）
- [x] 准备 PoC 数据子集（1k 条）
- [x] 创建实验目录和 META.json
- [x] 创建训练脚本和依赖配置
- [x] 编写 AutoDL 环境设置文档
- [ ] 安装/验证训练环境（在 AutoDL 上执行）

### Day 2：训练（已完成 ✓）
- [x] 执行 PoC 训练
- [x] 监控 loss 曲线（最终 loss: 1.9343）
- [x] 保存 LoRA 权重
- [x] 训练时间: 385.28 秒 (~6.4 分钟) @ AutoDL RTX 5090

### Day 3：验证（进行中）
- [ ] 下载 LoRA 权重到本地
- [ ] 验证 LoRA 权重可加载
- [ ] 跑 Layer 2 冒烟测试（前 10 条）

### Day 4：评估
- [ ] 执行 Layer 2 全量推理（500 条）
- [ ] 评委打分
- [ ] 结果汇总

### Day 5：决策
- [ ] 对比基线分数
- [ ] 做出 Accept/Iterate/Reject 决策
- [ ] 撰写复盘

## 待办清单

### 训练前检查（在 AutoDL 上执行）
- [ ] SSH 登录 AutoDL 实例
- [ ] 上传代码到 `/root/autodl-tmp/`
- [ ] 运行启动脚本: `bash scripts/train_poc_autodl.sh`
- [ ] 验证 GPU 可用: `nvidia-smi`
- [ ] 验证依赖安装: `python -c "import torch; print(torch.cuda.is_available())"`

### 训练执行（已完成）
- [x] 准备训练脚本或命令
- [x] 启动训练，记录日志
- [x] 监控显存占用
- [x] 保存最终 LoRA 权重

### 评估执行（计划中）
- [ ] 使用微调后模型跑 Layer 2 推理（D4 执行）
- [ ] 执行评委打分（D4 执行）
- [ ] 生成分层统计报告（D4 执行）

## 预期结果

### 成功标准（Accept）
- 训练成功完成，无崩溃/NaN/OOM
- LoRA 权重可加载、可推理
- Layer 2 评估可跑通，解析成功率 > 95%
- core 层不退化（相对基线波动 < 10%）

### 需要迭代（Iterate）
- loss 曲线异常但训练完成
- 某子层退化 > 15%
- zh_guard 退化 > 20%

### 拒绝（Reject）
- 训练反复失败
- 权重无法加载
- 全面退化（core 层下降 > 30%）

## 产物清单

| 产物 | 路径 | 状态 |
|------|------|------|
| 训练数据 | `data/poc_v1.0_1k.jsonl` | ✅ 已准备 |
| 元数据 | `data/poc_v1.0_1k_meta.json` | ✅ 已准备 |
| LoRA 配置 | `adapter_config.json` | ✅ 已生成 (AutoDL) |
| LoRA 权重 | `adapter_model.safetensors` | ✅ 已生成 (AutoDL) |
| 训练日志 | `training.log` | ✅ 已生成 (AutoDL) |
| 评估结果 | `results/` | ⏳ D4 执行 |

## 参考文档

- [Week 2 详细规划](../../_docs/sprints/Sprint1-05_week2_poc_plan_CN.md)
- [AutoDL 环境设置指南](../../_docs/sprints/Sprint1-06_autodl_setup_CN.md)
- [Sprint 1 训练主线](../../_docs/execution/sprint-1-train.md)
- [基线评测报告](../../_docs/execution/s1-baseline-report_CN.md)
- [数据配方规格](../../_docs/execution/s1-data-v1.0-spec_CN.md)
- [训练依赖列表](../../requirements-train.txt)
- [训练脚本](../../scripts/train_poc.py)
- [AutoDL 启动脚本](../../scripts/train_poc_autodl.sh)

## 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-17 | 初始化：准备数据子集，创建实验目录 |
| 2026-05-17 | 添加训练脚本、依赖配置、AutoDL 指南 |
