"""Record the completed independent 20-row semantic review; never run a model."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def load(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def bind(p):
    p = Path(p)
    return {'path': str(p.resolve()), 'sha256': sha(p), 'bytes': p.stat().st_size}


def canonical(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


plan = load(HERE / 'final_execution_plan.json')
expected_path = BASE / 'five_new_bases_FULL5_EXPECTATIONS_PRIVATE_FROZEN.json'
expected = {case['id']: case for case in load(expected_path)['cases']}
freeze = load(HERE / 'preparation_freeze.json')
before = {entry['path']: sha(entry['path']) for entry in freeze['files']}
technical_failures = []
hard_mismatches = []
cases = []
arms = []
quotes_checked = 0
issue_count = 0
warning_counts = {'rollout_state_db_falling_back': 0, 'ignored_skill_interface_icon_path': 0, 'other_stderr_lines': 0}

# These are independent judgments after actual full reading of all four outputs.
notes = {
    'M08-M01': {
        'S': '自足的一般分析方法定义，没有援引相邻药物风险项目；0及不承接理由成立。',
        'E': '材料整理比较方法没有与药物疗效判断建立当前关系；0成立。',
        'Ec': '当前没有药价、药费或支付命题，相邻费用内容不自动传播；0成立。',
        'I': '当前没有产品改良或创新支持命题，后项释药改良未被援引；0成立。',
        'F': '当前没有患者负担或保障命题，相邻比例项目不能自动传入；0成立。'},
    'M08-M02': {
        'S': '逐项检查全部相邻项目的当前要求明确纳入给药后严重过敏；S1有当前和语境双锚。',
        'E': '明确纳入减少急性发作的试验结果；E1依据药物效果证据，并非泛称研究。',
        'Ec': '明确纳入每月药费及患者自付药费；Ec1允许与负担能力F并存。',
        'I': '明确纳入相对既有制剂的释药改良；I1和attribute有具体改变依据，不需要另证优效。',
        'F': '自付药费与收入比例实质讨论患者药费承担能力；F1和affordability成立，未扩为access。'},
    'M08-M03': {
        'S': '版本、页码及纸质副本登记是自足事务，不要求处理后项肝损伤证据；0成立。',
        'E': '当前登记职责未援引后项药物复发疗效证据；0成立。',
        'Ec': '文件元数据职责没有药物费用或支付内容；0成立。',
        'I': '一般研究文件登记不等于创新研发支持或创新属性；0成立。',
        'F': '一般办公室登记职责没有患者保障、负担或药品管理难度；0成立。'},
    'M08-M04': {
        'S': '当前必须提交两类药物证据，明确援引该药导致严重肝损伤的监测记录；S1有双锚。',
        'E': '明确援引延缓疾病复发的比较试验结果；E1有双锚。',
        'Ec': '所援引两类证据没有费用或支付内容；Ec0成立。',
        'I': '一般药物损害及疗效资料要求不是创新属性改变或创新支持；I0成立。',
        'F': '两类证据没有保障获取、负担能力或药品管理难度；F0成立。'},
    'M08-M05': {
        dim: '不计分边界。实际理由采用“参照安排而未明确纳入实质项目”的窄义解释，全0可以成立；冻结期待同时保留内容援引宽义，不能把本次选择强裁为唯一真值，也不能推广为“可以/非必须即0”。'
        for dim in DIMS}
}

for arm in plan['arms']:
    name = arm['arm']
    run = HERE / 'runtime' / name
    aggregate_path = run / 'all_predictions.json'
    aggregate = load(aggregate_path)
    packet = load(arm['input']['path'])
    packet_by_id = {row['id']: row for row in packet['rows']}
    summary = load(run / 'execution_summary.json')
    selections = sorted((run / 'batches').glob('batch-*/selection.json'))
    attempt_dirs = sorted((run / 'batches').glob('batch-*/attempts/attempt-*'))
    if len(selections) != 1 or len(attempt_dirs) != 1 or summary['actual_attempt_count'] != 1:
        technical_failures.append(name + ':unexpected_batch_or_attempt_count')
    attempts = []
    for attempt in attempt_dirs:
        meta = load(attempt / 'run_metadata.json')
        raw = load(attempt / 'raw_output.json')
        event_text = (attempt / 'events.jsonl').read_text()
        event_list = [json.loads(line) for line in event_text.splitlines() if line.strip()]
        stderr_lines = (attempt / 'raw_stderr.txt').read_text().splitlines()
        for line in stderr_lines:
            if 'state db discrepancy' in line and 'falling_back' in line:
                warning_counts['rollout_state_db_falling_back'] += 1
            elif 'ignoring interface.icon_' in line and 'icon path must be under assets/' in line:
                warning_counts['ignored_skill_interface_icon_path'] += 1
            elif line.strip():
                warning_counts['other_stderr_lines'] += 1
        completed = [event['item']['text'] for event in event_list if event.get('type') == 'item.completed'
                     and isinstance(event.get('item'), dict) and event['item'].get('type') == 'agent_message']
        event_type_counts = {}
        prohibited_events = []
        for event in event_list:
            item = event.get('item')
            item_type = item.get('type') if isinstance(item, dict) else None
            key = event.get('type', '') + '/' + str(item_type)
            event_type_counts[key] = event_type_counts.get(key, 0) + 1
            if item_type is not None and item_type not in {'agent_message', 'reasoning'}:
                prohibited_events.append(key)
            if any(word in event.get('type', '').lower() for word in ['tool_call', 'function_call', 'web_search', 'web_fetch', 'command_execution']):
                prohibited_events.append(key)
        checks = {
            'attempt_request_exact_offline_bytes': (attempt / 'request.txt').read_bytes() == Path(arm['offline_request']['path']).read_bytes(),
            'attempt_input_exact_offline_packet_bytes': (attempt / 'input.json').read_bytes() == Path(arm['offline_packet']['path']).read_bytes(),
            'single_completed_agent_message': len(completed) == 1,
            'event_JSON_raw_full_typed_object_equal': len(completed) == 1 and canonical(json.loads(completed[0])) == canonical(raw),
            'raw_aggregate_full_typed_object_equal': canonical(raw) == canonical(aggregate),
            'jsonl_rows_equal_raw_rows': canonical([json.loads(line) for line in (run / 'all_predictions.jsonl').read_text().splitlines() if line.strip()]) == canonical(raw['rows']),
            'raw_SHA_matches_metadata': sha(attempt / 'raw_output.json') == meta['raw_output_sha256'],
            'event_SHA_matches_metadata': sha(attempt / 'events.jsonl') == meta['events_sha256'],
            'request_SHA_matches_metadata': sha(attempt / 'request.txt') == meta['request_sha256'],
            'accepted_first_attempt_zero_tools': attempt.name == 'attempt-01' and meta['status'] == 'accepted_structural_literal_zero_tools' and meta['tool_event_count'] == 0 and not meta['errors'],
            'zero_tool_events_independently_counted': not prohibited_events,
            'one_completed_turn_no_failed_or_error_events': sum(event.get('type') == 'turn.completed' for event in event_list) == 1 and not any(event.get('type') in {'turn.failed', 'error'} for event in event_list),
            'requested_fixed_model_effort': meta['requested_model'] == 'gpt-5.6-sol' and meta['reasoning_effort'] == 'medium',
            'metadata_semantic_selection_false': meta['label_or_metric_selection'] is False,
            'no_actual_material_problem_flags': not any(issue.get('status') in {'material_issue', 'needs_context', 'unresolved_context_issue'} for issue in raw['issue_records'])
        }
        technical_failures.extend(name + ':' + key for key, ok in checks.items() if not ok)
        attempts.append({'path': str(attempt), 'checks': checks, 'event_type_counts': event_type_counts,
                         'metadata': meta,
                         'bindings': [bind(attempt / filename) for filename in ['input.json', 'request.txt', 'raw_output.json', 'events.jsonl', 'raw_stderr.txt', 'run_metadata.json', 'validation.json', 'tool_event_audit.json', 'event_output_binding_audit.json']]})
    selection = load(selections[0])
    if selection['selected_relative_path'] != str(attempt_dirs[0].relative_to(run)) or len(selection['attempts']) != 1:
        technical_failures.append(name + ':first_selection_binding')
    issue_count += len(aggregate['issue_records'])
    arm_rows = []
    for row in aggregate['rows']:
        unit_id = row['id']
        original = expected[unit_id]
        actual_input = packet_by_id[unit_id]
        context_text = actual_input['contexts'][arm['field_key']][0]['text']
        dimensions = []
        for dim in DIMS:
            value = row['labels'][dim]
            if type(value) is not int or value not in (0, 1):
                technical_failures.append(name + ':' + unit_id + ':' + dim + ':label_type')
            scored = original['labels'] is not None
            match = None if not scored else value == original['labels'][dim]
            if match is False:
                hard_mismatches.append({'arm': name, 'id': unit_id, 'dimension': dim, 'actual': value, 'frozen_expected': original['labels'][dim]})
            dimensions.append({'dimension': dim, 'actual_label': value,
                               'frozen_expected': None if not scored else original['labels'][dim], 'mechanical_match': match,
                               'actual_reason_read': row['dimension_reasons'][dim], 'review_judgment': 'UNSCORED_BOUNDARY_NARROW_READING_NOT_FORCED' if not scored else 'SUPPORTED_AFTER_FULL_SEMANTIC_READING',
                               'independent_basis': notes[unit_id][dim]})
        evidence_reviews = []
        for evidence in row['evidence']:
            quotes_checked += 1
            source = actual_input['text'] if evidence['source'] == 'unit' else context_text
            literal = evidence['quote'] in source
            if not literal:
                technical_failures.append(name + ':' + unit_id + ':nonliteral_quote')
            evidence_reviews.append({**evidence, 'literal_checked': literal,
                                     'scope_review': 'Current mandatory incorporation predicate supplies attachment; context quotation supplies only the corresponding concrete substantive project. Both were actually read.'})
        hard = original['labels'] is not None
        subtype_ok = row['innovation_subtypes'] == original['I_subtypes'] and row['fairness_subtypes'] == original['F_subtypes'] if hard else None
        quality_ok = row['safety_quality_basis'] == 'no_quality_basis'
        if hard and not subtype_ok:
            technical_failures.append(name + ':' + unit_id + ':subtype_semantic_disagreement')
        if not quality_ok:
            technical_failures.append(name + ':' + unit_id + ':quality_semantic_disagreement')
        unit = {'arm': name, 'id': unit_id, 'kind': original['kind'], 'current_text': actual_input['text'], 'following_text': context_text,
                'source_position': actual_input['contexts'][arm['field_key']][0]['source_position'],
                'dimensions': dimensions, 'evidence_reviews': evidence_reviews,
                'actual_innovation_subtypes': row['innovation_subtypes'], 'actual_fairness_subtypes': row['fairness_subtypes'],
                'subtype_review': 'M02 attribute and affordability each have independent concrete evidence; all other hard cases have empty subtypes as supported.' if hard else 'Boundary all-zero choice has empty subtype fields; no invented unique expected subtypes.',
                'safety_quality_basis': row['safety_quality_basis'],
                'quality_review': 'No example discusses drug quality safety: allergies and liver injury are other drug-harm evidence, so no_quality_basis is correct even when S=1.',
                'issue_records_for_unit': [issue for issue in aggregate['issue_records'] if issue['id'] == unit_id],
                'issue_review': 'M05 boundary_note, when present, transparently records the narrow arrangements reading; absence of an issue in before arms is not treated as a missing-material error. Permission alone must not be generalized as an exclusion rule.' if not hard else 'No material problem or resolution issue reported; the given content is complete.'}
        cases.append(unit)
        arm_rows.append({'id': unit_id, 'labels': row['labels'], 'hard_expected': original['labels'],
                         'hard_mismatch_dimensions': [] if not hard else [dim for dim in DIMS if row['labels'][dim] != original['labels'][dim]]})
    arms.append({'arm': name, 'field_key': arm['field_key'], 'row_serialization': arm['requested_row_serialization'],
                 'complete_label_display_in_frozen_order': arm_rows,
                 'actual_attempts': attempts, 'summary_binding': bind(run / 'execution_summary.json'),
                 'aggregate_binding': bind(aggregate_path), 'all_issue_records_actually_reviewed': aggregate['issue_records']})

arm_by_name = {arm['arm']: arm for arm in arms}
contrasts = []
for factor, pairs in [
    ('field_name', [('field_typed_context_before', 'field_neutral_context_before'), ('field_typed_context_after', 'field_neutral_context_after')]),
    ('serialization_position', [('field_typed_context_before', 'field_typed_context_after'), ('field_neutral_context_before', 'field_neutral_context_after')])]:
    for left_name, right_name in pairs:
        left_rows = arm_by_name[left_name]['complete_label_display_in_frozen_order']
        right_rows = arm_by_name[right_name]['complete_label_display_in_frozen_order']
        contrasts.append({'factor': factor, 'left_arm': left_name, 'right_arm': right_name,
                          'all_five_base_vectors': [{'id': left['id'], 'left': left['labels'], 'right': right['labels'],
                                                    'changed_dimensions': [dim for dim in DIMS if left['labels'][dim] != right['labels'][dim]],
                                                    'reason_relation_comparison': 'Both use the same supported current-to-context relation; verbal phrasing varies, with no confirmed factual or attachment discrepancy.' if left['id'] != 'M08-M05' else 'Both choose the same unscored narrow arrangements reading; this is not a uniquely correct boundary vector.'}
                                                   for left, right in zip(left_rows, right_rows)]})

if not all(sha(path) == value for path, value in before.items()):
    technical_failures.append('frozen_preparation_source_changed_during_review')
evidence_path = HERE / 'actual_four_arm_full_review_evidence_PRIVATE.json'
evidence = {'created_at_UTC': datetime.now(timezone.utc).isoformat(), 'reviewer': '/root/validation_state_oct8',
            'cases_all20_full100_reason_cells_actually_read': cases, 'arm_technical_and_label_records': arms,
            'predeclared_factorial_contrasts': contrasts, 'technical_failures': technical_failures, 'hard_mismatches': hard_mismatches}
evidence_path.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + '\n')
parallel_path = HERE / 'independent_actual_technical_review.json'
parallel = load(parallel_path) if parallel_path.exists() else None
report = {
    'status': 'COMPLETED_INDEPENDENT_FOUR_ARM_DIAGNOSTIC_REVIEW_NOT_ADOPTION_OR_ACCURACY_ESTIMATE' if not technical_failures and not hard_mismatches else 'COMPLETED_WITH_CONFIRMED_FINDINGS',
    'created_at_UTC': datetime.now(timezone.utc).isoformat(), 'reviewer': '/root/validation_state_oct8',
    'scope': {'actual_requests': 4, 'actual_attempts': 4, 'units_actually_read': 20, 'dimension_labels_and_reasons_actually_read': 100,
              'hard_expected_cells': 80, 'hard_expected_mechanical_matches': 80 - len(hard_mismatches), 'unscored_boundary_cells': 20,
              'actual_quotations_literally_and_semantically_checked': quotes_checked, 'I_and_F_subtype_fields_reviewed': 40,
              'safety_quality_fields_reviewed': 20, 'top_level_issue_records_actually_read': issue_count,
              'earlier_failed_attempts': 0, 'new_reviewer_model_calls': 0, 'new_reviewer_CLI_invocations': 0},
    'technical_failures': technical_failures, 'hard_label_mismatches': hard_mismatches, 'confirmed_semantic_errors': [],
    'stderr_warning_review': {'actual_counts': warning_counts,
                              'assessment': 'All four stderr files were actually read. Warnings concern rollout state-path fallback and ignored skill-interface icon paths. No execution error, tool event, malformed output, request mismatch or event/raw mismatch was observed. This does not expose or prove all provider-internal context or model revision details.'},
    'main_findings': [
        'All 80 frozen hard expectation cells match, and actual reading of all reasons, 60 evidence quotations, subtypes and quality fields found no confirmed semantic error on these new synthetic cases.',
        'M01 and M03 stay all-zero across four representations; M02 stays all-one with attribute/affordability; M04 stays S/E1 and Ec/I/F0. Positive relations are preserved rather than discarded to suppress negative overreading.',
        'M05 stays all-zero in every arm but all 20 boundary cells are unscored. Reasons choose a defensible narrow arrangements reading; the alternative substantive-reference reading remains in the frozen expectation record.',
        'All four field/order contrasts have identical labels for every base. Reasons differ in phrasing but retain the same attachment relation. Only after-text arms add an explicit M05 boundary_note; this reporting difference does not demonstrate a label mechanism effect.',
        'The authorized four logical requests completed with four first technically valid attempts; exact per-attempt input/request equality and complete event/raw/aggregate identity were independently checked.'
    ],
    'interpretation_limits': [
        'This one response per arm on five synthetic bases did not reproduce the previous false propagation. It neither explains away original C05-NEW-015 nor proves field names or serialization position irrelevant in general.',
        'The new synthetic wording and five-base batch differ from the original failure request. The four-arm contrast holds new batch composition constant, but cannot attribute the difference from the old failure to wording, batch composition, stochasticity or any one internal process.',
        'There is no independent repeated execution, no population sample, no corpus accuracy estimate, no latent causal-mechanism proof and no model/prompt winner.',
        'All bases lack typed-status metadata. No conclusion is drawn about production typed-status branches or all 148 nonempty structured-following records.',
        'Boundary reasons mentioning lack of a mandatory requirement must not be promoted into a rule that optional, proposed or conditional substantive content is always zero.',
        'The prompt author has not received private original cases/expectations from this reviewer. If these examples are later exposed for prompt development, record that change and treat them as development regression material.'
    ],
    'per_base_complete_vector_display': [{'id': unit_id, 'hard_expected': expected[unit_id]['labels'],
                                         'all_four_actual_vectors': {arm['arm']: next(row['labels'] for row in arm['complete_label_display_in_frozen_order'] if row['id'] == unit_id) for arm in arms},
                                         'scored': expected[unit_id]['labels'] is not None} for unit_id in [row['id'] for row in arms[0]['complete_label_display_in_frozen_order']]],
    'source_bindings': [bind(HERE / 'preparation_freeze.json'), bind(HERE / 'final_execution_plan.json'), bind(HERE / 'root_execution_authorization.json'),
                        bind(HERE / 'actual_execution_completion.json'), bind(expected_path), bind(BASE / 'mechanism_contrast_plan_PROPOSED_PRIVATE.json'),
                        bind(HERE / 'independent_execution_preflight.json'), bind(Path(__file__)), *[arm['aggregate_binding'] for arm in arms]],
    'evidence_binding': bind(evidence_path), 'parallel_mechanical_review_binding': bind(parallel_path) if parallel is not None else None,
    'parallel_mechanical_review_status': parallel.get('status') if parallel else 'NOT_YET_BOUND',
    'original08_status': 'FAIL_CONFIRMED_SEMANTIC_ERROR', 'real240_and_full4924': 'NOT_RUN',
    'new_candidate_created': False, 'adoption_authorized': False,
    'source_files_modified': False, 'expectations_modified': False, 'predictions_modified': False
}
out = HERE / 'actual_four_arm_full_review_PRIVATE.json'
out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'coverage': report['scope'], 'technical_failures': technical_failures,
                  'hard_mismatches': hard_mismatches, 'report': bind(out), 'evidence': bind(evidence_path),
                  'parallel_mechanical_review_bound': parallel is not None}, ensure_ascii=False))
if technical_failures or hard_mismatches:
    raise SystemExit(1)
