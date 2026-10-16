已补齐 25 份同型 I/F 专项锚点的公共原文表示。以既有 F 单字段补丁 d4063ee7…（75605 B）为基准，新增一个本文件内 /$defs/common_public_source_quote，并在其余 24 个位置加入该定义的 $ref alternative；原 F.fairness_relation inline 分支完整保留。定义与原 source-quote.schema.json 的 JSON 结构逐字 deep-equal，仍是 exact 五字段 source_id/source_bundle_sha256/bundle_pointer/quote/span。

新 output-item.schema.json：88623 UTF8 file B，SHA 3b361770b6a708d3d5568cf39bfd15e5883743697ceedccffb008a1632ade3c7。相对基准增加 13018 B；文件 byte SHA 与 definition canonical SHA 分别记录，不混称。

| 五类逻辑字段 | 允许公共原文补足的有限内容 |
|---|---|
| innovation_support.rd_object | 当前同一安排的创新/实质改良研发对象、适用条件 |
| innovation_support.available_support | 当前确指可用安排的定义、直接资源/反馈/便利机会 |
| fairness_specific.patient_drug_object | 当前承接的患者药品获取、持续治疗或可负担对象 |
| fairness_specific.fairness_relation | 对应同一当前措施的公平/治疗需要/保障缺口关系 |
| fairness_specific.arrangement_or_evaluation | 当前确指安排或评价的直接内容 |

手册 v1.3 第44、46行的同版同一安排有限确指规则、I3第116/119行的对象—当前可用安排—直接关系、具体F第141/145/150/160行的对象与公平关系仍适用。公共定义只能补足当前承接，不能凭公共指南制造支持行动、借宗旨或兄弟项继承标签。25位置在 S/E/Ec/I/F 各 evidence 下是同一专项字段的复制；没有新增“非 canonical 组必须 null”的语义规则。

实际修改的 24 个精确 schema JSON Pointers（diff-report.json 另保存每个旧/新 subtree SHA、exact replace 与理由）：

- /properties/evidence/properties/S/properties/innovation_support/anyOf/1/properties/rd_object
- /properties/evidence/properties/S/properties/innovation_support/anyOf/1/properties/available_support
- /properties/evidence/properties/S/properties/fairness_specific/anyOf/1/properties/patient_drug_object
- /properties/evidence/properties/S/properties/fairness_specific/anyOf/1/properties/fairness_relation
- /properties/evidence/properties/S/properties/fairness_specific/anyOf/1/properties/arrangement_or_evaluation
- /properties/evidence/properties/E/properties/innovation_support/anyOf/1/properties/rd_object
- /properties/evidence/properties/E/properties/innovation_support/anyOf/1/properties/available_support
- /properties/evidence/properties/E/properties/fairness_specific/anyOf/1/properties/patient_drug_object
- /properties/evidence/properties/E/properties/fairness_specific/anyOf/1/properties/fairness_relation
- /properties/evidence/properties/E/properties/fairness_specific/anyOf/1/properties/arrangement_or_evaluation
- /properties/evidence/properties/Ec/properties/innovation_support/anyOf/1/properties/rd_object
- /properties/evidence/properties/Ec/properties/innovation_support/anyOf/1/properties/available_support
- /properties/evidence/properties/Ec/properties/fairness_specific/anyOf/1/properties/patient_drug_object
- /properties/evidence/properties/Ec/properties/fairness_specific/anyOf/1/properties/fairness_relation
- /properties/evidence/properties/Ec/properties/fairness_specific/anyOf/1/properties/arrangement_or_evaluation
- /properties/evidence/properties/I/properties/innovation_support/anyOf/1/properties/rd_object
- /properties/evidence/properties/I/properties/innovation_support/anyOf/1/properties/available_support
- /properties/evidence/properties/I/properties/fairness_specific/anyOf/1/properties/patient_drug_object
- /properties/evidence/properties/I/properties/fairness_specific/anyOf/1/properties/fairness_relation
- /properties/evidence/properties/I/properties/fairness_specific/anyOf/1/properties/arrangement_or_evaluation
- /properties/evidence/properties/F/properties/innovation_support/anyOf/1/properties/rd_object
- /properties/evidence/properties/F/properties/innovation_support/anyOf/1/properties/available_support
- /properties/evidence/properties/F/properties/fairness_specific/anyOf/1/properties/patient_drug_object
- /properties/evidence/properties/F/properties/fairness_specific/anyOf/1/properties/arrangement_or_evaluation

新增定义 diff 是 /$defs，内部唯一 key common_public_source_quote。保持原样的第25个位置为 /properties/evidence/properties/F/properties/fairness_specific/anyOf/1/properties/fairness_relation。将24分支与定义 addition 精确逆向还原，结果与基准 deep-equal；所有旧 current/context 子树、必填/null/枚举/路径及其他字段均保持。

没有 public alternative 的字段仍有原义：direct_relation 是关系说明字符串；relation_type 是原三类别枚举；current_quote/current_span 必须锚定完整当前正文；contexts_used 保持原CTX身份。labels、paths、reason、material_requests、图像/结构使用和其他字符串/锚点均不作放开。

有限验证共18个字段格式例，明确是人工构造 shape fixture，没有实际记录、scope/read/use 或标签声明：覆盖5逻辑位置的公共分支，current/context保留、一份非canonical复制位置一致性；坏pointer形状、错误quote类型、缺quote、额外字段失败；I3 direct_relation/F relation_type必填仍失败；公共对象不能替代说明字符串、枚举、当前正文或CTX条目。原既有 full-item schema_check 直接支持共享定义，无新兼容层。合法形状但不存在的实际pointer仍由原 verify_source_quote 拒绝，schema接受形状不冒称原文真实性。

只读 b5 历史两首件的 representation check：04915 基准/新schema均通过，00138 基准失败/新schema通过；原三个已有公共锚点沿原packet pointer/span机械验真通过。两个原文件 SHA/bytes 未变，不保存改写first、不新判标签、不创建阅读收据，不把字段表示兼容当成语义正确或完整batch成功。旧 batch5 material3/3仍 technical_representation_failed、saved2/expected10、剩8未处理；b1/b2/b5不会因本格式补齐重跑或追加 attempt04。

未来执行须由新独立材料/完整任务契约真实绑定本 schema 路径、SHA和字节；沿原source-quote侧文件和quote-index把首件具体字段关联原pointer及实际同view read/use，嵌套锚点及侧文件均调用原schema/verifier，不由侧文件绕过必填含义。format-binding.json只声明未来格式替换，未修改旧runtime绑定、source/manual/gate/首件/失败/seal。没有生成R0/fullR/bootstrap、新来源材料或执行框架，也不宣称正式方案或检验已完成。

模型、聊天、新材料尝试、原gate/来源大套件调用均0。有限完成并停止。
