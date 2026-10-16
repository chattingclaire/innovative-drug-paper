"""Execute a frozen <=40-row real development batch once, retaining failures.

Only unlabelled inputs are consumed. No annotation, opinion or expected label
is consulted; comparison is a separate post-exposure development activity.
"""
import argparse
import copy
import datetime
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import sys
import traceback

sys.dont_write_bytecode = True


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment_identity():
    spec = importlib.util.find_spec('pypdf')
    assert spec and spec.origin, 'Required PDF dependency unavailable'
    package = Path(spec.origin).resolve().parent
    return {'python_real_path':str(Path(sys.executable).resolve()),
            'python_version':sys.version,
            'python_binary_sha256':sha(Path(sys.executable).resolve()),
            'pypdf_version':importlib.metadata.version('pypdf'),
            'pypdf_package_real_path':str(package),
            'pypdf_key_file_sha256':{str(package/name):sha(package/name)
                                    for name in ('__init__.py','_reader.py','_page.py')}}


def main():
    parser = argparse.ArgumentParser()
    for name in ('input', 'output', 'freeze'):
        parser.add_argument('--' + name, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    source, output, frozen_path = map(Path, (args.input, args.output, args.freeze))
    manifest = output.with_suffix('.run.json')
    assert not output.exists() and not manifest.exists(), 'Preserve every first execution'
    frozen = json.loads(frozen_path.read_text())
    environment = environment_identity()
    assert environment == frozen['environment_identity'], 'Execution environment differs from frozen identity'
    assert all(sha(path) == value for path,value in frozen['code_sha256'].items())
    assert sha(source) == frozen['input_sha256'][str(source.resolve())]
    assert all(sha(path) == value for path,value in frozen['protected_sha256'].items())
    rows = [json.loads(line) for line in source.read_text().splitlines() if line.strip()]
    assert 0 < len(rows) <= 40 and len(rows) == len({row['id'] for row in rows})
    assert all(set(row) <= {'id','original_id','input'} and 'input' in row for row in rows)
    sys.path.insert(0, str(root/'runtime'))
    import policy_coding_v27 as coder
    assert Path(coder.__file__).resolve().parent == root/'runtime'
    output.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.datetime.now().astimezone().isoformat()
    results, failed, pending = [], [], []
    with output.open('x') as sink:
        for row in rows:
            item = {'id':row['id'], 'original_id':row.get('original_id')}
            original = copy.deepcopy(row['input'])
            record = copy.deepcopy(original)
            try:
                prediction = coder.code_unit(record)
                assert record == original, 'Coder mutated source input'
                assert prediction['unit_text_sha256'] == hashlib.sha256(original['unit_text'].encode()).hexdigest()
                for evidence in prediction.get('evidence', []):
                    assert original['unit_text'][evidence['start']:evidence['end']] == evidence['text']
                    for anchor in evidence.get('current_relation_anchors', []):
                        assert original['unit_text'][anchor['start']:anchor['end']] == anchor['text']
                item['prediction'] = prediction
                item['input_unchanged'] = True
                item['current_evidence_and_relation_offsets_checked'] = True
                if prediction.get('judgement_status') == 'undetermined':
                    pending.append(row['id'])
            except Exception as error:
                item['first_execution_failure'] = {'error_type':type(error).__name__,
                    'message':str(error), 'traceback':traceback.format_exc()}
                failed.append(row['id'])
            sink.write(json.dumps(item, ensure_ascii=False)+'\n')
            sink.flush()
            results.append(item)
    integrity = all(sha(path) == value for path,value in frozen['code_sha256'].items())
    integrity &= sha(source) == frozen['input_sha256'][str(source.resolve())]
    integrity &= all(sha(path) == value for path,value in frozen['protected_sha256'].items())
    report = {'started_at':started,'completed_at':datetime.datetime.now().astimezone().isoformat(),
        'n':len(rows),'n_processed':len(results),'runtime_failure_ids':failed,'pending_ids':pending,
        'version':coder.VERSION,'input':str(source.resolve()),'input_sha256':sha(source),
        'output':str(output.resolve()),'output_sha256':sha(output),'freeze_sha256':sha(frozen_path),
        'code_sha256':frozen['code_sha256'],'environment_identity':environment,
        'source_and_protected_file_integrity':integrity,
        'first_execution_failures_preserved':True,'reference_labels_loaded':False,
        'adopted':False,'full_corpus_run':False,
        'scope':'single_frozen_real_bounded_development_execution_not_independent_validation'}
    with manifest.open('x') as sink:
        json.dump(report,sink,ensure_ascii=False,indent=2)
        sink.write('\n')
    print(json.dumps({key:report[key] for key in ['n','runtime_failure_ids','pending_ids',
                                               'source_and_protected_file_integrity','output_sha256']},ensure_ascii=False))
    assert integrity, 'Files changed during run; first output and diagnostics preserved'


if __name__ == '__main__':
    main()
