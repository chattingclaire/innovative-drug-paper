"""Freeze only three existing raw source-log rows and a mechanical check runner."""
from pathlib import Path
import hashlib
import json
import shutil

D=Path(__file__).resolve().parent;R=D.parents[1]
AUDIT=R/'08-audits/v5-historical-S3-ledger-interface-sol'
BRIDGE=R/'08-audits/source-request-status-bridge-sol'
DRIVER=R/'06-coding/rule-full4481-final-v5-sol'
IDS=['RECODE25-00036','RECODE25-00038','RECODE25-00045']

def bind(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def load(p):return json.loads(Path(p).read_bytes())
def cj(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def write(name,v):
    with (D/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

assert bind(AUDIT/'output-seal.json')['sha256']=='8311a4f6876e1d8ce700551dc9d209d79b18f6201fca0fe18f4bb59561d8d6ee'
assert bind(BRIDGE/'output-seal.json')['sha256']=='df32a5eefebff587eaf0a3b1606146db85022c017e4574e466b17c8d92d3c5a5'
inputs=[bind(AUDIT/'output-seal.json'),bind(BRIDGE/'output-seal.json')]
for m in load(AUDIT/'output-seal.json')['members']:
    p=AUDIT/m['relative_path'];assert bind(p)['sha256']==m['sha256'] and p.stat().st_size==m['bytes'];inputs.append(bind(p))
for m in load(BRIDGE/'output-seal.json')['members']:
    assert bind(m['path'])==m;inputs.append(m)
scope=load(DRIVER/'frozen-scope.json');inputs.append(bind(DRIVER/'frozen-scope.json'))
known_inputs=load(AUDIT/'input-bindings.json')
for m in known_inputs:assert bind(m['path'])==m
inputs+=known_inputs
protocol=Path(scope['source_reading_protocol_code']['path']);assert bind(protocol)==scope['source_reading_protocol_code']
protocol_json=protocol.parent/'source-reading-protocol-v12.json'
assert bind(protocol_json) in scope['material_bindings'];inputs.append(bind(protocol_json))
original_dir=D/'original-three-row-bytes';original_dir.mkdir(exist_ok=True)
source_dir=D/'raw-source-packets';source_dir.mkdir(exist_ok=True)
snapshot=D/'code-snapshot';snapshot.mkdir(exist_ok=True)
for name in ['source_packet.py','source_receipts.py']:
    m=next(m for m in known_inputs if Path(m['path']).name==name)
    shutil.copyfile(m['path'],snapshot/name)
for p in [BRIDGE/'status_bridge.py',protocol,DRIVER/'rule_driver.py']:
    shutil.copyfile(p,snapshot/p.name)
selected=[json.loads(l) for l in (AUDIT/'selected-actual-source-consumption.jsonl').read_bytes().splitlines()]
assert [r['id'] for r in selected]==IDS
prefix=next(v for v in load(AUDIT/'observed-output-prefix-bindings.json') if Path(v['path']).name=='actual-source-consumption.jsonl')
prefix_digest=hashlib.sha256();remaining=prefix['observed_prefix_bytes']
with Path(prefix['path']).open('rb') as f:
    while remaining:
        b=f.read(min(1024*1024,remaining));assert b;prefix_digest.update(b);remaining-=len(b)
assert prefix_digest.hexdigest()==prefix['observed_prefix_sha256']
cases=[];line_bindings=[]
for rid,selected_row in zip(IDS,selected):
    pos=next(v for v in prefix['selected_record_positions'] if v['id']==rid)
    a,b=pos['byte_interval_half_open']
    with Path(prefix['path']).open('rb') as f:f.seek(a);raw=f.read(b-a)
    assert len(raw)==pos['raw_line_bytes'] and hashlib.sha256(raw).hexdigest()==pos['raw_line_sha256']
    assert json.loads(raw)==selected_row and selected_row['id']==rid
    rawpath=original_dir/(rid+'.json');rawpath.write_bytes(raw)
    log=selected_row['uniform_source_reading_log']
    assert log['record_id']==rid and log['reader_selector']=='rule'
    assert log['protocol_sha256']==bind(protocol_json)['sha256']
    # retained_error_source_requests is intentionally empty in the original exception capture;
    # the live view and returned source log are the complete available request copies.
    assert log['source_requests']==selected_row['source_requests']==selected_row['live_view_source_audit']['source_requests']
    assert selected_row['retained_error_source_requests']==[]
    assert len(log['source_requests'])==1 and log['source_requests'][0]['dependency_status']=='resolved' and 'status' not in log['source_requests'][0]
    assert selected_row['material_requests']==selected_row['retained_error_material_requests']==[]
    packet_binding=next(m for m in known_inputs if Path(m['path']).name==rid+'.json')
    shutil.copyfile(packet_binding['path'],source_dir/(rid+'.json'))
    packet=load(packet_binding['path']);assert packet['source_id']==rid
    bundle_sha=hashlib.sha256(cj(packet['source_bundle']).encode()).hexdigest()
    assert bundle_sha==packet['source_bundle_sha256']==log['actual_full_source_bundle_sha256']
    cases.append({'record_id':rid,'raw_saved_row_copy':bind(rawpath),'original_append_only_line_binding':pos,'raw_source_packet_copy':bind(source_dir/(rid+'.json')),'original_packet_binding':packet_binding,'source_bundle_sha256':bundle_sha,'source_requests_pointer_whitelist':['/uniform_source_reading_log/source_requests'],'expected_original_check':{'errors':[],'dependency_stop_reasons':['missing_required_source']},'expected_alias_check':{'errors':[],'dependency_stop_reasons':[]},'expected_original_driver_required_stop_N':1,'expected_alias_driver_required_stop_N':0,'check_calls_per_log_version':1,'not_recovery_or_retained_labels':True})
    line_bindings.append({'record_id':rid,'observed_live_file':prefix['path'],'observed_prefix_bytes':prefix['observed_prefix_bytes'],'observed_prefix_sha256':prefix['observed_prefix_sha256'],'original_line':pos,'selected_canonical_audit_copy_equals_raw_parsed_record':True,'original_line_bytes_copy':bind(rawpath)})
write('pointer-whitelist-and-fixed-expectations.json',cases)
write('original-three-prefix-and-line-readback.json',{'source_log_prefix_only':prefix,'target_lines_verified':line_bindings,'other_records_JSON_parsed_N':0,'not_full_run_final_seal':True})
unique={m['path']:m for m in inputs}
write('input-bindings.json',{'inputs':list(unique.values()),'scope_identity_reused_without_new_scope':{'canonical_sha256':scope['complete_bundles_canonical_sha256'],'manifest_sha256':scope['source_manifest_sha256'],'v12_source_base':scope['v12_source_base']},'facade_implementation':'exact finite_protocol function AST from frozen driver, unchanged body; lookup limited to three bound raw bundles','no_old_log_reconstruction':True,'saved_unit_absent':'Independent source audit documents frozen evidence.validate_decisions before original diagnostic capture; this integration does not reconstruct unit or re-run validation.'})
members=[bind(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='preparation-seal.json']
write('preparation-seal.json',{'status':'fixed_three_saved_logs_source_only_mechanical_check_6calls_before_execution','members':members,'inputs':list(unique.values()),'self_excluded':True,'allowed_record_ids':IDS,'allowed_request_pointer':'/uniform_source_reading_log/source_requests','expected_check_calls':6,'semantic_unit_RelationView_judge_actual_reading_log_calls':0,'recovery_or_label_reception_authorized':False})
print(json.dumps({'cases_N':3,'planned_protocol_check_calls_N':6,'preparation_seal':bind(D/'preparation-seal.json')},ensure_ascii=False))
