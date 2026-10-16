"""Finite independent AI controls against immutable sealed code; toys only."""
import ast
import copy
import hashlib
import json
import os
import sys
import traceback
import types
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = ROOT / '06-coding/human4-general-rule-repair-sol/versions' / (sys.argv[1] if len(sys.argv) > 1 else 'v2')
OUTPUT = HERE / (sys.argv[2] if len(sys.argv) > 2 else 'independent-results-attempt01-v2.json')
PRIOR = HERE / 'prior-expectations-and-toy-source-chains.json'
SUPPLEMENT = (HERE / sys.argv[3]).resolve() if len(sys.argv) > 3 else None
if OUTPUT.parent != HERE or OUTPUT.exists():
    raise ValueError('distinct new first-attempt output required; never overwrite')
CODE = ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions', 'interface_common', 'rule_driver')
BASE = ROOT / '05-validation/rule-request-routing-repair-sol'
allowed = {CANDIDATE / (n + '.py') for n in CODE} | {CANDIDATE / 'seal.json', CANDIDATE / 'algorithm-bindings.json',
    PRIOR, HERE / 'audit_controls.py', BASE / 'dimensions.py', BASE / 'rule_driver.py'}
allowed |= {p for p in HERE.iterdir() if p.is_file() and p.name.startswith('toy-')}
if SUPPLEMENT is not None:
    if SUPPLEMENT.parent != HERE:
        raise ValueError('supplement must be a prior saved in the isolated audit directory')
    allowed.add(SUPPLEMENT)
stdlib = Path(os.__file__).resolve().parent
reads = []


def audit(event, args):
    if event != 'open' or not args or isinstance(args[0], int):
        return
    path = Path(os.fsdecode(args[0])).resolve()
    mode = args[1] if len(args) > 1 else None
    flags = args[2] if len(args) > 2 else 0
    write = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or bool(flags and flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
    if write:
        if path.parent != HERE:
            raise PermissionError('independent audit write outside its own directory')
    elif path not in allowed and stdlib not in path.parents:
        raise PermissionError('independent audit cannot read study material or unapproved file: ' + str(path))
    else:
        reads.append(str(path))


sys.addaudithook(audit)


def h(data):
    return hashlib.sha256(data if isinstance(data, bytes) else data.encode('utf8')).hexdigest()


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


seal_raw = (CANDIDATE / 'seal.json').read_bytes()
seal = json.loads(seal_raw)
bindings = {Path(item['path']).name: item for item in seal['output_files']}
loaded = []


def load(name):
    path = CANDIDATE / (name + '.py')
    data = path.read_bytes()
    expected = bindings[path.name]
    if h(data) != expected['sha256'] or len(data) != expected['bytes']:
        raise ValueError('sealed code hash/bytes mismatch: ' + name)
    module = types.ModuleType(name)
    module.__file__, module.__package__ = str(path), ''
    sys.modules[name] = module
    exec(compile(data, str(path), 'exec'), module.__dict__)
    loaded.append({'module': name, 'path': str(path), 'sha256': h(data), 'bytes': len(data)})
    return module


mods = {name: load(name) for name in CODE}
driver, dim, ev, sp, sr, rel = (mods[name] for name in ('rule_driver', 'dimensions', 'evidence', 'source_packet', 'source_receipts', 'relations'))
prior = json.loads(PRIOR.read_bytes())
supplement = json.loads(SUPPLEMENT.read_bytes()) if SUPPLEMENT is not None else None
DIMS = dim.DIMENSIONS
checks, results = [], []


def check(name, passed, detail=None):
    checks.append({'name': name, 'passed': bool(passed), 'details': detail})


def values(decisions):
    return {d: decisions[d]['value'] for d in DIMS}


def guard_text(text):
    start = text.index('            if stops:\n')
    end = text.index('            prediction.update(labels=', start)
    return text[start:end]


driver_text = (CANDIDATE / 'rule_driver.py').read_text()
old_driver = (BASE / 'rule_driver.py').read_text()
guard = guard_text(driver_text)
check('actual_dependency_guard_exact_bytes_preserved', guard == guard_text(old_driver))
guard_code = compile('\n'.join(line[12:] for line in guard.splitlines()), str(CANDIDATE / 'rule_driver.py') + ':executed_TOY_dependency_guard', 'exec')


class ToyProtocol:
    """Only a synthetic receipt facade; not the native source protocol."""
    def __init__(self, b):
        self.b = b
        self.bound_source_identity = {'constructed_only': True, 'candidate_version': seal['algorithm_version'], 'real_cohort': False}
        self.producer_source_inventory = sp.source_inventory

    def source_identity_resolver(self, b):
        inv = sp.source_inventory(b)
        if any(r['resource_id'].startswith('FULLSOURCE-') for r in inv):
            return sr.resolve_inventory(b, inv, prior['toy_material_bindings'], HERE)
        return inv, []

    def prepare(self, rid, runid, method):
        inv, _ = self.source_identity_resolver(self.b)
        return {'source_inventory': inv, 'reference_resolution': []}

    def check(self, log):
        by_id = {r['receipt_id']: r for r in log['read_receipts']}
        inventory = {r['resource_id']: r for r in log['source_inventory']}
        for read in log['read_receipts']:
            r = inventory[read['resource_id']]
            if r['source_sha256'] != read['source_sha256'] or r['available_views'][read['view']] != read['view_sha256']:
                raise ValueError('TOY receipt identity mismatch')
        for use in log['use_receipts']:
            read = by_id[use['read_receipt_id']]
            if (read['resource_id'], read['view']) != (use['resource_id'], use['view']):
                raise ValueError('TOY source use has no matching actual read')
        return {'passed': True, 'constructed_only': True, 'native_source_protocol_executed': False,
                'actual_read_receipt_N': len(log['read_receipts']), 'actual_use_receipt_N': len(log['use_receipts'])}


def literal_quote_checks(cid, semantic, view, decisions):
    source = {c['context_id']: c for c in semantic['contexts']}
    for r in view.traces():
        a = r['current_anchor']
        check(cid + ':relation-current-complete:' + r['kind'], a['text'] == semantic['text'][a['start']:a['end']] and a == ev.anchor(semantic['text'], 0, len(semantic['text'])))
        for q in r['context_evidence']:
            c = source[q['context_id']]
            check(cid + ':relation-source-quote-literal:' + q['context_id'], q['text'] == c['text'][q['start']:q['end']] and q['source_ref'] == c['source_ref'])
    for d in DIMS:
        if decisions[d]['value'] == 1:
            check(cid + ':positive-current-proposition-complete:' + d, decisions[d]['current_proposition'] == ev.anchor(semantic['text'], 0, len(semantic['text'])))


for case in prior['cases'] + (supplement['cases'] if supplement else []):
    cid, b = case['case_id'], copy.deepcopy(case['source_bundle'])
    record = {'case_id': cid, 'expected_before_candidate_execution': case['expected'], 'prior_reason': case['prior_reason'],
              'constructed_bundle': b, 'constructed_only': True, 'actual_real_cohort_inference': False}
    view = None; decisions = None; log = None; logcheck = None; stage = 'not_started'
    try:
        if case.get('integrity_before_semantics') or case.get('require_literal_integrity'):
            record['literal_leaf_integrity'] = driver.literal_leaf_integrity([b], prior['toy_material_bindings'])
        if case.get('require_identity'):
            record['resolved_inventory'], record['identity_delta'] = sr.resolve_inventory(b, sp.source_inventory(b), prior['toy_material_bindings'], HERE)
        semantic = sp.semantic_unit(b)
        view = rel.RelationView(semantic)
        decisions = dim.judge(view)
        ev.validate_decisions(semantic, decisions)
        record['candidate_values'] = values(decisions)
        record['candidate_decisions'] = decisions
        record['relations'] = view.traces()
        record['material_requests'] = copy.deepcopy(view.material_requests)
        record['semantic_units_consumed'] = [{'text': u.text, 'kind': u.kind, 'details': u.details,
            'inherited': u.inherited, 'context_ids': [c['context_id'] for c in u.contexts]} for u in dim._units(view)]
        check(cid + ':prior-semantic-expectation', not case.get('expected_error') and all(record['candidate_values'][d] == value for d, value in case['expected'].items()),
              {'expected': case['expected'], 'actual': record['candidate_values']})
        if case.get('expected_request'):
            check(cid + ':concrete-request-path', {r['path'] for r in view.material_requests} == {case['expected_request']})
        if view.material_requests:
            exec(guard_code, {'view': view, 'decisions': decisions, 'stops': ['required_reference_unresolved']})
            check(cid + ':actual-guard-executed-with-unresolved-request', True)
        stage = 'executing'
        log, logcheck = driver.actual_reading_log(ToyProtocol(b), b, view, 'TOY-INDEPENDENT-' + cid)
        stage = 'returned'
        record['executed_driver_reading_log'] = log
        record['toy_receipt_check'] = logcheck
        literal_quote_checks(cid, semantic, view, decisions)
        slots = driver.dimension_slots([b], [{'id': b['source_record']['id'], 'labels': values(decisions),
            'decisions': decisions, 'implementation_errors': []}], [])
        record['actual_dimension_slots'] = slots
        check(cid + ':actual-output-masks-preserve-null-vs-decision', all(not s['technical_failure'] and s['comparison_eligible'] and
            s['rules_null'] == (decisions[s['dimension']]['value'] is None) and s['rule_value'] == decisions[s['dimension']]['value'] for s in slots))
        if case.get('must_preserve'):
            check(cid + ':negation-preserved-in-current-proposition', case['must_preserve'] in decisions['S']['current_proposition']['text'])
        if case.get('require_fullsource_use'):
            check(cid + ':FULLSOURCE-actual-read-and-use', any(u['resource_id'].startswith('FULLSOURCE-') and u['source_relation_kind'] == 'price_arrangement' for u in log['use_receipts']))
            check(cid + ':Ec-price-Unit-evidence-consumed', decisions['Ec']['details']['relation_kind'] == 'price_arrangement' and
                bool(decisions['Ec']['context_evidence']) and any(u['kind'] == 'price_arrangement' for u in record['semantic_units_consumed']))
        if case.get('expected_request') == 'price_arrangement':
            routes = {d: decisions[d].get('details', {}).get('material_request_routes', []) for d in DIMS}
            check(cid + ':price-request-only-actual-Ec-consumer', bool(routes['Ec']) and all(not routes[d] for d in DIMS if d != 'Ec'))
    except Exception as exc:
        record['exception'] = {'type': type(exc).__name__, 'message': str(exc), 'traceback': traceback.format_exc()}
        snapshot = driver.capture_exception_source_audit(view, exc, log, logcheck, stage)
        record['actual_exception_source_audit'] = snapshot
        slots = driver.dimension_slots([b], [{'id': b['source_record']['id'], 'decisions': decisions,
            'implementation_errors': [record['exception']]}], [])
        record['actual_dimension_slots'] = slots
        check(cid + ':expected-technical-failure', case.get('expected_error', False), record['exception'])
        check(cid + ':actual-technical-failure-masks-not-rules-null', all(s['technical_failure'] and not s['rules_null'] and not s['comparison_eligible'] for s in slots))
        check(cid + ':exception-source-state-not-reconstructed', snapshot['uniform_source_audit_state']['local_byte_reconstruction_claimed'] is False)
    record['passed'] = all(c['passed'] for c in checks if c['name'].startswith(cid + ':'))
    results.append(record)


raw_cases_path = HERE / (OUTPUT.stem + '.cases.json')
with raw_cases_path.open('x', encoding='utf8') as stream:
    json.dump({'cases': results, 'checks_before_engineering_probes': checks,
               'raw_executed_outputs_saved_before_remaining_probes': True}, stream, ensure_ascii=False, indent=2)
    stream.write('\n')


def functions(text):
    return {n.name: n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}


def astsha(node):
    return h(ast.dump(node, include_attributes=False))


old_dim = (BASE / 'dimensions.py').read_text()
new_dim = (CANDIDATE / 'dimensions.py').read_text()
of, nf = functions(old_dim), functions(new_dim)
for name in ('_substantive', '_form_only', '_object', '_publication_purpose', '_drug_effectiveness_topic'):
    check('original-generic-threshold-AST-retained:' + name, astsha(of[name]) == astsha(nf[name]))
check('original-generic-evaluation-body-retained-after-relation-skip',
      [astsha(n) for n in of['_generic'].body[1:]] == [astsha(n) for n in nf['_generic'].body[1:]])
oldassign = {n.targets[0].id: n for n in ast.parse(old_dim).body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
newassign = {n.targets[0].id: n for n in ast.parse(new_dim).body if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
for name in ('TOPICS', 'NONDIM', 'CONTENT_ACTION', 'FORM', 'PURE_STRUCTURE', 'INNOVATION_OBJECT', 'SUPPORT', 'SUPPORT_ACTION', 'OPPORTUNITY', 'GAPS'):
    check('original-generic-word-constant-retained:' + name, astsha(oldassign[name]) == astsha(newassign[name]))
for filename in ('relations.py', 'dimensions.py'):
    text = (CANDIDATE / filename).read_text()
    check('no-study-ID-white-list:' + filename, not any(token in text for token in ('RECODE25-', 'B-00005', '00005', '03876', '00138', '02573')))
check('price_arrangement-closed-consumer-contract-only-Ec', dim.MATERIAL_REQUEST_CONSUMERS['price_arrangement'] == ('Ec',))
try:
    dim._material_request_route({'path': 'price_arrangement', 'reference': 'TOY price', 'missing': 'TOY definition', 'dimensions': ['S']})
except dim.MaterialRequestRoutingError:
    check('price-route-rejects-explicit-wrong-consumer', True)
else:
    check('price-route-rejects-explicit-wrong-consumer', False)
preserve = HERE / ('toy-first-preservation-' + OUTPUT.stem + '.json')
allowed.add(preserve)
driver.write_json(preserve, {'first_attempt': True, 'constructed_only': True})
first = preserve.read_bytes()
try:
    driver.write_json(preserve, {'second_attempt': 'should never overwrite'})
except FileExistsError:
    check('actual-driver-write-json-first-attempt-preserved', preserve.read_bytes() == first)
else:
    check('actual-driver-write-json-first-attempt-preserved', False)

seal_after = (CANDIDATE / 'seal.json').read_bytes()
check('candidate-seal-bytes-unchanged-through-independent-controls', seal_raw == seal_after)
check('all-loaded-code-hashes-still-match-seal', all(h(Path(r['path']).read_bytes()) == r['sha256'] for r in loaded))
out = {'audit_kind': 'finite independent AI engineering and semantic counterexamples, disclosed-label development review',
    'candidate': str(CANDIDATE), 'candidate_version': seal['algorithm_version'],
    'candidate_seal': {'path': str(CANDIDATE / 'seal.json'), 'sha256': h(seal_raw), 'bytes': len(seal_raw)},
    'loaded_frozen_code': loaded, 'prior_expectations': {'path': str(PRIOR), 'sha256': h(PRIOR.read_bytes())},
    'repair_only_supplement_prior': {'path': str(SUPPLEMENT), 'sha256': h(SUPPLEMENT.read_bytes())} if SUPPLEMENT is not None else None,
    'case_N': len(results), 'passed_case_N': sum(r['passed'] for r in results),
    'check_N': len(checks), 'passed_check_N': sum(c['passed'] for c in checks),
    'cases': results, 'checks': checks, 'all_passed': all(c['passed'] for c in checks),
    'actual_executed_path': 'semantic_unit -> RelationView -> judge -> validate_decisions -> sourced dependency guard on toys -> actual_reading_log with ToyProtocol -> dimension_slots',
    'real_driver_main_executed': False, 'native_source_protocol_executed': False,
    'actual_77_800_4481_inference_runs': 0, 'real_study_record_body_read_N': 0,
    'formal_validation': False, 'independent_human_validation': False, 'read_allowlist': sorted(str(p) for p in allowed),
    'actual_read_paths': sorted(set(reads)), 'first_attempt_preservation': str(preserve)}
with OUTPUT.open('x', encoding='utf8') as stream:
    json.dump(out, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write('\n')
print(cj({'output': str(OUTPUT), 'all_passed': out['all_passed'], 'case_N': len(results),
    'passed_case_N': out['passed_case_N'], 'check_N': len(checks), 'passed_check_N': out['passed_check_N'],
    'failed_checks': [c for c in checks if not c['passed']]}))
