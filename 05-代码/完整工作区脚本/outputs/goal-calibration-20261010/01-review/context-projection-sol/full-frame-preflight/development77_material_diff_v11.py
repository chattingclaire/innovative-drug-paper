"""Compare only the two historical common source packets with current source."""
from pathlib import Path
import json,hashlib,copy,unicodedata
from collections import Counter
OUT=Path(__file__).resolve().parent;ROOT=OUT.parents[2]
H=lambda b:hashlib.sha256(b).hexdigest()
def sf(p):return H(p.read_bytes())
def rows(p):return [json.loads(x) for x in p.read_text().splitlines()]
def can(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jl(p,x):p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in x))
def fields(n):return {k:n[k] for k in ['text','title','headers','row_cells','caption'] if k in n}
def normalized(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace())
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
def basicstruct(x):
 if isinstance(x,dict):return {k:basicstruct(v) for k,v in x.items() if k not in ['source_resource_id','source_text_representation']}
 if isinstance(x,list):return [basicstruct(v) for v in x]
 return x
data=rows(OUT/'canonical_source_context-v11.jsonl');D={r['id']:r for r in data};lib=rows(OUT/'source-library/library-v11.jsonl');librarytext=normalized('\n'.join(strings(lib)));sourceinputs=[];report=[]
for batch,N in [('pilot02',41),('coverage01',36)]:
 packet=ROOT/f'04-calibration/{batch}/A/packet.jsonl';mapping=ROOT/f'04-calibration/{batch}/admin/private_mapping.json';mp=json.loads(mapping.read_text());m={x['blind_id']:x['frame_id'] for x in mp if x['coder']=='A'};old=rows(packet);assert len(old)==N;assert len(m)==N
 sourceinputs.extend([{'path':str(packet),'sha256':sf(packet),'purpose':'actual shared source-only packet, no coder labels read'}, {'path':str(mapping),'sha256':sf(mapping),'purpose':'only coder/blind_id/frame_id used to restore stable source IDs; no role or score used'}])
 # Independently verify that B received the identical material content by ID,
 # excluding only blind IDs and local asset directory locations.
 bp=ROOT/f'04-calibration/{batch}/B/packet.jsonl';bm={x['blind_id']:x['frame_id'] for x in mp if x['coder']=='B'};bd={bm[r['id']]:{k:v for k,v in r.items() if k!='id'} for r in rows(bp)}
 for o in old:
  rid=m[o['id']];assert {k:v for k,v in o.items() if k!='id'}==bd[rid];n=D[rid];oc={x['context_id']:x for x in o['contexts']};nc={x['context_id']:x for x in n['contexts']};common=set(oc)&set(nc);newids=sorted(set(nc)-set(oc));missing=sorted(set(oc)-set(nc));textdiff=[];identity=[];structure=[];pagechanges=[]
  for cid in sorted(common):
   if fields(oc[cid])!=fields(nc[cid]):textdiff.append({'context_id':cid,'old_fields':fields(oc[cid]),'new_fields':fields(nc[cid]),'old_text_fields_sha256':H(can(fields(oc[cid])).encode()),'new_text_fields_sha256':H(can(fields(nc[cid])).encode())})
   oldref=oc[cid].get('source_ref',{});newref=nc[cid].get('source_ref',{})
   if oldref.get('sha256')!=newref.get('sha256'):identity.append({'context_id':cid,'old_source_sha256':oldref.get('sha256'),'new_source_sha256':newref.get('sha256')})
   if basicstruct(oc[cid].get('structure',{}))!=basicstruct(nc[cid].get('structure',{})):structure.append(cid)
   if basicstruct(oldref.get('locator'))!=basicstruct(newref.get('locator')):pagechanges.append(cid)
  absent=[]
  for cid in missing:
   t='\n'.join(strings(fields(oc[cid])));nt=normalized(t);inrow=any(nt and nt in normalized('\n'.join(strings(fields(x)))) for x in n['contexts']);inlib=bool(nt and nt in librarytext);absent.append({'old_context_id':cid,'old_kind':oc[cid].get('kind'),'old_text_fields_sha256':H(can(fields(oc[cid])).encode()),'original_old_context':oc[cid],'same_literal_text_in_new_row':inrow,'same_literal_text_in_current_library':inlib,'textless_old_node':not bool(t),'status':'old extra context not represented by same context ID; source content availability audited separately'})
  oldassets=o.get('source_page_attachments',[]);newassets=n.get('source_attachments',[]);newassetset={a['sha256'] for a in newassets};oldassetset={a['sha256'] for a in oldassets};newkinds=Counter(nc[c]['kind'] for c in newids)
  substantive=bool(textdiff or o['text']!=n['text'] or any(nc[c]['kind'] in ['same_snapshot_referenced_source_paragraph','same_edition_explicitly_cited_source_paragraph'] for c in newids) or any(not a['same_literal_text_in_new_row'] and not a['same_literal_text_in_current_library'] and not a['textless_old_node'] for a in absent))
  geometry=bool(structure or any(nc[c]['kind'] in ['source_formula_geometry','source_graph_or_table_geometry','same_snapshot_source_numbered_group_geometry','source_table_row_geometry','source_table_group'] for c in newids))
  rec={'id':rid,'batch':batch,'old_packet_blind_id':o['id'],'old_packet_source_sha256':sf(packet),'current_canonical_sha256':sf(OUT/'canonical_source_context-v11.jsonl'),'old_body_sha256':H(o['text'].encode()),'new_body_sha256':H(n['text'].encode()),'body_text_changed':o['text']!=n['text'],'old_context_N':len(oc),'current_context_N':len(nc),'same_context_ID_N':len(common),'existing_context_text_change_N':len(textdiff),'existing_context_text_changes':textdiff,'context_primary_identity_change_N':len(identity),'context_primary_identity_changes':identity,'existing_context_structure_change_N':len(structure),'existing_context_structure_changed_ids':structure,'existing_context_locator_change_N':len(pagechanges),'existing_context_locator_changed_ids':pagechanges,'new_context_N':len(newids),'new_context_kind_N':dict(newkinds),'new_context_ids':newids,'old_extra_context_ID_absent_N':len(missing),'old_extra_context_availability':absent,'new_row_explicit_source_reference_N':len(n.get('source_references',[])),'current_explicit_source_references':n.get('source_references',[]),'new_asset_SHA_N':len(newassetset-oldassetset),'old_asset_SHA_absent_in_new_row_N':len(oldassetset-newassetset),'old_absent_asset_SHAs':sorted(oldassetset-newassetset),'material_content_or_reference_text_change':substantive,'material_source_geometry_change':geometry,'coding_label_impact_assessed':False,'recommended_source_review_bucket':'changed_source_text_or_reference_content' if substantive else 'source_geometry_or_scope_changed' if geometry else 'source_locator_registry_or_asset_packaging_only'}
  report.append(rec)
assert len(report)==77 and len({x['id'] for x in report})==77
jl(OUT/'development77-material-impact-v11.jsonl',report)
summary={'status':'source_content_impact_only; no coding result read; not blanket_recoding_decision','current_canonical_sha256':sf(OUT/'canonical_source_context-v11.jsonl'),'old_common_packets_confirmed_A_B_equal_by_stable_source_ID':True,'input_files':sourceinputs,'development_ID_N':77,'batch_N':dict(Counter(x['batch'] for x in report)),'body_text_changed_N':sum(x['body_text_changed'] for x in report),'body_text_changed_ids':[x['id'] for x in report if x['body_text_changed']],'existing_context_text_changed_record_N':sum(x['existing_context_text_change_N']>0 for x in report),'existing_context_text_changed_ids':[x['id'] for x in report if x['existing_context_text_change_N']>0],'new_context_record_N':sum(x['new_context_N']>0 for x in report),'new_reference_paragraph_record_N':sum(any(k in x['new_context_kind_N'] for k in ['same_snapshot_referenced_source_paragraph','same_edition_explicitly_cited_source_paragraph']) for x in report),'source_review_buckets':{k:[x['id'] for x in report if x['recommended_source_review_bucket']==k] for k in sorted({x['recommended_source_review_bucket'] for x in report})},'old_extra_context_ID_absent_record_N':sum(x['old_extra_context_ID_absent_N']>0 for x in report),'label_effect_not_inferred_from_source_change':True,'two_requested_renewal_records_in_current_source':[x['id'] for x in report if x['id'] in ['RECODE25-00900','RECODE25-00902']],'remaining_holdout_not_read_or_sampled_for_coding':True}
dump(OUT/'development77-material-impact-summary-v11.json',summary)
md='77条开发材料来源变化（v11）\n\n仅比较真实共同材料，无任何编码结果。原41条采用pilot02 A纯来源packet；36条采用coverage01 A纯来源packet，按private_mapping中的稳定ID恢复；B材料逐ID一致已复核。\n\n'+f"正文变化{summary['body_text_changed_N']}条；既有CTX文字变化{summary['existing_context_text_changed_record_N']}条；新增确指原文段落{summary['new_reference_paragraph_record_N']}条。原CTX中的source_resource_id补齐、页图包装变化与原文内容变化分开列出。\n\n"+'| 来源变化范围 | ID数 | 稳定ID |\n|---|---:|---|\n'+''.join('|'+k+'|'+str(len(ids))+'|'+', '.join(ids)+'|\n' for k,ids in summary['source_review_buckets'].items())+'\n旧共同包中额外SUPP等CTX若不在当前逐行CTX，逐条报告旧SHA/原节点，并核同文字在当前行或公共来源库的可读性；不把新CTX数量直接当作语义变化量，也不从字段包装变化推导需全框重判。详细逐ID和逐节点证据见development77-material-impact-v11.jsonl。\n'
(OUT/'development77-material-impact-v11.md').write_text(md)
print(json.dumps({k:v for k,v in summary.items() if k not in ['input_files','source_review_buckets']},ensure_ascii=False,indent=2));print(json.dumps(summary['source_review_buckets'],ensure_ascii=False,indent=2))
