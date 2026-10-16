# E 依赖与证据提交后继候选

基线为封存 `joint-v14e-evidence-scope-root`；新副本为 `joint-v14eb-evidence-dependency-root`。只修改 `relations.py` 与 `dimensions.py`，其余 3 个模块逐字保留。当前不是总体执行或生产采用。

未闭合的 E 实质内容范围现追加一份明确的 `E_explicit_content_scope` 请求到 `material_requests` 和 `source_requests`。其消费者固定为 E，状态为 stopped。原请求顺序、内容以及全部来源扫描事件保持。E 决定中的缺料项与正式路由使用同一请求；有独立当前阳性时仍保留其未闭合依赖，不造 READ，也不让其他维度因这份请求变成 NULL。成员引文/边界核验失败同样走此明确路由。

“应提交本药治疗获益的临床证据”按实质证据内容保留 E。此放行仅在 E 消费者中进行；需同分句的提交/递交/补充/提供谓词及治疗获益证据对象。引用文件名、字段/格式操作不成立；独立的文件格式要求不能清空另一分句的实质证据要求。

先固定 `protection-contract-fixed-before-edit.json`，复用原 386 个案例和独审 3 个案例，增加 1 个独立阳性并存未闭合依赖案例、2 个有直接必要性的文件角色/混句对照。`attempt01` 保留全部 392 条：377 个硬断言，376 通过；唯一失败为原 01402/I 历史期待，两版相同，15 个原待定案例保留。原 353 条五维完整决定全部相同；全部 392 条 S/Ec/I/F 完整决定相同。9 个原 E NULL 保持 NULL，仅补依赖与路由；2 个实质证据提交正例从 E0 改为 E1。

`routing_checks.py` 是 NONHUMAN 检查工具，不是新生产适配器。它执行现存 `rule_driver.actual_reading_log` 的原函数 AST、原 status bridge、原 `source_reading_protocol_v12.prepare/check`，并执行原 driver 的依赖停止验证块。使用明确的合成材料 facade，不替代真实材料身份。9 个缺料案例及 1 个独立阳性案例全部产生真实 E 请求日志且通过原停止契约；错误维度、冲突/缺失状态、删除决策缺料记录均拒绝。所有 READ 仍只指向实际递送视图。

因此本次无需修改协议或正式 driver；但既有 v13b 总体入口只授权 S/F 变化，不能拿此次局部接口检查冒充 E 总体执行授权。未来 E 总体执行还需其真实版本与允许变动范围的正常冻结。本目录没有启动该入口，也未修改 v13b、v14e、稳定性任务、原材料或原期待。

复查可运行 `python3 -B run_controls.py <不存在的运行目录名>`。每轮独占创建目录并封存候选副本；分类器文件 I/O 被禁止。无需重新执行无关运输检查。
