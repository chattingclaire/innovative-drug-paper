# 原 whole recovery：旧 3 停止后接续 13 的运输准备

准备状态：未签 GO，未发送信号，未调用模型。原 v4、manifest、guard、actor instructions、assignment、schema、原首答和运行中 slots 无修改。ROOT 审阅本封印后才进行真实停止与观察。

v4 无外部自然 drain：207 futures 一次提交；内存 STOP_NEW_DISPATCH 只由特定真实模型账号错误触发，没有 stop-file/signal handler。SIGINT 也不能保证取消排队任务。新的停派功能不能逆装进旧活进程。本准备不提供自动 signal/kill 代码。

ROOT 交接的必要顺序：

1. ROOT 运行 `observe.py --stage live --output H/observations/live-<唯一名称>`，获得实际旧父 PID、启动身份、CLI/子进程/进程组和槽状态。H 是本 README 所在绝对目录。
2. ROOT 审阅后可仅向该旧父发送 SIGSTOP；CLI 使用 start_new_session 的独立进程组继续捕获与完成。紧接着运行 `observe.py --stage frozen --prior <live>/observation.json --output H/observations/frozen-<唯一名称>`。必须实际观察同一父处于 T 状态，不能凭已发指令认定暂停。
3. 若 `may_ROOT_terminate_frozen_controller=false`，禁止终止。任何未 selected 第三槽有文件但缺真实 process-completion，均要求 ROOT 恢复旧父 SIGCONT，让该最后机会自然完成并收件，然后重新 live→暂停→frozen。即使 CLI 看似消失而第三槽完成记录尚未保存，也要先恢复。这样不会为了迁移消耗唯一第 3 槽。父暂停后无新增父线程派发，冻结观察也涵盖暂停前已写入的 dispatch/prompt。
4. 仅冻结保护通过，ROOT 才可明确终止该已暂停父。为避免重新恢复父时排队任务竞态，直接终止已暂停父是可审查方案；ROOT 需记录实际操作与真实身份，不把它描述为优雅完成。现有第 1/2 槽 CLI 可自然结束并保留原 stdout/first/report/seal；父退出后历史返回码通常不可得，继续记 unknown。必要子进程终止也必须另有 ROOT 的真实操作证据，本代码不执行。
5. ROOT 等旧父、所有已观察 CLI、后代及进程组实际消失，运行 `observe.py --stage terminal --prior <frozen>/observation.json --output H/observations/terminal-<唯一名称>`。它会核新鲜进程状态、第三槽保护，并封存不确定槽所有现存文件 hash。超时、turn.completed、旧 all_terminal 或单独 PID 消失都不能替代完整后代检查；terminal 也不声称未知历史 clean exit。ROOT 须另提供实际操作/终态证据绑定和永久停派声明。
6. ROOT 根据 GO.template.json 写真实外部 GO，绑定本 seal、terminal observation、真实操作证据，并只授权这个入口。GO 前仍不得启动新 13。未来执行入口：

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native-whole-capacity13-handoff-preparation-sol/runner.py' --mode run --go '<ROOT真实GO绝对路径>'
```

观察器与 runner 均使用同一个本封印；run 另取排他 execution.lock，只允许一次 runtime。执行前会再次核 terminal 对应槽状态和全部旧进程不存在。GO 后只向原 manifest 的空预留槽追加真实执行，容量侧记和外部 receipts/runtime 在 H 内。绝不同时启动旧 v4/另一个 runner。

容量 13 是对共同 protocol 第 11 行“最多3并发”、旧 cap3 sidecar 和模型可见 v4 dispatch prompt 的明确 ROOT 运输例外。旧 prompt 的“始终不超过3/13已撤回”句原字节保留，由公开外部容量例外覆盖，只涉及 ROOT 调度；不能声称新 13 仍逐字符合原 3。原 manual/execution prompt/actor requests/成员顺序/材料/schema/CWD/argv/model gpt-6.1-sol ultra/first capture 不变。

新 runner 直接执行冻结 v4 的原 prompt()/attempt()，原 stdout/stderr/final-message 捕获、first/seal 和技术超时预算不改；仅外置容量 metadata 与严格 ROOT 接收。原 guard 无修改。新 scheduler 最多 13 个活跃 batch futures，每个串行技术 attempts；每条实际 CLI 启动有外部 PID/进程组 lease，leader 完成后仍有同组后代则停止新增派发。13 指最多 13 个独立 CLI 执行组，包含 node/vendor 子链；不是所有 OS 子 PID 总数只有 13。

原 selected first/receipts/selection 不改。只处理实际尚无 selection 的原整批：先按 attempt 顺序核已有真实完成槽，最早严格有效整批即选；合法 null 不重试。不确定旧槽和任何非空未完整槽均保守消耗已有恢复轮机会且不覆盖；下一空槽仍是原 attempt 1..3，没有预算重置/第4次/跨 attempt 拼接/语义择优/35薄上下文。已有第三槽全耗尽则报告 exhausted，不能假称全量完成。若原 invalid receipt 因接收环境问题而同一 guard 现可通过，另存外部 receipt，并保留旧 receipt。collector 仍读原 root-selection-v3 与其 receipt binding；接口和统计公式不用改。

新 runner 支持 H/STOP-NEW-DISPATCH：停止尚未启动的 batch/技术重试，保留当前真实 CLI 捕获，等已有 futures 完成；它仅对新进程有效。runtime/result 如实披露剩余和子进程，不把 future 结束硬写成全量 clean。

后继 0216/v16：既有 native-v16-batch0216-material-delta-preparation 的旧 outer terminal 入口绑定 v4 整轮 complete；迁移后旧 v4 真实为运输中断，旧 result.json 不得伪造。等 whole 最终完成，ROOT 只需最小扩展外层 terminal 证书检查，以“原504/4481最终 collector 全覆盖 seal + v4 真实终止证明 + 新13真实 complete 和无子进程证明”为 parent；源、手册、guard、新 v16 材料与内层 0216 三成员协议仍不变。本轮不重做该准备。

准备仅有静态绑定/结构断言、第三槽保护与未 GO 拒绝的少量机械检查。任何实际观察/中断/推理尚未发生，provider 服务身份未独立核验，正式验收仍 false。
