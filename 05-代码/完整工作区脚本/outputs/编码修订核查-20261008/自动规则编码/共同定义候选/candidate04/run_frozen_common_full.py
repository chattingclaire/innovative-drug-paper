"""Run a frozen common-definition candidate on unlabelled corpus inputs.

No reference annotations or statistical targets are read. Preserve the old
adopted output. A technical failure leaves a visibly partial, unadopted file.
"""
import argparse
import copy
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def locators(value, keys):
    if isinstance(value, dict):
        for k, v in value.items():
            if k in keys and isinstance(v, str) and Path(v).is_absolute():
                yield v
            else:
                yield from locators(v, keys)
    elif isinstance(value, list):
        for v in value:
            yield from locators(v, keys)


def main():
    parser = argparse.ArgumentParser()
    for name in ('input', 'output', 'freeze'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    freeze = json.loads(Path(args.freeze).read_text())
    assert all(sha(k) == v for k, v in freeze['code_sha256'].items())
    inpath, outpath = Path(args.input), Path(args.output)
    partial = outpath.with_suffix('.partial.jsonl')
    manifest_path = outpath.with_suffix('.run.json')
    assert not any(p.exists() for p in (outpath, partial, manifest_path)), 'Never overwrite an actual run'
    input_sha = sha(inpath)
    rows = [json.loads(s) for s in inpath.read_text().splitlines() if s.strip()]
    assert len(rows) == 4924 and len({r['id'] for r in rows}) == len(rows)
    assert all(set(r) <= {'id', 'original_id', 'input'} and 'input' in r for r in rows)
    paths = set()
    for row in rows:
        paths.update(locators(row['input'], {'source', 'unit_source', 'candidate_file',
                                           'source_path', 'candidate_path', 'source_image'}))
    for path in list(paths):
        if Path(path).suffix.lower() == '.json':
            paths.update(locators(json.loads(Path(path).read_text()), {'source_html', 'source_image'}))
    hashes = {p: sha(p) for p in sorted(paths)}
    sys.path.insert(0, str(root / 'runtime'))
    import policy_coding_v27 as coder
    assert Path(coder.__file__).resolve().parent == root / 'runtime'
    started = datetime.datetime.now().astimezone().isoformat()
    outpath.parent.mkdir(parents=True, exist_ok=True)
    completed, pending = 0, 0
    try:
        with partial.open('x') as sink:
            for row in rows:
                record = copy.deepcopy(row['input'])
                result = coder.code_unit(record)
                assert result['unit_text_sha256'] == hashlib.sha256(record['unit_text'].encode()).hexdigest()
                assert all(record['unit_text'][e['start']:e['end']] == e['text']
                           for e in result.get('evidence', []))
                sink.write(json.dumps({'id': row['id'], 'original_id': row.get('original_id'),
                                       'prediction': result}, ensure_ascii=False) + '\n')
                completed += 1
                pending += result.get('judgement_status') == 'undetermined'
                if completed % 100 == 0:
                    sink.flush()
                    print(json.dumps({'completed': completed, 'total': len(rows), 'pending': pending}), flush=True)
        assert sha(inpath) == input_sha
        assert all(sha(k) == v for k, v in freeze['code_sha256'].items())
        assert all(sha(k) == v for k, v in hashes.items())
        os.replace(partial, outpath)
        manifest_path.write_text(json.dumps({'started_at': started,
            'completed_at': datetime.datetime.now().astimezone().isoformat(),
            'n': completed, 'pending_n': pending, 'version': coder.VERSION,
            'input': str(inpath.resolve()), 'input_sha256': input_sha,
            'output': str(outpath.resolve()), 'output_sha256': sha(outpath),
            'freeze_sha256': sha(args.freeze), 'code_sha256': freeze['code_sha256'],
            'source_candidate_and_linked_asset_sha256': hashes,
            'python': sys.executable, 'reference_labels_loaded': False, 'adopted': False,
            'scope': 'full_corpus_machine_shadow_run_not_independent_human_validation'},
            ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'completed': completed, 'pending_n': pending,
                          'output_sha256': sha(outpath), 'adopted': False}), flush=True)
    except Exception as error:
        failure = outpath.with_suffix('.failure.json')
        failure.write_text(json.dumps({'started_at': started,
            'failed_at': datetime.datetime.now().astimezone().isoformat(),
            'completed_n': completed, 'failed_id': rows[completed]['id'] if completed < len(rows) else None,
            'error': repr(error), 'traceback': traceback.format_exc(),
            'partial_output': str(partial.resolve()), 'reference_labels_loaded': False,
            'adopted': False}, ensure_ascii=False, indent=2) + '\n')
        raise


if __name__ == '__main__':
    main()
