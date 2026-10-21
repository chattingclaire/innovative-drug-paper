"""Independent byte/static reception. No bridge, candidate, protocol or recovery calls."""
import ast, datetime, hashlib, json
from pathlib import Path

BASE=Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
HERE=Path(__file__).resolve().parent
BRIDGE=BASE/'08-audits/source-request-status-bridge-sol'
HISTORY=BASE/'08-audits/v5-historical-S3-ledger-interface-sol'
H=lambda raw:hashlib.sha256(raw).hexdigest()
def bind(path):
    path=Path(path);raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':H(raw)}
def write(name,obj):
    with (HERE/name).open('x',encoding='utf8') as stream:
        json.dump(obj,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
def check_binding(b):
    actual=bind(b['path'])
    if any(actual[k]!=b[k] for k in ('path','bytes','sha256')):raise ValueError('input binding changed '+b['path'])
    return actual

def main():
    bridge_seal=bind(BRIDGE/'output-seal.json')
    if bridge_seal['sha256']!='df32a5eefebff587eaf0a3b1606146db85022c017e4574e466b17c8d92d3c5a5':raise ValueError('bridge seal differs')
    s=json.loads((BRIDGE/'output-seal.json').read_bytes())
    bridge_members=[check_binding(b) for b in s['members']]
    bridge_inputs=[check_binding(b) for b in s['inputs']]
    code=bind(BRIDGE/'status_bridge.py')
    if code['sha256']!='7f3bd52c6ffbd0a376433782b2ee70f276d670bd5fe3c720fbec9142d3be3cf4':raise ValueError('bridge code differs')
    tree=ast.parse((BRIDGE/'status_bridge.py').read_bytes())
    functions=[{'name':n.name,'start_line':n.lineno,'end_line':n.end_lineno} for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))]
    imports=[ast.unparse(n) for n in tree.body if isinstance(n,(ast.Import,ast.ImportFrom))]
    history_seal=bind(HISTORY/'output-seal.json')
    if history_seal['sha256']!='8311a4f6876e1d8ce700551dc9d209d79b18f6201fca0fe18f4bb59561d8d6ee':raise ValueError('history readback seal differs')
    hs=json.loads((HISTORY/'output-seal.json').read_bytes())
    history_members=[]
    for b in hs['members']:
        history_members.append(check_binding({'path':str(HISTORY/b['relative_path']),'bytes':b['bytes'],'sha256':b['sha256']}))
    original_inputs=json.loads((HISTORY/'input-bindings.json').read_bytes())
    unchanged_original=[check_binding(b) for b in original_inputs]
    findings=json.loads((HISTORY/'per-record-findings.json').read_bytes())
    proofs=json.loads((HISTORY/'scope-proof-readback.json').read_bytes())
    selected={}
    for line in (HISTORY/'selected-predictions.jsonl').read_bytes().splitlines():
        value=json.loads(line);selected[value['id']]=value
    sufficiency=[]
    for finding in findings:
        rid=finding['id'];p=selected[rid]
        request_arrays=[p['source_requests'],p['uniform_source_reading_log']['source_requests'],p['live_view_source_audit']['source_requests']]
        saved=bool(all(a==request_arrays[0] for a in request_arrays) and p['uniform_source_audit_state']['driver_call_stage']=='returned' and len(p['candidate_decisions_diagnostic_only'])==5 and finding['readback_errors']==[])
        sufficiency.append({'id':rid,'complete_diagnostic_after_original_evidence_validation':saved,'source_requests_copies_equal':all(a==request_arrays[0] for a in request_arrays),'candidate_decisions_original_sha256':finding['candidate_diagnostic_decisions_sha256'],'raw_source_requests_original_sha256':finding['raw_source_requests_sha256'],'source_log_original_sha256':finding['uniform_source_reading_log_sha256'],'single_saved_semantic_unit_required_to_recompute_judge':False,'single_saved_semantic_unit_exists_in_failed_prediction':False,'semantic_unit_gap_is_recording_policy_not_source_absence':True,'proposed_acceptable_alternative':'exact frozen driver validate-success control flow plus complete raw bundle/diagnostic/source trace/log/literal quotes/finite proof; receiver must independently check bindings and not rebuild semantics','existing_scope_proof_record':next(x for x in proofs if x['id']==rid),'acceptance_or_recovery_approved':False})
    write('received-bindings.json',{'bridge_seal':bridge_seal,'bridge_module':code,'bridge_members':bridge_members,'bridge_upstream_inputs':bridge_inputs,'historical_three_seal':history_seal,'historical_three_members':history_members,'original_static_inputs_still_equal':unchanged_original})
    write('static-code-scope.json',{'functions_or_classes':functions,'imports':imports,'candidate_classifier_modules_imported':False,'code_not_imported_or_executed':True,'known_statuses_literal':['resolved','stopped','unresolved'],'pointer_target_whitelist_in_helper':False,'scope':'read AST, literal frozen code and saved reports only'})
    write('historical-three-data-sufficiency.json',sufficiency)
    write('review-scope.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':'nonhuman AI independent code/contract reception','synthetic_controls_reexecuted':0,'bridge_function_calls':0,'protocol_check_calls':0,'source_adapter_calls':0,'RelationView_calls':0,'judge_calls':0,'full_domain_recovery_calls':0,'new_actual_policy_semantic_read_N':0,'main_LLM_output_reads':0,'actual_human_or_formal_metrics':0,'bridge_seal_members_received':len(bridge_members),'bridge_upstream_bindings_received':len(bridge_inputs),'historical_seal_members_received':len(history_members),'original_static_inputs_received':len(unchanged_original),'historical_data_alternative_supported_N':sum(x['complete_diagnostic_after_original_evidence_validation'] for x in sufficiency),'existing_owner_files_modified':False,'recovery_GO':False})
    print(json.dumps({'bridge_members':len(bridge_members),'bridge_inputs':len(bridge_inputs),'history_members':len(history_members),'history_inputs':len(unchanged_original),'three_data_sufficient_via_original_evidence_control_flow':sum(x['complete_diagnostic_after_original_evidence_validation'] for x in sufficiency),'new_executions':0},ensure_ascii=False))

if __name__=='__main__':main()
