"""Freeze after independent preflight. No CLI/model. Never overwrite history."""
import argparse
import ast
import json
import sys
from datetime import datetime,timezone
from pathlib import Path

sys.dont_write_bytecode=True
from candidate08_support import (HERE,OLD07,PLAN,FREEZE,RUNTIME,read,sha,binding,
    check_binding,check_plan,source_paths)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--independent-preflight',required=True,type=Path)
    args=parser.parse_args()
    assert not FREEZE.exists(),'Never overwrite an existing freeze.'
    preflight=read(args.independent_preflight)
    assert preflight['status'].startswith('PASS') and not preflight['blocking_findings']
    assert preflight['real_model_calls']==preflight['real_CLI_invocations']==0
    assert preflight['source_files_modified'] is False
    for x in preflight['source_bindings']:check_binding(x)
    prep=read(HERE/'preparation_manifest.json')
    for x in prep['core_files']+prep['source_bindings']:check_binding(x)
    assert sha(HERE/'candidate08_prompt_PROPOSED.txt')==read(HERE/'prompt_lock_before_independent_inputs.json')['prompt']['sha256']
    marker='--- 冻结的完整手册（原样） ---'.encode()
    assert (HERE/'candidate08_prompt_PROPOSED.txt').read_bytes().split(marker,1)[1]==(OLD07/'candidate07_prompt_PROPOSED.txt').read_bytes().split(marker,1)[1]
    for name in ['exposed240_inputs_UNCHANGED.jsonl','synthetic62_inputs_UNCHANGED.jsonl','synthetic24_inputs_UNCHANGED.jsonl','synthetic20_inputs_PROPOSED.jsonl']:
        assert (HERE/name).read_bytes()==(OLD07/name).read_bytes()
    assert (HERE/'synthetic106_expected_INHERITED_PRIVATE.json').read_bytes()==(OLD07/'synthetic106_expected_PRIVATE_PROPOSED.json').read_bytes()
    for name in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']:
        assert (RUNTIME/name).read_bytes()==(OLD07/'runtime-unchanged-v2'/name).read_bytes()
    plan=read(PLAN)
    check_plan(plan)
    for r in plan['runs']:assert not (RUNTIME/r['run_name']).exists()
    assert not (HERE/'execution-records').exists()
    for p in HERE.rglob('*.py'):ast.parse(p.read_text())
    files=[binding(p) for p in sorted(HERE.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p!=FREEZE]
    freeze={'status':'FROZEN_DESIGN_PENDING_SEPARATE_ROOT_PHASE_EXECUTION_AUTHORIZATION',
        'created_at_UTC':datetime.now(timezone.utc).isoformat(),'candidate':'08 proposition and evidence development',
        'model':'gpt-5.6-sol','reasoning_effort':'medium','nominal_logical_requests':17,'max_identical_technical_attempts':51,
        'scope_run_keys':plan['scope_run_keys'],'scope_sizes':plan['scope_sizes'],'phases':plan['phases'],
        'manual_scope':'Complete v1.3 and unchanged v1.4 substantive operational part; validation-discipline tail not in inherited suffix.',
        'schema_validator_runner_unchanged':True,'first_chronological_technically_valid_only':True,
        'semantic_or_metric_retries_or_selection':False,'full_corpus_or_automatic_adoption':False,
        'phase_semantic_gate_required':True,'unused_scope_must_be_reported_NOT_RUN':True,
        'independent16_expected_not_read_or_used_by_prompt_author':True,'prompt_locked_before_independent_control_metadata_added':True,
        'model_calls_before_freeze':0,'real_CLI_invocations_before_freeze':0,
        'independent_preflight':binding(args.independent_preflight),'independent_preflight_no_blocking_findings':True,
        'all_executed_rows_all_five_dimensions_and_fields_require_semantic_review':True,
        'known_working_cells_NOT_GOLD':27,'mandatory_review_current_units':42,
        'boundaries_not_forced_and_inherited_expectations_preserved':True,
        'files':files,'source_bindings':[binding(p) for p in source_paths()]}
    with FREEZE.open('x') as stream:
        json.dump(freeze,stream,ensure_ascii=False,indent=2);stream.write('\n')
    print(json.dumps({'status':freeze['status'],'path':str(FREEZE),'sha256':sha(FREEZE),
        'files':len(files),'source_bindings':len(freeze['source_bindings']),'model_calls':0},ensure_ascii=False))


if __name__=='__main__':main()
