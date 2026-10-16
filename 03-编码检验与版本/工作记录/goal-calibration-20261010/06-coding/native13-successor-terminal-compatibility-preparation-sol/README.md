本目录仅提供原 v4 运输中断后，两个既有后继准备所需的外层终态兼容接口。原 v4 的状态明确为 `transport_interrupted_not_complete`。不生成旧 result.json，不补旧 process-completion/退出码，也不把实际终止说成原 207 批正常完成。

改变只有外层前提。0216 原核心入口的 `check_go` 在新薄入口内替换为共用证书检查；原三成员 01402/01403/01404 顺序、v16 材料、概念手册、prompt、schema、模型请求、三技术槽、首个有效整批及接收/捕获逻辑完整保留。既有稳定性 capacity13 入口本来接受通用 production terminal certificate，新增薄入口只补验证本兼容封印和证书来源，随后仍使用原 controller/runner/receiver、87 批、800 条、五条件 R1/R2/R3/W/H、共享锁与容量 token。R 是三个新独立诊断重复；W/H 是原预设条件，不算 R，不是 P 原生产整批复现。两个后继必须分别签真实 GO，不能因共同证书即自动执行。

观察器供 ROOT 审阅后独立启动；本次准备没有启动它。它读取已封存 startup registry v2、真实 Popen leases 与新鲜 ps，累计 PID、lstart、PGID 和实际观察的传递子进程。除原 CLI 进程组外，它把隔离 CLI runtime 的确切 `codex-code-mode-host` 路径作为独立种子，能查到已被 reparent 的独立 PGID host；桌面应用自身另一条 runtime 路径的 host 不属于本轮。观测间隔默认 2 秒，不能声称内核级全部历史进程追踪；它证明全部已知/实际观察后代及当前隔离 runtime host 不存在。若发现遗留 host/未知状态、不能解析 ps、无真实结果或结果未完成，则不给终态。保守使用历史 PID/PGID 可因 PID 重用阻断；不得删除绑定以放行。

未来共用证书须同时绑定：原 504 批/4481 条 collector 全覆盖封印（完整原成员及顺序、无 thin35）、旧父真实暂停/终止操作和 terminal observation、原未知槽原文件哈希与未伪造的缺失 completion、新13 actual runtime/result complete、新父 PID91092/lstart 与 actual session38144 的 ROOT 真实 completion/退出码见证、观察器最终全部已知子进程/独立 host 为空、签证时再次新鲜 ps 为空。新13 result 的布尔值单独不够；未完成时不允许先生成证书。证书不改变已有选取、不作语义正确性或 formal 指标声明。

ROOT 审阅本封印后，可启动以下只读观察入口（不是 GO，没有 signals/model/classifier）：

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B outputs/goal-calibration-20261010/06-coding/native13-successor-terminal-compatibility-preparation-sol/observe.py --output outputs/goal-calibration-20261010/06-coding/native13-successor-terminal-compatibility-preparation-sol/observations/ROOT-monitor-01
```

真正完成后 ROOT 根据 `certificate-request.template.json` 和 `controller-exit-evidence.template.json` 另存实际证据（template_only=false，原模板保持），绑定实际全覆盖 collector 和观察输出，再运行唯一证书生成入口：

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B outputs/goal-calibration-20261010/06-coding/native13-successor-terminal-compatibility-preparation-sol/successor_entry.py --mode certificate --request <ROOT实际证书请求路径> --output outputs/goal-calibration-20261010/06-coding/native13-successor-terminal-compatibility-preparation-sol/certificates/ROOT-final-01
```

该命令只生成外层证书，绝不签 GO 或推理。未来 ROOT 分别采用原 GO 必需字段，并追加/替换本目录模板标明的外层绑定，才可用同一后继入口：

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B outputs/goal-calibration-20261010/06-coding/native13-successor-terminal-compatibility-preparation-sol/successor_entry.py --mode run --target native0216 --go <ROOT真实0216-GO路径>
/opt/homebrew/opt/python@3.14/bin/python3.14 -B outputs/goal-calibration-20261010/06-coding/native13-successor-terminal-compatibility-preparation-sol/successor_entry.py --mode run --target stability13 --go <ROOT真实稳定性-GO路径>
```

0216 新 GO 的 `authorized_entrypoint` 改绑定新薄入口；`native_v15_full_collection_seal` 必须等于证书全覆盖绑定。旧 `remaining_run_result` / 必须每个旧 dispatch 都有 completion 的整体前提由明确外层兼容证书替代，其他 ROOT 身份、run_id、原 preparation-seal、single_transport_owner/live_cli_pids、未来实际 GO 时间检查保留。稳定性原 ROOT_GO/schema 全部必需项保留，另加 `at_utc`、`authorized_successor_outer_entrypoint`、`successor_compatibility_seal`。原 certificate schema 已允许附加属性，未更改原 schema。共同手册、内层 read/quote/null、技术重试和统计接口均未更改。

当前只完成静态绑定、语法、未 GO/模板拒绝和独立 PGID/孤儿 host 选择的少量机械检查。没有模型/CLI帮助调用、分类器、signals、监控启动、实际证书或后继 GO；旧准备已有字节均保持。
