"""Coder A's personally authored v11 rereading; code only serializes and audits."""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
PROTOCOL = ROOT.parent / 'protocol'
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def row(n, values, reasons, evidence=(), fairness=(), issues=()):
    return {
        'id': f'AV3-A-{n:04d}',
        'labels': dict(zip(DIMS, values)),
        'dimension_reasons': dict(zip(DIMS, reasons)),
        'evidence': [dict(zip(('dimension', 'source', 'quote'), e)) for e in evidence],
        'innovation_subtypes': [],
        'fairness_subtypes': list(fairness),
        'safety_quality_basis': 'no_quality_basis',
        'issues': list(issues),
    }

# All labels, reasons, evidence selection and boundary notes below were authored
# by coder A after reading each complete supplied proposition and its contexts.
rows = [
    row(3, (1, 1, 1, 0, 0), (
        '当前规定要求目录外药品符合第七条、第八条；所明确援引的第七条把安全作为药品基本条件，故当前申请资格实质纳入安全要求。依据是该明确内容援引，不是由新上市身份推定安全。',
        '当前申请资格明确要求符合第七条、第八条，援引的第七条含药品有效这一基本条件，故涉及有效性要求；并未把已获上市批准等同疗效已被证明。',
        '当前要求符合第七条、第八条，明确援引的第七条以价格合理作为药品基本条件，因而资格要求包含药品价格内容。',
        '当前规定目录外药品的申报资格，没有独立陈述创新属性、创新研发支持或创新资格比较优势。完整后项中的新通用名、新上市及既有鼓励清单身份不向此引导句复制创新标签。',
        '当前结果是可以申报纳入基本目录，尚属申报资格，没有确定实际医保给付、纳入结果、患者费用负担或治疗获取安排；第八条的目录排除规定仅用于解释引用资格，不将其退出/保障标签复制到当前申报命题。',
    ), (
        ('S', 'unit', '符合《基本医疗保险用药管理暂行办法》第七条、第八条规定'),
        ('S', 'context', '并符合临床必需、安全有效、价格合理等基本条件'),
        ('E', 'unit', '符合《基本医疗保险用药管理暂行办法》第七条、第八条规定'),
        ('E', 'context', '并符合临床必需、安全有效、价格合理等基本条件'),
        ('Ec', 'unit', '符合《基本医疗保险用药管理暂行办法》第七条、第八条规定'),
        ('Ec', 'context', '价格合理'),
    ), issues=(
        '首次待定的缺口已由完整5项后续条件及第七、八条原文补齐。明确要求“符合”特定条文构成实质内容援引；S/E/Ec按被援引的药品基本条件判1，并非将后续各项或背景全部传播到当前句。完整材料下保留此个人边界判断。',
        '所有实际后项及第八条八项均已阅读。其作用是确定申报对象/排除条件；没有把罕见病、儿童药品或鼓励研发清单名称直接转换为F/I。',
    )),
    row(155, (0, 0, 0, 0, 1), (
        '当前句规定符合后列情形的目录内药品经评审直接调出，未在当前命题提出药物伤害、风险或质量安全评价内容；不能将第三后项的不良反应等标签复制给整个引导句。',
        '当前句陈述直接调出的处置结果，未独立要求药品疗效、临床价值或效果证据评价；第三后项的临床价值内容保留在其自身命题。',
        '当前句未陈述药价、费用、基金支出或药物经济学要求；完整后项中的药物经济性不自动赋给当前退出引导句。',
        '当前目录退出安排没有创新属性、明确创新研发支持或创新资格比较优势要求。',
        '当前对符合情形的目录内药品规定经评审后直接调出，实质确定医保药品保障范围的退出，按保障获取计F，方向为限制也计入。',
    ), (
        ('F', 'unit', '《药品目录》内的药品,有下列情况之一的,经专家评审后,直接调出《药品目录》'),
    ), fairness=('access',), issues=(
        '已阅读第九条完整5项实际列举及下一条边界。后项补足退出适用情形，但不把各后项S/E/Ec复制给当前直接退出命题。结构字段补齐不改变首次五维判断。',
    )),
    row(177, (0, 0, 0, 0, 1), (
        '当前命题是既有谈判药品到期后在满足条件时简易续约两年，未提出药物伤害、风险或质量安全要求。',
        '当前规定续约资格及续约年限，没有药品治疗效果、临床价值或疗效证据评价要求；完整后项亦不改变当前命题的这一边界。',
        '当前句没有陈述药价、治疗费用、基金金额或支付标准内容。完整后项的预算支出、价格和市场环境条件用于理解适用范围，其具体经济内容不复制给当前续约引导句。',
        '当前续约安排没有陈述创新属性、创新研发支持或创新资格比较优势，独家药品身份也不等同创新资格。',
        '经明确对象语境确认是谈判药品协议到期后的处理，当前对同时满足条件的既有药品给予两年简易续约，构成原有药物医保保障延续的实质条件和期限，按保障获取计F。',
    ), (
        ('F', 'unit', '协议将于2022年12月31日到期,并同时满足以下条件的药品,可以简易续约,续约有效期2年'),
        ('F', 'context', '现分类制定谈判药品(含续约药品)协议到期后的处理规则如下'),
    ), fairness=('access',), issues=(
        '首次所缺同时满足条件的完整列举现已补齐，包括5个主条件及预算增幅的2个分项，边界止于“二、规则”。材料已足够二元判断。',
        '边界判断：本人将当前给予既有谈判药品两年续约理解为原有保障连续性的实质安排；它超过仅提供重新谈判机会或办理路线。F依据为当前到期续约结果与期限，没有推定失败后的持续保障，也未把后项基金/价格条件复制为Ec。',
    )),
    row(191, (1, 1, 1, 0, 0), (
        '当前把符合第九、十条规定的药品列入本轮目录调整范围，明确援引的实质对象条件包括不良反应、风险收益和不符合安全性条件，故该具体资格命题涉及药品安全。',
        '当前直接用符合第九、十条规定识别调整药品，所援引的对象条件包括临床价值不确切、可被更好替代及不符合有效性，故涉及药品效果/临床价值要求。',
        '当前以第九、十条的具体规定确定调整对象，援引内容含药物经济性及同治疗领域价格或费用明显偏高等药品经济条件，故计Ec。依据不是父段泛称基金承受能力。',
        '当前特定条文引用及已核验条文均未提出创新属性、创新研发支持或创新资格比较优势。',
        '父谓词为2022年药品目录调整范围，当前只是确定本轮调整/评审对象，未在本命题实际决定某药调出或给付变化；不能将引用条文的最终退出处置复制为当前保障结果。',
    ), (
        ('S', 'unit', '符合《基本医疗保险用药管理暂行办法》第九条、第十条规定的药品'),
        ('S', 'context', '其他不符合安全性、有效性、经济性等条件的药品'),
        ('E', 'unit', '符合《基本医疗保险用药管理暂行办法》第九条、第十条规定的药品'),
        ('E', 'context', '临床价值不确切,可以被更好替代的药品'),
        ('Ec', 'unit', '符合《基本医疗保险用药管理暂行办法》第九条、第十条规定的药品'),
        ('Ec', 'context', '价格或费用明显偏高且没有合理理由的药品'),
    ), issues=(
        '保留首次个人二元判断。这里“符合第九条、第十条规定”明确援引具体实质对象条件，S/E/Ec据此判1；没有从一般父段复制全部范围标签。父段恢复本轮调整范围这一谓词后，引用中的实际调出行为不构成当前直接退出决定，故F仍为0。',
        '新增逐条引文与来源证书复核了既有补充文本，未发现改变当前五维判断的新增实质要求。',
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

def write_new(path, obj):
    with path.open('x', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write('\n')

if __name__ == '__main__':
    import jsonschema
    packet_path = BASE / '补充材料-v11.json'
    schema_path = ROOT / '结果schema-v11.json'
    packet = json.loads(packet_path.read_text())
    assert packet['material_version'] == 'v11'
    assert [r['id'] for r in rows] == [r['id'] for r in packet['rows']]
    result = {
        'coder': 'A',
        'protocol_version': 'CAL-5D-20260926-v1.3',
        'operational_version': 'v1.4',
        'material_version': 'v11',
        'input_packet_sha256': sha(packet_path),
        'rows': rows,
    }
    jsonschema.validate(result, json.loads(schema_path.read_text()))
    evidence_audit = []
    for material, judgment in zip(packet['rows'], rows):
        contexts = list(strings(material['contexts'], 'contexts'))
        assert set(judgment['labels']) == set(DIMS)
        assert set(judgment['dimension_reasons']) == set(DIMS)
        assert all(type(v) is int and v in (0, 1) for v in judgment['labels'].values())
        assert all(judgment['dimension_reasons'][d].strip() for d in DIMS)
        assert bool(judgment['innovation_subtypes']) == (judgment['labels']['I'] == 1)
        assert bool(judgment['fairness_subtypes']) == (judgment['labels']['F'] == 1)
        assert judgment['safety_quality_basis'] == 'no_quality_basis'
        for d in DIMS:
            if judgment['labels'][d] == 1:
                assert any(e['dimension'] == d and e['source'] == 'unit' for e in judgment['evidence'])
        for e in judgment['evidence']:
            pool = [('text', material['text'])] if e['source'] == 'unit' else contexts
            matches = [{'field': p, 'start': s.index(e['quote']), 'end': s.index(e['quote']) + len(e['quote'])}
                       for p, s in pool if e['quote'] in s]
            assert matches, (judgment['id'], e)
            evidence_audit.append({'id': judgment['id'], **e, 'literal_contiguous_match': True, 'matches': matches})
    # Only byte hashes of A's immutable first submissions are read for a
    # before/after preservation check; their semantic results are not loaded.
    first_paths = [BASE / f'结果-{i:02d}.json' for i in range(1, 9)]
    preservation_before = {str(p): sha(p) for p in first_paths}
    result_path = BASE / '补料复读结果-v11.json'
    write_new(result_path, result)

    changes = {
        'coder': 'A', 'material_version': 'v11',
        'input_packet_sha256': sha(packet_path),
        'protocol_version': result['protocol_version'], 'operational_version': 'v1.4',
        'comparison_basis': '本人首次提交时保存的判断与本次独立复读；首次文件未重新载入语义内容。',
        'rows': [
            {
                'id': 'AV3-A-0003',
                'first_labels': dict.fromkeys(DIMS, '待定'),
                'reread_labels': rows[0]['labels'],
                'change': '完整材料使五维均可二元判读；首次待定不是0。S/E/Ec=1来自当前对第七条基本条件的明确实质援引；I/F=0不从申报身份及后项名称推定。',
                'new_material_used': packet['rows'][0]['contexts']['structured_following_units'] + packet['rows'][0]['contexts']['explicitly_cited_articles_v10'],
                'removed_text_relied_on': [],
                'quality_marker_change': ['undetermined', 'no_quality_basis'],
            },
            {
                'id': 'AV3-A-0155',
                'first_labels': dict(zip(DIMS, (0, 0, 0, 0, 1))),
                'reread_labels': rows[1]['labels'],
                'change': '五维、F access及S质量标记不变。完整实际列举及下一条边界现明确。结构字段补齐第五项；既有证书中已经有该句，不作为首次新增语义。',
                'field_repair_text': '(五)国家规定的应当直接调出的其他情形。',
                'next_boundary_text': '第十条    《药品目录》内的药品,符合以下情况之一的,经专家评审等规定程序后,可以调出《药品目录》:',
                'removed_text_relied_on': [],
            },
            {
                'id': 'AV3-A-0177',
                'first_labels': dict.fromkeys(DIMS, '待定'),
                'reread_labels': rows[2]['labels'],
                'change': '同时满足的完整5项主条件及2个预算分项补齐后，五维改为本人二元判断。F access来自当前既有谈判药品到期后两年续约的保障延续安排；经济后项不复制为当前Ec。',
                'new_material_used': packet['rows'][2]['contexts']['structured_following_units'],
                'removed_text_relied_on': [],
                'quality_marker_change': ['undetermined', 'no_quality_basis'],
            },
            {
                'id': 'AV3-A-0191',
                'first_labels': dict(zip(DIMS, (1, 1, 1, 0, 0))),
                'reread_labels': rows[3]['labels'],
                'change': '五维、空I/F子类及S质量标记不变。逐条明确引用材料核对既有第九、十条补充文本；当前仍是目录调整范围，不能改写为实际退出决定。',
                'new_source_certificate_texts': [a['text'] for a in packet['rows'][3]['contexts']['explicitly_cited_articles_v10']],
                'removed_text_relied_on': [],
            },
        ],
        'not_metric_driven': True,
    }
    changes_path = BASE / '补料复读变更说明-v11.json'
    write_new(changes_path, changes)
    preservation_after = {str(p): sha(p) for p in first_paths}
    assert preservation_before == preservation_after
    assert sha(packet_path) == result['input_packet_sha256']
    loaded_result = json.loads(result_path.read_text())
    jsonschema.validate(loaded_result, json.loads(schema_path.read_text()))
    assert loaded_result == result
    qa = {
        'coder': 'A', 'actual_identity': 'AI agent',
        'completed_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'material_version': 'v11', 'input_packet_sha256': sha(packet_path),
        'protocol_version': result['protocol_version'], 'operational_version': 'v1.4',
        'reread_scope': '本方4条当前text及全部递归contexts，含全部版本后缀、父对象、引用条文、实际后项和边界证书；不因某数组为空忽略其他字段。',
        'authorized_read_files_sha256': {
            str(p): sha(p) for p in (
                packet_path, ROOT / '补料任务说明-v11.json', schema_path,
                PROTOCOL / '完整五维手册-v1.3.md', PROTOCOL / '共用操作说明-v1.4.md'
            )
        },
        'first_submissions_hash_check': {
            'method': '只读本方8包字节SHA，在新增文件写入前后比较；未载入首次标签作新判读。',
            'unchanged': True, 'before': preservation_before, 'after': preservation_after,
        },
        'row_ids_in_input_order': [r['id'] for r in rows],
        'checks': {
            'schema': 'passed', 'actual_input_sha_binding': 'passed',
            'coverage_4_rows_20_dimensions_and_reasons': 'passed',
            'all_labels_binary': 'passed', 'current_unit_quote_for_each_one': 'passed',
            'all_quotes_literal_contiguous_without_normalization': 'passed',
            'I_F_subtype_presence_and_manual_basis': 'passed',
            'S_quality_marker_manual_review': 'passed',
            'original_eight_packets_preserved': 'passed',
        },
        'subtype_manual_review': {
            'innovation': '4条I均0，无创新子类；没有由新通用名、独家、名单身份推定创新。',
            'fairness': '0155为医保目录实际退出，0177为既有谈判药品保障续约，均只有access；0003与0191分别为申报资格、调整对象，无F子类。',
            'safety_quality': '0003和0191安全依据是明确基本安全条件/药品风险，不是药品质量扩展；其余S=0，四条均no_quality_basis。',
        },
        'material_gaps_remaining': [],
        'reading_boundary': {
            'other_coder_or_machine_or_statistics_read': False,
            'external_pdf_or_locator_files_opened': False,
            'source_identity_completely_blind_claimed': False,
            'source_pdf_independently_verified_by_coder': False,
            'note': '只在获授权材料包内阅读源文和证书，实际SHA核验对象为本方包/规定文件，未打开证书中的外部定位路径。',
        },
        'method': 'AI coder A本人逐条语义判读；程序只序列化手写结果、复制指定补文、核验ID/schema/逐字引文/SHA/子类字段一致性，不按词表或正则生成标签与理由。',
        'evidence_audit': evidence_audit,
        'output_files_sha256': {str(p): sha(p) for p in (result_path, changes_path)},
    }
    write_new(BASE / '补料复读QA-v11.json', qa)
    print(json.dumps({'status': 'passed', 'rows': len(rows), 'dimensions': len(rows)*len(DIMS), 'input_sha256': sha(packet_path), 'outputs': [str(result_path), str(changes_path), str(BASE / '补料复读QA-v11.json')]}, ensure_ascii=False))
