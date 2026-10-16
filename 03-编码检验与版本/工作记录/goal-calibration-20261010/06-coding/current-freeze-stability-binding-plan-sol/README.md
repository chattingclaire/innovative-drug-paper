本方案安排新的诊断 R1、R2、R3、W、H，复用已抽取的固定 800 条。现行全量 P 不追认为 R1：其运行清单明确把稳定性验证分开，实际使用 native 首批与 fresh CLI 后续批的混合运输，且未事前绑定本诊断样本、批次和中性首行。P 的原初判与真实技术重试全部保留。

这是一份准备方案，所有实际执行由 ROOT 之后统一 GO。本轮未启动模型或规则推断，未读取真实预测、参照、标签或指标，也未实现或重跑旧测试。

固定样本、顺序和批次

只使用 draw-contract.json 已封存的 800 个 source_id（remaining600、exposed200；NMPA384/NHSA340/NHC76），不重新抽样、不增加真人量。ID 的 UTF8-LF SHA 是 `97e142eb4e79650f8833086ab465913e3545d90ff581d5702005f093f5f655e4`。pi_exact、weight_exact 来自原 mapping.json，解析为 Fraction；既有开发曝光身份不得改写成全量盲验证身份。样本选择不读取任何真实输出。

按 800 条在原全量 FRAME 中的顺序，重新应用 P 原贪心分批算法：最多12条、原始序列化 packet 文件字节合计不超过260000；单条超限保留单条。元数据计算结果为 **87 批**，每批 1–12 条，原 packet 总字节 14065070、最大批字节 258629。plan.json 已列全部固定批成员。本诊断分批与 P 不同；351个稀疏交集批不采用。五条件均使用同一固定批划分，W 格式增量不重新分批、不删成员，读取分段按实际材料记录。

条件与真实 CLI 执行

R1/R2/R3 是三次完整、独立诊断条件；R1 为诊断第一结果，R2/R3 为重复。W/H 分别与 R1 比较。按 R1→R2→R3→W→H 派发，各条件批次按固定顺序；异步完成不改变样本、次序或成员。并发仅为 ROOT 的执行容量，不是重复次数。

共同 manual.txt、execution-prompt.txt、common-execution-protocol.txt 及来源修订保持原字节。所有条件仍请求 gpt-6.1-sol / ultra。沿实际 fresh CLI 方式，每个真实 attempt 是新的 codex exec 进程与 thread：ephemeral、ignore-user-config、不开 resume/fork、memories/subagents 关闭、web disabled、docmax0。temperature、top_p、seed 当前未提供，登记 null/未暴露；抽样 seed20261010 不是模型随机 seed。记录真实 argv、请求、进程完成、事件、thread.started ID、stderr，不伪造 collaboration 代理或原生 tool 回执，也不把文件 SHA 说成 provider 身份认证。

R1/R2/R3/W 请求第一行固定为 `判读要求`，H 仅替换为原预设同义行 `判读说明`，都是 UTF8+LF；首行放在前瞻诊断请求 wrapper 的最前面。之后 CLI overlay/core 完全相同，原 frozen prompt 文件不编辑。当前 prompt 自身第一行是正式标题，旧候选在 prompt 文件上强制匹配“判读要求”的实现不能直接使用；修改为检查 wrapper 首行与移除首行后的共同 core，即可落实原 H 首行措辞要求。实际输出槽等 route envelope 单独保存为请求外操作元数据，原始完整请求同时保留，不能宣称五条件包括不同槽地址在内的全部发送字节相等。

W 仅把同一原 packet 严格解析后用 `json.dumps(parsed, ensure_ascii=False, allow_nan=False, indent=2)+LF` 输出；不排序键，不改数组顺序、parsed object 或任何解码后字符串。R1/R2/R3/H 保持原 packet 原字节。W 的物理文件路径/SHA 及 read_manifest 合理变化单独绑定，source_bundle 与合法语境内容保持一致，不复制新政策来源或生成新的盲包。本轮没有生成 W 文件。

每批每条件最多3次真实技术 attempt（2次重试）。首个技术有效整批答复即冻结，包括合法 null；不为 null 或条件间分歧重试。原整批 first.json 保留原字节，所有真实失败、事件和接收原因都保留；不得跨记录或 attempt 拼装。first.json 是 actor 写出的结构化首答，不冒充 provider wire。每个派生记录只指向该整批原件的 `/records/n`。若无 block/重试，五条件共 435 次批调用；全批都3次的上限为 1305 次；这些是批调用/attempt 数，不是 provider API 调用计数。

来源与旧接口的最小兼容修改

旧 native-v17 adapter 尚未生产采纳，其 closed-source-schema、mandatory complete 和另建 CTX/asset/text location graph 是候选接口限制，不能升级为本研究新的验收门槛。当前 v15 packet schema 和真实来源 inventory 可直接复用；schema 放在 development77 目录的路径只是冻结来源 schema 的存放位置，不读开发预测。来源版本、packet 内容、语境、附件及缺失定位事实按现行材料继承。pending 有具体理由即可如实保留；pending 不强制 null，必要材料缺失是否导致 null 仍完全由共同手册决定。

接收侧使用已修正 production-binding-v2 技术 validator，保留整批 ID/次序/N、0/1/null、非空理由、packet 指针连续引文、asset 与 source_id 绑定、read_manifest 现有检查。source SHA 证明字节绑定，不证明实际阅读、像素/转写一致或语义充分性。不建新的来源资格图，不假造来源 complete、文字视图、预填收据或真实阅读记录。原预检披露的9个缺失 relative page_asset 定位保持原事实，现有 PDF/全文绑定不猜路径。现行技术接收判断是本方案的接口基础；不能宣称额外资格检查已做。

具体改动位置及字段见 plan.json 的 minimal_future_mechanical_changes（6项）：v17_adapter 的 CONTEXT/source/plan/qualify、H/W 绑定比较、CLI dispatcher 的 campaign/condition/batch 路由参数、CLI ledger evidence，以及 terminal 后统计投影。旧 v17 中 `fork_turns=none`、native creation receipt、强制 original validator SHA 与 closed-source graph 的检查应分别替换为真实 CLI 回执、当前修正 validator 与生产来源接口，不做静默 bypass。当前新增 `campaign_scope_metadata_binding` 也必须明确按绑定允许读取。

前瞻 assignments、输出 schema 的 campaign/batch/N、共同 actor 指令以及每条件三槽 route 在 ROOT GO 后、任何诊断实际派发前一起绑定；它们是运行元数据，旧 P 包不改。R1/R2/R3/H 可复用同一共同 assignment；W 只叠加格式化 packet 物理绑定。runtime route 与条件号的映射由 ROOT 保存，不把 P 的 run_id 或旧答案注入上下文。普通技术接收状态、真正 zero-call block 理由和三次耗尽故障如实终止，不能把未派发悄悄删除。

数学与末态

只在所有计划 R1/R2/R3/W/H 批次达到末态并分别封存后比较；此前仅进度/绑定，不生产 pair/triple 指标。statistics_bridge.py 保持 SHA `5c51a23bd4613307295c4b0656aca818a9312c01f10d88ee39a7eea6d6ad8f4c`，vendor/stability_engine.py 保持 SHA `4e4bc00ef8f2d5e9d69b99841c18642bbb8919fbea83601d52c61816aca98e6d`；不改数学。比较固定5对 R1/R2、R1/R3、R2/R3、W/R1、H/R1 和 R1/R2/R3 三条件，报告逐维/逐条与五维向量稳定、κ、阳性数及变化，并保留 full800、registered remaining600/exposed200 的固定域口径和精确原权重。联合二元分母只含相应共同二元单元，null/技术故障/未调用计入覆盖和排除，双null或相同 null mask 单列，不能当二元一致。批次/重试不算独立重复，R1也不是参照真值；不加分数阈值、不据输出临时选域或代替分类效度。

规则同输入字节复现

最小安排为未来另获 ROOT GO 的两份 full4481 max1 授权，复用现行 driver、prepare_scope 和全部语义文件原字节，不引入800 driver。两次使用同一 full v15 JSONL/manifest/seal、4481顺序、manual/prompt/protocol、v12阅读代码及当前 v2 source inventory（含实际 runtime descriptor）。每次另建父目录、独立 release/授权与输出路径，但输出 basename 同为 `run4481-first`，保持 driver 从 out.name 派生的日志 run_id 一致。各 release 仍 max1，不复用原生产授权，也不把 runtime descriptor 技术重启算重复。

两次真实末态后直接比较完整原 predictions.jsonl 的 bytes/SHA 与首次差异，包含 null、异常、引文和关系痕迹，不归一化删除差异来造一致；再报告固定800顺序的原记录投影。execution 时间、目录和审计日志自然不同，不能声称整个目录字节复现。差异若发生据实保留；本轮没读现行 run4481-first 任何输出，也不宣称规则已复现。

封存范围

精确既有文件路径、字节和 SHA 见 input-bindings.json。plan.json 是本方案的机器可读正文和固定样本/批次元数据，README.md 是同一方案的说明，seal.json 仅封存这三个新文件。本轮没有新执行代码、答案、盲包或 receipt，也没有修改任何旧文件。独立接收 audit 原 seal 保持 `226ffb9d84007283a82be68780709a7cd1c4dbfe3436747a9690cb6659c213ba`；先前另存的 audit-addendum-seal 为 `c852bc7ccda412fb7f9593e21f4a9266aff9b42495d639f9d30d051ceb6de41a`，没有刷新旧 seal。
