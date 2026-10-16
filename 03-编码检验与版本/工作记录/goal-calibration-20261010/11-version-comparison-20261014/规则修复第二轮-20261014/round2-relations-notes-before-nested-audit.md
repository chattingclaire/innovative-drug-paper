# 第二轮关系解析修复说明

本轮只改第二轮副本 `code/relations.py`；未改第一轮或生产源码、任何人工答案、保存的机器结果和论文。未调用模型，未运行全量。此处是实现检验，不是新一批独立效度检验。

## 已修复的关系

|当前动作|关系补足及边界|局部保存输入结果|
|---|---|---|
|00113：专家论证是否符合优先程序纳入条件|当前实际资格论证→唯一同版具名程序→完整适用范围和条件。不是只读标题，不把申报前沟通当纳入后服务。|S/E/Ec=0，I/F=1|
|00123：经论证不符合纳入条件应终止程序|条件分支→完整同版资格条件。与逾期未提交说明的纯手续分支分开；未声称所有条件都失败。只消解前置解析器对此确指条件发出的那一个缺材请求。|S/E/Ec=0，I/F=1；原确指条件 NULL 请求解除|
|00120：公示无异议即纳入程序|当前实际授予程序待遇→同版该程序具体技术反馈及优先沟通机会。已纳入的身份状态、拟纳入、公示标题不触发。|S/E/Ec=0，I/F=1|
|00127：技术审评中优先安排沟通|当前明确优先沟通→同一技术审评组件内的纳入对象谓词。跨组件、一般安排、申报前沟通不能借此关系。|S/E/Ec=0，I/F=1|
|00134：沟通确认后实际提交技术资料且审评时限不延长|当前确认与提交→同源同段前句明确的纳入后技术反馈申请。需该段关系及有界程序同时成立。|S/E/Ec=0，I/F=1|
|00129：需要注册核查时通知核查中心组织核查|当前实际组织核查→同一工作组件内明文“应优先进行核查”的治理句→同程序适用对象。一般期限、检验通知单或仅记录核查不单独触发。|S/E/Ec=0，I/F=1|

## 接口

- 新 `bounded_current_eligibility_assessment` 属于原 `cited_standard` 类型，维度解析沿原完整标准路径。保留完整标准引文、当前条件/动作锚点、同源程序及工作组件边界。
- 复用 `bounded_primary_postadmission_technical_support`。新增 `current_service_mode`：`priority_technical_communication`、`confirmed_technical_submission`、`programme_admission`；原明确纳入后服务为 `explicit_postadmission_technical_service`。其消费由主 agent 在 dimensions.py 接入。
- 新模式均保留 `scope_binding.context_ids`、同源 SHA、当前与组件的原件坐标、治理组件连续原文引文；治理引文同时加入 context_evidence。用于界定归属的组件原文不自动进入继承文本；继承仍限定对象和与当前待遇相连的机制。
- 核查执行复用 `bounded_current_priority_resource`，并存 `scope_binding.execution_kind=actual_organization_of_priority_registration_inspection` 和当前执行锚点。
- `_closed_programme_for_current_action` 仅负责找到唯一同源原件边界，调用前必须先出现当前实质动作；标题本身不输出标签。

## 有限测试

- 15 条保存输入重放：本轮 6 条与第一轮 9 条，均通过字面原文及输出证据校验。
- 6 个等长同义改写：论证动作、无异议表述、强制终止表述、优先沟通动作、初步审核、按规定提交。明确为内存构造测试，给以独立 synthetic source SHA；不是政策原文，也不写回原材料。
- 13 个反例：6 个近邻动作替换（仅记载资格、已纳入状态、只有文书缺失、一般沟通、只记录核查、未经确认提交），6 个缺少完整原件的来源边界，以及缺少同段前件的确认后提交；目标新关系均不触发。
- 没有读取人工答案来生成分类逻辑，无编号或整句查表；测试文件中的编号只定位固定输入。
- 已核对保存输入文件 SHA 运行前后相同。

结果文件：`round2-relations-tests.json`；可复现脚本：`round2_relations_tests.py`；相对第一轮 diff：`round2-relations.diff`。

源码已冻结，留待主 agent 对 77+200 统一回归。本轮不是强求指标达标的进一步循环；其余分歧应先在回归后区分材料、实现与实质判读。

第二轮 relations.py SHA256：`2399e18b417e74a3fec9b46deef2cc7bf91590b1165ca8f9b4df7645fbbf8328`
第一轮 relations.py SHA256：`2035d918fa03f067a2cdfd1665767e8bdb099eba2a84041337cd62adfa310a31`
