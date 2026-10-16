"""Finite synthetic controls; original human labels and source files are untouched."""
import copy,hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'code'))
import relations,dimensions,evidence
units=json.loads((HERE/'semantic-overrides.json').read_text())
TYPE='bounded_statutory_postadmission_support'
def run(u):
 v=relations.RelationView(u);d=dimensions.judge(v);evidence.validate_decisions(v.unit,d)
 return v,{k:x['value'] for k,x in d.items()}
def rels(v):return [r for r in v.traces() if r['details'].get('relation_subtype')==TYPE]
def transform(u,old,new):
 leaf=next(c for c in u['contexts'] if c['kind']=='source_textleaf');sha=u['source_ref']['sha256'];text=leaf['text'].replace(old,new);syn=hashlib.sha256(text.encode()).hexdigest()
 def walk(x):
  if isinstance(x,str):return x.replace(old,new).replace(sha,syn)
  if isinstance(x,list):return [walk(z) for z in x]
  if isinstance(x,dict):
   z={k:walk(y) for k,y in x.items()}
   if isinstance(z.get('text'),str):
    for key in ['text_sha256','text_utf8_sha256']:
     if key in z:z[key]=hashlib.sha256(z['text'].encode()).hexdigest()
    if z.get('kind') in {'source_textleaf','verbatim_UTF8_snapshot_text'}:
     for loc in [z.get('locator',{}),z.get('source_locator',{}),z.get('source_ref',{}).get('locator',{})]:
      if 'unicode_code_point_interval_half_open' in loc:loc['unicode_code_point_interval_half_open']=[0,len(z['text'])]
   return z
  return x
 return walk(copy.deepcopy(u))
results=[]
def check(name,u,want_relation,want_label=None):
 v,l=run(u);rs=rels(v);assert bool(rs)==want_relation,(name,l,v.material_requests)
 if want_label:
  for k,value in want_label.items():assert l[k]==value,(name,l,v.material_requests)
 results.append({'test':name,'labels':l,'relation_count':len(rs),'requests':v.material_requests})
 return rs
for key,u in units.items():
 rs=check('saved_full_source_'+key,u,True)
 d=rs[0]['details'];assert d['innovation_eligible_branches'] and d['need_eligible_branches']
 if key.endswith('04614'):
  scope=''.join(q['text'] for q in d['complete_eligibility_quotes'])
  assert all(x in scope for x in ['（一）','（二）','（三）','（四）','（五）','（六）'])
  assert '其他优先审评审批的情形' in scope and d['deadline_comparison_quotes']
 # Independently supplied current body cannot borrow another source's scope.
 x=copy.deepcopy(u);x['source_ref']['sha256']='f'*64
 check('current_source_mismatch_'+key,x,False,{'I':None,'F':None})
 # A complete leaf alone does not license a contradictory/incomplete article projection.
 x=copy.deepcopy(u);doc=x['source_bundle']['explicit_or_primary_source_resources'][0]
 group=next(g for g in doc['ordered_article_groups'] if g['article']==d['scope_binding']['eligibility_article'])
 group['ordered_source_resource_ids']=group['ordered_source_resource_ids'][:-1]
 check('missing_eligibility_member_'+key,x,False,{'I':None,'F':None})
 x=copy.deepcopy(u);doc=x['source_bundle']['explicit_or_primary_source_resources'][0]
 group=next(g for g in doc['ordered_article_groups'] if g['article']==d['scope_binding']['admission_article'])
 group['ordered_source_resource_ids']*=2
 check('duplicate_admission_member_'+key,x,False,{'I':None,'F':None})
 x=copy.deepcopy(u)
 for c in x['contexts']:
  if c['kind']=='source_textleaf':c['text']=c['text'][:-1]
 check('incomplete_literal_leaf_'+key,x,False,{'I':None,'F':None})
 x=copy.deepcopy(u);x['structure']={'component_id':'A'}
 for c in x['contexts']:c.setdefault('structure',{})['component_id']='A'
 x['source_bundle']['explicit_or_primary_source_resources'][0]['structure']={'component_id':'B'}
 check('other_component_qualification_'+key,x,False,{'I':None,'F':None})
 # Current quotation of an operation is not performance of the operation.
 x=transform(u,u['text'],'系统栏目记载“'+u['text']+'”这一表述。')
 check('form_only_current_'+key,x,False)
u=units['RECODE25-04589']
check('same_name_other_object',transform(u,'对纳入突破性治疗药物程序的药物临床试验','对纳入突破性治疗药物程序的兽药临床试验'),False)
check('admission_not_granted',transform(u,'符合条件的，药品审评中心按照程序公示后纳入突破性治疗药物程序','符合条件的，药品审评中心按照程序公示后不予纳入突破性治疗药物程序'),False,{'I':None,'F':None})
check('different_programme_section',transform(u,'第一节 突破性治疗药物程序','第一节 其他治疗药物程序'),False,{'I':None,'F':None})
u=units['RECODE25-04614']
x=copy.deepcopy(u);doc=x['source_bundle']['explicit_or_primary_source_resources'][0];doc['ordered_article_groups']=[g for g in doc['ordered_article_groups'] if g['article']!='第九十六条']
check('deadline_no_complete_comparison',x,False,{'I':None,'F':None})
check('same_deadline_for_ordinary_and_priority',transform(u,'药品上市许可申请审评时限为二百日','药品上市许可申请审评时限为一百三十日'),False,{'I':None,'F':None})
# Keep complete scope including the exclusion; no eligible needs branch can be
# fabricated from words in a branch expressly removed from this programme.
x=transform(u,'临床急需的短缺药品、防治重大传染病和罕见病等疾病的创新药和改良型新药；','临床急需的短缺药品、防治重大传染病和罕见病等疾病的创新药和改良型新药（本项不在本程序纳入范围）；')
x=transform(x,'疾病预防、控制急需的疫苗和创新疫苗；','疾病预防、控制急需的疫苗和创新疫苗（本项不在本程序纳入范围）；')
rs=check('all_need_innovation_branches_excluded',x,True)
assert not rs[0]['details']['need_eligible_branches'] and not rs[0]['details']['innovation_eligible_branches']
assert '不在本程序纳入范围' in ''.join(q['text'] for q in rs[0]['details']['complete_eligibility_quotes'])
u=units['RECODE25-04589']
for name,old,new in [
 ('qualification_other_object','药物临床试验期间，用于防治严重危及生命','兽药临床试验期间，用于防治严重危及生命'),
 ('nonaffirmative_admission_bridge','符合条件的，药品审评中心按照程序公示后纳入突破性治疗药物程序','不保证符合条件的，药品审评中心按照程序公示后纳入突破性治疗药物程序'),
 ('nonaffirmative_eligibility','申请人可以申请适用突破性治疗药物程序','申请人不可以申请适用突破性治疗药物程序'),
]:check(name,transform(u,old,new),False)
x=transform(u,'药品审评中心安排审评人员进行沟通交流','药品审评中心不安排审评人员进行沟通交流')
x=transform(x,'对下一步研究方案提出意见或者建议，并反馈给申请人','不对下一步研究方案提出意见或者建议，也不反馈给申请人')
rs=check('current_explicit_service_restriction_direction',x,True)
assert rs[0]['details']['direction']=='restricted' and rs[0]['details']['positive_delivery'] is False
assert len(rs[0]['details']['current_restriction_quotes'])==2
assert all('不' in q['text'] for q in rs[0]['details']['current_restriction_quotes'])
out={'scope':'development replays, not independent validation','passed':len(results),'tests':results,'relations_sha256':hashlib.sha256((HERE/'code/relations.py').read_bytes()).hexdigest()}
(HERE/'round5-relations-tests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'passed':len(results),'sha':out['relations_sha256']},ensure_ascii=False))
