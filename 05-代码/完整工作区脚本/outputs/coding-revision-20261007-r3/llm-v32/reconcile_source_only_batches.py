"""Whole-batch source repair with actual five-dimensional model provenance.

Never read reference labels, assign a label, edit an output quote or choose by
accuracy. Reuse requires exact equality of the entire semantic input batch.
Changed/failed batches receive the same fixed prompt and actual new calls.
"""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    assert not path.exists(), f'Immutable artifact already exists: {path}'
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def rows(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def make_request(prompt, packet):
    return (prompt + '\n\n--- 本批冻结盲法输入 ---\n'
            + json.dumps(packet, ensure_ascii=False)
            + '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。')


def load_runner():
    path = HERE / 'run_production_v32.py'
    spec = importlib.util.spec_from_file_location('fixed_runner', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(old_run, new_input, output, expected_input_sha):
    """Call only after every original production batch has a selection record."""
    old_plan = read(old_run / 'run_plan.json')
    old_input = old_run / old_plan['frozen_input_relative_path']
    assert sha(old_input) == old_plan['input_sha256']
    assert sha(new_input) == expected_input_sha
    old, new = rows(old_input), rows(new_input)
    assert len(old) == len(new) == 4924
    assert len({r['id'] for r in new}) == len(new)
    for a, b in zip(old, new):
        assert a['id'] == b['id'] and a['text'] == b['text']
        assert a['source_title'] == b['source_title'] and a['pages'] == b['pages']
    size = old_plan['batch_size']
    batches, records, changed_ids = [], [], []
    for offset in range(0, len(new), size):
        index = offset // size + 1
        batch = new[offset:offset + size]
        old_batch = old[offset:offset + size]
        selection_path = old_run / 'batches' / f'batch-{index:04d}' / 'selection.json'
        assert selection_path.exists(), f'Original batch {index} still running'
        selection = read(selection_path)
        changed = old_batch != batch
        failed = selection['status'] != 'accepted_first_valid_actual_attempt'
        changed_ids.extend(b['id'] for a, b in zip(old_batch, batch) if a != b)
        records.append({'batch': index, 'n': len(batch), 'changed_input': changed,
                        'old_execution_failed': failed,
                        'action': 'rerun_complete_batch' if changed or failed else 'reuse_exact_batch',
                        'old_selection_path': str(selection_path),
                        'old_selection_sha256': sha(selection_path)})
        if changed or failed:
            batches.append(index)
    runner = load_runner()
    assert old_plan['runner_sha256'] == sha(HERE / 'run_production_v32.py')
    assert old_plan['validator_sha256'] == sha(runner.VALIDATOR)
    assert old_plan['schema_sha256'] == sha(runner.SCHEMA)
    assert old_plan['prompt_sha256'] == sha(old_run / 'frozen_prompt.txt')
    runner.no_reference_fields(new)
    output.mkdir(exist_ok=False, parents=True)
    (output / 'frozen_input.jsonl').write_bytes(new_input.read_bytes())
    for name in ('frozen_prompt.txt', 'frozen_schema.json', 'frozen_validator.py', 'frozen_runner.py'):
        (output / name).write_bytes((old_run / name).read_bytes())
    plan = {'purpose': 'source-only whole-batch repair; all five dimensions from actual v32 calls',
            'model': old_plan['model'], 'reasoning_effort': old_plan['reasoning_effort'],
            'original_run': str(old_run), 'original_plan_sha256': sha(old_run / 'run_plan.json'),
            'new_input_path': str(new_input), 'new_input_sha256': expected_input_sha,
            'prompt_sha256': old_plan['prompt_sha256'], 'batch_size': size,
            'n': len(new), 'batch_count': len(records), 'changed_ids': changed_ids,
            'rerun_batches': batches, 'batch_records': records,
            'selection_rule': old_plan['selection_rule'],
            'max_attempts': old_plan['max_attempts'],
            'labels_or_metrics_read': False, 'source_order_and_unit_text_unchanged': True,
            'reconciler_sha256': sha(Path(__file__))}
    write_new(output / 'source_reconciliation_plan.json', plan)
    return plan


def execute(output, workers):
    plan = read(output / 'source_reconciliation_plan.json')
    runner = load_runner()
    frozen = output / 'frozen_input.jsonl'
    assert sha(frozen) == plan['new_input_sha256']
    prompt_path = output / 'frozen_prompt.txt'
    assert sha(prompt_path) == plan['prompt_sha256']
    original_plan = read(Path(plan['original_run']) / 'run_plan.json')
    assert sha(runner.CLI) == original_plan['cli_binary_sha256']
    assert sha(HERE / 'run_production_v32.py') == original_plan['runner_sha256']
    new = rows(frozen)
    prompt = prompt_path.read_text()
    cli_version = subprocess.run([str(runner.CLI), '--version'], capture_output=True,
                                 text=True, check=True).stdout.strip()
    assert cli_version == original_plan['cli_version']

    def call(index):
        dest = output / 'batches' / f'batch-{index:04d}'
        if dest.exists():
            assert (dest / 'selection.json').exists(), 'Interrupted batch requires explicit recovery'
            return
        dest.mkdir(parents=True)
        offset = (index - 1) * plan['batch_size']
        packet = {'rows': new[offset:offset + plan['batch_size']]}
        write_new(dest / 'input.json', packet)
        request = make_request(prompt, packet)
        (dest / 'request.txt').write_text(request)
        attempts, selected = [], None
        for ai in range(1, plan['max_attempts'] + 1):
            attempt = dest / 'attempts' / f'attempt-{ai:02d}'
            meta = runner.run_attempt(attempt, packet, request, plan['prompt_sha256'],
                                      cli_version, original_plan['cli_binary_sha256'], 1800)
            attempts.append({'attempt': ai, 'relative_path': str(attempt.relative_to(output)),
                             'metadata_sha256': sha(attempt / 'run_metadata.json'),
                             'status': meta['status'], 'raw_output_sha256': meta['raw_output_sha256'],
                             'events_sha256': meta['events_sha256'],
                             'tool_event_count': meta['tool_event_count'], 'errors': meta['errors']})
            print(json.dumps({'batch': index, 'attempt': ai, 'status': meta['status'],
                              'errors': meta['errors']}, ensure_ascii=False), flush=True)
            if meta['status'] == 'accepted_structural_literal_zero_tools':
                selected = attempt
                break
            if ai < plan['max_attempts']:
                time.sleep(5 * ai)
        write_new(dest / 'selection.json', {
            'batch': index,
            'status': 'accepted_first_valid_actual_attempt' if selected else 'all_attempts_failed_preserved',
            'input_n': len(packet['rows']), 'ids': [r['id'] for r in packet['rows']],
            'selected_relative_path': str(selected.relative_to(output)) if selected else None,
            'selected_output_sha256': sha(selected / 'raw_output.json') if selected else None,
            'attempts': attempts, 'selection_uses_metric_or_label_values': False})

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        for future in concurrent.futures.as_completed([pool.submit(call, i) for i in plan['rerun_batches']]):
            future.result()


def seal(output):
    plan = read(output / 'source_reconciliation_plan.json')
    assert plan['reconciler_sha256'] == sha(Path(__file__))
    new = rows(output / 'frozen_input.jsonl')
    assert sha(output / 'frozen_input.jsonl') == plan['new_input_sha256']
    original = Path(plan['original_run'])
    runner = load_runner()
    assert sha(output / 'frozen_prompt.txt') == plan['prompt_sha256']
    prompt = (output / 'frozen_prompt.txt').read_text()
    aggregate = {'protocol_version': 'CAL-5D-20260926-v1.3', 'execution_version': 'LLM-binary-v32',
                 'release_stage': 'final_binary_labels', 'rows': [], 'issue_records': []}
    lineage, all_attempts, tools = [], 0, 0
    for record in plan['batch_records']:
        index = record['batch']
        reused = record['action'] == 'reuse_exact_batch'
        run = original if reused else output
        selection_path = run / 'batches' / f'batch-{index:04d}' / 'selection.json'
        if reused:
            assert sha(selection_path) == record['old_selection_sha256']
        selection = read(selection_path)
        assert selection['status'] == 'accepted_first_valid_actual_attempt'
        selected = run / selection['selected_relative_path']
        offset = (index - 1) * plan['batch_size']
        packet = {'rows': new[offset:offset + plan['batch_size']]}
        assert read(selected / 'input.json') == packet, 'Cannot reuse any changed semantic input'
        meta = read(selected / 'run_metadata.json')
        assert (selected / 'request.txt').read_text() == make_request(prompt, packet)
        assert meta['request_sha256'] == sha(selected / 'request.txt')
        assert meta['input_sha256'] == sha(selected / 'input.json')
        assert meta['prompt_sha256'] == plan['prompt_sha256']
        assert meta['requested_model'] == plan['model'] and meta['reasoning_effort'] == plan['reasoning_effort']
        assert meta['tool_event_count'] == 0 and meta['status'] == 'accepted_structural_literal_zero_tools'
        assert sha(selected / 'raw_output.json') == selection['selected_output_sha256']
        first_valid = None
        for attempt_record in selection['attempts']:
            attempt = run / attempt_record['relative_path']
            assert sha(attempt / 'run_metadata.json') == attempt_record['metadata_sha256']
            recorded_meta = read(attempt / 'run_metadata.json')
            assert sha(attempt / 'events.jsonl') == recorded_meta['events_sha256']
            audit = runner.event_audit((attempt / 'events.jsonl').read_text())
            assert audit == read(attempt / 'tool_event_audit.json')
            assert audit['tool_or_unknown_item_event_count'] == attempt_record['tool_event_count']
            assert read(attempt / 'input.json') == packet
            assert (attempt / 'request.txt').read_text() == make_request(prompt, packet)
            if recorded_meta['status'] == 'accepted_structural_literal_zero_tools' and first_valid is None:
                first_valid = attempt
        assert first_valid == selected, 'Selected attempt must be chronological first valid'
        raw = read(selected / 'raw_output.json')
        assert not runner.v.validate(packet, raw)
        # Exact raw row objects: no label/quote editing and no dimension splicing.
        aggregate['rows'].extend(raw['rows'])
        aggregate['issue_records'].extend(raw['issue_records'])
        lineage.append({'batch': index, 'action': record['action'],
                        'selected_raw_path': str(selected / 'raw_output.json'),
                        'selected_raw_sha256': sha(selected / 'raw_output.json'),
                        'selection_path': str(selection_path), 'selection_sha256': sha(selection_path),
                        'input_sha256': sha(selected / 'input.json'),
                        'metadata_sha256': sha(selected / 'run_metadata.json'),
                        'all_five_dimensions_from_one_actual_raw_row': True})
        all_attempts += len(selection['attempts'])
        tools += sum(a['tool_event_count'] for a in selection['attempts'])
    assert not runner.v.validate({'rows': new}, aggregate)
    write_new(output / 'all_predictions.json', aggregate)
    target = output / 'all_predictions.jsonl'
    assert not target.exists()
    target.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in aggregate['rows']))
    write_new(output / 'batch_lineage.json', lineage)
    summary = {'status': 'complete_actual_five_dimension_calls_with_source_only_batch_repair',
               'n': len(new), 'batch_count': len(lineage),
               'new_whole_batches': len(plan['rerun_batches']),
               'reused_exact_input_batches': len(lineage) - len(plan['rerun_batches']),
               'new_input_sha256': plan['new_input_sha256'], 'prompt_sha256': plan['prompt_sha256'],
               'output_sha256': sha(target), 'lineage_sha256': sha(output / 'batch_lineage.json'),
               'selected_branch_actual_attempt_count': all_attempts,
               'selected_branch_all_attempt_tool_events': tools,
               'superseded_original_attempts_retained_in_original_run': True,
               'old_three_dimension_outputs_used': False, 'reference_label_or_metric_selection': False,
               'semantic_validity_not_proven_by_structure': True}
    write_new(output / 'execution_summary.json', summary)
    print(json.dumps(summary, ensure_ascii=False), flush=True)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=['prepare', 'execute', 'seal'])
    parser.add_argument('--output', required=True)
    parser.add_argument('--old-run')
    parser.add_argument('--new-input')
    parser.add_argument('--expected-input-sha256')
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if args.mode == 'prepare':
        assert args.old_run and args.new_input and args.expected_input_sha256
        plan = prepare(Path(args.old_run).resolve(), Path(args.new_input).resolve(), output,
                       args.expected_input_sha256)
        print(json.dumps({'rerun_batches': plan['rerun_batches'],
                          'changed_ids_n': len(plan['changed_ids'])}), flush=True)
    elif args.mode == 'execute':
        assert 1 <= args.workers <= 12
        execute(output, args.workers)
    else:
        seal(output)


if __name__ == '__main__':
    main()
