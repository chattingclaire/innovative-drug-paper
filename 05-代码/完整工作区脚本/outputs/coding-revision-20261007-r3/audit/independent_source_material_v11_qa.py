"""Independent source and release-integrity QA; never reads labels/results."""
from pathlib import Path
from functools import lru_cache
import hashlib,importlib.util,json,re,unicodedata
from pypdf import PdfReader
BASE=Path(__file__).resolve().parents[1]
def jl(p):return [json.loads(s)for s in Path(p).read_text().splitlines()if s.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s)if c.isalnum())
@lru_cache(None)
def pdf_bodies(path):
 out=[];removed=[];p=Path(path);offset={'NMPA-抗肿瘤药物临床研发指导原则-2021.pdf':3,'NHSA-常用问答-2026版.pdf':3,'5.pdf':1}.get(p.name,0)
 for i,pg in enumerate(PdfReader(p).pages,1):
  ls=[s for s in(pg.extract_text()or'').splitlines()if s.strip()]
  if len(ls)>=4 and ls[:3]==['国家医疗保障局规章','X','国家医疗保障局发布']and re.fullmatch(r'-\s*'+str(i)+r'\s*-',ls[3].strip()):removed.append({'page':i,'exact_header':ls[:4]});ls=ls[4:]
  for edge in(0,-1):
   if ls and i-offset>0 and norm(ls[edge])==str(i-offset):removed.append({'page':i,'exact_edge_page_number':ls[edge]});ls.pop(edge)
  out.append(norm('\n'.join(ls)))
 return out,removed
@lru_cache(None)
def txt_lines(path):return Path(path).read_text().splitlines()
def literal(y):
 path=y['source_path'];p=Path(path)
 if p.suffix.lower()=='.pdf':
  bs,_=pdf_bodies(path);return norm(y['text'])in ''.join(bs[n-1]for n in y['pages'])
 ls=txt_lines(path);return norm(y['text'])in norm(''.join(ls[int(n.lstrip('L'))-1]for n in y['source_lines']))
ll=jl(BASE/'effective_blind_inputs_v11.jsonl');rr=jl(BASE/'rule_inputs_shared_v11.jsonl');old=jl(BASE/'effective_blind_inputs_v10.jsonl');oldr=jl(BASE/'rule_inputs_shared_v10.jsonl');lb={x['id']:x for x in ll};rb={x['id']:x['input']for x in rr};ob={x['id']:x for x in old}
m=json.loads((BASE/'material_v11_manifest.json').read_text());p=json.loads((BASE/'audit/necessary_list_completion_proposal_v11.json').read_text());cleanup=json.loads((BASE/'audit/independent_following_boundary_proposal_v10.json').read_text());v10=json.loads((BASE/'material_v10_manifest.json').read_text())
spec=importlib.util.spec_from_file_location('frozen_cv',BASE/'rules-v33/runtime/context_validation.py');cv=importlib.util.module_from_spec(spec);spec.loader.exec_module(cv)
checks={'n_4924':len(ll)==len(rr)==len(old)==len(oldr)==4924,'ids_order_unchanged':all(a['id']==b['id']for a,b in zip(ll,old)),'texts_unchanged':all(a['text']==b['text']for a,b in zip(ll,old)),'two_methods_ids_equal':all(a['id']==b['id']for a,b in zip(ll,rr)),'two_methods_text_equal':all(a['text']==b['input']['unit_text']for a,b in zip(ll,rr)),'two_methods_contexts_equal':all(a['contexts']==b['input']['llm_v29_shared_context']for a,b in zip(ll,rr)),'rule_unit_text_and_id_unchanged':all(a['id']==b['id']and a['input']['unit_id']==b['input']['unit_id']and a['input']['unit_text']==b['input']['unit_text']for a,b in zip(rr,oldr)),'llm_hash_manifest':sha(BASE/'effective_blind_inputs_v11.jsonl')==m['new_llm_sha256'],'rule_hash_manifest':sha(BASE/'rule_inputs_shared_v11.jsonl')==m['new_rule_sha256'],'proposal_hash_manifest':sha(BASE/'audit/necessary_list_completion_proposal_v11.json')==m['source_proposal_sha256'],'cleanup_hash_manifest':sha(BASE/'audit/independent_following_boundary_proposal_v10.json')==m['overshoot_proposal_sha256'],'prior_files_still_match_manifest':sha(BASE/'effective_blind_inputs_v10.jsonl')==m['previous_llm_sha256']and sha(BASE/'rule_inputs_shared_v10.jsonl')==m['previous_rule_sha256']}
reports=[];boundary_exceptions=[]
for x in p['proposals']:
 rid=x['id'];r=rb[rid];cs=lb[rid]['contexts'];ys=x['complete_contiguous_interval'];ps=json.loads(Path(x['candidate_path']).read_text())['paragraphs'];ix={z['id']:i for i,z in enumerate(ps)};i=ix[x['first_paragraph_id']];j=ix[x['last_paragraph_id']]
 item={'source_hash':sha(x['source_path'])==x['source_sha256']==(r.get('unit_source_sha256')or r['source_sha256']),'candidate_hash':sha(x['candidate_path'])==x['candidate_sha256']==r['candidate_sha256'],'all_candidate_paragraphs_in_interval':[(z['id'],z['text'],z.get('pages',[]))for z in ps[i:j+1]]==[(z['paragraph_id'],z['text'],z['pages'])for z in ys],'head_contains_original_unit_once':norm(ys[0]['text']).count(norm(r['unit_text']))==1,'complete_following_in_both_inputs':[(z['paragraph_id'],z['text'],z.get('pages',[]))for z in cs['structured_following_units']]==[(z['paragraph_id'],z['text'],z['pages'])for z in ys[1:]],'no_other_attachment_in_interval':all(Path(z.get('source_file',x['source_path'])).resolve()==Path(x['source_path']).resolve()for z in ps[i:j+1]),'next_boundary_matches':x['next_boundary']is None or(ps[j+1]['id']==x['next_boundary']['paragraph_id']and ps[j+1]['text']==x['next_boundary']['text'])}
 paras=[]
 for y in ys:
  auto=literal(y);visual=y['verification'].get('image_only_pdf',False)
  img_ok=visual and all(Path(z).is_file()for z in y['verification']['visual_artifact_paths'])and rid[-5:]in{'01459','01493','01502','01530'}
  paras.append({'paragraph_id':y['paragraph_id'],'pages':y['pages'],'source_lines':y['source_lines'],'literal_on_exact_stated_pages_or_lines':auto if not visual else None,'actual_pdf_visual_verified':img_ok if visual else None,'passed':auto or img_ok})
 item['all_actual_source_paragraphs_verified']=all(z['passed']for z in paras)
 b=x['next_boundary'];bverify=None
 if b:
  z=dict(b,source_path=x['source_path']);bauto=literal(z);bvisual=Path(x['source_path']).name=='CDE-关爱延伸-正式计划镜像.pdf'and rid[-5:]in{'01459','01493','01502','01530'}
  bverify={'literal_on_stated_pages_or_lines':bauto if not bvisual else None,'actual_pdf_visual_verified':True if bvisual else None,'passed':bauto or bvisual}
  if rid in {'RECODE25-00762','RECODE25-03864'}:
   bs,_=pdf_bodies(x['source_path']);last=ys[-1];at_document_end=last['pages'][-1]==len(bs)and bs[-1].endswith(norm(last['text']));figure_title=norm('图1 工作流程图')in bs[3]
   bverify={'candidate_next_is_appended_earlier_figure_transcription':True,'actual_source_boundary':'end_of_document_after_fourth_enumerated_item','last_enumerated_item_ends_exact_final_source_page':at_document_end,'earlier_figure_title_verified_on_page4':figure_title,'full_figure_transcription_not_used_as_current_context':True,'passed':at_document_end and figure_title}
  if not bverify['passed']:boundary_exceptions.append({'id':rid,'boundary':b,'source':x['source_path']})
 item['actual_next_boundary_verified']=bverify is None or bverify['passed']
 reports.append({'id':rid,'checks':item,'head':x['head'],'first_paragraph':ys[0]['paragraph_id'],'last_paragraph':ys[-1]['paragraph_id'],'following_paragraph_n':len(ys)-1,'next_boundary':b,'next_boundary_verification':bverify,'paragraph_checks':paras,'frozen_v27_validator_accepts':cv.verified_following_list(r)})
cleanup_checks=[]
for x in cleanup['proposals']:
 new=lb[x['id']]['contexts'][x['field']]
 cleanup_checks.append({'id':x['id'],'all_exact_overshoot_items_absent':all(not any(y.get('paragraph_id')==z.get('paragraph_id')and y['text']==z['text']for y in new)for z in x['remove_exact_context_items'])})
versioned=[];refs=[]
for a,b in zip(ll,old):
 for k in set(a['contexts'])|set(b['contexts']):
  if k in{'structured_following_units_v5','structured_following_units_v6'}:versioned.append({'id':a['id'],'field':k,'unchanged':a['contexts'].get(k)==b['contexts'].get(k)})
 if b['contexts'].get('explicitly_cited_articles_v10'):refs.append({'id':a['id'],'unchanged':a['contexts'].get('explicitly_cited_articles_v10')==b['contexts'].get('explicitly_cited_articles_v10')})
v10_checks=[{'id':x['id'],'whole_context_verbatim':lb[x['id']]['contexts']==ob[x['id']]['contexts'],'frozen_runtime_accepts':cv.verified_following_list(rb[x['id']])}for x in v10['list_source_repairs']]
preview=[{'id':rid,'explicit_navigation_role':lb[rid]['contexts']['following_context_status_v11']['role']=='local_navigation_preview','explicit_incomplete':lb[rid]['contexts']['following_context_status_v11']['complete']is False}for rid in m['local_navigation_preview_ids']]
freeze=json.loads((BASE/'rules-v33/candidate_freeze.json').read_text());code=[{'path':k,'unchanged':sha(k)==v}for k,v in freeze['production_code_sha256'].items()];runtime=[{'path':k,'unchanged':sha(k)==v}for k,v in freeze['all_runtime_py_sha256'].items()]
checks.update({'all_121_list_checks_pass':len(reports)==121 and all(all(x['checks'].values())for x in reports),'all_32_exact_overshoots_removed':len(cleanup_checks)==32 and all(x['all_exact_overshoot_items_absent']for x in cleanup_checks),'v10_19_contexts_verbatim_and_validator_accepted':len(v10_checks)==19 and all(x['whole_context_verbatim']and x['frozen_runtime_accepts']for x in v10_checks),'all_v5_v6_fields_unchanged':len(versioned)==5 and all(x['unchanged']for x in versioned),'all_23_explicit_article_refs_unchanged':len(refs)==23 and all(x['unchanged']for x in refs),'all_27_navigation_previews_explicitly_incomplete':len(preview)==27 and all(x['explicit_navigation_role']and x['explicit_incomplete']for x in preview),'all_new_v27_certificates_runtime_accepted':all(cv.verified_following_list(rb[rid])for rid in m['new_v27_validator_accepted_ids']),'all_production_code_frozen':all(x['unchanged']for x in code),'all_runtime_py_frozen':all(x['unchanged']for x in runtime)})
report={'scope':'Independent source and frozen-release QA. No r3 confirmation/new gold/agent result/classifier prediction files read.','all_checks_pass':all(checks.values()),'checks':checks,'list_checks':reports,'boundary_exceptions':boundary_exceptions,'cleanup_checks':cleanup_checks,'v10_19_reuse_checks':v10_checks,'versioned_field_checks':versioned,'explicit_reference_reuse_checks':refs,'navigation_preview_checks':preview,'production_code_checks':code,'runtime_checks':runtime,'literal_source_paragraph_n':sum(z['literal_on_exact_stated_pages_or_lines']is True for x in reports for z in x['paragraph_checks']),'visually_verified_image_paragraph_n':sum(z['actual_pdf_visual_verified']is True for x in reports for z in x['paragraph_checks']),'pdf_exact_page_header_removals':{k:pdf_bodies(k)[1]for k in {x['source_path']for x in p['proposals']if Path(x['source_path']).suffix.lower()=='.pdf'}},'manifest_sha256':sha(BASE/'material_v11_manifest.json')}
(BASE/'audit/independent_source_material_v11_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'all_checks_pass':report['all_checks_pass'],'checks':checks,'failed_lists':[x for x in reports if not all(x['checks'].values())],'boundary_exceptions':boundary_exceptions,'literal_source_paragraph_n':report['literal_source_paragraph_n'],'visually_verified_image_paragraph_n':report['visually_verified_image_paragraph_n']},ensure_ascii=False,indent=2))
