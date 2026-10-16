本组件已完成有限参数化接入，未启动新 campaign。实际 runtime-binding SHA `4a7a6f9c65cc99a7a81e6c1df29511fb761f9a9c74d31e8c663552147b051a4f`。正式 manual v1.3F 为 `a0ef2967ef964c625f331fefa82f4020d384ecae579e2a0a7d178651e8beda70`（42660 B），公共 quote v15 output schema 为 `3b361770b6a708d3d5568cf39bfd15e5883743697ceedccffb008a1632ade3c7`（88623 B）；builder 已读取该实际 schema、核 SHA、校验 dialect 和共享 quote 定义。相关实物均由原 component seal 成员表绑定。

`builder.py` 使用显式 `--binding/--binding-sha`，binding 内分别指定 source_profile/source_index/schema/manual/budget/protocol 的绝对路径、file-byte SHA 和 bytes。新分支读取已有 v14 frame identity 表和现 full800 共享来源索引的元数据；从真实 common-source JSONL 按该索引的连续 byte offset 取一条完整 nested bundle，逐条核 canonical SHA/bytes、当前正文与 CTX 身份，再沿原 resource/asset 检查及 packet schema 包装。十根键与可选 extension 不丢失。原 v13 路径和旧 v4 binding 可原样使用。没有生成新 profile 或扫描 4481 正文。

source_id 保持原 `RECODE25-*`，模型输出 `B-原数字ID`；真人 blind_id 作为独立 provenance，不能替代 source/output 身份。`unwrap_human_packet` 保留整份 source_bundle，不将 source_record 扁平提取。来源 metadata/文件 hash、解析或 producer 收据不被当作 actor 实读/实用。此轮只读 source metadata，未解码 full800 共享正文；common-source 全文件 SHA 依据已封存 producer 成员绑定，未来实际 build 在 lookup 前必须重核实际全文件 byte SHA，逐记录还核原 bundle SHA。

`necessary_read_gate.py` 显式 configure 后才加载组件。原 v3 check_scope 与 v4 三个纯函数体保持复用；原 scope schema、uniform protocol、pointer/span、source 身份、required/use/read、None available-unused 边界未变。源 inventory 的加载延迟至真实 scope 检查，因此组件 controls 不执行 source lookup。`native_records.py` 直接复用原 check_saved_scopes/select_technical_receipts/telemetry/all-batch guard；旧 max=3、首完整技术有效顺序、禁止选最佳/跨 attempt 拼接保留。

`receiver.py` 显式接收 plan/plan-sha/native-root/report-root/runtime-binding/SHA/scheduling-root。实际 plan 对 manual/schema/quote/scope 与 runtime 的路径、SHA、bytes必须一致；实际 creation-return/runtime UUID、actor seal 全成员、short wire SHA 与 long instruction SHA、whole/first 对象及顺序、外部 history/known truncation/compaction 原门槛仍保留。未知保持 null/pending，不能用自报补成 false。receiver 仍限 R1。原材料 13 上下文历史与已耗尽 attempt 状态不被此组件变更；Root 另行决定是否组织未来执行。

启动模板仅参数化真实 runtime/attempt namespace 和新版表示 schema。原首件 xb/identity/history/quote/read/scope/whole/seal 保存流程保留。6000 UTF8 B helper 原字节复用，单工具及 exec 输出额度至少12000 tokens；真实 end marker/连续 delivery 与 semantic read 分开。full instruction 与短 initial launcher 分别绑定 SHA；未来 build 规划一个记录一个新上下文，完整 wrapper/transport/schema/manual/source 最坏字节仍计入原 budget。新 launcher 代码强制 ≤4000 B，本轮未生成任何真实 launcher/输入包/actor 输出。

有限 controls 共 19 项通过，覆盖实际新绑定与旧绑定复用、错 binding/schema SHA 拒绝、原 quote pointer/同包 SHA/必填拒绝、真人/source/output 分离、原 xb 字节不可覆写、原首件顺序/unknown 守卫静态保留和 v4 纯函数体相同。控制仅构造接口值，无标签候选。初次静态断言使用了错误变量名 needle（key/k），已如实记录修复；没有修改对应原守卫。后续计划/runtime一致性与 legacy receipt-blank 分支仅作语法/静态检查，未模拟 actor 接收。

本轮实际模型调用、对话创建、输入包和 actor 输出均为0。没有重跑 old wholeQA、bootstrap 或来源大套件，没有读取参考标签、性能或800未曝光正文语义。真实 full800 build、scope/receiver 全流程、实际来源读取和外部 creation/lifecycle/history 仍待 ROOT 另行冻结与授权；本组件 seal 不表示联合发布、RWH稳定性、人类检验或正式验证已经完成。
