"""Synthetic JSON-contract checks only; never calls/imports the model runner.

The fixture text is deliberately not a policy source. Its arbitrary binary
values test contracts and must not be treated as teaching or reference labels.
"""
import ast
import copy
import hashlib
import json
import sys
import types
from pathlib import Path
from jsonschema import Draft202012Validator

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / '共同操作判据准备'
MANUAL = HERE.parents[1] / '定义溯源核查/测量与计数统一/共用编码手册.md'
MANUAL_SHA = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
EXECUTION = 'LLM-measurement-semantic-24007a19a724'
OLD_EXECUTION = 'LLM-common-operations-fb78f1922e2e'
DIMS = ['S', 'E', 'Ec', 'I', 'F']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    schema = json.loads((HERE / 'output_schema_codex_compatible.json').read_text(encoding='utf-8'))
    Draft202012Validator.check_schema(schema)
    schema_validator = Draft202012Validator(schema)
    validator = types.ModuleType('structure_only_validator')
    source = (HERE / 'validate_binary_output.py').read_text(encoding='utf-8')
    exec(compile(source, str(HERE / 'validate_binary_output.py'), 'exec'), validator.__dict__)
    packet = {'rows': [{'id': 'STRUCTURE-ONLY-A', 'text': '校验：甲\u00a0乙，丙。',
                        'contexts': [{'text': '语境校验：丁；戊。', 'sha256': 'METADATA-ONLY'}]}]}
    positive = {'protocol_version': 'COMMON-5D-20261009', 'execution_version': EXECUTION,
                'release_stage': 'development_labels', 'rows': [{
                    'id': packet['rows'][0]['id'], 'labels': {d: int(d == 'I') for d in DIMS},
                    'dimension_reasons': {d: '仅检验JSON合同，不作政策语义判断。' for d in DIMS},
                    'evidence': [{'dimension': 'I', 'source': 'unit', 'quote': '甲\u00a0乙'},
                                 {'dimension': 'I', 'source': 'context', 'quote': '丁；戊'}],
                    'fairness_subtypes': [], 'innovation_subtypes': ['research_support'],
                    'safety_quality_basis': 'no_quality_basis', 'quality_content_without_safety': False
                }], 'issue_records': []}
    results = []

    def check(name, output, expected_valid, required_error=None, schema_expected=None, inp=None):
        errors = validator.validate(packet if inp is None else inp, output)
        schema_errors = [e.message for e in schema_validator.iter_errors(output)]
        passed = (not errors) == expected_valid
        if required_error is not None:
            passed = passed and any(required_error in error for error in errors)
        if schema_expected is not None:
            passed = passed and (not schema_errors) == schema_expected
        results.append({'name': name, 'passed': passed, 'validator_valid': not errors,
                        'validator_errors': errors, 'schema_valid': not schema_errors,
                        'schema_errors': schema_errors})

    check('current_shape_and_literal_unit_context_accepted', positive, True, schema_expected=True)
    zero = copy.deepcopy(positive)
    zero['rows'][0]['labels'] = {d: 0 for d in DIMS}
    zero['rows'][0]['evidence'] = []
    zero['rows'][0]['innovation_subtypes'] = []
    check('all_zero_shape_accepted', zero, True, schema_expected=True)
    old = copy.deepcopy(positive)
    old['execution_version'] = OLD_EXECUTION
    check('old_execution_identity_rejected', old, False, 'root:execution_version', False)
    missing = copy.deepcopy(positive)
    missing['rows'][0]['evidence'] = [missing['rows'][0]['evidence'][1]]
    check('one_without_unit_quote_rejected', missing, False, 'missing_literal_unit_evidence', True)
    normalized = copy.deepcopy(positive)
    normalized['rows'][0]['evidence'][0]['quote'] = '甲 乙'
    check('unicode_whitespace_normalization_rejected', normalized, False, 'nonliteral_quote', True)
    punctuation = copy.deepcopy(positive)
    punctuation['rows'][0]['evidence'][0]['quote'] = '乙,丙'
    check('punctuation_rewrite_rejected', punctuation, False, 'nonliteral_quote', True)
    context = copy.deepcopy(positive)
    context['rows'][0]['evidence'][1]['quote'] = '丁,戊'
    check('nonliteral_context_rejected', context, False, 'nonliteral_quote', True)
    metadata = copy.deepcopy(positive)
    metadata['rows'][0]['evidence'][1]['quote'] = 'METADATA-ONLY'
    check('metadata_is_not_context_evidence', metadata, False, 'nonliteral_quote', True)
    binary = copy.deepcopy(positive)
    binary['rows'][0]['labels']['I'] = True
    check('boolean_is_not_binary_integer', binary, False, 'not_binary_integer', False)
    subtype = copy.deepcopy(zero)
    subtype['rows'][0]['fairness_subtypes'] = ['patient_affordability']
    check('fairness_subtype_zero_conflict_rejected', subtype, False, 'fairness_subtypes_label_conflict', True)
    quality = copy.deepcopy(positive)
    quality['rows'][0]['labels']['S'] = 1
    quality['rows'][0]['evidence'].append({'dimension': 'S', 'source': 'unit', 'quote': '丙'})
    quality['rows'][0]['quality_content_without_safety'] = True
    check('safety_one_quality_without_safety_conflict_rejected', quality, False,
          'S_one_quality_content_without_safety_conflict', True)
    unresolved = copy.deepcopy(zero)
    unresolved['rows'] = []
    unresolved['issue_records'] = [{'id': packet['rows'][0]['id'], 'status': 'material_issue',
                                  'description': '合成测试：必要材料缺失，禁止占位标签。'}]
    check('unresolved_material_issue_preserved_as_failure', unresolved, False,
          'unresolved_material_issue', True)

    # A literal substring may omit a negator. Acceptance here documents a
    # validator limitation, and is expressly not a semantic endorsement.
    tail_packet = copy.deepcopy(packet)
    tail_packet['rows'][0]['text'] = '合成校验：不符合技术安排。'
    tail = copy.deepcopy(positive)
    tail['rows'][0]['evidence'] = [{'dimension': 'I', 'source': 'unit', 'quote': '符合技术安排'}]
    tail_errors = validator.validate(tail_packet, tail)

    manual = MANUAL.read_bytes()
    prompt = (HERE / '编码提示.txt').read_bytes()
    embedded = prompt.split(b'<common_manual>\n', 1)[1].split(b'</common_manual>', 1)[0]
    old_schema = json.loads((OLD / 'output_schema_codex_compatible.json').read_text(encoding='utf-8'))
    old_row = old_schema['properties']['rows']['items']['properties']
    new_row = schema['properties']['rows']['items']['properties']
    record = json.loads((HERE / '准备记录.json').read_text(encoding='utf-8'))
    old_now = {str(p): sha(p) for p in OLD.iterdir() if p.is_file()}
    runner = (HERE / 'run_coding.py').read_text(encoding='utf-8')
    ast.parse(runner)
    prompt_text = prompt.decode('utf-8')
    static = {
        'exact_manual_bytes_embedded': embedded == manual,
        'manual_sha_matches_lock': hashlib.sha256(manual).hexdigest() == MANUAL_SHA,
        'execution_identity_matches_schema_and_validator_and_runner':
            schema['properties']['execution_version']['const'] == EXECUTION
            and schema['properties']['execution_version']['enum'] == [EXECUTION]
            and EXECUTION in source and EXECUTION in runner and EXECUTION in prompt_text,
        'old_identity_absent_from_all_core_files': all(
            OLD_EXECUTION not in (HERE / n).read_text(encoding='utf-8')
            for n in ['编码提示.txt', 'output_schema_codex_compatible.json', 'validate_binary_output.py', 'run_coding.py']),
        'validator_only_execution_identity_changed':
            source == (OLD / 'validate_binary_output.py').read_text(encoding='utf-8').replace(OLD_EXECUTION, EXECUTION),
        'runner_only_execution_identity_changed':
            runner == (OLD / 'run_coding.py').read_text(encoding='utf-8').replace(OLD_EXECUTION, EXECUTION),
        'fixed_model_and_effort_preserved': "MODEL='gpt-5.6-sol';EFFORT='medium'" in runner,
        'fairness_and_quality_schema_contracts_unchanged': all(
            new_row[k] == old_row[k] for k in ['fairness_subtypes', 'safety_quality_basis', 'quality_content_without_safety']),
        'innovation_enum_preserved': new_row['innovation_subtypes']['items'] == old_row['innovation_subtypes']['items'],
        'no_real_answer_ids_or_answer_paths_or_metrics_in_prompt': not any(
            x in prompt_text for x in ['RECODE25-', 'RECALL-BLIND-', 'expected_labels', 'expert_work_', 'private_selection',
                                       'development_outputs', 'all_predictions', '统计复算/', 'κ', 'F1', '0.80']),
        'old_preparation_unchanged': old_now == record['source_files_sha256'],
        'literal_negator_tail_limitation_observed': not tail_errors
    }
    report = {
        'status': 'structure_and_literal_checks_only',
        'all_structural_checks_pass': all(static.values()) and all(r['passed'] for r in results),
        'python_executable': sys.executable, 'python_version': sys.version,
        'manual_sha256': MANUAL_SHA, 'execution_identity': EXECUTION,
        'static_checks': static, 'synthetic_contract_cases': results,
        'limitations': {
            'literal_substring_does_not_verify_full_proposition_or_negation_scope': True,
            'literal_tail_case_validator_errors': tail_errors,
            'context_completeness_and_necessary_relation_not_verified': True,
            'semantic_classification_not_verified': True,
            'synthetic_fixtures_are_not_policy_teaching_or_reference_labels': True
        },
        'actual_model_calls': 0, 'runner_invocations': 0, 'plan_only_invocations': 0,
        'prepared_files_sha256': {n: sha(HERE / n) for n in ['编码提示.txt', 'output_schema_codex_compatible.json',
                                                           'validate_binary_output.py', 'run_coding.py',
                                                           'build_preparation.py', 'static_structure_checks.py']}
    }
    (HERE / '结构与引文核查.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'all_structural_checks_pass': report['all_structural_checks_pass'],
                      'case_count': len(results), 'static_checks': static,
                      'semantic_classification_not_verified': True}, ensure_ascii=False))
    assert report['all_structural_checks_pass']

if __name__ == '__main__':
    main()
