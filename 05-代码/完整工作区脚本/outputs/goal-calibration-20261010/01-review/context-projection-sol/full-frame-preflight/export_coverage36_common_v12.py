"""Export fixed36 previously exposed development IDs through sealed v12 source accessor.
No coding, reference-label reading, new agent, sampling, or source discovery.
"""
from pathlib import Path
import json,hashlib,importlib.util,sys
from collections import defaultdict
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];DEST=OUT/'coverage36-common-v12';INPUT=ROOT/'06-coding/development-reference36-v11/source.jsonl'
H=lambda b:hashlib.sha256(b).hexdigest()
def sf(p):return H(Path(p).read_bytes())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
spec=importlib.util.spec_from_file_location('source_interface_v12',OUT/'source_only_interface_v12.py');src=importlib.util.module_from_spec(spec);spec.loader.exec_module(src)
parent=OUT/'delivery-seal-v12.json';assert sf(parent)=='68b62081c523f3e22ae5830887b073f50ef79a02c0143a4608630355a4b7f426';seal=json.loads(parent.read_text());assert all(sf(z['path'])==z['sha256'] for z in seal['files'])
assert INPUT.exists();input_bytes=INPUT.read_bytes();ids=[json.loads(x)['id'] for x in input_bytes.decode('utf-8').splitlines()];assert len(ids)==len(set(ids))==36
exposure=json.loads((ROOT/'01-review/exposure-ids.json').read_text());assert set(ids)<=set(exposure['excluded_ids']);assert not (set(ids)-set(exposure['direct_exposure_ids']))
manual=ROOT/'03-manual/common-manual-v1.1-development.md';assert sf(manual)=='6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f'
DEST.mkdir(exist_ok=True);assert not (DEST/'delivery-seal.json').exists(),'Do not overwrite a sealed package'
files={};documents={};libraries={};assets={};paragraphs={};per_record=[];lines=[]
def add_file(path,sha,kind,rid,**details):
 p=Path(path).resolve();assert p.is_file();assert sf(p)==sha
 if sha not in files:files[sha]={'file_sha256':sha,'bytes':p.stat().st_size,'absolute_paths':[],'resource_kinds':[],'record_ids':[],'source_details':[]}
 f=files[sha]
 if str(p) not in f['absolute_paths']:f['absolute_paths'].append(str(p))
 if kind not in f['resource_kinds']:f['resource_kinds'].append(kind)
 if rid not in f['record_ids']:f['record_ids'].append(rid)
 if details and details not in f['source_details']:f['source_details'].append(details)
 return sha
for ordinal,rid in enumerate(ids,1):
 b=src.lookup(rid,'model');r=b['source_record'];line=src.cj(b).encode('utf-8');lines.append(line+b'\n')
 docrefs=[];librefs=[];assetrefs=[];parrefs=[]
 for d in b['source_documents']:
  key=d['source_sha256'];documents.setdefault(key,{'source_sha256':key,'source_document_resource_id':d['source_resource_id'],'snapshot_absolute_path':d['snapshot'],'snapshot_bytes':Path(d['snapshot']).stat().st_size,'record_ids':[]})
  if rid not in documents[key]['record_ids']:documents[key]['record_ids'].append(rid)
  add_file(d['snapshot'],key,'document_snapshot',rid,source_document_resource_id=d['source_resource_id']);docrefs.append(key)
  if d.get('source_text_resource'):
   e=d['source_text_resource'];add_file(OUT/e['relative_path'],e['sha256'],'neutral_full_source_transcription_file',rid,source_document_sha256=key)
  for k in ['source_visual_text_resource','source_display_geometry_resource']:
   if d.get(k):
    e=d[k];add_file(OUT/e['relative_path'],e['sha256'],k,rid,source_document_sha256=key)
 for d in b['explicit_or_primary_source_resources']:
  lid=d['source_resource_id'];payload=src.cj(d).encode();libraries.setdefault(lid,{'source_resource_id':lid,'source_sha256':d.get('source_sha256',d.get('snapshot_sha256')),'payload_json_utf8_bytes':len(payload),'payload_sha256':H(payload),'record_ids':[]})
  assert libraries[lid]['payload_sha256']==H(payload)
  if rid not in libraries[lid]['record_ids']:libraries[lid]['record_ids'].append(rid)
  librefs.append(lid)
  snapshot=d.get('snapshot')
  if not snapshot and d.get('snapshot_relative_path'):snapshot=str(OUT/'source-library'/d['snapshot_relative_path'])
  if snapshot:
   sha=d.get('snapshot_sha256',d.get('source_sha256'));add_file(snapshot,sha,'document_snapshot',rid,source_document_resource_id=lid)
   documents.setdefault(sha,{'source_sha256':sha,'source_document_resource_id':lid,'snapshot_absolute_path':str(Path(snapshot).resolve()),'snapshot_bytes':Path(snapshot).stat().st_size,'record_ids':[]})
   if rid not in documents[sha]['record_ids']:documents[sha]['record_ids'].append(rid)
   if sha not in docrefs:docrefs.append(sha)
  for ordinal_text,z in enumerate(d.get('source_texts',[]),1):
   if not isinstance(z,dict) or 'text' not in z:continue
   assert H(z['text'].encode())==z['text_sha256']
   locator=z.get('source_ref',z.get('source_locator'));key=H(src.cj({'doc':lid,'text_sha256':z['text_sha256'],'locator':locator}).encode())
   paragraphs.setdefault(key,{'neutral_resource_key':'SHARED-SOURCE-TEXT-'+key,'source_document_resource_id':lid,'source_document_sha256':d.get('source_sha256',d.get('snapshot_sha256')),'text_sha256':z['text_sha256'],'text_utf8_bytes':len(z['text'].encode()),'locator':locator,'resource_location':{'library_resource_id':lid,'source_text_ordinal_1based':ordinal_text},'record_ids':[]})
   if rid not in paragraphs[key]['record_ids']:paragraphs[key]['record_ids'].append(rid)
   parrefs.append(key)
 for a in b['source_asset_locations']:
  sha=a['sha256'];add_file(a['absolute_path'],sha,'image_asset',rid,source_document_sha256=a.get('source_pdf_sha256'),physical_page=a.get('physical_page'))
  assets.setdefault(sha,{'asset_sha256':sha,'asset_ids':[],'absolute_paths':[],'bytes':Path(a['absolute_path']).stat().st_size,'source_positions':[],'record_ids':[]})
  z=assets[sha]
  if a['attachment_id'] not in z['asset_ids']:z['asset_ids'].append(a['attachment_id'])
  if a['absolute_path'] not in z['absolute_paths']:z['absolute_paths'].append(a['absolute_path'])
  position={'source_document_sha256':a.get('source_pdf_sha256'),'physical_page':a.get('physical_page')}
  if position not in z['source_positions']:z['source_positions'].append(position)
  if rid not in z['record_ids']:z['record_ids'].append(rid)
  if sha not in assetrefs:assetrefs.append(sha)
 def text_strings(x):
  if isinstance(x,str):yield x
  elif isinstance(x,list):
   for y in x:yield from text_strings(y)
 ctx_strings=[t for n in r['contexts'] for k in ['text','title','caption','headers','row_cells'] if k in n for t in text_strings(n[k])]
 per_record.append({'ordinal_1based':ordinal,'record_id':rid,'common_bundle_json_utf8_bytes_excluding_newline':len(line),'common_bundle_json_sha256':H(line),'common_bundle_jsonl_line_utf8_bytes_including_newline':len(line)+1,'current_source_record_json_utf8_bytes':len(src.cj(r).encode()),'body_utf8_bytes':len(r['text'].encode()),'body_sha256':H(r['text'].encode()),'current_CTX_N':len(r['contexts']),'current_CTX_json_utf8_bytes':len(src.cj(r['contexts']).encode()),'current_CTX_literal_fields_utf8_bytes_sum':sum(len(t.encode()) for t in ctx_strings),'current_CTX_literal_fields_byte_definition':'Sum UTF8 bytes of each actual text/title/caption string and each headers/row_cells string, retaining repetition; no fabricated source-necessity assessment.','current_CTX_literal_fields_sha256':H(src.cj([{k:n[k] for k in ['context_id','text','title','caption','headers','row_cells'] if k in n} for n in r['contexts']]).encode()),'public_asset_path_N':len(b['source_asset_locations']),'public_asset_distinct_SHA_N':len(assetrefs),'source_document_sha256s':docrefs,'shared_library_resource_ids':librefs,'shared_text_resource_keys':parrefs,'image_asset_sha256s':assetrefs,'preserved_old_neutral_SUPP_N':len(b['preserved_historical_neutral_source_supplements']),'source_reference_index_row_N':len(b['source_reference_index']),'source_consumption_not_inferred':True})
 # Pure bundle keeps every original field; it cannot carry coding/reference-label keys.
 forbidden=set(json.loads((OUT/'current-source-schema-v12.json').read_text())['x-source-protocol']['recursive_forbidden_exact_keys'])
 def walk(x):
  if isinstance(x,dict):
   for k,v in x.items():yield k;yield from walk(v)
  elif isinstance(x,list):
   for y in x:yield from walk(y)
 assert not forbidden.intersection(walk(b))
packet=DEST/'common-source-bundles.jsonl';packet.write_bytes(b''.join(lines));assert packet.stat().st_size==sum(x['common_bundle_jsonl_line_utf8_bytes_including_newline'] for x in per_record)
index={'version':'coverage36-common-v12','fixed_record_ids_in_input_order':ids,'per_record':per_record,'shared_document_snapshots':list(documents.values()),'shared_document_library_resources':list(libraries.values()),'shared_source_text_resources':list(paragraphs.values()),'shared_image_assets':list(assets.values()),'deduplicated_actual_file_list_by_SHA':list(files.values()),'byte_counts_are_actual_utf8_or_file_bytes_not_token_estimates':True,'duplicate_text_and_assets_preserved_in_bundle_but_shared_index_deduplicated':True}
dump(DEST/'source-resource-index.json',index)
manifest={'status':'fixed36_previously_exposed_development_source_only_package_v12','record_N':36,'fixed_record_ids':ids,'id_order_source':{'path':str(INPUT),'sha256':sf(INPUT),'bytes':len(input_bytes),'fields_consumed':'id only; no reference labels, machine outputs, A/B answers or evaluations read'},'source_accessor':{'path':str(OUT/'source_only_interface_v12.py'),'sha256':sf(OUT/'source_only_interface_v12.py'),'endpoint':'model default complete bundle; original fields preserved'},'parent_v12_seal':{'path':str(parent),'sha256':sf(parent)},'common_manual':{'path':str(manual),'sha256':sf(manual),'version':'v1.1','semantics_modified':False},'actual_byte_counts':{'common_source_bundles_jsonl_UTF8_total_including_newlines':packet.stat().st_size,'bundle_JSON_UTF8_total_excluding_newlines':sum(x['common_bundle_json_utf8_bytes_excluding_newline'] for x in per_record),'body_UTF8_total':sum(x['body_utf8_bytes'] for x in per_record),'current_CTX_literal_fields_UTF8_total_with_repetition':sum(x['current_CTX_literal_fields_utf8_bytes_sum'] for x in per_record),'current_CTX_JSON_UTF8_total':sum(x['current_CTX_json_utf8_bytes'] for x in per_record),'source_document_snapshot_bytes_deduplicated_by_SHA':sum(z['snapshot_bytes'] for z in documents.values()),'image_asset_bytes_deduplicated_by_SHA':sum(z['bytes'] for z in assets.values()),'all_actual_source_resource_file_bytes_deduplicated_by_SHA':sum(z['bytes'] for z in files.values())},'deduplicated_resource_counts':{'source_document_snapshot_SHA_N':len(documents),'document_library_resource_N':len(libraries),'shared_source_text_resource_N':len(paragraphs),'image_asset_SHA_N':len(assets),'image_asset_absolute_path_N':len({p for a in assets.values() for p in a['absolute_paths']}),'all_actual_resource_file_SHA_N':len(files),'all_actual_resource_file_absolute_path_N':len({p for a in files.values() for p in a['absolute_paths']})},'all36_verified_existing_direct_exposure_by_stable_ID':True,'new_remaining_pool_records_selected_N':0,'source_resource_byte_hash_checks_passed':True,'token_capacity_not_estimated':True,'actual_read_use_or_coding_not_claimed':True,'v12_sealed_files_not_modified':True}
dump(DEST/'manifest.json',manifest)
(DEST/'README.md').write_text('36条已曝光开发覆盖共同来源包 v12\n\nID和顺序只取development-reference36-v11/source.jsonl的id字段。每条由已封存v12 model默认完整bundle导出，原字段/全部当前CTX、旧SUPP、引用、几何、原页定位和例示角色保持；没有读reference.jsonl或任何答案/评价。\n\nsource-resource-index.json列每条实际JSON、正文/CTX字节、图页数量与固定源ID顺序，并按SHA去重列来源快照、共享原文、图片和实际文件绝对定位。重复资源仍完整保留在各条输入；去重仅用于文件清单和容量分析。字节不是token，不推测模型容量。\n\n共同手册v1.1原文件/hash绑定于seal，语义未改。ROOT另行执行原生LLM开发覆盖；此包不作编码、真人检验或正式指标认证，资源可用不等于方法实际已读或使用。\n')
# Recheck fixed parent seal after preparation, without changing it.
assert all(sf(z['path'])==z['sha256'] for z in seal['files']);assert sf(parent)==manifest['parent_v12_seal']['sha256']
names=['common-source-bundles.jsonl','source-resource-index.json','manifest.json','README.md'];delivery={'status':'sealed_fixed36_existing_development_common_source_only_v12','record_N':36,'fixed_record_ids':ids,'parent_v12_seal_sha256':sf(parent),'source_canonical_sha256':src.CANON_SHA,'material_manifest_sha256':src.MANIFEST_SHA,'common_manual':manifest['common_manual'],'files':[{'path':str(DEST/n),'sha256':sf(DEST/n),'bytes':(DEST/n).stat().st_size} for n in names],'builder':{'path':str(Path(__file__).resolve()),'sha256':sf(Path(__file__))},'actual_byte_counts':manifest['actual_byte_counts'],'deduplicated_resource_counts':manifest['deduplicated_resource_counts'],'not_coding_or_read_receipt':True,'not_new_unseen_sample':True}
dump(DEST/'delivery-seal.json',delivery)
print(json.dumps({'seal_path':str(DEST/'delivery-seal.json'),'seal_sha256':sf(DEST/'delivery-seal.json'),'common_source_bundles_sha256':sf(packet),'actual_byte_counts':manifest['actual_byte_counts'],'deduplicated_resource_counts':manifest['deduplicated_resource_counts']},ensure_ascii=False,indent=2))
