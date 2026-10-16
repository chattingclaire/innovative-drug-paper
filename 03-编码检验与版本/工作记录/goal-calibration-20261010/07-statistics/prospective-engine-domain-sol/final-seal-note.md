# 分域统计接口交付封存

本轮源码、接口和构造数据验证已完成。新增内容仅在 `prospective-engine-domain-sol`，旧 `prospective-engine-sol` 的全部 56 个文件（原封存清单 54 个文件另已验哈希）逐字节保持，新增/缺失/变化均为 0。原 n600 及全域候选分配没有改动。

最终新源码 SHA256：`05f5999084a48b0e713e28f81e629015e61c1255cdaa43e89d30a6b59eed1d30`。旧源码及本目录冻结副本 SHA256：`7d6f75594745f0e2d6cf9e211c789bd5006630064089116c7553e2f7770ba0f1`。

接口 1.1 接受冻结 `stratum.domain`，输出 ALL、remaining、exposed、部门和非空分域×部门。所有输出在完整单位空间中用掩码投影同一次生成的 W，不能按域/比较重抽。新模式检查正纳入概率层、总体量、互斥覆盖、冻结部门、行层一致及分域覆盖拒绝；旧无 domain 设计保留原数值行为。κ/P/R/F1 从本视图加权四格计算，不平均域指标。

本轮验证结果：

- 主回归 284 项通过，覆盖旧版数学原语不变、分域全 16 状态表可加性、掩码与同一次 W、总体量、普查/NA/退化 CI、unknown/failure、逐域数值 flags 和全局 seal 绑定。
- 两路独立复核通过：86 项数学检查、179 项引擎数学接口检查；43 个独立元数据案例、9 个掩码检查、4 个旧版兼容场景。报告绑定同一最终源码 SHA。
- full800、full1000 均仅从 N/n/domain/department/schema 构造各 41 层 toy，默认 B=5000、seed=20261010。各运行 12 个视图使用同一完整 W，每次重复全域 assigned 权重为 4481，remaining 为 1444，exposed 为 3037。
- 默认 CLI 单独通过，输入与最终源码哈希记录在 `toy-small-defaults.cli.output.json`。

v2 的 .8 点门槛、NA、unknown、执行失败和低信息 CI 政策均未改动，没有加入 CI 下限、半宽或各域全部通过的验收门槛。解析协方差仍只作诊断 SE。joint16 只交付有限计数集合，严格非线性指标投影明确未实现；不声称跨视图或 45 指标联合覆盖。

真实项目统计执行、真实 ID 抽样、真人或 AI 新标签/预测读取、语料正文读取均为 0，没有安排人员。元数据、哈希及构造数据 PASS 不能认证真人、共同材料/手册、盲法、仲裁或真实方法表现；`formal_acceptance` 始终 false。

入口源码为 `metrics_engine.py`，详细接口和旧版对照见 `分域接口说明与旧版对照.md`，汇总见 `delivery-summary.json`，所有交付文件哈希见 `delivery-manifest.json`。复验脚本为 `verify_domain_engine.py`、两路独立脚本和 `verify_preservation.py`。
