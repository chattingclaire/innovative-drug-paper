from pathlib import Path
import hashlib, json, re, sys, unicodedata, importlib.util
from functools import lru_cache
from pypdf import PdfReader
BASE=Path(__file__).resolve().parents[1]
def jl(p):return [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if c.isalnum())
@lru_cache(None)
def page_bodies(p):
    result=[];removed=[]
    for i,page in enumerate(PdfReader(p).pages,1):
        lines=(page.extract_text() or '').splitlines()
        if len(lines)>=4 and lines[:3]==['国家医疗保障局规章','X','国家医疗保障局发布'] and re.fullmatch(r'-\s*'+str(i)+r'\s*-',lines[3].strip()):
            removed.append({'page':i,'type':'fixed_four_line_header','text':lines[:4]});lines=lines[4:]
        for edge in (0,-1):
            if lines and norm(lines[edge])==str(i):
                removed.append({'page':i,'type':'exact_edge_page_number','text':lines[edge]});lines.pop(edge)
        result.append(norm('\n'.join(lines)))
    return result,removed
spec=importlib.util.spec_from_file_location('frozen_context_validation',BASE/'rules-v33/runtime/context_validation.py');cv=importlib.util.module_from_spec(spec);spec.loader.exec_module(cv)
m=json.loads((BASE/'material_v10_manifest.json').read_text());ll=jl(BASE/'effective_blind_inputs_v10.jsonl');rr=jl(BASE/'rule_inputs_shared_v10.jsonl');old=jl(BASE/'effective_blind_inputs_v9.jsonl');oldr=jl(BASE/'rule_inputs_shared_v9.jsonl')
lb={x['id']:x for x in ll};rb={x['id']:x['input'] for x in rr}
checks={'n_4924':len(ll)==len(rr)==len(old)==len(oldr)==4924,'ids_order_unchanged':all(a['id']==b['id'] for a,b in zip(ll,old)),'texts_unchanged':all(a['text']==b['text'] for a,b in zip(ll,old)),'two_methods_ids_equal':all(a['id']==b['id'] for a,b in zip(ll,rr)),'two_methods_text_equal':all(a['text']==b['input']['unit_text'] for a,b in zip(ll,rr)),'two_methods_contexts_equal':all(a['contexts']==b['input']['llm_v29_shared_context'] for a,b in zip(ll,rr)),'rule_unit_text_and_id_unchanged':all(a['id']==b['id'] and a['input']['unit_id']==b['input']['unit_id'] and a['input']['unit_text']==b['input']['unit_text'] for a,b in zip(rr,oldr)),'llm_hash_manifest':sha(BASE/'effective_blind_inputs_v10.jsonl')==m['new_llm_sha256'],'rule_hash_manifest':sha(BASE/'rule_inputs_shared_v10.jsonl')==m['new_rule_sha256']}
reports=[]
for repair in m['list_source_repairs']:
    rid=repair['id'];r=rb[rid];c=r['verified_following_list_v27'];contexts=c['contexts'];ps=json.loads(Path(repair['candidate_path']).read_text())['paragraphs'];i=next(i for i,p in enumerate(ps) if p['id']==contexts[0]['paragraph_id']);j=i+len(contexts)-1
    item_checks={'frozen_runtime_accepts':cv.verified_following_list(r),'source_hash':sha(repair['source_path'])==repair['source_sha256'],'candidate_hash':sha(repair['candidate_path'])==repair['candidate_sha256'],'complete_contiguous_candidate_interval':[(p['id'],p['text'],p.get('pages',[])) for p in ps[i:j+1]]==[(p['paragraph_id'],p['text'],p.get('pages',[])) for p in contexts],'boundary_next_matches':repair['boundary']['next_paragraph_id']==ps[j+1]['id'] and repair['boundary']['next_paragraph_text']==ps[j+1]['text'],'head_contains_original_unit':norm(r['unit_text']) in norm(contexts[0]['text']),'llm_following_matches':lb[rid]['contexts']['structured_following_units']==contexts[1:],'shared_certificate_matches':lb[rid]['contexts']['verified_context_certificates']['verified_following_list_v27']==c}
    para_reports=[]
    for p in contexts:
        bodies,removed=page_bodies(p['source_path']);loc=''.join(bodies[x-1] for x in p['pages']);present=norm(p['text']) in loc
        para_reports.append({'paragraph_id':p['paragraph_id'],'pages':p['pages'],'literal_on_stated_pdf_pages':present})
    item_checks['all_paragraphs_on_stated_pdf_pages']=all(p['literal_on_stated_pdf_pages'] for p in para_reports)
    reports.append({'id':rid,'checks':item_checks,'head':contexts[0]['text'],'end':contexts[-1]['text'],'next':ps[j+1]['text'],'paragraphs':para_reports})
ref_reports=[]
for rid in m['explicit_cited_article_ids']:
    r=lb[rid];refs=r['contexts']['explicitly_cited_articles_v10'];pc={}
    for p in refs:
        if p['candidate_path'] not in pc:pc[p['candidate_path']]=json.loads(Path(p['candidate_path']).read_text())['paragraphs']
        bodies,_=page_bodies(p['source_path']);cand=next(x for x in pc[p['candidate_path']] if x['id']==p['paragraph_id'])
        ref_reports.append({'id':rid,'article':p['article'],'paragraph_id':p['paragraph_id'],'pages':p['pages'],'named_in_current_unit':p['article'] in r['text'],'candidate_literal_and_article_match':p['text']==cand['text'] and p['article']==cand['article'],'literal_on_stated_pdf_pages':norm(p['text']) in ''.join(bodies[x-1] for x in p['pages']),'source_hash':sha(p['source_path'])==p['source_sha256'],'candidate_hash':sha(p['candidate_path'])==p['candidate_sha256'],'reference_only_role':p['role']=='explicitly_cited_article_only_not_current_unit','no_dimension_labels':not(set(p)&{'S','E','Ec','I','F','labels','predictions','gold'})})
freeze=json.loads((BASE/'rules-v33/candidate_freeze.json').read_text());code=[{'path':p,'unchanged':sha(p)==h} for p,h in freeze['production_code_sha256'].items()];all_code=[{'path':p,'unchanged':sha(p)==h} for p,h in freeze['all_runtime_py_sha256'].items()]
checks.update({'list_count_19':len(reports)==19,'all_list_checks':all(all(x['checks'].values()) for x in reports),'reference_unit_count_23':len(set(x['id'] for x in ref_reports))==23,'all_reference_checks':all(all(v for k,v in x.items() if k not in {'id','article','paragraph_id','pages'}) for x in ref_reports),'all_production_code_frozen':all(x['unchanged'] for x in code),'all_runtime_py_frozen':all(x['unchanged'] for x in all_code)})
report={'audit_scope':'Independent read-only source QA; no r3 confirmation, new gold, or classifier prediction files read. Only shared v9/v10 inputs, material manifest, candidate/source files, frozen runtime validation and freeze manifest read.','checks':checks,'all_checks_pass':all(checks.values()),'input_sha256':sha(BASE/'effective_blind_inputs_v10.jsonl'),'rule_input_sha256':sha(BASE/'rule_inputs_shared_v10.jsonl'),'manifest_sha256':sha(BASE/'material_v10_manifest.json'),'completed_list_checks':reports,'explicit_reference_paragraph_checks':ref_reports,'production_code_checks':code,'runtime_checks':all_code,'removed_pdf_headers':{p:page_bodies(p)[1] for p in page_bodies.cache_info() and set([r['source_path'] for r in m['list_source_repairs']]+[p['source_path'] for r in ll for p in r['contexts'].get('explicitly_cited_articles_v10',[])])}}
(BASE/'audit/independent_source_material_v10_qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'checks':checks,'all_checks_pass':report['all_checks_pass'],'list_n':len(reports),'reference_paragraph_checks':len(ref_reports),'failed_lists':[x for x in reports if not all(x['checks'].values())],'failed_reference_checks':[x for x in ref_reports if not all(v for k,v in x.items() if k not in {'id','article','paragraph_id','pages'})]},ensure_ascii=False,indent=2))
