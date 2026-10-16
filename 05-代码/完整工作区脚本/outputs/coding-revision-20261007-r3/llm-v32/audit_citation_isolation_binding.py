"""Audit execution provenance only. Never load references or performance metrics."""
import argparse
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    run = Path(args.run).resolve()
    assert run.is_relative_to(HERE)
    output = Path(args.output).resolve()
    assert output.is_relative_to(HERE) and not output.exists()
    plan = read(run / 'source_reconciliation_plan.json')
    summary = read(run / 'execution_summary.json')
    helper = HERE / 'reconcile_source_only_batches_partial.py'
    assert sha(helper) == plan['reconciler_sha256'] == sha(run / 'frozen_reconciler.py')
    spec = importlib.util.spec_from_file_location('execution_only_auditor', helper)
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    runner = h.load_runner()
    frozen_runtime = read(run / 'execution_runtime_binding.json')
    assert frozen_runtime == plan['execution_runtime']
    post_execution_runtime = h.runtime_binding(runner)
    assert post_execution_runtime == frozen_runtime, 'Execution environment changed since frozen startup binding'
    source = rows(run / 'frozen_input.jsonl')
    predictions = rows(run / 'all_predictions.jsonl')
    aggregate = read(run / 'all_predictions.json')
    lineage = read(run / 'batch_lineage.json')
    provenance = rows(run / 'row_provenance.jsonl')
    assert len(source) == len(predictions) == len(provenance) == 4924
    assert [r['id'] for r in source] == [r['id'] for r in predictions] == [r['id'] for r in provenance]
    assert aggregate['rows'] == predictions
    assert not runner.v.validate({'rows': source}, aggregate)
    assert len(lineage) == plan['batch_count'] == 197
    assert sha(run / 'frozen_input.jsonl') == plan['new_input_sha256'] == summary['new_input_sha256']
    assert sha(run / 'all_predictions.jsonl') == summary['output_sha256']
    assert sha(run / 'row_provenance.jsonl') == summary['row_provenance_sha256']
    assert sha(run / 'batch_lineage.json') == summary['lineage_sha256']
    base = (run / 'frozen_prompt.txt').read_bytes()
    assert sha(run / 'frozen_prompt.txt') == h.BASE_PROMPT_SHA
    if plan['technical_batches']:
        appendix = (run / 'technical_format_clarification.txt').read_bytes()
        technical = (run / 'frozen_technical_prompt.txt').read_bytes()
        assert technical == base + appendix
        assert sha(run / 'frozen_technical_prompt.txt') == plan['technical_prompt_sha256']
        assert sha(run / 'technical_format_clarification.txt') == plan['technical_appendix_sha256']
    actual_call_rows, original_failures = [], []
    for record, branch in zip(plan['batch_records'], lineage):
        index = record['batch']
        assert index == branch['batch']
        offset = (index - 1) * plan['batch_size']
        packet = {'rows': source[offset:offset + plan['batch_size']]}
        origin = Path(branch['actual_origin_run'])
        assert origin.is_relative_to(HERE)
        sp = origin / 'batches' / f'batch-{index:04d}' / 'selection.json'
        assert sha(sp) == branch['selection_sha256']
        selection = read(sp)
        request = h.make_request(h.effective_prompt(base.decode(), bool(record['technical_version'])), packet)
        actual = h.audit_selection(origin, index, selection, packet, request,
                                   record['effective_prompt_sha256'], runner)
        meta = read(actual / 'run_metadata.json')
        origin_runtime_path = origin / 'execution_runtime_binding.json'
        if origin_runtime_path.exists():
            origin_runtime = read(origin_runtime_path)
            origin_plan = read(origin / 'source_reconciliation_plan.json')
            assert origin_runtime == origin_plan['execution_runtime'] == branch['execution_runtime']
            assert origin_runtime['reported_cli_version'] == meta['cli_version']
            assert origin_runtime['launcher_sha256'] == meta['cli_binary_sha256']
        raw = read(actual / 'raw_output.json')
        assert predictions[offset:offset + len(packet['rows'])] == raw['rows']
        assert branch['actual_prompt_sha256'] == meta['prompt_sha256']
        assert branch['actual_request_sha256'] == meta['request_sha256']
        assert branch['selected_raw_sha256'] == sha(actual / 'raw_output.json')
        for p in provenance[offset:offset + len(packet['rows'])]:
            assert {k: v for k, v in p.items() if k != 'id'} == branch
        actual_call_rows.append({'batch': index, 'origin': str(origin),
                                 'actual_prompt_sha256': meta['prompt_sha256'],
                                 'actual_cli_version': meta['cli_version'],
                                 'selected_attempt': actual.name,
                                 'attempt_count': len(selection['attempts']),
                                 'n': len(packet['rows'])})
    for origin in plan['ordered_origin_runs']:
        origin = Path(origin)
        failures = []
        for sp in sorted((origin / 'batches').glob('batch-*/selection.json')):
            selection = read(sp)
            if selection['status'] != 'accepted_first_valid_actual_attempt':
                failures.append({'batch': selection['batch'], 'selection_path': str(sp),
                                 'selection_sha256': sha(sp), 'status': selection['status'],
                                 'failed_attempt_count': len(selection['attempts'])})
        original_failures.append({'run': str(origin), 'failures_preserved': failures})
    result = {'status': 'execution_provenance_QA_passed',
              'run': str(run), 'input_sha256': plan['new_input_sha256'],
              'n': len(source), 'batch_count': len(lineage),
              'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium',
              'base_semantic_prompt_sha256': plan['prompt_sha256'],
              'technical_version': plan['technical_version'],
              'technical_prompt_sha256': plan['technical_prompt_sha256'],
              'technical_appendix_sha256': plan['technical_appendix_sha256'],
              'actual_prompt_row_counts': dict(Counter(p['actual_prompt_sha256'] for p in provenance)),
              'actual_cli_version_row_counts': dict(Counter(p['execution_runtime']['reported_cli_version'] for p in provenance)),
              'execution_runtime_start_end_hashes_equal': True,
              'post_execution_runtime': post_execution_runtime,
              'all_actual_prompts_byte_identical': summary['all_actual_prompts_byte_identical'],
              'complete_five_dimension_raw_rows_preserved': True,
              'raw_output_rows_or_quotes_edited': False,
              'first_valid_chronological_selection_verified': True,
              'whole_request_identity_verified_per_batch': True,
              'zero_tool_events_in_selected_attempts_verified': True,
              'partial_prior_runs_not_claimed_complete': True,
              'reference_labels_or_performance_metrics_read': False,
              'semantic_correctness_assessed': False,
              'source_version_inferred_from_execution': False,
              'statistical_release_requires_independent_final_material_binding': True,
              'artifacts': {name: {'path': str(run / name), 'sha256': sha(run / name)} for name in
                            ('source_reconciliation_plan.json', 'execution_summary.json', 'all_predictions.jsonl',
                             'batch_lineage.json', 'row_provenance.jsonl', 'execution_runtime_binding.json')},
              'actual_batches': actual_call_rows, 'historical_failed_branches': original_failures,
              'audit_script_sha256': sha(Path(__file__))}
    auditor_snapshot = run / 'frozen_execution_auditor.py'
    if auditor_snapshot.exists():
        assert sha(auditor_snapshot) == sha(Path(__file__))
    else:
        auditor_snapshot.write_bytes(Path(__file__).read_bytes())
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k:result[k] for k in ('status','n','batch_count','actual_prompt_row_counts','actual_cli_version_row_counts')},ensure_ascii=False))


if __name__ == '__main__':
    main()
