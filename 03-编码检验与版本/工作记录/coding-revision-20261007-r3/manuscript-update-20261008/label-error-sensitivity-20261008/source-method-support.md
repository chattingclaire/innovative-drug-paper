# 标签误差敏感性的方法依据

本备忘只支持解释，不修改正文、标签或未来真人样本。

1. **分类与比例估计不能互代。** Hopkins–King在p234的“Optimizing for a Different Goal”直接讨论个体分类准确而类别比例仍偏的情形。Forman作者报告§1及Fig1图注给出接近90% F-measure仍计数偏的文本分类例，并说明FP/FN相消可使计数准而单条未准。[Hopkins–King原文](https://gking.harvard.edu/files/gking/files/words.pdf)；[Forman作者报告镜像](https://shiftleft.com/mirrors/www.hpl.hp.com/techreports/2005/HPL-2005-96R1.pdf)

2. **双机器一致不能替代人工效度。** Artstein–Poesio §2.1（p557）明确，一致者仍可能共享错误。Grimmer–Stewart §5.2.3（advance PDF p13）将样本外机器—人工比较列为验证途径。本项目共用手册可能产生相关边界误读，是竞争解释，尚未测得其概率；人工参考也需记录裁定前分歧。[Artstein–Poesio](https://aclanthology.org/J08-4004/)；[Grimmer–Stewart](https://web.stanford.edu/~jgrimmer/tad2.pdf)

3. **稀有率解释不能删除FP/FN。** Artstein–Poesio §3.2（pp573–574）既解释偏斜边际对κ的影响，也强调稀有类别的辨别能力仍须检验。应与逐类P/R及四格合看，不能称所有低κ只是阳性稀少。[原文](https://aclanthology.org/J08-4004.pdf)

4. **总体样本与稀有联合结论须分别保证信息量。** Hopkins–King p243指出，总标注量不保证每类有足够实例，关心小类别比例差时尤其如此。因此，每部门80条的设计需另看人工Ec有效分母与两维联合状态，不能由总N、.8或75条重复性推导充分性；核查还须涵盖机器Ec阴性，才能发现被漏掉的条件分母。这是目标量导出的设计要求，不是对现240条必然不足的判断；本次未读其单位文本。[原文](https://gking.harvard.edu/files/gking/files/words.pdf)

有限等权二元参照下，比例误差=(FP−FN)/N，而逐条误分数=FP+FN；两者不能混同。P(F|Ec)另需处理Ec误纳/漏纳与F判定的联合错误。最小反转数只是在指定扰动模型下改变结论所需的距离，不是实际误差概率或置信区间。

现用61篇中，Grimmer–Stewart为[44]；Hopkins–King、Forman、Artstein–Poesio尚未列入，本次不修改参考集合。原始访问范围、具体页节、真实本地SHA与失败记录见同目录source-method-support.json。Grimmer与Artstein有可核本地PDF；Hopkins及Forman本轮核读web全文文本，但本地下载不完整，故未伪报完整本地原件或图像审读。
