# 内层历史 PID/进程组号兼容候选

真实 `actual-resume-01` 已由原持久监督器取得 controller 返回码 1。当前原 `terminal_common.owned` 重现的唯一阻断为系统 TelemetryDiskChecker 的 PID/PGID 939：新出生 13:22:08，旧身份 03:16:12，已证终态 04:55:20。失败瞬间未保存匹配表，不把此次后续观察冒称当时快照。

新 `entry.py` 仅在运行时预载精确绑定的原 terminal_common，并收窄历史纯数字 PID/PGID 的种子集合，随后调用原 owned。已知旧身份、所有原命令条件、保留种子的全部后代仍由原函数原样检查。只有进程出生明确晚于封存终态且不等于旧身份，才可排除 lease 数字误判；PGID 还必须有当前 pid=pgid 的新组长，组内成员也均明确新生。无组长、未知出生、旧身份成员均保守阻止。原文件、GO、schema、receiver、max3 和 13 个旧 unknown/failure 回执不变。

14 项纯 NONHUMAN 控制已通过。未启动真实 wrapper、监督器或模型。ROOT 实审后创建两个真实授权：

兼容采纳 JSON：`artifact_type=ROOT_outer_terminal_numeric_PID_alias_compatibility_adoption`，`issuer=ROOT`，`template_only=false`，`fixture_only=false`，`adopted=true`，`numeric_alias_only=true`，`receiver_schema_max3_unchanged=true`。绑定字段为 `candidate_seal`、`manifest`、`wrapper_entry`、`original_entry`、`original_GO`、`original_adoption`、`production_terminal_certificate`、`actual_refusal_diagnosis`，都绑定本目录和 manifest 指定原件。

续跑授权保留 v1 supervisor 的完整授权契约：原 `supervisor` 字段绑定被复用的 v1 helper，原 `configuration` 绑定 v1 config，`unchanged_entry` 指原 PID-birth entry；13 certificate/receipt 与新独占 runs 输出目录仍由原 metadata_gate 检查。增加：

- `actual_supervisor_entrypoint`：本目录 supervisor_v2.py binding。
- `outer_compatibility_manifest`：本目录 manifest.json binding。
- `execution_wrapper`：本目录 entry.py binding。
- `outer_compatibility_adoption`：上述真实兼容采纳文件 binding。
- `reused_wait_implementation`：原 supervisor.py binding。
- `runtime_scope`：`original_durable_wait_plus_adopted_outer_numeric_alias_guard`。
- `actual_controller_argv`：严格等于下述固定构造的 argv。

ROOT 通过固定 Python 以 `-B supervisor_v2.py --authorization <续跑授权绝对路径> --compatibility-adoption <兼容采纳绝对路径>` 启动 supervisor，参数顺序固定；`Popen(start_new_session=True, stdin=DEVNULL)`，supervisor stdout/stderr 独占保存。

最终 controller argv 为：固定 Python、`-B`、本目录 `entry.py`、`--original-entry`、原 entry 绝对路径、`--go`、原 GO 绝对路径、`--adoption`、原 adoption 绝对路径、`--compatibility-adoption`、真实兼容采纳绝对路径。v2 显式验证授权中的整条 argv。新 wrapper 内再调用原 entry.main，原 fresh 证书检查仍运行。

v2 持有与 v1 相同的独占锁，复用原 metadata/process gate 与原真实 wait/日志函数；另外拒绝其他 wrapper/v2 进程，排除自身必须精确符合 PID、独立 SID 和实际 argv。所有真实返回码继续由父 wait 取得，无自动重启。
