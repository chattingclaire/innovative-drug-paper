import sys,pathlib,json,hashlib,uuid
sys.dont_write_bytecode=True
sys.path.insert(0,'/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/protocol-necessary-read-v4')
import necessary_read_gate as gate
import native_records
import packet_builder as pb
from jsonschema import Draft202012Validator
p=pathlib.Path(__file__).parent
assert p.name==__import__('os').environ.get('CODEX_THREAD_ID')
def save(name,v):
 with (p/name).open('xb') as f:f.write(pb.canonical(v)+b'\n')
def file_info(path):
 raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
rows=json.loads((p/'packet-identities.json').read_bytes());whole=json.loads((p/'whole-output.json').read_bytes())
inputs=json.loads((p/'input-identities.json').read_bytes())
output_schema=json.loads(pathlib.Path(next(x['path'] for x in inputs if x['key']=='output-item.schema.json')).read_bytes())
quote_schema=json.loads(pathlib.Path(next(x['path'] for x in inputs if x['key']=='source-quote.schema.json')).read_bytes())
psid=json.loads((p/'packet-schema-identity.json').read_bytes());packet_schema=json.loads(pathlib.Path(psid['path']).read_bytes())
packet_checks=[]
for row in rows:
 packet=pb.parse(pathlib.Path(row['packet_file']['path']).read_bytes())
 assert pb.file_sha(row['packet_file']['path'])==row['packet_file']['sha256']
 gate.packet_identity(packet)
 errors=list(Draft202012Validator(packet_schema).iter_errors(packet))
 packet_checks.append({'source_id':row['source_id'],'file_sha256_verified':True,'canonical_bundle_sha256_verified':True,'ten_roots_and_optional_extension_preserved':True,'packet_schema_valid':not errors,'errors':[e.message for e in errors]})
checks=[];quote_checks=[]
for item,row in zip(whole['items'],rows):
 packet=pb.parse(pathlib.Path(row['packet_file']['path']).read_bytes());record=packet['source_bundle']['source_record']
 original=json.loads((p/'first-output'/(row['source_id']+'.json')).read_bytes())
 assert item==original
 errors=list(Draft202012Validator(output_schema).iter_errors(item))
 spans=[]
 for dim,e in item['evidence'].items():
  assert e['current_quote']==record['text'] and e['current_span']=={'start':0,'end':len(record['text'])}
  for c in e['contexts_used']:
   context=next(c0 for c0 in record['contexts'] if c0['context_id']==c['context_id'])
   value=context[c['field_path']];span=c['span'];assert value[span['start']:span['end']]==c['quote']
  spans.append({'dimension':dim,'current_complete_continuous_span':True,'original_CTX_continuous_spans':True})
 checks.append({'source_id':row['source_id'],'first_output_equals_whole_item':True,'output_schema_valid':not errors,'errors':[{'path':list(e.path),'message':e.message} for e in errors],'span_checks':spans})
 for qfile in sorted((p/'source-quotes').glob(row['source_id']+'*.json')):
  quote=pb.parse(qfile.read_bytes());pb.schema_check(quote,quote_schema);pb.verify_source_quote(packet,quote)
  quote_checks.append({'path':str(qfile),'schema_valid':True,'original_bundle_pointer_and_continuous_Unicode_span_valid':True})
save('format-check.json',{'state':'format_failed','expected_batch_count':len(rows),'saved_candidate_count':len(whole['items']),'complete_ordered_batch':len(whole['items'])==len(rows),'whole_is_exact_saved_first_candidate_sequence':True,'packet_checks':packet_checks,'item_checks':checks,'source_quote_checks':quote_checks,'schema_modified':False,'technical_representation_failure_file':str(p/'technical-representation-failure.json'),'validation_run_count':1})
results=[];exceptions=[]
for i,row in enumerate(rows):
 packet=pb.parse(pathlib.Path(row['packet_file']['path']).read_bytes());scope=pb.parse((p/'scopes'/(row['source_id']+'.json')).read_bytes())
 projection=gate.dependency_output_projection(whole['items'][i]) if i<len(whole['items']) else None
 try:results.append(gate.check_scope(packet,scope,projection))
 except Exception as e:exceptions.append({'source_id':row['source_id'],'exception_type':type(e).__name__,'message':str(e),'source_processed':i<len(whole['items'])})
save('scope-check.json',results)
save('scope-check-exceptions.json',exceptions)
expected=[{'source_id':r['source_id'],'path':r['packet_file']['path'],'sha256':r['packet_file']['sha256'],'source_bundle_sha256':r['source_bundle_sha256']} for r in rows]
receipt={'candidate_file':str(p/'whole-output.json'),'candidate_sha256':pb.file_sha(p/'whole-output.json'),'read_log_file':str(p/'scope-manifest.json'),'read_log_sha256':pb.file_sha(p/'scope-manifest.json'),'thread_id':p.name,'scope_run_id':p.name,'scope_check_file':str(p/'scope-check.json'),'scope_check_sha256':pb.file_sha(p/'scope-check.json'),'required_read_complete':False}
try:
 native_records.check_saved_scopes(receipt,expected)
 native={'state':'passed'}
except Exception as e:native={'state':'failed','exception_type':type(e).__name__,'message':str(e)}
save('native-records-check.json',{'receipt':receipt,'externally_frozen_packet_file_bindings':expected,'result':native})
m=json.loads((p/'packet-schema-000000-emission.json').read_bytes())
save('packet-schema-000000-delivery.json',{'local_delivery_event_id':str(uuid.uuid4()),'tool_name':'functions.exec / exec_command','event_id':None,'exec_command_chunk_id':'d56d72','emission_file':str(p/'packet-schema-000000-emission.json'),'matching_BEGIN_END':True,'actual_visible_body_UTF8_bytes':m['chunk_UTF8_bytes'],'start_byte':0,'end_byte':m['end_byte'],'source_file_sha256':m['input_file_byte_sha256'],'view_sha256':m['view_sha256'],'delivery_status':'complete','read_attestation':'recorded','reader':p.name,'truncated':False,'image_pixels_read':False,'wrapper_max_output_tokens':12000,'exec_command_max_output_tokens':12000})
print(json.dumps({'packet_schema_valid_count':sum(x['packet_schema_valid'] for x in packet_checks),'saved_candidate_count':len(whole['items']),'output_schema_valid':all(x['output_schema_valid'] for x in checks),'public_quote_checks_passed':len(quote_checks),'scope_results':results,'scope_exception_count':len(exceptions),'native_records_check':native},ensure_ascii=False))
