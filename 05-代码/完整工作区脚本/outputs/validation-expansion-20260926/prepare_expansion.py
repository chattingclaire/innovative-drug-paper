"""Reproducible exposure audit and 60-row development packet; no label loading."""
import argparse, collections, hashlib, json, random, re, shutil, unicodedata
from pathlib import Path
from datetime import datetime

BASE = Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区')
OUT = Path(__file__).parent
CAL = OUT.parent / '01a0dbb7-blind-review'
parser=argparse.ArgumentParser();parser.add_argument('--audit-only',action='store_true');parser.add_argument('--version',default='1');parser.add_argument('--corpus',type=Path,default=BASE/'统一文本复核包.jsonl');parser.add_argument('--adapter',type=Path,default=BASE/'统计输入接入准备.json');args=parser.parse_args()
audit_path=OUT/('开发暴露映射-当前语料.json' if args.version=='1' else f'开发暴露映射-当前语料-v{args.version}.json')
if audit_path.exists():raise RuntimeError('该审计版本已存在，禁止覆盖。')
if not args.audit_only and (OUT/'开发60-盲法与版本清单.json').exists():
    raise RuntimeError('开发60已经发送盲评，禁止覆盖既有输入；更新审计须另存新版本。')
def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p, o): p.write_text(json.dumps(o, ensure_ascii=False, indent=2))
def norm(s): return re.sub(r'\s+', '', unicodedata.normalize('NFKC', s)).strip('。.!！?？;；')

corpus = [json.loads(l) for l in args.corpus.read_text().splitlines()]
units = {r['review_id']: r for r in corpus if r['count_as_analysis_unit']}
adapter = read(args.adapter)
docs = {r['id']: r for r in adapter['documents']}
registered = read(BASE/'规则开发单元排除登记.json')['units']
old_audit = read(BASE/'人工旧样本与当前语料对应审计.json')
cal_rows = read(CAL/'agent-A/待评材料.json')['rows']
old_texts = []
for group in ['A339', 'A296']:
    old_texts += [{'origin': group, 'origin_id': r['sample_id'], 'text': r['old_text']} for r in old_audit['alignment'][group]['rows']]
old_texts += [{'origin': 'CAL18', 'origin_id': r['id'], 'text': r['text']} for r in cal_rows]
normalized = {k: norm(r['unit_text']) for k,r in units.items()}
exposure = collections.defaultdict(list)
for r in registered:
    if r['review_id'] in units: exposure[r['review_id']].append({'kind': 'registered_development', 'used_in': r['used_in']})
alignments = []
# Text-only conservative split/merge candidates; no old or new labels read.
for old in old_texts:
    s = norm(old['text']); exact=[]; fragments=[]
    for k,t in normalized.items():
        if s == t:
            exact.append(k); exposure[k].append({'kind':'historical_exact','origin':old['origin'],'origin_id':old['origin_id']})
        elif min(len(s),len(t)) >= 20 and (s in t or t in s):
            fragments.append(k); exposure[k].append({'kind':'historical_containment_candidate','origin':old['origin'],'origin_id':old['origin_id']})
    alignments.append({'origin':old['origin'], 'origin_id':old['origin_id'], 'exact':exact, 'containment_candidates':fragments})

# Propagate exact normalized duplicate exposure globally. No corpus units are deleted.
dup = collections.defaultdict(list)
for k,t in normalized.items(): dup[t].append(k)
for members in dup.values():
    seeds=[k for k in members if k in exposure]
    if seeds:
        for k in members:
            if k not in exposure: exposure[k].append({'kind':'exact_duplicate_of_exposed','seed_ids':seeds})

# Candidate near-duplicate exclusions are conservative, mechanical and label-free.
# Character 5-gram Dice >= .85, length ratio >= .75, min 30 normalized chars.
# Connected chains are not treated as verified semantic equivalence.
grams={k:set(t[i:i+5] for i in range(len(t)-4)) for k,t in normalized.items() if len(t)>=30}
post=collections.defaultdict(set)
for k,g in grams.items():
    for x in g: post[x].add(k)
seed_ids=set(exposure)
near_edges=[]
for k in sorted(seed_ids & grams.keys()):
    counts=collections.Counter(y for x in grams[k] for y in post[x] if y not in seed_ids)
    for y,overlap in counts.items():
        if min(len(normalized[k]),len(normalized[y]))/max(len(normalized[k]),len(normalized[y])) < .75: continue
        dice=2*overlap/(len(grams[k])+len(grams[y]))
        if dice>=.85:
            near_edges.append({'seed_id':k, 'candidate_id':y, 'dice':round(dice,6)})
            exposure[y].append({'kind':'near_duplicate_candidate','seed_id':k,'dice':round(dice,6)})

eligible=sorted(set(units)-set(exposure))
bygroup=collections.Counter(docs[units[k]['original_file_stem']]['group'] for k in eligible)
inputs={str(p):sha(p) for p in [args.corpus,args.adapter,BASE/'规则开发单元排除登记.json',BASE/'人工旧样本与当前语料对应审计.json']}
audit={'version':f'exposure-audit-v{args.version}','created_at':datetime.now().astimezone().isoformat(),'status':'provisional_not_complete_exposure_certificate',
 'limits':['全文恢复和版式QA曾读大量原文；没有可证明原文未见的池。','排除登记不完整；eligible仅表示未被本次已知开发映射排除。','旧296为空白表，但选样和原文已暴露，保守列入排除。','近重复仅用于保守排除，不确认语义等价，不改变分析语料或标签。'],
 'normalization':'NFKC + whitespace removal + terminal sentence punctuation removal',
 'near_duplicate_rule':'min normalized length 30; length ratio >= .75; character 5-gram Dice >= .85 against mapped exposure seeds',
 'inputs':inputs,'analysis_units':len(units),'exclusion_count':len(exposure),'provisional_eligible_count':len(eligible),'eligible_group_counts':dict(bygroup),
 'historical_mapping':alignments,'exclusions':dict(sorted(exposure.items())),'near_duplicate_edges':near_edges,'provisional_eligible_ids':eligible}
dump(audit_path,audit)
if args.audit_only:
    print(json.dumps({'audit':str(audit_path),'excluded':len(exposure),'eligible':len(eligible)},ensure_ascii=False));raise SystemExit(0)

# 60 additional development cases, all drawn from explicitly registered development.
# Never sample based on any predicted label or desired agreement; omit old CAL overlaps.
cal_excluded={k for k,v in exposure.items() if any(x.get('origin')=='CAL18' for x in v)}
cal_norms=[norm(x['text']) for x in cal_rows]
for k,t in normalized.items():
    if any(min(len(t),len(c))>=15 and (t in c or c in t) for c in cal_norms): cal_excluded.add(k)
pools=collections.defaultdict(list)
seen=set()
for reg in sorted(registered,key=lambda x:x['review_id']):
    k=reg['review_id']
    if k not in units or k in cal_excluded or normalized[k] in seen: continue
    seen.add(normalized[k]); pools[docs[units[k]['original_file_stem']]['group']].append(k)
quotas={'GOV':4,'NMPA':19,'NHSA':19,'NHC':18}
rng=random.Random(20260926)
selected=[]
for g,n in quotas.items():
    assert len(pools[g])>=n,(g,len(pools[g]),n)
    selected += rng.sample(sorted(pools[g]),n)
rng.shuffle(selected)
researcher=[]; blind=[]
fields=['paragraph_context','nearest_preceding_heading','immediately_preceding_paragraph','verified_parent_context','verified_table_context','verified_rule_branch_context']
for i,k in enumerate(selected,1):
    r=units[k]; rid=f'DEV60-{i:03d}'
    context={f:r[f] for f in fields if f in r and r[f]}
    blind.append({'id':rid,'text':r['unit_text'],'source_title':r['original_file_stem'],'pages':r['pages'],'contexts':context,
                  'context_usage':'只编码text。上下文只帮助核实对象/条件/范围，不把邻句或上级所有命中继承给本单元；nearest_preceding_heading和immediately_preceding_paragraph仅是位置关系，未经verified字段确认时不可自动当有效父级。信息不足填待定。'})
    researcher.append({'blind_id':rid,'review_id':k,'group':docs[r['original_file_stem']]['group'],'text_sha256':hashlib.sha256(r['unit_text'].encode()).hexdigest()})
dump(OUT/'开发60-研究者映射.json',{'seed':20260926,'quotas':quotas,'corpus_sha256':sha(BASE/'统一文本复核包.jsonl'),'rows':researcher,'sample_type':'development_not_final_validation','selected_using_labels':False})
packet={'version':'DEV60-20260926-v1','purpose':'扩大开发校准；不是最终验证样本','protocol':'CAL-5D-20260926-v1.1','rows':blind}
dump(OUT/'开发60-共同无答案材料.json',packet)
for coder in ['A','C']:
    d=OUT/f'agent-{coder}'; d.mkdir(exist_ok=True)
    dump(d/'待评材料.json',packet)
    shutil.copyfile(CAL/f'agent-{coder}'/'编码手册.txt',d/'编码手册.txt')
    shutil.copyfile(CAL/'统一口径/五维共用编码协议.md',d/'五维共用编码协议.md')
dump(OUT/'开发60-盲法与版本清单.json',{'created_at':datetime.now().astimezone().isoformat(),'packet_sha256':sha(OUT/'agent-A/待评材料.json'),'A_C_packets_identical':sha(OUT/'agent-A/待评材料.json')==sha(OUT/'agent-C/待评材料.json'),'protocol_sha256':sha(OUT/'agent-A/五维共用编码协议.md'),'corpus_sha256':sha(BASE/'统一文本复核包.jsonl'),'count':60,'selection_seed':20260926,'quotas':quotas,'not_formal_validation':True,'inputs':inputs})
print(json.dumps({'analysis_units':len(units),'excluded':len(exposure),'provisional_eligible':len(eligible),'eligible_groups':dict(bygroup),'development_sample':60,'development_pool_sizes':{k:len(v) for k,v in pools.items()},'packet_chars':len(json.dumps(packet,ensure_ascii=False))},ensure_ascii=False))
