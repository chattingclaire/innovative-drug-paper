"""Readback/documentation/seal only. Does not import or execute candidate code."""
from pathlib import Path
import datetime
import hashlib
import json

ROOT = Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
PREP = ROOT / '08-audits/joint-v4-independent-sol'
CANDIDATE = ROOT / '06-coding/rule-five-dimension-joint-root/versions/joint-v4-structure-normalization-sol'
OUT = Path(__file__).resolve().parent
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def load(path):
    return json.loads(path.read_text(encoding='utf-8'))


def bind(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


plan = load(PREP / 'controls6-fixed-before-execution.json')
execution = load(OUT / 'execution-results.json')
summary = load(OUT / 'execution-summary.json')
results = execution['cases']
assert len(results) == len(plan['cases']) == 6
assert [r['name'] for r in results] == [c['name'] for c in plan['cases']]
preseal = load(PREP / 'preparation-seal.json')
for member in preseal['output_members']:
    assert bind(Path(member['path'])) == member
assert bind(PREP / 'preparation-seal.json')['sha256'] == 'f0a5d3d68161f1856723c2d5ff1f107272a6a06f414fe23fb5d12bb92893f06b'
input_seal = load(OUT / 'execution-input-and-code-seal.json')
for member in input_seal['active_modules'] + input_seal['snapshot_modules'] + input_seal['common_frozen_bindings'] + [input_seal['manual'], input_seal['algorithm_bindings'], input_seal['candidate_pre_execution_seal']]:
    assert bind(Path(member['path'])) == member
events = [json.loads(line) for line in (OUT / 'immediate-events.jsonl').read_text().splitlines()]
immediate = [json.loads(line) for line in (OUT / 'immediate-case-results.jsonl').read_text().splitlines()]
assert immediate == results
assert sum(e['event'] == 'case_start' for e in events) == 6
assert sum(e['event'] == 'judge_enter' for e in events) == summary['candidate_judge_attempts_N']
assert sum(e['event'] == 'judge_return' for e in events) == summary['judge_returns_N']
assert sum(e['event'] == 'case_result_saved' for e in events) == 6

manual = load(PREP / 'manual-basis-quotes.json')
manual_raw = Path(manual['binding']['path']).read_text(encoding='utf-8')
assert bind(Path(manual['binding']['path'])) == manual['binding']
manual_by_line = {q['line_1based']: q for q in manual['quotes']}
for q in manual['quotes']:
    a, b = q['unicode_span_half_open']
    assert manual_raw[a:b] == q['quote']

semantic_notes = {
    'article_number_integer_same_original': '整数31与真实第三十一条头一致。当前直接要求满足同版实质条件以维持资格；已供风险证据全文、原件下一条闭合。S=1来自该条过敏风险内容；不是编号、资格名或边界字体格式赋标。',
    'article_number_chinese_literal_same_original': '与整数版使用同一原文及几何，仅中性结构条号为中文。自然绑定到同一31条、同样只判S；输入无格式转换或补字。',
    'structure31_original_head32_current31_unresolved': '元数据31与连续原文头32冲突被实际登记；当前要求31条，完整资源中也无31条可核实质内容。没有将32条风险复制为31条，无resolved。S/E/Ec与I/F分别保留该确指请求及NULL；这不是技术失败。',
    'original_head32_structure32_current32_resolved': '同一来源另一个当前明确指32条，实际原文头与中文结构号一致且闭合，直接消费32条风险内容。并行可见31条请求句不改变该确指；S=1、其余0。',
    'exact_second_clause_complete_inventory': '当前只要求41条第二款。自然内容引用只选降低复发率疗效第二款，第三款费用仅作为紧邻闭合边界，第一款风险未被复制。E=1、S/Ec=0；整条库存完整也不扩大当前适用范围。',
    'exact_second_clause_missing_middle_inventory': '第二款从交付contexts/成员和完整资源中缺失，虽然独立原件保存了它且first/last/next仍有真定位。接口未把这些边界当第二款已供，也未使用兄弟风险或费用。两类stopped请求保留，五维NULL为确指缺材；独立保存原件未成为候选新增材料。',
}

semantic_reviews = []
interface_checks = []
for case, result in zip(plan['cases'], results):
    assert result['expected_values_fixed_before_execution'] == case['expected_values_fixed_before_execution']
    boundary_ids = {q['context_id'] for t in result['source_relation_traces']
                    for q in t['details'].get('closure_proof', {}).get('boundary_quotes', [])}
    consumed_ids = {q['context_id'] for u in result['observed_natural_units'] if u['kind'] != 'current'
                    for q in u['contexts']}
    # Context lists legitimately retain boundary proof. Classification text
    # must still exclude these boundary-only quotations.
    boundary_texts = {q['text'] for t in result['source_relation_traces']
                      for q in t['details'].get('closure_proof', {}).get('boundary_quotes', [])}
    boundary_used_as_unit_text = []
    for u in result['observed_natural_units']:
        for text in boundary_texts:
            if ''.join(text.split()).replace('，', ',') == u['text']:
                boundary_used_as_unit_text.append({'unit': u, 'boundary_text': text})
    assert not boundary_used_as_unit_text
    check = {
        'case': case['name'], 'boundary_context_ids': sorted(boundary_ids),
        'boundary_quotes_retained_for_geometry_only': bool(boundary_ids),
        'boundary_text_used_as_classification_unit_N': len(boundary_used_as_unit_text),
        'no_injected_relations_units_or_receipts': True,
        'source_relation_N': len(result['source_relation_traces']),
        'resolved_receipt_N': len(result['resolved_receipts']),
        'stopped_request_N': len(result['stopped_requests']),
        'positive_consumer_violations_N': len(result['consumer_route_violations']),
    }
    interface_checks.append(check)
    semantic_reviews.append({
        'name': case['name'], 'pair_group': case['pair_group'],
        'current_text': case['synthetic_bundle']['source_record']['text'],
        'current_source_ref': case['synthetic_bundle']['source_record']['source_ref'],
        'complete_saved_synthetic_originals': case['synthetic_documents'],
        'candidate_available_contexts': case['synthetic_bundle']['source_record']['contexts'],
        'candidate_resource_slots': {k: case['synthetic_bundle'][k] for k in
                                     ['explicit_or_primary_source_resources', 'preserved_historical_neutral_source_supplements', 'source_full_text_resources']},
        'original_expected': case['expected_values_fixed_before_execution'],
        'first_actual_values': result['actual_values'],
        'assessment': 'fixed_control_matched' if result['values_matched'] else 'unmatched_original_expectation_preserved',
        'review_reason': semantic_notes[case['name']],
        'fixed_preexecution_reason': case['manual_reason'],
        'manual_quotes': [manual_by_line[n] for n in case['manual_lines']],
        'full_first_decisions': result['full_five_decisions_first_execution'],
        'actual_relations_and_source_paths': result['source_relation_traces'],
        'actual_requests': result['source_requests'],
        'actual_positive_consumers': result['accepted_positive_events'],
        'interface_checks': check,
        'NULL_is_not_technical_missing_output': result['semantic_output_present'],
        'expected_interpretation_boundary_newly_found': None,
        'formal_reference_validation_pending': True,
        'not_a_human_gold_standard_or_statistical_observation': True,
    })
write('semantic-and-interface-review.json', {'case_N': 6, 'cases': semantic_reviews})
write('failure-full-inputs-and-paths.json', {
    'numeric_failure_cases_N': summary['numeric_unmatched_cases_N'],
    'numeric_mismatched_dimensions_N': summary['numeric_mismatched_dimensions_N'],
    'technical_failure_cases_N': summary['execution_exceptions_N'],
    'cases': [{'original_control': c, 'first_execution_result': r}
              for c, r in zip(plan['cases'], results) if not r['values_matched']],
    'all_first_results_preserved_without_selection': True,
    'missing_technical_output_not_filled_as_semantic_NULL_or_five_FP_FN': True,
})

def source_excerpt(filename, start, end):
    path = OUT / 'code-snapshot' / filename
    lines = path.read_text().splitlines(keepends=True)
    return {'source_binding': bind(path), 'line_interval_inclusive': [start, end],
            'source_quote': ''.join(lines[start-1:end])}

write('consumer-coverage.json', {
    'natural_only_IF_units_N': summary['only_IF_natural_observed_units_N'],
    'natural_typed_subset_units_N': summary['typed_subset_natural_observed_units_N'],
    'only_IF_accepted_positive_consumers_N': summary['only_IF_accepted_positive_events_N'],
    'typed_subset_accepted_positive_consumers_N': summary['typed_subset_accepted_positive_events_N'],
    'accepted_positive_consumer_route_violations_N': summary['accepted_positive_consumer_route_violations_N'],
    'only_IF_positive_consumer_intersection_dynamically_tested': False,
    'reason': '4个自然only_IF标准单位的内容只有S或E；没有I/F正类，故只有自然生产与非允许维度未捐献的负向观察。typed子集有4个S/E正类，均由S/E/Ec单位消费，不来自only_IF单位。',
    'contract': 'allowed = affected_dimensions (or all five); when only_IF_consumers true, intersect with I/F',
    'static_dispatch_excerpts': [source_excerpt('dimensions.py', 376, 385),
                                 source_excerpt('dimensions.py', 789, 811),
                                 source_excerpt('dimensions.py', 857, 866)],
    'natural_relation_producer_excerpt': source_excerpt('relations.py', 2023, 2044),
    'per_case': [{'name': r['name'], 'natural_units': r['observed_natural_units'],
                  'accepted_positive_consumers': r['accepted_positive_events']} for r in results],
    'units_or_flags_or_resolved_receipts_injected': False,
    'general_unseen_role_intersection_proven': False,
})
write('source-interface-scope-review.json', {
    'case_checks': interface_checks,
    'neutral_address_original_heading_excerpts': source_excerpt('relations.py', 1825, 1872),
    'exact_clause_and_closed_reference_excerpts': source_excerpt('relations.py', 1891, 1981),
    'source_adapter_excerpt': source_excerpt('source_packet.py', 113, 144),
    'complete_originals_saved': 3,
    'complete_inventory_delivered_case_N': 5,
    'missing_middle_without_full_leaf_case_N': 1,
    'saved_original_available_to_auditor_is_not_material_added_to_candidate': True,
    'actual_scope_examples': ['31/32 original-heading conflict stopped', '41 second clause does not consume sibling risk or expense', 'middle second clause missing with true outer boundaries still stopped'],
    'no_new_scope_or_cases_created_after_execution': True,
})
write('actual-read-and-execution-boundary.json', {
    'preparation_members_byte_verified_N': 10,
    'final_candidate_preseal_algorithm_5modules_manual_4common_bindings_verified': True,
    'original_source_only_controls_read_N': 6,
    'complete_saved_synthetic_original_documents_actually_read_N': 3,
    'complete_current_and_candidate_context_text_actually_reviewed_case_N': 6,
    'first_full_five_decisions_and_relation_request_unit_paths_actually_reviewed_case_N': 6,
    'manual_basis_lines_read_and_literal_checked': sorted(manual_by_line),
    'candidate_code_read_scope': 'source adapter exposure; neutral address validation; finite article/clause proof; natural I/F reuse producer; only_IF/typed consumer dispatch excerpts. Five module bytes snapshotted and hashed; not a complete line-by-line algorithm audit.',
    'candidate_source_adapter_attempts_N': summary['source_adapter_attempts_N'],
    'candidate_RelationView_attempts_N': summary['source_view_attempts_N'],
    'candidate_judge_attempts_N': summary['candidate_judge_attempts_N'],
    'candidate_execution_processes_N': 1,
    'all_cases_started_and_returned_and_saved_with_incremental_flush': True,
    'audit_finalizer_calls_candidate': False,
    'parent75_235_answers_or_owner_development_result_contents_read': False,
    'main4481_LLM_partial_labels_read': False,
    'actual_cohort_run_N': 0,
    'actual_new_policy_source_ids_N': 0,
    'actual_human_results_or_reference_read_or_created_N': 0,
    'formal_statistical_metrics_created_N': 0,
    'original_preparation_or_candidate_files_modified': False,
})
write('report.json', {
    'status': 'bounded_hidden6_independent_source_interface_audit_complete_not_formal_validation',
    'first_execution_summary': summary,
    'preparation_seal': input_seal['original_preparation_seal'],
    'candidate_algorithm': input_seal['algorithm_bindings'],
    'candidate_pre_execution_seal': input_seal['candidate_pre_execution_seal'],
    'findings': ['整数与中文中性编号同值；原文头冲突被保留为缺材，不创建原文',
                 '当前第二款只消费该款，边界费用和兄弟风险不捐献维度',
                 '中间确指款缺失时保留五维NULL，完整外层边界不补成完整库存'],
    'only_IF_positive_consumer_intersection_not_dynamically_exercised': True,
    'natural_only_IF_generation_observed': True,
    'typed_subset_actual_positive_consumers_observed_N': 4,
    'semantic_failure_N': 0,
    'technical_failure_N': 0,
    'candidate_or_expectation_repaired_or_rerun': False,
    'formal_reference_validation_pending': True,
    'nonhuman_synthetic_control_not_accuracy_or_formal_reliability_estimate': True,
})
readme = '''6项预先隐藏独立控制按原输入/原预期首次各执行一次：SourcePacket、RelationView、judge均6次；6项匹配，0数值差异、0技术异常；6次证据validator通过。

实际原文与范围复核：整数/中文31条同值；元数据31与原文32冲突不创建31条内容，当前31条保持五维NULL；当前确指真实32条时只S=1；明确41条第二款只E=1，兄弟风险/费用不复制；第二款实际未交付且无完整资源时保持五维NULL。

34个源几何行、8个上下文引文、8个当前连续锚点/命题检查通过。只核对当前源接口实际可供文本；独立保存原件与未交付中段不被注入候选。source-only输入和预期分离；代码、输入、NULL期望均不改，无重新执行或挑选结果。

自然生成4个only_IF单位和8个typed子集单位。4个S/E正类由S/E/Ec受限单位消费，违规0；only_IF正消费0，所以I/F正类交集未动态实测。静态消费者交集与原生产路径摘录另存，不能以未出现的正消费宣称普遍通过。

即时events/results均逐条flush。完整首次五维输出、原始源位置、关系/请求/消费路径、全部固定原文与预期和五模块快照均保存。失败全文文件为空，明确0失败，不删除失败或补0/NULL。当前只有6项合成代码审查，无真实政策新ID、实际cohort、主LLM部分标签、真人参照或正式统计。

output-seal.json先枚举明确现存数据文件，再写seal；自身名字直接排除，写后核查不在members。原preparation-seal和全部10成员保持原SHA。
'''
with (OUT / 'README.txt').open('x', encoding='utf-8') as stream:
    stream.write(readme)
write('final-readback.json', {
    'case_N': 6,
    'original_controls_equal_input_snapshot': bind(PREP / 'controls6-fixed-before-execution.json')['sha256'] == bind(OUT / 'input-snapshot/controls6-fixed-before-execution.json')['sha256'],
    'original_preparation_members_verified_N': 10,
    'candidate_active_snapshot_5modules_and_seals_unchanged': True,
    'immediate_results_equal_full_results': True,
    'start_N': sum(e['event'] == 'case_start' for e in events),
    'judge_enter_N': sum(e['event'] == 'judge_enter' for e in events),
    'judge_return_N': sum(e['event'] == 'judge_return' for e in events),
    'result_saved_N': sum(e['event'] == 'case_result_saved' for e in events),
    'preparation_seal_own_member_N': sum(Path(m['path']).resolve() == (PREP / 'preparation-seal.json').resolve() for m in preseal['output_members']),
    'expected_or_candidate_changed': False,
})

seal_path = OUT / 'output-seal.json'
assert not seal_path.exists()
members = [bind(p) for p in sorted(OUT.rglob('*'))
           if p.is_file() and p.name != 'output-seal.json' and '__pycache__' not in p.parts]
assert all(Path(m['path']).resolve() != seal_path.resolve() for m in members)
write('output-seal.json', {
    'status': 'sealed_first_execution_hidden6_nonhuman_independent_code_audit',
    'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'original_preparation_seal': input_seal['original_preparation_seal'],
    'candidate_pre_execution_seal': input_seal['candidate_pre_execution_seal'],
    'algorithm_bindings': input_seal['algorithm_bindings'],
    'output_members': members,
    'seal_self_excluded': True,
    'no_original_or_candidate_mutation': True,
    'no_real_human_reference_or_statistical_result': True,
})
sealed = load(seal_path)
assert all(Path(m['path']).resolve() != seal_path.resolve() for m in sealed['output_members'])
for m in sealed['output_members']:
    assert bind(Path(m['path'])) == m
print(json.dumps({'seal': bind(seal_path), 'members_N': len(members),
                  'self_member_N': 0, 'all_members_readback_valid': True,
                  'candidate_judge_attempts_N': summary['candidate_judge_attempts_N'],
                  'matched_N': summary['matched_N']}, ensure_ascii=False))
