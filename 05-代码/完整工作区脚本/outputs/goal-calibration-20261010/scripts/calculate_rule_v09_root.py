"""Bind actual first v09 outputs and independently calculate development diagnostics."""
from pathlib import Path
import hashlib, json, subprocess, sys
from datetime import datetime, timezone
root=Path(__file__).resolve().parents[1]
source=root/'06-coding/development-rule-sol/coverage36/implementation09-purpose-v13'
dest=root/'06-coding/root-machine-review/rule-v09-unique77-first'
dest.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
index=source/'v09-final-delivery-bindings.json'
assert sha(index)=='c692a42e42769dc7a12c44eb9b84d94e6dc1a7caff40503568479ca3f54f316f'
delivery=json.loads(index.read_bytes())
checks=[]
for entry in delivery['files']:
    p=Path(entry['path'])
    assert sha(p)==entry['sha256'] and p.stat().st_size==entry['bytes']
    checks.append({'path':str(p),'sha256':entry['sha256'],'bytes':entry['bytes']})
rawlines=[]; rows=[]; parents=[]
for name,n in [('run-old41-01',41),('run-old36-01',36)]:
    p=source/name/'predictions.jsonl'
    lines=p.read_bytes().splitlines(keepends=True)
    parsed=[json.loads(l) for l in lines if l.strip()]
    assert len(parsed)==n
    for row in parsed:
        assert set(row['labels'])=={'S','E','Ec','I','F'}
        assert all(type(v) is int and v in (0,1) for v in row['labels'].values())
        assert not row['implementation_errors'] and not row['source_requests'] and not row['material_requests']
    rawlines.extend(lines); rows.extend(parsed)
    parents.append({'path':str(p),'sha256':sha(p),'n':n})
assert len({r['id'] for r in rows})==len(rows)==77
pred=dest/'predictions.jsonl';pred.write_bytes(b''.join(rawlines))
quality={'created_at_utc':datetime.now(timezone.utc).isoformat(),
 'root_quality_passed':True,'quality_scope':'file bindings, first sealed output integrity, labels/counts and unresolved-state separation; not semantic correctness',
 'source_delivery_index_sha256':sha(index),'file_bindings_checked':checks,
 'prediction_sha256':sha(pred),'parents':parents,'raw_rows_copied_without_rewriting':True,
 'unique_n':77,'slots':385,'technical_failure_n':0,'semantic_null_n':0,
 'source_request_n':0,'actual_inputs_v13':True,
 'human_validation':False,'formal_acceptance':False}
qp=dest/'root-quality-acceptance.json';qp.write_text(json.dumps(quality,ensure_ascii=False,indent=2)+'\n')
subprocess.run([sys.executable,str(root/'scripts/calculate_sealed_development_metrics.py'),
 str(pred),str(root/'06-coding/development-reference77-v12-root-adjudicated-v2/reference.jsonl'),
 str(dest/'arithmetic'),'--identity','rule_v09_first_vs_nonblind_AI_development_reference_v2',
 '--quality-report',str(qp),'--adjudication',str(root/'04-calibration/source-impact4-v12/admin/root-adjudication-native36-v2.json')],check=True)
metrics=json.loads((dest/'arithmetic/arithmetic-crosscheck.json').read_text())
print(json.dumps({'files_bound':len(checks),'n':77,'errors':metrics['binary_disagreements'],
 'per_dim_metrics':{k:v['metrics'] for k,v in metrics['per_dimension'].items()},'formal_acceptance':False},ensure_ascii=False))
