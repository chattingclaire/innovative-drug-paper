"""Reuse frozen census formulas after the new full rule result is received."""
import collections
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
BASE = ROOT / '07-statistics/full4481-attention-robustness-preparation-sol'
RECEIVED = ROOT / '06-coding/rule-full4481-v15-v17-received-root'
OLD = ROOT / '06-coding/rule-full4481-v11-v16-receipt-delta-merged-root'
PREVIOUS = ROOT / '06-coding/rule-full4481-v13b-sf-v16-delta-merged-root'
SOURCE = ROOT / '01-review/source-interface-v17-finite-source-addendum-root'
OLD_STATS = ROOT / '07-statistics/rule-v11-v16-conditional-attention-robustness-root'
OUTPUT = HERE / 'full-rule-impact'
DIMS = ('S', 'E', 'Ec', 'I', 'F')


def require(ok, why):
    if not ok:
        raise ValueError(why)


def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def load(path):
    return json.loads(Path(path).read_bytes())


def exact(binding):
    actual = bind(binding['path'])
    require(all(actual[k] == binding[k] for k in actual), 'Changed input: ' + binding['path'])


def sealed(directory, required):
    seal = load(directory / 'seal.json')
    files = {b['path']: b for b in seal['files']}
    for b in files.values():
        exact(b)
    for name in required:
        require(str((directory / name).resolve()) in files, 'Unsealed file: ' + name)
    return bind(directory / 'seal.json')


def rows(path):
    with Path(path).open() as f:
        return [json.loads(line) for line in f]


def save(path, value):
    with path.open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def rank(values):
    groups = []
    for d, value in sorted(((d, v) for d, v in values.items() if v is not None), key=lambda x: (-x[1], x[0])):
        if groups and abs(groups[-1]['value'] - value) < 1e-12:
            groups[-1]['dimensions'].append(d)
        else:
            groups.append({'value': value, 'dimensions': [d]})
    return {'groups': groups, 'undefined': [d for d, v in values.items() if v is None]}


def points(statistics):
    q, p = {}, {}
    for d in DIMS:
        v = statistics['dimensions'][d]
        q[d] = v.get('q_observed', v.get('q_mean_among_observed_positive_members'))
        p[d] = v.get('p_conditional_lower', v.get('p_mean_conditional_lower'))
    return {'q': q, 'p_observed_lower': p, 'q_rank': rank(q), 'p_rank': rank(p)}


def main():
    require(not OUTPUT.exists(), 'Do not overwrite an earlier impact analysis')
    core_path = BASE / 'full4481_attention_robustness.py'
    require(bind(core_path)['sha256'] == '9d7c3d98454faa41a40157aafb966d110dda40784e122651c0c8ac708b02d8dc', 'Frozen statistical formulas changed')
    spec = importlib.util.spec_from_file_location('unchanged_attention_core', core_path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    base_seal = sealed(BASE, ('input-bindings.json', 'unit-metadata.jsonl', 'source-entry-metadata.json', 'metadata-coverage.json'))
    frozen = load(BASE / 'input-bindings.json')
    for b in [frozen['entry'], *frozen['inputs'].values(), *frozen['prepared'].values()]:
        exact(b)
    received_seal = sealed(RECEIVED, ('predictions.jsonl', 'all-dimension-slots.jsonl', 'composite-status.json', 'execution-origin-lineage.jsonl'))
    status = load(RECEIVED / 'composite-status.json')
    require(status['status'] == load(RECEIVED / 'seal.json')['status'] == 'validated_complete_full4481_v17_not_adopted', 'Result has not passed full reception')
    require(status['actual_record_N'] == 4481 and status['actual_dimension_N'] == 22405 and status['technical_failure_dimension_N'] == 0, 'Incomplete or technically failed new result')
    require(status['actual_new_inference_record_N'] == 4481 and status['inherited_N'] == 0 and status['all4481_actually_inferred_under_candidate'] is True, 'Not the complete newly executed rule candidate')
    require(status['candidate_algorithm_version'] == 'joint-v15b-complete-repair-root', 'Unexpected candidate')
    common = bind(SOURCE / 'common-frame-bundles-v17.jsonl')
    require(status['source_common_v17'] == common, 'Result uses different source material')
    source_seal = load(SOURCE / 'output-seal.json')
    source_files = source_seal.get('files', source_seal.get('output_files', []))
    require(any(all(b.get(k) == common[k] for k in common) for b in source_files), 'Current complete source is not sealed')
    for b in source_files:
        exact(b)
    metadata = rows(BASE / 'unit-metadata.jsonl')
    bundles = rows(common['path'])
    predicted = rows(RECEIVED / 'predictions.jsonl')
    require(len(metadata) == len(bundles) == len(predicted) == 4481, 'Incomplete metadata/source/predictions')
    ids = [r['unit_id'] for r in metadata]
    require(len(set(ids)) == 4481, 'Duplicate source IDs')
    for meta, bundle, prediction in zip(metadata, bundles, predicted):
        source = bundle['source_record']
        require(meta['unit_id'] == source['id'] == prediction['id'], 'Source order changed')
        text = source['text']
        require(hashlib.sha256(text.encode()).hexdigest() == meta['exact_current_text_sha256'] and len(text) == meta['current_text_unicode_N'], 'Old statistical metadata no longer describes current text')
        require(not prediction['implementation_errors'] and set(prediction['labels']) == set(DIMS), 'Invalid new prediction')
    old_stats_seal = sealed(OLD_STATS, ('conditional-robustness.json',))
    old_stats = load(OLD_STATS / 'conditional-robustness.json')
    require(old_stats['inputs'] == frozen and old_stats['entry'] == frozen['entry'], 'Original statistics do not match the reused methods')
    comparisons = {}
    for name, directory in [('original_production_v11', OLD), ('previous_candidate_v13b', PREVIOUS)]:
        seal = sealed(directory, ('predictions.jsonl',))
        prior = rows(directory / 'predictions.jsonl')
        require([r['id'] for r in prior] == ids, 'Comparison baseline order differs')
        transitions = {d: collections.Counter() for d in DIMS}
        changes = []
        for a, b in zip(prior, predicted):
            require(not a['implementation_errors'], 'Failed baseline record')
            changed = {}
            for d in DIMS:
                av, bv = a['labels'][d], b['labels'][d]
                transitions[d][f'{av}->{bv}'] += 1
                if av != bv:
                    changed[d] = {'old': av, 'new': bv}
            if changed:
                changes.append({'id': a['id'], 'dimensions': changed})
        comparisons[name] = {'baseline_seal': seal, 'changed_record_N': len(changes), 'transitions': {d: dict(v) for d, v in transitions.items()}, 'changes': changes}
    OUTPUT.mkdir()
    facade = OUTPUT / 'statistical-inputs'
    facade.mkdir()
    for name in ('unit-metadata.jsonl', 'source-entry-metadata.json', 'metadata-coverage.json'):
        (facade / name).symlink_to(BASE / name)
    inputs = dict(frozen['inputs'])
    inputs['historical_rule_bounds_reference'] = inputs.pop('existing_bounds')
    inputs.update(bundles=common, material_seal=bind(SOURCE / 'output-seal.json'), predictions=bind(RECEIVED / 'predictions.jsonl'), rule_status=bind(RECEIVED / 'composite-status.json'), rule_seal=received_seal)
    rebound = dict(frozen, inputs=inputs)
    save(facade / 'input-bindings.json', rebound)
    save(facade / 'seal.json', {'files': [bind(facade / 'input-bindings.json')], 'self_excluded': True})
    m.HERE = facade
    m.analyze(OUTPUT / 'frozen-core-evaluation')
    actual = load(OUTPUT / 'frozen-core-evaluation/conditional-robustness.json')
    old_index = {(r['clock'], r['scenario'], tuple(r['group'])): r['statistics'] for r in old_stats['scenarios']}
    new_index = {(r['clock'], r['scenario'], tuple(r['group'])): r['statistics'] for r in actual['scenarios']}
    require(old_index.keys() == new_index.keys(), 'Scenario definitions changed')
    group_comparisons = []
    for key in old_index:
        if key[0] != 'policy_year':
            continue
        before, after = points(old_index[key]), points(new_index[key])
        group_comparisons.append({'scenario': key[1], 'group': list(key[2]), 'before': before, 'after': after,
            'q_change_percentage_points': {d: None if before['q'][d] is None or after['q'][d] is None else 100 * (after['q'][d] - before['q'][d]) for d in DIMS}})
    result = {'role': 'Complete rule candidate impact versus preserved original production; not independent accuracy acceptance or production adoption',
        'record_N': 4481, 'dimension_N': 22405, 'technical_failure_N': 0, 'lawful_null_N': status['lawful_null_N'],
        'unchanged_metadata_text_identity_checked_N': 4481, 'original_statistical_entry': bind(core_path),
        'formula_or_scenario_changes': False, 'classifier_calls': 0, 'model_calls': 0,
        'source_seal': bind(SOURCE / 'output-seal.json'), 'received_seal': received_seal,
        'original_statistics_seal': old_stats_seal, 'original_preparation_seal': base_seal,
        'label_comparisons': comparisons, 'policy_year_group_comparisons': group_comparisons,
        'new_complete_robustness': bind(OUTPUT / 'frozen-core-evaluation/conditional-robustness.json'),
        'formal_validation_complete': False, 'human_validation_complete': False, 'production_adopted': False}
    save(OUTPUT / 'impact.json', result)
    sealed(RECEIVED, ('predictions.jsonl', 'composite-status.json'))
    save(OUTPUT / 'seal.json', {'files': [bind(p) for p in sorted(OUTPUT.rglob('*')) if p.is_file()], 'self_excluded': True})
    print(json.dumps({'output': str(OUTPUT), 'changed_record_N': {k: v['changed_record_N'] for k, v in comparisons.items()}, 'lawful_null_N': status['lawful_null_N']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
