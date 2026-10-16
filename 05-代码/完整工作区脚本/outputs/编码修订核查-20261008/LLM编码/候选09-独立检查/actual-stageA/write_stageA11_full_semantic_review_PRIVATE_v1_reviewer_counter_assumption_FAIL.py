"""Seal already completed independent semantic review; no model/CLI calls."""
import sys
sys.dont_write_bytecode=True
import collections,datetime,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
BASE=HERE.parent
CAND=BASE.parent/'候选09-分步判读'
RUN=CAND/'runs/initial11-stageA-first-run'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(Path(p).resolve()),'sha256':sha(p),'bytes':Path(p).stat().st_size}
def load(name,p):
 s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);sys.modules[name]=m;s.loader.exec_module(m);return m
def save(p,o):
 with p.open('x')as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')
ip=BASE/'known11_inputs_ORIGINAL_FIELDS_PRIVATE_FROZEN.jsonl'
ep=BASE/'stageA_semantic_expectations_PRIVATE_PREOUTPUT.json'
ap=RUN/'all_stageA_records.json'
assert sha(ip)=='386d17fbe0fb45d6ebcbf8d0b3e834c18953c13b726f29d051b242662d9a0a9c'
assert sha(ep)=='4c4eae2b3c421ff9fd0fbc11a8d2b4b4d83e63a94d7630bb514fac8de402d1fe'
assert sha(ap)=='8f87de605448a7e4295d6deb166ae99b94a46437e1c954934c60432374625ef5'
inputs=[json.loads(s)for s in ip.read_text().splitlines()if s.strip()]
actual=json.loads(ap.read_text());expected=json.loads(ep.read_text())
exps={r['id']:r for r in expected['cases']}
inventory=load('c09_actualA_independent_inventory',CAND/'runtime/stageA_context_inventory.py')
validator=load('c09_actualA_independent_validator',CAND/'runtime/validate_stageA.py')
base=load('c09_actualA_independent_base',CAND/'runtime/run_production_v32.py')
assert validator.validate({'rows':inputs},actual)==[]
attempt=RUN/'attempts/attempt-01'
assert (attempt/'raw_output.json').read_bytes()==ap.read_bytes()
events=(attempt/'events.jsonl').read_text()
assert base.event_output_binding_audit(events,actual)['errors']==[]
audit=base.event_audit(events)
assert audit['tool_or_unknown_item_event_count']==0 and audit['completed_turns']==1 and audit['turn_errors']==[]
metadata=json.loads((attempt/'run_metadata.json').read_text())
summary=json.loads((RUN/'technical_summary.json').read_text())
assert summary['actual_attempts']==1 and metadata['status']=='accepted_structural_literal_zero_tools' and not metadata['errors']
assert not summary['material_flags'] and metadata['tool_event_count']==0
assert [r['id']for r in inputs]==[r['id']for r in actual['rows']]

opinions={
'RECODE25-04894':('平台—处方流转中心—经办机构/医疗机构/药店连通—保证电子处方顺畅流转的完整动作链保留。未将后续基金监管命题加到当前句。',[
'同段包含当前完整句和若干独立监管句；当前本身自足，not_used合理。',
'重复章节标题提供主题而非新增控制谓词，not_used合理。']),
'RECODE25-02220':('明确药审中心为起草和提供研发风险管理指导的施事，临床试验各方为接受者；没有缩成文件名或申请人一般申报义务。',[
'当前句包含完整起草及技术指导关系；前文背景和其他主体责任不必并入。',
'重复问答标题不添加当前义务或结果，not_used合理。']),
'RECODE25-02830':('三命题分别保留申请人更新DRMP及DSUR执行概要说明、持续药物警戒/风险最小化及双重结果、必要时沟通。施事与全部当前动作未遗漏，未改写为监管机构给予研发资源。',[
'同文段落副本没有新增实质关系，不使用合理。',
'一般考虑标题仅结构位置，不使用合理。',
'前段规定DRMP撰写基础，不直接控制本句更新和报告义务，不使用合理。',
'DRMP指称需要风险管理文件对象解释；定义与本句DRMP/药物警戒锚点相连，使用合理。',
'本次授权已读该完整既登记父语境。实际引用仅界定风险中的潜在治疗风险和数据可靠性风险，与p2并列目的对应；没有承接其余非强制性、未来更新或咨询说明。使用合理。']),
'RECODE25-01955':('时间、批准、适应症/功能主治重大变化、主动申请均被保留为药品限定；父谓词只恢复须申报后方可调整，没有声称已获给付调整或临床优效。一个复合命题已完整承载内容，不要求人为拆成多个p。',[
'同文副本不增加内容，not_used合理。',
'目录内西药和中成药标题恢复真实适用对象，used合理。',
'前一编号2是不同并列情况，未把协议到期/未重大变化混入当前编号3，not_used合理。',
'真实父清单谓词须申报后方可调整，used合理且没有改为申报即获保障。']),
'RECODE25-02764':('重大变化及针对此次变更取得药品批准证明均完整保留。目录外可按程序申报作为父资格结果，未说批准证明等于医保纳入。',[
'同文副本不增加内容，not_used合理。',
'目录外西药和中成药标题恢复适用对象，used合理。',
'新冠用药句属于上一编号条件，未混入当前编号2，not_used合理。',
'父条款恢复共同法条前提及可按程序申报。保留第七/八条这一未展开引用，不猜其具体实体要求，used合理。']),
'C05-NEW-015':('当前只给一般综合评价方法定义，未加入安全性等五维清单；原始期待的独立定义/相邻另列关系得到保留。',[
'相邻句独立另列项目；没有当前对下列内容的实质援引，not_used合理。判断依据为完整句功能与关系，而不是字段名或位置。']),
'RECODE25-02086':('当前父谓词的到期药品、同时满足清单条件、可以简易续约和2年有效期全部保留。后项1—5及预算项两个条件分支被逐项解读；不把所有药品无条件续约或把流程降为仅申报。',[
'当前句两处逐字副本不添加命题，not_used合理。',
'一、条件的两处结构标题不增加实体条件，not_used合理。',
'协议到期后谈判药品（含续约药品）恢复当前药品对象，used合理。',
'规则二简易续约与已明示性质重复，not_used合理。',
'规范化标点副本不新增语义，not_used合理。',
'下列的实质引导控制独家药品条件，used合理。',
'下列控制本协议期基金实际支出≤预算200%及企业预估值定义，used合理。',
'下列控制未来两年预算合理增幅这一总项，used合理。',
'总项下不调整范围分支保留100%和两者高者比较基准，used合理。',
'调整范围分支保留原范围满足前项和因调整所致增幅100%，未改成两分支同对象同时适用，used合理。',
'下列控制市场环境未重大变化及其直接定义，价格/费用情形范围被保留，used合理。',
'下列控制不符合常规目录管理条件，未翻转为已纳常规目录，used合理。']),
'C05-NEW-016':('当前应包括下列药物内容真实引导后项，五类项目被完整恢复为评价内容；没有声称药品已经满足正面评价。',[
'明确下列援引使后项清单成为必要对象补足，used合理，与015对称。']),
'RECODE25-01562':('预算子条件保留调整所致增幅、未来两年、100%及原范围满足条件1；连接真实父级共同条件和2年简易续约，未声称单独本项足够或保证所有药品续约。',[
'同文副本不增加内容，not_used合理。',
'条件标题无具体谓词，不使用合理。',
'明确条件(1)援引允许恢复比较基准，不是因相邻而盲目承接，used合理。',
'真实父谓词恢复到期/同时全部条件/简易续约2年，used合理。',
'续约规则总对象明确协议期内谈判药品，used合理且不传播其他未给条件。',
'分支标题与父谓词重复，not_used合理。']),
'RECODE25-02845':('保留申请人根据药物安全风险开展药物警戒、全面主动识别管理风险和确保受试者安全。没有把指导原则的存在变成当前机构提供支持。',[
'后续独立句再展开活动实例。当前完整总述不依赖逐项复制其内容；not_used可接受。注意无冒号/如下并非一般语境使用的必要门槛。',
'重复章节标题不改变自足当前内容，not_used合理。',
'DRMP背景不必再次补足已明确的药物安全性风险和受试者，not_used合理。',
'本次已读完整既登记风险父语境；当前明指药物安全性风险/受试者，无需把父段另一数据可靠性分支或一般说明自动加进来，not_used合理。']),
'RECODE25-03876':('七命题保留完整流程、两种目录外申报条件、目录类别、仅基本目录/仅商保/双目录的不同分支，以及目录内重大变化和新增适应症协商成功/失败结果。价格协商及条件性实际纳入没有被标题或申请资格覆盖。未把单纯更名当实体创新。',[
'同文图示段落副本不增加节点/条件/结果，not_used合理。'])}

reviews=[]
for row,out in zip(inputs,actual['rows']):
 rid=row['id'];overall,notes=opinions[rid];inv=inventory.inventory(row)
 assert len(notes)==len(out['context_records'])
 path_lookup={leaf['path']:leaf['text']for leaf in inv}
 covered=[p for cr in out['context_records']for p in cr['paths']]
 assert collections.Counter(covered)==collections.Counter(path_lookup)
 cr_reviews=[]
 for i,(cr,note)in enumerate(zip(out['context_records'],notes)):
  cr_reviews.append({'record_index':i,'paths':cr['paths'],'actual_status':cr['status'],'review_judgment':'SUPPORTED_IN_THIS_INPUT','semantic_basis':note,'proposition_ids':cr['proposition_ids'],'literal_context_quote_sha256':hashlib.sha256(cr['context_quote'].encode()).hexdigest(),'source_text_sha256_by_path':{p:hashlib.sha256(path_lookup[p].encode()).hexdigest()for p in cr['paths']}})
 reviews.append({'id':rid,'current_text_sha256':hashlib.sha256(row['text'].encode()).hexdigest(),'judgment':'PASS_NO_CONFIRMED_STAGEA_SEMANTIC_ERROR','current_propositions_reviewed':[p['proposition_id']for p in out['current_propositions']],
  'complete_current_proposition_review':overall,'preoutput_must_recognize_checked':exps[rid]['must_recognize'],'preoutput_must_not_infer_checked':exps[rid]['must_not_infer'],
  'preoutput_expectation_changed':False,'context_inventory_paths_count':len(inv),'context_record_reviews':cr_reviews,'material_status_actual':out['material_status'],'material_note_review':'Sufficient for the current propositions and the supplied parent/reference relationships; not a claim to reconstruct every external rule or unavailable branch. No observed missing-material issue or forced boundary in this StageA record.',
  'confirmed_errors':[],'boundaries':[]})

now=datetime.datetime.now(datetime.timezone.utc).isoformat()
meta_path=BASE/'known11_source_extraction_and_protection_metadata.json';em=json.loads(meta_path.read_text())
exposure={'status':'AUTHORIZED_NECESSARY_SEMANTIC_ACCESS_ACTUALLY_OCCURRED_PREVIOUS_UNREAD_STATE_SUPERSEDED_FOR_THIS_REVIEWER',
 'recorded_at_UTC':now,'semantic_reading_completed_by_UTC':now,'exact_first_read_clock':'Not independently captured; occurred during this task before this completion timestamp.',
 'reviewer':'/root/validation_state_oct8','role':'AI agent performing human-style semantic development review; not a new human coder or adjudicator',
 'authorization':'Root explicit task instruction after actual StageA terminal permitted only previously registered02822 context in these11 known-development inputs.',
 'reserved_unit_id':'RECODE25-02822','current_development_unit_ids':['RECODE25-02830','RECODE25-02845'],
 'occurrences':em['reserved_context_occurrences'],'actual_input':bind(ip),'actual_request':bind(RUN/'request.txt'),'actual_attempt_request':bind(attempt/'request.txt'),'actual_output':bind(ap),
 'prior_registered_exposure_metadata':em['prior_registered_metadata_02822'],
 'relationship_to_prior_exposure':'This member already appears in the06 all-changes17-member agent semantic-development exposure set and the06 full24059-member model-request visibility set. This adds a new reviewer and09 actual request access record; it is not a new independent or untouched evaluation item.',
 'current_semantic_scope':'Read the complete existing parent-context paragraph at the four registered paths; checked its limited actual use for02830 and non-use for02845. Other reserved original texts were not opened.',
 'protected_original_sentence_copied_into_this_addendum':False,'preoutput_expectations_unchanged':True,
 'real_CLI_invocations_by_reviewer':0,'real_model_calls_by_reviewer':0,'original_freeze_or_input_modified':False}
xp=BASE/'exposure_addenda/candidate09_stageA_02822_authorized_semantic_access_PRIVATE.json';save(xp,exposure)
seal_path=RUN/'stageA_seal.json'
report={'status':'PASS_INDEPENDENT_STAGEA11_FULL_SEMANTIC_REVIEW_ROOT_GATE_AND_B_AUTHORIZATION_STILL_REQUIRED',
 'created_at_UTC':now,'candidate':'candidate09-two-step','stage':'A','scope':'initial11-known-development','reviewed_rows':11,
 'confirmed_semantic_errors':0,'confirmed_errors':[],'boundaries':[],
 'precision_opinions':[{'id':'RECODE25-02845','issue':'Rationale mentions absence of colon/如下. Such punctuation or cue words are not necessary for every legitimate context relation; the supported decision here rests on the self-contained current duty and the independent elaborating sentence. No observed proposition omission or wrong relation follows in this actual output.','requires_rewriting_original_A':False},
 {'id':'RECODE25-02764','issue':'Parent refers to external articles7/8 without their contents. A appropriately retains that opaque reference rather than guessing; B must not use unstated article contents as evidence. This is not a missing-material blocker for the explicit current major-change proposition.','requires_rewriting_original_A':False},
 {'id':'RECODE25-01562','issue':'Other simultaneous conditions remain an unspecified joint requirement. A does not invent them or claim this one budget condition alone guarantees renewal. Sufficient applies to understanding this current subcondition and parent outcome, not full individual drug eligibility determination.','requires_rewriting_original_A':False}],
 'coverage':{'original_units':11,'all_original_context_policy_text_leaves':sum(len(inventory.inventory(x))for x in inputs),'current_propositions':sum(len(x['current_propositions'])for x in actual['rows']),'context_relation_records':sum(len(x['context_records'])for x in actual['rows']),'all_material_status_and_notes_reviewed':11,'all_given_contexts_semantically_read':True,'exact_duplicate_text_paths_checked_mechanically_and_reviewed_as_same_text':True,'protected02822_necessary_semantics_read_with_root_authorization':True,'not_based_only_on_redacted_projection':True},
 'cases':reviews,'original_stageA_not_edited':True,'preoutput_expectations_unchanged':True,'private_expectations_not_supplied_to_author':True,
 'recommendation':'No confirmed StageA semantic error found. Root may independently admit StageB by a separate semantic gate and bounded authorization. This report does not launch B or constitute the root gate.',
 'stageA_seal_sha256':sha(seal_path),'stageA_output_sha256':sha(ap),'input_sha256':sha(ip),'protected_exposure_addendum':bind(xp),
 'actual_technical_crosscheck':{'one_first_valid_attempt':True,'unique_completed_agent_event_full_JSON_equals_raw_equals_sealed_copy':True,'zero_tools':True,'literal_and_all_inventory_path_validator_errors':[],'technical_checks_do_not_establish_semantics_by_themselves':True},
 'source_bindings':[bind(p)for p in [ip,ep,ap,attempt/'raw_output.json',attempt/'events.jsonl',attempt/'run_metadata.json',RUN/'input_packet.json',RUN/'request.txt',RUN/'technical_summary.json',seal_path,CAND/'stageA_prompt.txt',CAND/'stageB_prompt.txt',CAND/'design_freeze.json',meta_path,xp,Path(__file__)] ]+expected['manual_bindings'],
 'real_CLI_invocations_by_this_reviewer':0,'real_model_calls_by_this_reviewer':0,'source_files_modified':False,
 'limits':['All11 examples are known, previously exposed development material, not external human validation.','StageA records have no five-dimensional final answers; this PASS says nothing yet about StageB correcting all six errors or preserving other labels.','Human A/B adjudicated originals remain fixed and were not read or used as full-vector gold here.','Other protected original texts were not opened.02822 is now explicitly read and cannot be called untouched by this reviewer.','Original08 FAIL and current full Rule39/LLM03 adoption remain unchanged; no automatic B or146/240/4924 run.']}
assert report['coverage']['current_propositions']==19 and report['coverage']['context_relation_records']==42 and report['coverage']['all_original_context_policy_text_leaves']==63
assert sha(ap)=='8f87de605448a7e4295d6deb166ae99b94a46437e1c954934c60432374625ef5'
assert sha(ep)=='4c4eae2b3c421ff9fd0fbc11a8d2b4b4d83e63a94d7630bb514fac8de402d1fe'
rp=HERE/'candidate09_stageA11_full_semantic_review_PRIVATE.json';save(rp,report)
print(json.dumps({'report':bind(rp),'exposure_addendum':bind(xp),'reviewed_rows':11,'propositions':19,'context_records':42,'original_context_paths':63,'confirmed_semantic_errors':0,'real_CLI_invocations_by_reviewer':0,'real_model_calls_by_reviewer':0},ensure_ascii=False))
