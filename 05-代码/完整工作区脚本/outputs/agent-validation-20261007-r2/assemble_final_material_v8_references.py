"""Append source-only independent rereads without overwriting first/v6 results."""
from pathlib import Path
import hashlib, json, copy
HERE=Path(__file__).resolve().parent
DIMS=['S','E','Ec','I','F']
def jl(p): return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def strings(x):
    if isinstance(x,str): yield x
    elif isinstance(x,dict):
        for v in x.values(): yield from strings(v)
    elif isinstance(x,list):
        for v in x: yield from strings(v)
mapping=json.loads((HERE/'admin/PRIVATE_mapping.json').read_text())
lookup={(m['coder'],m['blind_id']):m['original_id'] for m in mapping}
raw={r['id']:r for r in jl(HERE/'effective_blind_inputs_v8.jsonl')}
refs={}; changes={}; sources={}; affected=set()
for coder in ('A','C'):
    base={r['id']:r for r in jl(HERE/f'reference/agent_{coder}_final_v6.jsonl')}
    folder=HERE/'confirmation'/f'agent-{coder}'
    ip=folder/'补充材料-v8.json'; op=folder/'补料复核-v8.json'
    inp=json.loads(ip.read_text())['rows']; d=json.loads(op.read_text())
    assert d['input_packet_sha256']==sha(ip) and d['coder']==coder
    assert d['operational_version']=='v1.4'
    assert [r['id'] for r in inp]==[r['id'] for r in d['rows']]
    changes[coder]=[]
    for r in d['rows']:
        bid=r['id']; rid=lookup[(coder,bid)]; affected.add(rid)
        if r['labels']!=base[rid]['labels']:
            changes[coder].append({'id':rid,'before':base[rid]['labels'],'after':r['labels']})
        base[rid]={**copy.deepcopy(r),'id':rid,'blind_id':bid}
    for rid,r in base.items():
        assert set(r['labels'])==set(DIMS) and all(type(v)is int and v in (0,1) for v in r['labels'].values())
        assert set(r['dimension_reasons'])==set(DIMS) and all(r['dimension_reasons'].values())
        found=set()
        for e in r['evidence']:
            assert e['source'] in ('unit','context')
            corpus=[raw[rid]['text']] if e['source']=='unit' else list(strings(raw[rid]['contexts']))
            assert any(e['quote'] in t for t in corpus),(coder,rid,e)
            if e['source']=='unit': found.add(e['dimension'])
        assert all(r['labels'][dim]!=1 or dim in found for dim in DIMS)
        for dim,key,allowed in [('I','innovation_subtypes',{'attribute','research_support','qualification_advantage'}),('F','fairness_subtypes',{'access','affordability','clinical_management','dimension_information'})]:
            assert bool(r[key])==bool(r['labels'][dim]) and set(r[key])<=allowed
    assert len(base)==300
    out=HERE/f'reference/agent_{coder}_final_v8.jsonl'
    out.write_text(''.join(json.dumps(base[rid],ensure_ascii=False)+'\n' for rid in sorted(base)))
    refs[coder]=base; sources[str(ip)]=sha(ip); sources[str(op)]=sha(op); sources[str(out)]=sha(out)
assert len(affected)==4
packet=[]; amap=[]
for i,rid in enumerate(sorted(affected),1):
    bid=f'ADJ8-{i:04d}'
    packet.append({**raw[rid],'id':bid,'first_judgments':{c:{k:refs[c][rid][k] for k in ['labels','dimension_reasons','evidence','innovation_subtypes','fairness_subtypes']} for c in ('A','C')}})
    amap.append({'blind_id':bid,'original_id':rid,'selection':'source_only_scope_completion_review'})
dump(HERE/'adjudication-v8/材料-01.json',{'purpose':'Source-only review of four units whose actual governing scope was completed. Unchanged manual. Review current proposition independently, no machine predictions or metrics. Preserve old adjudication.','rows':packet})
dump(HERE/'admin/adjudication_v8_mapping_PRIVATE.json',amap)
dump(HERE/'reference/agent_reference_v8_QA.json',{'n_per_coder':300,'new_source_rereads_per_coder':4,'new_reread_label_changes':changes,'unresolved_pending':0,'first_and_v6_outputs_preserved':True,'final_material_version':'v8','source_sha256':sources,'human_validation_completed':False,'disagreement_units':sum(refs['A'][r]['labels']!=refs['C'][r]['labels'] for r in refs['A'])})
print(json.dumps({'n':300,'affected':sorted(affected),'changes':changes},ensure_ascii=False))
