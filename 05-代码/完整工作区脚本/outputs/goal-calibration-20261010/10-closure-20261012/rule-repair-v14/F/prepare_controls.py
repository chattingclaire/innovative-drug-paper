from pathlib import Path
import copy, datetime, hashlib, json, shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
VERS=ROOT/'06-coding/rule-five-dimension-joint-root/versions'
BASE=VERS/'joint-v13b-clinical-safety-role-root'
CAND=VERS/'joint-v14f-form-gap-root'
def bind(p):
 b=p.read_bytes();return {'path':str(p.resolve()),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(n,d):
 with (HERE/n).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
assert not CAND.exists()
shutil.copytree(BASE,CAND,ignore=shutil.ignore_patterns('__pycache__'))
current='(2)对于该药的新剂型，应当满足以下条件：现有上市剂型均不适用于儿童人群，新剂型属于儿童人群适宜剂型。'
parents=['申请适用优先审评审批程序的，应同时满足（一）（二）：','（二）符合优先审评审批范围的药品上市许可申请，以下列出的适用范围应满足相关条件：','3.符合儿童生理特征的儿童用药品新品种、剂型和规格。']
def unit(text,mode=None,sibling=None):
 ps=parents[:]
 if mode=='ordinary_parent':ps[0]='申请普通药品材料递交的，应同时满足（一）（二）：';ps[1]='（二）普通药品材料应满足相关条件：'
 before=['优先审评审批工作程序','一、适用范围','符合儿童生理特征的儿童用药品剂型，按以下条件申请适用本程序。','二、适用条件',ps[0],'（一）满足药品注册申报条件。',ps[1],ps[2]]
 if sibling:before.append(sibling)
 raw='\n'.join(before+[text,'三、工作要求','按本程序受理申请。'])
 sha=hashlib.sha256(raw.encode()).hexdigest()
 ref={'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'paragraph_id':'current','component_id':'main'}}
 cs=[{'context_id':'current','kind':'paragraph','text':text,'source_ref':copy.deepcopy(ref),'structure':{'paragraph_id':'current','component_id':'main'}}]
 for i,t in enumerate(ps):
  pr={'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'paragraph_id':'parent'+str(i),'component_id':'main','target_paragraph_id':'current'}}
  cs.append({'context_id':'parent'+str(i),'kind':'parent_paragraph','text':t,'source_ref':pr,'structure':{'sequence_index':i,'paragraph_id':'parent'+str(i),'component_id':'main','target_paragraph_id':'current'}})
 leaf={'context_id':'leaf','kind':'source_textleaf','text':raw,'source_ref':{'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'unicode_code_point_interval_half_open':[0,len(raw)]}},'structure':{}}
 cs.append(leaf)
 if sibling:cs.append({'context_id':'sibling','kind':'preceding_paragraph','text':sibling,'source_ref':{'sha256':sha,'source_resource_id':'SOURCE-'+sha,'locator':{'paragraph_id':'sibling','component_id':'main'}},'structure':{'paragraph_id':'sibling','component_id':'main'}})
 if mode=='no_parent':cs=[c for c in cs if c['kind']!='parent_paragraph']
 if mode=='no_literal':cs=[c for c in cs if c['kind']!='source_textleaf']
 if mode=='foreign_literal':leaf['source_ref']['sha256']='b'*64
 if mode=='incomplete_literal':leaf['source_ref']['locator']['unicode_code_point_interval_half_open']=[7,len(raw)+7]
 if mode in ('foreign_parent','wrong_component','wrong_target','conflicting_target','conflicting_component'):
  for c in cs:
   if c['kind']!='parent_paragraph':continue
   if mode=='foreign_parent':c['source_ref']['sha256']='b'*64
   if mode=='wrong_component':c['structure']['component_id']=c['source_ref']['locator']['component_id']='appendix'
   if mode=='wrong_target':c['structure']['target_paragraph_id']=c['source_ref']['locator']['target_paragraph_id']='other-current'
   if mode=='conflicting_target':c['structure']['target_paragraph_id']='other-current'
   if mode=='conflicting_component':c['source_ref']['locator']['component_id']='appendix'
 return {'text':text,'source_ref':ref,'contexts':cs}
cases=[]
def add(name,text,expected,reason,mode=None,sibling=None):
 cases.append({'name':name,'semantic_input':unit(text,mode,sibling),'expected':{'F':expected},'hard_assertion':True,'synthetic':True,'semantic_reason':reason})
add('all_existing_forms_unsuitable_priority_qualification',current,1,'当前明确全部现有剂型均不适用儿童，新适宜剂型通过真实优先申请直接父链承接按需机会。')
add('all_existing_forms_unsuitable_wording_variant','(2)对于该药新剂型，全部现有上市剂型均不适合儿童使用，而新剂型适用于儿童。',1,'全部现有剂型不适合儿童与同一药的新适宜剂型具有同一关系，不依赖唯一逐字句型。')
add('some_existing_form_remains_suitable','(2)对于该药新剂型，现有上市剂型中仍有适用于儿童的剂型，新剂型更便于服用。',0,'仍有适宜剂型，便利不能冒充全部现有剂型不适用的获取缺口。')
add('mere_convenience','(2)对于该药新剂型，现有剂型服用较为不便，新剂型更便于儿童服用。',0,'仅给药便利是既有明确排除。')
add('population_and_form_names_only','(2)儿童药品新剂型可以按要求提交材料。',0,'儿童、药品、剂型名称并不证明获取缺口。')
add('only_some_forms_unsuitable','(2)对于该药新剂型，部分现有上市剂型不适用于儿童，新剂型适用于儿童。',0,'部分不适用不足以证明当前所需药品缺少儿童适宜剂型。')
add('universal_gap_explicitly_denied','(2)对于该药新剂型，并非现有上市剂型均不适用于儿童人群，新剂型属于儿童人群适宜剂型。',0,'显式否定全部不适用，不可删掉否定词。')
add('gap_condition_not_required','(2)对于该药新剂型，不要求现有上市剂型均不适用于儿童人群，新剂型属于儿童人群适宜剂型。',0,'被否定的缺口条件不构成按该缺口分配资格。')
add('new_form_also_unsuitable','(2)对于该药新剂型，现有上市剂型均不适用于儿童人群，新剂型也不适用于儿童。',0,'新剂型同样不适用，未建立对缺口的适当安排。')
add('other_drug_new_form','(2)对于该药新剂型，现有上市剂型均不适用于儿童人群，另一药品的新剂型属于儿童人群适宜剂型。',0,'另一药品的适宜剂型不能连接当前同一所需药品的缺口。')
add('quoted_form_field_only','(2)应填写“现有上市剂型均不适用于儿童人群，新剂型属于儿童人群适宜剂型”字段，只要求该字段非空。',0,'仅字段名称与非空格式。')
for mode in ('no_parent','ordinary_parent','foreign_parent','wrong_component','wrong_target','conflicting_target','conflicting_component','no_literal','foreign_literal','incomplete_literal'):
 add(mode,current,0,'缺口文字不替代真实同源同组件、正确目标、完整同版原件中成立的优先申请直接父链。',mode=mode)
add('sibling_gap_not_donated','(2)对于该药新剂型，应当适宜儿童使用。',0,'缺口仅属于新品种兄弟分支，当前剂型成员不得借用。',sibling='(1)对于新品种，目前无有效治疗药物或治疗手段的，可按规定申请。')
add('form_gap_sibling_not_donated','(2)对于该药新剂型，应提交剂型名称。',0,'兄弟剂型缺口不能捐给当前纯名称成员。',sibling='(1)另一药品的现有上市剂型均不适用于儿童人群，新剂型属于儿童人群适宜剂型。')
p=ROOT/'06-coding/full4481-common-v15-production-preparation-sol/packets/RECODE25-00104.json'
manifest=ROOT/'01-review/source-interface-v16-article6-addendum-sol/packet-bindings-v16.json'
mb=next(x for x in json.loads(manifest.read_text()) if x['source_id']=='RECODE25-00104')
assert all(bind(p)[k]==mb[k] for k in ('path','bytes','sha256'))
real={'name':'current-v16-RECODE25-00104/F','packet_binding':bind(p),'expected':{'F':1},'hard_assertion':True,'semantic_reason':'同一药品全部现有上市剂型不适用于儿童且新剂型适宜，通过 p0087→p0089→p0093 真实父链取得优先申请资格；保留缺口类别，不改称无有效治疗/境内无批准/断供。','review_status':'已曝光研发诊断；AI 初评+真人复核，不是独立金标'}
save('form-gap-controls-fixed-before-edit.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'manual_basis':{'path':str(ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt'),'lines':[147,173],'interpretation':'广义所需药品保障缺口＋针对性优先/申请机会；纯人群名称、便利、普通申报排除。新剂型适用缺口独立于既有三类缺口。'},'real_cases':[real],'cases':cases,'case_N':len(cases)+1,'expected_frozen_before_algorithm_edit':True,'keep_all_failed_results':True})
save('preparation.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'baseline':str(BASE),'candidate':str(CAND),'base_files':[bind(BASE/(n+'.py')) for n in ('evidence','source_packet','source_receipts','relations','dimensions')],'manual':bind(ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt'),'current_packet_manifest':bind(manifest),'real_packet':bind(p),'controls':bind(HERE/'form-gap-controls-fixed-before-edit.json'),'mutable_dimension':'F','protected_full_decisions':['S','E','Ec','I'],'allowed_algorithm_file':'relations.py','immutable_modules':['evidence.py','source_packet.py','source_receipts.py','dimensions.py'],'source_state_must_remain_equal':['material_requests','source_requests','source_view_events','v11_protected_data_requests'],'no_global_GAPS_or_shared_definition_changes':True,'overall_execution':False,'adoption':False})
print('prepared',len(cases)+1)
