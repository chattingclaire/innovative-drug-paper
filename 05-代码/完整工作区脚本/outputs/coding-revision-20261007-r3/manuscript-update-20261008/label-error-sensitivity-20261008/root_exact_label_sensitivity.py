"""Read-only deterministic label perturbation, not an error-rate estimate.

Cost is the number of changed units. An Ec/F edit can change either or both
bits on that unit. No original labels, text, sample, or manuscript is edited.
The three states joint / Ec-only / not-Ec suffice for P(F | Ec): the exact
minimum cost of a state-count change is half its L1 distance. The outside-Ec
F bit is free in the target, so the collapsed minimum is attainable.
"""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
import hashlib, json

HERE = Path(__file__).resolve().parent
M = HERE.parent
R3 = M.parent
read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
bindings = []

def bound(p, expected=None):
    p = Path(p).resolve()
    actual = sha(p)
    assert expected is None or actual == expected
    bindings.append({'path': str(p), 'sha256': actual})
    return p

def extreme(cells, budget, mode, maximize):
    joint, ec_only, outside = cells
    total, ec = sum(cells), joint + ec_only
    feasible = []
    denominators = [ec] if mode == 'fixed_Ec_F_only' else range(max(1, ec-budget), min(total, ec+budget)+1)
    for new_ec in denominators:
        for new_joint in range(max(0, joint-budget), min(new_ec, joint+budget)+1):
            target = (new_joint, new_ec-new_joint, total-new_ec)
            distance = sum(abs(x-y) for x, y in zip(cells, target))
            assert distance % 2 == 0
            cost = abs(new_joint-joint) if mode == 'fixed_Ec_F_only' else distance//2
            if cost <= budget:
                feasible.append((Q(new_joint,new_ec), cost, target))
    assert feasible
    value = (max if maximize else min)(x[0] for x in feasible)
    witness = min((x for x in feasible if x[0] == value), key=lambda x:(x[1],x[2]))
    return {'fraction':str(value), 'cost':witness[1], 'target_joint_EcOnly_outside':list(witness[2])}

def threshold(left, right, mode):
    # Left=NHC, right=NHSA. At each budget enumerate every split, including
    # edits to either department. Each side's extrema are exhaustive.
    curve = []
    for total_budget in range(0, min(left[0]+1, 21)):
        candidates = []
        for nhc_budget in range(total_budget+1):
            lo = extreme(left,nhc_budget,mode,False)
            hi = extreme(right,total_budget-nhc_budget,mode,True)
            candidates.append((Q(lo['fraction'])-Q(hi['fraction']), nhc_budget, lo, hi))
        best = min(candidates, key=lambda x:(x[0],x[1]))
        curve.append({'max_changed_units':total_budget,
                      'minimum_NHC_minus_NHSA':str(best[0]),
                      'budget_split_NHC_NHSA':[best[1],total_budget-best[1]],
                      'NHC':best[2],'NHSA':best[3]})
        if best[0] < 0:
            return {'minimum_units_to_erase_strict_NHC_higher':next(x['max_changed_units'] for x in curve if Q(x['minimum_NHC_minus_NHSA'])<=0),
                    'minimum_units_to_strictly_reverse':total_budget,
                    'exhaustive_budget_curve_until_strict_reversal':curve}
    raise AssertionError('No reversal within proven search range')

def main():
    config_path = bound(M/'measurement-adapter-v3/采用方法_ROOT_CONFIRMED-v6.json')
    cfg = read(config_path)
    manifest = read(bound(cfg['reference_manifest']['path'],cfg['reference_manifest']['sha256']))
    raw_inputs = [json.loads(s) for s in bound(manifest['material']['rule_inputs']['path'],manifest['material']['rule_inputs']['sha256']).read_text().splitlines() if s.strip()]
    metadata = read(bound(manifest['metadata']['path'],manifest['metadata']['sha256']))
    by_stem = {Path(x['original_file']).stem:x['analysis_group'] for x in metadata['rows']}
    groups = {x['id']:by_stem[x['input']['original_file_stem']] for x in raw_inputs}
    assert Counter(groups.values()) == {'NMPA':1848,'NHSA':2100,'NHC':533,'GOV':443}
    payload_path = bound(M/'measurement-adapter-v4/actual-payload-ready-v6-report-v5/manuscript_measurement_payload.json')
    payload = read(payload_path)
    results = {}
    for role in ('rules','LLM'):
        spec = cfg['methods'][role]['output']
        rows = [json.loads(s) for s in bound(spec['path'],spec['sha256']).read_text().splitlines() if s.strip()]
        labels = {x['id']:x.get('prediction',x)['labels'] for x in rows}
        assert len(labels)==len(rows)==4924 and labels.keys()==groups.keys()
        assert all(set(z)=={'S','E','Ec','I','F'} and all(type(v) is int and v in (0,1) for v in z.values()) for z in labels.values())
        quartet = {}
        for group in ('NHSA','NHC'):
            q = Counter((z['Ec'],z['F']) for rid,z in labels.items() if groups[rid]==group)
            quartet[group] = {'neither':q[0,0],'F_only':q[0,1],'Ec_only':q[1,0],'joint':q[1,1]}
            frozen = next(x for x in payload['figure2_data'] if x['method_role']==role and x['group']==group)
            assert all(frozen['Ec_F'][key]==value for key,value in quartet[group].items())
        collapsed = {g:(q['joint'],q['Ec_only'],q['neither']+q['F_only']) for g,q in quartet.items()}
        modes = {mode:threshold(collapsed['NHC'],collapsed['NHSA'],mode) for mode in ('fixed_Ec_F_only','allow_Ec_and_F_changed_unit_cost')}
        assert modes['fixed_Ec_F_only']['minimum_units_to_strictly_reverse']==modes['allow_Ec_and_F_changed_unit_cost']['minimum_units_to_strictly_reverse']
        needed = modes['fixed_Ec_F_only']['minimum_units_to_strictly_reverse']
        nhc = quartet['NHC']
        results[role] = {'actual_four_cells':quartet,'modes':modes,
                         'explicit_attainable_witness':{'operation':'NHC joint (Ec1,F1) -> Ec-only (Ec1,F0)',
                            'unit_count':needed,'NHC_after_fraction':str(Q(nhc['joint']-needed,nhc['joint']+nhc['Ec_only'])),
                            'fraction_of_original_NHC_Ec_units':str(Q(needed,nhc['joint']+nhc['Ec_only'])),
                            'fraction_of_original_NHC_joint_units':str(Q(needed,nhc['joint'])),
                            'fraction_of_all_NHC_units':str(Q(needed,533))}}
    report = {'status':'PASS_DETERMINISTIC_PERTURBATION_CALCULATED',
              'inputs':bindings,'script':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},
              'definition':'Minimum changed units needed to make NHC P(F|Ec) no longer exceed NHSA; exact finite counts, all budget splits enumerated, nonzero denominators.',
              'results':results,'labels_or_documents_modified':False,'human_labels_read':False,'future_human_material_read':False,
              'interpretation_limits':['Not an estimated error rate, probability, confidence interval or publication cutoff.',
                'Method-specific perturbation thresholds do not assert a common erroneous ID set across methods.',
                'A hypothetical changed unit is not a verified coding error; no recoding follows from this calculation.',
                'Shared codebook and machine agreement do not establish correctness against an independent human reference.']}
    out = HERE/'root_exact_label_sensitivity.json'
    assert not out.exists()
    out.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({r:{m:v['minimum_units_to_strictly_reverse'] for m,v in x['modes'].items()} for r,x in results.items()},ensure_ascii=False))

if __name__=='__main__': main()
