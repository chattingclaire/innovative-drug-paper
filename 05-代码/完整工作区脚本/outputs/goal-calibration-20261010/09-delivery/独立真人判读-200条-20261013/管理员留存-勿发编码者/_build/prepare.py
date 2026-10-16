from pathlib import Path
import argparse, hashlib, json, random, secrets, sys
from datetime import datetime, timezone
from fractions import Fraction

HERE = Path(__file__).resolve().parent
ADMIN = HERE.parent
OUT = ADMIN.parent
ROOT = OUT.parent.parent
C = ROOT / '10-closure-20261012/current-validation/v15b-workload-preparation'
SOURCE = ROOT / '01-review/source-interface-v17-finite-source-addendum-root'

def sha(raw): return hashlib.sha256(raw).hexdigest()
def bind(p):
    p=Path(p).resolve(); raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
def write(p,v):
    with p.open('x',encoding='utf-8') as f: json.dump(v,f,ensure_ascii=False,indent=2); f.write('\n')
def read(p): return json.loads(Path(p).read_text())
def ids_sha(ids): return sha(('\n'.join(sorted(ids))+'\n').encode())
def now(): return datetime.now(timezone.utc).isoformat()

def freeze():
    assert not (ADMIN/'sampling-freeze.json').exists(), 'Already frozen; no replacement seed'
    candidate=read(C/'candidate.json')
    inp=candidate['inputs']
    for b in inp.values(): assert bind(b['path'])==b
    frame=[json.loads(x) for x in Path(inp['metadata_frame']['path']).read_text().splitlines()]
    exp=read(inp['exposure_registration']['path'])
    seed_ids=set(exp['direct_seed_source_ids'])
    fam={r['family_id'] for r in frame if r['source_id'] in seed_ids}
    excluded={r['source_id'] for r in frame if r['candidate_domain']=='exposed' or r['family_id'] in fam}
    remain=[r for r in frame if r['source_id'] not in excluded]
    assert len(remain)==1151 and len(excluded)==3330
    assert ids_sha([r['source_id'] for r in remain])==candidate['scope']['remaining_ids_sha256']
    assert ids_sha(excluded)==candidate['scope']['exposed_ids_sha256']
    machines=[]
    for key in ('rule_v15b_v17_labels','LLM_v16_auxiliary_labels'):
        machines.append({r['id']:r['labels'] for r in map(json.loads,Path(inp[key]['path']).read_text().splitlines())})
    strata=[]
    for s in candidate['candidate_design']['strata']:
        members=[]
        for r in remain:
            rid=r['source_id']
            positive=any(type(m[rid][d]) is int and m[rid][d]==1 for m in machines for d in ('I','F'))
            if r['department']==s['department'] and ('P' if positive else 'Q')==s['auxiliary_group']: members.append(rid)
        assert len(members)==s['N'] and ids_sha(members)==s['member_ids_sha256']
        strata.append({**s,'member_ids':sorted(members)})
    frozen={'schema':'independent-human200-sampling-freeze-v1','created_at_utc':now(),
      'authorization':'用户明确要求：所以给我需要给真人复核的材料呀。按现有200条候选发行材料。',
      'status':'frozen_before_unique_draw_and_human_access','human_responses_received':False,
      'scope':candidate['scope'],'source_candidate':bind(C/'candidate.json'),
      'current_pair_update':bind(C/'current-pair-update/current-pair-candidate.json'),
      'locator_exposure_event':bind(C/'current-pair-update/locator-exposure-crosscheck.json'),
      'inputs':inp,'strata':strata,'excluded_source_ids':sorted(excluded),
      'sampler':{'implementation':bind(__file__),'runtime':sys.version,'algorithm':'Python random.Random.sample over lexicographically sorted stratum member_ids. Census strata retained. Single RNG visits strata in frozen order. One draw only. Separate seeded shuffle for shared display order. A/B independently permuted blind codes, common source order retained for frozen reception compatibility.',
       'draw_seed':secrets.randbits(256),'display_seed':secrets.randbits(256),'A_blind_seed':secrets.randbits(256),'B_blind_seed':secrets.randbits(256)},
      'source_bundles':bind(SOURCE/'common-frame-bundles-v17.jsonl'),
      'source_bindings':bind(SOURCE/'packet-bindings-v17.json'),
      'manual':bind(ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt'),
      'method_locks':{side:bind(ROOT/rel/'seal.json') for side,rel in [('rule',Path('06-coding/rule-full4481-v15-v17-received-root')),('LLM',Path('06-coding/native-full4481-v17-two-whole-batch-compatible-root'))]},
      'acceptance_unchanged':candidate['unchanged_acceptance'],
      'interpretation':'本批抽样推断范围仅1151条未用于已登记开发的剩余材料。3330条曝光身份保留。发行材料不等于真人已完成或独立验证通过，不把原4481验收目标改写为1151。A/B和独立裁定须真实执行、分别保存。'}
    write(ADMIN/'sampling-freeze.json',frozen)
    print(json.dumps({'status':'freeze_saved_before_draw','strata':[(s['id'],s['N'],s['n']) for s in strata]},ensure_ascii=False))

def draw():
    assert not (ADMIN/'draw.json').exists(), 'Unique draw already exists; never redraw'
    f=read(ADMIN/'sampling-freeze.json')
    assert bind(__file__)==f['sampler']['implementation']
    for key in ('source_bundles','source_bindings','manual'): assert bind(f[key]['path'])==f[key]
    rng=random.Random(f['sampler']['draw_seed']); selected=[]
    for s in f['strata']:
        chosen=s['member_ids'][:] if s['n']==s['N'] else rng.sample(s['member_ids'],s['n'])
        selected += [{'unit_id':i,'stratum_id':s['id'],'department':s['department'],'population_N':s['N'],'sample_n':s['n'],'inclusion_probability_exact':s['pi_exact'],'sampling_weight_exact':s['w_exact']} for i in chosen]
    assert len(selected)==len({r['unit_id'] for r in selected})==200
    assert sum(Fraction(r['sampling_weight_exact']) for r in selected)==1151
    random.Random(f['sampler']['display_seed']).shuffle(selected)
    draw={'schema':'independent-human200-unique-draw-v1','created_at_utc':now(),'status':'actual_draw_before_human_access','sampling_freeze_binding':bind(ADMIN/'sampling-freeze.json'),'population_N':1151,'sample_N':200,'inherited_human_N':0,'scope':'registered_remaining_pool','records':selected}
    write(ADMIN/'draw.json',draw)
    allbindings={r['source_id']:r for r in read(f['source_bindings']['path'])}
    materials={'schema':'common-materials-manifest-v1','created_at_utc':now(),'source_binding':f['source_bundles'],'records':[{'unit_id':r['unit_id'],'source_bundle_sha256':allbindings[r['unit_id']]['source_bundle_sha256']} for r in selected]}
    write(ADMIN/'common-materials.json',materials)
    mapping={'schema':'independent-human200-blind-assignment-v1','draw_binding':bind(ADMIN/'draw.json'),'common_materials_binding':bind(ADMIN/'common-materials.json'),'inherited_human_N':0,'methods':{}}
    for side in ('A','B'):
        nums=list(range(1,201)); random.Random(f['sampler'][side+'_blind_seed']).shuffle(nums)
        mapping['methods'][side]=[{'unit_id':r['unit_id'],'original_blind_id':f'{side}-{n:03d}','source_bundle_sha256':allbindings[r['unit_id']]['source_bundle_sha256'],'material_locator':f'材料/{side}-{n:03d}.html'} for r,n in zip(selected,nums)]
    write(ADMIN/'blind-assignment.json',mapping)
    print(json.dumps({'status':'unique_draw_and_AB_mapping_saved','N':200,'population':1151,'weight_sum':1151},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=['freeze','draw']); a=p.parse_args()
    (freeze if a.action=='freeze' else draw)()
