"""One real entry point: approved original bytes -> full fixed join -> original math.

Real registry is deliberately empty until actual design and human receipts exist.
The legacy reuse/engine registries are not additional gates and are not edited.
"""
from pathlib import Path
import argparse,json
from support import *
from human_projection import project_humans
from core_adapter import analyze_received
import machine_projection

def authority_gate(request_path,synthetic):
    request=load(request_path)
    require(request.get('schema')=='current-reuse-statistics-handoff-v1','Wrong handoff request schema')
    require(request.get('synthetic_only')is synthetic,'Synthetic/actual mode mismatch')
    if synthetic:
        require(request.get('registration_id','').startswith('TOY-'),'Control must use TOY registration identity')
        return request,{'actual_ROOT_adoption':False,'synthetic_only':True,'request_binding':binding(request_path)}
    registry_path=HERE/'ROOT-registry.UNADOPTED.json'
    require(binding(registry_path)['sha256']==REGISTRY_SHA,'Unique real registry external pin changed')
    entry=load(registry_path)['registrations'].get(request.get('registration_id'))
    require(isinstance(entry,dict),'No ROOT-adopted complete handoff registration; no human or machine labels opened')
    require(entry.get('request_binding')==binding(request_path),'Exact handoff request not ROOT registered')
    review=load(verify(entry.get('ROOT_review_binding')))
    require(review.get('status')=='ROOT_reviewed_actual_reuse_handoff_originals'and review.get('control_or_synthetic')is False,'Actual original receipt review missing')
    require(review.get('request_binding')==binding(request_path),'Review binds a different complete handoff')
    require(all(review.get(k)is True for k in('actual_human_identities_and_first_submissions_reviewed','truthful_group_timing_and_blinding_reviewed','actual_new_design_and_once_only_draw_reviewed','original_projection_and_current_machine_receipts_reviewed')),'Required actual receipt review incomplete')
    return request,{'actual_ROOT_adoption':True,'synthetic_only':False,'registry_binding':binding(registry_path),
                    'ROOT_review_binding':entry['ROOT_review_binding'],'request_binding':binding(request_path)}

def build(request_path,*,synthetic=False):
    # Fail before dependencies, originals, or labels when actual registry is empty.
    request,authority=authority_gate(Path(request_path),synthetic)
    deps=dependencies();reuse_module=module('_reviewed_reuse_temporal_contract',deps['reuse_admission'])
    reuse=load(verify(request['reuse_request_binding']))
    stage=request.get('analysis_stage')
    require(stage in('human_first','machine_reference','combined'),'Supported actual analysis stage required')
    require(reuse['stage']==('human_first'if stage=='human_first'else'machine_reference'),'Human/reference receipt stage differs')
    if synthetic:
        view=load(verify(request['synthetic_view_binding']))
        frame_rows=jsonlines(verify(request['synthetic_full_frame_binding']))
        root=Path(request_path).resolve().parent
        require(root.is_relative_to(HERE/'controls'),'Synthetic requests live only under this candidate controls directory')
        def toy_originals(value):
            if isinstance(value,dict):
                if set(value)=={'path','bytes','sha256'}:
                    require(Path(value['path']).resolve().is_relative_to(root),'Synthetic original/evidence cannot point to project originals outside its control directory')
                else:
                    for child in value.values():toy_originals(child)
            elif isinstance(value,list):
                for child in value:toy_originals(child)
        toy_originals(reuse);toy_originals(view);toy_originals(request['human_sources'])
    else:
        require(not any(k.startswith('synthetic_')for k in request if k!='synthetic_only'),'Synthetic sources prohibited in real request')
        view=reuse_module.current_view()
        frame_rows=jsonlines(verify(deps['full_frame']))
    require(len({r['unit_id']for r in frame_rows})==len(frame_rows),'Duplicate full source identity')
    require(all(set(r)=={'unit_id','department','source_identity_sha256'}for r in frame_rows),'Full frame must be identity metadata only')
    require(all(r['unit_id'].startswith('TOY-')==synthetic and len(r['source_identity_sha256'])==64 for r in frame_rows),'Frame/control identity invalid')
    frame={r['unit_id']:r for r in frame_rows}
    if not synthetic: require(len(frame)==4481 and len(view['target'])==1261,'Actual current frozen4481/1261 required')
    require(set(r['unit_id']for r in view['target'])<=set(frame),'Target outside actual source frame')
    require(all(frame[r['unit_id']]['department']==r['department']for r in view['target']),'Source department differs')
    # Pure helper remains honestly unadopted; authority above is the sole adoption.
    admission=reuse_module.validate_metadata(reuse,view,synthetic=synthetic)
    require(admission['actual_ROOT_adoption']is False,'Pure metadata helper must not self-adopt')
    humans,human_proof=project_humans(reuse,view,request['human_sources'],frame,deps,synthetic=synthetic)
    assigned=reuse['draw']['records'];assigned_ids=[r['unit_id']for r in assigned]
    for method,outputs in humans.items():require(set(outputs)==set(assigned_ids),'Human projection omitted or added an assigned unit: '+method)
    machines=None
    if stage!='human_first':
        if synthetic:
            mk=request['synthetic_machine_sources']
            machines=machine_projection.project_machines(mk['machine_freeze_binding'],list(frame),synthetic=True,synthetic_sources=mk['synthetic_sources'])
        else:
            machines=machine_projection.project_machines(deps['machine_freeze'],list(frame))
        require(set(machines['rule'])==set(frame)and set(machines['LLM'])==set(frame),'Machines must cover complete frozen frame before selecting validation IDs')
    active={'human_first':['A','B'],'machine_reference':['reference','rule','LLM'],'combined':['A','B','reference','rule','LLM']}[stage]
    rows=[]
    for assigned_row in assigned:
        uid=assigned_row['unit_id']; outputs={}
        for method in active:outputs[method]=humans[method][uid]if method in humans else machines[method][uid]
        rows.append({'unit_id':uid,'stratum_id':assigned_row['stratum_id'],'department':frame[uid]['department'],'outputs':outputs})
    strata=[{'id':h['id'],'N':h['N'],'n':h['n'],'department':h['department'],'domain':'remaining'}for h in reuse['design']['strata']]
    source_proof={m:human_proof[m]if m in humans else machines['provenance']for m in active}
    meta={'analysis_stage':stage,'scope':{'kind':'current_frozen_remaining_reuse','population_N':len(view['target']),
          'frame_ids_sha256':canonical(sorted(r['unit_id']for r in view['target'])),
          'conditional_on_frozen_model_domain_and_C':True},
          'design':{'kind':'stratified_srswor','sampling_unit':'source_unit','strata':strata,
                    'assigned_ids_sha256':canonical(sorted(assigned_ids)), 'domain_population_N':{'remaining':len(view['target'])}},
          'reuse_temporal_receipt_sha256':canonical(admission),'handoff_authority_sha256':canonical(authority),
          'input_seals':{m:{'sealed':True,'sha256':(machines['provenance']['original_output_bindings'][m]['sha256']if m in('rule','LLM')else canonical(source_proof[m])),
                            'joined_projection_sha256':canonical([{'unit_id':r['unit_id'],'output':r['outputs'][m]}for r in sorted(rows,key=lambda x:x['unit_id'])])}
                         for m in active},
          'input_seal_hash_kind':'SHA256 of source provenance chain; actual original file bindings retained in receipt',
          'identities':{p:{'identity_code':reuse['human_receipts'][p]['identity_code'],'kind':'human_initial'if p in('A','B')else'human_adjudication'}for p in reuse['human_receipts']}}
    payload={'data_role':'synthetic'if synthetic else'sealed_project','metadata':meta,'records':rows}
    provenance={'authority':authority,'metadata_component_receipt':admission,'human_original_projections':human_proof,
                'machine_projection':machines['provenance']if machines else None,
                'original200_not_modified_or_reweighted':True,'current_C_and_supplement_new_probabilities':reuse['draw']['records'],
                'all_assigned_NULL_failed_unreturned_retained':True,'no_legacy_before_answers_attestation':True}
    return payload,authority,admission,deps,provenance

def execute(request_path,output_dir,*,synthetic=False):
    output=Path(output_dir).resolve()
    require(output.is_relative_to(HERE/'runs')and output!=HERE/'runs'and not output.exists(),'Use a new output directory below statistics-handoff/runs; never overwrite')
    payload,authority,admission,deps,provenance=build(request_path,synthetic=synthetic)
    result,math_proof=analyze_received(payload,authority,admission,deps,synthetic=synthetic)
    output.parent.mkdir(parents=True,exist_ok=True);output.mkdir(exist_ok=False)
    save_new(output/'joined-input.json',payload);save_new(output/'results.json',result)
    save_new(output/'provenance.json',provenance);save_new(output/'mathematics-identity.json',math_proof)
    receipt={'status':'synthetic_end_to_end_control_only'if synthetic else'actual_registered_current_remaining_results',
             'synthetic_only':synthetic,'actual_ROOT_adoption':authority['actual_ROOT_adoption'],
             'population_N':admission['target_N'],'certainty_N':admission['certainty_N'],
             'assigned_N':len(payload['records']),'analysis_stage':payload['metadata']['analysis_stage'],
             'numeric_target_N':math_proof['numeric_target_N'],'replicates':5000,'shared_W':True,
             'formal_acceptance':False,'validates_all4481_or_future_policies':False,
             'members':[binding(p)for p in sorted(output.iterdir())if p.is_file()]}
    save_new(output/'receipt.json',receipt)
    return receipt

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--request',required=True);p.add_argument('--output-dir',required=True);p.add_argument('--synthetic-control',action='store_true');a=p.parse_args()
    result=execute(a.request,a.output_dir,synthetic=a.synthetic_control)
    print(json.dumps({k:result[k]for k in('status','population_N','assigned_N','numeric_target_N','formal_acceptance')},ensure_ascii=False))

if __name__=='__main__':main()
