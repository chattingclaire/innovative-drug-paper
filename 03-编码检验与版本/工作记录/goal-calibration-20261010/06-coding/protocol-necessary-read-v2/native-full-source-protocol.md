# 原生完整来源协议：必要读取另版 v2

本目录仅修正 v1 把全部可用公共全文与所有图资产变为无条件必读的门槛。v1 的 03e4579fadf6ed04ef437f89f1689e3ca67aa2871fd419b338fc1d99e1703767 封存不变；B4 首判与其读取记录也不回写。没有选择新样本、运行模型、冻结实际批次、比较或改变共同手册。手册 v1.1 原字节 SHA 为 6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f。

原完整十根键 source bundle、原字段/值、公共全文、CTX、geometry、源角色、确指和 unknown 状态均逐值保留，原 packet/schema/profile、资产可访问性与 hash 检查沿用 v1。全 bundle canonical SHA 仍是输出 content_sha256。全部可用源资产仍按 v1 保守预算计入分组，41 条只是上限。此处只有限另版修改读取义务；不减小预算、不丢资源、不变顺序。

统一读取义务按已封存的 source-reading-protocol-v12.md/json。完整包交付与文件 SHA 核对并不证明实际语义阅读每份全文；完整库存不代表全部资源必要。先完整读当前/body 与原 CTX 关系、角色和边界，完成有原源依据的 scope review，再声明有限的必要同版确指、条件/例外、geometry、原图 closure。必要性不能由预期标签、分数或难度决定。其他可用资源可以未读、未用；已读也可以未用。索引只交付完整文件定位，不替代必要视图的阅读。

`necessary_read_gate.py prepare_scope(packet, run_id, reader)` 只构造完整库存与当前/body/CTX 机械基础要求，scope review 初值 pending，阅读/使用/请求为空；不调用 owner.lookup、不读新源正文、不推定阅读。库存来自 owner 封存的纯 source_inventory 函数。操作者根据真实源结构完成 note/anchors，补入必要视图与确指记录。公共资源可按原 bundle JSON Pointer 声明有限同版子视图；原包没有删节。新增视图严格绑定原资源 ID、source SHA、视图类型、原 pointer 和该完整子视图 SHA。

`check_scope` 的规则如下：

- scope review 必须 complete，且有原源定位与独立的结构说明。基础当前/body/CTX 的 resource/view/locator 不得删改；追加 requirement 的必要性依据须指向原包，机械校验不证明解释正确。
- 完整 recorded 阅读须同 resource、source SHA、view、view SHA、scope pointer 和原 locator，有当前 reader/run/record、工具及真实或本地事件 ID。文字阅读不能覆盖 image；父文档的读取声明不自动覆盖子视图。范围更小时应声明原 pointer 子视图或保留 partial，不能声称整个视图 complete。
- used 必须指向同资源同视图完整且 recorded 的实际 read_receipt；不可依靠另一个 resource、文字收据或生产者已看图声明。
- 可用未读未用合法。required 未读使 `required_read_complete=false`。必要确指未解、缺必要源/视图同样产生具体 dependency stop；每个缺口须有 source_request 与依赖维度。未请求/未停结论时 gate 不通过。
- 已请求且依赖维度实际在候选输出中为 null、附对应 material_requests 时，`dependency_handling_complete=true`，可作为首份格式完整语义输出保存；此时不称必要阅读完整，不因合法 null 重试。源请求不能掩盖 observed truncation/delivery failure 或已知压缩。
- read gate 检查只是操作记录的一致性，不独立认证实际阅读、来源必要性、语义正确性、真人身份或模型性能。

`native_records.py` 不再以“全部可用材料已读”的 visible_read_complete 布尔值选候选。它按外部冻结 packet 文件 SHA、全 bundle SHA 与完整输出文件 SHA 重算 scope gate，核对全部必要视图或实际 null+请求的依赖停止。read/scope/history/format/candidate 回执分别 SHA 绑定。scope/log/candidate 字段的错误不能用 null 修复，真实技术失败仍实留。其他最多3次技术尝试、全新线程、提示不变、首次完整保存、无反馈、无拼行与全部条件×批次封存门槛沿用 v1。

R1/R2/R3 使用同提示字节；W 只变 JSON 缩进和同值 packet 文件定位；H 只改首行。提示现在内含统一来源协议和必要 scope 技术 schema。`packet_builder.py` 仅替换提示读取义务、附协议/schema及其 SHA，并在新 batching manifest 标明 v2；其他 builder 函数原字节未变。owner binding 仍指 v1 已封存 final binding，可显式给新 build 使用。未实际调用 build、lookup 或模型。

本次仅运行必要读取 gate 的构造正反例及提示/hash 绑定检查。没有重跑原167项或全 source 检查；所有旧 v1 封存文件在前后逐 SHA 复核。
