import copy,hashlib,json,pathlib,re,sys
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'code'))
import relations,dimensions,evidence
units={r['id']:r['semantic_unit'] for r in map(json.loads,(HERE.parents[1]/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl').open()) if r['id'] in ['RECODE25-01735','RECODE25-01745','RECODE25-00111']}
PILOT='bounded_pilot_research_service_scope';ASSESS='bounded_current_eligibility_assessment';NEST='bounded_nested_clinical_advantage_standard'
def run(u):
 v=relations.RelationView(u);d=dimensions.judge(v);evidence.validate_decisions(v.unit,d)
 return v,{k:x['value'] for k,x in d.items()}
def types(v):return [r['details'].get('relation_subtype') for r in v.traces()]
def variant(u,old,new):
 sha=u['source_ref']['sha256'];syn=hashlib.sha256(('SYNTHETIC_ONLY'+old+new).encode()).hexdigest()
 def walk(x):
  if isinstance(x,str):return x.replace(old,new).replace(sha,syn)
  if isinstance(x,list):return [walk(z) for z in x]
  if isinstance(x,dict):
   z={k:walk(y) for k,y in x.items()}
   if isinstance(z.get('text'),str):
    for key in ['text_sha256','text_utf8_sha256']:
     if key in z:z[key]=hashlib.sha256(z['text'].encode()).hexdigest()
   return z
  return x
 return walk(copy.deepcopy(u))
results=[]
def check(name,u,sub,want,expected=None):
 v,l=run(u);assert (sub in types(v))==want,(name,l,types(v),v.material_requests)
 if expected:
  for k,value in expected.items():assert l[k]==value,(name,l)
 results.append({'test':name,'labels':l,'relations':types(v),'requests':v.material_requests})
 return v,l
for key in ['RECODE25-01735','RECODE25-01745']:
 u=units[key];v,l=check('saved_'+key,u,PILOT,True,{'I':1,'F':0})
 d=next(r['details'] for r in v.traces() if r['details'].get('relation_subtype')==PILOT)
 assert d['excluded_from_pilot_support']==key.endswith('01745')
 assert '细胞和基因治疗产品、疫苗产品等除外' in d['innovation_object_quotes'][0]['text']
 x=copy.deepcopy(u);x['source_bundle']['explicit_or_primary_source_resources'][0]['snapshot_sha256']='f'*64
 check('wrong_version_'+key,x,PILOT,False,{'I':None})
 x=copy.deepcopy(u);x['structure']={'component_id':'A'}
 for c in x['contexts']:c.setdefault('structure',{})['component_id']='A'
 x['source_bundle']['explicit_or_primary_source_resources'][0]['source_texts'][0]['structure']={'component_id':'B'}
 check('raw_scope_other_component_'+key,x,PILOT,False,{'I':None})
 check('form_quotation_'+key,variant(u,u['text'],'系统栏目仅记录“'+u['text']+'”这一表述。'),PILOT,False)
 check('removed_innovation_scope_'+key,variant(u,'试点项目范围为1类创新药','试点项目范围为普通仿制药'),PILOT,False,{'I':None})
 check('removed_actual_service_'+key,variant(u,'经确认的试点项目，药审中心在受理临床试验申请后30个工作日内完成审评审批','经确认的试点项目，仅按普通程序登记'),PILOT,False,{'I':None})
u=units['RECODE25-01735']
check('service_not_established',variant(u,'且已建立','且尚未建立'),PILOT,False)
check('wrong_service_stage',variant(u,'申请前提供','申请后提供'),PILOT,False)
check('institution_experience_only',variant(u,u['text'],'试点机构曾牵头完成过至少3项创新药临床试验。'),PILOT,False)
u=units['RECODE25-01745']
check('other_pilot',variant(u,'项目不纳入试点','项目不纳入其他试点'),PILOT,False)
check('receipt_record_only',variant(u,u['text'],'登记5个工作日内是否收到项目确认书。'),PILOT,False)
check('past_list_status_only',variant(u,u['text'],'该临床试验项目已经不在试点名单中。'),PILOT,False)
u=units['RECODE25-00111']
check('actual_research_data_eligibility_assessment',u,ASSESS,True,{'S':1,'E':1,'I':1,'F':1})
check('same_condition_nested_complete',u,NEST,True,{'S':1,'E':1})
for name,old,new in [
 ('no_actual_discussion','探讨现有研究数据','记录相关字段名称'),
 ('negated_discussion','探讨现有研究数据','不谈现有研究数据'),
 ('no_initial_assessment','初步评估认为符合','仅将字段命名符合'),
 ('different_programme','对于初步评估认为符合优先审评审批纳入条件的','对于初步评估认为符合其他审评审批纳入条件的'),
]:
 assert len(old)==len(new)
 x=variant(u,old,new);v,l=check(name,x,ASSESS,False);assert NEST not in types(v)
# A nested explicit standard cannot be silently replaced by zero if incomplete.
leaf=next(c for c in u['contexts'] if c['kind']=='source_textleaf' and '（5）与目前无法替代' in c.get('text',''))
fifth=re.search(r'(?m)^（5）[^\n]+',leaf['text']).group()
x=variant(u,fifth,' '*len(fifth));check('missing_nested_fifth_condition',x,NEST,False,{'S':None,'E':None})
x=copy.deepcopy(u)
for c in x['contexts']:
 if c['context_id']==leaf['context_id']:c['source_ref']['sha256']='f'*64
check('nested_other_source',x,NEST,False,{'S':None,'E':None})
# Same-clause clerical adjunct: preserve the actual assessment, while its
# own form/denial qualification remains decisive.
def reflow_leaf_coordinates(x):
 offset=0
 for c in sorted([c for c in x['contexts'] if c['kind']=='source_textleaf'],key=lambda c:c['source_ref']['locator']['unicode_code_point_interval_half_open'][0]):
  end=offset+len(c['text']);c['source_ref']['locator']['unicode_code_point_interval_half_open']=[offset,end]
  pointer=x['derived_context_origins'][c['context_id']]['source_bundle_pointer']
  doc=x['source_bundle']['source_full_text_resources'][int(pointer.split('/')[2])]
  for field in ['locator','source_locator']:
   if field in doc:doc[field]['unicode_code_point_interval_half_open']=[offset,end]
  offset=end
 return x
ending='应当在会议纪要中予以明确'
for name,addition,want in [
 ('actual_assessment_plus_secretary','，秘书仅记录会议开始时间',True),
 ('actual_assessment_plus_recording_staff','，由会议记录员仅记录会议开始时间',True),
 ('assessment_itself_form_only','，本次评估仅记录会议开始时间',False),
 ('assessment_itself_not_performed','，本次评估不进行核验',False),
]:
 x=reflow_leaf_coordinates(variant(u,ending,ending+addition))
 v,l=check(name,x,ASSESS,want,{'S':1,'E':1,'I':1,'F':1} if want else None)
 assert (NEST in types(v))==want
for name,prefix in [('only_forward_whole_assessment','仅转发如下文字：'),('only_field_whole_assessment','系统字段仅记录如下文字：')]:
 x=variant(u,u['text'],prefix+u['text']);v,l=check(name,x,ASSESS,False);assert NEST not in types(v)
out={'scope':'finite development checks, not independent validation','passed':len(results),'tests':results,'relations_sha256':hashlib.sha256((HERE/'code/relations.py').read_bytes()).hexdigest()}
(HERE/'round5-pilot-assessment-tests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'passed':len(results),'sha':out['relations_sha256']},ensure_ascii=False))
