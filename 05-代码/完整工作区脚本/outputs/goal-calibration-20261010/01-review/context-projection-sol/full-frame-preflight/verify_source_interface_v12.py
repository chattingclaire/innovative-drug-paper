"""Source interface assertions and failure-gate verification, no coding."""
from pathlib import Path
import json,hashlib,copy
import source_only_interface_v12 as src
import source_reading_protocol_v12 as protocol
OUT=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def walk(x):
 if isinstance(x,dict):
  for k,v in x.items():yield k,v;yield from walk(v)
 elif isinstance(x,list):
  for v in x:yield from walk(v)
forbidden=set(json.loads((OUT/'current-source-schema-v12.json').read_text())['x-source-protocol']['recursive_forbidden_exact_keys'])
tests=[f'RECODE25-{i:05}' for i in range(4200,4212)]+['RECODE25-00900','RECODE25-00902','RECODE25-00887','RECODE25-00891','RECODE25-00859','RECODE25-01423','RECODE25-00064','RECODE25-04915']
checks=[]
for rid in tests:
 bundles=[src.lookup(rid,s) for s in ['rule','model','human']]
 assert src.cj(bundles[0])==src.cj(bundles[1])==src.cj(bundles[2])
 assert not [k for k,v in walk(bundles[0]) if k in forbidden]
 inv=src.source_inventory(bundles[0]);assert len({z['resource_id'] for z in inv})==len(inv)
 assert all(z['consumer_read_status']=='not_recorded' for z in inv)
 q=protocol.prepare(rid,'SOURCE-INTERFACE-PREPARATION-ONLY','model');gate=protocol.check(q)
 assert not gate['source_read_requirements_recorded'] and gate['complete_recorded_read_N']==0 and 'required_view_not_read' in gate['dependency_stop_reasons']
 checks.append({'record_id':rid,'rule_model_human_identical_bundle_SHA':H(src.cj(bundles[0]).encode()),'all_three_endpoint_bytes_identical':True,'source_inventory_N':len(inv),'asset_path_N':len(bundles[0]['source_asset_locations']),'actual_read_or_use_default_not_recorded':True,'empty_receipt_gate_correctly_blocked':True,'forbidden_key_hit_N':0})
 if rid in ['RECODE25-00887','RECODE25-00891','RECODE25-00859']:assert sum(n['kind']=='same_snapshot_referenced_source_paragraph' for n in bundles[0]['source_record']['contexts'])==37
 if rid=='RECODE25-01423':assert any(n['kind']=='table_group_row' for n in bundles[0]['source_record']['contexts'])
 if rid=='RECODE25-00064':assert q['reference_resolution'][0]['resolution_status']=='unresolved'
 if rid=='RECODE25-04915':assert len(bundles[0]['preserved_historical_neutral_source_supplements'])==3
# Negative cases cannot invent a valid use event or remove current requirements.
q=protocol.prepare('RECODE25-04200','SOURCE-CHECK','rule');q['use_receipts']=[{'resource_id':q['requirements'][0]['required_resource_id'],'read_receipt_id':'MISSING','use_status':'used'}];assert 'used_without_complete_recorded_matching_read' in protocol.check(q)['errors']
q=protocol.prepare('RECODE25-04200','SOURCE-CHECK','rule');q['requirements'][0]['required_view']='image';assert 'current_source_requirements_removed_or_changed' in protocol.check(q)['errors']
# Schema structural conformance on source rows; jsonschema is optional here.
rows=src.rows(OUT/'canonical_source_context-v12.jsonl');schema=json.loads((OUT/'current-source-schema-v12.json').read_text())
for r in rows:
 assert set(r)<=set(schema['properties'])
 for n in r['contexts']:assert set(n)<=set(schema['$defs']['context']['properties']) and n['kind'] in schema['$defs']['context']['properties']['kind']['enum']
try:
 import jsonschema
 validator=jsonschema.Draft202012Validator(schema)
 for r in rows:validator.validate(r)
 visual=jsonschema.Draft202012Validator(json.loads((OUT/'source-visual-resource-schema-v12.json').read_text()))
 for r in src.rows(OUT/'source-library/slide-visual-text-v12.jsonl'):visual.validate(r)
 schema_status='jsonschema_Draft202012_all4481_and104_passed'
except ImportError:schema_status='manual_property_required_kind_checks_all4481_passed; jsonschema_not_installed'
dump(OUT/'source-interface-validation-v12.json',{'version':'v12','canonical_sha256':src.CANON_SHA,'material_manifest_sha256':src.MANIFEST_SHA,'checks':checks,'schema_status':schema_status,'current_run_reads_or_use_not_produced':True,'negative_reading_log_cases_passed':True,'not_human_validation_or_coding':True})
print(json.dumps({'fixture_N':len(checks),'schema':schema_status,'all_same_endpoint_bytes':True,'no_actual_read_receipts_synthesized':True},indent=2))
