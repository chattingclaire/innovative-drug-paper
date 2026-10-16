"""Attention shares, department contrasts and declared file-composition checks."""
from itertools import combinations
import numpy as np
import statistical_core_r3 as c
import statistical_extensions_r3 as e


def vector(rows,ids):
    return np.asarray([[c.label(rows[rid],d) for d in c.DIMS] for rid in ids],float)


def ranks(q):
    return {d:1+int(sum(v>q[j]+1e-12 for v in q)) if np.isfinite(q[j]) else None
            for j,d in enumerate(c.DIMS)}


def full_summary(rows,ids):
    total=vector(rows,ids).sum(axis=0) if ids else np.zeros(5)
    q=e.attention_share(total)
    return {'unit_n':len(ids),'five_dimension_coding_count':float(total.sum()),
            'coding_count':dict(zip(c.DIMS,map(float,total))),
            'attention_share':dict(zip(c.DIMS,map(c.safe,q))),
            'within_department_rank':ranks(q)}


def probability_attention(ctx,all_rows):
    ids=sorted(rid for rid,row in ctx['sample'].items() if row['component']=='probability_canonical')
    common=e.common_complete_mask(list(all_rows.values()),ids)
    assert common.all(),'Final references/methods must resolve all sampled labels before final attention tables'
    cache={};profiles=[];paired=[]
    for group,kind in c.groups_and_weights('probability_canonical'):
        chosen=[rid for rid in ids if group=='ALL' or ctx['sample'][rid]['group']==group]
        for name,rows in all_rows.items():
            profiles.append(e.attention_profile(ctx,rows,chosen,'probability_canonical',group,kind,name,cache))
        relevant=[('rules','A'),('rules','C'),('rules','candidate'),('LLM','A'),('LLM','C'),
                  ('LLM','candidate'),('LLM','rules'),('A','C')]
        for one,two in relevant:
            diff=e.paired_attention_difference(ctx,all_rows[one],all_rows[two],chosen,
                'probability_canonical',group,kind,cache)
            paired.append({'group':group,'weighting':kind,'method_one':one,'method_two':two,**diff})
    # Department contrasts retain the original n60 strata and their independent
    # design replicates; they are descriptive differences with approximate CIs.
    mechanism='department_unit_rescaled_SRSWOR'
    factors=c.replicate_factors(ctx,ids,'probability_canonical',mechanism)
    w=c.weighting(ctx,ids,'eligible_design_weighted');department=[]
    for name,rows in all_rows.items():
        hits=vector(rows,ids);points={};boots={}
        for group in c.GROUPS:
            mask=np.asarray([ctx['sample'][rid]['group']==group for rid in ids])
            points[group]=e.attention_share(w[mask]@hits[mask])
            boots[group]=e.attention_share((factors[:,mask]*w[mask])@hits[mask])
        for one,two in combinations(c.GROUPS,2):
            delta=points[one]-points[two];rep=boots[one]-boots[two]
            department.append({'method':name,'department_one':one,'department_two':two,
                'difference_direction':'department_one_minus_department_two',
                'primary_bootstrap_mechanism':mechanism,'unit_frame_n_per_department':60,
                'dimensions':{d:{'difference_percentage_points':c.safe(100*delta[j]),
                                 'ci95_percentage_points':c.interval(100*rep[:,j])}
                              for j,d in enumerate(c.DIMS)}})
    return {'scope':'same180 probability canonical representatives; design weights N_h/60',
            'profiles':profiles,'paired_method_differences':paired,'department_differences':department,
            'interpretation':'Approximate design intervals condition on fixed judgments and algorithms; no equivalence test or publication threshold.'}


def file_equal_summary(ctx,rows,ids,key):
    clusters={}
    for rid in ids:
        stem=ctx['inputs'][rid]['input']['original_file_stem']
        cluster=stem if key=='policy_file' else ctx['metadata'][stem]['policy_series']
        clusters.setdefault(cluster,[]).append(rid)
    vectors=[];zero=[]
    for cluster,members in clusters.items():
        q=e.attention_share(vector(rows,members).sum(axis=0))
        if np.isfinite(q).all():vectors.append(q)
        else:zero.append(cluster)
    average=np.mean(vectors,axis=0) if vectors else np.full(5,np.nan)
    return {'unit_n':len(ids),'equal_cluster_n':len(clusters),'defined_cluster_n':len(vectors),
            'zero_hit_cluster_names_excluded_from_average':sorted(zero),
            'attention_share':dict(zip(c.DIMS,map(c.safe,average))),
            'within_department_rank':ranks(average)}


def full_machine_attention(ctx,methods,scenario_names):
    allowed={'primary','policy_file_equal','policy_series_equal','leave_one_policy_entry_out',
             'latest_annual_series_member','exclude_joint_publications'}
    assert set(scenario_names)<=allowed
    full={name:{g:full_summary(rows,[rid for rid in rows if ctx['groups'][rid]==g])
                for g in c.GROUPS} for name,rows in methods.items()}
    paired=[];cluster_bindings=[]
    for group in c.GROUPS:
        ids=[rid for rid in ctx['inputs'] if ctx['groups'][rid]==group]
        sources=sorted({ctx['sources'][rid] for rid in ids});k=len(sources)
        arrays={name:np.stack([vector(rows,[rid for rid in ids if ctx['sources'][rid]==source]).sum(axis=0)
                              for source in sources]) for name,rows in methods.items()}
        rng=np.random.default_rng(c.seed('full_corpus_paired_source_file',group))
        multiplicities=rng.multinomial(k,np.repeat(1/k,k),size=c.B)
        q_boot={name:e.attention_share(multiplicities@arr) for name,arr in arrays.items()}
        q_point={name:e.attention_share(arr.sum(axis=0)) for name,arr in arrays.items()}
        for j,dim in enumerate(c.DIMS):
            paired.append({'group':group,'dimension':dim,'unit_n':len(ids),'source_file_cluster_n':k,
                'difference_direction':'LLM_minus_rules','difference_percentage_points':c.safe(100*(q_point['LLM'][j]-q_point['rules'][j])),
                'ci95_source_file_conditional_percentage_points':c.interval(100*(q_boot['LLM'][:,j]-q_boot['rules'][:,j]))})
        cluster_bindings.append({'group':group,'source_names':sources,'seed':c.seed('full_corpus_paired_source_file',group)})
    stems=sorted({ctx['inputs'][rid]['input']['original_file_stem'] for rid in ctx['inputs'] if ctx['groups'][rid] in c.GROUPS})
    scenarios=[(name,None) for name in scenario_names if name!='leave_one_policy_entry_out']
    if 'leave_one_policy_entry_out' in scenario_names:scenarios.extend(('leave_one_policy_entry_out',stem) for stem in stems)
    latest={}
    for stem in stems:
        meta=ctx['metadata'][stem]
        if meta['annual_series']:
            year=meta['year_in_filename'];assert type(year) is int
            latest[meta['policy_series']]=max(latest.get(meta['policy_series'],year),year)
    robust=[]
    for scenario,omitted in scenarios:
        values={}
        for name,rows in methods.items():
            values[name]={}
            for group in c.GROUPS:
                ids=[]
                for rid in ctx['inputs']:
                    if ctx['groups'][rid]!=group:continue
                    stem=ctx['inputs'][rid]['input']['original_file_stem'];meta=ctx['metadata'][stem]
                    if stem==omitted:continue
                    if scenario=='exclude_joint_publications' and meta['joint_publication']:continue
                    if scenario=='latest_annual_series_member' and meta['annual_series'] and meta['year_in_filename']!=latest[meta['policy_series']]:continue
                    ids.append(rid)
                values[name][group]=(file_equal_summary(ctx,rows,ids,'policy_file' if scenario=='policy_file_equal' else 'policy_series')
                    if scenario in ('policy_file_equal','policy_series_equal') else full_summary(rows,ids))
        robust.append({'scenario':scenario,'omitted_policy_entry':omitted,'methods':values})
    return {'scope':'fixed complete three-department corpus4481; excludes GOV443',
            'primary':full,'paired_file_composition_sensitivity':paired,'cluster_bindings':cluster_bindings,
            'declared_robustness_scenarios':scenario_names,'robustness_case_n':len(robust),'robustness':robust,
            'interpretation':'Full-corpus shares describe fixed observed texts. Source-file resampling and recodings-free scenarios are composition sensitivity, separate from canonical-frame estimation and semantic-truth uncertainty.'}
