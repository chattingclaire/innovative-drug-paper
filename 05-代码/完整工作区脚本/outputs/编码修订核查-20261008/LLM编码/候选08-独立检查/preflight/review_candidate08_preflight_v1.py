"""Independent read-only preflight. No CLI or model calls; own report only."""
import ast
import contextlib
import copy
import difflib
import hashlib
import importlib.util
import io
import json
import math
from pathlib import Path
import sys
from datetime import datetime, timezone
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE = ROOT/'outputs/编码修订核查-20261008/LLM编码'
AUTHOR = BASE/'候选08-命题与证据判定'
PRIVATE = BASE/'候选08-独立检查'
OUT = PRIVATE/'preflight'
OLD = BASE/'候选方案'
checks = []


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def binding(p):
    p = Path(p).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def read(p):
    return json.loads(Path(p).read_text())


def load(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def passed(name):
    checks.append({'check': name, 'status': 'PASS'})


def reject(name, fn):
    try:
        fn()
    except (AssertionError, ValueError, KeyError, FileNotFoundError):
        passed(name)
    else:
        raise AssertionError('Unexpected acceptance: '+name)


prep_path = AUTHOR/'preparation_manifest.json'
prep = read(prep_path)
sources = prep['core_files'] + prep['source_bindings']
for b in sources:
    assert binding(b['path']) == b
assert len(prep['core_files']) == 39 and len(prep['source_bindings']) == 37
assert prep['current_model_calls'] == prep['current_real_CLI_invocations'] == 0
passed('All 39 actual preparation core files and 37 external source bindings match SHA and bytes')

private_manifest = read(PRIVATE/'independent_design_manifest_v1.json')
for b in private_manifest['files']:
    assert sha(b['path']) == b['sha256']
assert private_manifest['model_calls'] == 0
assert private_manifest['actual_candidate08_prompt_read'] is False
assert private_manifest['actual_candidate08_outputs_read'] is False
passed('Independent control freeze remains unchanged; design preceded this reviewer reading 08 prompt')

lock = read(AUTHOR/'prompt_lock_before_independent_inputs.json')
prompt = AUTHOR/'candidate08_prompt_PROPOSED.txt'
assert binding(prompt) == lock['prompt']
assert lock['independent_control_text_or_expectations_read_by_prompt_author'] is False
assert prep['independent16_original_or_expected_not_semantically_read_by_prompt_author'] is True
assert sha(prompt) == 'd79c097443fa249051c5264da1ff532ddf7d984225ac3e776807de95f7f21803'
passed('Locked prompt actual SHA/36714 bytes match lock and final preparation')

marker = '--- 冻结的完整手册（原样） ---'.encode()
suffix = prompt.read_bytes().split(marker, 1)[1]
assert suffix == (OLD/'candidate07_prompt_PROPOSED.txt').read_bytes().split(marker, 1)[1]
v13 = ROOT/'outputs/coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md'
assert v13.read_bytes() in suffix
assert b'RECODE25-' not in prompt.read_bytes()
passed('From handbook marker, 08 suffix equals 07 byte for byte; full v1.3 embedded; no real unit IDs')
for n in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']:
    assert (AUTHOR/'runtime-unchanged-v2'/n).read_bytes() == (OLD/'runtime-unchanged-v2'/n).read_bytes()
passed('Actual runner/schema/validator bytes identical to 07')
for n in ['exposed240_inputs_UNCHANGED.jsonl','synthetic62_inputs_UNCHANGED.jsonl','synthetic24_inputs_UNCHANGED.jsonl','synthetic20_inputs_PROPOSED.jsonl']:
    assert (AUTHOR/n).read_bytes() == (OLD/n).read_bytes()
assert (AUTHOR/'synthetic106_expected_INHERITED_PRIVATE.json').read_bytes() == (OLD/'synthetic106_expected_PRIVATE_PROPOSED.json').read_bytes()
passed('Exposed240 and inherited106 inputs/order plus inherited expected file byte unchanged')

# Exact limited adapter diff; original selection/validation logic is not replaced.
old_audit = ROOT/'outputs/coding-revision-20261008-r4/llm-candidate05-preparation/audit_candidate05_v2.py'
adapter = AUTHOR/'technical_audit_json_adapter.py'
want = old_audit.read_text().replace("HERE = Path(__file__).resolve().parent", "HERE = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/coding-revision-20261008-r4/llm-candidate05-preparation')")
want = want.replace("    source = lines(run / 'frozen_input.jsonl')\n    assert sha(run / 'frozen_input.jsonl') == plan['input_sha256'] == sha(declared['input'])", "    frozen_input = run / plan['frozen_input_relative_path']\n    assert frozen_input.name in ['frozen_input.jsonl', 'frozen_input.json']\n    source = lines(frozen_input) if frozen_input.suffix == '.jsonl' else read(frozen_input)['rows']\n    assert sha(frozen_input) == plan['input_sha256'] == sha(declared['input'])")
assert adapter.read_text() == want
passed('Technical adapter changes limited to source HERE binding and JSON/JSONL input format')

sys.path.insert(0, str(AUTHOR))
support = load('candidate08_support', AUTHOR/'candidate08_support.py')
sys.modules['candidate08_support'] = support
plan = read(AUTHOR/'candidate08_execution_plan_PROPOSED.json')
support.check_plan(plan)
assert plan['nominal_logical_requests'] == 17
assert plan['maximum_identical_technical_attempts'] == 51
assert plan['scope_sizes'] == [24,16,62,24,20,240]
assert [x['logical_requests'] for x in plan['phases']] == [2,5,10]
assert plan['full_corpus_or_adoption'] is False
for r in plan['runs']:
    assert r['logical_requests'] == math.ceil(r['n']/25)
    cmd = r['future_execution_command_after_separate_root_authorization_only']
    assert cmd[0] == '/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
    assert cmd[1] == str(AUTHOR/'runtime-unchanged-v2/run_production_v32.py')
    assert cmd[cmd.index('--workers')+1] == str(r['workers'])
    assert '--start' not in cmd and '--limit-batches' not in cmd and '--plan-only' not in cmd
    assert not (AUTHOR/'runtime-unchanged-v2'/r['run_name']).exists()
assert not (AUTHOR/'execution-records').exists()
passed('Actual final plan: 40→106→240, 2+5+10 logical / maximum51, no executions yet')

runner = load('candidate08_independent_runner', AUTHOR/'runtime-unchanged-v2/run_production_v32.py')
assert runner.MODEL == 'gpt-5.6-sol' and runner.EFFORT == 'medium'
for r in plan['runs']:
    p = Path(r['input_binding']['path'])
    rows = [json.loads(x) for x in p.read_text().splitlines() if x.strip()] if p.suffix == '.jsonl' else read(p)['rows']
    assert len(rows) == r['n'] and len({x['id'] for x in rows}) == r['n']
    runner.no_reference_fields(rows)
passed('All 386 planned inputs mechanically pass recursive no-reference-field check; no values displayed')
assert plan['runs'][1]['input_binding'] == binding(PRIVATE/'independent_synthetic16_inputs_ONLY_PRIVATE_PREDECLARED.json')
passed('Independent16 request binds no-answer file only, not full expectations or boundary register')

wrapper = load('candidate08_independent_wrapper', AUTHOR/'run_bounded_candidate08.py')
with patch.object(sys, 'argv', ['run_bounded_candidate08.py']), patch.object(wrapper.subprocess, 'run', side_effect=AssertionError('Forbidden CLI/model invocation')) as call:
    with contextlib.redirect_stdout(io.StringIO()) as capture:
        wrapper.main()
    default = json.loads(capture.getvalue())
    assert call.call_count == 0 and default['status'] == 'PLAN_ONLY_NO_CLI_OR_MODEL_CALLS'
passed('Actually ran default wrapper in-process with subprocess forbidden: metadata only, zero subprocess')

auth_base = {'authorized':True,'design_freeze_sha256':'MOCK', 'model':'gpt-5.6-sol','reasoning_effort':'medium',
             'first_technically_valid_only':True,'semantic_retry_allowed':False,
             'full_corpus_or_adoption_allowed':False,'phase_semantic_gate_required':True}
for phase in plan['phases']:
    runs = [r for r in plan['runs'] if r['run_key'] in phase['run_keys']]
    logical = sum(r['logical_requests'] for r in runs)
    auth = {**auth_base,'authorized_phase':phase['phase'],'scope_run_keys':phase['run_keys'],
            'scope_sizes':[r['n'] for r in runs], 'max_logical_requests':logical,'max_technical_attempts':3*logical}
    support.check_authorization(auth, 'MOCK', plan, phase['phase'])
    passed('Single-phase authorization accepted: '+phase['phase'])
    for key, value in [('authorized_phase','wrong'),('scope_sizes',[4924]),('semantic_retry_allowed',True),('full_corpus_or_adoption_allowed',True),('max_technical_attempts',3*logical+1)]:
        bad = copy.deepcopy(auth); bad[key]=value
        reject('Single-phase rejects '+key+': '+phase['phase'],lambda bad=bad,phase=phase:support.check_authorization(bad,'MOCK',plan,phase['phase']))

# In-memory contract only: no fabricated execution files in the candidate directory.
fake_binding = lambda p: {'path':str(p),'sha256':'MOCK','bytes':1}
for phase in plan['phases'][:2]:
    runs = [r for r in plan['runs'] if r['run_key'] in phase['run_keys']]
    n = sum(r['n'] for r in runs)
    gate = {'status':'PASS_NO_CONFIRMED_SEMANTIC_ERROR','phase':phase['phase'],'design_freeze_sha256':'MOCK',
            'root_reviewed_and_approved_to_continue':True,'confirmed_semantic_error_count':0,
            'all_rows_all_five_dimensions_and_fields_reviewed':True,'boundary_disputes_separately_retained_not_forced':True,
            'run_keys':phase['run_keys'],'reviewed_rows':n,'reviewed_dimension_cells':5*n,
            'actual_output_bindings':[fake_binding(support.RUNTIME/r['run_name']/'all_predictions.json') for r in runs],
            'semantic_review_report_bindings':[fake_binding('/MOCK/semantic-report.json')],
            'technical_QA_binding':fake_binding(support.HERE/'execution-audit'/phase['phase']/'candidate08_technical_QA.json')}
    fake_qa = {'status':'PASS_TECHNICAL_ONLY_SEMANTIC_REVIEW_PENDING','completed_run_keys':phase['run_keys']}
    with patch.object(support,'binding',fake_binding),patch.object(support,'check_binding',lambda x:None),patch.object(support,'read',lambda x:fake_qa):
        support.check_phase_gate(gate,phase['phase'],'MOCK',plan)
        passed('Complete root-reviewed semantic gate accepted in-memory: '+phase['phase'])
        for key,value in [('status','FAIL'),('confirmed_semantic_error_count',1),('root_reviewed_and_approved_to_continue',False),('all_rows_all_five_dimensions_and_fields_reviewed',False),('reviewed_dimension_cells',5*n-1),('actual_output_bindings',[]),('semantic_review_report_bindings',[])]:
            bad=copy.deepcopy(gate);bad[key]=value
            reject('Phase gate stops '+key+': '+phase['phase'],lambda bad=bad,phase=phase:support.check_phase_gate(bad,phase['phase'],'MOCK',plan))

def events(messages):
    return '\n'.join(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':json.dumps(x)}}) for x in messages)

raw={'x':1,'y':[0,True]}
assert not runner.event_output_binding_audit(events([raw]),raw)['errors']
passed('Unique completed agent message matches full raw JSON')
for name,messages,out,available in [('missing',[],raw,True),('multiple',[raw,raw],raw,True),('mismatch',[raw],{'x':2},True),('bool-int',[{'x':True}],{'x':1},True),('float-int',[{'x':1.0}],{'x':1},True),('raw unavailable',[raw],None,False)]:
    assert runner.event_output_binding_audit(events(messages),out,available)['errors']
    passed('Technical event/raw binding rejects '+name)
assert not runner.event_output_binding_audit(events([{'b':2,'a':1}]),{'a':1,'b':2})['errors']
passed('Technical event/raw binding accepts JSON key-order difference')

audit = load('candidate08_independent_audit', AUTHOR/'audit_candidate08.py')
old = {'id':'SYN','labels':{'S':0,'E':0,'Ec':0,'I':0,'F':0},'dimension_reasons':{},'evidence':[],
       'innovation_subtypes':[],'fairness_subtypes':[],'safety_quality_basis':'no_quality_basis'}
for field,value in [('dimension_reasons',{'S':'changed'}),('evidence',[{'quote':'x'}]),('innovation_subtypes',['attribute']),('fairness_subtypes',['access']),('safety_quality_basis','quality_only')]:
    new=copy.deepcopy(old);new[field]=value
    assert audit.changed_fields(old,new)==[field]
    passed('Equal-label changes still detected for '+field)
gate_plan=read(AUTHOR/'predeclared_acceptance_PROPOSED.json')
assert len(gate_plan['mandatory_review_ids'])==len(set(gate_plan['mandatory_review_ids']))==42
assert set(gate_plan['current_six_known_items'])<=set(gate_plan['mandatory_review_ids'])
assert len(gate_plan['required_working_cells_NOT_GOLD'])==27
assert len(gate_plan['boundary_cells_NOT_FORCED'])==22
passed('Six current issues and 42 mandatory units retained even unchanged; 27 working cells and22 boundary cells separate')

for p in AUTHOR.rglob('*.py'):
    ast.parse(p.read_text())
passed('All candidate Python files parse without calling CLI or model')
for b in sources:
    assert binding(b['path']) == b
for b in private_manifest['files']:
    assert sha(b['path']) == b['sha256']
passed('All actual preparation and independent private bindings unchanged after read-only checks')

source_bindings = list(sources) + [binding(prep_path),binding(PRIVATE/'independent_design_manifest_v1.json')] + [binding(x['path']) for x in private_manifest['files']]
report = {
 'status':'PASS_INDEPENDENT_CANDIDATE08_PREFLIGHT_ZERO_CLI_MODEL_CALLS',
 'created_at_UTC':datetime.now(timezone.utc).isoformat(),
 'reviewer':'/root/validation_state_oct8',
 'blocking_findings':[], 'real_model_calls':0, 'real_CLI_invocations':0,
 'source_files_modified':False, 'source_bindings':source_bindings,
 'actual_checks':checks, 'actual_check_count':len(checks),
 'scope':{'prompt_lock_SHA':sha(prompt),'preparation_manifest_SHA':sha(prep_path),'phases':[40,106,240],
          'logical_requests':[2,5,10],'maximum_identical_technical_attempts':51,
          'author24_semantic_design_review':'Separate agent report bound; not claimed as this reviewer\'s own complete author24 semantic review.',
          'independent16_actual_semantic_review':{'all16_current_inputs_contexts_and80_expectations_actually_read':True,
                'all_reasons_quotes_I_F_subtypes_and_S_quality_checked':True,'blocking_conflicts':[],
                'three_separate_unscored_boundaries_not_forced':True,'private_originals_or_expectations_sent_to_author':False,
                'author_prompt_modifications_proposed_by_this_reviewer':False,'author_prompt_or_outputs_read_before_control_design':False}},
 'prompt_semantic_review':{'execution_layer_actually_read':True,'inconsistent_extra_definition_gate_found':False,
          'full_v13_and_v14_substantive_suffix_byte_equal_to07':True,'v14_version_discipline_tail_not_in_inherited_prompt':True,
          'reviewer_did_not_modify_or_propose_prompt':True},
 'privacy_and_timing_evidence':{'author_nonreading_supported_by':'Explicit author lock/declaration, trusted root coordination and this reviewer\'s metadata-only disclosure; no global filesystem-access audit is available.',
          'lock_file_binding':binding(AUTHOR/'prompt_lock_before_independent_inputs.json'),
          'control_inputs_never_sent_in_messages':True,'author_nonreading_not_independently_proven_by_OS_access_log':True,
          'post_lock_current_prompt_SHA_unchanged':True,'future_freeze_and_wrapper_recheck_SHA':True},
 'technical_scope':{'first_chronological_technically_valid_only':True,'same_request_technical_retry_max3':True,
          'event_raw_unique_final_message_full_typed_JSON_gate':True,'no_reference_or_expected_answers_in_request_inputs':True,
          'all_run_scopes_bounded_and_independent_input_separate':True,'confirm_error_stops_later_phases_via_root_semantic_gate':True,
          'unused_requests_NOT_RUN_required':True,'no_full4924_or_adoption_authorization':True,
          'provider_internal_model_revision_not_verified_by_preflight':True},
 'manual_AB_predictions_manuscript_modified':False,
 'limitations':['This PASS concerns design, bindings and no-model contract checks; actual model outputs and later semantic gates do not exist yet.',
     'The controls are synthetic development behavior checks, not external human validity or corpus accuracy evidence.',
     'Predeclared technical bounds do not prove future semantic correctness or kappa attainment; boundary disagreements remain separately recorded.',
     'Protected267 originals were not semantically read; original240 was mechanically inspected for counts/reference fields only and is already exposed development material.']
}
target=OUT/'candidate08_independent_preflight_v1.json'
assert not target.exists(),'Never overwrite earlier preflight.'
target.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':report['status'],'path':str(target),'sha256':sha(target),'actual_check_count':len(checks),
                  'real_model_calls':0,'real_CLI_invocations':0,'source_files_modified':False},ensure_ascii=False))
