本 bootstrap-v1 针对真实原生长 initial message 可见截断，仅改变任务要求的交付运输方式。七个短启动提示使用同字节 common text，加各批现有完整 instruction 的 path/bytes/SHA；每个均≤2500 UTF8 bytes。完整 instruction 与 preparation plan-v2 的原 R+wrapper-v2 SHA/bytes完全一致。原 196 输入、逐字手册、schema、规则、9465-byte wrapper、v4 runtime均未修改或重建。

这是新 variant：short initial launcher + 实际工具完整读取任务要求，不能称原长 prompt 的同字节技术重试，也不能把长文件SHA填入实际 initial_prompt_sha256。ROOT 已报告旧 batch-0001、0005 可见截断；另五条保持未知，不推断截断。原七次首次尝试的首件、真实读取、失败或行政停止由 ROOT 原样保留，新包不覆盖或读其答案。此包没有创建任务、运行模型或生成标签；R1-only、未来 RWH、真人与正式验证仍未完成。

ROOT 仅把各短 batch-000N.txt 原字节传作新原生任务的初始 prompt，使用 Sol/ultra、每批独立新上下文。完整 instruction 文件在短提示中明确授权为本轮任务要求。actor先核真实文件bytes/SHA，再逐块用真实工具读取全部要求；正文每块≤1500 UTF8 bytes，输出额度至少3000 tokens，并保留身份/序号/实际字节范围/SHA/结束标记。文件 hash 是身份核验，不是读完证明。全部块连续覆盖0到EOF且真实完整可见之后，才按已读完整手册/schema/protocol/index和原scope判读同一indexed packets；必要外部说明照原绑定读取。instruction-read-log为本attempt独立附件并进入seal，不能污染现有source receipt schema。

逐块读取可在实际actor工具中用以下最小方式；每个真实工具调用只返回一个块，不能把循环全块stdout一次输出。start来自上个完整返回的end，严格UTF8解码失败即保留技术失败。

```python
raw = Path(instruction_path).read_bytes()
end = min(start + 1500, len(raw))
while end < len(raw) and raw[end] & 0xC0 == 0x80:
    end -= 1
part = raw[start:end]
part.decode("utf-8", errors="strict")
meta = {"start_byte": start, "end_byte": end, "bytes": len(part),
        "chunk_sha256": hashlib.sha256(part).hexdigest()}
# 一次工具返回中以明确BEGIN/END元数据包围原part；使用stdout.buffer保留原字节。
# 收到完整结束标记且无截断后才将这块记complete并推进start=end。
```

截断、缺块、结束标记缺失或完整性未知都保留失败并停止，不靠补读掩盖成技术有效。actor不得自己读取其他scheduling、旧attempt答案、参照/性能/规则/其他actor输出或创建聊天。真实身份、首完整item/whole-output、view/scope/read/use记录、必要null/request、schema表示边界和失败封存沿用已授权 wrapper-v2/v4；已读图像文件字节仍不等于看过pixels。

预算保留完整材料worst，另加短launcher，完整instruction文件bytes另列作运输材料身份而不重复计其已纳入worst的手册/schema/index/wrapper。七批最小剩余操作额度见plan.json；provider容量仍未知，实际chunk标记/日志开销及任何输出超预留如实保留，不能截断首输出。原native_records按本轮短初始SHA核首完整收据，外部完整packet bindings不变；只声明本轮R1开发子集，不套五条件门禁。
