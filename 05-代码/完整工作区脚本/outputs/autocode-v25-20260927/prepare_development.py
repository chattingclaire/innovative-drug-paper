"""Prepare already observed V600 for development; never a new holdout.

No text from unselected records is emitted. Frozen sources are read-only.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / 'validation-expansion-20260926'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    archive_path = OLD / 'V600-正式成对统计.json'
    archive = json.loads(archive_path.read_text())['archive']
    frozen = archive['freeze_manifest_original']['files']
    paths = {k: Path(frozen[k]['path']) for k in ['corpus', 'candidate_dictionary', 'protocol']}
    for k, p in paths.items():
        assert digest(p) == frozen[k]['sha256'], (k, 'frozen input changed')
    code_path = HERE / 'baseline_candidate17.py'
    protocol_path = HERE / 'protocol-v1.3.md'
    for src, dst in [(paths['candidate_dictionary'], code_path), (paths['protocol'], protocol_path)]:
        if dst.exists():
            assert dst.read_bytes() == src.read_bytes(), f'Refusing to replace {dst}'
        else:
            dst.write_bytes(src.read_bytes())
    predictions = archive['selected_machine_records_by_version_and_blind_id']['candidate']
    lookup = {v['id']: blind for blind, v in predictions.items()}
    selected = {}
    with paths['corpus'].open() as handle:
        for line in handle:
            record = json.loads(line)
            if record['review_id'] in lookup:
                selected[lookup[record['review_id']]] = record
    assert len(selected) == len(lookup) == 600
    labels = {coder: {} for coder in ['A', 'C']}
    for name, submission in archive['raw_coder_submissions'].items():
        coder = submission['coder']
        for row in submission['rows']:
            assert row['id'] not in labels[coder]
            labels[coder][row['id']] = row
    rows = []
    for row in archive['normalized_rows_without_generated_reference']:
        bid = row['id']
        rows.append({'id': bid, 'purpose': 'post_V600_development_not_holdout',
                     'input': selected[bid], 'baseline_frozen': predictions[bid],
                     'original_references': {c: labels[c][bid] for c in labels},
                     'historical_sampling': {k: row[k] for k in ['stratum', 'N_h', 'n_h']}})
    target = HERE / 'development_v600.jsonl'
    target.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    manifest = {'stage': 'development_only_after_prior_validation_observed',
                'n': len(rows), 'reference_type': 'two_AI_first_submissions_not_human_gold',
                'labels_modified': False, 'manual_modified': False,
                'sources': {str(p): digest(p) for p in [archive_path, *paths.values()]},
                'outputs': {str(p): digest(p) for p in [target, code_path, protocol_path]},
                'restrictions': ['No resplit of these records may be called independent validation.',
                                 'Historical design weights do not make post-tuning scores unbiased.',
                                 'No future candidate unit text was printed or selected here.']}
    (HERE / 'development_manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'prepared': len(rows), 'purpose': manifest['stage']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
