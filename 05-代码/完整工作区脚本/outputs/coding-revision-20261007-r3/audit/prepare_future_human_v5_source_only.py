"""Refresh both complete 240-row blank packages to v14, without resampling."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import copy
import csv
import hashlib
import json
import shutil

B = Path(__file__).resolve().parents[1]; ROOT = B.parents[1]
OLD = B / 'future-human-validation-v4'; OUT = B / 'future-human-validation-v5'; ADMIN = B / 'admin'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
obj = lambda p: json.loads(Path(p).read_text())
def dump(p, value):
    assert not p.exists(), 'Never overwrite a frozen package'
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

assert not OUT.exists()
private_path = ADMIN / 'future_human_v4_sampling_PRIVATE.json'
s = obj(private_path); assert s['execution_status'] == 'not_started_no_real_human_labels'
old_private_sha = sha(private_path)
prior_hashes = {str(p.relative_to(ROOT)): sha(p) for p in sorted(OLD.rglob('*')) if p.is_file()}
source_paths = [B / name for name in ['effective_blind_inputs_v14.jsonl', 'rule_inputs_shared_v14.jsonl', 'material_v14_manifest.json']]
source_hashes = {str(p.relative_to(ROOT)): sha(p) for p in source_paths}
full = {x['id']: x for x in map(json.loads, (B / 'effective_blind_inputs_v14.jsonl').read_text().splitlines())}
prior_full = {x['id']: x for x in map(json.loads, (B / 'effective_blind_inputs_v13.jsonl').read_text().splitlines())}
expected = {'RECODE25-04371', 'RECODE25-04390'}
OUT.mkdir(); shutil.copytree(OLD / '手册', OUT / '手册')
mapping = []; changed = {}; maxctx = 0
for coder in ['A', 'C']:
    package = obj(OLD / f'真人{coder}-无答案材料.json')
    lookup = {x['blind_id']: x['original_id'] for x in s['mapping'] if x['coder'] == coder}
    with (OLD / f'真人{coder}-空白编码表.csv').open(encoding='utf-8-sig', newline='') as f:
        prior_csv = list(csv.DictReader(f))
    headers = list(prior_csv[0]); oldrows = copy.deepcopy(package['rows']); changes = []
    assert len(oldrows) == len(lookup) == len(prior_csv) == 240
    assert all(package[k] == '' for k in ['coder_name', 'professional_background', 'execution_date'])
    for n, (row, prev, csvrow) in enumerate(zip(package['rows'], oldrows, prior_csv), 1):
        orig = lookup[prev['id']]; current = full[orig]
        assert row['text'] == current['text'] and row['source_title'] == current['source_title'] and row['pages'] == current['pages']
        assert row['contexts'] == prior_full[orig]['contexts']
        assert all(v == '' for v in row['coding'].values())
        assert csvrow['匿名编号'] == prev['id'] and csvrow['政策原文'] == row['text'] and json.loads(csvrow['完整语境JSON']) == row['contexts']
        assert all(csvrow[k] == '' for k in row['coding'])
        row['id'] = f'HV5-{coder}-{n:04d}'
        row['contexts'] = copy.deepcopy(current['contexts']); row['context_usage'] = current['context_usage']
        mapping.append({'coder': coder, 'blind_id': row['id'], 'original_id': orig, 'v4_blind_id': prev['id']})
        maxctx = max(maxctx, len(json.dumps(row['contexts'], ensure_ascii=False)))
        if row['contexts'] != prev['contexts']:
            changes.append({'blind_id': row['id'], 'original_id': orig, 'v4_blind_id': prev['id']})
    assert {x['original_id'] for x in changes} == expected
    changed[coder] = changes
    package.update(package_version='v5', material_version='v14', source_material_sha256=sha(B / 'effective_blind_inputs_v14.jsonl'))
    dump(OUT / f'真人{coder}-无答案材料.json', package)
    with (OUT / f'真人{coder}-空白编码表.csv').open('w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=headers); w.writeheader()
        for row in package['rows']:
            w.writerow({'匿名编号': row['id'], '政策原文': row['text'], '来源标题': row['source_title'], '页码': json.dumps(row['pages'], ensure_ascii=False), '完整语境JSON': json.dumps(row['contexts'], ensure_ascii=False), **row['coding']})
assert maxctx < 32767
readme = (OLD / '使用说明.md').read_text()
readme = readme.replace(' v4', ' v5').replace('本v4', '本v5').replace('v4没有', 'v5没有').replace('冻结v12', '冻结v14').replace('v12完整contexts', 'v14完整contexts').replace('HV3匿名编号', 'HV5匿名编号')
readme = readme[:readme.index('\n旧v2和v3、')] + '\n旧v2至v4、旧私有设计，以及既有冻结来源输入均保留原字节。本v5为尚未执行的source-only材料更新；任何后续真人提交应另存，不能回填覆盖本空白包。\n\n本v5沿用v4的同240条实际样本、抽样概率π、分析权重、A/C分别的条目顺序和全部空白身份/答题字段。本次相对v4每位仅2条语境更新为v14的实际局部父句及连续来源结构，其余238条语境保持原样。全部240条均已与v14冻结材料逐条核对，未重新抽样。旧v4完整保留，不覆盖或补写任何旧材料。\n'
readme = readme.replace('24,032字符', f'{maxctx:,}字符')
(OUT / '使用说明.md').write_text(readme)
created = datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
admin = copy.deepcopy(s)
admin.update(created_at=created, package_version='v5', material_version='v14', mapping=[{k: v for k, v in x.items() if k != 'v4_blind_id'} for x in mapping], prior_v4_mapping=copy.deepcopy(s['mapping']), v4_to_v5_blind_mapping=mapping, previous_v4_files_sha256=prior_hashes, previous_v4_sampling_private_sha256=old_private_sha, source_material_sha256=source_hashes, source_update_scope='v4 same frozen240 sample, probabilities, weights and order; only exact v14 contexts, two actual units04371/04390. All responses blank.')
dump(ADMIN / 'future_human_v5_sampling_PRIVATE.json', admin)
manual_hashes = {str(p.relative_to(OUT)): sha(p) for p in (OUT / '手册').iterdir()}
files = {str(p.relative_to(OUT)): sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}
manifest = {'package_version': 'v5', 'material_version': 'v14', 'execution_status': 'not_started_no_real_human_labels', 'source_only': True, 'sample_design_version': 'future-human-v2-frozen-sample', 'actual_sample_n': 240, 'coder_row_counts': {'A': 240, 'C': 240}, 'department_sample_counts': {'NMPA': 80, 'NHSA': 80, 'NHC': 80}, 'resampled': False, 'sampling_design_changed': False, 'sample_weights_changed': False, 'sample_order_changed': False, 'original_text_changes': 0, 'original_source_title_or_page_changes': 0, 'context_changed_counts': {c: len(v) for c, v in changed.items()}, 'context_changed_blind_ids': {c: [x['blind_id'] for x in v] for c, v in changed.items()}, 'all_contexts_equal_exact_frozen_v14': True, 'all_v4_240_contexts_each_already_equal_v13_verified': True, 'two_coders_symmetric_actual_sample': True, 'all_identity_coding_reason_evidence_fields_blank': True, 'maximum_complete_context_json_characters': maxctx, 'context_truncated': False, 'manual_versions': 'v1.3 + operational v1.4', 'manual_hashes': manual_hashes, 'source_v14_hashes': source_hashes, 'preserved_v4_file_hashes': prior_hashes, 'preserved_v4_sampling_private_sha256': old_private_sha, 'independence_scope': 'Current-unit normalized text families excluded against known development/training. Historical49-full-document context exposure disclosed; not new-document external validation.', 'public_file_hashes': files}
dump(OUT / 'source_update_manifest.json', manifest)
append = {'created_at': created, 'execution_status': 'not_started_no_real_human_labels', 'previous_v4_design_mapping_and_blank_material_unchanged': True, 'v4_file_hashes_before_and_after': prior_hashes, 'v4_private_hash_before_and_after': old_private_sha, 'v14_hashes_before_and_after': source_hashes, 'v5_public_file_hashes': {str(p.relative_to(OUT)): sha(p) for p in sorted(OUT.rglob('*')) if p.is_file()}, 'v5_private_mapping_sha256': sha(ADMIN / 'future_human_v5_sampling_PRIVATE.json'), 'unit_text_changes': 0, 'sample_design_changes': 0, 'resampled': False, 'weight_changes': 0, 'order_changes': 0, 'labels_or_predictions_read': False}
dump(ADMIN / 'future_human_v5_appendfreeze_PRIVATE.json', append)
assert all(sha(ROOT / p) == h for p, h in prior_hashes.items())
assert sha(private_path) == old_private_sha and all(sha(ROOT / p) == h for p, h in source_hashes.items())
print(json.dumps({'n': 240, 'contexts_changed_each': 2, 'max_context_chars': maxctx, 'private_mapping_n': len(mapping), 'changed': changed}, ensure_ascii=False))
