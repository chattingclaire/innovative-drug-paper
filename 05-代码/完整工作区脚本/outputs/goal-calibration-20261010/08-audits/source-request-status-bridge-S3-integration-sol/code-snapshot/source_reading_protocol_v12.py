"""Prepare/check source-only reading logs; never infer coding or actual reading."""
from pathlib import Path
import argparse,json,hashlib,sys
import source_only_interface_v12 as src
OUT=Path(__file__).resolve().parent
H=lambda b:hashlib.sha256(b).hexdigest()
def protocol_sha():return H((OUT/'source-reading-protocol-v12.json').read_bytes())
def prepare(rid,run,reader):
 b=src.lookup(rid,reader);inv=src.source_inventory(b);items={z['resource_id']:z for z in inv};req=[]
 def add(i,v,relation):
  q={'requirement_id':'REQ-'+H((i+':'+v).encode())[:20],'required_resource_id':i,'required_view':v,'source_relation_kind':relation,'requirement_status':'resolved','source_evidence_locator':items[i]['locator']}
  if q['requirement_id'] not in {z['requirement_id'] for z in req}:req.append(q)
 add('BODY-'+rid,'text','current_body')
 for n in b['source_record']['contexts']:
  for v in items[n['context_id']]['available_views']:add(n['context_id'],v,'preserved_current_source_context')
  if n['kind']=='same_snapshot_source_display_geometry':
   st=n['structure'];add(st['bound_body_instruction_resource_id'],'text','same_snapshot_body_instruction')
   add(st['bound_body_instruction_region_id'],'geometry','same_frame_display_relationship')
   for d in b['explicit_or_primary_source_resources']:
    for region in d.get('source_display_regions',[]):
     if region['region_id']==st['bound_body_instruction_region_id']:
      for i in region['children_resource_ids']:add(i,'text','same_frame_text_and_role')
    for z in d.get('source_visual_text_resources',[]):
     if z['role']=='illustration_scope_notice':add(z['source_resource_id'],'text','same_document_printed_example_scope_notice')
 references=[]
 if rid=='RECODE25-00064':references=[{'citation_kind':'July_expressly_cited_technical_guide','citation_source_ref':b['source_record']['source_ref'],'citation_literal':b['source_record']['text'],'target_resource_id':None,'target_source_sha256':None,'resolution_status':'unresolved','necessary_dependency':None,'identity_basis_refs':['SOURCE-REFERENCE-VERSION-CONDITIONAL-202007'],'source_status':'July_program_original_DOC_confirmed; cited_technical_guide_version_not_unique'}]
 return {'protocol_version':'uniform-necessary-source-reading/v12','protocol_sha256':protocol_sha(),'run_id':run,'reader_selector':reader,'record_id':rid,'canonical_sha256':src.CANON_SHA,'material_manifest_sha256':src.MANIFEST_SHA,'source_inventory':inv,'requirements':req,'necessary_source_scope_review_status':'pending','necessary_source_scope_review_note':None,'reference_resolution':references,'read_receipts':[],'use_receipts':[],'source_requests':[],'read_or_use_inferred_from_availability':False,'identity_attestation_verified_as_true_human':False}
def check(log):
 errors=[];stops=[]
 if log.get('protocol_sha256')!=protocol_sha():errors.append('protocol_SHA_mismatch')
 b=src.lookup(log['record_id'],log['reader_selector']);expected_inv={z['resource_id']:z for z in src.source_inventory(b)}
 if log.get('canonical_sha256')!=src.CANON_SHA or log.get('material_manifest_sha256')!=src.MANIFEST_SHA:errors.append('source_material_version_mismatch')
 actual={z['resource_id']:z for z in log.get('source_inventory',[])}
 if src.cj(actual)!=src.cj(expected_inv):errors.append('source_inventory_changed')
 good={};read_by_id={}
 for z in log.get('read_receipts',[]):
  needed=['receipt_id','run_id','record_id','resource_id','source_sha256','view','view_sha256','locator_read','delivery_status','read_attestation','reader','event_id']
  if any(k not in z for k in needed):errors.append('incomplete_read_receipt_fields');continue
  if z['receipt_id'] in read_by_id:errors.append('duplicate_receipt_ID');continue
  read_by_id[z['receipt_id']]=z
  if z['run_id']!=log['run_id'] or z['record_id']!=log['record_id']:errors.append('read_receipt_run_or_record_mismatch');continue
  i=expected_inv.get(z['resource_id'])
  if not i or z['view_sha256']!=i['available_views'].get(z['view']) or z['source_sha256']!=i['source_sha256']:errors.append('read_receipt_source_or_view_SHA_mismatch');continue
  if z['delivery_status']=='complete' and z['read_attestation']=='recorded':good[z['resource_id'],z['view']]=z['receipt_id']
  elif z['delivery_status']!='complete':stops.append('read_delivery_incomplete')
 for r in log.get('requirements',[]):
  if r.get('requirement_status')!='resolved':stops.append('required_reference_unresolved');continue
  if r.get('required_resource_id') not in expected_inv:stops.append('missing_required_source')
  elif (r['required_resource_id'],r['required_view']) not in good:stops.append('required_view_not_read')
 # Original mechanical requirements cannot silently be removed.
 base=prepare(log['record_id'],log['run_id'],log['reader_selector'])
 logged_req={z.get('requirement_id'):z for z in log.get('requirements',[])}
 if any(src.cj(z)!=src.cj(logged_req.get(z['requirement_id'])) for z in base['requirements']):errors.append('current_source_requirements_removed_or_changed')
 for z in log.get('reference_resolution',[]):
  if z.get('necessary_dependency') and z.get('resolution_status') not in ['exact_snapshot','same_edition_confirmed']:stops.append('required_reference_unresolved')
  if z.get('resolution_status') in ['exact_snapshot','same_edition_confirmed']:
   if not z.get('target_source_sha256') or not z.get('identity_basis_refs'):errors.append('reference_identity_basis_missing')
 for z in log.get('source_requests',[]):
  if z.get('status','unresolved')!='resolved' and z.get('necessary_dependency',True):stops.append(z.get('stop_reason','missing_required_source'))
 for z in log.get('use_receipts',[]):
  if z.get('use_status')=='used':
   r=read_by_id.get(z.get('read_receipt_id'))
   if not r or r['resource_id']!=z.get('resource_id') or r['delivery_status']!='complete' or r['read_attestation']!='recorded' or (r['resource_id'],r['view']) not in good:errors.append('used_without_complete_recorded_matching_read')
 if log.get('necessary_source_scope_review_status')!='complete':stops.append('scope_boundary_unknown')
 elif not log.get('necessary_source_scope_review_note'):errors.append('scope_review_source_evidence_note_missing')
 if log['record_id']=='RECODE25-00064' and any(z.get('resolution_status') in ['exact_snapshot','same_edition_confirmed'] and z.get('citation_kind')=='July_expressly_cited_technical_guide' for z in log.get('reference_resolution',[])):errors.append('known_unresolved_00064_guide_silently_bound')
 return {'record_id':log['record_id'],'run_id':log['run_id'],'source_read_requirements_recorded':not errors and not stops,'errors':sorted(set(errors)),'dependency_stop_reasons':sorted(set(stops)),'available_resource_N':len(expected_inv),'complete_recorded_read_N':len(good),'use_receipt_N':len(log.get('use_receipts',[])),'actual_reading_is_operator_attestation_not_independently_verified':True,'semantic_correctness_or_coding_certified':False,'true_human_independent_validation_certified':False,'final_material_or_execution_freeze_certified':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();sub=p.add_subparsers(dest='mode',required=True);a=sub.add_parser('prepare');a.add_argument('record');a.add_argument('--run',required=True);a.add_argument('--reader',choices=['rule','model','human'],required=True);c=sub.add_parser('check');c.add_argument('log');z=p.parse_args()
 try:r=prepare(z.record,z.run,z.reader) if z.mode=='prepare' else check(json.loads(Path(z.log).read_text()))
 except (ValueError,KeyError) as e:p.error(str(e))
 print(json.dumps(r,ensure_ascii=False,indent=2))
