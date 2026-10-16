"""Finite NONHUMAN scope checks; these do not produce dimension labels."""
import argparse
import copy
import json
from pathlib import Path
import select_static_impact as selector


def run():
    config = json.loads((Path(__file__).parent / 'input-bindings.json').read_text())
    proof, entry = selector.static_code_proof(config)
    if not proof['passed']:
        raise AssertionError('Bound static code proof failed')
    base = {'source_record': {'text': '药审中心开展研发。', 'source_ref': {'sha256': 'a' * 64}, 'contexts': []},
            'source_full_text_resources': []}
    cases = []
    def case(name, text=None, context=None, extra=None, expected=False, expected_reason=None):
        bundle = copy.deepcopy(base)
        if text is not None:
            bundle['source_record']['text'] = text
        if context is not None:
            bundle['source_record']['contexts'] = [{'text': context}]
        if extra:
            bundle.update(extra)
        cases.append((name, bundle, expected, expected_reason))
    case('plain_development_without_new_helper_witness')
    case('data_security_owner_selected', text='计算机系统应保障数据安全。', expected=True, expected_reason='S_security_scope')
    case('drug_safety_data_stays_selected', text='提供药物安全性数据。', expected=True, expected_reason='S_security_scope')
    case('current_contraindication_question', text='是否有用药禁忌？', expected=True, expected_reason='S_risk_action_scope')
    case('context_only_risk_is_not_missed', context='审核以下处方禁忌。', expected=True, expected_reason='S_risk_action_scope')
    case('derived_literal_snapshot_is_in_envelope', extra={'source_full_text_resources': [{'kind': 'verbatim_UTF8_snapshot_text', 'text': '药物可能引起肝损伤。'}]}, expected=True, expected_reason='S_risk_action_scope')
    case('named_medication_control_without_risk_word', text='文件“核对处方剂量是否准确无误”的格式应完整。', expected=True, expected_reason='S_named_content_scope')
    case('administrative_description_is_not_Unit_text', extra={'administrative_description': '文件路径与附件元数据'} )
    case('NFKC_and_whitespace_risk', text='是否有用药禁　忌？', expected=True, expected_reason='S_risk_action_scope')
    case('ASCII_risk_boundary_relaxed_conservatively', text='xSAEx', expected=True, expected_reason='S_risk_action_scope')
    plan = {'source_full_text_resources': [{'source_sha256': 'a' * 64, 'paragraphs': [{'text': '“同源方案”试点项目'}]}]}
    case('F_same_source_named_plan', text='申请加入该试点。', extra=plan, expected=True, expected_reason='F_structured_plan_entry')
    case('F_exact_matching_view_space_removal', text='申　请加入该试点。', extra=plan, expected=True, expected_reason='F_structured_plan_entry')
    wrong = copy.deepcopy(plan); wrong['source_full_text_resources'][0]['source_sha256'] = 'b' * 64
    case('F_wrong_source_cannot_reach_changed_plan_suffix', text='申请加入该试点。', extra=wrong)
    case('F_outer_current_gate_false', text='登记表。', extra=plan)
    case('F_absent_named_plan_structure', text='申请加入该试点。', extra={'source_full_text_resources': [{'source_sha256': 'a' * 64, 'paragraphs': [{'text': '一般计划'}]}]})
    results = []
    for name, bundle, expected, reason in cases:
        actual = selector.source_gate(bundle, entry)
        passed = bool(actual) == expected and (reason is None or reason in actual)
        results.append({'name': name, 'NONHUMAN': True, 'input': bundle,
                        'expected_selected': expected, 'required_reason': reason,
                        'actual_reasons': sorted(actual), 'passed': passed})
    return {'kind': 'finite_static_selection_controls_not_classification',
            'N': len(results), 'passed_N': sum(r['passed'] for r in results),
            'classifier_executions': 0, 'bound_AST_proof': proof,
            'selector_binding': selector.binding(selector.__file__), 'cases': results}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = run()
    with args.out.open('x') as out:
        out.write(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'N': result['N'], 'passed_N': result['passed_N'], 'classifier_executions': 0}))
    if result['N'] != result['passed_N']:
        raise SystemExit(1)
