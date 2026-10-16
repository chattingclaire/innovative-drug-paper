# 唯一24条队列的恢复依赖重绑候选

此目录只有待审副本，未采用、未启动、未创建锁或GO。原 `v17-dependent-continuation` 代码、配置、授权及 `actual-wait-01` 全部保留。原1130真实parent-wait、原18140自己的stopped、新鲜进程清空和native GO不存在仍是恢复入口的前提；本候选不会代替这些事实。

## 最小变更与固定路径

原模块在导入时固定 `HERE` 和 `CONFIG=HERE/config.json`，没有 `--config` 参数。故采用时需要另行封存一份新目录副本及实际配置，不能只向旧脚本传新路径，也不能原地改旧Q配置（恢复入口还精确绑定它）。

- 新副本仅在 `context` 增加真实重绑校验，在 `process_observation` 增加新进程识别及精确自身排除，在 `watch` 将队列锁位置固定到原Q的 **同一个 `queue.lock`**。不得删除或替换这个锁文件，否则旧、新锁的inode互斥会失效。
- 新队列 `runtime_output` 和 `conditional_authorization` 使用新路径；`actual_GO`、两批native目录、runner的 `execution.lock` 和唯一合并输出目录全部保持原值。不能另取GO或合并目录规避已有输出门。
- 原Q尚持锁或未生成自身stopped时，不启动替代Q。原队列失败事实与旧controller终态不被新记录覆盖。`fresh_native`、每批fresh检查、独占GO创建、两批串行严格接收、每批释放容量及单次24+4457合并门均保留。

## 新依赖绑定的真实来源

恢复durable候选目录为 `../durable-recovery-preparation`；它计划的真实输出位置为 `../durable-recovery-runs/actual-recovery-01`。以下文件必须由实际Popen/原wait实现产生，不能由准备脚本补写：

| 新配置字段 | 必须绑定的实际文件或值 |
|---|---|
| `bindings.dependency_authorization` | ROOT另发的新durable恢复授权，精确字节绑定 |
| `bindings.controller_start` | 新输出内 `controller-start.json`，实际PID=PGID、实际argv |
| `bindings.controller_identity` | 同一实际PID及观察到的birth，不能用旧1130身份 |
| `bindings.supervisor_start` | 新输出内真实 `supervisor-start.json` |
| `controller_terminal` | 同一新输出内实际 `controller-terminal.json` 路径；到场后仍须原严格parent-wait门 |

新durable授权必须有 `runtime_scope=original_durable_wait_plus_terminal_pointer_bounds_adapter`，`pointer_recovery_adoption`绑定实际恢复采用，`execution_wrapper`绑定新terminal recovery入口，`actual_supervisor_entrypoint`绑定新durable supervisor。实际argv必须精确为：冻结Python、`-B`、新terminal recovery `entry.py`、`--mode run --adoption`、真实采用路径。新start、supervisor-start与授权的argv一致；supervisor provenance继续绑定新ROOT授权、**原** `reused_wait_implementation`、冻结Framework进程映像，并新增实际wrapper/supervisor/恢复采用绑定。

新授权继承原auth03的 `unchanged_GO`、`campaign_manifest`、`closed_attempts`（原13条）、`unchanged_entry`、`unchanged_adoption`，本候选逐项要求相等。H0041指针错误通过窄adapter形成普通技术失败/后续原max3接续，不能并入原13个unknown-returncode orphan或改写其历史。新恢复采用还须精确绑定原Q的stopped与原1130的parent-wait。

当前 `config.json` 的四个依赖绑定**仍是原配置的机械比较基线**，由 `candidate_only=true`、`execution_authorized=false`及非空 `pending_actual_bindings` 明确禁用；另以 `pending_actual_paths` 明列待最终固定的 `controller_terminal`、`conditional_authorization`、`runtime_output` 三个路径字段。新未来文件只列路径，未伪造存在或SHA。`context()`在任何实际依赖读取、观察、watch或锁操作前拒绝此候选。

## 进程与终态门

原 matcher 带 `--original-entry`，不能识别新recovery wrapper的 `--mode run --adoption`。新副本补充按实际start完整argv的三种已绑定Python路径匹配；同一新入口出现其他argv也按身份不明阻断。旧outer、旧durable supervisor及旧Q matcher继续保留，同时阻断其他新Q。只有 **当前调用的真实PID＋PGID＋新Q完整已固定argv** 全部相等时，才排除自身；同名、同命令的另一个PID不会被排除。原PID/PGID birth、数字复用证明、后代闭合和相隔至少5秒的两次清空观察未删减。

原 `successful_wait` 的真实wait、整数returncode=0、实际输出绑定与时序仍执行；退出码0不能代替全批终态。`full_terminal_gate`继续一次核定：1305＝5×87×3个预分配路由（不是实际调用次数）；435＝5×87个实际批终态；4000＝五条件各按同一800来源顺序的投影槽。未返回/zero-call不冒充终态，technical_fail保留且标签为空。

新controller启动时间仅约束新epoch。旧attempt仍遵守 `dispatch ≤ 自身actual-start ≤ 自身真实terminal ≤ 新parent terminal`；不得新增“旧attempt必须晚于新controller启动”的限制。原GO链、原首答/接收/实际完成记录和13个orphan失败证书原样保留，`returncode=None`不补为0。

## 封存与采用顺序

1. 完成且独立接收真正的恢复采用和新durable启动；实际start、identity、supervisor-start出现后，将本已核验 `supervisor.py` **逐字节复制**到独立实际Q目录A，另生成A的实际 `config.json`，替换四个实际绑定、固定新terminal路径与新Q输出/授权路径。不得覆盖这里已经封存的candidate配置。两个pending列表清空、机械基线标志置false，实际新版本才明确 `candidate_only=false/execution_authorized=true`；这些标志只反映已完成的独立采用，不能代替真实文件链。
2. 对新版本复核所有输入SHA与原门保持，封存代码/配置；ROOT另行签发新Q conditional authorization，绑定新supervisor、完整新configuration、新dependency authorization及新增原链/恢复组件绑定。授权继续固定两批、共享原锁、唯一native GO/合并输出及原所有必需标志。
3. 只有独立审查完成后，单一新Q才可在原共享锁上启动。它等待新真实parent-wait，再执行原完整gate、清空观察和native freshness门。实际新controller或wrapper尚活跃、历史身份不明、有native GO/partial output时即停；不自动恢复。

同字节脚本被复制后，模块自身 `HERE` 自动成为A，`CONFIG` 自动指向A/config.json，硬固定的 `SHARED_QUEUE_LOCK` 仍是原Q锁。建议实际配置显式用 `conditional_authorization=A/ROOT-conditional-authorization.json`、`runtime_output=A/actual-wait-01`。原 `authorization()` **没有** `runtime_output.parent == HERE` 这个检查；它检查传入授权路径等于配置路径、授权的supervisor绑定等于实际 `__file__`、configuration等于实际 `CONFIG`，并逐个精确核对配置中的运行路径。原 `watch()`要求输出目录全新。采用上述A内路径即可同时满足这些门和新的完整自身argv匹配；真实新terminal仍指向恢复durable输出目录，不放进A。原GO及唯一merge输出保持原路径。

`verify_preparation.py`只做6项有限机械检查。原18函数中仅三处显式接线改变；移除这些指定接线后所有原函数AST相等，尤其原attempt/full_terminal_gate及watch内部严格24+merge主体保持。matcher使用合成进程字典，未读取实时进程；只调用候选context拒绝门，未运行实际context、projection、watch、原完整套件或模型。`verification.json`记录这次检查；本交付不代表真实恢复或队列已准入。
