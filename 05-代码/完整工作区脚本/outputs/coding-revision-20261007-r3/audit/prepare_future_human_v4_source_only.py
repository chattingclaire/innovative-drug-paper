"""Update blank future-human v3 to v12 contexts, never changing its sample."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import copy,csv,hashlib,json,shutil
B=Path(__file__).resolve().parents[1];ROOT=B.parents[1];OLD=B/'future-human-validation-v3';OUT=B/'future-human-validation-v4';ADMIN=B/'admin'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def obj(p):return json.loads(Path(p).read_text())
assert not OUT.exists(),'Never overwrite v4'
prior_hashes={str(p.relative_to(ROOT)):sha(p)for p in sorted(OLD.rglob('*'))if p.is_file()};old_private=ADMIN/'future_human_v3_sampling_PRIVATE.json';prior_private_hash=sha(old_private);s=obj(old_private);assert s['execution_status']=='not_started_no_real_human_labels'
full={x['id']:x for x in map(json.loads,(B/'effective_blind_inputs_v12.jsonl').read_text().splitlines())};source_hashes={str(p.relative_to(ROOT)):sha(p)for p in[B/'effective_blind_inputs_v12.jsonl',B/'rule_inputs_shared_v12.jsonl',B/'material_v12_manifest.json']}
OUT.mkdir();shutil.copytree(OLD/'手册',OUT/'手册');mapping=[];changed={};maxctx=0;sample_ids={x['original_id']for x in s['sample']}
for coder in['A','C']:
 package=obj(OLD/f'真人{coder}-无答案材料.json');lookup={x['blind_id']:x['original_id']for x in s['mapping']if x['coder']==coder};prior_csv=list(csv.DictReader((OLD/f'真人{coder}-空白编码表.csv').open(encoding='utf-8-sig',newline='')));headers=list(prior_csv[0]);oldrows=copy.deepcopy(package['rows']);changes=[]
 assert len(oldrows)==len(lookup)==len(prior_csv)==240
 for n,(r,oldrow,csvrow)in enumerate(zip(package['rows'],oldrows,prior_csv),1):
  orig=lookup[oldrow['id']];current=full[orig];assert r['text']==current['text'];assert r['source_title']==current['source_title']and r['pages']==current['pages'];assert all(v==''for v in r['coding'].values());assert all(package[k]==''for k in['coder_name','professional_background','execution_date'])
  r['id']=f'HV4-{coder}-{n:04d}';r['contexts']=copy.deepcopy(current['contexts']);r['context_usage']=current['context_usage'];mapping.append({'coder':coder,'blind_id':r['id'],'original_id':orig,'v3_blind_id':oldrow['id']});maxctx=max(maxctx,len(json.dumps(r['contexts'],ensure_ascii=False)))
  if r['contexts']!=oldrow['contexts']:changes.append({'blind_id':r['id'],'original_id':orig})
 package.update(package_version='v4',material_version='v12',source_material_sha256=sha(B/'effective_blind_inputs_v12.jsonl'));dump(OUT/f'真人{coder}-无答案材料.json',package)
 with(OUT/f'真人{coder}-空白编码表.csv').open('w',encoding='utf-8-sig',newline='')as f:
  w=csv.DictWriter(f,fieldnames=headers);w.writeheader()
  for r in package['rows']:w.writerow({'匿名编号':r['id'],'政策原文':r['text'],'来源标题':r['source_title'],'页码':json.dumps(r['pages'],ensure_ascii=False),'完整语境JSON':json.dumps(r['contexts'],ensure_ascii=False),**r['coding']})
 assert {x['original_id']for x in changes}=={'RECODE25-03822'};changed[coder]=changes
assert maxctx<32767
readme=(OLD/'使用说明.md').read_text().replace('v3','v4').replace('v11','v12')
readme=readme.replace('旧v2、旧私有设计、任何既有标签及冻结v12文件均保留原字节。','旧v2和v3、旧私有设计、任何既有标签，以及冻结v11和v12文件均保留原字节。')
readme+='\n本v4沿用v3的同240条实际样本、抽样概率π、分析权重、A/C分别的条目顺序和全部空白身份/答题字段。本次相对v3仅每位1条语境更新为v12的确切所引条件；其余239条语境保持原样。旧v3完整保留，不覆盖或补写任何旧材料。\n'
(OUT/'使用说明.md').write_text(readme)
created=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat();admin=copy.deepcopy(s);admin.update(created_at=created,package_version='v4',material_version='v12',mapping=[{k:v for k,v in x.items()if k!='v3_blind_id'}for x in mapping],prior_v3_mapping=copy.deepcopy(s['mapping']),v3_to_v4_blind_mapping=mapping,previous_v3_files_sha256=prior_hashes,previous_v3_sampling_private_sha256=prior_private_hash,source_material_sha256=source_hashes);admin['source_update_scope']='v3 frozen240 sample, probabilities, weights and order unchanged; only exact v12 contexts, one actual unit03822 changed. All response fields remain blank.'
dump(ADMIN/'future_human_v4_sampling_PRIVATE.json',admin)
manual_hashes={str(p.relative_to(OUT)):sha(p)for p in(OUT/'手册').iterdir()};files={str(p.relative_to(OUT)):sha(p)for p in sorted(OUT.rglob('*'))if p.is_file()}
manifest={'package_version':'v4','material_version':'v12','execution_status':'not_started_no_real_human_labels','source_only':True,'sample_design_version':'future-human-v2-frozen-sample','actual_sample_n':240,'coder_row_counts':{'A':240,'C':240},'department_sample_counts':{'NMPA':80,'NHSA':80,'NHC':80},'resampled':False,'sampling_design_changed':False,'sample_weights_changed':False,'sample_order_changed':False,'original_text_changes':0,'original_source_title_or_page_changes':0,'context_changed_counts':{c:len(v)for c,v in changed.items()},'context_changed_blind_ids':{c:[x['blind_id']for x in v]for c,v in changed.items()},'all_contexts_equal_exact_frozen_v12':True,'two_coders_symmetric_actual_sample':True,'all_identity_coding_reason_evidence_fields_blank':True,'maximum_complete_context_json_characters':maxctx,'context_truncated':False,'manual_versions':'v1.3 + operational v1.4','manual_hashes':manual_hashes,'source_v12_hashes':source_hashes,'preserved_v3_file_hashes':prior_hashes,'preserved_v3_sampling_private_sha256':prior_private_hash,'independence_scope':'Current-unit normalized text families excluded against known development/training. Historical49-full-document context exposure disclosed; not new-document external validation.','public_file_hashes':files}
dump(OUT/'source_update_manifest.json',manifest)
append={'created_at':created,'execution_status':'not_started_no_real_human_labels','previous_v3_design_mapping_and_blank_material_unchanged':True,'v3_file_hashes_before_and_after':prior_hashes,'v3_private_hash_before_and_after':prior_private_hash,'v12_hashes_before_and_after':source_hashes,'v4_public_file_hashes':{str(p.relative_to(OUT)):sha(p)for p in sorted(OUT.rglob('*'))if p.is_file()},'v4_private_mapping_sha256':sha(ADMIN/'future_human_v4_sampling_PRIVATE.json'),'unit_text_changes':0,'sample_design_changes':0,'resampled':False,'weight_changes':0,'order_changes':0,'labels_or_predictions_read':False}
dump(ADMIN/'future_human_v4_appendfreeze_PRIVATE.json',append)
assert all(sha(ROOT/p)==h for p,h in prior_hashes.items());assert sha(old_private)==prior_private_hash;assert all(sha(ROOT/p)==h for p,h in source_hashes.items())
print(json.dumps({'n':240,'contexts_changed_each':1,'max_context_chars':maxctx,'private_mapping_n':len(mapping)},ensure_ascii=False))
