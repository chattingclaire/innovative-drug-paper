本目录是 GPT-6.1 Sol ultra 的非真人规则技术候选。手册仍为冻结共同手册 SHA `5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b`。未修改冻结 release、生产首答、原材料或既有审查文件；未读取正式 LLM 全量部分输出。AI 复审建议是开发诊断材料，不是真人参照或金标准。

五个 coder 模块从 `full4481-rule-production-adapter-sol` 复制，原文件 SHA/bytes 在 `frozen-origin-bindings.json`。`source_packet.py`、`source_receipts.py`、`evidence.py` 逐字节保留；本分支只在 `dimensions.py` 和 `relations.py` 新增 S/E/Ec 执行关系与消费者限制。I/F 实质函数保持原字节，成功接收的 800 条 I/F 结果均没有变动。中性材料投影未接入，未新增共同源材料。

已实施：

- S/E 识别药物风险、实际安全性/效果信息内容、风险获益与否定/条件关系，区分报告递交及学科/研究状态；E 排除孤立 PK-PD、没有标准治疗、证件有效性和既有一致性评价身份。
- Ec 识别报价、支付意愿、价格评估职责、预算约束、费用与支付内容核验、实质支付授权；排除字段/格式/签章、目录甲乙归类、一般谈判阶段、主动申报支付范围调整的品种身份及纯支付范围标题。
- 补充明确同段风险响应、指标/费用数据/负担说明/终点与对照的有限关系，以及已交付原包的操作性条文/章节条件。消费者限 S/E/Ec；不把 I/F 支持机制扩给该三维，不继承无关兄弟条款。

42 个合成正反例在执行前固定预期。`semantic-selfcheck.json` 保留首轮 4 项失败；修正后 `semantic-selfcheck-attempt2.json` 全部通过。覆盖负面/不确定/条件/例外、混合手续与实质要求、身份/字段/PK-PD排除、有限条文与故意缺最后成员等。合成控制不是政策标签效度或正式验收。

候选代码在 `candidate-seal.json` 封存后仅做一次 800 开发语义回放：`development800-first` 恰好 800 条，785 通过引文/源视图核验，15 因旧库存缺来源 SHA 而停止。15 的原 FULLSOURCE payload 已含 `source_pdf_sha256`；冻结 `source_receipts.resolve_inventory` 以既有源原件和原转录 payload 的精确绑定补充库存身份，不改变源文字、可用视图或读取/使用状态。诊断在 `technical15-diagnosis.json`，许可和输入绑定在 `technical15-scope.json`。

按 ROOT 明确授权，仅这 15 项进行了一次同语义技术回放。`development800-identity-reception` 同时保留接收器首版把库存桥过度调用到 785 项、造成另外 69 项未绑定原件接收错误的结果；这些 69 项没有重新判读。最终 `development800-identity-reception-v2` 只机械接收原 785 项，并复用已保存的 15 项技术回放结果，没有调用 judge；800 全部源视图和逐维字面引文核验通过。原首轮、技术回放、失败接收版均保留。

候选修复尚不完整。原包未闭合提供的附条件/优先/暂停标准、PRO 定义、实际竞价结果价格期限等需要共同材料接口处理；还有中文邻接 AE/ADR 词边界、定性“安全有效”、直接支付父谓词以及完整条件总领等尚未覆盖的执行关系。具体清单见 `remaining-dependencies.json`。这些不能把首轮机器 0 解释为手册确定 0，也不能依据原 AI 或 AI 复审建议补成 1。A157 GLP、S8 未定、Ec79/Ec149/Ec337、E704 等保留审查边界；`pending-review-not-targets.json` 明示 13 项不作为优化目标。

合并材料：`dimensions.py.patch`、`relations.py.patch` 是相对冻结原件的完整差异；`se_predicates.inc`、`se_relations.inc` 保留本分支新增代码。ROOT 合并 I/F 分支时，应逐函数/关系合并，并保留 `affected_dimensions` 和 `only_IF_consumers` 限制；不直接用整份 dimensions.py 覆盖另一分支。`technical-receiver-diff.patch` 另列接收器变化，技术桥独立于语义补丁。

开发输出中的全部变动和未定均有记录；未运行开发77、正式全量或新的 Codex CLI，未计算正式验收分数。当前输入、冻结原件、候选五模块和首轮输出的 SHA 复核见 `final-integrity-check.json`。
