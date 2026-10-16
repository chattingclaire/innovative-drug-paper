"""Freeze one bounded candidate05 development plan. Never invokes a model.

Only previously exposed development240 and synthetic controls enter the plan.
No human-reserved text, prediction or label is consulted. No source is changed.
"""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PRIOR = PROJECT / 'outputs/coding-revision-20261007-r3/llm-candidate03-development'
EXCLUSION = PROJECT / 'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json'
EXCLUSION_SHA = 'a3ea2e0aaabbf9d00fafb4f3511b3a8910b182111d1cff803c0bb5f03040d135'
DIMS = ['S', 'E', 'Ec', 'I', 'F']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def binding(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def save_new(path, data):
    content = data if isinstance(data, bytes) else data.encode()
    if path.exists():
        assert path.read_bytes() == content, f'Frozen file differs: {path}'
    else:
        path.write_bytes(content)


def dump_new(path, obj):
    save_new(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


ADDITION = '''
## 候选05：把当前行为与语境作用写清楚

以下是执行与理由留痕要求，沿用完整v1.3/v1.4的五维定义、纳入和排除边界，不增加或缩窄构念。仍须同次完整阅读、独立判断全部五维；不是只重判I/F，也不能用脚本改标签。

I和F的理由应当用针对本条的普通语言，简短说明当前谁对谁做了什么；需要语境时说明它补足什么。不要只把“具体指导”“实质支持”“实际保障”等结论换一种说法。理由中无需增加字段、编号或固定模板，证据结构完全沿用既定格式。

对I，先说明当前讨论的是哪条依据：具体原创或改良/相对既有产品的变化、创新信息或资格、专有试验数据权利，还是创新研发支持。若以研发支持为依据，写清当前由谁向什么创新研发对象提供何种人员、资源、优先便利、技术指导、支持资格或其他实质措施。申请人承担监测、风险控制、报告、材料准备等义务，本身不因为指南对此提出要求就成为指南向申请人提供了研发支持；这些义务可能明确属于S/E等，须保留。也不能把“由申请人实施”当作一律排除I的规则：当前明确规定其研发支持权益、资源或实质资格，或独立讨论产品变化/专有权利，仍按相应内容纳入。创新对象可由真实适用范围补足，但范围只补对象，不替代当前支持措施。明确相对既有产品的具体改变，无须再同时写出“创新”“改良”、优效结果或新靶点。

对F，先说明当前命题讨论何种药物保障、获取、患者负担、使用管理难度或相应信息要求。当前单元是子项/条件时，找出真正控制本项的给定父谓词，用普通语言说明“本条件决定何种结果”：该结果若是药物实际给付、供应、保障的持续/退出或具体适用条件，可组成同一F命题；不能因为本项只写预算、比例或期限而遗漏真实控制结果。条件所决定的若只是材料处理、申请或管理转类，就不能把既有给付范围/保障期限变成本句的新保障内容。条件性、拟定、负向退出和制度部署本身不排除F，也不要求已经对个别患者实施。

语境的作用只按当前真实关系说明：它可能消解对象或指代、补足直接控制本子项的省略谓词，或说明当前证据的明确用途。相邻后句罗列了评价维度，并不说明当前抽象定义句已经逐项要求那些内容；真正由当前引导句控制的列表则应按其真实内容判断。不要为补足一项F/I而把同一语境中的其他维度一并传播，也不要忽略同句独立成立的其他维度。

填写I/F理由后，对照本条的引文检查理由是否只是用背景说明“通常有助于研发/保障”，还是指出了当前成立的属性、措施、条件、结果或内容要求。存在完整材料下的解释边界时保留自己的判断并写boundary_note；不因预计分布、部门或其他方法答案而修改。其余理由、逐字引文、子类型、材料门禁和最终JSON要求全部保持。

'''


def main():
    assert sha(EXCLUSION) == EXCLUSION_SHA
    excluded = set(json.loads(EXCLUSION.read_text())['all_registered_members_of_reserved_families_unit_ids'])
    assert len(excluded) == 267
    source240 = PRIOR / 'exposed240_inputs.jsonl'
    # Mechanical ID check only. Input is copied byte-for-byte after zero overlap.
    rows240 = [json.loads(s) for s in source240.read_text().splitlines() if s.strip()]
    ids240 = [r['id'] for r in rows240]
    assert len(ids240) == len(set(ids240)) == 240
    assert not excluded.intersection(ids240)
    assert sha(source240) == '4fb4dbaf39e47de5b6ff6773ace5e9e6cec98356c6538401c076845d22c31960'
    old30 = json.loads((PRIOR / 'synthetic30_expected_PRIVATE.json').read_text())['tests']
    old38 = json.loads((PRIOR / 'synthetic38_candidate04_expected_PRIVATE.json').read_text())['tests']
    assert old30 == old38[:30] and len(old38) == 38

    tests = []
    for test in old38:
        tests.append({**test, 'control_origin': 'inherited_candidate03_30' if len(tests) < 30 else 'inherited_candidate04_extra8'})

    def add(text, positives, rationale, contexts=None, pair=None):
        rid = f'C05-NEW-{len(tests) - 37:03d}'
        tests.append({'input': {'id': rid, 'text': text, 'contexts': contexts or {}},
                      'labels': {d: int(d in positives) for d in DIMS},
                      'rationale': rationale, 'control_origin': 'new_candidate05_24',
                      'pair': pair})

    add('申请人应持续收集试验药物的不良反应信息，采取风险控制措施保护受试者。', ['S'],
        '申请人安全义务保留S；创新研发适用对象不把该义务变成实体支持。',
        {'verified_parent_context': [{'text': '本节适用于创新药研发。'}]}, 'agency_safety')
    add('监管机构为创新药研发配备专门专家，向申请人提供试验药物风险控制方案的技术辅导。', ['S', 'I'],
        '安全主题与机构实际配置人员、向创新研发提供技术指导同时成立。', pair='agency_safety')
    add('创新药研发项目申请人应在每季度结束时报告研究进度。', [],
        '已有创新项目对象和报告义务本身不是当前实体支持。', pair='support_entitlement')
    add('经核定达到本项目条件的创新药研发申请人，可获得专门研发设备的优先使用权。', ['I'],
        '当前规定取得具体研发资源权益的实质资格，不因申请人是受规制对象而排除。', pair='support_entitlement')
    add('为支持创新药研发，现发布本项研究资料提交指南。', [],
        '发布宗旨不替代当前实体创新支持。', pair='publication_vs_guidance')
    add('创新药研发期间，审评机构根据已提交的试验资料安排专业人员对下一阶段研究设计提出技术建议。', ['I'],
        '实际人员安排和研究设计指导属于实体支持，无须已经完成辅导。', pair='publication_vs_guidance')
    add('机构为本节所述药物提供专门的研究方案咨询。', ['I'],
        '真实适用范围补足创新对象，当前咨询措施独立成立。',
        {'verified_parent_context': [{'text': '本节所述药物是具有原创属性的新药。'}]}, 'object_scope')
    add('机构为本节所述药物提供专门的研究方案咨询。', [],
        '当前一般药物研究措施不能继承相邻后句才引入的创新项目对象。',
        {'verified_parent_context': [{'text': '本节所述药物包括各种普通药品。'}],
         'structured_following_units': [{'text': '下一节另行规定原创药物项目。'}]}, 'object_scope')
    add('本药下一周期的基金支出预算增幅不超过规定上限。', ['Ec', 'F'],
        '费用条件被真实药物保障延续父谓词直接控制。',
        {'verified_parent_context': [{'text': '满足下列条件的药物保障协议可继续生效两年，期间基金继续支付约定药费。'}]}, 'parent_result')
    add('本药下一周期的基金支出预算增幅不超过规定上限。', ['Ec'],
        '相同费用文字仅控制材料办理排序，不决定药物保障。',
        {'verified_parent_context': [{'text': '按下列条件安排申报材料的办理顺序，排序不决定给付或供应。'}]}, 'parent_result')
    add('已经履行两年药物保障协议的品种，按规定转入另一管理类别。', [],
        '既有保障期限只是当前管理转类的前提，不传播为新保障命题。', pair='prior_vs_current_duration')
    add('本药现有保障协议自本期到期之日起继续生效两年，原约定的给付条件在此期间适用。', ['F'],
        '当前直接规定保障持续及其期限。', pair='prior_vs_current_duration')
    add('需要增加药物支付范围的申请人，应先提交书面申请。', [],
        '申请动作没有实质确定新给付范围。', pair='application_vs_scope')
    add('经审定新增的治疗适应证纳入本药保障范围，基金自协议生效日起按该范围承担药费。', ['Ec', 'F'],
        '当前同时确定实际保障范围和药费承担。', pair='application_vs_scope')
    add('综合评价是运用多方面证据进行系统分析的过程。', [],
        '当前抽象定义没有继承相邻后句列出的各维内容。',
        {'structured_following_units': [{'text': '评价项目另列药物安全性、治疗效果、药费、原创属性与患者可负担性。'}]}, 'definition_vs_list')
    add('本次综合评价应包括下列药物内容。', ['S', 'E', 'Ec', 'I', 'F'],
        '当前引导句真实控制随后明确列出的评价内容，应分别保留五维。',
        {'structured_following_units': [{'text': '药物安全性、治疗效果、药费、原创属性与患者可负担性。'}]}, 'definition_vs_list')
    add('本药存在常规剂量调整的需求。', [],
        '一般剂量调整需求不自行推定损害、治疗推荐或临床管理复杂性。', pair='management_difficulty')
    add('评价使用本药每周采血监测的管理负担，以及基层能否完成这些必要监测。', ['F'],
        '当前直接评价药物使用监测的管理负担，不需自行补入未写出的毒性。', pair='management_difficulty')
    add('本次申请的注射剂仅使用新的申报编号，产品组成和剂型均未改变。', [],
        '新申报编号不等于产品创新。', pair='specific_product_change')
    add('本药由小容量注射液变为注射用无菌粉末制剂，申报相应剂型改变。', ['I'],
        '相对既有产品的具体剂型变化成立，不额外要求创新词或优效结果。', pair='specific_product_change')
    add('申请人应把药物试验数据按规定格式存档，未经许可不得擅自公开档案。', [],
        '一般存档及保密义务不等于专有试验数据保护权利。', pair='exclusive_data_right')
    add('对申请人自行取得且未公开的药物试验数据，授予六年的专有保护期，期间不接受他人依赖该数据提出的上市申请。', ['I'],
        '当前规定专有试验数据权利范围和期限。', pair='exclusive_data_right')
    add('病情严重且临床急需的患者希望尽早使用本药。', [],
        '严重、急需及尽早使用本身不证明治疗获取缺口或药物效果。', pair='unmet_access')
    add('对尚无可获得治疗药物的患者，由指定机构提供本药并持续保障供应。', ['F'],
        '明确治疗获取缺口及对应药物供应安排。', pair='unmet_access')
    assert len(tests) == 62
    assert not excluded.intersection(t['input']['id'] for t in tests)
    # Fixed order generated from IDs only; labels never determine order or batch.
    ordered = sorted(tests, key=lambda t: hashlib.sha256(('candidate05-controls-order-v1:' + t['input']['id']).encode()).hexdigest())
    input_path = HERE / 'exposed240_inputs_frozen.jsonl'
    controls_path = HERE / 'synthetic62_inputs_frozen.jsonl'
    expected_path = HERE / 'synthetic62_expected_PRIVATE_frozen.json'
    prompt_path = HERE / 'candidate05_prompt_frozen.txt'
    save_new(input_path, source240.read_bytes())
    save_new(controls_path, ''.join(json.dumps(t['input'], ensure_ascii=False) + '\n' for t in ordered))
    dump_new(expected_path, {'status': 'predeclared_before_candidate05_calls', 'independent_validation': False,
                             'inherited_unique_controls': 38, 'inherited30_exact_subset_of38': True,
                             'new_controls': 24, 'tests': tests})
    base_prompt = PRIOR / 'candidate03_prompt.txt'
    assert sha(base_prompt) == '8576d9a1be10b0dd7b69b4c12367f4c357f55abf4ca30d979d5b333493089ba4'
    prompt = base_prompt.read_text().replace('全五维LLM语义执行说明 v32 候选03-development',
                                           '全五维LLM语义执行说明 v32 候选05-development', 1)
    assert prompt.count('--- 冻结的完整手册（原样） ---') == 1
    prompt = prompt.replace('--- 冻结的完整手册（原样） ---', ADDITION + '\n--- 冻结的完整手册（原样） ---')
    assert '候选04：保障期限' not in prompt
    assert 'RECODE25-' not in prompt and 'C05-NEW-' not in prompt and '0.80' not in prompt
    for path in [PROJECT / 'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md',
                 PROJECT / 'outputs/coding-revision-20261007-r3/llm-v32/共用实质操作说明-v1.4-运行摘录.txt']:
        assert path.read_text().strip() in prompt
    save_new(prompt_path, prompt)
    runtime = HERE / 'runtime'
    runtime.mkdir(exist_ok=True)
    runtime_bindings = {}
    for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
        save_new(runtime / name, (PRIOR / name).read_bytes())
        assert sha(runtime / name) == sha(PRIOR / name)
        runtime_bindings[name] = binding(runtime / name)
    freeze = {
        'status': 'PREPARED_FROZEN_NO_MODEL_CALLS_ROOT_EXECUTION_DECISION_PENDING',
        'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'method_id': 'LLM-v32-candidate05-bounded-development', 'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium',
        'format_family': 'LLM-binary-v32; original schema/validator unchanged',
        'base': binding(base_prompt), 'candidate05_prompt': binding(prompt_path),
        'exposed240_input': binding(input_path), 'synthetic62_input': binding(controls_path),
        'synthetic_expected_private': binding(expected_path), 'runtime': runtime_bindings,
        'human_reserved_exclusion_metadata': binding(EXCLUSION),
        'human_reserved_registered_members': 267, 'old240_reserved_intersection_count': 0,
        'current_scope': 'Complete exposed240 plus all38 unique inherited synthetic controls and24 new symmetric controls.',
        'new_semantic_constructs': False, 'new_schema_fields': False, 'material_or_unit_edits': False,
        'novel_execution_hypothesis': 'Require I/F reasons to state the current actor/action/recipient and the actual result controlled by a parent condition, rather than adding further case rules.',
        'safe_improvement_proven': False, 'independent_validation_claimed': False,
        'cross_request_variation_known': ['02845 was I0 in candidate03 exposed240 and candidate04 exposed240, but I1 in the current full-corpus candidate03; its full input object and complete candidate03 prompt are equal across old03/current03, but the complete requests and execution occasions differ. No single cause is isolated.'],
        'planned_runs': [
            {'name': 'exposed240-candidate05-first-run', 'input': str(input_path), 'n': 240, 'batch_size': 25, 'logical_batches': 10, 'workers': 3},
            {'name': 'synthetic62-candidate05-first-run', 'input': str(controls_path), 'n': 62, 'batch_size': 25, 'logical_batches': 3, 'workers': 1}],
        'nominal_model_calls': 13, 'max_identical_technical_attempts_per_batch': 3, 'technical_maximum_calls': 39,
        'selection': 'first chronological technically valid attempt; preserve all attempts; never semantic/label/reference/metric selection',
        'retry': 'identical input+prompt only after technical execution/schema/literal/tool-event failure; never retry semantic errors',
        'release_limit': 'This bounded development run cannot replace production labels or update a manuscript. No full-corpus run is included.',
        'decision_basis': 'Review all changed dimensions, every confirmed regression and both sides of every control pair under v1.3/v1.4. No kappa threshold or target distribution.',
        'root_confirmation_before_actual_calls': True,
        'future_independent_confirmation': [
            'Review frozen prompt and all control expectations without reference labels before root executes.',
            'After calls, audit every source/request/raw-output/final-event binding and first-valid selection.',
            'Review all changed five-dimension decisions in exposed240, not only I/F or the known errors; preserve ambiguous cases.',
            'If semantic results justify continuation, separately freeze a stability check that repeats unchanged candidate05 requests and perturbs batch context without selecting favorable repeats.',
            'Only a separately registered source-family-excluded independent validation can support generalization; do not inspect current human-reserved text/labels for prompt development.'
        ],
        'prior_artifacts_preserved': {name: binding(PRIOR / name) for name in [
            'candidate03_prompt.txt', 'candidate04_prompt.txt', 'exposed240_inputs.jsonl',
            'synthetic30_expected_PRIVATE.json', 'synthetic38_candidate04_expected_PRIVATE.json',
            'exposed240-first-run/all_predictions.jsonl', 'exposed240-candidate04-first-run/all_predictions.jsonl',
            'candidate04_semantic_QA_PRIVATE.json']},
        'current_full_corpus_candidate03_binding_hash_only': binding(PRIOR / 'full-corpus-candidate03-material-v14-single-unit-reconciled-development/all_predictions.jsonl')
    }
    freeze_path = HERE / 'candidate05_development_freeze.json'
    if freeze_path.exists():
        old_freeze = json.loads(freeze_path.read_text())
        freeze['created_at'] = old_freeze['created_at']
    dump_new(freeze_path, freeze)
    print(json.dumps({'status': freeze['status'], 'freeze': binding(freeze_path), 'planned_calls': 13,
                      'new_controls': 24, 'total_unique_controls': 62, 'actual_model_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
