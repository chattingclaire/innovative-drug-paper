"""Document input comparison and existing contract limits; no labels or engines."""
from pathlib import Path
import hashlib
import json
import datetime

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OUT = Path(__file__).resolve().parent


def load(p):
    return json.loads(Path(p).read_bytes())


def bind(p):
    p = Path(p).resolve(); raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def excerpt(rel, first, last):
    p = ROOT / rel
    lines = p.read_text().splitlines(keepends=True)
    return {'file_binding': bind(p), 'line_interval_inclusive': [first, last],
            'literal_quote': ''.join(lines[first - 1:last])}


summary = load(OUT / 'summary.json')
records = load(OUT / 'record-byte-and-context-comparison.json')['records']
assert len(records) == 4481
assert sum(r['inner_source_bundle_bytes_equal'] for r in records) == 3254
assert all(not r['whole_file_bytes_equal'] and not r['whole_compact_packet_bytes_equal'] for r in records)
checks = load(ROOT / '06-coding/common-material-new-batch-plan-sol/17-original-binding-checks.json')['checks']
assert len(checks) == 17
for c in checks:
    assert bind(c['original']['path']) == c['original']
    assert bind(c['candidate_copy']['path']) == c['candidate_copy']
    assert c['original']['sha256'] == c['candidate_copy']['sha256']
    assert Path(c['original']['path']).read_bytes() == Path(c['candidate_copy']['path']).read_bytes()
write('external-original-copy-readback.json', {'file_N': 17, 'checks': checks,
                                           'all_same_original_bytes': True,
                                           'no_original_locator_or_input_changed': True})
contract = [
    excerpt('03-manual/full4481-common-release-20261010-root/common-execution-protocol.txt', 5, 15),
    excerpt('06-coding/native-full4481-v1-sol/actor-instructions.txt', 3, 9),
    excerpt('06-coding/native-full4481-v1-sol/actor-instructions.txt', 17, 25),
    excerpt('06-coding/native-full4481-v1-sol/validate-structured-batch.py', 78, 93),
    excerpt('07-statistics/human200-machine-reference-handoff-sol/handoff.py', 81, 92),
    excerpt('07-statistics/human200-machine-reference-handoff-sol/handoff.py', 245, 255),
    excerpt('07-statistics/prospective-dynamic-domain-engine-sol/scope_admission.py', 234, 251),
]
write('existing-contract-basis.json', {
    'excerpts': contract,
    'candidate_plan_self_limits': load(ROOT / '06-coding/common-material-new-batch-plan-sol/summary.json')['required_before_any_GO'],
    'same_five_role_prepared_inventory': load(ROOT / '06-coding/common-material-new-batch-plan-sol/equal-role-planned-input-bindings.json'),
    'old_handoff_or_dynamic_engine_invoked': False,
})
write('report.json', {
    'status': 'bounded_read_only_future_execution_planning',
    'actual_counts': {k: summary[k] for k in [
        'record_N', 'inner_source_bundle_unchanged_N', 'inner_source_bundle_changed_N',
        'source_record_exact_equal_N', 'whole_packet_file_byte_equal_N',
        'whole_compact_packet_byte_equal_N', 'outer_changed_field_counts',
        'inner_changed_field_counts', 'record_categories', 'same_ordered_batch_group_N',
        'same_ordered_batch_all_inner_material_equal_group_N',
        'same_ordered_batch_all_inner_material_equal_record_N',
        'old_actual_packet_file_bytes_sum', 'candidate_actual_compact_packet_plus_LF_sum']},
    'material_identity': {
        'genuinely_same_inner_source_bundle_N': 3254,
        'these_same_inner_records_differ_only_in_packet_version_provenance_and_serialization_envelope': True,
        'changed_material_records_N': 1227,
        'current_source_record_and_original_context_fields_unchanged_N': 4481,
        'no_same_full_packet_bytes_for_any_record': True,
        'original17_copy_bytes_equal': True,
    },
    'prompt_protocol_settings': {
        'manual_prompt_protocol_copy_exact_bytes_equal': True,
        'paths_differ': True,
        'old_requested_model': 'gpt-6.1-sol', 'old_requested_effort': 'ultra',
        'protocol_limits': {'context_unit': 'batch', 'max_records': 12, 'packet_bytes': 260000, 'max_parallel': 3, 'max_total_technical_attempts': 3},
        'old_groups_N': 504, 'candidate_groups_N': 659,
        'candidate_final_runtime_assignment_actor_instruction_request_settings_frozen': False,
        'provider_wire_body_or_complete_runtime_tool_context_available_to_this_audit': False,
        'temperature_seed_or_actual_serving_model_equivalence_not_inferred': True,
    },
    'current_contract_conclusion': {
        'automatic_old_result_reuse_for_new_candidate_admitted': False,
        'reason': '旧首答技术验证绑定原packet SHA、原run/batch、完整顺序与原manual/prompt路径；旧统计handoff绑定原504整批终结campaign及旧共同材料/设计。当前准备计划未给来源等价复用的执行授权。3254内层相同或420同组同内层，只是可核验输入事实，不解除完整字节/上下文/版本和终结接收约束。',
        'old_running_attempt_may_receive_new_source_materials_as_technical_retry': False,
        'new_material_1227_can_be_claimed_read_by_old_run': False,
        'all4481_must_rerun_claimed': False,
        'future_limited_reuse_requires_prospective_protocol_decision': '如拟复用，须在未来新执行/结果选择前明确允许比较的材料身份层、原批次上下文及旧原件归属与新共同材料接口；保留原run/packet/首答收据，不改绑旧first、不按标签决定复用。还须完成既有整批终结接收及适用统计scope登记。此处不制定新协议、不登记scope，也不认定420已可复用。',
        'candidate_same_five_role_inventory_is_preparation_only_not_actual_delivery': True,
    },
    'actual_read_limit': '机械全字节读取/解析旧4481 packet、新4481 packet与659 source-inputs.jsonl，核原504 assignments及候选1329 seal成员；阅读固定指令/协议和有限准入代码。不是provider wire、模型工具历史或政策语义阅读审计。',
    'main_LLM_partial_labels_or_machine_predictions_read': False,
    'old_campaign_terminal_status_independently_reviewed_now': False,
    'no_label_based_decision': True,
    'model_dispatch_retry_selection_or_actual_statistics_N': 0,
    'protocol_or_scope_modified': False,
    'reuse_or_GO_declared': False,
})
readme = '''3254条内层source_bundle字节相同，1227条改变；4481条当前source_record（含原contexts）均相同。3254条只有外层packet_version、新候选provenance与序列化差异；完整packet原文件及紧凑字节相同均0。1227条内层另有common_source_bundle_version、source_bundle_extension、source_full_text_resources差异，各1227。

旧504批到候选659批：151组成员顺序相同；149组/420条整组内层材料相同。13条自身内层相同但同组有材料变化，2821条自身内层相同却换了批次成员。每条input SHA、字段差异、旧/新批次及类别已另存可核验清单。

manual/prompt/protocol复制字节相同而路径不同；旧请求GPT-6.1 Sol/ultra、context_unit=batch，原分批及整批首答/重试约束保持。新目录只准备完整source-only输入，没有最终runtime assignment/actor request/settings或实际派发。实际provider wire及完整工具上下文不可得，不能把文件字节比较称全模型输入完全等价。旧紧凑包合计77905594字节，候选实际紧凑JSONL为123466714；漂亮JSON文件151070247字节未用来判断260000预算。

当前契约不授权自动复用或把旧运行改称新材料运行。原技术验证绑定完整原packet SHA和原整批；旧200统计入口固定原campaign/material/域，动态入口要求ROOT登记材料/版本及完整机器终结收据。3254不能自动按逐条独立上下文处理；420也只是内层+成员事实，完整wrapper仍不同。新材料1227不能声称旧模型已读；旧技术重试要求原输入不变，不能夹入新材料。

未来如拟有限复用，需要预先明确材料身份比较层、批次上下文、旧原件归属与新执行接口；保留真实旧首答/收据，不能改packet绑定或按标签选择。本审查不制定该协议，不注册scope，不宣布复用/GO，也不要求全4481必然重跑。五方同inventory仅准备状态，无实际交付证明。

实际只读输入和已有技术契约。未读取主LLM部分标签或任何first/attempt/root-selection结果，未重试、选择、调用模型/judge/统计。没有核验本轮旧campaign终结状态。输出是未来执行规划；不把机械解析当模型完整阅读或正式验证。
'''
with (OUT / 'README.txt').open('x', encoding='utf-8') as f:
    f.write(readme)
write('readback.json', {
    'record_comparison_N': len(records), 'labels_read_N': 0,
    'old_assignments_N': 504, 'candidate_input_batches_N': 659,
    'candidate_seal_member_N': 1329, 'old_new_packet_files_N_each': 4481,
    'original_copy_readback_N': 17,
    'summary_and_record_categories_match': True,
    'original_or_upstream_files_modified': False,
    'output_seal_self_excluded': True,
})
seal_path = OUT / 'output-seal.json'
assert not seal_path.exists()
members = [bind(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name != 'output-seal.json']
assert not any(Path(m['path']).resolve() == seal_path.resolve() for m in members)
write('output-seal.json', {'status': 'sealed_read_only_execution_planning_not_reuse_or_GO',
                           'at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                           'output_members': members, 'self_excluded': True,
                           'labels_or_results_used_in_decision': False})
for m in load(seal_path)['output_members']:
    assert bind(m['path']) == m
print(json.dumps({'seal': bind(seal_path), 'members_N': len(members), 'self_member_N': 0,
                  'all_members_valid': True, 'reuse_or_GO': False}, ensure_ascii=False))
