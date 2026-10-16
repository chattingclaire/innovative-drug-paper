"""Create a fixed same-bundle accessor and source-reading contract, without coding."""
from pathlib import Path
import json,hashlib,copy
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
def sf(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def rows(p):return list(map(json.loads,Path(p).read_text().splitlines()))
schema=json.loads((OUT/'current-source-schema-v11.json').read_text());schema['$id']='neutral-source-projection-v12';schema['$defs']['context']['properties']['kind']['enum']=sorted({n['kind'] for r in rows(OUT/'canonical_source_context-v12.jsonl') for n in r['contexts']});schema['x-source-protocol']['version_canonical_sha256']=sf(OUT/'canonical_source_context-v12.jsonl');schema['x-source-protocol']['bounded_visual_source_resources']='104 literal source text regions,17 manual padded display frames from two existing sameSHA PDFs; example, placeholder, heading/page number, and body instruction roles remain separate. Source producer AI visual reading is provenance, never a consumer read receipt.'
dump(OUT/'current-source-schema-v12.json',schema)
roles=sorted({r['role'] for r in rows(OUT/'source-library/slide-visual-text-v12.jsonl')})
visual_schema={'$schema':schema['$schema'],'$id':'neutral-source-visual-text-v12','type':'object','required':['source_resource_id','kind','source_sha256','source_document_resource_id','physical_page','slide_region_id','role','text','text_sha256','representation','source_locator','source_review_provenance'],'additionalProperties':False,'properties':{'source_resource_id':{'type':'string','pattern':'^SOURCEVISUAL-'},'kind':{'const':'bounded_visual_source_text'},'source_sha256':{'type':'string','pattern':'^[a-f0-9]{64}$'},'source_document_resource_id':{'type':'string','pattern':'^SOURCE-[a-f0-9]{64}$'},'physical_page':{'type':'integer','minimum':1},'printed_page':{'type':['integer','null']},'slide_region_id':{'type':['string','null'],'pattern':'^SLIDE-'},'role':{'enum':roles},'section_heading_verbatim':{'type':['string','null']},'text':{'type':'string'},'text_sha256':{'type':'string','pattern':'^[a-f0-9]{64}$'},'representation':{'type':'string'},'source_locator':{'type':'object','required':['coordinate_system','bbox_points_xyxy','bbox_status','original_page_asset_absolute_path','original_page_asset_sha256','new_300dpi_asset_absolute_path','new_300dpi_asset_sha256']},'source_review_provenance':{'type':'object'},'uncertain_characters':{'type':'array'},'source_preservation_note':{'type':'string'}}}
dump(OUT/'source-visual-resource-schema-v12.json',visual_schema)
protocol={'protocol_version':'uniform-necessary-source-reading/v12','scope':'source material access and actual-reading records; no dimension definitions, coding decisions, thresholds, or human/machine validation certificate','common_bundle_required':True,'same_rule_model_human_payload':True,'body_only_or_record_only_is_complete_material':False,'source_roles':roles,'stages':[{'stage':1,'name':'current_source_text','actions':['Verify bundle/projection hash and ID; read current body and its source representation; note physical page/paragraph/sourceSHA.','Read governing heading/parent text, qualifiers, exceptions and relevant child/list members preserved by CTX links; EOF/container is a boundary, not policy text.']},{'stage':2,'name':'source_scope_and_layout','actions':['Follow preserved parent/child/ordered-group links to complete the applicable numbered group and shared predicate.','For table rows read printed headers, row/cell membership, spanning/merged cells and the relevant row-group boundary.','For graph/image dependence read actual nodes, branches, caption/legend and visible printed operators; do not infer an unprinted OR/AND from arrangement.','Read bounded source visual text with its role and original region/page locator; same-frame examples/placeholders are separate from body instructions.','Resource availability of entire document does not automatically establish applicability of every passage.']},{'stage':3,'name':'explicit_same_edition_reference','actions':['Resolve an exact cited title/article/section/document number/year against the shared source library and reference index; record source identities and scope.','SameSHA proves same archived snapshot. DifferentSHA same-edition binding needs actual source title/date/edition and explicit relation; filename year/PDF metadata/content similarity alone do not prove it.','Use complete relevant original group and shared conditions/exceptions; do not substitute a later source or a broadly related policy.','00064 July source is identified but its expressly cited technical-guide version remains unresolved; preserve that status, do not search again or backfill the November final/drafts/other legal articles.']},{'stage':4,'name':'missing_material_and_actual_consumption','actions':['If a necessary source/view/scope/version is absent, ambiguous, unread or truncated, record a source-only request and stop conclusions depending on it; unknown never implies absence or a negative code.','Continue independent source reading whose dependency is self-contained.','Record available resources, actual delivered/read views and actual use separately; returned bundle/path/file bytes are not an actual-reading or use attestation.','A text-only rule records text/geometry consumed. It cannot claim pixels were read because image paths were available.','Resource-production AI visual reading is provenance; it is not a true human independent coding event or the current consumer\'s reading.']}],'stop_reason_enum':['missing_required_source','source_hash_mismatch','required_reference_unresolved','reference_edition_ambiguous','required_view_not_read','read_delivery_incomplete','source_role_unknown','source_operator_not_visible','scope_boundary_unknown'],'executable_commands':{'prepare':'python3 source_reading_protocol_v12.py prepare RECORD_ID --run RUN_ID --reader rule|model|human > run-source-log.json','check':'python3 source_reading_protocol_v12.py check run-source-log.json'},'requirements_policy':'prepare produces mechanical current-body/CTX requirements and a source-scope-review-pending state. The operator must record finite necessary-source requirements and explicit-reference status using source evidence; it does not infer universal necessity or applicability from all fulltext.','gate_limit':'source_reads_recorded gate checks source/view receipts only; it never certifies interpretation, labels, method performance, human identity, or final freeze.'}
dump(OUT/'source-reading-protocol-v12.json',protocol)
manifest_names=['canonical_source_context-v12.jsonl','current-source-schema-v12.json','source-visual-resource-schema-v12.json','source-document-identities-v12.jsonl','source-library/library-v12.jsonl','source-library/reference-index-v12.jsonl','source-library/slide-visual-text-v12.jsonl','source-library/slide-display-geometry-v12.json','source-assets-manifest-v12.jsonl','source-asset-locator-bases-v12.json','source-reading-protocol-v12.json','renewal-official-provenance-addendum-v11.json']
paths=[OUT/n for n in manifest_names]+[OUT.parent/'prospective-common-supplements-source-only-v3.jsonl']
for d in rows(OUT/'source-document-identities-v12.jsonl'):
 if d.get('source_text_resource'):paths.append(OUT/d['source_text_resource']['relative_path'])
manifest={'version':'v12','canonical_sha256':sf(OUT/'canonical_source_context-v12.jsonl'),'files':[{'path':str(p),'sha256':sf(p),'bytes':p.stat().st_size} for p in dict.fromkeys(paths)],'source_assets_are_separately_manifested_and_checked_by_accessor':True,'actual_read_and_use_not_inferred':True}
dump(OUT/'source-material-manifest-v12.json',manifest)
reader=r'''"""Same neutral source bundle for rule/model/human. No consumer read/use inference."""
from pathlib import Path
import json,hashlib,copy,argparse
OUT=Path(__file__).resolve().parent
CANON_SHA='__CANON__'
MANIFEST_SHA='__MANIFEST__'
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
 result={'common_source_bundle_version':{'version':'v12','canonical_sha256':CANON_SHA,'material_manifest_sha256':MANIFEST_SHA,'actual_consumer_read_and_use_status':'not_recorded'},'source_record':r,'source_documents':docs,'explicit_or_primary_source_resources':lib,'preserved_historical_neutral_source_supplements':historical,'source_full_text_resources':text_resources,'source_asset_locations':used,'source_locator_bases':load('source-asset-locator-bases-v12.json'),'source_reference_index':[x for x in load('source-library/reference-index-v12.jsonl',True) if x['record_id']==record_id],'source_provenance_addenda':[load('renewal-official-provenance-addendum-v11.json')] if any(x.get('source_sha256')=='d76f3d33b14f1405fc5880b84953e8c978f5b9b0b97e52d77b9d4629f4fcd6dba' for x in lib) else []}
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
'''
# Select provenance by verified actual archived SHA, not a guessed ID.
off=json.loads((OUT/'renewal-official-provenance-addendum-v11.json').read_text());reader=reader.replace('d76f3d33b14f1405fc5880b84953e8c978f5b9b0b97e52d77b9d4629f4fcd6dba',off['source_pdf_archived_sha256']);reader=reader.replace('__CANON__',sf(OUT/'canonical_source_context-v12.jsonl')).replace('__MANIFEST__',sf(OUT/'source-material-manifest-v12.json'));(OUT/'source_only_interface_v12.py').write_text(reader)
print(json.dumps({'canonical_sha256':sf(OUT/'canonical_source_context-v12.jsonl'),'material_manifest_sha256':sf(OUT/'source-material-manifest-v12.json'),'protocol_sha256':sf(OUT/'source-reading-protocol-v12.json')},indent=2))
