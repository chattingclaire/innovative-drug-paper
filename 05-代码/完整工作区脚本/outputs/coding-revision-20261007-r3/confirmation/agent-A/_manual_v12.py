"""Personal semantic judgments by AI coder A; serialization/QA only."""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import jsonschema

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
PROTOCOL = ROOT.parent / 'protocol'
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def row(n, labels, reasons, evidence=(), innovation=(), issues=()):
    return {
        'id': f'AV3-A-{n:04d}',
        'labels': dict(zip(DIMS, labels)),
        'dimension_reasons': dict(zip(DIMS, reasons)),
        'evidence': [dict(zip(('dimension', 'source', 'quote'), e)) for e in evidence],
        'innovation_subtypes': list(innovation),
        'fairness_subtypes': [],
        'safety_quality_basis': 'no_quality_basis',
        'issues': list(issues),
    }

# Judgments were fixed after complete v12 reading, before looking up any first
# submission for the mechanically generated change comparison below.
rows = [
    row(148, (0, 0, 0, 0, 0), (
        '当前要求处方审核人员符合第五条资格；完整引用仅规定药师职务资格、调剂经历、岗位知识培训与考核，没有药物损害、风险或用药错误的实质评价要求。“审核质量管理”标题不等于药品质量安全。',
        '当前及所援引两项条件讨论审核人员资历和岗位能力，没有药物防治效果、临床获益或效果证据要求。',
        '处方审核人员任职、经历和培训条件不涉及药价、药费、治疗成本、支付标准或基金支出。',
        '该人员资格要求没有药物原创/改良属性、专有创新权利、创新研发支持或创新资格比较优势。',
        '当前是处方审核队伍的一般人员管理要求，没有药品实际保障/供应安排、患者药费负担、治疗获取缺口或针对某药临床管理难度的评价。',
    ), issues=(
        '已读第五条引导句及完整两项资格，并读第六条边界文本；当前明确引用已被消解。人员审核资历不由合理用药或审核质量背景自动赋S/F。当前资格命题可自足，不因其他父级数组为空而猜测缺料。',
    )),
    row(239, (1, 1, 0, 1, 0), (
        '表行备注明确以符合第七条第一款为六年保护期的条件；该款要求提交用于证明药品安全性的全部试验数据，故当前实质适用条件包含安全证据要求。质量可控性本身不被转写成药品质量安全，S独立依据为药品安全性数据。',
        '当前六年数据保护适用条件明确援引第七条第一款，其要求提交用于证明药品有效性的全部试验数据，故涉及药物效果证据要求，而非将保护期中的年限解释为有效性。',
        '表行规定药品注册类别、专有数据保护期限及实质适用条件，没有药价、治疗费用、支付标准、药费承担或药物经济评价内容，不能从专有权可能具有经济价值推定Ec。',
        '核验表头后，当前内容列明改良型生物制品这一注册分类，构成改良属性依据；数据保护期列及备注实质给予四年/符合条件六年的专有试验数据保护，结合被明确援引的权利范围，构成针对药品研发数据的专有权利支持。分别记录attribute与research_support，不推定临床比较优势。',
        '当前确定专有数据权利期限与适用条件，未实质规定常规治疗药品给付、配备供应、患者负担或临床管理难度；不由潜在市场竞争/许可影响推定患者保障获取变化。',
    ), (
        ('S', 'unit', '并符合本办法第七条第一款的'),
        ('S', 'context', '并提交本办法第五条第三款规定的用于证明药品安全性、有效性和质量可控性的全部试验数据的'),
        ('E', 'unit', '并符合本办法第七条第一款的'),
        ('E', 'context', '用于证明药品安全性、有效性和质量可控性的全部试验数据'),
        ('I', 'unit', '2类 | 改良型生物制品 | 4年'),
        ('I', 'unit', '数据保护期为6年'),
        ('I', 'context', '治疗用生物制品注册分类和数据保护期；列名：分类 | 内容 | 数据保护期 | 备注'),
        ('I', 'context', '在数据保护期内,其他申请人未经持有人同意,依赖该持有人受保护的数据提交的改良型新药、化学仿制药和生物类似药的上市申请或者补充申请,国家药监局不予许可'),
    ), innovation=('attribute', 'research_support'), issues=(
        '当前表行、列名、原始行单元格、第七条两款和其明确再援引的第五条完整范围均已阅读。明确“符合第七条第一款”使安全/有效性试验数据提交成为当前六年保护的实质资格条件，故S/E=1；不是从数据保护主题自动复制所有背景标签。',
        '第七条第二款、第五条其他款及相邻第六/八条边界只用于消解范围和回指，不另加分析单元，也未把这些段落的一切维度归给当前表行。',
        '安全质量标记保留no_quality_basis：质量可控性与安全性并列，但未明确表达药品质量安全/质量风险；本条S由独立药品安全性证据要求成立。I不含qualification_advantage，材料没有临床比较优势命题。',
    )),
]

def strings(x, path):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from strings(v, path + '.' + k)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            yield from strings(v, path + f'[{i}]')
    elif isinstance(x, str):
        yield path, x

def write_new(p, obj):
    with p.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')

if __name__ == '__main__':
    packet_path = BASE / '补充材料-v12.json'
    schema_path = ROOT / '结果schema-v12.json'
    packet = json.loads(packet_path.read_text())
    assert packet['material_version'] == 'v12'
    assert [r['id'] for r in rows] == [r['id'] for r in packet['rows']]
    result = {
        'coder': 'A', 'protocol_version': 'CAL-5D-20260926-v1.3',
        'operational_version': 'v1.4', 'material_version': 'v12',
        'input_packet_sha256': sha(packet_path), 'rows': rows,
    }
    jsonschema.validate(result, json.loads(schema_path.read_text()))
    evidence_audit = []
    for material, judgment in zip(packet['rows'], rows):
        ctx_strings = list(strings(material['contexts'], 'contexts'))
        assert set(judgment['labels']) == set(DIMS)
        assert set(judgment['dimension_reasons']) == set(DIMS)
        assert all(type(v) is int and v in (0, 1) for v in judgment['labels'].values())
        assert all(judgment['dimension_reasons'][d].strip() for d in DIMS)
        assert bool(judgment['innovation_subtypes']) == (judgment['labels']['I'] == 1)
        assert bool(judgment['fairness_subtypes']) == (judgment['labels']['F'] == 1)
        for d in DIMS:
            if judgment['labels'][d] == 1:
                assert any(e['dimension'] == d and e['source'] == 'unit' for e in judgment['evidence'])
        for e in judgment['evidence']:
            pool = [('text', material['text'])] if e['source'] == 'unit' else ctx_strings
            matches = [{'field': p, 'start': s.index(e['quote']), 'end': s.index(e['quote']) + len(e['quote'])}
                       for p, s in pool if e['quote'] in s]
            assert matches, (judgment['id'], e)
            evidence_audit.append({'id': judgment['id'], **e, 'literal_contiguous_match': True, 'matches': matches})

    preserved_paths = [BASE / f'结果-{i:02d}.json' for i in range(1, 9)] + [
        BASE / '补料复读结果-v11.json', BASE / '补料复读变更说明-v11.json', BASE / '补料复读QA-v11.json'
    ]
    preservation_before = {str(p): sha(p) for p in preserved_paths}
    result_path = BASE / '补料复读结果-v12.json'
    write_new(result_path, result)

    # Look up only these two A first rows after the complete v12 judgments have
    # been fixed and saved. This step supplies accurate change documentation;
    # no first label is used to generate or revise the new judgments.
    prior_rows = {}
    for n, packet_no in ((148, 5), (239, 8)):
        prior = json.loads((BASE / f'结果-{packet_no:02d}.json').read_text())
        ident = f'AV3-A-{n:04d}'
        selected = [r for r in prior['rows'] if r['id'] == ident]
        assert len(selected) == 1
        prior_rows[ident] = selected[0]
    change_rows = []
    for material, judgment in zip(packet['rows'], rows):
        prior = prior_rows[judgment['id']]
        change_rows.append({
            'id': judgment['id'], 'first_labels': prior['labels'], 'reread_labels': judgment['labels'],
            'label_changes': {d: [prior['labels'][d], judgment['labels'][d]] for d in DIMS if prior['labels'][d] != judgment['labels'][d]},
            'first_innovation_subtypes': prior['innovation_subtypes'], 'reread_innovation_subtypes': judgment['innovation_subtypes'],
            'first_fairness_subtypes': prior['fairness_subtypes'], 'reread_fairness_subtypes': judgment['fairness_subtypes'],
            'first_safety_quality_basis': prior['safety_quality_basis'], 'reread_safety_quality_basis': judgment['safety_quality_basis'],
            'material_change': '新增当前原句明确引用的完整资格/条文及边界，当前text保持材料包原句。',
            'new_material_used': material['contexts']['explicitly_cited_qualifications_v12']['references'],
            'removed_text_relied_on': [],
            'reread_basis': judgment['dimension_reasons'], 'boundary_issues': judgment['issues'],
        })
    changes = {
        'coder': 'A', 'material_version': 'v12', 'protocol_version': result['protocol_version'],
        'operational_version': 'v1.4', 'input_packet_sha256': sha(packet_path),
        'comparison_method': '本次两条判断先独立固定并写出结果，再仅检索本方首次文件中对应ID以记载准确变化；不据首次标签修改本次判断。',
        'not_metric_driven': True, 'rows': change_rows,
    }
    changes_path = BASE / '补料复读变更说明-v12.json'
    write_new(changes_path, changes)
    preservation_after = {str(p): sha(p) for p in preserved_paths}
    assert preservation_before == preservation_after
    assert sha(packet_path) == result['input_packet_sha256']
    reread_saved = json.loads(result_path.read_text())
    jsonschema.validate(reread_saved, json.loads(schema_path.read_text()))
    assert reread_saved == result
    qa = {
        'coder': 'A', 'actual_identity': 'AI agent', 'material_version': 'v12',
        'completed_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'protocol_version': result['protocol_version'], 'operational_version': 'v1.4',
        'input_packet_sha256': sha(packet_path),
        'authorized_source_and_protocol_reads_sha256': {str(p): sha(p) for p in (
            packet_path, ROOT / '补料任务说明-v12.json', schema_path,
            PROTOCOL / '完整五维手册-v1.3.md', PROTOCOL / '共用操作说明-v1.4.md'
        )},
        'own_first_submission_comparison_reads': {
            'after_new_judgments_saved': True,
            'files_sha256': {str(BASE / f'结果-{i:02d}.json'): sha(BASE / f'结果-{i:02d}.json') for i in (5, 8)},
            'selected_ids_only_for_comparison': ['AV3-A-0148', 'AV3-A-0239'],
        },
        'row_ids_in_input_order': [r['id'] for r in rows],
        'manual_read_scope': '两条当前text及全部递归contexts均完整阅读，包括明确引用、二级引用、表头/行对应、版本后缀、边界文本及源证书；空数组不替代其他字段阅读。',
        'checks': {
            'schema': 'passed', 'actual_input_sha_binding': 'passed',
            'coverage_2_rows_10_dimensions_and_reasons': 'passed', 'all_labels_binary': 'passed',
            'current_unit_quote_for_each_one': 'passed',
            'all_quotes_literal_contiguous_without_normalization': 'passed',
            'I_F_subtype_presence_and_manual_basis': 'passed', 'S_quality_basis_manual_review': 'passed',
            'first_eight_and_v11_files_preserved': 'passed',
        },
        'subtype_manual_review': {
            'I_attribute': {'id': 'AV3-A-0239', 'unit_quote': '2类 | 改良型生物制品 | 4年', 'basis': '核验注册分类表列后的改良属性。'},
            'I_research_support': {'id': 'AV3-A-0239', 'unit_quote': '数据保护期为6年', 'basis': '当前实质专有数据保护期限，已引用第五条的许可排他范围确认属于专有研发数据权利，不是一般保密。'},
            'I_qualification_advantage': '两条均无临床比较优势资格依据。',
            'F': '两条均F=0且无F子类；一般审核队伍要求及专有数据权利不推定患者保障获取。',
            'S_quality': '0148 S=0；0239 S来自明确药品安全性数据，普通质量可控性不另作为质量安全扩展依据，均no_quality_basis。',
        },
        'material_gaps_remaining': [],
        'preservation_before': preservation_before, 'preservation_after': preservation_after,
        'reading_boundary': {
            'other_coder_or_machine_or_statistics_or_private_read': False,
            'external_source_pdf_image_url_or_locator_opened': False,
            'source_identity_completely_blind_claimed': False,
            'note': '来源内容及证书仅在获授权A材料包内读取；没有打开证书定位文件或外部网址。',
        },
        'method': '本人语义判断；程序仅序列化、核验ID/schema/SHA/连续引文及字段覆盖，并在新结果固定后比较本方首次对应ID；未以词表正则生成标签或理由，未追求指标一致。',
        'evidence_audit': evidence_audit,
        'output_files_sha256': {str(p): sha(p) for p in (result_path, changes_path)},
    }
    write_new(BASE / '补料复读QA-v12.json', qa)
    print(json.dumps({'status': 'passed', 'rows': len(rows), 'dimensions': 10,
                      'input_sha256': sha(packet_path), 'old_files_unchanged': True,
                      'outputs': [str(result_path), str(changes_path), str(BASE / '补料复读QA-v12.json')]}, ensure_ascii=False))
