# 独立输出完整性审计

本次逐项核验 77 条 predictions、385 个维度槽位；39604 个独立布尔检查中 39536 通过、68 失败。未读参照标签，未运行/import coder，未计算准确率。

run seal SHA256：`2d6318c7b5db190061259e73ee2023cc50ebd15cac84b539a00d34ab9beb205a`。唯一 source packet SHA256：`6c8623909a30566fd5348df3679f14c74cba1b86ccda5602b45707dd55fcb16a`，原始 input 2,565,289 bytes，77 ID 与冻结顺序逐一匹配。

seal member 逐个重算 132 个（implementation 10、material 113、control 1、output 8）；另核 pre-run 的 134 个 member 条目，含重复绑定。实际原始 input 行 byte 起止、行 SHA、bundle canonical SHA 逐行核验。

实际 read receipts 1404（text 751、geometry 642、document_bundle 11）；events 1463；use 143；request 0；requirements 1315；relation traces 41。

五字段 source quotes 71；普通 context exact quotes 62；结构 pointer uses 8；reference chain uses 2。全部核 pointer、原文半开区间、resource/source/view identity、read receipt。

producer/resolved inventories 各 898 个资源（逐记录累计）；可用 view 1494；身份 delta 3 个，逐一重核显式 SHA、snapshot/payload file hash、canonical payload 和只变动 source SHA。

权威生产证据 body spans 422、context spans 382；全 prediction 包含重复副本累计 body spans 844、context spans 764。

重新计数技术失败 0、null 0；保存的 launch/result/execution 共同记录一次执行、exit 0、无重试、stderr 空。

错误：

- {"category": "input", "key": "delivered_raw_bytes_exact_original", "passed": false}
- {"category": "relation", "key": "RECODE25-00045/trace/1/content_exact_selected_evidence", "passed": false}
- {"category": "event_binding", "key": "RECODE25-00887/98/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-00891/97/locator", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00891/trace/1/CTX-SRCRENEW-7451406ddc9c2e433f86", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00891/trace/2/CTX-SRCRENEW-7451406ddc9c2e433f86", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00891/trace/2/CTX-SRCRENEW-5c1535630e5078d29e87", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00891/trace/2/CTX-SRCRENEW-883f09dd034cf8a543c8", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00891/trace/2/CTX-SRCRENEW-bf1652c287cb647e50d9", "passed": false}
- {"category": "event_binding", "key": "RECODE25-00900/116/locator", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/1/CTX-SRCRENEW-cc80e7e3b94171ceecbf", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/1/CTX-SRCRENEW-224f499a4979865d3701", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/1/CTX-SRCRENEW-4a3e3bc4efd03efbb6ba", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/1/CTX-SRCRENEW-56fe2e17cafd32891a72", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/1/CTX-SRCRENEW-e2722fb2ac3883021894", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/1/CTX-SRCRENEW-5bebdda8ec8f2f9b2109", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/1/CTX-SRCRENEW-d3857139ed7ae46f0479", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/1/CTX-SRCRENEW-d98366e2f09c996b18f8", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/2/CTX-SRCRENEW-45042c298e5ca2337473", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/2/CTX-SRCRENEW-f4b4ff3b62e46d258d96", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00900/trace/2/CTX-SRCRENEW-7547b0c859b93e2d06d8", "passed": false}
- {"category": "event_binding", "key": "RECODE25-00902/93/locator", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/1/CTX-SRCRENEW-0278939820179e2ef7d2", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/1/CTX-SRCRENEW-2c68ac9aeedf985dfd43", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/1/CTX-SRCRENEW-37aefc9ded7f31c31434", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/1/CTX-SRCRENEW-ebf39d1803f37cc9b2b9", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/1/CTX-SRCRENEW-93d3bacfa65fd169ba39", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/1/CTX-SRCRENEW-184e8631b6493fa89faa", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/1/CTX-SRCRENEW-1ddcec8d17b8f7515014", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/1/CTX-SRCRENEW-deba2a4f88a56eca8ec7", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/2/CTX-SRCRENEW-9ce263a63c901ed60be6", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/2/CTX-SRCRENEW-f3b69344d205a8826d50", "passed": false}
- {"category": "quote_bridge", "key": "RECODE25-00902/trace/2/CTX-SRCRENEW-74d9d4cfd5ddf03dc451", "passed": false}
- {"category": "inventory", "key": "RECODE25-01459/top_inventory_resolved", "passed": false}
- {"category": "event_binding", "key": "RECODE25-01459/68/locator", "passed": false}
- {"category": "inventory", "key": "RECODE25-01464/top_inventory_resolved", "passed": false}
- {"category": "event_binding", "key": "RECODE25-01464/15/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-01729/6/locator", "passed": false}
- {"category": "quote", "key": "RECODE25-01729/trace/0/quote/40/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-01729/trace/0/quote/41/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-01729/trace/0/quote/42/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-01729/trace/0/quote/43/raw_pointer_target", "passed": false}
- {"category": "event_binding", "key": "RECODE25-02233/4/locator", "passed": false}
- {"category": "quote", "key": "RECODE25-02233/trace/0/quote/44/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-02233/trace/0/quote/45/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-02233/trace/0/quote/46/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-02233/trace/0/quote/47/raw_pointer_target", "passed": false}
- {"category": "event_binding", "key": "RECODE25-02269/6/locator", "passed": false}
- {"category": "quote", "key": "RECODE25-02269/trace/0/quote/48/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-02269/trace/0/quote/49/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-02269/trace/0/quote/50/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-02269/trace/0/quote/51/raw_pointer_target", "passed": false}
- {"category": "event_binding", "key": "RECODE25-03704/7/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-03767/7/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-03876/3/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-04915/8/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-04915/9/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-04915/10/locator", "passed": false}
- {"category": "quote", "key": "RECODE25-04915/trace/0/quote/54/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-04915/trace/0/quote/55/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-04915/trace/0/quote/58/raw_pointer_target", "passed": false}
- {"category": "quote", "key": "RECODE25-04915/trace/0/quote/59/raw_pointer_target", "passed": false}
- {"category": "relation", "key": "RECODE25-00138/trace/0/content_exact_selected_evidence", "passed": false}
- {"category": "event_binding", "key": "RECODE25-00859/98/locator", "passed": false}
- {"category": "inventory", "key": "RECODE25-01480/top_inventory_resolved", "passed": false}
- {"category": "event_binding", "key": "RECODE25-01480/7/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-03800/7/locator", "passed": false}
- {"category": "event_binding", "key": "RECODE25-03818/14/locator", "passed": false}

局限：

- 这是标签已经披露后的 AI 开发回归输出完整性审计；没有计算或推断准确率，不构成正式盲验或真人独立验证。
- event/read/use 是本次程序保存的记录；本审计核验其原始 source/view/locator 与事件和凭据的一致性，不独立观察此前执行时刻的实际认知读取，也不认证语义适用性或编码正确性。
- 一次执行结论来自冻结控制、一次 launch 及 result/execution 记录的一致性；没有系统级进程审计，无法从这些文件证明不存在未记录的外部进程。
- source packet 及所有 seal member 原始 bytes/hash 均重算。外部依赖只作 opaque bytes/hash 检查；只有字面 textleaf snapshot 和 identity delta 的 source payload 作指定原文/身份比对。
- 图片文件 hash 的读取不等于像素解读；日志记录 image/pixel read 为 0。PDF/HTML 生产链的转写真实性没有重新渲染、OCR 或人工核验。
- Python 标准库路径按 driver 的明示 stdlib 契约分类，既有 stdlib pyc 不当作未绑定 source。
- body/context span occurrence 包含 predictions 中的 diagnostic copy 和重复 source_relation_traces；权威生产部分与重复部分分别计数，避免把复制证据当作新增证据。
