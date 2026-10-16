"""Freeze a complete batch; no A/C or other reference labels are loaded."""
from pathlib import Path
from collections import Counter
import argparse, json, hashlib, sys, datetime

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--module-dir',required=True)
    parser.add_argument('--input',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--version-expected',required=True)
    parser.add_argument('--freeze',required=True)
    parser.add_argument('--source-adapter',choices=['on','off'],default='on')
    parser.add_argument('--substantive-rules',choices=['on','off'],default='on')
    parser.add_argument('--legacy-model',action='store_true')
    args=parser.parse_args()
    module_dir=Path(args.module_dir).resolve()
    sys.path.insert(0,str(module_dir))
    import policy_coding_v27 as coder
    assert Path(coder.__file__).parent==module_dir
    assert coder.VERSION==args.version_expected
    input_path=Path(args.input).resolve();output_path=Path(args.output).resolve()
    freeze_path=Path(args.freeze).resolve();freeze=json.loads(freeze_path.read_text())
    assert not output_path.exists() and not output_path.with_suffix('.run.json').exists(), 'Never overwrite an actual run.'
    assert all(sha(path)==value for path,value in freeze['production_code_sha256'].items())
    if args.legacy_model:
        oldfreeze=json.loads(Path(freeze['parent_candidate_freeze']).read_text())
        assert all(sha(path)==value for path,value in oldfreeze['production_code_sha256'].items())
    binding=sha(input_path)
    rows=[json.loads(line) for line in input_path.read_text().splitlines() if line.strip()]
    assert len(rows)==len({r['id'] for r in rows})==4924
    source_files={str(Path(r['input'][k]).resolve()) for r in rows
                  for k in ('source','unit_source','candidate_file') if r['input'].get(k)}
    source_hashes={p:sha(p) for p in sorted(source_files)}
    code={str(Path(m.__file__).resolve()):sha(m.__file__) for m in list(sys.modules.values())
          if getattr(m,'__file__',None) and Path(m.__file__).suffix=='.py'
          and '/outputs/' in str(Path(m.__file__).resolve())}
    started=datetime.datetime.now().astimezone().isoformat()
    predictions=[];checks=Counter()
    for row in rows:
        result=(coder.code_unit(row['input']) if args.legacy_model else
                coder.code_unit(row['input'],source_adapter=args.source_adapter=='on',
                                substantive_rules=args.substantive_rules=='on'))
        original=row['input']['unit_text']
        assert result['unit_text_sha256']==hashlib.sha256(original.encode()).hexdigest()
        assert result['judgement_status']!='undetermined',row['id']
        assert set(result['labels'])=={'S','E','Ec','I','F'}
        assert all(type(v) is int and v in (0,1) for v in result['labels'].values())
        for item in result.get('evidence',[]):
            assert original[item['start']:item['end']]==item['text']
            checks['literal_evidence_spans']+=1
        for item in result.get('suppressions',[]):
            if all(k in item for k in ('start','end','text')):
                assert original[item['start']:item['end']]==item['text']
                checks['literal_suppression_spans']+=1
        predictions.append({'id':row['id'],'original_id':row['original_id'],'prediction':result})
    assert sha(input_path)==binding
    assert all(sha(path)==digest for path,digest in code.items())
    assert all(sha(path)==digest for path,digest in source_hashes.items())
    output_path.write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in predictions))
    manifest={'version':coder.VERSION,'started_at':started,'completed_at':datetime.datetime.now().astimezone().isoformat(),
              'n':len(predictions),'pending_n':0,'input_path':str(input_path),'input_sha256':binding,
              'prediction_path':str(output_path),'prediction_sha256':sha(output_path),
              'runtime_code_sha256':code,'runner_sha256':sha(__file__),
              'actual_source_and_candidate_sha256':source_hashes,
              'python_executable':sys.executable,'python_version':sys.version,
              'candidate_freeze_path':str(freeze_path),'candidate_freeze_sha256':sha(freeze_path),
              'component_settings':{'legacy_model':args.legacy_model,
                   'source_adapter':False if args.legacy_model else args.source_adapter=='on',
                   'substantive_rules':False if args.legacy_model else args.substantive_rules=='on'},
              'checks':dict(checks),'reference_labels_loaded':False}
    output_path.with_suffix('.run.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'n':len(predictions),'version':coder.VERSION,'output':str(output_path),'checks':dict(checks)},ensure_ascii=False))

if __name__=='__main__':main()
