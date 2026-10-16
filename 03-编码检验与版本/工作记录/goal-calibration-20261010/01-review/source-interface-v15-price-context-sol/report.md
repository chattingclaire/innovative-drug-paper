# v15 源材料机械投影报告

封存完成：原 PDF 物理页 8/9/20/21 的完整抽取文本公共可见。四页逐字、逐 UTF-8 byte 与原补材块一致，包括 formfeed；原 PDF bytes 未变。

源接口以 exact SHA/bytes 绑定原 v14 accessor，采用旧 FULLSOURCE payload + paragraphs 结构。新增 payload canonical SHA：`826591b6766f63e9d0ec85c2a58982a0459675b9dc398c343ddebec7ced9fb9e`；inventory ID：`FULLSOURCE-826591b6766f63e9d0ec`。源文档 metadata 中 relative_path 以旧 v12_source_base 解析，且处于共同 exact material whitelist 中。

4481 束机械投影：同源 224 束改变，4257 束不变；原 body/context/页码/单位/order/source assets 及 base bundle identity 精确保留。77 束维持固定顺序，其中 5 束新增公共资源；13 个历史 native assignment 组保持 source-ID 顺序。两个机器输入指向同一个新 source JSONL 与 77 个相同的 bundle SHA。

新增材料可用不等于实际机器已读。4481 遍历是机械投影，不是编码。本交付没有执行任何真实 inference，没有产生 actual reading/use receipt，也未创建 actual run scope。

source-only-QA-v15.json 记录 77 个 packet/source schema、adapter 与 FULLSOURCE identity 检查；common-material-bindings-v15.json 保留旧 v18 原 13 material entries 并绑定新 PDF/payload/wrapper/77 source。development77/packet.schema.v15.json 只扩展 nested v15 source extension 的容许形状，旧 schema/source/packet 文件只读。
