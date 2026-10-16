"""Finite current-content tests; synthetic source mutations never replace originals."""
import copy,hashlib,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;sys.path.insert(0,str(P/'code'))
from relations import RelationView
from dimensions import judge,_literal_pdf_span
from evidence import validate_decisions
units=json.loads((P/'semantic-overrides.json').read_text())
for r in map(json.loads,(P.parents[1]/'06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl').open()):
 if r['id'].endswith('03780'):units[r['id']]=r['semantic_unit']
units={k.rsplit('-',1)[-1]:v for k,v in units.items()}
def walk(v,f):
 if isinstance(v,str):return f(v)
 if isinstance(v,list):return [walk(x,f) for x in v]
 if isinstance(v,dict):return {k:walk(x,f) for k,x in v.items()}
 return v
def fix(u):
 u=copy.deepcopy(u)
 for r in u['source_bundle'].get('source_full_text_resources',[]):
  pages={p.get('source_resource_id'):p for p in r.get('paragraphs',[])}
  for m in r.get('bounded_unordered_list',{}).get('ordered_member_ranges',[]):
   p=pages.get(m['source_resource_id'])
   if p and m['text'] in p['text']:
    a=p['text'].index(m['text']);m['unicode_code_point_interval_half_open']=[a,a+len(m['text'])]
  for m in r.get('annex_literal_index',{}).get('ordered_question_headings',[]):
   p=pages.get(m['source_resource_id'])
   if p and m['literal_heading'] in p['text']:
    a=p['text'].index(m['literal_heading']);m['unicode_code_point_interval_half_open']=[a,a+len(m['literal_heading'])]
 def hashes(x):
  if isinstance(x,list):return [hashes(a) for a in x]
  if isinstance(x,dict):
   x={k:hashes(v) for k,v in x.items()}
   if isinstance(x.get('text'),str):
    for key in ('text_sha256','text_utf8_sha256'):
     if key in x:x[key]=hashlib.sha256(x['text'].encode()).hexdigest()
   return x
  return x
 return hashes(u)
def variant(u,old,new):
 sha=u['source_ref']['sha256'];synthetic=hashlib.sha256(('ROUND6_SYNTHETIC'+old+new).encode()).hexdigest()
 return fix(walk(u,lambda s:s.replace(old,new).replace(sha,synthetic)))
def current(u,new):
 old=u['text']
 def rep(s):
  span=_literal_pdf_span(s,old)
  return s[:span[0]]+new+s[span[1]:] if span else s
 return fix(walk(u,rep))
results=[]
def check(name,key,u,want,path=None):
 v=RelationView(u);ds=judge(v);validate_decisions(v.unit,ds)
 labels={k:d['value'] for k,d in ds.items()};paths={k:[d['basis_path']]+[a['basis_path'] for a in d.get('details',{}).get('additional_evidence',[])] for k,d in ds.items()}
 ok=all(labels[k]==val for k,val in want.items())
 if path:ok=ok and path[1] in paths[path[0]]
 results.append({'name':name,'target':key,'expected':want,'labels':labels,'passed':ok,'paths':paths,'requests':v.material_requests})
for key,expected in [('01383',{'S':1,'E':1,'I':1,'Ec':0,'F':0}),('04067',{'S':1,'E':0,'I':0,'F':0}),('03423',{'S':1,'E':1,'Ec':0,'I':0,'F':0}),('03919',{'S':1,'E':0,'Ec':0,'I':0,'F':0}),('03780',{'Ec':1,'S':0,'E':0,'I':0,'F':0})]:check('original_'+key,key,units[key],expected)
for key in ['03423','03919']:
 u=units[key]
 check('current_only_quoted_field_'+key,key,current(u,'栏目名称：“'+u['text']+'”'),{'S':0,'E':0})
 x=copy.deepcopy(u)
 for c in x['contexts']:
  if c['kind']=='source_resource_text':c['source_ref']['sha256']='f'*64
 check('wrong_page_source_'+key,key,x,{'S':None,**({'E':None} if key=='03423' else {})})
 x=copy.deepcopy(u);x['structure']={'component_id':'CURRENT'}
 for c in x['contexts']:
  if c['kind']=='source_resource_text':c['structure']['component_id']='OTHER'
 check('wrong_page_component_'+key,key,x,{'S':None,**({'E':None} if key=='03423' else {})})
 x=copy.deepcopy(u);x['source_bundle']['source_full_text_resources'][0]['paragraphs'].pop()
 removed=[cid for cid,o in x['derived_context_origins'].items() if o.get('source_bundle_pointer')=='/source_full_text_resources/0/paragraphs/2']
 x['contexts']=[c for c in x['contexts'] if c['context_id'] not in removed]
 for cid in removed:x['derived_context_origins'].pop(cid)
 check('missing_last_page_'+key,key,x,{'S':None,**({'E':None} if key=='03423' else {})})
u=units['03423']
check('list_lead_only','03423',current(u,'这些特征包括但不限于以下几个方面：'),{'S':0,'E':0})
check('elderly_generic_healthcare','03423',current(u,'在开展老年患者一般照护时，需要将老年患者特征纳入考虑。'),{'S':0,'E':0})
check('merely_enter_characteristic_field','03423',current(u,'在药物研发表格中，需要将老年患者特征填写在对应字段。'),{'S':0,'E':0})
check('mixed_consideration_and_form','03423',current(u,u['text'].rstrip('。')+'；秘书填写会议日期。'),{'S':1,'E':1})
x=variant(u,'药效学','吸收率');check('no_effect_response_member','03423',x,{'S':1,'E':0})
x=copy.deepcopy(u);x['source_bundle']['source_full_text_resources'][0]['bounded_unordered_list']['ordered_member_ranges'].pop(1)
check('missing_one_complete_member','03423',x,{'S':None,'E':None})
x=variant(u,'这些特征包括但不限于以下几个方面：','这些特征仅指身高体重；下列为其他项目背景：')
check('explicit_different_features','03423',x,{'S':0,'E':0})
x=variant(units['03423'],'这些特征包括但不限于以下几个方面：','这些特征包括但不限于以下几个方面：仅指行政登记，后文是其他项目描述。')
# Keep the literal lead index unchanged so the extra content is a real gap.
x['source_bundle']['source_full_text_resources'][0]['bounded_unordered_list']['literal_lead_in']='这些特征包括但不限于以下几个方面：'
check('unindexed_intervening_scope_text','03423',x,{'S':None,'E':None})
u=units['03919']
check('signature_only','03919',current(u,'明确电子签名的要求及地位。'),{'S':0})
check('general_risk_without_direct_safety_info','03919',current(u,'增加申办者对临床试验实施风险管理的要求。'),{'S':0})
check('info_file_transfer_only','03919',current(u,'上传安全性信息报告文件并填写递交时间。'),{'S':0})
check('wrong_information_object','03919',current(u,'优化网络安全性信息的报告流程，明确相关责任方。'),{'S':0})
check('mixed_actual_plus_signature','03919',current(u,'优化安全性信息的报告流程，明确相关责任方；明确电子签名要求。'),{'S':1})
x=variant(u,'（2026 年修订）','（2025 年修订）')
# Consistently changed synthetic edition is still coherent; version years are not hard-coded labels.
check('same_source_consistent_other_edition','03919',x,{'S':1})
x=copy.deepcopy(u);x['source_bundle']['source_full_text_resources'][0]['annex_literal_index']['literal_annex_reference']=x['source_bundle']['source_full_text_resources'][0]['annex_literal_index']['literal_annex_reference'].replace('2026','2025')
check('mismatching_cited_edition','03919',x,{'S':None})
x=variant(u,'在保护试验参与者方面','在保护试验数据网络方面');check('missing_direct_participant_information_link','03919',x,{'S':None})
u=units['03780']
check('publication_only','03780',current(u,'国家医保局印发了《支持创新药高质量发展的若干措施》。'),{'Ec':0})
check('catalogue_title_only','03780',current(u,'栏目标题：商保创新药目录。'),{'Ec':0})
check('catalogue_field_only','03780',current(u,'填写“明确提出增设商保创新药目录”字段。'),{'Ec':0})
check('other_catalogue_current','03780',current(u,u['text'].replace('商保创新药目录','常用药目录')),{'Ec':0})
x=copy.deepcopy(u)
for c in x['contexts']:
 if c['kind']=='paragraph':c['text']=c['text'].replace('商保创新药目录是国家医保局','2026年新版商保创新药目录是国家医保局')
check('later_edition_payment_not_borrowed','03780',x,{'Ec':0})
x=copy.deepcopy(u)
for c in x['contexts']:
 if c['kind']=='paragraph':c['text']=c['text'].replace('也是为创新药拓展多元支付的有效尝试','只是一个目录名称')
check('missing_payment_definition','03780',x,{'Ec':0})
check('mixed_establishment_and_signature','03780',current(u,u['text'].rstrip('。')+'；相关人员在收文表签字。'),{'Ec':1})
x=copy.deepcopy(u)
for c in x['contexts']:
 if c['kind']=='paragraph':c['source_ref']['sha256']='f'*64
check('catalogue_cross_source','03780',x,{'Ec':0})
report={'scope':'finite implementation tests, not independent validation','dimensions_sha256':hashlib.sha256((P/'code/dimensions.py').read_bytes()).hexdigest(),'passed':sum(r['passed'] for r in results),'total':len(results),'cases':results}
(P/'round6-dimensions-tests.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'passed':report['passed'],'total':len(results),'failed':[x for x in results if not x['passed']]},ensure_ascii=False,indent=2))
