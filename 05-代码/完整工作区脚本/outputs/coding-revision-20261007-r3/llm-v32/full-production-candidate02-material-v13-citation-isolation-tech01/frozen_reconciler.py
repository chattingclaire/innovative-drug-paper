"""Whole-batch source repair with actual five-dimensional model provenance.

Never read reference labels, assign a label, edit an output quote or choose by
accuracy. Reuse requires exact equality of the entire semantic input batch.
Changed/failed batches receive the same fixed prompt and actual new calls.
An explicitly ordered prior source-repair run may supply an exact whole-batch
request even if other batches failed. Prior runs remain explicitly partial.
The order is frozen before any new call; no metric is ever consulted.
Optional citation-isolation-tech01 only clarifies literal quote ownership and is
bound as a distinct effective prompt, per batch, with at most three actual calls.
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
BASE_PROMPT_SHA = '682770e2fb6f1a6b8b7ba1703f6900d7ee0d586179282b94c14e0b23feec300e'
TECH_VERSION = 'citation-isolation-tech01'
TECH_APPENDIX = '''\n\n【引文格式澄清：citation-isolation-tech01】
以下仅明确既有逐字引文的所属记录与复制格式，不改变五维定义、纳入排除标准、语境使用标准或独立判断要求。
对输出中每一个 id，source=unit 的 quote 必须逐字复制输入中同一 id 的 text 内的一个连续片段；source=context 的 quote 必须逐字复制输入中同一 id 的 contexts 内某一实际正文字符串中的一个连续片段。
同批其他 rows 的 text 或 contexts 不属于当前 id 的可引用字符串，即使来源标题相同或内容相邻也不能混用。引用时保留原有字符、空格和标点，不改写，不拼接，不加省略号。
提交前逐条核对每个 quote 的所属 id、source 和连续逐字匹配。五维标签、理由和子类型仍依据此前完整规范及当前 id 的完整给定材料重新独立判断，不依据其他记录或历史输出。\n'''


def effective_prompt(prompt, technical=False):
    return prompt + TECH_APPENDIX if technical else prompt


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def checked_path(root, relative):
    target = (root / relative).resolve()
    assert target.is_relative_to(root.resolve()), 'Artifact must remain within its actual run'
    return target


def audit_selection(run, index, selection, packet, request, prompt_sha, runner):
    """Audit real attempts; never infer acceptance from a prior aggregate."""
    assert selection['batch'] == index
    assert selection['status'] == 'accepted_first_valid_actual_attempt'
    assert selection['ids'] == [r['id'] for r in packet['rows']]
    assert selection['input_n'] == len(packet['rows'])
    assert selection['selection_uses_metric_or_label_values'] is False
    selected = checked_path(run, selection['selected_relative_path'])
    first_valid = None
    assert selection['attempts']
    for ai, item in enumerate(selection['attempts'], 1):
        assert item['attempt'] == ai
        attempt = checked_path(run, item['relative_path'])
        assert sha(attempt / 'run_metadata.json') == item['metadata_sha256']
        meta = read(attempt / 'run_metadata.json')
        assert read(attempt / 'input.json') == packet
        assert (attempt / 'request.txt').read_text() == request
        assert sha(attempt / 'input.json') == meta['input_sha256']
        assert sha(attempt / 'request.txt') == meta['request_sha256']
        assert meta['prompt_sha256'] == prompt_sha
        assert meta['requested_model'] == 'gpt-5.6-sol' and meta['reasoning_effort'] == 'medium'
        assert meta['label_or_metric_selection'] is False
        assert meta['status'] == item['status'] and meta['errors'] == item['errors']
        for filename, key in [('events.jsonl', 'events_sha256'), ('raw_stderr.txt', 'stderr_sha256'),
                              ('tool_event_audit.json', 'tool_event_audit_sha256'),
                              ('validation.json', 'validation_sha256')]:
            assert sha(attempt / filename) == meta[key]
        audit = runner.event_audit((attempt / 'events.jsonl').read_text())
        assert audit == read(attempt / 'tool_event_audit.json')
        assert audit['tool_or_unknown_item_event_count'] == meta['tool_event_count'] == item['tool_event_count']
        if meta['raw_output_sha256'] is not None:
            assert sha(attempt / 'raw_output.json') == meta['raw_output_sha256'] == item['raw_output_sha256']
        if meta['status'] == 'accepted_structural_literal_zero_tools':
            assert meta['exit_code'] == 0 and meta['execution_error'] is None
            assert meta['tool_event_count'] == 0 and not meta['errors']
            assert audit['completed_turns'] == 1 and not audit['turn_errors']
            assert all(m == 'gpt-5.6-sol' for m in audit['observed_model_fields'])
            raw = read(attempt / 'raw_output.json')
            assert not runner.v.validate(packet, raw)
            if first_valid is None:
                first_valid = attempt
    assert first_valid == selected, 'Only chronological first valid attempt is eligible'
    assert sha(selected / 'raw_output.json') == selection['selected_output_sha256']
    return selected


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


def prepare(old_run, new_input, output, expected_input_sha, reuse_runs, technical_batches=()):
    """Call only after every original production batch has a selection record."""
    old_plan = read(old_run / 'run_plan.json')
    assert old_plan['prompt_sha256'] == BASE_PROMPT_SHA
    assert old_plan['model'] == 'gpt-5.6-sol' and old_plan['reasoning_effort'] == 'medium'
    runner = load_runner()
    assert old_plan['runner_sha256'] == sha(HERE / 'run_production_v32.py')
    assert old_plan['validator_sha256'] == sha(runner.VALIDATOR)
    assert old_plan['schema_sha256'] == sha(runner.SCHEMA)
    assert old_plan['prompt_sha256'] == sha(old_run / 'frozen_prompt.txt')
    prompt = (old_run / 'frozen_prompt.txt').read_text()
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
    technical_batches = sorted(set(technical_batches))
    assert all(1 <= i <= (len(new) + size - 1) // size for i in technical_batches)
    batches, records, changed_ids = [], [], []
    extra_bindings = []
    for prior in reuse_runs:
        pp = prior / 'source_reconciliation_plan.json'
        ps = prior / 'execution_summary.json'
        assert pp.exists(), 'Prior source-repair plan required; a summary is optional'
        prior_plan = read(pp)
        assert prior_plan['prompt_sha256'] == old_plan['prompt_sha256']
        assert prior_plan['model'] == old_plan['model']
        assert prior_plan['reasoning_effort'] == old_plan['reasoning_effort']
        assert sha(prior / 'frozen_prompt.txt') == old_plan['prompt_sha256']
        selections = []
        for sp in sorted((prior / 'batches').glob('batch-*/selection.json')):
            s = read(sp)
            selections.append({'batch': s['batch'], 'status': s['status'],
                               'path': str(sp), 'sha256': sha(sp)})
        extra_bindings.append({'path': str(prior), 'plan_sha256': sha(pp),
                               'summary_sha256': sha(ps) if ps.exists() else None,
                               'recorded_summary_status': read(ps)['status'] if ps.exists() else 'absent_unsealed',
                               'reuse_scope': 'actual accepted batches only; no assertion that prior run completed',
                               'actual_selection_records': selections})
    for offset in range(0, len(new), size):
        index = offset // size + 1
        batch = new[offset:offset + size]
        batch_prompt = effective_prompt(prompt, index in technical_batches)
        batch_prompt_sha = digest(batch_prompt)
        packet = {'rows': batch}
        expected_request = make_request(batch_prompt, packet)
        old_batch = old[offset:offset + size]
        selection_path = old_run / 'batches' / f'batch-{index:04d}' / 'selection.json'
        assert selection_path.exists(), f'Original batch {index} still running'
        selection = read(selection_path)
        changed = old_batch != batch
        failed = selection['status'] != 'accepted_first_valid_actual_attempt'
        changed_ids.extend(b['id'] for a, b in zip(old_batch, batch) if a != b)
        origin, selected_path = None, None
        # Original actual run has fixed precedence, followed by explicitly
        # supplied source-repair runs. Compare whole input, never label values.
        for possible in [old_run, *reuse_runs]:
            sp = possible / 'batches' / f'batch-{index:04d}' / 'selection.json'
            if not sp.exists():
                continue
            candidate_selection = read(sp)
            if candidate_selection['status'] != 'accepted_first_valid_actual_attempt':
                continue
            raw_dir = possible / candidate_selection['selected_relative_path']
            if read(raw_dir / 'input.json') != {'rows': batch}:
                continue
            meta = read(raw_dir / 'run_metadata.json')
            if meta['prompt_sha256'] != batch_prompt_sha:
                continue
            if (raw_dir / 'request.txt').read_text() != expected_request:
                continue
            audit_selection(possible, index, candidate_selection, packet,
                            expected_request, batch_prompt_sha, runner)
            origin, selected_path = possible, sp
            break
        records.append({'batch': index, 'n': len(batch), 'changed_input': changed,
                        'effective_prompt_sha256': batch_prompt_sha,
                        'expected_request_sha256': digest(expected_request),
                        'technical_version': TECH_VERSION if index in technical_batches else None,
                        'max_attempts': 3 if index in technical_batches else old_plan['max_attempts'],
                        'old_execution_failed': failed,
                        'action': 'reuse_exact_batch' if origin else 'rerun_complete_batch',
                        'origin_run': str(origin) if origin else None,
                        'origin_selection_path': str(selected_path) if origin else None,
                        'origin_selection_sha256': sha(selected_path) if origin else None,
                        'old_selection_path': str(selection_path),
                        'old_selection_sha256': sha(selection_path)})
        if origin is None:
            batches.append(index)
    runner.no_reference_fields(new)
    output.mkdir(exist_ok=False, parents=True)
    (output / 'frozen_input.jsonl').write_bytes(new_input.read_bytes())
    for name in ('frozen_prompt.txt', 'frozen_schema.json', 'frozen_validator.py', 'frozen_runner.py'):
        (output / name).write_bytes((old_run / name).read_bytes())
    if technical_batches:
        (output / 'frozen_technical_prompt.txt').write_text(effective_prompt(prompt, True))
        (output / 'technical_format_clarification.txt').write_text(TECH_APPENDIX)
    plan = {'purpose': 'source-only whole-batch repair; all five dimensions from actual v32 calls',
            'model': old_plan['model'], 'reasoning_effort': old_plan['reasoning_effort'],
            'original_run': str(old_run), 'original_plan_sha256': sha(old_run / 'run_plan.json'),
            'additional_actual_runs_in_frozen_precedence_order': extra_bindings,
            'ordered_origin_runs': [str(old_run), *[str(p) for p in reuse_runs]],
            'reuse_rule': 'original then explicit prior source-repair runs; first audited accepted complete batch with exactly equal final input, effective prompt, and entire request; prior runs may be partial; otherwise new complete batch; never inspect correctness',
            'technical_version': TECH_VERSION if technical_batches else None,
            'technical_batches': technical_batches,
            'technical_prompt_sha256': digest(effective_prompt(prompt, True)) if technical_batches else None,
            'technical_appendix_sha256': digest(TECH_APPENDIX) if technical_batches else None,
            'technical_reason': 'repeated cross-row context quotation rejected by unchanged literal validator; generic same-ID quote ownership clarification only' if technical_batches else None,
            'technical_retry_limit': 3 if technical_batches else None,
            'technical_version_is_same_semantic_manual_with_distinct_request': True,
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
    assert plan['reconciler_sha256'] == sha(Path(__file__))
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
    if plan['technical_batches']:
        assert sha(output / 'frozen_technical_prompt.txt') == plan['technical_prompt_sha256']
        assert sha(output / 'technical_format_clarification.txt') == plan['technical_appendix_sha256']
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
        record = plan['batch_records'][index - 1]
        request = make_request(effective_prompt(prompt, bool(record['technical_version'])), packet)
        assert digest(request) == record['expected_request_sha256']
        (dest / 'request.txt').write_text(request)
        attempts, selected = [], None
        for ai in range(1, record['max_attempts'] + 1):
            attempt = dest / 'attempts' / f'attempt-{ai:02d}'
            meta = runner.run_attempt(attempt, packet, request, record['effective_prompt_sha256'],
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
            if ai < record['max_attempts']:
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
    original_plan = read(original / 'run_plan.json')
    assert sha(original / 'run_plan.json') == plan['original_plan_sha256']
    assert sha(HERE / 'run_production_v32.py') == original_plan['runner_sha256']
    assert sha(runner.VALIDATOR) == original_plan['validator_sha256']
    assert sha(runner.SCHEMA) == original_plan['schema_sha256']
    assert sha(output / 'frozen_prompt.txt') == plan['prompt_sha256']
    if plan['technical_batches']:
        assert sha(output / 'frozen_technical_prompt.txt') == plan['technical_prompt_sha256']
        assert sha(output / 'technical_format_clarification.txt') == plan['technical_appendix_sha256']
    prompt = (output / 'frozen_prompt.txt').read_text()
    aggregate = {'protocol_version': 'CAL-5D-20260926-v1.3', 'execution_version': 'LLM-binary-v32',
                 'release_stage': 'final_binary_labels', 'rows': [], 'issue_records': []}
    lineage, row_provenance, all_attempts, tools = [], [], 0, 0
    for record in plan['batch_records']:
        index = record['batch']
        reused = record['action'] == 'reuse_exact_batch'
        run = Path(record['origin_run']) if reused else output
        selection_path = run / 'batches' / f'batch-{index:04d}' / 'selection.json'
        if reused:
            assert str(selection_path) == record['origin_selection_path']
            assert sha(selection_path) == record['origin_selection_sha256']
        selection = read(selection_path)
        assert selection['status'] == 'accepted_first_valid_actual_attempt'
        offset = (index - 1) * plan['batch_size']
        packet = {'rows': new[offset:offset + plan['batch_size']]}
        request = make_request(effective_prompt(prompt, bool(record['technical_version'])), packet)
        assert digest(request) == record['expected_request_sha256']
        selected = audit_selection(run, index, selection, packet, request,
                                   record['effective_prompt_sha256'], runner)
        raw = read(selected / 'raw_output.json')
        assert not runner.v.validate(packet, raw)
        # Exact raw row objects: no label/quote editing and no dimension splicing.
        aggregate['rows'].extend(raw['rows'])
        aggregate['issue_records'].extend(raw['issue_records'])
        lineage.append({'batch': index, 'action': record['action'],
                        'actual_origin_run': str(run),
                        'selected_raw_path': str(selected / 'raw_output.json'),
                        'selected_raw_sha256': sha(selected / 'raw_output.json'),
                        'selection_path': str(selection_path), 'selection_sha256': sha(selection_path),
                        'input_sha256': sha(selected / 'input.json'),
                        'metadata_sha256': sha(selected / 'run_metadata.json'),
                        'base_semantic_prompt_sha256': plan['prompt_sha256'],
                        'actual_prompt_sha256': record['effective_prompt_sha256'],
                        'actual_request_sha256': record['expected_request_sha256'],
                        'technical_version': record['technical_version'],
                        'all_five_dimensions_from_one_actual_raw_row': True})
        for row in raw['rows']:
            row_provenance.append({'id': row['id'], **lineage[-1]})
        all_attempts += len(selection['attempts'])
        tools += sum(a['tool_event_count'] for a in selection['attempts'])
    assert not runner.v.validate({'rows': new}, aggregate)
    write_new(output / 'all_predictions.json', aggregate)
    target = output / 'all_predictions.jsonl'
    assert not target.exists()
    target.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in aggregate['rows']))
    write_new(output / 'batch_lineage.json', lineage)
    provenance_path = output / 'row_provenance.jsonl'
    assert not provenance_path.exists()
    provenance_path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in row_provenance))
    summary = {'status': 'complete_actual_five_dimension_calls_with_source_only_batch_repair',
               'n': len(new), 'batch_count': len(lineage),
               'new_whole_batches': len(plan['rerun_batches']),
               'reused_exact_input_batches': len(lineage) - len(plan['rerun_batches']),
               'exact_batch_origin_counts': {origin: sum(item['actual_origin_run'] == origin for item in lineage)
                                             for origin in sorted({item['actual_origin_run'] for item in lineage})},
               'new_input_sha256': plan['new_input_sha256'], 'prompt_sha256': plan['prompt_sha256'],
               'output_sha256': sha(target), 'lineage_sha256': sha(output / 'batch_lineage.json'),
               'row_provenance_sha256': sha(provenance_path),
               'base_semantic_prompt_sha256': plan['prompt_sha256'],
               'actual_prompt_sha256_counts': {h: sum(r['actual_prompt_sha256'] == h for r in row_provenance)
                                               for h in sorted({r['actual_prompt_sha256'] for r in row_provenance})},
               'all_actual_prompts_byte_identical': len({r['actual_prompt_sha256'] for r in row_provenance}) == 1,
               'technical_version': plan['technical_version'],
               'technical_batches': plan['technical_batches'],
               'technical_prompt_sha256': plan['technical_prompt_sha256'],
               'technical_appendix_sha256': plan['technical_appendix_sha256'],
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
    parser.add_argument('--reuse-run', action='append', default=[])
    parser.add_argument('--technical-batch', type=int, action='append', default=[],
                        help='Explicitly frozen whole batch to use citation-isolation-tech01 prompt')
    parser.add_argument('--workers', type=int, default=8)
    args = parser.parse_args()
    output = Path(args.output).resolve()
    if args.mode == 'prepare':
        assert args.old_run and args.new_input and args.expected_input_sha256
        plan = prepare(Path(args.old_run).resolve(), Path(args.new_input).resolve(), output,
                       args.expected_input_sha256, [Path(p).resolve() for p in args.reuse_run],
                       args.technical_batch)
        print(json.dumps({'rerun_batches': plan['rerun_batches'],
                          'changed_ids_n': len(plan['changed_ids'])}), flush=True)
    elif args.mode == 'execute':
        assert 1 <= args.workers <= 12
        execute(output, args.workers)
    else:
        seal(output)


if __name__ == '__main__':
    main()
