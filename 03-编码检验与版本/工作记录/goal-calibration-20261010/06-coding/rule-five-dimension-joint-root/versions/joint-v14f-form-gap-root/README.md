# F 剂型适用缺口隔离候选

本候选从完整冻结 v13b 复制。算法仅修改 relations.py：当前同一所需药品的全部现有剂型不适用于儿童、新剂型适宜，且通过同版完整来源中真实优先申请直接父链获得机会时，建立 F-only 关系。该缺口单列 no_child_suitable_existing_form，不改称无有效治疗、境内无批准或断供。其他四核心模块与 v13b 字节一致。

尚未采纳，未运行总体。有限控制由 run_finite_controls.py 接入 rule-repair-v14/F/run_controls.py，须提供新的独占输出目录名。本轮保护 S/E/Ec/I 完整决定及原来源动作，不套用旧保护 F 的合同。历史 I-only 选择器仅保留，当前静态入口明确停用。

实际 377 控制的结果、输入绑定、代码快照与剩余限制见 rule-repair-v14/F/candidate-summary.json。该有限开发检查不属于独立准确性验证；00104 使用既有当前 v16 绑定材料，没有新来源递送。
