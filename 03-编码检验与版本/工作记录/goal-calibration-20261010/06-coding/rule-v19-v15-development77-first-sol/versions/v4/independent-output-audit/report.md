# 独立输出完整性审计

本次逐项核验 77 条 predictions、385 个维度槽位；39671 个独立布尔检查中 39671 通过、0 失败。未读参照标签，未运行/import coder，未计算准确率。

run seal SHA256：`2d6318c7b5db190061259e73ee2023cc50ebd15cac84b539a00d34ab9beb205a`。唯一 source packet SHA256：`6c8623909a30566fd5348df3679f14c74cba1b86ccda5602b45707dd55fcb16a`，原始 input 2,565,289 bytes，77 ID 与冻结顺序逐一匹配。

seal member 逐个重算 132 个（implementation 10、material 113、control 1、output 8）；另核 pre-run 的 134 个 member 条目，含重复绑定。实际原始 input 行 byte 起止、行 SHA、bundle canonical SHA 逐行核验。

实际 read receipts 1404（text 751、geometry 642、document_bundle 11）；events 1463；use 143；request 0；requirements 1315；relation traces 41。

五字段 source quotes 71；普通 context exact quotes 62；结构 pointer uses 8；reference chain uses 2。全部核 pointer、原文半开区间、resource/source/view identity、read receipt。

producer/resolved inventories 各 898 个资源（逐记录累计）；可用 view 1494；身份 delta 3 个，逐一重核显式 SHA、snapshot/payload file hash、canonical payload 和只变动 source SHA。

权威生产证据 body spans 422、context spans 382；全 prediction 包含重复副本累计 body spans 844、context spans 764。

重新计数技术失败 0、null 0；保存的 launch/result/execution 共同记录一次执行、exit 0、无重试、stderr 空。

错误：

0 个检查错误。


局限：

- 这是标签已经披露后的 AI 开发回归输出完整性审计；没有计算或推断准确率，不构成正式盲验或真人独立验证。
- event/read/use 是本次程序保存的记录；本审计核验其原始 source/view/locator 与事件和凭据的一致性，不独立观察此前执行时刻的实际认知读取，也不认证语义适用性或编码正确性。
- 一次执行结论来自冻结控制、一次 launch 及 result/execution 记录的一致性；没有系统级进程审计，无法从这些文件证明不存在未记录的外部进程。
- source packet 及所有 seal member 原始 bytes/hash 均重算。外部依赖只作 opaque bytes/hash 检查；只有字面 textleaf snapshot 和 identity delta 的 source payload 作指定原文/身份比对。
- 图片文件 hash 的读取不等于像素解读；日志记录 image/pixel read 为 0。PDF/HTML 生产链的转写真实性没有重新渲染、OCR 或人工核验。
- Python 标准库路径按 driver 的明示 stdlib 契约分类，既有 stdlib pyc 不当作未绑定 source。
- body/context span occurrence 包含 predictions 中的 diagnostic copy 和重复 source_relation_traces；权威生产部分与重复部分分别计数，避免把复制证据当作新增证据。
- 71 个五字段 pointer 引用与 62 个 ordinary CTX 引用是使用记录计数，可能指向同一个物理证据；不是 133 个独立来源。8 个结构 pointer 与 2 个 chain 使用的完整核验路径、target hash、container/成员顺序及 read receipt 另存 structure-use-evidence.json。
- 初探 68 个诊断已保留原始脚本、ledger、报告与 seal 字节。6 类诊断由明示 schema 的序列化、locator 替代、双 CTX/derived 句柄、parent document id fallback、producer/resolved 分离与有界 role content 消解；判据及具体诊断见 schema-review.json。
- delivered output 是源 bundle 的重新序列化副本，其原始 bytes/SHA 与 input 文件不同；77 个对象与逐条 canonical SHA 完全一致，真正输入的原始 byte offset、行 SHA 及文件 SHA 已单独核验。


初次诊断的 schema 复核：

- 1 个 input：driver write_jsonl uses JSON reserialization; original input is separately bound by input line byte offsets, byte SHA and canonical bundle SHA. 静态契约 rule_driver.py:30。
- 2 个 relation：source_roles distinguish support-content from qualification-standard/heading evidence. For qualification support, content is only inherited_as_support_definition=true; postadmission content excludes programme_heading. Both exact role joins independently match. 静态契约 relations.py:691。
- 19 个 event_binding：FULLSOURCE scanner locator_read is {document_resource_id: inventory_id}, while inventory locator denotes payload representation; historical scanner reads the raw locator whereas inventory source_locator defaults to {}. Each alternative independently matches its exact raw payload schema. 静态契约 relations.py:245。
- 27 个 quote_bridge：A preserved raw CTX that also has a neutral source origin produces both raw CTX text use and origin document/text use. Ordinary CTX quote binds to its raw CTX receipt; five-field origin quote separately binds to source pointer and origin view. 静态契约 relations.py:268。
- 3 个 inventory：Top-level consumption inventory is original producer inventory, including 3 missing source SHA entries. uniform_source_reading_log.source_inventory contains separately verified identity resolution; deltas independently verified against raw payload, unique source document, snapshot and payload file. 静态契约 rule_driver.py:362。
- 16 个 quote：source_texts entries may omit per-text resource id. Their pointer still resolves exact text, with source_resource_id inherited from explicit parent source document; every declared id equals the exact parent document id and its origin inventory. 静态契约 source_packet.py:64。
