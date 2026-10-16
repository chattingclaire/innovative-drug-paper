现有Agent编码表的实际复算已完成。77条基础A/B、补材复判和最新混合表分开保存；所有真人新值/理由/姓名/日期仍为空。本次无新的语义判断或模型任务。

| 比较 | N保存/分配 | S κ | E κ | Ec κ | I κ | F κ |
|---|---:|---:|---:|---:|---:|---:|
| A_B_pilot01 | 41/41 | 1.000000 | 0.858131 | 0.942496 | 1.000000 | 0.942496 |
| A_B_pilot02 | 41/41 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| A_B_coverage01 | 36/36 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | NA |
| A_B_renewal-rejudge-v11 | 2/2 | NA | NA | NA | NA | NA |
| A_B_source-impact4-v12 | 4/4 | NA | 1.000000 | 1.000000 | 1.000000 | NA |
| A_B_development77_base_v11 | 77/77 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| A_B_latest_actual_development_composite77 | 77/77 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| rule_v17_complete77_vs_AI_reference_v3 | 77/77 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| native38_complete_format_subset_vs_AI_reference_v3 | 38/77 | 0.842975 | 0.786517 | 1.000000 | 1.000000 | 1.000000 |
| native38_complete_format_subset_vs_historical_AI_reference_v2 | 38/77 | 0.842975 | 0.786517 | 1.000000 | 1.000000 | 1.000000 |
| native_partial7_saved_subset_vs_AI_reference_v3 | 7/16 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| native_partial7_saved_subset_vs_historical_AI_reference_v2 | 7/16 | 0.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |
| rule17_vs_native38_implementation_agreement | 38/38 | 0.842975 | 0.786517 | 1.000000 | 1.000000 | 1.000000 |
| rule17_vs_partial7_implementation_agreement | 7/7 | 1.000000 | 1.000000 | 1.000000 | 1.000000 | 1.000000 |

A/B四格行=A、列=B，a=A1B1、b=A1B0、c=A0B1、d=A0B0；A/B均不是truth。机器行=候选、列=实际AI开发参照，TP=a、FP=b、FN=c、TN=d。Specificity=TN/(FP+TN)，NPV=TN/(FN+TN)。逐维详细四格、类别/待定/失败/覆盖、Po/Pe/Ppos/Pneg、分类指标、NA理由和真实差错ID均在metrics-all-available.json。

最新A/B混合表只将续约2条与source-impact4的实际后续提交覆盖显示；其余71条保留原1.1提交。原首件全部保存，混合修订结果不是原独立盲评κ。ROOT v3非盲裁定另列，未复制入A/B。

规则17、native38、partial7分别使用实际原预测。native38技术selection仍pending，partial7是失败批中的逐记录技术有效部分；它们不能拼成完整77。v3参照74条历史metadata保留，只有3个S为ROOT1.3/source14开发裁定，不能冒称真人gold或同版全部新参照。

开发点估计达到.80只称该保存数据上的数值状态；没有正式人类检验/验收结论。非概率曝光开发资料不套抽样权重，按既有统计契约不报告总体95%CI。800正式空表无A/B首件及可信参照，分类/概率CI仍NA。

复核数据review-rows.json包含77条完整原文CTX与实际源定位、385逐维行、双方原值与真实最新修订值/证据/身份版本、原first定位；真人复核字段为空。ROOT可制作分别A/B表与原文语境sheet。

既有sklearn 1.8.0在单一进程对所有比较逐维四格/κ及适用P/R/F1交叉复算；不以软件默认zero_division代NA。

未计算项目：
- 800 A/B agreement, classification, weighted fourcells/CI：800正式A/B表仍空，无真实独立人类首件或参照；空占位不作为semantic null或0。没有可信reference，规则800不能算classification。
- Probability-sample CI for development77/native38/partial7：非概率且历史曝光；既有contract明确开发资料不报总体CI。没有人为添加条件二项CI。
- Full77 native classification：native38完整候选与partial7失败批部分首件不同实际批/版本；不拼77，其他39或9未完成保持失败。
- LLM independent repeated full frozen runs / pairwise stability：缺同版本三次完整独立重复；技术retry、不同版本修复不能当稳定性重复。
- Rule same-input repeated byte stability：冻结版本只有本轮一实际run；未重跑生成新数据。
- Final4481 departmental attention and downstream robustness：可信真人参照/最终验证与必要全库重编码未实际完成；77非概率开发阳性数不能代总体部门占比。
- Material source/semantic correctness, real human identity：本轮只复算保存值，不新增源语义裁定；真人复核值/姓名仍为空。
