"""Bounded list/parent/trial tests on saved sources and explicit synthetic controls."""
import copy,hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'code'))
import relations,dimensions,evidence
units={r['id']:r['semantic_unit'] for r in map(json.loads,open(ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl')) if r['id'] in {'RECODE25-'+s for s in ['04377','04589','04614','01456']}}
REVIEW='bounded_operative_review_checklist';TRIAL='bounded_trial_admission_support'
def run(u):
 v=relations.RelationView(u);d=dimensions.judge(v);evidence.validate_decisions(v.unit,d)
 return v,{k:x['value'] for k,x in d.items()}
def subtype(v,name):return [r for r in v.traces() if r['details'].get('relation_subtype')==name]
def transform(u,old,new):
 sha=u['source_ref']['sha256'];syn=hashlib.sha256(('SYNTHETIC_ROUND4:'+old+new).encode()).hexdigest()
 def walk(x):
  if isinstance(x,str):return x.replace(old,new).replace(sha,syn)
  if isinstance(x,list):return [walk(y) for y in x]
  if isinstance(x,dict):
   z={k:walk(y) for k,y in x.items()}
   if isinstance(z.get('text'),str):
    for key in ['text_sha256','text_utf8_sha256']:
     if key in z:z[key]=hashlib.sha256(z['text'].encode()).hexdigest()
   return z
  return x
 return walk(copy.deepcopy(u))
results=[]
for suffix in ['04377','04589','04614','01456']:
 v,l=run(units['RECODE25-'+suffix])
 if suffix=='04377':assert l==dict(S=1,E=0,Ec=0,I=0,F=0) and len(subtype(v,REVIEW))==1
 elif suffix in ['04589','04614']:assert l['I'] is None and l['F'] is None
 else:assert len(subtype(v,TRIAL))==1 and l['I']==l['F']==1
 results.append({'test':'saved_source','id':suffix,'labels':l,'relations':v.traces(),'requests':v.material_requests})
base=units['RECODE25-04377']
for name,old,new in [('audit_synonym','应当审核','必须核验')]:
 v,l=run(transform(base,old,new));assert l['S']==1 and len(subtype(v,REVIEW))==1
 results.append({'test':name,'synthetic_only':True,'labels':l})
for name,text in [('pure_heading','(二)中药饮片处方，以下为审核项目目录：'),('quoted_form_label','申报系统新增“中药饮片处方，应当审核以下项目”栏目：')]:
 v,l=run(transform(base,base['text'],text));assert not subtype(v,REVIEW) and l['S']==0
 results.append({'test':name,'synthetic_only':True,'labels':l})
for name,change in [('audit_missing_member','remove'),('audit_cross_source','source'),('audit_cross_component','component'),('audit_duplicate_numbered_item','duplicate')]:
 u=copy.deepcopy(base)
 if change=='remove':u['contexts']=[c for c in u['contexts'] if c.get('structure',{}).get('paragraph_id')!='p0053']
 elif change=='source':
  for c in u['contexts']:
   if c.get('structure',{}).get('paragraph_id')=='p0053':c['source_ref']['sha256']='f'*64
 elif change=='component':
  u['structure']={'component_id':'CURRENT'}
  for c in u['contexts']:c.setdefault('structure',{})['component_id']='OTHER' if c['kind']=='ordered_members' else 'CURRENT'
 else:
  for c in u['contexts']:
   if c['kind']=='ordered_list':
    for g in c['structure']['child_groups']:
     if g['position']=='contexts':g['ordered_context_ids'][-1]=g['ordered_context_ids'][-2]
 v,l=run(u);assert not subtype(v,REVIEW) and l['S'] is None,(name,l)
 results.append({'test':name,'synthetic_only':True,'labels':l,'requests':v.material_requests})
# Original input has two container aliases for the same physical checklist.
# It remains one relation, not two independent supporting lists.
v,l=run(base);assert len(subtype(v,REVIEW))==1
results.append({'test':'same_physical_list_aliases_deduplicated','labels':l,'relation_count':1})
base=units['RECODE25-01456']
for name,old,new in [('admission_synonym','最终将纳入','即纳入')]:
 v,l=run(transform(base,old,new));assert subtype(v,TRIAL)
 results.append({'test':name,'synthetic_only':True,'labels':l})
for name,old,new in [('already_admitted_status','最终将纳入','已经被纳入'),('proposed_only','最终将纳入','拟考虑纳入')]:
 v,l=run(transform(base,old,new));assert not subtype(v,TRIAL) and l['I']==l['F']==0,(name,l)
 results.append({'test':name,'synthetic_only':True,'labels':l})
for name,text in [('publication_only','药审中心将公示拟纳入“关爱计划-延伸”试点工作的品种，公示期为5日。'),('quoted_trial_field','系统栏目记载“公示无异议的品种最终将纳入“关爱计划-延伸”试点工作”这一表述。')]:
 v,l=run(transform(base,base['text'],text));assert not subtype(v,TRIAL) and l['I']==l['F']==0,(name,l)
 results.append({'test':name,'synthetic_only':True,'labels':l})
for name,predicate in [
 ('missing_concrete_support',lambda c:'项目的核心内容' in c.get('text','')),
 ('missing_complete_OR',lambda c:'首创新药（First-In-Class' in c.get('text','')),
 ('missing_early_stage_exception',lambda c:'尚未推进至关键研究阶段' in c.get('text','')),
 ('missing_eligibility_end_boundary',lambda c:c.get('text')=='1.2 纳入标准'),
]:
 u=copy.deepcopy(base);u['contexts']=[c for c in u['contexts'] if not predicate(c)]
 v,l=run(u);assert not subtype(v,TRIAL) and l['I'] is None and l['F'] is None,(name,l)
 results.append({'test':name,'synthetic_only':True,'labels':l})
for name,kind in [('trial_cross_source','source'),('trial_cross_component','component')]:
 u=copy.deepcopy(base)
 if kind=='source':u['source_bundle']['source_full_text_resources'][0]['source_pdf_sha256']='f'*64
 else:
  u['structure']={'component_id':'CURRENT'}
  for c in u['contexts']:c.setdefault('structure',{})['component_id']='OTHER' if c['kind']=='source_resource_text' else 'CURRENT'
 v,l=run(u);assert not subtype(v,TRIAL) and l['I'] is None and l['F'] is None,(name,l)
 results.append({'test':name,'synthetic_only':True,'labels':l})
# Duplicating the same OR quote cannot replace an absent early-stage condition.
u=copy.deepcopy(base);u['contexts']=[c for c in u['contexts'] if '尚未推进至关键研究阶段' not in c.get('text','')]
orquote=next(c for c in u['contexts'] if '首创新药（First-In-Class' in c.get('text',''));extra=copy.deepcopy(orquote);extra['context_id']='SYNTHETIC-DUPLICATE-OR';u['contexts'].append(extra)
u['derived_context_origins'][extra['context_id']]=copy.deepcopy(u['derived_context_origins'][orquote['context_id']])
v,l=run(u);assert not subtype(v,TRIAL) and l['I'] is None and l['F'] is None
results.append({'test':'duplicate_OR_cannot_fill_missing_condition','synthetic_only':True,'labels':l})
# Unrelated illustrative material is not a necessary dependency for admission.
u=copy.deepcopy(base);u['contexts']=[c for c in u['contexts'] if c.get('text')!='单臂、单次给药']
v,l=run(u);assert subtype(v,TRIAL)
results.append({'test':'unrelated_example_missing_does_not_block','synthetic_only':True,'labels':l})
for name,old,new in [
 ('postadmission_service_explicitly_denied','便于在整个开发过程中及时高效地与药审中心开展沟通交流','不得在整个开发过程中及时高效地与药审中心开展沟通交流'),
 ('innovation_scope_explicitly_excluded','因此申请“关爱计划-延伸”试点工作的品种，需同时满足以下条件：','本试点不适用于创新药，因此申请“关爱计划-延伸”试点工作的品种，需同时满足以下条件：'),
]:
 u=transform(base,old,new);v,l=run(u);assert not subtype(v,TRIAL) and l['I'] is None and l['F'] is None,(name,l)
 results.append({'test':name,'synthetic_only':True,'labels':l})
# Independent review blockers: local/raw identities, actual operation,
# effective OR branch, and the continued service's same-product anaphor.
u=copy.deepcopy(units['RECODE25-04377']);u['source_ref']['sha256']='f'*64
v,l=run(u);assert not subtype(v,REVIEW) and l['S'] is None
results.append({'test':'review_unit_source_mismatch','synthetic_only':True,'labels':l})
u=copy.deepcopy(base);u.setdefault('structure',{})['component_id']='A'
for c in u['contexts']:c.setdefault('structure',{})['component_id']='A'
doc=u['source_bundle']['source_full_text_resources'][0];doc['structure']={'component_id':'A'}
for p in doc['paragraphs']:p['structure']={'component_id':'B'}
v,l=run(u);assert not subtype(v,TRIAL) and l['I'] is None and l['F'] is None
results.append({'test':'trial_raw_component_mismatch','synthetic_only':True,'labels':l})
for replacement in ['不一定最终将纳入','不应予以纳入','可能最终将纳入']:
 v,l=run(transform(base,'最终将纳入',replacement));assert not subtype(v,TRIAL) and l['I']==l['F']==0
 results.append({'test':'nonoperative_admission_'+replacement,'synthetic_only':True,'labels':l})
u=transform(base,'或②在境内尚无药物获批拟开发的罕见疾病适应症；','或②在境内尚无药物获批拟开发的罕见疾病适应症（此分支不在本试点纳入范围）；')
v,l=run(u);rs=subtype(v,TRIAL);assert len(rs)==1 and l['I']==1 and l['F']==0
assert len(rs[0]['details']['excluded_eligibility_branches'])==1 and not rs[0]['details']['need_eligible_branches']
assert any('此分支不在本试点纳入范围' in q['text'] for q in rs[0]['details']['eligibility_quotes'])
results.append({'test':'excluded_need_branch_preserves_full_OR_without_F','synthetic_only':True,'labels':l})
u=transform(base,'实施框架将成为该品种罕见疾病适应症的临床研发档案','其他试点品种的实施框架将成为其他品种罕见疾病适应症的临床研发档案')
v,l=run(u);assert not subtype(v,TRIAL) and l['I'] is None and l['F'] is None
results.append({'test':'continuing_service_different_product','synthetic_only':True,'labels':l})
out={'scope':'finite implementation replays; not new independent validation','passed':len(results),'tests':results,'relations_sha256':hashlib.sha256((HERE/'code/relations.py').read_bytes()).hexdigest()}
(HERE/'round4-relations-tests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'passed':len(results),'labels':[(r.get('id'),r['labels']) for r in results if r['test']=='saved_source'],'relations_sha256':out['relations_sha256']},ensure_ascii=False))
