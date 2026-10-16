# 原整批汇总快照：独立只读对账

**快照对账通过；2168条都来自所选完整批次首答，值未改变，没有混入35条薄语境结果或人工参照标签。** 本审查没有重跑collector、调用模型、改变标签或选择。

| 来源 | 完整批次 | 记录 |
|---|---:|---:|
| 原冻结轮有效首答 | 297 | 2132 |
| 原既定批次的另存运输恢复 | 3 | 36 |
| 合计 | 300 | 2168 |

独立核对了全部300批，而非抽样：原成员和顺序、真实所选attempt、slot、receipt、seal、first、report、selection及原canonical镜像绑定均相符。每条汇总dimensions和labels逐项等于所选原首答，不存在跨attempt拼接、重排或变值。首答使用同一冻结manual/prompt，全部为batch语境，请求gpt-6.1-sol及ultra。

10840个已覆盖维度中，10801个为二元值，39个为合法null。所有二元决策至少有一条逐字packet证据；14675个packet pointer/quote/role逐条核对，零引文或角色pointer问题。各维度正、负、null数量及完整二元记录数与coverage.json重算一致。null没有转为0，未输出部分没有转为null。

7个首答缺少schema可选的attempt_number字段，分别为原轮5批、恢复2批；必需receipt、实际slot和selection中的attempt链均完整。不能对此事后追加要求，或触发重试。

快照仍缺204批、2313条及11565个维度；其保存的状态为201批未派发、3批在途。该状态属于coverage.json所载真实UTC时点，不是审查时或后续运行中的最新状态。目录名字中的1515不能替代报告时间。

快照的五个输出均与自身seal相符；5013个实际来源/输出输入前后哈希无变化。收集合并工具中的source identity、唯一记录、原顺序及whole-batch来源限制，与真实快照逐项吻合。人工77参照标签与35条薄语境补跑均未成为收集来源；同ID的合法原整批native结果不因曾属于参照集而被排除。

可用：截至快照时点，冻结原整批生产编码与另存运输恢复结果的真实覆盖/缺失记录，供后续完整收集。不可用：4481条已完成证明、正式准确率验证、独立重复实验，或服务端模型身份已核实的证据。本审查没有独立重建原297批所有模型实际阅读过程；三批恢复的实际呈现限制另见pilot-completed-independent-audit-20261011-sol报告。

详细计数、7个可选字段缺项和限制见report.json，全部批次绑定见selected-batch-bindings-audit.json。输入/输出哈希见input-seal.json、input-integrity-readback.json、output-seal.json。
