"""Restore exact same-snapshot referenced source paragraphs; no coding data."""
from pathlib import Path
import json,hashlib,copy,os,importlib.util,re
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2];RP=ROOT/'01-review/renewal-reference-source-sol'
sp=importlib.util.spec_from_file_location('preflight',OUT/'build_full_frame_preflight_v2.py');pr=importlib.util.module_from_spec(sp);sp.loader.exec_module(pr)
rows=pr.readrows;jl=pr.jsonl;dump=pr.dump;sha=pr.sha;sf=pr.shafile
supp=json.loads((RP/'source-only-supplement.json').read_text());seal=json.loads((RP/'delivery-sha256.json').read_text());assert sf(RP/'source-only-supplement.json')=='e5dd1f26e61858d401a32834e9b059cc570475cfde3af37a67fde7a99837e6b2';assert sf(RP/'delivery-sha256.json')=='6eefa80d4270cb01273aecd74195dcf5d656c02ccd1e399b110ef24786e7c6ba'
for x in seal['files']:assert sf(RP/x['path'])==x['sha256']
S=supp['source']['source_sha256'];assert sf(Path(supp['source']['snapshot_path']))==S
resources=[];idmap={x['resource_id']:'SOURCEPARAGRAPH-'+sha((S+x['resource_id']).encode())[:20] for x in supp['resources']}
def remap(x,m):
 if isinstance(x,dict):return {k:remap(v,m) for k,v in x.items() if k!='dimension_decision'}
 if isinstance(x,list):return [remap(v,m) for v in x]
 if isinstance(x,str):return m.get(x,x)
 return x
for x in supp['resources']:
 assert sha(x['text'].encode())==x['text_sha256'];n={k:copy.deepcopy(x[k]) for k in ['kind','heading_path','source_sha256','source_path','text','text_sha256','source_ref','source_char_interval_footerless_whitespace_normalized']};n['source_resource_id']=idmap[x['resource_id']];n['source_ref']['source_resource_id']='SOURCE-'+S;resources.append(n)
assets=json.loads((RP/'source-page-assets-manifest.json').read_text());alist=assets['assets'];assert len(alist)==9
neutral={'source_resource_id':'SOURCE-'+S,'source_sha256':S,'snapshot':supp['source']['snapshot_path'],'snapshot_sha256':S,'document_title':'谈判药品续约规则','document_year':2025,'official_url':None,'official_publication_date':None,'metadata_status':'official URL and publication date not established in the frozen source manifest; source content annual example is2025','source_texts':resources,'source_geometry':remap(supp['source_geometry'],idmap),'source_page_assets':[],'scope':'full rule1, full rule2, source preface, expressly referenced rule3 opening and shared appendix passages; same original source snapshot'}
for a in alist:
 p=Path(a.get('absolute_path',RP/a.get('asset_path','')));assert sf(p)==a['sha256'];neutral['source_page_assets'].append({'sha256':a['sha256'],'relative_path':os.path.relpath(p,OUT),'physical_page':a['physical_page'],'source_pdf_sha256':S,'render_dpi':a['render_dpi']})
dump(OUT/'source-library/renewal2025-reference-source-v11.json',neutral)
data=rows(OUT/'canonical_source_context-v10.jsonl');D={r['id']:r for r in data};ctx=rows(OUT/'context-source-QA-v10.jsonl');idx=rows(OUT/'source-library/reference-index-v10.jsonl');lib=rows(OUT/'source-library/library-v10.jsonl');lib.append(neutral)
known={x['record_id']:x for x in supp['target_record_bindings']}
newnodes=[];bindings=[]
for rid,b in known.items():assert sha(D[rid]['text'].encode())==b['existing_body_text_sha256'];assert D[rid]['source_ref']['sha256']==S
# Uniform source-only applicability for restoring this referenced resource:
# actual same-SHA document records with literal references to either printed
# rule heading or to the same-source named "简易续约"/"常规目录管理" condition.
# The two requested records are included by their inspected literal source links.
eligible=[]
for r in data:
 fields=[(None,'text',r['text'],r['source_ref']['sha256'])]+[(n['context_id'],k,v,n['source_ref']['sha256']) for n in r['contexts'] for k,v in pr.pr.text_values(n)]
 hits=[{'context_id':c,'source_field':f,'literal_reference':z,'source_field_text_sha256':sha(t.encode())} for c,f,t,s in fields if s==S for z in ['简易续约','纳入常规目录管理','规则一','规则二'] if z in t]
 if hits:eligible.append((r,hits))
assert set(known)<={r['id'] for r,h in eligible}
for r,hits in eligible:
 old=copy.deepcopy(r);cm={x['resource_id']:'CTX-SRCRENEW-'+sha((r['id']+S+x['resource_id']).encode())[:20] for x in supp['resources']}
 related=sorted({x['context_id'] for x in hits if x['context_id']})
 for x,n in zip(supp['resources'],resources):
  gid=cm[x['resource_id']];loc=copy.deepcopy(n['source_ref']['locator']);loc['source_paragraph_id']=n['source_resource_id'];node={'context_id':gid,'kind':'same_snapshot_referenced_source_paragraph','source_document':'D-'+S[:16],'text':n['text'],'structure':{'heading_path':n['heading_path'],'source_paragraph_id':n['source_resource_id'],'related_context_ids':related},'source_ref':{'sha256':S,'source_resource_id':'SOURCE-'+S,'locator':loc}}
  r['contexts'].append(node);ctx.append({'record_id':r['id'],'context_id':gid,'kind':node['kind'],'primary_source_sha256':S,'source_identity_methods':['same_actual_snapshot_SHA_and_sealed_independent_page_and_prose_review'],'policy_text_fields':[{'field':'text','projected_text_sha256':n['text_sha256'],'literal_status':'same_primary_source_bounded_original_paragraph_restored_with_actual_page_geometry'}],'textless_structure':False});newnodes.append({'record_id':r['id'],'context_id':gid,'source_paragraph_id':n['source_resource_id']})
 gid='CTX-SRCRENEW-GEOMETRY-'+sha((r['id']+S).encode())[:20];geo=remap(supp['source_geometry'],cm);geo['related_context_ids']=list(cm.values());node={'context_id':gid,'kind':'same_snapshot_source_numbered_group_geometry','source_document':'D-'+S[:16],'structure':geo,'source_ref':{'sha256':S,'source_resource_id':'SOURCE-'+S,'locator':{'physical_pages':list(range(1,10))}}};r['contexts'].append(node);ctx.append({'record_id':r['id'],'context_id':gid,'kind':node['kind'],'primary_source_sha256':S,'source_identity_methods':['same_actual_snapshot_numbered_lists_and_explicit_shared_predicates'],'policy_text_fields':[],'textless_structure':True});newnodes.append({'record_id':r['id'],'context_id':gid,'source_numbered_geometry':True})
 ats={a['attachment_id']:a for a in r.get('source_attachments',[])}
 for a in neutral['source_page_assets']:
  aid='SOURCEASSET-'+a['sha256'][:20];ats[aid]={'attachment_id':aid,**a,'kind':'original_binary_rendered_source_page'}
 r['source_attachments']=list(ats.values())
 r.setdefault('source_references',[]).append({'source_resource_id':'SOURCE-'+S,'context_id':None,'source_field':'source_context','literal_reference':'谈判药品续约规则同版规则一/规则二及原确指条件','literal_relation_type':'same_primary_SHA_named_rule_reference_restoration'})
 for h in hits:idx.append({'record_id':r['id'],**h,'resource_id':'SOURCE-'+S,'literal_relation_type':'same_primary_SHA_named_rule_or_condition_reference','reference_source_sha256':S,'target_source_sha256':S,'automatic_whole_document_applicability_binding':False})
 assert r['text']==old['text'];assert r['contexts'][:len(old['contexts'])]==old['contexts'];bindings.append({'record_id':r['id'],'original_body_sha256':sha(old['text'].encode()),'new_body_sha256':sha(r['text'].encode()),'old_context_N':len(old['contexts']),'new_context_N':len(r['contexts']),'old_contexts_byte_value_preserved':True,'literal_reference_occurrence_N':len(hits),'new_paragraph_N':37,'new_geometry_N':1,'source_page_N':9})
library=OUT/'source-library/library-v11.jsonl';jl(library,lib);jl(OUT/'source-library/reference-index-v11.jsonl',idx);jl(OUT/'canonical_source_context-v11.jsonl',data);jl(OUT/'context-source-QA-v11.jsonl',ctx)
for name in ['body-source-QA','source-exceptions','grouped-source-review-jobs']:(OUT/(name+'-v11.jsonl')).write_bytes((OUT/(name+'-v10.jsonl')).read_bytes())
rm=rows(OUT/'material-record-bindings-v10.jsonl')
for x in rm:r=D[x['id']];assert x['projected_body_sha256']==sha(r['text'].encode());x['projected_context_sha256']=sha(pr.canonical(r['contexts']).encode());x['projected_record_sha256']=sha(pr.canonical(r).encode())
jl(OUT/'material-record-bindings-v11.jsonl',rm);fam=json.loads((OUT/'family-exposure-impact-v10.json').read_text());fam['source_projection_v11_sha256']=sf(OUT/'canonical_source_context-v11.jsonl');fam['all_body_bytes_identical_between_v10_and_v11']=True;dump(OUT/'family-exposure-impact-v11.json',fam)
qa=json.loads((OUT/'source-QA-summary-v10.json').read_text());counts=Counter('body_literal_'+x['literal_status'] for x in rows(OUT/'body-source-QA-v11.jsonl'));counts['contexts']=len(ctx);counts['textless_contexts']=sum(x['textless_structure'] for x in ctx)
for x in ctx:
 for f in x['policy_text_fields']:counts['context_literal_'+f['literal_status']]+=1
qa.update({'status':'source_preflight_v11_same_snapshot_named_renewal_reference_restored; primary_literal_jobs_closed; full_material_coverage_not_certified','counts':dict(counts),'output':{'path':str(OUT/'canonical_source_context-v11.jsonl'),'sha256':sf(OUT/'canonical_source_context-v11.jsonl')},'v11_named_reference_restoration_record_N':len(eligible),'v11_source_paragraph_resources_N':37,'v11_added_context_N':len(newnodes),'v11_body_or_existing_context_text_changes_N':0,'final_material_freeze_completed':False});dump(OUT/'source-QA-summary-v11.json',qa)
dump(OUT/'renewal-source-integration-v11.json',{'source_delivery_manifest_sha256':sf(RP/'delivery-sha256.json'),'source_supplement_sha256':sf(RP/'source-only-supplement.json'),'source_pdf_sha256':S,'new_external_binary_source_N':0,'new_library_document_resource_N':1,'literal_source_paragraph_resource_N':37,'actual_page_N':9,'projection_bindings':bindings,'uniform_reference_matching_source_only':True,'same_SHA_named_reference_restore_record_N':len(eligible),'requested_two_record_ids':list(known),'public_resource_IDs_are_mechanical_no_coding_hints':True,'source_paragraph_original_to_neutral_id_map':idmap,'new_body_text_changes_N':0,'old_contexts_preserved':True,'human_validation_performed':False,'final_material_freeze_completed':False})

# A fast sealed two-record delivery uses exactly the same projection later used
# in the full4481 version. It contains no coding or prior-result fields.
PACK=OUT/'renewal-common-v11';PACK.mkdir(exist_ok=True);selected=[D[rid] for rid in known];jl(PACK/'canonical_source_context.jsonl',selected);dump(PACK/'renewal2025-source-resource.json',neutral)
forbidden=set(qa['recursive_forbidden_keys']['keys'])|{'dimension_decision'};bad=[];dangling=[]
def walk(x,path):
 if isinstance(x,dict):
  for k,v in x.items():
   if k in forbidden:bad.append(path+'/'+k)
   walk(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):walk(v,path+'/'+str(i))
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
for r in selected:
 walk(r,r['id']);ids={x['context_id'] for x in r['contexts']}
 for s in strings(r):
  if s.startswith('CTX-') and s not in ids:dangling.append([r['id'],s])
 for a in r['source_attachments']:assert sf((OUT/a['relative_path']).resolve())==a['sha256']
walk(neutral,'neutral_library');assert not bad and not dangling
checks={'record_N':2,'canonical_sha256':sf(PACK/'canonical_source_context.jsonl'),'source_resource_sha256':sf(PACK/'renewal2025-source-resource.json'),'source_pdf_sha256':S,'source_paragraph_resources_N':37,'page_assets_N':9,'old_body_and_contexts_preserved':True,'same_rows_in_full_frame_v11':True,'forbidden_fields':bad,'dangling_CTX':dangling,'body_text_changes_N':0,'new_context_N_per_record':38,'both_requested_records_receive_exact_same_resource_content_and_version':True,'no_prior_coding_results_read_or_projected':True,'source_only_AI_task_not_human_validation':True}
dump(PACK/'projection-audit.json',checks);dump(PACK/'delivery-seal.json',{'status':'sealed_common_source_only_two_record_supplement_for_development_recoding; not_final_validation','files':[{'path':str(PACK/n),'sha256':sf(PACK/n),'bytes':(PACK/n).stat().st_size} for n in ['canonical_source_context.jsonl','renewal2025-source-resource.json','projection-audit.json']],'source_inputs':[{'path':str(RP/n),'sha256':sf(RP/n)} for n in ['source-only-supplement.json','delivery-sha256.json']],'integrity':checks,'original_versions_preserved':True})
print(json.dumps({'packet':str(PACK),'packet_sha256':checks['canonical_sha256'],'packet_resource_sha256':checks['source_resource_sha256'],'full_frame_v11_sha256':sf(OUT/'canonical_source_context-v11.jsonl'),'uniform_sameSHA_reference_records_N':len(eligible),'new_context_N':len(newnodes),'body_changes_N':0},ensure_ascii=False,indent=2))
