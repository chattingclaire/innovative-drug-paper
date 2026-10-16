已封存 batch-0003（01a122ee-98e6-7290-a07c-4eb2df4aef55）37 个成员与 batch-0002（01a122ee-8fb3-7010-81e0-7a224a9b0fc5）14 个成员的实际 SHA/bytes 均相符。只读了 seal、纯技术状态/历史、实际截断返回或失败摘要和 prepared scope 的字段/字节规模；没有读取标签、参照、性能或未封存尝试。batch-0003 原始工具返回保存完整截断证据：原规模43137 tokens，含省略31137 tokens标记。其一次输出运行说明、92条 requirements（compact canonical 79373B）和大 source_record；batch-0002 合并两条 source_record、requirements（81703/93643B）及gate源码，摘要报92533 tokens原规模、12000返回额度，但原始平台返回未保存，不能更强地证明其精确stdout/请求。

故障是来源检查阶段的聚合stdout过大；已成功核hash、生成prepared文件或完成instruction分块，均不能弥补源视图真实返回截断。修复只提供一个 bounded pointer/view CLI，不改语义协议、输入、手册、schema或旧失败/首件。requirements/inventory保留为身份/必要view索引，使用小摘要与实际必要view逐个读取，不把大量canon重复source_basis当来源正文整批输出。

actor 使用本批索引中的真实文件byte SHA调用：

```sh
python3 "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-llm77-v13-sol/source-read-transport-fix-sol/source_view_chunk.py" \
  --file "<本批packet绝对路径>" --file-sha256 "<冻结索引文件byte SHA>" \
  --pointer /source_bundle/source_record/text --encoding utf8_text \
  --start-byte 0 --max-bytes 6000 --audit-log "<自身attempt内唯一chunk-emission.json>"
```

优先读取原字符串叶（当前text、具体原CTX文字等）；必要结构可用 canonical_json，不输出整包/整requirements作为正文。文件中的JSON pointer保留真实路径；packet中的 /source_bundle 前缀只是访问完整packet，scope/source-quote仍沿原bundle指针、原resource/source SHA绑定，不能把packet文件SHA当PDF/source SHA。必要绑定说明或代码可改用 `--encoding file_utf8` 并不传pointer；这只返回UTF8文本，不读图像pixels。

一次工具调用仅一块，exec_command 与 functions.exec 输出预算都至少12000 tokens。核BEGIN/END相同元信息、无截断、实际可见原内容、chunk SHA和连续范围之后，才用返回end_byte作为下一start_byte；保持同file SHA/pointer/encoding/view SHA，到view总字节数才是该视图完整。source scope/角色/确指、image读取和依赖null/request仍遵循原协议，不增必读资源或标签hint；此额度不是provider保证，截断保留技术失败停止。

--audit-log 只排他记录本次真实程序执行、原字节范围和 stdout 已写入；它明确把 actual_tool_event_id/delivery_status留null、read_attestation留not_recorded。actor必须在真实返回后另存事件/首尾标记/完整可见范围与本人read，不能原样把程序日志粘为schema读收据，不能让metadata hash冒称实际阅读。程序成功emission仍可能被平台裁剪，必须检查实际返回。

仅做语法compile与一次实际原字符串边界检查：原view7449B，首块[0,5999)保持完整UTF8字符，原字节、view/chunk SHA、首尾标记全部匹配，stdout共7620B。保存的stdout只是物理检查证据，不是新actor语义阅读或看图收据。未执行编码/模型、未评性能、未建聊天或重建profile/packet/framework；有限候选封存后停止。
