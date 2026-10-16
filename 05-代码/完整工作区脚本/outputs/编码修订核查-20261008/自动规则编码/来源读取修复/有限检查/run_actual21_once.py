"""One bounded actual full-entry run; retain all failures and source inputs."""
import ast,collections,hashlib,json,sys,time,traceback
from pathlib import Path
BASE=Path(__file__).resolve().parents[1];RT=BASE/'runtime';CHECK=Path(__file__).parent
W=BASE.parents[1];DATA=W/'统计复算/测量与语义统一全量'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def manifest(root):return {str(p.relative_to(root)):sha(p) for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.suffix!='.pyc'}
def tree_hash(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
before=manifest(RT);old=manifest(W/'自动规则编码/测量与语义统一/runtime')
for p in RT.glob('*.py'):ast.parse(p.read_text(),filename=str(p))
all_input_path=DATA/'规则输入4480.jsonl';old_output_path=DATA/'规则全量输出4480.jsonl';manual=W/'定义溯源核查/测量与计数统一/共用编码手册.md'
protected={str(p):sha(p) for p in [all_input_path,old_output_path,manual]}
inp=CHECK/'规则待核输入21.jsonl';rows=[json.loads(s) for s in inp.read_text().splitlines()]
whole={r['id']:r for r in map(json.loads,all_input_path.read_text().splitlines())}
assert len(rows)==21 and all(whole[r['id']]==r for r in rows)
old_results={r['id']:r for r in map(json.loads,(CHECK/'修正前输出21.jsonl').read_text().splitlines())}
for row in rows:
    for field in ['unit_source','candidate_file']:
        p=Path(row['input'][field]);protected[str(p)]=sha(p)
outpath=CHECK/'修正后实际输出21.jsonl';assert not outpath.exists(),'one actual run only; do not overwrite'
freeze=dict(kind='source_reader_development_run_not_validity',n=21,input_sha256=sha(inp),full_original_input_sha256=sha(all_input_path),manual_sha256=sha(manual),runtime_manifest=before,runtime_tree_sha256=tree_hash(before),original_runtime_manifest=old,original_runtime_tree_sha256=tree_hash(old),protected_files_before=protected)
(CHECK/'实际21执行冻结.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
sys.path.insert(0,str(RT))
from pypdf import PdfReader
import policy_coding_v27
started=time.monotonic();results=[]
with outpath.open('w') as handle:
    for row in rows:
        try:
            result=policy_coding_v27.code_unit(row['input']);out=dict(id=row['id'],status='completed',result=result)
        except Exception as error:
            out=dict(id=row['id'],status='failed',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc())
        results.append(out);handle.write(json.dumps(out,ensure_ascii=False)+'\n');handle.flush()
        print(row['id'],out['status'],flush=True)
changes=[]
for out in results:
    prior=old_results[out['id']]['result']
    current=out.get('result')
    changes.append(dict(id=out['id'],outer_status=out['status'],before_labels=prior['labels'],after_labels=current['labels'] if current else None,before_judgement_status=prior.get('judgement_status'),after_judgement_status=current.get('judgement_status') if current else None,changed_dimensions=[d for d,v in prior['labels'].items() if current and current['labels'][d]!=v],pending=current.get('common14_pending_dimensions',{}) if current else {},failure=out.get('error')))
after=manifest(RT);protected_after={p:sha(p) for p in protected}
report=dict(kind='one_finite_actual_entry_regression_not_validity',n=21,status_counts=dict(collections.Counter(r['status'] for r in results)),n_unresolved=sum(r.get('result',{}).get('judgement_status')=='undetermined' for r in results),elapsed_seconds=round(time.monotonic()-started,3),input_sha256=sha(inp),full_original_input_sha256=sha(all_input_path),output_sha256=sha(outpath),current_manual_sha256=sha(manual),runtime_tree_sha256=tree_hash(before),runtime_manifest=before,runtime_unchanged_during_run=before==after,original_runtime_unchanged=old==manifest(W/'自动规则编码/测量与语义统一/runtime'),protected_original_files_unchanged=protected==protected_after,protected_files_after=protected_after,changes=changes)
(CHECK/'actual21_execution_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['n','status_counts','n_unresolved','elapsed_seconds','runtime_unchanged_during_run','original_runtime_unchanged','protected_original_files_unchanged']},ensure_ascii=False))
