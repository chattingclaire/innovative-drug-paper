"""Two separately authorized, immutable initial11 stages; never auto-enters StageB.

Only --execute invokes CLI. StageA semantic opinions/targets are gate data only;
assemble_stageB_packet does not accept a gate or review as an argument.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
import subprocess
import sys
import uuid
from pathlib import Path

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[3]
RUNTIME=HERE/'runtime'
MODEL='gpt-5.6-sol'; EFFORT='medium'; N=11; MAX_ATTEMPTS=3
CANDIDATE='candidate09-two-step'; SCOPE='initial11-known-development'
INPUT_BINDING=HERE/'initial11_input_binding.json'
DESIGN_FREEZE=HERE/'design_freeze.json'
RUN_NAMES={'A':'initial11-stageA-first-run','B':'initial11-stageB-first-run'}
PROMPTS={'A':HERE/'stageA_prompt.txt','B':HERE/'stageB_prompt.txt'}
SCHEMAS={'A':RUNTIME/'stageA_output_schema.json','B':RUNTIME/'output_schema_codex_compatible.json'}
VALIDATORS={'A':RUNTIME/'validate_stageA.py','B':RUNTIME/'validate_binary_output.py'}
TRAILER='\n\n只根据上述完整给定材料直接返回本阶段规定JSON。禁止外部检索、读取文件、调用工具、运行命令或代码。不从ID推断答案。'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def canonical(obj):return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def row_sha(obj):return hashlib.sha256(canonical(obj).encode()).hexdigest()
def binding(path):
    p=Path(path);return {'path':str(p.resolve()),'sha256':sha(p),'bytes':p.stat().st_size}
def write_new(path,data):
    p=Path(path);data=data if isinstance(data,bytes) else data.encode()
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb')as f:f.write(data)
def dump_new(path,obj):write_new(path,json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
def stage_states():
    states={}
    for s,name in RUN_NAMES.items():
        d=HERE/'runs'/name;summary=d/'technical_summary.json'
        states[s]={'run_key':name,'state':json.loads(summary.read_text())['status']if summary.exists()else('STARTED_NO_TECHNICAL_COMPLETION'if d.exists()else'NOT_RUN')}
    return states
def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m;spec.loader.exec_module(m);return m

def load_runtime():
    base=load_module('candidate09_frozen_base_runner',RUNTIME/'run_production_v32.py')
    inv=load_module('candidate09_inventory',RUNTIME/'stageA_context_inventory.py')
    av=load_module('candidate09_stageA_validator',VALIDATORS['A'])
    return base,inv,av

def verify_binding(obj):
    p=Path(obj['path']);assert p.is_absolute() and p.is_file(),'binding path must be an existing absolute file'
    assert sha(p)==obj['sha256'],f'binding hash mismatch: {p}'
    if 'bytes'in obj:assert p.stat().st_size==obj['bytes'],f'binding bytes mismatch: {p}'
    return p

def load_design():
    d=json.loads(DESIGN_FREEZE.read_text())
    assert d['candidate']==CANDIDATE and d['scope']==SCOPE and d['n']==N
    assert d['model']==MODEL and d['reasoning_effort']==EFFORT
    assert d['stageA_and_B_separately_authorized'] is True
    assert d['max_attempts_per_stage']==MAX_ATTEMPTS
    for x in d['files']+d['sources']:verify_binding(x)
    return d

def read_input():
    ib=json.loads(INPUT_BINDING.read_text())
    assert ib['candidate']==CANDIDATE and ib['scope']==SCOPE and ib['n']==N
    p=Path(ib['input_path']);assert p.is_absolute() and sha(p)==ib['input_sha256']
    data=p.read_bytes()
    rows=[json.loads(s)for s in data.decode().splitlines()if s.strip()]if p.suffix=='.jsonl'else json.loads(data)['rows']
    assert len(rows)==N and all(isinstance(r,dict)and isinstance(r.get('id'),str)and r['id']for r in rows)
    assert len({r['id']for r in rows})==N
    base,_,_=load_runtime();base.no_reference_fields(rows)
    exclusions=PROJECT/'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json'
    assert sha(exclusions)=='a3ea2e0aaabbf9d00fafb4f3511b3a8910b182111d1cff803c0bb5f03040d135'
    protected=set(json.loads(exclusions.read_text())['all_registered_members_of_reserved_families_unit_ids'])
    assert len(protected)==267 and not protected.intersection(r['id']for r in rows)
    # Visibility metadata is hashed only; it is never a packet field.
    if ib.get('visibility_metadata_path'):
        assert sha(ib['visibility_metadata_path'])==ib['visibility_metadata_sha256']
    return ib,p,data,rows

def assemble_stageA_packet(rows,inventory_module):
    before=canonical(rows)
    packet={'rows':rows,'context_path_inventory':inventory_module.inventory_packet(rows)}
    assert canonical(rows)==before,'inventory mutated original input'
    return packet

def assemble_stageB_packet(rows,stageA_output):
    # This deliberately has no semantic-gate/review/expected-label argument.
    assert [r['id']for r in rows]==[r['id']for r in stageA_output['rows']]
    assert all(r['material_status']!='material_issue'for r in stageA_output['rows'])
    return {'rows':rows,'stageA_records':[{'id':r['id'],'record':r,'record_sha256':row_sha(r)}for r in stageA_output['rows']]}

def make_request(stage,packet,prompt):
    marker='\n\n--- 本批完整原始输入与路径库存 ---\n'if stage=='A'else'\n\n--- 同一完整原始输入与封存StageA原记录 ---\n'
    return prompt+marker+json.dumps(packet,ensure_ascii=False)+TRAILER

def check_stageA_source(rows,ib,auth):
    seal_path=verify_binding(auth['stageA_seal'])
    assert seal_path==(HERE/'runs'/RUN_NAMES['A']/'stageA_seal.json').resolve()
    seal=json.loads(seal_path.read_text())
    assert seal['candidate']==CANDIDATE and seal['stage']=='A'and seal['n']==N
    assert seal['status']=='TECHNICAL_COMPLETE_SEMANTIC_REVIEW_REQUIRED'
    assert seal['input_sha256']==ib['input_sha256']and seal['stageA_material_issue_count']==0
    for k in ['selected_raw','unique_completed_agent_events','source_input','frozen_prompt','selected_request',
      'selected_input_packet','selected_attempt_metadata','technical_summary','all_records']:
        verify_binding(seal[k])
    assert Path(seal['source_input']['path']).resolve()==Path(ib['input_path']).resolve()
    assert seal['source_input']['sha256']==ib['input_sha256']
    raw=json.loads(Path(seal['selected_raw']['path']).read_text())
    copied=json.loads(Path(seal['all_records']['path']).read_text())
    assert canonical(raw)==canonical(copied),'StageA copied record changed'
    base,inv,av=load_runtime()
    assert not av.validate({'rows':rows},raw),'StageA source no longer technically valid'
    original_packet=assemble_stageA_packet(rows,inv)
    assert canonical(json.loads(Path(seal['selected_input_packet']['path']).read_text()))==canonical(original_packet)
    assert Path(seal['selected_request']['path']).read_text()==make_request('A',original_packet,PROMPTS['A'].read_text())
    assert seal['frozen_prompt']['sha256']==sha(PROMPTS['A'])
    meta=json.loads(Path(seal['selected_attempt_metadata']['path']).read_text())
    assert meta['status']=='accepted_structural_literal_zero_tools'and not meta['errors']
    assert meta['prompt_sha256']==sha(PROMPTS['A'])and meta['tool_event_count']==0
    summary=json.loads(Path(seal['technical_summary']['path']).read_text())
    assert summary['status']=='TECHNICAL_COMPLETE_SEMANTIC_REVIEW_REQUIRED'
    assert summary['candidate']==CANDIDATE and summary['stage']=='A'and summary['n']==N
    assert summary['selected_raw']==seal['selected_raw']
    assert 1<=len(summary['attempts'])<=MAX_ATTEMPTS and summary['actual_attempts']==len(summary['attempts'])
    assert summary['attempts']and summary['attempts'][-1]['metadata']==seal['selected_attempt_metadata']
    for i,attempt in enumerate(summary['attempts']):
        verify_binding(attempt['metadata']);verify_binding(attempt['candidate09_attempt_binding'])
        am=json.loads(Path(attempt['metadata']['path']).read_text())
        supplement=json.loads(Path(attempt['candidate09_attempt_binding']['path']).read_text())
        assert attempt['attempt']==i+1 and attempt['status']==am['status']
        assert canonical(attempt['errors'])==canonical(am['errors'])and attempt['tool_event_count']==am['tool_event_count']
        assert supplement['metadata']==attempt['metadata']and supplement['stage']=='A'
        assert supplement['material_flags_no_semantic_retry']==attempt['material_flags']
        assert supplement['source_rows_canonical_sha256']==row_sha(rows)
        assert am['prompt_sha256']==sha(PROMPTS['A'])and am['request_sha256']==sha(seal['selected_request']['path'])
        assert am['input_sha256']==sha(Path(attempt['metadata']['path']).parent/'input.json')
        assert Path(attempt['metadata']['path']).parent.joinpath('request.txt').read_text()==make_request('A',original_packet,PROMPTS['A'].read_text())
        if i<len(summary['attempts'])-1:
            assert attempt['status']!='accepted_structural_literal_zero_tools'and not attempt['material_flags']
    events=Path(seal['unique_completed_agent_events']['path']).read_text()
    assert not base.event_output_binding_audit(events,raw)['errors']
    event_check=base.event_audit(events)
    assert event_check['tool_or_unknown_item_event_count']==0 and event_check['completed_turns']==1 and not event_check['turn_errors']
    assert seal['row_record_sha256']=={r['id']:row_sha(r)for r in raw['rows']}
    gate_path=verify_binding(auth['stageA_semantic_gate'])
    gate=json.loads(gate_path.read_text())
    assert gate['status']=='PASS_ROOT_STAGEA_SEMANTIC_REVIEW'and gate['candidate']==CANDIDATE
    assert gate['approved_for_stageB'] is True and gate['reviewed_rows']==N
    assert type(gate['confirmed_semantic_errors'])is int and gate['confirmed_semantic_errors']==0
    assert gate['original_stageA_not_edited']is True
    assert gate['stageA_seal_sha256']==sha(seal_path)
    assert gate['stageA_output_sha256']==seal['all_records']['sha256']
    assert gate['input_sha256']==ib['input_sha256']
    # Only raw StageA rows are returned to the request assembler. The gate is
    # consumed here and never returned, serialized or copied into model input.
    return raw,{'stageA_seal':binding(seal_path),'stageA_semantic_gate':binding(gate_path)}

def read_authorization(path,stage,ib):
    p=Path(path).resolve();a=json.loads(p.read_text())
    assert a['status']=='AUTHORIZED_BOUNDED_EXECUTION'and a['candidate']==CANDIDATE
    assert a['authorized_stage']==stage and a['scope']==SCOPE and a['n']==N
    assert a['model']==MODEL and a['reasoning_effort']==EFFORT
    assert a['batch_size']==N and a['workers']==1 and a['max_attempts']==MAX_ATTEMPTS
    assert a['design_freeze_sha256']==sha(DESIGN_FREEZE)
    assert a['input_binding_sha256']==sha(INPUT_BINDING)and a['input_sha256']==ib['input_sha256']
    for k in ['allow_other_scopes','allow_semantic_retries','allow_automatic_next_stage']:
        assert a[k]is False
    return a,binding(p)

def material_flags(stage,raw_path):
    if not raw_path.exists():return []
    try:raw=json.loads(raw_path.read_text())
    except (ValueError,UnicodeError):return []
    if not isinstance(raw,dict):return []
    if stage=='A':return [r.get('id')for r in raw.get('rows',[])if isinstance(r,dict)and r.get('material_status')=='material_issue']
    return [x.get('id')for x in raw.get('issue_records',[])if isinstance(x,dict)and x.get('status')=='material_issue']

def _execute_stage_impl(stage,packet,request,ib,input_path,input_bytes,auth_binding,gate_bindings=None):
    """One eleven-row batch; all attempts immutable; never calls the other stage."""
    run=HERE/'runs'/RUN_NAMES[stage]
    run.mkdir(parents=True,exist_ok=False)
    assert hashlib.sha256(input_bytes).hexdigest()==ib['input_sha256']and sha(input_path)==ib['input_sha256'],'source input changed before execution'
    base,_,av=load_runtime()
    base.SCHEMA=SCHEMAS[stage]
    if stage=='A':base.v=av
    assert base.MODEL==MODEL and base.EFFORT==EFFORT
    # Keep raw source bytes separately from the packet with execution metadata.
    write_new(run/('frozen_input'+input_path.suffix),input_bytes)
    write_new(run/'frozen_prompt.txt',PROMPTS[stage].read_bytes())
    write_new(run/'frozen_schema.json',SCHEMAS[stage].read_bytes())
    write_new(run/'frozen_validator.py',VALIDATORS[stage].read_bytes())
    write_new(run/'input_packet.json',json.dumps(packet,ensure_ascii=False,indent=2)+'\n')
    write_new(run/'request.txt',request)
    cli_sha=sha(base.CLI)
    cli_version_result=subprocess.run([str(base.CLI),'--version'],capture_output=True,text=True,check=True)
    cli_version=cli_version_result.stdout.strip()
    dump_new(run/'cli_version_query.json',{'command':[str(base.CLI),'--version'],'exit_code':cli_version_result.returncode,
      'stdout':cli_version_result.stdout,'stderr':cli_version_result.stderr,'cli_entry_sha256':cli_sha,
      'not_a_model_request':True})
    run_plan={'candidate':CANDIDATE,'stage':stage,'scope':SCOPE,'n':N,'model':MODEL,'reasoning_effort':EFFORT,
      'batch_size':N,'workers':1,'max_attempts':MAX_ATTEMPTS,'authorization':auth_binding,
      'design_freeze':binding(DESIGN_FREEZE),'source_input':binding(input_path),'input_binding':binding(INPUT_BINDING),
      'prompt':binding(PROMPTS[stage]),'schema':binding(SCHEMAS[stage]),'validator':binding(VALIDATORS[stage]),
      'source_rows_canonical_sha256':row_sha(packet['rows']),'request_sha256':hashlib.sha256(request.encode()).hexdigest(),
      'first_technical_valid_only':True,'no_semantic_retries_or_selection':True,'next_stage_automatically_run':False,
      'root_semantic_gate_bindings_not_in_model_packet':gate_bindings or None}
    dump_new(run/'run_plan.json',run_plan)
    attempts=[];selected=None;stop_material=[]
    try:
        for i in range(1,MAX_ATTEMPTS+1):
            dest=run/'attempts'/f'attempt-{i:02d}'
            m=base.run_attempt(dest,packet,request,sha(PROMPTS[stage]),cli_version,cli_sha,1800)
            assert (dest/'request.txt').read_text()==request,'same-request retry violated'
            flags=material_flags(stage,dest/'raw_output.json')
            supplement={'stage':stage,'schema':binding(SCHEMAS[stage]),'validator':binding(VALIDATORS[stage]),
              'metadata':binding(dest/'run_metadata.json'),'material_flags_no_semantic_retry':flags,
              'source_rows_canonical_sha256':row_sha(packet['rows'])}
            dump_new(dest/'candidate09_attempt_binding.json',supplement)
            attempts.append({'attempt':i,'metadata':binding(dest/'run_metadata.json'),
              'candidate09_attempt_binding':binding(dest/'candidate09_attempt_binding.json'),'status':m['status'],
              'errors':m['errors'],'tool_event_count':m['tool_event_count'],'material_flags':flags})
            if m['status']=='accepted_structural_literal_zero_tools':selected=dest;stop_material=flags;break
            if flags:
                stop_material=flags;break  # material/semantic finding is never a technical retry
        if selected is None:
            dump_new(run/'technical_summary.json',{'status':'FAILED_ATTEMPTS_PRESERVED','stage':stage,'attempts':attempts,
              'material_flags':stop_material,'next_stage':'NOT_RUN','semantic_correctness_verified':False})
            return 2
        assert sha(input_path)==ib['input_sha256'],'source input changed during execution; successful seal forbidden'
        raw_path=selected/'raw_output.json';raw=json.loads(raw_path.read_text())
        output_name='all_stageA_records.json'if stage=='A'else'all_predictions.json'
        output=run/output_name;write_new(output,raw_path.read_bytes())
        lines=run/(output_name+'l');write_new(lines,''.join(json.dumps(r,ensure_ascii=False)+'\n'for r in raw['rows']))
        summary={'status':'TECHNICAL_COMPLETE_SEMANTIC_REVIEW_REQUIRED','candidate':CANDIDATE,'stage':stage,'n':N,
          'logical_requests':1,'actual_attempts':len(attempts),'attempts':attempts,'first_technical_valid_only':True,
          'selected_attempt':str(selected),'output_JSON':binding(output),'output_JSONL':binding(lines),
          'selected_raw':binding(raw_path),'material_flags':stop_material,'semantic_correctness_verified':False,
          'next_stage_automatically_run':False,'other_scope':'NOT_RUN'}
        dump_new(run/'technical_summary.json',summary)
        if stage=='A':
            seal={'status':'TECHNICAL_COMPLETE_SEMANTIC_REVIEW_REQUIRED','candidate':CANDIDATE,'stage':'A','n':N,
              'input_sha256':ib['input_sha256'],'source_input':binding(input_path),'frozen_prompt':binding(run/'frozen_prompt.txt'),
              'selected_raw':binding(raw_path),'unique_completed_agent_events':binding(selected/'events.jsonl'),
              'selected_input_packet':binding(selected/'input.json'),'selected_attempt_metadata':binding(selected/'run_metadata.json'),
              'selected_request':binding(selected/'request.txt'),'all_records':binding(output),
              'row_record_sha256':{r['id']:row_sha(r)for r in raw['rows']},'stageA_material_issue_count':len(stop_material),
              'technical_summary':binding(run/'technical_summary.json'),'StageB':'NOT_RUN_ROOT_SEMANTIC_REVIEW_AND_AUTHORIZATION_REQUIRED'}
            dump_new(run/'stageA_seal.json',seal)
        return 0
    finally:
        # Re-check source immutability and record BOTH fixed stage run keys,
        # including an unstarted B when A fails. No semantic PASS is emitted.
        receipt={'stage_invoked':stage,'stage_states':stage_states(),'source_input_unchanged':sha(input_path)==ib['input_sha256'],
          'original_source_rows_canonical_sha256':row_sha(packet['rows']),'semantic_PASS_or_adoption_written':False,
          'created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()}
        dump_new(run/'final_stage_scope_receipt.json',receipt)

def execute_stage(stage,packet,request,ib,input_path,input_bytes,auth_binding,gate_bindings=None):
    """Also records a pre-attempt CLI-version/startup failure without retrying it."""
    run=HERE/'runs'/RUN_NAMES[stage]
    assert not run.exists(),'initial stage run is immutable and may not be restarted'
    try:
        return _execute_stage_impl(stage,packet,request,ib,input_path,input_bytes,auth_binding,gate_bindings)
    except Exception as exc:
        if run.exists()and not(run/'execution_exception.json').exists():
            dump_new(run/'execution_exception.json',{'type':type(exc).__name__,'message':str(exc),
              'stage':stage,'semantic_retry':False,'no_automatic_next_stage':True})
        raise
    finally:
        if run.exists()and not(run/'final_stage_scope_receipt.json').exists():
            dump_new(run/'final_stage_scope_receipt.json',{'stage_invoked':stage,'stage_states':stage_states(),
              'source_input_unchanged':sha(input_path)==ib['input_sha256'],'semantic_PASS_or_adoption_written':False,
              'created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()})

def _main_admitted(args):
    load_design();ib,input_path,input_bytes,rows=read_input()
    base,inv,_=load_runtime();base.no_reference_fields(rows)
    auth=None;auth_binding=None;gate_bindings=None
    if args.execute or args.stage=='B':
        assert args.authorization_file,'authorized StageB assembly and all execution require an explicit authorization file'
        auth,auth_binding=read_authorization(args.authorization_file,args.stage,ib)
    if args.stage=='A':packet=assemble_stageA_packet(rows,inv)
    else:
        ar,gate_bindings=check_stageA_source(rows,ib,auth)
        packet=assemble_stageB_packet(rows,ar)
    request=make_request(args.stage,packet,PROMPTS[args.stage].read_text())
    if args.plan_only:
        out=HERE/'offline-plans'/RUN_NAMES[args.stage];out.mkdir(parents=True,exist_ok=False)
        dump_new(out/'input_packet.json',packet);write_new(out/'request.txt',request)
        dump_new(out/'plan_only.json',{'status':'PLAN_ONLY_NO_CLI_OR_MODEL_CALL','stage':args.stage,
          'n':N,'input':binding(input_path),'prompt':binding(PROMPTS[args.stage]),'request':binding(out/'request.txt'),
          'source_rows_canonical_sha256':row_sha(rows),'automatic_next_stage':False})
        print(json.dumps({'status':'PLAN_ONLY_NO_CLI_OR_MODEL_CALL','stage':args.stage,'metadata':binding(out/'plan_only.json')},ensure_ascii=False))
        return 0
    result=execute_stage(args.stage,packet,request,ib,input_path,input_bytes,auth_binding,gate_bindings)
    print(json.dumps({'stage':args.stage,'exit_code':result,'next_stage_automatically_run':False},ensure_ascii=False))
    return result

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument('--stage',required=True,choices=['A','B'])
    mode=ap.add_mutually_exclusive_group(required=True);mode.add_argument('--plan-only',action='store_true');mode.add_argument('--execute',action='store_true')
    ap.add_argument('--authorization-file')
    args=ap.parse_args(argv)
    invocation={'stage_requested':args.stage,'mode':'execute'if args.execute else'plan_only','semantic_PASS_or_adoption_written':False}
    try:
        result=_main_admitted(args);invocation.update({'exit_code':result,'status':'RETURNED'})
        return result
    except Exception as exc:
        invocation.update({'status':'REJECTED_OR_FAILED_PRESERVED','exception_type':type(exc).__name__,'exception_message':str(exc)})
        raise
    finally:
        invocation['stage_states']=stage_states()
        invocation['created_at_UTC']=datetime.datetime.now(datetime.timezone.utc).isoformat()
        # Includes freeze/input/auth/gate rejection before any CLI startup; a
        # receipt never creates a run directory or authorizes a next stage.
        dump_new(HERE/'invocation-records'/f'{uuid.uuid4().hex}.json',invocation)

if __name__=='__main__':raise SystemExit(main())
