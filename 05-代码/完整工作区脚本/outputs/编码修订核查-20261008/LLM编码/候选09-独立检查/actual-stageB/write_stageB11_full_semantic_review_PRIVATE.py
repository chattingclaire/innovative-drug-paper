"""Seal independent reading of all55 actual B dimensions. No model calls."""
import sys
sys.dont_write_bytecode=True
import datetime,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parent;CAND=BASE.parent/'候选09-分步判读'
RUN=CAND/'runs/initial11-stageB-first-run';ARUN=CAND/'runs/initial11-stageA-first-run'
DIMS=['S','E','Ec','I','F']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(Path(p).resolve()),'sha256':sha(p),'bytes':Path(p).stat().st_size}
def canonical(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def save(p,o):
 with p.open('x')as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
ip=BASE/'known11_inputs_ORIGINAL_FIELDS_PRIVATE_FROZEN.jsonl';ep=BASE/'stageB_partial_expectations_PRIVATE_PREOUTPUT.json';op=RUN/'all_predictions.json'
assert sha(ip)=='386d17fbe0fb45d6ebcbf8d0b3e834c18953c13b726f29d051b242662d9a0a9c'
assert sha(ep)=='6f3d6397064510cc1a9419b8e40d5586db0d091e5f881b77980b9faa5d0d3c16'
assert sha(op)=='38a3f8968c2ccb68fbf93fe2d1e3c7cd2ea79100a0aedd25cc17bb78f322bc17'
inputs=[json.loads(s)for s in ip.read_text().splitlines()if s.strip()];out=json.loads(op.read_text());expected=json.loads(ep.read_text());exps={r['id']:r for r in expected['cases']}
packet=json.loads((RUN/'input_packet.json').read_text());aout=json.loads((ARUN/'all_stageA_records.json').read_text())
assert canonical(packet['rows'])==canonical(inputs)
assert set(packet)=={'rows','stageA_records'}
assert [x['id']for x in packet['stageA_records']]==[x['id']for x in inputs]
for item,record in zip(packet['stageA_records'],aout['rows']):
 assert canonical(item['record'])==canonical(record)
 assert item['record_sha256']==hashlib.sha256(canonical(record).encode()).hexdigest()
base=load('c09_independent_actualB_base',CAND/'runtime/run_production_v32.py')
assert not base.v.validate({'rows':inputs},out)
attempt=RUN/'attempts/attempt-01'
assert (attempt/'raw_output.json').read_bytes()==op.read_bytes()
events=(attempt/'events.jsonl').read_text();assert not base.event_output_binding_audit(events,out)['errors']
ea=base.event_audit(events);assert ea['tool_or_unknown_item_event_count']==0 and ea['completed_turns']==1 and ea['turn_errors']==[]
metadata=json.loads((attempt/'run_metadata.json').read_text());summary=json.loads((RUN/'technical_summary.json').read_text())
assert summary['actual_attempts']==1 and metadata['status']=='accepted_structural_literal_zero_tools' and not metadata['errors']
assert not summary['material_flags'] and metadata['tool_event_count']==0
assert [x['id']for x in inputs]==[x['id']for x in out['rows']]

# Each value below is a post-output agent judgment under the frozen manual,
# distinct from pre-output partial expectations and original human labels.
bases={
'RECODE25-04894':[
 '处方流转设施本句不讨论药物损害；未继承章节风险或同段基金监管，S0支持。',
 '没有治疗效果或效果证据命题，E0支持。',
 '没有本句药费/药价/支付/基金支出内容，未复制同段后续基金监测，Ec0支持。',
 '没有药物创新属性或研发支持，I0支持。',
 '确定漏判：当前明确连通经办机构、定点医疗机构、定点零售药店并保证电子处方流转，构成常规用药获取渠道。v1.3保障获取及常规治疗获取渠道、v1.4 F4支持F1/access；不能额外要求本句也改变支付范围或承诺药品持续供货。'],
'RECODE25-02220':[
 '起草研发风险管理技术指导并指导临床试验各方；同段为该风险管理补足药物临床试验安全风险控制对象，S1支持。并未仅凭安全章节标题赋值。',
 '背景虽说明临床试验用于安全/有效研究，当前技术指导命题不要求疗效评价或证据，E0支持。',
 '无价格/药费/成本/支付内容，Ec0支持。',
 '药审中心实际为创新药研发期间风险管理提供技术指导，I1/research_support支持，保护目标保留。',
 '无治疗获取缺口/负担/药品管理难度命题，F0支持。'],
'RECODE25-02830':[
 '申请人更新DRMP和DSUR、持续药物警戒/风险最小化、保障受试者安全，S1支持。',
 '可靠性与治疗效果判断未有当前明确联系，不能把数据可靠性自动转疗效，E0支持。',
 '无价格/药费/支付成本命题，Ec0支持。',
 '当前施事为申请人执行安全义务，并非机构给予创新资源或支持；I0支持，旧错目标修复。',
 '一般受试者权益、安全及福祉不是实际治疗获取安排，F0支持。'],
'RECODE25-01955':[
 '监管批准/适应症变化不自动证明安全内容，S0支持。',
 '未陈述效果/获益或效果证据，E0支持；重大变化无须另证优效才能讨论I。',
 '支付范围仅为主动申请调整事项，当前不规定实际费用责任或支付条件，Ec0可支持。',
 '确定漏判：当前明确适应症或功能主治发生重大变化，且A完整保留。v1.4 I2允许相对既有产品的具体属性变化，无需再证原创、新靶点、注册创新分类或优效。应I1/attribute。',
 '须申报后方可调整属于申请办理前提，未明确实际新增/退出保障结果，F0支持。'],
'RECODE25-02764':[
 '批准及变更状态不自动讨论损害或安全证据，S0支持。',
 '适应症变化不等于效果评价，未给疗效依据，E0支持。',
 '无价格/药费/支付责任，Ec0支持。',
 '确定漏判：适应症/功能主治重大变化并针对此次变更取得批准证明，是当前明确属性变化。v1.4 I2不要求另有原创/改良类别名或创新注册分类，应I1/attribute。',
 '父条款仅允许目录外药品按程序申报，不等于实际保障纳入，F0支持；引用第七/八条未给全文，未据想象增标。'],
'C05-NEW-015':[
 '独立方法定义不实质援引相邻安全清单，S0支持。','没有效果内容承接，E0支持。','没有价格费用内容承接，Ec0支持。','没有创新属性内容承接，I0支持。','没有可负担等保障内容承接，F0支持。'],
'RECODE25-02086':[
 '共同续约条件无损害/风险/药物警戒内容，S0支持。','同治疗领域是价格比较对象，不是效果评价，E0支持。',
 '直接援引完整清单中的预算/基金支出/治疗费用/销售价格/支付标准，Ec1支持。',
 '独家身份不等于创新属性，条件不规定创新支持或资格，I0支持。',
 '到期药品满足共同条件后可简易续约两年，实质保障连续性，F1/access支持，保护目标保留。'],
'C05-NEW-016':[
 '当前下列直接控制清单中的药物安全性，S1支持。','同一真实援引包括治疗效果，E1支持。','同一真实援引包括药费，Ec1支持。','同一真实援引包括原创属性评价内容，I1/attribute支持。','同一真实援引包括患者可负担性，F1/affordability支持。'],
'RECODE25-01562':[
 '预算/续约条件无药物安全内容，S0支持。','无治疗效果/效果证据，E0支持。',
 '直接预算增幅上限及条件1比较基准为药品基金支出条件，Ec1支持。','无创新属性/支持/资格，I0支持。',
 '真实父谓词恢复到期药品共同条件下简易续约2年；当前是保障延续的实质子条件，F1/access支持，旧错目标修复。'],
'RECODE25-02845':[
 '申请人按药物安全风险特征执行药物警戒并保障受试者安全，S1支持。','未讨论治疗效果/证据，E0支持。','未讨论价格/药费/支付成本，Ec0支持。',
 '当前为申请人安全管理义务，不是监管机构提供创新研发资源，I0支持，旧错目标修复。',
 '受试者一般安全无实际治疗获取缺口或负担/药品管理难度内容，F0支持。'],
'RECODE25-03876':[
 '完整图示无药物损害或安全证据命题，S0支持。','罕见病名/技术审评/适应症变化不等于治疗效果判断，E0支持。',
 '价格谈判/协商在本图为流程节点和成败分流；没有实际药价、费用责任或经济评价条件，依v1.3仅谈判程序排除，Ec0可支持。不是要求所有Ec必须有金额。',
 '确定漏判：理由仅否定目录名称、新通用名、技术审评身份，漏掉完整图示目录内分支明确适应症/功能主治重大变化。A的p7已完整保存这一实体改变，v1.4 I2支持I1/attribute。',
 '各分支实质明确条件性纳入/不纳入、新增适应症/维持表述，F1/access支持，没有仅据申报名称赋值。']}
errors={('RECODE25-04894','F'):1,('RECODE25-01955','I'):1,('RECODE25-02764','I'):1,('RECODE25-03876','I'):1}
issue_judgments={
'RECODE25-02220':'可接受的B补充语境解释。A和B使用语境目的不同；这条resolved_context_issue不证明原A必须改写，不能把A记录编辑后重发。',
'RECODE25-04894':'该boundary_note不能消除已确认F漏判；把处方渠道仅作信息设施，缩窄既定F范围。',
'RECODE25-01955':'Ec/F申报资格与实际保障区别可接受；该issue未承认独立I重大属性变化漏判。',
'RECODE25-02764':'申报资格不是保障、变化不必证明疗效均可接受；将明确重大属性变化的I漏判也称边界不成立。',
'RECODE25-02086':'正确说明控制性清单、基金价格条件及共同续约连续性，支持Ec/F。',
'RECODE25-01562':'正确保留明确条件1引用、预算及父续约保障关系，支持Ec/F。',
'RECODE25-03876':'F条件性保障范围与仅流程Ec排除可支持；只讨论标题不够，仍漏掉本单元内部重大变化这一I直接依据。'}
case_reviews=[];hard=[];confirmed=[]
for inp,row in zip(inputs,out['rows']):
 rid=row['id'];exp=exps[rid];dims=[]
 for i,d in enumerate(DIMS):
  failed=(rid,d)in errors;frozen=d in exp['frozen_partial_labels'];actual_value=row['labels'][d]
  if frozen:hard.append({'id':rid,'dimension':d,'expected':exp['frozen_partial_labels'][d],'actual':actual_value,'match':actual_value==exp['frozen_partial_labels'][d]})
  dr={'dimension':d,'actual_label':actual_value,'actual_reason':row['dimension_reasons'][d],'preoutput_frozen_cell':frozen,'judgment':'CONFIRMED_FALSE_NEGATIVE'if failed else'SUPPORTED_BY_CURRENT_TEXT_AND_MANUAL','independent_postoutput_agent_opinion':errors[(rid,d)]if failed else actual_value,'basis':bases[rid][i]}
  if frozen:dr['preoutput_expected_label']=exp['frozen_partial_labels'][d]
  dims.append(dr)
  if failed:confirmed.append({'id':rid,'dimension':d,'actual':actual_value,'preoutput_expected':exp['frozen_partial_labels'][d],'agent_review_opinion':errors[(rid,d)],'basis':bases[rid][i],'kind':'regression_of_previously_correct_protection'if exp['role']=='currently_correct_protection'else'known_error_not_repaired'})
 evidence=[]
 for i,e in enumerate(row['evidence']):evidence.append({'index':i,'dimension':e['dimension'],'source':e['source'],'quote_sha256':hashlib.sha256(e['quote'].encode()).hexdigest(),'literal_validator_pass':True,'semantic_judgment':'Supports the assigned dimension when read with its current-unit anchor and necessary supplied context; reviewed individually.'})
 subtype_findings=[]
 for k,vals in exp['frozen_subtypes'].items():
  if set(row[k])!=set(vals):subtype_findings.append({'field':k,'actual':row[k],'preoutput_expected':vals,'judgment':'Downstream omission accompanying the same confirmed false-negative dimension; not counted as an additional independent dimension error.'})
 case_reviews.append({'id':rid,'role':exp['role'],'current_text_sha256':hashlib.sha256(inp['text'].encode()).hexdigest(),'dimension_reviews':dims,'evidence_reviews':evidence,'fairness_subtypes_actual':row['fairness_subtypes'],'innovation_subtypes_actual':row['innovation_subtypes'],'all_subtype_fields_reviewed':True,'subtype_findings':subtype_findings,'safety_quality_basis_actual':row['safety_quality_basis'],'quality_judgment':'no_quality_basis supported: no explicit medicinal manufacturing-quality safety/risk basis in this unit or relevant context. Existing therapeutic risk evidence remains S without a quality marker.','issues':[{'actual_status':x['status'],'actual_description':x['description'],'independent_review':issue_judgments[rid]}for x in out['issue_records']if x['id']==rid]})
assert len(hard)==19 and sum(x['match']for x in hard)==15 and len(confirmed)==4
assert sum(len(x['dimension_reviews'])for x in case_reviews)==55
assert sum(len(x['evidence_reviews'])for x in case_reviews)==28

# Metadata-only B visibility addendum. Original four context locations and two
# A-record quotations are reported separately; no protected sentence copied.
em_path=BASE/'known11_source_extraction_and_protection_metadata.json';em=json.loads(em_path.read_text());occ=[]
for item in em['reserved_context_occurrences']:
 rid=item['current_development_unit_id'];idx=[x['id']for x in packet['rows']].index(rid)
 keypath=item['locator'].split('].',1)[1];v=packet['rows'][idx]
 import re
 for k,n in re.findall(r'([^.\[\]]+)|\[(\d+)\]',keypath):v=v[int(n)]if n else v[k]
 assert hashlib.sha256(v.encode()).hexdigest()==item['context_sha256']
 occ.append({'kind':'unchanged_full_original_context','current_development_unit_id':rid,'reserved_unit_id':'RECODE25-02822','path':item['locator'].replace('root','rows',1),'sha256':item['context_sha256'],'prior_registered_original_span_sha256':item['matched_original_span_sha256']})
for i,item in enumerate(packet['stageA_records']):
 if item['id']in ['RECODE25-02830','RECODE25-02845']:
  original=next(x for x in inputs if x['id']==item['id'])['contexts']['verified_parent_context'][1]['text']
  for j,cr in enumerate(item['record']['context_records']):
   if '/contexts/verified_parent_context/1/text'in cr['paths']:
    assert cr['context_quote']in original
    occ.append({'kind':'sealed_original_A_context_quotation_from_same_authorized_paragraph','current_development_unit_id':item['id'],'reserved_unit_id':'RECODE25-02822','path':f'stageA_records[{i}].record.context_records[{j}].context_quote','sha256':hashlib.sha256(cr['context_quote'].encode()).hexdigest(),'entire_original_context_or_shorter_quote':'entire paragraph'if cr['context_quote']==original else'shorter literal quotation','not_claimed_as_new_independent_full_reserved_text_match':True})
assert len(occ)==6
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
xp=BASE/'exposure_addenda/candidate09_StageB_actual_request_02822_visibility_metadata_PRIVATE.json'
save(xp,{'status':'ACTUAL_STAGEB_REQUEST_VISIBILITY_REGISTERED_SAME_PREVIOUSLY_AUTHORIZED_CONTEXT','created_at_UTC':now,'candidate':'candidate09-two-step','stage':'B','reserved_unit_id':'RECODE25-02822','original_context_occurrences':4,'sealed_A_context_quotation_occurrences':2,'occurrences':occ,'actual_request':bind(RUN/'request.txt'),'actual_attempt_request':bind(attempt/'request.txt'),'actual_input_packet':bind(RUN/'input_packet.json'),'model_execution':'Root reported actual terminal exit0; one actual request/first valid attempt, zero tools. Internal provider reading/attention not observable.','human_semantic_access':'Already necessarily read under explicit root authorization during StageA review; same given paragraph used to review B. No other protected original opened. Not untouched or independent.','prior_A_semantic_access_addendum':bind(BASE/'exposure_addenda/candidate09_stageA_02822_authorized_semantic_access_PRIVATE.json'),'protected_sentence_copied_into_this_addendum':False,'real_CLI_invocations_by_reviewer':0,'real_model_calls_by_reviewer':0,'original_frozen_files_modified':False})
report={'status':'FAIL_INDEPENDENT_STAGEB11_FULL_SEMANTIC_REVIEW_CONFIRMED_ERRORS_BLOCK_EXPANSION','created_at_UTC':now,'candidate':'candidate09-two-step','stage':'B','scope':'initial11-known-development','reviewed_rows':11,'confirmed_semantic_errors':4,'confirmed_errors':confirmed,
 'coverage':{'all_actual_dimension_cells':55,'all_actual_dimension_reasons':55,'preoutput_hard_cells':19,'hard_cells_matching':15,'hard_cells_failed':4,'not_prefilled_cells_independently_reviewed':36,'not_prefilled_cells_defaulted_to_zero':False,'all_evidence_quotes':28,'all_F_I_subtype_fields':22,'all_quality_fields':11,'all_top_level_issue_records':7,'all_original_units_and_contexts_read':True,'original_context_policy_text_paths_from_full_A_review':63,'actual_input_rows_identical_to_A_source':True},
 'preoutput_hard_cell_comparison':hard,'cases':case_reviews,
 'six_known_old_errors':{'repaired_targets':[{'id':'RECODE25-02830','dimension':'I','actual':0},{'id':'RECODE25-02845','dimension':'I','actual':0},{'id':'RECODE25-01562','dimension':'F','actual':1}],'not_repaired_targets':[{'id':rid,'dimension':'I','actual':0,'preoutput_expected':1}for rid in ['RECODE25-01955','RECODE25-02764','RECODE25-03876']],'repaired_count':3,'required_count':6},
 'three_correct_protection_targets':{'preserved':[{'id':'RECODE25-02220','dimension':'I','actual':1},{'id':'RECODE25-02086','dimension':'F','actual':1}],'regressed':[{'id':'RECODE25-04894','dimension':'F','actual':0,'preoutput_expected':1}],'preserved_count':2,'required_count':3},
 'synthetic015_016':{'015_five_zeros_preserved':True,'016_five_ones_preserved':True,'ten_frozen_cells_match':True,'subtype_aux_expectations_provenance':'New09 pre-output manual-based auxiliary expectations; not falsely claimed as original old86 subtype gold.'},
 'boundaries':[],
 'precision_opinions':[{'id':'RECODE25-03876','dimension':'Ec','opinion':'Ec0 is supportable because the actual statements are procedural price-negotiation nodes and outcome routing. This must not become an extra rule demanding numeric prices: actual qualitative price/payment conditions can supportEc without amounts. No new confirmedEc error is asserted.'},{'id':'RECODE25-02220','opinion':'B may independently use original context to resolve drug-risk meaning even where A marked that paragraph not_used. The resolved_context_issue does not authorize editing sealed A and does not by itself refute the prior complete A proposition review.'}],
 'mechanism_diagnosis':'A retained the major attribute changes and concrete prescription-channel relation, and B received those exact records with full original inputs. B nevertheless added a narrower I gate requiring originality/improvement/category beyond explicit major product change, and narrowed F channel content to pure infrastructure. Passing StageA did not establish final-label correctness.',
 'recommendation':'STOP. Do not authorize146/240/4924, adopt09, splice corrected rows, retry semantically, change frozen expectations or edit A/B. Preserve this failed known-development result. Any future authorized revision is a new development candidate and needs separate preparation/review.',
 'private_expectations_unchanged':True,'original_A_and_B_not_edited':True,'human_AB_adjudicated_originals_unchanged_and_not_used_as_full_vector_gold':True,'protected_visibility_addendum':bind(xp),
 'technical_provenance':{'one_first_technical_valid_attempt':True,'unique_completed_agent_full_JSON_equals_raw_equals_final':True,'zero_tools':True,'structural_literal_validator_errors':[],'does_not_prove_semantic_quality':True},
 'source_bindings':[bind(p)for p in [ip,ep,op,ARUN/'all_stageA_records.json',BASE/'actual-stageA/candidate09_stageA11_full_semantic_review_PRIVATE.json',RUN/'input_packet.json',RUN/'request.txt',RUN/'technical_summary.json',attempt/'input.json',attempt/'request.txt',attempt/'raw_output.json',attempt/'events.jsonl',attempt/'run_metadata.json',CAND/'stageA_prompt.txt',CAND/'stageB_prompt.txt',CAND/'design_freeze.json',xp,Path(__file__)]]+expected['manual_bindings'],
 'real_CLI_invocations_by_this_reviewer':0,'real_model_calls_by_this_reviewer':0,'source_files_modified':False,
 'limitations':['This is a single known-development11 pilot, not accuracy on the full corpus or new independent human validity.','36 unfilled pre-output cells were judged from actual originals and frozen handbook, not assumed zero or copied human/old machine vectors.','Pre-output19 comparisons are fixed-regression diagnostics, not a newly representative accuracy estimate.','The4 confirmed failures are not relabeled genuine boundaries by model issue metadata; no human reference labels were changed.','Other protected original texts were not opened;02822 access and visibility remain explicitly exposed.','Original08 FAIL and adopted Rule39/fullLLM03 results remain unchanged.']}
assert sha(op)=='38a3f8968c2ccb68fbf93fe2d1e3c7cd2ea79100a0aedd25cc17bb78f322bc17'
assert sha(ep)=='6f3d6397064510cc1a9419b8e40d5586db0d091e5f881b77980b9faa5d0d3c16'
rp=HERE/'candidate09_stageB11_full_semantic_review_PRIVATE.json';save(rp,report)
print(json.dumps({'report':bind(rp),'B_visibility_addendum':bind(xp),'cells':55,'frozen19_matching':15,'confirmed_semantic_errors':4,'quotes':28,'issues':7,'real_CLI_invocations':0,'real_model_calls':0},ensure_ascii=False))
