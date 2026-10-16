import importlib.util, json, sys, re
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
for n in ('evidence','source_packet','source_receipts','relations','dimensions'):
 s=importlib.util.spec_from_file_location(n,P/(n+'.py'));m=importlib.util.module_from_spec(s);sys.modules[n]=m;s.loader.exec_module(m)
packets=P.parents[2]/'full4481-common-v15-production-preparation-sol/packets'
for sid in sys.argv[1:]:
 raw=json.loads((packets/('RECODE25-'+sid+'.json')).read_text());u=sys.modules['source_packet'].semantic_unit(raw['source_bundle'])
 v=sys.modules['relations'].RelationView(u);ds=sys.modules['dimensions'].judge(v)
 print('\nSOURCE',sid,'current=',u['text'])
 print('labels',{d:x['value'] for d,x in ds.items()},'requests',v.material_requests)
 print('contexts',json.dumps([{'id':c['context_id'],'kind':c['kind'],'text':c.get('text','')[:240],'structure':c.get('structure',{})} for c in u['contexts'] if c['kind'] not in ('source_textleaf','source_resource_text')],ensure_ascii=False))
 print('relations',json.dumps([{'kind':r['kind'],'subtype':r['details'].get('relation_subtype'),'SE_scope_verified':r['details'].get('SE_scope_verified'),'affected_dimensions':r['details'].get('affected_dimensions'),'reason':r['details']['relation_reason'],'quotes':[{k:q[k] for k in ('context_id','text','usage')} for q in r['context_evidence'][:6]]} for r in v.traces()],ensure_ascii=False))
 print('units',json.dumps([{'kind':x.kind,'text':x.text[:500],'inherited':x.inherited[:500],'subtype':x.details.get('relation_subtype'),'SE_scope_verified':x.details.get('SE_scope_verified')} for x in sys.modules['dimensions']._units(v) if x.kind in ('parent_predicate','substantive_list','cited_standard')],ensure_ascii=False))
