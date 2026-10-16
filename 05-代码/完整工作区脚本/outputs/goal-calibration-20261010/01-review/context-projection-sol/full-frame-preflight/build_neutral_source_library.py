"""Two neutral document resources + literal references, without coder labels."""
from pathlib import Path
import json,hashlib,re,unicodedata,importlib.util
from collections import Counter
OUT=Path(__file__).resolve().parent/'source-library';ROOT=OUT.parents[3]
def sha(b):return hashlib.sha256(b).hexdigest()
def sf(p):return sha(Path(p).read_bytes())
def save(p,b):
 if isinstance(b,str):b=b.encode()
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
 if p.exists():assert p.read_bytes()==b
 else:p.write_bytes(b)
def norm(s):return ''.join(c for c in unicodedata.normalize('NFKC',s) if not c.isspace())
def jl(p,rows):save(p,''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
supppath=OUT.parent.parent/'prospective-common-supplements-source-only-v3.jsonl';sups=[json.loads(x) for x in supppath.read_text().splitlines()];a=sups[0]
txt=Path(a['source_snapshot']);assert sf(txt)==a['source_sha256'];dest=OUT/'snapshots'/('SOURCE-'+a['source_sha256']+'.txt');save(dest,txt.read_bytes())
nmpa={'source_resource_id':'SOURCE-NMPA-2024-PILOT-21','document_title':a['source_title'],'document_number':a['document_number'],'document_year':2024,'document_date':a['document_date'],'document_kind':'normative_work_plan','original_url':a['original_url'],'republication_url':a['source_url'],'republication_date':a['republication_date'],'snapshot_sha256':sf(dest),'snapshot_relative_path':str(dest.relative_to(OUT)),'snapshot_mime_type':'text/plain','original_online_binary_authenticated':False,'source_texts':[{'source_locator':a['locator'],'text':a['text'],'text_sha256':a['text_sha256']}],'authority_identity':'NMPA plan officially republished by Shanghai MPA; archived derived UTF8 text bytes verified'}
nhcp=ROOT/'02-methods/source-supplements/NHC-2024-policy-explainer-paragraphs.json';d=json.loads(nhcp.read_text());src=Path(d['binary_snapshot']);assert sf(src)==d['binary_sha256'];dest=OUT/'snapshots'/('SOURCE-'+d['binary_sha256']+'.html');save(dest,src.read_bytes());b=sups[-1]
nhc={'source_resource_id':'SOURCE-NHC-2024-EXPLAINER-38','document_title':d['source_title'],'document_kind':'official_policy_explainer','explained_policy_title':'关于改革完善基层药品联动管理机制 扩大基层药品种类的意见','explained_policy_document_number':b['policy_document_number'],'explained_policy_document_date':b['policy_document_date'],'document_year':2024,'source_publication_date':d['original_date'],'original_url':d['original_url'],'republication_url':d['republication_url'],'republication_datetime':b['republication_datetime'],'snapshot_sha256':sf(dest),'snapshot_relative_path':str(dest.relative_to(OUT)),'snapshot_mime_type':'text/html','original_online_binary_authenticated':False,'republication_binary_HTTP200_retrieval_and_SHA_checked':True,'source_texts':[{'source_locator':{'local_paragraph_id':p['paragraph_id'],'paragraph_index_1based':i},'text':p['text'],'text_sha256':sha(p['text'].encode())} for i,p in enumerate(d['paragraphs'],1)],'authority_identity':'NHC official explainer, full text in official Shanxi Health Commission repost; original date and repost date separated'}
spec=importlib.util.spec_from_file_location('pure_source_primitives',OUT.parent.parent/'build_projection.py');pr=importlib.util.module_from_spec(spec);spec.loader.exec_module(pr);ht,method=pr.extract_snapshot_text(dest)
assert all(norm(p['text']) in norm(ht) for p in d['paragraphs'])
resources=[nmpa,nhc];jl(OUT/'library.jsonl',resources)
framepath=ROOT/'00-baseline/source-only-frame.jsonl';frames={r['id']:r for r in map(json.loads,framepath.read_text().splitlines())};mpath=ROOT/'00-baseline/source-files/f4da9adad83e91ba-source_only_with_scope04.jsonl';models=[r for r in map(json.loads,mpath.read_text().splitlines()) if r['id'] in frames];assert len(models)==4481
patterns=[(nmpa['source_resource_id'],'exact_title',r'优化创新药临床试验审评审批试点工作方案'),(nmpa['source_resource_id'],'exact_document_number',r'国药监药注[〔\[（(]2024[〕\]）)]\s*21\s*号'),(nmpa['source_resource_id'],'ambiguous_literal_candidate',r'优化创新药临床试验审评审批(?:改革)?试点'),(nhc['source_resource_id'],'exact_title',r'关于改革完善基层药品联动管理机制\s*扩大基层药品种类的意见'),(nhc['source_resource_id'],'exact_document_number',r'国卫药政发[〔\[（(]2024[〕\]）)]\s*38\s*号')]
index=[]
for r in models:
 fields=[(None,'text',r['text'])]
 for n in r['contexts']:
  for f,t in pr.text_values(n):fields.append((n['context_id'],f,t))
 for cid,f,t in fields:
  for sr,kind,pattern in patterns:
   for m in re.finditer(pattern,t):
    index.append({'record_id':r['id'],'context_id':cid,'source_field':f,'source_field_text_sha256':sha(t.encode()),'resource_id':sr,'literal_relation_type':kind,'literal_reference':m.group(),'character_range_0based_halfopen':[m.start(),m.end()],'unit_primary_source_sha256':frames[r['id']]['source_position']['unit_source_sha256_recorded'],'source_document_stem':frames[r['id']]['source_document_stem'],'context_year_literals':[m.group() for m in re.finditer(r'(?:19|20)\d{2}年',t)],'automatic_whole_document_applicability_binding':False})
jl(OUT/'reference-index.jsonl',index)
audit={'status':'two_complete_neutral_sources_sealed; literal_reference_candidates_indexed_without_semantic_applicability','resource_N':2,'NMPA_full_plan_source_texts_N':1,'NHC_full_explainer_paragraph_N':len(d['paragraphs']),'indexed_target_record_N':4481,'literal_reference_occurrence_N':len(index),'unique_record_with_literal_reference_N':len({x['record_id'] for x in index}),'occurrence_types':dict(Counter(x['literal_relation_type'] for x in index)),'source_library_body_word_or_character_spans_reverified':True,'dimension_judgment':False,'new_machine_inference':False,'coder_outputs_read':False,'unit_contexts_augmented_automatically':False,'old_development_supplement_IDs_used_as_binding_rules':False,'input_files':[{'path':str(p),'sha256':sf(p)} for p in [supppath,nhcp,framepath,mpath]],'outputs':[{'path':str(p),'sha256':sf(p)} for p in [OUT/'library.jsonl',OUT/'reference-index.jsonl']], 'limits':['Exact title or document number is a literal reference candidate and does not establish whether every clause of the referred document applies to the current unit.','2025 documents recalling2024 pilot activity do not establish current wholesale applicability of the2024 plan. The source year and text year literals remain visible.','Ordinary policy purpose or topic similarity is not indexed as a definite reference.','The full neutral sources are separate library resources; the material protocol determines consistent source retrieval before future coding.','Source-only review is not a five-dimension development judgment and does not certify that final human coders have never seen these texts.','Local archived byte hashes and official repost relationships are verified; no NMPA original HTML download or original NHC server binary authentication is claimed.']}
save(OUT/'audit.json',json.dumps(audit,ensure_ascii=False,indent=2)+'\n');save(OUT/'README.md','两份完整中性来源库与逐字段字面引用候选索引。library.jsonl不含开发41 ID或规则提示；reference-index.jsonl扫描全4481及实际来源字段，仅索引原文标题、文号和试点措辞，不决定全文件适用、不添加五维标签。2025回顾2024不是2024所有条件当期适用的证明。完整方案/完整解读通过统一事前材料检索协议提供，不能仅依某开发ID曾补材。快照SHA、原始/转载日期和原件认证范围见audit.json。\n')
print(json.dumps({k:audit[k] for k in ['resource_N','NHC_full_explainer_paragraph_N','literal_reference_occurrence_N','unique_record_with_literal_reference_N','occurrence_types']},ensure_ascii=False,indent=2))
