# 事前统计契约 v2：独立只读对齐附记

日期：2026-10-10。此次只读两个指定方法文件及当前新引擎源码；未打开它们引用的正文、标签、未封存结果或其他数据文件，未运行新数据统计、母引擎或模型。旧方法与旧复核文件均未修改。

**结论：v2 指定的 primary 共同单位 Rao–Wu FPC 重缩放 percentile bootstrap，与当前引擎默认执行流程一致；secondary 解析协方差及梯度仅作独立复核/诊断，未提供结果出现后择优替换 primary 的路径。剩余 1444 域与 full 4481 审计被明确区分。此为方法和实现对齐，不是实际执行、整体冻结或真实指标达标证明。**

## 所读文件及哈希

| 文件 | SHA256 |
|---|---|
| [validation-design-v2.json](/PROJECT_ROOT/outputs/goal-calibration-20261010/02-methods/prospective-statistical-contract-v2/validation-design-v2.json) | `e53487ee355a1a8872833f7740edef1368035565b35a35817c4e171b976e2266` |
| [统计契约说明与勘误.md](/PROJECT_ROOT/outputs/goal-calibration-20261010/02-methods/prospective-statistical-contract-v2/统计契约说明与勘误.md) | `3752307f5b63cd9d1efea7c8ab6dbfd274f0756cd245349dcecd5675531148da` |
| [metrics_engine.py](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py) | `7d6f75594745f0e2d6cf9e211c789bd5006630064089116c7553e2f7770ba0f1` |

哈希亦存于本目录 `statistical-contract-v2-read-manifest.json`。该清单只绑定此次实际读过的三份文件，不声称已审核它们引用的其他材料。

## Primary 与 secondary 的逐项匹配

| v2 事前契约 | 当前实现 | 核定 |
|---|---|---|
| 固定单阶段分层 SRSWOR、基础权重 $N_h/n_h$、保留 FPC | `prepare` 的设计及 n/N 检查；`rao_wu_weights` 的 $m_h=n_h-1$ 多项重抽及 $1+\sqrt{1-n_h/N_h}(n_hk_{hi}/m_h-1)$ 因子 | 一致。全取层因子 1；非全取 singleton 拒绝。不是可选 union/两阶段设计的实现。 |
| primary 预设 5000 次、seed=20261010 | `rao_wu_weights`、`analyze` 及 CLI 的默认值均为 5000/20261010 | 默认参数一致。bootstrap seed 与尚待冻结的真实抽样 seed 是不同参数。 |
| 所有方法及五维共用每个单位的重复权重 | [analyze](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:378) 在任何比较/维度循环前生成一张 W；后续 A/B、rule/reference、LLM/reference、所有维度及 attention 均使用这张 W | 一致，保留配对与跨指标协方差，不重新抽标签或重跑模型。 |
| primary 为逐指标 percentile 95% | `vector_metrics(W@X)` 后 `_interval` 取 .025/.975 分位；明确 `method='linear'`；输出逐指标近似区间声明 | 一致，不声称有限样本精确覆盖或 45 项同时 95%。 |
| secondary 为四格设计协方差与解析梯度、保留 FPC | [analytic_covariance 与梯度调用](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:400) 使用原 assigned-unit n，层内样本协方差乘 $N_h^2(1-f_h)/n_h$；`metric_gradients` 得到 $g$，诊断 SE=$\sqrt{g^TVg}$ | 一致。解析 SE 与 primary CI 并列诊断，不重新构造可供择优的另一套主 CI。可比较四格的随机分母包含在齐次指标梯度内，没有删除未知行后重新定义原抽样 n。 |
| 未定义重复与稀疏退化须明示 | `_interval` 不把有无定义重复混合后宣称无条件 95%；非全取退化抑制充分性 CI；全取域依 `domain_is_census` 单独识别 | 一致，全取零抽样误差仍条件于现有标签，不能证明参照或构念无误。 |
| 零类别/稀有格使用有限总体保护；联合 $H\times C$ 区域须保留格数约束 | `finite_count_interval` 超几何参数反演；单类别跨层 Bonferroni；完整含 null/failure 状态的 joint guard 使用 $C=16$、$\alpha/(16H)$ | 一致。当前联合指标可行极值投影明确未实现；输出为计数约束，不能改称 κ/P/R/F1 的精确联合置信限。 |
| 非概率开发材料不报总体 CI | `nonprobability` 不生成 W，`_interval` 返回无总体 CI | 一致，不将开发合成例或历史算术当正式验证。 |

四格方向和修正后的诊断公式亦一致：机器为行、reference 为列；$a=TP,b=FP,c=FN,d=TN$；Specificity=$d/(b+d)$，NPV=$d/(c+d)$。勘误明确修正这两个诊断分母，未更改 κ/P/R/F1 主公式或点目标。

## 范围：1444 不能被权重扩张成 4481

两个方法文件均声明：当前剩余池范围是 1444；被开发曝光闭包排除的 3037 项在 remaining-only 设计下 $\pi=0$。HT 设计加权只能恢复具有正纳入概率的该剩余有限总体；不能把 1444 的机器参照比较、错误率或信度重加权成 full 4481 的相同验证结论。另做 full 4481 审计需在全部目标 ID 上实施正概率抽样及真实参照流程；开发曝光项可以被审计，但不能重新叫未见泛化验证。

当前 [review_eligibility](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:339) 将 `remaining_1444` 与 `full_4481_audit` 分为两种范围；分别核对声明总体 N 为 1444/4481，并对 remaining 输出 `remaining_1444_cannot_validate_all4481=True`。`prepare` 另要求总体 N 等于所有已声明正概率层总体大小之和。实现与该范围约束相符。

这些 checks 只检查输入声明和绑定，不能自行鉴证总体 ID 框的真实性或证明遗漏层未被隐去；正式身份/冻结/框范围证据仍须外部审查。当前引擎保留 `formal_acceptance=False`，没有将 metadata 完整或数值点值达标自动当正式项目验收。

## 对齐的界限与最终执行核对

v2 的 `root_revision` 明示 `sampling_n_locked=False`、`source_and_manual_and_methods_fully_frozen=False`、`human_execution_completed=False`。这与两文件“冻结前契约、尚未真实执行”的状态一致。5000 次是本研究事前执行选择，不是文献普遍的合格线；不能把方法文件写好等同于整个流程已冻结。

当前通用函数/CLI 仍允许调用者显式传入其他 `replicates` 或 `seed`，用于合成 QA 是合理的。故本次确认的是**正式契约与引擎默认值匹配**，不声称引擎已经强制锁住契约参数。未来正式执行需将实际记录的 B、bootstrap seed、量化方法、输入与统计源码哈希同事前冻结契约核对；不得在真实结果后选择更有利的参数或区间。这是遵守已选方法的执行核对，不增加项目阈值。

JSON 保留的精度工作目标及 n 规划例子不能被改写成新的结果验收门槛。v2 勘误及引擎 `CI_lower_or_halfwidth_gate_added=False` 均保留逐维 0.80 **点指标**目标；primary CI 和 secondary SE 分别报告不确定性与诊断，没有新增 CI 下界/半宽或 AC1 宏平均、CVI、KMO 要求。

对齐附记状态：**V2_PRIMARY_SECONDARY_AND_SCOPE_CONFORM / DEFAULT_B5000_SEED20261010_MATCH / PREEXECUTION_NOT_FULLY_FROZEN / NO_STATISTICAL_EXECUTION_OR_REAL_RESULT_REVIEW**。
