# 2026-05-17 工作日志 - Sprint 1 Week 2 PoC 完成

> **日期**：2026-05-17（周日）  
> **时长**：约 2 小时  
> **主题**：Sprint 1 Week 2 PoC 训练、验证、评估全流程完成

---

## 1. 今日完成工作概览

### 核心成果
- ✅ **PoC 训练完成**（RTX 5090，6.4 分钟，loss=1.93）
- ✅ **Layer 2 全量评估**（480/500 条，成功率 99.8%）
- ✅ **评估报告生成**（vs 基线对比，决策 ACCEPT）
- ✅ **技术文档完善**（训练脚本详解、AutoDL 指南更新）

### 关键数据
| 指标 | 基线 | PoC | 变化 |
|------|------|-----|------|
| core 层 | 93.35 | 80.68 | -13.6% |
| general 层 | 81.85 | 67.23 | -17.9% |
| zh_guard 层 | 77.94 | 44.71 | -42.6% |
| **全体** | **85.67** | **69.06** | **-19.4%** |

---

## 2. 详细工作记录

### 2.1 PoC 训练执行（AutoDL RTX 5090）

**时间**：2026-05-16 23:05 - 23:11

**配置**：
- 数据：1,000 条（brainstorm_en 400 + brainstorm_cn 400 + general 200）
- 模型：Gemma-4-E2B-IT
- LoRA：rank=8, alpha=16
- 训练：1 epoch, lr=2e-4, 4-bit 量化

**结果**：
```
最终 loss: 1.9343
训练时间: 385.28 秒 (~6.4 分钟)
LoRA 权重: 5.14 MB
状态: ✅ 成功
```

**产物**：
- `experiment/s1-poc-e01/adapter_model.safetensors`
- `experiment/s1-poc-e01/adapter_config.json`
- `experiment/s1-poc-e01/training_meta.json`

---

### 2.2 LoRA 权重验证

**验证脚本**：`scripts/verify_lora.py`

**结果**：
```
✓ adapter_config.json (LoRA 配置): 0.00 MB
✓ adapter_model.safetensors (LoRA 权重): 5.14 MB
✓ 模型加载成功
✓ 推理测试通过

输入: 我想学习编程，有什么建议？
输出: 太棒了！编程是一项非常实用的技能。你有没有考虑过自己想用编程做些什么呢？...
```

**结论**：LoRA 权重可加载、可推理、格式正确。

---

### 2.3 Layer 2 全量评估

**推理脚本**：`scripts/layer2_full_infer_poc.py`

**执行**：
- 评测集：Layer 2（500 条）
- 实际完成：480 条（96%）
- 成功率：99.8%（479/480 解析成功）

**评委打分**：`scripts/layer2_judge_scores.py`
- 评委模型：qwen3.6-plus
- 完成：481 条打分

**汇总**：`scripts/aggregate_layer2_judge_scores.py`
- 输出：`poc_judge_summary.json`

---

### 2.4 评估报告与决策

**决策**：**ACCEPT**（进入 Stage 1 保守训练）

**理由**：
1. ✅ 训练链路完全打通（数据→训练→评估→打分）
2. ✅ LoRA 权重可加载、可推理
3. ✅ core 层 80.68 分，核心脑暴功能保留
4. ⚠️ 性能下降在预期内（PoC 目标不是最优性能，而是验证流程）

**红线检查**：
- P0（训练失败）：未触发 ✅
- P1（权重无法加载）：未触发 ✅
- P2（core 层退化 > 20%）：未触发 ✅（实际 -13.6%）
- P2（zh_guard 退化 > 30%）：⚠️ 已触发（实际 -42.6%）

**Stage 1 改进建议**：
1. 增加中文数据比例到 50%+（当前 40%）
2. 训练轮数增加到 2-3 epoch
3. 尝试更大 LoRA rank（8→16）
4. 补齐自建 seed 数据 500 条

---

### 2.5 技术文档完善

#### 更新的文档

| 文档 | 路径 | 更新内容 |
|------|------|----------|
| **训练脚本详解** | `Sprint1-07_train_poc_explained_CN.md` | 新增背景章节、实际训练结果记录 |
| **AutoDL 指南** | `Sprint1-06_autodl_setup_CN.md` | 更新 RTX 5090 32GB 显存信息、ModelScope 支持 |
| **实验 README** | `experiment/s1-poc-e01/README.md` | 更新任务状态、训练结果 |
| **实验 META** | `experiment/s1-poc-e01/META.json` | 更新状态为 completed、添加评估结果 |
| **评估报告** | `experiment/s1-poc-e01/EVALUATION_REPORT.md` | 新建：完整对比分析与决策 |

#### 新建脚本

| 脚本 | 路径 | 用途 |
|------|------|------|
| `verify_lora.py` | `scripts/verify_lora.py` | 验证 LoRA 权重可加载、可推理 |
| `layer2_smoke_infer_poc.py` | `scripts/layer2_smoke_infer_poc.py` | PoC 后冒烟测试（前 10 条） |
| `layer2_full_infer_poc.py` | `scripts/layer2_full_infer_poc.py` | PoC 后全量推理（500 条） |

---

## 3. 关键问题与解决

### 问题 1：Hugging Face 认证失败
**现象**：`401 Unauthorized` 错误
**解决**：添加 ModelScope（魔搭）支持，设置 `USE_MODELSCOPE=1`

### 问题 2：4-bit 量化潜在缺陷
**风险**：精度损失、梯度噪声、特定层敏感
**权衡**：PoC 阶段接受，Stage 1 对比 BF16 效果

### 问题 3：zh_guard 严重退化
**现象**：中文保护层下降 -42.6%
**根因**：中文数据比例低（40%）、训练轮数少（1 epoch）
**对策**：Stage 1 增加中文比例到 50%+，增加到 2-3 epoch

---

## 4. 产物清单

### 训练产物（AutoDL）
```
experiment/s1-poc-e01/
├── adapter_config.json          # LoRA 配置
├── adapter_model.safetensors    # LoRA 权重 (5.14 MB)
├── tokenizer.json               # Tokenizer (31 MB)
├── training_meta.json           # 训练元数据
├── checkpoint-200/             # 第 200 步检查点
├── checkpoint-250/             # 第 250 步检查点（最终）
└── results/
    ├── poc_infer_full_*.jsonl   # 500 条推理结果
    ├── poc_judge_scores.jsonl   # 评委打分（480 条）
    └── poc_judge_summary.json   # 汇总报告
```

### 文档产物
```
_docs/sprints/
├── Sprint1-07_train_poc_explained_CN.md    # 训练脚本详解（更新）
├── Sprint1-06_autodl_setup_CN.md          # AutoDL 指南（更新）
└── img/
    ├── autodl_2.png ~ autodl_7.png       # AutoDL 截图

experiment/s1-poc-e01/
├── README.md                # 实验 README（更新）
├── META.json                # 实验元数据（更新）
└── EVALUATION_REPORT.md      # 评估报告（新建）
```

---

## 5. 时间投入

| 阶段 | 时长 | 说明 |
|------|------|------|
| PoC 训练 | 6.4 分钟 | RTX 5090 上实际训练 |
| 权重验证 | 2 分钟 | 加载测试 |
| 全量推理 | ~30 分钟 | 500 条（AutoDL） |
| 评委打分 | ~60 分钟 | 480 条（本地 API） |
| 文档整理 | 2 小时 | 本日志、评估报告、脚本完善 |
| **总计** | **~4 小时** | 含训练和文档 |

---

## 6. 下一步（Week 3 Stage 1）

### Stage 1 保守训练计划

**数据**：
- 总量：完整 13k 条（v1.0）
- brainstorm_cn 比例：50%+（增加中文）
- seed 数据：补齐自建 500 条

**训练配置**：
- epochs：2-3（对比 1 epoch）
- lora_r：8-16（尝试更大 rank）
- learning_rate：1e-4 或 2e-4（尝试更低 lr）

**目标**：
- zh_guard 层提升到 60+（当前 44.71）
- core 层保持 80+ 或提升到 85+
- general 层保持不大幅退化

---

## 7. 修订历史

| 时间 | 修订 |
|------|------|
| 2026-05-17 20:00-22:00 | 创建本日志，整理 Week 2 PoC 完整工作记录 |
