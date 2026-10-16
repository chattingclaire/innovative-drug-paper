"""Finite preparation checks, synthetic events only. No CLI/model/classifier."""
import copy, datetime, hashlib, json, types
from pathlib import Path
import jsonschema
H=Path(__file__).resolve().parent
def save(p,x):
    with Path(p).open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def binding(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def module(path):
    m=types.ModuleType('control_only');m.__file__=str(path);exec(compile(path.read_bytes(),str(path),'exec'),m.__dict__);return m
def main():
    directory=H/'preparation-controls';directory.mkdir()
    names={'schema_legal_null':'accept','schema_wrong_packet':'reject','schema_reorder':'reject','schema_missing_binary_evidence':'reject','observable_complete_synthetic':'accept','observable_truncated_synthetic':'reject','observable_wrong_literal_synthetic':'reject','observable_wrong_packet_order_synthetic':'reject','observable_unbound_file_synthetic':'reject','ROOT_GO_false':'reject'}
    save(directory/'fixed-controls-before-execution.json',dict(controls=names,synthetic_only=True,no_actor_actual_read_claim=True,attempt_slots_not_used=True,no_model_classifier_or_CLI=True))
    a=json.loads((H/'batch-0216/assignment.json').read_bytes());schema=json.loads(Path(a['output_schema']['path']).read_bytes())
    first=dict(artifact_type='CONTROL_TEMPLATE_NOT_ACTUAL',run_id=a['run_id'],batch_id=a['batch_id'],requested_model=a['requested_model'],requested_reasoning_effort=a['requested_reasoning_effort'],manual_binding=a['manual'],execution_prompt_binding=a['execution_prompt'],context_unit='batch',scope=a['scope'],read_manifest={'context_unit':'batch','files':[]},records=[dict(source_id=p['source_id'],output_id=p['output_id'],packet_sha256=p['sha256'],dimensions={d:dict(value=None,reason='Synthetic transport control only; no coding performed.',evidence=[]) for d in ('S','E','Ec','I','F')}) for p in a['packets']])
    outcomes=[]
    def test(name,fn):
        try:fn();observed='accept';error=None
        except Exception as e:observed='reject';error={'type':type(e).__name__,'message':str(e)}
        outcomes.append(dict(name=name,expected=names[name],observed=observed,passed=observed==names[name],error=error))
    test('schema_legal_null',lambda:jsonschema.Draft202012Validator(schema).validate(first))
    bad=copy.deepcopy(first);bad['records'][0]['packet_sha256']='0'*64;test('schema_wrong_packet',lambda:jsonschema.Draft202012Validator(schema).validate(bad))
    bad2=copy.deepcopy(first);bad2['records'][0],bad2['records'][1]=bad2['records'][1],bad2['records'][0];test('schema_reorder',lambda:jsonschema.Draft202012Validator(schema).validate(bad2))
    bad3=copy.deepcopy(first);bad3['records'][0]['dimensions']['I']['value']=1;test('schema_missing_binary_evidence',lambda:jsonschema.Draft202012Validator(schema).validate(bad3))
    # Small fabricated text/events exclusively exercise literal receiver logic.
    # They are labeled synthetic, outside all actual attempt slots.
    files={}
    for key in ('manual','execution_prompt','actor_instructions','output_schema','output_validation_contract','campaign_scope_metadata_binding','packet1','packet2','packet3'):
        p=directory/(key+'.txt');p.write_text('SYNTHETIC CONTROL '+key+'\n甲乙丙丁\n');files[key]=binding(p)
    ca={k:files[k] for k in ('manual','execution_prompt','actor_instructions','output_schema','output_validation_contract','campaign_scope_metadata_binding')};ca['packets']=[files['packet1'],files['packet2'],files['packet3']];ca['source_asset_bindings']=[]
    ap=directory/'control-assignment.json';save(ap,ca)
    fp=directory/'control-first.json';cf={'records':[{'dimensions':{'I':{'value':None,'evidence':[]}}}],'read_manifest':{'files':[]}}
    required=[binding(ap),*[ca[k] for k in ('manual','execution_prompt','actor_instructions','output_schema','output_validation_contract','campaign_scope_metadata_binding')],*ca['packets']]
    for b in required:
        text=Path(b['path']).read_text();cf['read_manifest']['files'].append(dict(path=b['path'],actual_presented_ranges=[dict(range_kind='unicode_code_points',start=0,end=len(text),presentation_event='present:'+b['sha256']+':0:'+str(len(text)))]))
    save(fp,cf);helper=H/'submit-first.py';events=[]
    for n,b in enumerate(required):
        literal=Path(b['path']).read_text();key='present:'+b['sha256']+':0:'+str(len(literal));header=dict(**b,start=0,end=len(literal),range_kind='unicode_code_points',presentation_event=key)
        out='PRESENTATION '+json.dumps(header,ensure_ascii=False,separators=(',',':'))+'\n'+literal+'\nEND_PRESENTATION '+key+'\n'
        events.append({'type':'item.completed','item':{'type':'command_execution','id':'synthetic_'+str(n),'exit_code':0,'command':'synthetic_emit '+b['path'],'aggregated_output':out}})
    events.append({'type':'item.completed','item':{'type':'command_execution','id':'synthetic_writer','exit_code':0,'command':str(helper),'aggregated_output':'FIRST_CREATED '+str(fp)+' '+binding(fp)['sha256']}})
    receiver=module(H/'strict-readback-receiver.py')
    test('observable_complete_synthetic',lambda:receiver.observable_reads(ap,fp,events,helper))
    e=copy.deepcopy(events);e[1]['item']['aggregated_output']+='Warning: truncated output';test('observable_truncated_synthetic',lambda:receiver.observable_reads(ap,fp,e,helper))
    e=copy.deepcopy(events);e[1]['item']['aggregated_output']=e[1]['item']['aggregated_output'].replace('甲乙丙丁','甲乙');test('observable_wrong_literal_synthetic',lambda:receiver.observable_reads(ap,fp,e,helper))
    e=copy.deepcopy(events);e[7],e[8]=e[8],e[7];test('observable_wrong_packet_order_synthetic',lambda:receiver.observable_reads(ap,fp,e,helper))
    e=copy.deepcopy(events);e[1]['item']['aggregated_output']=e[1]['item']['aggregated_output'].replace(files['manual']['path'],str(directory/'unbound.txt'));test('observable_unbound_file_synthetic',lambda:receiver.observable_reads(ap,fp,e,helper))
    go=directory/'GO-UNAUTHORIZED-TEMPLATE.json';save(go,{'author':'ROOT','execution_authorized':False,'template_only':True});runner=module(H/'runner.py');test('ROOT_GO_false',lambda:runner.check_go(go,{'run_id':H.name}))
    assert all(not list((H/'batch-0216'/f'attempt-{i:04d}').iterdir()) for i in range(1,4))
    save(directory/'results.json',dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),control_N=len(outcomes),passed_N=sum(o['passed'] for o in outcomes),outcomes=outcomes,all_three_actual_slots_empty=True,actual_processes_started=0,synthetic_events_not_actual_actor_receipts=True,model_calls=0,classifier_calls=0,CLI_calls=0,provider_identity_tested=False,full_actual_guard_end_to_end_not_executed=True,base_guard_prior_controls_reused=True))
    assert all(o['passed'] for o in outcomes),'Preparation control failure retained'
    print(json.dumps({'control_N':len(outcomes),'passed_N':len(outcomes),'model_classifier_CLI_calls':0}))
if __name__=='__main__':main()
