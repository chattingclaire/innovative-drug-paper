"""Independent literal-source and symmetric-input binding audit for v12."""
from pathlib import Path
from functools import lru_cache
from html.parser import HTMLParser
import hashlib,json,re,unicodedata
from pypdf import PdfReader
B=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.encode()).hexdigest()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s)if c.isalnum())
def jl(p):return [json.loads(s)for s in Path(p).read_text().splitlines()if s.strip()]
@lru_cache(None)
def pages(path):
 out=[]
 for n,pg in enumerate(PdfReader(path).pages,1):
  ls=[s for s in(pg.extract_text()or'').splitlines()if s.strip()]
  if len(ls)>=4 and ls[:3]==['国家医疗保障局规章','X','国家医疗保障局发布']and re.fullmatch(r'-\s*'+str(n)+r'\s*-',ls[3].strip()):ls=ls[4:]
  off={'5.pdf':1,'NHSA-常用问答-2026版.pdf':3}.get(Path(path).name,0)
  for edge in(0,-1):
   if ls and n-off>0 and norm(ls[edge])==str(n-off):ls.pop(edge)
  out.append(norm('\n'.join(ls)))
 return out
class Text(HTMLParser):
 def __init__(self):super().__init__();self.ts=[]
 def handle_data(self,s):self.ts.append(s)
@lru_cache(None)
def html(path):
 p=Text();p.feed(Path(path).read_text());return norm(''.join(p.ts))
@lru_cache(None)
def obj(path):return json.loads(Path(path).read_text())
def literal(c):
 source=Path(c['source_path']);lines=c.get('source_lines',[])
 if source.suffix.lower()=='.pdf':
  if source.name=='CDE-关爱延伸-正式计划镜像.pdf':
   evidence=obj(str(B/'audit/v11_image_visual_review_evidence.json'));return set(c['pages'])<={5,6}and all(sha(x['path'])==x['sha256']for x in evidence['images'])and c['verification']['verified']
  ps=pages(str(source));return norm(c['text'])in ''.join(ps[n-1]for n in c['pages'])
 if source.suffix.lower()=='.json':
  s=obj(str(source));values=[]
  for key in lines:
   name,n=key.split(':');raw=s[name][int(n)-1];values.extend([norm(c['text'])in norm(raw),norm(raw)in html(s['source_html']),sha(s['source_html'])==s['source_sha256']])
  return bool(values)and all(values)
 ls=source.read_text().splitlines();return norm(c['text'])in norm(''.join(ls[int(n.lstrip('L'))-1]for n in lines))
ll=jl(B/'effective_blind_inputs_v12.jsonl');rr=jl(B/'rule_inputs_shared_v12.jsonl');old=jl(B/'effective_blind_inputs_v11.jsonl');oldr=jl(B/'rule_inputs_shared_v11.jsonl');lb={x['id']:x for x in ll};rb={x['id']:x['input']for x in rr};ob={x['id']:x for x in old};p=obj(str(B/'audit/explicit_qualification_source_proposal_v12.json'));m=obj(str(B/'material_v12_manifest.json'))
checks={'n_4924':len(ll)==len(rr)==len(old)==len(oldr)==4924,'original_ids_order_text_unchanged':all(a['id']==b['id']and a['text']==b['text']for a,b in zip(ll,old)),'rule_original_units_unchanged':all(a['id']==b['id']and a['input']['unit_id']==b['input']['unit_id']and a['input']['unit_text']==b['input']['unit_text']for a,b in zip(rr,oldr)),'all_original_context_fields_verbatim':all({k:v for k,v in a['contexts'].items()if k!='explicitly_cited_qualifications_v12'}==b['contexts']for a,b in zip(ll,old)),'both_methods_exact_same_context_and_original_text':all(a['id']==b['id']and a['text']==b['input']['unit_text']and a['contexts']==b['input']['llm_v29_shared_context']for a,b in zip(ll,rr)),'exactly_48_actual_context_changes':sorted(a['id']for a,b in zip(ll,old)if a['contexts']!=b['contexts'])==m['affected_ids']==p['affected_ids']and len(m['affected_ids'])==48,'v11_all_bytes_immutable':all(sha(B/fn)==h for fn,h in m['prior_v11_files_preserved_sha256'].items()),'v12_new_input_hashes_match':sha(B/'effective_blind_inputs_v12.jsonl')==m['new_llm_sha256']and sha(B/'rule_inputs_shared_v12.jsonl')==m['new_rule_sha256'],'proposal_hash_matches':sha(B/'audit/explicit_qualification_source_proposal_v12.json')==m['proposal_sha256']}
reports=[];paras=0;refs=0;nested_n=0
for x in p['proposals']:
 rid=x['id'];cert=lb[rid]['contexts']['explicitly_cited_qualifications_v12'];r=rb[rid];rc={'current_text_binding':cert['current_unit_sha256']==dig(lb[rid]['text'])==dig(r['unit_text']),'current_unit_source_binding':cert['current_unit_source_sha256']==(r.get('unit_source_sha256')or r['source_sha256'])and sha(cert['current_unit_source_path'])==cert['current_unit_source_sha256'],'current_candidate_binding':cert['current_unit_candidate_sha256']==r['candidate_sha256']==sha(cert['current_unit_candidate_path']),'references_payload_binding':cert['references']==x['references']and cert['references_sha256']==dig(json.dumps(cert['references'],ensure_ascii=False,sort_keys=True)),'rule_new_field_identical_to_shared_field':r['explicitly_cited_qualifications_v12']==cert}
 rs=[]
 for ref in cert['references']:
  refs+=1;cs=ref['contexts'];cp=obj(cs[0]['candidate_path']);ps=cp['paragraphs'];ix={z['id']:i for i,z in enumerate(ps)};i=ix[cs[0]['paragraph_id']];j=ix[cs[-1]['paragraph_id']];bd=ref['structure_boundary'];pc=[]
  for c in cs:
   paras+=1;z=ps[ix[c['paragraph_id']]];pc.append({'paragraph_id':c['paragraph_id'],'pages':c['pages'],'checks':{'literal_source_match':literal(c),'source_hash':sha(c['source_path'])==c['source_sha256'],'candidate_hash':sha(c['candidate_path'])==c['candidate_sha256'],'exact_candidate_text_pages_lines':z['text']==c['text']and z.get('pages',[])==c['pages']and(z.get('line_ids')or z.get('source_lines')or[])==c['source_lines'],'actual_candidate_source_matches':Path(z.get('source_file')or cp['source']).resolve()==Path(c['source_path']).resolve(),'reference_only_role':c['role']=='explicit_reference_only_not_current_analysis_unit','no_dimension_labels_supplied':not(set(c)&{'S','E','Ec','I','F','labels','predictions','gold'})}})
  nc=[]
  for c in ref.get('incorporated_explicit_reference',[]):
   nested_n+=1;nc.append({'paragraph_id':c['paragraph_id'],'article':c['article'],'source_literal_and_hash':literal(c)and sha(c['source_path'])==c['source_sha256']and sha(c['candidate_path'])==c['candidate_sha256']})
  rs.append({'address':ref['reference_address'],'checks':{'complete_contiguous_cited_candidate_interval':[(z['id'],z['text'])for z in ps[i:j+1]]==[(z['paragraph_id'],z['text'])for z in cs],'boundary_first_last_match':bd['first_paragraph_id']==cs[0]['paragraph_id']and bd['last_paragraph_id']==cs[-1]['paragraph_id']and bd['all_paragraphs_in_interval_included']is True,'next_boundary_exact_candidate_match':(bd['next_candidate_paragraph_id']is None and j==len(ps)-1)or(j+1<len(ps)and bd['next_candidate_paragraph_id']==ps[j+1]['id']and bd['next_candidate_paragraph_text']==ps[j+1]['text']),'all_source_paragraph_checks':all(all(z['checks'].values())for z in pc),'all_nested_explicit_articles_verified':all(z['source_literal_and_hash']for z in nc)},'paragraph_checks':pc,'nested_reference_checks':nc})
 rc['all_reference_checks']=all(all(z['checks'].values())for z in rs);reports.append({'id':rid,'checks':rc,'references':rs})
freeze=obj(str(B/'rules-v33/candidate_freeze.json'));prod=[{'path':k,'unchanged':sha(k)==v}for k,v in freeze['production_code_sha256'].items()];runtime=[{'path':k,'unchanged':sha(k)==v}for k,v in freeze['all_runtime_py_sha256'].items()];checks.update({'all_48_reference_target_and_source_bindings':len(reports)==48 and all(all(x['checks'].values())for x in reports),'all_62_explicit_reference_intervals':refs==62,'all_frozen_production_code_hashes':all(x['unchanged']for x in prod),'all_frozen_runtime_hashes':all(x['unchanged']for x in runtime),'same_manuals_unchanged':all((B/'protocol'/f).read_bytes()==(B/'future-human-validation-v3/手册'/f).read_bytes()for f in['完整五维手册-v1.3.md','共用操作说明-v1.4.md'])})
x=next(x for x in p['proposals']if x['id']=='RECODE25-01043')['references'][0];cs=x['contexts'];checks['01043_exact_outside_section_excludes_inside_sibling']=cs[0]['paragraph_id']=='p0006'and cs[-1]['paragraph_id']=='p0015'and x['structure_boundary']['next_candidate_paragraph_id']=='p0016'and'目录内'in x['structure_boundary']['next_candidate_paragraph_text']and not any('目录内'in c['text']for c in cs);checks['annex_four_self_contained_inside_rows_unchanged']=all(lb['RECODE25-'+s]==ob['RECODE25-'+s]for s in['01044','01045','01290','01291'])
report={'scope':'Independent source-only binding audit: no A/C/T labels, new confirmation, actual-model prediction labels or reference answers read. Same material availability does not establish frozen-rule semantic use of the newly added field.','all_checks_pass':all(checks.values()),'checks':checks,'affected_unit_n':48,'reference_interval_n':refs,'literal_or_visual_verified_reference_paragraph_instances':paras,'nested_explicit_article_paragraph_instances':nested_n,'reference_checks':reports,'production_code_checks':prod,'runtime_checks':runtime,'manifest_sha256':sha(B/'material_v12_manifest.json'),'v12_frozen_rule_new_field_consumption_not_claimed':True}
(B/'audit/independent_source_material_v12_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all_checks_pass':report['all_checks_pass'],'checks':checks,'reference_interval_n':refs,'paragraph_instances':paras,'nested_article_paragraph_instances':nested_n,'failed_units':[x for x in reports if not all(x['checks'].values())]},ensure_ascii=False,indent=2))
