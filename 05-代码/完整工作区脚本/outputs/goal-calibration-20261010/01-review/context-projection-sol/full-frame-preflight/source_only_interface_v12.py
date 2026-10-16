"""Same neutral source bundle for rule/model/human. No consumer read/use inference."""
from pathlib import Path
import json,hashlib,copy,argparse
OUT=Path(__file__).resolve().parent
CANON_SHA='c417474ecbd801f1ea0f784f96dad23bf88b7ac00b12780e3ce67c3cbb8f2764'
MANIFEST_SHA='0fa14322edbd614496b014be77144701d052ebde6d41383b788b9e6712b63797'
def sf(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def h(x):return hashlib.sha256(x.encode()).hexdigest()
def rows(p):return list(map(json.loads,Path(p).read_text().splitlines()))
def checked(p,expected):
 if sf(p)!=expected:raise ValueError('source hash mismatch: '+str(p))
def load_manifest():
 p=OUT/'source-material-manifest-v12.json';checked(p,MANIFEST_SHA);return json.loads(p.read_text())
def lookup(record_id,selector='model',bundle=True):
 if selector not in ['rule','model','human','unit']:raise ValueError('unknown source endpoint')
 m=load_manifest();expected={x['path']:x['sha256'] for x in m['files']}
 def load(name,jsonl=False):
  p=OUT/name;checked(p,expected[str(p)]);return rows(p) if jsonl else json.loads(p.read_text())
 data={r['id']:r for r in load('canonical_source_context-v12.jsonl',True)}
 if record_id not in data:raise ValueError('ID outside4481 source frame')
 r=copy.deepcopy(data[record_id])
 if selector=='unit':return {k:r[k] for k in ['id','text','pages','source_ref']}
 if not bundle:return r
 needed={r['source_ref']['sha256']}|{n['source_ref']['sha256'] for n in r['contexts']}
 docs=[x for x in load('source-document-identities-v12.jsonl',True) if x['source_sha256'] in needed]
 references={x['source_resource_id'] for x in r.get('source_references',[])}
 p=OUT.parent/'prospective-common-supplements-source-only-v3.jsonl';checked(p,expected[str(p)]);historical=[x for x in rows(p) if x['record_id']==record_id]
 historical_sha={x['source_sha256'] for x in historical}
 lib=[x for x in load('source-library/library-v12.jsonl',True) if x['source_resource_id'] in references or x.get('source_sha256') in needed or x.get('snapshot_sha256') in needed or x.get('snapshot_sha256') in historical_sha]
 text_resources=[]
 for d in docs:
  e=d.get('source_text_resource')
  if e:
   p=OUT/e['relative_path'];checked(p,e['sha256']);text_resources.append(json.loads(p.read_text()))
 assets=load('source-assets-manifest-v12.jsonl',True);asset_ids={a['sha256'] for a in r.get('source_attachments',[])}
 for x in lib:asset_ids.update(a['sha256'] for a in x.get('source_page_assets',[]))
 used=[a for a in assets if a['sha256'] in asset_ids]
 for a in used:checked(Path(a['absolute_path']),a['sha256'])
 result={'common_source_bundle_version':{'version':'v12','canonical_sha256':CANON_SHA,'material_manifest_sha256':MANIFEST_SHA,'actual_consumer_read_and_use_status':'not_recorded'},'source_record':r,'source_documents':docs,'explicit_or_primary_source_resources':lib,'preserved_historical_neutral_source_supplements':historical,'source_full_text_resources':text_resources,'source_asset_locations':used,'source_locator_bases':load('source-asset-locator-bases-v12.json'),'source_reference_index':[x for x in load('source-library/reference-index-v12.jsonl',True) if x['record_id']==record_id],'source_provenance_addenda':[load('renewal-official-provenance-addendum-v11.json')] if any(x.get('source_sha256')=='d76f3d33e1ea70990992a99ae76371fcc1f99da93078e72b4376265679167a73' for x in lib) else []}
 return result
def source_inventory(b):
 """Describe available views, never claim the consumer read or used them."""
 inv=[];r=b['source_record'];s=r['source_ref']['sha256']
 inv.append({'resource_id':'BODY-'+r['id'],'source_document_id':'SOURCE-'+s,'source_sha256':s,'locator':r['source_ref']['locator'],'available_views':{'text':h(r['text'])},'availability_status':'available','representation':r.get('body_source_representation',{'kind':'current_source_body'}),'consumer_read_status':'not_recorded'})
 for n in r['contexts']:
  views={'geometry':h(cj(n['structure']))};fields={k:n[k] for k in ['text','title','caption','headers','row_cells'] if k in n}
  if fields:views['text']=h(cj(fields))
  inv.append({'resource_id':n['context_id'],'source_document_id':n['source_ref']['source_resource_id'],'source_sha256':n['source_ref']['sha256'],'locator':n['source_ref']['locator'],'available_views':views,'availability_status':'available','representation':n['kind'],'consumer_read_status':'not_recorded'})
 for d in b['explicit_or_primary_source_resources']:
  ds=d.get('source_sha256',d.get('snapshot_sha256'));inv.append({'resource_id':d['source_resource_id'],'source_document_id':d['source_resource_id'],'source_sha256':ds,'locator':{'document_resource_id':d['source_resource_id']},'available_views':{'document_bundle':h(cj(d))},'availability_status':'available','representation':'source_document_resource; applicability_scope_requires_source_read','consumer_read_status':'not_recorded'})
  for z in d.get('source_visual_text_resources',[]):
   inv.append({'resource_id':z['source_resource_id'],'source_document_id':z['source_document_resource_id'],'source_sha256':z['source_sha256'],'locator':z['source_locator'],'available_views':{'text':z['text_sha256']},'availability_status':'available','representation':z['representation'],'role':z['role'],'production_read_provenance':z['source_review_provenance'],'consumer_read_status':'not_recorded'})
  for z in d.get('source_display_regions',[]):
   inv.append({'resource_id':z['region_id'],'source_document_id':'SOURCE-'+z['source_sha256'],'source_sha256':z['source_sha256'],'locator':{'physical_page':z['physical_page'],'coordinate_system':z['coordinate_system'],'bbox_points_xyxy':z['bbox_points_xyxy']},'available_views':{'geometry':h(cj(z))},'availability_status':'available','representation':'pure_display_region_manual_padded','consumer_read_status':'not_recorded'})
 for z in b['preserved_historical_neutral_source_supplements']:
  inv.append({'resource_id':'HISTORICALSOURCE-'+h(cj(z))[:20],'source_document_id':'SOURCE-'+z['source_sha256'],'source_sha256':z['source_sha256'],'locator':z.get('source_locator',{}),'available_views':{'text':h(cj(z))},'availability_status':'available','representation':'previously_shared_neutral_source_fragment','consumer_read_status':'not_recorded'})
 for z in b['source_full_text_resources']:
  inv.append({'resource_id':'FULLSOURCE-'+h(cj(z))[:20],'source_document_id':z.get('source_resource_id'),'source_sha256':z.get('source_sha256'),'locator':{'representation':'source_full_text_resource_payload'},'available_views':{'text':h(cj(z))},'availability_status':'available','representation':'source_full_text_resource; scope_requires_source_read','consumer_read_status':'not_recorded'})
 for a in b['source_asset_locations']:
  inv.append({'resource_id':a['attachment_id'],'source_document_id':'SOURCE-'+a.get('source_pdf_sha256',s),'source_sha256':a.get('source_pdf_sha256',s),'locator':{'absolute_path':a['absolute_path'],'physical_page':a.get('physical_page')},'available_views':{'image':a['sha256']},'availability_status':'available_SHA_matched','representation':a.get('kind','original_source_asset'),'consumer_read_status':'not_recorded'})
 seen={};out=[]
 for z in inv:
  if z['resource_id'] in seen:
   if cj(z)!=cj(seen[z['resource_id']]):
    old=seen[z['resource_id']]
    if old['available_views']!=z['available_views'] or old['source_sha256']!=z['source_sha256'] or old['locator'].get('physical_page')!=z['locator'].get('physical_page'):raise ValueError('conflicting resource ID')
    old['locator'].setdefault('alternate_absolute_paths',[]).append(z['locator']['absolute_path'])
  else:seen[z['resource_id']]=z;out.append(z)
 return out
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('interface',choices=['rule','model','human','unit']);p.add_argument('id');p.add_argument('--record-only',action='store_true');p.add_argument('--inventory',action='store_true');a=p.parse_args()
 try:
  r=lookup(a.id,a.interface,bundle=not a.record_only)
  if a.inventory:
   if a.record_only or a.interface=='unit':raise ValueError('inventory needs complete bundle')
   r=source_inventory(r)
 except ValueError as e:p.error(str(e))
 print(cj(r))
