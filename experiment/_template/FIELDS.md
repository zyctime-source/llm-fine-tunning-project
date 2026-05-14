# META.json 字段说明（`schema_version`: `experiment-meta-v0`）

| 字段 | 类型 | 说明 |
|------|------|------|
| `schema_version` | string | 本文件结构版本； bump 时同步更新模板与历史实验。 |
| `experiment_id` | string | 唯一 ID；基线建议 `baseline-gemma4e2b-it-layer2-v0`，训练实验见 shaping 命名习惯。 |
| `experiment_kind` | string | `training` \| `eval_only`。 |
| `stage` | string | `baseline` \| `poc` \| `stage-1` 等。 |
| `status` | string | `draft` \| `wip` \| `completed` \| `aborted`。 |
| `parent_experiment` | string \| null | 父实验 ID；基线为 `null`。 |
| `base_model.repo_id` | string | Hugging Face `repo_id`。 |
| `base_model.revision` | string \| null | **强烈建议**在首次下载后填入具体 commit，便于 bitwise 复现。 |
| `training` | object \| null | `eval_only` 时为 `null`。 |
| `data_recipe` | object | 指向数据 spec 与 `recipe_id`；训练可补 `data_mix`。 |
| `evaluation` | object | manifest 与 `eval-protocol-v*`；无评测可留空对象或删字段（需在团队内统一）。 |
| `results.*` | string \| null | 本地或相对仓库的产出路径；跑完后填写。 |
| `results.raw_outputs_dir` | string \| null | 原始推理 JSONL 等所在**目录**（相对仓库根）。 |
| `results.smoke_infer_jsonl` | string \| null | （可选）Layer 2 冒烟脚本单次输出的 JSONL 文件路径。 |
| `results.smoke_infer_profile` | object \| null | （可选）冒烟参数摘要：`items`、`max_new_tokens`、`script`。 |
| `baseline_scores` / `result_scores` | object \| null | 摘要指标；详细表留在报告或 `results/`。 |
| `decision` | string \| null | `accept` \| `iterate` \| `reject`；评测基线可选 `null`。 |

与 [_docs/shaping/8_train_iterate_CN.md](../../_docs/shaping/8_train_iterate_CN.md) §8.2.3 示例兼容；本仓库扩展了 `experiment_kind`、`evaluation` 嵌套对象与 `schema_version`。
