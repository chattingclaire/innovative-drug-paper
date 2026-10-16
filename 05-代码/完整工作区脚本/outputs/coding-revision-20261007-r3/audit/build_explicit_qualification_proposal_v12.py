"""Source-only explicit-reference family proposal. No predictions/labels read."""
from pathlib import Path
from functools import lru_cache
import copy,hashlib,json,re,unicodedata
from html.parser import HTMLParser
from pypdf import PdfReader
B=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s)if c.isalnum())
ll={x['id']:x for x in map(json.loads,(B/'effective_blind_inputs_v11.jsonl').read_text().splitlines())};rr={x['id']:x['input']for x in map(json.loads,(B/'rule_inputs_shared_v11.jsonl').read_text().splitlines())}
def rid(s):return 'RECODE25-'+s
def texts(v):
 if isinstance(v,dict):
  for k,x in v.items():
   if k=='text'and isinstance(x,str):yield x
   else:yield from texts(x)
 elif isinstance(v,list):
  for x in v:yield from texts(x)
@lru_cache(None)
def cd(s):return json.loads(Path(rr[rid(s)]['candidate_file']).read_text())
@lru_cache(None)
def bodies(path):
 out=[]
 for i,pg in enumerate(PdfReader(path).pages,1):
  ls=[s for s in(pg.extract_text()or'').splitlines()if s.strip()]
  if len(ls)>=4 and ls[:3]==['国家医疗保障局规章','X','国家医疗保障局发布']and re.fullmatch(r'-\s*'+str(i)+r'\s*-',ls[3].strip()):ls=ls[4:]
  offset={'NHSA-常用问答-2026版.pdf':3,'5.pdf':1}.get(Path(path).name,0)
  for edge in(0,-1):
   if ls and i-offset>0 and norm(ls[edge])==str(i-offset):ls.pop(edge)
  out.append(norm('\n'.join(ls)))
 return out
class HT(HTMLParser):
 def __init__(self):super().__init__();self.out=[]
 def handle_data(self,s):self.out.append(s)
@lru_cache(None)
def html_text(p):
 h=HT();h.feed(Path(p).read_text());return norm(''.join(h.out))
@lru_cache(None)
def source_json(p):return json.loads(Path(p).read_text())
def verify(p,source):
 sp=Path(source);ids=p.get('line_ids')or p.get('source_lines')or[]
 if sp.suffix.lower()=='.pdf':
  if sp.name=='CDE-关爱延伸-正式计划镜像.pdf':return {'verified':True,'method':'actual_pdf_pages5_6_visually_reviewed_v11','pages':p['pages'],'evidence_audit':'v11_image_visual_review_evidence.json'}
  bs=bodies(source);ok=norm(p['text'])in ''.join(bs[i-1]for i in p['pages']);return {'verified':ok,'method':'exact_normalized_literal_on_stated_original_pdf_pages'}
 if sp.suffix.lower()=='.json':
  sj=source_json(source);checks=[]
  for k in ids:
   if k.startswith('normative_paragraphs:')or k.startswith('announcement_paragraphs:'):
    name,n=k.split(':');raw=sj[name][int(n)-1];checks.append(norm(p['text'])in norm(raw));checks.append(norm(raw)in html_text(sj['source_html']));checks.append(sha(sj['source_html'])==sj['source_sha256'])
   elif k.startswith('tables:'):
    _,n,_,row=k.split(':');tb=sj['tables'][int(n)-1];checks.extend([norm(p['text'])==norm(' | '.join(tb['rows'][int(row)-1])),sha(tb['source_image'])==tb['source_sha256'],tb['visually_checked']is True])
  return {'verified':bool(checks)and all(checks),'method':'exact_source_json_key_plus_bound_original_html_or_table_image','source_keys':ids}
 ls=sp.read_text().splitlines();raw=''.join(ls[int(x.lstrip('L'))-1]for x in ids);return {'verified':norm(p['text'])in norm(raw),'method':'exact_literal_on_original_source_lines'}
def extract(donor,first,last=None):
 c=cd(donor);ps=c['paragraphs'];ix={p['id']:i for i,p in enumerate(ps)};i=ix[first];j=ix[last or first];assert i<=j;cp=rr[rid(donor)]['candidate_file'];out=[]
 for p in ps[i:j+1]:
  sp=p.get('source_file')or c['source'];v=verify(p,sp);assert v['verified'],(donor,p['id'],'source verification failed')
  out.append({'paragraph_id':p['id'],'text':p['text'],'pages':p.get('pages',[]),'source_lines':p.get('line_ids')or p.get('source_lines')or[],'source_path':sp,'source_sha256':sha(sp),'candidate_path':cp,'candidate_sha256':sha(cp),'role':'explicit_reference_only_not_current_analysis_unit','verification':v})
 nxt=ps[j+1]if j+1<len(ps)else None
 return out,{'first_paragraph_id':first,'last_paragraph_id':last or first,'all_paragraphs_in_interval_included':True,'next_candidate_paragraph_id':nxt['id']if nxt else None,'next_candidate_paragraph_text':nxt['text']if nxt else None}
plans={};inventory=[]
def add(s,donor,first,last,address,nested=None):
 cs,bd=extract(donor,first,last);current=list(texts(ll[rid(s)]['contexts']));available=all(any(norm(x['text'])==norm(t)for t in current)for x in cs)
 inventory.append({'id':rid(s),'current_unit':ll[rid(s)]['text'],'reference_address':address,'referent_paragraph_ids':[x['paragraph_id']for x in cs],'already_exactly_available_in_v11':available,'action':'no_change_already_available'if available else 'supply_exact_explicit_reference'})
 if available:return
 x={'reference_address':address,'selection':'complete_exact_cited_interval_only','contexts':cs,'structure_boundary':bd,'usage':'只消解当前原句明确援引的资格、条件或范围；不新增分析单元，不自动继承所引条款的维度标签。'}
 if nested:x['incorporated_explicit_reference']=copy.deepcopy(nested)
 plans.setdefault(rid(s),[]).append(x)
# The entire actual 2020/2021 annex eligibility-reference family, plus the
# definite within-section qualifying restatement, has the same source repair.
for s,donor,first,last in [('01043','00997','p0006','p0015'),('01006','00997','p0006','p0014'),('01289','01234','p0006','p0012'),('01239','01234','p0006','p0011')]:
 nested=ll[rid(donor)]['contexts'].get('explicitly_cited_articles_v10',[]);add(s,donor,first,last,'本方案第二部分（一）目录外西药和中成药的完整资格条件',nested)
# Precisely named commercial-insurance criteria, preserving the distinct
# normative work-plan and application-guide source text in each document.
for s,d,a,z in [('00784','00784','guide25_p006','guide25_p010'),('00936','00936','p0009','p0013'),('02297','02297','p0008','p0014'),('02450','02450','p0006','p0012')]:
 add(s,d,a,None,'前述基本目录外条件（1）');add(s,d,z,None,'前述基本目录外条件（5）'if s in['00784','00936']else'前述基本目录外条件（7）')
# All exact numbered inside-directory routes. Source text is bound to the
# actual corresponding year, not a later-year criterion with similar wording.
def inside(d,number):
 c=cd(d);ps=c['paragraphs'];source=rr[rid(d)].get('unit_source')or rr[rid(d)]['source'];scope=[p for p in ps if Path(p.get('source_file')or c['source']).resolve()==Path(source).resolve()];i=next(i for i,p in enumerate(scope)if '目录内西药和中成药'in p['text']);tail=scope[i+1:];matches=[p for p in tail if re.match(r'^(?:\('+str(number)+r'\)|'+str(number)+r'\.)',p['text'])];assert matches;return matches[0]['id']
for s,d,ns in [('00717','00784',[1]),('00719','00784',[2]),('00720','00784',[3]),('00721','00784',[3]),('00785','00784',[3]),('00813','00784',[2,3]),('01304','01304',[3]),('01332','01332',[2,3]),('02452','02450',[3]),('02485','02450',[2,3]),('02799','02799',[2,3]),('03815','02450',[1]),('03818','02450',[2]),('03819','02450',[3]),('03820','02450',[3]),('03822','02450',[3])]:
 for n in ns:add(s,d,inside(d,n),None,'本年度申报指南基本目录内条件'+str(n))
add('02485','02450','p0023','p0024','本指南商保创新药目录内申报条件')
for s,addr,a,z in [('03715','本年度工作方案基本目录外条件5','p0012',None),('03716','本年度工作方案商保创新药目录内条件1','p0035','p0036'),('03826','本年度工作方案基本目录外条件1','p0008',None),('03826','本年度工作方案基本目录外条件7','p0014',None)]:add(s,'02297',a,z,addr)
# Exact within-renewal-rule references: qualification(1) and sections (一)/(二).
for s in ['00851','01562','01654','02091','03318']:
 c=cd(s);ps=c['paragraphs'];i=next(i for i,p in enumerate(ps)if ll[rid(s)]['text']in p['text']);prior=ps[i-1];assert prior['text'].startswith('(1)');add(s,s,prior['id'],None,'本条件（1）：原支付范围适用条件')
for a,b,start,end in [('00889','00893','renew25_p039','renew25_p047'),('01604','01608','p0040','p0048'),('01696','01700','p0040','p0048'),('02124','02123','renew22_p037','renew22_p043'),('03360','03364','p0022','p0030')]:
 for s in[a,b]:add(s,s,start,end,'本规则（二）调整支付范围的药品：完整计算规定')
ps=cd('02106')['paragraphs'];i=next(i for i,p in enumerate(ps)if p['id']=='renew22_p037');j=max(j for j,p in enumerate(ps[:i])if p['text'].startswith('(一)'));add('02106','02106',ps[j]['id'],ps[i-1]['id'],'本规则（一）原支付范围降幅计算')
# CDE eligibility subsection and its exact third-item exception, visually
# checked against the original image-only PDF pages5/6 in the v11 source audit.
for s in['01449','01468']:add(s,s,'p0016','p0023','申报指南1.1申请资格：完整三项资格及解释')
add('01466','01466','p0020','p0021','上述第（2）条第3项；第1/2项只保留在同段原文中，不属本次例外的引用范围')
# Explicit article-based qualification/scope references in the data-protection
# structure, including identical chemical and biological table rows.
add('01403','01403','p0013','p0017','本办法第五条（含第三款保护范围）')
add('01404','01404','p0018','p0021','本办法第六条')
for s in['01420','01423','01432','01433']:
 add(s,s,'p0022','p0023','本办法第七条第一/第二款（含“该药品”的第一款对象）')
 if s in['01420','01432']:add(s,s,'p0013','p0017','第七条第一款明确再援引的第五条')
 else:add(s,s,'p0018','p0021','第七条第二款明确再援引的第六条')
add('04388','04388','p0008','p0010','本规范第五条：处方审核药师的完整两项资格')
# Verify the annex inside-directory criteria are explicit and self-contained;
# they do not merely point to an unseen whole source section.
for s in['01044','01045','01290','01291']:
 inventory.append({'id':rid(s),'current_unit':ll[rid(s)]['text'],'action':'no_change_self_contained_annex_inside_directory_criterion','reason':'原句直接给出该项全部资格条件，并非仅以第二部分标题回指；不把目录内其他情形移入当前项。'})
freeze=json.loads((B/'rules-v33/candidate_freeze.json').read_text());assert all(sha(k)==v for k,v in freeze['production_code_sha256'].items());assert all(sha(k)==v for k,v in freeze['all_runtime_py_sha256'].items())
proposal={'scope':'Source-only explicit cited qualification/condition/section family repair, after the root supplied01043/01289 actual unresolved-source issue; no new confirmation, machine labels or references read. Whole-family selection based on exact current-unit cross-reference addresses, not scores or labels.','proposal_version':'v12_pending_root_freeze','previous_material':'v11_immutable','new_analysis_units':0,'original_unit_text_changes':0,'new_reference_field':'explicitly_cited_qualifications_v12','affected_unit_n':len(plans),'affected_ids':sorted(plans),'proposals':[{'id':k,'current_unit':ll[k]['text'],'current_unit_sha256':hashlib.sha256(ll[k]['text'].encode()).hexdigest(),'references':v}for k,v in sorted(plans.items())],'source_family_inventory':inventory,'frozen_production_code_unchanged':True,'frozen_runtime_unchanged':True,'references_or_predictions_read':False}
(B/'audit/explicit_qualification_source_proposal_v12.json').write_text(json.dumps(proposal,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'affected_unit_n':len(plans),'affected_ids':sorted(plans),'inventory_n':len(inventory),'reference_n':sum(len(v)for v in plans.values())},ensure_ascii=False,indent=2))
