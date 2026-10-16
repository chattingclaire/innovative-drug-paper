# metrics_engine.py 的独立接口复核

日期：2026-10-10。审查方式：只读代码静态复核；没有运行母引擎，没有读取任何真实记录文件或结果文件。本次仅新增本报告，未修改母引擎或此前独立 toy 文件。

审查源：`07-statistics/prospective-engine-sol/metrics_engine.py`，首次读取为 442 行版本；随后读取时的 SHA256 为 `9fcf2bd699bec79e0be325bf72efe3c9db66cc299c52482e9c2cab6e492a513b`。母代理后续修订会改变行号和 hash，本报告的公式与函数名为主要定位依据。

结论：核心 κ、P/R/F1、九格、按维比较域、未知 share 的 H=0 分支和 numeric/formal 分离正确。发现 **Specificity/NPV 互换的明确数学错误**，已即时告知母代理；另需收紧元数据断言类型与身份码要求。封存 joined projection/assigned ID 绑定、positive-share 可行性显式字段为母代理已声明会补的项目，尚未在首次读取版本中验证。

## 1. 必须修正：Specificity 与 NPV 互换

母引擎分类比较的方向是 prediction 行、reference 列，四格为 `a=TP`、`b=FP`、`c=FN`、`d=TN`。正确式为：

`Specificity = d/(b+d)`；`NPV = d/(c+d)`。

首次读取版本的 `exact_metrics`、`vector_metrics` 均用了相反分母；`metric_gradients` 的相应导数也沿用了相反定义。应一起修点值、replicate 点值和梯度，避免点值修正后 SE/CI 仍与错定义对应。

正确梯度，按 `(a,b,c,d)` 顺序：

`∇Specificity = (0,-d,0,b)/(b+d)²`；`∇NPV = (0,0,-d,c)/(c+d)²`。

透明手算回归案例：

| a,b,c,d | Specificity | NPV |
|---|---|---|
| 4,1,3,2 | 2/3 | 2/5 |
| 2,1,0,3 | 3/4 | 1 |

第一例用母引擎正确的其余公式还应得到：Precision=4/5、Recall=4/7、F1=Ppos=2/3、Pneg=1/2、κ=1/5。交换 b/c 会交换 Precision/Recall，并交换 Specificity/NPV；F1、Ppos、Pneg、κ 不变。建议在 meaningful_math_checks.py 中对附加指标与梯度加入这两个非对称案例。

此错不影响当前 κ/P/R/F1 的 0.8 分项门槛，但影响公开附加诊断数值与其 SE/CI，因此应在交付前修复。

## 2. 必须收紧：元数据布尔断言和身份码

`review_eligibility` 对 human 的 `verified` / `independent_initial`、reference 的 `credible` / `blinded_to_machines`、外部 `identity_and_source_evidence_reviewed` 使用 Python truthiness。`_validate_metadata` 及 review 中的 seal `sealed` 也使用 truthiness。于是字符串 `"false"`、`"no"` 或数字 1 可被当成肯定断言。

这里应要求每个布尔确认字段 `is True`，其余值给 prerequisite gap 或 DataError。已有六个 freeze 字段采用 `is True`，建议沿用同样约定。

A/B `identity_code` 当前仅检查是否相等：两者缺失会被拒绝，但单方缺失与另一方非空不同，反而不会触发 distinct-people 缺口。应先分别验证 A/B identity code 为非空字符串，再验证不相同；不能凭 `None != "coder-B"` 视为已证明两位不同的人。

这两项可能让 `metadata_attestations_complete_for_project_review` 误报 complete。由于 `formal_acceptance` 始终 False，当前不会自动变成正式验收；但 review-ready 元数据状态本身也应准确。

封存输入目前首次读取版本仅确认 seal 的声明和 64 位 hash 格式，尚未将它与 records 的实际投影内容比较；`frame_ids_sha256` 同样仅验格式。母代理已声明会增加 sealed joined projection 与 assigned ID 绑定，必须以内容复核一致为条件，而不是格式检查通过后推断一致。

## 3. 状态层与 assigned 保留

`prepare` 严格限制 0/1 为 integer，拒绝 bool/string/NaN；completed 输出必须含全部五个维度，显式 null 可保留。按维 `dimension_status=execution_failure` 时要求标签为 null，并仅将该维记为 failure；其余维度仍可正常比较。整份 execution_failure 时不允许任何非 null 标签。

没有返回输出 `out is None` 被显式映射为五维 execution_failure，且仍保留 assigned 行。每层 observed row 数须等于冻结 n，因此漏行不会减少 assigned denominator；这一点正确。

首次版本将“技术失败”和“没有返回输出”合并为同一第四状态。这满足 no-output 不是 semantic null、未决质量包含两者的要求，但不提供两者各自的过程审计计数。建议保留 `nonreturned_output_count` 或原始 terminal reason 旁表；数学仍使用同一个 failure state。不要为区分原因而从 joint table 或 denominator 删除未返回单位。

接口细节：整份 failure 的 labels 目前仅支持省略字段或全 null 字典；若 `labels:null`，调用 `.values()` 会产生 AttributeError。可以明确冻结 schema 禁止这种形态，或在验证器中将其识别为空标签并给出一致处理。outputs、labels、dimension_status 的 mapping 类型也宜显式校验，使 malformed 输入得到 DataError。当前这个问题只会阻止运行，不会静默产生通过数值。

`unit_id` 的错误文字要求非空，但当前判断仅检查字符串和去重，空字符串本身可通过。建议增加非空验证；assigned ID 内容绑定补齐后也应在验证入口给出明确错误。

## 4. 九格、边际与可比域核查通过

每维状态组合 `left*4+right` 映射到 4×4；左上 3×3 是 0/1/null 九格，左上 2×2 是可比四格。`_exact_weighted_cells` 的类别顺序 `(5,4,1,0)` 与 prediction-row 的 TP/FP/FN/TN 一致；A/B 比较明确声明双方无真值优先。

`_table_summary` 的 row/column all-assigned state totals 保留角色边际；comparable 总数只来自二者同时有效 0/1 的四格。即使某维未知，该单位其余有效维度依然进入各维自己的比较域。加权表与 exact fraction 四格使用冻结层权重 N_h/n_h，failure/null 单位没有从权重母体消失。

角色有效边际 n 没有单独命名字段，但可由各自 state totals 的 0+1 直接取得；不得误用 `left_comparable_positive_negative` 的和来声称角色所有有效边际。建议导出显式 `left_valid_binary_total` / `right_valid_binary_total`，以减少读表歧义。五维同时完整的配对数可另外作诊断，不能替代当前按维比较的 denominator。

独立 fixture 中的透明期望仍适用：assigned=7、weight=11；A/B D1 有效边际各为 4，但 D1 pair=2、pair weight=3；D2–D5 pair=3/3/4/4；五维同时完整 pair=1、weight=1。当前代码结构与该分母定义一致，但本次未调用母引擎执行该 fixture。

## 5. attention 与 H=0 核查通过，需显式 positive possible 字段

`analyze` 以 `U = weighted(semantic null + failure)` 计算未决质量，denominator 是 domain 内全部 assigned 权重和。其已知 coverage 与 share 字段含 known 前缀；unknown bounds 单独命名为 not_CI，没有把未知值替代为 0 后称为完成的真实关注度。

`attention_bounds` 的 H>0 两端点与独立数学审查一致。H=0 时：U=0 返回 share bounds=None；本维 u=0 返回 [0,0]；仅本维可 positive 返回 [1,1]；本维与其他维均可 positive 返回 [0,1]；所有这些数值范围明确 conditional on positive total，另返回 zero-total undefined possible。

母代理计划增加的 `positive_share_possible` 应为 `H+U>0`，与 `zero_total_share_undefined_possible=(H==0)` 分别独立报告。H=0,U>0 时两者均 True；H=0,U=0 时前者 False、后者 True。否则消费者可能误把 conditional-positive bounds 误解为 share 已定义。

部门 contrast 用 `[L_A-U_B,U_A-L_B]`，并保留任一域 zero-total 导致 undefined 可能，且声明双方 denominator positive 条件；在 disjoint domain、独立未知补全下正确。若 positive scenario 不可行，已有 None 阻止生成数值 contrast；建议同步导出 `both_domains_positive_possible` 便于消费端区分空条件。

## 6. κ、P/R/F1、NA 和正式验收核查通过

κ、Po、Pe、Precision、Recall、F1、Ppos、Pneg 的主公式与 gradient 在当前方向下正确。Fraction 点值直接与 4/5 比较，避免 0.8 附近二进制舍入改变分项通过。human 比较只取 κ 目标；machine 每维取 κ/P/R/F1，diagnostics 没有额外机械门槛。

Ppos 和 F1 同式的解释已写入输出，不把其称为两份独立证据。direct-count F1 的 NA 处理正确：单侧无 positive 而另一侧有 positive 时 F1=0；双方都无 positive 时 F1/Ppos=None。全负全一致 κ=None；全正全一致 κ=None，即使 F1=1，κ 目标仍不通过。任何目标 None 均不通过。

`all_numeric` 只聚合 ALL 域三个比较的五维目标；部门分项另行输出。只执行 human-first 或 machine-reference 阶段时，全项目 numeric 不会默认为通过。`review_eligibility` 把数值通过、元数据供复核状态和正式验收分开，且 formal_acceptance 恒 False；human 身份、冻结过程、可信 reference 缺失不会因 κ≥0.8 自动正式通过。元数据自身不能认证身份的限制也明确保留。

已知 hit 指标的 bootstrap CI 与 unknown partial-identification bounds 分栏。undefined replicate 不输出无条件 95% CI，非 census 退化 interval 不宣称信息充分；这些边界契约与本任务要求一致。本报告不重复审定整个 bootstrap/finite-guard 理论，其独立方法复核由相应代理负责。

## 7. 合成验证材料与本次执行边界

此前独立数学材料中的 `toy-boundary-cases.json`、`toy_boundary_enumeration.py` 与 `toy-enumeration-result.json` 可作母引擎 meaningful_math_checks.py 的 expected oracle。完整精确穷举通过 59,292 个基础模式、1,049,600 个未知二元补全；另外 7 个手工边界案例、8 个四格案例及边际/配对/九格案例通过。

本次接口审查没有运行母引擎，不能将静态通过条目写成母引擎已完成合成执行测试。建议母代理完成 Specificity/NPV、严格元数据断言及封存内容绑定修正后，用自己的接口运行独立 fixture，并保留 snapshot hash 与结果；这些仍是透明 synthetic tests，不是正式人工/机器验证结果。
