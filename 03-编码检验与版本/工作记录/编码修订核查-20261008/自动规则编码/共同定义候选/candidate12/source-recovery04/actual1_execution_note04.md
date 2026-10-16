# 03894 材料04固定规则入口单次执行

以材料04规则输入第3894行 RECODE25-03894（original_id `b994cb6be5:u00024`），实际调用冻结的 `candidate12/attempt01/runtime/policy_coding_v27.py` 的 `code_unit(record, source_adapter=True, substantive_rules=True)` 一次。运行使用 bundled Python 3.12.14 与 pypdf 6.10.0，开启 `-B`。无异常，无语义重试。

`actual1.jsonl` 为一行原样返回封装：`{id, original_id, prediction}`。状态为 `rule_prediction`，`input_assessment_status` 为 `not_assessed`。未手工追加或修改返回标签；未载入其他行预测、人工标签或指标，未调用模型，未作统计或人工效度审读。

调用前已落盘 `preexecution_lock04.json`，锁定手册 SHA `5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c`、原 candidate12 freeze、全部51个固定代码文件、材料04输入及本行、实际 Python/pypdf 文件、实际源PDF及candidate。材料04规则输入 SHA `bab2da6586fade4a5fc6b188b3fee9cbfbf4099579b9205fee93639c3d7af960`。调用后 input、manual、freeze、全部51代码、源PDF与candidate字节均保持；没有修改原03/11/12全量运行文件。

真实返回的 `source_field_consumption_v34` 记载 `explicitly_cited_qualifications_v12` 已认证，消费11段，usage 为 `typed_reference_resolution_only`，`dimension_assignment=false`。1.3.8.7、1.3.9、1.8.3 三组分别为3、3、5段，`complete_interval_authenticated=true`；11段均为当前运行 `actual_source_literal_reproduced`，未依赖既有人工认证或伪造认证。实际三组 role 均为 `unclassified_explicit_reference_needs_relation_review`；来源已交付与认证，不等于当前语义接口已完成该关系的解释。

新增 `source_application_scope04` 的 p0001、p0002、p0003、p0018 四段未进入返回的命名字段消费日志或 typed contexts；51个冻结代码文件中也没有该字段引用。这里只核定新增字段的消费差异，不据此声称其他既有范围逻辑不存在或已认证。真实“二中药”heading仍在常规来源字段中；00064未解决状态未纳入本次操作。此次结果不构成全部效度通过的证据。

文件SHA：

- `actual1.jsonl`：`6bdea549d0786e5b6bdba3264fd2d5c315257336641906af9867c0da5c6d7642`
- `actual1.run.json`：`5483326cc802578c6918ec5388e77b3044a1999399a3981776f70ba315d22295`
- `actual_source_interface04.json`：`2531dc7bfd0ab91a5b50082596d6c65cacc4116490056790677f574284735ddb`
- `preexecution_lock04.json`：`211ac91469da32889e1265dea0b34b079b69da856aea2d9a33f81e08a036cee6`
- `run_actual1_source04.py`：`ebb6e4bc1625c3013ed921ec61053bae92403c00b157f5c04dab59a997ad97f5`
