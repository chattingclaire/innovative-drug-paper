"""Verify the separate n=600 proposal against only frozen metadata."""
import json,hashlib,math
from pathlib import Path
import small_plan as s
import precision_plan as p

HERE=Path(__file__).resolve().parent
d=json.loads((HERE/'small-plan-comparison.json').read_text())
b=json.loads((HERE/'source-bindings.json').read_text())
f=HERE/'inputs/metadata-and-fixed-labels.jsonl'
assert p.sha(f)==b['projection']['sha256']
rows=[r for r in map(json.loads,f.open()) if r['exposure']=='remaining']
by={h['key']:h for h in d['strata']}
assert d['N']==1444 and d['n']==sum(h['n'] for h in by.values())==600
assert sum(h['N'] for h in by.values())==1444 and len(by)==23
for r in rows:
    h=by[s.layer(r)]
    assert 0<h['pi']<=1 and h['pi']==h['n']/h['N'] and h['weight']==h['N']/h['n']
    if any(r['rules39'][dim]!=r['LLM03'][dim] for dim in p.DIMS):assert h['census']
    if any(r[m][dim]==1 for m in p.METHODS for dim in ['I','F']):assert h['census']
assert sum(h['n'] for h in by.values() if h['tag']=='IF')==141
assert sum(h['n'] for h in by.values() if h['tag']=='OTHER_DISAGREEMENT')==102
assert all(h['n']>=2 or h['census'] for h in by.values())
assert not d['CI_halfwidth_gate_added'] and not d['CI_lower_bound_gate_added']
assert d['project_goals']['each_machine_per_dimension_kappa_precision_recall_F1_point']==.8
assert len(d['machine_joint_synthetic_scenarios'])==90
for case in d['machine_joint_synthetic_scenarios']:
    joint=case['joint_counts'];assert sum(x['N'] for x in joint)==1444
    assert sum(x['reference_positive'] for x in joint)==case['reference_positive_total']
    assert all(0<=x['reference_positive']<=x['N'] for x in joint)
    for m,result in case['machine_results'].items():
        cells=result['TP_FP_FN_TN'];assert sum(cells)==1444
        assert cells[0]+cells[2]==case['reference_positive_total']
        assert cells[0]+cells[1]==b['summary']['remaining_positive_counts'][m][case['dimension']]
        if case['dimension'] in ['I','F']:
            assert result['metrics']['precision']['linearized_95_halfwidth']==0
    assert all(-1e-12<=v<=1+1e-12 for v in case['raw_reference_positive_shortfall_probability'].values())
Nn=[(h['N'],h['n']) for h in by.values() if not h['census']]
guard=p.zero_error_upper(Nn,.025)
assert guard['maximum_unseen_count']==14
ind_path=HERE/'independent-review/small-plan-review.json'
ind=json.loads(ind_path.read_text())
out={'status':'passed','n':600,'strata':23,
     'all_old_IF_positive_and_all_old_machine_disagreements_census':True,
     'all_nonempty_layers_positive_probability':True,
     'all_90_joint_reference_scenes_capacity_and_margin_valid':True,
     'marginal_95_zero_one_category_upper':guard,
     'independent_review_path':str(ind_path),
     'no_new_CI_gate':True,'no_actual_sample_or_human_labels':True,
     'prior_report_sha256':p.sha(HERE/'precision-planning.md'),
     'prior_allocation_sha256':p.sha(HERE/'strata-planning.json'),
     'small_script_sha256':p.sha(HERE/'small_plan.py')}
(HERE/'small-plan-QA.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(out,ensure_ascii=False,indent=2))
