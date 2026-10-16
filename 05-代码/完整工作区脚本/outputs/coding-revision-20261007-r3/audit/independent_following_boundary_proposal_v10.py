from pathlib import Path
import json, re, hashlib, unicodedata
from functools import lru_cache
from pypdf import PdfReader
BASE=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if c.isalnum())
@lru_cache(None)
def source(p):
    p=Path(p)
    if p.suffix.lower()!='.pdf':return norm(p.read_text())
    out=[]
    for i,page in enumerate(PdfReader(p).pages,1):
        ls=(page.extract_text() or '').splitlines()
        if len(ls)>=4 and ls[:3]==['国家医疗保障局规章','X','国家医疗保障局发布'] and re.fullmatch(r'-\s*'+str(i)+r'\s*-',ls[3].strip()):ls=ls[4:]
        for edge in (0,-1):
            if ls and norm(ls[edge])==str(i):ls.pop(edge)
        out.append('\n'.join(ls))
    return norm('\n'.join(out))
# Boundary paragraphs explicitly read in source structure, never chosen by labels.
bounds={
'00039':('p0033','enumeration 1-3 ends; p0033 is independent publication/state-update proposition'),
'00050':('p0044','different source form: 附2异议表 starts at source line72 after current附1申请理由'),
'00054':('p0045','different source form: 附3首次沟通交流拟讨论问题 starts at line88 after current附2异议理由/signature'),
'00834':('renew25_p007','condition section ends before 二、规则'),
'00900':('renew25_p071','condition section ends before 二、规则'),
'00925':('p0019','same-level (2) exit-consideration subsection after current (1) application conditions'),
'00929':('p0023','higher-level 3.其他 after current 2.目录内药品/(2) exit conditions'),
'01493':('p0054','same-level 2、自然病史研究 after current 1、诊疗情况 subsection'),
'01544':('p0008','condition section ends before 二、规则'),
'01618':('p0074','condition section ends before 二、规则'),
'01636':('p0008','condition section ends before 二、规则'),
'01710':('p0074','condition section ends before 二、规则'),
'01952':('p0019','same-level 3.调出目录重点考虑情形 after current 2.须申报方可调整'),
'01956':('p0023','higher-level (三)其他 after current (二)目录内药品 exit conditions'),
'02074':('renew22_p007','condition section ends before 二、规则'),
'02133':('renew22_p065','condition section ends before 二、规则'),
'02282':('p0021','same-level (2) exit-consideration subsection after current (1) application conditions'),
'02914':('p0013','same-level (三)中药饮片 after current (二)目录内西药和中成药'),
'03232':('p0013','next article 第十一条'),
'03371':('p0054','condition section ends before 二、规则'),
'03391':('p0078','condition section ends before 二、规则'),
'03701':('p0020','figure-flow section ends before 二、政策问答'),
'03974':('p0042','next article 第二十二条'),
'03977':('p0046','next article 第二十三条'),
'04240':('p0015','same-level (三)中药饮片 after current (二)目录内西药和中成药'),
'04338':('p0011','next article 第六条'),
'04589':('p0145','next article 第六十二条'),
'04594':('p0151','next article 第六十四条'),
'04643':('p0200','next article 第八十一条 before 第二节药品再注册'),
'04709':('p0255','next article 第九十八条'),
'04712':('p0259','next article 第九十九条'),
'04752':('p0296','next article 第一百一十七条')}
rows=[json.loads(s) for s in (BASE/'rule_inputs_shared_v10.jsonl').read_text().splitlines()];rb={r['id']:r['input'] for r in rows};out=[]
for short,(bid,reason) in bounds.items():
    rid='RECODE25-'+short;r=rb[rid];ps=json.loads(Path(r['candidate_file']).read_text())['paragraphs'];idx={p['id']:i for i,p in enumerate(ps)};b=ps[idx[bid]];f=r['llm_v29_shared_context']['structured_following_units'];removed=[x for x in f if idx[x['paragraph_id']]>=idx[bid]];kept=[x for x in f if idx[x['paragraph_id']]<idx[bid]]
    sp=str(Path(b.get('source_file') or r.get('unit_source') or r['source']));checks={'boundary_literal_in_source':norm(b['text']) in source(sp),'source_hash_matches_current':sha(sp)==(r.get('unit_source_sha256') or r['source_sha256']),'candidate_hash_matches_current':sha(r['candidate_file'])==r['candidate_sha256'],'all_removed_literal_in_source':all(norm(x['text']) in source(sp) for x in removed),'nonempty_removal':bool(removed)}
    out.append({'id':rid,'field':'structured_following_units','current_unit':r['unit_text'],'source_path':sp,'source_sha256':sha(sp),'candidate_path':r['candidate_file'],'candidate_sha256':sha(r['candidate_file']),'boundary':{'paragraph_id':bid,'text':b['text'],'pages':b.get('pages',[]),'source_lines':b.get('line_ids') or b.get('source_lines',[])},'reason':reason,'remove_exact_context_items':removed,'keep_exact_context_items':kept,'checks':checks})
report={'scope':'Source-only proposal; no labels or predictions read for boundary selection; frozen classifier and prompts untouched. All154 nonempty following fields reviewed for existing overshoot; versioned v5 siblings and v6 complete five-condition lists retained as legitimate same-head/scope reference context. Heading crossings that are direct children of a broad document/stage/requirements intro are not automatically removed. This proposal repairs definite overshoots; it does not certify first-four previews as complete lists.','n_definite_boundary_overshoot_units':len(out),'n_removed_items':sum(len(x['remove_exact_context_items']) for x in out),'all_source_checks_pass':all(all(x['checks'].values()) for x in out),'proposals':out,'broad_intro_heading_crossings_retained_ids':['00321','00596','00916','00937','00996','01046','01088','01194','01233','01250','01797','01944','01963','02147','02163','02250','02299','02592','02614','02832','02908','03164','03655','04271','04287'],'additional_warning':'Many old first-four following previews stop before remaining same-list items. Repaired v10 19 certificates are complete; completeness for all other old previews is not asserted.'}
(BASE/'audit/independent_following_boundary_proposal_v10.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in {'proposals'}},ensure_ascii=False,indent=2));print('Failed source checks:',[(x['id'],x['checks']) for x in out if not all(x['checks'].values())])
