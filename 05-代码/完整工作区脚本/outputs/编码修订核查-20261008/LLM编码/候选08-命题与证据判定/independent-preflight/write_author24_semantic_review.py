from pathlib import Path
import hashlib
import json

BASE = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/编码修订核查-20261008/LLM编码/候选08-命题与证据判定')
OUT = BASE / 'independent-preflight'
PROTOCOL = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/coding-revision-20261007-r3/protocol')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

source = BASE / 'synthetic24_pairs_PRIVATE_PROPOSED.json'
entry = BASE / 'execution_layer_PROPOSED.txt'
prompt = BASE / 'candidate08_prompt_PROPOSED.txt'
assert sha(source) == '8bede02451ecc21e848116b5958e1a378322198fdc48744227e29420cd6e1e7e'
assert sha(entry) == 'c9bb8b3d04f662f1b519835d27980496583f1cb260de563753ca8e1a2a383efa'
assert sha(prompt) == 'd79c097443fa249051c5264da1ff532ddf7d984225ac3e776807de95f7f21803'
assert prompt.read_text().startswith(entry.read_text())
old_phrase = '说明当前条件导致什么结果'
new_phrase = '若当前命题依赖条件—结果关系，说明该条件决定什么结果'
reconstructed_initial = entry.read_text().replace(new_phrase, old_phrase)
assert hashlib.sha256(reconstructed_initial.encode()).hexdigest() == 'ddd3461defd5fc3f316ac5e6a7caa745e0fea68cf7ced1f7e42f16f68bd95a72'

# Independent semantic judgments recorded explicitly; do not infer these from source labels.
# Order: S, E, Ec, I, F. Each reason addresses that dimension in the complete synthetic input.
J = {
'01-A': ([0,0,0,1,0], ['没有药物损害或风险内容。','获准使用人群改变未陈述治疗效果。','没有药价费用内容。','原获准人群明确由成人增补儿童，表述相对既有产品使用属性改变，不要求优效。','儿童名称及获准人群变化本身没有治疗缺口、保障获取或患者负担内容。'], ['attribute'], [], 'v1.3:142; v1.4:14,16'),
'01-B': ([0,0,0,0,0], ['窗口登记不是风险内容。','未要求效果内容。','没有治疗费用内容。','首次递交只为申报身份，未述产品属性改变。','登记窗口不是实际药物保障。'], [], [], 'v1.3:67,142; v1.4:9,16,21'),
'02-A': ([0,0,0,1,0], ['没有损害风险依据。','缓释改变未另述效果或临床获益。','没有费用依据。','明确要求说明即释改缓释的制剂变化，备案动作不抹去实质属性要求。','未述获取、负担或临床管理难度。'], ['attribute'], [], 'v1.3:43,65,142; v1.4:14'),
'02-B': ([0,0,0,0,0], ['通用名及备案单无风险依据。','无效果依据。','无费用依据。','名称登记未讨论创新属性。','无保障获取依据。'], [], [], 'v1.3:67; v1.4:9,16'),
'03-A': ([1,0,0,1,0], ['毒性监测方案技术指导是风险识别与控制内容。','未述药物防治效果。','无治疗费用内容。','服务机构当前向明确原创药研发对象提供实体技术指导，属于研发支持；对象身份不另记attribute。','未述治疗获取或管理难度。'], ['research_support'], [], 'v1.3:21,166; v1.4:13'),
'03-B': ([1,0,0,0,0], ['申请人执行毒性监测并报告结果为明确安全内容要求。','未述效果。','无费用内容。','原创药研发对象仅为义务承担者；未提供或讨论支持措施。','监测未用于评价具体管理难度，不由安全义务自动补F。'], [], [], 'v1.3:21,45,73; v1.4:13,25'),
'04-A': ([1,0,0,0,0], ['提交药物毒性结果和风险控制方案为当前安全证据要求。','无治疗效果要求。','无费用要求。','资料义务不是创新支持或属性。','无获取或管理难度依据。'], [], [], 'v1.3:21,65; v1.4:13'),
'04-B': ([0,0,0,0,0], ['当前只有预约沟通及联系方式更新，安全主题未构成当前安全内容要求。','无效果要求。','无费用要求。','无创新属性或实体研发支持。','无药物保障安排。'], [], [], 'v1.3:17,67; v1.4:7,9,13'),
'05-A': ([0,0,1,0,1], ['安全资料已在别处评估只是背景，不是当前费用子项内容。','疗效资料已在别处评估只是背景，不传入当前子项。','当前规定该药治疗费用增幅的上限。','没有创新属性或研发支持。','实际父谓词把当前费用条件与原药物保障协议延续一年连接，属于保障连续条件。'], [], ['access'], 'v1.3:17,35; v1.4:7,21,22'),
'05-B': ([0,0,1,0,0], ['别处已评估安全资料不传入当前条件。','别处已评估疗效资料不传入当前条件。','费用增幅阈值为当前经济内容；用途仅为申请条件，不称实际费用管制。','没有创新依据。','只获得递交续约申请资格，是否续签另定，不能补保障延续。'], [], [], 'v1.3:17,35; v1.4:7,21,22'),
'06-A': ([1,1,1,1,1], ['当前必须提交清单明确包含药物毒性分析。','当前必须提交清单包含临床疗效数据。','当前必须提交清单包含药费预算。','当前必须提交原制剂改良信息，属于属性信息要求。','当前必须提交公平性信息，内容未细分，不猜获取、可负担或管理难度。'], ['attribute'], ['dimension_information'], 'v1.3:65,69,125,148; v1.4:7'),
'06-B': ([0,0,0,0,0], ['版式说明和未来文件规划不是当前毒性内容要求。','不由相邻未来专题补当前效果要求。','不由未来专题补当前药费要求。','不由未来专题补当前改良属性要求。','不由未来专题补当前公平信息要求。'], [], [], 'v1.3:17,67,146; v1.4:7,9,17'),
'07-A': ([0,0,0,0,0], ['无药物风险内容。','无效果内容。','仅组织参加协商并安排会场，未述价格取值、费用承担或经济评价；属于谈判事务。','无创新内容。','无保障范围或获取内容。'], [], [], 'v1.3:35,37; v1.4:9'),
'07-B': ([0,0,1,0,0], ['无风险依据。','无效果依据。','实际采购价格用于计算基金支付上限，明确药价及支付经济内容。','无创新依据。','未确定该药的保障纳入、获取渠道或患者负担，不由基金支付金额自动补F。'], [], [], 'v1.3:35,57; v1.4:21,24'),
'08-A': ([0,0,0,0,0], ['预约受理无风险内容。','无效果内容。','没有费用/支付标准内容。','无创新内容。','企业拟申请是手续适用对象；当前要求预约，不是政策确定具体药物覆盖。'], [], [], 'v1.3:11,67; v1.4:21,22'),
'08-B': ([0,0,0,0,1], ['无风险依据。','无效果依据。','仅覆盖纳入未述价格费用，不补Ec。','无创新依据。','方案当前拟定该药具体保障覆盖，不要求已实施或方向扩大。'], [], ['access'], 'v1.3:11; v1.4:21'),
'09-A': ([0,0,0,0,1], ['无风险内容。','提供治疗安排本身未述效果、推荐比较或效果证据。','无药费承担内容。','研究药名称未述创新。','明确缺少可获得治疗及对应研究药治疗安排，符合治疗获取例外，不另加常规渠道/穷尽替代要求。'], [], ['access'], 'v1.3:55,83; v1.4:23,26'),
'09-B': ([0,0,0,0,0], ['无风险内容。','随机分组和供研究药未明确效果判断用途。','无费用内容。','研究药未述创新属性。','仅向已入组受试者按组分配，未述治疗获取缺口。'], [], [], 'v1.3:55,81; v1.4:23'),
'10-A': ([0,1,0,1,0], ['无独立风险内容。','当前技术建议明确针对疗效终点科学选择，服务于药物效果判断。','无费用内容。','实际技术指导结合给定原创药研发服务对象，构成研发支持；对象身份不另记attribute。','无获取或管理难度内容。'], ['research_support'], [], 'v1.3:29,31,166; v1.4:7,13'),
'10-B': ([0,0,0,0,0], ['无风险内容。','无效果内容。','无费用内容。','对原创药团队解释排版/编号仍是通用事务，不由服务对象复制I。','无保障内容。'], [], [], 'v1.3:17,67; v1.4:13,17'),
'11-A': ([0,1,0,0,0], ['复发效果不是已表述的药物损害。','研究明确比较药物降低疾病复发的效果并报告终点结果。','无费用内容。','研究本身未陈述创新属性或创新支持。','无治疗获取缺口或保障依据。'], [], [], 'v1.3:29,31,65'),
'11-B': ([0,0,0,0,0], ['访视日期记录未述风险内容。','方法/访视形式未与药物效果判断建立明确联系。','无费用内容。','研究形式未述创新。','一般访视安排未述治疗获取或管理难度。'], [], [], 'v1.3:31,67,81'),
'12-A': ([0,0,1,0,1], ['无风险依据。','无效果依据。','保险机构承担药费是明确费用责任。','无创新依据。','明确该药纳入保障范围支持access；保险费用责任本身未另述患者支付能力或药费负担，不多选affordability。'], [], ['access'], 'v1.3:35,53,57,156'),
'12-B': ([0,0,1,0,1], ['无风险依据。','无效果依据。','减免个人药费是明确费用内容。','无创新依据。','具体保障覆盖支持access；患者难以负担自付药费及减免另有独立affordability依据。'], [], ['access','affordability'], 'v1.3:35,53,156'),
}

payload = json.loads(source.read_text())
rows = []
for pair in payload['pairs']:
    for member in pair['members']:
        key = member['input']['id'].removeprefix('C08-PAIR-')
        vector, reasons, itypes, ftypes, basis = J[key]
        labels = dict(zip(['S','E','Ec','I','F'], vector))
        assert labels == member['labels'], key
        assert itypes == member['innovation_subtypes'], key
        assert ftypes == member['fairness_subtypes'], key
        assert member['safety_quality_basis'] == 'no_quality_basis', key
        rows.append({
            'id': member['input']['id'], 'complete_input_actually_reviewed': member['input'],
            'independent_dimension_judgments': labels,
            'dimension_reasons': dict(zip(['S','E','Ec','I','F'], reasons)),
            'innovation_subtypes_supported': itypes, 'fairness_subtypes_supported': ftypes,
            'safety_quality_basis_supported': 'no_quality_basis',
            'quality_basis_reason': 'No member mentions explicit drug quality safety/quality risk; positive S cases concern toxicity or clinical risk only.',
            'manual_basis': basis, 'matches_proposed_labels_and_attached_fields': True,
            'status': 'SUPPORTED_WITHIN_THIS_SYNTHETIC_DESIGN',
        })
assert len(rows) == 24 and len(J) == 24

report = {
    'status': 'PASS_DESIGN_ONLY_NO_ACTUAL_MODEL_OR_REAL_MATERIAL_ADOPTION_CLAIM',
    'date': '2026-10-08',
    'review_identity': 'Separate AI semantic review of author-proposed synthetic expectations; proposed labels were visible. Not a blind accuracy test or human review.',
    'scope': {'synthetic_pairs': 12, 'members': 24, 'dimension_judgments': 120,
              'all_complete_input_contexts_and_proposed_auxiliary_fields_actually_read': True,
              'actual_model_calls': 0, 'resampling': 0,
              'root_independent16_read': False, 'real240_or_reserved_originals_or_AB_scores_read': False},
    'bindings': [{'path': str(p), 'sha256': sha(p)} for p in [source, entry, prompt,
        PROTOCOL/'完整五维手册-v1.3.md', PROTOCOL/'共用操作说明-v1.4.md']],
    'execution_layer_review': {
        'initial_sha256': 'ddd3461defd5fc3f316ac5e6a7caa745e0fea68cf7ced1f7e42f16f68bd95a72',
        'initial_comment': 'Unqualified request to state what condition causes what result could impose a conditional structure on every self-contained statement.',
        'original_phrase': old_phrase, 'accepted_replacement': new_phrase,
        'current_sha256': sha(entry), 'revision_status': 'ACTUALLY_READ_AND_FIXED',
        'only_that_phrase_changed_verified_by_reconstructed_initial_sha': True,
        'current_prompt_sha256': sha(prompt), 'current_prompt_has_reviewed_execution_layer_as_exact_prefix': True,
        'definition_change_found': False,
        'remaining_blocking_issue': False,
    },
    'rows': rows,
    'limitations': [
        'This supports the semantics of these constructed inputs and execution instructions only.',
        'No output labels, reasons, quotations, offsets or runtime behavior have been evaluated; the full technical wrapper and preflight remain a separate task.',
        'Does not decide unresolved boundaries in real material, establish independent validity, or guarantee every kappa exceeds 0.80.',
        'Original 07 failure and observed low values remain unchanged. Manual definitions and schema are not modified.',
    ],
}
OUT.mkdir(exist_ok=True)
json_path = OUT/'author24_semantic_design_review.json'
md_path = OUT/'author24_semantic_design_review.md'
assert not json_path.exists() and not md_path.exists()
json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
lines = [
    '# 候选08作者24控制独立语义设计预检', '',
    '结论：当前执行层与12对24构造控制在既定v1.3/v1.4下无语义阻断。已实际完整读全部输入及contexts、120维和全部I/F子类、S质量预期；逐条理由见JSON。', '',
    '这是可见作者预期的单独AI设计复核，不是盲测、真人审查、实际模型结果或独立验证。0模型、0重采样，未读真实240、保留原文、A/B分数或root独立16。', '',
    '最初唯一意见：将“说明当前条件导致什么结果”改为“若当前命题依赖条件—结果关系，说明该条件决定什么结果”。当前已实际回读修正；逆替换后SHA与原版本一致，未扩大定义或改变24预期。', '',
    f'当前完整prompt SHA：`{sha(prompt)}`；执行层SHA：`{sha(entry)}`；24控制SHA：`{sha(source)}`。', '',
    '| 控制 | S/E/Ec/I/F | I来源 | F来源 | 独立语义结论 |',
    '|---|---|---|---|---|',
]
for row in rows:
    v='/'.join(str(row['independent_dimension_judgments'][d]) for d in ['S','E','Ec','I','F'])
    lines.append('| '+row['id']+' | '+v+' | '+(','.join(row['innovation_subtypes_supported']) or '无')+' | '+(','.join(row['fairness_subtypes_supported']) or '无')+' | 支持；逐维理由见JSON |')
lines += ['', '全部S质量预期均为no_quality_basis；S正类构造依据毒性/风险，不含药品质量安全表达。PAIR01明确获准使用属性改变而非仅人群名；PAIR05不复制已在别处评估的S/E；PAIR06区分当前必需清单与未来文件规划；PAIR07协商事务0、价格计算Ec1；PAIR09明确试验治疗缺口不加常规渠道门槛；PAIR12仅有独立患者负担内容才增加affordability。', '',
          '当前通过仅限合成开发设计。真实材料边界不因此裁断；实际输出的理由、证据offset、子类、技术门禁须另审，不保证κ达0.80。']
md_path.write_text('\n'.join(lines)+'\n')
print(json.dumps({'json': str(json_path), 'json_sha256': sha(json_path), 'md': str(md_path),
                  'md_sha256': sha(md_path), 'status': report['status']}, ensure_ascii=False))
