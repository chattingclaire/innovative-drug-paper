# Derived read-only comparison kernel; original script SHA1ede8a8ab978f65c6be56afcc267ab6073f8a0e301526bd2576c80fa968f32d9.
# Only the completion-audit population count is parameterized; original main is excluded.
"""Compare complete, bound new rule/LLM outputs. Never calls either coder.

The LLM completion gate runs before predictions are opened. Unknown cells are
not zeros. No method is a gold standard; no precision/recall is calculated.
"""
import argparse
import hashlib
import json
import math
import sys
import types
from collections import Counter
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[2]
DIMS = ['S', 'E', 'Ec', 'I', 'F']
EXECUTION = 'LLM-measurement-semantic-24007a19a724'
MANUAL_SHA = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
LLM_RUN = W / 'LLM编码/测量与语义统一/full4480'
DEFAULT_PATHS = {
    'rule_output': HERE.parent / '规则全量输出4480.jsonl',
    'rule_input': HERE.parent / '规则输入4480.jsonl',
    'frame': W / '人工参照复核/全量目标框验证准备01/source_only_frame_all4481.jsonl',
    'rule_summary_helper': HERE.parent / '规则描述统计/count_rule_descriptive.py',
    'manual': W / '定义溯源核查/测量与计数统一/共用编码手册.md'
}
SOURCE_LOCKS = {
    'rule_output': 'a15f974a30cbe3d95ff339c88a63c786cdd84fae43a4e8a530509318d7a0cc8e',
    'rule_input': '0a0704613e29ca81bc35c25bcdab8c36f5b2367250562d2f5f80a73f0e71fe2d',
    'frame': '301f05240c8ada00129ed8f84bc68e5047118cdedef9777937f01d49cad17c29',
    'rule_summary_helper': '3e16bcda2a7d605a055c5f3ff94d8a5126566e9bed42e99877454d59c5a9524a',
    'manual': MANUAL_SHA
}
FROZEN_LOCKS = {
    'frozen_prompt.txt': 'a2263837c009c80cce84ee7e8e39f1e719cd77b92c727a790967f172eaa5ba4d',
    'frozen_schema.json': '120bec39fc38ba1e234a6c5f60d4298468950fc303617b77b55651b89167a0d4',
    'frozen_validator.py': 'cf38105364f723972b46b6a781ea75c7c8da871bc22455c9cb002b500b6b1e8c',
    'frozen_runner.py': '145815cd373725dd71beffd2ba6c492347a840da99d833129261d8b295dd6856'
}

class BindingError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise BindingError(message)

def digest(data):
    return hashlib.sha256(data).hexdigest()

def is_sha256(value):
    return isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value)

def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

def read_bound(path, bindings, expected=None):
    path = Path(path).resolve()
    require(path.is_file(), f'required file missing: {path}')
    data = path.read_bytes()
    actual = digest(data)
    if expected is not None:
        require(actual == expected, f'SHA mismatch: {path}; expected={expected}; actual={actual}')
    bindings[str(path)] = {'sha256': actual, 'bytes': len(data)}
    return data

def read_json(path, bindings, expected=None):
    return json.loads(read_bound(path, bindings, expected).decode('utf-8'))

def read_jsonl(path, bindings, expected=None):
    return [json.loads(s) for s in read_bound(path, bindings, expected).decode('utf-8').splitlines() if s.strip()]

def index_unique(rows, name):
    require(all(isinstance(r, dict) and isinstance(r.get('id'), str) and r['id'] for r in rows), f'{name}: invalid ID')
    require(len({r['id'] for r in rows}) == len(rows), f'{name}: duplicate ID')
    return {r['id']: r for r in rows}

def validate_complete_summary(summary, expected_n):
    # This metadata-only gate intentionally precedes opening any prediction.
    require(isinstance(summary, dict), 'LLM summary is not an object')
    require(summary.get('status') == 'complete_actual_calls_structurally_valid', 'LLM run is missing, partial or failed; complete comparison refused')
    require(summary.get('n') == expected_n, f'LLM summary n is not{expected_n}')
    expected = summary.get('expected_batch_count')
    require(type(expected) is int and expected > 0, 'invalid expected batch count')
    require(summary.get('accepted_batch_count') == expected == summary.get('recorded_batch_count'), 'LLM batches are incomplete')
    require(summary.get('selected_tool_event_count') == 0 and summary.get('all_attempt_tool_event_count') == 0, 'LLM tool-event contract failed')
    require(summary.get('source_unchanged_during_run') is True, 'LLM source changed during execution')
    require(summary.get('source_input_current_sha256') == summary.get('input_sha256'), 'LLM source/input SHA disagreement')
    require(summary.get('metric_or_reference_label_based_selection') is False, 'LLM selection contract not recorded as independent of labels/metrics')
    for key in ['output_sha256', 'input_sha256', 'prompt_sha256', 'plan_sha256']:
        value = summary.get(key)
        require(is_sha256(value), f'LLM summary lacks valid {key}')

def load_complete_llm(args, bindings, expected_n):
    run = Path(args.llm_run).resolve()
    summary_path = Path(args.llm_summary).resolve() if args.llm_summary else run / 'execution_summary.json'
    output_path = Path(args.llm_output).resolve() if args.llm_output else run / 'all_predictions.jsonl'
    require(summary_path == run / 'execution_summary.json' and output_path == run / 'all_predictions.jsonl', 'LLM summary/output must belong to the selected single run; arbitrary composite files refused')
    summary = read_json(summary_path, bindings, args.expected_llm_summary_sha256)
    validate_complete_summary(summary, expected_n)
    if args.expected_llm_output_sha256:
        require(summary['output_sha256'] == args.expected_llm_output_sha256, 'LLM output disagrees with explicit caller SHA')
    plan = read_json(run / 'run_plan.json', bindings, summary['plan_sha256'])
    require(plan.get('n') == expected_n and plan.get('method_version') == EXECUTION, 'LLM plan belongs to another method/population')
    require(plan.get('model') == 'gpt-5.6-sol' and plan.get('reasoning_effort') == 'medium', 'LLM model/effort differs')
    require(plan.get('input_sha256') == summary['input_sha256'] and plan.get('prompt_sha256') == summary['prompt_sha256'], 'LLM summary/plan source binding differs')
    require(type(plan.get('batch_size')) is int and 1 <= plan['batch_size'] <= 50, 'invalid LLM batch size')
    require(plan.get('batch_count') == math.ceil(expected_n / plan['batch_size']) == summary['expected_batch_count'], f'LLM batch plan does not cover{expected_n}')
    frozen = {}
    for name, expected in FROZEN_LOCKS.items():
        frozen[name] = read_bound(run / name, bindings, expected)
    for plan_key, filename in [('prompt_sha256', 'frozen_prompt.txt'), ('schema_sha256', 'frozen_schema.json'),
                                ('validator_sha256', 'frozen_validator.py'), ('runner_sha256', 'frozen_runner.py')]:
        require(plan.get(plan_key) == FROZEN_LOCKS[filename], f'LLM plan {plan_key} differs from the new fixed preparation')
    prompt = frozen['frozen_prompt.txt'].decode('utf-8')
    embedded = frozen['frozen_prompt.txt'].split(b'<common_manual>\n', 1)[1].split(b'</common_manual>', 1)[0]
    require(digest(embedded) == MANUAL_SHA, 'LLM embedded manual is not the fixed new manual')
    relative = Path(plan.get('frozen_input_relative_path', ''))
    require(relative.name == str(relative) and str(relative) in {'frozen_input.jsonl', 'frozen_input.json'}, 'invalid frozen input relative path')
    data = read_bound(run / relative, bindings, summary['input_sha256'])
    inputs = ([json.loads(s) for s in data.decode('utf-8').splitlines() if s.strip()]
              if relative.suffix == '.jsonl' else json.loads(data.decode('utf-8'))['rows'])
    read_bound(Path(plan['source_input_path']), bindings, summary['input_sha256'])
    require(len(inputs) == expected_n, 'LLM frozen input count differs')
    index_unique(inputs, 'LLM input')
    rows = read_jsonl(output_path, bindings, summary['output_sha256'])
    aggregate = read_json(run / 'all_predictions.json', bindings)
    require(aggregate.get('protocol_version') == 'COMMON-5D-20261009'
            and aggregate.get('execution_version') == EXECUTION and aggregate.get('release_stage') == 'development_labels', 'LLM aggregate identity differs')
    require(canonical(aggregate.get('rows')) == canonical(rows), 'LLM JSONL/aggregate rows differ')
    require([r['id'] for r in inputs] == [r.get('id') for r in rows], 'LLM output count/order differs from frozen input')
    validator = types.ModuleType('comparison_fixed_literal_validator')
    exec(compile(frozen['frozen_validator.py'], str(run / 'frozen_validator.py'), 'exec'), validator.__dict__)
    errors = validator.validate({'rows': inputs}, aggregate)
    require(not errors, f'complete LLM aggregate failed the frozen structure/literal validator: {errors[:12]}')
    # Bind every selected current-run batch to the frozen request and aggregate.
    selection_paths = sorted((run / 'batches').glob('batch-*/selection.json'))
    require(len(selection_paths) == plan['batch_count'], 'selection files do not cover the complete single run')
    assembled = []
    batch_ledger = []
    attempt_count = 0
    for number, selection_path in enumerate(selection_paths, 1):
        require(selection_path.parent.name == f'batch-{number:04d}', 'batch indices are missing, duplicated or out of order')
        selection = read_json(selection_path, bindings)
        require(selection.get('batch') == number and selection.get('status') == 'accepted_first_valid_actual_attempt', 'batch is not accepted')
        require(selection.get('selection_uses_metric_or_label_values') is False, 'batch selection contract differs')
        batch_input = read_json(selection_path.parent / 'input.json', bindings)
        expected_rows = inputs[(number - 1) * plan['batch_size']:number * plan['batch_size']]
        require(canonical(batch_input) == canonical({'rows': expected_rows}), 'batch input is not the corresponding frozen current-run slice')
        ids = [r['id'] for r in expected_rows]
        require(selection.get('ids') == ids and selection.get('input_n') == len(ids), 'batch selection IDs differ')
        relative_attempt = selection.get('selected_relative_path')
        require(isinstance(relative_attempt, str) and relative_attempt.startswith(f'batches/batch-{number:04d}/attempts/attempt-'), 'selected attempt is not in this batch')
        attempts = selection.get('attempts')
        require(isinstance(attempts, list) and 1 <= len(attempts) <= plan.get('max_attempts', 0), 'invalid attempt ledger')
        require([a.get('attempt') for a in attempts] == list(range(1, len(attempts) + 1)), 'attempt sequence differs')
        require(all(a.get('tool_event_count') == 0 and a.get('status') in {'failed_attempt_preserved', 'accepted_structural_literal_zero_tools'} for a in attempts), 'attempt status/tool contract differs')
        accepted_attempts = [a for a in attempts if a['status'] == 'accepted_structural_literal_zero_tools']
        require(len(accepted_attempts) == 1 and accepted_attempts[0] is attempts[-1]
                and accepted_attempts[0].get('relative_path') == relative_attempt, 'selected attempt is not the first accepted chronological attempt')
        selected_entry = accepted_attempts[0]
        require(is_sha256(selected_entry.get('metadata_sha256')), 'selected attempt metadata SHA missing')
        attempt_count += len(attempts)
        attempt = (run / relative_attempt).resolve()
        require(attempt.is_relative_to(run) and attempt.is_dir(), 'selected attempt path escapes run or is missing')
        metadata = read_json(attempt / 'run_metadata.json', bindings, selected_entry['metadata_sha256'])
        require(metadata.get('status') == 'accepted_structural_literal_zero_tools'
                and metadata.get('requested_model') == plan['model'] and metadata.get('reasoning_effort') == plan['reasoning_effort'], 'selected attempt identity/status differs')
        require(metadata.get('prompt_sha256') == plan['prompt_sha256'] and metadata.get('ids') == ids
                and metadata.get('input_n') == len(ids) and metadata.get('tool_event_count') == 0
                and metadata.get('label_or_metric_selection') is False, 'selected attempt contract differs')
        require(metadata.get('raw_output_matches_unique_completed_agent_message') is True
                and metadata.get('completed_agent_message_count') == 1, 'selected attempt lacks event/output binding')
        require(all(is_sha256(metadata.get(k)) for k in ['input_sha256', 'request_sha256', 'raw_output_sha256'])
                and is_sha256(selection.get('selected_output_sha256')), 'selected attempt lacks original input/request/output SHA')
        attempt_input = read_json(attempt / 'input.json', bindings, metadata.get('input_sha256'))
        require(canonical(attempt_input) == canonical(batch_input), 'attempt input differs from current batch')
        request = read_bound(attempt / 'request.txt', bindings, metadata.get('request_sha256')).decode('utf-8')
        expected_request = prompt + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps(batch_input, ensure_ascii=False) + '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        require(request == expected_request, 'attempt request is not the fixed new prompt and corresponding frozen input')
        raw = read_json(attempt / 'raw_output.json', bindings, selection.get('selected_output_sha256'))
        require(metadata.get('raw_output_sha256') == selection.get('selected_output_sha256') == selected_entry.get('raw_output_sha256')
                and metadata.get('events_sha256') == selected_entry.get('events_sha256'), 'selection/attempt raw-output or event SHA differs')
        require(raw.get('execution_version') == EXECUTION and [r.get('id') for r in raw.get('rows', [])] == ids, 'selected output belongs to another execution/input')
        for filename, metakey in [('events.jsonl', 'events_sha256'), ('raw_stderr.txt', 'stderr_sha256'),
                                  ('validation.json', 'validation_sha256'), ('tool_event_audit.json', 'tool_event_audit_sha256'),
                                  ('event_output_binding_audit.json', 'event_output_binding_audit_sha256')]:
            require(is_sha256(metadata.get(metakey)), f'selected attempt missing {metakey}')
            read_bound(attempt / filename, bindings, metadata[metakey])
        assembled.extend(raw['rows'])
        batch_ledger.append({'batch': number, 'input_ids': ids, 'selected_relative_path': relative_attempt,
                             'selected_output_sha256': selection['selected_output_sha256'],
                             'request_sha256': metadata['request_sha256'], 'metadata_path': str(attempt / 'run_metadata.json')})
    require(summary.get('actual_attempt_count') == attempt_count, 'summary/selection attempt counts differ')
    require(canonical(assembled) == canonical(rows), 'aggregate is not exactly the complete selected outputs of this single run; stitching refused')
    return inputs, rows, summary, plan, batch_ledger

def paired_binary(records, dim):
    eligible = [r for r in records if r['rule'][dim] is not None and r['llm'][dim] is not None]
    excluded = [r['id'] for r in records if r['rule'][dim] is None or r['llm'][dim] is None]
    table = Counter((r['rule'][dim], r['llm'][dim]) for r in eligible)
    n00, n01, n10, n11 = [table[k] for k in [(0, 0), (0, 1), (1, 0), (1, 1)]]
    n = len(eligible)
    po = Fraction(n00 + n11, n) if n else None
    pe = Fraction((n10 + n11) * (n01 + n11) + (n00 + n01) * (n00 + n10), n * n) if n else None
    kappa = (po - pe) / (1 - pe) if pe is not None and pe != 1 else None
    return {'dimension': dim, 'paired_determined_n': n, 'excluded_unknown_n': len(excluded), 'excluded_unknown_ids': excluded,
            'cells': {'rule0_llm0': n00, 'rule0_llm1': n01, 'rule1_llm0': n10, 'rule1_llm1': n11},
            'rule_positive_n': n10 + n11, 'llm_positive_n': n01 + n11,
            'agreement': float(po) if po is not None else None, 'chance_agreement': float(pe) if pe is not None else None,
            'cohen_kappa': float(kappa) if kappa is not None else None,
            'kappa_exact_fraction': str(kappa) if kappa is not None else None,
            'kappa_undefined_reason': 'no_paired_units' if not n else ('expected_agreement_is_one' if pe == 1 else None),
            'disagreement_n': n01 + n10, 'methods_are_raters_not_gold_standard': True}

def ranking(summary):
    if not summary['conditional_q_denominator_positive_label_occurrences']:
        return None
    counts = {d: summary['dimensions'][d]['fully_determined_units_positive_n'] for d in DIMS}
    return [[d for d in DIMS if counts[d] == n] for n in sorted(set(counts.values()), reverse=True)]

def compare_group(records, helper):
    methods = {m: helper.summarize([{'id': r['id'], 'group': r['group'], 'labels': r[m]} for r in records]) for m in ['rule', 'llm']}
    common = [r for r in records if all(r[m][d] is not None for m in ['rule', 'llm'] for d in DIMS)]
    common_ids = {r['id'] for r in common}
    common_summaries = {m: helper.summarize([{'id': r['id'], 'group': r['group'], 'labels': r[m]} for r in common]) for m in ['rule', 'llm']}
    differences = {}
    for d in DIMS:
        own = {m: methods[m]['dimensions'][d]['q_conditional_on_fully_determined_units']['percent'] for m in methods}
        paired = {m: common_summaries[m]['dimensions'][d]['q_conditional_on_fully_determined_units']['percent'] for m in methods}
        bound = {m: methods[m]['dimensions'][d]['full_target_relative_attention_q_bounds'] for m in methods}
        differences[d] = {
            'own_fully_determined_population_q_llm_minus_rule_percentage_points': own['llm'] - own['rule'] if all(v is not None for v in own.values()) else None,
            'common_all_five_determined_population_q_llm_minus_rule_percentage_points': paired['llm'] - paired['rule'] if all(v is not None for v in paired.values()) else None,
            'full_target_q_difference_conservative_bounds_percentage_points': {
                'lower': bound['llm']['lower']['percent'] - bound['rule']['upper']['percent'] if bound['llm']['lower']['percent'] is not None and bound['rule']['upper']['percent'] is not None else None,
                'upper': bound['llm']['upper']['percent'] - bound['rule']['lower']['percent'] if bound['llm']['upper']['percent'] is not None and bound['rule']['lower']['percent'] is not None else None
            }
        }
    return {'target_unit_n': len(records), 'method_descriptive': methods,
            'binary_agreement_on_dimensionwise_common_determined': {d: paired_binary(records, d) for d in DIMS},
            'common_all_five_determined_comparison': {
                'unit_n': len(common), 'excluded_unknown_n': len(records) - len(common),
                'excluded_unknown_ids': [r['id'] for r in records if r['id'] not in common_ids],
                'method_descriptive': common_summaries,
                'binary_agreement_same_unit_set_for_all_dimensions': {d: paired_binary(common, d) for d in DIMS},
                'ranking_tie_groups': {m: ranking(common_summaries[m]) for m in methods}},
            'own_fully_determined_population_ranking_tie_groups': {m: ranking(methods[m]) for m in methods},
            'q_differences': differences}
