from pathlib import Path
import hashlib
import json
import re
import zipfile
import xml.etree.ElementTree as ET

PROJECT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
W = PROJECT / 'outputs/编码修订核查-20261008'
OUT = W / '正文同步/用途澄清独立核查'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
NAMES = ['创新药评价的注意力配置差异与协调路径.docx', '编码复核说明与真人检验事项.docx']
EXPECTED_NEW = ['2335ad123737735ea5ae32234de323d3c7ae1ac0c23136d4d2eb7a2742b15db6', '11a01f77b5830c12f58b8bbc9ce446a273d9af206ea4e9ed2f6bcf8ea8604cbb']
EXPECTED_OLD = ['9f817ee2cec4c1696fc2e0b724eea49670e48190911943fe1cfb3b9ed7561489', '441b742713b1f7abc6b3ae2272a413949d9779ad94122e9807c0335c44e2f874']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def text(element):
    return ''.join(x.text or '' for x in element.findall('.//w:t', NS))

def load(path):
    with zipfile.ZipFile(path) as z:
        package = {name: z.read(name) for name in z.namelist()}
    root = ET.fromstring(package['word/document.xml'])
    paragraphs = root.findall('w:body/w:p', NS)
    tables = root.findall('w:body/w:tbl', NS)
    return package, root, paragraphs, tables

def citations(paragraphs):
    result = []
    for p in paragraphs:
        value = text(p)
        if re.match(r'^\[\d+\]', value):
            continue
        result.extend(re.findall(r'\[\d+(?:[,，–—-]\d+)*\]', value))
    return result

reports = []
for index, name in enumerate(NAMES):
    old = W / '正文同步/澄清人工验证用途前记录' / name
    new = W / '本轮结果' / name
    assert sha(old) == EXPECTED_OLD[index]
    assert sha(new) == EXPECTED_NEW[index]
    ao, ro, po, to = load(old)
    an, rn, pn, tn = load(new)
    assert len(po) == len(pn)
    differences = [{'paragraph_index_zero_based': i, 'before': text(a), 'after': text(b)}
                   for i, (a, b) in enumerate(zip(po, pn)) if text(a) != text(b)]
    expected_indices = [51, 57, 110] if index == 0 else [8]
    assert [x['paragraph_index_zero_based'] for x in differences] == expected_indices
    changed_paragraph_xml = [i for i, (a, b) in enumerate(zip(po, pn))
                             if ET.tostring(a) != ET.tostring(b)]
    assert changed_paragraph_xml == expected_indices
    assert len(to) == len(tn)
    for a, b in zip(to, tn):
        assert ET.tostring(a) == ET.tostring(b)
        assert [text(c) for c in a.findall('.//w:tc', NS)] == [text(c) for c in b.findall('.//w:tc', NS)]
    assert set(ao) == set(an)
    package_differences = [k for k in ao if ao[k] != an[k]]
    assert package_differences == ['word/document.xml']
    image_names = [k for k in ao if k.startswith('word/media/')]
    assert all(ao[k] == an[k] for k in image_names)
    old_refs = [text(p) for p in po if re.match(r'^\[\d+\]', text(p))]
    new_refs = [text(p) for p in pn if re.match(r'^\[\d+\]', text(p))]
    assert old_refs == new_refs
    old_citations, new_citations = citations(po), citations(pn)
    assert old_citations == new_citations
    if index == 0:
        assert len(new_refs) == 66
        assert len(new_citations) == 95
        citation_runs = [run for run in pn[57].findall('.//w:r', NS) if text(run) == '[49]']
        assert len(citation_runs) == 1
        assert citation_runs[0].find('w:rPr/w:vertAlign', NS).get('{'+NS['w']+'}val') == 'superscript'
    reports.append({
        'name': name, 'old_path': str(old), 'old_sha256': sha(old),
        'current_path': str(new), 'current_sha256': sha(new),
        'paragraph_count': len(pn), 'text_and_xml_changed_paragraphs': changed_paragraph_xml,
        'actual_changes': differences, 'table_count': len(tn),
        'all_table_xml_and_cell_text_unchanged': True,
        'all_package_members_unchanged_except': package_differences,
        'image_names_all_byte_identical': image_names,
        'reference_count': len(new_refs), 'reference_text_and_order_unchanged': True,
        'body_citation_count': len(new_citations), 'body_citation_sequence_unchanged': True,
    })

freeze_path = W / '统计复算/完整39与LLM03-同步复算01/output_freeze.json'
assert sha(freeze_path) == 'f411935421447c6fd39fdf1887078dc6ba297e201ac5bed6498befe2ba753c3a'
freeze = json.loads(freeze_path.read_text())
hashed_items = []
for item in [freeze['bindings'], freeze['entrypoint']] + freeze['files']:
    p = Path(item['path'])
    if not p.is_absolute():
        p = PROJECT / p
    assert sha(p) == item['sha256'], str(p)
    assert p.stat().st_size == item['bytes'], str(p)
    hashed_items.append({'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size})
csv_checks = []
for name, expected in [
    ('编码检验补充统计表.csv', 'a4c2e4725a1e98dcb541cc7081c029ba787d61f44f833f44df664c296febf8ae'),
    ('维度共同表达补充统计表.csv', '4602177a2859d1bb241b719e46458c62bafa5673c7925c16bbcc1144abdb0f18'),
]:
    p = W / '本轮结果' / name
    assert sha(p) == expected
    csv_checks.append({'path': str(p), 'sha256': sha(p), 'unchanged_from_previous_independent_cell_review': True})

report = {
    'status': 'PASS_WITHIN_REQUESTED_CONTENT_AND_BYTE_IDENTITY_SCOPE',
    'date': '2026-10-08',
    'scope': 'Current purpose-clarification DOCX delta, exact package/table/image/reference/citation identity, frozen statistical outputs and two CSV byte identity. No model, sampling, scoring, individual input or reserved material read.',
    'documents': reports,
    'main_p57_citation_49_is_explicit_superscript': True,
    'preserved_value_binding': {
        'main_table2_80_values': 'Entire table XML and all cell texts identical to previously independently source-checked final manuscript.',
        'main_table3_30_values': 'Entire table XML and all cell texts identical to previously independently source-checked final manuscript.',
        'companion_25_kappa_values': 'Entire table XML and all cell texts identical to previously independently source-checked corrected companion.',
        'previous_source_review': str(W / '正文同步/独立正文审查/independent_final_manuscript_companion_review.json'),
        'previous_source_review_sha256': sha(W / '正文同步/独立正文审查/independent_final_manuscript_companion_review.json'),
    },
    'statistics_freeze': {'path': str(freeze_path), 'sha256': sha(freeze_path), 'all_20_declared_items_verified': hashed_items},
    'csv_checks': csv_checks,
    'semantic_review': {
        'p51': '0.80 retained as a development-stage diagnostic goal; no new statement that it is a universal publication threshold or that all goals passed. Definitions and low reported values preserved.',
        'p57': '180 probability units primarily validate coding quality. Same-sample attention distribution is auxiliary diagnosis within the remaining canonical sampling frame. The two complete machine outputs independently determine full-corpus 4481 distributions. No human-sample/full-corpus equality acceptance imposed.',
        'p110': 'Initial judgments and human-adjudicated results distinguished, consistent with unchanged p49. No new claim of independent human inter-coder validation.',
        'companion_p8': 'A/B are human-adjudicated references for sample coding; sample distribution/conditional proportions are auxiliary error-impact checks; full-corpus attention is calculated separately from complete machine versions. Machine agreement does not replace quality validation.',
        'remaining_results_and_conclusion': 'Byte-identical to previous source-checked manuscript. In particular 14/15 directional agreement and the NHSA/NHC innovation reversal remain unchanged.',
        'blocking_issue_found': False,
    },
    'visual_scope': 'Not repeated here; root conducts render and visual inspection.',
}
OUT.mkdir(parents=True, exist_ok=True)
target = OUT / '用途澄清_独立内容与来源核查.json'
assert not target.exists(), 'Refuse to overwrite prior audit'
target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'status': report['status'], 'report': str(target), 'sha256': sha(target),
                  'changed_paragraphs': [[51,57,110],[8]], 'statistics_bound_items': len(hashed_items),
                  'table_image_reference_citation_csv_unchanged': True, 'citation_49_superscript': True}, ensure_ascii=False))
