"""Immutable real model calls; no label generation, answer post-processing or metric selection."""
import argparse,concurrent.futures,hashlib,importlib.util,json,subprocess,tempfile,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
CLI=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')
PROMPT=HERE/'完整系统提示词-v30.txt'
SCHEMA=HERE/'output_schema_codex_compatible.json'
MODEL='gpt-5.6-sol'
spec=importlib.util.spec_from_file_location('validator',HERE/'validate_binary_output.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def audit_events(events):
    violations=[];counts={};models=[]
    for index,line in enumerate(events.splitlines()):
        try:e=json.loads(line)
        except ValueError:violations.append({'line':index+1,'reason':'non_json_event'});continue
        et=e.get('type');item=e.get('item',{});it=item.get('type') if isinstance(item,dict) else None
        key=f'{et}/{it}';counts[key]=counts.get(key,0)+1
        for field in ('model','model_name'):
            if isinstance(e.get(field),str) and e[field] not in models:models.append(e[field])
        if it is not None and it not in {'agent_message','reasoning'}:
            violations.append({'line':index+1,'reason':'non_message_item_potential_tool','event':e})
        if isinstance(et,str) and any(s in et.lower() for s in ('tool_call','function_call','web_search','web_fetch','command_execution')):
            violations.append({'line':index+1,'reason':'tool_event_type','event':e})
    return {'tool_event_count':len(violations),'violations':violations,'event_type_counts':counts,'observed_model_fields':models}
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--expected-n',type=int,required=True);ap.add_argument('--run-name',required=True);ap.add_argument('--batch-size',type=int,default=25);ap.add_argument('--start',type=int,default=1);ap.add_argument('--limit-batches',type=int);ap.add_argument('--workers',type=int,default=1);a=ap.parse_args()
    assert Path(a.run_name).name==a.run_name and 1<=a.batch_size<=25 and 1<=a.workers<=4 and a.start>=1
    ip=Path(a.input).resolve()
    rows=[json.loads(x) for x in ip.read_text().splitlines() if x.strip()] if ip.suffix=='.jsonl' else json.loads(ip.read_text())['rows']
    assert len(rows)==a.expected_n and len({r['id'] for r in rows})==len(rows)
    prohibited={'labels','A','C','rule','machine_labels','dimension_reasons','reference_labels','expected_labels'}
    assert not any(set(r)&prohibited for r in rows),'reference fields in input'
    batches=[rows[i:i+a.batch_size] for i in range(0,len(rows),a.batch_size)];run=HERE/a.run_name;run.mkdir(exist_ok=True)
    plan={'method_version':'LLM-binary-v30','model':MODEL,'reasoning_effort':'medium','input_sha256':sha(ip),'prompt_sha256':sha(PROMPT),'schema_sha256':sha(SCHEMA),'validator_sha256':sha(HERE/'validate_binary_output.py'),'n':len(rows),'batch_size':a.batch_size,'batches':len(batches),'selection':'first output passing structural/literal and zero-tool validation; failed outputs preserved; no label/metric selection','purpose':'development probe' if a.expected_n!=4924 else 'whole-corpus prospective fixed-prompt development revision','strict_independent_validation':False,'effective_materials_not_altered':True}
    planpath=run/'run_plan.json'
    if planpath.exists():assert json.loads(planpath.read_text())==plan,'resume plan changed'
    else:write(planpath,plan)
    prompt=PROMPT.read_text();last=len(batches) if a.limit_batches is None else min(len(batches),a.start+a.limit_batches-1)
    def execute(index):
        dest=run/'batches'/f'batch-{index:04d}'
        if dest.exists():return {'batch':index,'status':'prior_attempt_preserved_skip'}
        dest.mkdir(parents=True)
        packet={'rows':batches[index-1]};inp=dest/'input.json';write(inp,packet)
        req=prompt+'\n\n--- 本批冻结盲法输入 ---\n'+json.dumps(packet,ensure_ascii=False)+'\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        (dest/'request.txt').write_text(req);out=dest/'raw_output.json';start=time.time()
        proc=None;execution_error=None
        try:
            with tempfile.TemporaryDirectory(prefix='llm-v30-isolated-') as cwd:
                cmd=[str(CLI),'exec','-','--model',MODEL,'--cd',cwd,'-c','model_reasoning_effort="medium"','-c','web_search="disabled"','--skip-git-repo-check','--ephemeral','--ignore-user-config','--ignore-rules','--sandbox','read-only','--output-schema',str(SCHEMA),'--output-last-message',str(out),'--json']
                proc=subprocess.run(cmd,input=req,text=True,capture_output=True,timeout=1800)
        except (subprocess.TimeoutExpired,Exception) as e:
            execution_error=f'{type(e).__name__}: {e}'
            if isinstance(e,subprocess.TimeoutExpired):
                (dest/'events.jsonl').write_bytes(e.stdout or b'');(dest/'raw_stderr.txt').write_bytes(e.stderr or b'')
        if proc is not None:(dest/'events.jsonl').write_text(proc.stdout);(dest/'raw_stderr.txt').write_text(proc.stderr)
        events=(dest/'events.jsonl').read_text() if (dest/'events.jsonl').exists() else ''
        audit=audit_events(events);write(dest/'tool_event_audit.json',audit)
        errors=[]
        if proc is None or proc.returncode!=0:errors.append('cli_execution_failure')
        if not out.exists():errors.append('missing_output')
        else:
            try:errors.extend(v.validate(packet,json.loads(out.read_text())))
            except Exception as e:errors.append(f'json_or_validator_error:{type(e).__name__}:{e}')
        if audit['tool_event_count']:errors.append('nonzero_tool_or_unknown_item_events')
        validation={'n':len(packet['rows']),'valid':not errors,'errors':errors,'semantic_correctness_verified':False};write(dest/'validation.json',validation)
        meta={'status':'accepted_first_output' if not errors else 'failed_first_output_preserved','batch':index,'requested_model':MODEL,'reasoning_effort':'medium','web_search':'disabled','elapsed_seconds':round(time.time()-start,3),'input_n':len(packet['rows']),'ids':[r['id'] for r in packet['rows']],'input_sha256':sha(inp),'request_sha256':digest(req),'raw_output_sha256':sha(out) if out.exists() else None,'events_sha256':sha(dest/'events.jsonl') if (dest/'events.jsonl').exists() else None,'tool_event_count':audit['tool_event_count'],'observed_model_fields':audit['observed_model_fields'],'exit_code':proc.returncode if proc else None,'execution_error':execution_error,'errors':errors,'tool_isolation':'empty temporary cwd; read-only; ignore user config and exec rules; web search disabled; no tools permitted in prompt','runtime_parameters_not_exposed':['temperature','provider_internal_model_revision']};write(dest/'run_metadata.json',meta)
        print(json.dumps({'batch':index,'status':meta['status'],'elapsed_seconds':meta['elapsed_seconds'],'errors':errors},ensure_ascii=False),flush=True)
        return meta
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        for f in concurrent.futures.as_completed([pool.submit(execute,i) for i in range(a.start,last+1)]):f.result()
    allmeta=[json.loads(p.read_text()) for p in sorted((run/'batches').glob('batch-*/run_metadata.json'))]
    accepted=[m for m in allmeta if m['status']=='accepted_first_output'];complete=len(accepted)==len(batches)
    aggregate={'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v30','release_stage':'final_binary_labels','rows':[],'issue_records':[]}
    if complete:
        for index in range(1,len(batches)+1):
            d=json.loads((run/'batches'/f'batch-{index:04d}'/'raw_output.json').read_text());aggregate['rows'].extend(d['rows']);aggregate['issue_records'].extend(d['issue_records'])
        errs=v.validate({'rows':rows},aggregate);assert not errs,errs
        write(run/'all_predictions.json',aggregate)
        (run/'all_predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in aggregate['rows']))
    summary={'status':'complete_actual_calls_structurally_valid' if complete else 'partial_or_failed_preserved','n':len(rows),'accepted_batch_count':len(accepted),'expected_batch_count':len(batches),'metadata_batch_count':len(allmeta),'tool_event_count':sum(m['tool_event_count'] for m in allmeta),'input_sha256':sha(ip),'prompt_sha256':sha(PROMPT),'output_sha256':sha(run/'all_predictions.jsonl') if complete else None,'semantic_validity_not_proven_by_structure':True};write(run/'execution_summary.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
    if not complete:raise SystemExit(2)
if __name__=='__main__':main()
