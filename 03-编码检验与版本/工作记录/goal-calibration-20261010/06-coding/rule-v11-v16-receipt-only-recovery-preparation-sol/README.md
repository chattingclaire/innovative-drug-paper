# 原 v11/v16 01402 收据保全准备

本目录仅准备接口；未执行收据恢复、合并、分类器或模型。ROOT 审阅本封印后，分别运行以下两个入口。输出目录必须此前不存在。

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/rule-v11-v16-receipt-only-recovery-preparation-sol/recover.py' --mode recover --go '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/08-audits/ROOT-v11-01402-receipt-only-causal-recovery-adoption.json' --output '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/rule-v11-v16-receipt-only-recovered44-root'
```

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/rule-v11-v16-receipt-only-recovery-preparation-sol/merge.py' --delta '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/rule-v11-v16-receipt-only-recovered44-root' --output '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/rule-full4481-v11-v16-receipt-delta-merged-root'
```

原 44 条实际运行仍是失败封印：43 条有效、01402 五个维度技术失败。纠正先前“在 judge 之前失败”的说法：原 judge 与 validate_decisions 已完成，完整五维候选保存在原 first；失败发生在后续读取收据清单核对。

恢复仅向原 14 项 inventory 增加 NP013–NP017-HEADER 五项，原项逐字保留。新增绑定来自封存 packet 与原结构化 JSON/HTML 精确区间，不从实际事件反推预期 hash。原 v12 prepare/check 字节与必读要求保持不变，通过有限中立 facade 消费同一材料。

原 29 个 source_view_events 与一个 relation trace 保持原组及原字段。BODY/READ-0 是冻结 driver、完整当前文本与后续第 14 项失败共同证明的历史局部动作，标记 `code_derived_historical_local_event_not_stored`；它不是第 30 个已保存事件，不追加时间戳。scope_review 只取冻结构造函数唯一 literal，标记 `frozen_literal_constructor_causal_recovery_not_stored`。原有效语义单元只有 43 个；01402 缺项继续明示，不重建。

派生 44 条保持 43 个原有效 prediction/215 slots 原始行字节，01402 decisions 直接取原 candidate diagnostic 的原始 JSON token；五个 slots 的 decision token 不改。完整 44 deliveries、bundles、原 ledger 和 43 units 原字节复制，故原 ledger 的失败记录仍可见。新 receipt ledger、execution 与 origin 分别说明派生状态。原失败目录无写入。

合并选择固定 44 条派生结果与 4437 条 v10 父行，保留所有真实推理来源；S/E/Ec/F 完整 decision 值与 token 字节必须相同，否则停止。原 44 条一次推理的失败身份和 01402 辅助 unit 缺失进入新 status。合并不新增推理。结果是 4481/22405 兼容集合，不是全 4481 都在 v11 下重新推理。

既有 `source-aligned-statistics-entry-sol/calculate.py` 无须修改：新 status 为 `complete_v11_v16_receipt_compatible_composite_with_explicit_execution_origins`，符合既有 `complete_*_compatible_composite_with_explicit_execution_origins` 接口，携带 source_common_v15/v16、material_delta_bindings 四绑定、01402 changed ID、impact/adoption/original lineage、prediction/slot 路径与真实逐行 origin。正式验收、人审核定与论文 gate 仍为 false。

预检只核真实 44 行、220 slots、43 units、存储事件与源绑定及冻结 AST。准备未调用 protocol prepare/check；实际恢复时才核接收，失败即停止，不能用 null/0 填补。可用 `recover.py --mode preflight` 作只读绑定检查。
