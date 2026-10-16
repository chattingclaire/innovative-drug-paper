字段桥接候选已准备，尚未部署或执行恢复。旧protocol（source_reading_protocol_v12.py第58–59行）和final-v5 driver第370–373行只读status；v5发布dependency_status。已绑定真实冻结代码，不改原件。

接口：bridge_json_bytes(raw, expected_sha256, pointer='/source_requests')返回复制文档和别名receipt。只接受resolved/stopped/unresolved三个精确字符串；单字段明确resolved或两字段相等resolved才生成status resolved。stopped/unresolved保留停止；两字段冲突、缺失、null、未知、非字符串、重复JSON键及原字节SHA不符均拒绝，不产出可用canonical document。空列表只是空列表。

status以外字段、请求顺序、未解材料、引文、闭合证明及消费者限制全部保留。CLI只准备一个明确JSON指针，保存原字节和逐请求来源；不认证来源、实际阅读、消费或语义，也不运行protocol.check。若CLI生成候选，其文件SHA在receipt另存，结构canonical SHA与文件字节SHA分开。

代码和18项输入/预期在preparation-seal中事前固定；首次实际18/18匹配，0意外技术失败。执行结果在execution/first-results.jsonl逐项即时保存；仅核旧status谓词，完整protocol.check未执行，classifier/全域/恢复均0。没有读取实际全域首轮输出或主LLM标签。

未来只有在原首轮终结、独立接收及ROOT明确授权后，才可用已保存完整diagnostic/semantic unit/source logs作机械再接收。须核原完整封存字节、当前精确原文、同版有限proof、消费者与read/use receipts，保留所有独立stopped请求和其他错误；别名成功不能免检，不能用缺失首答重新分类填补。具体原全域保存要求见report.json。候选不是恢复GO、正式结果接收或统计认证。
