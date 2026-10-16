本次 batch-0005 材料 attempt03 已终止为 technical_representation_failed，保存 2/10 首件。核 parent seal 的实际 SHA/108780 B 和 74 个本次相关成员，未重复全 345 成员或大型来源套件。有效 schema、完整 fullR 与实际短启动分别实测为 d4063ee7…（75605 B）、0f093658…（28523 B）、e12ace36…（3662 B）；短启动文件 SHA 不冒称平台 wire initial-prompt SHA。

| 首件 | 有效 schema | 新 F 公共引文分支 | 具体失败字段 | 原 v4 scope | 已记录必要读缺口 |
|---|---|---|---|---|---|
| RECODE25-04915 | 通过 | 实际可表示 | 无 | complete / valid | 0 |
| RECODE25-00138 | 失败 | 实际可表示 | I.innovation_support.rd_object | complete / valid | 0 |

04915 的 F 首件内锚点与侧文件相同，pointer 为 /explicit_or_primary_source_resources/0/source_texts/3/text，Unicode span [0,348)。真实父资源 SOURCE-NHC-2024-EXPLAINER-38，snapshot SHA a316b256…；document_bundle view SHA f14c85a8…，连续工具返回 [0,6000)、[6000,11998)、[11998,12986) 共 12986 UTF8 B。逐块 raw/guard/emission 各自 SHA/bytes、相同 BEGIN/END、payload/原 view 字节、完整范围及同 view 的 recorded read/use 已核。

00138 的 F 引文 pointer /source_full_text_resources/3/text，span [169,235)；I 对象引文 pointer /source_full_text_resources/2/text，span [1911,1949)。两者原父 SHA 均 980acf76…，对应完整实读叶 5843/5962 B。三项公共引文均按原 source-quote.schema 和原 packet_builder.verify_source_quote 精确通过；当前/CTX 及嵌套锚点合计 13/10 项连续 span 核验通过。

第二首件唯一 schema 边界是 I.rd_object：它与旧 schema 相同，仅允许 current/context，要求 source_kind/context_id/field_path/quote/span。保存对象是实际公共 source-quote 五字段，缺前三字段并额外含 source_id/source_bundle_sha256/bundle_pointer。F 格式补丁已经生效，但未改变 I。公共引文真实性不使 I 字段合法；“仅公共来源能支撑”的语义必要性是 actor 自报，本审查不另判。

两个 scope 共 19 条完整 recorded read 收据的实际 raw 连续返回已核，重新调用原 v4 gate 与旧 scope-check 相同；程序转写/geometry 不称 pixel 阅读。原 native_records 对完整 10 packet 再核仍报 ordered batch scope logs incomplete/different。whole-output 仅有本次两个原首件；原始文件全体保留，不跨尝试拼接、不选最佳、不填剩余 8 条 0/null，不解除整批失败。

代码与读取界限另存：前两 instruction 外层 functions 默认 10000 tokens 低于要求 12000 的偏差被如实保留，实际首尾 guard 通过、未观察到截断。身份检查错字段、调度语法错误与原文定位 StopIteration 均有独立诊断及后续处理，不是已证实的必要来源交付失败，也未重写旧失败。实际 provider/model/config、初始 wire SHA、平台 compaction 与隐藏交付保证仍未知/null；未读取线程追加隐藏证明。

材料 3/3 最后一次；不允许 attempt04。本核查仅确认格式、真实源字节、保存的读取日志和机械接口，不评标签真值、指标、语义必要性或正式检验。未修改旧首件/source/manual/schema/gate/seal，模型/聊天/重试调用 0。完成即停止。
