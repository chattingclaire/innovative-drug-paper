"""Finite source-backed rights mechanism tests; no reference answers read."""
import copy,hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent;ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE/'code'))
import relations,dimensions,evidence
SUB='bounded_data_protection_rights_consequence'
units={r['id']:r['semantic_unit'] for r in map(json.loads,open(ROOT/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl')) if r['id'] in {'RECODE25-'+s for s in ['01408','01412','01416','01383']}}
def run(u):
 v=relations.RelationView(u);a=dimensions.judge(v);evidence.validate_decisions(v.unit,a)
 return v,{d:x['value'] for d,x in a.items()}
def rights(v):return [x for x in v.traces() if x['details'].get('relation_subtype')==SUB]
# Change in-memory text consistently and assign a distinct synthetic source.
def transform(u,old,new):
 sha=u['source_ref']['sha256'];syn=hashlib.sha256(('SYNTHETIC_RIGHTS:'+old+new).encode()).hexdigest()
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
 out=walk(copy.deepcopy(u))
 for c in out['contexts']:
  o=out.get('derived_context_origins',{}).get(c['context_id'],{})
  if o.get('origin_inventory_view')=='text':o['origin_inventory_view_sha256']=hashlib.sha256(c.get('text','').encode()).hexdigest()
 return out
results=[]
for suffix,mode in [('01408','protection_application'),('01412','expiry_conditioned_market_permission'),('01416','termination_releases_market_permission')]:
 v,l=run(units['RECODE25-'+suffix]);r=rights(v);assert len(r)==1 and l['I']==1,(suffix,l)
 assert r[0]['details']['action_mode']==mode
 assert l['S']==l['E']==l['Ec']==l['F']==0
 assert r[0]['details']['research_technical_service_inferred'] is False
 results.append({'test':'saved_source','id':suffix,'labels':l,'relations':r})
for suffix,old,new in [('01408','应当在提交','必须在提交'),('01412','可以提交','可提出'),('01416','可以受理或者批准','允许受理或批准')]:
 v,l=run(transform(units['RECODE25-'+suffix],old,new));assert rights(v) and l['I']==1,(suffix,l)
 results.append({'test':'synonym','synthetic_only':True,'based_on':suffix,'replacement':[old,new],'labels':l})
base=units['RECODE25-01408']
for name,text in [
 ('list','第九条 公布已经获得药品数据保护的品种名单，更新网站专栏。'),
 ('consultation','第九条 对药品数据保护相关问题存在疑问的，可以申请电话沟通交流。'),
 ('form','第九条 申请人拟申请数据保护的，应当在提交药品上市许可申请时同时提出数据保护申请材料。'),
 ('quoted_field','第九条 申报系统新增“申请人拟申请数据保护的，应当在提交药品上市许可申请时同时提出数据保护申请”栏目。'),
 ('wording_consultation','第九条 对“申请人拟申请数据保护的，应当在提交药品上市许可申请时同时提出数据保护申请”这一表述，企业可以咨询其标点格式。'),
 ('noninnovation_protected_data','第九条 申请人拟申请数据保护的，应当在提交药品上市许可申请时同时提出数据保护申请，本条仅涉及非创新药的受保护数据。'),
 ('independent_data_only','第九条 申请人拟申请数据保护的，应当在提交药品上市许可申请时同时提出数据保护申请，本条仅适用于自行取得且未依赖他人受保护数据。'),
 ('ordinary_confidentiality','第九条 网络平台应当保障药品生产企业提交的账号和个人信息数据保密。'),
]:
 v,l=run(transform(base,base['text'],text));assert not rights(v) and l['I']==0,(name,l)
 results.append({'test':name,'synthetic_only':True,'labels':l})
for suffix,old,new in [('01412','可以提交','不可以提交'),('01416','可以受理','不可以受理')]:
 v,l=run(transform(units['RECODE25-'+suffix],old,new));assert not rights(v) and l['I']==0,(suffix,l)
 results.append({'test':'negated_permission_not_positive_permission','synthetic_only':True,'id':suffix,'labels':l})
# Strong article identities need both complete definition/exception and a
# supplied entitlement branch. Missing required material remains I=NULL.
for name,select in [('missing_permission_exception',lambda c:'在数据保护期内，其他申请人未经药品上市许可持有人' in c.get('text','')),
                    ('missing_innovation_entitlement',lambda c:c.get('text','').startswith('第五条'))]:
 u=copy.deepcopy(base);u['contexts']=[c for c in u['contexts'] if not select(c)]
 v,l=run(u);assert not rights(v) and l['I'] is None,(name,l)
 results.append({'test':name,'synthetic_only':True,'labels':l,'requests':v.material_requests})
u=copy.deepcopy(base)
for c in u['contexts']:
 if c['kind']=='source_resource_text':c['source_ref']['sha256']='f'*64
v,l=run(u);assert not rights(v) and l['I'] is None
results.append({'test':'wrong_source_definition','synthetic_only':True,'labels':l})
u=copy.deepcopy(base);u['structure']={'component_id':'CURRENT'}
for c in u['contexts']:c.setdefault('structure',{})['component_id']='OTHER' if c['kind']=='source_resource_text' else 'CURRENT'
v,l=run(u);assert not rights(v) and l['I']!=1
results.append({'test':'same_sha_different_component','synthetic_only':True,'labels':l})
u=copy.deepcopy(base);u['structure']={'component_id':'CURRENT'}
for c in u['contexts']:
 if c['kind']=='paragraph':c.setdefault('structure',{})['component_id']='OTHER'
v,l=run(u);assert not rights(v) and l['I']!=1
results.append({'test':'current_paragraph_component_conflict','synthetic_only':True,'labels':l})
u=transform(base,'自创新药首次境内上市许可之日起','自非创新药首次境内上市许可之日起')
v,l=run(u);assert not rights(v) and l['I']==0
results.append({'test':'noninnovation_entitlement_not_positive_innovation','synthetic_only':True,'labels':l})
# An unrelated unavailable article is not a necessary dependency.
u=copy.deepcopy(base);u['source_bundle']['explicit_or_primary_source_resources'][0]['ordered_article_groups'].append({'article':'第九十九条','ordered_source_resource_ids':['UNRELATED-MISSING']})
v,l=run(u);assert rights(v) and l['I']==1 and not v.material_requests
results.append({'test':'unrelated_missing_article_does_not_block','synthetic_only':True,'labels':l})
v,l=run(units['RECODE25-01383']);assert not rights(v)
results.append({'test':'announcement_abbreviation_not_resolved_by_same_sha_alone','id':'01383','labels':l})
out={'scope':'finite implementation tests; no new independent validation','passed':len(results),'tests':results,'relations_sha256':hashlib.sha256((HERE/'code/relations.py').read_bytes()).hexdigest()}
(HERE/'round3-rights-tests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps({'passed':len(results),'relations_sha256':out['relations_sha256']},ensure_ascii=False))
