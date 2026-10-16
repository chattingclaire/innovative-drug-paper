#!/usr/bin/env python3
"""Integrate date/department metadata only; never open coding or reference outputs."""
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime, date
from zoneinfo import ZoneInfo
import csv
import hashlib
import json
import re
import unicodedata

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OUT = ROOT / '01-review/annual-metadata-integrated-sol'
ARCHIVE = Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区')
PLAN_DIR = ROOT / '02-methods/department-year-analysis-plan-sol'
AUDIT_DIR = ROOT / '01-review/annual-publication-date-audit-sol'
FROZEN = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/validation-expansion-20260926/frozen-inputs')
CUTOFF = '2026-07-31'
STAMP = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
INPUTS = {}

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def bind(p, role, expected=None):
    p = Path(p)
    value = sha(p)
    if expected is not None:
        assert value == expected, ('hash_drift', str(p), expected, value)
    INPUTS[str(p)] = {'path': str(p), 'sha256': value, 'bytes': p.stat().st_size, 'role': role}
    return value

def read_json(p, role):
    bind(p, role)
    return json.loads(Path(p).read_text())

def write_json(name, obj):
    (OUT / name).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')

def write_jsonl(name, rows):
    (OUT / name).write_text(''.join(json.dumps(x, ensure_ascii=False, separators=(',', ':')) + '\n' for x in rows))

def write_csv(name, rows, fields):
    with (OUT / name).open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

def norm(s):
    return re.sub(r'[^0-9a-zA-Z\u4e00-\u9fff]', '', unicodedata.normalize('NFKC', s))

def year(s):
    return date.fromisoformat(s).year if s is not None else None

plan = read_json(PLAN_DIR / 'report.json', 'unchanged_annual_analysis_plan')
plan_seal = read_json(PLAN_DIR / 'seal.json', 'annual_plan_input_locator')
audit = read_json(AUDIT_DIR / 'metadata.json', '20_original_publication_dates')
audit_seal = read_json(AUDIT_DIR / 'seal.json', 'original_publication_date_audit_seal')

# Check the existing audit inventory, including retained failed-request traces.
# No failed HTTP response is used below as a date or version source.
audit_file_checks = []
for record in audit_seal['files']:
    p = AUDIT_DIR / record['relative_path']
    bind(p, 'audit_retained_artifact_integrity', record['sha256'])
    assert p.stat().st_size == record['bytes']
    audit_file_checks.append({'path': str(p), 'sha256': record['sha256'], 'matched': True})
assert sha(AUDIT_DIR / 'metadata.json') == audit_seal['summary_metadata_sha256']
for record in audit['inputs']:
    bind(record['path'], 'audit_input_integrity', record['sha256'])

selected_names = {
    'source-only-frame.jsonl', 'source_files_manifest.json', 'legacy-frame-manifest.json',
    '来源条目与分析单元明细.json', '政策元数据已核验补充.json',
    'classification--部门归属与年度系列-冻结v1.json'
}
locators = {}
for record in plan_seal['inputs']:
    p = Path(record['path'])
    if p.name in selected_names:
        bind(p, 'plan_located_metadata_only_input', record['sha256'])
        locators[p.name] = p
assert selected_names == set(locators)
frame_path = locators['source-only-frame.jsonl']
frame = [json.loads(l) for l in frame_path.read_text().splitlines() if l.strip()]
assert len(frame) == 4481
assert len({x['id'] for x in frame}) == 4481
assert all(not any(k in x for k in ['labels', 'final_accepted_labels', 'prediction', 'gold_labels']) for x in frame)
details = json.loads(locators['来源条目与分析单元明细.json'].read_text())
supplement = json.loads(locators['政策元数据已核验补充.json'].read_text())
classification = json.loads(locators['classification--部门归属与年度系列-冻结v1.json'].read_text())
source_manifest = json.loads(locators['source_files_manifest.json'].read_text())
legacy_manifest = json.loads(locators['legacy-frame-manifest.json'].read_text())
frozen_metadata_path = Path(audit['inputs'][1]['path'])
frozen_metadata = json.loads(frozen_metadata_path.read_text())
frozen_by_file = {x['original_file']: x for x in frozen_metadata}
class_by_stem = {Path(x['original_file']).stem: x for x in classification['rows']}
assert len(class_by_stem) == len(classification['rows'])
entry_by_stem = {x['id']: x for x in details['entries']}
assert len(entry_by_stem) == len(details['entries'])
frame_by_stem = defaultdict(list)
for x in frame:
    frame_by_stem[x['source_document_stem']].append(x)
assert len(frame_by_stem) == 51
assert set(frame_by_stem) <= set(entry_by_stem)
manifest_by_original = {x['original']: x for x in source_manifest['files']}
assert len(manifest_by_original) == len(source_manifest['files'])
frame_source_paths = {x['source_position'][k] for x in frame for k in ['source_file', 'unit_source_file']}
for pth in sorted(frame_source_paths):
    record = manifest_by_original[pth]
    bind(record['snapshot'], 'frame_source_snapshot_integrity', record['sha256'])

plan_dates = {x['stem']: x for x in plan['year_assignment']['six_source_date_checks']}
assert len(plan_dates) == 6
audited_by_stem = {}
new_checks = []
current_original_checks = []
for entry in audit['entries']:
    p = Path(entry['metadata_path'])
    bind(p, 'new_date_entry_metadata', entry['metadata_sha256'])
    m = json.loads(p.read_text())
    assert m['id'] == entry['id'] and m['publication_date'] == entry['publication_date']
    stem = m['id']
    assert stem in frame_by_stem and stem not in audited_by_stem
    preserved_hashes = {
        row['source_position'].get(k)
        for row in frame_by_stem[stem]
        for k in ['source_sha256_recorded', 'unit_source_sha256_recorded']
    }
    retained_hash = m['version_identity_check']['original_source_sha256']
    assert retained_hash in preserved_hashes
    for ev in m['evidence']:
        if ev.get('original_path'):
            bind(ev['original_path'], 'new_date_preserved_current_original_integrity', ev['sha256'])
            current_original_checks.append({'source_entry_id': stem, 'path': ev['original_path'], 'sha256': ev['sha256'], 'matched': True})
    ev = next(e for e in m['evidence'] if e['role'].startswith('primary_original_publication_date'))
    bind(ev['saved_path'], 'new_original_date_primary_evidence', ev['sha256'])
    bind(ev['text_saved_path'], 'new_original_date_read_text', ev['text_sha256'])
    lines = Path(ev['text_saved_path']).read_text().splitlines()
    assert m['publication_date'] in '\n'.join(lines[:50])
    proof = []
    for i, line in enumerate(lines[:50]):
        if any(t in line for t in ['发布时间', '发布日期', '日期：']):
            window = lines[max(0, i-1):min(len(lines), i+3)]
            if m['publication_date'] in '\n'.join(window):
                proof.append({'line': i + 1, 'lines': window})
    assert proof, ('no_labelled_date_proof', stem)
    doc_no_match = norm(m['document_version']) in norm('\n'.join(lines))
    attachment_match = m['version_identity_check'].get('official_attachment_sha256') == retained_hash
    assert doc_no_match or attachment_match, ('unresolved_version_identity', stem)
    new_checks.append({
        'source_entry_id': stem, 'audit_index': m['index'],
        'publication_date': m['publication_date'], 'document_version': m['document_version'],
        'primary_publication_url': m['primary_publication_url'],
        'primary_evidence_path': ev['saved_path'], 'primary_evidence_sha256': ev['sha256'],
        'read_text_path': ev['text_saved_path'], 'read_text_sha256': ev['text_sha256'],
        'labelled_date_proof': proof,
        'primary_document_number_rechecked': doc_no_match,
        'official_attachment_exact_hash_match': attachment_match,
        'preserved_source_sha256_in_fixed_frame': retained_hash,
        'fixed_frame_source_sha_match': True,
        'identity_status': 'same_preserved_source_version_confirmed_by_hash_and_notice_identity',
        'evidence_extent': ev.get('content_extent'),
        'prior_date_metadata_conflict': m.get('date_metadata_conflict'),
        'excluded_date_candidates_preserved': m.get('excluded_date_candidates', [])
    })
    audited_by_stem[stem] = m
assert len(audited_by_stem) == 20

# Historical metadata evidence is checked for byte integrity, without re-reading
# or certifying all 31 historical original publication date pages in this round.
historical_evidence_checks = []
for stem in frame_by_stem:
    e = entry_by_stem[stem]
    s = supplement.get(e['original_file'], {})
    fm = frozen_by_file[e['original_file']]
    for key in ['issue_date', 'publication_date', 'effective_date', 'metadata_evidence_source', 'metadata_evidence_sha256']:
        assert s.get(key) == fm.get(key), ('current_frozen_metadata_difference', stem, key)
    if s.get('metadata_evidence_source'):
        bind(s['metadata_evidence_source'], 'historical_recorded_evidence_integrity_only', s['metadata_evidence_sha256'])
        historical_evidence_checks.append({'source_entry_id': stem, 'path': s['metadata_evidence_source'], 'sha256': s['metadata_evidence_sha256'], 'integrity_checked': True, 'date_semantics_reaudited_this_round': False})

corrections = []
entries = []
for stem in sorted(frame_by_stem):
    old = entry_by_stem[stem]
    cl = class_by_stem[stem]
    sup = supplement.get(old['original_file'], {})
    fm = frozen_by_file[old['original_file']]
    rows = frame_by_stem[stem]
    assert old['original_file'] == cl['original_file']
    assert len(rows) == old['candidate_unit_count']
    assert {x['analysis_group'] for x in rows} == {old['group']} == {cl['analysis_group']}
    assert old['publishers'] == cl['publishers'] and old['joint'] == cl['joint_publication']
    assert old['series'] == cl['policy_series'] and old['annual_series'] == cl['annual_series']
    assert old['publication_date'] == sup.get('publication_date')
    assert old['effective_date'] == sup.get('effective_date')
    source_paths = sorted({x['source_position'][k] for x in rows for k in ['source_file', 'unit_source_file']})
    source_refs = []
    for pth in source_paths:
        mr = manifest_by_original[pth]
        roles = sorted({k for x in rows for k in ['source_file', 'unit_source_file'] if x['source_position'][k] == pth})
        for x in rows:
            for key, recorded_key in [('source_file', 'source_sha256_recorded'), ('unit_source_file', 'unit_source_sha256_recorded')]:
                if x['source_position'][key] == pth:
                    assert x['source_position'][recorded_key] == mr['sha256']
        source_refs.append({'original_path': pth, 'preserved_snapshot': mr['snapshot'], 'sha256': mr['sha256'], 'roles': roles, 'snapshot_sha_checked': True})
    prior_evidence = {k: sup.get(k) for k in ['metadata_evidence_source', 'metadata_evidence_sha256', 'metadata_evidence_url', 'metadata_evidence_page', 'evidence_type', 'publisher_evidence', 'date_note', 'effective_date_basis', 'effective_date_evidence', 'additional_metadata_evidence', 'official_attachment_url', 'attachment_identity_sha256'] if k in sup}
    issue = sup.get('issue_date')
    issue_basis = 'inherited_verified_supplement_issue_date' if issue else 'unavailable_no_issue_date_in_recorded_metadata'
    issue_ref = {'path': str(locators['政策元数据已核验补充.json']), 'record_key': old['original_file'], 'sha256': sha(locators['政策元数据已核验补充.json'])} if issue else None
    if stem in plan_dates:
        assert issue is None
        check = plan_dates[stem]
        issue = check['issue_date']
        issue_basis = 'inherited_six_source_local_read_from_annual_plan'
        issue_ref = {'path': str(PLAN_DIR / 'report.json'), 'sha256': sha(PLAN_DIR / 'report.json'), 'record_location': 'year_assignment.six_source_date_checks', 'original_source_snapshot': check['source_snapshot'], 'original_source_sha256': sha(check['source_snapshot']), 'read_location_preserved': check['read_location'], 'date_semantics_reaudited_this_integration': stem in audited_by_stem}
    pub = old['publication_date']
    pub_origin = 'historical_available_entry_metadata'
    pub_status = 'inherited_previously_recorded_original_date_not_reaudited_this_integration'
    pub_ref = {'path': str(locators['来源条目与分析单元明细.json']), 'sha256': sha(locators['来源条目与分析单元明细.json']), 'record_key': stem, 'prior_evidence': prior_evidence}
    if stem == 'NHC-第一批国家重点监控合理用药药品目录-2019':
        assert pub is None and stem in plan_dates
        pub = '2019-07-01'
        pub_origin = 'historical_annual_plan_original_pdf_recovery'
        pub_ref = {'path': str(PLAN_DIR / 'report.json'), 'sha256': sha(PLAN_DIR / 'report.json'), 'record_location': 'year_assignment.six_source_date_checks + provenance_limit', 'original_source_snapshot': plan_dates[stem]['source_snapshot'], 'original_source_sha256': sha(plan_dates[stem]['source_snapshot']), 'evidence_preserved': '原PDF首页发布2019-07-01；署名2019-06-11。沿用计划已核读结果，本整合未重新审读该PDF日期页。'}
    effective = old['effective_date']
    effective_basis = sup.get('effective_date_basis') or sup.get('publisher_evidence') if effective is not None else None
    effective_status = 'inherited_explicit_effective_date_not_reaudited_this_integration' if effective is not None else 'not_verified_or_not_applicable_keep_null'
    new = audited_by_stem.get(stem)
    if new is not None:
        assert pub is None and old['publication_date'] is None
        assert issue == new['issue_date']
        pub = new['publication_date']
        pub_origin = 'new_20_original_agency_date_audit_rechecked_this_integration'
        pub_status = 'original_agency_label_and_same_preserved_version_rechecked'
        pub_ref = {'path': str(new['directory'] + '/metadata.json'), 'sha256': sha(new['directory'] + '/metadata.json'), 'primary_publication_url': new['primary_publication_url'], 'evidence': [e for e in new['evidence'] if e['role'].startswith('primary_original_publication_date')], 'date_metadata_conflict_preserved': new.get('date_metadata_conflict')}
        if effective != new['effective_date']:
            assert effective is None and new['effective_date'] is not None
            corrections.append({'source_entry_id': stem, 'field': 'effective_date', 'prior_entry_metadata_value': effective, 'prior_new_date_audit_value': new['effective_date'], 'integrated_value': new['effective_date'], 'basis': new['effective_date_basis'], 'evidence_path': new['directory'] + '/evidence/primary-http-visible-text.txt', 'classification': 'explicit_evidence_addition_no_main_year_change'})
        effective = new['effective_date']
        effective_basis = new['effective_date_basis']
        effective_status = 'new_original_agency_explicit_effective_clause_rechecked' if effective is not None else new['effective_date_status']
        if stem == 'NMPA-优化创新药临床试验审评审批公告-2025':
            # Original audit retained null despite an explicit implementation clause.
            p = Path(new['directory']) / 'evidence/primary-http-visible-text.txt'
            text = p.read_text()
            assert '本公告自发布之日起实施。' in text and pub == '2025-09-12'
            effective = pub
            effective_basis = '原页正文第26行“本公告自发布之日起实施。”；以已核原公开日2025-09-12填写实施时点。'
            effective_status = 'explicit_implementation_clause_recovered_this_integration'
            corrections.append({'source_entry_id': stem, 'field': 'effective_date', 'prior_entry_metadata_value': None, 'prior_new_date_audit_value': None, 'integrated_value': effective, 'basis': effective_basis, 'evidence_path': str(p), 'evidence_sha256': sha(p), 'classification': 'audit_omission_corrected_from_explicit_saved_original_page_no_main_year_change'})
    assert pub is not None
    policy_year = year(issue) if issue is not None else year(pub)
    basis = 'issue_date' if issue is not None else 'original_publication_date_fallback_no_issue_date'
    assert policy_year == cl['year_in_filename']  # A cross-check only, never an assignment source.
    assert pub <= CUTOFF and old['cutoff'] == CUTOFF
    components = old['components']
    assert sum(x['candidate_units'] for x in components) == len(rows)
    identity_payload = {'source_entry_id': stem, 'original_file': old['original_file'], 'department': cl['analysis_group'], 'source_hashes': sorted({x['sha256'] for x in source_refs})}
    identity_sha = hashlib.sha256(json.dumps(identity_payload, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    entries.append({
        'source_entry_id': stem, 'source_document_stem': stem, 'original_file': old['original_file'],
        'department': cl['analysis_group'], 'analysis_group': cl['analysis_group'],
        'department_name': rows[0]['department_name'], 'publishers': cl['publishers'],
        'joint_publication': cl['joint_publication'], 'policy_series': cl['policy_series'],
        'annual_series': cl['annual_series'], 'series_basis': cl.get('series_basis'),
        'department_assignment_basis': 'unchanged_frozen_institutional_system_single_assignment',
        'clause_n': len(rows), 'source_entry_identity_sha256': identity_sha,
        'document_version': new['document_version'] if new else None,
        'document_version_status': 'original_notice_identity_rechecked' if new else 'source_identity_hashes_preserved_version_text_not_reconstructed_this_round',
        'preserved_source_files': source_refs,
        'policy_year': policy_year, 'year_basis': basis, 'year_in_filename_crosscheck_only': cl['year_in_filename'],
        'issue_date': issue, 'issue_date_evidence_status': issue_basis, 'issue_date_evidence': issue_ref,
        'publication_date': pub, 'publication_year': year(pub),
        'publication_date_origin': pub_origin, 'publication_date_evidence_status': pub_status,
        'publication_date_evidence': pub_ref,
        'prior_publication_date': old['publication_date'],
        'prior_publication_date_upper_bound': old.get('publication_date_upper_bound'),
        'prior_publication_date_bound_basis': old.get('publication_date_bound_basis'),
        'publication_date_upper_bound': None,
        'upper_bound_status': 'superseded_by_rechecked_exact_original_date' if old.get('publication_date_upper_bound') else 'not_used',
        'effective_date': effective, 'effective_date_evidence_status': effective_status,
        'effective_date_basis': effective_basis, 'prior_effective_date': old['effective_date'],
        'prior_new_audit_effective_date': new['effective_date'] if new else None,
        'date_year_relationships': {'issue_publication_cross_year': year(issue) != year(pub) if issue else None, 'policy_publication_cross_year': policy_year != year(pub), 'effective_publication_cross_year': year(effective) != year(pub) if effective else None, 'effective_before_original_publication': effective < pub if effective else None},
        'cutoff': CUTOFF, 'published_by_cutoff': pub <= CUTOFF,
        'effective_date_on_or_before_cutoff': effective <= CUTOFF if effective else None,
        'effective_date_after_cutoff': effective > CUTOFF if effective else None,
        'cutoff_interpretation': '公开纳入边界；effective_date单存，非在效政策存量认证',
        'observation_year_window': '截至2026-07-31（部分年度）' if policy_year == 2026 else '完整日历年边界（所收集文本，非政策穷尽普查）',
        'listed_component_n': len(components), 'listed_component_metadata_preserved': components,
        'component_mapping_status': 'pending_independent_component_id_and_unit_map_acceptance',
        'component_clock_status': 'pending_no_independent_component_date_overrides_in_this_entry_map',
        'prior_metadata_evidence_preserved': prior_evidence,
        'original_source_metadata_ref': {'path': str(frozen_metadata_path), 'sha256': sha(frozen_metadata_path), 'original_file': old['original_file'], 'source': fm['source'], 'source_sha256': fm['source_sha256'], 'prior_metadata_frozen_status': fm.get('metadata_frozen'), 'prior_group_status': fm.get('group_status'), 'prior_evidence_type': fm.get('evidence_type'), 'prior_in_force_at_cutoff_value_preserved_not_recertified': fm.get('in_force_at_cutoff')}
    })

entry_map = {x['source_entry_id']: x for x in entries}
assert len(entries) == 51 and sum(x['clause_n'] for x in entries) == 4481
assert sum(x['listed_component_n'] for x in entries) == 56
assert sum(x['issue_date'] is not None for x in entries) == 48
assert sum(x['publication_date_origin'].startswith('historical') for x in entries) == 31
assert sum(x['publication_date_origin'].startswith('new_20') for x in entries) == 20

main_map = []
pub_map = []
for row in frame:
    e = entry_map[row['source_document_stem']]
    assert row['analysis_group'] == e['department']
    common = {'source_id': row['id'], 'id': row['id'], 'original_id': row['original_id'], 'department': e['department'], 'analysis_group': e['department'], 'department_name': e['department_name'], 'source_entry_id': e['source_entry_id'], 'source_document_stem': e['source_document_stem'], 'source_entry_identity_sha256': e['source_entry_identity_sha256'], 'issue_date': e['issue_date'], 'publication_date': e['publication_date'], 'effective_date': e['effective_date'], 'policy_series': e['policy_series'], 'annual_series': e['annual_series'], 'joint_publication': e['joint_publication'], 'cutoff': CUTOFF, 'published_by_cutoff': True, 'component_id': None, 'component_mapping_status': e['component_mapping_status']}
    main_map.append({**common, 'policy_year': e['policy_year'], 'year_basis': e['year_basis'], 'publication_year': e['publication_year'], 'mapping_scenario': 'main_issue_or_original_publication_year'})
    pub_map.append({**common, 'publication_year': e['publication_year'], 'sensitivity_year': e['publication_year'], 'policy_year_main': e['policy_year'], 'year_basis': 'original_publication_date', 'mapping_scenario': 'publication_year_sensitivity'})
expected_ids = {x['id'] for x in frame}
for mapping in [main_map, pub_map]:
    ids = [x['source_id'] for x in mapping]
    assert len(ids) == len(set(ids)) == 4481 and set(ids) == expected_ids

inventory = []
for department in ['NMPA', 'NHSA', 'NHC']:
    for y in range(2017, 2027):
        subset = [e for e in entries if e['department'] == department and e['policy_year'] == y]
        n = sum(e['clause_n'] for e in subset)
        pub_subset = [e for e in entries if e['department'] == department and e['publication_year'] == y]
        inventory.append({'department': department, 'year': y, 'source_entry_n': len(subset), 'listed_component_n': sum(e['listed_component_n'] for e in subset), 'clause_n': n, 'joint_entry_n': sum(e['joint_publication'] for e in subset), 'joint_clause_n': sum(e['clause_n'] for e in subset if e['joint_publication']), 'publication_year_source_entry_n': len(pub_subset), 'publication_year_clause_n': sum(e['clause_n'] for e in pub_subset), 'cell_status': 'observed_source' if n else 'no_observed_source', 'downstream_q_p_status_if_no_source': None if n else 'NA(no_observed_source)', 'year_window': '截至2026-07-31' if y == 2026 else '完整日历年边界，非政策穷尽普查', 'labels_or_dimension_results_computed': False})
assert sum(x['clause_n'] for x in inventory) == 4481
prior_inventory = {(x['department'], x['year']): x for x in plan['metadata_only_year_inventory']}
for cell in inventory:
    old = prior_inventory[(cell['department'], cell['year'])]
    for k in ['source_entry_n', 'listed_component_n', 'clause_n', 'joint_entry_n', 'joint_clause_n']:
        assert old[k] == cell[k], ('plan_inventory_disagreement', cell, k)
group_n = dict(Counter(x['analysis_group'] for x in frame))
group_entries = dict(Counter(e['department'] for e in entries))
assert group_n == {'NMPA': 1848, 'NHSA': 2100, 'NHC': 533}
assert group_entries == {'NMPA': 17, 'NHSA': 24, 'NHC': 10}

verification = {
    'schema': 'annual-metadata-integration-verification-v1', 'created_at': STAMP,
    'fixed_frame_n': len(frame), 'fixed_frame_unique_source_id_n': len(expected_ids),
    'main_map_n': len(main_map), 'publication_sensitivity_map_n': len(pub_map),
    'both_maps_one_to_one_complete_unique_4481': True,
    'source_entry_n': len(entries), 'all_51_entry_counts_and_departments_match_frame_and_frozen_metadata': True,
    'group_clause_n': group_n, 'group_source_entry_n': group_entries,
    'joint_source_entry_n': sum(e['joint_publication'] for e in entries),
    'joint_clause_n': sum(e['clause_n'] for e in entries if e['joint_publication']),
    'listed_component_n': 56, 'independent_component_id_map_accepted': False,
    'component_map_status': 'pending', 'component_date_map_status': 'pending',
    'issue_date_available_n': 48, 'publication_fallback_main_year_n': 3,
    'original_publication_date_available_n': 51, 'historical_31_not_reaudited_n': 31,
    'new_20_original_label_and_source_version_rechecked_n': 20,
    'paired_issue_publication_same_year_n': sum(e['issue_date'] is not None and year(e['issue_date']) == e['publication_year'] for e in entries),
    'main_vs_publication_year_disagreement_entry_n': sum(e['policy_year'] != e['publication_year'] for e in entries),
    'main_vs_publication_year_disagreement_clause_n': sum(e['clause_n'] for e in entries if e['policy_year'] != e['publication_year']),
    'all_51_published_by_2026_07_31': all(e['published_by_cutoff'] for e in entries),
    'missing_year_assignment_entry_n': sum(e['policy_year'] is None for e in entries),
    'missing_year_assignment_clause_n': sum(e['clause_n'] for e in entries if e['policy_year'] is None),
    'missing_department_assignment_entry_n': sum(e['department'] is None for e in entries),
    'missing_department_assignment_clause_n': sum(e['clause_n'] for e in entries if e['department'] is None),
    'nonempty_department_year_cell_n': sum(e['clause_n'] > 0 for e in inventory),
    'empty_department_year_cell_n': sum(e['clause_n'] == 0 for e in inventory),
    'global_years_without_any_observed_source': [y for y in range(2017, 2027) if not any(e['year'] == y and e['clause_n'] > 0 for e in inventory)],
    'preserved_source_snapshot_path_n': len(frame_source_paths),
    'all_preserved_source_snapshot_SHA_checks_passed': True,
    'new_audit_retained_file_SHA_checks_n': len(audit_file_checks),
    'new_audit_current_original_path_SHA_checks_n': len(current_original_checks),
    'historical_metadata_evidence_SHA_checks_n': len(historical_evidence_checks),
    'historical_evidence_SHA_check_is_not_semantic_date_reaudit': True,
    'metadata_corrections_n': len(corrections), 'metadata_corrections': corrections,
    'year_inventory_matches_unchanged_plan': True,
    'machine_labels_reference_labels_formal_blind_labels_read': False,
    'label_or_dimension_statistics_computed': False,
    'only_this_new_directory_written': True,
    'goal_progress_analysis_plan_or_original_sources_modified': False
}
write_json('metadata.json', {'schema': 'annual-source-entry-metadata-integrated-v1', 'created_at': STAMP, 'status': 'complete_51_source_entry_date_metadata_and_4481_entry_year_maps_component_mapping_pending', 'cutoff': CUTOFF, 'source_id_definition': 'source_id精确等于无标签固定框id（RECODE25-xxxxx），source_entry_id为51个来源条目标识。', 'year_assignment_rule': 'issue_date有值优先；缺成文日用原公开publication_date年度；文件名只交叉核对；effective_date永不用于主赋年。', 'date_evidence_review_scope': '新增20项保存原页日期标签/题名文号及当前来源SHA再次核对；此前31项公开日保留原可用值与证据状态，未声称本轮逐页复审。', 'join_rule': 'fixed source-only frame.source_document_stem == source-entry.id == classification.original_file去扩展名；逐条精确匹配，不做模糊/主题/文件名赋年。', 'component_limit': '51条目列示56组件及数量关系保留；未验收独立component_id、逐单元组件映射、逐组件日期或覆盖规则，全部pending，主映射只到source-entry。', 'entries': entries})
write_jsonl('source-entry-metadata.jsonl', entries)
write_csv('source-entry-metadata.csv', entries, ['source_entry_id', 'original_file', 'department', 'department_name', 'clause_n', 'listed_component_n', 'policy_year', 'year_basis', 'issue_date', 'publication_date', 'publication_year', 'effective_date', 'publication_date_origin', 'publication_date_evidence_status', 'effective_date_evidence_status', 'joint_publication', 'policy_series', 'annual_series', 'cutoff', 'published_by_cutoff', 'effective_date_after_cutoff', 'component_mapping_status'])
write_jsonl('source-id-year-map.jsonl', main_map)
write_csv('source-id-year-map.csv', main_map, ['source_id', 'id', 'original_id', 'department', 'department_name', 'source_entry_id', 'policy_year', 'year_basis', 'publication_year', 'issue_date', 'publication_date', 'effective_date', 'joint_publication', 'policy_series', 'annual_series', 'cutoff', 'component_id', 'component_mapping_status'])
write_jsonl('source-id-publication-year-map.jsonl', pub_map)
write_csv('source-id-publication-year-map.csv', pub_map, ['source_id', 'id', 'original_id', 'department', 'department_name', 'source_entry_id', 'publication_year', 'sensitivity_year', 'policy_year_main', 'year_basis', 'issue_date', 'publication_date', 'effective_date', 'joint_publication', 'policy_series', 'annual_series', 'cutoff', 'component_id', 'component_mapping_status'])
write_json('annual-source-inventory.json', inventory)
write_csv('annual-source-inventory.csv', inventory, list(inventory[0]))
write_json('new-20-date-version-verification.json', {'schema': 'new-20-date-version-verification-v1', 'created_at': STAMP, 'scope': '保存原页日期证据与固定框同版本SHA核对；不替换来源，不读取编码标签。', 'checks': new_checks, 'current_original_integrity_checks': current_original_checks})
write_json('historical-provenance-integrity.json', {'schema': 'historical-evidence-integrity-only-v1', 'scope': '仅检查已记录历史元数据证据字节完整性，不等于本轮重新核读31个原公开日期页。', 'checks': historical_evidence_checks})
write_json('verification.json', verification)
write_json('report.json', {**verification, 'scope': '全51来源条目的三时钟、部门与年度元数据，固定4481无标签框的一对一映射；未计算任何五维结果。', 'main_year_rule': 'issue_date年度优先，缺失时original publication_date年度回退', 'sensitivity_year_rule': '原公开publication_date年度，保留主policy_year字段用于比较', 'sensitivity_result_metadata_only': '主赋年与原公开年度在51条目/4481条款上均相同；这只说明日期分组一致，不构成任何标签结果稳健性证据。', 'pending': [{'item': 'independent_component_map', 'reason': '56为51条目下列示组件；没有验收component_id与4481逐单元映射。通知与本体不能按路径机械拆分。'}, {'item': 'component_date_and_window_map', 'reason': '未逐组件核定独立公开日期；source-entry日期不能无条件用于bundle所有组件的月/日相同窗口或替代覆盖筛选。'}], 'three_clocks_GCP_2026': {'issue_date': '2026-05-21', 'publication_date': '2026-06-08', 'effective_date': '2026-09-01', 'policy_year': 2026, 'published_by_cutoff': True, 'effective_date_after_cutoff': True}, 'empty_year_interpretation': {'2017': '三部门均无纳入来源：全局无源年；日期缺失或赋年失败为0条，不与无源混同。', 'department_year': '9个空部门年度为该部门该年无纳入来源；N及条目数为0，下游q/p须NA(no_observed_source)，不能写维度为0。'}, 'annual_source_inventory': inventory})
write_json('input-bindings.json', {'schema': 'annual-metadata-input-bindings-v1', 'created_at': STAMP, 'inputs': list(INPUTS.values())})

readme = '''本交付仅整合年度元数据，不含任何机器标签、参照标签、盲包labels或五维结果。

51个来源条目已按固定无标签框完整连接4481个唯一source_id；source_id等于原框id，source_entry_id是来源条目。药监/医保/卫健分别1848/2100/533条款、17/24/10条目。主映射：source-id-year-map.jsonl；原公开年度敏感性映射：source-id-publication-year-map.jsonl；两者完整且唯一，不删除条款、不多部门重复计入。

主policy_year采用成文issue_date年度；48项有成文日，其余3项回退到原公开publication_date。未以文件名赋年，也未以施行日替代。原公开日已具51项：历史30项来源明细值及1项计划从2019监控目录原PDF补核值，共31项沿用；新增20项原页日期标签、题名/文号与固定框当前版本SHA再次核对。31项旧证据仅保留状态和进行哈希完整性检查，不能称本轮全部原日期页复审。9项卫健新增证据为此前正常浏览器读取的原页DOM选摘，其HTTP412仅失败留痕，不作正文证据；其余11项有完整原机关HTML。所有20项保留来源SHA均能匹配固定框；审计171个文件、35处当前原路径证据及框中83处来源快照哈希均一致。

主成文/公布年度与原公开年度在51条目和4481条款上相同，48对成文/公开已知日期同年。此处一致只说明元数据分组一致，不说明五维结果或敏感性结论。医保2022原公开上界2022-07-01保留在prior字段，其明确原公开日2022-06-29已核；未将上界当精确日期。

三时钟分存：2026 GCP成文2026-05-21、原公开2026-06-08、施行2026-09-01。它已于2026-07-31公开截止前发布，但不能据此说截至7月底已施行。施行日前后字段只描述日期，不认证存量有效性/废止关系。2018处方审核规范及2021监控目录调整规程的印发施行日早于网页公开日，是已有明确“自印发”规则，未强制调整为公开日。

本整合保存两处施行时点补充/更正：三程序2020由旧null补入公告明确的自发布施行2020-07-08；2025创新药临床审批公告的原页第26行明确“本公告自发布之日起实施”，此前新增日期审计仍为null，此处按原公开日2025-09-12补入，保留两套prior值及确切依据。二者均不改变主年度，详情见verification.json.metadata_corrections。

56为51条目下列示组件，不是已认证56个独立政策文件。已保留2022医保方案169条（方案含通知63、竞价34、续约72）与2025医保方案403条（方案含通知78、申报57、续约83、官方问答185）的原计数。独立component_id、4481逐单元组件归属、逐组件日期、覆盖和同月日窗口规则仍pending。每条映射component_id保持null；不按路径猜独立文件，不用source-entry日期覆盖全部bundle组件的日级时间筛选。下游51条目年度分析可以接入本映射；56组件等权或组件日期敏感性须另验收。

2017是全局无纳入来源年；另有9个空department×year单元。赋年缺失/部门缺失均为0条，与真正无源单元分开。空单元条款数/条目数可为0，下游q/p应NA(no_observed_source)，不能填五维0。2026统一标截至2026-07-31；其他年份仅完整日历边界的所收集文本，不是穷尽政策普查。

本交付仅写当前新目录，Goal/progress、原方法plan、固定框、原材料、标签文件均未改。seal.json绑定全部交付文件哈希及只读输入。build_metadata.py是复现程序；任何原输入漂移都会失败。
'''
(OUT / '说明.txt').write_text(readme)
outputs = []
for p in sorted(OUT.rglob('*')):
    if p.is_file() and p.name != 'seal.json':
        outputs.append({'relative_path': str(p.relative_to(OUT)), 'sha256': sha(p), 'bytes': p.stat().st_size})
write_json('seal.json', {'schema': 'annual-metadata-integrated-seal-v1', 'created_at': STAMP, 'root': str(OUT), 'status': 'complete_source_entry_maps_components_pending', 'cutoff': CUTOFF, 'source_frame_sha256': sha(frame_path), 'analysis_plan_sha256': sha(PLAN_DIR / 'report.json'), 'original_publication_audit_metadata_sha256': sha(AUDIT_DIR / 'metadata.json'), 'original_publication_audit_seal_sha256': sha(AUDIT_DIR / 'seal.json'), 'metadata_sha256': sha(OUT / 'metadata.json'), 'main_year_map_sha256': sha(OUT / 'source-id-year-map.jsonl'), 'publication_year_sensitivity_map_sha256': sha(OUT / 'source-id-publication-year-map.jsonl'), 'inputs': list(INPUTS.values()), 'file_n': len(outputs), 'files': outputs, 'only_this_new_directory_written': True, 'labels_read_or_computed': False, 'component_map_status': 'pending'})
print(json.dumps(verification, ensure_ascii=False, indent=2))
