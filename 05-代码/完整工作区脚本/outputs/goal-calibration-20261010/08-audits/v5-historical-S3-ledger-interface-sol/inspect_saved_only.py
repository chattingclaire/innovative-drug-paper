"""Read only three already exposed saved records. No candidate imports or recovery."""
import copy, datetime, hashlib, json, pathlib, unicodedata

BASE = pathlib.Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
HERE = pathlib.Path(__file__).resolve().parent
RUNNER = BASE / '06-coding/rule-full4481-final-v5-sol'
RUN = RUNNER / 'run4481-first'
IDS = ('RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045')

def sha(raw): return hashlib.sha256(raw).hexdigest()
def cj(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
def write(name, value):
    with (HERE/name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
def binding(path):
    raw=path.read_bytes()
    return {'path':str(path), 'bytes':len(raw), 'sha256':sha(raw)}
def norm(text): return ''.join(unicodedata.normalize('NFKC', text).split())

def select_saved(filename):
    path=RUN/filename
    # Take one immutable byte snapshot of the observed append-only prefix. Never
    # parse any other record's policy text, predictions or source consumption.
    raw=path.read_bytes(); selected={}; offset=0; positions=[]
    for line_no,line in enumerate(raw.splitlines(keepends=True),1):
        # The mechanical ledger starts with index, while prediction/log start
        # with id. Select only exact known id fields before JSON parsing.
        rid=next((rid for rid in IDS if ('"id": "'+rid+'"').encode() in line), None)
        if rid:
            if rid in selected: raise ValueError('duplicate target in saved output')
            value=json.loads(line)
            if value.get('id')!=rid: raise ValueError('selected ID changed')
            selected[rid]=value
            positions.append({'id':rid,'line_1based':line_no,'byte_interval_half_open':[offset,offset+len(line)],'raw_line_bytes':len(line),'raw_line_sha256':sha(line)})
        offset+=len(line)
    if set(selected)!=set(IDS):raise ValueError('three saved target records incomplete')
    out=HERE/('selected-'+filename)
    with out.open('xb') as stream:
        for rid in IDS:stream.write(cj(selected[rid])+b'\n')
    return selected, {'path':str(path),'observation_type':'append_only_observed_byte_prefix_not_final_run_seal','observed_prefix_bytes':len(raw),'observed_prefix_sha256':sha(raw),'selected_record_positions':positions,'other_records_not_JSON_parsed':True}

def walk(value, path='$'):
    if isinstance(value,dict):
        yield path,value
        for key,child in value.items(): yield from walk(child,path+'/'+str(key))
    elif isinstance(value,list):
        for i,child in enumerate(value): yield from walk(child,path+'/'+str(i))

def check_quotes(bundle, objects):
    contexts={c['context_id']:c for c in bundle['source_record']['contexts']}
    for leaf in bundle['source_full_text_resources']:
        if leaf.get('kind')!='verbatim_UTF8_snapshot_text':continue
        ref={'sha256':leaf['source_sha256'], 'source_resource_id':leaf.get('source_document_resource_id','SOURCE-'+leaf['source_sha256']), 'locator':leaf['locator']}
        identity={'source_resource_id':leaf['source_resource_id'],'source_ref':ref,'text':leaf['text'],'role':leaf.get('role'),'representation':leaf.get('representation',leaf.get('kind'))}
        cid='CTX-DERIVED-'+sha(cj(identity))[:24]
        contexts[cid]={'text':leaf['text'],'source_ref':ref}
    checked=[];errors=[]
    for label,obj in objects.items():
        for pointer,q in walk(obj,'$/'+label):
            if not {'context_id','start','end','text','source_ref'}<=set(q):continue
            c=contexts.get(q['context_id']); a=q['start']; b=q['end']
            exact=bool(c and type(a) is int and type(b) is int and 0<=a<b<=len(c['text']) and c['text'][a:b]==q['text'] and c['source_ref']==q['source_ref'])
            entry={'pointer':pointer,'context_id':q['context_id'],'start':a,'end':b,'quote_utf8_sha256':sha(q['text'].encode()),'source_sha256':q['source_ref'].get('sha256'),'exact_raw_context_or_literal_leaf_and_ref':exact}
            checked.append(entry)
            if not exact:errors.append(entry)
    return checked,errors

def main():
    p, pb=select_saved('predictions.jsonl'); logs,lb=select_saved('actual-source-consumption.jsonl'); ledger,eb=select_saved('execution-ledger.jsonl')
    snapshots=[pb,lb,eb];inputs=[]
    scope=json.loads((RUNNER/'frozen-scope.json').read_bytes())
    algorithms=json.loads((RUNNER/'algorithm-bindings.json').read_bytes())
    for name in ('rule_driver.py','interface_common.py','frozen-scope.json','algorithm-bindings.json','packet-bindings.json','pre-execution-run-seal.json'):
        inputs.append(binding(RUNNER/name))
    for b in algorithms['modules']:
        actual=binding(pathlib.Path(b['path']))
        if actual['bytes']!=b['bytes'] or actual['sha256']!=b['sha256']:raise ValueError('frozen module binding mismatch')
        inputs.append(actual)
    for key in ('manual','source_reading_protocol_code'):
        b=scope[key];actual=binding(pathlib.Path(b['path']))
        if actual!=b:raise ValueError('frozen material mismatch')
        inputs.append(actual)
    packetplan=json.loads((RUNNER/'packet-bindings.json').read_bytes())
    packets={z.get('source_id',z.get('id')):z for z in packetplan['packets']}
    # Packet manifest has record_id, not source_id, in some sealed producers.
    if not set(IDS)<=set(packets):
        packets={rid:packetplan['packets'][packetplan['ordered_source_ids'].index(rid)] for rid in IDS}
    findings=[];allquotes=[];proofs=[]
    for rid in IDS:
        packetpath=pathlib.Path(packets[rid]['path']);raw=packetpath.read_bytes();packet=json.loads(raw);bundle=packet['source_bundle']
        actual=binding(packetpath)
        if actual['sha256']!=packets[rid]['sha256'] or actual['bytes']!=packets[rid]['bytes']:raise ValueError('native packet changed')
        inputs.append(actual)
        if packet['source_id']!=rid or bundle['source_record']['id']!=rid:raise ValueError('native packet ID mismatch')
        bundle_sha=sha(cj(bundle));log=p[rid]['uniform_source_reading_log'];check=p[rid]['uniform_source_protocol_check'];diag=p[rid]['candidate_decisions_diagnostic_only']
        errs=[]
        if log['actual_full_source_bundle_sha256']!=bundle_sha or ledger[rid]['source_bundle_sha256']!=bundle_sha:errs.append('full bundle SHA differs')
        if p[rid]['labels'] is not None or p[rid]['decisions'] is not None or ledger[rid]['labels'] is not None or not ledger[rid]['technical_failure']:errs.append('first technical failure identity differs')
        if set(diag)!=set(('S','E','Ec','I','F')) or any(d.get('value') not in (0,1,None) for d in diag.values()):errs.append('candidate five-dimensional diagnostic incomplete')
        if logs[rid]['uniform_source_reading_log']!=log or logs[rid]['uniform_source_protocol_check']!=check:errs.append('two saved source logs differ')
        if p[rid]['source_requests']!=log['source_requests']:errs.append('raw request projection differs')
        inventory={z['resource_id']:z for z in log['source_inventory']};reads={z['receipt_id']:z for z in log['read_receipts']};good={}
        receiptchecks=[]
        for r in reads.values():
            target=inventory.get(r['resource_id']);ok=bool(target and r['source_sha256']==target['source_sha256'] and r['view_sha256']==target['available_views'].get(r['view']) and r['record_id']==rid and r['run_id']==log['run_id'] and r['delivery_status']=='complete' and r['read_attestation']=='recorded')
            receiptchecks.append({'receipt_id':r['receipt_id'],'resource_id':r['resource_id'],'view':r['view'],'matched_inventory_and_run_complete':ok})
            if ok:good[r['resource_id'],r['view']]=r['receipt_id']
            else:errs.append('read receipt mismatch '+r['receipt_id'])
        for req in log['requirements']:
            if req['requirement_status']!='resolved' or (req['required_resource_id'],req['required_view']) not in good:errs.append('unsatisfied original read requirement '+req['requirement_id'])
        for i,u in enumerate(log['use_receipts']):
            r=reads.get(u['read_receipt_id']);ok=bool(r and u['use_status']=='used' and r['resource_id']==u['resource_id'] and r['view']==u['view'] and (u['resource_id'],u['view']) in good)
            receiptchecks.append({'use_index':i,'read_receipt_id':u['read_receipt_id'],'matched_used_view_and_read':ok})
            if not ok:errs.append('use receipt mismatch '+str(i))
        for event in p[rid]['source_view_events']:
            target=inventory.get(event['resource_id'])
            if not target or event['source_sha256']!=target['source_sha256'] or event['view_sha256']!=target['available_views'].get(event['view']):errs.append('source view event mismatch')
        qchecks,qerrors=check_quotes(bundle,{'diagnostic':diag,'source_requests':p[rid]['source_requests'],'source_relation_traces':p[rid]['source_relation_traces'],'use_receipts':log['use_receipts']})
        allquotes.append({'id':rid,'quotes_checked':qchecks,'quote_errors':qerrors})
        errs.extend('quote mismatch '+e['pointer'] for e in qerrors)
        se=[t for t in p[rid]['source_relation_traces'] if t['details'].get('relation_subtype')=='SE_primary_literal_operational_standard']
        if len(se)!=1:errs.append('exactly one new finite SE relation not saved')
        for t in se:
            details=t['details'];proof=details['closure_proof'];snap=pathlib.Path(proof['boundary_quotes'][0]['source_ref']['locator']['snapshot_absolute_path']);snapraw=snap.read_bytes();snaptext=snapraw.decode('utf8')
            if binding(snap) not in inputs:inputs.append(binding(snap))
            a,b=proof['actual_next_boundary_snapshot_span'];x,y=proof['current_snapshot_span'];g,h=proof['group_snapshot_span'];contenta,contentb=proof['content_snapshot_span']
            exact=sha(snapraw)==proof['source_sha256'] and proof['actual_next_normative_boundary'] is True and proof['EOF_is_not_closure'] is True and snaptext[x:y]==proof['current_exact_raw_text'] and norm(snaptext[x:y])==norm(bundle['source_record']['text']) and 0<=contenta<contentb<=a<b<=len(snaptext)
            if not exact:errs.append('finite closed proof source or current mismatch')
            proofs.append({'id':rid,'saved_relation_subtype':details['relation_subtype'],'consumer_scope':details['affected_dimensions'],'SE_scope_verified_saved':details['SE_scope_verified'],'version_binding_saved':details['version_binding'],'source_sha256':proof['source_sha256'],'current_snapshot_span':[x,y],'current_exact_raw_text':proof['current_exact_raw_text'],'standard_group_snapshot_span':[g,h],'standard_content_snapshot_span':[contenta,contentb],'next_boundary_span':[a,b],'next_boundary_text':snaptext[a:b],'next_boundary_physical_line_1based':snaptext[:a].count('\n')+1,'literal_primary_snapshot_and_finite_boundary_verified':exact,'content_not_borrowed_from_boundary':True,'raw_closure_proof_sha256':sha(cj(proof))})
        requests=p[rid]['source_requests']
        reason={'producer_field':'dependency_status','producer_value':requests[0].get('dependency_status'),'legacy_status_field_present':'status' in requests[0],'protocol_check_errors':check['errors'],'protocol_dependency_stop_reasons':check['dependency_stop_reasons'],'no_concrete_stopped_material_requests':p[rid]['material_requests']==[],'stage':p[rid]['uniform_source_audit_state'],'runner_error':p[rid]['implementation_errors']}
        findings.append({'id':rid,'classification':'receipt/validator schema mismatch; not an algorithm NULL or missing-source finding','retained_original_technical_failure':True,'original_retained_labels':p[rid]['labels'],'candidate_diagnostic_values_observation_only':{dim:decision['value'] for dim,decision in diag.items()},'candidate_diagnostic_decisions_sha256':sha(cj(diag)),'full_source_bundle_sha256':bundle_sha,'raw_source_requests_sha256':sha(cj(requests)),'uniform_source_reading_log_sha256':sha(cj(log)),'saved_source_relation_traces_sha256':sha(cj(p[rid]['source_relation_traces'])),'schema_mismatch':reason,'original_requirement_N':len(log['requirements']),'complete_read_receipt_N':len(reads),'use_receipt_N':len(log['use_receipts']),'source_identity_resolution_delta':log['source_identity_resolution_delta'],'receipt_checks':receiptchecks,'quote_check_N':len(qchecks),'readback_errors':errs,'mechanical_saved_data_sufficient_for_future_separate_receipt_review':not errs,'acceptance_or_recovery_executed':False})
    write('observed-output-prefix-bindings.json',snapshots)
    write('input-bindings.json',inputs)
    write('per-record-findings.json',findings)
    write('quote-readback.json',allquotes)
    write('scope-proof-readback.json',proofs)
    write('inspection-scope.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':'nonhuman AI read-only interface audit','allowed_already_exposed_actual_ids':list(IDS),'selected_saved_record_N':3,'classifier_calls':0,'source_adapter_calls':0,'RelationView_calls':0,'judge_calls':0,'protocol_check_calls':0,'recovery_or_retention_calls':0,'new_policy_semantic_read_N':0,'main_LLM_output_reads':0,'actual_human_results_created':0,'existing_files_modified':False,'run_not_claimed_finalized':True,'saved_data_sufficient_N':sum(f['mechanical_saved_data_sufficient_for_future_separate_receipt_review'] for f in findings),'readback_error_N':sum(len(f['readback_errors']) for f in findings)})
    print(json.dumps({'selected_N':len(findings),'saved_data_sufficient_N':sum(f['mechanical_saved_data_sufficient_for_future_separate_receipt_review'] for f in findings),'readback_error_N':sum(len(f['readback_errors']) for f in findings),'recovery_executed':False},ensure_ascii=False))

if __name__=='__main__':main()
