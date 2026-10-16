# 母引擎修复复核附记

日期：2026-10-10。仅新增本附记；保留此前 `engine-interface-review.md` 与数学/toy 交付，不覆盖初审记录。

审查对象：`07-statistics/prospective-engine-sol/metrics_engine.py` 当前 478 行版本，SHA256：`56504e6422ce59f75fc20ceb94627ef5274133c80b7b0e7fc5851d7afd9f8d14`。

方式：只读代码静态复核；未运行母引擎，未读取真实未揭盲数据、真实标签结果或正文/语境。母代理报告 meaningful_math_checks.py 已通过 47 项；此为母代理提供的执行事实，本复核不将其写成本代理运行结果。

**复核结论：初审指出的数学错误和元数据门禁问题已修复；当前代码在本代理负责的状态、分母、边界和验收分离范围内，没有剩余阻断问题。** 这确认 prospective 引擎接口与数学实现，不构成真实项目验收。

## 修复逐项确认

| 初审问题 | 当前代码核查 | 结论 |
|---|---|---|
| Specificity/NPV 分母交换 | `exact_metrics` 与 `vector_metrics` 均为 Specificity=`d/(b+d)`、NPV=`d/(c+d)` | 已修复 |
| 同两项 gradient 沿用错式 | `metric_gradients` 为 `(0,-d,0,b)/(b+d)^2` 与 `(0,0,-d,c)/(c+d)^2`，对应顺序一致 | 已修复 |
| seal / verified / independent / credible / blinded / reviewed 使用 truthiness | 相关判断均要求 `is True`；freeze 与 artifact seals 同样严格 | 已修复 |
| 单方缺失 identity code 可误报 distinct | A、B、reference 均要求字符串且 `.strip()` 后非空；A/B 相同码仍拒绝 | 已修复 |
| missing return 与执行失败无审计分型 | `failure_causes` 分别编码 1 missing_return、2 method_execution_failure、3 dimension_execution_failure；按维输出 raw_n 与 weighted_total | 已修复 |
| 整份 failure 的 labels:null 出错 | `labels is None` 转为空映射；其余非法类型抛 DataError；有效标签仍禁止出现在失败输出 | 已修复 |
| 空 unit_id 通过 | 明确 `not rid` 拒绝 | 已修复 |
| H=0 缺少正 denominator 是否可行情景字段 | 新增 `positive_total_share_possible=(H+U>0)`，与 `zero_total_share_undefined_possible=(H==0)` 分开 | 已修复 |
| joined 投影与 assigned ID 仅有 hash 声明 | `prepare` 对 frozen assigned-ID hash 与实际 sorted IDs 比较；对每个 active 方法的 sealed joined-projection hash 与实际 canonical 投影比较 | 已修复该内容绑定 |

`failure_causes` 的三个 subtype 互斥；每个 state=3 的维度均在上述三个分型之一。分型没有将失败改成 semantic null；统计四状态表仍用第四状态，attention 未决质量仍使用 semantic null + 全部 failure。按维失败不删除其他四维已完成标签。

封存投影包含 unit_id 及该方法原始 output，按 ID 排序并采用 canonical JSON；更换标签、状态、输出版本字段或单位 ID 均改变投影绑定。active stage 之外的 unused outputs 被拒绝，避免把未封存的无关输出带入分析。

## 整体边界再次确认

四格方向仍为 machine prediction 行、reference 列，`a,b,c,d=TP,FP,FN,TN`；human A/B 无真值优先。九格是四状态表的 0/1/null 投影，可比 n 是两边同时有效 0/1 的四格总数；角色边际状态和保留在各自 row/column totals。权重使用原冻结层 N_h/n_h，包括 null/failure assigned 单位，不以 observed-only 子域重定义 assigned denominator。

coverage 的分母为域内全部 assigned 权重；unresolved 包含 semantic null、missing return、方法失败和维度失败。H>0 的 share 两个端点保持正确；H=0 时“仅 undefined”“正 hit 条件下 {0}/{1}/[0,1]”的分支保持正确。H=0,U>0 时正 share 与 undefined 两种情景都可行；H=0,U=0 时正 share 不可行、share 始终 undefined。部门差值仍声明双方正 denominator 条件，并保留 undefined 可能。

κ/P/R/F1/Ppos/Pneg 与 direct-count F1 的 NA 分支保持正确。全负全一致 κ/P/R/F1 不被当作达标；单侧无正类时 F1=0 且相应 P 或 R 可以 NA。Fraction 与 4/5 的点值门槛比较不受浮点舍入影响。

unknown bounds 仍以 not_CI 命名；known/status sampling CI 单独报告，未把 partial-identification 区间冒充 95% CI。undefined replicate 与非 census 退化区间限制仍显式保留。本代理未重复审定整体抽样/bootstrap 方法理论。

numeric point targets 与 review prerequisites 保持分离，`formal_acceptance=False` 恒定；缺少真实 human 身份、冻结过程、可信参考或外部 evidence review 会产生 prerequisite gap。真实身份无法由 JSON 自证，实际 target frame 成员资格及 frozen 设计/层归属、材料/流程证据仍需要项目显式复核。该限制已由代码保留，不是本次修复遗留阻断，也不能把 synthetic 检查成功用作真实验收依据。

## 交付判断

可将初审问题状态更新为“已修复并经独立静态复核”。此前独立 exact toy enumeration（59,292 基础模式、1,049,600 二元完成情景）与手工期望仍有效。本附记允许合成测试结果与 prospective 接口交付继续汇总；不授权新增真实标签计算，也不改变 policy 的正式验收状态。
