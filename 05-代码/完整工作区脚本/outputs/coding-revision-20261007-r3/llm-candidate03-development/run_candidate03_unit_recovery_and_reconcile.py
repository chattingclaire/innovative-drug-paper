"""Explicitly supplemented technical recovery. No original-run mutation."""
import datetime, json, pathlib, subprocess, sys
from candidate03_execution_audit_utils import audit, bind, canonical_sha, dump, lines, read, sha

H = pathlib.Path(__file__).resolve().parent
P = H / 'candidate03-batch115-unit-isolation-plan'
FULL = H / 'full-corpus-candidate03-material-v14-development'
PROMPT_SHA = '8576d9a1be10b0dd7b69b4c12367f4c357f55abf4ca30d979d5b333493089ba4'
INPUT_SHA = '6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'
BASELINE_SHA = 'c6a5672053aacc3e9839e0d04d8e457d1207a500682460bdacbbc4abee10c5aa'
METHOD = 'LLM-v32-candidate03-single-unit-reconciled-development'

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def check(b): assert sha(b['path']) == b['sha256'], b
def original_manifest():
    return {str(p.relative_to(FULL)): sha(p) for p in sorted(FULL.rglob('*')) if p.is_file() and '__pycache__' not in p.parts}

def main():
    plan_path = P / 'supplemental_technical_recovery_freeze.json'; plan = read(plan_path)
    auth_path = P / 'root_recovery_review_and_execution_authorization.json'; auth = read(auth_path)
    assert auth['status'] == 'passed_root_independent_recovery_review' and auth['plan_sha256'] == sha(plan_path)
    assert auth['new_calls_authorized'] == 25 and auth['technical_max_attempts'] == 75
    assert plan['permitted_original_terminal_failed_batches'] == [115]
    for b in [plan['source'], plan['prompt'], plan['recovery_input'], plan['diagnosis'], *plan['code_bindings'].values()]: check(b)
    run = pathlib.Path(plan['recovery_run']); out = pathlib.Path(plan['reconciled_run'])
    assert plan['prompt']['sha256'] == PROMPT_SHA and plan['source']['sha256'] == INPUT_SHA
    # Requiring all 197 final selection records and the original terminal summary
    # prevents overlap with the original 3-worker process.
    original, original_qa, validator = audit(FULL, 4924, 25, INPUT_SHA, PROMPT_SHA, [115])
    assert original_qa['accepted_batches'] == 196 and original_qa['accepted_rows'] == 4899
    if '--audit-only' in sys.argv:
        state = read(P / 'execution_state.json'); assert state['exit_code'] == 0
        assert state['command'] == plan['command']; check(state['original_manifest'])
        before = read(pathlib.Path(state['original_manifest']['path']))['files']
    else:
        assert len(sys.argv) == 1 and not run.exists() and not out.exists(), 'No overwrite or unplanned model rerun.'
        before = original_manifest()
        dump(P / 'original_run_immutable_manifest.json', {'files': before})
        state = {'status': 'authorized_technical_recovery_running', 'started_at': now(), 'plan': bind(plan_path), 'authorization': bind(auth_path), 'execution_driver': bind(pathlib.Path(__file__).resolve()), 'original_manifest': bind(P / 'original_run_immutable_manifest.json'), 'command': plan['command']}
        dump(P / 'execution_state.json', state)
        log = P / 'recovery_stdout.log'
        with log.open('w') as f:
            proc = subprocess.Popen(plan['command'], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
            state['runner_pid'] = proc.pid; dump(P / 'execution_state.json', state)
            for line in proc.stdout:
                f.write(line); f.flush(); print(line, end='', flush=True)
            state['exit_code'] = proc.wait()
        state['ended_at'] = now(); state['stdout'] = bind(log); dump(P / 'execution_state.json', state)
    assert before == original_manifest(), 'Original run changed during recovery.'
    if state['exit_code'] != 0:
        state['status'] = 'recovery_technical_incomplete_no_reconciled_aggregate'; dump(P / 'execution_state.json', state)
        raise RuntimeError('No extension beyond the fixed 25-ID recovery scope or three attempts per unit.')
    recovery, recovery_qa, _ = audit(run, 25, 1, plan['recovery_input']['sha256'], PROMPT_SHA, [])
    assert recovery_qa['accepted_batches'] == recovery_qa['accepted_rows'] == 25
    source = lines(pathlib.Path(plan['source']['path'])); recovered_source = lines(pathlib.Path(plan['recovery_input']['path']))
    assert recovered_source == source[114 * 25:115 * 25]
    assert [r['id'] for r in recovered_source] == plan['recovery_ids']
    rows = []; provenance = []; issues = []
    for bi in range(1, 198):
        components = [recovery[i] for i in range(1, 26)] if bi == 115 else [original[bi]]
        for component in components:
            raw = component['raw']; m = component['metadata']; a = component['attempt_path']
            assert len(raw['rows']) == len(component['packet']['rows'])
            rows.extend(raw['rows']); issues.extend(raw['issue_records'])
            for src, row in zip(component['packet']['rows'], raw['rows']):
                assert src['id'] == row['id']
                provenance.append({'id': row['id'], 'method_id': METHOD, 'original_production_batch': bi, 'source_kind': 'single_unit_protocol_supplement' if bi == 115 else 'original_full_run_first_valid_batch', 'actual_request_batch_size': len(component['packet']['rows']), 'actual_attempt_path': str(a), 'actual_prompt_sha256': m['prompt_sha256'], 'actual_request_sha256': m['request_sha256'], 'raw_output_sha256': m['raw_output_sha256'], 'events_sha256': m['events_sha256'], 'metadata_sha256': sha(a / 'run_metadata.json'), 'requested_model': m['requested_model'], 'reasoning_effort': m['reasoning_effort'], 'provider_internal_revision': m['provider_internal_model_revision'], 'source_row_canonical_sha256': canonical_sha(src), 'output_row_canonical_sha256': canonical_sha(row), 'all_five_labels_from_one_intact_actual_row': True, 'selection': 'first valid actual attempt within the explicitly bound protocol', 'release_scope': 'development comparison with disclosed technical protocol supplement'})
    assert len(rows) == len(provenance) == 4924
    assert [r['id'] for r in rows] == [r['id'] for r in source]
    aggregate = {'protocol_version': 'CAL-5D-20260926-v1.3', 'execution_version': 'LLM-binary-v32', 'release_stage': 'final_binary_labels', 'rows': rows, 'issue_records': issues}
    assert not validator.validate({'rows': source}, aggregate)
    assert sum(p['source_kind'] == 'single_unit_protocol_supplement' for p in provenance) == 25
    assert all(sha(H / p) == x for p, x in read(H / 'candidate03_preservation_hashes.json')['files'].items())
    assert sha(H.parent / 'llm-v32/full-production-candidate02-material-v14-source-citation-reconciled/all_predictions.jsonl') == BASELINE_SHA
    out.mkdir(exist_ok='--audit-only' in sys.argv)
    dump(out / 'all_predictions.json', aggregate)
    (out / 'all_predictions.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    (out / 'row_provenance.jsonl').write_text(''.join(json.dumps(p, ensure_ascii=False) + '\n' for p in provenance))
    dump(out / 'original_incomplete_run_QA.json', original_qa); dump(out / 'single_unit_recovery_QA.json', recovery_qa)
    known = [{'id': rid, 'frozen_input': next(r for r in source if r['id'] == rid), 'actual_full_run_row': next(r for r in rows if r['id'] == rid), 'note': 'Prior known semantic errors not assumed to repeat; actual complete row retained without repair.'} for rid in ['RECODE25-01562', 'RECODE25-02086']]
    dump(out / 'known_continuity_cases_preserved.json', known)
    summary = {'status': 'complete_reconciled_actual_development_with_disclosed_protocol_supplement', 'method_id': METHOD, 'n': 4924, 'source_production_batches': 197, 'original_accepted_batches': 196, 'original_terminal_failed_batches': [115], 'original_execution_status': original_qa['original_execution_status'], 'original_actual_attempts': original_qa['actual_attempts'], 'original_failed_attempts_preserved': original_qa['failed_attempts_preserved'], 'recovery_logical_single_unit_calls': 25, 'recovery_actual_attempts': recovery_qa['actual_attempts'], 'recovery_failed_attempts_preserved': recovery_qa['failed_attempts_preserved'], 'accepted_model_request_batches': 221, 'same_frozen_prompt_sha256': PROMPT_SHA, 'same_v14_input_sha256': INPUT_SHA, 'batch_partition_changed_only_for_original_batch115': True, 'original_max3_protocol_not_claimed_successful': True, 'new_requests_semantically_five_dimensional': True, 'references_or_metrics_used_to_select': False, 'rows_or_quotes_manually_changed': False, 'dimension_splicing': False, 'formal_adoption': False, 'independent_validation': False, 'all_240_exposed_development': True}
    dump(out / 'execution_summary.json', summary)
    qa = {'status': 'PASS', 'scope': 'Transparent reconciliation of original incomplete run and separately authorized single-unit recovery; technical identity, first-valid selection, literal evidence, complete intact rows only; not semantic accuracy', **{k: v for k, v in summary.items() if k != 'status'}, 'original_run_unchanged': before == original_manifest(), 'formal_candidate02_unchanged': True, 'candidate03_previous_artifacts_unchanged': True, 'output': bind(out / 'all_predictions.jsonl'), 'row_provenance': bind(out / 'row_provenance.jsonl'), 'original_incomplete_run_QA': bind(out / 'original_incomplete_run_QA.json'), 'recovery_QA': bind(out / 'single_unit_recovery_QA.json'), 'protocol_supplement': bind(plan_path), 'authorization': bind(auth_path)}
    assert qa['original_run_unchanged']; dump(out / 'full_execution_and_row_binding_QA.json', qa)
    binding = {'status': 'complete_actual_full_corpus_development_reconciled_QA_PASS', 'method_id': METHOD, 'run': str(out), 'n': 4924, 'batches': 221, 'batches_meaning': '196 original accepted requests plus 25 independent single-unit requests; not all197 original batches passed', 'source_production_batches': 197, 'original_terminal_failed_batches': [115], 'requested_model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'source_input': plan['source'], 'prompt': plan['prompt'], 'formal_adoption': False, 'independent_validation': False, 'all_240_exposed_development': True, 'protocol_supplement': bind(plan_path), 'root_authorization': bind(auth_path), 'original_run': str(FULL), 'recovery_run': str(run), 'original_execution_status': original_qa['original_execution_status']}
    for key, file in [('output', 'all_predictions.jsonl'), ('execution_summary', 'execution_summary.json'), ('row_provenance', 'row_provenance.jsonl'), ('technical_QA', 'full_execution_and_row_binding_QA.json'), ('original_run_QA', 'original_incomplete_run_QA.json'), ('recovery_QA', 'single_unit_recovery_QA.json'), ('known_continuity_cases', 'known_continuity_cases_preserved.json')]: binding[key] = bind(out / file)
    binding['run_plan'] = bind(plan_path)
    dump(out / 'full_development_binding.json', binding)
    state['status'] = 'complete_recovery_and_transparent_reconciliation_QA_PASS'; state['reconciled_binding'] = bind(out / 'full_development_binding.json'); dump(P / 'execution_state.json', state)
    print(json.dumps({'status': state['status'], 'binding': state['reconciled_binding'], 'summary': summary}, ensure_ascii=False), flush=True)

if __name__ == '__main__': main()
