# 三个完成试点：独立只读审查

**三批原完整批次首答均通过独立严格接收，没有发现需重编码或技术重试的阻断问题。** 0296、0299、0300各12条，均选择attempt 1；没有合入人工77或35条薄语境结果。本审查没有调用模型、改变首答、标签、接收记录或选择。

| 批次 | 条数 | 0 / 1 / null | packet引文 | 补充资产引文 | 真实输入绑定 |
|---|---:|---:|---:|---:|---:|
| 0296 | 12 | 51 / 9 / 0 | 89 | 8 | 28 |
| 0299 | 12 | 52 / 8 / 0 | 87 | 7 | 29 |
| 0300 | 12 | 51 / 9 / 0 | 150 | 0 | 28 |

用ROOT修复后同一system Python与jsonschema独立重跑只读guard，结果与保存的root-reception-v3.validation逐项相等。三批first/report/seal、process/events/stderr、reception、selection及全部真实输入绑定字节与SHA相符。每批恰有一个fresh thread、一个完成turn，进程正常结束。首答必需身份、records及既定成员/顺序相符。

全部180个0/1都有至少一条逐字packet证据；326条packet引文的pointer可解、引文逐字匹配，current/context角色与pointer及所给context_id匹配。每个维度都有当前记录正文证据。15条补充资产引文中，10条文本引文逐字落在真实呈现的限定范围；另外5条跨页PNG引文由审查者独立打开绑定原图，字形均相符。此为证据精确性核验，不是标签语义正确性或准确率验证。

原assignment的成员、顺序、手册、prompt、全部packet、资产绑定、batch语境及请求模型/effort保持一致。所有可核read_manifest文本范围均找到真实stdout逐字依据，没有范围/顺序错误。manual与prompt在packet之前完整呈现；各12个packet按既定顺序完整呈现。日志未见自行运行validator、重答、读取旧尝试/同伴/参照或保存首答后的反馈修订。

0299的schema外层截断自述涉及[39000,65000)、[97500,110500)，分别在CLI第20、24行逐字补呈现；0300涉及[19500,32500)，在第26行逐字补呈现。排除原被自述为受影响的块后，schema仍完整覆盖[0,310418)。CLI aggregated_output本身完整，不保存外层functions.exec警告及实际工具反馈预算；因而补读内容可核，截断次数、70/3454/1469 token数量及模型实际收到的所有反馈范围仍仅来自actor自述。

0299声明两张PNG为full_image，但CLI没有独立view_image结果。审查者核对原图可以证明引用精确，不能倒推编码模型实际看过原图。0296 DOC和0300 PDF使用文本提取，未冒称视觉阅读。三批argv明确请求gpt-6.1-sol、ultra；实际服务模型身份及provider wire均未独立核验。

0296和0300的seal没有显式template_only字段；原v3和本guard规定缺失默认false，因此合法接收，不能把它们写成“显式四标志全部存在”。0299显式false，三批actual_completion_claimed均为true，run_id/batch_id均正确。后续v4 dispatch已明确规定四标志，不能事后追加更强字段要求而重试这三批。

原薄receiver因ROOT缺jsonschema误判，触发三个冗余attempt 2。原错误回执与记录保留；修复记录明确是ROOT依赖问题，重核原attempt 1，未重生成或按语义挑选。attempt 2均无首答，缺少终结回执；停止记录仅确认发出SIGTERM，原退出码未知。本审查只读核对其4个进程组当前均无存活进程，不补造终结回执。

可用：作为独立运输恢复轮的原既定整批生产首答，与原有效整批保持来源和轮次记录后收集。不可用：作为全部4481已完成、正式准确率验证、独立重复实验，或服务模型身份/模型完整视觉阅读已独立证明的证据。合法null本身始终不能触发重试。

逐维证据见decision-evidence-audit.json，实际范围和接收链见strict-reception-and-presentation-audit.json，补读核验见schema-truncation-repair-audit.json。4628个此前冻结输入均保持一致；本次4681个输入前后哈希无变化。最终输入/输出封存分别见input-seal.json、input-integrity-readback.json、output-seal.json。
