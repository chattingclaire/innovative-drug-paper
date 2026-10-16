"""Keep original sample intact; describe deletion of known development-text matches."""
import argparse,datetime
from fractions import Fraction
from statistical_core import *
from final_machine_contract import rule_binding,llm_binding,old_bindings


def conditional_factors(ctx,ids,mechanism):
    rng=np.random.default_rng(seed('text_family_deletion_conditional',mechanism,'/'.join(ids)))
    result=np.zeros((B,len(ids)))
    for g in GROUPS:
        ii=[i for i,rid in enumerate(ids)if ctx['sample'][rid]['group']==g]
        if not ii:continue
        if mechanism=='department_unit_conditional_WR':
            n=len(ii);result[:,ii]=rng.multinomial(n,np.repeat(1/n,n),size=B)
        else:
            assert mechanism=='department_source_file_conditional_WR'
            files=sorted({ctx['sources'][ids[i]]for i in ii});k=len(files)
            m=rng.multinomial(k,np.repeat(1/k,k),size=B)
            result[:,ii]=np.stack([m[:,files.index(ctx['sources'][ids[i]])]for i in ii],axis=1)
    assert result.min()>=0
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['references_only','final'],required=True);p.add_argument('--reference-version',required=True,choices=['v6','v8']);args=p.parse_args()
    ctx=load_context();audit_path=RUN/'audit-training/独立培训材料QA.json';audit=read(audit_path)
    matches=audit['checks']['text_overlap']['current_training_vs_known_development']['normalized_matches']
    excluded={r['training_id']for r in matches};assert len(excluded)==20 and set(excluded)<=set(ctx['sample'])
    assert Counter((ctx['sample'][rid]['component'],ctx['sample'][rid]['group'])for rid in excluded)==Counter({('probability_base','NHSA'):18,('enriched_challenge','NHSA'):2})
    refpaths={c:RUN/f'reference/agent_{c}_final_{args.reference_version}.jsonl'for c in('A','C')}
    refs={c:jsonl(path)for c,path in refpaths.items()};pairs=[('A_C','C',refs['A'],refs['C'])]
    paths=ctx['source_paths']+[audit_path,Path(__file__)]+list(refpaths.values());bindings={}
    if args.stage=='final':
        cp=OUT/'adjudicated_agent_reference_candidate_v8.jsonl';cq=OUT/'裁决候选参照来源核验-v8.json';assert read(cq)['candidate_sha256']==sha(cp)
        refs['third_agent_candidate']=jsonl(cp);paths +=[cp,cq]
        rule,rb,rpaths=rule_binding();llm,lb,lpaths=llm_binding();old,ob,op=old_bindings()
        machines={rb['method']:rule,lb['method']:llm,**old};bindings={rb['method']:rb,lb['method']:lb,**ob};paths+=rpaths+lpaths+op
        for method,data in machines.items():
            for reference,right in refs.items():pairs.append((method,reference,data,right))
    before={str(path):sha(path)for path in set(paths)};records=[];cache={}
    for method,reference,left,right in pairs:
        for component in('probability_base','enriched_challenge'):
            for group in('ALL',)+GROUPS:
                ids=[rid for rid,s in ctx['sample'].items()if rid not in excluded and s['component']==component and(group=='ALL'or s['group']==group)]
                for d in DIMS:
                    matrix,valid=cells(left,right,d,ids);assert valid.all()
                    counts=matrix.sum(axis=0);point=metrics(counts)[0];names=('kappa','agreement','left_positive_rate','right_positive_rate')if method=='A_C'else METRIC_NAMES
                    cis={}
                    for mechanism in('department_unit_conditional_WR','department_source_file_conditional_WR'):
                        key=(component,group,mechanism,tuple(ids))
                        if key not in cache:cache[key]=conditional_factors(ctx,ids,mechanism)
                        boot=metrics(cache[key]@matrix);cis[mechanism]={name:interval(boot[:,j])for j,name in enumerate(METRIC_NAMES)}
                    records.append({'component':component,'group':group,'weighting':'unweighted_conditional_deleted_text_subset','method':method,'reference':reference,'dimension':d,
                        'paired_n':len(ids),'left_positive_n':int(counts[0]+counts[1]),'reference_positive_n':int(counts[0]+counts[2]),
                        'raw_confusion':dict(zip(('TP','FP','FN','TN'),map(int,counts))),
                        'metrics':{name:{'estimate':safe(point[METRIC_NAMES.index(name)]),
                            'ci95_conditional_unit_WR':cis['department_unit_conditional_WR'][name],
                            'ci95_conditional_source_file_WR':cis['department_source_file_conditional_WR'][name]}for name in names},
                        'point_0_80_diagnostics':{name:('undefined'if not np.isfinite(point[METRIC_NAMES.index(name)])else'at_least_0_80'if point[METRIC_NAMES.index(name)]>=.8 else'below_0_80')for name in(('kappa',)if method=='A_C'else('kappa','precision','recall','f1'))}})
    attention=[]
    available={**refs}
    if args.stage=='final':available.update(machines)
    for method,data in available.items():
        for group in('ALL',)+GROUPS:
            ids=[rid for rid,s in ctx['sample'].items()if rid not in excluded and s['component']=='probability_base'and(group=='ALL'or s['group']==group)]
            counts={d:sum(label(data[rid],d)for rid in ids)for d in DIMS};total=sum(counts.values())
            q={d:counts[d]/total if total else None for d in DIMS}
            attention.append({'method':method,'group':group,'n':len(ids),'dimension_hit_counts':counts,'five_hit_denominator':total,'shares':q,
                'rank_tiers':None if not total else[[d for d in DIMS if counts[d]==v]for v in sorted(set(counts.values()),reverse=True)]})
    stem=f'正文重复剔除-{args.reference_version}-'+('最终机器与参照'if args.stage=='final'else'A_C预览')
    report={'status':'completed_conditional_text_deletion_sensitivity','created_at':datetime.datetime.now().astimezone().isoformat(),
        'reference_version':args.reference_version,'new_LLM_partial_or_fallback_used':False,'excluded_n':20,'excluded_original_ids':sorted(excluded),'probability_remaining_n':222,'challenge_remaining_n':58,
        'original240_and60_results_and_design_unchanged':True,'human_validation_completed':False,
        'scope':'Descriptive subset after deleting known development-normalized-text matches. No original fixed-design/FPC/eligible-frame representativeness claim. Unit and sampled-file WR intervals condition on observed labels and subset only. ID-disjointness did not establish text-unseen external validation.',
        'source_normalization':'Independent audit uses NFKC and removes all Unicode P* punctuation and whitespace. Audit exact matches retained; no score-driven deletions.',
        'original_weights_not_reused_as_design_weights':True,'bootstrap_repetitions':B,'base_seed':BASE_SEED,'method_bindings':bindings,'records':records,
        'probability_deleted_subset_attention':attention,'source_sha256':before}
    write_json(OUT/(stem+'.json'),report);assert before=={p:sha(p)for p in before}
    print(json.dumps({'status':report['status'],'classification_records':len(records),'attention_vectors':len(attention),'remaining_probability':222,'remaining_challenge':58},ensure_ascii=False))

if __name__=='__main__':main()
