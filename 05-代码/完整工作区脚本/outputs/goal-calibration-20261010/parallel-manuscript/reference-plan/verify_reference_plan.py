#!/usr/bin/env python3
"""Verify bookkeeping, provenance bytes, and non-mutation for the source plan."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import json
import re
import hashlib
import zipfile
import xml.etree.ElementTree as ET

BASE = Path(__file__).resolve().parent
PARENT = BASE.parent
checks = []


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(name):
    return json.loads((BASE / name).read_text())


def check(name, passed, detail=None):
    checks.append({'check': name, 'passed': bool(passed), 'detail': detail})


p = read('core-reference-coverage.json')
f = read('bibliographic-fixes.json')
m = read('planning_input_manifest.json')
s = read('later-steering-input.json')
core = p['core_references']
conditional = p['conditional_references']
legacy = p['legacy_66_dispositions']
core_ids = {x['id'] for x in core}
conditional_ids = {x['id'] for x in conditional}

check('core_count_23_unique', len(core) == len(core_ids) == 23)
check('core_21_legacy_2_new', sum(x['legacy_number'] is not None for x in core) == 21 and sum(x['legacy_number'] is None for x in core) == 2)
check('policy_core_12', len(core_ids & {f'R{x:03d}' for x in [2,3,35,36,37,39,40,52,55,58,59,61]}) == 12)
check('conditional_31_unique', len(conditional) == len(conditional_ids) == 31)
check('core_and_conditional_disjoint', not core_ids & conditional_ids)
check('legacy_66_complete_unique', len(legacy) == 66 and {x['original_number'] for x in legacy} == set(range(1,67)))
check('legacy_disposition_21_23_22', [sum(x['planned_disposition'] == y for x in legacy) for y in ['core','conditional','development_or_redundant_after_claim_removal']] == [21,23,22])
check('all21_steps_unique', len(p['steps_21_coverage']) == 21 and {x['id'] for x in p['steps_21_coverage']} == {f'M{x:02d}' for x in range(1,22)})
check('no_per_step_single_paper_requirement', all(x['standalone_citation_required'] is False for x in p['steps_21_coverage']))
for row in p['steps_21_coverage']:
    check('step_reference_ids_exist_' + row['id'], set(row['core_refs'] + row['conditional_refs']) <= core_ids | conditional_ids)

for x in core:
    src = x['source']
    check('core_metadata_and_locator_' + x['id'], bool(src['bibliography'] and src['publication_year'] and src['actual_reading_level'] and src['actual_locator']))
    check('core_original_support_boundary_' + x['id'], bool(src['supports'] and src['does_not_support'] and x['no_expansion']))
    check('core_read_scope_not_inflated_' + x['id'], src['whole_text_read_this_round'] is False)
    check('core_primary_url_or_doi_' + x['id'], bool(src.get('doi') or src.get('primary_urls')))

source = next(x for x in m['files'] if x['id'] == 'current-manuscript')
check('authoritative_docx_original_unchanged', sha(source['original_path']) == source['sha256'], source['original_path'])
with zipfile.ZipFile(source['original_path']) as archive:
    root = ET.fromstring(archive.read('word/document.xml'))
ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
# The current DOCX stores reference numbers as displayed [n] prefixes.
paras = [''.join(t.text or '' for t in q.findall('.//w:t', ns)).strip() for q in root.findall('.//w:body/w:p', ns)]
for item in legacy:
    numbered = '[' + str(item['original_number']) + '] ' + item['original_entry_unchanged'].strip()
    check('original_reference_preserved_' + item['id'], numbered in paras)

for entry in m['files'] + s['files']:
    check('input_snapshot_bytes_' + Path(entry['snapshot_path']).name, sha(entry['snapshot_path']) == entry['sha256'], entry['snapshot_path'])
# Immutable manuscript and old delivery bytes are verified live. Progress and
# statistical code can legitimately advance in the main task after snapshot.
for seal_name in [PARENT / '交付封存.json', PARENT / 'interview-audit/交付封存.json']:
    sealed = json.loads(seal_name.read_text())
    for entry in sealed['outputs']:
        check('earlier_seal_preserved_' + str(Path(entry['path']).relative_to(PARENT)), sha(entry['path']) == entry['sha256'])

seen = {}
remote = []
for item in core + conditional:
    for e in item['source'].get('evidence', []):
        path = e.get('path', e.get('source_path'))
        expected = e.get('sha256', e.get('source_sha256'))
        if not path:
            if expected:
                remote.append({'id': item['id'], 'url': e.get('url', e.get('official_url')), 'sha256': expected,
                               'note': '内存读取哈希；未持久保存文件，不作本地重验'})
            continue
        if not expected:
            continue
        if path in seen:
            check('duplicate_source_hash_agrees_' + item['id'], seen[path] == expected)
            continue
        seen[path] = expected
        check('local_source_bytes_' + item['id'] + '_' + Path(path).name, Path(path).exists() and sha(path) == expected, path)

check('bibliographic_edits_not_applied', f['applied_changes'] == 0 and all(x['applied'] is False for x in f['fixes']))
check('Guo_year_guard_preserved', any(x['id'] == 'R026' and x.get('issue_year') == 2023 for x in f['fixes']))
check('R51_year_guard_preserved', any(x['id'] == 'R051' and x.get('publication_date') == '2025-09-12' for x in f['fixes']))
check('Tornberg_is_conditional', 'R066' in conditional_ids and 'R066' not in core_ids)
check('bootstrap_direct_source_conditional', 'N-BE2022' in conditional_ids and 'R049' in conditional_ids)
check('bootstrap5000_project_parameter', '5000' in p['bootstrap_citation_implementation_match']['declared_primary'] and '项目' in p['bootstrap_citation_implementation_match']['decisions'][4])
check('still_not_final_empirical_acceptance', p['scope']['final_empirical_acceptance_asserted'] is False and '未' in s['execution_status'])
check('0_80_not_publication_threshold', any('不是统一文献发表阈值' in t for t in p['critical_claim_boundaries']))

md = (BASE / 'core-reference-coverage.md').read_text()
check('markdown_has_23_core_rows', sum(x.startswith('| R') or x.startswith('| N-') for x in md.split('## 一、')[1].split('## 二、')[0].splitlines()) == 23)
check('markdown_has_21_step_rows', sum(x.startswith('| M') for x in md.split('## 四、')[1].split('## 五、')[0].splitlines()) == 21)
for target in re.findall(r'\]\(<(/[^>]+)>\)', md):
    check('markdown_local_link_exists_' + Path(target).name, Path(target).exists())

result = {'created_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(), 'status': 'PASS' if all(x['passed'] for x in checks) else 'FAIL',
          'checks_total': len(checks), 'failures': [x for x in checks if not x['passed']], 'checks': checks,
          'local_provenance_files_checked': len(seen), 'remote_memory_hashes_not_rechecked_as_local': remote,
          'limitations': '机械检查确认清单/编号/载体/旧交付不变；不把哈希或通过状态当作全文语义核验、真人信度或新实证验收。'}
(BASE / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
if result['status'] != 'PASS':
    print(json.dumps({'status': result['status'], 'failures': result['failures']}, ensure_ascii=False))
    raise SystemExit(1)

outputs = []
for path in sorted(BASE.rglob('*')):
    if path.is_file() and path.name != '交付封存.json' and '__pycache__' not in path.parts:
        outputs.append({'path': str(path), 'sha256': sha(path)})
seal = {'created_at': result['created_at'], 'status': 'reference_preparation_complete', 'validation_status': result['status'],
        'checks_total': len(checks), 'outputs': outputs, 'original_manuscript_modified': False,
        'legacy_references_preserved': 66, 'earlier_deliveries_preserved': True, 'citations_replaced': False,
        'scope': '来源预案及书目修正建议封存；不代表主任务指标合规或完整论文完成'}
(BASE / '交付封存.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': result['status'], 'checks': len(checks), 'local_source_files': len(seen), 'sealed_files': len(outputs)}, ensure_ascii=False))
