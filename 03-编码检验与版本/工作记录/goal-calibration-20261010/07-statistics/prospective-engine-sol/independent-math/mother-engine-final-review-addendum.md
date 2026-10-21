# 母统计引擎修复后最终数学附记

日期：2026-10-10。本附记补充原 `math-review.md` 及 `mother-engine-review-addendum.md`，两份原记录保持不变。仅只读修复后的母源码与合成 QA 源码；未执行母引擎、未重跑 QA、未查看任何真实数据、未揭盲结果或母引擎运行输出。

本次复核绑定：

- `metrics_engine.py` SHA256：`7d6f75594745f0e2d6cf9e211c789bd5006630064089116c7553e2f7770ba0f1`
- `meaningful_math_checks.py` SHA256：`9c1359b6a5df753f06156a970c5d48a4f01ea48bb11aeafb78b6554ba8074eb0`

**结论：前次报告的部门域全取遗漏已在静态逻辑上修复，guard 的先验证后转换亦符合要求。此次指定修复中未发现新的数学阻塞项。含 FPC 重复权重、解析协方差、单类别及联合状态格计数保护的原核心核定结论继续成立。**

| 修复 | 只读核定 |
|---|---|
| [domain_is_census](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:283) | 非概率设计返回 False。若全部总体层均全取，返回 True；否则 ALL 不是全取，部门域只有在**所有总体层均有固定非空部门标记**、目标部门有对应层、该部门所有层都满足 n=N 时才为 True。未将观测样本成员身份代替未抽单位的总体归属信息，符合前次建议的必要边界。 |
| [比较指标的域级调用](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:389) | 每域生成 `domain_census`，传给该域全部 `_interval` 调用，并在输出标记 `domain_full_census_no_sampling_error`。因此全总体非全取不再抑制已全取部门的确定指标区间。 |
| [attention 的域级调用](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:432) | null、failure、unresolved、known coverage 和 known share 的所有区间均改用相同域全取标记。未定义 share 或指标仍由 `_interval` 拒绝，域全取不会把无定义分母变成有定义结果。 |
| [single-category guard](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:221) | 原始数组须与 assigned records 一一等长且每值精确属于 0/1，随后才 `astype(int)`；0.5、NaN、超范围值或错误形状不会被整数转换掩盖。 |
| [joint-state guard](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:237) | 原始数组须一维等长且每值精确属于 0…15，验证后才转换；不会静默截断 16.5 或漏掉超范围类别。原 $\alpha/(16H)$ 联合计数区域及“尚未实现指标投影”的声明保持一致。 |
| [分位数调用](/PROJECT_ROOT/outputs/goal-calibration-20261010/07-statistics/prospective-engine-sol/metrics_engine.py:299) | `numpy.quantile(..., method='linear')` 明确指定插值约定；输出也声明该方法，并声明重抽单位顺序为由完整执行输入 SHA256 冻结的输入记录顺序。 |

只读检阅新增合成检查，确认其触发例有两个 NHC 全取单位且 S 标签分别为 0 和 1，因此 κ 可定义为 1，覆盖比例为 0.5；对应检查要求 κ 点区间 `[1,1]`、coverage 点区间 `[.5,.5]`。删除全部层的部门 metadata 后，检查要求不能仅由已抽记录部门归属声称域全取。另有 0.5 类别、16.5 配对状态及错误指示量长度的拒绝检查。**这里确认检查源代码的数学意义，未自行运行或宣称新增检查已通过；运行证据由父任务保留。**

前次非阻塞说明继续有效：`variance_about_original_point` 是关于原点估计的 bootstrap 均方偏差；对非线性指标可包含 bootstrap 均值偏移平方，不能被另行解释为严格中心化条件方差。该字段不参与新验收门槛，不影响本次修复核定。

原独立合成校核与主源码只读核定仍不构成真实指标达标证据。身份、freeze、范围和标签完整性条件须按既定封存流程审查；真实点指标与 0.8 的比较只在授权的封存输入执行后形成。没有新增 CI 下限/半宽、AC1 宏平均、CVI 或 KMO 要求。

最终附记状态：**STATIC_MATH_REVIEW_CONFORM / DOMAIN_CENSUS_ISSUE_RESOLVED / NO_NEW_BLOCKING_MATH_FINDING / NO_MOTHER_ENGINE_EXECUTION / NO_REAL_DATA_REVIEW**。
