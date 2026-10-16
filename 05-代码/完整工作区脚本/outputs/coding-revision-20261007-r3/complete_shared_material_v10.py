"""Complete actual enumerated conditions and explicitly cited articles, without labels.

Boundaries below were read in the candidate and the original PDF.  Apply the
same repair to every member of each source-list family, before final execution.
No predictions, reference labels, or performance scores are read here.
"""
from pathlib import Path
import copy, hashlib, json, re, unicodedata
from functools import lru_cache
from pypdf import PdfReader

HERE = Path(__file__).resolve().parent
def jl(p): return [json.loads(x) for x in Path(p).read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s): return hashlib.sha256(s.encode()).hexdigest()
def norm(s): return ''.join(c for c in unicodedata.normalize('NFKC', s) if c.isalnum())
@lru_cache(None)
def source_text(p):
    p=Path(p)
    if p.suffix.lower()!='.pdf': return norm(p.read_text())
    bodies=[]
    for index,page in enumerate(PdfReader(p).pages,1):
        lines=(page.extract_text() or '').splitlines()
        if (len(lines)>=4 and lines[:3]==['国家医疗保障局规章','X','国家医疗保障局发布']
                and re.fullmatch(r'-\s*'+str(index)+r'\s*-',lines[3].strip())):
            lines=lines[4:]
        # Remove only a page's first/last standalone, exact printed page number.
        # Other numeric tokens and all policy text remain untouched.
        for edge in (0,-1):
            if lines and norm(lines[edge])==str(index):lines.pop(edge)
        bodies.append('\n'.join(lines))
    return norm('\n'.join(bodies))

ll=jl(HERE/'effective_blind_inputs_v9.jsonl'); rr=jl(HERE/'rule_inputs_shared_v9.jsonl')
lb={r['id']:r for r in ll}; rb={r['id']:r['input'] for r in rr}
# Inclusive paragraph ranges. Endpoints precede the next actual section/item.
ranges={
 '00846':('renew25_p021','renew25_p028'), '00889':('renew25_p058','renew25_p061'),
 '00919':('p0008','p0013'), '00997':('p0007','p0015'),
 '01008':('p0017','p0024'), '01195':('p0004','p0011'),
 '01204':('p0013','p0015'), '01234':('p0007','p0012'),
 '01241':('p0014','p0021'), '01557':('p0022','p0029'),
 '01604':('p0059','p0062'), '01649':('p0022','p0029'),
 '01945':('p0007','p0012'), '02086':('renew22_p021','renew22_p028'),
 '02124':('renew22_p054','renew22_p057'), '02148':('p0007','p0013'),
 '02273':('p0007','p0015'), '03360':('p0041','p0044'),
 '04272':('p0007','p0013'),
}
repairs=[]
for short,(first,last) in ranges.items():
    rid='RECODE25-'+short;ri=rb[rid];candidate=Path(ri['candidate_file'])
    assert sha(candidate)==ri['candidate_sha256']
    cd=json.loads(candidate.read_text());ps=cd['paragraphs']
    i=next(i for i,p in enumerate(ps) if p['id']==first)
    j=next(i for i,p in enumerate(ps) if p['id']==last)
    assert i<j and norm(ri['unit_text']) in norm(ps[i]['text'])
    source=Path(ri.get('unit_source') or ri['source']);sh=sha(source)
    assert sh==(ri.get('unit_source_sha256') or ri['source_sha256'])
    contexts=[]
    for p in ps[i:j+1]:
        assert Path(p.get('source_file',source)).resolve()==source.resolve()
        assert norm(p['text']) in source_text(str(source)), (rid,p['id'],'not in original source')
        contexts.append({'paragraph_id':p['id'],'text':p['text'],'pages':p.get('pages',[]),
                         'source_lines':p.get('line_ids') or p.get('source_lines',[]),
                         'source_path':str(source),'source_sha256':sh,
                         'candidate_path':str(candidate),'candidate_sha256':sha(candidate),
                         'verification':{'verified':True,'method':'original_source_and_complete_enumerated_interval'}})
    boundary={'first_paragraph':first,'last_paragraph':last,
              'all_paragraphs_in_interval_included':True,
              'next_paragraph_id':ps[j+1]['id'] if j+1<len(ps) else None,
              'next_paragraph_text':ps[j+1]['text'] if j+1<len(ps) else None}
    cert={'original_unit_sha256':digest(ri['unit_text']),'source_sha256':sh,
          'contexts':contexts,'contexts_sha256':digest(json.dumps(contexts,ensure_ascii=False,sort_keys=True)),
          'repair_status':'supplemented','unresolved_material_gaps':[],
          'source_files_hash_verified':True,'structure_boundary':boundary,
          'usage':'Resolve only the actual conditions and references of this proposition. Never copy every child dimension into the head or add extra analysis units.'}
    ri['verified_following_list_v27']=copy.deepcopy(cert)
    c=lb[rid]['contexts'];c['structured_following_units']=copy.deepcopy(contexts[1:])
    c['verified_context_certificates']['verified_following_list_v27']=copy.deepcopy(cert)
    c['following_list_usage_v10']=cert['usage']
    ri['llm_v29_shared_context']=copy.deepcopy(c)
    repairs.append({'id':rid,'source_path':str(source),'source_sha256':sh,
                    'candidate_path':str(candidate),'candidate_sha256':sha(candidate),
                    'following_paragraph_n':j-i,'boundary':boundary})

# Supply the actual text of the named, explicitly incorporated articles. These
# are references, not additional current propositions or transferred labels.
cp=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区/原文补全/PDF段落与句子候选/NHSA-基本医疗保险用药管理暂行办法-2020.json')
cd=json.loads(cp.read_text());articles={}
for article in ('第七条','第八条','第九条','第十条'):
    out=[]
    for p in cd['paragraphs']:
        if p.get('article')!=article: continue
        source=Path(p.get('source_file') or cd['source'])
        assert norm(p['text']) in source_text(str(source)), (article,p['id'])
        out.append({'paragraph_id':p['id'],'article':article,'text':p['text'],
                    'pages':p.get('pages',[]),'source_path':str(source),
                    'source_sha256':sha(source),'candidate_path':str(cp),'candidate_sha256':sha(cp),
                    'role':'explicitly_cited_article_only_not_current_unit'})
    assert out
    articles[article]=out
ref_ids=[]
for r in ll:
    t=r['text']
    if not re.search(r'《基本医疗保险用药(?:范围)?管理暂行办法》',t):continue
    names=[a for a in articles if a in t]
    if not names: continue
    c=r['contexts'];c['explicitly_cited_articles_v10']=[copy.deepcopy(p) for a in names for p in articles[a]]
    c['cited_article_usage_v10']='Read the exact incorporated reference only to resolve this current proposition; neither treat citation text as additional current units nor automatically inherit its dimension labels.'
    rb[r['id']]['llm_v29_shared_context']=copy.deepcopy(c)
    ref_ids.append(r['id'])

old=jl(HERE/'effective_blind_inputs_v9.jsonl')
assert len(ll)==len(rr)==4924
assert all(a['id']==b['id'] and a['text']==b['text'] for a,b in zip(ll,old))
assert all(a['contexts']==b['input']['llm_v29_shared_context'] for a,b in zip(ll,rr))
for name,rows in [('effective_blind_inputs_v10.jsonl',ll),('rule_inputs_shared_v10.jsonl',rr)]:
    (HERE/name).write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
changed=[a['id'] for a,b in zip(ll,old) if a!=b]
manifest={'material_version':'v10','n':4924,'unit_text_changes':0,'unit_id_changes':0,
          'incremental_context_changed_n':len(changed),'affected_ids':changed,
          'completed_list_n':len(repairs),'list_source_repairs':repairs,
          'explicit_cited_article_unit_n':len(ref_ids),'explicit_cited_article_ids':ref_ids,
          'reason':'Source-only repair of the complete structural family after independent coders flagged missing following conditions; no classification code or standard changed.',
          'two_methods_same_text_and_context':True,'references_or_predictions_read':False,
          'coding_standard_unchanged':'CAL-5D-v1.3 + operational-v1.4',
          'previous_llm_sha256':sha(HERE/'effective_blind_inputs_v9.jsonl'),
          'previous_rule_sha256':sha(HERE/'rule_inputs_shared_v9.jsonl'),
          'new_llm_sha256':sha(HERE/'effective_blind_inputs_v10.jsonl'),
          'new_rule_sha256':sha(HERE/'rule_inputs_shared_v10.jsonl'),
          'frozen_before_full_v32_model_execution':True,
          'new_blind_first_outputs_preserved':True,
          'scope_of_confirmation':'Frozen algorithms on source-completed material, with first coding and source-only rereading reported separately.'}
(HERE/'material_v10_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:manifest[k] for k in ['n','incremental_context_changed_n','completed_list_n','explicit_cited_article_unit_n','new_llm_sha256','new_rule_sha256']},ensure_ascii=False))
