"""Extend exposure exclusions using developer supplied files, without sampling labels."""
import argparse, ast, collections, hashlib, json, re, unicodedata
from datetime import datetime
from pathlib import Path
BASE=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区')
OUT=Path(__file__).parent
parser=argparse.ArgumentParser();parser.add_argument('--version',default='2');parser.add_argument('--prior',default='开发暴露映射-当前语料.json');parser.add_argument('--corpus',type=Path,default=BASE/'统一文本复核包.jsonl');parser.add_argument('--adapter',type=Path,default=BASE/'统计输入接入准备.json');args=parser.parse_args()
def load(p): return json.loads(p.read_text())
def norm(s): return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).strip('。.!！?？;；')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
raw=[json.loads(l) for l in args.corpus.read_text().splitlines()]
units={r['review_id']:r for r in raw if r['count_as_analysis_unit']}
norms={k:norm(r['unit_text']) for k,r in units.items()}
prior=load(OUT/args.prior)
assert digest(args.corpus)==prior['inputs'][str(args.corpus)]
ex={k:list(v) for k,v in prior['exclusions'].items()}
supp=load(BASE/'开发暴露文件补充清单.json')
filemeta=[]; strings=[]; direct=collections.defaultdict(set)
id_re=re.compile(r'\b[a-f0-9]{10}:[A-Za-z0-9_]+\b')
textkeys={'text','old_text','unit_text','sent','sentence','expected_text','原文'}
def walk(x,origin):
    if isinstance(x,dict):
        for k,v in x.items():
            if k in textkeys and isinstance(v,str) and len(v)>=15: strings.append((origin,v))
            if isinstance(v,str):
                for rid in id_re.findall(v): direct[rid].add(origin)
            walk(v,origin)
    elif isinstance(x,list):
        for y in x: walk(y,origin)

for f in supp['files']:
    p=Path(f['path']); content=p.read_text(); origin=str(p)
    filemeta.append({'path':origin,'sha256':digest(p),'manifest_hash_matches':digest(p)==f['sha256']})
    for rid in id_re.findall(content): direct[rid].add(origin)
    if p.suffix=='.json': walk(json.loads(content),origin)
    elif p.suffix=='.py':
        for n in ast.walk(ast.parse(content)):
            if isinstance(n,ast.Constant) and isinstance(n.value,str) and len(n.value)>=15 and len(re.findall(r'[\u4e00-\u9fff]',n.value))>=10:
                strings.append((origin,n.value))
for k,origins in direct.items():
    if k in units: ex.setdefault(k,[]).append({'kind':'supplement_explicit_id','used_in':sorted(origins)})
unique={}
for origin,s in strings: unique.setdefault(norm(s),set()).add(origin)
for s,origins in unique.items():
    for k,t in norms.items():
        if s==t or (min(len(s),len(t))>=20 and (s in t or t in s)):
            ex.setdefault(k,[]).append({'kind':'supplement_text_exact' if s==t else 'supplement_containment_candidate','used_in':sorted(origins)})
groups=collections.defaultdict(list)
for k,t in norms.items(): groups[t].append(k)
for members in groups.values():
    seeds=[k for k in members if k in ex]
    if seeds:
        for k in members:
            if k not in ex: ex[k]=[{'kind':'exact_duplicate_of_exposed','seed_ids':seeds}]
grams={k:set(t[i:i+5] for i in range(len(t)-4)) for k,t in norms.items() if len(t)>=30}
post=collections.defaultdict(set)
for k,g in grams.items():
    for x in g: post[x].add(k)
seeds=set(ex); edges=[]
for k in sorted(seeds & grams.keys()):
    counts=collections.Counter(y for x in grams[k] for y in post[x] if y not in seeds)
    for y,overlap in counts.items():
        if min(len(norms[k]),len(norms[y]))/max(len(norms[k]),len(norms[y])) < .75: continue
        dice=2*overlap/(len(grams[k])+len(grams[y]))
        if dice>=.85:
            ex.setdefault(y,[]).append({'kind':'supplement_near_duplicate_candidate','seed_id':k,'dice':round(dice,6)})
            edges.append({'seed_id':k,'candidate_id':y,'dice':round(dice,6)})
eligible=sorted(set(units)-set(ex))
ad=load(args.adapter); docs={d['id']:d for d in ad['documents']}
strata=collections.Counter()
for k in eligible:
    r=units[k]; d=docs[r['original_file_stem']]
    yr=r.get('component_year') or (d.get('publication_date') or '')[:4] or 'unknown'
    strata[f'{d["group"]}|{yr}']+=1
result={'version':f'exposure-audit-supplement-v{args.version}','created_at':datetime.now().astimezone().isoformat(),
 'status':'provisional_reference_label_holdout_frame_not_unseen_text_certificate',
 'analysis_units':len(units),'excluded_count':len(ex),'provisional_eligible_count':len(eligible),
 'prior_exclusions':len(prior['exclusions']),'newly_excluded_count':len(set(ex)-set(prior['exclusions'])),
 'limits':prior['limits']+['补充文件路径也不是完整曝光证明。未按标签或预测表现选择排除。','材料不足/难判不因此剔除，后续盲评可为待定并报告覆盖率。'],
 'inputs':{'corpus_path':str(args.corpus),'corpus_sha256':digest(args.corpus),'adapter_path':str(args.adapter),'adapter_sha256':digest(args.adapter),'prior_audit_sha256':digest(OUT/args.prior),'supplement_manifest_sha256':digest(BASE/'开发暴露文件补充清单.json'),'files':filemeta},
 'stratum_counts':dict(sorted(strata.items())),'exclusions':dict(sorted(ex.items())),'added_near_duplicate_edges':edges,'provisional_eligible_ids':eligible,
 'algorithm':'原审计+补充材料明确ID/文本精确或>=20字包含匹配+测试源中文长字面量匹配+全体相同文本及长度比>=.75/5-gram Dice>=.85近重复候选；不把近重复称语义等价。'}
target=OUT/f'开发暴露映射-补充v{args.version}.json'
if target.exists(): raise RuntimeError('Do not overwrite exposure history')
target.write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps({k:result[k] for k in ['analysis_units','excluded_count','provisional_eligible_count','newly_excluded_count','stratum_counts']},ensure_ascii=False))
