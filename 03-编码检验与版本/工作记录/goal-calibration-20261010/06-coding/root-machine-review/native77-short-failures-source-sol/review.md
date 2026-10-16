# 原生77短启动两次失败的有限技术核验

本次为非盲AI技术/来源接口核验（GPT-6.1 Sol ultra）。本人此前参与A开发判读及来源恢复；本次未读取首件标签值、参照、性能或旧规则结果，未运行模型、重试或修改旧文件。

| 批次/attempt | 真实threadId | seal成员SHA/bytes | 已保存首件文件 | 未处理 |
|---|---|---:|---:|---:|
| batch-0001 attempt3 | 01a122fa-c09a-79e0-b706-435b39338e70 | 98/98吻合 | 4/13 | 9 |
| batch-0002 attempt1 | 01a122ee-8fb3-7010-81e0-7a224a9b0fc5 | 14/14吻合 | 0/2 | 2 |

两个目录均无seal漏列文件（seal自身除外）或缺失成员。首件和whole-output仅按不透明字节核SHA/bytes，数量由封存文件名、冻结批次元数据和技术诊断交叉核对，未重新核候选对象内容。详细逐成员凭据见review.json。

第一批真实失败记录为RECODE25-00045原快照终止正文不在原bundle字符串叶，source-quote.bundle_pointer与v4 additional_views.utf8_text无法合法表示该有限文本。四件保存的格式诊断均报item schema/currentCTX/publicquote valid，仍不能据此称批次完整：actor-status明确batch_complete/required_read_complete/scope_record_valid=false。来源已存在的说法来自失败诊断，本次未扩大读取正文验证。

确切接口条件是source quote五字段source_id/source_bundle_sha256/bundle_pointer/quote/span，pointer必须落在当前bundle原字符串叶且quote为Unicode连续切片；v4继承的additional view还要求scope_pointer所指原叶、真实resource/source SHA、UTF-8 view SHA与原pointer locator。原文件路径字符串不能替代文件正文。

另一个预先已记录的静态限制是evidence.I.innovation_support（字段必填、可null）；非null对象必须含rd_object、available_support、direct_relation，前两者source_kind枚举只有current/context，并要求context_id/field_path/quote/span、禁止额外字段。该JSON schema没有I3触发非null的if/then条件。它与本次实际source-quote/text-view失败分开记录；本次不推断候选实际采用何路径。

最小前瞻修复是把同SHA原快照的有界原文作为显式原text resource投影到新共同bundle，让已有quote/view接口指向真实叶；旧包和首件保持原字节。如果未来I3确需public-only支持，再于共同新schema为rd_object/available_support增加既有public quote锚点分支，直接联系证据要求保持原样。以上仅建议，未实施，也不新增旧attempt验收门槛。

第二批保存的packet-inspection-001诊断报告两层工具输出截断（原token count 92533与12027），完整source ranges为null、read receipt为0、格式检查未执行。原始平台response未存、event_id为null，因此仅确认保存的警告摘录/事件描述，不声称已验证平台原始响应或完整阅读史。

创建return的外部匹配本次未另核，actor状态为pending；不可见provider/wire/历史保持unknown。未评估七批全部封存gate、未做任何性能比较。原始首件及失败封存保持不变。
