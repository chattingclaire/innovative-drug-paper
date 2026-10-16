"""Join a fixed full actual LLM run with one source-corrected actual call.

Selection is fixed by the source change ID, never by label or performance.
Preserve the raw executions. Bind the current rule run and common materials.
"""
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
DIMS = ('S', 'E', 'Ec', 'I', 'F')
RID = 'RECODE25-03875'
OLD = W / 'LLM编码/测量与语义统一/full4480'
ONE = W / 'LLM编码/测量与语义统一/figure03875_correction'
PATCH = W / '自动规则编码/来源读取修复/编号边界修复'
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
CANON = lambda x: json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
READ = lambda p: json.loads(Path(p).read_text())
ROWS = lambda p: [json.loads(s) for s in Path(p).read_text().splitlines() if s.strip()]
bindings = {}


def bind(path, expected=None):
    path = Path(path).resolve()
    actual = SHA(path)
    if expected is not None:
        assert actual == expected, (str(path), actual, expected)
    value = {'path': str(path), 'sha256': actual}
    bindings[str(path)] = value
    return value


def raw_lines(path):
    lines = Path(path).read_bytes().splitlines(keepends=True)
    assert all(line.endswith(b'\n') and line.strip() for line in lines)
    return {json.loads(line)['id']: line for line in lines}


def patched_rule(base_path, full_input, manual_sha):
    report = READ(PATCH / '实际34执行报告.json')
    frozen = READ(PATCH / '实际34执行冻结.json')
    scope = READ(PATCH / '静态影响范围.json')
    delivery = READ(PATCH / '交付冻结记录.json')
    for name in ('实际34执行报告.json', '实际34执行冻结.json', '静态影响范围.json',
                 '交付冻结记录.json', '单处改动.json', '编号机制检查.json'):
        bind(PATCH / name)
    bind(PATCH / '静态影响范围.json', frozen['scope_sha256'])
    bind(full_input, frozen['full_input_sha256'])
    bind(base_path, frozen['base_full_output_sha256'])
    patch_in = PATCH / '保守34输入.jsonl'
    patch_out = PATCH / '保守34实际输出.jsonl'
    bind(patch_in, report['input_sha256'])
    bind(patch_out, report['output_sha256'])
    assert frozen['manual_sha256'] == report['manual_sha256'] == manual_sha
    assert report['status_counts'] == {'completed': report['n']}
    assert report['runtime_unchanged_during_run'] and report['no_human_or_model_labels_used']
    assert frozen['expected_labels_not_used']
    ids = frozen['ids']
    assert ids == scope['conservative_current_paragraph_ids'] == delivery['scope_ids']
    assert scope['input_rows'] == 4480 and len(ids) == len(set(ids)) == report['n'] == 34
    full = {r['id']: r for r in ROWS(full_input)}
    pin, pout = ROWS(patch_in), ROWS(patch_out)
    assert [r['id'] for r in pin] == [r['id'] for r in pout] == ids
    assert all(CANON(r) == CANON(full[r['id']]) for r in pin)
    assert frozen['runtime_manifest'] == report['runtime_manifest'] == delivery['all_runtime_files_sha256']
    for rel, expected in frozen['runtime_manifest'].items():
        bind(PATCH / 'runtime' / rel, expected)
    for rel, expected in delivery['development_artifacts_sha256'].items():
        bind(PATCH / rel, expected)
    base, replacement = ROWS(base_path), {r['id']: r for r in pout}
    merged = [replacement.get(r['id'], r) for r in base]
    changed = [r['id'] for r, new in zip(base, merged) if r['result']['labels'] != new['result']['labels']]
    assert changed == [r['id'] for r in report['changed_rows']]
    return merged, ids, patch_in, patch_out, changed


def actual(run, n, output_sha):
    summary = READ(run / 'execution_summary.json')
    bind(run / 'execution_summary.json')
    assert summary['status'] == 'complete_actual_calls_structurally_valid'
    assert summary['n'] == n and summary['source_unchanged_during_run']
    assert summary['accepted_batch_count'] == summary['recorded_batch_count'] == summary['expected_batch_count']
    assert summary['selected_tool_event_count'] == summary['all_attempt_tool_event_count'] == 0
    assert summary['metric_or_reference_label_based_selection'] is False
    assert summary['output_sha256'] == output_sha
    bind(run / 'all_predictions.jsonl', output_sha)
    bind(run / 'run_plan.json', summary['plan_sha256'])
    plan = READ(run / 'run_plan.json')
    assert plan['model'] == 'gpt-5.6-sol' and plan['reasoning_effort'] == 'medium'
    assert plan['method_version'] == 'LLM-measurement-semantic-24007a19a724'
    for filename, key in [('frozen_input.jsonl', 'input_sha256'), ('frozen_prompt.txt', 'prompt_sha256'),
                          ('frozen_schema.json', 'schema_sha256'), ('frozen_validator.py', 'validator_sha256'),
                          ('frozen_runner.py', 'runner_sha256')]:
        bind(run / filename, plan[key])
    inputs = ROWS(run / 'frozen_input.jsonl')
    rows = ROWS(run / 'all_predictions.jsonl')
    aggregate = READ(run / 'all_predictions.json')
    bind(run / 'all_predictions.json')
    assert len(inputs) == len(rows) == n
    assert [r['id'] for r in inputs] == [r['id'] for r in rows]
    assert CANON(rows) == CANON(aggregate['rows'])
    spec = importlib.util.spec_from_file_location('frozen_bundle_validator', run / 'frozen_validator.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert module.validate({'rows': inputs}, aggregate) == []
    if n == 1:
        batch = run / 'batches/batch-0001'
        selection = READ(batch / 'selection.json')
        assert selection['status'] == 'accepted_first_valid_actual_attempt'
        assert selection['ids'] == [RID] and not selection['selection_uses_metric_or_label_values']
        assert len(selection['attempts']) == 1
        chosen = run / selection['selected_relative_path']
        meta = READ(chosen / 'run_metadata.json')
        assert meta['status'] == 'accepted_structural_literal_zero_tools'
        assert meta['raw_output_matches_unique_completed_agent_message']
        assert meta['completed_agent_message_count'] == 1 and meta['tool_event_count'] == 0
        assert meta['label_or_metric_selection'] is False
        bind(batch / 'selection.json')
        bind(chosen / 'run_metadata.json', selection['attempts'][0]['metadata_sha256'])
        for filename, key in [('input.json', 'input_sha256'), ('request.txt', 'request_sha256'),
                              ('raw_output.json', 'raw_output_sha256'), ('events.jsonl', 'events_sha256'),
                              ('raw_stderr.txt', 'stderr_sha256'), ('validation.json', 'validation_sha256'),
                              ('tool_event_audit.json', 'tool_event_audit_sha256'),
                              ('event_output_binding_audit.json', 'event_output_binding_audit_sha256')]:
            bind(chosen / filename, meta[key])
        assert READ(chosen / 'validation.json')['valid'] is True
        assert CANON(READ(chosen / 'raw_output.json')['rows']) == CANON(rows)
    return inputs, rows, summary, plan


def main():
    destination = HERE / '当前同材料结果'
    assert not destination.exists(), 'No overwriting an existing assembled result.'
    old_inputs, old_rows, old_summary, old_plan = actual(
        OLD, 4480, 'e4fb8b2f3dca2e00e816800ae56755231e577822e7286201816f5801b192c1c7')
    one_inputs, one_rows, one_summary, one_plan = actual(
        ONE, 1, '70bf576e8ffddb8549ec915efeeadf539c063766d3294ee5be7679877a9b6a57')
    for key in ('prompt_sha256', 'schema_sha256', 'validator_sha256', 'runner_sha256'):
        assert old_plan[key] == one_plan[key]
    old_qa_path = W / '统计复算/测量与语义统一全量/两方法比较/首次全量实际比较/输入绑定与完整性核查.json'
    qa = READ(old_qa_path)
    assert qa['all_checks_pass'] and qa['llm_summary']['output_sha256'] == old_summary['output_sha256']
    bind(old_qa_path)
    for path, item in qa['source_files'].items():
        bind(path, item['sha256'])
    correction_record = W / '来源材料核查/03875图示分支校正/来源校正记录.json'
    record = READ(correction_record)
    bind(correction_record)
    assert record['impact_scan'] == {'LLM': [RID], 'rule': [RID]}
    for filename in ('独立视觉校核结论01.json', '校正后视觉认证记录.json'):
        bind(correction_record.parent / filename)
    current_input = ROWS(HERE / '纯来源材料4480.jsonl')
    current_rule_input = ROWS(HERE / '规则输入4480.jsonl')
    frame = ROWS(HERE / '同材料目标框4481.jsonl')
    for filename in ('纯来源材料4480.jsonl', '规则输入4480.jsonl', '同材料目标框4481.jsonl', '目标框材料校核.json'):
        bind(HERE / filename)
    assert len(frame) == 4481 and len({r['id'] for r in frame}) == 4481
    assert [r['id'] for r in current_input] == [r['id'] for r in old_inputs]
    assert [r['id'] for r in current_rule_input] == [r['id'] for r in current_input]
    assert [a['id'] for a, b in zip(old_inputs, current_input) if CANON(a) != CANON(b)] == [RID]
    assert CANON(next(r for r in current_input if r['id'] == RID)) == CANON(one_inputs[0])
    combined = [one_rows[0] if row['id'] == RID else row for row in old_rows]
    unchanged_ids = [row['id'] for row in old_rows if row['id'] != RID]
    assert len(unchanged_ids) == 4479
    assert all(CANON(a) == CANON(b) for a, b in zip(old_rows, combined) if a['id'] != RID)
    rule_summary = READ(HERE / '规则全量输出4480.execution.json')
    assert rule_summary['n'] == rule_summary['completed'] == 4480
    assert rule_summary['failed'] == 0 and rule_summary['runtime_unchanged_during_execution']
    bind(HERE / '规则全量输出4480.execution.json')
    rule_path = HERE / '规则全量输出4480.jsonl'
    bind(rule_path, rule_summary['output_sha256'])
    assert rule_summary['input_sha256'] == SHA(HERE / '规则输入4480.jsonl')
    rules = ROWS(rule_path)
    assert [r['id'] for r in rules] == [r['id'] for r in combined]
    freeze = READ(HERE / '执行冻结记录.json')
    bind(HERE / '执行冻结记录.json')
    for rel, expected in freeze['runtime_files_sha256'].items():
        bind(Path(freeze['runtime_path']) / rel, expected)
    rule_base_path = rule_path
    rules, patch_ids, patch_input, patch_output, rule_changed_ids = patched_rule(
        rule_base_path, HERE / '规则输入4480.jsonl', freeze['same_manual_sha256'])
    fidx = {r['id']: r for r in frame}
    for rr, ri, li, lr in zip(rules, current_rule_input, current_input, combined):
        rid = rr['id']
        assert rr['status'] == 'completed'
        assert rr['result']['current_manual_sha256'] == freeze['same_manual_sha256']
        assert ri['input']['unit_text'] == li['text'] == fidx[rid]['unit_text']
        assert hashlib.sha256(li['text'].encode()).hexdigest() == rr['result']['unit_text_sha256'] == fidx[rid]['unit_text_sha256']
        for result in (rr['result'], lr):
            assert set(result['labels']) == set(DIMS)
            assert all(v is None or type(v) is int and v in (0, 1) for v in result['labels'].values())
        for evidence in rr['result']['evidence']:
            assert evidence['display_quote'] == li['text']
    assert set(fidx) - {r['id'] for r in combined} == {'RECODE25-00064'}
    assert all(SHA(b['path']) == b['sha256'] for b in bindings.values())
    destination.mkdir()
    lp = destination / 'LLM全量输出4480.jsonl'
    original_llm_lines = raw_lines(OLD / 'all_predictions.jsonl')
    corrected_llm_lines = raw_lines(ONE / 'all_predictions.jsonl')
    lp.write_bytes(b''.join(corrected_llm_lines[r['id']] if r['id'] == RID else original_llm_lines[r['id']] for r in combined))
    assert ROWS(lp) == combined
    rule_path = destination / '规则全量输出4480.jsonl'
    base_rule_lines, patch_rule_lines = raw_lines(rule_base_path), raw_lines(patch_output)
    rule_path.write_bytes(b''.join(patch_rule_lines[r['id']] if r['id'] in patch_rule_lines else base_rule_lines[r['id']] for r in rules))
    assert ROWS(rule_path) == rules
    base_rule_sha, patch_rule_sha = SHA(rule_base_path), SHA(patch_output)
    rule_lineage = [{'id': r['id'],
                     'actual_output': str(patch_output if r['id'] in patch_ids else rule_base_path),
                     'actual_output_sha256': patch_rule_sha if r['id'] in patch_ids else base_rule_sha,
                     'row_sha256': hashlib.sha256(CANON(r).encode()).hexdigest(),
                     'selection_basis': 'fixed_source_parse_scope' if r['id'] in patch_ids else 'unchanged_full_run_row'} for r in rules]
    rule_linep = destination / '规则逐条执行来源.jsonl'
    rule_linep.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rule_lineage))
    lineage = [{'id': r['id'], 'actual_run': str(ONE if r['id'] == RID else OLD),
                'actual_output_sha256': one_summary['output_sha256'] if r['id'] == RID else old_summary['output_sha256'],
                'actual_input_sha256': one_summary['input_sha256'] if r['id'] == RID else old_summary['input_sha256'],
                'row_sha256': hashlib.sha256(CANON(r).encode()).hexdigest(),
                'selection_basis': 'fixed_source_correction_id' if r['id'] == RID else 'unchanged_full_run_row'} for r in combined]
    linep = destination / 'LLM逐条执行来源.jsonl'
    linep.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in lineage))
    manifest = {
        'status': 'complete_same_material_current_methods_bound_not_human_validated',
        'target_n': 4481, 'executed_n': 4480, 'manual_sha256': freeze['same_manual_sha256'],
        'rule_output': bind(rule_path), 'llm_output': bind(lp),
        'rule_input': bind(HERE / '规则输入4480.jsonl'), 'llm_input': bind(HERE / '纯来源材料4480.jsonl'),
        'frame': bind(HERE / '同材料目标框4481.jsonl'), 'llm_lineage': bind(linep),
        'rule_base_output': bind(rule_base_path),
        'rule_base_execution': bind(HERE / '规则全量输出4480.execution.json'),
        'rule_patch_input': bind(patch_input), 'rule_patch_output': bind(patch_output),
        'rule_patch_report': bind(PATCH / '实际34执行报告.json'),
        'rule_patch_freeze': bind(PATCH / '实际34执行冻结.json'),
        'rule_patch_scope': bind(PATCH / '静态影响范围.json'),
        'rule_patch_delivery': bind(PATCH / '交付冻结记录.json'),
        'rule_lineage': bind(rule_linep), 'rule_patch_ids': patch_ids,
        'rule_changed_label_ids': rule_changed_ids, 'unchanged_rule_rows_n': 4480 - len(patch_ids),
        'rule_execution_scope': 'complete actual full4480 run plus fixed source-parser scope of 34 actual reruns; not claimed one single run',
        'llm_execution_scope': 'complete actual full4480 run plus exactly one actual source-corrected run; not claimed one single run',
        'llm_replaced_source_ids': [RID], 'unchanged_llm_rows_n': 4479,
        'known_source_unknown_ids': ['RECODE25-00064'],
        'rule_partially_unknown_ids': [r['id'] for r in rules if any(v is None for v in r['result']['labels'].values())],
        'source_correction': bind(correction_record), 'complete_original_llm_execution_QA': bind(old_qa_path),
        'one_row_actual_execution': bind(ONE / 'execution_summary.json'),
        'assembly_code': bind(Path(__file__)), 'source_bindings': bindings,
        'original_references_and_formal_paper_edited': False,
        'label_or_metric_based_selection': False, 'new_independent_human_validation': False
    }
    # Detach bindings before JSON serialisation to avoid shared recursive construction.
    manifest['source_bindings'] = dict(bindings)
    (destination / '同材料结果绑定.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'manifest': str(destination / '同材料结果绑定.json'),
                      'rule_unknown_n': len(manifest['rule_partially_unknown_ids']),
                      'llm_output_sha256': manifest['llm_output']['sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
