"""One source-bound sampling-description correction; preserves the sealed draft."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE / '完整论文局部替换稿.json'
NEW = HERE / '完整论文局部替换稿-v4.json'
AUDIT = HERE.parent / 'methods-20261008/sampling-scope-readonly-audit/P47抽样范围局部修正依据.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    assert sha(OLD) == '8a653f4e65487c85913d361d39046523e82d78c8a47a8d606b0925a9a8278675'
    assert sha(AUDIT) == '2335b238b2ca171dc5d652b78384b871611e4d1bb2199fd4ae1cf70adba7713f'
    evidence = json.loads(AUDIT.read_text())
    assert evidence['status'] == 'PASS_FROZEN_ADMIN_EVIDENCE_READONLY'
    assert len(evidence['checks']) == 14 and all(evidence['checks'].values())
    for binding in evidence['bindings']:
        assert sha(Path(binding['path'])) == binding['sha256']
    draft = json.loads(OLD.read_text())
    prior = json.loads(OLD.read_text())
    target = next(r for r in draft['replacements'] if r['zero_based_body_p_index'] == 47)
    old_first, remainder = target['replacement_text'].split('。', 1)
    assert old_first.startswith('从排除既往开发材料后的同文家族中各取一个规范代表')
    target['replacement_text'] = evidence['recommended_replace_first_sentence_only'] + remainder
    changed = [b['zero_based_body_p_index'] for a, b in zip(prior['replacements'], draft['replacements']) if a != b]
    assert changed == [47]
    assert len(draft['replacements']) == 52 and len(draft['measurement_fields']) == 39
    assert all(draft[k] == prior[k] for k in prior if k != 'replacements')
    md_path = HERE / '完整论文局部替换稿-v4.md'
    manifest_path = HERE / '局部替换稿v4抽样描述修正绑定.json'
    assert not any(p.exists() for p in (NEW, md_path, manifest_path))
    NEW.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + '\n')
    md = ['# 完整论文局部替换稿 v4', '',
          '仅修正P47抽样框排除范围的描述。52段、39个待填字段、引用和旧文锚点均保留；没有生成DOCX，没有变更样本、权重、标签或统计。', '']
    for row in draft['replacements']:
        md.extend([f"P{row['zero_based_body_p_index']}", '', row['replacement_text'], ''])
    md_path.write_text('\n'.join(md) + '\n')
    manifest = {'status': 'PASS_ONE_PARAGRAPH_SOURCE_BOUND_CORRECTION_NOT_FINAL_MANUSCRIPT',
                'previous_staged': {'path': str(OLD), 'sha256': sha(OLD)},
                'sampling_evidence': {'path': str(AUDIT), 'sha256': sha(AUDIT)},
                'producer': {'path': str(Path(__file__).resolve()), 'sha256': sha(Path(__file__).resolve())},
                'new_staged': {'path': str(NEW), 'sha256': sha(NEW)},
                'preview': {'path': str(md_path), 'sha256': sha(md_path)},
                'changed_paragraphs': changed, 'old_first_sentence': old_first + '。',
                'new_first_sentence': evidence['recommended_replace_first_sentence_only'],
                'other51_paragraphs_exactly_unchanged': True, 'all39_field_definitions_unchanged': True,
                'all_citations_unchanged': True, 'samples_weights_labels_statistics_changed': False,
                'original_staged_preserved': sha(OLD) == '8a653f4e65487c85913d361d39046523e82d78c8a47a8d606b0925a9a8278675',
                'cross_department_actual_excluded_families': 0, 'DOCX_generated': False}
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'status': manifest['status'], 'new_staged': manifest['new_staged'],
                      'manifest_sha256': sha(manifest_path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
