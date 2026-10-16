# 36条首轮前范围与接口适配审查

审查通过。允许在当前五份文件哈希下运行首轮36条、180项并封存；此次许可只确认固定implementation03实质关系与各维判断未变，以及来源接口适配，不能作为语义正确性或正式效度结论。

|coverage36模块|SHA256|与旧03的关系|
|---|---|---|
|source_packet.py|d4d21497a4e926d8db146800a2de3a7ea083597d2390a9afb81a53983474a8ea|纯范围/来源接口适配|
|evidence.py|5ce0fc8c39862edbcab837c0b1fdc7f5c605758f34fbf0ab34487a0b4531cdb3|逐字节一致|
|relations.py|193b2f9b60b5313d1906003b702a6663ed00b04bf2b61ee83a1de25b529d0ffb|逐字节一致|
|dimensions.py|d9d045745f2df2ebb7053972749d320ed71e5136442ed30c116a76af45c8e3ff|逐字节一致|
|runner.py|8300902a1796930ef6911a3e559bf20560684ada52888354ddd86552d0121761|纯范围/来源接口适配|

运行器仅变版本标识、36条范围、180槽故障诊断说明和共同fixture内原PNG/JPG/JPEG资产允许读取。原冻结、字节执行、reference.jsonl拒读、五维判断调用及全失败保全逻辑保持原样。

reader仅扩展原source_image_attachments独立字段、原JPG MIME/URL/SHA、两种原始context kind、定位/物理合并单元格元数据，以及row_cell_column_pairs两种严格原shape。它不新增原文、OCR、CTX映射、关系角色、语义权限或标签。源JPG未删除、未伪装为PDF页；图像原意义继续只由共同同版来源文字结构承载。

reader报告实际36条/172CTX加载成功，返回对象与原parsed JSON序列化逐字节一致，20项通用接口测试通过；我核实报告所绑定最终reader哈希、source/manual/manifest哈希，独立核对manifest20个资产哈希并审阅完整最终diff。此审计未重复运行分类或进行图像语义认证。

原reader实测失败、适配01/02失败及代码快照全部保留。旧implementation03五文件、旧81份交付物及三份arithmetic-crosscheck记录均保持原哈希；prior41-final-delivery-seal.json绑定核对通过。

审计在run01目录创建前写成；没有读取reference36/reference.jsonl或coverage01标签/管理诊断正文，没有查看首轮预测或做预标签。完整结构、函数差异、失败留档和哈希绑定见scope-adaptation-review.json。
