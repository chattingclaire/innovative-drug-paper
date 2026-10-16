"""Reproducible label-free frame QA and synthetic statistical checks."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
from itertools import product
import hashlib
import json
import random
import numpy as np
import statistical_core_r3 as c
import statistical_extensions_r3 as e
import reference_bindings_r3 as b
from stability_r3 import summarize_stability

RUN = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent


def read(p):
    return json.loads(p.read_text())


def main():
    design = read(RUN/'admin/confirmation_sampling_PRIVATE.json')
    freeze = read(RUN/'admin/confirmation_sampling_freeze.json')
    frame = read(RUN/'admin/confirmation_canonical_frame_PRIVATE.json')
    mapping = read(RUN/'admin/PRIVATE_mapping.json')
    for name,key in [('confirmation_sampling_PRIVATE.json','design_sha256'),
                     ('confirmation_canonical_frame_PRIVATE.json','frame_sha256'),
                     ('PRIVATE_mapping.json','mapping_sha256'),
                     ('confirmation_exclusion_evidence_PRIVATE.json','exclusion_evidence_sha256')]:
        assert c.sha(RUN/'admin'/name) == freeze[key]
    sample = {r['original_id']:r for r in design['sample']}
    assert len(sample)==240
    assert design['frame_N_by_group']==c.EXPECTED_ELIGIBLE
    assert all(len(frame['frame_by_group'][g])==c.EXPECTED_ELIGIBLE[g] for g in c.GROUPS)
    assert all(r['canonical_id']==min(r['all_remaining_family_members'])
               for rows in frame['frame_by_group'].values() for r in rows)
    expected = Counter({('probability_canonical',g):60 for g in c.GROUPS}
                       | {('enriched_challenge',g):30 for g in ('NMPA','NHSA')})
    assert Counter((r['component'],r['group']) for r in sample.values())==expected
    rng=random.Random(design['seed'])
    replay=[]
    for g in c.GROUPS:
        replay += rng.sample(sorted(r['canonical_id'] for r in frame['frame_by_group'][g]),60)
    ids=[r['original_id'] for r in design['sample'] if r['component']=='probability_canonical']
    assert replay==ids
    weights={}
    for g in c.GROUPS:
        group=[r for r in sample.values() if r['component']=='probability_canonical' and r['group']==g]
        N=c.EXPECTED_ELIGIBLE[g]
        assert all(r['sample_n']==60 and r['canonical_frame_N']==N
                   and abs(r['analysis_weight']-N/60)<1e-12
                   and abs(r['inclusion_probability']-60/N)<1e-12 for r in group)
        weights[g]={'N':N,'n':60,'inclusion_probability':60/N,'weight':N/60,
                    'sample_weight_sum':sum(r['analysis_weight'] for r in group)}
        assert np.isclose(weights[g]['sample_weight_sum'],N)
    assert all(r['analysis_weight'] is None and r['inclusion_probability'] is None
               for r in sample.values() if r['component']=='enriched_challenge')
    assert len({(r['coder'],r['blind_id']) for r in mapping})==480
    assert all({r['original_id'] for r in mapping if r['coder']==coder}==set(sample) for coder in 'AC')
    ctx={'sample':sample,'sources':{rid:sample[rid]['group']+'-synthetic-source' for rid in ids}}
    factors=c.replicate_factors(ctx,ids,'probability_canonical','department_unit_rescaled_SRSWOR')
    assert np.array_equal(factors,c.replicate_factors(ctx,ids,'probability_canonical','department_unit_rescaled_SRSWOR'))
    variance_checks={}
    for g in c.GROUPS:
        positions=[i for i,rid in enumerate(ids) if sample[rid]['group']==g]
        f=factors[:,positions]
        assert np.allclose(f.sum(axis=1),60,atol=1e-11) and f.min()>=0
        if g=='NHC':
            assert np.array_equal(f,np.ones_like(f))
        y=np.arange(60,dtype=float)/59
        expected_var=(1-60/c.EXPECTED_ELIGIBLE[g])*np.var(y,ddof=1)/60
        observed_var=float(np.var(f@y/60,ddof=1))
        assert np.isclose(observed_var,expected_var,rtol=.07,atol=1e-20)
        variance_checks[g]={'analytic_SRSWOR_mean_variance':expected_var,
                            'replicate_variance':observed_var}
    # Hand-computed mixed cells and corner cases: all0, all1, no predicted1,
    # no reference1 and no paired observations; zero denominators stay NA.
    mixed=c.metrics([8,2,3,7])[0]
    assert np.allclose(mixed[:5],[.5,.75,.8,8/11,16/21])
    zero=c.metrics([0,0,0,20])[0]
    assert np.isnan(zero[[0,2,3,4]]).all() and zero[1]==1
    one=c.metrics([20,0,0,0])[0]
    assert np.isnan(one[0]) and np.all(one[1:5]==1)
    assert np.isnan(c.metrics([0,0,2,18])[0][2])
    assert np.isnan(c.metrics([0,2,0,18])[0][3])
    assert np.isnan(c.metrics([0,0,0,0])).all()
    assert np.isnan(e.attention_share(np.zeros(5))).all()
    assert np.isclose(e.attention_share([1,2,3,4,5]).sum(),1)
    # Enumerate every binary completion for random small missing patterns.
    synth=np.random.default_rng(2026100733)
    for _ in range(200):
        t=synth.integers(0,3,5);m=synth.integers(0,2,5)
        bounds=e.missing_share_bounds(t,m)
        possible=[]
        for v in product((0,1),repeat=int(m.sum())):
            x=np.zeros(5);x[np.flatnonzero(m)]=v
            if (t+x).sum():possible.append(e.attention_share(t+x))
        if possible:
            actual=np.asarray(possible)
            assert all(np.isclose(bounds[j]['low'],actual[:,j].min())
                       and np.isclose(bounds[j]['high'],actual[:,j].max()) for j in range(5))
        else:assert all(x=={'low':None,'high':None} for x in bounds)
    # The binding merger copies sources and never overwrites first judgments.
    original={'x':{'row':{'id':'AV3-A-0001','labels':dict.fromkeys(c.DIMS,0)},
                   'provenance':{'material_version':'v9'}}}
    reread=deepcopy(original);reread['x']['row']['labels']['F']='待定'
    reread['x']['provenance']['material_version']='v11'
    before=deepcopy(original)
    final,audit=b.merge_coder([original],[reread],['x'],['x'])
    assert original==before and final['x']['id']=='x' and final['x']['blind_id']=='AV3-A-0001'
    assert final['x']['labels']['F']=='待定' and audit['x']['label_change_dimensions']==['F']
    assert b.require_symmetric_reread(audit,audit,['x'])
    rejected=False
    try:b.merge_coder([original],[reread],['x'],[])
    except ValueError:rejected=True
    assert rejected
    # Synthetic repeatability report: two stable runs and one flipped dimension.
    stable_ids=[f's{i}' for i in range(75)]
    gs={rid:('NMPA' if i<20 else 'NHSA' if i<42 else 'NHC' if i<72 else 'GOV')
        for i,rid in enumerate(stable_ids)}
    run={rid:{'labels':{d:int((i+j)%3==0) for j,d in enumerate(c.DIMS)}}
         for i,rid in enumerate(stable_ids)}
    changed=deepcopy(run);changed['s0']['labels']['F']=1-changed['s0']['labels']['F']
    report=summarize_stability({'production':run,'repeat1':run,'repeat2':changed},stable_ids,gs)
    assert report['records'][0]['actual_id_n']==72
    assert report['records'][-1]['actual_id_n']==75
    assert report['records'][0]['three_run_dimensions']['F']['label_varies_n']==1
    qa={'status':'pass_label_free_frame_and_synthetic_mathematical_QA',
        'new_coder_or_machine_labels_read':False,'weights':weights,
        'canonical_frame_total_N':sum(c.EXPECTED_ELIGIBLE.values()),
        'probability_n':180,'challenge_n':60,'mapping_rows':480,
        'probability_seed_replay_matches':True,'NHC_factors_strictly_one':True,
        'SRSWOR_n_minus_one_formula_checked':True,'synthetic_variance_checks':variance_checks,
        'zero_denominator_NA_checks_pass':True,'missing_share_bounds_enumeration_checks':200,
        'first_submission_nonmutation_and_explicit_reread_checks_pass':True,
        'three_run_stability_scope_and_flip_check_pass':True,
        'code_sha256':{p.name:c.sha(p) for p in OUT.glob('*.py')},
        'primary_source_crosscheck':{'url':'https://github.com/bschneidr/svrep/blob/main/R/make_bootstrap_weights.R',
            'implementation':'make_rwyb_bootstrap_weights',
            'details':'m_h=n_h−1; a_k=1−sqrt(m_h(1−pi_k)/(n_h−1))+sqrt(m_h(1−pi_k)/(n_h−1))(n_h/m_h)M_k; equivalent to core formula for equal pi.'},
        'limits':['No r3 labels or machine outputs inspected. This verifies arithmetic, frozen frame metadata and synthetic edge cases, not semantic correctness.',
                  'Percentile nonlinear intervals are approximate; degenerate census/rare-class intervals do not measure semantic uncertainty.',
                  'Missing dimensions are excluded only on declared paired support; no automatic imputation.',
                  'Challenge NHC is absent, not a sampled zero-positive stratum. Skip absent group in q analysis.',
                  'Source-file WR is composition sensitivity, separate from primary SRSWOR intervals.']}
    target=OUT/'数学与框权重独立QA-r3.json'
    target.write_text(json.dumps(qa,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':qa['status'],'qa_path':str(target),'labels_read':False},ensure_ascii=False))


if __name__=='__main__':main()
