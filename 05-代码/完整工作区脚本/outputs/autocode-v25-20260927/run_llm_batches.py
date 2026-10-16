"""Immutable, resumable current-protocol LLM runs; stop on first failure.

Defaults to the 1268 current-reference units first. --scope all covers the
4924 analysis units. This script never reads reference labels into prompts.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import llm_recoder

HERE=Path(__file__).resolve().parent

def file_sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--scope',choices=['current1268','all'],default='current1268')
    p.add_argument('--batch-size',type=int,default=10)
    p.add_argument('--workers',type=int,default=1)
    p.add_argument('--model',required=True,help='Exact provider model ID fixed in the run plan.')
    p.add_argument('--run-name',required=True)
    p.add_argument('--prepare-only',action='store_true')
    args=p.parse_args()
    assert 1<=args.batch_size<=25 and 1<=args.workers<=4
    # Keep output directory names local, not arbitrary filesystem paths.
    assert args.run_name and Path(args.run_name).name==args.run_name
    manifest=json.loads((HERE/'current_input_manifest.json').read_text())
    for name,sha in manifest['output_hashes'].items():
        assert file_sha(HERE/name)==sha,(name,'input changed')
    rows=[json.loads(s) for s in (HERE/'current_llm_inputs.jsonl').read_text().splitlines()]
    if args.scope=='current1268':
        # Only opaque IDs are read; labels are not sent to the LLM process.
        ids={json.loads(s)['id'] for s in (HERE/'current_1268_references.jsonl').read_text().splitlines()}
        rows=[r for r in rows if r['id'] in ids]
    expected=1268 if args.scope=='current1268' else 4924
    assert len(rows)==expected
    root=HERE/'llm_runs'/args.run_name;root.mkdir(parents=True,exist_ok=True)
    batches=[rows[i:i+args.batch_size] for i in range(0,len(rows),args.batch_size)]
    plan={'method_version':llm_recoder.VERSION,'scope':args.scope,'n':len(rows),
          'batch_size':args.batch_size,'batch_count':len(batches),'model':args.model,
          'system_prompt_sha256':hashlib.sha256(llm_recoder.system_prompt().encode()).hexdigest(),
          'runner_sha256':file_sha(Path(llm_recoder.__file__)),'input_manifest_sha256':file_sha(HERE/'current_input_manifest.json'),
          'validation_policy':'First output preserved; no silent label edits or performance-selected retries.',
          'reference_labels_in_prompt':False,'full_input_not_truncated':True,
          'ids':[[r['id'] for r in batch] for batch in batches]}
    planpath=root/'run_plan.json'
    if planpath.exists():assert json.loads(planpath.read_text())==plan,'Cannot resume changed plan; use a new named run.'
    else:planpath.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n')
    if args.prepare_only:
        print(json.dumps({'prepared':len(rows),'batches':len(batches),'provider_calls':0},ensure_ascii=False));return
    pending=[];accepted=[]
    for i,batch in enumerate(batches,1):
        dest=root/f'batch-{i:04d}'
        if dest.exists():
            meta_file=dest/'run_metadata.json'
            if not meta_file.exists():raise RuntimeError(f'{dest.name}: incomplete attempt preserved; inspect before retry')
            meta=json.loads(meta_file.read_text())
            if meta['status']!='accepted_first_output':raise RuntimeError(f'{dest.name}: previous failure preserved; resolve before new named attempt')
            assert meta['requested_model']==args.model
            accepted.append(i)
        else:pending.append((i,batch,dest))
    # Submit only one small wave at a time so authentication/rate errors cannot
    # launch hundreds of calls. A failed wave ends the run without overwriting.
    for first in range(0,len(pending),args.workers):
        failures=[]
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures={pool.submit(llm_recoder.run_batch,batch,dest,args.model):(i,dest)
                     for i,batch,dest in pending[first:first+args.workers]}
            for future in as_completed(futures):
                i,dest=futures[future]
                try:
                    meta=future.result()
                    if meta['status']=='accepted_first_output':accepted.append(i)
                    else:failures.append(i)
                    print(json.dumps({'batch':i,'status':meta['status'],'completed_batches':len(accepted),'total_batches':len(batches)},ensure_ascii=False),flush=True)
                except Exception as error:
                    failures.append(i)
                    print(json.dumps({'batch':i,'status':'runner_exception','type':type(error).__name__},ensure_ascii=False),flush=True)
        status={'accepted_batches':sorted(accepted),'failed_batches':failures,'total_batches':len(batches),
                'status':'failed_requires_resolution' if failures else 'running' if len(accepted)<len(batches) else 'complete'}
        (root/'progress.json').write_text(json.dumps(status,ensure_ascii=False,indent=2)+'\n')
        if failures:sys.exit(2)
    if len(accepted)==len(batches):
        allrows=[]
        for i in range(1,len(batches)+1):
            allrows.extend(json.loads((root/f'batch-{i:04d}'/'extracted.json').read_text())['rows'])
        assert [r['id'] for r in allrows]==[r['id'] for r in rows]
        (root/'all_predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in allrows))
        print(json.dumps({'complete':len(allrows),'run':args.run_name},ensure_ascii=False))

if __name__=='__main__':main()
