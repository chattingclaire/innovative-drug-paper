"""Render the frozen planning counts and transparent limitations to Markdown."""
from pathlib import Path
import json
P=Path(__file__).resolve().parent
d=json.loads((P/'strata-planning.json').read_text())
b=json.loads((P/'source-bindings.json').read_text())
sc=json.loads((P/'scenario-error-tables.json').read_text())['scenarios']
lines=[]
def add(s=''):lines.append(s)
add('# 剩余1444独立检验：固定分层与精度规划')
add('\n2026-10-10；GPT-6.1 Sol / ultra。本文件只完成独立设计任务，未抽样、未提供未曝光正文、未新跑机器、未执行真人首判或裁定，也未替主对话冻结最终手册/执行。')
add('\n**选定的单一建议是剩余1444条全部双人独立判读及另存裁定。** 按冻结旧机器I/F阳性、阴性联合辅助层列清20个非空层，每层n_h=N_h。两位真人共2888次单位阅读、14440个五维首判项；裁定最多1444条。这样可精确核定本有限池的人—人信度和最终机器对参照的四格，排除抽样误差，但不能排除手册、来源或参照判断误差。它不是已获执行确认或已完成的验收。')
add('\n采用全核是当前信息下的精度与工作量选择，不是文献规定必须全核。1312条抽样在本次部分情景下已能有较窄区间；若以资源上限另选抽样，必须在任何检验答案前另锁一套完整分配，不能先抽后看是否过线再扩到1444。本文件的较省工分配是规划比较，不是本轮备用扩样计划。')
add('\n## 1. 冻结对象与范围')
add('\n已采用版本绑定自`整套编码采用记录.json`，不是按目录最新时间另挑候选：')
for m in ['rules39','LLM03']:
 add(f"\n- {m}：SHA `{b['sources'][m]['sha256']}`；原文件4924条唯一ID、目标三部门4481条、其他443条；4481目标ID全部齐全，五维均为整数0/1，无缺失/NA。")
add('\nrules39内部版本为`v39-five-current-relations-development`。LLM03从整套采用记录绑定完整文件；不与其他候选拼接。采用记录SHA、原文件路径、字节数、目标齐全性、规则内部版本和标签计数均在[source-bindings.json](source-bindings.json)。投影只保留ID、部门、族ID、曝光状态、两机器固定标签，完全不输出正文、语境、理由或人工答案。')
add('\n三部门总框4481：药监1848、医保2100、卫健533。直接开发曝光2770、同规范正文族追加267，排除共3037；剩余1444为药监778、医保562、卫健104，共1344族。它是“未查到已列明逐条开发证据的剩余池”，不能称所有原文/语境从未被看见。族去重仅作曝光闭包，当前估计单位仍是每条文本单元，不改成1344个等权族。')
add('\n剩余池设计中3037条pi=0。因此1444的信度、机器表现和人工正类数不能重加权成全4481。任何补充开发使用都应重新核定曝光池；若N或ID集合变化，本建议失去当前绑定，须在答案前重新规划。')
add('\n方法复核文件在并行工作期间有更新，核心frame、exposure-ids及两预测SHA保持不变。原绑定与新版方法说明/曝光汇总分别保存在[supplemental-source-bindings.json](supplemental-source-bindings.json)，没有改写旧冻结投影。')
add('\n## 2. 实际辅助层与一次固定n')
add('\n四位签名顺序固定为：规则I、LLM I、规则F、LLM F。`0000`再分“其他阳性”（任一机S/E/Ec=1）和“两机五维全阴性”；其他签名维持原联合层。无效/NA理论上单设层并保持正概率，但当前实际为0条，不人为造样本。所有20个实际非空层均纳入。')
add('\n| 部门 | I/F四位签名 | 补充类别 | N_h | 预先建议n_h | pi | w |\n|---|---|---|---:|---:|---:|---:|')
order={'NMPA':0,'NHSA':1,'NHC':2};names={'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
for h in sorted(d['selected_remaining_plan']['strata'],key=lambda h:(order[h['department']],h['IF_signature'],h['tag'])):
 tag={'ALL_NEG':'两机五维全阴性','OTHER_POS':'其他S/E/Ec阳性','IF':'I/F辅助阳性'}[h['tag']]
 add(f"| {names[h['department']]} | {h['IF_signature']} | {tag} | {h['N']} | {h['n']} | 1 | 1 |")
add('| **合计** | | | **1444** | **1444** | | |')
add('\nI/F任一辅助阳性141条；I/F全阴性1303条，其中其他五维任一辅助阳性328条、两机五维全阴性975条。总计两机任一五维阳性469条。阴性层全部覆盖，不能只判机器分歧或旧I/F阳性。')
add('\n| 维度 | 规则阳性 | LLM阳性 | 两机共同阳性 |\n|---|---:|---:|---:|')
for dim in ['S','E','Ec','I','F']:
 f=d['old_prediction_point_target_feasibility'][dim]
 add(f"| {dim} | {f['old_prediction_positive_margins']['rules39']} | {f['old_prediction_positive_margins']['LLM03']} | {f['fixed_joint_table_feasibility']['fixed_old_machine_joint11_10_01_00'][0]} |")
add('\n全核没有随机抽样seed或入选列表，也不需要人为随机抽取再全取。后续可随机化真人材料呈现次序，目的在执行盲判，不把它记作抽样随机性。所有批次和全部1444个任务应在见到答案前固定；首判完成前不得根据某维分数选择停止。')
add('\n## 3. Precision/Recall分母及可行情景')
add('\n机器行为预测、参照为列：a=TP,b=FP,c=FN,d=TN。P=a/(a+b)，R=a/(a+c)，F1=2a/(2a+b+c)，Cohen κ由同一四格的Po和Pe计算。P的分母是预测阳性，R的分母是裁定阳性；两者与总n不等价，也不能把旧预测阳性当作裁定阳性。人—人用A/B原始首判，不把一人视为真值；机器用另存真实裁定。')
add('\n常见等权独立比例近似：p=.80、95%半宽.10给n0≈62；保守p=.50给≈97。这只是有效分母的正态近似。真实加权、有限池、不对称精确区间需按实际设计计算。如下是二项精确95%区间的说明，**不作为本项目主区间**：')
add('\n| 等权分母 | 成功数 | 比例 | 二项精确95%区间 | 距点值最大半径 |\n|---:|---:|---:|---|---:|')
for x in d['equal_weight_denominator_illustrations']:
 if x['equal_weight_denominator'] in [22,40,55,62,78,97]:
  lo,hi=x['binomial_exact_95']
  add(f"| {x['equal_weight_denominator']} | {x['successes']} | {x['observed_ratio']:.3f} | [{lo:.3f}, {hi:.3f}] | {x['exact_max_radius_about_observed']:.3f} |")
add('\n比如50/62的精确区间是[.686,.896]，距点值最大半径.120，不是已保证±.10。[NIST比例区间说明](https://www.itl.nist.gov/div898/handbook/prc/section2/prc241.htm)支持小计数的精确反演和区间不对称；其二项模型不能直接替代本分层有限池推断。')
add('\n### 同一参照必须同时容纳两机器')
add('\n给定旧机器阳性M和参照阳性T，P、R同时≥.80至少要求.80M≤T≤M/.80（保留整数取整）。两机必须共享同一T，且共同真阳性不能超过已知机器阳性交集J。')
add('\n- 旧I：规则必要T∈[18,27]；LLM必要T∈[32,50]，无交集。\n- 旧F：边际必要共同T∈[63,68]，但所需共同真阳性至少50，实际旧阳性交集仅39，仍不可行。\n- S/E/Ec在P/R约束下存在可行整数参考表；这不是已达κ或参照有效的证明。')
add('\n上述是固定旧预测的计数可行性判断，不使用任何真人答案，不断言未来新手册下两方法不能达标。旧输出在本任务仅为辅助变量；后续最终机器输出仍须在新手册/输入冻结后独立执行并评价。尤其抽样比较中的旧P抽样方差为0，是因为469条旧辅助阳性全部判读；未来机器可能在旧阴性里新增阳性，这个0不能沿用。1444全核覆盖了这类变动。')
add('\n### 90组真实可行的整数误差表')
add('\n脚本使用每维已知“部门/辅助层×两机器0/1联合格”容量，设共同参照阳性总数T=14、43、72、144、289、722（约1%、3%、5%、10%、20%、50%）。参考阳性赔率每多一个旧辅助阳性乘.25、1、20，分别涵盖反向、无信息、有信息情景；用校准总量的logistic配置及有上限的整数余数分配生成参考格。不为任何实际ID生成伪真人答案，不从检验标签估计情景参数。每个情景严格保留旧两机边际与联合容量，生成两机共用的参照四格，故不会独立指定不相容的P/R。')
add('\n以下是T=14与43、有信息倍率20的部分计数示例；低分也原样保留。全部表与每层计数在[scenario-error-tables.json](scenario-error-tables.json)。半宽列仅为n=1312比较方案的设计线性化规划近似。')
add('\n| 维度 | T | 方法 | TP/FP/FN/TN | P | R | R规划95%半宽 |\n|---|---:|---|---|---:|---:|---:|')
for s in sc:
 if s['dimension'] in ['I','F'] and s['T'] in [14,43] and s['reference_odds_multiplier_per_auxiliary_positive']==20:
  for m,x in s['allocation_results']['negative85pct'].items():
   add(f"| {s['dimension']} | {s['T']} | {m} | {'/'.join(map(str,x['TP_FP_FN_TN']))} | {x['metrics']['precision']['point']:.3f} | {x['metrics']['recall']['point']:.3f} | {x['metrics']['recall']['linearized_95_halfwidth']:.3f} |")
add('\nT=14时，任何设计都不可能提供62个实际参照阳性。全核仍可精确知道此有限池的R；如果把目标改成未来政策或无限总体推断，14个正例的信息有限，必须另定义总体和模型，不能拿本次FPC把未来不确定性抹去。若T=0，Recall=NA；预测阳性0时P=NA；双方全为单一类别致Pe=1时κ=NA。NA不能填1。')
add('\n## 4. 有限池精度与事前比较')
add('\n按[Olofsson等2014](https://samv.elearning.unipd.it/pluginfile.php/175898/mod_resource/content/0/articolo_oloffson.pdf)的概率验证/误差表分配原则，比较不同误差表下的设计精度，兼顾稀有类和漏判。其空间案例配额不照搬；本文保留精确有限总体校正。每个比较方案469辅助阳性全取、卫健104全取，仅药监/医保两机全阴性层按固定50%、85%、95%或100%抽取。')
add('\n| 规划分配（比较用途） | 药监n | 医保n | 卫健n | 总n | 网格最差κ半宽 | 网格最差R半宽 | 网格最差F1半宽 | 零观测隐藏类别上界* |\n|---|---:|---:|---:|---:|---:|---:|---:|---:|')
for x in d['planning_comparisons']:
 hw=x['worst_linearized_95_halfwidth_on_prespecified_grid'];dn=x['department_n'];star=' **选定**' if x['key']=='census' else ''
 add(f"| {x['key']}{star} | {dn['NMPA']} | {dn['NHSA']} | {dn['NHC']} | {x['n']} | {hw['kappa']:.4f} | {hw['recall']:.4f} | {hw['F1']:.4f} | {x['zero_hidden_positive_guard']['maximum_unseen_count']} |")
add('\n*仅针对这些全阴性辅助层里的一个预先指定错误/参考类别，假设样本中该类别全部观测为0；采用双侧95%上侧α=.025、未知各层真实类别总数下的最大零事件概率反演。它不是整个四格、所有指标或45项联合95%边界。1312方案的该上界为1；若已经精确得TP=18且仅此处可能漏判，则R下界18/19=.947；若TP=1则下界1/2=.500，分母仍关键。')
add('\n网格最大值不等于所有可能真实状态的最大值。稀疏、零格的正态线性化可能失准；未观察到某类别时普通bootstrap甚至退化。本报告同时计算参考阳性分母不足尾概率及有限超几何guard，不用“预期已有62个”代替实际信息。18个等边际、18个不同边际A/B合成表另检查人—人κ精度；例如A+/B+=14/14、四格11/3/3/1427，实际κ=.7836，50%负层方案半宽.1369、85%方案.0574，仍不是当前真人结果。不同边际场景还保留名义κ不可达的计数约束。')
add('\n选定1444的原因是：一次完整覆盖可直接核定稀疏分母，保留所有阴性层和小部门；新方法未执行时不以旧标签分布假定其最终误差结构；相对1312只增加132条、264次双人阅读，消除本有限池全部抽样误差。当前没有预算上限，不靠提高预期分数缩小样本。全核将消耗本次剩余池，不留声称可重测的同池新留出；后续若检验材料用于开发，该次结果仍可报告，但新版本需要另有未开发材料验证。')
add('\n### 统计实现')
add('\n抽样比较用HT总四格t̂=Σ_h(N_h/n_h)t_sample,h。固定有限情景下，S_h=N_h/(N_h−1){diag(p_h)−p_hp_h′}，Var(t̂)=Σ_h N_h²(1−n_h/N_h)S_h/n_h；P/R/F1/κ各用解析梯度g，规划半宽=1.959964√(g′Vg)。正式抽样若另获采用，要用实际样本协方差估计S_h，保留原始与设计加权四格及unknown九格；不能把未知总体场景协方差当作正式样本标准误。[Penn State分层抽样公式](https://online.stat.psu.edu/stat506/Lesson06)给出分层方差与FPC，四格协方差为其向量推广。')
add('\n每层参照阳性样本计数X_h服从Hypergeom(N_h,T_h,n_h)，不同层独立；脚本卷积这些离散概率求Pr(ΣX_h<m)。该尾只说明原始参照阳性不足风险，不保证加权Recall半宽。[R官方超几何说明](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/Hypergeometric.html)给出无放回计数分布。零类别guard最大化∏_h Pr(X_h=0|T_h)于ΣT_h=K，按α=.025反演上界。')
add('\n选定全核的n_h=N_h、pi=1、w=1，所有完整可判四格总数是有限池实测总数，不存在抽样误差，设计区间可标为“无抽样误差；条件区间[θ,θ]”或直接报告精确有限池值。不能用它声称100%确定参照正确或未来政策同样准确。未知/缺材/非响应导致未完全测量时，不能把完成子集当作1444全核；保留全域未知率、可判子域结果和可行上下界。')
add('\n用户0.80继续是逐维点值项目目标：真实人—人Cohen κ≥.80；两最终机器分别逐维κ/P/R/F1≥.80。未增加CI下限≥.80要求，也不以其他一致系数、稳定率或综合占比替代这些指标。95%默认逐指标；若需全矩阵同时覆盖，应在答案前明确多重区间合同。')
add('\n## 5. 全4481真人审查与剩余机器留出用途')
add('\n若论文需要全4481有限语料的人—人信度、可信参照、两机器误差及人工覆盖/注意力总量，应另采用本文件已列明的全4481普查设计：部门×direct/family_only/remaining曝光状态×同一辅助类别，全部实际层n=N、pi=1。药监1848、医保2100、卫健533；两人8962次阅读、44810个五维首判项。全池可包含同批1444首判/裁定，条件是手册/材料版本及独立过程完全相同，无需重复阅读；增量3037条、6074次双人阅读。各实际层及N写在[strata-planning.json](strata-planning.json)的`separate_full_corpus_plan`。')
add('\n两个用途的报告必须分开：全4481是现有有限语料审计，含已开发材料；1444分域才是当前登记范围内未用于开发的独立检验。两者均须真正真人首判、答案封存、盲于机器的可信裁定。单做1444不能完成全4481人工总量；单做全4481也不能把开发3037包装为未见验证。若不开展全4481真人审查，本文件不替主对话声称其已完成，也不把旧180/240的统计当作全框证据。')
add('\n## 6. 交付与复算')
add('\n- [source-bindings.json](source-bindings.json)：已采用预测、目标ID/NA与投影SHA。\n- [strata-planning.json](strata-planning.json)：20层固定N/n、概率、工作量、独立范围、全4481方案、所有精度参数。\n- [scenario-error-tables.json](scenario-error-tables.json)：90组共同参照整数误差表、四种分配的方差和阳性不足尾。\n- [precision_plan.py](precision_plan.py)：仅根据许可投影复算层与规划，不读取正文、不抽实际ID。\n- [verify_planning.py](verify_planning.py) / [planning-QA.json](planning-QA.json)：解析梯度数值复核、小总体SRS穷举协方差、零事件反演穷举、90组整数容量/边际、NA和核心SHA。\n- [independent-review/method-review.md](independent-review/method-review.md)：另一个Sol/ultra代理独立方法复核（身份为AI方法复核，不是真人编码）。')
add('\n运行环境沿用上一份复算包私有`.venv`只读依赖（Python3.14.4、NumPy2.4.2、SciPy1.17.1），未改公共环境。命令在本目录执行：')
add('\n```sh\n../.venv/bin/python precision_plan.py\n../.venv/bin/python verify_planning.py\npython3 build_precision_report.py\n```')
add('\n原投影有一次族字段类型处理失败（源family为对象，最初未只取family_id），未形成source-bindings；修复为许可族ID后成功。规划QA首次发现三份方法复核文件外部更新，保留前后SHA并核核心ID/预测不变后再次通过。失败及修复记录另存，旧完整历史报告与矩阵均未覆盖。')
(P/'precision-planning.md').write_text('\n'.join(lines)+'\n')
print('precision-planning.md',len('\n'.join(lines).encode('utf-8')),'bytes')
