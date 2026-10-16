"""Prepare a separate candidate07 design. Never invoke a CLI/model or edit history."""
import difflib
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate06-design/revision-v2'
DRAFT = ROOT / 'outputs/coding-revision-20261008-r4/llm-candidate07-design'
PYTHON = '/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def member(ident, text, ones=(), contexts=None, fairness=(), innovation=()):
    return {'input': {'id': ident, 'text': text, 'contexts': contexts or {}},
            'labels': {d: int(d in ones) for d in DIMS},
            'fairness_subtypes': list(fairness), 'innovation_subtypes': list(innovation),
            'safety_quality_basis': 'no_quality_basis'}


def main():
    assert not (HERE / 'design_freeze.json').exists(), 'Frozen designs must not be rebuilt.'
    prefix = (HERE / 'execution_layer_PROPOSED.txt').read_text()
    # Only the execution layer is replaced. Every byte of the complete manual,
    # schema examples and technical citation footer is retained.
    marker = '--- 冻结的完整手册（原样） ---'
    previous = (OLD / 'candidate06_prompt_PROPOSED.txt').read_text()
    assert previous.count(marker) == 1
    suffix = marker + previous.split(marker, 1)[1]
    (HERE / 'execution_layer_PROPOSED.txt').write_text(prefix)
    prompt = prefix.rstrip() + '\n\n' + suffix
    assert prompt.split(marker, 1)[1] == previous.split(marker, 1)[1]
    assert 'RECODE25-' not in prompt and '0.80' not in prompt
    (HERE / 'candidate07_prompt_PROPOSED.txt').write_text(prompt)
    (HERE / 'candidate06_to_07_prompt.diff').write_text(''.join(difflib.unified_diff(
        previous.splitlines(keepends=True), prompt.splitlines(keepends=True),
        fromfile='candidate06_frozen_prompt', tofile='candidate07_proposed_prompt')))
    for source, dest in [
        ('exposed240_inputs_UNCHANGED.jsonl', 'exposed240_inputs_UNCHANGED.jsonl'),
        ('synthetic62_inputs_UNCHANGED.jsonl', 'synthetic62_inputs_UNCHANGED.jsonl'),
        ('synthetic24_inputs_PROPOSED.jsonl', 'synthetic24_inputs_UNCHANGED.jsonl'),
        ('synthetic86_expected_PRIVATE_PROPOSED.json', 'synthetic86_expected_INHERITED_PRIVATE.json'),
        ('manual_rule_basis.json', 'manual_rule_basis_UNCHANGED.json')]:
        shutil.copyfile(OLD / source, HERE / dest)
    shutil.copyfile(DRAFT / 'prompt_conflict_and_mechanism_audit_PRIVATE.json', HERE / 'prompt_conflict_and_mechanism_audit_PRIVATE.json')
    mechanism = json.loads((HERE / 'prompt_conflict_and_mechanism_audit_PRIVATE.json').read_text())
    mechanism['candidate06_prompt_source'] = str(OLD / 'candidate06_prompt_PROPOSED.txt')
    dump(HERE / 'prompt_conflict_and_mechanism_audit_PRIVATE.json', mechanism)
    shutil.copyfile(DRAFT / 'preceding06_context_exposure_addendum.json', HERE / 'preceding06_context_exposure_addendum_INHERITED.json')
    runtime = HERE / 'runtime-unchanged-v2'
    runtime.mkdir(exist_ok=True)
    for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
        shutil.copyfile(OLD / 'runtime-unchanged-v2' / name, runtime / name)

    pairs = []
    def pair(i, target, rationale, a, b, basis):
        for side, obj in zip('AB', [a, b]): obj['input']['id'] = f'C07-PAIR-{i:02d}-{side}'
        pairs.append({'pair_id': f'C07-PAIR-{i:02d}', 'target': target, 'rationale': rationale,
                      'manual_basis': basis, 'members': [a, b], 'synthetic_not_policy_quote': True,
                      'not_derived_from_reserved_contexts': True})
    pair(1, '指南制定目的/资料办理与实体科研指导', '创新对象和帮助宗旨不替代当前提供的研发支持内容；真实科学指导仍纳入。',
         member('', '为便于原创药物研发团队按期递交文件，现发布研究资料排版说明。'),
         member('', '审评部门为原创药物研发团队安排药学专家，为研发方案的科学设计提出技术建议。', ['I'], innovation=['research_support']),
         ['v1.3:166', 'v1.4:13', 'v1.4:17'])
    child = '本期药物治疗支出不得超过约定预算的两倍。'
    pair(2, '相同经济子条件：申请续约与续签后继续有效', '真实父谓词决定是否存在保障连续，不另要求逐字重复患者权益承诺。',
         member('', child, ['Ec'], {'verified_parent_context': [{'text': '本节对象为既有医保药品协议；符合以下条件可以提交续约申请，是否续签另行决定。'}]}),
         member('', child, ['Ec', 'F'], {'verified_parent_context': [{'text': '本节对象为既有医保药品协议；符合以下条件可续签，协议再有效十八个月。'}]}, fairness=['access']),
         ['v1.3:17', 'v1.4:7', 'v1.4:22'])
    ctx = {'paragraph_context': [{'text': '本节讨论药物毒性资料整理。'}]}
    pair(3, '安全主题下的一般沟通与当前风险分析', '主题可消解对象，当前仍须有安全评价、证据或风险控制命题。',
         member('', '未列明的问题可通过视频会议沟通，明年修订资料指引。', contexts=ctx),
         member('', '未列明的毒性问题应在视频会议中逐项分析其发生原因，并确定风险控制措施。', ['S'], ctx),
         ['v1.3:21', 'v1.3:65', 'v1.3:67', 'v1.4:9'])
    pair(4, '拟定保障范围与独立费用责任', '计划性不排除当前覆盖命题，覆盖限制本身不自动成为经济内容。',
         member('', '评议组拟将该药的保障适用人群限定为经确诊的成年患者。', ['F'], fairness=['access']),
         member('', '评议组拟将该药的保障适用人群限定为经确诊的成年患者，并规定基金承担药费的百分之七十。', ['Ec', 'F'], fairness=['access']),
         ['v1.3:11', 'v1.3:35', 'v1.3:37', 'v1.4:21'])
    pair(5, '一般机构资金稳定与药品支付基金约束', '经济性须有药品治疗/支付资源联系，不要求金额或价格变化。',
         member('', '本机构档案室的年度运行不得危及单位储备资金的稳定。'),
         member('', '制定年度药品支付预算时，应以医保基金的可持续使用为约束。', ['Ec']),
         ['v1.3:35', 'v1.3:37'])
    pair(6, '拟申请扩围的手续与拟定具体扩围', '两侧均非既成结果；关键在申请手续还是当前提出的具体保障范围。',
         member('', '企业拟申请扩大保障范围的，应先预约受理时段。'),
         member('', '本年度拟将该药纳入保障范围。', ['F'], fairness=['access']),
         ['v1.3:11', 'v1.4:21', 'v1.4:22'])
    pair(7, '信息载体中的内部归档与常规领药渠道', '不以信息系统形式排除实际渠道，也不把档案连通推为患者渠道。',
         member('', '平台连通档案室与统计室，保证药品处方扫描件及时归档。'),
         member('', '平台连通门诊开方机构与协议药房，使处方可转送药房并由患者领药。', ['F'], fairness=['access']),
         ['v1.3:152', 'v1.4:24'])
    pair(8, '一般减量与具体监测管理负担', '同一老年减量对象不自动临床管理；独立监测负担与难度评价可纳入。',
         member('', '老年用药者可能需要把常规给药量减少到原来的一半。'),
         member('', '应评价老年用药者减量期间每日监测所造成的管理负担，以及社区药房完成监测的难度。', ['F'], fairness=['clinical_management']),
         ['v1.3:53', 'v1.3:123', 'v1.4:25'])
    pair(9, '覆盖和保险承担与独立患者负担依据', '保险责任支持Ec、覆盖支持access；affordability须另有患者支付能力/药费负担依据。',
         member('', '本保障方案覆盖该药，相关药费由保险机构承担。', ['Ec', 'F'], fairness=['access']),
         member('', '本保障方案覆盖该药；因患者难以负担自付药费，规定减免其个人药费。', ['Ec', 'F'], fairness=['access', 'affordability']),
         ['v1.3:35', 'v1.3:53', 'v1.3:156'])
    pair(10, '实体创新支持与有效性/安全性的独立共存', '支持内容不得被程序排除；真实效果和风险内容分别判，不从创新对象复制属性子类。',
         member('', '药审机构为原创药物研发团队配置专家，比较不同临床终点反映治疗获益的能力并提出设计建议。', ['E', 'I'], innovation=['research_support']),
         member('', '药审机构为原创药物研发团队配置专家，针对药物毒性风险提出临床监测方案建议。', ['S', 'I'], innovation=['research_support']),
         ['v1.3:21', 'v1.3:29', 'v1.3:31', 'v1.3:65', 'v1.3:166', 'v1.4:13'])
    new = [m for p in pairs for m in p['members']]
    dump(HERE / 'synthetic20_pairs_PRIVATE_PROPOSED.json', {'status': 'PREEXECUTION_REQUIRE_INDEPENDENT_REVIEW', 'pairs': pairs})
    (HERE / 'synthetic20_inputs_PROPOSED.jsonl').write_text(''.join(json.dumps(m['input'], ensure_ascii=False)+'\n' for m in new))
    inherited = json.loads((HERE / 'synthetic86_expected_INHERITED_PRIVATE.json').read_text())['tests']
    dump(HERE / 'synthetic106_expected_PRIVATE_PROPOSED.json', {'status': 'PREEXECUTION_NOT_MODEL_TESTED',
        'inherited86_expectations_unmodified': True, 'preexisting_disputed_control': 'C05-NEW-019',
        'inherited008_extra_affordability_objection_retained': True,
        'inherited034_reason_precision_issue_retained': True, 'new_pairs': 10, 'tests': inherited + new})

    plan = {'status': 'DESIGN_ONLY_NOT_AUTHORIZED_NOT_EXECUTED', 'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'runs': []}
    for n, src, workers in [(240, 'exposed240_inputs_UNCHANGED.jsonl', 3), (62, 'synthetic62_inputs_UNCHANGED.jsonl', 1),
                            (24, 'synthetic24_inputs_UNCHANGED.jsonl', 1), (20, 'synthetic20_inputs_PROPOSED.jsonl', 1)]:
        name = f'{"exposed" if n==240 else "synthetic"}{n}-candidate07-first-run'
        command = [PYTHON, str(runtime / 'run_production_v32.py'), '--input', str(HERE / src),
            '--expected-input-sha256', sha(HERE / src), '--prompt', str(HERE / 'candidate07_prompt_PROPOSED.txt'),
            '--expected-n', str(n), '--run-name', name, '--batch-size', '25', '--workers', str(workers),
            '--max-attempts', '3', '--purpose', 'One complete candidate07 development run; no semantic retries, label splicing, independent-validation claim, production or manuscript update.']
        plan['runs'].append({'n': n, 'batch_size': 25, 'logical_requests': (n+24)//25, 'workers': workers,
            'plan_only_command': command + ['--plan-only'], 'future_execution_command_after_separate_root_authorization_only': command})
    plan.update({'nominal_logical_requests': 15, 'maximum_identical_technical_attempts': 45, 'model_calls_by_this_design': 0,
        'scope': [240, 62, 24, 20], 'synthetic_total': 106, 'old240_62_24_bytes_order_batch_membership_preserved': True,
        'manuals_schema_validator_runner_unchanged': True, 'first_technically_valid_only': True, 'full_corpus': False,
        'separate_root_authorization_required': True, 'raw_outputs_isolated_from_all_old_candidates': True})
    dump(HERE / 'candidate07_execution_plan_PROPOSED.json', plan)
    qa = {'status': 'STRUCTURAL_DESIGN_QA_ONLY_NO_MODEL', 'complete_manual_and_footer_byte_identical': True,
          'old240_62_24_bytes_unchanged': True, 'inherited86_expected_records_unchanged': True,
          'runtime_schema_validator_unchanged': True, 'new_pairs': 10, 'new_units': len(new),
          'predeclared_logical_requests': 15, 'max_technical_attempts': 45, 'model_calls': 0,
          'all_old_outputs_untouched': True}
    assert len({m['input']['id'] for m in new}) == 20
    for source, dest in [('exposed240_inputs_UNCHANGED.jsonl', 'exposed240_inputs_UNCHANGED.jsonl'),
                         ('synthetic62_inputs_UNCHANGED.jsonl', 'synthetic62_inputs_UNCHANGED.jsonl'),
                         ('synthetic24_inputs_PROPOSED.jsonl', 'synthetic24_inputs_UNCHANGED.jsonl')]:
        assert (OLD/source).read_bytes() == (HERE/dest).read_bytes()
    for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
        assert (OLD/'runtime-unchanged-v2'/name).read_bytes() == (runtime/name).read_bytes()
    dump(HERE / 'design_structural_QA.json', qa)
    print(json.dumps(qa, ensure_ascii=False))


if __name__ == '__main__':
    main()
