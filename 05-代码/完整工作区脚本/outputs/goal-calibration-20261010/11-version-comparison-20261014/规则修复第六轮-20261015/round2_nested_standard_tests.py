"""Exact-reference chain tests, separate from validation/accuracy estimates."""
import copy,hashlib,json,pathlib,re,runpy,sys
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
shared=runpy.run_path(str(HERE/'round2_relations_tests.py'))
units,run,types,variant=(shared[k] for k in ('units','run','types','variant'))
import relations,dimensions,evidence
SUB='bounded_nested_clinical_advantage_standard'
results=[]
for suffix in ['00113','00123','00141']:
 v,l=run(units['RECODE25-'+suffix]);assert SUB in types(v)
 assert l['S']==l['E']==1,(suffix,l)
 tr=next(r for r in v.traces() if r['details'].get('relation_subtype')==SUB)
 assert tr['details']['complete_member_numbers']==['1','2','3','4','5']
 results.append({'test':'same_explicit_standard_uniformly_applied','id':suffix,'labels':l,'trace':tr})

u0=units['RECODE25-00123']
# Construct in-memory source variants; character length and the complete
# source span stay valid, while altered definition content gets a new SHA.
def alter_context(unit,old,new):
 assert len(old)==len(new)
 assert any(old in c.get('text','') for c in unit['contexts'])
 sha=unit['source_ref']['sha256'];testsha=hashlib.sha256(('SYNTHETIC_NESTED_TEST'+old+new).encode()).hexdigest()
 def walk(x):
  if isinstance(x,str):return x.replace(old,new).replace(sha,testsha)
  if isinstance(x,list):return [walk(y) for y in x]
  if isinstance(x,dict):
   z={k:walk(y) for k,y in x.items()}
   if isinstance(z.get('text'),str):
    for key in ['text_sha256','text_utf8_sha256']:
     if key in z:z[key]=hashlib.sha256(z['text'].encode()).hexdigest()
   return z
  return x
 out=walk(copy.deepcopy(unit))
 for c in out['contexts']:
  o=out.get('derived_context_origins',{}).get(c['context_id'],{})
  if o.get('origin_inventory_view')=='text':o['origin_inventory_view_sha256']=hashlib.sha256(c.get('text','').encode()).hexdigest()
 return out
first=next(c for c in u0['contexts'] if c['kind']=='source_textleaf' and '（5）与目前无法替代' in c.get('text',''))
fifth=re.search(r'(?m)^（5）[^\n]+',first['text']).group()
third=re.search(r'(?m)^（3）与现有[^\n]+',first['text']).group()
for name,old,new in [
 ('missing_fifth_alternative',fifth,' '*len(fifth)),
 ('missing_middle_alternative',third,' '*len(third)),
 ('incomplete_group_operator','具体包括以下任一情形','仅列部分相关参考情形'),
 ('wrong_edition_title','突破性治疗药物审评工作程序（试行）\n为鼓励','突破性治疗药物审评工作程序（新版）\n为鼓励'),
]:
 v,l=run(alter_context(u0,old,new))
 assert SUB not in types(v),(name,types(v))
 assert l['S'] is None and l['E'] is None,(name,l)
 assert any(r.get('affected_dimensions')==['S','E'] for r in v.material_requests),(name,v.material_requests)
 results.append({'test':name,'synthetic_only':True,'labels':l,'requests':v.material_requests})

# A definition supplied under a different source SHA cannot satisfy the
# same-edition reference, even if its text is otherwise identical.
u=copy.deepcopy(u0)
for c in u['contexts']:
 if c['context_id']==first['context_id']:c['source_ref']['sha256']='1'*64
v,l=run(u);assert SUB not in types(v);assert l['S'] is None and l['E'] is None
results.append({'test':'target_definition_different_source_sha','synthetic_only':True,'labels':l,'requests':v.material_requests})

# No operative condition means no reference expansion. A paperwork branch
# does not inherit a parallel, removed substantive eligibility branch.
v,l=run(variant(u0,'不符合纳入条件','未提交申报材料'))
assert SUB not in types(v);assert l['S']==l['E']==0
results.append({'test':'no_operative_condition_paperwork_only','synthetic_only':True,'labels':l})

# Same bounded programme admission/service can use directly given benefits,
# but does not thereby consume all substantive admission standards.
for suffix in ['00120','00127','00134']:
 v,l=run(units['RECODE25-'+suffix]);assert SUB not in types(v);assert l['S']==l['E']==0
 results.append({'test':'service_or_admission_without_standard_review','id':suffix,'labels':l})

# Independent reviewer counterexample: application is not admission. The
# entire unsupported second-round inspection inheritance path was removed.
suffix='00129';u=units['RECODE25-'+suffix]
v,l=run(u);assert 'bounded_current_priority_resource' not in types(v);assert l['I']==l['F']==0
results.append({'test':'application_does_not_prove_admission','id':suffix,'labels':l})
old='申请人未在药品注册申请受理前提出药品注册检验的'
new='尚未纳入的申请只按普通流程核查而不享受优先待遇'
v,l=run(variant(u,old,new));assert 'bounded_current_priority_resource' not in types(v);assert l['I']==l['F']==0
results.append({'test':'explicit_nonadmission_and_no_priority','synthetic_only':True,'labels':l})

out={'scope':'finite same-standard reference and object-scope tests; no human labels read or rewritten',
 'tests':results,'passed':len(results),'relations_sha256':hashlib.sha256((HERE/'code/relations.py').read_bytes()).hexdigest()}
(HERE/'round2-nested-standard-tests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'nested_tests_passed':len(results),'relations_sha256':out['relations_sha256']},ensure_ascii=False))
