正式800条人类独立编码的本次冻结材料已准备完成。released_for_independent_human_coding仅表示材料冻结可用；实际分发、两名真人安排、独立执行和提交尚未发生，本次没有创建真人标签。

A/B各800个盲号、4000行五维，D的8000个值和E的8000个理由全部空白。抽样沿原41层、remaining600/exposed200及原纳入概率；原ID、各方presentation order、材料页、原始JSON、原source资产和XLSX全部逐字节保留。51来源与既有来源版本不重新构建。工作簿沿用原表名“初判-pre-release”以保留已验证模板字节；实际release.json绑定本次冻结手册/提示/协议。没有真人复核栏。

给每名编码者本方coder-A或coder-B目录以及shared-source，放在同一个根目录并保持相对路径。每方目录有正式manual.txt、execution-prompt.txt、common-execution-protocol.txt、填写说明、XLSX和全部材料。协调员保留另一方目录、release.json与coordinator-private；不要把A/B初判或coordinator-private映射材料互相交给编码者。包内源引用保留原始身份，但“可用材料”不构成已阅读/已使用声明。

实际返回时只收原始XLSX与真实执行说明，可由用户文字形成已绑定receipt。协调员保留原文说明，按实际事实保存既有字段：executor_code、actual_actor_type=real_human_independent、completion_status、human_coding_completed、actual_started_at/actual_submitted_at、prior_development_exposure、AI_assistance及四项independence_declaration（own_first_judgment、machine_answers_unseen、peer_answers_unseen、no_discussion_before_seal）。原件SHA、packet SHA、manual SHA和800/4000计数由协调员机械绑定，不要求编码者填技术JSON或sidecar。未知字段不得造填，内容仍能保存解析，资格状态如实待确认。

原件→派生接收入口使用已存在05-validation/formal800-xlsx-reception-adapter-sol/adapter.py，精确release SHA见coordinator-private/reception-contract.json。命令：

    python3 /Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/05-validation/formal800-xlsx-reception-adapter-sol/adapter.py receive --xlsx-a /实际返回/A.xlsx --xlsx-b /实际返回/B.xlsx --release /本包绝对路径/release.json --release-sha256 /本包release实际SHA --declaration-a /协调员已保存真实A声明.json --declaration-b /协调员已保存真实B声明.json --out /Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/05-validation/formal800-xlsx-reception-adapter-sol/receptions/新首件目录

其中/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010为本项目outputs/goal-calibration-20261010的绝对路径，SHA是字符串而非文件路径。必须用尚不存在的接收目录；接收器保存原始XLSX bytes与SHA，保留独立A/B，按私有source_id对齐并产生分歧/待定清单，不自动合并成裁定。未收到声明或有待填时不称正式内容接收完成，不计算指标或CI。真实接收命令尚未运行。

机械核对见mechanical-readback.json，原件及最终发布绑定见seal.json。未重跑既有16项控制，没有读Gold、机器first/labels/metrics或新裁定标签。
