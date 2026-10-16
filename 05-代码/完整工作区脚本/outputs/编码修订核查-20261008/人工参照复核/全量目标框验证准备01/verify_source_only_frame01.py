"""Independently rejoin original source rows to verify the export; no sampling/coding."""
from pathlib import Path
from collections import Counter
import hashlib
import json

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
W = ROOT / 'outputs/编码修订核查-20261008'
OUT = Path(__file__).resolve().parent
RULE = W / 'LLM编码/统一判据编码准备/共用纯来源材料04/rule_inputs_material04.jsonl'
META = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
FRAME = OUT / 'source_only_frame_all4481.jsonl'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rows(path):
    return [json.loads(v) for v in path.read_text().splitlines() if v.strip()]


def main():
    qa_path = OUT / 'independent_source_frame_QA01.json'
    assert not qa_path.exists(), 'Never overwrite previous QA.'
    original = rows(RULE)
    metadata = json.loads(META.read_text())['rows']
    dept = {Path(v['original_file']).stem: v['analysis_group'] for v in metadata}
    target = {v['id']: v for v in original if dept[v['input']['original_file_stem']] in {'NMPA', 'NHSA', 'NHC'}}
    raw_counts = Counter(dept[v['input']['original_file_stem']] for v in target.values())
    exported = rows(FRAME)
    byid = {v['id']: v for v in exported}
    assert len(byid) == len(exported) == len(target) == 4481
    assert set(byid) == set(target)
    assert dict(raw_counts) == {'NMPA': 1848, 'NHSA': 2100, 'NHC': 533}
    for rid, source in target.items():
        inp = source['input']
        result = byid[rid]
        assert result['analysis_group'] == dept[inp['original_file_stem']]
        assert result['unit_text'] == inp['unit_text']
        assert result['unit_text_sha256'] == hashlib.sha256(inp['unit_text'].encode('utf-8')).hexdigest()
        assert result['source_position']['unit_id'] == inp.get('unit_id')
        assert result['source_position']['source_file'] == inp.get('source')
        assert result['source_position']['candidate_file'] == inp.get('candidate_file')
    assert byid['RECODE25-00064']['known_material_issues'][0]['status'] == 'unresolved_source_reference'
    assert all(v['frame_eligibility'] == 'included_in_complete_three_department_target_no_development_exclusion' for v in exported)
    before = json.loads((OUT / 'source_frame_manifest01.json').read_text())
    for s in before['sources']:
        assert sha(Path(s['path'])) == s['sha256'], 'A source snapshot changed during frame export.'
    qa = {'status': 'mechanical_source_frame_QA_only', 'all_mechanical_checks_pass': True,
          'independent_raw_source_department_join_counts': dict(raw_counts), 'n': 4481,
          'exact_ID_set_matches_all_three_department_source04_rows': True,
          'current_text_byte_content_preserved': True, 'source_positions_preserved': True,
          'historical_development_not_excluded': True, '00064_retained_unresolved': True,
          'input_sha256': sha(RULE), 'department_mapping_sha256': sha(META),
          'frame_sha256': sha(FRAME), 'family_index_sha256': sha(OUT / 'normalized_text_families_all4481.json'),
          'sources_unchanged_since_export': True,
          'sampling_or_coder_model_execution': False, 'machine_or_expected_labels_read': False,
          'limitation': 'Independent refers to a fresh raw-source/department join, not independent human validity certification. All material content is not authenticated; 00064 remains unresolved.',
          'verifier': {'path': str(Path(__file__).resolve()), 'sha256': sha(Path(__file__))}}
    qa_path.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(qa, ensure_ascii=False))


if __name__ == '__main__':
    main()
