"""Metadata/hash-only validation availability audit. Never reveals protected rows."""
from pathlib import Path
from collections import Counter
from datetime import datetime, timezone, timedelta
import hashlib
import json
import math
import re

ROOT = Path('/PROJECT_ROOT')
OUT = ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit'
R3 = ROOT / 'outputs/coding-revision-20261007-r3'
DELIVERY = ROOT / 'outputs/final-three-department-20261008-human-validation-template'
PKG = R3 / 'future-human-validation-v5'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def read_metadata(p):
    return json.loads(p.read_text())


def binding(p):
    return {'path': str(p), 'sha256': sha(p)}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    private_path = R3 / 'admin/future_human_v5_sampling_PRIVATE.json'
    old_dev_path = R3 / 'admin/confirmation_sampling_PRIVATE.json'
    manifest_path = PKG / 'source_update_manifest.json'
    qa_path = R3 / 'audit/future_human_v5_source_only_qa.json'
    previous_path = R3 / 'manuscript-update-20261008/真人材料独立性元数据根复核-20261008.json'
    protocol_path = DELIVERY / 'human-design-audit/真人复核统计方法预设冻结.json'
    human_design_path = DELIVERY / 'human-design-audit/人检抽样元数据独立审计.json'
    method_path = ROOT / 'outputs/recall-revision-20261007/方法文献-真人验证与效度核查.json'
    source_path = DELIVERY / 'human-design-audit/一手来源核验.json'
    final_path = DELIVERY / 'final_freeze_actual.json'
    exclusion_path = OUT / 'future_human_v5_development_exclusion_metadata.json'
    private = read_metadata(private_path)
    old_dev = read_metadata(old_dev_path)
    manifest = read_metadata(manifest_path)
    qa = read_metadata(qa_path)
    previous = read_metadata(previous_path)
    protocol = read_metadata(protocol_path)
    design = read_metadata(human_design_path)
    methods = read_metadata(method_path)
    source = read_metadata(source_path)
    final = read_metadata(final_path)
    sample = private['sample']
    reserved_ids = {r['original_id'] for r in sample}
    reserved_families = {r['family_id'] for r in sample}
    reserved_members = {uid for r in sample for uid in r['eligible_family_members']}
    dev_ids = {r['original_id'] for r in old_dev['sample']}
    dev_families = {r['family_id'] for r in old_dev['sample']}

    # The byte stream is searched only for RECODE IDs. Neither prose nor labels
    # are decoded or returned, even though these historical audit files contain them.
    case_files = []
    for name in ['当前两方法具体差异审计.json', '当前两方法具体差异审计.md']:
        p = DELIVERY / 'method-difference-audit' / name
        ids = sorted({v.decode('ascii') for v in re.findall(rb'RECODE25-\d{5}', p.read_bytes())})
        case_files.append({**binding(p), 'unit_ids_extracted_only': ids,
                           'case_count': len(ids), 'reserved_family_member_intersection': sorted(set(ids) & reserved_members)})
    exposed_ids = set(case_files[0]['reserved_family_member_intersection'])
    assert exposed_ids == {'RECODE25-01353', 'RECODE25-01361'}
    assert case_files[0]['unit_ids_extracted_only'] == case_files[1]['unit_ids_extracted_only']
    exposed = []
    for uid in sorted(exposed_ids):
        r = next(r for r in sample if uid in r['eligible_family_members'])
        exposed.append({'exposed_unit_id': uid, 'sampled_unit_id': r['original_id'],
                        'group': r['group'], 'family_id': r['family_id'],
                        'registered_family_members': r['eligible_family_members'],
                        'k_family': r['k_family'],
                        'earliest_disclosed_exposure': 'At least previous-round ten-case method-difference audit and actual manuscript review, as explicitly confirmed by root in this audit turn.',
                        'known_current_contacts': ['root read full ten-case MD; previous writing review used both cases',
                                                   'llm_repair05 read short source excerpts, current machine labels and conclusions before exclusion table arrived; reports neither used for candidate05 prompt/control design'] +
                                                  (['rule_repair37 read source and used this case to design rule repair before exclusion table arrived'] if uid == 'RECODE25-01353' else []),
                        'classification': 'disclosed development exposure; original v5 material remains unchanged'})
    exposed_families = {r['family_id'] for r in exposed}
    unaffected_sample = [r for r in sample if r['family_id'] not in exposed_families]
    unaffected_members = reserved_members - {v for r in exposed for v in r['registered_family_members']}

    public = []
    for rel, expected in manifest['public_file_hashes'].items():
        p = PKG / rel
        actual = sha(p)
        public.append({'path': str(p), 'expected_verified_blank_sha256': expected,
                       'actual_sha256': actual, 'matches_verified_blank': actual == expected})
    current_package_names = sorted(str(p.relative_to(PKG)) for p in PKG.rglob('*') if p.is_file())
    expected_package_names = sorted(['source_update_manifest.json', *manifest['public_file_hashes']])
    prior_metadata_bindings = []
    for record in previous['files']:
        p = Path(record['path'])
        prior_metadata_bindings.append({'path': str(p), 'expected_sha256': record['sha256'],
                                        'actual_sha256': sha(p), 'matches': sha(p) == record['sha256']})
    probability_checks = []
    for r in sample:
        F, k = r['eligible_family_count'], r['k_family']
        probability_checks.append(math.isclose(r['unit_inclusion_probability'], 80/(F*k), rel_tol=1e-14)
                                  and math.isclose(r['unit_analysis_weight'], F*k/80, rel_tol=1e-14)
                                  and r['original_id'] in r['eligible_family_members']
                                  and len(r['eligible_family_members']) == k)

    # Filename/stat-only discovery in the project; no personal chats/external tree.
    markers = ['future-human', 'future_human', 'human-validation', '真人', 'human_submission',
               'submission_receipt', 'submission_registry', 'submitted', '执行记录', '提交',
               '回收', '复核结果', '独立提交接收登记', '裁定', '裁决']
    skip = ['.git', 'node_modules', '__pycache__', 'site-packages', 'authoring-python-overlay',
            'D668-runtime', 'isolated-python312-jsonschema-deps']
    inventory = []
    for p in ROOT.rglob('*'):
        if not p.is_file() or OUT in p.parents:
            continue
        rel = str(p.relative_to(ROOT))
        if any(s in rel for s in skip) or not any(s in rel.lower() for s in markers):
            continue
        st = p.stat()
        inventory.append({'path': str(p), 'bytes': st.st_size,
                          'modified_at': datetime.fromtimestamp(st.st_mtime, timezone(timedelta(hours=8))).isoformat()})
    inventory.sort(key=lambda x: x['path'])
    (OUT / 'candidate_filename_inventory.json').write_text(json.dumps({
        'scope': str(ROOT), 'discovery': 'filename and filesystem stat only; broad names are not proof of human authorship',
        'markers': markers, 'files': inventory,
        'boundary': 'No contents of candidate result files, source originals, machine row outputs or human labels opened. Arbitrarily named or privately held submissions cannot be excluded by filename search.'}, ensure_ascii=False, indent=2) + '\n')

    report = {
        'status': 'METADATA_AUDIT_COMPLETE_NO_VERIFIED_HUMAN_RESULTS_TWO_RESERVED_FAMILIES_DISCLOSED_EXPOSED',
        'created_at': datetime.now(timezone(timedelta(hours=8))).isoformat(),
        'scope': 'Project and registered paths only. Read-only existing inputs; new audit outputs only.',
        'blindness': {'reserved_unit_source_or_context_opened': False,
                      'reserved_machine_row_prediction_opened': False,
                      'human_specific_label_opened': False,
                      'reserved_material_files_processed_only_as_hashes': True,
                      'csv_headers_read_only_no_data_rows': True,
                      'case_audit_scan': 'byte-pattern ID extraction only; no prose/labels returned',
                      'personal_chats_or_unregistered_external_paths_opened': False,
                      'new_model_calls': 0, 'human_metrics_executed': 0,
                      'original_inputs_modified': False},
        'human_result_availability': {
            'verified_real_human_raw_submissions_found': False,
            'verified_real_human_adjudication_records_found': False,
            'actual_result_paths': [],
            'registered_manifest_status': manifest['execution_status'],
            'original_manifest_blank_identity_labels_reasons_evidence': manifest['all_identity_coding_reason_evidence_fields_blank'],
            'prior_full_packaging_QA': {'all_checks_pass': qa['all_checks_pass'],
                                       'actual_sample_n': qa['actual_sample_n'], 'anonymous_rows_n': qa['anonymous_rows_n'],
                                       'coder_checks': [{'coder': v['coder'], 'checks': v['checks']} for v in qa['coder_checks']]},
            'current_blank_evidence': 'All seven public files and registered sampling/QA bindings match verified blank hashes; no CSV label values were read.',
            'registered_package_no_added_files': current_package_names == expected_package_names,
            'registered_package_file_names': current_package_names,
            'human_statistics_run_in_registered_protocol': protocol['human_statistics_executed'],
            'actual_human_bootstrap_replicates': protocol['human_bootstrap_replicates_executed'],
            'availability_boundary': 'No verifiable result found in registered paths/project filename inventory. This does not establish whether real humans have privately begun or completed coding.'},
        'proxy_vs_future_human_separation': {
            'latest_delivery_status': final['status'],
            'latest_result_identity': final['result_identity'],
            'current_proxy_material': {'total': 240, 'probability': old_dev['probability_n'], 'challenge': old_dev['challenge_n'],
                                       'status': 'Already exposed development; original AI A/C/T identity retained. Display B aliases original C.'},
            'future_human_original_sample': {'same_selected_units_for_two_coders': 240,
                                             'total_anonymous_rows': 480,
                                             'unique_unit_n': len(reserved_ids), 'unique_family_n': len(reserved_families),
                                             'department_n': dict(Counter(r['group'] for r in sample)),
                                             'all_registered_family_member_n': len(reserved_members)},
            'overlap_with_proxy_development240': {'selected_unit_n': len(reserved_ids & dev_ids),
                                                   'family_n': len(reserved_families & dev_families)},
            'overlap_with_older_known_development_and_training_ids': len(reserved_members & set(private['known_development_excluded_ids'] + private['current_training_excluded_ids']))},
        'newly_reconciled_exposure': {'case_file_ID_crosscheck': case_files,
                                      'affected_sampled_unit_n': len(exposed), 'affected_family_n': len(exposed_families),
                                      'affected_registered_family_member_n': len(reserved_members - unaffected_members),
                                      'events': exposed,
                                      'not_only_current_turn': True,
                                      'preserved_original_v5_package': True,
                                      'historical_full240_independence_claim_requires_correction': True},
        'remaining_material_evidence': {
            'selected_units_without_newly_disclosed_exposure_in_this_audit': len(unaffected_sample),
            'families_without_newly_disclosed_exposure_in_this_audit': len(reserved_families - exposed_families),
            'registered_members_of_those_families': len(unaffected_members),
            'department_n': dict(Counter(r['group'] for r in unaffected_sample)),
            'original_two_stage_probability_weight_checks': {'checked': len(probability_checks), 'all_pass': all(probability_checks)},
            'historical_document_exposure': design['historical_document_exposure_note'],
            'independence_scope': manifest['independence_scope'],
            'no_new_equal_probability_validation_claim': True,
            'no_posthoc_deletion_or_sample_redesign_performed': True,
            'remaining_scope_boundary': '238 is the remaining registered selected-unit range after two disclosed exposed families. It is not a new equal-probability confirmation sample, not an exhaustive guarantee against undisclosed historical contacts, and not new-document external validation.'},
        'verification_not_replaceable_by_same_batch_recalculation': [
            'Actual independent human identities, dates, raw first submissions and human adjudication; AI proxy output cannot instantiate these records.',
            'Human A/B pre-adjudication agreement must be computed from preserved real first submissions, separately from adjudicated reference.',
            'Independent machine validity for updated rules/LLM requires frozen adopted outputs and genuinely unused confirmation evidence. Reusing the exposed development240, or deleting the two exposed rows and retaining original240 weights, does not supply it.',
            'Five-dimension and department-specific confusion cells, positive support, kappa/precision/recall/F1 and NA diagnostics against real humans; rerunning old proxy comparisons is still development diagnosis.',
            'Same-sample attention shares and Ec/F joint/conditional proportions against real humans, including human Ec denominators and machine-Ec-negative units. Marginal classifier scores, repeated LLM agreement, full-corpus direction and file-composition robustness do not replace these checks.',
            'Actual execution of the reserved-sample analysis protocol with sealed implementation configuration; the 5000 planned bootstrap replicates remain unexecuted for real-human labels.'
        ],
        'permitted_next_validation_handling': {
            'human_reliability': 'If genuine first submissions arrive, preserve and hash both originals; human pre-adjudication reliability can be calculated for the actual submitted materials despite machine-development exposure.',
            'machine_validity': 'Disclose exposed families and analyze them separately as exposure sensitivity. For updated methods, freeze outputs first and prespecify additional unused confirmation materials/design; do not call the remaining238 a redesigned independent probability sample automatically.',
            'original_v5': 'Do not overwrite, silently drop cases, resample, reweight or relabel original v5.',
            'goal_status': 'This audit does not set blocked or complete. Current verified rule/LLM errors may still be repaired; missing human results remain a separate empirical completion condition.'},
        'recommended_independence_wording': '两位真人首次提交尚未在工作区得到核验。预留240条中2个卫健家族已在差异审读和论文举例中暴露，另238个抽中家族本次未发现新增暴露记录；该剩余范围不作为新的等概率验证样本。真人协商前一致性可据实际首次提交计算；更新机器方法的独立效度须在冻结后另行预定未用于开发的确认材料，并单列已暴露材料敏感性。',
        'primary_method_support_already_verified': {
            'metadata_memo': binding(method_path),
            'source_scope': [{'citation': s['citation'], 'doi': s['doi'], 'exact_locations': s['exact_locations'],
                             'supports': s['specific_applicability'], 'does_not_transfer': s['not_transferable']} for s in methods['sources']],
            'reserved_protocol_source': {'binding': binding(source_path), 'official_url': source['primary_reference']['official_url'],
                                         'verified_sections': source['verified_support'], 'excluded_claims': source['unverified_claims_excluded']},
            'no_new_broad_literature_search': True,
            'no_universal_point8_publication_or_validity_rule': True},
        'bindings': [binding(p) for p in [ROOT/'plan.md', final_path, private_path, manifest_path, qa_path,
                    previous_path, protocol_path, human_design_path, old_dev_path, exclusion_path]],
        'public_blank_file_hashes': public,
        'prior_registered_metadata_SHA_recheck': prior_metadata_bindings,
        'all_blank_and_metadata_binding_hashes_match': all(x['matches_verified_blank'] for x in public) and all(x['matches'] for x in prior_metadata_bindings),
        'candidate_filename_inventory': binding(OUT/'candidate_filename_inventory.json'),
        'audit_code': binding(Path(__file__).resolve()),
    }
    assert report['all_blank_and_metadata_binding_hashes_match']
    assert len(unaffected_sample) == 238 and len(unaffected_members) == 265
    assert report['proxy_vs_future_human_separation']['overlap_with_proxy_development240'] == {'selected_unit_n': 0, 'family_n': 0}
    target = OUT / 'validation_state_audit.json'
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    text = '\n'.join([
        '验证状态元数据审计（2026-10-08）',
        '',
        '目前未在登记路径和项目文件名检索中发现可核验的真人独立首次提交或真人裁定记录。v5七个公开文件与原已验证空白版SHA全部相同；两份各240条、共480匿名行，仍以原QA和哈希证明空白。没有读取待评原句、机器逐条预测或人工具体标签。该结论不代表真人私下尚未开始。',
        '',
        '最新正文表2的80个比较值及五维A/B κ来自已暴露的180条AI代理概率材料，另60条为挑战开发材料；B仅为原C的显示别名。它们与待真人的240条不同，不能作为真人结果。',
        '',
        '新核清的暴露：十例差异审计JSON/MD与保留267家族成员只在 RECODE25-01353、RECODE25-01361 交叉，均为卫健实际抽中单位和单成员家族。root确认暴露至少起于上一轮差异审计及实写稿审读；本轮规则修复亦使用01353设计修复，LLM修复者看到两例短摘/机器标签/审查结论但未用于候选05提示或控制设计。旧“完整240未暴露”表述需更正。原v5不改。',
        '',
        '剩余范围为238抽中家族、265登记家族成员：药监80、医保80、卫健78。这是本次未发现新增暴露记录的登记范围，不是事后新建的等概率验证样本，也不是对所有历史接触的保证。历史49完整来源文件接触已披露，因此不称新文件外部验证。原240的两阶段入样概率与权重均核对通过，但删2后不能直接沿用完整240的统计设计。',
        '',
        report['recommended_independence_wording'],
        '',
        '同批重算不能替代：真人身份/日期/首次独立提交/裁定；协商前真人信度；对真实人工参照逐维分部门的分类表现和NA；在同一样本检验注意力及Ec/F联合条件比例（含人工Ec有效分母和机器Ec阴性单元）；冻结后未用于开发材料的确认。重复性、全量方法同向、文件构成敏感性和bootstrap均有各自用途，不能代替上述证据。',
        '',
        '已核一手范围：Grimmer–Stewart（2013）作者稿§2.2–2.4、§5.1及§5.2.1–5.2.4支持任务内验证、训练/验证区分和逐条/聚合目标分别核查；Gilardi等（2023）§4.1、4.3–4.6及S1支持共用手册和真实人工参照，但不移植其英语任务表现或把一致子集等同全争议裁决；Kristensen-McLachlan等（2025）Results及Methods/S1/S3支持逐类表现和人工裁定，不能将其α当本项目κ或通用阈值。具体原文版本/页节/哈希见既有方法文献核查JSON。',
        '预留真人区间依据Bessonneau等（2021）官方HTML §3.1/§3.3与§6：每层重抽n−1个PSU、权重乘n/(n−1)与重数；此为有放回近似，并不证明非线性有限样本覆盖。真人统计实际执行仍为0，实施配置还需按原冻结方案在观察标签分布前封存。',
        '',
        '本审计未修改原标签、原空白包或稿件，未新增模型调用；未将目标标为blocked或完成。规则与LLM的确证错误仍可继续修复，真实人工提交是另一项尚未完成的实证条件。',
        '',
        '完整证据与哈希：' + str(target),
        '开发逐条排除ID/家族哈希：' + str(exclusion_path),
    ]) + '\n'
    (OUT / 'validation_state_audit.txt').write_text(text)
    print(json.dumps({'status': report['status'], 'report': str(target), 'sha256': sha(target),
                      'blank_file_hash_matches': len(public), 'human_results_verified': False,
                      'known_exposed_reserved_units': sorted(exposed_ids),
                      'remaining_selected_families': 238}, ensure_ascii=False))


if __name__ == '__main__':
    main()
