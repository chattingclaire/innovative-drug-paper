"""Read actual source bytes and retained first results; execute no classifier."""
import datetime
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '08-audits/joint20-and-batch659-reception-root'
assert not OUT.exists(), 'Keep prior receipts immutable'


def load(p):
    return json.loads(Path(p).read_bytes())


def bind(p):
    p = Path(p).resolve()
    b = p.read_bytes()
    return {'path': str(p), 'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()}


def exact(b):
    assert bind(b['path']) == {k: b[k] for k in ('path', 'bytes', 'sha256')}, b['path']


def canonical(v):
    return json.dumps(v, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf8')


def seal(p, sha, n):
    b = bind(p)
    assert b['sha256'] == sha, p
    members = load(p)['output_members']
    assert len(members) == n
    for m in members:
        exact(m)
    return b, members


# Full candidate material envelopes, actual JSONL line bytes, and old input preservation.
B = ROOT / '06-coding/common-material-new-batch-plan-sol'
bs, bm = seal(B / 'output-seal.json',
              'b54f022cd8876544d497643f62f328db16cc628731f982a494e6bfd831b71c5d', 1329)
ib = load(B / 'input-bindings.json')
for v in ib.values():
    if isinstance(v, dict) and {'path', 'bytes', 'sha256'} <= v.keys():
        exact(v)
for b in ib['core_candidate_bindings']:
    exact(b)
assert ib['model_runs'] == 0 and not ib['candidate_material_adopted']
assert not ib['labels_or_main_LLM_files_read'] and not ib['sampling_created']
inventory = load(ib['candidate_inventory']['path'])
frame = load(ib['frame_order']['path'])['source_ids']
assert len(inventory) == len(frame) == len(set(frame)) == 4481
assert [r['source_id'] for r in inventory] == frame
inv = {r['source_id']: r for r in inventory}
plan = load(B / 'batch-plan.json')
assert plan['batch_N'] == len(plan['batches']) == 659
assert plan['record_N'] == 4481 and plan['deployment_or_dispatch_N'] == 0
assert (plan['max_records'], plan['packet_byte_limit']) == (12, 260000)
seen, byte_sum, max_batch = [], 0, 0
for batch in plan['batches']:
    fb = batch['source_only_complete_inputs']
    exact(fb)
    raw = Path(fb['path']).read_bytes()
    lines = raw.splitlines(keepends=True)
    records = batch['records']
    assert len(lines) == len(records) == batch['record_N'] <= 12
    assert len(raw) == batch['actual_compact_whole_packet_bytes'] <= 260000
    offset = 0
    for line, r in zip(lines, records):
        sid = r['source_id']
        exact(r['candidate_packet_binding'])
        assert r['candidate_packet_binding'] == inv[sid]['packet_binding']
        packet = load(r['candidate_packet_binding']['path'])
        assert line == canonical(packet) + b'\n'
        assert (packet['source_id'], packet['output_id']) == (sid, r['output_id'])
        bundle_sha = hashlib.sha256(canonical(packet['source_bundle'])).hexdigest()
        assert bundle_sha == r['source_bundle_sha256'] == packet['source_bundle_sha256']
        assert len(line) == r['compact_whole_packet_line_bytes']
        assert hashlib.sha256(line).hexdigest() == r['compact_whole_packet_line_sha256']
        assert r['batch_byte_interval_half_open'] == [offset, offset + len(line)]
        assert r['frame_ordinal_1based'] == len(seen) + 1
        offset += len(line)
        seen.append(sid)
    assert offset == len(raw)
    assert batch['source_ids'] == [r['source_id'] for r in records]
    byte_sum += len(raw)
    max_batch = max(max_batch, len(raw))
assert seen == frame
assert (byte_sum, max_batch) == (123466714, 259626)
originals = load(B / '17-original-binding-checks.json')['checks']
assert len(originals) == 17
for r in originals:
    exact(r['original'])
    exact(r['candidate_copy'])
    assert Path(r['original']['path']).read_bytes() == Path(r['candidate_copy']['path']).read_bytes()
old = load(B / 'historical504-preservation-bindings.json')
for b in old['old504_plan_and_preparation_files']:
    exact(b)
assert len(old['old4481_packet_bindings']) == 4481
for r in old['old4481_packet_bindings']:
    exact(r['parent_packet_binding'])
    assert r['parent_packet_binding'] == inv[r['source_id']]['parent_packet']

# Original independent 20 first executions, without rerunning their classifier.
A = ROOT / '08-audits/five-dimension-joint-independent-controls-sol'
X = A / 'execution-joint-v2-geometry01'
as_, am = seal(X / 'output-seal.json',
                '60647ff02a8c92800f104ab1b186295ce213ce8e82fdb879d06b3da615294950', 20)
pre = load(A / 'preparation-seal.json')
assert pre['case_N'] == 20 and pre['candidate_judge_attempts_N'] == 0
for m in pre['output_members']:
    exact(m)
execution_seal = load(X / 'execution-input-and-code-seal.json')
for k in ('original_preparation_seal', 'original_controls', 'candidate_pre_execution_seal',
          'candidate_algorithm_binding', 'manual', 'runner'):
    exact(execution_seal[k])
for pair in execution_seal['snapshots']:
    exact(pair['candidate'])
    exact(pair['executed_snapshot'])
    assert pair['candidate']['sha256'] == pair['executed_snapshot']['sha256']
spec = importlib.util.spec_from_file_location('root_joint20_pure_adapter', X / 'code-snapshot/source_packet.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
cases = {r['name']: r for r in load(A / 'controls20-fixed-before-execution.json')['cases']}
rows = {r['name']: r for r in load(X / 'execution-results.json')['cases']}
bindings = load(X / 'case-input-bindings.json')['cases']
assert len(cases) == len(rows) == len(bindings) == 20
units = {}
for b in bindings:
    name = b['name']
    case, row = cases[name], rows[name]
    raw = canonical(case['synthetic_bundle'])
    assert len(raw) == b['source_only_bundle_canonical_bytes']
    assert hashlib.sha256(raw).hexdigest() == b['source_only_bundle_canonical_sha256']
    unit = adapter.semantic_unit(case['synthetic_bundle'])
    units[name] = unit
    assert unit['text'] == b['current_text']
    expected = case['expected_values_fixed_before_execution']
    assert row['expected_values_fixed_before_execution'] == expected
    observed = {d: row['full_five_decisions_first_execution'][d]['value'] for d in expected}
    assert observed == row['actual_values']
    differences = [d for d in expected if observed[d] != expected[d]]
    assert differences == row['mismatched_dimensions']
    assert row['values_matched'] == (not differences)
    assert row['execution_error'] is None and row['evidence_validator_passed']
quotes = load(X / 'literal-quote-first-execution-validation.json')['quotes']
assert len(quotes) == 36
for q in quotes:
    exact(q['synthetic_source_binding'])
    text = Path(q['synthetic_source_binding']['path']).read_text()
    a, z = q['synthetic_document_unicode_span']
    assert text[a:z] == q['quote']
    a8, z8 = q['synthetic_document_utf8_byte_span']
    assert text.encode('utf8')[a8:z8].decode('utf8') == q['quote']
    unit = units[q['case']]
    ctx = next(c for c in unit['contexts'] if c['context_id'] == q['context_id'])
    lo, hi = q['context_relative_unicode_span']
    assert ctx['text'][lo:hi] == q['quote'] and ctx['source_ref'] == q['source_ref']
manual = load(A / 'manual-basis-quotes.json')
exact(manual['binding'])
mt = Path(manual['binding']['path']).read_text()
for q in manual['quotes']:
    a, z = q['unicode_span_half_open']
    assert mt[a:z] == q['quote'] and mt[:a].count('\n') + 1 == q['line_1based']
matched = sum(r['values_matched'] for r in rows.values())
differences = sum(len(r['mismatched_dimensions']) for r in rows.values())
assert (matched, differences) == (15, 9)
for b in bm + am:
    exact(b)
receipt = {
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'status': 'ROOT_actual_byte_and_retained_result_reception',
    'source_only_batch_plan': {
        'seal': bs, 'sealed_members_checked_N': len(bm), 'actual_batch_N': 659,
        'records_exact_once_in_frozen_order_N': 4481,
        'complete_envelope_lines_checked_N': 4481, 'total_JSONL_bytes': byte_sum,
        'max_batch_bytes': max_batch, 'identical_original_copy_N': 17,
        'historical_packet_bindings_checked_N': 4481, 'adopted': False,
        'provider_context_capacity_verified': False},
    'joint20_first_execution': {
        'seal': as_, 'sealed_members_checked_N': len(am), 'case_N': 20,
        'matched_N': matched, 'raw_mismatched_dimensions_N': differences,
        'literal_context_and_source_quote_checks_N': len(quotes),
        'manual_literal_quote_checks_N': len(manual['quotes']),
        'S1_vs_original_NULL_interpretation_boundary_preserved': True,
        'other_missing_standard_request_still_unresolved': True,
        'naturally_observed_only_IF_units_N': 0,
        'now_exposed_development_controls': True},
    'receiver': bind(__file__), 'classifier_calls_N': 0, 'model_dispatch_N': 0,
    'sample_draw_N': 0, 'new_human_results_N': 0, 'formal_metric_acceptance': False,
    'main_LLM_partial_labels_read': False, 'fresh_hidden12_content_read': False,
    'new_semantic_policy_adjudication': False, 'original_outputs_modified': False}
OUT.mkdir()
def save(path, v):
    with path.open('x', encoding='utf8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')
save(OUT / 'actual-reception.json', receipt)
save(OUT / 'output-seal.json', {'output_members': [bind(OUT / 'actual-reception.json')], 'self_excluded': True})
print(json.dumps({'status': receipt['status'], 'batch_N': 659, 'record_N': 4481,
                  'joint20_matches': matched, 'raw_dimension_mismatches': differences,
                  'classifier_calls_N': 0}, ensure_ascii=False))
