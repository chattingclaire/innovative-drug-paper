"""Compare already-executed decisions and receipts; never invoke judge/view."""
import ast,copy,re,types
from pathlib import Path
from merge_common import cj
from scope_contract import require
from status_bridge import canonicalize_request

NEW_DEPENDENCIES={
 'E_explicit_content_scope':('E','E_closed_content_dependency','E_explicit_content_scope_unresolved'),
 'S_finite_standard_scope':('S','S_finite_standard_dependency','S_finite_standard_scope_unresolved'),
 'F_finite_standard_scope':('F','F_finite_standard_dependency','F_finite_standard_scope_unresolved'),
 'F_requested_qualification_scope':('F','F_requested_qualification_dependency','F_requested_qualification_scope_unresolved'),
 'price_arrangement':('Ec',None,'finite_negotiation_definition_unresolved'),
}

def ordered_additions(old,new,what):
    """The old sequence remains intact, including duplicate occurrences."""
    i=0;added=[]
    for x in new:
        if i<len(old) and x==old[i]:i+=1
        else:added.append(x)
    require(i==len(old),'Old '+what+' was removed, reordered, or rewritten')
    return added

def requests_in(decision):
    return decision['needed_material']+decision.get('details',{}).get('unresolved_material_requests',[])

def validate_new_request(request,modules,decisions):
    path=request.get('path');require(path in NEW_DEPENDENCIES,'Unreviewed new necessary source request: '+str(path))
    dim,producer,stop=NEW_DEPENDENCIES[path]
    require(request.get('stop_reason')==stop and request.get('dependency_status')=='stopped','New dependency status/stop differs')
    if producer is not None:
        require(request.get('producer')==producer and request.get('dimensions')==[dim] and request.get('affected_dimensions')==[dim] and request.get('necessary_dependency') is True,'New explicit dependency producer/dimension differs')
    route=modules['dimensions']._material_request_route(request)
    require(route['dimensions']==[dim],'New dependency routed to another dimension')
    require(request in requests_in(decisions[dim]),'New dependency not retained by correct decision')
    require(all(request not in requests_in(decisions[d]) for d in decisions if d!=dim),'New dependency leaked across dimensions')
    return route

def source_delta(old,new,old_log,new_log,modules,decisions):
    changes={}
    for key in ['source_requests','material_requests']:
        require(new_log[key]==new[key],'Prediction/source log request differs')
        added=ordered_additions(old[key],new[key],key)
        for request in added:validate_new_request(request,modules,decisions)
        changes[key+'_added']=added
    added_events=ordered_additions(recorded_events(old_log),recorded_events(new_log),'actual source events')
    changes['actual_source_events_added']=added_events
    # Added events have already been checked against the delivered inventory
    # and rebuilt original protocol receipts; availability alone is never READ.
    return changes

def recorded_events(record):
    if 'actual_text_geometry_events' in record:return record['actual_text_geometry_events']
    if record.get('primary_source_audit_origin',{}).get('source_view_events')=='live_view':
        require(record['source_view_events']==record['live_view_source_audit']['source_view_events'],'Historical live source event snapshot differs')
        return record['source_view_events']
    raise ValueError('No stored actual source events; cannot synthesize history')

def validate_actual_log(driver,protocol,modules,bundle,prediction,log,run_id):
    """Rebuild receipts from stored actual events with the original log code."""
    uniform=log['uniform_source_reading_log'];decisions=prediction['decisions']
    require(log['source_relation_traces']==prediction['source_relation_traces'],'Source relation traces differ from actual prediction')
    require(log['inventory']==modules['source_packet'].source_inventory(bundle),'Original producer inventory changed')
    prep=protocol.prepare(bundle['source_record']['id'],run_id,'rule')
    original=prep['reference_resolution'];resolutions=uniform['reference_resolution']
    require(resolutions[:len(original)]==original,'Original reference resolution prefix changed')
    view=types.SimpleNamespace(text=bundle['source_record']['text'],
      source_view_events=recorded_events(log),source_requests=prediction['source_requests'],
      material_requests=prediction['material_requests'],source_relation_traces=prediction['source_relation_traces'],
      source_scope_review={'status':uniform['necessary_source_scope_review_status'],'source_evidence_note':uniform['necessary_source_scope_review_note']},
      source_reference_resolution=resolutions[len(original):])
    rebuilt,check=driver.actual_reading_log(protocol,bundle,view,run_id)
    require(rebuilt==uniform and check==log['uniform_source_protocol_check'],'Actual original log/protocol replay differs')
    require(not check['errors'],'Actual source protocol failed')
    require(not set(check['dependency_stop_reasons'])&{'required_view_not_read','scope_boundary_unknown','read_delivery_incomplete'},'Required source reading incomplete')
    tree=ast.parse(Path(driver.__file__).read_text())
    guard=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='stops')
    exec(compile(ast.Module(body=[guard],type_ignores=[]),driver.__file__,'exec'),
         {'stops':check['dependency_stop_reasons'],'view':view,'decisions':decisions,'canonicalize_request':canonicalize_request})
    for request in prediction['material_requests']:
        route=modules['dimensions']._material_request_route(request)
        for dim in route['dimensions']:require(request in requests_in(decisions[dim]),'Actual necessary request missing from consumer decision')
        for dim in decisions:
            if dim not in route['dimensions']:require(request not in requests_in(decisions[dim]),'Actual necessary request leaked to an undeclared dimension')
    return check

def conditional_s_basis(old,new,bundle,modules):
    """Only the two independently reviewed S semantic changes are admitted."""
    s=new['decisions']['S'];details=s['details']
    reqs=[q for q in requests_in(s) if q.get('path')=='S_finite_standard_scope']
    if reqs:
        for q in reqs:validate_new_request(q,modules,new['decisions'])
        require(s['value'] is None or s['value']==1,'Necessary unresolved S must be NULL or independently positive')
        if s['value']==1:
            prior=old['decisions']['S'];require(prior['value']==1,'Independent-positive S with missing standard must already have positive evidence')
            clean=copy.deepcopy(s);clean['needed_material']=[q for q in clean['needed_material'] if q not in reqs]
            clean['details']['unresolved_material_requests']=[q for q in clean['details'].get('unresolved_material_requests',[]) if q not in reqs]
            clean['details']['material_request_routes']=[q for q in clean['details'].get('material_request_routes',[]) if q.get('request') not in reqs]
            require(clean==prior,'Missing-standard request cannot mask unrelated S evidence changes')
        return 'finite_standard_S_dependency'
    if s['value']==1 and s['basis_path']=='S_actual_drug_risk_or_safety_content':
        matched=details.get('matched_risk_or_content','')
        for trace in new['relation_traces']:
            td=trace.get('details',{})
            if trace.get('kind')!='finite_standard_scope' or td.get('relation_subtype')!='finite_adjacent_operated_standard':continue
            require(td.get('SE_scope_verified') is True and td.get('full_scope') is True and td.get('not_whole_file_inheritance') is True,'Finite S scope lacks closure')
            proof=td['closure_proof'];require(proof.get('actual_next_normative_boundary') is True and proof.get('EOF_is_not_closure') is True,'Finite S boundary lacks exact next article')
            content=td.get('neutral_members',[])
            if matched and any(matched in modules['evidence'].matching_view(q['text'])[0] and q in s['context_evidence'] for q in content):
                require(trace.get('used_source_views'),'Finite S has no actual source use');return 'finite_standard_S_content'
        text=modules['evidence'].matching_view(bundle['source_record']['text'])[0]
        require(details.get('relation_kind')=='current' and details.get('object_evidence',{}).get('established') is True,'S change outside approved current drug-object scope')
        for clause in re.split('[。；;，,]',text):
            risk=re.search(r'(?:治疗|用药)(?:的)?获益(?:和|与|及|、)风险',clause)
            if risk and risk.group()==matched and re.search('评价|评估|分析|考察|比较|核验|说明|阐述|监测|识别',clause[:risk.start()]):
                return 'current_parallel_treatment_benefit_risk'
    raise ValueError('S complete decision changed outside reviewed finite-standard/current-treatment-risk boundary')
