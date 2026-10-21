# 全量LLM缺失部分的最小运输恢复合同（只读审计补充）

**旧207批已经耗尽每批3次；恢复必须另开有明确身份的新运输恢复轮，不能冒称原协议内第4次。** 覆盖原既定207个完整batch、2349条，保留原批次顺序、手册、执行提示、packet与必要资产、严格schema、实际读取和逐字证据。此次未建立或执行新恢复轮。

## 已查明的失败主因

| 旧207失败批次内的621次尝试 | 次数 |
|---|---:|
| CLI明确报模型不支持ChatGPT账户，returncode=1；接收器因缺seal报错 | 615 |
| returncode=0，Packet exact quote mismatch | 1 |
| returncode=0，KeyError bytes | 2 |
| returncode=0，KeyError source_record | 3 |

615次原始error/turn.failed明确为“gpt-6.1-sol model is not supported when using Codex with a ChatGPT account”。这是接收前的服务请求拒绝，不能把missing seal.json当成仅需放宽封存检查的格式问题。另6次才是已经完成CLI turn后出现的技术输出/结构问题。旧原件、失败及任何不完整first都要保留。

身份归因须谨慎：旧[CLI冻结profile](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/full4481-fresh-cli-dispatch-root/CLI-execution-profile-amendment.json:1)与旧dispatch-start实际argv[0]，已经都指向isolated-codex-cli-0.162.1-root；其显式launcher SHA与35条新补跑manifest相同。新35条全部returncode=0表明该显式请求路径后来可返回完整turn，**没有证明CLI版本更换导致恢复，也没有解释服务端许可为什么变化**。不能改成别的默认模型后仍声称同模型。

## 最小恢复接口

1. 先冻结新campaign envelope及207原batch→新slot映射。旧assignment/手册/prompt/schema/资产不修改，旧attempt与canonical不写入；首答内部继续用原schema的contract run/batch/scope常量，外围真实执行回执明确recovery_campaign_id和source_contract_run_id，避免把常量冒充旧执行身份。
2. 将[原CLI派发器](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/full4481-fresh-cli-dispatch-root/run_one_cli_batch.py:39)的读取及模型请求方式复用到新路由：完整既定batch、fresh ephemeral exec、gpt-6.1-sol/ultra、禁用用户配置/记忆/网页/代理。只机械替换逻辑标签与输出slot；原core request及实质prompt保持字节。绑定当前已成功运输的launcher、平台binary、package lock和routing overlay。
3. 采用新ROOT运输接收适配层，引用既有[v3严格接收器](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/full4481-native-execution-adapter-sol/root-validator-amendment-01/receive_full4481_batch_v3.py:1)及严格validator的约束。最小改动只有“submission必须位于原batch目录”改成“必须等于新恢复route map绑定slot”。原assignment路径合法性、schema、run/batch常量、严格JSON、整数类型、完整records次序/coverage、packet身份、逐字quote、允许资产、实际read_manifest、first/report/seal SHA均保留。不得用35条薄接收器，不准拆条拼批或在首答后修补缺证据。
4. 先执行原顺序第一个失败batch的整批运输及严格接收门槛，最多1并发。完整turn加35条薄接收器的历史成功不是整批通过；该完整batch只有在实读、证据、schema和封存均通过后才扩展到其余batch，总并发最多3。若模型/account再次系统性拒绝，立即停止新增派发，记录运输阻塞，避免继续消耗全部批次次数。
5. 读取应采用与实际工具输出预算相容的小段（例如最多4000 Unicode字符），显示路径和明确首尾区间；收到完整工具回复后才记录真正read_manifest。必要图像要有可归属实际查看记录；若CLI JSON不保存图像消息，保留额外真实呈现回执，不能仅复制packet的verified或SHA作为已读证明。
6. 新恢复轮每批首次加最多2次真正fresh整批技术重试；只选最早完整技术有效整批，保留所有失败和原字节。canonical与selection只写新恢复轮。结果可使297原成功batch与207恢复batch共同覆盖4481，但报告必须披露阶段与运输差异，不能叫原首次主运行从未失败或独立重复。

建议的接口是：new_dispatcher --recovery-manifest <新冻结清单> --original-assignment <原完整batch assignment> --recovery-attempt 1；new_strict_receiver --recovery-manifest <新冻结清单> --original-assignment <原assignment> --submission <新slot>/first.json --actor-completed。完整参数清单、必要回执字段和不可执行的合同提案见transport-repair-audit.json；它不是已经创建的命令或已经获得的完成回执。

本补充只读所有旧v3回执及207失败批的执行轨迹，未读取标签作语义比较、未重编码、未改旧目录。附加输入前后SHA见transport-input-seal.json和transport-input-integrity-readback.json；所有审查输出的最终SHA见final-output-seal.json。
