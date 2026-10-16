"""Export the complete source-only target frame. No sampling or coding functions."""
from pathlib import Path
from collections import Counter, defaultdict
import hashlib
import json
import unicodedata

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
W = ROOT / 'outputs/编码修订核查-20261008'
OUT = Path(__file__).resolve().parent
RULE = W / 'LLM编码/统一判据编码准备/共用纯来源材料04/rule_inputs_material04.jsonl'
MODEL_SOURCE = W / 'LLM编码/统一判据编码准备/共用纯来源材料04/source_only_with_scope04.jsonl'
MAPPING = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
PLAN = ROOT / 'plan.md'
OLD_SCOPE = W / '统计复算/验证框与全量范围核查01/verification_frame_scope01.json'
MANUAL = W / '定义溯源核查/共同判据定稿/共用编码手册.md'
GROUP_NAMES = {'NMPA': '药监', 'NHSA': '医保', 'NHC': '卫健'}
EXPECTED_COUNTS = {'NMPA': 1848, 'NHSA': 2100, 'NHC': 533}


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha_file(path):
    return sha_bytes(path.read_bytes())


def canonical_sha(value):
    return sha_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8'))


def norm(value):
    return ''.join(c for c in unicodedata.normalize('NFKC', value)
                   if not c.isspace() and not unicodedata.category(c).startswith('P'))


def load_lines(path):
    return [(i, json.loads(line)) for i, line in enumerate(path.read_text().splitlines(), 1) if line.strip()]


def prohibit_label_fields(value):
    forbidden = {'labels', 'prediction', 'predictions', 'expected_labels', 'judgments', 'human_labels', 'gold_labels'}
    if isinstance(value, dict):
        assert not forbidden.intersection(value), 'Source input contains a prohibited label/output field.'
        for v in value.values():
            prohibit_label_fields(v)
    elif isinstance(value, list):
        for v in value:
            prohibit_label_fields(v)


def main():
    assert sha_file(RULE) == 'bab2da6586fade4a5fc6b188b3fee9cbfbf4099579b9205fee93639c3d7af960'
    assert sha_file(MAPPING) == 'e35c0b3643093ecc3a41dfd0c3cf50aca27a43aea7fa2b4594d5cf7857ce3fb2'
    assert sha_file(MANUAL) == '5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c'
    files = ['source_only_frame_all4481.jsonl', 'normalized_text_families_all4481.json', 'source_frame_manifest01.json']
    assert not any((OUT / name).exists() for name in files), 'Never overwrite a prior frame.'
    rules = load_lines(RULE)
    model_lines = load_lines(MODEL_SOURCE)
    model = {row['id']: (line, row) for line, row in model_lines}
    assert len(model) == len(model_lines) == len(rules) == 4924
    assert {r['id'] for _, r in rules} == set(model)
    metadata = json.loads(MAPPING.read_text())['rows']
    departments = {Path(r['original_file']).stem: r['analysis_group'] for r in metadata}
    assert len(departments) == len(metadata)
    selected = []
    outside = Counter()
    families = defaultdict(list)
    for line, row in rules:
        prohibit_label_fields(row)
        inp = row['input']
        group = departments[inp['original_file_stem']]
        model_line, model_row = model[row['id']]
        assert set(model_row) == {'id', 'text', 'pages', 'contexts'}
        prohibit_label_fields(model_row)
        assert inp['unit_text'] == model_row['text']
        if group not in GROUP_NAMES:
            outside[group] += 1
            continue
        fid = 'TEXTFAM-' + sha_bytes(norm(inp['unit_text']).encode('utf-8'))
        families[fid].append((row['id'], group))
        selected.append((line, row, group, model_line, model_row, fid))
    counts = Counter(g for _, _, g, _, _, _ in selected)
    assert dict(counts) == EXPECTED_COUNTS and len(selected) == 4481
    assert outside == {'GOV': 443}
    assert len({row['id'] for _, row, _, _, _, _ in selected}) == 4481
    assert any(row['id'] == 'RECODE25-00064' for _, row, _, _, _, _ in selected)
    rows = []
    for line, row, group, model_line, model_row, fid in selected:
        inp = row['input']
        contexts = model_row['contexts']
        shared = inp.get('llm_v29_shared_context')
        fam_counts = Counter(g for _, g in families[fid])
        paragraphs = [p.get('paragraph_id', p.get('id')) for p in inp.get('paragraph_context', []) if isinstance(p, dict)]
        contexts_meta = [{'context_id': c.get('context_id'), 'kind': c.get('kind'),
                          'source_document': c.get('source_document'), 'structure': c.get('structure')}
                         for c in contexts]
        issue = []
        if row['id'] == 'RECODE25-00064':
            issue = [{'issue_id': 'MATERIAL-00064', 'status': 'unresolved_source_reference',
                      'basis': '既有来源问题及root本次明确保护指令；本次不重审所援指南。',
                      'handling': '保留本单位及正抽样资格；先核原文后向所有方法同步补齐，不能把未知记0或无说明删除。'}]
        rows.append({
            'id': row['id'], 'original_id': row.get('original_id'),
            'analysis_group': group, 'department_name': GROUP_NAMES[group],
            'source_document_stem': inp['original_file_stem'],
            'unit_text': inp['unit_text'], 'unit_text_sha256': sha_bytes(inp['unit_text'].encode('utf-8')),
            'pages': inp.get('pages', []),
            'source_position': {
                'source_file': inp.get('source'), 'source_sha256_recorded': inp.get('source_sha256'),
                'unit_source_file': inp.get('unit_source', inp.get('source')),
                'unit_source_sha256_recorded': inp.get('unit_source_sha256', inp.get('source_sha256')),
                'candidate_file': inp.get('candidate_file'), 'candidate_sha256_recorded': inp.get('candidate_sha256'),
                'unit_id': inp.get('unit_id'), 'review_id': inp.get('review_id'),
                'paragraph_ids': paragraphs, 'rule_input_file': str(RULE), 'rule_input_line': line},
            'normalized_text_family': {
                'family_id': fid, 'normalized_text_sha256': fid.removeprefix('TEXTFAM-'),
                'family_size_all_departments': len(families[fid]),
                'family_size_within_department': fam_counts[group],
                'departments': sorted(fam_counts), 'cross_department_family': len(fam_counts) > 1},
            'shared_context_identity': {
                'canonical_serialization': 'UTF-8 JSON; ensure_ascii=False; sort_keys=True; separators=comma/colon; no text normalization',
                'rule_shared_context_present': shared is not None,
                'rule_shared_context_sha256': canonical_sha(shared),
                'model_contexts_sha256': canonical_sha(contexts),
                'model_context_count': len(contexts), 'model_context_identity_fields': contexts_meta,
                'model_source_file': str(MODEL_SOURCE), 'model_source_line': model_line},
            'known_material_issues': issue,
            'frame_eligibility': 'included_in_complete_three_department_target_no_development_exclusion'
        })
    OUT.mkdir(parents=True, exist_ok=True)
    frame_path = OUT / files[0]
    frame_path.write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in rows))
    family_path = OUT / files[1]
    family_path.write_text(json.dumps({
        'normalization': 'NFKC; remove Unicode whitespace and P* punctuation; keep remaining symbols and case; original unit text unchanged',
        'cross_department_families_are_retained': True,
        'families': [{'family_id': f, 'n_members': len(ids),
                      'members': [{'id': rid, 'analysis_group': g} for rid, g in ids]}
                     for f, ids in sorted(families.items())]
    }, ensure_ascii=False, indent=2) + '\n')
    sources = [{'path': str(p), 'sha256': sha_file(p)} for p in [RULE, MODEL_SOURCE, MAPPING, PLAN, OLD_SCOPE, MANUAL]]
    manifest = {
        'status': 'source_only_full_target_frame_exported_no_sample_drawn',
        'n_source_input': 4924, 'n_target': 4481, 'counts_by_group': dict(counts),
        'outside_target_counts': dict(outside), 'outside_target_reason': '当前目标仅三部门；GOV443按冻结部门归属在目标之外，不因材料缺口或开发暴露排除。',
        'no_historical_development_family_or_control_exclusion': True,
        'normalized_family_count': len(families),
        'cross_department_family_count_retained': sum(len({g for _, g in ids}) > 1 for ids in families.values()),
        'known_material_issue_ids_retained': ['RECODE25-00064'],
        'material_completeness_not_certified_for_all_units': True,
        'source_position_sha_note': 'source_position中的source/candidate SHA原样承载冻结source04记录；本次没有重新认证全部原始来源文件。对输入文件与导出文件的SHA本次实际计算。',
        'human_results_created': False, 'sampling_performed': False, 'coder_or_model_executed': False,
        'machine_or_expected_labels_read': False, 'sampling_n_and_seed_not_fixed': True,
        'sources': sources,
        'outputs': [{'path': str(p), 'sha256': sha_file(p)} for p in [frame_path, family_path]],
        'builder': {'path': str(Path(__file__).resolve()), 'sha256': sha_file(Path(__file__))}}
    (OUT / files[2]).write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'n': len(rows), 'counts': dict(counts), 'frame_sha256': sha_file(frame_path),
                      'families': len(families), 'known_issue_retained': 'RECODE25-00064'}, ensure_ascii=False))


if __name__ == '__main__':
    main()
