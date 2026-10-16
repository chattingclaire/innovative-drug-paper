# 冻结版回归与两条更新材料交付

implementation04 在同一代码下分别完成旧41材料回归与36条开发比较。旧41为41/41整条、205/205维度一致；36为35/36整条、179/180维度一致，保留RECODE25-03818的Ec假阳性。36全维度F1=0.960000、κ=0.957020；F维度全阴性，F1/κ仍为null。全部比较、算术复算、首次预测及失败版已封存，当前版未追补“说明书”误判。

| 阶段 | 真实执行结果 | 交付状态 |
|---|---|---|
| 旧41材料回归 | 41/41整条、205/205维度一致；预测与前版byte相同 | 单独封存、独立评价及复算 |
| 36条开发比较 | 35/36整条、179/180维度一致；首8格分歧改7格，仍1 Ec FP | 单独封存、独立评价及复算 |
| 两条更新共材 | 2个UnsupportedSourceGraph；规则判断未执行；10技术失败槽 | 单独接口版、实际首失败封存；未比较新参照 |

两条共材的原始2对象、60/46个上下文、37份来源文本、49个区域和9张原PNG完整保留且哈希核验。三份实质源码evidence/relations/dimensions与implementation04逐字节相同。来源适配仅核验原字段/类型/路径；原始新增kind和source_references图没有转换成旧角色、没有把全文作为默认各维输入。

静态与合成契约对照表明，旧ordered-list边可以局部引用任意成员文本；本批恢复正文没有进入那些旧入口，新增geometry容器和source_references没有冻结关系消费接口。因此严格semantic_unit拒绝两条，实际程序返回失败码2，封存2个原失败记录和10格技术诊断；每格保留完整source_record，rule_not_executed=true，rule_value/decision为空，rules_null=false，comparison_eligible=false。不能计为规则0、普通规则空值或有效一致率。

来源与接口分别通过48项reader合成控制、13项runner控制、197项独立完整性检查、13项独立reader控制、7项独立fallback控制和8项独立消费契约对照；数量存在覆盖，未相加为独立样本。修前失败、源码快照、审计失败和实际首失败均保留。实际读取9PNG，读轨迹22路径，无新参照/A/B/native答案读取，未运行新2评价程序。

下一版只需在dimensions.py的_payment_route_only谓语候选中解决文书名内部“说明”的误识别，另加必要的名词/真实动作正反对照。真实“说明支付标准”“明确预算或费用”必须保留。具体文件范围已报告；implementation05尚未创建或执行，本次冻结源码不改。

这些结果均为AI开发工作。旧41中的两条材料投影有已知缺口，旧41表仅表示旧材料回归；本批新材料接口失败不构成新的内容判断或材料验收。

交付入口：

- [41+36完整报告](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/implementation04/paired-v04-development-report.md)
- [41+36完整封存清单](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/implementation04/paired-v04-final-delivery-bindings.json)
- [两条实际失败seal](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/renewal2-v04-interface01/run01/seal.json)
- [全10技术失败槽](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/renewal2-v04-interface01/run01/technical-diagnostics.jsonl)
- [两条执行完整记录](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/renewal2-v04-interface01/updated-two-material-execution-report.json)
- [下一版具体文件范围](/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010/06-coding/development-rule-sol/coverage36/renewal2-v04-interface01/next-version-specific-change-scope.md)
