# 持久控制器监督候选

此目录仅为候选，未创建恢复授权、未启动 campaign。`supervisor.py` 只调用 `config.json` 精确绑定的原 PID-birth v2 entry、原 GO 和原 adoption，不修改模型参数、原 max3、接收、选择或统计。

ROOT 实审后自行创建授权 JSON，字段约定为：

- `artifact_type`: `ROOT_stability_orphan_recovery_and_durable_continuation_authorization`
- `issuer`: `ROOT`；`template_only`: false；`orphan_recovery_adopted`: true；`same_campaign_continuation`: true
- 精确绑定：`supervisor`、`configuration`、`unchanged_entry`、`unchanged_GO`、`unchanged_adoption`、`controller_exit_diagnosis`、`campaign_manifest`
- `output_directory`：本目录 `runs` 下一个尚不存在的直接子目录，每份授权只能使用该独占目录。
- `closed_attempts`：全部 13 个固定 R3 route，每项含 `condition`、`batch_number`、`attempt_number`、`terminal_certificate`、`technical_reception`；两个绑定指向真实证书和已经安装的原 selection 接收回执。

准入仅接受真实 unknown-parent-wait 外部终态证书及技术失败回执。ROOT 于 15:59 尝试注册 kernel exit observer 时 3 个先前活跃 root 已退出，registration_N=0，没有取得实际 kernel 退出事件或返回码；16:00 刷新 13 项均无 live root。因此全部 13 项仍用 unknown/failure 契约，不把非模型演示的返回码作为实际任务证据，也不扩展 known-exit 有效接收。全进程组和 host 的真实终态证书及回执仍须核验齐全后才可启动。

ROOT 的实际启动器应使用固定 Python `/opt/homebrew/opt/python@3.14/bin/python3.14`，参数 `-B supervisor.py --authorization <实际授权路径>`，并用 `Popen(start_new_session=True, stdin=DEVNULL)` 独立启动，监督器自身 stdout/stderr 也写入 ROOT 独占日志文件，记录返回 PID。监督器检查自身 SID 和 stdin，持有整个运行期间的排他 flock；原 controller 仍保留其自身锁。

启动前再核原证据绑定、原 orphan PID/进程组、旧 controller、campaign CLI 和隔离 host 均无活跃项。新 controller 同样使用 `start_new_session=True` 和 `stdin=DEVNULL`。立即写 `controller-start.json` 的实际 PID，随后写 `controller-identity.json` 的真实 ps 出生观察；观察不到时如实为 unknown，不伪造。`controller-stdout.txt` / `controller-stderr.txt` 接收原字节。父监督器真实 `Popen.wait()` 返回后，独占写 `controller-terminal.json` 的真实返回码；若无法取得返回，值保留 null，绝不默认 0。启动或监督错误一并保留，不自动重启、不清理原捕获。

这里的 terminal 仅指被等待的 controller。它不宣称全部 CLI/host、5 条件或统计完成；ROOT 后续仍按原终态检查判断。监督器可脱离临时工具会话生存，但无法保证机器关机或监督器自身被终止后的退出信息；这些情况仍须保留为未知。

`local-wait-check.json` 记录两个真实本地非模型子进程：退出码 0、7 均由父 wait 原样取得，PID/出生时间实际观察，stdout/stderr 字节及绑定核验通过。仅测等待封存函数，没有执行真实授权门、恢复、模型调用或统计。
