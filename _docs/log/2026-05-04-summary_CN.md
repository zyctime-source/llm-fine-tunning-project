# 沟通小结 · 2026-05-04（1小时）

本文档整理当日与「项目 shaping：产品形态 + 模型与能力策略 + 数据策略」相关的讨论与定稿产出。

---

## 1. 阶段定位

- 当日工作处于 **shaping**：界定产品形态、模型选型、数据配方与评估策略，**不包含**训练脚本、超参数、具体实现。
- 延续 05-03 的 shaping 进度，完成第 5、6、7 章初稿。

---

## 2. 第 5 章：产品形态（Surface）· 已定要点

### 2.1 客户端形态（决策已定）

- **首版形态**：Kotlin 原生 Android 应用
- **排除**：微信小程序、纯 Web、Kotlin Multiplatform 跨平台
- **决策理由**：本地模型部署是核心目标；全球可用性（Google Play）；开发者已有 Kotlin 经验
- **iOS 策略**：首版不包含；日后独立评估 Swift 或 KMP

### 2.2 推理部署形态

- **端侧推理（主要）**：小参数模型（2B-5B）本地运行，负责快速响应与隐私敏感场景
- **云端推理（备选）**：DeepSeek/Qwen 大模型 via API，用于深度生成与对比学习
- **协同逻辑**：默认端侧，显式切换云端，首版不定自动路由策略

---

## 3. 第 6 章：模型与能力策略（Model）· 已定要点

### 3.1 小模型候选观察清单

| 优先级 | 模型 | 参数 | 发布日期 | 许可证 |
|--------|------|------|----------|--------|
| P0 | Gemma-4-E2B-IT | 2B | 2026.4 | Google 自定义 |
| P0 | Gemma-4-E4B-IT | 4B | 2026.4 | Google 自定义 |
| P0 | Qwen3.5-2B | 2B | 2026.3 | Apache 2.0 |
| P1 | Qwen3.5-4B | 5B | 2026.3 | Apache 2.0 |
| P1 | Qwen3.5-0.8B | 0.9B | 2026.3 | Apache 2.0 |

- **2B 级对决**：Gemma-4-E2B vs Qwen3.5-2B 是 PoC 阶段核心对比焦点
- **不定最终选择**，PoC 实测后决策

### 3.2 大模型云端备选

- **DeepSeek-V3 / R1**：深度推理、对比学习
- **Qwen-Max / Plus**：中文场景深度生成
- **首版不考虑 GPT 系列**

### 3.3 能力扩展（Tools / skills+Tools / 多模态）

- 首版：纯对话脑暴 + 卡片收成
- 预留：Gemma-4 Any-to-Any 多模态扩展位
- 不定：具体 Tools 实现路径

### 3.4 微调策略

- **阶段 1（基础微调）**：公开数据 + 少量种子数据，学会「脑暴对话 + 总结收成」
- **阶段 2（个性化微调）**：用户定稿卡片（需授权），学习个人风格
- 技术：LoRA 优先，全参数微调备选

---

## 4. 第 7 章：数据策略（Data）· 已定要点

### 4.1 核心数据集

- **主数据集**：`DevQuasar/brainstorm_vicuna_10k`（10k 训练 + 1k 测试，英文）
- **数据增强**：Qwen-Max 翻译 → 中英双语平行数据集

### 4.2 微调数据配方（保守版）

| 数据集 | 条数 | 占比 |
|--------|------|------|
| brainstorm_vicuna_10k 英文原版 | 5,000 | 35% |
| brainstorm_vicuna_10k Qwen翻译中文版 | 5,000 | 35% |
| Alpaca/ShareGPT 通用 | 3,000 | 25% |
| 自建种子数据 | 500 | 5% |
| **总计** | **13,500** | **100%** |

### 4.3 评估基准（Machine Evaluation）

**机器评估方案（LLM-as-a-Judge）**：
- 评委模型：Qwen-Max（中文）、GPT-4（英文/交叉验证）
- 评分维度：相关性、连贯性、有用性、创造性（1-5分）

**公开基准数据集**：

| 数据集 | 规模 | 用途 |
|--------|------|------|
| X-AlpacaEval | 805 条 | 通用指令遵循（中英） |
| CMT-Eval | 596 条对话 | 中文多轮对话 |
| brainstorm_vicuna_10k 测试集 | 1,000 条 | 脑暴基础版 |
| brainstorm-v3.1_vicnua_1k | 1,000 条 | 脑暴+小结（评估总结能力） |
| brainstorm-v2.1_vicuna_1k | 1,000 条 | 脑暴追问深化版 |
| MT-Bench | 80 条 | 多轮深度对话 |

- **公开基准总计**：约 4,500 条
- **自建补充**：约 250 条（创意写作、卡片总结、产品场景）
- **评估集总规模**：约 **4,750 条**（可检测 > 3% 能力变化）

### 4.4 保守微调原则

- **LoRA 优先**：rank=8，冻结原模型 95%+ 参数
- **学习率控制**：1e-4，宁可欠拟合
- **轮数限制**：3 epochs
- **混合保底**：通用数据 25%，防遗忘

### 4.5 止损线

| 情况 | 统计标准 | 决策 |
|------|----------|------|
| 任一维度显著下降 | p < 0.05 且下降 > 10% | 警告，分析原因 |
| 任一维度大幅下降 | p < 0.01 且下降 > 20% | 回退基座模型 |
| 脑暴能力不升反降 | 上升 < 5% 或下降 | 调整数据配方重训 |

---

## 5. 落地文件（初稿）

| 路径 | 说明 |
|------|------|
| `shaping/5_surface_CN.md` | 第 5 章中文初稿（产品形态） |
| `shaping/5_surface_EN.md` | 第 5 章英文初稿 |
| `shaping/6_model_strategy_CN.md` | 第 6 章中文初稿（模型与能力策略） |
| `shaping/6_model_strategy_EN.md` | 第 6 章英文初稿 |
| `shaping/7_data_CN.md` | 第 7 章中文初稿（数据策略） |
| `shaping/7_data_EN.md` | 第 7 章英文初稿 |

---

## 6. 关键数据集链接汇总

| 数据集 | 地址 | 用途 |
|--------|------|------|
| brainstorm_vicuna_10k | https://huggingface.co/datasets/DevQuasar/brainstorm_vicuna_10k | 训练+测试 |
| brainstorm-v3.1_vicnua_1k | https://huggingface.co/datasets/DevQuasar/brainstorm-v3.1_vicnua_1k | 评估（带小结） |
| brainstorm-v2.1_vicuna_1k | https://huggingface.co/datasets/DevQuasar/brainstorm-v2.1_vicuna_1k | 评估（追问深化） |
| X-AlpacaEval | https://huggingface.co/datasets/zhihz0535/X-AlpacaEval | 评估（通用指令） |
| MT-Bench | https://huggingface.co/datasets/yzygalaxy/mt_bench_human_judgments | 评估（多轮对话） |

---

## 7. 建议的下一步

1. **Review**：通读 `5_surface_CN.md`、`6_model_strategy_CN.md`、`7_data_CN.md`，检查一致性。
2. **数据准备**：下载 brainstorm_vicuna_10k，开始翻译中文版本。
3. **评估集构建**：从公开基准中筛选适合脑暴场景的子集。
4. **下一 shaping 模块**：训练/实验策略（Train）、评测与质量（Eval）、或 3 个月项目规划。

---

*文档生成于项目 `log/` 目录，供个人学习与项目推进使用。*
