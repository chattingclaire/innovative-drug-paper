"""Read-only classifier review probes for the 04071 identified-risk path."""
import copy
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

TEXT = '(三)申办者应当记录已识别的风险和相应的缓解措施，并与参与采取措施或者受此类活动影响的人员沟通。'
PREV = '(二)风险控制应当与风险对试验参与者权益和安全，以及试验结果可靠性影响的重要性相称。申办者应当预先设定风险控制可接受范围。'
SCOPE = '第二条 本规范适用于经药品监督管理部门批准，为研制药品而进行的药物临床试验。'
BASE = {
    'text': TEXT, 'source_ref': {'sha256': 'a' * 64},
    'structure': {'component_id': 'A'},
    'contexts': [
        {'context_id': 'scope', 'kind': 'source_paragraph', 'text': SCOPE,
         'source_ref': {'sha256': 'a' * 64}, 'structure': {'component_id': 'A'}},
        {'context_id': 'risk', 'kind': 'preceding_paragraph', 'text': PREV,
         'source_ref': {'sha256': 'a' * 64}, 'structure': {'component_id': 'A'}},
    ],
}
CASES = [
    ('current_data_only_prefix', 'text', '(三)本项仅涉及试验结果可靠性，不包括参与者安全。申办者应当记录已识别的风险和相应的缓解措施，并与参与采取措施或者受此类活动影响的人员沟通。', 0),
    ('current_data_only_suffix', 'text', TEXT + '本项所称风险仅指数据质量风险，不含参与者安全风险。', 0),
    ('definition_disconnection', 'risk', PREV + '以下第三项仅记录数据可靠性风险，不适用前述参与者安全风险要求。', 0),
    ('definition_only_form_mentions', 'risk', '(二)风险控制应当与风险对试验参与者权益和安全的表述只是栏目标题，不构成实质要求；另一个栏目标题为“申办者应当预先设定风险控制可接受范围”。', 0),
    ('current_form_unquoted_colon', 'text', '(三)栏目名称：申办者应当记录已识别的风险和相应的缓解措施。', 0),
    ('current_form_then_actual', 'text', '(三)栏目名称：申办者应当记录已识别的风险和相应的缓解措施；申办者应当记录已识别的风险和相应的缓解措施，并沟通实际风险控制情况。', 1),
    ('current_actual_then_form', 'text', TEXT + '风险管理表格还应签字盖章。', 1),
    ('current_data_branch_then_safety_branch', 'text', '(三)数据记录部分仅涉及试验结果可靠性，不包括参与者安全；另针对前项的试验参与者安全风险，申办者应当记录已识别的风险和相应的缓解措施，并向实施人员沟通。', 1),
    ('scope_excludes_current_item', 'scope', SCOPE + '但第三项仅适用于医疗器械试验，不适用于上述药物临床试验。', 0),
    ('scope_other_source', 'scope_sha', 'b' * 64, 0),
    ('scope_other_component', 'scope_component', 'B', 0),
    ('definition_other_source', 'risk_sha', 'b' * 64, 0),
    ('definition_other_component', 'risk_component', 'B', 0),
    ('ambiguous_duplicate_scope', 'duplicate_scope', None, 0),
    ('ambiguous_duplicate_definition', 'duplicate_risk', None, 0),
]
results = []
for name, change, value, expected in CASES:
    unit = copy.deepcopy(BASE)
    if change == 'text':
        unit['text'] = value
    elif change in ('risk', 'scope'):
        unit['contexts'][int(change == 'risk')]['text'] = value
    elif change.endswith('_sha'):
        unit['contexts'][int(change.startswith('risk'))]['source_ref']['sha256'] = value
    elif change.endswith('_component'):
        unit['contexts'][int(change.startswith('risk'))]['structure']['component_id'] = value
    elif change.startswith('duplicate_'):
        extra = copy.deepcopy(unit['contexts'][int(change.endswith('risk'))])
        extra['context_id'] += '-duplicate'
        unit['contexts'].append(extra)
    view = RelationView(unit)
    decision = judge(view)
    validate_decisions(view.unit, decision)
    actual = decision['S']['value']
    results.append({'name': name, 'expected': expected, 'actual': actual,
                    'passed': actual == expected, 'input': unit, 'decision': decision['S']})
report = {'purpose': 'synthetic code-review development probes, not independent empirical validation',
          'dimensions_sha256': hashlib.sha256((HERE / 'code/dimensions.py').read_bytes()).hexdigest(),
          'passed': sum(r['passed'] for r in results), 'total': len(results), 'cases': results}
(HERE / 'round4-safety-review-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({k: report[k] for k in ('dimensions_sha256', 'passed', 'total')} | {
    'failed': [r['name'] for r in results if not r['passed']]}, ensure_ascii=False))
