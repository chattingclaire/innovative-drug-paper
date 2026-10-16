"""Receive immutable finite-review inputs and outputs; never execute a judge."""
import copy
import datetime
import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / '08-audits/SE-Ec-v2-independent-controls-sol'
OUT = ROOT / '08-audits/SEv2-independent43-reception-root'


def load(p):
    return json.loads(Path(p).read_bytes())


def bind(p):
    p = Path(p).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def exact(b):
    assert bind(b['path']) == {k: b[k] for k in ('path', 'bytes', 'sha256')}, b['path']


def value_binding(v):
    raw = json.dumps(v, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
    return {'canonical_UTF8_bytes': len(raw), 'canonical_sha256': hashlib.sha256(raw).hexdigest()}


def save(p, value):
    with p.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


assert not OUT.exists(), 'Do not replace a receipt'
seal_binding = bind(SRC / 'output-seal.json')
assert seal_binding['sha256'] == '8a043197a1393a41030b3565ee78005c712367a77ba7f3856ba835460d7cb890'
members = load(SRC / 'output-seal.json')['output_members']
assert len(members) == 26
for b in members:
    exact(b)
preseal = load(SRC / 'pre-execution-seal.json')
for b in preseal['inputs']:
    exact(b)
verification = load(SRC / 'sealed-input-verification.json')
for b in verification['files']:
    exact(b)
for pair in verification['code_snapshots']:
    exact(pair['independent_snapshot'])
    exact(pair['owner_binding'])

# Import only the pure source adapter; there are no RelationView/judge calls.
spec = importlib.util.spec_from_file_location('root43_source_adapter', SRC / 'code-snapshot/source_packet.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
execution = load(SRC / 'execution-results.json')
rows = {(r['suite'], r['name']): r for r in execution['cases']}
input_bindings = load(SRC / 'executed43-input-bindings.json')
assert len(rows) == len(input_bindings) == 43
units = {}
cases = {}
adapter_N = 0
for b in input_bindings:
    exact(b['source_file'])
    pointer = b['case_JSON_pointer'].split('/')
    assert len(pointer) == 3 and pointer[0] == '' and pointer[1] == 'cases'
    case = load(b['source_file']['path'])['cases'][int(pointer[2])]
    key = (b['suite'], b['name'])
    assert case['name'] == b['name']
    raw = case.get('synthetic_input', case.get('synthetic_bundle', case.get('bound_source_bundle')))
    assert value_binding(raw) == b['raw_input_object_binding']
    if 'synthetic_input' in case:
        unit = copy.deepcopy(raw)
    else:
        unit = adapter.semantic_unit(copy.deepcopy(raw))
        adapter_N += 1
    assert value_binding(unit) == b['reconstructed_received_semantic_unit_binding']
    assert value_binding(case['expected']) == b['expected_binding']
    row = rows[key]
    assert row['expected'] == case['expected'] and row['current_text'] == unit['text']
    assert row['judge_attempted'] and row['evidence_validation_passed'] and 'error' not in row
    observed = {d: row['decisions'][d]['value'] for d in case['expected']}
    mismatches = [{'dimension': d, 'expected': v, 'observed': observed[d]}
                  for d, v in case['expected'].items() if observed[d] != v]
    assert row['observed'] == observed and row['mismatches'] == mismatches
    assert row['passed'] == (not mismatches)
    cases[key] = case
    units[key] = unit

suite_counts = {}
for suite in ('legacy20', 'new20', 'owner_closure3'):
    rr = [r for (s, _), r in rows.items() if s == suite]
    value = {'case_N': len(rr), 'passed_N': sum(r['passed'] for r in rr),
             'failed_N': sum(not r['passed'] for r in rr),
             'mismatched_dimensions_N': sum(len(r['mismatches']) for r in rr),
             'exceptions_N': 0, 'evidence_validation_passed_N': len(rr),
             'failed_names': [r['name'] for r in rr if not r['passed']]}
    assert value == execution['summary']['suite_summary'][suite]
    suite_counts[suite] = value
assert (suite_counts['legacy20']['passed_N'], suite_counts['new20']['passed_N'],
        suite_counts['owner_closure3']['passed_N']) == (19, 15, 3)
failures = load(SRC / 'all-failures-full-inputs-and-paths.json')
assert len(failures) == 6
assert {(f['suite'], f['name']) for f in failures} == {k for k, r in rows.items() if not r['passed']}
for f in failures:
    key = (f['suite'], f['name'])
    assert f['complete_received_unit'] == units[key] and f['original_presealed_case'] == cases[key]
    assert f['expected'] == rows[key]['expected'] and f['observed'] == rows[key]['observed']

quote_checks = load(SRC / 'literal-quote-validation.json')
assert len(quote_checks) == 50
synthetic_quote_N = 0
for q in quote_checks:
    key = (q['suite'], q['name'])
    unit = units[key]
    context = next(c for c in unit['contexts'] if c['context_id'] == q['context_id'])
    a, z = q['context_range']
    assert context['text'][a:z] == q['quote'] and context['source_ref'] == q['source_ref']
    decision = rows[key]['decisions'][q['dimension']]
    records = [decision] + decision['details'].get('additional_evidence', [])
    original_quote = records[q['record_index']]['context_evidence'][q['quote_index']]
    assert original_quote['text'] == q['quote'] and original_quote['source_ref'] == q['source_ref']
    assert [original_quote['start'], original_quote['end']] == q['context_range']
    if 'synthetic_document_range' in q:
        doc = next(d for d in cases[key]['synthetic_documents'] if d['sha256'] == q['source_ref']['sha256'])
        assert hashlib.sha256(doc['text'].encode()).hexdigest() == doc['sha256']
        lo, hi = q['synthetic_document_range']
        assert doc['text'][lo:hi] == q['quote']
        assert lo == context['source_ref']['locator']['unicode_code_point_interval_half_open'][0] + a
        synthetic_quote_N += 1

manual = load(SRC / 'manual-basis-quotes.json')
exact(manual['binding'])
manual_text = Path(manual['binding']['path']).read_text()
for q in manual['quotes']:
    assert manual_text[q['start']:q['end']] == q['quote']
    assert manual_text[:q['start']].count('\n') + 1 == q['line_1based']

for b in members:
    exact(b)
OUT.mkdir()
receipt = {'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'status': 'ROOT_mechanical_reception_of_independent_finite_review',
           'audit_seal': seal_binding, 'sealed_members_N': len(members),
           'pre_execution_inputs_exact': True, 'actual_adapter_readback_N': adapter_N,
           'input_expected_and_results_checked_N': len(rows), 'suite_counts': suite_counts,
           'failure_full_inputs_checked_N': len(failures), 'exact_context_quote_checks_N': len(quote_checks),
           'synthetic_document_quote_checks_N': synthetic_quote_N,
           'manual_literal_quotes_checked_N': len(manual['quotes']),
           'judge_calls_by_ROOT': 0, 'classification_rerun': False,
           'new20_geometry_errors': {'case_N': 5, 'dimension_N': 9, 'retained': True},
           'legacy_complete_article_missing_closure': {'case_N': 1, 'dimension_N': 3, 'expected_preserved': True},
           'current_repair_status': 'separate_v3_geometry_candidate_under_revision',
           'independent_controls_now_development_exposed': True,
           'human_reference_created': False, 'formal_metric_acceptance': False,
           'primary_LLM_partial_labels_read': False, 'originals_changed': False,
           'readback_scope_is_not_new_semantic_adjudication': True,
           'receiver': bind(__file__)}
save(OUT / 'actual-reception.json', receipt)
save(OUT / 'output-seal.json', {'output_members': [bind(OUT / 'actual-reception.json')], 'self_excluded': True})
print(json.dumps({k: receipt[k] for k in ('status', 'sealed_members_N', 'input_expected_and_results_checked_N',
                                       'exact_context_quote_checks_N', 'judge_calls_by_ROOT')}, ensure_ascii=False))
