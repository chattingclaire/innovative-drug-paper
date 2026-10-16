# 年度输入绑定准备

已将已验收的51个来源条目年度元数据按原框 source_id 一对一连接到4481条款，并按既有抽样管理契约抽出同一800条款。4481及800的 policy_year 均为实际整数，没有主年度缺失；component_id 仍全部为 null。51条目下列示56组件，尚无验收的逐条组件归属与独立组件日期，不能把51条目称为56独立文件，不能启动组件或月/日窗口分析。

主方案沿用成文日期优先、缺成文日期时原公开日期回退（48条目成文日期、3条目回退）。公开年度方案直接沿用原公开日期。两者在51条目/4481条款的日期分组一致；本次没有标签结果，不能称为标签稳健性。年份均来自已验收日期字段，没有从文件名、ID、effective_date或标签推年。source_entry_id、来源身份SHA、成文/公开日期证据SHA均保留。证据SHA继承自已验收管理元数据，本次不打开其指向的日期来源文件。

`full4481-year-map.jsonl` 保存完整年度映射；`full800-year-map.jsonl` 保留800原框顺序及原层、部门、域、N_h、n_h、pi、weight；`engine-records-full800.jsonl` 仅含引擎允许的 unit_id/stratum_id/department/policy_year 四列。source_id→unit_id、stratum→stratum_id 是明确管理字段适配。原800抽样已存在，本次没有重抽，seed20261010、41层、remaining600/exposed200、部门NMPA384/NHSA340/NHC76均沿用；年度不是新抽样层。

`source-entry-date-evidence.jsonl` 保存51条目的继承证据与SHA；`source-year-binding-descriptor.json` 绑定真实全量映射、原800管理数据、日期证据、修复候选路径/SHA和未完成组件边界。其 no_source_views 只从全4481已验收 inventory 派生：2017全局及9个空部门×年度。含义是所收集文本中没有纳入来源，不是全部政策的穷尽缺失；没有从800空样本推无来源。

`prepare-input-management-only.json` 是结构检查输入。它采用引擎既有 historical_arithmetic 角色，因为真实方法封存尚不存在；该角色在这里仅用于管理字段检查，不表示实际历史统计，也不表示正式项目提交。记录没有 outputs 字段。实际只调用修复候选的 prepare 一次，内部对缺outputs临时创建的状态数组丢弃，不写成标签、执行失败或研究证据。未调用 analyze、analysis_scopes、复抽或任何年度指标计算。prepare 成功只证明提交的管理结构和原设计匹配；无源声明的管理含义由本次按全量元数据核对，没有声称通过 analysis_scopes 的语义检查。

metadata.year_mapping.frozen_before_labels=true 的范围限定为年度来源字段独立于标签且在未来正式标签结果前封存；不声称早于历史全部开发标签。修复引擎原件及原审计交付保持只读；ROOT在独立新接收记录中决定采用，不修改旧candidate标头或旧contract。

`future-formal-input-references.template.json` 是未填引用模板。A/B/reference/rule/LLM实际提交路径、SHA、标签投影SHA、真人身份、共同材料/手册与执行冻结证明均未填；所有方法 sealed=false，实际 ledger 引用为空。本模板尚不能作为 sealed_project 执行。未来需用真实接收标签和可信执行证据填引用，按同一 unit_id 加入管理四列；本次不写假标签、假SHA、假发布、假身份。

`selected800-year-projection.json` 保存无标签年度投影；引擎校验的是规范化JSON投影SHA（见readback），并非该美化JSON文件的字节SHA。`readback.json`记录有限核对、一次prepare、0次analyze、0个标签及旧输入SHA不变。`seal.json`封存本目录所有交付与允许读取的原管理依据，排除seal自身防止递归。执行使用Python -B并禁写字节码缓存。没有修改旧文件，没有读取政策正文、A/B/reference具体内容、机器标签、开发77结果或盲包内容，没有执行新正式检验，没有计算全年标签统计或派生结论。
