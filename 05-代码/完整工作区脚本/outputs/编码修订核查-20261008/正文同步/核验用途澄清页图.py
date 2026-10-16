from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parent
OUT = ROOT.parent / '本轮结果'

def binding(p):
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}

main = OUT / '创新药评价的注意力配置差异与协调路径.docx'
memo = OUT / '编码复核说明与真人检验事项.docx'
assert binding(main)['sha256'] == '2335ad123737735ea5ae32234de323d3c7ae1ac0c23136d4d2eb7a2742b15db6'
assert binding(memo)['sha256'] == '11a01f77b5830c12f58b8bbc9ce446a273d9af206ea4e9ed2f6bcf8ea8604cbb'

groups = []
for label, old_dir, new_dir, count, viewed in [
    ('main', '渲染正文', '渲染用途澄清正文', 21, [8, 9, 17]),
    ('memo', '渲染说明', '渲染用途澄清说明', 3, [2, 3]),
]:
    pages = []
    changed = []
    for n in range(1, count + 1):
        old = ROOT / old_dir / f'page-{n}.png'
        new = ROOT / new_dir / f'page-{n}.png'
        same = binding(old)['sha256'] == binding(new)['sha256']
        if not same:
            changed.append(n)
        assert same or n in viewed, f'Unreviewed changed image: {new}'
        pages.append({'page': n, 'current': binding(new), 'previous': binding(old), 'review_basis': 'byte_identical_to_previously_actually_reviewed_image' if same else 'root_actually_viewed_original_image', 'visual_issue_observed': False})
    assert changed == viewed, (label, changed, viewed)
    groups.append({'document': label, 'pages': count, 'changed_pages_actually_viewed': changed, 'page_coverage': pages})

result = {
    'status': 'PASS_INCREMENTAL_ACTUAL_VISUAL_REVIEW',
    'scope': 'Changed original PNGs were actually displayed and visually inspected by root. Unchanged PNGs are bound byte-for-byte to the previous actual-review coverage; they are not represented as newly viewed.',
    'documents': [binding(main), binding(memo)],
    'groups': groups,
    'observations': ['Main pages 8, 9 and 17: text, table 2, table 3 and appendix transitions remain readable; no clipping, overlap or broken table borders observed.', 'Memo pages 2 and 3: role clarification, threshold explanation and follow-up sections remain readable with normal page continuation.'],
    'previous_delivery_seal': binding(ROOT / '澄清人工验证用途前记录' / '当前采用稿交付封存.json'),
    'not_a_coding_semantic_validation_or_publication_certification': True,
}
dest = ROOT / '用途澄清实际页图核查.json'
assert not dest.exists()
dest.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'path': str(dest), 'sha256': binding(dest)['sha256'], 'main_changed': [8, 9, 17], 'memo_changed': [2, 3]}, ensure_ascii=False))
