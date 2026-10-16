已知真实ps出生时刻严格晚于原生产真实终态证书，且时区一致，即可证明这是不同的新进程。原91681于03:05:58出生；已封真实新91681出生05:36:27，晚于原生产20:55:20 UTC终态。判断旧进程是否仍存在不需要进一步知道新进程属于谁。

v1在此后仍要求pid∈new_owned，会对“出生已明确较晚、但归属未记录”的输入必然返回False，属于代码上过严的身份判据。本次没有观察到具体外部进程、Popen落盘竞态或无法追踪的工具子进程；**83186本轮实际错误类别须等真实R1-result，当前不作归因。**

v2继承原entry，只改historical_closed的最后必要条件，并从GO包装层移除已无必要的新子进程归属/Popen扫描。旧birth身份仍在、birth未知或不晚于原证书仍拒绝；缺身份信息不会推成“已关闭”。未知拒绝只记录PID/birth/执行文件basename/原因，不输出完整命令或正文。旧归属helper字节/AST保留，但新GO包装层不调用。

原GO所有检查、outer初始fresh扫描、bootstrap/controller、manual/prompt/material、cap13/receiver/selection及每批三次总预算保持。6fd168既有采纳及86083真实终止链必须原绑定；另必须新增83186当前控制器97797/05:59:27及全部实际启动CLI-host真实末态证据。当前83186尚在运行，本候选无执行权，未填新terminal/exit。

四项必要metadata控制通过：已封较晚birth在归属为空的构造条件下v1=False/v2=True；同原birth拒绝；未知birth拒绝；早于证书拒绝。另无调用preflight与缺采纳拒绝通过。构造条件/拒绝示例不冒称实际现场或GO错误。

未来唯一入口（只在83186真实末态、ROOT单独采纳后）：

```sh
/opt/homebrew/opt/python@3.14/bin/python3.14 -B '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/08-audits/stability-certified-PID-birth-compatibility-v2-sol/entry.py' --mode run --target stability13 --go '/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/native13-successor-terminal-compatibility-preparation-sol/ROOT-actual-stability13-GO-01.json' --adoption '<ROOT真实v2采纳文件>'
```

采纳模板需绑定本seal/entry/同GO、parent_PID_compatibility_adoption原6fd168、原prior_controller_terminal_evidence(86083)，以及未来current_controller_terminal_evidence(83186)。后者必须actual_controller_terminal/all_started_CLI_children_and_hosts_terminal/actual_exit_observed=true、真实整数actual_returncode、live_owned_processes=[]，prior_controller_identity与已封97797/lstart匹配；入口再查真实ps。所有selected/invalid/首答/剩余额度沿同campaign继续，不新建实验、不补第四槽。

0模型、0接收器、0分类器、0信号。当前运行及全部旧文件不动。准备封存后停止。
