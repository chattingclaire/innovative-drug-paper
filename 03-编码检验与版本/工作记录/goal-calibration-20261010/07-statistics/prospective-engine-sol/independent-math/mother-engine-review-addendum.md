# 母统计引擎只读数学复核附记

日期：2026-10-10。此附记保留原独立数学复核，不替代原记录。只读检阅 `metrics_engine.py` 与 `meaningful_math_checks.py`；未执行母引擎、未重跑母 QA 脚本、未读取任何真实未揭盲结果或任何引擎运行输出文件。只使用源代码及下述明确人工合成的算术例子。

复核时源码绑定：

- `metrics_engine.py` SHA256：`56504e6422ce59f75fc20ceb94627ef5274133c80b7b0e7fc5851d7afd9f8d14`
- `meaningful_math_checks.py` SHA256：`87c900185d7920b4136da93218625d47e02d0a5f09c2e34d8f00b715b1f5f076`

**结论：指定五处核心实现与独立数学结论一致。发现一处部门域全取判定遗漏，会错误地抑制已全取部门的零抽样误差区间；属于偏保守的结果标记问题，不是 FPC 公式错误或伪造达标。其余两处为可读性和接口硬化建议。**

## 核心实现逐项复核

| 实现 | 静态结论与理由 |
|---|---|
| [rao_wu_weights](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:177) | 非全取层用 `Multinomial(n−1;1/n,…)`；因子为 $1+\sqrt{1-n/N}[nk/(n-1)-1]$；每个已抽单位权重为基础 $N/n$ 乘该因子。全取先跳过，合法 singleton 全取保持权重 1；非全取 singleton 拒绝。调用点只生成一张 W，所有方法/维度共用。符合独立证明。 |
| [analytic_covariance](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:194) | 按原已抽单位保留全部行，逐层计算样本协方差 `center.T@center/(n−1)`，乘 $N_h^2(1-f_h)/n_h$ 后相加；全取跳过。域内变量由域外行置 0 表示，没有对可比较子集重抽或缩小原 n。既支持线性四格总量，也保留配对协方差。 |
| [finite_count_interval](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:207) | 遍历可行整数总体类别数 $T\in[x,N-n+x]$；保留 $P_T(X\ge x)\ge\alpha/2$ 且 $P_T(X\le x)\ge\alpha/2$ 的参数集合。`sf(x−1)` 使用正确含等号上尾；这是超几何参数区间，而非超几何样本计数分位区间。全取返回 `[x,x]`。边界容差向保守方向扩大集合。 |
| [joint_table_guard](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:235) | 将 null/failure 保留为 4×4=16 个相互排斥状态类别，按 $\alpha/(16H)$ 分配给每个层×格的双侧参数区间；Bonferroni 为一个比较×一个维度给出至少 $1-\alpha$ 同时计数区域。输出明确要求整数、格数总和为 N，并明确 `metric_projection_implemented=False`；没有把边际端点当作 κ/P/R/F1 的联合置信限，也没有宣称 45 指标同时覆盖。 |
| [_interval](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:278) | 点指标无定义或出现任何无定义重复时，均不给无条件 CI95；定义子集的分位数被另标为 conditional。非全取重复分布退化时不给充分性的 CI95；全取才给确定点区间。正常重复用 2.5%/97.5% 分位数并明确 approximate。符合稀疏边界原则，但传入的 census 目前只有全总体级标记，见下述遗漏。 |

`finite_category_guard` 的 $\alpha/H$ 再传入双侧等尾区间，是单个预定类别总数的分层 Bonferroni 保护。它与原独立报告的**单侧** 95% 零专用上界并非同一尾概率约定：主引擎 `alpha=.05` 的零格上端用 0.025 尾概率，因此通常更保守。例如 $N=16,n=8,x=0$，主引擎双侧区间为 `[0,4]`；独立单侧 95% 零上界为 3。二者不是矛盾，也不需将主引擎改成单侧形式。

## 可操作遗漏：部门域全取应按冻结总体域判定

位置：[全总体 census 标记](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:362)、[域指标区间调用](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:384)、[注意力比例区间调用](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:432)。

当前 `census=all(h.n==h.N)` 被原样传入 ALL 和每个部门域。若总体中某部门已全取、另一部门仍为非全取，则该全取部门的指标确定且解析抽样 SE 为 0，但 `_interval` 会返回 `CI95=None` 与 `degenerate_non_census_requires_finite_guard_not_adequacy_evidence`。

无需运行引擎即可手算的合成触发例：冻结层 D 声明 `department=D,N=2,n=2`，两单位 A=B 的标签分别为 0 和 1；冻结层 E 声明 `department=E,N=4,n=2`，其两已抽单位标签任取合法值。D 域的真实有限总体只有两单位且均已观察，D 域 Po=κ=1。D 层 W 固定为 1，E 层在 D 域指示变量上全为 0，因此 D 域所有重复指标恰为 1，解析设计方差恰为 0。全总体 census 为 False 不能据此否认 D 域已经全取。

建议：保留全总体 census 字段，但给各域区间另传 `domain_census`。只在设计 metadata **事先明确了每层总体的部门成员范围**、该部门总体范围完整、且所有属于该部门的非空层均全取时判定域全取。若层的总体部门归属未声明，不能仅凭已抽记录恰好归于某部门就认定整个部门已全取。随后给此合成情形增加一个有意义的域级检查。

此遗漏抑制了本可报告的确定区间，没有造成虚假的 95% 区间或项目 0.8 达标判定。修复它不新增 CI 下限、CI 半宽或任何验收门槛。

## 两项不阻塞当前受控调用的说明

1. [_interval 中的 variance_about_original_point](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:291) 计算 $B^{-1}\sum_b(\hat\theta_b^*-\hat\theta)^2$。对于线性总量，完整 bootstrap 均值等于原点，它与条件方差相同；对于非线性指标，完整分布下它等于条件方差加 bootstrap 偏移平方。建议名称或说明明确为“关于原估计的均方偏差”，避免与中心化 conditional variance 混称。其本身不用于 CI 门槛，原值不必删除。
2. `finite_category_guard` 和 `joint_table_guard` 在转成整数后才检查或使用类别，可能将外部 0.5 指示量截断成 0，或把非法配对类别漏出 16 格。当前 `analyze` 调用由严格 `prepare` 的状态数组派生，因此当前内部路径安全。若今后将这两个函数暴露为独立接口，建议先验证输入长度、精确整数值和 0/1 或 0…15 范围再转换；不能依赖 `dtype=int` 来作类别认证。

源代码还使用固定种子和完整输入/源码哈希绑定执行。重复抽样分配顺序由输入层顺序及记录顺序决定，经验分位数用 NumPy 默认插值。未来若要求同一封存标签集合在文件重排后逐字得到相同 Monte Carlo 区间，应固定层/单位规范顺序并记录分位插值方法及 NumPy/RNG 版本。保留原输入文件可复现当前顺序，但仅保留排序后的投影哈希不够描述该顺序。

## 合成 QA 源代码覆盖的边界

只读检查显示 `meaningful_math_checks.py` 已写有：独立 sklearn 四格方向比较；指标梯度数值导数；小总体所有原 SRSWOR 样本的设计协方差；完整条件 Rao–Wu 九个重抽结果；实际生成器与解析 FPC 的合成比较；共享 W 的调用计数；超几何区间覆盖遍历；未定义重复、退化重复、全取 singleton、非全取 singleton 等边界。此附记未重新运行或独立确认其“47 项已通过”的运行输出；原父任务对此结果已有执行证据。

所有数学正确性结论仍条件于冻结的固定分层单位级 SRSWOR、完整 assigned-unit 行和正确总体大小。真实人类身份、盲态、封存、范围验证不能由这些数学函数自动认证；实现保持 `formal_acceptance=False`、不加 CI 下限/半宽门槛，符合本任务边界。

附记状态：**CORE_FORMULAS_CONFORM / DOMAIN_CENSUS_HANDLING_ISSUE_REPORTED / NO_MOTHER_ENGINE_EXECUTION / NO_REAL_DATA_RESULT_REVIEW**。
