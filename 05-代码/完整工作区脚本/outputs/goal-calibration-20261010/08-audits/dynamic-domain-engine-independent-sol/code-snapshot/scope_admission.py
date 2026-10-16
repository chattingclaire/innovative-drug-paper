"""Registered source/draw/status admission, with no sampling or statistical math.

ROOT's immutable registry is the trusted local release authority. The current
registry is empty. SHA binds ROOT-reviewed artifacts, not human identity.
Synthetic fixture admission is separate and can never activate sealed_project.
"""
import hashlib
import json
from collections import Counter
from fractions import Fraction
from pathlib import Path
HERE=Path(__file__).resolve().parent
SCOPE_KINDS={'registered_full_4481_audit':'full_4481_audit','registered_remaining_pool':'remaining_pool'}
REGISTRY_PATH=HERE/'ROOT-scope-registry.UNADOPTED.json'
REGISTRY_SHA256='74bf9727bae061068ddfdc575681698170c66a254541568fe1527de7c059066e'
FROZEN_STATISTICAL_CORE_SHA256='f6b33491bb27d7325cdc18c25fb7d54fef45909e1ef38c3f27606edcb61c2262'
STATISTICS_CONTRACT_SHA256='e53487ee355a1a8872833f7740edef1368035565b35a35817c4e171b976e2266'
ORIGINAL_FRAME_IDS_BINDING={'path':str(HERE.parents[1]/'06-coding/full4481-common-v15-production-preparation-sol/approved_record_ids.json'),'bytes':76341,'sha256':'602588f7bdbba615b43598ab33cca7f41e618f2e2142575a72899738112bfbbe'}


def require(ok,message):
    if not ok:raise ValueError(message)


def canonical(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def strict_json(raw):
    def pairs(items):
        out={}
        for k,v in items:require(k not in out,'Duplicate key in registered artifact: '+k);out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Invalid number in registered artifact')))


def binding(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def verify(b):
    require(isinstance(b,dict) and set(b)=={'path','bytes','sha256'},'Exact registered path/bytes/SHA binding required')
    require(Path(b['path']).is_absolute() and type(b['bytes']) is int and b['bytes']>=0,'Absolute path and integer byte count required')
    require(binding(b['path'])==b,'Registered artifact SHA/bytes changed: '+str(b['path']))
    return Path(b['path']).resolve()


def load(b):return strict_json(verify(b).read_text())


def rows(b):return [strict_json(x) for x in verify(b).read_text().splitlines() if x.strip()]


def unique_rows(items,key):
    require(isinstance(items,list) and items and all(isinstance(r,dict) for r in items),'Nonempty registered rows required')
    ids=[r.get(key) for r in items]
    require(all(isinstance(rid,str) and rid for rid in ids) and len(set(ids))==len(ids),'Unique exact registered IDs required')
    return {r[key]:r for r in items}



def validate_original_frame_identity(approved_binding,source_ids):
    # Anchor original4481 wrapper externally to this frozen candidate, rather
    # than allowing a caller's self-consistent replacement wrapper.
    require(approved_binding==ORIGINAL_FRAME_IDS_BINDING,'Original approved4481 ID wrapper differs from code-pinned path/bytes/SHA')
    old=load(approved_binding)
    require(set(old)=={'approved_record_ids','frame_order_UTF8_LF_sha256','preserves_original_FRAME4481_order'},'Original approved-ID wrapper structure changed')
    ids=old['approved_record_ids']
    require(isinstance(ids,list) and len(ids)==4481 and len(set(ids))==4481 and all(isinstance(rid,str) and rid for rid in ids),'Original approved4481 IDs must be a unique complete list')
    require(old['preserves_original_FRAME4481_order'] is True and ids==source_ids,'Registered full frame differs from original4481 order')
    require(hashlib.sha256(('\n'.join(source_ids)+'\n').encode()).hexdigest()==old['frame_order_UTF8_LF_sha256'],'Original full frame order receipt differs')

def registry_entry(payload):
    meta=payload.get('metadata',{});scope=meta.get('scope',{});kind=scope.get('kind');role=payload.get('data_role')
    if kind not in SCOPE_KINDS:
        if role=='sealed_project':require(kind in ('full_4481_audit','remaining_1444'),'Unregistered sealed_project scope cannot bypass old domain guards')
        require('synthetic_registration_fixture' not in meta,'Fixture must be used only with a named synthetic registered scope')
        return None
    rid=scope.get('registration_id');require(isinstance(rid,str) and rid,'New scope requires a registration_id')
    require(role in ('synthetic','sealed_project'),'New registered scope is not historical arithmetic')
    if role=='synthetic':
        b=meta.get('synthetic_registration_fixture');descriptor=load(b)
        require(descriptor.get('synthetic_only') is True and descriptor.get('status')=='synthetic_fixture_not_ROOT_approved','Synthetic fixture cannot impersonate ROOT registration')
        require(descriptor.get('registration_id')==rid,'Synthetic registration ID differs')
        return descriptor,{'authority':'synthetic_fixture_only','registration_binding':b,'actual_ROOT_adoption':False}
    require('synthetic_registration_fixture' not in meta,'Synthetic fixture cannot activate real project execution')
    require(binding(REGISTRY_PATH)['sha256']==REGISTRY_SHA256,'ROOT registry changed or is not pinned by this release')
    registry=strict_json(REGISTRY_PATH.read_text())
    require(registry.get('schema')=='ROOT-dynamic-prospective-scope-registry-v1' and registry.get('authority')=='ROOT','ROOT registered authority required')
    entry=registry.get('registrations',{}).get(rid)
    require(isinstance(entry,dict),'Scope has not been ROOT-adopted; current exposure candidate is not a registration')
    approval=load(entry.get('ROOT_approval_binding'));descriptor=load(entry.get('registration_binding'))
    require(approval.get('status')=='ROOT_reviewed_frozen_scope_design_before_answers' and approval.get('control_or_synthetic') is False,'Actual ROOT scope review required')
    require(approval.get('registration_binding')==entry['registration_binding'] and approval.get('registration_id')==rid,'ROOT scope review binds a different registration')
    require(approval.get('no_validation_label_based_scope_or_allocation') is True and approval.get('no_actual_accuracy_used_in_activation') is True,'Scope/draw must precede test-label feedback')
    require(descriptor.get('synthetic_only') is False and descriptor.get('status')=='ROOT_frozen_scope_materials_versions_design_and_draw','Not an actual final source/design freeze')
    require(descriptor.get('registration_id')==rid,'Registered descriptor ID differs')
    descriptor=dict(descriptor,_ROOT_admitted_submission_receipts=entry.get('admitted_submission_receipts',{}))
    return descriptor,{'authority':'ROOT_pinned_registry','registry_binding':binding(REGISTRY_PATH),'registration_binding':entry['registration_binding'],'ROOT_approval_binding':entry['ROOT_approval_binding'],'actual_ROOT_adoption':True}


def validate_registration(descriptor,scope,synthetic=False):
    require(scope.get('kind') in SCOPE_KINDS,'Named dynamic scope required')
    estimand=SCOPE_KINDS[scope['kind']]
    require(descriptor.get('estimand')==estimand,'Registered estimand differs from requested scope')
    require(descriptor.get('statistical_core_sha256')==FROZEN_STATISTICAL_CORE_SHA256,'Mathematical/annual core changed')
    require(descriptor.get('statistics_contract_sha256')==STATISTICS_CONTRACT_SHA256,'Registered metric contract changed')
    require(descriptor.get('statistical_execution')=={'replicates':5000,'seed':20261010,'guard_mode':'single_category','numeric_gate':'unchanged_45_ALL_point_targets','new_CI_threshold':False},'Registered statistical settings differ from frozen contract')
    for key in ('full_frame','domain_partition','stratum_membership','design_contract','original_draw','common_manual','common_materials','rule_version','LLM_version','exposure_freeze'):
        verify(descriptor.get(key))
    full=rows(descriptor['full_frame']);fb=unique_rows(full,'unit_id')
    require(len(full)==4481,'Exact complete4481 frame required')
    require(all(isinstance(r.get('department'),str) and r['department'] for r in full),'Every frame row needs frozen department')
    require(all(not (set(r)-{'unit_id','department','source_identity_sha256'}) for r in full),'Frame is source identity metadata only, no label/exposure override')
    require(all(isinstance(r.get('source_identity_sha256'),str) and len(r['source_identity_sha256'])==64 and all(c in '0123456789abcdef' for c in r['source_identity_sha256']) for r in full),'Every source frame identity needs exact bundle SHA256')
    material=load(descriptor['common_materials']);material_rows=material.get('records',[]);materialby=unique_rows(material_rows,'unit_id')
    require(material.get('status')==('synthetic_common_materials_identity_fixture' if synthetic else 'ROOT_frozen_complete_common_materials_identity_manifest'),'Complete same-frame common material identity manifest required')
    require(list(materialby)==list(fb) and all(set(r)=={'unit_id','source_bundle_sha256'} and r['source_bundle_sha256']==fb[r['unit_id']]['source_identity_sha256'] for r in material_rows),'Common material manifest must match every source frame bundle identity')
    verify(material.get('source_packet_binding'))
    if synthetic:require(all(r['unit_id'].startswith('TOY-') for r in full),'Synthetic positive fixtures must use TOY identities')
    else:
        validate_original_frame_identity(descriptor.get('original_4481_ids'),list(fb))
    part=rows(descriptor['domain_partition']);pb=unique_rows(part,'unit_id')
    require(list(pb)==list(fb),'Domain partition must cover full4481 exactly in frame order')
    for rid,p in pb.items():
        require(set(p)=={'unit_id','department','domain','family_id','exposure_status'},'Domain partition accepts no arbitrary counts or label fields')
        require(p['department']==fb[rid]['department'] and p['domain'] in ('remaining','exposed'),'Domain/department integrity differs')
        require(isinstance(p['family_id'],str) and p['family_id'],'Frozen text-family identity required')
        require(p['exposure_status'] in ('unexposed_at_final_freeze','direct','family_exposed'),'Exposure status incomplete/unknown')
        require((p['domain']=='remaining')==(p['exposure_status']=='unexposed_at_final_freeze'),'Domain does not match registered exposure status')
    families={}
    for p in part:families.setdefault(p['family_id'],set()).add(p['domain'])
    require(all(len(v)==1 for v in families.values()),'Exact text family spans exposed and remaining; exclusion closure incomplete')
    exposure=load(descriptor['exposure_freeze'])
    require(exposure.get('status')==('synthetic_final_exposure_fixture' if synthetic else 'ROOT_final_exposure_freeze_before_draw'), 'Intermediate exposure candidate is not final freeze')
    require(exposure.get('domain_partition_binding')==descriptor['domain_partition'] and exposure.get('family_closure_complete') is True,'Final exposure evidence does not bind exact partition/closure')
    require(exposure.get('no_validation_results_used') is True,'Exposure freeze cannot use new validation outcomes')
    dn=dict(Counter(r['domain'] for r in part));require(set(dn)=={'remaining','exposed'} and sum(dn.values())==4481,'Both nonempty domains must exactly partition4481')
    target=[r['unit_id'] for r in part if estimand=='full_4481_audit' or r['domain']=='remaining'];targetset=set(target)
    membership=rows(descriptor['stratum_membership']);mb=unique_rows(membership,'unit_id')
    require(list(mb)==target,'Stratum frame must exactly cover registered estimand in original order; no zero-pi omissions')
    require(all(set(r)=={'unit_id','stratum_id'} and isinstance(r['stratum_id'],str) and r['stratum_id'] for r in membership),'Frozen strata identity required')
    design=load(descriptor['design_contract'])
    require(design.get('status')==('synthetic_design_frozen_before_draw' if synthetic else 'ROOT_design_frozen_before_draw_and_answers'),'Original pre-draw design required')
    require(design.get('kind')=='stratified_srswor' and design.get('sampling_unit')=='source_unit','Only fixed one-stage source SRSWOR implemented')
    require(design.get('estimand')==estimand and design.get('planned_allocation_before_answers') is True,'Estimand/allocation not pre-frozen')
    require(design.get('frame_binding')==descriptor['full_frame'] and design.get('partition_binding')==descriptor['domain_partition'] and design.get('stratum_membership_binding')==descriptor['stratum_membership'],'Design used different registered source/partition/strata')
    require(type(design.get('seed')) is int,'Original draw seed must be an integer')
    strata=design.get('strata');sb=unique_rows(strata,'id');mh=Counter(r['stratum_id'] for r in membership)
    require(set(mh)==set(sb),'All nonempty population strata must be registered; no additional or omitted layer')
    for hid,s in sb.items():
        require(set(s)=={'id','N','n','department','domain'},'Registered layer table only accepts actual population/allocation fields')
        require(type(s['N']) is int and type(s['n']) is int and s['N']==mh[hid] and 1<=s['n']<=s['N'],'Layer N must equal actual complete frame membership and n must be positive')
        require(s['n']==s['N'] or s['n']>=2,'Noncensus singleton has unidentified variance')
        for rid in (r['unit_id'] for r in membership if r['stratum_id']==hid):require(s['domain']==pb[rid]['domain'] and s['department']==fb[rid]['department'],'Layer domain/department differs from exact unit membership')
    require(sum(s['N'] for s in strata)==len(target),'Registered population not fully covered by layers')
    draw=load(descriptor['original_draw'])
    require(draw.get('status')==('synthetic_demonstration_draw_only' if synthetic else 'ROOT_actual_draw_completed_before_answers'),'Actual original draw evidence required, not a planned blank draw')
    require(draw.get('design_binding')==descriptor['design_contract'] and draw.get('seed')==design['seed'],'Original draw uses different design/seed')
    require(draw.get('answers_read_for_draw') is False and draw.get('redraw_or_outcome_adaptive') is False,'Post-outcome/redraw allocation forbidden')
    assigned=draw.get('records');ab=unique_rows(assigned,'unit_id');nh=Counter(r.get('stratum_id') for r in assigned)
    require(len(assigned)==sum(s['n'] for s in strata) and nh=={hid:s['n'] for hid,s in sb.items()},'Assigned draw must preserve every planned n_h')
    require(set(ab)<=targetset,'Draw contains out-of-frame or exposed unit in remaining estimand')
    for rid,r in ab.items():
        require(set(r)=={'unit_id','stratum_id','department','domain','pi_exact','weight_exact'},'Draw preserves only registered identity and exact sampling weights')
        hid=mb[rid]['stratum_id'];s=sb[hid]
        require(r['stratum_id']==hid and r['department']==fb[rid]['department'] and r['domain']==pb[rid]['domain'],'Draw row membership differs from frozen population')
        require(isinstance(r['pi_exact'],str) and isinstance(r['weight_exact'],str),'Exact rational probability/weight strings required')
        require(Fraction(r['pi_exact'])==Fraction(s['n'],s['N']) and Fraction(r['weight_exact'])==Fraction(s['N'],s['n']),'Old sample weights or altered probabilities rejected')
    require(design.get('target_ids_sha256')==canonical(sorted(target)) and draw.get('assigned_ids_sha256')==canonical(sorted(ab)),'Target or draw ID receipt differs')
    require(draw.get('assigned_order_sha256')==canonical(list(ab)),'Original assigned order receipt differs')
    versions={k:load(descriptor[k]) for k in ('rule_version','LLM_version')}
    for method,v in versions.items():
        require(v.get('status')==('synthetic_fixed_machine_version' if synthetic else 'ROOT_final_machine_version_frozen_before_test_feedback'),'Machine version not final before test feedback')
        require(v.get('manual_binding')==descriptor['common_manual'] and v.get('common_materials_binding')==descriptor['common_materials'],'Machine does not share exact registered manual/material')
        require(v.get('first_answer_selection_fixed_before_feedback') is True,'Output selection not pre-fixed')
        if not synthetic:
            require(v.get('expected_full_frame_binding')==descriptor['full_frame'] and type(v.get('expected_full_record_N')) is int and v['expected_full_record_N']==4481,'Machine version must pre-bind the complete same4481 frame')
            verify(v.get('algorithm_or_model_protocol_binding'))
    year=descriptor.get('year_source_map')
    yearby=None;year_config=None
    if year is not None:
        yrows=rows(year);yearby=unique_rows(yrows,'unit_id');require(list(yearby)==list(fb),'Year map must be complete same4481 frame, not selected800/old200')
        year_config=load(descriptor.get('year_metadata'))
        require(year_config.get('status')==('synthetic_source_year_metadata_fixture' if synthetic else 'ROOT_frozen_complete_source_year_metadata'),'Independent registered source-year metadata required')
        require(year_config.get('source_year_map_binding')==year and year_config.get('frozen_before_labels') is True,'Year metadata not bound to this exact full-frame map')
        require(set(year_config)=={'status','source_year_map_binding','assignment_basis','frozen_before_labels','requested_years','no_source_views'},'Year metadata accepts no outcome or sample-weight fields')
        require(all(set(r)=={'unit_id','policy_year'} and (r['policy_year'] is None or type(r['policy_year']) is int) for r in yrows),'Source year exact integer/null metadata only')
    return {'full_frame_population_N':4481,'full_domain_population_N':dn,'target_population_N':len(target),'target_ids_sha256':canonical(sorted(target)),'strata':strata,'assigned':assigned,'assigned_order':list(ab),'assigned_ids_sha256':draw['assigned_ids_sha256'],'target_domain_population_N':dict(Counter(pb[rid]['domain'] for rid in target)),'estimand':estimand,'design_binding':descriptor['design_contract'],'draw_binding':descriptor['original_draw'],'year_source_map':year,'yearby':yearby,'year_config':year_config}



def validate_stage_attestations(metadata):
    # Pure stage contract validation; this does not approve a scope or a person.
    stage=metadata.get('analysis_stage','combined')
    active={'human_first':('A','B'),'machine_reference':('reference','rule','LLM'),'combined':('A','B','reference','rule','LLM')}.get(stage)
    require(active is not None,'Unregistered analysis stage')
    required=['common_manual','common_materials','design_before_answers']
    if {'A','B'} & set(active):required.append('initial_submissions_before_discussion')
    if 'reference' in active and {'rule','LLM'} & set(active):required.append('reference_before_machine_comparison')
    if {'rule','LLM'} & set(active):required.append('final_rule_and_LLM_before_test_feedback')
    freezes=metadata.get('freeze_attestations',{})
    for flag in required:require(freezes.get(flag) is True,'Actual registered freeze missing for '+stage+': '+flag)
    return {'analysis_stage':stage,'active_methods':list(active),'required_freeze_attestations':required,'ROOT_scope_or_human_admission':False}

def admit(payload):
    selected=registry_entry(payload)
    if selected is None:return None
    descriptor,receipt=selected;meta=payload['metadata'];scope=meta['scope'];synthetic=payload['data_role']=='synthetic'
    checked=validate_registration(descriptor,scope,synthetic)
    require(set(scope)=={'kind','registration_id','population_N','frame_ids_sha256'},'Registered scope accepts no unregistered population/alias fields')
    require(type(scope.get('population_N')) is int and scope['population_N']==checked['target_population_N'] and scope['frame_ids_sha256']==checked['target_ids_sha256'],'Caller population/frame hash differs from complete registered target')
    expected_design={'kind':'stratified_srswor','sampling_unit':'source_unit','strata':checked['strata'],'assigned_ids_sha256':checked['assigned_ids_sha256'],'domain_population_N':checked['target_domain_population_N']}
    if checked['estimand']=='full_4481_audit':expected_design['domain_partition']='remaining_exposed'
    require(meta.get('design')==expected_design,'Input design must exactly equal registered original strata/allocation, not old200/800 or freely supplied N')
    records=payload.get('records');require(isinstance(records,list) and [r.get('unit_id') for r in records]==checked['assigned_order'],'Label ledger must exactly preserve original assigned IDs/order; no nonresponse deletion')
    for r,assigned in zip(records,checked['assigned']):
        require(r.get('stratum_id')==assigned['stratum_id'] and r.get('department')==assigned['department'],'Ledger row reclassified outside original draw')
    year_enabled='year_mapping' in meta or any('policy_year' in r for r in records)
    if year_enabled:
        require(checked['yearby'] is not None,'Year mode requires same registered complete4481 year source map')
        ym=meta.get('year_mapping',{});yc=checked['year_config']
        require(ym.get('sha256')==checked['year_source_map']['sha256'] and ym.get('sealed') is True and ym.get('frozen_before_labels') is True and all(ym.get(k)==yc[k] for k in ('assignment_basis','requested_years','no_source_views')),'Year map/views bound to a different design/source metadata')
        require(all('policy_year' in r and r['policy_year']==checked['yearby'][r['unit_id']]['policy_year'] for r in records),'Year assignment differs from exact registered source map')
    if not synthetic:
        stage=meta.get('analysis_stage','combined');active={'human_first':('A','B'),'machine_reference':('reference','rule','LLM'),'combined':('A','B','reference','rule','LLM')}.get(stage)
        require(active is not None,'Unregistered analysis stage')
        approvals=descriptor.get('_ROOT_admitted_submission_receipts',{})
        identities=meta.get('identities',{})
        require(meta.get('identity_and_source_evidence_reviewed') is True,'Actual identity/source review required before statistics')
        stage_contract=validate_stage_attestations(meta)
        require(stage_contract['active_methods']==list(active),'Stage freeze and active method contract disagree')
        if 'A' in active and 'B' in active:
            require(identities.get('A',{}).get('identity_code')!=identities.get('B',{}).get('identity_code'),'Actual A/B must be distinct people')
        for method in active:
            rb=approvals.get(method);r=load(rb)
            require(r.get('status')=='ROOT_reviewed_actual_method_submission' and r.get('control_or_synthetic') is False,'Actual ROOT receipt required for every active method')
            require(r.get('registration_id')==scope['registration_id'] and r.get('method')==method and r.get('draw_binding')==descriptor['original_draw'],'Original actual submission belongs to another registered draw')
            require(r.get('identity_and_freeze_reviewed') is True,'Actual identity/material/first submission review missing')
            original=verify(r.get('original_bytes_binding'));seal=meta.get('input_seals',{}).get(method,{})
            require(seal.get('sealed') is True and seal.get('sha256')==binding(original)['sha256'] and seal.get('joined_projection_sha256')==r.get('joined_projection_sha256'),'Actual original byte or normalized output binding differs')
            require(r.get('common_manual_binding')==descriptor['common_manual'] and r.get('common_materials_binding')==descriptor['common_materials'],'Actual submission used different common materials')
            if method in ('rule','LLM'):
                require(r.get('whole_campaign_terminal') is True and r.get('version_binding')==descriptor[method+'_version'],'Partial/different machine version forbidden')
                require(r.get('label_based_attempt_selection') is False,'Machine result cannot be selected using validation labels')
                require(type(r.get('whole_record_N')) is int and r['whole_record_N']==4481 and r.get('whole_frame_binding')==descriptor['full_frame'],'Machine terminal receipt must cover complete same4481 including failure/null records')
                require(r.get('complete_first_answer_reception_reviewed') is True,'Complete first machine reception has not been reviewed')
            else:
                require(r.get('machine_answers_visible') is False and r.get('actual_human_execution_reviewed') is True,'Actual human/machine blinding not established')
                require(r.get('auto_agreement_or_AI_substitution') is False,'A/B agreement/AI cannot create a human reference')
                identity=identities.get(method,{})
                require(isinstance(identity.get('identity_code'),str) and identity['identity_code'].strip() and r.get('reviewed_identity_code')==identity['identity_code'],'Human identity must match ROOT-reviewed actual original submission')
                verify(r.get('human_identity_evidence_binding'))
                require(r.get('first_submission_locked') is True,'Original human first submission was not locked')
                if method in ('A','B'):
                    require(identity.get('kind')=='human' and identity.get('verified') is True and identity.get('independent_initial') is True and r.get('independent_initial_before_discussion') is True,'Actual independent human first judgement missing')
                else:
                    require(identity.get('kind')=='human_adjudication' and identity.get('credible') is True and identity.get('blinded_to_machines') is True and r.get('actual_human_adjudication_reviewed') is True,'Reference requires actual credible human adjudication blinded to machines')
        for key,dkey in (('common_manual','common_manual'),('common_materials','common_materials'),('design','design_contract'),('rule_protocol','rule_version'),('LLM_protocol','LLM_version')):
            seal=meta.get('artifact_seals',{}).get(key,{})
            require(seal.get('sealed') is True and seal.get('sha256')==descriptor[dkey]['sha256'],'Registered common artifact seal differs: '+key)
    # No row label is altered; the unchanged core checks label/status projections.
    return {'scope_kind':scope['kind'],'registration_id':scope['registration_id'],'estimand':checked['estimand'],'full_frame_population_N':4481,'full_domain_population_N':checked['full_domain_population_N'],'target_population_N':checked['target_population_N'],'target_ids_sha256':checked['target_ids_sha256'],'draw_binding':checked['draw_binding'],'design_binding':checked['design_binding'],'authority_receipt':receipt,'actual_ROOT_admission':not synthetic,'synthetic_only':synthetic}
