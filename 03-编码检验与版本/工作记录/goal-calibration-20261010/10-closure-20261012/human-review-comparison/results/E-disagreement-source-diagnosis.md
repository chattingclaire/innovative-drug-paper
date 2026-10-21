# 5 项有效性 E 分歧的原文诊断

结论：**03037、00050、00094、04598 有明确或较强的通用规则漏识别依据；00190 保留上下文承接争议。** 本次是研发诊断，不是验收或改判。对照中的人工值来自 AI 初评后的真人确认，不能作为独立金标；00190 原逐项意见仍是“倾向建议，未正式裁定”。

五项冻结规则均为 E=0；LLM 除 00190 为 0 外，其余均为 1；复核表均登记为 1。五项实际来源均是 v9 首轮，当前 v11/v16 混合生产保留其原件。本报告未读取正在运行的 v12 结果。

|记录|原文与缺失环节|结论及修正边界|
|---|---|---|
|03037|当前明确“考察不同亚组的治疗获益和风险”，同段仅补足药物对象。现有 E 表达模式遗漏此类“治疗获益”句式。|高确定性；可研发对药物治疗获益及其证据的通用识别，不能仅凭“获益”一词赋 E。LLM 未见过推断。|
|00050|“请按照以下内容提供相关说明及依据”确指的完整成员 2 要求临床优势、效果终点和研究结果证据。旧入口漏识别“请…提供…”这一实质总领。|高确定性；补实质内容要求与完整成员承接，继续核同源、成员及边界，纯“如下”引导仍排除。|
|00094|“申请…应同时满足（一）（二）”是实质资格要求；完整成员含明确效果分支。原结果已有 substantive_list，但缺 SE_scope_verified，E 消费被阻止。|高确定性；应补明确枚举地址的关系识别和范围证明，**不得删除 _se_allowed 安全边界或直接开放未验证 parent**。不是把笼统“临床价值”都认成 E。|
|04598|当前要求就附条件上市条件沟通确认后申请；同版第 63 条明确临床数据证实/显示疗效。原规则仅记录 3 个 CTX 的读取，未有限核读完整条件。|较高语义确定性；可研发“具名条件内容确认→同版完整标准”的有限补全。原完整文件已经可用，不能称缺原文，也不能虚构旧规则已读取标准。普通沟通形式仍排除。|
|00190|当前鼓励患者访谈；同一段紧接“例如，收集…现有治疗所产生的疗效…患者对获益风险的评价”。两机认定举例不能倒补，原逐项意见倾向认为直接解释访谈内容。|中等确定性；E=1 有文本依据，但保留“直接释义或相邻倒借”的边界。不能仅由录入 1 断言双机错误或列为必修金标。|

手册依据为[共同实质与证据门槛](/PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt:9)、[总领及必要语境](/PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt:41)、[实质总领与纯引导的区分](/PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt:59)、[E 定义与边界](/PROJECT_ROOT/outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt:94)。本次未发现必须新增源材料才能判断的缺口；04598 的问题是未完成有限来源消费。

精确材料入口：03037 的[当前包 p0081／第 13 页](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/full4481-common-v15-production-preparation-sol/packets/RECODE25-03037.json)；00190 的[当前包 p0031／第 10 页](/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/full4481-common-v15-production-preparation-sol/packets/RECODE25-00190.json)；00050 的[原文第 69—71 行](/PROJECT_ROOT/outputs/goal-calibration-20261010/00-baseline/source-files/980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt:69)；00094 的[完整条件第 163—175 行](/PROJECT_ROOT/outputs/goal-calibration-20261010/00-baseline/source-files/980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt:163)；04598 的[同版第 63—64 条](/PROJECT_ROOT/outputs/goal-calibration-20261010/00-baseline/source-files/d959108cdaaa3b46-NMPA-药品注册管理办法-2020-正文.txt:209)。包路径中的 v15 名称不改变其已核对的当前 v16 绑定身份。

[完整诊断 JSON](/PROJECT_ROOT/outputs/goal-calibration-20261010/10-closure-20261012/human-review-comparison/results/E-disagreement-source-diagnosis.json) 保存每项当前两机理由、复核来源、原始执行链、完整引文、手册行号与代码缺失环节。未改标签、代码或冻结材料，未运行分类或重算指标；这些已曝光个案不能据以推断总体准确性或凑足 0.8。
