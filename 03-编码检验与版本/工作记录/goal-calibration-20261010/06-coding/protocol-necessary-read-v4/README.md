# Necessary-source gate v4

v4 修正 v3 在必要范围判断之前对全库存强制要求来源 SHA 的门槛。完整原库存及其 hash 不变，其中缺失的来源身份继续保留 None。未使用、未声明必要的可用项不会因身份缺失而阻断整条记录。

身份完整的视图才能进入 read/use 绑定索引。必要视图未绑定时，`required_read_complete` 必须为 false；必须记录具体来源请求并停止依赖维度，才能通过依赖处理检查。身份未齐的库存项不能用猜补的 SHA 产生有效 read 或 used 记录。原来完整视图的冲突身份、定位、实际读入收据与 used 条件保持原校验。

确实需要原全文或段落时，使用已有 `additional_views` 通用路径：从原对象取得真实 `source_resource_id` 和显式 `source_pdf_sha256` 等来源身份；完整对象使用 `document_bundle` / `canonical_json`，原文字叶使用 `text` / `utf8_text`；`scope_pointer` 和 locator 精确绑定原对象或文字叶，view SHA 使用对应原值。不能把库存生成的 FULLSOURCE 标识猜映射到原 SOURCE 对象，不能伪造原定位或来源 SHA。这个机械校验不证明语义必要性、实际阅读或使用。

这是两个小型运行覆盖模块。`necessary_read_gate.py` 按 `native-binding.json` 校验并复用封存 v3 的 packet builder 和 gate，仅替换库存视图索引门槛，增加未绑定身份的明确诊断。`native_records.py` 显式把继承的 native records 检查绑定到 v4 gate。所有文件变化只发生在此目录。

运行入口使用此目录的 gate/native_records，且应在独立 Python 进程中载入，避免混用之前缓存的同名模块。原 scope schema 仍为 v3，原 77 条提示、完整 packet、分批、v1.3 手册与预算全部 hash 绑定复用；不重造输入，也不增加初始提示内容。blank ledger 的外部执行协议标记为 v4，收据 schema 保持 v3。

诊断将原库存中身份未齐的视图计入可用和未读总数，并另列 `unbound_available_view_identities`，保留原 None 和缺失字段；`identity_bound_view_count` 单列可被收据绑定的视图数。缺失身份没有被改成零或替代值。

仅运行 8 项新增机械对照，覆盖三条已封存 Nil 库存未用、真实原对象额外视图允许，以及无绑定必要/使用、伪资源别名、伪定位和伪来源 SHA 的阻断。测试的阅读和使用字典是仅存在内存的合成 fixture，没有保存为真实收据，没有生成编码标签，也没有声明实际语义阅读。未重跑旧 13/19/167，未扫描全框，未调用 lookup 或编码模型。v3 的 35 文件和开发输入的 196 文件独立 opaque hash 保留核验均通过。
