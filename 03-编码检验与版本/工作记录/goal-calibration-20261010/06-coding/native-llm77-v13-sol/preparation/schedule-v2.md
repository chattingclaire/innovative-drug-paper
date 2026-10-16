R1-only 原生开发调度准备已封存：77 条均为历史曝光记录，复用原七批（13/2/3/22/10/11/16）的完整 prompt-R 和 packet/index。每批使用独立新原生上下文，批内共享历史。此包没有创建对话、调用模型、产生阅读收据或标签；不能宣称 RWH 全条件稳定性或正式验证，今后 RWH 另立全条件方案。

实际初始 prompt 按 UTF8 原字节拼接 `existing prompt-R + actor-wrapper-v2.txt`，逐批 SHA/bytes 在 plan-v2.json 中，不能增加 thread/run/condition ID 或临时说明。v4 无单独 annex；其封存 native-binding、gate、native_records、README 已精确绑定，最小 None-unused/真实原 SOURCE 额外视图说明已写入所有批次相同 wrapper。wrapper 为 9465 bytes，另计 v4 README 2756 bytes；最紧第二批的原 135016-byte 余量现剩 122795 bytes，七批均正。仍无 provider 容量保证。

ROOT 最小派发：读 plan-v2.json 某批的 base_prompt 原文件与 common_actor_wrapper 文件，拼接原字节并核对 actual_initial_prompt.sha256，然后调用 `mcp__codex_app__create_thread`，prompt 使用原 UTF8 字符串，target 为 projectless（directoryName 只在创建元数据），model=`gpt-6.1-sol`、thinking=`ultra`。先保存真实创建请求与返回；本包仅提供参数模板，不执行调用。actor 在运行时读取 CODEX_THREAD_ID，基于其 UUID 排他创建 attempts/<uuid> 并自行保存 identity、真实 reads/scopes、逐条完整 first-output、whole-output 和 seal。ROOT 再以实际创建返回 threadId 对照身份；不匹配则保留失败，不能改写身份或首判。

Actor 机械入口使用新的独立 Python 进程并优先 v4 路径：

```python
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, "/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/protocol-necessary-read-v4")
import necessary_read_gate as gate
import native_records as records
scope = gate.prepare_scope(packet, scope_run_id, runtime_thread_id)
# 真实读取/独立判读后，原样排他保存完整 item 与本条 scope；没有预填标签。
result = gate.check_scope(packet, saved_scope, gate.dependency_output_projection(item))
# 按批序保存裸 results list 为 scope-check.json；投影不能替代完整 whole-output。
```

保存 scope-manifest 的顶层仅 `scope_log_files`，按本批 frozen packet 次序含 source_id/path/sha256。逐条 first-output 必须与同 attempt 的 whole-output.items 原对象一致，首件不覆盖；完整五维 evidence 和条件字段遵循原 output-item schema。公共引用保持 source-quote 原 pointer/span 侧文件并关联真实 read receipt，不能伪造 CTX 或擅加枚举。read-event blank 的 note 不能进入禁止额外属性的真实 read_receipts。

ROOT 对每批只填真实 attempt-record metadata，复用 v4 `records.check_saved_scopes(receipt, externally_frozen_packet_file_bindings)` 和 `records.select_technical_receipts(receipts, frozen_actual_prompt_sha, externally_frozen_packet_file_bindings)`；无真实创建/历史/截断证据的字段保留未知，不能冒填 false 或 provider telemetry。最多三次确认技术失败的全新同字节 attempt；第一份完整技术有效输出（含合法 null/request）立即选定，不作语义重试、最佳选择或跨 attempt 拼接。机械检查在每批接收时可进行；ROOT 语义比较等七批首完整/真实失败都封存后才进行。

R1-only 完成仅声明七批开发子集的选定或真实技术失败均已封存。继承 `all_batches_sealed_gate` 要求五条件，不能用于本轮完成或冒称 RWH 门禁通过。准备文件与输入 seal 独立保存；不修改原 196 输入、v3 35 文件、v4 文件或任何旧 seal。


本 v2 澄清在首份 preparation seal 之后追加，原四文件与 seal 原字节保留。实际调度使用本版 plan-v2/actor-wrapper-v2/schedule-v2/seal-v2，不混用首版初始 prompt SHA。

已静态确认 innovation_support.rd_object 和 available_support 的 source_kind 只接受 current/context。真实当前/原 CTX 足以满足字段时如实用原 schema；公共 supplement 的连续引文可复用 `packet_builder.verify_source_quote` 和原 source-quote 侧文件，不能伪造为 CTX 或替代必填 evidence。若完全依赖公共源而原 schema 无法合法表达，保留原首判完整 candidate 与原引文/读账，记 terminal technical_representation_failed，不能通过假 source_kind、0/null 或重判标签求过格式。本次不裁标签、不扩 schema/v5，不执行接口或模型。
