"""Seal exhaustive eligible change review, without reference/human labels."""
from pathlib import Path
from datetime import datetime, timezone, timedelta
import hashlib
import json

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
DEV = OUT.parent / 'rules-v37.2-development'
BASE_DIR = ROOT / 'outputs/coding-revision-20261007-r3/rules-v36.2-development'
EXPECTED_FREEZE = '166d8d96781248b5f0f09edeb2433e8be3452c08aefa013ea2dacd500e3115ee'
PREFLIGHT = OUT.parent / 'independent-rule-v37.2-review/independent_preflight_v37_2.json'
EXPECTED_PREFLIGHT = 'ac5b130db5cd508a27ea6e4502b44ff721983d8fe9364224f55427c0cf7caec3'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def save(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def main():
    freeze_path = DEV / 'candidate_freeze.json'
    assert sha(freeze_path) == EXPECTED_FREEZE
    assert sha(PREFLIGHT) == EXPECTED_PREFLIGHT
    freeze = json.loads(freeze_path.read_text())
    current = json.loads((OUT / 'all_predictions_material_v14_shadow.run.json').read_text())
    baseline = json.loads((BASE_DIR / 'all_predictions_material_v14.run.json').read_text())
    summary = json.loads((OUT / 'mechanical_comparison_summary.json').read_text())
    projection_path = OUT / 'nonreserved_changes_manual_review_projection.json'
    projection = json.loads(projection_path.read_text())
    checked = {}
    for field in ('production_code_sha256', 'controls_and_review_sha256', 'test_script_sha256'):
        for path, expected in freeze[field].items():
            actual = sha(Path(path))
            assert actual == expected, path
            checked[path] = actual
    assert len(checked) == 57
    assert current['candidate_freeze_sha256'] == EXPECTED_FREEZE
    assert current['n'] == baseline['n'] == 4924
    assert current['pending_n'] == baseline['pending_n'] == 0
    assert current['input_sha256'] == baseline['input_sha256'] == summary['inputs_sha256']
    assert current['actual_source_and_candidate_sha256'] == baseline['actual_source_and_candidate_sha256']
    assert current['component_settings'] == baseline['component_settings']
    assert not current['reference_labels_loaded'] and not baseline['reference_labels_loaded']
    assert sha(OUT / 'all_predictions_material_v14_shadow.jsonl') == current['prediction_sha256']
    assert sha(BASE_DIR / 'all_predictions_material_v14.jsonl') == baseline['prediction_sha256']
    assert summary['manual_review_projection_n'] == len(projection) == 5
    # These are conclusions from reading EVERY eligible changed unit, not a
    # selected evaluation sample or replacement gold labels.
    decisions = {
        'RECODE25-00035': {
            'dimension': 'I', 'change': '0->1', 'assessment': '符合手册，修复漏判',
            'manual_basis': 'v1.4 创新性I第1项；共同判断步骤的对象消解边界',
            'reason': '当前单元明确由药审中心按咨询问题安排相关审评人员沟通，并基于研究资料对下一步研究方案给出意见建议；这既有人员资源，又有科学方案指导。实际运行认证的突破性治疗程序适用范围明确为创新药/改良型新药等，语境仅用于消解对象。当前命题并非仅申请渠道、沟通形式或截止时间。',
            'relationship_check': '药审中心为安排人员的施事，随后“同时基于……对……提出……”为同施事承接；没有申请人自提建议的主语切换，建议宾语为研究方案本身。',
            'evidence_rule': 'V37_I_actual_professional_scientific_guidance',
            'source_scope_verified_in_actual_pipeline': True,
        },
        'RECODE25-00741': {
            'dimension': 'Ec', 'change': '0->1', 'assessment': '符合手册，修复漏判',
            'manual_basis': 'v1.3 经济性Ec；v1.4 其余三维沿用说明',
            'reason': '当前单元明确在参照药纳入集采的条件下，取药品集采中选最高价。取值动词、药品对象和价格量均在当前单元中；完整问答语境也明确这是参照药品价格取值，不是采购流程或条款编排。',
            'relationship_check': '“取”的完整宾语是“药品集采中选最高价”；没有跨逗号把其他采购主体借成药品，没有条款/标题等后续名词改变价格宾语。',
            'evidence_rule': 'V37_Ec_current_drug_procurement_price_selection',
        },
        'RECODE25-01378': {
            'dimension': 'I', 'change': '1->0', 'assessment': '符合手册，删除宗旨误报',
            'manual_basis': 'v1.4 创新性I第5项',
            'reason': '完整当前单元及给定同段仅陈述促进创新/完善制度的宗旨、制定实施办法、发布和施行。没有给予特定权利、期限、适用范围或实际研发资源；不能将文件名称中的试验数据保护当作已经陈述实体保护权利。',
            'relationship_check': '旧证据唯一来源为“为促进……完善……”宗旨短语；本次删除的全部受影响实际单元只有此一条，已完整审读，未发现随发布一并陈述的实体创新措施。',
            'removed_legacy_rule': 'V27_I_data_protection_purpose',
            'all_purpose_deletion_affected_units_reviewed': True,
        },
        'RECODE25-01388': {
            'dimension': 'I', 'change': '0->1', 'assessment': '符合手册，修复漏判',
            'manual_basis': 'v1.4 创新性I第3项',
            'reason': '当前条款以符合条件的化学药品和生物制品获批上市为条件，对申请人自行取得且未披露的试验及其他数据实施保护，并明确最长不超过6年的期限。这是专有试验数据权利范围、条件及期限，不是一般保密、文件保存或递交程序。',
            'relationship_check': '保护施事、药品条件、申请人专有数据宾语及量化期限形成当前单元内连续权利关系；不依靠文件标题推断。',
            'evidence_rule': 'V37_I_proprietary_trial_data_quantified_right',
        },
        'RECODE25-03574': {
            'dimension': 'I', 'change': '0->1', 'assessment': '符合手册，修复漏判',
            'manual_basis': 'v1.4 创新性I第2项及共同判断步骤；v1.3 新品种、剂型、规格与属性',
            'reason': '“口服制剂改注射制剂”明确从已有口服制剂改为注射制剂的具体产品属性变化。严格控制和不批准是对该变化的限制性评价，手册不要求变化已经证明优效或获准；当前实质不是仅列剂型名称。',
            'relationship_check': '改动两端均为具体且不同的制剂类型，改变关系在当前单元；不从邻段支持罕见病研发复制I。',
            'evidence_rule': 'V37_I_explicit_between_formulation_change',
        },
    }
    assert set(decisions) == {r['id'] for r in projection}
    reviews = []
    for row in projection:
        d = decisions[row['id']]
        assert row['changed_dimensions'] == [d['dimension']]
        reviews.append({'id': row['id'], **d, 'unit_text': row['unit_text'],
                        'machine_changes': row['machine_changes'],
                        'actual_evidence': row['new_changed_dimension_evidence'],
                        'old_evidence': row['old_changed_dimension_evidence'],
                        'necessary_context_reviewed': True})
    exposed_path = OUT / 'previously_exposed_01353_flagged_check.json'
    exposed = json.loads(exposed_path.read_text())
    assert exposed['id'] == 'RECODE25-01353' and exposed['root_authorized_exception']
    assert exposed['machine_change'] == {'v36.2': 0, 'v37.2': 1}
    exposed_review = {
        'id': 'RECODE25-01353', 'dimension': 'S', 'change': '0->1',
        'exposure_flag': 'previously_exposed_development_case_not_independent_validation',
        'manual_basis': 'v1.3 安全性S；v1.4 其余三维沿用说明',
        'assessment': '符合手册，修复已暴露案例漏判',
        'reason': '已暴露原句在药品调配、交接、发放使用场景下要求医务人员互相提醒、向患者开展用药教育并防范误选误用，明确为用药错误预防。实际流水线发出完整连续关系引文，不是泛称误用或科研经费误用。',
        'flagged_check_sha256': sha(exposed_path),
        'independent_validation_claimed': False,
    }
    report = {
        'status': 'shadow_completed_eligible_change_review_completed_not_adopted',
        'reviewed_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'reviewer': '/root/rule_repair37 (candidate author; development review)',
        'candidate_freeze_sha256': EXPECTED_FREEZE,
        'independent_preflight_sha256': EXPECTED_PREFLIGHT,
        'shared_input_same_as_v36_2': True,
        'actual_source_and_candidate_bindings_same_as_v36_2': True,
        'all_57_frozen_artifact_bindings_unchanged_after_shadow': True,
        'shadow_predictions_sha256': current['prediction_sha256'],
        'baseline_predictions_sha256': baseline['prediction_sha256'],
        'mechanical_comparison_summary_sha256': sha(OUT / 'mechanical_comparison_summary.json'),
        'review_projection_sha256': sha(projection_path),
        'review_scope': 'All 5 nonreserved changed units, every changed dimension, full original unit and necessary supplied/authenticated context; no favorable-ID sampling.',
        'nonreserved_changed_units_n': 5,
        'reviewed_nonreserved_changed_units_n': len(reviews),
        'nonreserved_review_findings': reviews,
        'reserved267_handling': 'All 267 excluded from ordinary manual projection; only aggregate machine change counts. Prior exposed 01353 is a separately flagged, root-authorized exception, never independent validation.',
        'previously_exposed_exception_review': exposed_review,
        'unexpected_changed_units_n': 0,
        'reverse_change_summary': {'I_1_to_0_n': 1, 'all_reverse_changes_reviewed': True, 'assessment': 'Only general-purpose publication I false positive removed.'},
        'regressions_identified_among_reviewed_changes_n': 0,
        'scope_limit': 'This is exhaustive review of changed outputs only; it is not a full-corpus gold audit or an independent validation estimate. Unchanged units were not individually adjudicated.',
        'rule_changes_after_shadow': False,
        'reference_or_human_labels_loaded': False,
        'scores_or_kappa_read_or_computed': False,
        'old_adopted_predictions_or_reference_labels_modified': False,
        'formal_adoption_performed': False,
    }
    save('exhaustive_nonreserved_change_review.json', report)
    lines = [
        '# v37.2 全量影子运行及变化审读', '',
        '状态：完成开发影子运行与全部允许审读的变化复核；未正式采用。', '',
        '冻结候选与独立预检哈希均吻合，运行后57项冻结绑定未变。4,924条全部得到五维二元预测，pending=0。输入、原始来源及候选材料绑定、运行组件与v36.2完全相同。未读取A/C/T或新旧真人标签、提交、分数及κ。', '',
        '与v36.2相比，6个单元的6个维度格改变：I 0→1三条、I 1→0一条、Ec 0→1一条、S 0→1一条；E/F无改变。267个预留家族成员均排除在常规逐条审读投影之外；其中只有一条机器变化。01353依root授权作为先前已暴露开发案例单列核查，不用于独立验证。', '',
        '|全部非保留变化|维度与方向|完整命题核查结论|',
        '|---|---|---|',
    ]
    for r in reviews:
        lines.append(f"|{r['id']}|{r['dimension']} {r['change']}|{r['reason']}|")
    lines.extend([
        '', '5条非保留变化均逐条读完当前完整原句和必要语境。唯一反向变化01378亦完整审读，未误删实体制度措施。已暴露01353的S新增依据为药品使用场景下明确防范误选误用，实际流水线发出完整证据。此次改变范围内未识别新增误报或回归；未变化单元没有逐条裁决，不能据此声称全语料无错误。', '',
        '代码保持冻结，未据任何得分调参、补标签或选择版本。本文为候选作者的开发审读，不能替代后续独立评价。', '',
        f"- 完整五维预测：`all_predictions_material_v14_shadow.jsonl`，SHA256 `{current['prediction_sha256']}`。",
        '- 全变化ID/维度清单：`changes_all_ids_dimensions.json`（预留成员不列文本及预测值）。',
        '- 纯机械计数：`mechanical_comparison_summary.json`。',
        '- 逐例证据与理由：`exhaustive_nonreserved_change_review.json`。',
        '- 已暴露例外：`previously_exposed_01353_flagged_check.json`。',
    ])
    (OUT / '全量影子运行与全部变化审读.md').write_text('\n'.join(lines) + '\n')
    seal_names = [p.name for p in OUT.iterdir() if p.is_file() and p.name != 'shadow_review_artifact_seal.json']
    save('shadow_review_artifact_seal.json', {
        'status': 'sealed_shadow_only_not_adopted',
        'candidate_freeze_sha256': EXPECTED_FREEZE,
        'frozen_artifacts_verified_n': len(checked),
        'artifacts_sha256': {name: sha(OUT / name) for name in sorted(seal_names)},
        'reference_or_human_labels_loaded': False,
        'scores_or_kappa_read_or_computed': False,
    })
    print(json.dumps({'reviewed_nonreserved_n': len(reviews), 'flagged_preexposed_exception_n': 1,
                      'regressions_identified_in_changed_outputs_n': 0,
                      'review_sha256': sha(OUT / 'exhaustive_nonreserved_change_review.json'),
                      'seal_sha256': sha(OUT / 'shadow_review_artifact_seal.json'),
                      'shadow_predictions_sha256': current['prediction_sha256']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
