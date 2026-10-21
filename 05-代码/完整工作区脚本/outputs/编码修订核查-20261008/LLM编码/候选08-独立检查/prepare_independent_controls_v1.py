"""Prepare synthetic regressions before seeing any candidate08 output.

No model, classifier, prompt edit, original-unit inspection, or label mutation.
"""
from pathlib import Path
import datetime, hashlib, importlib.util, json

ROOT = Path('/PROJECT_ROOT')
HERE = Path(__file__).resolve().parent
DIMS = ('S', 'E', 'Ec', 'I', 'F')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def evidence(dimension, quote, source='unit'):
    return {'dimension': dimension, 'source': source, 'quote': quote}


def control(num, pair, polarity, text, context, labels, reasons, quotes,
            mechanism, anchors, I=(), F=()):
    labels = dict(zip(DIMS, labels))
    assert set(reasons) == set(DIMS)
    return {
        'id': f'C08-U{num:03d}', 'pair_id': pair, 'mechanism_polarity': polarity,
        'input': {
            'id': f'C08-U{num:03d}', 'text': text,
            'source_title': '合成政策片段', 'pages': [1],
            'contexts': {
                'paragraph_context': [],
                'verified_parent_context': ([{'paragraph_id': 'synthetic-parent',
                    'text': context, 'pages': [1],
                    'usage': '仅消解适用对象、控制谓词及列项关系，不复制其他维度。'}]
                    if context else []),
                'structured_following_units': []
            },
            'context_usage': '仅消解对象、指代、条件、列项或明确承接；不从背景复制标签。'
        },
        'expected': {
            'labels': labels, 'dimension_reasons': reasons,
            'evidence': quotes, 'innovation_subtypes': list(I),
            'fairness_subtypes': list(F), 'safety_quality_basis': 'no_quality_basis'
        },
        'mechanism_explanation': mechanism,
        'manual_anchors': anchors,
        'not_a_real_policy_quote': True,
        'same_as_adopted_machine_or_human_label_used_as_truth': False
    }


def ordinary(**updates):
    result = {
        'S': '无药物损害、药物风险或明确药品质量安全内容。',
        'E': '无药物治疗效果、临床获益或其证据内容。',
        'Ec': '无药品价格、药费、支付标准、费用责任或经济效果内容。',
        'I': '无原创改良、具体属性变化、创新资格或实体创新研发支持。',
        'F': '无实际药物给付/配备/供应、治疗获取、患者可负担或药物管理难度内容。'
    }
    result.update(updates)
    return result


def build():
    rows = []
    add = lambda *a, **k: rows.append(control(*a, **k))
    attr = '原批准适应症仅限成人；本次经批准扩展为六岁及以上儿童。'
    add(1, 'P01-attribute-change', 'positive', attr, '', (0, 0, 0, 1, 0),
        ordinary(I='明确相对既有产品的适应症人群改变；无需证明优效。',
                 E='适应症扩展本身未陈述效果大小、获益或效果证据。',
                 F='适应症人群改变不自行等于实际保障范围或治疗获取缺口。'),
        [evidence('I', '原批准适应症仅限成人；本次经批准扩展为六岁及以上儿童。')],
        '实体属性变化，不以新申报身份或创新字样为必要条件。',
        ['v1.3:新品种剂型规格与属性', 'v1.4:I2'], I=['attribute'])
    add(2, 'P01-attribute-change', 'negative',
        '本次申报沿用原批准的成人适应症文字，仅将原文录入信息栏并登记提交日期。',
        '', (0, 0, 0, 0, 0),
        ordinary(I='仅复制既有适应症和登记申报资料，未陈述产品属性变化或创新属性评价。'), [],
        '适应症信息原样录入及申报身份不自动成为创新性内容；不是否定创新属性的实质评价。',
        ['v1.3:新品种剂型规格与属性', 'v1.4:I2/I4/I5'])

    safety_context = '本规范适用于创新药临床研发中的风险管理记录。'
    safety = '申请人应按既定方案收集试验中的药物不良反应，并及时更新风险控制记录。'
    add(3, 'P02-safety-vs-support', 'negative_for_I', safety, safety_context,
        (1, 0, 0, 0, 0),
        ordinary(S='当前要求收集药物不良反应并进行风险控制，实质讨论药物安全。',
                 I='当前行为是申请人的安全操作与记录义务，背景中的创新药对象不能补成机构提供研发支持。'),
        [evidence('S', '收集试验中的药物不良反应，并及时更新风险控制记录')],
        '保留S，排除将每项创新药试验安全规范都扩大成research_support。',
        ['v1.3:S', 'v1.4:I1/I5'])
    support = '药审机构为创新药研发团队配置专职专家，逐项指导其识别试验中的药物不良反应并制定风险控制措施。'
    add(4, 'P02-safety-vs-support', 'positive_for_I', support, safety_context,
        (1, 0, 0, 1, 0),
        ordinary(S='药物不良反应识别及风险控制为明确安全内容。',
                 I='当前明确由机构配置专职专家并提供针对创新药研发的实质指导。'),
        [evidence('S', '识别试验中的药物不良反应并制定风险控制措施'),
         evidence('I', '药审机构为创新药研发团队配置专职专家，逐项指导')],
        '实体提供指导资源与申请人安全义务区分，S和I可并存。',
        ['v1.3:S/I', 'v1.4:I1'], I=['research_support'])

    budget = '因调整支付范围所致的未来两年基金支出预算增幅不超过百分之九十。'
    renewal = '现有保障协议当年到期且同时满足以下条件的药品，可以续约两年，并在协议期内按原支付范围持续保障：'
    application = '符合以下条件的申请人，可以在平台提交续约材料，受理后按工作程序安排谈判：'
    add(5, 'P03-renewal-parent-condition', 'positive', budget, renewal,
        (0, 0, 1, 0, 1),
        ordinary(Ec='当前明确药品支付范围调整导致的基金支出预算影响上限。',
                 F='给定控制谓词将当前预算条件用于两年续约并持续保障原支付范围；属于保障连续性的实质条件。'),
        [evidence('Ec', '未来两年基金支出预算增幅不超过百分之九十'),
         evidence('F', budget), evidence('F', renewal, 'context')],
        '读取父条款的实际续约谓词；不是把父段全部维度复制到子项。',
        ['v1.3:上下文边界/Ec', 'v1.4:F1/F2'], F=['access'])
    add(6, 'P03-renewal-parent-condition', 'negative', budget, application,
        (0, 0, 1, 0, 0),
        ordinary(Ec='预算增幅是当前明确经济条件，仍计Ec。',
                 F='控制谓词只决定提交材料及进入谈判的资格，没有确定续约成功、保障连续性或实际给付范围。'),
        [evidence('Ec', '未来两年基金支出预算增幅不超过百分之九十')],
        '保持完全相同子句，改变给定控制谓词；申请资格和一般谈判路线不当作保障承诺。',
        ['v1.3:上下文边界/Ec', 'v1.4:F1/F2'])

    unused = '连续十二个月没有院内处方使用记录的药品。'
    withdrawal = '本院拟将符合以下条件的药品调出常规配备目录：'
    clerical = '以下药品条目的资料由甲组核对，其他条目的资料由乙组核对：'
    add(7, 'P04-supply-scope-vs-administration', 'positive', unused, withdrawal,
        (0, 0, 0, 0, 1),
        ordinary(Ec='仅为处方使用记录，不自行推定销量金额、价格或预算影响。',
                 F='给定控制谓词明确拟退出机构常规配备范围，当前是其具体条件；不要求已实施或扩大保障。'),
        [evidence('F', unused), evidence('F', withdrawal, 'context')],
        '实际药物供应范围的退出条件可以处于拟议阶段；不得以尚未实施一律判0。',
        ['v1.3:条件陈述/上下文边界', 'v1.4:F1'], F=['access'])
    add(8, 'P04-supply-scope-vs-administration', 'negative', unused, clerical,
        (0, 0, 0, 0, 0),
        ordinary(Ec='仅按既往使用记录分派资料核对，没有经济量值或经济评价。',
                 F='控制谓词仅分派核对资料的工作组，没有改变实际用药配备、供应或给付范围。'), [],
        '相同药品条件只用于行政分工；不能将药品目录整理任务当作保障内容。',
        ['v1.3:上下文边界', 'v1.4:F1/F5'])

    add(9, 'P05-price-consultation-vs-condition', 'negative',
        '有关药品价格的咨询通过预约入口办理，申请人仅登记来访人姓名和希望联系的时间。',
        '', (0, 0, 0, 0, 0),
        ordinary(Ec='当前规定咨询预约办理及联系人/时间登记，没有陈述价格水平、价格条件、经济评价或费用信息要求。'), [],
        '纯咨询通道和时间安排不等同当前实质药价条件；不能因咨询主题词自动赋Ec。',
        ['v1.3:Ec/当前内容原则'])
    add(10, 'P05-price-consultation-vs-condition', 'positive',
        '供应给医疗机构的该药每盒价格不得超过八十元，采购部门应逐月核对发票单价。',
        '', (0, 0, 1, 0, 0),
        ordinary(Ec='明确规定药品对机构的供货价格上限及价格核对。',
                 F='价格上限并未另规定持续供货、保障范围或患者可负担，不能省略价格中心词。'),
        [evidence('Ec', '供应给医疗机构的该药每盒价格不得超过八十元')],
        '实际价格约束为Ec；供货价不是独立持续供货或患者负担安排。',
        ['v1.3:Ec', 'v1.4:F4'])

    add(11, 'P06-future-file-vs-substantive-support', 'negative',
        '下季度拟编制并送审《创新药研发服务目录》，办公室负责登记文件名称、页数和送审份数。',
        '', (0, 0, 0, 0, 0),
        ordinary(I='仅拟编制含创新药研发字样的文件并办理文书记录，未规定具体支持资源、内容或资格。'), [],
        '未来文件清单/文件标题及文书任务不自动赋I。',
        ['v1.4:I1/I5'])
    add(12, 'P06-future-file-vs-substantive-support', 'positive',
        '下季度拟为创新药研发团队配备两名统计顾问，每月免费提供四小时的试验设计指导。',
        '', (0, 0, 0, 1, 0),
        ordinary(E='试验设计指导本身未说明药物效果、获益或效果判断。',
                 Ec='免费的是研发指导服务，不是药价、患者药费或药品支付条件。',
                 I='拟提供的专职顾问、时间资源及指导对象均明确，属于创新研发实质支持；无需已实施。'),
        [evidence('I', '拟为创新药研发团队配备两名统计顾问，每月免费提供四小时的试验设计指导')],
        '拟议的具体研发资源仍讨论I；避免用完成状态替代实质关系判断。',
        ['v1.3:条件陈述/I', 'v1.4:I1'], I=['research_support'])

    background = '项目拟分别准备药品安全性、有效性、经济性、创新性和公平性五类评价文件，各组承担不同任务。'
    add(13, 'P07-background-not-propagated-to-tasks', 'negative',
        '秘书处负责收集各工作组提交的文件名称、版本号和送审份数。',
        background, (0, 0, 0, 0, 0),
        ordinary(I='创新性仅在给定背景文件清单中，当前秘书处文书任务没有实体创新内容。',
                 F='公平性仅在背景文件清单中，当前文书任务没有药物保障、负担或管理难度内容。'), [],
        '自足一般文书职责不继承未来五类文件清单全部维度；材料不缺失。',
        ['v1.3:上下文边界/冒号引导句边界', 'v1.4:共同判断步骤'])
    add(14, 'P07-background-not-propagated-to-tasks', 'positive_for_SE_only',
        '资料组应逐药汇总药物导致的严重不良反应，以及该药降低患者住院率的试验结果。',
        background, (1, 1, 0, 0, 0),
        ordinary(S='当前明确要求汇总药物导致的严重不良反应。',
                 E='当前明确汇总该药降低住院率的治疗效果试验结果。',
                 I='创新性仅在背景清单中，当前药物安全/效果信息不自动是创新属性。',
                 F='当前安全/治疗效果信息不自动构成保障获取或患者负担。'),
        [evidence('S', '药物导致的严重不良反应'),
         evidence('E', '该药降低患者住院率的试验结果')],
        '当前两项明确内容只支持S/E，不能补成背景清单全部五维。',
        ['v1.3:S/E/上下文边界', 'v1.4:共同判断步骤'])

    add(15, 'P08-budget-vs-patient-affordability', 'negative_for_F',
        '预计本年度该药的医保基金支出总额为六十万元。', '',
        (0, 0, 1, 0, 0),
        ordinary(Ec='当前是药品对医保基金的支出预算影响。',
                 F='基金总支出未陈述患者承担、可负担程度、实际保障范围或获取缺口。'),
        [evidence('Ec', '该药的医保基金支出总额为六十万元')],
        '药品经济内容不自动带出患者可负担；基金安全或预算不等于F。',
        ['v1.3:Ec/F', 'v1.4:F1/F4'])
    burden = '患者每月该药自付费用不得超过其家庭月可支配收入的百分之五。'
    add(16, 'P08-budget-vs-patient-affordability', 'positive_for_F', burden, '',
        (0, 0, 1, 0, 1),
        ordinary(Ec='明确患者承担的药费及费用上限。',
                 F='将患者自付药费与家庭可支配收入联系，直接规定可负担程度。'),
        [evidence('Ec', '患者每月该药自付费用不得超过其家庭月可支配收入的百分之五'),
         evidence('F', '患者每月该药自付费用不得超过其家庭月可支配收入的百分之五')],
        '患者可负担与药费可以同时赋Ec/F，F子型应有独立患者负担依据。',
        ['v1.3:Ec/F', 'v1.4:F'], F=['affordability'])
    return rows


def main():
    sources = {
        'manual_v13': ROOT/'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md',
        'manual_v14': ROOT/'outputs/coding-revision-20261007-r3/protocol/共用操作说明-v1.4.md',
        'current_repair_inventory': ROOT/'outputs/编码修订核查-20261008/统计复算/同样本注意力解释/当前Rule39与完整LLM03_已修待修与边界清单.json',
        'reserved_redactor': ROOT/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py'
    }
    bindings = {k: {'path': str(v), 'sha256': sha(v)} for k, v in sources.items()}
    assert bindings['manual_v13']['sha256'] == '75ff8ebda018a15e008bc1075892000fb9c9c053943d05f04bbe193176c605a6'
    assert bindings['manual_v14']['sha256'] == '1b894ea4b6a7e7c06f04a9cbc38d8eaa7c9f28ffe536e839c7a48e0183fc27ee'
    assert bindings['current_repair_inventory']['sha256'] == '64d3e7f71abe6d6f82ee11a3c167aed2bbcc7ee30603475c2125c9e04e29954a'
    rows = build()
    assert len(rows) == 16 and len({x['id'] for x in rows}) == 16
    for row in rows:
        ex = row['expected']; assert set(ex['labels']) == set(DIMS)
        assert all(type(x) is int and x in (0, 1) for x in ex['labels'].values())
        assert bool(ex['innovation_subtypes']) == bool(ex['labels']['I'])
        assert bool(ex['fairness_subtypes']) == bool(ex['labels']['F'])
        for ev in ex['evidence']:
            available = row['input']['text'] if ev['source'] == 'unit' else '\n'.join(
                x['text'] for x in row['input']['contexts']['verified_parent_context'])
            assert ev['quote'] in available
            assert ex['labels'][ev['dimension']] == 1
        assert {e['dimension'] for e in ex['evidence'] if e['source'] == 'unit'} == {
            d for d, value in ex['labels'].items() if value}
    spec = importlib.util.spec_from_file_location('safe_redactor', sources['reserved_redactor'])
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    redactor = module.ReservedContextRedactor()
    protection = redactor.audit_object_no_full_match(rows)
    assert protection['no_remaining_full_normalized_reserved_unit_match']
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    full = {
        'status': 'PREDECLARED_SYNTHETIC_DEVELOPMENT_CONTROLS_NOT_EXECUTED',
        'created_at_UTC': now, 'designer': '/root/validation_state_oct8',
        'n_cases': 16, 'n_pairs': 8, 'n_explicit_dimension_expectations': 80,
        'definition_versions_unchanged': ['CAL-5D-20260926-v1.3', 'v1.4'],
        'unseeded_meaning': 'These new synthetic sentences have not been put into any model request or author prompt by this designer. No candidate08 prompt or output was read before this declaration. They are developer regressions, not independent human validation or a guarantee of unseen mechanism evaluation.',
        'private_before_prompt_freeze': 'Only root receives file paths, hashes and aggregate mechanism descriptions. Do not send the exact synthetic inputs or expectations to the prompt author until candidate08 prompt is frozen.',
        'later_prompt_revision_identity': 'If this reviewer, having read these controls, proposes changes to the candidate08 prompt, record that exposure and the revised prompt SHA; these controls then serve as development regressions rather than an unseeded frozen-prompt behavior check.',
        'controls': rows, 'source_bindings': bindings,
        'protected_full_match_check': protection,
        'new_models_or_classifiers_run': 0,
        'author_prompt_or_handbook_modified': False,
        'original_AB_human_adjudicated_labels_changed': False,
        'scope_not_claimed': 'Not a complete five-dimensional accuracy test; not an estimate of corpus error rate or independent validity.'
    }
    boundaries = {
        'status': 'BOUNDARY_REGISTER_NOT_HARD_TRUTH_OR_ACCEPTANCE_SCORE',
        'created_at_UTC': now,
        'items': [
            {'id': 'C08-B001', 'text': '申请人可在关键试验前，围绕拟支持上市的试验方案申请单专业或多专业沟通。',
             'uncertain_dimension': 'I', 'admissible_interpretations': [0, 1],
             'reason': '一般沟通申请形式与特定方案专业交流本身是否为实体研发便利的界面；不得静默强设唯一I真值。',
             'excluded_from_hard_control_n': True},
            {'id': 'C08-B002', 'text': '本制度规范临床急需短缺药品的申请办理流程。',
             'uncertain_dimension': 'F', 'admissible_interpretations': [0, 1],
             'reason': '短缺为明示关注对象还是仅办理类别/制定宗旨；保留解释，不从短缺词或纯程序一律裁定。',
             'excluded_from_hard_control_n': True},
            {'id': 'C08-B003', 'text': '维持原医保支付范围的药品，按简易续约路线办理。',
             'uncertain_dimension': 'F', 'admissible_interpretations': [0, 1],
             'reason': '既有支付范围作为管理路线前提与保障连续性当前安排的界面；不把旧02072不同意见包装成统一真值。',
             'excluded_from_hard_control_n': True}
        ],
        'rule': 'If used later, report each interpretation and source reasoning; do not use these rows to rescue a failed hard gate or rewrite original human adjudication.'
    }
    assert redactor.audit_object_no_full_match(boundaries)['no_remaining_full_normalized_reserved_unit_match']
    order = [5, 12, 1, 16, 3, 10, 7, 14, 2, 9, 4, 13, 6, 15, 8, 11]
    by_num = {int(r['id'][-3:]): r['input'] for r in rows}
    inputs = [by_num[i] for i in order]
    gates = {
        'status': 'INDEPENDENT_SEMANTIC_ACCEPTANCE_PREDECLARATION_FOR_ROOT_REVIEW_NOT_EXECUTION_AUTHORIZATION',
        'created_at_UTC': now,
        'meaning': 'Predeclare manual compliance checks before candidate08 actual output; do not tune to project kappa targets or A/B labels.',
        'hard_synthetic_scope': {'n': 16, 'dimension_cells': 80, 'all_five_dimensions_reviewed_per_case': True},
        'semantic_requirements': [
            'All16 full outputs must be reviewed: labels, five reasons, continuous literal current-unit evidence, necessary controlling-context evidence, I/F subtypes, S quality basis and issue/material flags.',
            'Positive evidence must establish the declared relation, not merely share a keyword. Attribute is distinct from research_support; affordability is distinct from access.',
            'Read P03/P04 controlling parent relations; do not copy parent background labels or demand that planned substantive support/withdrawal already be implemented.',
            'Preserve S/E/Ec when independently present; do not erase other dimensions to fix I/F.',
            'P07 clerical task is self-contained and has no material gap; future five-document background must not be spread to the task. Positive current S/E content supports only S/E.',
            'Keep pure price-consultation appointment administration apart from actual drug-price conditions, and keep price/fund-budget content apart from patient affordability.',
            'All16 declared hard expectations and justified subtype/quality relations must hold; mechanical expected-label matches alone are insufficient.',
            'Any genuine ambiguity found before execution must be retained, discussed and placed into a separately frozen revision. Never change expected labels after observing candidate08 output simply to pass.'
        ],
        'boundary_policy': 'Three separately registered boundary cases do not enter the16/80 hard gate; no forced unique truth.',
        'real_development_followup': [
            'Use only authorized old240 development inputs and redacted reviewer projections; protect267 unit and context members.',
            'Force review of known current03 omissions01955/02764/03876 and overinclusions02830/02845, plus F01562; label-unchanged outputs must not skip review.',
            'Do not transfer candidate07 new regressions to03; preserve07 failure history and require whole-candidate adoption rather than splicing individual passing rows.',
            'Original A/B human-adjudicated labels stay fixed; diagnostic AI review opinions remain separate.'
        ],
        'technical_separation': 'Model/schema/runtime/first valid technical selection and retry bounds must be separately frozen by the execution owner. This package does not run or authorize a model.',
        'root_requested_first_stage': 'After prompt freeze and explicit root execution authorization, these16 cases fit one synthetic behavioral-check logical request. It is not external or human validity evidence; technical-attempt bounds belong to the execution owner.',
        'expectations_must_not_be_model_input': True,
        'new_model_calls': 0, 'source_files_modified': False
    }
    files = {
        'independent_synthetic16_FULL5_PRIVATE_PREDECLARED.json': json.dumps(full, ensure_ascii=False, indent=2) + '\n',
        'independent_synthetic16_inputs_ONLY_PRIVATE_PREDECLARED.json': json.dumps(inputs, ensure_ascii=False, indent=2) + '\n',
        'boundary_register_PRIVATE_NOT_SCORED.json': json.dumps(boundaries, ensure_ascii=False, indent=2) + '\n',
        'semantic_acceptance_PRIVATE_PREDECLARED.json': json.dumps(gates, ensure_ascii=False, indent=2) + '\n'
    }
    for name, text in files.items():
        path = HERE/name; assert not path.exists(); path.write_text(text, encoding='utf-8')
    manifest = {
        'status': 'FROZEN_INDEPENDENT_DESIGN_V1_ZERO_MODEL_CALLS_ROOT_REVIEW_PENDING',
        'created_at_UTC': now, 'source_bindings': bindings,
        'files': [{'path': str(HERE/name), 'sha256': sha(HERE/name)} for name in files],
        'builder': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)},
        'mechanical_QA': {'cases': 16, 'pairs': 8, 'dimension_expectations': 80,
            'all_labels_binary': True, 'all_positive_dimensions_have_literal_unit_evidence': True,
            'all_quotes_exact_substrings_of_assigned_source': True,
            'I_F_subtypes_present_only_on_positive_labels': True,
            'context_relations_positive_and_negative_paired': True,
            'protected_full_match_check': protection},
        'actual_candidate08_prompt_read': False,
        'actual_candidate08_outputs_read': False,
        'private_author_content_disclosure_before_prompt_freeze': False,
        'reviewer_later_prompt_edit_requires_identity_transition_record': True,
        'model_calls': 0, 'source_handbook_AB_predictions_modified': False,
        'not_external_validation': True
    }
    assert all(sha(Path(v['path'])) == v['sha256'] for v in bindings.values())
    path = HERE/'independent_design_manifest_v1.json'; assert not path.exists()
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(path), 'sha256': sha(path), 'cases': 16,
                      'pairs': 8, 'dimensions': 80, 'model_calls': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
