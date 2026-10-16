# 终态后恢复入口：仅候选

本入口不自行授权恢复。没有另行 ROOT 采用文件时，`--mode check` 和 `--mode run` 均拒绝。没有生成实际采用文件，也没有运行原接收器、原控制器或模型。

全部门槛满足后，运行模式只先包装已绑定的 capacity13 `bootstrap.runtime()`，在原 runtime 返回后包装其 `receiver.module`，再把 `sys.argv` 设为原 outer argv 的 `[2:]` 并调用原 outer `main()`。原 GO、历史 PID/证书、capacity13、campaign、schema、首答保留及 max3 守卫全部保留；失败即原样拒绝，没有旁路。该入口自身不负责 parent wait；ROOT 必须另行用持久等待实现启动它并记录新的 controller-start、identity 和实际 parent-wait，供后续队列使用。

额外门槛：原1130的真实 parent-wait；原固定 epoch 的 H-result 仅0041为精确 IndexError，其他434批均终态；原 watcher 的 `actual-wait-01/stopped.json` 已生成；native GO 仍不存在；两次新鲜进程观察相隔至少5秒，原控制器、18140原birth、同队列watcher、campaign所有隔离CLI exec/code-mode-host及相关后代均已退出。旧 watcher 外部被杀而无自身 stopped 记录时，本候选拒绝，不提供替代证据路径。

ROOT 采用文件的精确结构由 `entry.py:require_adoption` 检查：`artifact_type=ROOT_terminal_pointer_bounds_recovery_adoption`、`issuer=ROOT`、`template_only=false`、`fixture_only=false`、`execution_authorized=true`、`same_campaign_continuation=true`、`original_max3_preserved=true`、`no_changed_labels_or_first_bytes=true`。它还必须绑定 entrypoint、candidate_seal、configuration、pointer_adapter_seal、original_outer_entry、original_GO、original_controller_start、queue_configuration，以及 manifest 中固定路径的 parent_wait、H_result、controller_result、watcher_stopped。`fresh_gate_output` 必须为本目录 `runtime-evidence/` 下尚不存在的 JSON 文件。此说明不是采用文件。

实际采用后的入口形状为冻结 Python `-B entry.py --mode check|run --adoption <另行ROOT文件>`。check 完整检查但仅打印证据；run 在所有门槛后保存新鲜观察，再调用原 outer。不会创建或修改原native GO、旧Q配置和旧Q文件；后续队列如何绑定新恢复parent-wait由ROOT单独处理。

`verification.json` 只记录准备阶段机械检查：缺少采用拒绝、真实仍live时拒绝、hook顺序与对象不变、outer argv无错误的-B传入、绑定文件哈希未变。没有假造终态、实采纳或成功执行证据。
