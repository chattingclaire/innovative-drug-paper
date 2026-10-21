#!/usr/bin/env python3
"""Read-only structural recheck. Never output unit text, row labels, or scores."""
import csv, datetime as dt, hashlib, io, json
from collections import Counter
from pathlib import Path
ROOT=Path('/PROJECT_ROOT')
ARCHIVE=Path('/LOCAL_HOME/Desktop/战略院/创新药论文-完整归档-20260914')
OUT=Path(__file__).parent
NOW=dt.datetime.now(dt.timezone.utc).isoformat()
DIMS=('S','E','Ec','I','F')
def sha(b):return hashlib.sha256(b).hexdigest()
def meta(p):
    b=p.read_bytes(); st=p.stat()
    return {'path':str(p),'bytes':len(b),'sha256':sha(b),'mtime_utc':dt.datetime.fromtimestamp(st.st_mtime,dt.timezone.utc).isoformat()}
def dump(p,o):p.write_text(json.dumps(o,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
BASE={'使用说明.md':'594c00764acb26bf16b7b08f0474040b42b7f3884595f1c5030762e43d6f2f90','手册/共用操作说明-v1.4.md':'1b894ea4b6a7e7c06f04a9cbc38d8eaa7c9f28ffe536e839c7a48e0183fc27ee','手册/完整五维手册-v1.3.md':'75ff8ebda018a15e008bc1075892000fb9c9c053943d05f04bbe193176c605a6','真人A-无答案材料.json':'3282fb4dbca3509fbf0f492d36515861d4ae0d9ff5b625bfe896a3db334cac87','真人A-空白编码表.csv':'78a034b4ca9123bd55899ce74718cb15f2deb71ecf58469bd5260f47b27983dc','真人C-无答案材料.json':'ab704417350d8b191090130a2a76b84c35fc33b119b77b52c003589293a370d1','真人C-空白编码表.csv':'548fbf810a268ddf367b169f71ccf5a3ed66ceb990b9aa596630bff8182cdb06','source_update_manifest.json':'66c99f9b7e9877e7712281ed15ddeebc685f0d95b433d1adf6caf8d646ae9e5f'}
v5=ROOT/'outputs/coding-revision-20261007-r3/future-human-validation-v5'
sampling_p=ROOT/'outputs/coding-revision-20261007-r3/admin/future_human_v5_sampling_PRIVATE.json'
sampling=json.loads(sampling_p.read_bytes())
public=[]
for relative,expected in BASE.items():
    p=v5/relative; m=meta(p); m['prior_registered_sha256']=expected; m['bytes_identical_to_prior_registered_file']=m['sha256']==expected; public.append(m)

def cat(value):
    if value is None or (isinstance(value,str) and not value.strip()):return 'blank'
    if type(value) is int and value==0:return 'zero'
    if type(value) is int and value==1:return 'one'
    if isinstance(value,str):
        v=value.strip()
        if v=='0':return 'zero'
        if v=='1':return 'one'
        if v in {'待定','不确定','待裁定','NA','N/A','?','？'}:return 'undetermined'
    return 'other'
def completeness(rows,getter):
    result={}
    for d in DIMS:
        c=Counter(cat(getter(r,d)) for r in rows)
        result[d]={'nonempty':len(rows)-c['blank'],**{k:c[k] for k in ('blank','zero','one','undetermined','other')}}
    return result
csv_results=[]
for coder in ('A','C'):
    p=v5/f'真人{coder}-空白编码表.csv'
    b=p.read_bytes(); reader=csv.DictReader(io.StringIO(b.decode('utf-8-sig'))); rows=list(reader)
    ids=[r.get('匿名编号') for r in rows]
    expected=[r['blind_id'] for r in sampling['mapping'] if r['coder']==coder]
    origmap={r['blind_id']:r['original_id'] for r in sampling['mapping'] if r['coder']==coder}
    c=completeness(rows,lambda r,d:r.get(d))
    entry={**meta(p),'coder_file_alias':coder,'row_count':len(rows),'headers':reader.fieldnames,'unique_blind_id_count':len(set(ids)),'id_multiset_exact_v5':Counter(ids)==Counter(expected),'id_order_exact_v5':ids==expected,'missing_expected_id_count':len(set(expected)-set(ids)),'unexpected_id_count':len(set(ids)-set(expected)),'dimensions':c,'source_package_version':sampling.get('package_version'),'source_material_version':sampling.get('material_version'),'mapped_known_exposure_flag_count':sum(origmap.get(x) in {'RECODE25-01353','RECODE25-01361'} for x in ids)}
    entry['submission_data_available_at_this_path']=any(c[d]['nonempty'] for d in DIMS)
    csv_results.append(entry)
    if entry['submission_data_available_at_this_path'] and entry['sha256']!=BASE[p.name]:
        backup=OUT/'raw-submissions'/p.name; backup.parent.mkdir(exist_ok=True); backup.write_bytes(b)
        entry['raw_submission_backup']={**meta(backup),'source_read_utc':NOW}

archive_inventory=[]
markers=('校准','试填','编码员','人工编码','人工标','真人','编码结果','编码表','盲评','盲审')
for p in ARCHIVE.rglob('*'):
    if p.is_file() and any(x in p.name for x in markers):archive_inventory.append(meta(p))
archive_inventory.sort(key=lambda x:x['path'])
dump(OUT/'archive_filename_hash_inventory.json',{'read_utc':NOW,'allowed_root':str(ARCHIVE),'contents_inspected':False,'matching_files':archive_inventory})

binding_p=ROOT/'outputs/coding-revision-20261007-r3/statistics/final_bindings_v14_CONFIRMED_r3.json'
binding=json.loads(binding_p.read_bytes())
ref_results=[]
for coder in ('A','C'):
    slot=binding['references'][coder]; p=ROOT/slot['path']; rows=[json.loads(s) for s in p.read_bytes().splitlines() if s.strip()]
    ids=[r.get('id') for r in rows]
    ref_results.append({**meta(p),'registered_sha256':slot['sha256'],'bytes_identical_to_final_v14_frozen_binding':sha(p.read_bytes())==slot['sha256'],'row_count':len(rows),'unique_id_count':len(set(ids)),'dimensions':completeness(rows,lambda r,d:r.get('labels',{}).get(d)),'effective_material_version_counts':dict(Counter(r.get('effective_material_version') for r in rows)),'first_result_paths':sorted({r.get('annotation_provenance',{}).get('first',{}).get('result_path') for r in rows if r.get('annotation_provenance',{}).get('first',{}).get('result_path')})})
first_results=[]; qa_metadata=[]
for coder,qaname in (('A','完成清单及QA.json'),('C','完成清单与QA-首次.json')):
    qap=ROOT/f'outputs/coding-revision-20261007-r3/confirmation/agent-{coder}/{qaname}'; qa=json.loads(qap.read_bytes())
    qa_metadata.append({**meta(qap),'coder':qa.get('coder'),'registered_executor_metadata':{k:qa.get(k) for k in ('executor_identity','executor','model_revision','model','protocol_version','operational_version','material_version','qa_completed_at_local','completed_at','first_submission_preserved') if k in qa}})
    expected={int(x['packet']):x['first_result_sha256'] for x in qa['packets']}
    for n in range(1,9):
        p=qap.parent/f'结果-{n:02}.json'; j=json.loads(p.read_bytes()); rows=j['rows']; ids=[r.get('id') for r in rows]
        first_results.append({**meta(p),'coder':coder,'packet':n,'registered_first_result_sha256':expected[n],'bytes_identical_to_registered_first_submission':sha(p.read_bytes())==expected[n],'source_versions':{k:j.get(k) for k in ('protocol_version','operational_version','material_version')},'row_count':len(rows),'unique_id_count':len(set(ids)),'all_five_dimensions_binary_complete':all(all(type(r.get('labels',{}).get(d)) is int and r['labels'][d] in (0,1) for d in DIMS) for r in rows)})

report={'audit_read_utc':NOW,'trusted_user_statement':'真人A/B已填写并替换目前路径；据用户声明接受人员身份与已完成状态。实际文件位置仍须定位。','status':'USER_CONFIRMED_COMPLETION_BUT_UPDATED_FILE_NOT_LOCATED_IN_CHECKED_PATHS','scope':'项目已登记v5八文件（七交付文件加manifest）、项目reference A/C与confirmation首次结果；归档仅文件名mtime与SHA，未读内容；未搜索其他私人目录。','v5_public_files':public,'v5_csv_structure_and_completeness':csv_results,'v5_B_display_alias':'本套历史登记名为C，B是显示别名，未重命名或改动原件。','archive_inventory':str(OUT/'archive_filename_hash_inventory.json'),'reference_final_v14':ref_results,'registered_first_submissions':first_results,'registered_execution_metadata':qa_metadata,'observations':{'all_v5_registered_bytes_unchanged':all(x['bytes_identical_to_prior_registered_file'] for x in public),'both_v5_label_columns_empty':all(not x['submission_data_available_at_this_path'] for x in csv_results),'all_reference_hashes_match_original_final_binding':all(x['bytes_identical_to_final_v14_frozen_binding'] for x in ref_results),'all_confirmation_first_results_match_registered_first_hashes':all(x['bytes_identical_to_registered_first_submission'] for x in first_results),'new_submission_raw_backup_count':sum('raw_submission_backup' in x for x in csv_results)},'limitations':['归档仅允许元数据核查，没有读取任何工作簿单元格；相同哈希或旧mtime不能反驳用户已填写的声明，也不能据此认定非真人。','当前路径无新字节或空列只说明检查的这些路径尚未定位到新填写结果；请取得用户准确保存路径后继续机械入库。','未做人工一致性、人工质量、机器效度计算；未读取任何待保留单元原文或逐条具体标签给模型。','真实首次提交时间、独立填写、裁定过程仍需实际新文件及提交记录核查。'],'preserved_exposure_flags':[{'original_id':'RECODE25-01353','family_id':'TEXTFAM-2581e0e1d107f28b0ee3acfa9d5efa239eadbadeab719aae7a9204375422c2db','exposure_start':'至少上一轮十例具体差异审计与实际稿件审读'},{'original_id':'RECODE25-01361','family_id':'TEXTFAM-8f92e3edf1f01fb0d53d6ac6deadafb61f6d0e7cd629907429069b403d8610de','exposure_start':'至少上一轮十例具体差异审计与实际稿件审读'}],'no_original_file_modified':True,'model_calls_by_this_audit':0}
dump(OUT/'receipt_location_recheck.json',report)
text='''用户已确认真人A/B完成并替换文件；本次接受该人员状态，继续定位实际新文件。\n\n现场核查：原登记v5七交付文件及manifest的字节全部与此前冻结相同。两CSV各240行、240个匿名ID，ID集合与顺序均匹配各自v5登记映射，S/E/Ec/I/F每列非空数均0。登记路径中尚无已填写新字节，未生成冒称已收到提交的原件备份。\n\n项目reference A/C的最终文件SHA均匹配原final-v14冻结绑定；confirmation A/C各8份首次结果SHA均匹配原首次完成QA登记，五维均完整0/1。这些项目现存执行身份只按登记元数据记录，不能当作此次用户新提交。\n\n归档已按授权仅检索文件名、mtime、SHA，发现历史校准A/C及编码员A/B工作簿，具体路径见archive_filename_hash_inventory.json；没有读取归档工作簿单元格。历史文件同哈希不能用于认定非真人。仍需用户准确保存的已填写A/B路径。\n\n原01353与01361开发暴露flag保留；没有删除原样本、计算人工质量分数、机器效度或进行逐条原文审读。\n'''
(OUT/'receipt_location_recheck.txt').write_text(text,encoding='utf-8')
print(json.dumps({'read_utc':NOW,'report_path':str(OUT/'receipt_location_recheck.json'),'report_sha256':sha((OUT/'receipt_location_recheck.json').read_bytes()),'archive_filename_matches':len(archive_inventory),'observations':report['observations'],'v5_id_map_checks':[{k:x[k] for k in ('coder_file_alias','row_count','unique_blind_id_count','id_multiset_exact_v5','id_order_exact_v5','mapped_known_exposure_flag_count')} for x in csv_results]},ensure_ascii=False,indent=2))
