"""Execute the original log/protocol/stop guard on delivered finite controls.
This bounded source facade is not a population execution or production receipt.
"""
import ast,copy,hashlib,json,sys,types
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
DRIVER=ROOT/'10-closure-20261012/rule-repair-v13/execution-preparation/rule_driver.py'
BRIDGE=DRIVER.with_name('status_bridge.py')
PROTOCOL=ROOT/'01-review/context-projection-sol/full-frame-preflight/source_reading_protocol_v12.py'
def binding(p):
 raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def cj(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def check_actual_route(loaded,view,decisions,bundle):
 assert binding(DRIVER)['sha256']=='979363460d383412a060e4032a3aa010660f12a0aa316fbd6c492713a54085a3'
 assert binding(BRIDGE)['sha256']=='7f3bd52c6ffbd0a376433782b2ee70f276d670bd5fe3c720fbec9142d3be3cf4'
 assert binding(PROTOCOL)['sha256']=='edec7a03cb29b835f106acb55f306ad8fe4767d3964fdf130e2f3f91754ff076'
 bridge={'__name__':'bounded_status_bridge'};exec(compile(BRIDGE.read_bytes(),str(BRIDGE),'exec'),bridge)
 tree=ast.parse(DRIVER.read_text());logfn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='actual_reading_log');leaf_fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='literal_leaf_integrity');guard=next(n for n in ast.walk(tree) if isinstance(n,ast.If) and isinstance(n.test,ast.Name) and n.test.id=='stops')
 env={'copy':copy,'hashlib':hashlib,'cj':cj,'Path':Path,'canonicalize_request':bridge['canonicalize_request']}
 exec(compile(ast.Module(body=[logfn,leaf_fn],type_ignores=[]),str(DRIVER),'exec'),env)
 paths={Path(z['locator']['snapshot_absolute_path']) for z in bundle['source_full_text_resources'] if z.get('kind')=='verbatim_UTF8_snapshot_text'}
 literal_checks=env['literal_leaf_integrity']([bundle],[binding(p) for p in paths])
 facade=types.ModuleType('source_only_interface_v12');rid=bundle['source_record']['id']
 def lookup(record,selector='rule',**kwargs):
  assert record==rid and selector=='rule';return copy.deepcopy(bundle)
 facade.lookup=lookup;facade.source_inventory=loaded['source_packet'].source_inventory;facade.cj=cj
 facade.CANON_SHA=hashlib.sha256(cj(bundle).encode()).hexdigest();facade.MANIFEST_SHA=hashlib.sha256(b'FINITE_EC_SOURCE_DEVELOPMENT_ONLY').hexdigest()
 old=sys.modules.get('source_only_interface_v12');sys.modules['source_only_interface_v12']=facade
 try:
  protocol=types.ModuleType('bounded_original_protocol');protocol.__file__=str(PROTOCOL);exec(compile(PROTOCOL.read_bytes(),str(PROTOCOL),'exec'),protocol.__dict__)
 finally:
  if old is None:sys.modules.pop('source_only_interface_v12',None)
  else:sys.modules['source_only_interface_v12']=old
 protocol.bound_source_identity={'status':'FINITE_DEVELOPMENT_DELIVERED_BUNDLE_NOT_PRODUCTION','bundle_sha256':facade.CANON_SHA,'fixture_only':rid.startswith('TOY-')}
 protocol.producer_source_inventory=facade.source_inventory;protocol.source_identity_resolver=lambda b:(facade.source_inventory(b),[])
 log,checked=env['actual_reading_log'](protocol,bundle,view,'FINITE-EC-SOURCE-CONTROL')
 assert not checked['errors'],checked['errors']
 assert log['original_source_requests']==view.source_requests
 guardcode=compile(ast.Module(body=[guard],type_ignores=[]),str(DRIVER),'exec')
 guardenv={'stops':checked['dependency_stop_reasons'],'view':view,'decisions':decisions,'canonicalize_request':bridge['canonicalize_request']}
 exec(guardcode,guardenv)
 emitted=[r for r in view.material_requests if r.get('stop_reason')=='finite_negotiation_definition_unresolved']
 for r in emitted:
  route=loaded['dimensions']._material_request_route(r);assert route['dimensions']==['Ec']
  assert r in decisions['Ec']['needed_material'] or r in decisions['Ec']['details'].get('unresolved_material_requests',[])
  assert all(r not in decisions[d]['needed_material'] and r not in decisions[d]['details'].get('unresolved_material_requests',[]) for d in ['S','E','I','F'])
  assert any(q.get('path')=='price_arrangement' and q['status']=='stopped' for q in log['source_requests'])
 negative={}
 if emitted:
  absent=copy.deepcopy(decisions)
  for d in absent.values():d['needed_material']=[];d['details']['unresolved_material_requests']=[]
  try:exec(guardcode,{**guardenv,'decisions':absent})
  except ValueError:negative['removed_dependency_rejected']=True
  wrong=copy.deepcopy(emitted[0]);wrong['affected_dimensions']=['E']
  try:loaded['dimensions']._material_request_route(wrong)
  except loaded['dimensions'].MaterialRequestRoutingError:negative['wrong_dimension_rejected']=True
  assert len(negative)==2
 inv={x['resource_id'] for x in log['source_inventory']};reads={x['resource_id'] for x in log['read_receipts']}
 assert reads<=inv and all(x['resource_id'] in reads for x in log['use_receipts'])
 return {'actual_log':log,'protocol_check':checked,'literal_integrity':literal_checks,'actual_driver_stop_guard_passed':True,'Ec_only_request_N':len(emitted),'negative_controls':negative,'driver':binding(DRIVER),'bridge':binding(BRIDGE),'protocol':binding(PROTOCOL),'finite_development_facade_only':True,'production_entry_executed':False}
