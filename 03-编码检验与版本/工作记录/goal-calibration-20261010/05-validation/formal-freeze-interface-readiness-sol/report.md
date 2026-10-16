静态接口核对已完成。正式手册1.3F若只编辑标题/状态，新的SHA可以由现有字段表示；当前三个已封存入口不能仅替换手册路径就直接启动正式800执行。需要前瞻性的新绑定与少量入口/形状兼容修改。此报告未运行规则、LLM、真人接收器或任何800编码，未读取800未曝光正文。没有提供最终1.3F文件，因此它的实际SHA及逐字差异仍未知，不能声称已经接通。

| 流程 | 已存在真实入口 | 新手册SHA | 当前具体阻塞 |
| --- | --- | --- | --- |
| 规则 | v17 runner.py --scope --scope-sha256 --out | scope.manual 与 material_bindings 支持精确新路径/SHA/bytes，并写入actual_source_material_identity | runner.py:192锁定本实现目录、未存在的run77-first；该目录已经存在。213–214期待裸完整bundle和预声明ID顺序，不能直接读真人五键wrapper。198等开发77身份/名称需另版准确绑定。 |
| LLM | v3 packet_builder.py build --binding --binding-sha --authorized-order --order-file-sha --manual --manual-sha --budget --budget-sha --out；R1 receiver.py接收actor seal | v15 output-item.schema的manual_sha256仅64hex；receiver实际比较plan.manual_v1_3.sha256 | v4 import读取固定native-binding.json，校验旧手册；receiver固定旧PLAN/SHA/NATIVE/HOME。旧builder仍检查v13全框hash/profile，且从自己的旧output schema文件读取，不能凭--manual把v14和v15格式一起接入。 |
| 真人 | workflow.py verify/seal --packet-dir --labels --submission；seal再加--destination | 旧manifest.manual_sha256与submission字段可表示任意精确SHA，但旧入口固定manual.md | 新800的manifest、五键嵌套packet、四键空表和submission均非旧draft1形状，实际verify/seal在read_packet即不兼容；目前仍未release、身份未分配。 |

旧“8root”需要准确区分。workflow.py:206的八个键是旧扁平source_record：record_id/unit_text/unit_source_ref/source_title/contexts/attachments/material_status/neutral_material_note，这一条用于prepare的来源校验。接收器不是只依赖此prepare检查：verify:555和seal:613都会调用read_packet，459要求旧manifest精确键，461要求manual.md，467再要求旧十一键扁平packet。因此，八键那行本身不是verify的首个报错；旧接口形状确实会阻止当前800接收，不能宣称“8root只影响准备，所以现接收可用”。旧五键labels_row及八字段dimension也与现表不符（482、584起）。

实际800元数据与空白表已按A/B分别核对：各800行、4000维，全部completion_status=unfilled且value=null；这些是占位而非合法语义null首判。manifest使用record_N/dimension_blank_N/manual{absolute_path,bytes,sha256}/packet_file等；packet外层由已封存生成器238–240行明确为packet_version/blind_id/source_bundle_canonical_sha256/source_bundle_canonical_UTF8_bytes/source_bundle。没有打开两份packet.jsonl或shared-source/common-source-bundles.jsonl。其source_bundle内原值/原文是否逐条符合未来执行仍不由本报告认证。

最小前瞻接入修改如下，均应在新版本中做，旧文件保持只读：

1. 联合release绑定：提供真实正式1.3F文件，记录新path/SHA/bytes和准确版本状态；新规则scope、LLM计划/runtime binding/实际完整指令、新真人manifest/submission使用同一字节手册。旧pre-draw-freeze和旧开发手册绑定保留作历史，另写release关联，不重抽800或改源正文。800现status、real_executor_assigned=false、identity_registry=null、final_release_freeze_completed=false应保持真实pending，直到实际落实；不能把metadata改名当作真人已执行。
2. 规则：复用v17源adapter和receipt resolver，另版有限driver把77固定输出名/身份元数据参数化；输入使用完整共同裸bundle，或逐条只解外层source_bundle，保留原嵌套对象与SHA、独立记录packet文件/行SHA。前瞻scope明确800顺序、数量、共同源seal和新manual binding；不得令已执行的run77-first重新变成未执行。asset index中的absolute_path字段转换为resolver的path并绑定实际原路径/同SHA副本，原snapshot、text-resource相对基准和定位不猜补。source_receipts.py:65–76对真实文件绑定的校验应保留。这里不宣称133源文件或800条都已被规则实际读取。
3. LLM：在原receiver上增加显式plan/path/SHA、native root和report root参数，复用原首件/whole顺序、真实creation request/return/runtime和source quote校验；新plan指向v15 schema（3b361770…，88623 B）、原source-quote schema、新manual和新公共来源绑定。v4 overlay的binding文件也必须允许显式新路径，其纯scope/read/use算法可保持。旧packet_builder的v13 hash/profile接点需绑定真实v14 owner/相应形状或复用已有v14保真包装路径，不能只换manual参数；不要重新扫描整框。现800真人wrapper到native wrapper需要明确source_id、output_id、source_bundle_sha256等元数据，原source_bundle不得扁平丢失。旧gate:61强制B-原编号，这条可按既有model协议保留、真人blind_id另绑，不能直接把A/B的800随机序号冒作原source_id。source-quote的五字段pointer/span验真保持；format-binding本身不是新运行plan。不可用未证实平台史编造false，不增加telemetry缺失门槛。
4. 真人：在现workflow的接收/封存函数添加明确v14-wrapper版本分支，保留完整source_bundle，通过现v14 source index及五字段public quote验证当前/CTX/公共源证据，不仅在prepare里放宽八键。映射manifest的manual路径与SHA、数量/packet hash/身份/首判状态，映射submission字段和labels根绑定；保留全包SHA及嵌套bundle SHA不同用途。现表没有旧image_evidence/path_evidence/material_requests，且有source_quotes/单数material_request，必须在前瞻完整表单/schema中明确I3三证据、具体F路径、实际图/同view读取使用及合法null请求的保存位置；不能靠删旧校验接受缺证据，也不能伪造CTX来容纳公共全文。旧check_evidence:523–535只接受current/CTX/image，单纯表头重命名无法接公共源。沿原首判不可覆盖、身份与独立性管理，补材重判另轮；这不新增定义或验收门槛。

以上是已有接口的具体兼容修改建议，未创建另一框架或修改代码。某个shape接点不兼容不说明所有源或标签错误。现有空表没有真人首判，不能被“接收通过”。正式手册新SHA、真人身份、release以及未来新入口实际执行均待真实落实；本审查只证明静态接点，不宣称正式冻结、真人验证或模型执行完成。

身份：AI pilot01_a_sol，已有开发判读、来源恢复和v15/v16/v17规则工作历史，非盲接口审查。请求模型gpt-6.1-sol、ultra；实际provider模型/推理设置未独立可见，记unknown。模型/规则推断/接收执行/语义标签/800正文读取均为0。输入出处、原文件SHA与具体行见evidence.json，实际读取范围见read-ledger.json。
