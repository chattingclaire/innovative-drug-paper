"""Independent, no-model verification of synthetic actual outputs; no author audit import."""
from pathlib import Path
import json, hashlib, datetime, importlib.util

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/编码修订核查-20261008/LLM编码/候选方案'
OUT=BASE/'semantic-review/independent-controls'
SOURCE=BASE/'execution-audit/candidate07_all106_controls_PRIVATE.json'
SHA='a43467ddfad077fe573517b96e037a379b7e8cc7b44a36b482253dd8cb36c985'
DIMS=['S','E','Ec','I','F']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canon(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
bindings={}
def read(p):
    bindings[str(p)]=sha(p)
    return json.loads(p.read_text())
def strings(x):
    if isinstance(x,str): return [x]
    if isinstance(x,dict): return [s for v in x.values() for s in strings(v)]
    if isinstance(x,list): return [s for v in x for s in strings(v)]
    return []
assert sha(SOURCE)==SHA
tests=read(SOURCE)['tests'];assert len(tests)==106
first=read(OUT/'review_progress_first40.json')['reviews'];assert len(first)==40
notes={
41:'创新研发项目申请人季度报告义务，身份不等于实体支持。',
42:'专门研发设备优先使用权提供实体创新研发资源，research_support。',
43:'发布资料指南仅以支持创新为宗旨，无实际指导资源。',
44:'审评机构安排专业人员提供下一阶段研究设计技术建议，research_support；未明确效果或安全用途。',
45:'父级明确创新研发对象，当前提供专门方案咨询；research_support，不把背景原创身份另复制为attribute。',
46:'普通药品研究咨询，另节原创药物不能移入。',
47:'预算增幅条件直接决定药物保障继续生效并支付药费，Ec及access。',
48:'预算条件仅材料排序且明示不决定给付供应，Ec1F0；理由准确限定并非实际给付管制。',
49:'已履行保障协议仅作管理转类前提，无新覆盖或延续。',
50:'当前明确保障协议续两年且原给付条件继续适用；F access及Ec支付条件均有当前独立依据。预期Ec0偏窄，保留预期原件及分歧。',
51:'扩大支付范围的申请人先书面申请，当前程序未实际覆盖或费用安排。',
52:'新适应证作为当前纳入对象，主谓为覆盖扩展和基金承担药费，Ec及access；未独立评价产品创新。',
53:'实质错误：完整自足的泛定义没有明确引导或援引随后另列项目，实际理由把后续五维整体传播到当前句。独立判断全0；逐字引文存在不证明语义归属成立。',
54:'明确“包括下列药物内容”的引导关系，后列五维真正补足评价内容，全1及各来源子类成立。',
55:'常规剂量调整无损害或管理困难依据，不自动S/F。',
56:'每周采血管理负担及基层完成能力，clinical_management；未明确毒性不自动S。',
57:'保留边界：新的编号本身不属创新，预期I0有依据；但当前另有产品组成和剂型均未改变的明确否定属性判断，v1.3允许否定陈述，实际I1理由也可辩护。未用目标分数强迫改标；偏好I0不作无争议错误。',
58:'从小容量注射液变为无菌粉末制剂的明确相对产品改变，attribute；无优效门槛。',
59:'试验数据格式存档和一般保密义务，没有独占创新权利。',
60:'六年专有数据保护且排除依赖申报，知识产权attribute；不猜数据S/E内容。',
61:'病重急需且希望早用药，未明确无治疗或获取障碍、保障安排。',
62:'尚无可获得治疗药物且提供持续供应，access；缺口不自动E/I。',
63:'慢病急救用药仅为材料分组，未实质讨论五维。',
64:'明确美容用途药物不覆盖，保障排除也属于access。',
65:'核对编号到期日并归档，保障协议仅事务对象。',
66:'药物保障协议十八个月期限本身规定连续性，access；无独立药费责任不自动Ec。',
67:'药费预算条件仅获再次谈判申请机会，Ec1F0。',
68:'同预算条件明确决定既有保障延续，Ec1及access。',
69:'核对既已依第九款存档的记录编号，未再实质要求S/E内容，不把援引文全部复制。',
70:'当前获得资格必须满足被明确援引的毒性及降低死亡率证据，S/E双1；普通资格不自动I。',
71:'会议地点及签约手续不等于实质经济评价。',
72:'价格相对对照治疗费用下调，Ec；费用基准不等于疗效或患者可负担。',
73:'已列治疗方案仅为资料延期对象，当前不作治疗推荐或药品可及安排。',
74:'推荐药物并提高无进展生存率，E；临床推荐不自动F。',
75:'预约电话沟通形式不从肝毒性主题继承S。',
76:'补充肝毒性发生率及监测结果为实质S资料；监测未说明使用困难不自动F。',
77:'保障延续十八个月，access；另一独立任务的成本分担不能移入Ec。',
78:'明确引导后列疗程成本及药费分担评价，Ec；仅费用责任没有患者负担不额外F。',
79:'购药单据核对及入库一般职责，没有具体质量风险、费用或患者渠道。',
80:'患者在指定基层药房领取计划覆盖治疗药，常规access。',
81:'R7未给实际创新含义，不能凭编号推定I。',
82:'实际定义明确R7为首次开发活性成分原创药，注册类别有创新含义，attribute。',
83:'价格下调比例为Ec；总体创新宗旨不足以补足R7类别或实体支持。',
84:'同价格规则Ec，另有R7实际原创分类定义支持attribute；未另添research_support。',
85:'原创研发团队季度联系人报送是事务性义务，不继承I。',
86:'持续提供面向原创研发团队的免费药学技术咨询，research_support；咨询免费不是药品治疗费用。',
87:'原创团队资料排版便利不是实体研发支持。',
88:'配置专家并对研发方案科学设计提供技术建议，research_support；身份不额外attribute，未具体S/E。',
89:'治疗支出上限为Ec，父条仅申请续约且另决，不作F。',
90:'同支出条件直接决定续签并延长十八个月，Ec及access。',
91:'毒性主题下会议形式和指引修订，未具体分析风险，不继承S。',
92:'逐项分析毒性原因并确定风险控制，S；会议形式不消除实质内容。',
93:'拟限定具体药物保障人群为确诊成人，F access；拟议并不一律排除实质关注。',
94:'拟限定保障人群且基金承担70%药费，Ec及access；仅比例不增加affordability。',
95:'档案室运行及单位储备资金稳定不是药物S/Ec。',
96:'年度药品支付预算与医保基金可持续约束，Ec；无具体覆盖或患者负担不加F。',
97:'企业申请扩大保障范围前预约，仅申请路线。',
98:'当前实际句为本年度拟将该药纳入保障范围，明确药物覆盖命题F；没有已删除的新增适应证，不加I。',
99:'档案室与统计室连通为处方扫描件归档，不是常规患者取药。',
100:'开方机构与协议药房连通并转送处方供患者领药，access。',
101:'老年用药减量没有明确风险或困难依据，不自动S/F。',
102:'每日监测管理负担及社区实施难度为clinical_management；监测不自动药品S。',
103:'方案覆盖及保险承担药费，Ec及access；无患者负担不加affordability。',
104:'覆盖及患者难付自付药费减免，两项独立依据支持access+affordability及Ec。',
105:'比较终点反映治疗获益能力明确E；配置专家向原创研发团队给设计建议为research_support，不复制attribute。',
106:'毒性风险监测设计建议为S且实体研发支持I；无临床管理困难不加F，不复制attribute。',
}
manual_bits=[
'00000','00010','00000','00010','00010','00000','00101','00100','00000','00101',
'00000','00101','00000','11111','00000','00001','00000','00010','00000','00010',
'00000','00001','00000','00001','00000','00001','00100','00101','00000','11000',
'00000','00100','00000','01000','00000','10000','00001','00100','00000','00001',
'00000','00010','00100','00110','00000','00010','00000','00010','00100','00101',
'00000','10000','00001','00101','00000','00100','00000','00001','00000','00001',
'00000','00001','00101','00101','01010','10010']
assert len(manual_bits)==66
independent=first[:]
for i,bits in enumerate(manual_bits,41):
    independent.append({'ordinal':i,'id':tests[i-1]['input']['id'],
      'independent_labels':dict(zip(DIMS,map(int,bits))),
      'full_five_dimension_actual_reasons_evidence_subtypes_quality_read':True,
      'judgement':'substantive_context_propagation_error' if i==53 else 'retained_reasonable_boundary' if i==57 else 'supported',
      'note':notes[i]})
assert len(independent)==106

errors=[];evidence_n=0;rawmap={};inputmap={};synthetic_batches=[]
for n in [62,24,20]:
    run=BASE/f'runtime-unchanged-v2/synthetic{n}-candidate07-first-run'
    pred=read(run/'all_predictions.json');summary=read(run/'execution_summary.json')
    frozen=run/'frozen_input.jsonl';bindings[str(frozen)]=sha(frozen)
    ins=[json.loads(line) for line in frozen.read_text().splitlines() if line.strip()]
    assert len(ins)==n and len(pred['rows'])==n
    assert summary['input_sha256']==sha(frozen)
    jsonl=run/'all_predictions.jsonl';bindings[str(jsonl)]=sha(jsonl)
    jsonlrows=[json.loads(line) for line in jsonl.read_text().splitlines() if line.strip()]
    assert summary['output_sha256']==sha(jsonl)
    assert canon(jsonlrows)==canon(pred['rows'])
    assert summary['selected_tool_event_count']==0
    for row in ins: assert row['id'] not in inputmap;inputmap[row['id']]=row
    for row in pred['rows']: assert row['id'] not in rawmap;rawmap[row['id']]=row
    for batch in sorted((run/'batches').glob('batch-*')):
        sel=read(batch/'selection.json');assert len(sel['attempts'])==1
        a=run/sel['selected_relative_path'];raw=read(a/'raw_output.json')
        eventpath=a/'events.jsonl';bindings[str(eventpath)]=sha(eventpath)
        ev=[json.loads(line) for line in eventpath.read_text().splitlines() if line.strip()]
        messages=[e['item'] for e in ev if e.get('type')=='item.completed' and e.get('item',{}).get('type')=='agent_message']
        assert len(messages)==1 and canon(json.loads(messages[0]['text']))==canon(raw)
        assert sel['selected_output_sha256']==sha(a/'raw_output.json')
        assert sel['selection_uses_metric_or_label_values'] is False
        assert sel['attempts'][0]['errors']==[] and sel['attempts'][0]['tool_event_count']==0
        for row in raw['rows']: assert canon(row)==canon(rawmap[row['id']])
        synthetic_batches.append({'run_n':n,'batch':batch.name,'attempt_count':1,'event_raw_full_object_equal':True,'selected_output_sha256':sha(a/'raw_output.json')})

expected_diff=[]
for t,review in zip(tests,independent):
    inp=t['input'];a=t['candidate07_intact_actual_row'];ident=inp['id']
    assert ident==a['id']==review['id']
    assert canon(inp)==canon(inputmap[ident]) and canon(a)==canon(rawmap[ident])
    assert set(a)=={'id','labels','dimension_reasons','evidence','fairness_subtypes','innovation_subtypes','safety_quality_basis'}
    assert set(a['labels'])==set(a['dimension_reasons'])==set(DIMS)
    assert all(type(a['labels'][d]) is int and a['labels'][d] in [0,1] for d in DIMS)
    assert all(isinstance(a['dimension_reasons'][d],str) and a['dimension_reasons'][d].strip() for d in DIMS)
    for e in a['evidence']:
        evidence_n+=1
        assert set(e)=={'dimension','source','quote'}
        assert a['labels'][e['dimension']]==1 and e['quote']
        assert e['source'] in ['unit','context']
        target=[inp['text']] if e['source']=='unit' else strings(inp['contexts'])
        assert any(e['quote'] in x for x in target), (ident,'nonliteral',e['dimension'])
    for d in DIMS:
        assert a['labels'][d]==0 or any(e['dimension']==d and e['source']=='unit' for e in a['evidence'])
    for dim,key,allowed in [('F','fairness_subtypes',{'access','affordability','clinical_management','dimension_information'}),('I','innovation_subtypes',{'attribute','research_support','qualification_advantage'})]:
        assert set(a[key])<=allowed and len(a[key])==len(set(a[key]))
        assert bool(a[key])==bool(a['labels'][dim])
    assert a['safety_quality_basis']=='no_quality_basis'
    dif=[d for d in DIMS if a['labels'][d]!=t['labels'][d]]
    assert dif==t['mechanical_different_dimensions']
    if dif: expected_diff.append({'id':ident,'dimensions':dif,'preregistered':t['labels'],'actual':a['labels'],'semantic_status':review['judgement'],'independent_note':review['note']})
    review['actual_row_sha256']=hashlib.sha256(canon(a).encode()).hexdigest()
    review['input_sha256']=hashlib.sha256(canon(inp).encode()).hexdigest()
    review['each_dimension']={d:{'actual':a['labels'][d],'independent_preferred':review['independent_labels'][d],
      'status':'substantive_error' if review['ordinal']==53 else 'reasonable_boundary' if review['ordinal']==57 and d=='I' else 'supported',
      'reason_and_evidence_read':True} for d in DIMS}
    review['F_I_subtypes_independently_reviewed']=True
    review['S_quality_basis_independently_reviewed']=True
    review['literal_evidence_mechanical_check']='PASS'

redactorpath=ROOT/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py'
bindings[str(redactorpath)]=sha(redactorpath)
spec=importlib.util.spec_from_file_location('reserved_redactor',redactorpath)
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
redactor=module.ReservedContextRedactor()
reserved=redactor.audit_object_no_full_match({'tests':tests});assert reserved['no_remaining_full_normalized_reserved_unit_match']
assert len(inputmap)==len(rawmap)==106 and all(not redactor.is_reserved(x) for x in inputmap)
for name in ['完整五维手册-v1.3.md','共用操作说明-v1.4.md']:
    p=ROOT/'outputs/coding-revision-20261007-r3/protocol'/name;bindings[str(p)]=sha(p)
assert sha(SOURCE)==SHA
assert all(sha(Path(p))==h for p,h in bindings.items())
report={
 'review_finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'review_kind':'independent_agent_full_field_semantic_review_of_development_synthetic_controls',
 'source_path':str(SOURCE),'source_sha256':SHA,'source_files_modified':False,
 'scope':{'synthetic_cases':106,'dimensions_read':530,'every_input_and_all_given_contexts_read':True,'every_actual_reason_evidence_F_I_subtype_S_quality_read':True,
  'real240_read':False,'protected_originals_manually_read':False,'reviewer_model_calls':0,'reviewer_classifier_calls':0,
  'actual_synthetic_run_logical_batches_independently_bound':5,'actual_synthetic_attempts_independently_bound':5,
  'whole_candidate_15_logical_15_attempts':'author-reported; this report independently binds only the five synthetic batches, not real240'},
 'overall_status':'SUBSTANTIVE_FAILURE_RETAINED_BOUNDARY_NOT_UNQUALIFIED_PASS',
 'semantic_summary':{'supported_cases':104,'substantive_error_cases':1,'reasonable_boundary_cases':1,
  'substantive_error_id':'C05-NEW-015','substantive_error_dimensions':DIMS,'reasonable_boundary_id':'C05-NEW-019',
  'all_current20_new_controls_full_semantic_review':'supported',
  'mechanical_match_is_not_semantic_acceptance':True},
 'mechanical_checks':{'status':'PASS','input_actual_projection_raw_event_identity':True,'actual_schema_binary_and_reasons':True,
  'all_evidence_literal':True,'evidence_objects_checked':evidence_n,'every_one_has_current_unit_evidence':True,
  'F_I_presence_and_enum_consistent':True,'all_quality_markers_no_quality_basis_semantically_supported_except_context_error_noted':True,
  'first_valid_attempt_zero_tool_selection_bound':synthetic_batches,'protected_full_match_scan':reserved,
  'does_not_prove_absence_of_partial_or_paraphrased_overlap':True},
 'preregistered_actual_disagreements':expected_diff,
 'historical_issue_tracking':[
  {'id':'C03-CONTROL-008','historical':'额外affordability缺乏独立负担依据','current':'CLOSED:当前仅access，Ec费用责任有据。历史异议不抹除。'},
  {'id':'C04-CONTROL-034','historical':'审核排序费用阈值理由误作费用管制','current':'CLOSED:当前理由明确仅排序，Ec1F0。'},
  {'id':'C05-NEW-019','historical':'行政编号不构成产品创新，预期I0','current':'OPEN_BOUNDARY:当前I1依否定产品属性判断，可与否定关注原则辩护；未擅自修改预期或输出。'}],
 'manual_basis':{'context_rule':['v1.3:17','v1.4:7'],'negative_attention':['v1.3:9','v1.3:11','v1.4:7'],
  'I':['v1.3:43-47','v1.3:125','v1.3:142','v1.3:166','v1.4:13-16'],
  'F_Ec':['v1.3:35-37','v1.3:53','v1.3:123','v1.3:152','v1.4:21-26']},
 'interpretive_limits':['这是开发合成控制的agent复审，不是新的真人盲评或独立概率验证。',
  '不把当前522/530机械预期匹配当作效度；原预期存在可辩护分歧，语义结果单列。',
  'v1预检时点失配的99维旧意见不用于当前106；当前输入及实际结果逐条重新读取。',
  '不能保证全量语义正确、论文录用或新独立效度；不改提示、控制预期、实际输出、A/C、手册或正文。'],
 'reviewer_check_repair_history':{'initial_failed_assertion_preserved':str(OUT/'review_actual106_attempt01_failure_PRESERVED.json'),
  'correction':'execution_summary.output_sha256实际绑定all_predictions.jsonl，修正原JSON假定并独立核JSONL与JSON行完整相等；不是候选实际输出或模型重跑。'},
 'reviews':independent,'source_bindings':bindings}
rp=OUT/'candidate07_actual106_independent_semantic_review.json'
rp.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
md='''# 候选07实际106合成控制独立复审

结论：不能记为无保留通过。106条均实际逐条读完输入、给定上下文、五维理由与引文、F/I子类和S质量来源；104条支持当前输出，1条实质错误，1条合理边界保留。

- C05-NEW-015：当前完整泛定义未明确引导后列项目，却从后续另列项目传播五维，实际全1，独立意见全0（v1.3第17行、v1.4第7行）。引文逐字存在不能替代语义归属。C05-NEW-016明确“包括下列”是真实引导，五维1成立。
- C05-NEW-019：新编号本身不是创新；当前还明确否定组成/剂型改变。I0预期与I1否定性属性判断均有手册解释空间，保留争议，不强改。
- C03-CONTROL-003的明确更快上市/更多患者用药，当前F1有可及目的依据；C05-NEW-012实际延续给付条件，当前Ec1有支付条件依据。这两项与旧预期不同，未擅自回填。
- 历史008额外affordability、034理由精度异议保留；当前008仅access，034明确仅审核排序，两项当前闭合。

独立机械检查通过：106输入/投影与原始合成实际输出相等，五个合成批次的唯一完成agent_message与raw完整对象相等、首次有效技术选择及零工具记录可绑定；全部引文逐字，所有1均有当前句引文，F/I子类枚举和S质量标记有效。保护正文机械完整匹配为0，未人工读取真实240或267保留正文。复审者模型/分类器调用0。

这是开发合成控制的AI复审，不能替代新真人盲评或独立概率验证；机械匹配不是语义效度。所有冻结/实际源文件未改。完整逐例、逐维意见及来源哈希见同名JSON。
'''
(OUT/'candidate07_actual106_independent_semantic_review.md').write_text(md)
seal={'finished_utc':report['review_finished_utc'],'files':{str(p):sha(p) for p in [rp,OUT/'candidate07_actual106_independent_semantic_review.md',Path(__file__)]}}
(OUT/'actual106_review_seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(rp),'sha256':sha(rp),'status':report['overall_status'],'cases':len(independent),'mechanical':'PASS','semantic_errors':['C05-NEW-015'],'boundary':['C05-NEW-019']},ensure_ascii=False))
