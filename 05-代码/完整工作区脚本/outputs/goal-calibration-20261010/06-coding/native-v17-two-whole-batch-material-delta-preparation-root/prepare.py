"""Exclusive offline identity rebinding; no CLI/model dispatch or response reads."""
from pathlib import Path
import ast, copy, datetime, hashlib, json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
OLD=ROOT/'06-coding/native-v16-batch0216-material-delta-preparation-sol'
ORIGINAL=ROOT/'06-coding/native-full4481-v1-sol'
V17=ROOT/'01-review/source-interface-v17-finite-source-addendum-root'

def load(p):return json.loads(Path(p).read_bytes())
def bind(p):
    p=Path(p).resolve();b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def exact(b):assert bind(b['path'])=={k:b[k] for k in ('path','bytes','sha256')}
def save(p,x):
    with (HERE/p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def write(p,s):
    with (HERE/p).open('x',encoding='utf8') as f:f.write(s)
def replace_once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b)
def differences(a,b,p=''):
    if type(a)!=type(b):return [p]
    if isinstance(a,dict):return [p+'/'+k for k in set(a)^set(b)]+sum((differences(a[k],b[k],p+'/'+k) for k in a.keys()&b.keys()),[])
    if isinstance(a,list):return [p] if len(a)!=len(b) else sum((differences(x,y,p+'/'+str(i)) for i,(x,y) in enumerate(zip(a,b))),[])
    return [] if a==b else [p]

v=load(V17/'source-extension-manifest-v17.json');old_manifest=load(OLD/'manifest.json')
assert [c['batch_id'] for c in v['native_whole_batch_closures']]==['batch-0325','batch-0485']
for name in ['base-validator.py','emit-presentation.py','submit-first.py']:
    with (HERE/name).open('xb') as f:f.write((OLD/name).read_bytes())
receiver=(OLD/'strict-readback-receiver.py').read_text();receiver=replace_once(receiver,'new_v16_material_delta=True','new_v17_material_delta=True');write('strict-readback-receiver.py',receiver)
# Scientific manual/prompt are referenced unchanged. Actor and dispatch text change only transport identities.
instructions=(OLD/'actor-instructions.txt').read_text()
for a,b in [
 ('本次独立v16同版材料修订原整批0216','本次独立v17同版材料修订原整批0325或0485'),
 ('v15原packet或v16同版补材packet','原packet或v17同版补材packet'),
 ('未由本批assignment绑定的旧v16候选目录','未由本批assignment绑定的旧候选目录'),
 ('本轮仅处理原整批0216的3条：01402使用明确绑定的v16同版中性补材，另外两条原packet不变；','本轮只处理assignment指定的原整批0325或0485的12条；该批02588或04598使用明确绑定的v17同版中性补材，其余11条原packet不变；'),
 ('再按既定成员顺序完整读三个packet','再按既定成员顺序完整读十二个packet')]:instructions=replace_once(instructions,a,b)
write('actor-instructions.txt',instructions)
dispatch=(OLD/'dispatch-core.txt').read_text()
for a,b in [('原整批0216','assignment指定的原整批0325或0485'),('再按01402/01403/01404顺序','再按assignment的原12成员顺序'),('本轮仅01402使用已绑定同版v16中性补材，其他两条packet原字节不变','本批仅02588或04598使用已绑定同版v17中性补材，其他11条packet原字节不变')]:dispatch=replace_once(dispatch,a,b)
write('dispatch-core.txt',dispatch)
scope='separate actual v17 same-version material recoding of original whole batches0325/0485; not previous technical recovery or independent stability repeat'
contract={'artifact_type':'neutral_v17_material_delta_transport_contract','run_id':HERE.name,'scope':scope,'changed_material_source_ids':['RECODE25-02588','RECODE25-04598'],'context_unit':'batch','current_source_record_and_contexts_unchanged':True,'added_material':'Only prepared exact same-version TXT leaves; no definitions, expected labels or semantic applicability assigned.','batches':[{'batch_id':c['batch_id'],'source_ids':c['source_ids'],'expected_N':12,'packet_bytes':c['new_packet_sum_bytes'],'packet_byte_limit':c['original_packet_byte_limit']} for c in v['native_whole_batch_closures']],'max_total_technical_attempts':3,'actual_concurrency_cap':1,'maximum_common_protocol_concurrency':3,'semantic_or_null_retry_prohibited':True,'earliest_technically_valid_complete_new_material_batch':True,'original_results_immutable':True,'first_is_actor_structured_submission_not_provider_wire':True,'provider_serving_model_independently_verified':False,'preparation_is_not_READ_or_USE':True}
save('neutral-material-transport-contract.json',contract)
# Keep the successful dispatch/receive/attempt body; replace obsolete identity/GO-only code.
runner=(OLD/'runner.py').read_text()
runner=replace_once(runner,'One original whole batch, new v16 material. No dispatch without actual ROOT GO.','Two original whole batches, new v17 material. No dispatch without actual ROOT capacity binding.')
runner=replace_once(runner,"REMAINING=ROOT/'06-coding/native-full4481-transport-recovery-v2-sol/execution-runs/20261011T150825641847Z'", "if not __debug__:raise RuntimeError('Required binding assertions disabled')")
start=runner.index('def preflight():');end=runner.index('def prompt(',start)
runner=runner[:start]+'''def assignment_binding(m,a):
    return next(b['assignment'] for b in m['batches'] if b['batch_id']==a['batch_id'])
def preflight(batch_id):
    for b in load(HERE/'preparation-seal.json')['files']:exact(b)
    m=load(HERE/'manifest.json')
    for k in ('runner','receiver','base_guard','validator','cli_launcher','instructions','transport_contract','presentation_helper','submit_helper','v17_material_seal','v17_material_manifest','parent_collection_seal'):exact(m[k])
    material=load(m['v17_material_manifest']['path'])
    closure={c['batch_id']:c for c in material['native_whole_batch_closures']}
    assert [b['batch_id'] for b in m['batches']]==['batch-0325','batch-0485']
    assert m['source_N']==24 and m['actual_concurrency_cap']==1
    selected=None
    for batch in m['batches']:
        exact(batch['assignment']);a=load(batch['assignment']['path']);c=closure[batch['batch_id']]
        assert a['batch_id']==batch['batch_id'] and a['run_id']==m['run_id']
        assert a['source_ids']==batch['source_ids']==c['source_ids'] and a['expected_N']==c['expected_N']==12
        assert a['packets']==c['new_packets'] and a['packet_bytes']==sum(p['bytes'] for p in a['packets'])<=c['original_packet_byte_limit']
        assert m['max_total_technical_attempts']==a['max_total_technical_attempts']==3
        for value in a.values():
            if isinstance(value,dict) and {'path','bytes','sha256'}<=set(value):exact(value)
        for b in a['packets']+a['source_asset_bindings']:exact(b)
        if batch['batch_id']==batch_id:selected=a
    assert selected is not None,'Only two bound whole batches are executable'
    return m,selected
def check_go(path,m):
    assert Path(path).resolve()==HERE/'ROOT-execution-binding.json','Use the actual ROOT binding, not the template'
    go=load(path)
    assert go.get('author')=='ROOT' and go.get('template_only') is False and go.get('execution_authorized') is True,'Actual ROOT execution binding absent'
    assert go['run_id']==m['run_id'] and go['authorized_entrypoint']==binding(__file__) and go['preparation_seal']==binding(HERE/'preparation-seal.json')
    assert go['batch_ids']==[b['batch_id'] for b in m['batches']] and go['native_additional_concurrency_cap']==1
    cap=go['capacity_reservation']
    assert cap['confirmed_by_ROOT'] is True and cap['stability_capacity_can_accommodate'] is True
    assert cap['reserved_additional_cli_slots']==1 and cap['reserved_for_run_id']==m['run_id']
    assert cap['existing_stability_configuration_unchanged'] is True and go['single_transport_owner'] is True
    # ROOT records a real current observation and reserves one additional slot.
    # Do not equate existing stability processes with forbidden global CLI activity.
    exact(cap['observed_capacity_evidence'])
    assert datetime.datetime.fromisoformat(cap['observed_at_utc'])<=datetime.datetime.fromisoformat(go['at_utc'])<=datetime.datetime.now(datetime.timezone.utc)
    assert go['parent_collection_seal']==m['parent_collection_seal'];exact(go['parent_collection_seal'])
    coverage=load(Path(go['parent_collection_seal']['path']).parent/'coverage.json')
    assert coverage['full_corpus_complete'] is True and coverage['selected_record_N']==4481 and coverage['selected_batch_N']==504
    return go
''' +runner[end:]
runner=runner.replace("m['batches'][0]['assignment']","assignment_binding(m,a)")
runner=replace_once(runner,"slot=Path(route['output_directory']);assert not (slot/'dispatch-start.json').exists();text=prompt(m,a,route)","slot=Path(route['output_directory']);slot.mkdir(parents=True,exist_ok=True);assert not (slot/'dispatch-start.json').exists();text=prompt(m,a,route)")
runner=replace_once(runner,"p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','run'],required=True);p.add_argument('--go');x=p.parse_args();m,a=preflight()","p=argparse.ArgumentParser();p.add_argument('--mode',choices=['preflight','run'],required=True);p.add_argument('--batch-id',choices=['batch-0325','batch-0485'],required=True);p.add_argument('--go');x=p.parse_args();m,a=preflight(x.batch_id)")
runner=replace_once(runner,"'record_N':3,'model_calls':0,'requires_future_ROOT_GO_and_actual_remaining_terminal':True","'batch_id':a['batch_id'],'record_N':12,'model_calls':0,'requires_actual_ROOT_capacity_binding':True")
runner=replace_once(runner,"selection=HERE/'batch-0216/root-selection.json'","selection=HERE/a['batch_id']/'root-selection.json'")
runner=replace_once(runner,"result=HERE/'batch-0216/exhausted.json'","result=HERE/a['batch_id']/'exhausted.json'")
runner=replace_once(runner,"'earliest_valid_new_v16_material_whole_batch'","'earliest_valid_new_v17_material_whole_batch'")
runner=replace_once(runner,"'original_v15_results_never_overwritten'","'original_results_never_overwritten'")
write('runner.py',runner)
batches=[];checks=[]
for c in v['native_whole_batch_closures']:
    bid=c['batch_id'];directory=HERE/bid;directory.mkdir();old=load(ORIGINAL/bid/'assignment.json')
    assert old['source_ids']==c['source_ids'] and old['expected_N']==12
    for x in old.values():
        if isinstance(x,dict) and {'path','bytes','sha256'}<=set(x):exact(x)
    for x in old['packets']+old['source_asset_bindings']:exact(x)
    routes=[dict(batch_id=bid,attempt_number=n,runtime_task_name='native_v17_material_'+bid.replace('-','')+'_a'+str(n),output_directory=str(directory/f'attempt-{n:04d}'),first_path=str(directory/f'attempt-{n:04d}'/'first.json'),report_path=str(directory/f'attempt-{n:04d}'/'report.txt'),seal_path=str(directory/f'attempt-{n:04d}'/'seal.json')) for n in range(1,4)]
    save(bid+'/attempt-output-routing.json',dict(run_id=HERE.name,routes=routes,fresh_ephemeral_CLI_each_attempt=True,max_total_technical_attempts=3,route_is_operational_not_scientific_definition=True))
    schema=load(Path(old['output_schema']['path']));schema['properties']['run_id']['const']=HERE.name;schema['properties']['scope']['const']=scope
    changes=[]
    for i,(op,np) in enumerate(zip(old['packets'],c['new_packets'])):
        assert op['source_id']==np['source_id']
        if op!=np:
            assert np['source_id'] in ['RECODE25-02588','RECODE25-04598'];schema['properties']['records']['prefixItems'][i]['properties']['packet_sha256']['const']=np['sha256'];changes.append(i)
    assert len(changes)==1
    save(bid+'/output.schema.json',schema)
    validation=load(Path(old['output_validation_contract']['path']));validation.update(run_id=HERE.name,output_schema_binding=bind(directory/'output.schema.json'),strict_technical_validator=bind(HERE/'base-validator.py'),attempt_output_routing=bind(directory/'attempt-output-routing.json'),new_material_round=True,observable_pre_first_literal_readback_required=True,explicit_actor_template_only_false_required=True)
    validation.pop('v16_structure_compatibility',None)
    save(bid+'/output-validation-contract.json',validation)
    a=copy.deepcopy(old);a.update(run_id=HERE.name,scope=scope,state='prepared_new_v17_material_not_dispatched',output_directory=str(directory),packets=c['new_packets'],packet_bytes=c['new_packet_sum_bytes'],common_source_jsonl_identity_only=v['new_common'],original_assignment_binding=bind(ORIGINAL/bid/'assignment.json'),actor_instructions=bind(HERE/'actor-instructions.txt'),output_schema=bind(directory/'output.schema.json'),output_validation_contract=bind(directory/'output-validation-contract.json'),strict_technical_validator=bind(HERE/'base-validator.py'),attempt_output_routing=bind(directory/'attempt-output-routing.json'),campaign_scope_metadata_binding=bind(HERE/'neutral-material-transport-contract.json'),presentation_helper=bind(HERE/'emit-presentation.py'),submit_helper=bind(HERE/'submit-first.py'))
    # Both required exact TXT sources are already present in the original asset inventory.
    assert a['source_asset_bindings']==old['source_asset_bindings']
    for x in a['packets']+a['source_asset_bindings']:exact(x)
    save(bid+'/assignment.json',a);batches.append(dict(batch_id=bid,source_ids=a['source_ids'],assignment=bind(directory/'assignment.json')))
    delta=sorted(differences(load(Path(old['output_schema']['path'])),schema));assert delta==sorted(['/properties/run_id/const','/properties/scope/const',f'/properties/records/prefixItems/{changes[0]}/properties/packet_sha256/const'])
    checks.append(dict(batch_id=bid,schema_changed_paths=delta,original_member_order_unchanged=True,scientific_manual_prompt_protocol_exact=all(a[k]==old[k] for k in ['manual','execution_prompt','run_scope_binding']),source_asset_inventory_exact=True,packet_bytes=a['packet_bytes'],unchanged_packets=11))
manifest={k:old_manifest[k] for k in ['base_guard','cli_launcher','conceptual_protocol_cap','max_total_technical_attempts','model_requested','reasoning_requested','provider_identity_verified','formal_validation_complete']}
manifest.update(run_id=HERE.name,scope=scope,source_N=24,batch_N=2,batches=batches,runner=bind(HERE/'runner.py'),receiver=bind(HERE/'strict-readback-receiver.py'),validator=bind(HERE/'base-validator.py'),instructions=bind(HERE/'actor-instructions.txt'),transport_contract=bind(HERE/'neutral-material-transport-contract.json'),presentation_helper=bind(HERE/'emit-presentation.py'),submit_helper=bind(HERE/'submit-first.py'),v17_material_seal=bind(V17/'output-seal.json'),v17_material_manifest=bind(V17/'source-extension-manifest-v17.json'),parent_collection_seal=bind(ROOT/'06-coding/native-full4481-v16-three-member-compatible-root/seal.json'),actual_concurrency_cap=1,technical_states_only=True,actual_execution=False)
save('manifest.json',manifest)
save('ROOT-execution-binding.TEMPLATE.json',{'author':'ROOT','template_only':True,'execution_authorized':False,'at_utc':None,'run_id':HERE.name,'authorized_entrypoint':bind(HERE/'runner.py'),'preparation_seal':None,'batch_ids':[b['batch_id'] for b in batches],'native_additional_concurrency_cap':1,'single_transport_owner':False,'parent_collection_seal':manifest['parent_collection_seal'],'capacity_reservation':{'confirmed_by_ROOT':False,'stability_capacity_can_accommodate':False,'reserved_additional_cli_slots':1,'reserved_for_run_id':HERE.name,'existing_stability_configuration_unchanged':True,'observed_at_utc':None,'observed_capacity_evidence':None},'note':'Template only, no dispatch. ROOT fills real current capacity evidence and reserves one additional CLI slot before creating ROOT-execution-binding.json.'})
for p in HERE.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
save('offline-identity-checks.json',{'checks':checks,'identical_reused_modules':[{'new':bind(HERE/n),'old':bind(OLD/n),'byte_equal':(HERE/n).read_bytes()==(OLD/n).read_bytes()} for n in ['base-validator.py','emit-presentation.py','submit-first.py']],'receiver_only_difference':'new_v16_material_delta -> new_v17_material_delta','model_calls':0,'CLI_starts':0,'actual_attempt_directories_created':False,'schemas_to_check_with_jsonschema_at_readonly_preflight':True})
print(json.dumps({'prepared':str(HERE),'batch_N':2,'source_N':24,'model_calls':0},ensure_ascii=False))
