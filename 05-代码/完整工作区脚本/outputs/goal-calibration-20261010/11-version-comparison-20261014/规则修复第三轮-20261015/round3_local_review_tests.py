"""Independent local-relation review: forms, mixed clauses and broken scope."""
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'code'))
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions


def sample(text, prefix, kind='paragraph'):
    return {
        'text': text,
        'source_ref': {'sha256': 'a' * 64, 'locator': {'paragraph_ids': ['p1']}},
        'structure': {'component_id': 'A'},
        'contexts': [{
            'context_id': 'SYNTH-local-review', 'kind': kind,
            'text': prefix + text if kind == 'paragraph' else prefix,
            'source_ref': {'sha256': 'a' * 64, 'locator': {'paragraph_id': 'p1'}},
            'structure': {'component_id': 'A', 'paragraph_id': 'p1'},
        }],
    }


base = '药品审评中心根据申报品种、工艺、设施等因素，基于风险决定是否启动药品注册生产现场核查。'
route = '45日通道是审评机构将现有审评审批资源向符合条件的创新药临床试验申请倾斜的改革举措。'
safety = '加强医疗机构药品安全管理。建立覆盖药品采购、贮存、调配、使用全过程的监测系统。'
ftext = '因此，原则上，单臂试验适用于治疗严重危及生命且缺乏有效标准治疗手段的难治疾病，并在早期研究中初步显示突出疗效的单药治疗。'
fpre = '晚期无药可治的肿瘤患者存在急迫的治疗需求；一旦早期数据提示突出疗效，则希望入组的受试者均能接受试验治疗，得到潜在的治疗机会，因此不再要求采用安慰剂对照，可以采用单臂试验设计。'

# Expected zero means this complete synthetic record lacks a substantive
# relation, not that every restriction/termination should be zero.
cases = [
    ('I4_form_title', '将“对于创新药，应当进行药品注册生产现场核查”作为药品申报系统的栏目标题。', base, 'preceding_paragraph', 'I', 0),
    ('I3_form_choice', '申请人应当根据品种研发的实际需求，填写“选择45日通道或者60日默示许可”的栏目并上传文件。', route, 'paragraph', 'I', 0),
    ('S_negated_scope', '遵循近效期先出的原则，避免出现过期药品。', '本段并非为加强医疗机构药品安全管理，也不建立覆盖药品采购、贮存、调配、使用全过程的监测系统，仅为减少库存损失。', 'paragraph', 'S', 0),
    ('F_explicit_disconnection', ftext, fpre + '但上述治疗机会安排不适用于以下对象。', 'paragraph', 'F', 0),
    ('I4_mixed_actual_then_form', '对于创新药，应当进行药品注册生产现场核查，并上传核查记录。', base, 'preceding_paragraph', 'I', 1),
    ('I3_mixed_actual_then_form', '申请人应当根据品种研发的实际需求，合理选择45日通道，并登记通道名称。', route, 'paragraph', 'I', 1),
    ('S_mixed_actual_then_form', '遵循近效期先出的原则，避免出现过期药品，并上传管理记录。', safety, 'paragraph', 'S', 1),
    ('F_mixed_actual_then_form', ftext + '申报材料还应签字盖章。', fpre, 'paragraph', 'F', 1),
    ('I4_mixed_form_then_actual', '将“对于创新药，应当进行药品注册生产现场核查”作为栏目标题；对于创新药，应当进行药品注册生产现场核查，并上传核查记录。', base, 'preceding_paragraph', 'I', 1),
    ('I3_mixed_form_then_actual', '根据药品研发的实际需求，填写“选择45日通道”的栏目；申请人应当根据品种研发的实际需求，合理选择45日通道。', route, 'paragraph', 'I', 1),
    ('I4_quote_only_upload', '上传写有“对于创新药，应当进行药品注册生产现场核查”的文件。', base, 'preceding_paragraph', 'I', 0),
    ('S_scope_switched_to_inventory', '遵循近效期先出的原则，避免出现过期药品。', safety + '以下仅讨论库存报损财务核算，不涉及上述药品安全管理措施。', 'paragraph', 'S', 0),
    ('F_need_object_switched', ftext, fpre.replace('；一旦', '；这里另讨论有有效标准治疗药物可选的患者，一旦'), 'paragraph', 'F', 0),
    ('S_quote_only_upload', '上传写有“遵循近效期先出的原则，避免出现过期药品”的文件。', safety, 'paragraph', 'S', 0),
    ('S_quote_only_title', '将“遵循近效期先出的原则，避免出现过期药品”作为药品库存系统的栏目标题。', safety, 'paragraph', 'S', 0),
    ('S_mixed_form_then_actual', '将“遵循近效期先出的原则，避免出现过期药品”作为栏目标题；遵循近效期先出的原则，避免出现过期药品，并上传管理记录。', safety, 'paragraph', 'S', 1),
]
results = []
for name, text, prefix, kind, dimension, expected in cases:
    view = RelationView(sample(text, prefix, kind))
    decisions = judge(view)
    validate_decisions(view.unit, decisions)
    actual = decisions[dimension]['value']
    results.append({
        'name': name, 'text': text, 'prefix': prefix, 'kind': kind,
        'dimension': dimension, 'expected': expected, 'actual': actual,
        'passed': actual == expected, 'basis_path': decisions[dimension]['basis_path'],
        'reason': decisions[dimension]['reason'],
    })
report = {
    'purpose': 'synthetic independent code-review probes; development regression, not independent empirical validation',
    'dimensions_sha256': hashlib.sha256((HERE / 'code/dimensions.py').read_bytes()).hexdigest(),
    'passed': sum(r['passed'] for r in results), 'total': len(results), 'cases': results,
}
(HERE / 'round3-local-review-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({**{k: report[k] for k in ['dimensions_sha256', 'passed', 'total']}, 'failed': [r['name'] for r in results if not r['passed']]}, ensure_ascii=False))
