# 指针兼容恢复的持久等待器：仅候选

没有实际 ROOT authorization 和另行 `pointer_recovery_adoption` 时不得运行。本候选没有生成任何真实采用/授权，没有获取实际锁、创建运行输出或调用 parent wait、恢复入口、模型、接收器。

候选复用原 `supervisor.exclusive()` 和 `wait_and_seal()`，并保留恢复入口的 `require_adoption` → `terminal_evidence` → `fresh_quiet_gate` 顺序。旧 metadata_gate 含“后续槽必须为空”的首次孤儿恢复限制，已有后续槽后不适用；本候选不调用它，改为要求原 auth03、原 GO/campaign、原13条closed_attempts内容精确不变并验证其26个证书/接收文件哈希及失败语义。它不重新安装或更改孤儿接收记录。

新授权 `artifact_type=ROOT_stability_pointer_bounds_durable_recovery_authorization`、`issuer=ROOT`、`template_only=false`、`fixture_only=false`、`execution_authorized=true`、`same_campaign_continuation=true`、`original_max3_preserved=true`、`orphan_recovery_adopted=true`；`runtime_scope` 固定为 `original_durable_wait_plus_terminal_pointer_bounds_adapter`。精确绑定由 `authorization_gate` 检查，包括候选seal、configuration、supervisor/actual_supervisor_entrypoint、execution_wrapper、recovery_candidate_seal、reused_wait_implementation、original_authorization_03、unchanged_GO/campaign_manifest、unchanged_entry/unchanged_adoption、closed_attempts、pointer_recovery_adoption及完整actual_controller_argv。此文档不是授权文件。

控制器argv固定为 `[python,'-B',execution_wrapper.path,'--mode','run','--adoption',pointer_recovery_adoption.path]`。新输出固定在manifest的 `output_directory`，已存在则拒绝，不自动重启。新supervisor只接受 `--authorization`，无需在自身参数中传恢复entry路径；完整PID/SID/冻结Framework实际进程映像/argv经原supervisor_v3的身份函数核验，session必须脱离、stdin必须DEVNULL。恢复入口原进程匹配器不修改，不放宽自身或其他进程豁免。

新授权及原wait生成的启动provenance保留现有Q所需 `actual_controller_argv`、`unchanged_GO`、`campaign_manifest`、`closed_attempts`、`actual_supervisor_entrypoint`、`execution_wrapper`、`reused_wait_implementation`；provenance同时绑定ROOT_authorization与self_runtime_executable_binding。原wait会新建controller-start、identity和真实parent-wait；新Q必须另行配置绑定这些新文件，不修改旧Q。

实际采用后启动形状：冻结Python `-B supervisor.py --authorization <另行ROOT授权>`，由启动方使用DEVNULL、start_new_session=True和独立日志。待ROOT独立审核决定，本目录仅提供封存候选。
