"""Run one frozen development batch, maximum 40 records; no reference labels."""
import argparse
import copy
import datetime
import hashlib
import json
import pathlib
import sys


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--input', required=True)
    p.add_argument('--output', required=True)
    p.add_argument('--freeze', required=True)
    args = p.parse_args()
    root = pathlib.Path(__file__).resolve().parent
    freeze = json.loads(pathlib.Path(args.freeze).read_text())
    assert all(sha(k) == v for k, v in freeze['code_sha256'].items()), 'Code differs from pre-run freeze'
    inpath, outpath = pathlib.Path(args.input), pathlib.Path(args.output)
    assert not outpath.exists() and not outpath.with_suffix('.run.json').exists(), 'Preserve each actual run'
    input_hash = sha(inpath)
    rows = [json.loads(s) for s in inpath.read_text().splitlines() if s.strip()]
    assert 0 < len(rows) <= 40 and len(rows) == len({r['id'] for r in rows})
    assert all(set(r) <= {'id', 'original_id', 'input'} and 'input' in r for r in rows), 'No label-bearing wrappers'
    sys.path.insert(0, str(root / 'runtime'))
    import policy_coding_v27 as coder
    assert pathlib.Path(coder.__file__).resolve().parent == root / 'runtime'
    source_hashes = {}
    for row in rows:
        for key in ('source', 'unit_source', 'candidate_file'):
            if row['input'].get(key):
                path = str(pathlib.Path(row['input'][key]).resolve())
                source_hashes[path] = sha(path)
    started = datetime.datetime.now().astimezone().isoformat()
    results = []
    for row in rows:
        record = copy.deepcopy(row['input'])
        result = coder.code_unit(record)
        assert result['unit_text_sha256'] == hashlib.sha256(record['unit_text'].encode()).hexdigest()
        for e in result.get('evidence', []):
            assert record['unit_text'][e['start']:e['end']] == e['text']
        results.append({'id': row['id'], 'original_id': row.get('original_id'), 'prediction': result})
    assert sha(inpath) == input_hash
    assert all(sha(k) == v for k, v in freeze['code_sha256'].items())
    assert all(sha(k) == v for k, v in source_hashes.items())
    outpath.parent.mkdir(parents=True, exist_ok=True)
    outpath.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in results))
    manifest = {'n': len(results), 'version': coder.VERSION,
        'started_at': started, 'completed_at': datetime.datetime.now().astimezone().isoformat(),
        'input': str(inpath.resolve()), 'input_sha256': input_hash,
        'output': str(outpath.resolve()), 'output_sha256': sha(outpath),
        'code_sha256': freeze['code_sha256'], 'freeze_sha256': sha(args.freeze),
        'source_and_candidate_sha256': source_hashes, 'python_executable': sys.executable,
        'pending_n': sum(r['prediction'].get('judgement_status') == 'undetermined' for r in results),
        'reference_labels_loaded': False, 'adopted': False,
        'scope': 'bounded_development_check_not_independent_human_validation'}
    outpath.with_suffix('.run.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: manifest[k] for k in ('n', 'pending_n', 'output', 'output_sha256', 'adopted')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
