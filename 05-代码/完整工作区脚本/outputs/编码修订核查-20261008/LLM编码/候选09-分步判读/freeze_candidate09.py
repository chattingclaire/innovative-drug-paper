"""Offline source closure and post-independent-preflight design freeze; no CLI."""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('c09_freeze_runner_helpers',HERE/'run_candidate09.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
MANIFEST=HERE/'preparation_manifest.json'
LOCK_SHA='8d72c9c84219be2c3d3da8fdbe4392b0699b9a20bc7de0b1eda8d18fa22964ef'
EXCLUDED_DIRS={'__pycache__','runs','offline-plans','invocation-records','independent-preflight'}
EXCLUDED_NAMES={'preparation_manifest.json','design_freeze.json'}

def save_once(path,obj):
    encoded=(json.dumps(obj,ensure_ascii=False,indent=2)+'\n').encode()
    if path.exists():assert path.read_bytes()==encoded,f'Immutable file differs: {path}'
    else:r.write_new(path,encoded)

def validate_locked_sources():
    assert r.sha(HERE/'prompt_lock.json')==LOCK_SHA,'original prompt lock changed'
    lock=json.loads((HERE/'prompt_lock.json').read_text())
    for b in lock['prompts']+lock['manual_sources']+[lock['manual_suffix']]+lock['B_runtime_byte_identical_copies']:
        r.verify_binding(b)
    sources=lock['manual_sources']
    v13=Path(sources[0]['path']).read_text();v14=Path(sources[1]['path']).read_text().split('## 版本与验证纪律')[0]
    suffix='\n--- 冻结的完整v1.3手册原文 ---\n\n'+v13+'\n--- 冻结的v1.4实质操作部分原文 ---\n\n'+v14
    assert (HERE/'manual_suffix_UNCHANGED.txt').read_text()==suffix
    for stage in ['A','B']:
        prompt=r.PROMPTS[stage].read_text();assert prompt.endswith(suffix)
        prefix=prompt[:-len(suffix)]
        assert 'RECODE25-'not in prefix and 'C05-NEW-'not in prefix and '0.80'not in prefix
    prior=HERE.parent/'候选08-命题与证据判定'/'runtime-unchanged-v2'
    originals=[]
    for name in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']:
        assert (HERE/'runtime'/name).read_bytes()==(prior/name).read_bytes()
        originals.append(r.binding(prior/name))
    return lock,originals

def validate_selftests():
    a=json.loads((HERE/'selftest_stageA_no_model_result.json').read_text())
    assert a['status']=='PASS_NO_MODEL_TECHNICAL_SELFTEST'and a['failures']==[]
    assert a['tests_passed']==a['tests_total']and a['model_calls']==a['model_CLI_invocations']==0
    for b in a['source_bindings']+a['implementation_bindings']:r.verify_binding(b)
    b=json.loads((HERE/'selftest_runtime_no_model_result.json').read_text())
    assert b['status']=='PASS'and b['checks_n']==len(b['checks'])and all(x['passed']for x in b['checks'])
    assert b['real_CLI_invocations']==b['real_model_calls']==0 and b['source_files_modified']is False
    for p,h in b['locked_source_bindings'].items():assert r.sha(p)==h
    # The old reviewer report intentionally binds the prior runner. Preserve
    # that identity instead of claiming it reviewed the later hardening diff.
    old=json.loads((HERE/'runner-code-review/runner_code_review.json').read_text())
    archived=HERE/'preparation-history/runner-before-final-integrity-receipts/run_candidate09.py'
    assert old['runner_sha256']==r.sha(archived)
    return {'stageA_synthetic_checks':a['tests_total'],'runtime_synthetic_checks':b['checks_n']}

def build_manifest():
    lock,originals=validate_locked_sources();tests=validate_selftests()
    ib,ip,raw,rows=r.read_input()  # Mechanical only. No text, IDs or expectations printed.
    plan=json.loads((HERE/'offline_plan.json').read_text())
    assert plan['candidate']==r.CANDIDATE and plan['scope']==r.SCOPE and plan['n']==r.N
    assert plan['model']==r.MODEL and plan['reasoning_effort']==r.EFFORT
    assert plan['design_total_logical_requests_if_both_separately_authorized']==2
    assert plan['design_total_max_technical_attempts']==6
    files=[]
    for p in sorted(HERE.rglob('*')):
        rel=p.relative_to(HERE)
        if not p.is_file()or set(rel.parts[:-1])&EXCLUDED_DIRS or p.name in EXCLUDED_NAMES:continue
        if p.suffix not in {'.py','.json','.md','.txt','.diff'}:continue
        files.append(r.binding(p))
    exclusion=r.PROJECT/'outputs/coding-revision-20261008-r4/validation-state-audit/future_human_v5_development_exclusion_metadata.json'
    sources=lock['manual_sources']+originals+[r.binding(ip),r.binding(exclusion)]
    if ib.get('visibility_metadata_path'):sources.append(r.binding(ib['visibility_metadata_path']))
    return {'status':'OFFLINE_PREPARATION_MANIFEST_REQUIRES_INDEPENDENT_PREFLIGHT',
      'candidate':r.CANDIDATE,'scope':r.SCOPE,'n':r.N,'model':r.MODEL,'reasoning_effort':r.EFFORT,
      'stageA_and_B_separately_authorized':True,'max_attempts_per_stage':r.MAX_ATTEMPTS,
      'prompt_lock_sha256':LOCK_SHA,'files':files,'sources':sources,'tests':tests,
      'raw_input_bytes':len(raw),'original_rows_canonical_sha256':r.row_sha(rows),
      'input_row_ID_order_canonical_sha256':r.row_sha([x['id']for x in rows]),
      'private_expectations_read':False,'original_materials_modified':False,
      'real_CLI_invocations':0,'real_model_calls':0,'execution_authorized':False,
      'old_candidate08_status':'FAIL unchanged','other_scopes':'NOT_RUN'}

def main():
    ap=argparse.ArgumentParser();mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--manifest-only',action='store_true');mode.add_argument('--freeze',action='store_true')
    ap.add_argument('--independent-review-file');ap.add_argument('--expected-review-sha256')
    args=ap.parse_args();manifest=build_manifest()
    if args.manifest_only:
        save_once(MANIFEST,manifest)
        print(json.dumps({'status':manifest['status'],'manifest':r.binding(MANIFEST),
          'files_n':len(manifest['files']),'sources_n':len(manifest['sources']),
          'real_CLI_invocations':0,'real_model_calls':0},ensure_ascii=False));return
    assert MANIFEST.exists()and json.loads(MANIFEST.read_text())==manifest,'manifest source closure changed before freeze'
    assert args.independent_review_file and args.expected_review_sha256
    review_path=Path(args.independent_review_file).resolve()
    assert r.sha(review_path)==args.expected_review_sha256
    review=json.loads(review_path.read_text())
    assert str(review['status']).startswith('PASS')and review['blocking_findings']==[]
    assert review['real_CLI_invocations']==review['real_model_calls']==0 and review['source_files_modified']is False
    assert review['preparation_manifest_sha256']==r.sha(MANIFEST),'independent review must bind this exact stable manifest'
    for b in review['source_bindings']:r.verify_binding(b)
    freeze={'status':'DESIGN_FROZEN_NO_MODEL_EXECUTION_AUTHORIZED',
      'candidate':r.CANDIDATE,'scope':r.SCOPE,'n':r.N,'model':r.MODEL,'reasoning_effort':r.EFFORT,
      'stageA_and_B_separately_authorized':True,'max_attempts_per_stage':r.MAX_ATTEMPTS,
      'created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'files':manifest['files']+[r.binding(MANIFEST),r.binding(review_path)],'sources':manifest['sources'],
      'preparation_manifest':r.binding(MANIFEST),'independent_preflight':r.binding(review_path),
      'logical_requests_if_both_separately_authorized':2,'max_total_technical_attempts':6,
      'root_stageA_authorization_required':True,'root_original_A_semantic_gate_and_stageB_authorization_required':True,
      'gate_review_or_expectations_in_model_request':False,
      'real_CLI_invocations':0,'real_model_calls':0,'other_scopes':'NOT_RUN','old_candidate08_status':'FAIL unchanged'}
    save_once(HERE/'design_freeze.json',freeze)
    print(json.dumps({'status':freeze['status'],'design_freeze':r.binding(HERE/'design_freeze.json'),
      'real_CLI_invocations':0,'real_model_calls':0},ensure_ascii=False))

if __name__=='__main__':main()
