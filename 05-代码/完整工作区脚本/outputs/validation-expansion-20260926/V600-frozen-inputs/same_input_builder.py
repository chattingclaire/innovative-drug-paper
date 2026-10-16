"""Mechanical pre-freeze input build. Never display held-out texts or predictions."""
from pathlib import Path
import sys,json,hashlib,importlib.util
D=Path(__file__).resolve().parent;W=D.parent
sys.path.append(str(W))
from attach_object_scope import attach_scope
from policy_statistics_adapter import prepare,bind_labels,file_hash

def load(path,name):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def write(path,obj):path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
oldpath=W/'policy_coding_v4_development.py';newpath=D/'policy_coding_v4_development.py'
old=load(oldpath,'frozen_old');new=load(newpath,'candidate_new')
output=D/('同输入接入预览-'+new.VERSION);output.mkdir(exist_ok=True)
original=W/'统一文本复核包-语境v2.jsonl'
assert file_hash(original)=='1c47600b22d1e087bb21ef95625286f2b0978184432bd7bc8de9b8ee3ac037ec'
base=[json.loads(l) for l in original.read_text().splitlines()]
records=[attach_scope(r) for r in base]
for a,b in zip(base,records):
    assert {k:v for k,v in b.items() if k!='verified_object_scope'}=={k:v for k,v in a.items() if k!='verified_object_scope'}
corpus=output/'统一文本复核包-适用范围预览.jsonl'
corpus.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in records))
prepared=prepare(corpus,W/'55条部门与系列映射-核验中.json',W/'部门归属与年度系列-冻结v1.json')
write(output/'统计输入接入准备.json',prepared)
by={r['review_id']:r for r in records}
manual=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/validation-expansion-20260926/统一口径-v1.3/五维共用编码协议.md')
artifacts=[]
for label,module,path in [('旧版',old,oldpath),('新版',new,newpath)]:
    rows=[dict(id=u['id'],record_sha256=u['record_sha256'],**module.code_unit(by[u['id']])) for u in prepared['units']]
    bundle=dict(method='rule_based',run_id='same-input-preview-'+module.VERSION,binding_sha256=prepared['binding_sha256'],codebook_sha256=file_hash(manual),coder_sha256=file_hash(path),rows=rows,status='pre_freeze_mechanical_run_not_validation')
    bound=bind_labels(prepared,bundle,manual,path)
    for row,unit in zip(rows,bound['units']):
        assert row['safety_subtypes']==unit['safety_subtypes']
        assert row['fairness_subtypes']==unit['fairness_subtypes']
    outfile=output/(label+'逐单元预测.json');write(outfile,bundle)
    artifacts.append(dict(method=label,version=module.VERSION,coder_path=str(path),coder_sha256=file_hash(path),prediction_path=str(outfile),prediction_sha256=file_hash(outfile),row_count=len(rows),subtype_roundtrip=True))
report=dict(status='pre_freeze_mechanical_input_checks_only',submission_ready=False,corpus_path=str(corpus),corpus_sha256=file_hash(corpus),original_corpus_sha256=file_hash(original),unit_text_and_all_original_fields_unchanged=True,records=len(records),analysis_units=len(prepared['units']),context_only=len(prepared['excluded_context']),scope_record_count=sum(bool(r.get('verified_object_scope')) for r in records),binding_sha256=prepared['binding_sha256'],adapter_path=str(D/'policy_statistics_adapter.py'),adapter_sha256=file_hash(D/'policy_statistics_adapter.py'),scope_attacher_sha256=file_hash(D/'attach_object_scope.py'),scope_registry_sha256=file_hash(D/'对象适用范围登记.json'),artifacts=artifacts,limitation='Old implementation receives identical input but does not implement the new object-scope field. No sample drawn, no reference comparisons or performance results. Scope additions only; original fields unchanged.')
write(output/'同输入接入QA.json',report)
print(json.dumps({k:report[k] for k in ['status','records','analysis_units','context_only','scope_record_count','binding_sha256']},ensure_ascii=False))
print(str(output/'同输入接入QA.json'))
