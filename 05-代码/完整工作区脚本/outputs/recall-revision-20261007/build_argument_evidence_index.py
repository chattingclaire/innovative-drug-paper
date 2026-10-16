from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import json,hashlib,importlib.util,re,datetime,argparse
OUT=Path(__file__).resolve().parent
ROOT=OUT.parent.parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SPEC=importlib.util.spec_from_file_location('prose',OUT/'final_prose.py');prose=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(prose)
base=ROOT/'outputs/indicator-alignment-20261007/论文修订稿-指标统一版-待补真人验证.docx';ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
x=E.fromstring(ZipFile(base).read('word/document.xml'));ps=x.find('w:body',ns).findall('w:p',ns);plain=lambda p:''.join(p.xpath('.//w:t/text()',namespaces=ns))
refs={int(re.match(r'\[(\d+)\]',plain(p))[1]):re.sub(r'^\[\d+\]\s*','',plain(p)) for p in ps[125:]};refs.update(prose.NEW_REFERENCES)
ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');args=ap.parse_args()
manifest_path=OUT/'文稿生成与证据绑定.json';manifest=json.loads(manifest_path.read_text()) if manifest_path.exists() else None
if not args.prepare:
 assert manifest and manifest.get('status')=='actual_results_bound','Actual final manuscript must exist before final evidence indexing'
remap={int(k):v for k,v in manifest['reference_stable_to_final'].items()} if manifest else {}
policy=json.loads((OUT/'policy_evidence_matrix.json').read_text());source_catalog={s['id']:{'title':s['title'],'issuer':s['issuer'],'path':s['local_path'],'sha256':s['sha256'],'official_url':s['official_url']} for s in policy['sources']}
policy_ev={e['id']:{'source_id':e['source_id'],'locator':e['locator'],'fragment':e['quote_fragment']} for c in policy['matrix'] for e in c['evidence']}
prior=OUT.parent/'final-three-department-20261007'
SOURCE_REUSE_SCOPE='Unchanged policy/literature/interview source evidence only; not current model, numerical, document-layout, or new visual validation'
def source_audit_path(name):
 p=OUT/name
 if not p.exists():p=prior/name
 assert p.is_file(),('Missing source audit',name)
 return p.resolve()
policy_qa_path=OUT/'最终政策证据独立QA.json'
if not policy_qa_path.exists():policy_qa_path=prior/'最终政策证据独立QA.json'
interview_qa=json.loads(policy_qa_path.read_text())['root_requested_claim_checks']['p10']
stat_files=[OUT/f for f in ['三部门编码指标.json','三部门注意力分布与敏感性.json','llm-v30/stability_comparison_v30.json','rules-v31/all_predictions_completed_material_v3.run.json','rules-v31/release_completed_material_v3.json','source_safety_population_v3_independent_QA.json','source_safety_population_v3_QA.json','safety_population_context_v3_manifest.json']]
stats_path=OUT/'三部门编码指标.json'
if stats_path.exists():
 stats=json.loads(stats_path.read_text());llm_path=stats.get('method_bindings',{}).get('llm',{}).get('path')
 if llm_path:
  lp=Path(llm_path).resolve();assert lp.is_relative_to(OUT.resolve()),'Old model output cannot bind the new paper'
  stat_files.extend([lp,lp.parent/'final_manifest.json',lp.parent/'selected_execution_lineage.json',lp.parent/'actual_execution_reconstruction_QA.json'])
files={str(f.relative_to(OUT)):{'path':str(f.resolve()),'sha256':sha(f)} for f in stat_files if f.exists()}
if not args.prepare:assert len(files)==len(stat_files),'A final evidence index cannot silently omit actual statistical/execution records'
paragraphs=[]
def row(i,role,**kwargs):
 t=manifest['paragraph_changes'].get(str(i)) if manifest else None
 if t is None:t=prose.UPDATES.get(i,plain(ps[i]))
 ids=[]
 for m in re.finditer(r'\[([\d,，—–\- ]+)\]',t):
  for f in re.split('[,，]',m.group(1)):
   rr=re.split(r'[—–\-]',f.strip());ids.extend(range(int(rr[0]),int(rr[-1])+1))
 paragraphs.append({'original_paragraph_index_zero_based':i,'role':role,'stable_reference_ids':sorted(set(ids)),'final_reference_numbers':sorted(remap[z] for z in set(ids) if z in remap),'verification_scope':kwargs.pop('verification_scope','原始记录与既有文献审计按所列职责核查；不扩大为全部来源全文已读'),**kwargs})
row(9,'政策背景与问题来源',policy_sources=['ref61十五五纲要第三十九章第三节（正文91–92/PDF96–97）','ref50支持创新药若干措施','ref62医保局2025-12-07发布目录页面'],verification_scope='NDRC完整140页原始PDF及实际页面图像、NHSA官方页面；2026年1月1日实施，不把发布与实施日期混同')
row(10,'访谈所提出的两个具体跨环节问题',interview_bindings=interview_qa['interview_bindings'],verification_scope='医保专家第6段支持注册一类与医保临床价值区分；史录文第15、17段支持医保进入后医院实际使用障碍；充分配备程度已不作此处结论')
for i,scope in [(15,'国内多维价值评估、历史准入及定价支付研究'),(16,'博弈模型、制度与政策工具分析；模型条件与政策观察分别概括'),(17,'跨国HTA对应药品/适应症比较、探索性参与者偏好与创新定义综述'),(19,'抗生素领域访谈、亚洲HTA政策论坛、患者偏好与多重制度逻辑文献'),(20,'国内医保落地制度逻辑与利益相关者视角')]:row(i,scope,audit='outputs/manuscript-completion-20261006/参考文献核验.json及outputs/validation-expansion-20260926/参考文献缺口*审计')
row(25,'注意力变量与五维构成指标定义',method_sources=['文宏2014原始PDF印刷23–24页','陈星平等2018官网全文2.1–2.3、表1–3、3.2'],formula='q_gd=C_gd/sum_j(C_gj)',verification_scope='文献支持语境计句、同维一次和跨维分别计数；五维合计归一化分母为本文操作定义')
row(26,'制度逻辑作为分析视角',method_sources=['Thornton/Ocasio2008手册章节','Greenwood等2011制度复杂性综述'],verification_scope='理论归属核验；以评价目标、对象、证据和用途组织比较，不将制度逻辑作已量化因果自变量')
row(27,'注意力基础观与政府文本观察',method_sources=['Ocasio1997注意力基础观','陶鹏/初春2020公开批示研究','李梦颖等2024医保落地分析'],verification_scope='理论归属与各研究对象核验；本文观察量是纳入政策文本的相对关注')
row(31,'三种制度逻辑的分析性概括',policy_sources=['REG第一条/第十三条','医保用药管理暂行办法第一条/第七条','NHC第一章目标与评价应用'],verification_scope='原文件目标支持本文概括；科学—安全、经济—效率、公共服务三名称为本文分析性命名')
row(42,'研究时间起点',policy_sources=['2017年人社部36种药品纳入目录通知'],verification_scope='通知题名、36种数与年份核验，起点为目录纳入，不声称价格谈判始于2017')
row(43,'语料范围与筛选',statistics=['三部门注意力分布与敏感性.json'],policy_sources=['完整55条来源清单、51条主分析、4条背景审计'],verification_scope='按真实机关与冻结制度系统核对范围；联合文件单次归属，敏感性另行剔除')
framework_audit=OUT/'source-checks/2023-2026申报指南五维名称逐年核查.json'
if not framework_audit.exists():framework_audit=prior/'source-checks/2023-2026申报指南五维名称逐年核查.json'
row(44,'医保五维框架与逐年名称沿用',policy_sources=['APP附件二（二）至（六）'],source_record=str(framework_audit),source_record_sha256=sha(framework_audit),verification_scope='沿用已封存原文源核查：2023PDF5–6、2024PDF6–7、2025PDF6–7、2026正式PDF7–8；本轮重新绑定文件散列，未将旧视觉审读称为本轮新审读；具体价格信息与销量预测年限有调整')
row(45,'跨部门五维映射',policy_evidence_ids=['NHSA-F1','NHC-F1','NHC-F2'],verification_scope='卫健原为六维，可及性的获取与可负担映射到研究公平性；没有把卫健原政策重写成五维')
row(46,'规则与LLM各自的方法依据',method_sources=['Sevenans等2014 CAP会议稿存在与题名确认；不援引未读全文算法','Loughran/McDonald2011原刊35–36、43–45','Gilardi等2023公开作者稿4.2–4.6','Halterman/Keith2026正式卷期、出版社全文5–8节'],verification_scope='词典领域语义、共享代码本和任务内验证的职责分别映射；本任务规则/提示和实跑结果由本项目记录支持')
row(47,'单元、二元标签与分母计算',statistics=['三部门注意力分布与敏感性.json'],formula='C_gd=sum_i y_igd; q_gd=C_gd/sum_j C_gj; difference_pp=100*(q_gd-q_hd)',verification_scope='4481单元与1848/2100/533由输入与来源映射重建；同一单元可多维，同维一次')
row(49,'参考身份与机会校正一致性',statistics=['三部门编码指标.json'],method_sources=['Grimmer/Stewart2013作者稿5.2.1及5.2.3','Cohen1960书目及κ独立公式核验'],verification_scope='A/C实际为AI agent首次提交；1057为开发复核材料，不制造真人或独立验证身份')
row(50,'正类识别与区间',statistics=['三部门编码指标.json'],method_sources=['Kristensen-McLachlan等2025原稿第3–4、6页','Davison/Hinkley1997出版社第3/8章公开说明'],formula='P=TP/(TP+FP); R=TP/(TP+FN); F1=2TP/(2TP+FP+FN)',verification_scope='κ/P/R/F1与95%文件聚类区间由实际配对重算；5000次为本文实现，按来源文件保留组内单元，NA不以0替代')
row(54,'逐维与低频类别的实际比较',statistics=['三部门编码指标.json'],policy_units=['RECODE25-03090一般医保数据定义','RECODE25-02912诊疗方案申报资格'],verification_scope='逐维汇总及分部门四格核对；低κ语义差异记录，不将所有分部门比较称为合格')
row(55,'内容依据核查',policy_sources=['policy_evidence_matrix.json三部门×五维15格'],verification_scope='14原文源SHA与34项引用复核；32项原字匹配、1项中英文逗号差异、1项扫描视觉核验；不声称真实专家内容效度评分已实施')
row(56,'A/C设计加权',statistics=['三部门注意力分布与敏感性.json'],method_sources=['Horvitz/Thompson1952印刷669/PDF8页式6；实际查看原图'],formula='C_hat_gd=sum_i I(g_i=g)*y_id/pi_i; q_hat_gd=C_hat_gd/sum_j C_hat_gj',verification_scope='HT支持逆纳入概率估计总量，最终五维比率为本文定义；未把总量无偏性移写为比率无偏')
row(61,'访谈、研讨与政策原文的多来源对照',method_sources=['Carter等2014 The Use of Triangulation in Qualitative Research，PubMed原始著录及摘要；既有2026-10-06审计记录'],interview_sources=['史录文教授访谈会议纪要-0605.docx，实际会议日期2025-06-09','医保局专家调研-0616.docx'],verification_scope='实际访谈、研讨会材料与政策文本分别留存；两份专家访谈用于问题与决策情境比较，未转写为逐句人工标签验证；Carter负责多来源对照的方法依据')
for i,role in [(65,'规则全量五维注意力分布'),(73,'部门间同维百分点差'),(74,'平行方法、加权参照与敏感性'),(104,'数量发现与内容判断的综合结论')]:row(i,role,statistics=['三部门注意力分布与敏感性.json'],verification_scope='数值、排序、分母和敏感性从封存输入独立重建；因果效果不由占比差识别')
row(79,'政策内容矩阵来源',policy_sources=['policy_evidence_matrix.json15格'],verification_scope='每格按判断对象、参照、证据、用途映射；原条页码及片段见政策证据目录')
row(80,'药监安全/有效/经济/获取内容',policy_evidence_ids=['NMPA-S1','NMPA-S2','NMPA-E1','NMPA-E2','NMPA-Ec1','NMPA-Ec2','NMPA-F0'],verification_scope='风险计划、抗肿瘤研发、RWE三（三）及GCP45条；GCP2026已发布但施行晚于语料截止')
row(81,'医保与卫健经济/安全/获取内容',policy_evidence_ids=['NHSA-Ec1','NHSA-Ec2','NHSA-F1','NHSA-F2','NHC-S1','NHC-S2','NHC-Ec1','NHC-Ec2','NHC-F1','NHC-F2'],verification_scope='医保续约A为药品费用/预算比，不改为基金支出/预算；卫健为增量经济分析和机构/患者获取')
row(84,'三个环节创新判断的具体用途',policy_evidence_ids=['NMPA-I0','NMPA-I1','NHSA-I1','NHSA-I2','NHC-I1','NHC-I2'],interview='医保局专家调研-0616.docx第6、25段',verification_scope='区分注册新颖性/临床价值/支付用途；不概括成药监仅新颖、医保仅疗效的二分')
row(85,'试验对照、支付参照与临床参比',policy_evidence_ids=['NMPA-E1','NHSA-E1','NHSA-E2','NHSA-E3','NHC-E1','NHC-E2'],verification_scope='抗肿瘤最佳治疗对照为领域实例；医保正式指南与官方问答联读；卫健也使用研究证据与真实世界数据')
row(86,'价值衡量与决策用途',policy_sources=['REG','医保用药管理暂行办法','NHC'],interview='史录文纪要第7–8段与医保专家第3段',verification_scope='政策与真实访谈分别核查；末句方法复用与条件注明属于作者基于条文的分析')
for i,role in [(88,'制度逻辑视角下的内容解释'),(89,'共同关注与衔接需求'),(90,'由差异引出协调重点')]:row(i,role,policy_sources=['policy_evidence_matrix.json'],verification_scope='以原文的对象/证据/用途与数量结构相互解释；不把职责分工写成冲突或协调失灵的实测因果结论')
for i,path_id,role in [(92,None,'协调路径导入'),(94,0,'建立结论对照单的建议'),(95,0,'结论对照的既有政策接口'),(97,1,'跨环节证据补充计划建议'),(98,1,'补充研究与续约/使用更新的既有政策依据'),(99,1,'AIFA按疗效费用安排与再评价的参考'),(101,2,'结构化反馈的建议与访谈动因'),(102,2,'共享目录与使用反馈的建议'),(105,None,'三条协调路径的归纳')]:
 kw={'classification':'recommendation_supported_by_existing_interfaces_not_measured_effect','verification_scope':'区分现有正式安排与作者提出的扩展做法；不写成措施已实施或效果已检验'}
 if path_id is not None:kw['coordination_path_basis']=policy['coordination_paths'][path_id]['basis'];kw['policy_interface']=policy['coordination_paths'][path_id]['current_policy']
 if i==99:kw['specific_source']='AIFA官方registri-farmaci-sottoposti-a-monitoraggio页面的Payment by Result；岳晓萌等2021目录退出研究'
 if i==101:kw['specific_source']='医保专家纪要第4段PPT表述；史录文第31段商保取得公立医院数据困难；Casilli2023对应评价资料'
 row(i,role,**kw)
protocol_path=OUT/'rules-v31/protocol-v1.3.md'
row(108,'五维操作定义',protocol=str(protocol_path.resolve()),protocol_sha256=sha(protocol_path),verification_scope='冻结v1.3手册副本，研究维度标签S/E/Ec/I/F名称与纳排统一；临床管理难度与获取/负担子类型分列')
row(110,'边界和来源稳健性',statistics=['三部门注意力分布与敏感性.json'],verification_scope='各口径重算分子和五维分母，不仅删分子；卫健S/F次序和Ec位置按实际反转记录')
row(111,'真实LLM执行及稳定性',statistics=[f for f in files if f.endswith(('final_manifest.json','stability_comparison_v30.json','selected_execution_lineage.json','actual_execution_reconstruction_QA.json'))],method_sources=['Törnberg2024正式HTML第4/7/9节'],verification_scope='只绑定本轮候选03及最终v3逐单元材料：最终197个选中批包括195个与v3逐条同材的原实际批与2个源补料后完整批重跑，不称197为历史全部调用数；全部输出重建自原始实际raw响应，相同输入重复/顺序扰动/批次组成差异分别报告；不沿用旧v29稳定性数值')
row(112,'配套统计可追溯性',statistics=['三部门编码指标.json','三部门注意力分布与敏感性.json'],verification_scope='首次参考、逐维可判掩码、四格、区间、分歧、源文与哈希均有文件，不虚构真实人类标签')
row(122,'语料覆盖与排除的数量',statistics=['三部门注意力分布与敏感性.json'],verification_scope='51条主比较/4481单元，4条背景/443单元；不增加第四部门')
row(123,'文件/系列等权与联合来源处理',statistics=['三部门注意力分布与敏感性.json'],verification_scope='零分母保留NA，年度与原始文件非同一聚类单位，A/C可得条目范围如实记录')
used=set(z for r in paragraphs for z in r['stable_reference_ids'])
catalog_ids=set(remap) if manifest and manifest.get('status')=='actual_results_bound' else used
assert catalog_ids<=set(refs),'Final reference remap contains missing bibliographic entries'
catalog={str(z):{'full_citation':refs[z],'final_number':remap.get(z),'covered_by_indexed_argument_paragraph':z in used} for z in sorted(catalog_ids)}
result={'created_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),'purpose':'论文论证与证据职责的轻量索引；按原稿零基直接段号定位，最终引用编号由生成manifest重映射','status':'final_bound' if manifest and manifest.get('status')=='actual_results_bound' else 'pending_final_manuscript_reference_remap','final_manifest':{'path':str(manifest_path),'sha256':sha(manifest_path)} if manifest else None,'four_evidence_roles':{'quantitative':'封存标签、来源映射、公式与JSON重算','policy_content':'原文源SHA、条款/物理页与对应片段','theory_method':'原始文献及实际读取范围；书目与全文分别记','coordination_recommendations':'据已存在接口提出的建议，非已检验的因果效果'},'statistic_file_catalog':files,'reference_catalog':catalog,'policy_source_catalog':source_catalog,'policy_evidence_catalog':policy_ev,'paragraphs':paragraphs,'verification_artifacts':[str(OUT/'最终政策证据独立QA.json'),str(OUT/'prose_evidence_QA.json'),str(OUT/'prose_evidence_QA_refs61-63_interviews.json'),str(OUT/'指标依据与理论对齐.md'),str(ROOT/'outputs/manuscript-completion-20261006/参考文献核验.json')]}
result['final_document_bindings']={name:{'path':str((OUT/name).resolve()),'sha256':sha(OUT/name)} for name in ['论文修订稿-三部门版.docx','校核与待确认事项.docx'] if (OUT/name).exists()}
result['prior_source_audit_binding']={'path':str(policy_qa_path),'sha256':sha(policy_qa_path),'reuse_scope':SOURCE_REUSE_SCOPE}
result['AC_reference_identity']='Original independent AI-agent first submissions with their original visible materials preserved; not new human validation'
result['model_material_identity']='Rules and every selected actual LLM request row use completed material v3. Two affected whole batches were unconditionally rerun; unchanged actual batches are retained only after exact per-row material equality. Original A/C were not rerun on the new material.'
source_audit_paths=[policy_qa_path.resolve(),source_audit_path('prose_evidence_QA.json'),source_audit_path('prose_evidence_QA_refs61-63_interviews.json'),(ROOT/'outputs/manuscript-completion-20261006/参考文献核验.json').resolve()]
current_method_paths=[(OUT/'指标依据与理论对齐.md').resolve()]
method_binding_path=OUT/'指标依据与理论对齐.json'
if method_binding_path.exists():current_method_paths.append(method_binding_path.resolve())
elif not args.prepare:raise AssertionError('Final method basis must bind current actual results before evidence indexing')
artifact_bindings={}
for p in source_audit_paths:
 assert p.is_file(),('Missing reused source evidence',p)
 artifact_bindings[str(p)]={'path':str(p),'sha256':sha(p),'reuse_scope':SOURCE_REUSE_SCOPE,'source_review_identity':'Original source audit retained with its original reading and review scope'}
for p in current_method_paths:
 assert p.is_file(),('Missing current method basis',p)
 artifact_bindings[str(p)]={'path':str(p),'sha256':sha(p),'verification_scope':'Current implementation and variable/method basis; literature-source scope remains that of the original audits'}
result['verification_artifacts']=list(artifact_bindings)
result['verification_artifact_bindings']=artifact_bindings
diagnostic_files=[OUT/f for f in ['independent_blind_review.json','independent_blind_supplement_review.json','independent_blind_material_gap_recheck.json']]
result['current_development_review_bindings']=[{'path':str(p),'sha256':sha(p),'verification_scope':'Current sealed AI development diagnosis, not replacement A/C, human adjudication, or independent reliability validation'} for p in diagnostic_files if p.exists()]
# Verify that every named policy evidence item actually exists before saving.
for rr in paragraphs:
 for e in rr.get('policy_evidence_ids',[]):assert e in policy_ev,(rr['original_paragraph_index_zero_based'],e)
assert all(Path(p).is_file() for p in result['verification_artifacts']),'Dangling verification artifact'
if args.prepare:result['status']='pending_final_manuscript_reference_remap'
destination=OUT/('论证证据索引-待生成.json' if args.prepare else '论证证据索引.json')
destination.write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({'status':result['status'],'n_paragraphs':len(paragraphs),'n_reference_entries':len(catalog),'path':str(destination),'bytes':destination.stat().st_size},ensure_ascii=False))
