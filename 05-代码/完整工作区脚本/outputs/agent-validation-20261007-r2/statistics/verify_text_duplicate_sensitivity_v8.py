"""Independent checks for conditional text-deletion diagnostics; no builder imports."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import datetime,hashlib,json
import numpy as np
from verify_final_statistics import point,arrays,verify_ci,val,valid,close,q_exact,rank

P=Path(__file__).resolve().parent;RUN=P.parent;B=5000;BASE=2026100721
DIMS=('S','E','Ec','I','F');GROUPS=('NMPA','NHSA','NHC')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
read=lambda p:json.loads(Path(p).read_text())
def rows(p):return{r['id']:r for r in map(json.loads,Path(p).read_text().splitlines())}
def main():
    path=P/'正文重复剔除-v8-最终机器与参照.json';report=read(path)
    sample={r['original_id']:r for r in read(RUN/'admin/sampling_design.json')['sample']}
    audit=read(RUN/'audit-training/独立培训材料QA.json')['checks']['text_overlap']['current_training_vs_known_development']['normalized_matches']
    excluded={r['training_id']for r in audit};assert sorted(excluded)==report['excluded_original_ids']and len(excluded)==20
    assert report['original_weights_not_reused_as_design_weights']is True and report['original240_and60_results_and_design_unchanged']is True
    inputs=rows(RUN/'rule_inputs_shared_v8.jsonl');sources={rid:r['input'].get('unit_source',r['input']['source'])for rid,r in inputs.items()}
    objects={c:rows(RUN/f'reference/agent_{c}_final_v8.jsonl')for c in('A','C')};objects['third_agent_candidate']=rows(P/'adjudicated_agent_reference_candidate_v8.jsonl')
    objects.update({m:rows(b['path'])for m,b in report['method_bindings'].items()})
    sourcesha={**report['source_sha256'],str(path):sha(path),str(Path(__file__)):sha(__file__),str(P/'verify_final_statistics.py'):sha(P/'verify_final_statistics.py')}
    assert all(sha(p)==s for p,s in sourcesha.items());cache={};records=0;cis=0
    for r in report['records']:
        ids=[rid for rid,s in sample.items()if rid not in excluded and s['component']==r['component']and(r['group']=='ALL'or s['group']==r['group'])]
        left=objects['A'if r['method']=='A_C'else r['method']];right=objects[r['reference']];d=r['dimension']
        table=np.asarray([[int((val(left[rid],d),val(right[rid],d))==pair)for pair in((1,1),(1,0),(0,1),(0,0))]for rid in ids],float)
        raw=list(map(int,table.sum(axis=0)));est=point(raw)
        assert r['paired_n']==len(ids)and r['raw_confusion']==dict(zip(('TP','FP','FN','TN'),raw))
        assert r['left_positive_n']==raw[0]+raw[1]and r['reference_positive_n']==raw[0]+raw[2]
        for k,v in r['metrics'].items():close(v['estimate'],est[k])
        for mechanism,field in(('department_unit_conditional_WR','ci95_conditional_unit_WR'),('department_source_file_conditional_WR','ci95_conditional_source_file_WR')):
            key=(r['component'],r['group'],mechanism,tuple(ids))
            if key not in cache:
                message='/'.join(('text_family_deletion_conditional',mechanism,'/'.join(ids)))
                rng=np.random.default_rng((BASE+int(hashlib.sha256(message.encode()).hexdigest()[:8],16))%2**32);f=np.zeros((B,len(ids)))
                for g in GROUPS:
                    ii=[i for i,rid in enumerate(ids)if sample[rid]['group']==g]
                    if not ii:continue
                    if mechanism=='department_unit_conditional_WR':f[:,ii]=rng.multinomial(len(ii),[1/len(ii)]*len(ii),size=B)
                    else:
                        files=sorted({sources[ids[i]]for i in ii});k=len(files);m=rng.multinomial(k,[1/k]*k,size=B)
                        for i in ii:f[:,i]=m[:,files.index(sources[ids[i]])]
                cache[key]=f
            boot=arrays(cache[key]@table)
            for k,v in r['metrics'].items():verify_ci(v[field],boot[k]);cis+=1
        records+=1
    vectors=0
    for r in report['probability_deleted_subset_attention']:
        ids=[rid for rid,s in sample.items()if rid not in excluded and s['component']=='probability_base'and(r['group']=='ALL'or s['group']==r['group'])]
        counts,q=q_exact(objects[r['method']],ids);assert r['n']==len(ids)and r['rank_tiers']==rank(q)
        for d in DIMS:assert r['dimension_hit_counts'][d]==counts[d];close(r['shares'][d],None if q[d]is None else float(q[d]))
        assert r['five_hit_denominator']==sum(counts.values());vectors+=1
    assert records==520 and vectors==28
    assert all(sha(p)==s for p,s in sourcesha.items())
    qa={'status':'passed','checked_at':datetime.datetime.now().astimezone().isoformat(),'classification_records':records,'classification_intervals_checked':cis,'attention_vectors_checked':vectors,
        'independence':'No builders/core imports; shares rational, alternative kappa algebra, both conditional WR mechanisms independently reconstructed.',
        'original_design_not_reused_for_deleted_subset':True,'human_validation_completed':False,'source_sha256':sourcesha}
    (P/'正文重复剔除-v8独立数值QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in qa.items()if k not in('source_sha256','independence')},ensure_ascii=False))
if __name__=='__main__':main()
