七个原始首件全部保留，逐记录机械验证均通过；未挑选、重判或修改首件。

| 原记录 | schema/实际packet | current/CTX/条件span | public quote | v4逐条scope | 已记录必要read缺口 |
|---|---|---|---:|---|---:|
| RECODE25-00005 | 通过 | 5/5/5，通过 | 2，通过 | 通过 | 0 |
| RECODE25-00036 | 通过 | 5/13/2，通过 | 3，通过 | 通过 | 0 |
| RECODE25-00038 | 通过 | 5/13/2，通过 | 3，通过 | 通过 | 0 |
| RECODE25-00045 | 通过 | 5/13/2，通过 | 4，通过 | 通过 | 0 |
| RECODE25-00086 | 通过 | 5/10/0，通过 | 0，通过 | 通过 | 0 |
| RECODE25-00099 | 通过 | 5/15/3，通过 | 0，通过 | 通过 | 0 |
| RECODE25-00902 | 通过 | 5/6/0，通过 | 0，通过 | 通过 | 0 |

验证使用原output-item.schema和source-quote.schema、实际v14 batching-manifest外部packet SHA/bytes，以及原packet_builder.verify_source_quote（current/CTX条件anchor仅适配精确原pointer）和v4 gate.check_scope。每条首件、scope、packet的原ID/完整bundleSHA/manualSHA、同thread/run与文件身份均相符；已有12项public引文也核原连续Unicode span/pointer及其记录read链接。空public quote不自动当缺证。全体7行技术状态为all_valid_per_record_mechanical，具体失败/缺证均0。

b1原partial whole仅6/13、b3仅1/3首件，仍保持原known_compaction技术失败/整批未完成，剩余9条不补0。原native_records.check_saved_scopes要求整批完整candidate与精确{scope_log_files} manifest；本审查仅逐记录核其ID/file/thread/run契约，不伪造或调用partial替代整批接口。b3现存manifest形状不符合该整批接口，旧scope-check空/validator未跑状态原样保留；新逐条检查结果只封存在本目录。

机械引文与scope记录通过不证明语义正确、必要性、同版关系或实际认知阅读；不声明正式接收、完整77、人类/RWH稳定性或解除旧gate。独立00902复核亦确认5 current+6 CTX连续span通过及原packet字节一致。未读参照/指标，未调用模型或重跑全部382/472来源成员；无旧文件修改。有限完成即停止。
