"""Prepare one bounded v8 repair pass from a sealed, complete v7 production run.

This is metadata preparation, not classification. No human reference is opened.
All records reaching the sole changed v7 branch are included, even if F was 1.
"""
from pathlib import Path
import ast, copy, datetime, hashlib, json

R = Path(__file__).resolve().parents[1]
PARENT = R / '06-coding/rule-full4481-final-v7-root'
CANDIDATE = R / '06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol'
OUT = R / '06-coding/rule-v8-bounded-delta-root'
VERSION = 'v8-bounded-original-common-delta-driver-1'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
BOUNDARY = '单品种未上市与按需优先机会'
BRANCH = "    if re.search('境外已上市[^。；;]{0,8}境内未上市', text) and opportunity and (not any((re.search(pattern, text) for pattern in GAPS.values()))):\n"
NEXT = "    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_IF_actual_support'"


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def bind(path):
    p = Path(path).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def verify(b):
    actual = bind(b['path'])
    assert all(actual[k] == b[k] for k in ('path', 'bytes', 'sha256')), b['path']
    return Path(b['path']).read_bytes()


def load(p):
    return json.loads(Path(p).read_bytes())


def save(p, value):
    with Path(p).open('x', encoding='utf8') as s:
        json.dump(value, s, ensure_ascii=False, indent=2, allow_nan=False); s.write('\n')


def all_references(value):
    if isinstance(value, dict):
        if value.get('reference') == BOUNDARY:
            yield value
        for v in value.values():
            yield from all_references(v)
    elif isinstance(value, list):
        for v in value:
            yield from all_references(v)


def replace_once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)


def main():
    assert not OUT.exists(), 'Do not overwrite any prior prepared or actual run'
    delivery_path = CANDIDATE / 'output-seal.json'
    delivery = load(delivery_path)
    members = delivery.get('files', delivery.get('members', delivery.get('output_files', [])))
    assert members, 'Final candidate must have an actual enumerated delivery seal'
    for b in members:
        p = Path(b.get('path', b.get('relative_path', '')))
        if not p.is_absolute(): p = CANDIDATE / p
        actual = bind(p)
        assert actual['bytes'] == b['bytes'] and actual['sha256'] == b['sha256'], p
    parent_run = PARENT / 'run4481-first'
    parent_seal = load(parent_run / 'seal.json')
    for k in ('implementation_files', 'material_bindings', 'control_inputs', 'output_files'):
        for b in parent_seal[k]: verify(b)
    execution = load(parent_run / 'execution.json')
    assert execution['status'] == 'completed' and execution['actual_record_N'] == 4481
    assert execution['actual_dimension_N'] == 22405 and execution['technical_failure_dimension_N'] == 0
    assert parent_seal['record_N'] == 4481 and parent_seal['source_packet_unchanged']
    parent_alg = load(PARENT / 'algorithm-bindings.json')
    old_modules = {b['module']: Path(b['path']) for b in parent_alg['modules']}
    for name in ('source_packet', 'source_receipts', 'evidence', 'relations'):
        assert old_modules[name].read_bytes() == (CANDIDATE / (name + '.py')).read_bytes(), name
    old = old_modules['dimensions'].read_text(); new = (CANDIDATE / 'dimensions.py').read_text()
    assert old.count(BRANCH) == new.count(BRANCH) == 1
    start = old.index(BRANCH) + len(BRANCH); end = old.index(NEXT, start)
    ns = new.index(BRANCH) + len(BRANCH); ne = new.index(NEXT, ns)
    assert old[:start] == new[:ns] and old[end:] == new[ne:]
    restored = new[:ns] + old[start:end] + new[ne:]
    assert ast.dump(ast.parse(restored), include_attributes=False) == ast.dump(ast.parse(old), include_attributes=False)
    static = load(CANDIDATE / 'static-impact-proof.json')
    for k in ('four_non_dimension_modules_byte_identical', 'dimensions_prefix_suffix_outside_original_if_body_byte_identical', 'all_AST_identical_after_restoring_only_old_if_body', 'outer_branch_condition_byte_and_AST_identical'):
        assert static[k] is True, k
    scope = load(PARENT / 'frozen-scope.json')
    rows = [json.loads(x) for x in (parent_run / 'predictions.jsonl').read_bytes().splitlines()]
    assert [x['id'] for x in rows] == scope['approved_record_ids'] and len(rows) == 4481
    affected = []; retention = []
    for row in rows:
        assert not row['implementation_errors'] and set(row['decisions']) == set(DIMS)
        assert set(row['labels']) == set(DIMS)
        for d in DIMS:
            dec = row['decisions'][d]
            assert dec['value'] in (0, 1, None) and row['labels'][d] == dec['value']
        f = row['decisions']['F']
        if f['value'] == 1:
            assert isinstance(f['details']['unresolved_semantic_boundaries'], list)
        if f['value'] is None and f['basis_path'] == 'manual_relation_boundary':
            assert isinstance(f['needed_material'], list)
            assert f['needed_material'] == f['rule_conflict']['boundary_requests']
        hits = list(all_references(f))
        # Broad text readback catches unexpected serialization or lossy projections.
        assert bool(hits) == (BOUNDARY in json.dumps(row, ensure_ascii=False)), row['id']
        if hits:
            affected.append(row['id'])
            retention.append({'id': row['id'], 'old_F_value': f['value'], 'boundary_reference_N': len(hits)})
    assert affected, 'An empty affected set needs an explicit different no-op release'
    assert len(affected) == len(set(affected)) and len(affected) < 4481
    packet_plan = load(PARENT / 'packet-bindings.json')
    selected = set(affected)
    raw = verify(scope['source_packet'])
    lines = raw.splitlines(keepends=True)
    assert len(lines) == 4481
    subset = []
    for line, rid in zip(lines, scope['approved_record_ids']):
        bundle = json.loads(line)
        assert bundle['source_record']['id'] == rid
        if rid in selected: subset.append(line)
    OUT.mkdir()
    source_path = OUT / 'affected-original-common-lines.jsonl'
    source_path.write_bytes(b''.join(subset))
    plan = {'at_utc': now(), 'parent_seal': bind(parent_run / 'seal.json'), 'parent_execution': bind(parent_run / 'execution.json'), 'parent_predictions': bind(parent_run / 'predictions.jsonl'), 'candidate_delivery': bind(delivery_path), 'static_impact_proof': bind(CANDIDATE / 'static-impact-proof.json'), 'affected_record_ids': affected, 'affected_record_N': len(affected), 'unaffected_inherited_record_N': 4481-len(affected), 'retention_checks': retention, 'all_old_branch_hits_included_including_positive_F': True, 'outside_branch_four_modules_and_remainder_byte_identical': True, 'same_original_inputs_manual_and_protocol': True, 'full4481_executed_under_v8': False, 'formal_validation_complete': False, 'reference_used_by_preparation': False}
    save(OUT / 'impact-closure-plan.json', plan)
    packets = [b for b in packet_plan['packets'] if b['source_id'] in selected]
    assert [b['source_id'] for b in packets] == affected
    packet_plan.update(packet_N=len(affected), ordered_source_ids=affected, packets=packets,
                       parent_complete_packet_manifest=bind(PARENT / 'packet-bindings.json'), bounded_delta_only=True)
    save(OUT / 'packet-bindings.json', packet_plan)
    for name in ('interface_common.py', 'status_bridge.py'):
        (OUT / name).write_bytes((PARENT / name).read_bytes())
    driver = (PARENT / 'rule_driver.py').read_text()
    driver = replace_once(driver, "VERSION='v7-full4481-original-common-driver-1'", "VERSION='" + VERSION + "'")
    driver = replace_once(driver,
        "    if scope.get('expected_record_N') != 4481 or scope.get('expected_dimension_N') != 22405:\n        raise ValueError('adapter requires the complete 4481-record, 22405-dimension scope')",
        "    if not scope.get('bounded_delta_only') or scope.get('parent_complete_record_N') != 4481:\n        raise ValueError('explicit bounded delta and complete parent scope required')\n    delta_N = scope.get('expected_record_N')\n    if type(delta_N) is not int or not (0 < delta_N < 4481) or scope.get('expected_dimension_N') != delta_N * 5:\n        raise ValueError('adapter requires the exact pre-frozen affected subset')")
    driver = replace_once(driver, "packet_plan['packet_N']!=4481", "packet_plan['packet_N']!=scope['expected_record_N']")
    driver = driver.replace('joint-v7 generic direct-content and bounded-relation repair; original common packets/manual/prompt/protocol unchanged', 'joint-v8 bounded needed-product access relation repair; original common packets/manual/prompt/protocol unchanged; partial execution with complete parent v7 inheritance')
    driver = driver.replace("'fixed_algorithm_version':'joint-v7-relation-content-sol'", "'fixed_algorithm_version':'joint-v8-target-product-gap-sol'")
    driver = driver.replace("'sealed_complete_production_provisional_rule_run'", "'sealed_complete_production_provisional_rule_delta_run'")
    driver = driver.replace('Final sealed v5 full4481 original common source-only execution; one first domain pass; persistent per-record outputs.', 'Sealed v8 bounded delta on original common sources; one pass over all affected records; no full v8 run claim.')
    ast.parse(driver)
    (OUT / 'rule_driver.py').write_text(driver)
    modules = [dict(bind(CANDIDATE / (n + '.py')), module=n) for n in ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions')]
    pre_candidate = CANDIDATE / 'candidate-freeze.json'
    assert pre_candidate.exists()
    algorithm = {'algorithm_version': 'joint-v8-target-product-gap-sol', 'modules': modules, 'final_candidate_delivery_seal': bind(delivery_path), 'final_candidate_pre_execution_seal': bind(pre_candidate), 'source_and_manual_unchanged': True, 'reference_not_classifier_input': True, 'bounded_delta_execution': True, 'impact_closure_plan': bind(OUT / 'impact-closure-plan.json')}
    save(OUT / 'algorithm-bindings.json', algorithm)
    run = OUT / 'run-affected-first'
    auth = 'ROOT-v8-complete-affected-branch-delta-once-20261011'
    release = load(PARENT / 'rule-production-release.json')
    release.update(authorization_id=auth, output_directory=str(run), source_input=bind(source_path), algorithm=bind(OUT / 'algorithm-bindings.json'), algorithm_version=algorithm['algorithm_version'], final_algorithm=bind(OUT / 'algorithm-bindings.json'), parent_explicit_authorization='User requested partial recalculation first; complete fallback if necessary.', description='Actual one-pass v8 inference over every affected old-branch record; unaffected v7 decisions may be inherited only under separately verified closure.', bounded_delta_only=True, parent_complete_seal=bind(parent_run / 'seal.json'))
    release.pop('first_final_v5_full_domain_run', None)
    save(OUT / 'rule-production-release.json', release)
    scope = copy.deepcopy(scope)
    old_release_path = scope['release']['path']
    scope.update(authorization_id=auth, output_directory=str(run), source_packet=bind(source_path), release=bind(OUT / 'rule-production-release.json'), algorithm_bindings=bind(OUT / 'algorithm-bindings.json'), driver_version=VERSION, algorithm_origin='sealed v8 sole fairness branch repair; bounded subset, with sealed full v7 parent', final_candidate_algorithm=bind(OUT / 'algorithm-bindings.json'), final_candidate_pre_execution_seal=bind(pre_candidate), final_candidate_delivery_seal=bind(delivery_path), approved_record_ids=affected, expected_record_N=len(affected), expected_dimension_N=len(affected)*5, packet_bindings=bind(OUT / 'packet-bindings.json'), bounded_delta_only=True, parent_complete_record_N=4481, parent_complete_seal=bind(parent_run / 'seal.json'), impact_closure_plan=bind(OUT / 'impact-closure-plan.json'), original_ordered_record_ids_binding=scope['ordered_record_ids_binding'])
    save(OUT / 'approved-affected-record-ids.json', {'approved_record_ids': affected, 'parent_scope': bind(PARENT / 'frozen-scope.json')})
    scope['ordered_record_ids_binding'] = bind(OUT / 'approved-affected-record-ids.json')
    scope['material_bindings'] = [b for b in scope['material_bindings'] if b['path'] != old_release_path] + [scope['source_packet'], scope['release']]
    save(OUT / 'frozen-scope.json', scope)
    preflight = {'at_utc': now(), 'scope': bind(OUT / 'frozen-scope.json'), 'implementation_files': [bind(OUT / n) for n in ('rule_driver.py', 'interface_common.py', 'status_bridge.py', 'packet-bindings.json', 'algorithm-bindings.json', 'rule-production-release.json')], 'closure_plan': bind(OUT / 'impact-closure-plan.json'), 'affected_record_N': len(affected), 'unaffected_record_N': 4481-len(affected), 'source_lines_original_byte_identical': True, 'max_actual_cohort_inference_runs': 1, 'all4481_ran_v8': False, 'classification_executed_in_preparation': False, 'formal_validation_complete': False}
    save(OUT / 'pre-execution-run-seal.json', preflight)
    print(json.dumps({'scope': preflight['scope'], 'input': scope['source_packet'], 'out': str(run), 'affected_record_N': len(affected)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
