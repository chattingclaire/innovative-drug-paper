# 孤儿尝试的失败接续候选

仅适用于 scope.json 固定的 R3 13 次已实际启动尝试。原控制器失联后没有取得父进程 wait 返回码；不能用捕获正文补造 rc=0，也不改变原 receiver 的任何有效接收要求。本入口仅生成外部观察终态证书与 technical_invalid_whole_batch 旁账，不创建旧 ROOT-process-completion、first、有效 seal，不启动、重试或终止任何进程。

`observe` 读取完整进程表、13 个原始 start/dispatch 和原始文件字节哈希。前后两张进程表保留原始文本；检查原 root 身份、原数字 PGID、已知后代、原控制器、同 campaign 及隔离 CLI/host。PID 的新出生时间可区分单独 PID 复用；数字 PGID 仍有成员时保守拒绝，并不凭 PID 复用忽略整组。哈希读取不解析捕获、事件或标签。

在两个不重叠的观察中，全 13 个尝试及相关已知进程须已消失，原文件哈希须稳定。`prepare` 才能为明确指定的 unknown 子集生成证书和待采用 receipt；本次实际 13 个退出码均未获知，可全部指定。保留 `returncode=null`、`timed_out=null`，它们表示缺少原 wait 事实，不代表返回零或未超时。有最终捕获的尝试同样只记技术失败。遇到新的真实退出证明，应另行核查，不能覆盖成 unknown，也不能经此失败入口直接宣称 valid。

从本目录操作，一次真实接续使用以下步骤；每个输出路径必须不存在：

```sh
python3 orphan_recovery.py observe --output observation-01.json
# 第二次真实独立观察，时间必须在前次结束之后。
python3 orphan_recovery.py observe --output observation-02.json
python3 orphan_recovery.py prepare \
  --observation observation-01.json --observation observation-02.json \
  --unknown-batches 42,47,49,51,52,53,54,55,56,57,58,59,60 \
  --output prepared-13
```

`prepared-13/plan.json` 逐项列 certificate、receipt payload、原目标路径及剩余原额度。attempt 3 的剩余次数为 0，不能生成 attempt 4。证书的 `actual_process_terminal=true` 只表示所述外部过程观察终结，不能冒充父进程成功 wait 或原内容/来源校验通过。

独审和 ROOT 的实际采用完成后，ROOT 写一份 `artifact_type=ROOT_failure_only_orphan_closure_adoption` 回执：issuer=ROOT、template_only=false、fixture_only=false、adopted=true，并精确绑定 plan、scope、implementation、original_GO、original_adoption。候选不预制真实采用回执。执行：

```sh
python3 orphan_recovery.py install --plan prepared-13/plan.json --adoption ROOT-actual-adoption.json
```

安装拿原 controller 锁及 13 个 reception 锁，重新读取原绑定、完整进程表及文件哈希，只独占创建原 selection 目录的 invalid receipt；已存在且逐字一致的 receipt 可幂等续完，任何差异拒绝。原 capture、events、stderr、start/dispatch 均保留。失败 receipt 的 completion 指向独立外部证书；原 controller/check_prior/terminal_projection 已有的失败路径可以复用。之后仍须由另行采用的持久监督入口，在原 GO、原 adoption、原总额度下继续；本入口没有 launch 功能。

`controls-final.json`：18 项 NONHUMAN 控制通过，包含完整 13 槽、unknown+完整外观捕获仍 invalid、第三次耗尽、PGID/host/已知后代仍活拒绝、PID 出生身份、文件/GO/route 漂移、先后时序、已有回执及后来尝试拒绝、空采用拒绝、合成真实隔离、安装幂等。旧 controls.json 保留为前版控制结果；最终以 controls-final.json 绑定实现为准。作者没有执行真实 observer、接收、安装、信号或模型调用。
