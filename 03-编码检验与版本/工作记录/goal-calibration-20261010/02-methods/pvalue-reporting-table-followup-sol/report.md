已核正式原刊的实表与正文，结论是：**编码质量的κ、precision、recall、F1可以直接报告数值并引用表，正文不必附***。** 这是实际发表例子的写法，不是声称期刊禁止星号。

最直接的一例是 Karyn Ayre、André Bittar、Joyce Kam、Somain Verma、Louise M. Howard、Rina Dutta（2021），*Developing a Natural Language Processing tool to identify perinatal self-harm in electronic healthcare records*，**PLOS ONE 16(8): e0253809**。取得的是出版社原刊Research Article，首页明确收稿、接收日期及Peer Review History；不是preprint。[原论文](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0253809)

第7页 **Table 2** 是人工两两一致性，**Table 3** 是机器工具的development/test验证。两表都列Precision、Recall、F-score、Kappa；没有p列、显著性星号或相应星号表注。原文第4页把F-score定义为P/R调和平均，即F1。摘取实际行如下：

| 实表/对象 | Precision | Recall | F-score | Kappa |
|---|---:|---:|---:|---:|
| Table 2，人工Polarity | 0.96 | 0.96 | 0.96 | 0.92 |
| Table 2，人工Temporality | 0.90 | 0.90 | 0.90 | 0.78 |
| Table 3，机器test Polarity | 0.96 | 0.96 | 0.96 | 0.91 |
| Table 3，机器test Temporality | 0.83 | 0.83 | 0.83 | 0.62 |
| Table 3，机器test Status | 0.88 | 0.88 | 0.88 | 0.68 |

原表Span的κ是N/A，不能补成0。它是临床文本mention/属性编码，格式可参考；任务、平均方式及质量阈值不能直接移到本研究。

**正文怎样写：**第6页Results / Inter-annotator agreement介绍Table 2呈现320份development文档的四指标，并解释micro平均；第7页Evaluation of the tool介绍Table 3呈现development 320/test 80文档的验证结果。正文引用表、说明样本与平均方式，没有给这些质量指标加***。[正文第6页截图](screenshots/Ayre_2021_page6_body_table2_reference.png)、[表及正文第7页截图](screenshots/Ayre_2021_page7_tables2-3.png)已逐页视觉核。

对照既有《科学决策》原刊实物：李斌、陈琪（2026）第17页表3把回归系数写为0.219***、0.311***、0.129**，相邻正文则用“1%/5%水平显著”的文字说明，没有给每条正文结果再加星号。此处只说明回归表与正文的写法，不能代替编码质量证据。[既有封存核查](../pvalue-reporting-local-sol/report.md)

第二个候选是 Gennaro 等（2025）PSRM正式政治学论文，官方附录缓存能定位Table D.3四指标；但原PDF本地下载两次HTTP500，作者页一次502，未取得PDF SHA/视觉证据。因此本报告只把它列为未完成候选，不用它充当已核实表。[出版社文章](https://doi.org/10.1017/psrm.2025.10063)

对本研究，正文可写“逐维一致性及分类质量见表X”，再说明真正达到的预定门槛；不要添加尚未计算的p或***。人工κ≥.8、机器κ/P/R/F1≥.8不能被p<.05替代。本轮没有改稿或计算项目指标。
