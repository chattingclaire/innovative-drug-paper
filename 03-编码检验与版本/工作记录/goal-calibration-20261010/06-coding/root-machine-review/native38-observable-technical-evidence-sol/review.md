# 旧native38候选的可观测技术证据审计

本次只审旧batch4（22条）与batch7（16条）的技术事实，未改旧receiver、gate、attempt、pending或首判，未读参照或指标，未裁定标签，也未认证allcomplete_valid。依据ROOT已保存的真实read_thread返回；没有新增read_thread调用、模型运行、框架或测试套件。

两批身份pending已有真实工具补证：commandExecution返回的CODEX_THREAD_ID分别为 `01a122ee-a55b-7613-a663-e00794aa0967` 和 `01a122ee-c249-7be0-b975-539f78f8cee4`，均与实际create-return匹配。两个create-request的prompt、工具delegation的`<input>`和各2186B封存短启动文件逐UTF8字节相同。工具展示了实际初始任务，不展示供应商完整wire/system/user隐藏历史；不能将“初始输入已核”扩写成“隐藏历史全部已核”。

| 观测对象 | batch4 | batch7 | 本次核查范围 |
|---|---:|---:|---|
| 完整R指令实际返回 | 163983B／28块 | 159939B／27块 | 每块与冻结文件相同字节、SHA、连续范围0至EOF；非仅hash或load |
| 手册v1.3 | 42941B | 42941B | 两指令均为字节区间[4361,47302)，实际返回完整覆盖 |
| 必要语境schema | 13275B | 13275B | [51227,64502)完整覆盖 |
| 输出schema | 74543B | 74543B | [64531,139074)完整覆盖 |
| quote schema | 1043B | 1043B | 两批各有单独的完整真实工具返回 |
| 当前正文与全部CTX | 22条／127节点 | 16条／71节点 | source_record逐值对应原纯来源包，固定顺序相同 |
| 原图查看记录 | 2个imageView | 2个imageView | 路径与实际资产SHA可绑定；不冒称provider图片wire已认证 |

batch4首条01562的完整packet实际返回12726B，与原包相同，结束标记在可取回文本内；该read_thread command输出达到20000字符并标truncated，截取发生于后续scope尾部。它证明审计摘要尾部不可完整取回，不能证明actor原工具来源包交付被截掉。其余21条是完整source_record的SOURCE_CORE视图；共享原文另有6169B叶节点实返，绑定01729/02233/02269同一可用资源。长公共材料在core里可能仅有pointer概览，未据此宣称actor读完所有可用资料。batch7的16个完整packet逐UTF8字节相同，packet结束标记齐全，没有saved read_thread command输出截取标记。

本次没有发现上述当前正文、CTX或完整指令的可观测缺尾／错配。额外材料是否在语义上必读不由本技术审计裁定；资源可用、实际返回读入、声称使用与真实语义使用须分开。实际返回完整也不能证明认知使用或判断正确。

原有第三条pending仍不能改成全局false保证。两个保存历史均是read_thread可访问的一个completed turn（page.hasMore=false），这只覆盖该工具能展示的turn/item摘要。工具没有给出provider完整wire历史、隐藏compaction事件或隐藏截断保证；这些保持unknown/null。batch4有一次可观察的optional签名内省异常（ValueError），不属于来源内容读取失败。batch7自存technical-event记录TextEncoder的post-return bookkeeping异常；本次能独立核实前面的来源packet完整返回，不将该自述异常提升为来源失败或供应商证明。

建议未来操作判定分列“真实runtime／冻结启动payload／必要材料实际返回范围”与“工具不提供的供应商信息”。必要view若实测缺尾、未返回或hash错配，应记该view的技术缺口；隐藏信息缺失不应伪装成文本或标签错误。若据此调整操作判定，应作为前瞻方法变更，保留旧三条pending及旧结果；本报告没有替旧候选解除gate或宣布allcomplete_valid。

审计边界事件：一次命令过滤漏掉转义JSON形式的commit脚本，工具输出意外展示少量旧候选判断文本。随后排除所有commit/labels持久化命令；未引用或使用这些值，不作盲审声明。报告不含标签、维度裁定或性能计算。

全部证据事件ID、指令块范围、38条源绑定、原图资产和71个实际文件SHA/bytes见[review.json](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/root-machine-review/native38-observable-technical-evidence-sol/review.json)。71个输入绑定在审计结束时再次核SHA/bytes相同；原件保持只读。
