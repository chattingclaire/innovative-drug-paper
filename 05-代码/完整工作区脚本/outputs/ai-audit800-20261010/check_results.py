"""Read-only validation and aggregation of AI-authored judgments; no inference."""
from pathlib import Path
from collections import Counter, defaultdict
import json, hashlib, csv, sys, re, datetime

BASE=Path(__file__).resolve().parent
ROOT=BASE.parent.parent
DIMS=['S','E','Ec','I','F']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def strings(v):
    if isinstance(v,str): yield v
    elif isinstance(v,dict):
        for x in v.values(): yield from strings(x)
    elif isinstance(v,list):
        for x in v: yield from strings(x)
mapping_path=ROOT/'outputs/goal-calibration-20261010/09-delivery/formal800-human-final-release-v2-20261010-sol/coordinator-private/mapping.json'
raw=json.loads(mapping_path.read_text())
mapping={r['A_blind_id']:{k:r[k] for k in ['source_id','A_blind_id','B_blind_id','domain','department','registered_exposure_status']} for r in raw['records']}
assert len(mapping)==800
assert Counter(r['domain'] for r in mapping.values())=={'remaining':600,'exposed':200}
(BASE/'checks').mkdir(exist_ok=True)
(BASE/'checks/sample-metadata.json').write_text(json.dumps({'mapping_source_sha256':sha(mapping_path),'records':mapping},ensure_ascii=False,indent=2))
reviews=[]; errors=[]; quote_warnings=[]; pdf_quote_cache={}
for f in sorted((BASE/'reviews').glob('part-*.jsonl')):
    if not re.fullmatch(r'part-\d+-\d+\.jsonl',f.name):continue
    for n,line in enumerate(f.read_text().splitlines(),1):
        if not line.strip():continue
        try:r=json.loads(line)
        except Exception as e: errors.append(f'{f.name}:{n}: {e}');continue
        r['review_part']=f.name
        bid=r.get('blind_id'); mp=mapping.get(bid)
        if not mp:errors.append(f'{bid}: unexpected blind id');continue
        srcp=BASE/'source-A/coder-A/materials'/f'{bid}.json'
        src=json.loads(srcp.read_text());sr=src['source_record']
        if r.get('source_id')!=sr['id'] or sr['id']!=mp['source_id']:errors.append(f'{bid}: source id mismatch')
        if r.get('source_text_sha256')!=hashlib.sha256(sr['text'].encode()).hexdigest():errors.append(f'{bid}: source text hash mismatch')
        js=r.get('judgments',{})
        if set(js)!=set(DIMS):errors.append(f'{bid}: dimension keys mismatch');continue
        if not r.get('read_sources'):errors.append(f'{bid}: missing actual read log')
        source_strings=list(strings(src))
        for actual in r.get('read_sources',[]):
            fp=Path(actual.split('#')[0])
            if not fp.is_absolute(): fp=ROOT/fp
            if fp.exists() and fp.suffix in ['.txt','.json','.html'] and fp!=srcp:
                source_strings.append(fp.read_text())
            elif fp.exists() and fp.suffix=='.pdf':
                # Automated quote membership only; this does not count as model reading.
                if str(fp) not in pdf_quote_cache:
                    from pypdf import PdfReader
                    pdf_quote_cache[str(fp)]='\n'.join(p.extract_text() or '' for p in PdfReader(fp).pages)
                source_strings.append(pdf_quote_cache[str(fp)])
        source_join='\n'.join(source_strings)
        norm=lambda x:re.sub(r'\s+','',str(x))
        source_norm=norm(source_join)
        for d,j in js.items():
            val=j.get('value')
            if val is not None and (type(val)!=int or val not in [0,1]):errors.append(f'{bid}/{d}: illegal value')
            for k in ['evidence','locator','reason']:
                if not isinstance(j.get(k),str) or not j[k].strip():errors.append(f'{bid}/{d}: empty {k}')
            ev=[norm(q) for q in j.get('evidence','').splitlines() if norm(q)]
            if ev and not all(q in source_norm for q in ev):quote_warnings.append({'blind_id':bid,'dimension':d,'evidence':j['evidence'],'part':f.name})
        reviews.append(r)
counts=Counter(r['blind_id'] for r in reviews)
errors.extend([f'{bid}: duplicate review' for bid,n in counts.items() if n!=1])
status={'records_completed':len(reviews),'slots_completed':len(reviews)*5,'expected_records':800,'expected_slots':4000,'errors':errors,'quote_warnings':quote_warnings,'by_part':dict(Counter(r['review_part'] for r in reviews))}
(BASE/'checks/progress.json').write_text(json.dumps(status,ensure_ascii=False,indent=2))
print(json.dumps({k:v for k,v in status.items() if k not in ['errors','quote_warnings']},ensure_ascii=False))
print(json.dumps({'errors':errors[:20],'quote_warning_count':len(quote_warnings),'quote_warning_examples':quote_warnings[:4]},ensure_ascii=False))
if '--final' not in sys.argv:sys.exit(bool(errors))
assert not errors,errors
assert set(counts)==set(mapping),'Missing records'
reviews.sort(key=lambda r:r['blind_id'])
(BASE/'AI原始判读-800条.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in reviews)+'\n')
data=[];summary=defaultdict(Counter);nulls=[]
rows=[]
for r in reviews:
    mp=mapping[r['blind_id']]
    for d in DIMS:
        j=r['judgments'][d];v=j['value']
        summary[(mp['domain'],d)][str(v)]+=1
        e=f"{j['reason']}\n依据：{j['evidence']}\n定位：{j['locator']}"
        if v is None:
            e='待定：'+e
            nulls.append({'blind_id':r['blind_id'],'source_id':r['source_id'],'domain':mp['domain'],'dimension':d,**j})
        data.append([v,e])
        rows.append([r['blind_id'],r['source_id'],mp['domain'],mp['department'],d,v,j['evidence'],j['locator'],j['reason'],'AI-Codex'])
(BASE/'checks/workbook-data.json').write_text(json.dumps(data,ensure_ascii=False))
with (BASE/'AI抽检800条-逐维明细.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.writer(f);w.writerow(['A盲号','原记录号','样本分组','部门','维度','AI判定','原文依据','定位','判定理由','执行者']);w.writerows(rows)
(BASE/'待定与补材清单.json').write_text(json.dumps(nulls,ensure_ascii=False,indent=2))
out={'identity':'AI-Codex辅助抽检，一轮800条；非真人结果，非正式LLM生产主运行','records':800,'slots':4000,'summary':[{'domain':a,'dimension':b,'zero':c['0'],'one':c['1'],'null':c['None']} for (a,b),c in sorted(summary.items())], 'null_slots':len(nulls),'quote_warnings':len(quote_warnings),'initial_jsonl_sha256':sha(BASE/'AI原始判读-800条.jsonl'),'source_package_sha256':sha(ROOT/'outputs/goal-calibration-20261010/09-delivery/formal800-human-distribution-packages-20261010-sol/formal800-A-independent.zip')}
(BASE/'抽检汇总.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print(json.dumps(out,ensure_ascii=False))
