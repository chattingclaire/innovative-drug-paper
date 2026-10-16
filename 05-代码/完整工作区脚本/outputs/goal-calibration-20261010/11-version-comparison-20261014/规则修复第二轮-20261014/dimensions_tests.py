"""Constructed semantic boundary controls; not a held-out validation sample."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'code'))
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions

CASES = [
    ('price_ceiling_cannot', '药品供应价格不能超过竞价报价。', {'Ec': 1}),
    ('price_ceiling_must_not', '向医疗机构供应药品的价格不得超过承诺报价。', {'Ec': 1}),
    ('price_reduction_bound', '合理控制谈判药品降价幅度。', {'Ec': 1}),
    ('administrative_file_redaction', '药品申报幻灯片提交两个版本，版本二删去经济性信息，分别命名。', {'Ec': 0}),
    ('substantive_evaluation_with_file_name', '药品申报幻灯片应分析经济性信息，并按要求命名。', {'Ec': 1}),
    ('price_content_and_redacted_name', '应提供药品价格信息，材料命名为公开版本，不含企业名称。', {'Ec': 1}),
    ('risk_content_and_redacted_name', '应提交该药不良反应证据，材料命名为公开版本，不含企业名称。', {'S': 1}),
    ('effect_content_and_redacted_name', '应提供该药疗效证据，材料命名为公开版本，不含企业名称。', {'E': 1}),
    ('deferred_payment_rule', '药品支付标准的调整办法另行制定。', {'Ec': 0}),
    ('deferred_plus_current_price', '药品支付标准的调整办法另行制定。当前药品价格不得超过原报价。', {'Ec': 1}),
    ('deferred_but_specified_price', '规定药品价格不得超过竞价报价的细则另行制定。', {'Ec': 1}),
    ('deferred_but_price_cap', '对药品价格实施上限控制的规则另行制定。', {'Ec': 1}),
    ('deferred_but_specified_affordability', '要求药品费用不超过患者家庭年收入百分之十的办法另行制定。', {'Ec': 1}),
    ('safety_case_content_with_window', '该药死亡病例和严重不良事件病例的报告小结，应包括截止日期内已完成研究的相关病例。', {'S': 1}),
    ('drug_device_improvement', '改进药品给药器的操作步骤，以降低患者操作负担。', {'I': 1}),
    ('injection_step_improvement', '药品注射步骤应简化，减少患者操作困难。', {'I': 1}),
    ('device_cosmetic_change', '药品给药器应改变包装颜色，以满足一般外观偏好。', {'I': 0}),
    ('device_general_convenience', '药品注射器应易于把持。', {'I': 0}),
    ('patient_affordability', '应评价药品费用对低收入患者家庭的负担。', {'F': 1}),
    ('institution_cost_is_not_patient_equity', '应评价药品费用对医疗机构的负担。', {'Ec': 1, 'F': 0}),
    ('income_data_alone', '药品研究登记患者家庭收入资料。', {'F': 0}),
    ('ordinary_filing_support', '创新药申报材料可通过网站提交，并按登记时间顺序归档。', {'I': 0, 'F': 0}),
]
results = []
for name, text, expected in CASES:
    view = RelationView({'text': text, 'contexts': []})
    decisions = judge(view)
    validate_decisions(view.unit, decisions)
    actual = {d: v['value'] for d, v in decisions.items()}
    results.append({'name': name, 'text': text, 'expected': expected,
                    'actual': actual, 'passed': all(actual[d] == v for d, v in expected.items())})
output = {'purpose': 'synthetic development controls; not independent validation',
          'code_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (HERE / 'code').glob('*.py')}, 'cases': results}
(HERE / 'dimensions-tests.json').write_text(json.dumps(output, ensure_ascii=False, indent=2))
failed = [r for r in results if not r['passed']]
print(json.dumps({'passed': len(results) - len(failed), 'total': len(results), 'failed': failed}, ensure_ascii=False))
if failed:
    raise SystemExit(1)
