# 必要来源读取门槛 v2（有限另版）

v1 的完整十根键 packet、来源/资产 hash、schema/profile、预算、顺序、R/W/H 差异约束保留；v1 封存与 B4 首判未回写。本版改正“全部可用全文/图片无条件必读”。实际阅读要求是统一 v12 协议的当前/body/CTX 和完成源结构 scope review 后声明的必要确指、几何、原图有限 closure。可用未读未用合法；使用须有同一视图的实际完整读入。

`native-reader-instructions.txt`、`native-full-source-protocol.md` 是执行说明。`necessary-source-scope.schema.json`、`necessary_read_gate.py` 是收据 gate；`native_records.py` 重算 gate 并绑定外部冻结 packet、首份候选、scope/read/check 文件。必要未读/确指未解必须 `required_read_complete=false`，记录 request 并将依赖维度在实际输出中停为 null、附 material_requests，才能成为完整语义提交。技术截断/失败/压缩仍实留。gate 不证明实际阅读、必要性或标签正确。

`packet_builder.py` 仅修改 prompt 与新 manifest 的读取协议绑定；其余函数源码逐字与旧版相等。所有原 schema 与手册副本 SHA 相同，final owner binding 仍用 `parent-binding.json` 所指旧封存路径。新 build CLI 参数与旧版相同；必须显式给定授权顺序、冻结预算、binding/手册及各 SHA。未选样本或执行 build/model。

外部协调者应从冻结 batching manifest 中取得该批对应 R/W packet 文件路径/SHA 与原全包 SHA，传给 `select_technical_receipts(receipts, expected_prompt_sha, expected_packet_files)`。scope/read log 的 reader 和 run 由外部实际线程/尝试回执绑定，不能把身份写进 R1/R2/R3 初始提示，也不能借用生产者或其他线程阅读记录。`read_log_file` 为含有序 `scope_log_files` 的 SHA manifest，每项有 source_id/path/sha256。`scope_check_file` 保存 `check_scope` 有序结果；候选 SHA、原文件内容和实际 null+请求在 gate 重新核对。`required_read_complete` 与处理好依赖停止是两个状态。

必要 gate 的19个有限构造对照与提示/hash 检查全部通过，见 `necessary-gate-results.run02.json`；run01 保留。构造源只有 token，无实际政策候选/标签，未调用 owner.lookup、未打开图、未选新来源或调用模型。没有重跑原167项或全source检查。

本目录仍是技术准备；原生 provider/model/参数/token/API调用数不可见字段保留 null，不将文件输出或收据冒称 provider wire 证据。正式执行与比较尚未发生。
