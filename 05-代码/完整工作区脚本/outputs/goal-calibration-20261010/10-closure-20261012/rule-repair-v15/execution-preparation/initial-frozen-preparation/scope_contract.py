"""Exact full-frame identity and one external ROOT release; no inference."""
from pathlib import Path
from merge_common import bind, exact, load

H=Path(__file__).resolve().parent
VERSION='full4481-v15-current-v17-first-candidate-1'
MODULES=('source_packet','source_receipts','evidence','relations','dimensions')
IMPLEMENTATION_FILES=('rule_driver.py','interface_common.py','status_bridge.py',
 'literal_inventory_bridge.py','merge_common.py','scope_contract.py',
 'receive_boundaries.py','receive_merge.py','finalize_scope.py',
 'actual-first-run-supervisor.py','packet-bindings.json','full-frame.json',
 'source-material-bindings.json','comparison-baseline-bindings.json','execution-contract.json')

def require(ok,why):
    if not ok:raise ValueError(why)

def contract():
    c=load(H/'execution-contract.json')
    require(c['actual_record_N']==4481 and c['dimension_N']==22405 and c['inherited_record_N']==0 and c['max_runs']==1,'full frame/one-run contract changed')
    for key in ['plan','source_input','source_package_seal','source_manifest','source_extension_manifest',
                'packet_bindings','full_frame','source_material_bindings','comparison_baseline_bindings',
                'manual','prompt','protocol','source_reading_protocol_code','wait_helper']:exact(c[key])
    for b in c['source_bindings']:exact(b)
    return c

def algorithm(binding):
    exact(binding);a=load(binding['path'])
    require(isinstance(a.get('algorithm_version'),str) and a['algorithm_version'],'final frozen algorithm version required')
    mods=a.get('modules',[])
    require([m.get('module') for m in mods]==list(MODULES),'exact five-module manifest required')
    parents={str(Path(m['path']).resolve().parent) for m in mods}
    require(len(parents)==1,'five modules must belong to one frozen candidate')
    parent=Path(next(iter(parents)))
    require(parent.parent==H.parents[2]/'06-coding/rule-five-dimension-joint-root/versions','candidate outside declared version directory')
    require(parent.name==a['algorithm_version'],'algorithm version differs from actual directory')
    for m in mods:
        require(Path(m['path']).name==m['module']+'.py','module/file identity differs');exact(m)
    return a

def expected_implementation(algorithm_binding):
    a=algorithm(algorithm_binding)
    return [bind(H/n) for n in IMPLEMENTATION_FILES]+[algorithm_binding]+a['modules']

def build_scope(release_binding):
    """Only derives a scope from an existing truthful ROOT release."""
    c=contract();exact(release_binding);r=load(release_binding['path'])
    require(r.get('status')=='released_for_production_provisional' and r.get('issuer')=='ROOT','actual external ROOT release absent')
    require(r.get('authorization_id') and r.get('execution_purpose')=='production_provisional','release purpose/identity absent')
    require(r.get('execution_contract')==bind(H/'execution-contract.json'),'release changed reviewed full-frame preparation')
    for k in ['output_directory','received_directory','wait_directory','allowed_mutable_dimensions','immutable_dimensions','conditional_S_contract']:
        require(r.get(k)==c[k],'release changes '+k)
    require(r.get('max_actual_cohort_inference_runs')==1 and r.get('actual_record_N')==4481 and r.get('inherited_record_N')==0,'release is not one complete actual frame')
    for k,rk in [('manual','manual'),('prompt','prompt'),('protocol','protocol'),('source_input','source_input')]:
        require(r.get(rk)==c[k],'release material mismatch '+k)
    require(r.get('final_algorithm_and_controls_reviewed') is True,'ROOT final candidate/control review not declared')
    for k in ['algorithm_manifest','candidate_code_review','integrated_control_result']:exact(r[k])
    a=algorithm(r['algorithm_manifest'])
    require(r.get('implementation_bindings')==expected_implementation(r['algorithm_manifest']),'release implementation differs')
    require(isinstance(r.get('semantic_change'),str) and r['semantic_change'].strip(),'final semantic change must be described truthfully')
    frames=load(c['full_frame']['path']);packets=load(c['packet_bindings']['path'])
    require(frames['ordered_source_ids']==packets['ordered_source_ids'] and len(set(frames['ordered_source_ids']))==4481,'full ordered ID frame differs')
    require(packets['packet_N']==4481 and len(packets['packets'])==4481,'full packet count differs')
    require(packets['packets']==load(packets['current_complete_packet_manifest']['path']),'full original packet mapping changed')
    materials={}
    def add(b):
        p=b['path'];simple={k:b[k] for k in ['path','bytes','sha256']}
        require(p not in materials or materials[p]==simple,'conflicting file binding')
        materials[p]=simple
    for b in load(c['source_material_bindings']['path'])['materials']:add(b)
    for k in ['source_input','manual','prompt','protocol','source_reading_protocol_code','source_package_seal','source_manifest','source_extension_manifest']:add(c[k])
    for k in ['algorithm_manifest','candidate_code_review','integrated_control_result']:add(r[k])
    add(release_binding)
    scope={'driver_version':VERSION,'status':'frozen_for_execution','execution_purpose':'production_provisional',
      'authorization_id':r['authorization_id'],'release':release_binding,
      'execution_contract':bind(H/'execution-contract.json'),'algorithm_bindings':r['algorithm_manifest'],
      'candidate_algorithm_version':a['algorithm_version'],'semantic_change':r['semantic_change'],
      'candidate_code_review':r['candidate_code_review'],'integrated_control_result':r['integrated_control_result'],
      'algorithm_origin':'one complete actual inference over all frozen v17 records; zero inherited predictions',
      'output_directory':c['output_directory'],'received_directory':c['received_directory'],'wait_directory':c['wait_directory'],
      'max_actual_cohort_inference_runs':1,'full_frame_actual_execution':True,'inherited_record_N':0,
      'expected_record_N':4481,'expected_dimension_N':22405,'approved_record_ids':frames['ordered_source_ids'],
      'full_frame':c['full_frame'],'packet_bindings':c['packet_bindings'],'source_packet':c['source_input'],
      'source_package_seal':c['source_package_seal'],'source_manifest':c['source_manifest'],
      'complete_bundles_canonical_sha256':c['source_input']['sha256'],
      'source_manifest_sha256':c['source_manifest']['sha256'],'v12_source_base':c['v12_source_base'],
      'material_bindings':list(materials.values()),'material_changed_record_ids':c['material_changed_record_ids'],
      'manual_version':c['manual_version'],
      **{k:c[k] for k in ['manual','prompt','protocol','source_reading_protocol_code','allowed_mutable_dimensions','immutable_dimensions','conditional_S_contract']},
      'formal_validation_complete':False,'human_validation_complete':False,'blind_validation':False,
      'calibration_labels_already_disclosed':True,'new2_new4_reference_comparison_authorized':False,
      'new_material_adopted':False,'neutral_projection_GO':False}
    return scope

def validate_full_scope(scope):
    require(isinstance(scope,dict) and isinstance(scope.get('release'),dict),'actual scope/release required')
    expected=build_scope(scope['release'])
    require(scope==expected,'scope differs from exact full frame and ROOT release derivation')
    return scope

def driver_argv(scope_path,scope):
    c=contract();return [c['python_executable'],'-B',str(H/'rule_driver.py'),
      '--scope',str(Path(scope_path).resolve()),'--scope-sha256',bind(scope_path)['sha256'],
      '--input',scope['source_packet']['path'],'--input-sha256',scope['source_packet']['sha256'],
      '--out',scope['output_directory']]
