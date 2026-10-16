"""Manual-grounded explicit drug relations; exposed-development candidate.

No IDs, departments, filenames, reference vectors or metric targets are read.
Patterns apply to current-unit predicates and retain literal current evidence.
"""
import re
from rule_support import RuleView
from rules_se import S_BASIS, E_BASIS
from rules_ec import EC_BASIS
from rules_if import BASIS_F

BASES = {'S': S_BASIS, 'E': E_BASIS, 'Ec': EC_BASIS, 'F': BASIS_F}


def apply(v, dimension, name, pattern, subtype=None):
    if name == 'explicit_patient_unmet_clinical_need' and not v.drug_scope:
        return
    for m in re.finditer(pattern, v.text):
        # Every pattern includes an actual drug object or requires bound drug scope. It does
        # not infer a dimension from a title or from all surrounding research.
        v.add('V35_'+dimension+'_'+name, dimension, *m.span(), subtype,
              BASES[dimension], safety_basis='other_safety' if dimension == 'S' else None)


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    v = RuleView(record, result)
    apply(v, 'S', 'medication_error_prevention',
          r'(?:避免|防止|预防|减少|防范)[^。；;，,]{0,12}(?:用错药|错用药|用药差错|药物误用|误用药物)')
    apply(v, 'E', 'long_term_treatment_effect_assessment',
          r'(?:评价|评估|比较|分析|研究|验证|证明)[^。；;，,]{0,16}'
          r'(?:药物|药品|该药|本药)(?:的)?(?:长期|短期|远期|近期|持续)?(?:治疗|预防)?(?:效果|疗效|获益)')
    apply(v, 'E', 'drug_economic_effect_enumeration',
          r'(?:分析|测算|评价|评估|比较)[^。；;]{0,20}(?:药品|药物)(?:的)?'
          r'(?:成本|费用)[、，,](?:效果|效用|治疗效益)')
    apply(v, 'Ec', 'reference_drug_price_calculation',
          r'(?:参照药|参考药|对照药)[^。；;]{0,60}'
          r'(?:取|采用|按照|参照|计算)[^。；;]{0,50}'
          r'(?:加权平均价|平均价格|最低挂网价|最高挂网价|最低价格|最低中标价)')
    apply(v, 'F', 'explicit_patient_unmet_clinical_need',
          r'(?:患者|人群)[^。；;，,]{0,16}未(?:被|获)?满足(?:的)?(?:临床|治疗|用药)需求|'
          r'(?:未(?:被|获)?满足(?:的)?(?:临床|治疗|用药)需求)[^。；;，,]{0,16}(?:患者|人群)',
          'access')
    apply(v, 'F', 'actual_formulary_limit_relaxation',
          r'(?:遴选|配备|供应)[^。；;]{0,60}(?:药品|用药)[^。；;]{0,80}'
          r'(?:可不受|不受|取消|放宽)[^。；;]{0,25}(?:药品总品种数|一品两规)[^。；;]{0,20}'
          r'(?:限制|增加用药范围)', 'access')
    return result
