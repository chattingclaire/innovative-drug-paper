"""Close actual initial11 reviews. Offline only; never runs a model or edits outputs."""
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PRIVATE = ROOT.parent
WORK = PRIVATE.parents[1]
C09 = WORK / 'LLM编码/候选09-分步判读'
PROJECT = WORK.parents[1]

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bind(p):
    p = Path(p).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}

def read(p):
    return json.loads(Path(p).read_text())

def new(p, obj):
    with Path(p).open('x') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def load(name, p):
    s = importlib.util.spec_from_file_location(name, p)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m

checked = {}
def verify_tree(o):
    if isinstance(o, dict):
        if isinstance(o.get('path'), str) and 'sha256' in o:
            p = Path(o['path'])
            assert p.is_absolute() and p.is_file(), o
            assert sha(p) == o['sha256'], str(p)
            if 'bytes' in o:
                assert p.stat().st_size == o['bytes'], str(p)
            checked[str(p)] = bind(p)
        for v in o.values():
            verify_tree(v)
    elif isinstance(o, list):
        for v in o:
            verify_tree(v)

now = datetime.datetime.now(datetime.timezone.utc).isoformat()
review_path = PRIVATE / 'actual-stageB/candidate09_stageB11_full_semantic_review_PRIVATE.json'
review = read(review_path)
verify_tree(review)
assert review['confirmed_semantic_errors'] == 4
assert review['coverage']['all_actual_dimension_cells'] == 55
assert review['coverage']['not_prefilled_cells_independently_reviewed'] == 36
assert review['coverage']['hard_cells_matching'] == 15
assert review['coverage']['hard_cells_failed'] == 4
assert len(review['cases']) == 11

root_review = {
    'status': 'FAIL_ROOT_FULL11_STAGEB_SEMANTIC_REVIEW',
    'created_at_UTC': now,
    'reviewer': '/root',
    'actual_read_scope': 'Root actually read all11 original units and supplied necessary contexts during A review, all original A records, and all55 actual B labels/reasons, all28 literal evidence quotations, all22 I/F subtype fields, all11 S-quality fields and all7 top-level issues before this closure. The independent review was then read in full case-by-case.',
    'reviewed_n': 11,
    'reviewed_dimension_cells': 55,
    'root_confirmed_errors': review['confirmed_errors'],
    'root_conclusion': 'I2 explicitly includes substantive relative product-attribute changes without requiring demonstrated superiority or a named innovative-registration category. F4 includes concrete ordinary medication access channels. B received the complete raw materials and preserved A records but added narrower conditions. These four errors are not resolved by labeling them boundary_note.',
    'old_six_errors_fixed': 3,
    'old_six_errors_remaining': 3,
    'correct_protection_targets_preserved': 2,
    'correct_protection_targets_regressed': 1,
    'synthetic015_016_frozen_cells_matching': 10,
    'other36_dimensions': 'Individually reviewed; not prefilled or assumed zero. No additional confirmed error found in this11 pilot.',
    'precision_opinions_retained': review['precision_opinions'],
    'not_a_population_accuracy_or_external_human_validation_estimate': True,
    'independent_report': bind(review_path),
    'actual_B': bind(C09 / 'runs/initial11-stageB-first-run/all_predictions.json'),
    'actual_A': bind(C09 / 'runs/initial11-stageA-first-run/all_stageA_records.json'),
    'preoutput_partial_expectations': bind(PRIVATE / 'stageB_partial_expectations_PRIVATE_PREOUTPUT.json'),
    'originals_or_expectations_modified': False,
}
root_review_path = ROOT / 'root_stageB_full11_semantic_review.json'
new(root_review_path, root_review)
gate = {
    'status': 'FAIL_CONFIRMED_STAGEB_SEMANTIC_ERRORS_BLOCK_EXPANSION_AND_ADOPTION',
    'created_at_UTC': now,
    'scope': 'candidate09 initial11 actual StageB only',
    'root_review': bind(root_review_path),
    'independent_review': bind(review_path),
    'actual_B': root_review['actual_B'],
    'confirmed_errors': review['confirmed_errors'],
    'first_valid_response_retained': True,
    'StageA_PASS_not_retracted_or_misrepresented_as_B_PASS': True,
    'semantic_retry_authorized': False,
    'expanded_execution_authorized': False,
    'adoption_authorized': False,
    'decision': 'Keep actual09 FAIL immutable. A new general implementation must be frozen and pass actual correction and protection checks before any expanded targeted review. Do not overwrite A/B, hard expectations, human references or manuscript statistics.',
}
gate_path = ROOT / 'stageB_semantic_gate.json'
new(gate_path, gate)

runner = load('root09_offline_runner', C09 / 'run_candidate09.py')
runner.load_design()  # Integrity only; does not call main, execute_stage or CLI.
frozen_rows = [json.loads(s) for s in (PRIVATE / 'known11_inputs_ORIGINAL_FIELDS_PRIVATE_FROZEN.jsonl').read_text().splitlines() if s.strip()]
actual_A = read(C09 / 'runs/initial11-stageA-first-run/all_stageA_records.json')
actual_B = read(C09 / 'runs/initial11-stageB-first-run/all_predictions.json')
run_B = C09 / 'runs/initial11-stageB-first-run'
attempt = run_B / 'attempts/attempt-01'
packet = read(run_B / 'input_packet.json')
assert packet == runner.assemble_stageB_packet(frozen_rows, actual_A)
assert set(packet) == {'rows', 'stageA_records'}
assert packet['rows'] == frozen_rows
assert (attempt / 'input.json').read_bytes() == (run_B / 'input_packet.json').read_bytes()
request = runner.make_request('B', packet, (C09 / 'stageB_prompt.txt').read_text())
assert request.encode() == (run_B / 'request.txt').read_bytes() == (attempt / 'request.txt').read_bytes()
assert read(attempt / 'raw_output.json') == actual_B
assert (attempt / 'raw_output.json').read_bytes() == (run_B / 'all_predictions.json').read_bytes()
assert [json.loads(s) for s in (run_B / 'all_predictions.jsonl').read_text().splitlines()] == actual_B['rows']
validator = load('root09_offline_B_validator', C09 / 'runtime/validate_binary_output.py')
assert validator.validate(packet, actual_B) == []
base = load('root09_offline_base', C09 / 'runtime/run_production_v32.py')
events = (attempt / 'events.jsonl').read_text()
event_audit = base.event_audit(events)
event_binding = base.event_output_binding_audit(events, actual_B)
assert event_audit['tool_or_unknown_item_event_count'] == 0
assert event_audit['completed_turns'] == 1 and not event_audit['turn_errors']
assert event_binding['completed_agent_message_count'] == 1
assert event_binding['event_raw_full_object_equal'] and not event_binding['errors']
assert list((run_B / 'attempts').iterdir()) == [attempt]
metadata = read(attempt / 'run_metadata.json')
for key, filename in [('input_sha256', 'input.json'), ('request_sha256', 'request.txt'), ('raw_output_sha256', 'raw_output.json'), ('events_sha256', 'events.jsonl'), ('stderr_sha256', 'stderr.txt'), ('validation_sha256', 'validation.json'), ('tool_event_audit_sha256', 'tool_event_audit.json'), ('event_output_binding_audit_sha256', 'event_output_binding_audit.json')]:
    assert metadata[key] == sha(attempt / filename), key
assert metadata['exit_code'] == 0 and metadata['errors'] == []
assert metadata['requested_model'] == 'gpt-5.6-sol' and metadata['reasoning_effort'] == 'medium'
stderr = (attempt / 'stderr.txt').read_text()
tech = {
    'status': 'PASS_ROOT_ACTUAL_B_TECHNICAL_PROVENANCE_NOT_SEMANTIC_PASS',
    'created_at_UTC': now,
    'frozen_design_and_all_bound_files_current': True,
    'exact_original_rows_plus_original_same_ID_A_records': True,
    'request_exactly_locked_prompt_plus_only_allowed_packet': True,
    'one_actual_attempt_first_valid_only': True,
    'complete_event_message_equals_raw_equals_aggregate': True,
    'frozen_structure_literal_validator_errors': [],
    'event_audit': event_audit,
    'event_binding': event_binding,
    'stderr': {'bytes': len(stderr.encode()), 'nonempty_lines': len(stderr.splitlines()), 'sha256': sha(attempt / 'stderr.txt'), 'content_review_status': 'Retained; inspect actual lines separately. No semantic failure erased by successful exit.'},
    'provider_model_revision': 'Not exposed; requested CLI model only is verified.',
    'actual_request': bind(run_B / 'request.txt'),
    'metadata': bind(attempt / 'run_metadata.json'),
    'originals_modified': False,
    'new_model_calls_by_this_audit': 0,
    'new_model_CLI_invocations_by_this_audit': 0,
}
tech_path = ROOT / 'root_stageB_actual_technical_review.json'
new(tech_path, tech)

for relative in ['actual-stageA/candidate09_stageA11_full_semantic_review_PRIVATE.json', 'actual-stageB/candidate09_stageB_actual_request_fidelity_supplement.json', 'root-execution/stageA_semantic_gate.json']:
    verify_tree(read(PRIVATE / relative))
assert read(ROOT / 'stageA_semantic_gate.json')['status'].startswith('PASS')
source_expectations = {
    WORK / '整套编码采用记录.json': '40c974eac1fc1583e1627d743777f5e4388d1c7b2db3833801e3377c52ae206f',
    WORK / '本轮结果/创新药评价的注意力配置差异与协调路径.docx': '2335ad123737735ea5ae32234de323d3c7ae1ac0c23136d4d2eb7a2742b15db6',
    WORK / '本轮结果/编码复核说明与真人检验事项.docx': '11a01f77b5830c12f58b8bbc9ce446a273d9af206ea4e9ed2f6bcf8ea8604cbb',
}
for p, expected in source_expectations.items():
    assert sha(p) == expected, str(p)
run_files = [bind(p) for folder in ['initial11-stageA-first-run', 'initial11-stageB-first-run'] for p in sorted((C09 / 'runs' / folder).rglob('*')) if p.is_file()]
closure = {
    'status': 'CLOSED_ACTUAL_INITIAL11_A_PASS_B_FAIL_NOT_ADOPTED',
    'created_at_UTC': now,
    'actual_logical_requests': 2,
    'actual_model_attempts': 2,
    'both_first_technical_valid': True,
    'tool_events': 0,
    'unique_policy_or_control_units': 11,
    'stage_processing_records': 22,
    'final_coded_units': 11,
    'final_dimension_cells': 55,
    'A_semantic_status': 'PASS_NO_CONFIRMED_PROPOSITION_OR_CONTEXT_RELATION_ERROR_IN_ACTUAL11',
    'B_semantic_status': 'FAIL_4_CONFIRMED_DIMENSION_ERRORS',
    'root_A_gate': bind(ROOT / 'stageA_semantic_gate.json'),
    'root_B_gate': bind(gate_path),
    'root_B_technical_review': bind(tech_path),
    'root_B_semantic_review': bind(root_review_path),
    'independent_B_review': bind(review_path),
    'source_bindings_checked_recursively': list(checked.values()),
    'all_actual_run_files': run_files,
    'current_adoption_and_manuscript_unchanged': [bind(p) for p in source_expectations],
    'initial11_only_not_146_240_or_full_scope': True,
    'expanded_partial_rerun_or_full_rerun_executed': False,
    'new_kappa_or_attention_statistics_computed': False,
    'not_claimed': ['New09 adopted', 'Known-development diagnostic is population accuracy', 'StageA PASS guarantees StageB correctness', 'Scores or human references may be changed to pass', 'Failed09 may later be called passed without a separately frozen new implementation'],
    'next': 'Prioritize defensible partial review per user steering. First repair general StageB adherence to unchanged handbook; do not enlarge context machinery merely because B ignored preserved meaning. Then freeze affected scope, test corrections and protections, audit the complement, and recompute full derived-table statistics only after actual adoption.',
}
closure_path = ROOT / 'candidate09_initial11_actual_execution_review_closure.json'
new(closure_path, closure)
print(json.dumps({'gate': bind(gate_path), 'closure': bind(closure_path), 'recursive_source_bindings_verified': len(checked), 'actual_run_files_bound': len(run_files), 'new_model_calls': 0}, ensure_ascii=False))
