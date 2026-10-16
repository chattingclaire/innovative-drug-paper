from pathlib import Path
import json,hashlib,datetime,shutil,difflib,ast
ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/goal-calibration-20261010/06-coding'
OLD=BASE/'full4481-rule-production-adapter-sol'
CAND=BASE/'rule-five-dimension-joint-root/versions/joint-v5-primary-standard-bridge-sol'
DEST=BASE/'rule-full4481-final-v5-sol'
DEST.mkdir(exist_ok=False)
def binding(p):
 p=p.resolve();r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def write(p,x): p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def cj(x): return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
a=json.loads((CAND/'algorithm-bindings.json').read_text())
expected={'algorithm-bindings.json':'5f9d780b4a72779f69e91082881109f65aa8adc6395ebf94b061bd207e0d14bf','pre-execution-seal.json':'4f8ae9d0a3eb116dd3cd6b44bd8355683b08a54921ee1a6739aff0b609dc3cae','delivery-seal.json':'029a125a217ecd61d745da1ea4b9a88614a6d4bc6a3f6fe759eb431d323fc9ad'}
for n,sha in expected.items(): assert binding(CAND/n)['sha256']==sha
modules=[]
for item in a['five_modules']:
 assert binding(Path(item['path']))==item
 modules.append(dict(item,module=Path(item['path']).stem))
write(DEST/'algorithm-bindings.json',{'version':'final-v5-full4481-execution-binding-1','algorithm_version':'joint-v5-primary-standard-bridge-sol','modules':modules,'final_candidate_algorithm':binding(CAND/'algorithm-bindings.json'),'final_candidate_pre_execution_seal':binding(CAND/'pre-execution-seal.json'),'final_candidate_delivery_seal':binding(CAND/'delivery-seal.json'),'module_bytes_not_copied_or_edited':True})
shutil.copyfile(OLD/'interface_common.py',DEST/'interface_common.py')
s=json.loads((BASE/'rule-full4481-v2-root/frozen-scope.json').read_text())
order=s['approved_record_ids'];assert len(order)==len(set(order))==4481
frames=[json.loads(line) for line in Path(s['source_packet']['path']).read_bytes().splitlines()]
assert [f['source_record']['id'] for f in frames]==order
packet_bindings=[]
for rid,frame in zip(order,frames):
 p=BASE/'full4481-common-v15-production-preparation-sol/packets'/f'{rid}.json'
 raw=p.read_bytes();packet=json.loads(raw)
 assert packet['packet_version']=='native-full-source-3' and packet['source_id']==rid and packet['source_bundle']['source_record']['id']==rid
 can=cj(packet['source_bundle']).encode();assert hashlib.sha256(can).hexdigest()==packet['source_bundle_sha256']
 assert cj(packet['source_bundle'])==cj(frame)
 packet_bindings.append(dict(binding(p),source_id=rid,output_id=packet['output_id'],source_bundle_sha256=packet['source_bundle_sha256']))
write(DEST/'packet-bindings.json',{'packet_N':4481,'ordered_source_ids':order,'packets':packet_bindings,'original_packets_match_frozen_common_JSONL_all':True,'semantic_source_read_or_classification_in_preparation':False})
r=json.loads((BASE/'rule-full4481-v2-root/rule-production-release.json').read_text())
r.update(authorization_id='ROOT-final-sealed-v5-original-common4481-once-20261011',output_directory=str(DEST/'run4481-first'),algorithm_version='joint-v5-primary-standard-bridge-sol',actual_cohort_inference_runs_authorized=1,new_material_adopted=False,neutral_projection_GO=False,first_final_v5_full_domain_run=True,final_algorithm= binding(DEST/'algorithm-bindings.json'),parent_explicit_authorization='ROOT task: final sealed v5 full4481 once on original common frozen packets; original baseline retained; no formal validity claim')
r.pop('technical_restart_from',None);r.pop('technical_restart_reason',None)
write(DEST/'rule-production-release.json',r)
s.update(authorization_id=r['authorization_id'],driver_version='final-v5-full4481-original-common-driver-1',output_directory=str(DEST/'run4481-first'),release=binding(DEST/'rule-production-release.json'),algorithm_bindings=binding(DEST/'algorithm-bindings.json'),original_scope=binding(BASE/'rule-full4481-v2-root/frozen-scope.json'),packet_bindings=binding(DEST/'packet-bindings.json'),algorithm_origin='AI semantic repair candidate joint-v5; full-domain first execution on unchanged original common input; disclosed development',final_candidate_algorithm=binding(CAND/'algorithm-bindings.json'),final_candidate_pre_execution_seal=binding(CAND/'pre-execution-seal.json'),final_candidate_delivery_seal=binding(CAND/'delivery-seal.json'),new_material_adopted=False,neutral_projection_GO=False)
s['material_bindings'] += [s[k] for k in ('release','packet_bindings','original_scope','final_candidate_algorithm','final_candidate_pre_execution_seal','final_candidate_delivery_seal')] + [ {k:v for k,v in x.items() if k in ('path','sha256','bytes')} for x in packet_bindings]
write(DEST/'frozen-scope.json',s)
old=(OLD/'rule_driver.py').read_text();new=old
new=new.replace('Single full4481 production_provisional rule execution adapter; unchanged disclosed-calibration algorithm.','Final sealed v5 full4481 original common source-only execution; one first domain pass; persistent per-record outputs.')
new=new.replace("VERSION='full4481-production-provisional-rule-driver-1'","VERSION='final-v5-full4481-original-common-driver-1'")
new=new.replace("'manual-candidate-binding.json'","'packet-bindings.json'")
new=new.replace("'semantic_change':'none; same v4 disclosed-calibration semantic modules; mechanical production scope/binding/status adaptation only'","'semantic_change':'final sealed joint-v5 semantic repair; original common packets/manual/prompt/protocol unchanged'")
new=new.replace("'fixed_algorithm_version':'rule-v19-human4-general-repair-development-candidate-4'","'fixed_algorithm_version':'joint-v5-primary-standard-bridge-sol'")
new=new.replace("'algorithm_origin':'AI_development_disclosed_calibration; unchanged v4 candidate bytes'","'algorithm_origin':scope['algorithm_origin'],'final_candidate_algorithm':scope['final_candidate_algorithm'],'final_candidate_pre_execution_seal':scope['final_candidate_pre_execution_seal'],'final_candidate_delivery_seal':scope['final_candidate_delivery_seal'],'source_material_candidate_adopted':False,'neutral_projection_GO':False")
oldblock="""        bundle,metadata=unpack_packet(parse_json(line))
        metadata.update(input_line_1based=line_no,input_line_sha256=hashlib.sha256(line).hexdigest(),
                        input_start_utf8_byte=cursor,input_end_utf8_byte_exclusive=cursor+len(line))"""
newblock="""        frozen_bundle,metadata=unpack_packet(parse_json(line))
        packet_entry=packet_plan['packets'][line_no-1]
        packet_raw=verify_binding(packet_entry)
        packet=parse_json(packet_raw)
        if set(packet)!={'output_id','packet_version','source_bundle','source_bundle_sha256','source_id','verified_asset_files'} or packet['packet_version']!='native-full-source-3':
            raise ValueError('original native packet shape/version changed')
        bundle=packet['source_bundle']
        if packet['source_id']!=packet_entry['source_id'] or packet['source_bundle_sha256']!=packet_entry['source_bundle_sha256'] or cj(bundle)!=cj(frozen_bundle):
            raise ValueError('original packet differs from frozen same-order common bundle')
        if hashlib.sha256(cj(bundle).encode()).hexdigest()!=packet['source_bundle_sha256']:
            raise ValueError('original packet canonical SHA differs')
        metadata.update(input_line_1based=line_no,input_line_sha256=hashlib.sha256(line).hexdigest(),
                        input_start_utf8_byte=cursor,input_end_utf8_byte_exclusive=cursor+len(line),
                        actual_input_kind='original_frozen_native_packet',actual_packet_binding=packet_entry,
                        original_packet_output_id=packet['output_id'],same_common_JSONL_identity_verified=True)"""
assert oldblock in new;new=new.replace(oldblock,newblock)
new=new.replace("    cursor=0\n", "    packet_plan=parse_json(verify_binding(scope['packet_bindings']))\n    if packet_plan['ordered_source_ids']!=scope['approved_record_ids'] or packet_plan['packet_N']!=4481:raise ValueError('packet manifest order differs')\n    cursor=0\n")
new=new.replace("    RUNTIME_STAGE='inference'\n    for bundle in delivered:","""    streams={name:(out/name).open('x',encoding='utf-8') for name in ('predictions.jsonl','effective-semantic-units.jsonl','actual-source-consumption.jsonl','execution-ledger.jsonl')}
    RUNTIME_STAGE='inference'
    for bundle in delivered:""")
new=new.replace("        predictions.append(prediction)\n    write_jsonl(out/'predictions.jsonl',predictions);write_jsonl(out/'effective-semantic-units.jsonl',units);write_jsonl(out/'actual-source-consumption.jsonl',consumption_logs)","""        predictions.append(prediction)
        streams['predictions.jsonl'].write(json.dumps(prediction,ensure_ascii=False,allow_nan=False)+'\\n')
        streams['actual-source-consumption.jsonl'].write(json.dumps(consumption_logs[-1],ensure_ascii=False,allow_nan=False)+'\\n')
        if units and units[-1]['id']==row['id']:
            streams['effective-semantic-units.jsonl'].write(json.dumps(units[-1],ensure_ascii=False,allow_nan=False)+'\\n')
        ledger={'index_1based':len(predictions),'id':row['id'],'at_utc':now(),'stage':'record_completed','technical_failure':bool(prediction['implementation_errors']),'labels':prediction.get('labels'),'source_bundle_sha256':hashlib.sha256(cj(bundle).encode()).hexdigest(),'one_adapter_view_judge_attempt_only':True,'no_null_filled_zero':True}
        streams['execution-ledger.jsonl'].write(json.dumps(ledger,ensure_ascii=False,allow_nan=False)+'\\n')
        for stream in streams.values():stream.flush()
        units.clear();consumption_logs.clear()
        if len(predictions)%100==0:
            print(json.dumps({'stage':'inference','completed_record_N':len(predictions),'technical_failure_record_N':len(errors),'at_utc':now()},ensure_ascii=False),flush=True)
    for stream in streams.values():stream.close()""")
assert new!=old;ast.parse(new)
(DEST/'rule_driver.py').write_text(new)
(DEST/'rule-driver-vs-baseline.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile=str(OLD/'rule_driver.py'),tofile=str(DEST/'rule_driver.py'))))
write(DEST/'entry-static-check.json',{'syntax_valid':True,'candidate_modules_not_imported_or_executed':True,'all4481_original_packet_bindings_verified':True,'exact_original_order':True,'packet_JSONL_canonical_identity_matches_N':4481,'candidate_final_seals_verified':{n:binding(CAND/n) for n in expected},'runner_changes_only': ['final v5 algorithm path/version/final seals binding','original native packet shape/canonical verification','per-record immediate persistent predictions/evidence/source consumption/ledger','periodic count progress'],'freeze_no_human_or_formal_validity_claim':True,'neutral_projection_GO':False})
print(json.dumps({'prepared':str(DEST),'scope':binding(DEST/'frozen-scope.json'),'driver':binding(DEST/'rule_driver.py'),'packets_verified_N':4481,'semantic_module_imports':0},ensure_ascii=False))
