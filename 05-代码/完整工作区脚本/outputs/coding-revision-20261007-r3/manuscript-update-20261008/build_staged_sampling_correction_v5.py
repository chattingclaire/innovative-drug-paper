"""Restore the unchanged sampling-operation clause in a new source-bound v5 draft."""
import hashlib
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE / '完整论文局部替换稿.json'
V4 = HERE / '完整论文局部替换稿-v4.json'
NEW = HERE / '完整论文局部替换稿-v5.json'
AUDIT = HERE.parent / 'methods-20261008/sampling-scope-readonly-audit/P47抽样范围局部修正依据.json'
REVIEW = HERE / 'integration-preflight/v4抽样描述与绑定独立复核-20261008.json'
OPERATION = '按部门简单随机不放回各抽60条，共180条，卫健为框内全查。'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def bind(path):
    return {'path': str(path), 'sha256': sha(path)}


def require(value, message):
    if not value:
        raise ValueError(message)


def main():
    expected = {OLD: '8a653f4e65487c85913d361d39046523e82d78c8a47a8d606b0925a9a8278675',
                V4: 'f065566c348591a5c2217ec43427c6293081c133f9584a84c7ea0a608b6f8158',
                AUDIT: '2335b238b2ca171dc5d652b78384b871611e4d1bb2199fd4ae1cf70adba7713f',
                REVIEW: 'd56e148ebe6d9b43a27c793b7653da6bc61584fb13be56f7b8e54bc80b50ed11'}
    for path, digest in expected.items():
        require(sha(path) == digest, 'Changed source: ' + str(path))
    protected = {p: sha(p) for p in [OLD, HERE/'完整论文局部替换稿.md', HERE/'build_complete_staged_prose.py',
                 V4, HERE/'完整论文局部替换稿-v4.md', HERE/'build_staged_sampling_correction_v4.py',
                 HERE/'局部替换稿v4抽样描述修正绑定.json', HERE/'新引用接入清单.json',
                 *sorted((HERE/'integration-preflight').glob('*v4*.*')),
                 *sorted((HERE/'integration-preflight/snapshot-20261008-v4').iterdir())] if p.is_file()}
    evidence = json.loads(AUDIT.read_text())
    require(evidence['status'] == 'PASS_FROZEN_ADMIN_EVIDENCE_READONLY', 'Audit not passed')
    require(len(evidence['checks']) == 14 and all(evidence['checks'].values()), 'Missing audit checks')
    for binding in evidence['bindings']:
        require(sha(Path(binding['path'])) == binding['sha256'], 'Changed audit dependency')
    draft = json.loads(OLD.read_text())
    prior = json.loads(OLD.read_text())
    v4 = json.loads(V4.read_text())
    target = next(r for r in draft['replacements'] if r['zero_based_body_p_index'] == 47)
    old_first, remainder = target['replacement_text'].split('。', 1)
    require(old_first.endswith('；' + OPERATION[:-1]), 'Original operation clause differs')
    first = evidence['recommended_replace_first_sentence_only']
    require(first.endswith('。'), 'Exclusion sentence punctuation differs')
    target['replacement_text'] = first + OPERATION + remainder
    changed = [b['zero_based_body_p_index'] for a, b in zip(prior['replacements'], draft['replacements']) if a != b]
    require(changed == [47], 'Unexpected paragraph change')
    require(len(draft['replacements']) == 52 and len(draft['measurement_fields']) == 39, 'Unexpected scope')
    require(all(draft[k] == prior[k] for k in prior if k != 'replacements'), 'Top-level contract changed')
    cite = re.compile(r'\[[0-9,，;；\s–—-]+\]|〔[A-Za-z][A-Za-z0-9_;；,，\s]*〕')
    require([cite.findall(r['replacement_text']) for r in draft['replacements']] ==
            [cite.findall(r['replacement_text']) for r in prior['replacements']], 'Citation tokens changed')
    require(all(a['old_text'] == b['old_text'] and a['old_text_sha256'] == b['old_text_sha256']
                for a,b in zip(prior['replacements'],draft['replacements'])), 'Baseline anchors changed')
    v4p47 = next(r for r in v4['replacements'] if r['zero_based_body_p_index'] == 47)
    require(v4p47['replacement_text'] == first + remainder, 'v4 difference unexpected')
    md_path = HERE / '完整论文局部替换稿-v5.md'
    manifest_path = HERE / '局部替换稿v5抽样描述修正绑定.json'
    require(not any(p.exists() for p in (NEW, md_path, manifest_path)), 'Refuse overwriting previous outputs')
    with NEW.open('x') as f:
        f.write(json.dumps(draft, ensure_ascii=False, indent=2) + '\n')
    md = ['# 完整论文局部替换稿 v5', '',
          '仅在封存原52段的P47修正抽样框排除范围，并原样保留简单随机不放回各抽60条、共180条及卫健框内全查的操作说明。其余51段、39个待填字段、引用和旧文锚点均不变。没有生成DOCX，没有变更样本、权重、标签或统计。v4存在抽样操作句遗漏，不得用于最终成稿。', '']
    for row in draft['replacements']:
        md.extend([f"P{row['zero_based_body_p_index']}", '', row['replacement_text'], ''])
    with md_path.open('x') as f:
        f.write('\n'.join(md) + '\n')
    require(all(sha(p) == h for p,h in protected.items()), 'Protected input changed')
    manifest = {'status': 'PASS_P47_EXCLUSION_CORRECTION_WITH_ORIGINAL_SAMPLING_OPERATION_RETAINED_NOT_FINAL_MANUSCRIPT',
                'previous_staged': bind(OLD), 'superseded_v4': bind(V4), 'sampling_evidence': bind(AUDIT),
                'v4_independent_review': bind(REVIEW), 'producer': bind(Path(__file__).resolve()),
                'new_staged': bind(NEW), 'preview': bind(md_path), 'changed_paragraphs': changed,
                'old_first_sentence': old_first + '。', 'new_exclusion_sentence': first,
                'original_operation_retained_verbatim': OPERATION, 'remaining_P47_text_unchanged': True,
                'other51_paragraphs_exactly_unchanged': True, 'all39_field_definitions_unchanged': True,
                'all_citation_tokens_and_original_text_anchors_unchanged': True,
                'cross_department_actual_excluded_families': 0,
                'samples_weights_labels_statistics_changed': False, 'DOCX_generated_or_modified': False,
                'v4_may_be_used_for_final_manuscript': False,
                'v4_reason': 'Historical frozen version omitted the original sampling-operation clause; use v5 for the corrected source text after actual adoption gates are satisfied.',
                'protected_inputs_preserved': [{'path': str(p), 'sha256': h} for p,h in protected.items()]}
    with manifest_path.open('x') as f:
        f.write(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'new_staged': bind(NEW), 'manifest': bind(manifest_path),
                      'protected_input_n': len(protected)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
