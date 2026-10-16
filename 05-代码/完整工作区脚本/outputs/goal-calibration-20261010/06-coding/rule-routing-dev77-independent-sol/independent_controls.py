"""Independent finite controls. No study source, historical labels or Gold reads."""
import ast, copy, hashlib, json, os, sys, types, traceback
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CANDIDATE = ROOT / '05-validation/rule-request-routing-repair-sol'
BASE = ROOT / '06-coding/rule-v18-overall-health-boundary-development-root'
OLD_DRIVER = ROOT / '05-validation/rule-driver-exception-audit-v2-sol'
OUTPUT = HERE / 'independent-control-results-attempt01.json'
if OUTPUT.exists():
    raise ValueError('first independent control output must not be overwritten')
allowed = {HERE / 'independent_controls.py'}
allowed |= {p / n for p in (CANDIDATE, BASE) for n in ('source_packet.py', 'source_receipts.py', 'evidence.py', 'relations.py', 'dimensions.py')}
allowed |= {CANDIDATE / n for n in ('rule_driver.py', 'interface_common.py', 'seal.json')}
allowed |= {OLD_DRIVER / n for n in ('rule_driver.py', 'interface_common.py')}
stdlib = Path(os.__file__).resolve().parent
reads = []
def audit(event, args):
    if event != 'open' or not args or isinstance(args[0], int):
        return
    p = Path(os.fsdecode(args[0])).resolve()
    mode, flags = args[1], args[2]
    writing = (isinstance(mode, str) and any(c in mode for c in 'wax+')) or bool(flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC))
    if writing:
        if p != OUTPUT:
            raise PermissionError('control writes only first declared output')
    else:
        if p not in allowed and stdlib not in p.parents:
            raise PermissionError('control read outside code-only allowlist: ' + str(p))
        reads.append(str(p))
sys.addaudithook(audit)
checks, cases = [], []
def record(name, ok, detail=None):
    checks.append({'name': name, 'passed': bool(ok), 'details': detail})
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
def ast_hash(node):
    return sha(ast.dump(node, include_attributes=False).encode())
def tops(raw):
    return {n.name: n for n in ast.parse(raw).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
def load(name, p):
    mod = types.ModuleType(name)
    mod.__file__, mod.__package__ = str(p), ''
    sys.modules[name] = mod
    exec(compile(p.read_bytes(), str(p), 'exec'), mod.__dict__)
    return mod
mods = {n: load(n, CANDIDATE / (n + '.py')) for n in ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions')}
base = load('independent_baseline_dimensions', BASE / 'dimensions.py')
old_raw, new_raw = (BASE / 'dimensions.py').read_text(), (CANDIDATE / 'dimensions.py').read_text()
old, new = tops(old_raw), tops(new_raw)
ast_records = []
for name, node in old.items():
    if name == 'Accumulator':
        continue
    a, b = ast_hash(node), ast_hash(new[name])
    ast_records.append({'name': name, 'old_AST_sha256': a, 'candidate_AST_sha256': b})
    record('original_definition_unchanged:' + name, a == b)
for name in ('add', 'exclude', 'request', 'error'):
    nodes = [next(n for n in t['Accumulator'].body if isinstance(n, ast.FunctionDef) and n.name == name) for t in (old, new)]
    record('accumulator_positive_method_unchanged:' + name, ast_hash(nodes[0]) == ast_hash(nodes[1]))
assigns = lambda raw: {tuple(ast.dump(t, include_attributes=False) for t in n.targets): n for n in ast.parse(raw).body if isinstance(n, ast.Assign)}
oa, na = assigns(old_raw), assigns(new_raw)
record('all_original_global_constants_unchanged', all(ast_hash(v) == ast_hash(na[k]) for k, v in oa.items()))
for name in ('source_packet.py', 'source_receipts.py', 'evidence.py', 'relations.py'):
    record('source_relation_module_byte_identity:' + name, (BASE / name).read_bytes() == (CANDIDATE / name).read_bytes())
record('interface_helper_byte_identity', (OLD_DRIVER / 'interface_common.py').read_bytes() == (CANDIDATE / 'interface_common.py').read_bytes())
od, nd = (OLD_DRIVER / 'rule_driver.py').read_text(), (CANDIDATE / 'rule_driver.py').read_text()
for name, node in tops(od).items():
    if name != 'main':
        record('driver_nonmain_function_AST_unchanged:' + name, ast_hash(node) == ast_hash(tops(nd)[name]))
def guard(raw):
    return raw[raw.index('            if stops:\n'):raw.index('            prediction.update(labels=')]
record('dependency_guard_exact_bytes_unchanged', guard(od) == guard(nd))
guard_code = compile('\n'.join(s[12:] for s in guard(nd).splitlines()), str(CANDIDATE / 'rule_driver.py') + ':independent_guard', 'exec')
required = ["if out.exists():raise ValueError('first output exists; use a distinct authorized round, never overwrite')", "if scope.get('max_actual_cohort_inference_runs')!=1:", "if target.name=='reference.jsonl' or '/04-calibration/' in str(target):raise PermissionError('reference/calibration prohibited')", "if target not in allowed and out not in target.parents and stdlib not in target.parents:raise PermissionError('unapproved read '+str(target))"]
record('no_overwrite_single_run_exact_read_whitelist_retained', all(t in nd for t in required))
helper_nodes = [tops(nd)[n] for n in ('capture_exception_source_audit', 'dimension_slots')]
ns = {'copy': copy, 'hashlib': hashlib, 'DIMENSIONS': ('S', 'E', 'Ec', 'I', 'F'), 'cj': lambda v: json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)}
exec(compile(ast.fix_missing_locations(ast.Module(body=helper_nodes, type_ignores=[])), str(CANDIDATE / 'rule_driver.py') + ':independent_helpers', 'exec'), ns)
DIMS = mods['dimensions'].DIMENSIONS
def bundle(text):
    return {'common_source_bundle_version': 'independent_constructed_only', 'source_record': {'id': 'INDEPENDENT-CONSTRUCTED', 'text': text, 'contexts': [], 'source_ref': {'source_resource_id': 'INDEPENDENT-SOURCE', 'sha256': sha(('construct:' + text).encode()), 'locator': {}}}, 'source_documents': [], 'explicit_or_primary_source_resources': [], 'preserved_historical_neutral_source_supplements': [], 'source_full_text_resources': [], 'source_asset_locations': [], 'source_locator_bases': {}, 'source_reference_index': [], 'source_provenance_addenda': []}
def view(text='药品资料已经归档。'):
    return mods['relations'].RelationView(mods['source_packet'].semantic_unit(bundle(text)))
def request(kind, tag, **fields):
    return {'path': kind, 'reference': '独立构造确指-' + tag, 'missing': '独立构造缺失-' + tag, **fields}
def inject(v, requests):
    v.material_requests = copy.deepcopy(requests)
    v.source_requests = [dict(r, dependency_status='stopped') for r in v.material_requests]
    return v
def values(d):
    return {k: d[k]['value'] for k in DIMS}
def run_case(name, v, expected, requests=None):
    before = base.judge(v)
    d = mods['dimensions'].judge(v)
    mods['evidence'].validate_decisions(v.unit, d)
    if v.material_requests:
        exec(guard_code, {'view': v, 'decisions': d, 'stops': ['required_reference_unresolved']})
    record(name, values(d) == expected)
    if requests is not None:
        record(name + ':exact_unmodified_requests', v.material_requests == requests)
    cases.append({'name': name, 'constructed_current': v.text, 'requests': copy.deepcopy(v.material_requests), 'baseline_values': values(before), 'candidate_values': values(d), 'expected_from_interface_contract': expected, 'decisions': d})
    return d, before
empty = {k: 0 for k in DIMS}
union = [request('named_mechanism', '机制'), request('cited_standard', '标准', dimensions=['S'])]
v = inject(view(), union)
d, b = run_case('two_distinct_requests_union_only_legal_consumers', v, {'S': None, 'E': 0, 'Ec': 0, 'I': None, 'F': None}, union)
record('no_current_topic_matching_or_missing_topic_inference', all(d[k]['details']['material_request_routes'][0]['absent_source_topics_inferred'] is False for k in ('S', 'I', 'F')))
equiv = request('named_mechanism', '双字段等价', dimensions=['F', 'I'], affected_dimensions=['I', 'F'])
ev = inject(view(), [equiv])
ed, _ = run_case('equivalent_subset_fields_normalize_dimension_order', ev, {'S': 0, 'E': 0, 'Ec': 0, 'I': None, 'F': None}, [equiv])
record('normalized_route_retains_original_declared_order', ed['I']['needed_material'][0]['dimensions'] == ['F', 'I'] and ed['I']['details']['material_request_routes'][0]['dimensions'] == ['I', 'F'])
posview = inject(view('应核实药品有效性。'), [request('cited_standard', '独立疗效与未读安全资料', affected_dimensions=['S'])])
pd, pb = run_case('unrelated_subset_unknown_does_not_mask_independent_E', posview, {'S': None, 'E': 1, 'Ec': 0, 'I': 0, 'F': 0})
record('independent_E_positive_semantic_fields_exactly_preserved', all(pd['E'][k] == pb['E'][k] for k in ('value', 'basis_path', 'current_anchor', 'current_proposition', 'context_evidence', 'reason')))
pv = inject(view('应核实药品有效性。'), [request('cited_standard', '同维未知', dimensions=['E'])])
same, before = run_case('same_dimension_unknown_keeps_independent_E_with_audit', pv, {'S': 0, 'E': 1, 'Ec': 0, 'I': 0, 'F': 0})
record('same_dimension_positive_exact_request_in_audit', same['E']['needed_material'] == [] and same['E']['details']['unresolved_material_requests'] == pv.material_requests)
actual = view('药品应说明以下证据；应验证药品有效性。')
actual_d, actual_b = run_case('actual_relation_generator_missing_list_keeps_E_only_positive', actual, {'S': None, 'E': 1, 'Ec': None, 'I': None, 'F': None})
record('actual_list_generator_request_not_injected', len(actual.material_requests) == 1 and actual.material_requests[0]['path'] == 'substantive_list')
non = view('药品以下内容仅作目录编号。')
non_d, _ = run_case('nonoperative_list_cue_does_not_create_unknown', non, empty)
record('nonoperative_list_has_no_material_request', non.material_requests == [])
# A retained first request must not conceal a distinct unretained second request.
lost = copy.deepcopy(d)
lost['S']['needed_material'] = []
lost['S']['details']['unresolved_material_requests'] = []
try:
    exec(guard_code, {'view': v, 'decisions': lost, 'stops': ['required_reference_unresolved']})
except ValueError:
    record('guard_rejects_second_request_even_when_first_is_retained', True)
else:
    record('guard_rejects_second_request_even_when_first_is_retained', False)
bad = [request('named_mechanism', '重复', dimensions=['I', 'I']), request('cited_standard', '元组', dimensions=('S',)), request('named_mechanism', '跨消费者', affected_dimensions=['E']), request('cited_standard', '依赖未停止', dependency_status='available'), request('cited_standard', '真假值', necessary_dependency=1), request('mystery_link', '未知类'), request('cited_standard', '子集冲突', dimensions=['S'], affected_dimensions=['E'])]
for i, req in enumerate(bad):
    bv = inject(view('应提供药品安全性、有效性、经济性、创新性及公平性评价资料。'), [req])
    try:
        mods['dimensions'].judge(bv)
    except mods['dimensions'].MaterialRequestRoutingError as err:
        snapshot = ns['capture_exception_source_audit'](bv, err, None, None, 'not_started')
        p = {'id': 'INDEPENDENT-CONSTRUCTED', 'labels': None, 'decisions': None, 'implementation_errors': [{'type': type(err).__name__, 'message': str(err)}], **snapshot}
        slots = ns['dimension_slots']([{'source_record': {'id': p['id']}}], [p], [])
        record('invalid_dependency_masks_even_existing_positive:' + str(i), snapshot['material_requests'] == [req] and all(s['technical_failure'] and not s['rules_null'] and s['rule_value'] is None and not s['comparison_eligible'] for s in slots), str(err))
    else:
        record('invalid_dependency_masks_even_existing_positive:' + str(i), False)
global_slots = ns['dimension_slots']([{'source_record': {'id': 'INDEPENDENT-CONSTRUCTED'}}], [{'id': 'INDEPENDENT-CONSTRUCTED', 'labels': values(same), 'decisions': same, 'implementation_errors': []}], [{'type': 'ConstructedChangedDependency'}])
record('global_error_masks_all_retained_positive_or_zero', all(s['technical_failure'] and not s['rules_null'] and s['rule_value'] is None and not s['comparison_eligible'] for s in global_slots))
# Driver guard is propagation validation, not the routing oracle. A wrong route
# can pass its existential test. The independent exact-route controls above
# therefore test the candidate accumulator directly.
wrong = {k: {'value': 0, 'needed_material': [], 'details': {}} for k in DIMS}
wrong['E'] = {'value': None, 'needed_material': [union[0], union[1]], 'details': {}}
try:
    exec(guard_code, {'view': v, 'decisions': wrong, 'stops': ['required_reference_unresolved']})
except ValueError:
    record('guard_limitation_constructed_wrong_dimension_retention_is_not_detected', False)
else:
    record('guard_limitation_constructed_wrong_dimension_retention_is_not_detected', True, 'Inherited existential propagation guard does not prove correct consumer allocation; exact routing is separately validated.')
result = {'status': 'finite_independent_constructed_review', 'created_at_utc': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(), 'controls_N': len(checks), 'passed': all(c['passed'] for c in checks), 'checks': checks, 'cases': cases, 'original_definition_AST_bindings': ast_records, 'guard_sha256': sha(guard(nd).encode()), 'runtime_read_paths': sorted(set(reads)), 'actual_cohort_inference_runs': 0, 'study_source_body_or_Gold_or_human_labels_read': False, 'human_independent_label_N': 0, 'formal_validation_complete': False, 'human_validation_complete': False}
with OUTPUT.open('x', encoding='utf8') as f:
    f.write(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
print(json.dumps({'controls_N': len(checks), 'passed': result['passed'], 'failed': [c['name'] for c in checks if not c['passed']]}, ensure_ascii=False))
raise SystemExit(0 if result['passed'] else 2)
