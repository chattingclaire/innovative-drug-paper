"""Compare a completed received v13b composite with the sealed v12 composite.

No classifier, source interpretation, metric, release or adoption is performed.
"""
import argparse
import json
from pathlib import Path
from merge_common import bind, exact, load, rows, save, seal, spans

if not __debug__:
    raise RuntimeError('Run without Python optimization; original checks remain active')

H = Path(__file__).resolve().parent
FIXED = ('E', 'Ec', 'I', 'F')


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def member(raw, key):
    return raw[slice(*spans(raw)[key])]


def compare(candidate_composite, output):
    contract = load(H / 'v12-comparison-contract.json')
    for entry in contract['baseline_bindings'].values():
        exact(entry)
    exact(contract['candidate_review'])
    old = Path(contract['baseline_composite'])
    new = Path(candidate_composite).resolve()
    require(str(new) == contract['expected_candidate_composite'], 'Unexpected candidate composite')
    require(not Path(output).exists(), 'Never overwrite a comparison')
    seal(old / 'seal.json')
    sealed = seal(new / 'seal.json')
    status = load(new / 'composite-status.json')
    require(sealed['status'] == status['status'] == 'complete_v13b_SF_v16_compatible_composite_with_explicit_execution_origins', 'Candidate not a completed received composite')
    require(status['candidate_algorithm_version'] == contract['candidate_version'], 'Candidate version differs')
    require(status['actual_record_N'] == 4481 and status['actual_dimension_N'] == 22405 and status['technical_failure_dimension_N'] == 0, 'Candidate coverage or technical failure differs')
    old_status = load(old / 'composite-status.json')
    require(status['parent_seal'] == old_status['parent_seal'], 'Comparisons do not share the actual v11 parent')
    require(status['static_impact_selection'] == old_status['static_impact_selection'], 'Original 2082 selection differs')
    require(status['prediction_binding'] == bind(new / 'predictions.jsonl'), 'Candidate predictions are not the received binding')
    before = rows(old / 'predictions.jsonl')
    after = rows(new / 'predictions.jsonl')
    require(len(before) == len(after) == contract['expected_record_N'] and list(before) == list(after), 'Complete ordered record coverage differs')
    changes = []
    for rid, (_, old_raw, old_row) in before.items():
        _, new_raw, new_row = after[rid]
        require(not old_row['implementation_errors'] and not new_row['implementation_errors'], 'Technical failure cannot become a decision')
        for dim in FIXED:
            require(old_row['labels'][dim] == new_row['labels'][dim], f'Protected label differs: {rid}/{dim}')
            require(old_row['decisions'][dim] == new_row['decisions'][dim], f'Protected complete decision differs: {rid}/{dim}')
            require(member(member(old_raw, 'decisions'), dim) == member(member(new_raw, 'decisions'), dim), f'Protected original decision token differs: {rid}/{dim}')
        if old_row['decisions']['S'] != new_row['decisions']['S']:
            changes.append({'id': rid, 'label_before': old_row['labels']['S'], 'label_after': new_row['labels']['S'], 'complete_S_decision_changed': True})
    result = {
        'status': 'complete_v13b_vs_completed_v12_non_S_decisions_equal',
        'record_N': len(before), 'protected_dimensions': list(FIXED),
        'protected_complete_decisions_and_original_JSON_tokens_equal': True,
        'S_decision_changed_N': len(changes), 'S_changes': changes,
        'baseline': contract['baseline_bindings'],
        'candidate_seal': bind(new / 'seal.json'),
        'candidate_predictions': bind(new / 'predictions.jsonl'),
        'comparison_contract': bind(H / 'v12-comparison-contract.json'),
        'comparison_code': bind(Path(__file__).resolve()),
        'new_inference_executed': False, 'production_adopted': False,
        'formal_validation_complete': False,
    }
    save(output, result)
    return {'status': result['status'], 'record_N': len(before), 'S_decision_changed_N': len(changes), 'output': bind(Path(output).resolve())}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--candidate-composite', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    print(json.dumps(compare(args.candidate_composite, args.output), ensure_ascii=False))
