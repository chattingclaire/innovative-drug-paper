# 关系解析副本的首轮有限修复

2026年10月14日。仅修改本试验目录`code/relations.py`，未改原规则文件、人工答案、保存机器标签或论文。维度判定文件由主agent独立负责。本次没有全量运行。

## 改动

1. **技术沟通申请与直接服务。** 既有`bounded_primary_postadmission_technical_support`增加当前明确允许提出/提交补充技术资料或方案反馈沟通申请的表达。仍要求同一具名程序、完整同源边界、纳入后阶段和具体技术内容，普通电话/视频/提交表单不成立。
2. **具名程序条件与待遇撤回。** 新增`cited_standard / bounded_named_conditions_withdrawal`，识别“不能满足某程序条件→终止该程序待遇”。只读取同源闭合程序的适用范围/条件至工作程序之前的完整范围，保留分支；不读整份文件的所有内容。
3. **当前优先资源配置。** 新增`named_mechanism / bounded_current_priority_resource`，只对当前明确为已纳入项目优先配置审评/核查资源的行动补足同版适用范围。不把普通通知、未实施或一般程序身份当作行动。
4. **专门团队执行职能。** 新增`named_mechanism / bounded_specialized_team_execution`。当前必须实际解决技术问题并按时限完成审评，同时有同源闭合组件中的创新研发范围、上市前阶段、单独序列/优先时限。纯行政文件处理、一般按期完成任务都不触发。
5. **按治疗需要适用的核查后置。** 新增`named_mechanism / bounded_need_linked_inspection_deferral`。当前明确允许上市审批后开展药品注册核查，同段明确临床急需且境外已上市境内未上市的药品对象，相邻同源一般程序明确审评期限前完成同一种注册核查。对象和基准保存连续原引文；注册检验不能代替注册核查。`content`只补对象，基准不自动继承成维度内容。

没有记录ID、人工标签查表或整句相等匹配。所有新增入口依赖当前动作、语义对象及来源结构证据。宽度限定的正则仍有覆盖局限，本轮不追求把所有分歧改为1。

## 与dimensions.py的接口

- 技术沟通复用现有subtype和`current_service_anchor`。主agent须将实际技术申请机会作为该路径的action，与仅沟通形式区分。
- 团队：`object_definition`、`research_stage`、`direct_mechanism`为原文字符串；`current_execution_anchor`为连续原文锚点；`scope_binding`为字典，含`source_sha256`、`boundary_context_id`、`context_ids`列表、组件起止段号；`version_binding.established=true`。只在上述证据齐备时消费I3。
- 核查后置：`object_definition`为同段对象原文；`object_scope_quote`和`baseline_before_review_quote`为完整证据字典；`current_deferral_anchor`为当前原文锚点；`scope_binding.context_ids`记录对象与基准两处，另有同源SHA和`inspection_kind='药品注册核查'`。F应走该明确关系的直接路径，不能仅靠扩大机会关键词。

## 验证

`relations_tests.py`执行9条原保存输入的确定性重放、15项构造边界反例。它只写本试验目录的`relations-tests.json`；不是新的独立检验，不回填旧成绩。

实际来源的关系结果：

|记录|新增或保留的关系|本次局部运行标签|
|---|---|---|
|00125|当前优先资源与同程序对象|I=1，F=1|
|00133|纳入后具体技术沟通申请|I=1，F=1|
|00141|具名条件不满足与待遇撤回|I=1，F=1；未自行扩展未核明的安全/效果条件|
|04197|专门团队执行审评技术职能|I=1，F=0|
|00132|急需药对象、审批后核查及同源审批前核查基准|关系已生成；局部运行时F直接消费者尚未接入，标签仍0，由主agent统合后重放|
|00038、00118、00138、04162|原77条成功对照|原成功I/F判断保留|

9条实际重放全部通过`evidence.validate_decisions`。15项构造反例均通过：只有沟通形式、提交申请表、申报前服务、身份/状态而无待遇撤回、行政团队、无具体技术执行、仅通知优先结果、未实施优先、普通上市后检查、注册检验、缺失核查基准、检验替代核查基准、基准跨来源、团队无闭合范围。这些反例只检查新增关系边界，不证明所有现存规则没有误判。

`relations.diff`保存与原版的完整差异。原版`relations.py`SHA-256保持`75fc214094e81c57aa56c5dc93c0dd950d5199b12c4e4f1a92924c9151d79161`，原始全量预测文件未修改。主agent可在统合维度消费者后运行77+200回归，再决定是否需要继续修复；本子任务已停改。
