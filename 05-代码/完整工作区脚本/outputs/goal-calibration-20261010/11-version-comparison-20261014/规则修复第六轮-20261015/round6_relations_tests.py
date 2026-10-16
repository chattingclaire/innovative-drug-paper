"""Finite original-input and synthetic binding controls; no original file edits."""
import copy,hashlib,json,pathlib,sys
sys.dont_write_bytecode=True
P=pathlib.Path(__file__).resolve().parent;sys.path.insert(0,str(P/'code'))
import relations,dimensions,evidence
units=json.loads((P/'semantic-overrides.json').read_text());PROTECT='bounded_annex_protection_application';RISK='bounded_current_risk_management_scope'
def run(u):
 v=relations.RelationView(u);d=dimensions.judge(v);evidence.validate_decisions(v.unit,d);return v,{k:q['value'] for k,q in d.items()}
def sub(v,t):return [r for r in v.traces() if r['details'].get('relation_subtype')==t]
def replace(x,old,new):
 if isinstance(x,str):return x.replace(old,new)
 if isinstance(x,list):return [replace(v,old,new) for v in x]
 if isinstance(x,dict):return {k:replace(v,old,new) for k,v in x.items()}
 return x
def transform(u,old,new):
 """Keep synthetic primary/raw HTML byte hashes and attachment spans coherent."""
 x=replace(copy.deepcopy(u),old,new);primary=u['source_ref']['sha256']
 oldleaves={c['source_ref']['sha256']:c for c in u['contexts'] if c['kind']=='source_textleaf'}
 # HTML changes must be sealed before JSON, which cites HTML bytes.
 ordered=sorted(oldleaves,key=lambda sha:sha==primary)
 for sha in ordered:
  before=oldleaves[sha];after=next(c for c in x['contexts'] if c['kind']=='source_textleaf' and c['source_ref']['sha256']==sha)
  syn=hashlib.sha256(after['text'].encode()).hexdigest();x=replace(x,sha,syn)
 def hashes(v):
  if isinstance(v,list):return [hashes(z) for z in v]
  if not isinstance(v,dict):return v
  z={k:hashes(y) for k,y in v.items()}
  if isinstance(z.get('text'),str):
   for key in ['text_sha256','text_utf8_sha256']:
    if key in z:z[key]=hashlib.sha256(z['text'].encode()).hexdigest()
   if z.get('kind') in ['source_textleaf','verbatim_UTF8_snapshot_text']:
    for loc in [z.get('locator',{}),z.get('source_locator',{}),z.get('source_ref',{}).get('locator',{})]:
     if 'unicode_code_point_interval_half_open' in loc:loc['unicode_code_point_interval_half_open']=[0,len(z['text'])]
  return z
 x=hashes(x)
 # Explicit attachment anchors are updated against the synthetic raw HTML;
 # other page/paragraph indices are unchanged by these no-newline variants.
 for di,doc in enumerate(x['source_bundle'].get('explicit_or_primary_source_resources',[])):
  olddoc=u['source_bundle']['explicit_or_primary_source_resources'][di]
  for i,t in enumerate(doc.get('source_texts',[])):
   loc=t.get('source_locator',{});oldloc=olddoc['source_texts'][i].get('source_locator',{})
   if 'raw_html_sha256' not in loc:continue
   oldsha=oldloc['raw_html_sha256'];orig=oldleaves[oldsha]['text'];html=next(c['text'] for c in x['contexts'] if c['kind']=='source_textleaf' and c['source_ref']['sha256']==loc['raw_html_sha256'])
   a,b=oldloc['unicode_character_interval_half_open'];piece=orig[a:b].replace(old,new);start=html.index(piece)
   loc['unicode_character_interval_half_open']=[start,start+len(piece)];loc['outer_html_sha256_utf8']=hashlib.sha256(piece.encode()).hexdigest()
 # Rebase exact original TXT offsets for length-changing mixed-clause probes.
 if primary in oldleaves and not oldleaves[primary]['text'].lstrip().startswith('{'):
  oldraw=oldleaves[primary]['text'];newraw=next(c['text'] for c in x['contexts'] if c['kind']=='source_textleaf' and c['source_ref']['sha256']==x['source_ref']['sha256'])
  def rebase(z):
   if isinstance(z,list):
    for v in z:rebase(v)
   elif isinstance(z,dict):
    span=z.get('unicode_code_point_interval_half_open')
    if span and z.get('snapshot_sha256')==x['source_ref']['sha256']:
     a,b=(0,len(newraw)) if span==[0,len(newraw)] else [len(oldraw[:n].replace(old,new)) for n in span]
     z['unicode_code_point_interval_half_open']=[a,b]
     if 'utf8_byte_interval_half_open' in z:z['utf8_byte_interval_half_open']=[len(newraw[:a].encode()),len(newraw[:b].encode())]
    for v in z.values():rebase(v)
  rebase(x)
  for d in x['source_bundle']['explicit_or_primary_source_resources']:
   for t in d.get('source_texts',[]):
    span=t.get('source_locator',{}).get('unicode_code_point_interval_half_open')
    if span:assert newraw[span[0]:span[1]]==t['text']
 return x
results=[]
def check(name,u,t,expected,labels=None):
 v,l=run(u);rs=sub(v,t);assert bool(rs)==expected,(name,l,v.material_requests)
 if labels:
  for k,z in labels.items():assert l[k]==z,(name,l)
 results.append({'test':name,'labels':l,'has_relation':bool(rs),'requests':v.material_requests});return v,l,rs
for key,t in [('RECODE25-01383',PROTECT),('RECODE25-04067',RISK)]:
 u=units[key];check('original_'+key,u,t,True)
 x=copy.deepcopy(u);x['source_ref']['sha256']='f'*64;check('unit_wrong_source_'+key,x,t,False)
 x=copy.deepcopy(u);x['text']='系统字段仅记载“'+x['text']+'”';check('current_form_'+key,x,t,False)
 x=copy.deepcopy(u);x['structure']={'component_id':'A'}
 for c in x['contexts']:c.setdefault('structure',{})['component_id']='A'
 di=1 if t==PROTECT else 0;x['source_bundle']['explicit_or_primary_source_resources'][di]['structure']={'component_id':'B'}
 check('resource_component_mismatch_'+key,x,t,False)
u=units['RECODE25-01383'];di=1
for name,mut in [
 ('missing_attachment_link',lambda d:d['attachment_connection_resource_ids'].pop()),
 ('missing_announcement_alias',lambda d:d['ordered_announcement_resource_ids'].pop(0)),
 ('missing_normative_clause',lambda d:d['ordered_normative_resource_ids'].pop(4)),
 ('missing_table',lambda d:d['original_tables'].pop()),
 ('missing_protection_exception',lambda d:next(g for g in d['ordered_article_groups'] if g['article']=='第三条')['ordered_source_resource_ids'].pop()),
]:
 x=copy.deepcopy(u);mut(x['source_bundle']['explicit_or_primary_source_resources'][di]);check(name,x,PROTECT,False,{'I':None})
x=copy.deepcopy(u)
for c in x['contexts']:
 if c['kind']=='source_textleaf' and c['source_ref']['sha256']!=u['source_ref']['sha256']:c['source_ref']['sha256']='b'*64
check('attachment_html_wrong_source',x,PROTECT,False,{'I':None})
x=copy.deepcopy(u);x['text']=x['text'].replace('《实施办法》','《其他办法》');check('same_source_wrong_abbreviation',x,PROTECT,False,{'I':None})
x=copy.deepcopy(u);x['text']=x['text'].replace('提出药品试验数据保护申请','提交药品试验数据保护申请表');check('application_form_only',x,PROTECT,False)
x=transform(u,'自创新药首次境内上市许可之日起','自非创新药首次境内上市许可之日起');check('noninnovation_entitlement',x,PROTECT,False)
u=units['RECODE25-04067'];doc=u['source_bundle']['explicit_or_primary_source_resources'][0]
for name,which in [('risk_missing_member','member'),('risk_missing_next_boundary','boundary'),('risk_scope_wrong_source','scope')]:
 x=copy.deepcopy(u);d=x['source_bundle']['explicit_or_primary_source_resources'][0];g=next(g for g in d['ordered_article_groups'] if g['article']=='第四十二条')
 if which=='member':g['ordered_source_resource_ids'].pop(4)
 elif which=='boundary':g['next_boundary_source_resource_id']='MISSING'
 else:
  scope=next(g for g in d['ordered_article_groups'] if g['article']=='第二条');scope['source_sha256']='b'*64
 check(name,x,RISK,False,{'S':None})
x=copy.deepcopy(u);x['text']='第四十二条申办者只登记临床试验风险管理文件名称。';check('risk_only_file_name',x,RISK,False)
x=copy.deepcopy(u);x['text']='（五）申办者应当在临床试验报告中总结并报告重要的质量问题，包括偏离预先设定可接受范围的问题和补救措施。';check('member_cannot_inherit_complete_parent',x,RISK,False)
# Equal-length original-source mutations preserve every original line interval.
x=copy.deepcopy(u)
for old,new in [('试验参与者权益和安全','数据可靠性'),('试验参与者安全','数据可靠性'),('试验参与者保护','数据可靠性')]:
 x=transform(x,old,new+' '*(len(old)-len(new)))
v,l,rs=check('data_reliability_without_participant_safety',x,RISK,True)
assert rs[0]['details']['participant_safety_quotes']==[]
# Full literal resource identity is checked back against the raw bundle.
for key,t in [('RECODE25-01383',PROTECT),('RECODE25-04067',RISK)]:
 u=units[key];x=copy.deepcopy(u);x['structure']={'component_id':'A'}
 for c in x['contexts']:c.setdefault('structure',{})['component_id']='A'
 for doc in x['source_bundle']['source_full_text_resources']:
  if doc.get('kind')=='verbatim_UTF8_snapshot_text':doc['structure']={'component_id':'B'}
 check('raw_full_literal_component_'+key,x,t,False)
u=units['RECODE25-01383'];STANDARD='bounded_annex_protection_substantive_condition'
v,l,rs=check('operative_original_drug_new_indication_condition',u,STANDARD,True)
assert rs[0]['details']['branch_scope']=='only_original_drug_new_indication_entitlement_branch'
assert len(rs[0]['details']['operative_condition_branch_quotes'])==2
for name,old,new in [
 ('data_names_without_submission_condition','并提交本办法第五条第三款规定的','仅列明本办法第五条第三款规定的'),
 ('other_indication_not_explicit_branch','首次提交境内外均未获批的新适应症','首次提交境内外已经获批的旧适应症'),
]:
 x=transform(u,old,new);v,l,rs=check(name,x,STANDARD,False);assert sub(v,PROTECT)
u=units['RECODE25-04067'];old='药物临床试验的相关活动应当遵守本规范。';new='本规范不适用于药物临床试验。'
x=transform(u,old,new+' '*(len(old)-len(new)));check('explicit_drug_trial_scope_exclusion',x,RISK,False,{'S':None})
# True operative propositions remain under independent paperwork adjuncts.
u=units['RECODE25-01383']
for extra in ['，并填写申请表','，秘书另行登记受理日期','，并在回执上签章']:
 x=transform(u,'提出药品试验数据保护申请。','提出药品试验数据保护申请'+extra+'。')
 v,l,rs=check('application_mixed_'+extra,x,PROTECT,True,{'S':1,'E':1,'I':1,'F':0});assert sub(v,STANDARD)
for extra in ['，上述申请仅为表格字段','，并未实际提出药品试验数据保护申请']:
 x=transform(u,'提出药品试验数据保护申请。','提出药品试验数据保护申请'+extra+'。')
 v,l,rs=check('application_explicit_cancel_'+extra,x,PROTECT,False);assert not sub(v,STANDARD)
x=transform(u,'境外已上市境内未上市的原研药品，首次提交','医疗器械（不是境外已上市境内未上市的原研药品），首次提交')
check('negated_parenthetical_drug_is_not_current_object',x,STANDARD,False,{'S':0,'E':0,'I':1})
u=units['RECODE25-04067']
for extra in ['，并登记文件名称','，秘书另行记录会议时间','，并在记录单上签字']:
 x=transform(u,'应当对临床试验进行风险管理。','应当对临床试验进行风险管理'+extra+'。')
 check('risk_mixed_'+extra,x,RISK,True,{'S':1,'E':0})
for extra in ['，上述风险管理仅为表格栏目','，并不实际实施风险管理']:
 x=transform(u,'应当对临床试验进行风险管理。','应当对临床试验进行风险管理'+extra+'。')
 check('risk_explicit_cancel_'+extra,x,RISK,False)
out={'scope':'finite development tests, not independent validation','passed':len(results),'tests':results,'relations_sha256':hashlib.sha256((P/'code/relations.py').read_bytes()).hexdigest()}
(P/'round6-relations-tests.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(json.dumps({'passed':len(results),'sha':out['relations_sha256']},ensure_ascii=False))
