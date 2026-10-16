"""Seal existing bounded outputs and completed AI audits. No model/statistical calls."""
import collections
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
REVIEW = BASE / 'semantic-review'
def read(path):
    return json.loads(path.read_text())
def bind(path):
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
def save(path, obj):
    assert not path.exists(), path
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

tech_path = BASE / 'execution-audit/candidate07_technical_QA.json'
comparison_path = BASE / 'execution-audit/candidate07_all240_comparison_REDACTED_PRIVATE.json'
controls_path = BASE / 'execution-audit/candidate07_all106_controls_PRIVATE.json'
primary_path = REVIEW / 'primary_complete240_semantic_review_PRIVATE.json'
reconciliation_path = REVIEW / 'independent9_reconciliation_addendum_PRIVATE.json'
independent9_path = REVIEW / 'independent-additional9/independent_additional9_full5_semantic_review_PRIVATE.json'
independent106_path = REVIEW / 'independent-controls/candidate07_actual106_independent_semantic_review.json'
root20_path = REVIEW / 'root-known20-review/root_20_unit_full_dimension_review.json'
technical_reverification_path = REVIEW / 'frozen_execution_dependency_reverification.json'

tech = read(tech_path)
comparison = read(comparison_path)['rows']
controls = read(controls_path)['tests']
primary = read(primary_path)
reconciliation = read(reconciliation_path)
independent106 = read(independent106_path)
root20 = read(root20_path)
rows = reconciliation['all240_final_AI_review_rows']
assert len(rows) == len({r['id'] for r in rows}) == 240
assert [r['id'] for r in rows] == [r['id'] for r in comparison]
assert len(controls) == len(independent106['reviews']) == 106
assert [r['input']['id'] for r in controls] == [r['id'] for r in independent106['reviews']]
assert independent106['source_sha256'] == bind(controls_path)['sha256']
assert tech['actual_logical_requests'] == tech['actual_attempts'] == 15
assert tech['all_selected_raw_bound_to_unique_completed_agent_message']
assert tech['first_technically_valid_selection_verified']
assert root20['required_cell_pass_n'] == 15 and root20['required_cell_fail_n'] == 4
assert all(len(r['five_dimension_review']) == 5 for r in rows)
assert all(len(r['each_dimension']) == 5 for r in independent106['reviews'])
assert all(r['full_five_dimension_actual_reasons_evidence_subtypes_quality_read'] for r in independent106['reviews'])
assert all(r['F_I_subtypes_independently_reviewed'] and r['S_quality_basis_independently_reviewed'] for r in independent106['reviews'])

by = {r['id']: r for r in comparison}
clear = []
boundaries = []
for row in rows:
    for dim, annotation in row['five_dimension_review'].items():
        item = {'id': row['id'], 'dimension': dim, 'actual07': annotation['actual'], 'audit_annotation': annotation}
        assert annotation['actual'] == by[row['id']]['candidate07_intact_actual_row']['labels'][dim]
        if annotation['review_status'].startswith('confirmed'):
            item['historical_actual_labels_not_truth'] = {k: v['labels'][dim] for k, v in by[row['id']]['historical_intact_rows'].items()}
            item['vs06'] = 'new_regression' if item['historical_actual_labels_not_truth']['candidate06_intact_actual_rows'] != annotation['actual'] else 'persistent'
            clear.append(item)
        elif 'boundary' in annotation['review_status']:
            boundaries.append(item)
assert len(clear) == 8 and len(boundaries) == 22
assert collections.Counter(r['vs06'] for r in clear) == {'new_regression': 4, 'persistent': 4}

label_changes = {}
for history in comparison[0]['historical_intact_rows']:
    counts = collections.Counter()
    unit_n = 0
    for row in comparison:
        changed = [d for d in ['S', 'E', 'Ec', 'I', 'F'] if row['candidate07_intact_actual_row']['labels'][d] != row['historical_intact_rows'][history]['labels'][d]]
        counts.update(changed)
        unit_n += bool(changed)
    label_changes[history] = {'units': unit_n, 'dimension_cells': sum(counts.values()), 'dimensions': dict(counts)}

control_diffs = [{'id': r['input']['id'], 'dimensions': r['mechanical_different_dimensions']} for r in controls if r['mechanical_different_dimensions']]
assert len(control_diffs) == 4
control_disputes = [
    {'id': 'C03-CONTROL-003', 'dimension': 'F', 'frozen_expected': 0, 'actual07': 1,
     'lead_AI_opinion': 0, 'independent_AI_opinion': 1,
     'lead_reason': '当前缩短审批、争取上市及满足更多患者的一般目的，未直接陈述治疗获取缺口或具体保障安排；按v1.3:55与v1.4:26倾向0。并非所有F均须缺口，争点是此一般上市目的是否已构成实质获取安排。',
     'independent_reason': '审批缩短明确连到更快上市及更多患者用药，解释为实际可及支持1。',
     'status': 'FROZEN_EXPECTATION_MISMATCH_AND_UNRESOLVED_SEMANTIC_REVIEW_DISAGREEMENT'},
    {'id': 'C05-NEW-012', 'dimension': 'Ec', 'frozen_expected': 0, 'actual07': 1,
     'lead_AI_opinion': 0, 'independent_AI_opinion': 1,
     'lead_reason': '保障协议与原给付条件继续适用明确F，但未具体说明药费、支付标准或费用责任；按v1.3:35-37倾向Ec0。',
     'independent_reason': '给付条件继续适用解释为当前实质支付条件，支持Ec1。',
     'status': 'FROZEN_EXPECTATION_MISMATCH_AND_UNRESOLVED_SEMANTIC_REVIEW_DISAGREEMENT'}]

source_paths = [BASE/'design_freeze.json', BASE/'root_bounded_execution_authorization.json',
    BASE/'predeclared_acceptance_PROPOSED.json', tech_path, comparison_path, controls_path,
    primary_path, reconciliation_path, independent9_path, REVIEW/'independent-additional9/precision_addendum.json',
    independent106_path, root20_path, REVIEW/'root-known20-review/formal_projection_confirmation_addendum.json',
    REVIEW/'interim_to_formal_mandatory30_equality_QA.json',
    REVIEW/'postexecution_manual_precision_and_root20_status_addendum.json', technical_reverification_path,
    BASE/'execution-audit/candidate07_human_review_redaction_metadata.json']
source_bindings = [bind(p) for p in source_paths]
report = {
    'status': 'FINAL_CANDIDATE07_SEMANTIC_GATE_FAIL_NOT_ADOPTED',
    'created_at_UTC': datetime.now(timezone.utc).isoformat(),
    'review_identity': 'AI audit of exposed development units and synthetic controls; not new human coding, gold truth, or independent validation.',
    'execution': {'requested_model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'scope': [240,62,24,20],
        'logical_requests': 15, 'attempts': 15, 'each_attempt01_selected': True, 'technical_retries': 0,
        'semantic_retries': 0, 'tool_calls': 0, 'technical_gate': 'PASS',
        'raw_unique_completed_event_and_first_valid_selection_bound': True,
        'provider_snapshot_or_randomness_isolation_claimed': False},
    'semantic_gate': {'result': 'FAIL', 'predeclared_required_cells_pass': 15, 'predeclared_required_cells_fail': 4,
        'old06_eight_errors_resolved': 7, 'old06_eight_errors_total': 8,
        'old06_nine_fixed_cells_preserved': 7, 'old06_nine_fixed_cells_total': 9,
        'additional_known_checks_resolved': 1, 'additional_known_checks_total': 2,
        'four_fixed_gate_failures': ['RECODE25-00964 Ec', 'RECODE25-01768 S', 'RECODE25-01955 I', 'RECODE25-03712 I'],
        'all_other_changes_without_new_confirmed_error': False,
        'all_controls_pass': False,
        'boundary_note_does_not_exempt_known_error': True},
    'development_coverage': {'complete_units': 240, 'explicit_dimension_reviews': 1200,
        'all_output_fields_change_projection_units': 240, 'label_change_counts_not_performance': label_changes,
        'all_current_text_and_unique_given_NONMASKED_contexts_read': True,
        'all_five_reasons_evidence_F_I_subtypes_S_quality_issue_records_read': True,
        '51_units_have_mechanically_masked_context_text': True,
        'formal30_equals_interim30_entire_object_and_source_hash': True,
        'all_same_label_historical_known_items_forced_into_review': True,
        'annotation_counts_not_accuracy': reconciliation['all240_explicit_dimension_classification_counts'],
        'primary_previous_findings_immutable_revisions_additive': True},
    'clear_development_manual_conflicts': clear,
    'development_boundaries_NOT_FORCED': boundaries,
    'synthetic_controls': {'n': 106, 'dimension_cells_read': 530, 'new20_and_all100_dimensions_supported': True,
        'mechanical_mismatch_cases': control_diffs, 'frozen_nonboundary_inherited_label_matches': 82,
        'frozen_nonboundary_inherited_cases': 85,
        'predeclared_inherited_label_gate': 'FAIL_WITHOUT_CHANGING_EXPECTATIONS',
        'independent_review_summary_preserved': independent106['semantic_summary'],
        'joint_clear_conflict': {'id': 'C05-NEW-015', 'dimensions': ['S','E','Ec','I','F'],
            'reason': 'Self-contained general definition does not introduce or refer to separately following five-dimensional items; actual reasons propagate all following content into the current unit.'},
        'semantic_review_disagreements_not_silently_adjudicated': control_disputes,
        'C05_NEW_019_I_boundary_remains_not_forced': True,
        '008_extra_affordability_removed_and_034_sorting_reason_corrected': True,
        'all_actual_reasons_quotes_subtypes_and_quality_reviewed_by_named_independent_agent': True,
        'independent_reviewer': '/root/validation_state_oct8'},
    'definition_and_material_limits': [
        'The unchanged prompt suffix is complete v1.3 plus the v1.4 substantive operation part, not the omitted validation-discipline ending.',
        'All 240 current IDs are outside the 267 reserved members, but original supplied contexts have shared-family exposure. Model inputs were preserved; safety redaction is only for current manual AI review projections.',
        'The redactor found full-normalized protected text in 84 locations covering 59 registered members in the full projection; zero such remaining matches does not exclude partial extracts or paraphrases.',
        'Masked context was neither opened nor reconstructed; 51 unit reviews are conditional on available safe material. This audit is not a fresh independent validation.',
        'Trial F exception requires an explicit acquisition gap plus a corresponding arrangement; no added requirement of routine channels or exhaustion of all alternative treatments.',
        'Single sequential development runs do not isolate prompt effects from batch/date/provider/randomness. A shorter unified execution layer did not pass the preregistered safety gate; no causal mechanism proof follows.',
        'The 1170 supported/8 conflict/22 boundary annotations describe this AI audit and are not accuracy, reference labels, or a validity estimate.',
        'A/B/C/T reference metrics were not read or used for this semantic audit; fixed-reference feasibility and publication statistics are separate work. No promise that further prompting can meet every fixed kappa threshold.'
    ],
    'disposition': {'candidate07_full_corpus_run': False, 'candidate07_adopted': False,
        'output_splicing': False, 'production_or_original_reference_labels_changed': False,
        'manuscript_changed_by_this_task': False, 'candidate08_automatically_designed_or_executed': False,
        'next_scientific_choice': 'Preserve this failed bounded experiment; statistical/adoption work uses separately authorized intact versions. No automatic further prompt iteration.'},
    'source_bindings': source_bindings
}

redactor_path = BASE.parents[3]/'coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py'
# Locate from project outputs, without opening or emitting reserved source material.
redactor_path = BASE.parents[3]/'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py' if not redactor_path.exists() else redactor_path
assert redactor_path.exists(), redactor_path
spec = importlib.util.spec_from_file_location('candidate07_seal_redactor',redactor_path)
module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
safe_check = module.ReservedContextRedactor().audit_object_no_full_match(report)
assert safe_check['no_remaining_full_normalized_reserved_unit_match']
report['final_report_mechanical_protected_full_match_check'] = safe_check
report_path = REVIEW/'candidate07_final_semantic_gate_report_PRIVATE.json'
save(report_path, report)

md = '''# 候选07最终开发审计：FAIL，未采用

本轮完整执行240个已暴露开发单元及106个合成控制，调用入口为gpt-5.6-sol/medium。15个逻辑请求均在第1次技术有效响应完成，共15次尝试；没有技术或语义重试。原始响应与唯一完成事件、首次有效选择、schema、顺序及逐字引文通过实际技术审计。

预声明19个工作检查项15通过、4失败：00964Ec与03712I回归；01768S与01955I持续错误。8个06错误修复7个，9个06已修细胞保留7个，新增2个已知检查解决1个。模型的boundary_note不豁免这些检查。

完整240单元、1200维及全部理由、证据、F/I子类、S质量标记和问题记录均已由AI审读。追加独立复核后，共保留8处明确手册冲突：另有00198F、00292F新过推及02764I、03876I持续漏判。00090E、00161I保留两方原意见为边界，01448I在可见父谓词和实际研发指导下得到支持。22个边界不强迫答案。以上为审计分类，不能称为准确率、真人金标或独立效度证据。

全部106控制、530维及附加字段由独立代理复核。新增20控制得到支持；C05-NEW-015的自足泛定义错误继承后续另列内容，五维均误为1。C05-NEW-019的否定属性判断保留I边界。C03-CONTROL-003的F与C05-NEW-012的Ec与冻结预期不符，主审与独立审查解释不同；两方意见和原预期均保留，不事后改预期宣布通过。继承85个非边界控制仅82个与冻结标签匹配。008额外affordability已消除，034理由正确区分排序用途。无论两项复核分歧如何裁定，确定错误已足以使本轮失败。

当前人工审读投影机械遮蔽了预留家族的完整归一原文命中；51个单元含被遮蔽语境，未打开或重构。原模型240输入未静默变更，既有共享语境接触限制如实登记。本轮不是新的独立验证，也不能把一次前后差异归因为提示改变。

完整07输出、原始事件及审计原件单独封存；未全量、未采用、未拼回03、未改参照或正文，不自动进入08。固定参照的数学可行性及后续统计采用另行处理，本失败实验不能支持继续提示即可全部达标的承诺。

详细逐维记录、8项错误、22项边界、2项控制复核分歧和精确来源SHA见同目录candidate07_final_semantic_gate_report_PRIVATE.json；原主审与各独立报告保持不变。
'''
md_path = REVIEW/'candidate07_final_semantic_gate_report.md'
assert not md_path.exists();md_path.write_text(md)
paths_to_seal = source_paths + [report_path, md_path, Path(__file__).resolve()]
seal = {'status':'FINAL_CANDIDATE07_CLOSED_GATE_FAIL_NO_FULL_OR_ADOPTION',
    'created_at_UTC':datetime.now(timezone.utc).isoformat(),
    'actual_model_logical_requests':15,'actual_model_attempts':15,
    'technical_status':'PASS','semantic_status':'FAIL',
    'complete240_1200_dimensions_and106_530_dimensions_audited':True,
    'files':[bind(p) for p in paths_to_seal],
    'runtime220_files_and92_frozen_dependencies_bound_via':bind(technical_reverification_path),
    'original_design_freeze_not_overwritten':True,'raw_outputs_not_modified':True}
seal_path = REVIEW/'candidate07_final_closure_seal.json';save(seal_path,seal)
for p in [report_path, md_path, seal_path]: print(json.dumps(bind(p),ensure_ascii=False))
