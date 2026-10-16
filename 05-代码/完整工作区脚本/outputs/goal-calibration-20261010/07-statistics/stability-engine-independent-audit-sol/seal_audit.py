#!/usr/bin/env python3
"""Seal this constructed audit and its explicitly permitted read-only sources."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

BASE=Path(__file__).resolve().parent
SOURCE=BASE.parent/'prospective-stability-engine-sol'
SEAL=BASE/'audit-seal.json'

def sha(data):
    return hashlib.sha256(data).hexdigest()

def metadata(path,name):
    data=path.read_bytes()
    return {'path':name,'sha256':sha(data),'bytes':len(data)}

def current_files():
    return [p for p in sorted(BASE.rglob('*')) if p.is_file() and p!=SEAL and '__pycache__' not in p.parts and not p.name.startswith('.')]

def permitted_sources():
    prep=json.loads((SOURCE/'preparation-seal.json').read_text())
    refs=[]
    for item in prep['files']:
        path=Path(item['path'])
        assert not path.is_absolute() and '..' not in path.parts
        p=(SOURCE/path).resolve();assert p.is_relative_to(SOURCE.resolve())
        assert metadata(p,str(path))==item,'Original candidate changed: '+str(path)
        refs.append(metadata(p,str(p)))
    refs.append(metadata(SOURCE/'preparation-seal.json',str((SOURCE/'preparation-seal.json').resolve())))
    allowed={str((SOURCE.parent.parent/'06-coding/llm-protocol-sol/稳定性与运行封存预设.md').resolve()),
             str((SOURCE.parent.parent/'02-methods/prospective-statistical-contract-v2/validation-design-v2.json').resolve())}
    assert {x['path'] for x in prep['read_only_method_sources']}==allowed
    for item in prep['read_only_method_sources']:
        p=Path(item['path']);assert metadata(p,str(p))==item
        refs.append(metadata(p,str(p)))
    return refs

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--verify',action='store_true');args=ap.parse_args()
    if args.verify:
        s=json.loads(SEAL.read_text());failures=[]
        listed={i['path'] for i in s['files']};current={p.relative_to(BASE).as_posix() for p in current_files()}
        if listed!=current:failures.append('audit membership changed')
        for item in s['files']:
            p=BASE/item['path']
            if not p.is_file() or metadata(p,item['path'])!=item:failures.append(item['path'])
        for item in s['read_only_sources']:
            p=Path(item['path'])
            if not p.is_file() or metadata(p,item['path'])!=item:failures.append(item['path'])
        print(json.dumps({'status':'audit_seal_verified' if not failures else 'audit_seal_mismatch',
                          'audit_files':len(s['files']),'read_only_source_files':len(s['read_only_sources']),
                          'failures':failures,'actual_model_or_independent_context_verified':False},ensure_ascii=False))
        return bool(failures)
    assert not SEAL.exists(),'Refuse to overwrite audit seal'
    sources=permitted_sources()
    files=[metadata(p,p.relative_to(BASE).as_posix()) for p in current_files()]
    s={'bundle':'stability-engine-independent-audit-sol','status':'finite_constructed_audit_with_local_repair_candidate_only',
       'sealed_at_utc':datetime.now(timezone.utc).isoformat(),'self_included':False,'ignored':['__pycache__','hidden runtime files'],
       'audit_identity':{'kind':'AI','requested_model':'gpt-6.1-sol','requested_reasoning_effort':'ultra','human_expert':False},
       'scope':{'real_labels_or_gold_or_policy_body_read':False,'shared_source_or_real_packets_searched':False,
                'model_dispatch_count':0,'formal_plan_modified':False,'original_candidate_modified':False,
                'actual_stability_established':False,'project_completion_established':False,
                'pure_source_or_native_batch_provenance_certified':False,'fixed_stability_or_CI_gate_added':False},
       'finite_controls':{'original_expected_controls':38,'repair_expected_controls':34,'supplemental_repair_controls':8,
                          'copied_original_regression_tests':22,'phases_have_overlap_not_independent_sum':True,
                          'original_contract_type_defects_found':2,'both_reproductions_retained':True,'local_repair_verified':True},
       'read_only_source_scope':{'original_candidate_manifest_files':651,'original_candidate_preparation_seal':1,'permitted_method_sources':2},
       'read_only_sources':sources,'files':files,'identity_or_independence_authenticated_by_hash':False}
    SEAL.write_text(json.dumps(s,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    print(json.dumps({'status':'audit_sealed','audit_files':len(files),'read_only_source_files':len(sources),'seal_path':str(SEAL)},ensure_ascii=False))
    return 0

if __name__=='__main__':
    raise SystemExit(main())
