"""Read-only final binding checks and record the root's completed visual review."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

root = Path(__file__).resolve().parent
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
read = lambda p: json.loads(Path(p).read_text())
freeze_path = root / 'V600-最终冻结清单.json'
freeze = read(freeze_path)
for item in freeze['files'].values():
    assert sha(item['path']) == item['sha256']
primary_path = root / 'V600-正式成对统计.json'
secondary_path = root / 'V600-预定敏感性统计.json'
primary, secondary = read(primary_path), read(secondary_path)
archive = primary['archive']
assert archive['input_snapshot_hashes']['freeze'] == sha(freeze_path)
assert secondary['source_primary_sha256'] == sha(primary_path)
assert secondary['freeze_manifest_sha256'] == sha(freeze_path)
assert len(archive['original_submission_manifest']) == 48
for name, record in archive['original_submission_manifest'].items():
    assert sha(root / 'V600' / name) == record['sha256']
    assert sha(root / 'V600-原始提交接收' / name) == record['sha256']
old_results = {
    'H600-正式统计.json': '2aecc0a417c2aef3d84d1b05bccd7c46c4fd292e62a813f529af1c54523e2cfd',
    'R200-描述统计.json': '21b5eee108dd745b72bbbc977ae30697f61f309e59ea7a6d76d3fe84421ba62d',
}
for name, digest in old_results.items():
    assert sha(root / name) == digest
books, previews = {}, {}
folder = root / 'V600工作簿交付'
for c in ('A', 'C'):
    book = folder / f'新增验证600-{c}-AI评审.xlsx'
    qa_path = folder / f'v600-{c}-raw-QA.json'
    qa = read(qa_path)
    assert qa['workbook_sha256'] == sha(book)
    assert qa['completed_results_sha256'] == sha(primary_path)
    assert qa['freeze_sha256'] == sha(freeze_path)
    assert qa['all_cells_match_display_plan'] and qa['all_original_fields_reconstructed']
    assert qa['analysis_units'] == qa['main_display_rows'] == 600
    assert qa['formula_or_error_cells'] == 0
    books[c] = {'path': str(book), 'sha256': sha(book), 'raw_QA_sha256': sha(qa_path),
                'original_field_count': qa['original_field_count'], 'analysis_units': 600,
                'main_display_rows': 600, 'builder_sha256': qa['builder_sha256']}
    for suffix in ('labels', 'reasons', 'end', 'contexts', 'contexts-end', 'manual',
                   'clarifications', 'instructions', 'full-heading'):
        p = folder / f'v600-{c}-{suffix}.png'
        previews[str(p)] = sha(p)
stamp = datetime.now(timezone.utc).isoformat()
delivery = {'status': 'V600_workbooks_exported_and_bound_to_complete_originals', 'checked_at': stamp,
            'books': books, 'frozen_files_unchanged': len(freeze['files']),
            'first_submission_files_unchanged': 48, 'primary_sha256': sha(primary_path),
            'secondary_sha256': sha(secondary_path), 'historical_result_hashes_unchanged': old_results,
            'no_recoding_or_statistics_rerun': True}
visual = {'status': 'representative_ranges_visually_reviewed', 'reviewer': 'root AI coordinator',
          'checked_at': stamp, 'books': books, 'preview_hashes': previews,
          'scope': 'Each of four sheets in both workbooks; main first rows/reasons/last rows, context first/last fields, manual, common clarification, instructions; full merged main header reimported from saved XLSX.',
          'observations': ['Labels 0/1 and pending remain visible; pending has a distinct text label and fill.',
                           'Main rows preserve 600 units in each workbook; both independent rationales remain separate.',
                           'Representative text wrapping, headings and tail fields are readable without observed clipping.',
                           'Initial A:H preview omitted merged A:J title; additional read-only A:J renders verified the saved header. No workbook change was needed.',
                           'Read-only full-field checks allow reversible literal-text escaping and reconstruct the original fields exactly.'],
          'limitations': ['Representative visual review, not a screenshot review of every metadata row.',
                          'Artifact-tool export/import checked; native Microsoft Excel interaction was not exercised.',
                          'Layout and byte checks do not establish semantic label correctness or true human expertise.']}
for name, obj in [('V600-工作簿交付核验.json', delivery), ('V600-工作簿视觉核验.json', visual)]:
    with (root / name).open('x') as stream:
        json.dump(obj, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
print(json.dumps({'status': delivery['status'], 'workbooks': 2, 'units_per_coder': 600,
                  'frozen_files_unchanged': len(freeze['files']), 'previews_reviewed': len(previews)}, ensure_ascii=False))
