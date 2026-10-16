"""Export four historically developed neutral source bundles; no labels or sampling."""
from pathlib import Path
import json,hashlib
import source_only_interface_v12 as src
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];DEST=OUT/'4-record-common-v12'
H=lambda b:hashlib.sha256(b).hexdigest()
def sf(p):return H(Path(p).read_bytes())
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def lines(p,x):Path(p).write_text(''.join(json.dumps(z,ensure_ascii=False,separators=(',',':'))+'\n' for z in x))
assert (OUT/'delivery-seal-v12.json').exists(),'Seal v12 before making dependent four-record package'
DEST.mkdir(exist_ok=True)
ids=['RECODE25-00887','RECODE25-00891','RECODE25-00859','RECODE25-01423'];old={r['id']:r for r in src.rows(OUT/'canonical_source_context-v11.jsonl')};bundles=[src.lookup(i,'model') for i in ids]
manual=ROOT/'03-manual/common-manual-v1.1-development.md';assert manual.exists()
changes=[];resource_index=[]
for b in bundles:
 r=b['source_record'];rid=r['id'];assert r==old[rid]
 assert src.cj(src.lookup(rid,'rule'))==src.cj(b)==src.cj(src.lookup(rid,'human'))
 refs=[]
 for d in b['source_documents']:
  assert sf(d['snapshot'])==d['source_sha256'];refs.append({'source_document_resource_id':d['source_resource_id'],'source_sha256':d['source_sha256'],'snapshot_absolute_path':d['snapshot'],'actual_snapshot_SHA_matched':True})
 paras=[]
 for d in b['explicit_or_primary_source_resources']:
  for k,z in enumerate(d.get('source_texts',[]),1):
   if isinstance(z,dict) and 'text' in z:
    assert H(z['text'].encode())==z['text_sha256'];paras.append({'source_document_resource_id':d['source_resource_id'],'source_sha256':d.get('source_sha256',d.get('snapshot_sha256')),'source_text_ordinal_1based':k,'text_sha256':z['text_sha256'],'source_ref':z.get('source_ref',z.get('source_locator'))})
 assets=[]
 for a in b['source_asset_locations']:
  assert sf(a['absolute_path'])==a['sha256'];assets.append({'asset_id':a['attachment_id'],'absolute_path':a['absolute_path'],'asset_sha256':a['sha256'],'source_pdf_sha256':a.get('source_pdf_sha256'),'physical_page':a.get('physical_page'),'actual_file_SHA_matched':True})
 if rid!='RECODE25-01423':assert len(paras)==37 and len(assets)==9 and sum(n['kind']=='same_snapshot_referenced_source_paragraph' for n in r['contexts'])==37
 else:assert any(n['kind']=='table_group_row' for n in r['contexts']) and len(assets)>=1
 resource_index.append({'record_id':rid,'source_files':refs,'shared_source_text_resources':paras,'source_assets':assets,'preserved_old_neutral_supplement_N':len(b['preserved_historical_neutral_source_supplements']),'body_source_ref':r['source_ref'],'context_ids':[n['context_id'] for n in r['contexts']]})
 changes.append({'record_id':rid,'body_sha256':H(r['text'].encode()),'canonical_record_normalized_byte_SHA':H(src.cj(r).encode()),'canonical_row_content_identical_to_v11':True,'body_and_existing_CTX_unchanged':True,'added_v12_slide_source_resources_for_this_record_N':0,'current_context_N':len(r['contexts']),'same_bundle_three_endpoint_SHA':H(src.cj(b).encode()),'all_three_endpoints_identical':True,'actual_consumer_reads_or_codes_not_produced':True})
lines(DEST/'common-source-bundles.jsonl',bundles);lines(DEST/'canonical-source-context.jsonl',[b['source_record'] for b in bundles]);dump(DEST/'source-resource-index.json',resource_index);dump(DEST/'source-content-comparison.json',{'status':'previously_developed_source_material; not_new_unseen_sample','compared_version':'v11','current_version':'v12','checks':changes,'source_content_changed_record_N':0,'four_record_canonical_rows_content_identical':True,'shared_source_metadata_and_accessor_now_version_bound_to_v12':True,'no_coding_answers_reference_labels_private_mapping_or_selection_roles_used':True})
readme='''四条既有开发语料完整共同来源包 v12\n\n00887、00891、00859、01423均为历史开发记录。它们的当前正文、CTX和规范化逐行字节与v11相同；本包从已封存v12默认完整来源接口导出，不是新留出样本。\n\n前三条各保留同版续约原文37资源、完整编号/共享条件几何和实际9页图。01423保留原表格行组、CTX、表格结构和实际原页。现有公共中性补材仅按原source accessor的实际绑定保留；source-resource-index.json列逐记录资源/原件/原图绝对路径与SHA。\n\ncommon-source-bundles.jsonl为完整共同输入；canonical-source-context.jsonl只是逐行副本，不能独立替代共同bundle。共同手册v1.1仅在seal绑定原文件及SHA，正文语义未改。此封存不包含参照、旧机器答案、A/B结果或private mapping角色。\n\n资源可用不证明当前方法已读入或使用；按v12统一读取协议记录必要语境、确指同版、图文视图和真实消费事件。规则若只读text/geometry，不能声称看过图片。ROOT另定A/B复判、提示/规则/抽样及联合冻结；本包不声称真人或正式指标检验完成。\n'''
(DEST/'README.md').write_text(readme)
names=['common-source-bundles.jsonl','canonical-source-context.jsonl','source-resource-index.json','source-content-comparison.json','README.md']
seal={'status':'sealed_four_existing_development_records_common_source_only_v12','record_ids':ids,'source_frame_version':'v12','canonical_projection_sha256':src.CANON_SHA,'source_material_manifest_sha256':src.MANIFEST_SHA,'parent_v12_delivery_seal':{'path':str(OUT/'delivery-seal-v12.json'),'sha256':sf(OUT/'delivery-seal-v12.json')},'source_protocol':{'path':str(OUT/'source-reading-protocol-v12.json'),'sha256':sf(OUT/'source-reading-protocol-v12.json')},'common_manual':{'path':str(manual),'sha256':sf(manual),'version':'v1.1','semantics_modified':False},'files':[{'path':str(DEST/n),'sha256':sf(DEST/n),'bytes':(DEST/n).stat().st_size} for n in names],'canonical_rows_identical_to_v11':True,'not_new_unseen_sample':True,'no_labels_or_coding_launched':True,'not_human_independent_validation':True}
dump(DEST/'delivery-seal.json',seal)
print(json.dumps({'directory':str(DEST),'seal_sha256':sf(DEST/'delivery-seal.json'),'source_bundles_sha256':sf(DEST/'common-source-bundles.jsonl'),'common_manual_v1_1_sha256':sf(manual),'record_N':4},ensure_ascii=False,indent=2))
