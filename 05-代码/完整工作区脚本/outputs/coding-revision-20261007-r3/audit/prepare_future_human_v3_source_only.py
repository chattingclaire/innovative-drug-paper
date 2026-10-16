"""Prepare blank future real-human material, preserving the frozen v2 sample.

Reads no reference answer, new confirmation or machine prediction. Old v2 and
v11 material are immutable. Only contexts are updated to frozen v11; new blind
IDs and blank response fields are packaging, not new sampling.
"""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import copy,csv,hashlib,json,shutil
ROOT=Path(__file__).resolve().parents[3]
R3=ROOT/'outputs/coding-revision-20261007-r3';R2=ROOT/'outputs/agent-validation-20261007-r2'
OLD=R2/'future-human-validation-v2';PRIVATE=R2/'admin/future_human_v2_sampling_PRIVATE.json';OUT=R3/'future-human-validation-v3';ADMIN=R3/'admin'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def jl(p):return [json.loads(s)for s in Path(p).read_text().splitlines()if s.strip()]
assert not OUT.exists(),'Never overwrite an existing v3 release'
old_hashes={str(p.relative_to(ROOT)):sha(p)for p in sorted(OLD.iterdir())if p.is_file()};old_private_hash=sha(PRIVATE)
v11ll=R3/'effective_blind_inputs_v11.jsonl';v11rr=R3/'rule_inputs_shared_v11.jsonl';v11manifest=R3/'material_v11_manifest.json';full_hashes={str(p.relative_to(ROOT)):sha(p)for p in[v11ll,v11rr,v11manifest]}
sampling=json.loads(PRIVATE.read_text());full={x['id']:x for x in jl(v11ll)};sample=copy.deepcopy(sampling['sample']);sample_ids={x['original_id']for x in sample}
assert len(sample)==len(sample_ids)==240 and sample_ids<=full.keys()
assert sampling['execution_status']=='not_started_no_real_human_labels'
assert len(sampling['mapping'])==480
OUT.mkdir();(OUT/'手册').mkdir();ADMIN.mkdir(exist_ok=True)
manual_hashes={}
for fn in['完整五维手册-v1.3.md','共用操作说明-v1.4.md']:
 src=R3/'protocol'/fn;dst=OUT/'手册'/fn;shutil.copyfile(src,dst);manual_hashes[str(dst.relative_to(OUT))]=sha(dst)
answer_fields=['编码员姓名','专业经历','实施日期','S','E','Ec','I','F','S理由','E理由','Ec理由','I理由','F理由','S证据','E证据','Ec证据','I证据','F证据','逐字证据','I来源类型','F来源类型','判定状态','问题说明']
headers=['匿名编号','政策原文','来源标题','页码','完整语境JSON']+answer_fields
mapping=[];changed_by_coder={};unchanged_by_coder={};max_context=0
for coder in['A','C']:
 old=json.loads((OLD/f'真人{coder}-无答案材料.json').read_text());old_map={m['blind_id']:m['original_id']for m in sampling['mapping']if m['coder']==coder};rows=[];changed=[];unchanged=[]
 assert len(old['rows'])==len(old_map)==240
 for n,row in enumerate(old['rows'],1):
  orig=old_map[row['id']];bound=full[orig];assert row['text']==bound['text'];assert row['source_title']==bound['source_title'];assert row['pages']==bound['pages']
  blind=f'HV3-{coder}-{n:04d}';r=copy.deepcopy(row);r['id']=blind;r['contexts']=copy.deepcopy(bound['contexts']);r['context_usage']=bound['context_usage'];r['coding']={k:''for k in answer_fields}
  assert 'RECODE25-'not in json.dumps(r['contexts'],ensure_ascii=False)
  rows.append(r);mapping.append({'coder':coder,'blind_id':blind,'original_id':orig,'v2_blind_id':row['id']})
  (changed if row['contexts']!=bound['contexts']else unchanged).append(blind);max_context=max(max_context,len(json.dumps(r['contexts'],ensure_ascii=False)))
 package={'status':'blank_for_future_real_human_execution','execution_status':'not_started_no_real_human_labels','package_version':'v3','material_version':'v11','coder_name':'','professional_background':'','execution_date':'','manual_version':'v1.3 + operational v1.4','sample_design_version':'future-human-v2-frozen-sample','source_material_sha256':sha(v11ll),'rows':rows}
 dump(OUT/f'真人{coder}-无答案材料.json',package)
 with(OUT/f'真人{coder}-空白编码表.csv').open('w',encoding='utf-8-sig',newline='')as f:
  writer=csv.DictWriter(f,fieldnames=headers);writer.writeheader()
  for r in rows:writer.writerow({'匿名编号':r['id'],'政策原文':r['text'],'来源标题':r['source_title'],'页码':json.dumps(r['pages'],ensure_ascii=False),'完整语境JSON':json.dumps(r['contexts'],ensure_ascii=False),**r['coding']})
 changed_by_coder[coder]=changed;unchanged_by_coder[coder]=unchanged
assert max_context<32767
instructions='''# 未来真人正式执行空白材料 v3（尚未执行）

本目录供未来两名真人分别独立编码，每人240条。A/C的实际样本相同，沿用v2的抽样、顺序、部门分层、正文族和权重，仅更新为冻结v11的全部共享语境，并使用HV3匿名编号。所有政策原句保持不变。编码员姓名、专业经历、实施日期、五维标签、各维理由、逐字证据、来源类型及问题说明全部留空，须由实际执行者填写。本包没有答案，也不代表已完成人工编码或获得真人信度结论；现有agent培训和确认不得冒充真人完成。

附有完整五维手册v1.3及共用操作说明v1.4，文件与本轮冻结手册字节相同。正式执行前完成培训；两位编码员不得共享答案或查看机器输出。双方先独立完成并封存原始提交，再计算协商前信度，之后才进行人工裁决。遇到缺字、对象、父条件或必要后项不足，应记录材料问题，不得猜0。语境用于消解对象、条件和明确回指，不能把后项维度复制到当前原句。

JSON为完整无损材料，每条包含完整原句、来源标题、页码和v11完整contexts；每行coding字段均为空。CSV使用UTF-8 BOM，可用表格软件打开，包含相同的完整语境JSON及空白编码栏，未截断长语境。最长语境JSON为24,032字符，低于Excel单元格32,767字符限制；如查看工具显示不全，请打开对应JSON，勿凭显示截取判断缺材。A/C材料须分别发给对应执行者；私有映射及抽样权重封存在admin，不向正式编码员提供。

本设计保持v2不变：先排除已知历史开发单位、当前300条培训单位及其规范化正文族，再按部门在剩余独特正文族中各随机抽80族，每族随机抽1条，共240条。规范化为NFKC后删除全部空白与Unicode标点；跨部门共享正文族整体排除。可用正文族为药监1031、医保841、卫健140族。本设计是部门分层的两阶段抽样（先正文族、后单位），不是普通单位简单随机抽样，v3没有重抽或调整权重。

独立性边界是当前单位正文族相对于已开发和培训正文族的排除。历史记录显示，历史版未来材料涉及的49个全文曾在培训上下文中出现；不能宣称所有来源全文均未见，也不能称新文档外部验证。本包只能支持该剩余正文族抽样框内的未来真人核验，不代表被排除正文族、全部政策总体或新政策文件。

旧v2、旧私有设计、任何既有标签及冻结v11文件均保留原字节。本v3为尚未执行的source-only材料更新；任何后续真人提交应另存，不能回填覆盖本空白包。
'''
(OUT/'使用说明.md').write_text(instructions)
created=datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()
admin=copy.deepcopy(sampling);admin.update(created_at=created,execution_status='not_started_no_real_human_labels',package_version='v3',material_version='v11',sample=sample,mapping=[{k:v for k,v in m.items()if k!='v2_blind_id'}for m in mapping]);admin['prior_v2_mapping']=copy.deepcopy(sampling['mapping']);admin['v2_to_v3_blind_mapping']=copy.deepcopy(mapping);admin['previous_v2_files_sha256']=old_hashes;admin['previous_v2_sampling_private_sha256']=old_private_hash;admin['source_material_sha256']=full_hashes;admin['source_update_scope']='Only contexts replaced by exact frozen v11 contexts; original text/sample/design/weights unchanged. New anonymous IDs and blank response fields only.';admin['historical_full_document_exposure_note']='Historical future package had49 full documents appearing in training context; no claim that all original documents are unseen or that this is new-document external validation.'
dump(ADMIN/'future_human_v3_sampling_PRIVATE.json',admin)
for p,h in old_hashes.items():assert sha(ROOT/p)==h
assert sha(PRIVATE)==old_private_hash
for p,h in full_hashes.items():assert sha(ROOT/p)==h
public_files={str(p.relative_to(OUT)):sha(p)for p in sorted(OUT.rglob('*'))if p.is_file()}
manifest={'package_version':'v3','material_version':'v11','execution_status':'not_started_no_real_human_labels','source_only':True,'sample_design_version':'future-human-v2-frozen-sample','actual_sample_n':240,'coder_row_counts':{'A':240,'C':240},'department_sample_counts':{'NMPA':80,'NHSA':80,'NHC':80},'resampled':False,'sampling_design_changed':False,'sample_weights_changed':False,'original_text_changes':0,'original_source_title_or_page_changes':0,'context_changed_counts':{c:len(x)for c,x in changed_by_coder.items()},'context_changed_blind_ids':changed_by_coder,'all_contexts_equal_exact_frozen_v11':True,'two_coders_symmetric_actual_sample':True,'all_identity_coding_reason_evidence_fields_blank':True,'maximum_complete_context_json_characters':max_context,'context_truncated':False,'manual_versions':'v1.3 + operational v1.4','manual_hashes':manual_hashes,'source_v11_hashes':full_hashes,'preserved_v2_file_hashes':old_hashes,'preserved_v2_sampling_private_sha256':old_private_hash,'independence_scope':'Unit normalized-text families excluded against known development/training; not unseen original-document or new-document external validation. Historical49-document context exposure explicitly disclosed.','public_file_hashes':public_files}
dump(OUT/'source_update_manifest.json',manifest)
appendfreeze={'created_at':created,'execution_status':'not_started_no_real_human_labels','previous_v2_design_and_mapping_unchanged':True,'v2_file_hashes_before_and_after':old_hashes,'v2_private_hash_before_and_after':old_private_hash,'v11_hashes_before_and_after':full_hashes,'v3_public_file_hashes':{str(p.relative_to(OUT)):sha(p)for p in sorted(OUT.rglob('*'))if p.is_file()},'v3_private_mapping_sha256':sha(ADMIN/'future_human_v3_sampling_PRIVATE.json'),'unit_text_changes':0,'sample_design_changes':0,'resampled':False,'weight_changes':0,'labels_or_predictions_read':False}
dump(ADMIN/'future_human_v3_appendfreeze_PRIVATE.json',appendfreeze)
print(json.dumps({'n':240,'contexts_changed_each_coder':len(changed_by_coder['A']),'max_context_chars':max_context,'public_files':list(public_files),'v3_private_mapping_n':len(mapping)},ensure_ascii=False))
