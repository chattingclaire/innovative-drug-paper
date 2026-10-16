"""Prepare candidate08 only; never invoke a CLI/model or edit frozen history."""
import ast
import difflib
import hashlib
import importlib.util
import json
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
OLD = HERE.parent / '候选方案'
OLD03 = ROOT / 'outputs/coding-revision-20261007-r3/llm-candidate03-development'
PROTOCOL = ROOT / 'outputs/coding-revision-20261007-r3/protocol'
PYTHON = '/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
MARKER = b'--- \xe5\x86\xbb\xe7\xbb\x93\xe7\x9a\x84\xe5\xae\x8c\xe6\x95\xb4\xe6\x89\x8b\xe5\x86\x8c\xef\xbc\x88\xe5\x8e\x9f\xe6\xa0\xb7\xef\xbc\x89 ---'
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dump(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def binding(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def member(text, ones=(), contexts=None, fairness=(), innovation=()):
    return {'input': {'id': '', 'text': text, 'contexts': contexts or {}},
            'labels': {d: int(d in ones) for d in DIMS},
            'fairness_subtypes': list(fairness), 'innovation_subtypes': list(innovation),
            'safety_quality_basis': 'no_quality_basis'}


def main():
    assert not (HERE / 'design_freeze.json').exists(), 'Never overwrite a frozen design.'
    old_prompt = (OLD / 'candidate07_prompt_PROPOSED.txt').read_bytes()
    assert old_prompt.count(MARKER) == 1
    suffix = MARKER + old_prompt.split(MARKER, 1)[1]
    prefix = (HERE / 'execution_layer_PROPOSED.txt').read_bytes().rstrip() + b'\n\n'
    prompt = prefix + suffix
    lock = read(HERE / 'prompt_lock_before_independent_inputs.json')
    assert hashlib.sha256(prompt).hexdigest() == lock['prompt']['sha256'], 'Prompt already locked; no fitting independent controls.'
    assert prompt.split(MARKER, 1)[1] == old_prompt.split(MARKER, 1)[1]
    assert (PROTOCOL / '完整五维手册-v1.3.md').read_bytes() in suffix
    substantive_v14 = (PROTOCOL / '共用操作说明-v1.4.md').read_bytes().split('## 版本与验证纪律'.encode())[0]
    assert substantive_v14.rstrip() in suffix
    assert b'RECODE25-' not in prompt and b'0.80' not in prompt
    (HERE / 'candidate08_prompt_PROPOSED.txt').write_bytes(prompt)
    for version, p in [('03-base-development', OLD03 / 'candidate03_prompt.txt'),
                       ('03-full-corpus-request-prompt', OLD03 / 'full-corpus-candidate03-material-v14-development/frozen_prompt.txt'),
                       ('07-frozen', OLD / 'candidate07_prompt_PROPOSED.txt')]:
        (HERE / f'{version}_to_08_prompt.diff').write_text(''.join(difflib.unified_diff(
            p.read_text().splitlines(keepends=True), prompt.decode().splitlines(keepends=True),
            fromfile=str(p), tofile='candidate08_proposed_prompt')))
    for name in ['exposed240_inputs_UNCHANGED.jsonl', 'synthetic62_inputs_UNCHANGED.jsonl',
                 'synthetic24_inputs_UNCHANGED.jsonl', 'synthetic20_inputs_PROPOSED.jsonl']:
        shutil.copyfile(OLD / name, HERE / name)
        assert (OLD / name).read_bytes() == (HERE / name).read_bytes()
    shutil.copyfile(OLD / 'synthetic106_expected_PRIVATE_PROPOSED.json', HERE / 'synthetic106_expected_INHERITED_PRIVATE.json')
    runtime = HERE / 'runtime-unchanged-v2'
    runtime.mkdir(exist_ok=True)
    for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
        shutil.copyfile(OLD / 'runtime-unchanged-v2' / name, runtime / name)
        assert (OLD / 'runtime-unchanged-v2' / name).read_bytes() == (runtime / name).read_bytes()

    pairs = []
    def pair(i, mechanism, a, b, basis):
        for side, obj in zip('AB', [a, b]):
            obj['input']['id'] = f'C08-PAIR-{i:02d}-{side}'
        pairs.append({'pair_id': f'C08-PAIR-{i:02d}', 'mechanism': mechanism,
                      'manual_basis': basis, 'members': [a, b],
                      'synthetic_not_policy_quote': True, 'not_from_reserved_originals': True,
                      'all_five_dimensions_and_output_fields_require_review': True})
    pair(1, '限定申报对象中的明确产品属性改变与首次申报身份分开',
         member('该药原获准的使用人群由成人增补为儿童，相关资料通过本期窗口递交。', ['I'], innovation=['attribute']),
         member('本期首次递交资料的药品，应通过指定窗口登记。'),
         ['v1.3:11', 'v1.3:142', 'v1.4:14'])
    pair(2, '同句程序不得抹去独立制剂改变；名称登记不自带创新',
         member('办理备案时，应说明该制剂由即释改为缓释的改变，并上传备案单。', ['I'], innovation=['attribute']),
         member('办理备案时，应填写该制剂的通用名称，并上传备案单。'),
         ['v1.3:43', 'v1.3:67', 'v1.3:142', 'v1.4:14', 'v1.4:16'])
    pair(3, '创新研发支持与申请人安全义务：两侧安全内容均保留',
         member('服务机构向原创药物研发团队提供毒性监测方案的技术指导。', ['S', 'I'], innovation=['research_support']),
         member('原创药物研发团队应执行毒性监测方案并报告监测结果。', ['S']),
         ['v1.3:21', 'v1.3:166', 'v1.4:13'])
    safety_context = {'paragraph_context': [{'text': '本段对象为药物毒性研究资料的准备。'}]}
    pair(4, '安全主题下当前资料要求与沟通形式分开',
         member('申请人应提交毒性研究结果和相应风险控制方案。', ['S'], safety_context),
         member('申请人可预约电话沟通个别问题，联系方式将在下次修订时更新。', contexts=safety_context),
         ['v1.3:21', 'v1.3:65', 'v1.3:67', 'v1.4:7', 'v1.4:9'])
    condition = '本期该药治疗费用的增幅不超过约定上限。'
    pair(5, '相同费用子条件只承接直接控制它的保障结果',
         member(condition, ['Ec', 'F'], {'verified_parent_context': [{'text': '本节面向既有药物保障协议；安全性和疗效资料已在别处评估。满足以下条件可续签，原药物保障协议延续一年。'}]}, fairness=['access']),
         member(condition, ['Ec'], {'verified_parent_context': [{'text': '本节面向既有药物保障协议；安全性和疗效资料已在别处评估。满足以下条件可递交续约申请，是否续签另行决定。'}]}),
         ['v1.3:17', 'v1.3:35', 'v1.4:7', 'v1.4:21', 'v1.4:22'])
    following = {'following_context': [{'text': '药物毒性分析；临床疗效数据；药费预算；原制剂改良信息；公平性信息。'}]}
    pair(6, '明确当前资料清单与今后另行发布的文件规划不混同',
         member('本次申报必须提交以下五项内容：', DIMS, following, fairness=['dimension_information'], innovation=['attribute']),
         member('本说明用于统一文件版式；今后将另行发布各专题文件。', contexts=following),
         ['v1.3:17', 'v1.3:65', 'v1.3:67', 'v1.3:146', 'v1.3:148', 'v1.4:7'])
    pair(7, '价格协商事务与价格取值计算分开',
         member('委员会组织企业参加药品价格协商，并安排会场顺序。'),
         member('委员会以该药的实际采购价格计算基金支付上限。', ['Ec']),
         ['v1.3:35', 'v1.3:37', 'v1.4:24'])
    pair(8, '拟申请手续与当前拟定的具体药物覆盖分开',
         member('企业拟申请将该药纳入保障范围的，应先预约受理时段。'),
         member('本方案拟将该药纳入本年度药物保障范围。', ['F'], fairness=['access']),
         ['v1.3:11', 'v1.4:21', 'v1.4:22'])
    pair(9, '试验治疗获取缺口与一般研究药分配分开',
         member('对目前缺少可获得治疗的患者，本项目安排提供研究药物治疗。', ['F'], fairness=['access']),
         member('对本项目已入组的受试者，按随机分组安排提供研究药物。'),
         ['v1.3:55', 'v1.3:81', 'v1.3:83', 'v1.4:23', 'v1.4:26'])
    innovation_context = {'verified_parent_context': [{'text': '本项服务对象为开展原创药物研发的团队。'}]}
    pair(10, '明确创新对象下技术指导与材料排版服务分开',
         member('服务专员对研发方案中疗效终点的科学选择提出技术建议。', ['E', 'I'], innovation_context, innovation=['research_support']),
         member('服务专员说明申报资料的排版格式和文件编号。', contexts=innovation_context),
         ['v1.3:29', 'v1.3:31', 'v1.3:166', 'v1.4:13', 'v1.4:17'])
    pair(11, '研究方法须有当前明确效果证据用途',
         member('该研究用于比较药物降低疾病复发的效果，应报告预设终点结果。', ['E']),
         member('该研究应按预先登记的访视日期完成记录。'),
         ['v1.3:29', 'v1.3:31', 'v1.3:65', 'v1.3:67'])
    pair(12, '覆盖和保险费用责任不自动带出患者可负担子类',
         member('本方案将该药纳入保障范围，药费由保险机构承担。', ['Ec', 'F'], fairness=['access']),
         member('本方案将该药纳入保障范围；因患者难以负担自付药费，减免其个人药费。', ['Ec', 'F'], fairness=['access', 'affordability']),
         ['v1.3:35', 'v1.3:53', 'v1.3:57', 'v1.3:156'])
    new = [m for p in pairs for m in p['members']]
    assert len(new) == len({m['input']['id'] for m in new}) == 24
    dump(HERE / 'synthetic24_pairs_PRIVATE_PROPOSED.json', {'status': 'PROPOSED_EXPECTATIONS_REQUIRE_INDEPENDENT_REVIEW', 'pairs': pairs})
    (HERE / 'synthetic24_new_inputs_PROPOSED.jsonl').write_text(''.join(json.dumps(m['input'], ensure_ascii=False)+'\n' for m in new))
    inherited = read(HERE / 'synthetic106_expected_INHERITED_PRIVATE.json')['tests']
    dump(HERE / 'synthetic130_expected_PRIVATE_PROPOSED.json', {'status': 'DESIGN_ONLY_NOT_MODEL_TESTED',
        'inherited106_expectations_unmodified': True, 'new_pair_n': 12,
        'inherited_review_disputes_not_forced': ['C03-CONTROL-003 F', 'C05-NEW-012 Ec', 'C05-NEW-019 I'],
        'tests': inherited + new})
    assert len(inherited) == 106
    assert len({x['input']['id'] for x in inherited+new}) == 130

    prior_gates = read(OLD / 'predeclared_acceptance_PROPOSED.json')
    final07 = read(OLD / 'semantic-review/candidate07_final_semantic_gate_report_PRIVATE.json')
    checks = {}
    def check(ident, dimension, value, basis, subtype=None):
        key = (ident, dimension)
        if key in checks:
            assert checks[key]['working_judgment_not_gold'] == value
            checks[key]['basis_sources'].append(basis)
            if subtype: checks[key]['expected_innovation_subtype'] = subtype
            return
        checks[key] = {'id': ident, 'dimension': dimension, 'working_judgment_not_gold': value,
                       'basis_sources': [basis], 'all_five_dimensions_review_even_if_unchanged': True}
        if subtype: checks[key]['expected_innovation_subtype'] = subtype
    for key in ['eight_clear06_error_cells_WORKING_NOT_GOLD', 'nine_fixed06_working_cells_to_preserve']:
        for rec in prior_gates[key]:
            check(rec['id'], rec['dimension'], rec['reviewer_manual_judgment_not_gold'], rec.get('reason', key))
    for rec in prior_gates['additional_independently_identified_known_items_NOT_GOLD']:
        check(rec['id'], rec['target_dimension'], rec['working_judgment_not_gold'], rec['basis'], rec['expected_innovation_subtype'])
    for rec in final07['clear_development_manual_conflicts']:
        value = rec['audit_annotation']['reviewer_working_judgment_not_gold']
        check(rec['id'], rec['dimension'], value, '07最终封存明确错误（非参照标签）', 'attribute' if rec['id'] in ['RECODE25-01955','RECODE25-02764','RECODE25-03876'] else None)
    for ident in ['RECODE25-02830', 'RECODE25-02845']:
        check(ident, 'S', 1, '已确认安全义务须保留S；不从I排除删除S')
        check(ident, 'I', 0, '已确认申请人安全义务不等于向其提供创新研发支持')
    boundaries = [{'id': r['id'], 'dimension': r['dimension'], 'status': 'INHERITED_BOUNDARY_NOT_FORCED'} for r in final07['development_boundaries_NOT_FORCED']]
    mandatory_ids = sorted({r['id'] for r in checks.values()} | {r['id'] for r in boundaries})
    six = ['RECODE25-01955','RECODE25-02764','RECODE25-03876','RECODE25-02830','RECODE25-02845','RECODE25-01562']
    gates = {'status': 'PREDECLARED_PROPOSED_REQUIRES_ROOT_AND_INDEPENDENT_REVIEW',
        'current_six_known_items': six, 'required_working_cells_NOT_GOLD': list(checks.values()),
        'boundary_cells_NOT_FORCED': boundaries, 'mandatory_review_ids': mandatory_ids,
        'technical': ['固定17逻辑，最多51同请求技术尝试；唯一完成agent_message与raw完整JSON类型保留相等，首个技术有效，无语义重试。',
                      '同240及继承62/24/20原字节、顺序和25条批次保留；输入只含原材料，不含预期或历史输出。'],
        'semantic_fixed_gate': ['全部已确认六例的目标维正确；28条以前已知/新增明确工作检查（实际数量以required_working_cells为准）均正确，理由/证据/子类不违背手册。',
            '全部已运行240与146合成控制逐条审五维、理由、证据、子类和质量依据；不得只看变化或标签。独立16期望对提示作者保持隔离，由独立检查者审读。所有历史候选只作差异诊断，不作多数真值。未运行部分明确NOT_RUN。',
            '07四个预声明失败及其余明确回归全部解决，旧06九已修项保留；其他单元无确认的新误报或漏判。',
            '新24控制全部五维及字段成立；继承106期望逐字保留，原始匹配门禁单独完整报告，不重写旧期望。C05-NEW-015一般未来文件传播须全五维修复。',
            '003F/012Ec/019I旧控制争议与真实边界保留，不强迫答案；旧机械期望不符仍照实记FAIL，不以解释抹去。语义门禁与机械旧期望门禁分别列出，任何确定错误/回归导致总体FAIL，未决争议不得称无保留验证通过。',
            '所有审读投影使用现有redactor，当前267先排除；遮蔽影响实质判断时记录条件性/未决，不把看不到的上下文称已逐句审完。'],
        'execution_and_release_limits': ['本轮只准备；root及独立检查通过后才另行冻结/授权一次预定范围的有界开发运行。',
            '固定阶段顺序：作者新24与独立16先跑，完整技术/语义无确定失败才进入继承106，再无确定失败才进入原240；未跑阶段记录NOT_RUN，不能称完整240改进。每阶段提示和期望均已事先冻结，不按结果改提示或选择成功标签。',
            '不读A/B分数调参，不改A/B，不按κ/F1选提示或输出，不拼接03/05/06/07/08。',
            '原4924只绑定，不在本开发wrapper授权范围。全量、采纳、统计或正文同步均需另行决定。',
            '开发重测不称独立确认；已暴露240及共享上下文接触限制保留。不承诺κ达到0.8，不把一次前后差异归因为唯一提示因果。'],
        'model_calls': 0}
    gates['semantic_fixed_gate'][0] = gates['semantic_fixed_gate'][0].replace('28条', f'{len(checks)}条')
    dump(HERE / 'predeclared_acceptance_PROPOSED.json', gates)

    plan = {'status': 'DESIGN_ONLY_NO_MODEL_AUTHORIZATION', 'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'runs': []}
    scopes = [('new24', 24, 'synthetic24_new_inputs_PROPOSED.jsonl', 1),
              ('independent16', 16, str(HERE.parent/'候选08-独立检查/independent_synthetic16_inputs_ONLY_PRIVATE_PREDECLARED.json'), 1),
              ('inherited62', 62, 'synthetic62_inputs_UNCHANGED.jsonl', 1),
              ('inherited24', 24, 'synthetic24_inputs_UNCHANGED.jsonl', 1),
              ('inherited20', 20, 'synthetic20_inputs_PROPOSED.jsonl', 1),
              ('exposed240', 240, 'exposed240_inputs_UNCHANGED.jsonl', 3)]
    for key, n, src, workers in scopes:
        source = HERE/src
        if key == 'independent16':
            assert sha(source) == '9b19ec94b519c58088b0e1567f887a08aa425d2d9ed8ab63cbc2cdf0233a5643'
        name = f'{key}-candidate08-first-run'
        command = [PYTHON, str(runtime/'run_production_v32.py'), '--input', str(HERE/src),
            '--expected-input-sha256', sha(HERE/src), '--prompt', str(HERE/'candidate08_prompt_PROPOSED.txt'),
            '--expected-n', str(n), '--run-name', name, '--batch-size', '25', '--workers', str(workers),
            '--max-attempts', '3', '--purpose', 'One whole candidate08 development scope; first technical valid response; no semantic retries, score selection, splicing, full-corpus run or adoption.']
        plan['runs'].append({'run_key': key, 'run_name': name, 'input_binding': binding(source),
            'n': n, 'logical_requests': (n+24)//25, 'workers': workers,
            'future_execution_command_after_separate_root_authorization_only': command})
    plan.update({'scope_run_keys': [x[0] for x in scopes], 'scope_sizes': [x[1] for x in scopes],
        'nominal_logical_requests': 17, 'maximum_identical_technical_attempts': 51,
        'synthetic_total': 146, 'author_or_inherited_synthetic_total': 130,
        'independent16_content_not_read_by_prompt_author': True,
        'model_calls_by_preparation': 0, 'actual_CLI_invocations_by_preparation': 0,
        'phases': [{'phase':'new-controls','run_keys':['new24','independent16'],'logical_requests':2},
                   {'phase':'inherited-controls','run_keys':['inherited62','inherited24','inherited20'],'logical_requests':5,'requires_previous_phase_semantic_gate':'new-controls'},
                   {'phase':'exposed240','run_keys':['exposed240'],'logical_requests':10,'requires_previous_phase_semantic_gate':'inherited-controls'}],
        'stop_rule':'Confirmed semantic failure stops later phases; unused requests remain NOT_RUN. No semantic retry, prompt replacement or label splicing.',
        'full4924_material_binding_only_not_execution_authorized': binding(ROOT/'outputs/coding-revision-20261007-r3/effective_blind_inputs_v14.jsonl'),
        'original_240_and_inherited106_unchanged': True, 'full_corpus_or_adoption': False,
        'same_n24_runs_distinguished_by_run_key_not_numeric_size': True})
    dump(HERE / 'candidate08_execution_plan_PROPOSED.json', plan)

    redactor_path = ROOT/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py'
    spec = importlib.util.spec_from_file_location('candidate08_safe_redactor', redactor_path)
    rm = importlib.util.module_from_spec(spec); spec.loader.exec_module(rm)
    redactor = rm.ReservedContextRedactor()
    rows = read(OLD/'execution-audit/candidate07_all240_comparison_REDACTED_PRIVATE.json')['rows']
    original240 = [json.loads(line) for line in (HERE/'exposed240_inputs_UNCHANGED.jsonl').read_text().splitlines() if line.strip()]
    assert not any(redactor.is_reserved(x['id']) for x in original240)
    assert set(mandatory_ids) <= {x['id'] for x in original240}
    projection = {'status': 'KNOWN_EXPOSED_DEVELOPMENT_ONLY_NOT_PROMPT_INPUT',
        'rows': [{'id': x['id'], 'input': x['input'], 'historical_intact_rows': x['historical_intact_rows'],
                  'candidate07_intact_actual_row': x['candidate07_intact_actual_row'],
                  'required_working_cells_NOT_GOLD': [c for c in checks.values() if c['id']==x['id']]} for x in rows if x['id'] in six]}
    clean, hits = redactor.redact_object(projection)
    assert redactor.audit_object_no_full_match(clean)['no_remaining_full_normalized_reserved_unit_match']
    dump(HERE/'confirmed_six_DEVELOPMENT_REDACTED_PRIVATE.json', clean)
    dump(HERE/'preparation_redaction_metadata.json', {'new_original_model_input_change': False,
        'redactor': binding(redactor_path), 'known_six_current_ids_outside_reserved267': True,
        'hits_ID_and_field_path_only': [{'reserved_unit_id': h['reserved_unit_id'], 'field_path': h['locator']} for h in hits],
        'already_redacted_source_used': binding(OLD/'execution-audit/candidate07_all240_comparison_REDACTED_PRIVATE.json'),
        'projection_sha256': sha(HERE/'confirmed_six_DEVELOPMENT_REDACTED_PRIVATE.json'),
        'no_remaining_full_normalized_reserved_match': True,
        'partial_extracts_or_paraphrases_not_guaranteed_detected': True})
    lengths = []
    for name, p in [('03-base-development', OLD03/'candidate03_prompt.txt'),
                    ('03-full-corpus-request-prompt', OLD03/'full-corpus-candidate03-material-v14-development/frozen_prompt.txt'),
                    ('07-frozen', OLD/'candidate07_prompt_PROPOSED.txt'), ('08-proposed', HERE/'candidate08_prompt_PROPOSED.txt')]:
        data=p.read_bytes(); pos=data.find(MARKER)
        lengths.append({'name':name,**binding(p),'characters':len(data.decode()),'execution_prefix_bytes':pos,
                        'execution_prefix_characters':len(data[:pos].decode()) if pos>=0 else None})
    quotes=[]
    anchors=[('v1.3','完整五维手册-v1.3.md',[11,17,21,29,31,35,37,43,53,65,67,121,136,142,146,148,152,156,166]),
             ('v1.4','共用操作说明-v1.4.md',[7,9,13,14,15,16,17,21,22,23,24,25,26,30])]
    for version, name, lines in anchors:
        path=PROTOCOL/name;text=path.read_text().splitlines()
        quotes.append({'version':version,**binding(path),'quotes':[{'line':line,'quote':text[line-1]} for line in lines]})
    dump(HERE/'manual_rule_basis_UNCHANGED.json', {'definitions_unchanged': True,'sources':quotes})
    dump(HERE/'prompt_change_map.json', {'status':'PROPOSED_EXECUTION_LAYER_ONLY', 'definitions_changed':False,
        'schema_validator_runner_changed':False,'suffix_byte_identical_to_07':True,
        'suffix_sha256':hashlib.sha256(suffix).hexdigest(), 'manual_scope':'完整v1.3+v1.4实质操作部分，继承原byte；v1.4末尾版本纪律未入提示，不声称全文。',
        'length_measurement':'字节和Unicode字符为机械实际值，不冒充模型token计数；不调用模型分词器。',
        'prompt_lengths':lengths,
        'change_flow':['完整单元的各个对象/谓词/属性或条件','仅补足必要的直接控制/援引/引导关系','按不变五维定义分别纳入与排除','逐维核短理由、unit/context引文及独立子类','材料缺口与固定JSON结构'],
        'changes':[{'mechanism':'用于申报对象界定的属性改变被程序排除','manual_basis':['v1.3:11','v1.3:142','v1.4:14'],'execution_change':'先保留整句每个成分，再判断用途；当前明确变化不因管理用途消失。'},
                   {'mechanism':'安全义务被当创新支持或安全指导被全删','manual_basis':['v1.3:21','v1.3:166','v1.4:13'],'execution_change':'区分申请人承担义务与向创新团队提供支持；S/E与I独立共存。'},
                   {'mechanism':'父条件保障延续漏读/全部维度继承','manual_basis':['v1.3:17','v1.4:7','v1.4:21','v1.4:22'],'execution_change':'说明子条件直接导致何种结果，仅用所控制结果，不复制其他父条件。'},
                   {'mechanism':'未来文件清单与同主题后项被自动传播','manual_basis':['v1.3:17','v1.3:146','v1.3:148','v1.4:7'],'execution_change':'明确区分当前引导/援引的实质清单与另行发布的文件规划。'},
                   {'mechanism':'经济程序和研究参与被当实质经济/保障','manual_basis':['v1.3:35','v1.3:37','v1.4:23','v1.4:26'],'execution_change':'同一对象/谓词顺序检查，实际费用或治疗缺口须在当前成立。'}],
        'no_real_unit_ids_or_actual_answer_templates_in_prompt':True,
        'no_claim_of_causal_mechanism_proof_or_paper_validated_new_method':True})
    qa = {'status':'STRUCTURAL_PREPARATION_ONLY_INDEPENDENT_SEMANTIC_PREFLIGHT_PENDING',
        'manual_suffix_bytes_identical':True,'complete_v13_bytes_contained':True,'v14_substantive_bytes_contained':True,
        'old240_and_inherited106_bytes_preserved':True,'inherited_expectation_records_unchanged':True,
        'runner_validator_schema_bytes_preserved':True,'new_pairs':12,'new_controls':24,
        'author_and_inherited_synthetic_total':130,'independent_control_metadata_only_n':16,
        'synthetic_total':146,'required_working_cells':len(checks),'mandatory_review_current_units':len(mandatory_ids),
        'no_reserved_current_unit_in240':True,'new_review_projection_full_match_clear':True,
        'prompt_has_no_real_ids_or_scores':True,'logical_requests':17,'maximum_technical_attempts':51,
        'model_calls':0,'real_CLI_invocations':0,'no_A_B_read_for_tuning':True}
    dump(HERE/'design_structural_QA.json',qa)
    for p in HERE.rglob('*.py'):ast.parse(p.read_text())
    print(json.dumps(qa,ensure_ascii=False))


if __name__ == '__main__':
    main()
