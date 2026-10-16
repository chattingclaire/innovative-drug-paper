"""Five separate attention shares and paired conditional source-file bootstrap gaps."""
import argparse,csv,datetime
from fractions import Fraction
from itertools import combinations
from statistical_core import *
from current_material_context import load_current_context
from final_machine_contract import rule_binding,llm_binding,old_bindings

CURRENT_RULE='rules_v32_1_material_v8'
CURRENT_LLM='llm_v31_IF_v30_SEEc_material_v8'

def vector(data,ids):
    return np.asarray([[label(data[rid],d) for d in DIMS] for rid in ids],dtype=float)

def share_boot(hits):
    hits=np.asarray(hits,dtype=float);total=hits.sum(axis=-1,keepdims=True)
    return np.divide(hits,total,out=np.full_like(hits,np.nan),where=total>0)

def ranks(q):
    if any(q[d] is None for d in DIMS):return None
    values=sorted(set(q.values()),reverse=True)
    return [[d for d in DIMS if q[d]==v] for v in values]

def exact_summary(data,ids,weights=None):
    if weights is None:weights=[Fraction(1)]*len(ids)
    counts={d:sum((w*label(data[rid],d) for rid,w in zip(ids,weights)),Fraction()) for d in DIMS}
    total=sum(counts.values(),Fraction());exact={d:counts[d]/total if total else None for d in DIMS}
    return {'unit_n':len(ids),'positive_unit_n':sum(any(label(data[rid],d) for d in DIMS) for rid in ids),
        'dimension_hit_counts':{d:float(v) for d,v in counts.items()},'five_dimension_hit_denominator':float(total),
        'shares':{d:None if exact[d] is None else float(exact[d]) for d in DIMS},
        'exact_share_fractions':{d:None if exact[d] is None else str(exact[d]) for d in DIMS},'rank_tiers':ranks(exact)}

def probability_records(ctx,data,method):
    records=[]
    for group,kind in groups_and_weights('probability_base'):
        ids=[rid for rid,s in ctx['sample'].items() if s['component']=='probability_base' and(group=='ALL' or s['group']==group)]
        weights=[Fraction(1) if kind=='unweighted' else Fraction(ctx['sample'][rid]['eligible_N'],80) for rid in ids]
        r=exact_summary(data,ids,weights);r.update(method=method,group=group,weighting=kind,
            component='probability_base',scope='Development-ID-excluded eligible frame only; text-family leakage audited separately; no full-corpus human estimate.')
        factors=replicate_factors(ctx,ids,'probability_base','department_unit_rescaled_SRSWOR')
        boot=share_boot((factors*np.asarray(list(map(float,weights))))@vector(data,ids))
        r['ci95_approximate_unit_design']={d:interval(boot[:,j]) for j,d in enumerate(DIMS)}
        records.append(r)
    return records

def department_direction(summaries):
    result=[]
    for left,right in combinations(GROUPS,2):
        for d in DIMS:
            l=summaries[left]['exact_share_fractions'][d];r=summaries[right]['exact_share_fractions'][d]
            gap=None if l is None or r is None else Fraction(l)-Fraction(r)
            result.append({'left_department':left,'right_department':right,'dimension':d,
                'left_minus_right':None if gap is None else float(gap),'sign':None if gap is None else int(gap>0)-int(gap<0)})
    return result

def equal_summary(ctx,data,ids,key):
    pieces={}
    for rid in ids:
        stem=ctx['inputs'][rid]['input']['original_file_stem'];meta=ctx['metadata'][stem]
        cluster=stem if key=='policy_file' else meta['policy_series']
        pieces.setdefault(cluster,[]).append(rid)
    active=[];excluded=[]
    for name,unitids in sorted(pieces.items()):
        r=exact_summary(data,unitids)
        if r['five_dimension_hit_denominator']>0:active.append(r)
        else:excluded.append(name)
    exact={d:sum((Fraction(r['exact_share_fractions'][d]) for r in active),Fraction())/len(active) if active else None for d in DIMS}
    return {'unit_n':len(ids),'weighting':'mean_of_within_cluster_share_vectors',
        'cluster_key':key,'clusters_total':len(pieces),'clusters_active':len(active),'zero_hit_excluded_clusters':excluded,
        'shares':{d:None if exact[d] is None else float(exact[d]) for d in DIMS},
        'exact_share_fractions':{d:None if exact[d] is None else str(exact[d]) for d in DIMS},'rank_tiers':ranks(exact)}

def paired_file_bootstrap(ctx,rule,llm):
    records=[];source_bindings=[]
    for group in GROUPS:
        ids=[rid for rid,g in ctx['groups'].items() if g==group];files=sorted({ctx['sources'][rid] for rid in ids})
        sums=[]
        for method,data in [('rule',rule),('llm',llm)]:
            arr=np.stack([vector(data,[rid for rid in ids if ctx['sources'][rid]==f]).sum(axis=0) for f in files])
            sums.append(arr)
        rng=np.random.default_rng(seed('full_corpus_paired_source_file',group));k=len(files)
        multiplicity=rng.multinomial(k,np.repeat(1/k,k),size=B)
        rb=share_boot(multiplicity@sums[0]);lb=share_boot(multiplicity@sums[1]);delta=(rb-lb)*100
        r=exact_summary(rule,ids);l=exact_summary(llm,ids)
        for j,d in enumerate(DIMS):
            diff=100*(r['shares'][d]-l['shares'][d]);ci=interval(delta[:,j])
            records.append({'group':group,'dimension':d,'unit_n':len(ids),'source_file_cluster_n':k,
                'rule_share':r['shares'][d],'LLM_share':l['shares'][d],
                'rule_minus_LLM_percentage_points':diff,'ci95_paired_difference_percentage_points':ci,
                'rule_share_ci95_conditional_file':interval(rb[:,j]),'LLM_share_ci95_conditional_file':interval(lb[:,j]),
                'ci_contains_zero':None if ci['low'] is None else ci['low']<=0<=ci['high'],
                'equivalence_margin_prespecified':False,'equivalence_test_performed':False})
        source_bindings.append({'group':group,'source_file_cluster_names':files,'n':k,
            'seed':seed('full_corpus_paired_source_file',group),'both_methods_share_same_multiplicities':True})
    return records,source_bindings

def main():
    p=argparse.ArgumentParser();p.add_argument('--stage',choices=['rule_only','final'],required=True);args=p.parse_args()
    ctx=load_current_context();rule,rb,rpaths=rule_binding();machines={rb['method']:rule};bindings={rb['method']:rb}
    paths=ctx['source_paths']+rpaths+[Path(__file__)]
    if args.stage=='final':
        llm,lb,lpaths=llm_binding();machines[lb['method']]=llm;bindings[lb['method']]=lb;paths+=lpaths
    old,ob,op=old_bindings();machines.update(old);bindings.update(ob);paths+=op
    refs={name:jsonl(RUN/f'reference/agent_{name}_final_v8.jsonl') for name in ('A','C')}
    cp=OUT/'adjudicated_agent_reference_candidate_v8.jsonl';cq=OUT/'裁决候选参照来源核验-v8.json'
    assert read(cq)['candidate_sha256']==sha(cp);refs['third_agent_candidate']=jsonl(cp)
    paths += [RUN/f'reference/agent_{name}_final_v8.jsonl' for name in ('A','C')]+[cp,cq]
    before={str(path):sha(path) for path in set(paths)}
    probability=[]
    for method,data in {**machines,**refs}.items():probability+=probability_records(ctx,data,method)
    full={}
    for method,data in machines.items():
        full[method]={g:exact_summary(data,[rid for rid,dept in ctx['groups'].items() if dept==g]) for g in GROUPS}
        assert sum(r['unit_n'] for r in full[method].values())==4481
    current={m:data for m,data in machines.items() if not m.startswith('old_')}
    stems=sorted({ctx['inputs'][rid]['input']['original_file_stem'] for rid,g in ctx['groups'].items() if g in GROUPS});assert len(stems)==51
    cases=[('primary',None,None),('policy_file_equal','policy_file',None),('policy_series_equal','policy_series',None)]+[(f'leave_one_policy_entry:{stem}',None,stem) for stem in stems]
    robustness=[]
    for case,equal_key,omit in cases:
        per_method={}
        for method,data in current.items():
            groups={}
            for group in GROUPS:
                ids=[rid for rid,g in ctx['groups'].items() if g==group and ctx['inputs'][rid]['input']['original_file_stem']!=omit]
                groups[group]=equal_summary(ctx,data,ids,equal_key) if equal_key else exact_summary(data,ids)
            per_method[method]={'departments':groups,'same_dimension_department_directions':department_direction(groups)}
        agreement=None;different=[]
        if len(current)==2:
            m1,m2=current.keys();a=per_method[m1]['same_dimension_department_directions'];b=per_method[m2]['same_dimension_department_directions']
            agreement=sum(x['sign']==y['sign'] for x,y in zip(a,b));different=[{'rule_direction':x,'LLM_direction':y} for x,y in zip(a,b) if x['sign']!=y['sign']]
        robustness.append({'case':case,'omitted_policy_entry':omit,'methods':per_method,'consistent_same_dimension_department_directions_n':agreement,'possible_directions_n':15,'inconsistent_directions':different})
    differences=[];clusters=[]
    if args.stage=='final':differences,clusters=paired_file_bootstrap(ctx,rule,llm)
    notes=analysis_notes();notes.update({
        'attention_definition':'For each method and department, q_d=sum_i w_i label_id / sum_i w_i sum_{k in five dimensions}label_ik. Five shares sum to1 when denominator>0. This is attention-share allocation, not percent of all units positive.',
        'no_composite_indicator':'All five dimensions are reported individually. No S+E aggregate or new compound indicator.',
        'full_corpus_scope':'Machine descriptive allocation over all4481 three-professional-department units, excluding443 GOV units. No human full-corpus estimates.',
        'paired_gap_interval':'Within each department, resample observed source files with replacement5000 times using the SAME file multiplicities for both completed methods. Recompute each method own five-hit denominator and subtract rule−LLM, in percentage points. Conditional composition-sensitivity intervals, not exact finite-population design intervals, semantic measurement-error intervals or tests of equivalence.',
        'sample_interval':'240-probability sample share intervals use the same nonnegative finite-population rescaled unit factors as classification. Eligible frame2962, fixed agent/model labels, approximate nonlinear ratio percentile intervals.',
        'robustness':'54 finite recodings-free summaries: primary, within-policy-file share vectors equally averaged, within-policy-series share vectors equally averaged, and51 leave-one-policy-entry-out cases. Zero-hit clusters explicitly excluded from equal-share averages.',
        'no_equivalence_claim':'No prespecified equivalence margin. A difference interval containing0 does not prove equivalence; excluding0 does not establish practical unacceptability.'})
    stem='最终五维注意力与配对差值' if args.stage=='final' else '规则阶段五维注意力'
    report={'status':'completed_final_machine_attention' if args.stage=='final' else 'completed_rule_stage_new_LLM_not_included',
        'created_at':datetime.datetime.now().astimezone().isoformat(),'human_validation_completed':False,'source_material_version':ctx['final_material_version'],
        'final_source_reread_sample_ids':ctx['final_source_reread_sample_ids'],
        'analysis_notes':notes,'method_bindings':bindings,'probability_sample_attention':probability,'full_4481_attention':full,
        'paired_full_corpus_rule_minus_LLM_difference_CIs':differences,'paired_cluster_bootstrap_bindings':clusters,
        'robustness_case_n':len(robustness),'robustness':robustness,'source_sha256':before}
    write_json(OUT/(stem+'.json'),report)
    with (OUT/(stem+'-概率样本.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        fields=['method','group','weighting','unit_n','five_dimension_hit_denominator','dimension','q','q_CI_low','q_CI_high'];w=csv.DictWriter(f,fields);w.writeheader()
        for r in probability:
            for d in DIMS:w.writerow({**{k:r[k] for k in fields if k in r},'dimension':d,'q':r['shares'][d],'q_CI_low':r['ci95_approximate_unit_design'][d]['low'],'q_CI_high':r['ci95_approximate_unit_design'][d]['high']})
    with (OUT/(stem+'-全量配对差值.csv')).open('w',encoding='utf-8-sig',newline='') as f:
        fields=['group','dimension','unit_n','source_file_cluster_n','rule_share','LLM_share','rule_minus_LLM_percentage_points','paired_CI_low_pp','paired_CI_high_pp'];w=csv.DictWriter(f,fields);w.writeheader()
        for r in differences:w.writerow({**{k:r[k] for k in fields if k in r},'paired_CI_low_pp':r['ci95_paired_difference_percentage_points']['low'],'paired_CI_high_pp':r['ci95_paired_difference_percentage_points']['high']})
    assert before=={path:sha(path) for path in before}
    print(json.dumps({'status':report['status'],'sample_attention_vectors':len(probability),'paired_dimension_gaps':len(differences),'robustness_cases':len(robustness)},ensure_ascii=False))

if __name__=='__main__':main()
