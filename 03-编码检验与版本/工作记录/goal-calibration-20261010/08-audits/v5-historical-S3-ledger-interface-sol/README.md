本次仅只读检查已暴露的 RECODE25-00036、RECODE25-00038、RECODE25-00045。三条失败属于请求状态字段与旧接收协议的契约差异；未发现本次失败由来源缺失或算法 NULL 触发。没有执行恢复、协议重检或任何分类调用。

三条 source_requests 都只提供 dependency_status="resolved"，没有 status。冻结旧 source_reading_protocol_v12.py 第58–59行按缺失 status 默认 unresolved，返回唯一停止原因 missing_required_source，errors 均为空。全量入口 rule_driver.py 第370–373行再次按 status 识别未解决请求；此时 material_requests 为空，遂抛出“source dependency stop has no concrete stopped rule dependency”。这说明停止信号没有对应的真实停止依赖，不能反过来据此把已保存判读称作材料缺失或实质待定。

v5 relations.py 第763–769行保存两种关系：旧有限标准关系及带 SE_primary_literal_operational_standard 子类型的新受限关系。后者已有 affected_dimensions=[S,E,Ec]、同版 version_binding、实际闭合 proof 和当前操作锚点；dimensions.py 第887–894行允许受限消费者使用已核实的范围。三条完整 candidate_decisions_diagnostic_only 在来源接收检查之前已写入内存并在异常分支原样保存，其 S 观察值均为1，正式 retained labels/decisions 均仍为 NULL，ledger 仍标 technical_failure。其他四维只记录原观察值，未设预期或重审定义。

只读核验覆盖三份完整诊断、三份 raw request/log、三份 ledger 及相同内容的异常来源归档。共304处嵌套引文出现逐项核对原 CTX 或原件文字叶及 source_ref；这是重复出现的引文位置数量，不是304条不同政策。45个完整 read receipts 与49个 use receipts均匹配库存、run/record及实际源视图；原要求无缺读，source_identity_resolution_delta 均为空。三条包字节与冻结 native packet manifest、一致的原 bundle SHA均通过。五模块、手册、旧协议绑定均保持。

00036/00038标准组为原件字符[132,1181)，实际下一边界[1181,1187)“二、工作程序”，物理第18行。00045原组[2349,2718)，实质内容仅[2349,2647)，真实下一边界[2718,2724)“三、工作要求”，物理第36行；中间公开状态名单尾段用于闭合定位，不向维度捐入条件内容。proof中的当前原文、唯一当前跨度、原件SHA与边界引文均实际读回。材料和有限闭合仍需检查，resolved 状态不能替代这些检验。

建议首轮结束并完整封存后，另建一次机械接收复核版本。仅为 protocol 输入及停止依赖比对建立通用 canonical request bridge，不修改原 raw 请求、冻结旧协议或五模块，不再执行 source adapter / RelationView / judge。对白名单 dependency_status="resolved"或"stopped"明确映射 status；双键不一致、无状态、未知状态均拒绝 resolved。保留原始键、请求SHA、数组索引、映射规则与新投影SHA；必要依赖、维度范围、stop_reason、引文和其余字段原样保存。

随后按冻结原件和库存重核新投影 receipt，要求原机械条件、实际闭合、使用范围和全部引用仍满足。只可逐字承接首轮完整 candidate_decisions_diagnostic_only，原 NULL 不能填值，其他失败不能沿本原因抹除。新接收值和 receipt 必须单独绑定到原 prediction 原字节/行号、candidate decisions SHA、原 log/request SHA、原技术失败及首轮最终 seal；旧预测、ledger、技术失败、console和首轮汇总都不改。这里的数据充分性仅对已读三条成立，不外推整个4481。

现有失败记录没有完整 effective-semantic-unit 留存，因为入口只在接收成功后保存该对象；但完整原包、诊断决策、引用、来源关系、读用回执和闭合证明均已留存，且冻结控制流先通过 evidence.validate_decisions 再保存诊断并进入 receipt 检查。因此可用原字节机械回核三条，不需要重做语义推断。未来接收版本应另明确保存 evidence-validation 完成凭据、每项映射前后SHA与范围证明校验结果；本轮没有虚构旧凭据或修改旧文件。

observed-output-prefix-bindings.json 是读取时追加文件的字节前缀绑定，包含三条原始行号/字节位置/行SHA，不声称全量运行最终封存。selected-*.jsonl 是这三条记录的规范JSON副本，原始行字节SHA仍单列。first-inspection-attempt 保留首个只读提取器失败：它误认为 ledger 的首键是 id，实际首键是 index；修正仅适用于自有提取脚本，未改已有运行或代码。所有首个失败、候选原值和本次读回结果均保留。

身份为非真人AI接口检查；实际新真人、正式准确率、正式接收、标签恢复均为0。本目录 seal 排除自身。
