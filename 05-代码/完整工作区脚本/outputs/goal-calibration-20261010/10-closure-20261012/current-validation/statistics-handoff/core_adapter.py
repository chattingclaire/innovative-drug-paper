"""The original mathematics, with only metadata and project-review gates replaced.

No before_answers alias is supplied. Source files remain immutable. The two
replacement functions operate on the independently received immutable payload.
"""
import ast,types
from support import module,require,canonical,verify,load,HERE,REGISTRY_SHA

def analyze_received(payload,authority,admission,deps,*,synthetic):
    core=module('_immutable_current_reuse_math',deps['core'])
    require(payload['data_role']==('synthetic'if synthetic else'sealed_project'),'Data role cannot bypass actual authority')
    require(authority.get('actual_ROOT_adoption')is(not synthetic),'Actual ROOT adoption must come from unique handoff registry')
    if not synthetic:
        rb=authority.get('registry_binding'); path=verify(rb)
        require(path==HERE/'ROOT-registry.UNADOPTED.json'and rb['sha256']==REGISTRY_SHA,'Core receives the same unique externally pinned registry')
        request_binding=authority.get('request_binding');request=load(verify(request_binding))
        entry=load(path)['registrations'].get(request.get('registration_id'))
        require(isinstance(entry,dict)and entry.get('request_binding')==request_binding and entry.get('ROOT_review_binding')==authority.get('ROOT_review_binding'),'Core cannot confer adoption from caller booleans')
        review=load(verify(authority['ROOT_review_binding']))
        require(review.get('status')=='ROOT_reviewed_actual_reuse_handoff_originals'and review.get('control_or_synthetic')is False,'Actual ROOT review required at mathematical handoff')
    require(admission.get('metadata_component_only')is True and admission.get('actual_ROOT_adoption')is False,'Use honest validated metadata helper receipt, not a relabeled adoption')
    expected_payload=canonical(payload); base_validate=core._validate_metadata
    prior={name:obj for name,obj in vars(core).items()if isinstance(obj,types.FunctionType)}
    def validate_received(value):
        require(canonical(value)==expected_payload,'Received source/label join changed after review')
        role,meta,active=base_validate(value)
        require(meta['scope']['kind']=='current_frozen_remaining_reuse','New finite scope required; no historical alias')
        require(meta['scope']['population_N']==admission['target_N'],'Scope differs from reviewed target')
        require(meta['scope']['conditional_on_frozen_model_domain_and_C']is True,'Conditional target must be explicit')
        require('freeze_attestations'not in meta,'Legacy before_answers metadata is forbidden')
        require(meta['reuse_temporal_receipt_sha256']==canonical(admission),'Truthful temporal receipt binding differs')
        require(meta['handoff_authority_sha256']==canonical(authority),'Actual authority binding differs')
        return role,meta,active
    def review_received(prepared,numeric):
        require(canonical(prepared['meta'])==canonical(payload['metadata']),'Prepared metadata changed')
        return {'all_numerical_point_targets_met':numeric,
                'metadata_attestations_complete_for_project_review':not synthetic,
                'prerequisite_gaps':['Synthetic control is not actual validation']if synthetic else[],
                'formal_acceptance':False,
                'formal_acceptance_status':'requires_explicit_interpretation_of_numeric_results_scope_and_unknowns',
                'actual_ROOT_adoption':not synthetic,'truthful_inherited_timing_used':True,
                'legacy_before_answers_attestation_created':False,
                'finite_target_population_N':admission['target_N'],
                'conditional_on_frozen_model_domain_and_certainty_set':True,
                'validates_all4481_or_future_policies':False,
                'original200_historical_design_is_a_separate_use':True,
                'CI_lower_or_halfwidth_gate_added':False,
                'metadata_cannot_authenticate_human_identity_on_its_own':True}
    core._validate_metadata=validate_received;core.review_eligibility=review_received
    unchanged=[name for name,obj in prior.items()if name not in('_validate_metadata','review_eligibility')and getattr(core,name)is obj]
    require(len(unchanged)==len(prior)-2,'A mathematical/state function was replaced')
    source=ast.parse(verify(deps['core']).read_text())
    functions={node.name:ast.dump(node,include_attributes=False)for node in source.body if isinstance(node,ast.FunctionDef)}
    result=core.analyze(payload,replicates=5000,seed=20261010,guard_mode='single_category')
    count=sum(len(targets)for comp in result['numeric_targets'].values()for targets in comp.values())
    expected={'human_first':5,'machine_reference':40,'combined':45}[payload['metadata']['analysis_stage']]
    require(count==expected,'Active-stage numeric target count differs from original core')
    return result,{'core_binding':deps['core'],'source_file_modified':False,
                   'replaced_qualification_functions':['_validate_metadata','review_eligibility'],
                   'all_other_function_objects_identical':True,'unchanged_function_count':len(unchanged),
                   'unchanged_function_AST_sha256':canonical({name:functions[name]for name in unchanged}),
                   'original_states_thresholds_FPC_guards_intervals_analyze_preserved':True,
                   'original_analyze_uses_one_shared_W':True,'replicates':5000,'seed':20261010,
                   'numeric_target_N':count}
