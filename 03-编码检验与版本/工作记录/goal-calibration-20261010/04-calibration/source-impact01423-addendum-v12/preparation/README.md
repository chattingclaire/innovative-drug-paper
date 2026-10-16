# 01423来源envelope准备件

材料版本为 `v12+bound_addendum1`。这是未来共同开发输入的准备层容器，尚未接入现有正式packet schema或规则读取器，不是正式协议freeze。后续共同包绑定由ROOT决定。

`material-envelope.json` 的两个显式来源成员为：

- `source_bundle`：原4-record-common-v12中01423的完整十根键对象，逐值保留；原当前完整表行、25个CTX、原图路径、SHA、合并关系和scope均原样保留。
- `bound_addendum`：已封存addendum的全部原值，包含第三条四款和第五条完整五款九段原文、原HTML定位、源SHA与原表JPG SHA。保留其原有独立对象的历史元数据，当前准备层取件方式由外层envelope_metadata说明。

所有角色默认取得整个envelope的相同原字节。直接读 `material-envelope.json`，或运行 `python3 read_material_envelope.py --role rule`；`model`、`human`均取得相同完整内容。CLI只是准备层读取器，不表示现有规则程序已支持该envelope。

阅读时保留两个来源成员各自的适用范围、原图定位与来源结构说明。补充段落属于同版原源已有、旧25CTX未完整投影的内容；收到资源不意味着整文件属性可自动继承。此准备件不提供五维建议。

`material-bindings.json`给出旧包、两个嵌套对象、九段、原来源、原图和共同手册v1.1的hash清单。嵌套对象值SHA采用UTF-8、ensure_ascii=False、键排序、紧凑JSON且无尾换行；输入文件SHA始终按原文件字节计算。`verification-ledger.json`仅记录九段逐字核查、十根键逐值保留和三角色实际CLI输出字节相等。原图在本次仅核文件SHA，未把字节读取声称为新看图事件。

既有v12/default、source_record/body、25CTX和首判均未修改；未重建canonical、改技术gate、建立新增测试体系或执行模型编码调用。
