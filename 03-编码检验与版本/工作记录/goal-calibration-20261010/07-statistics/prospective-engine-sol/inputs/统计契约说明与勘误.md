# 冻结前统计契约v2与勘误

初始设计、600/1444精度规划和全部历史结果保留。该文件仅修正事前方法契约；尚未选定实际n、抽取新检验ID或完成真人判读，不能据此宣布整个流程冻结。

四格以机器预测为行、裁定参照为列：a=TP，b=FP，c=FN，d=TN。Specificity=TN/(FP+TN)，即d/(b+d)；NPV=TN/(FN+TN)，即d/(c+d)。初始validation-design-sol.md与.json把这两个诊断分母写反，新引擎已修正；κ、Precision、Recall、F1的主公式不因此改变。简单非对称表(8,2,4,6)可区分两者：Specificity=.75，NPV=.60。[FDA统计指导](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-guidance-reporting-results-studies-evaluating-diagnostic-tests-guidance-industry-and-fda)明确特异度以参照阴性为分母；这里只借鉴二元分类统计定义，政策文本编码不属于临床诊断。

为与已经独立数学核验的新执行引擎一致，事前确定主要区间为同分层SRSWOR设计的Rao-Wu重缩放bootstrap：5000次，seed=20261010，同记录全部方法及五维共用重复权重，保留有限总体修正。四格设计协方差与解析梯度线性化用于独立复核/诊断。二者不能在新结果出现后择优。最终抽样seed与此bootstrap seed分别记录；5000次是本次执行参数，不是文献普遍验收线。

每项默认逐指标95%区间，不声称45项同时95%。未定义指标及未定义重复比例明示；退化[1,1]不证明稀有误差不存在，适用时另报有限总体超几何guard。开发材料没有总体概率CI。0.80项目逐维点值目标保持；没有新增CI下界或半宽阈值。

600/1444目前均是1444剩余池方案，3037开发项在该设计中概率为0。这个域上的性能不能重加权成4481全框性能；若报告全框机器验证，须另按全框正概率设计实施并真实裁定。完整论文仍待最终手册、源材料、方法、独立参照和实际指标完成。
