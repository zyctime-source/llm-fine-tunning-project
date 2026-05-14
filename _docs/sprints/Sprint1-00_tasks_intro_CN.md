# Sprint 1 任务总览：端到端微调流程打通

> **类型**：个人项目技术备忘  
> **日期**：2026-05-13  
> **GitHub repo**：https://github.com/zyctime-source/llm-fine-tunning-project  
> **英文版**：[Sprint1-00_tasks_intro_EN.md](Sprint1-00_tasks_intro_EN.md)

---

## 1. 背景

我一直对大模型微调很感兴趣。希望通过 vibe coding 在 3～4 个月内从零推进一个以大模型微调为核心、最终落在安卓端应用的落地项目，并全程留档。

### 1.1 项目背景：手机里的 AI 思维助手

**痛点**：灵感来时随手记，但传统笔记只能「存」不能「想」，也不能和其他灵感关联，三个月后回看，早已忘了当时的思路。

**方案**：做一款安卓 App，让「随手记的一句话」经过端侧大模型**追问-发散-收敛**，最终收成结构化的「灵感卡片」。选型上，用 **Gemma-4-E2B-IT**（4B 级）做基座，**LoRA 微调**对齐「头脑风暴」节奏，再量化到 INT4/INT8 塞进手机，兼顾隐私与成本。

**理解要点**：这不是通用聊天机器人，而是**结构化的思维辅助工具**——必须会追问、会收敛、能把散漫对话变成可行动的卡片。

### 1.2 本文聊什么

[Sprint1-dataset_download_processing_CN.md](Sprint1-dataset_download_processing_CN.md) 记录了数据准备，[Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) 说明了评测题单生成，[Sprint1-03_baseline-gemma-layer2-infer_CN.md](Sprint1-03_baseline-gemma-layer2-infer_CN.md) 覆盖了基线推理。本文从**项目管理视角**整理 **Sprint 1（第 1 个月）** 的完整任务清单：目标拆解、四周进度、交付物定义、通过标准与风险预案。

详细训练主线见 [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md)。

---

## 2. Sprint 1 核心目标

在 4 周内完成 **Gemma-4-E2B** 的 PoC 验证与 Stage 1 基础微调闭环，建立**最小可复现、可评估、可回滚**的训练流程。

### 2.1 时间投入

| 项目 | 数值 |
|------|------|
| **周期** | 4 周 |
| **预计投入** | 约 80 小时（每周 20 小时） |
| **预算建议** | 120-180 GPU 小时中，优先分配 40-70 小时到本 Sprint |

---

## 3. 任务优先级：Must / Should / Won't

### Must（必须完成）

- [ ] **冻结数据版本 `v1.0`**：形成数据说明与追溯信息  
  产物：[_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md)（已冻结 ✓）
- [ ] **完成 1 次 PoC + 1 次 Stage 1 训练**：产出可加载的 LoRA 权重
- [ ] **跑通 Layer 2 回归评估**：形成首份基线与微调对比报告  
  产物：[_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md)
- [ ] **固化实验命名与 lineage 记录**：建立实验 ID 规则（`s1-{类型}-e{序号}`）与父子血缘追踪

### Should（建议完成）

- [ ] **补齐中文保护题观察**：提前识别中文退化风险（zh_guard 子层小样本验证）
- [ ] **输出失败样本清单**：减少下个 Sprint 重复踩坑  
  产物：`s1-train-e01-error-cases.jsonl` 或类似结构化清单

### Won't（明确不做）

- ❌ **Stage 2 个性化微调**：用户个人风格学习留到后续 Sprint
- ❌ **多模型并行主线**：Qwen 仅作为风险备选，Sprint 1 不并行推进（先单点突破 Gemma）

---

## 4. 四周进度拆解

### Week 1：数据与基线准备

**目标**：让数据与评测基础设施就绪，基座模型可跑通 Layer 2。

| 任务 | 产物/参考 |
|------|-----------|
| 冻结 `v1.0` 数据配方 | [s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) |
| 产出实验元数据模板 | [experiment/README.md](../../experiment/README.md) `_template/` |
| 跑基座模型基线评估 | [baseline-gemma4e2b-it-layer2-v0](../../experiment/baseline-gemma4e2b-it-layer2-v0/) |
| Layer 2 manifest 生成 | [Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) |

**关键交付物**：
- `s1-data-v1.0-spec`（已定稿）
- `s1-baseline-report`（骨架已建，跑完 500 条后填入实测）
- 实验元数据模板 + 基线实例草稿

---

### Week 2：PoC 快速闭环

**目标**：用最短路径验证「数据 + 训练 + 评估」链路可跑通。

| 任务 | 说明 | 产物 |
|------|------|------|
| PoC 训练 | 小数据量（如 1k 条）、短轮数、快速验证训练脚本 | `s1-poc-e01/` 实验目录 |
| LoRA 权重导出 | 确保可加载、可推理 | `adapter_model.safetensors` |
| PoC 后评估 | Layer 2 对比基线，输出 Accept/Iterate/Reject | `s1-poc-e01-eval.json` |

**关键交付物**：
- `s1-poc-e01`（实验记录）
- `s1-poc-e01-eval`（评估结果与决策结论）

**决策出口**：
- **Accept**：PoC 验证通过，进入 Week 3 Stage 1 保守训练
- **Iterate**：调整数据或配置，本周内再跑一轮 PoC
- **Reject**：触发重大回滚（如换模型、改数据配方）

---

### Week 3：Stage 1 保守训练

**目标**：在 PoC 结论基础上，完成一次保守但完整的 Stage 1 训练。

| 任务 | 说明 | 检查点 |
|------|------|--------|
| 保守训练主跑 | 使用 `v1.0` 完整 13k 数据（或 12k 跳过种子）、标准 LoRA 配置 | loss 曲线平稳、无 NaN |
| 失败样本记录 | 同步记录异常输入与模型输出 | 按 Sprint 备忘格式结构化 |
| 中文保护验证 | zh_guard 子层快速回归，确认中文未退化 | 与基线对比，波动 < 10% |

**关键交付物**：
- `s1-train-e01`（实验记录）
- `s1-train-e01-error-cases`（问题清单）

---

### Week 4：收敛与 Gate1 评审

**目标**：固化成果，完成 Sprint 复盘，通过 Gate1。

| 任务 | 说明 | 产物 |
|------|------|------|
| Stage 1 对比报告 | 基线 vs 微调后，分层汇总 + 红线结论 | 填入 s1-baseline-report §5-§6 |
| Lineage 树状记录 | 可视化实验血缘：基线 → PoC → Stage 1 | `experiment/lineage-tree.md` 或工具图 |
| Gate1 评审 | 自检是否达到通过标准 | `s1-gate1-review.md` |
| Sprint 复盘 | 目标达成度、阻塞根因、下 Sprint 计划 | `s1-retro.md` |

**关键交付物**：
- `s1-gate1-review`（评审报告）
- `s1-retro`（Sprint 复盘）

---

## 5. Gate1 通过标准

Sprint 1 结束时的质量门槛，四项必须同时满足：

| 标准 | 具体含义 | 验证方式 |
|------|---------|---------|
| **训练可复现** | 同一配置重复运行，得到可接受的相似结果 | 固定种子、相同数据、两次训练 loss 曲线对比 |
| **评估可复跑** | Layer 2 能稳定运行并输出结构化结果 | 同一 manifest、同一协议，两次推理结果 SHA 一致 |
| **模型可加载** | LoRA 权重可被端侧/测试推理链路加载 | `layer2_smoke_infer.py` 加载 checkpoint 验证 |
| **能力不退化** | 核心能力达到「可用」，不触发 P0/P1 红线 | 见 [9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) §9.3 |

---

## 6. 风险与止损预案

| 风险场景 | 触发条件 | 止损动作 |
|---------|---------|---------|
| **中文质量显著退化** | 连续两轮中文保护题不可用（zh_guard 平均分 < 2 或 P1 触发） | 立即启动 Qwen 备选评估；暂停 Gemma 训练，评估切换成本 |
| **训练不稳定** | 当周重复失败超过 2 次（loss 发散、OOM、NaN） | 缩小变量范围（如减数据量、减 rank、冻更多层）；停掉 Should 任务，仅保留 Must |
| **成本超预期** | GPU 小时逼近当月上限 70h | 仅保留 Must 任务；中断非关键实验；考虑 CPU 推理验证替代 |
| **数据缺口** | 自建种子 500 条始终无法补齐 | 接受 `v1.0-skip-seed` 跑法，Gate1 后再评估补种必要性 |

---

## 7. Sprint 复盘模板

Sprint 1 结束时（Week 4 最后 1-2 天），按以下结构输出复盘：

```markdown
## Sprint 1 复盘（s1-retro）

### 目标达成
- 达成 / 部分达成 / 未达成
- 说明：________________________________

### 关键指标
- 核心能力（脑暴+总结）：基线 ____ → 微调后 ____（目标：不退化）
- 中文保护题（zh_guard）：基线 ____ → 微调后 ____（目标：不退化）
- 训练稳定性：成功 ____ 次 / 失败 ____ 次

### 主要阻塞与根因
1. ________________（根因：______________）
2. ________________（根因：______________）

### 下 Sprint 调整
- 保留项（继续做）：
  - ________________
- 删除项（不再做）：
  - ________________
- 新增项（新发现）：
  - ________________
```

---

## 8. 相关文档索引

| 文档 | 用途 |
|------|------|
| [Sprint1-dataset_download_processing_CN.md](Sprint1-dataset_download_processing_CN.md) | Week 1 数据准备细节 |
| [Sprint1-layer2-manifest_CN.md](Sprint1-layer2-manifest_CN.md) | Week 1 评测题单生成 |
| [Sprint1-03_baseline-gemma-layer2-infer_CN.md](Sprint1-03_baseline-gemma-layer2-infer_CN.md) | Week 1 基线推理执行 |
| [_docs/execution/sprint-1-train.md](../execution/sprint-1-train.md) | 详细训练主线说明 |
| [_docs/execution/s1-data-v1.0-spec_CN.md](../execution/s1-data-v1.0-spec_CN.md) | 数据配方冻结规格 |
| [_docs/execution/s1-baseline-report_CN.md](../execution/s1-baseline-report_CN.md) | 评测协议与报告骨架 |
| [_docs/shaping/9_eval_qa_CN.md](../shaping/9_eval_qa_CN.md) | 红线类型与评估维度 |

---

## 9. 修订历史

| 日期 | 修订 |
|------|------|
| 2026-05-14 | 初版：整合 sprint-1-train.md 主线，增加任务总览视角、四周进度表、风险预案与复盘模板 |
