# 36条迁移前冻结审计

本审计仅为AI开发执行边界检查；未读取36条reference.jsonl或coverage01标签/管理诊断正文，未执行分类，也未生成任何预标签。

旧41条implementation-bindings.json所绑定81份文件逐项SHA与字节数全部一致。第二、三版独立复算记录均为independent_arithmetic_crosscheck_passed；旧第一版记录仍保留。新复算文件位于root-machine-review，未修改旧交付文件。

|旧implementation03模块|SHA256|字节|
|---|---|---:|
|source_packet.py|b3f1de391684c1b417b39fbf1c0c1ede890306e0a7bc60a14381c986ef776b7b|17631|
|evidence.py|5ce0fc8c39862edbcab837c0b1fdc7f5c605758f34fbf0ab34487a0b4531cdb3|10486|
|relations.py|193b2f9b60b5313d1906003b702a6663ed00b04bf2b61ee83a1de25b529d0ffb|26171|
|dimensions.py|d9d045745f2df2ebb7053972749d320ed71e5136442ed30c116a76af45c8e3ff|45256|
|runner.py|b5b232b8aa2e75264337e06ef5dde1e35e7bee83d111ce105226d24a72891943|12585|

36条来源SHA与授权值一致；共同manual.md仍为v1.1原哈希。schema检查只汇总结构及附件元数据：36条、172 CTX，其中158个含text字段；PDF页附件21处，原JPG附件1处；manifest共20个source-pages文件，全部实际SHA一致。此处仅作文件绑定检查，未将图像内容转换成规则或声称实质图像认证。

旧运行器在coder导入前冻结，动态执行已核SHA源码；读取守卫明确拒绝reference.jsonl。旧运行器scope固定41，资产allowlist仅PNG；旧reader顶层没有source_image_attachments，因此36条副本需要通用数量、路径、原JPG附件接口适配。原JPG应保留mime_type、source_url、attachment_id、relative_path、sha256，不能借PDF物理页或source_pdf_sha256冒充其身份。

已读取旧source_packet.py、evidence.py、relations.py、dimensions.py、runner.py及原报告、绑定和复算记录。关系与维度代码无来源I/O；semantic_unit去除管理ID，保留原文和上下文结构；图像附件未被旧判断代码使用为语义特征。

后续验收边界：coverage36副本的evidence.py、relations.py、dimensions.py应逐字节等于上述原文件；source_packet.py仅允许来源形状验证/无损传递；runner.py仅允许范围、路径/版本、数量、合法原资产及故障保全接口适配。未经首轮prediction seal，不得加入任何本36条的语义规则变更。

逐项哈希、三份外部复算绑定、20个资产核对及原JPG字段见pre-adaptation-baseline.json。
