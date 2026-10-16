"""Real fixed-prompt model execution with immutable attempts and deterministic audit selection.

The program never reads reference labels, computes accuracy, assigns labels or repairs
quotes. A retry is the identical independent request, triggered only by execution,
structural/literal validation or nonzero tool events. All attempts are preserved.
"""
import argparse,concurrent.futures,hashlib,importlib.util,json,os,subprocess,tempfile,time,traceback
from pathlib import Path
HERE=Path(__file__).resolve().parent
CLI=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')
SCHEMA=HERE/'output_schema_codex_compatible.json';VALIDATOR=HERE/'validate_binary_output.py'
MODEL='gpt-5.6-sol';EFFORT='medium'
spec=importlib.util.spec_from_file_location('validator',VALIDATOR);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def event_audit(events):
    violations=[];counts={};models=[];turn_completed=0;turn_errors=[]
    for index,line in enumerate(events.splitlines()):
        if not line.strip():continue
        try:e=json.loads(line)
        except ValueError:violations.append({'line':index+1,'reason':'non_json_event'});continue
        if not isinstance(e,dict):violations.append({'line':index+1,'reason':'non_object_event'});continue
        et=e.get('type');item=e.get('item',{});it=item.get('type') if isinstance(item,dict) else None
        key=f'{et}/{it}';counts[key]=counts.get(key,0)+1
        for field in ('model','model_name'):
            if isinstance(e.get(field),str) and e[field] not in models:models.append(e[field])
        if it is not None and it not in {'agent_message','reasoning'}:
            violations.append({'line':index+1,'reason':'non_message_item_potential_tool','event':e})
        if isinstance(et,str) and any(s in et.lower() for s in ('tool_call','function_call','web_search','web_fetch','command_execution')):
            violations.append({'line':index+1,'reason':'tool_event_type','event':e})
        if et=='turn.completed':turn_completed+=1
        if et in {'turn.failed','error'}:turn_errors.append(e)
    return {'tool_or_unknown_item_event_count':len(violations),'violations':violations,'event_type_counts':counts,'observed_model_fields':models,'completed_turns':turn_completed,'turn_errors':turn_errors}
def event_output_binding_audit(events,raw_output,raw_output_json_available=True):
    """Require one completed agent message whose parsed JSON equals raw output.

    This is a technical provenance gate only. It never evaluates label quality.
    Canonical JSON comparison preserves value types (e.g. true is not integer1).
    """
    completed=[];errors=[]
    for line in events.splitlines():
        if not line.strip():continue
        try:event=json.loads(line)
        except ValueError:continue  # event_audit separately rejects malformed events
        item=event.get('item',{}) if isinstance(event,dict) else {}
        if isinstance(event,dict) and event.get('type')=='item.completed' and isinstance(item,dict) and item.get('type')=='agent_message':
            completed.append(item.get('text'))
    result={'completed_agent_message_count':len(completed),'raw_output_json_available':raw_output_json_available,
            'event_final_json_canonical_sha256':None,'raw_output_json_canonical_sha256':None,
            'event_raw_full_object_equal':False,'errors':errors}
    if len(completed)!=1:errors.append('completed_agent_message_count_not_one')
    final=None;final_ok=False
    if len(completed)==1:
        try:
            if not isinstance(completed[0],str):raise TypeError('agent message text is not a string')
            final=json.loads(completed[0]);final_ok=True
        except (ValueError,TypeError):errors.append('unique_completed_agent_message_not_json')
    canonical=lambda obj:json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    if final_ok:result['event_final_json_canonical_sha256']=digest(canonical(final))
    if raw_output_json_available:result['raw_output_json_canonical_sha256']=digest(canonical(raw_output))
    else:errors.append('raw_output_not_available_as_json_for_event_binding')
    if final_ok and raw_output_json_available:
        result['event_raw_full_object_equal']=canonical(final)==canonical(raw_output)
        if not result['event_raw_full_object_equal']:errors.append('unique_completed_agent_message_raw_output_mismatch')
    return result
def no_reference_fields(rows):
    forbidden={'labels','A','C','rule','machine_labels','reference_labels','expected_labels','dimension_reasons','current_labels','current_llm_reason','diagnosis','metric_contributions'}
    def visit(x,path):
        if isinstance(x,dict):
            bad=set(x)&forbidden
            if bad:raise ValueError(f'forbidden reference/prediction field {path}: {sorted(bad)}')
            for k,z in x.items():visit(z,f'{path}.{k}')
        elif isinstance(x,list):
            for i,z in enumerate(x):visit(z,f'{path}[{i}]')
    for i,r in enumerate(rows):visit(r,f'rows[{i}]')
def run_attempt(dest,packet,request,prompt_sha,cli_version,cli_sha,timeout):
    dest.mkdir(parents=True,exist_ok=False)
    inp=dest/'input.json';write(inp,packet);(dest/'request.txt').write_text(request)
    out=dest/'raw_output.json';events=dest/'events.jsonl';stderr=dest/'raw_stderr.txt';start=time.time();proc=None;exc=None
    command=None
    try:
        with tempfile.TemporaryDirectory(prefix='llm-v32-empty-') as cwd:
            command=[str(CLI),'exec','-','--model',MODEL,'--cd',cwd,'-c',f'model_reasoning_effort="{EFFORT}"','-c','web_search="disabled"','--skip-git-repo-check','--ephemeral','--ignore-user-config','--ignore-rules','--sandbox','read-only','--output-schema',str(SCHEMA),'--output-last-message',str(out),'--json']
            proc=subprocess.run(command,input=request,text=True,capture_output=True,timeout=timeout)
    except subprocess.TimeoutExpired as e:
        exc=f'{type(e).__name__}: timeout {timeout}s'
        for path,data in ((events,e.stdout),(stderr,e.stderr)):
            path.write_bytes(data if isinstance(data,bytes) else (data or '').encode())
    except Exception as e:exc=f'{type(e).__name__}: {e}'
    if proc is not None:events.write_text(proc.stdout);stderr.write_text(proc.stderr)
    if not events.exists():events.write_text('')
    if not stderr.exists():stderr.write_text('')
    audit=event_audit(events.read_text());write(dest/'tool_event_audit.json',audit);errors=[]
    if proc is None or proc.returncode!=0:errors.append('cli_execution_failure')
    raw_output=None;raw_output_json_available=False
    if not out.exists():errors.append('missing_raw_output')
    else:
        try:
            raw_output=json.loads(out.read_text());raw_output_json_available=True
            errors.extend(v.validate(packet,raw_output))
        except Exception as e:errors.append(f'json_or_validator_error:{type(e).__name__}:{e}')
    if audit['tool_or_unknown_item_event_count']:errors.append('nonzero_tool_or_unknown_item_events')
    if audit['completed_turns']!=1:errors.append('completed_turn_count_not_one')
    if audit['turn_errors']:errors.append('turn_error_event')
    if audit['observed_model_fields'] and any(m!=MODEL for m in audit['observed_model_fields']):errors.append('observed_model_mismatch')
    binding=event_output_binding_audit(events.read_text(),raw_output,raw_output_json_available)
    write(dest/'event_output_binding_audit.json',binding);errors.extend(binding['errors'])
    validation={'input_n':len(packet['rows']),'valid':not errors,'errors':errors,'semantic_correctness_verified':False};write(dest/'validation.json',validation)
    meta={'status':'accepted_structural_literal_zero_tools' if not errors else 'failed_attempt_preserved','requested_model':MODEL,'reasoning_effort':EFFORT,'observed_model_fields':audit['observed_model_fields'],'actual_model_identity_beyond_cli_parameter':('exposed_event_field' if audit['observed_model_fields'] else 'not_exposed_by_cli_events'),'provider_internal_model_revision':'not_exposed','web_search':'disabled','cli_path':str(CLI),'cli_version':cli_version,'cli_binary_sha256':cli_sha,'command':command,'exit_code':proc.returncode if proc else None,'execution_error':exc,'elapsed_seconds':round(time.time()-start,3),'input_n':len(packet['rows']),'ids':[r['id'] for r in packet['rows']],'input_sha256':sha(inp),'request_sha256':digest(request),'prompt_sha256':prompt_sha,'raw_output_sha256':sha(out) if out.exists() else None,'events_sha256':sha(events),'stderr_sha256':sha(stderr),'tool_event_audit_sha256':sha(dest/'tool_event_audit.json'),'validation_sha256':sha(dest/'validation.json'),'tool_event_count':audit['tool_or_unknown_item_event_count'],'errors':errors,'label_or_metric_selection':False}
    meta['event_output_binding_audit_sha256']=sha(dest/'event_output_binding_audit.json')
    meta['completed_agent_message_count']=binding['completed_agent_message_count']
    meta['raw_output_matches_unique_completed_agent_message']=binding['event_raw_full_object_equal']
    write(dest/'run_metadata.json',meta)
    return meta

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--input',required=True);ap.add_argument('--expected-input-sha256');ap.add_argument('--prompt',default=str(HERE/'完整系统提示词-v32-候选01.txt'));ap.add_argument('--expected-n',type=int,required=True);ap.add_argument('--run-name',required=True);ap.add_argument('--batch-size',type=int,default=25);ap.add_argument('--workers',type=int,default=8);ap.add_argument('--max-attempts',type=int,default=3);ap.add_argument('--start',type=int,default=1);ap.add_argument('--limit-batches',type=int);ap.add_argument('--timeout-seconds',type=int,default=1800);ap.add_argument('--purpose');ap.add_argument('--plan-only',action='store_true');a=ap.parse_args()
    assert Path(a.run_name).name==a.run_name and 1<=a.batch_size<=50 and 1<=a.workers<=12 and 1<=a.max_attempts<=3 and a.start>=1
    ip=Path(a.input).resolve();prompt_path=Path(a.prompt).resolve();prompt=prompt_path.read_text();prompt_sha=sha(prompt_path)
    input_bytes=ip.read_bytes();input_sha=hashlib.sha256(input_bytes).hexdigest()
    if a.expected_n==4924:assert a.expected_input_sha256,'full corpus requires explicit input hash lock'
    if a.expected_input_sha256:assert input_sha==a.expected_input_sha256,'source input hash does not match explicit lock'
    rows=[json.loads(line) for line in input_bytes.decode().splitlines() if line.strip()] if ip.suffix=='.jsonl' else json.loads(input_bytes)['rows']
    assert len(rows)==a.expected_n and all(isinstance(r.get('id'),str) and r['id'] for r in rows) and len({r['id'] for r in rows})==len(rows)
    no_reference_fields(rows)
    assert 'RECODE25-' not in prompt and 'RECALL-BLIND-' not in prompt and '0.80' not in prompt
    cli_version=subprocess.run([str(CLI),'--version'],capture_output=True,text=True,check=True).stdout.strip();cli_sha=sha(CLI)
    batches=[rows[i:i+a.batch_size] for i in range(0,len(rows),a.batch_size)];run=HERE/a.run_name;run.mkdir(exist_ok=True)
    plan={'method_version':'LLM-common-definition-pilot','model':MODEL,'reasoning_effort':EFFORT,'source_input_path':str(ip),'input_sha256':input_sha,'input_format':'jsonl' if ip.suffix=='.jsonl' else 'json','frozen_input_relative_path':'frozen_input'+ip.suffix,'source_prompt_path':str(prompt_path),'prompt_sha256':prompt_sha,'schema_sha256':sha(SCHEMA),'validator_sha256':sha(VALIDATOR),'runner_sha256':sha(Path(__file__)),'cli_path':str(CLI),'cli_version':cli_version,'cli_binary_sha256':cli_sha,'n':len(rows),'batch_size':a.batch_size,'batch_count':len(batches),'max_attempts':a.max_attempts,'selection_rule':'first chronologically created actual attempt passing execution+structure+literal evidence+exact ID order+zero tool events; all failed attempts retained; never use labels or metrics to select','retry_rule':'identical request only after execution/structure/literal/tool-event failure; no metric or semantic-performance retry','purpose':a.purpose or ('fixed-prompt development probe' if a.expected_n!=4924 else 'whole-corpus fixed-prompt development revision'),'strict_independent_validation':False,'materials_not_altered_by_runner':True,'isolation':'empty temporary cwd; read-only sandbox; ignore user config and exec rules; disabled web search; prompt prohibits all tools','provider_model_revision':'not_exposed','workers_not_part_of_semantic_batch_plan':True}
    planpath=run/'run_plan.json'
    if planpath.exists():assert json.loads(planpath.read_text())==plan,'resume plan changed'
    else:write(planpath,plan)
    frozen_input=run/plan['frozen_input_relative_path']
    if frozen_input.exists():assert frozen_input.read_bytes()==input_bytes,'frozen input snapshot mismatch'
    else:frozen_input.write_bytes(input_bytes)
    assert sha(ip)==input_sha,'source input changed while freezing startup plan'
    for name,source in [('frozen_prompt.txt',prompt_path),('frozen_schema.json',SCHEMA),('frozen_validator.py',VALIDATOR),('frozen_runner.py',Path(__file__))]:
        dest=run/name
        if dest.exists():assert dest.read_bytes()==source.read_bytes(),'frozen source mismatch'
        else:dest.write_bytes(source.read_bytes())
    if a.plan_only:print(json.dumps({'status':'plan_only_no_model_calls','plan_sha256':sha(planpath),'plan':plan},ensure_ascii=False),flush=True);return
    last=len(batches) if a.limit_batches is None else min(len(batches),a.start+a.limit_batches-1)
    def execute(index):
        dest=run/'batches'/f'batch-{index:04d}'
        try:dest.mkdir(parents=True,exist_ok=False)
        except FileExistsError:
            print(json.dumps({'batch':index,'status':'previous_batch_immutable_skip'}),flush=True);return
        packet={'rows':batches[index-1]};write(dest/'input.json',packet)
        request=prompt+'\n\n--- 本批冻结盲法输入 ---\n'+json.dumps(packet,ensure_ascii=False)+'\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        (dest/'request.txt').write_text(request);attempts=[];selected=None
        for ai in range(1,a.max_attempts+1):
            attempt=dest/'attempts'/f'attempt-{ai:02d}';m=run_attempt(attempt,packet,request,prompt_sha,cli_version,cli_sha,a.timeout_seconds);attempts.append({'attempt':ai,'relative_path':str(attempt.relative_to(run)),'metadata_sha256':sha(attempt/'run_metadata.json'),'status':m['status'],'raw_output_sha256':m['raw_output_sha256'],'events_sha256':m['events_sha256'],'tool_event_count':m['tool_event_count'],'errors':m['errors']})
            print(json.dumps({'batch':index,'attempt':ai,'status':m['status'],'elapsed_seconds':m['elapsed_seconds'],'errors':m['errors']},ensure_ascii=False),flush=True)
            if m['status']=='accepted_structural_literal_zero_tools':selected=attempt;break
            if ai<a.max_attempts:time.sleep(min(15,5*ai))
        selection={'batch':index,'status':'accepted_first_valid_actual_attempt' if selected else 'all_attempts_failed_preserved','input_n':len(packet['rows']),'ids':[r['id'] for r in packet['rows']],'selected_relative_path':str(selected.relative_to(run)) if selected else None,'selected_output_sha256':sha(selected/'raw_output.json') if selected else None,'attempts':attempts,'selection_uses_metric_or_label_values':False};write(dest/'selection.json',selection)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        for f in concurrent.futures.as_completed([pool.submit(execute,i) for i in range(a.start,last+1)]):f.result()
    selections=[json.loads(p.read_text()) for p in sorted((run/'batches').glob('batch-*/selection.json'))]
    accepted=[s for s in selections if s['status']=='accepted_first_valid_actual_attempt'];complete=len(accepted)==len(batches)
    aggregate={'protocol_version':'COMMON-5D-20261009','execution_version':'LLM-common-definition-pilot','release_stage':'development_labels','rows':[],'issue_records':[]}
    if complete:
        byindex={s['batch']:s for s in accepted}
        for index in range(1,len(batches)+1):
            s=byindex[index];selected=run/s['selected_relative_path'];assert sha(selected/'raw_output.json')==s['selected_output_sha256'];d=json.loads((selected/'raw_output.json').read_text());aggregate['rows'].extend(d['rows']);aggregate['issue_records'].extend(d['issue_records'])
        errors=v.validate({'rows':rows},aggregate);assert not errors,errors
        write(run/'all_predictions.json',aggregate);(run/'all_predictions.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in aggregate['rows']))
    summary={'status':'complete_actual_calls_structurally_valid' if complete else 'partial_or_failed_preserved','n':len(rows),'accepted_batch_count':len(accepted),'expected_batch_count':len(batches),'recorded_batch_count':len(selections),'actual_attempt_count':sum(len(s['attempts']) for s in selections),'all_attempt_tool_event_count':sum(x['tool_event_count'] for s in selections for x in s['attempts']),'selected_tool_event_count':0 if complete else None,'input_sha256':input_sha,'source_input_current_sha256':sha(ip),'source_unchanged_during_run':sha(ip)==input_sha,'prompt_sha256':prompt_sha,'plan_sha256':sha(planpath),'output_sha256':sha(run/'all_predictions.jsonl') if complete else None,'semantic_validity_not_proven_by_structure':True,'metric_or_reference_label_based_selection':False};write(run/'execution_summary.json',summary);print(json.dumps(summary,ensure_ascii=False),flush=True)
    if not complete:raise SystemExit(2)
if __name__=='__main__':main()
