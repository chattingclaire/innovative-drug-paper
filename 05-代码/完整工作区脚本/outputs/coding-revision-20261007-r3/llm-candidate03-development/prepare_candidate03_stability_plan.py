"""Freeze a plan only. Never read predictions or launch model calls."""
import datetime, hashlib, json, pathlib

H = pathlib.Path(__file__).resolve().parent
R = H.parent
OLD = R / 'llm-v32'
DEST = H / 'candidate03-stability-plan'
PROMPT_SHA = '8576d9a1be10b0dd7b69b4c12367f4c357f55abf4ca30d979d5b333493089ba4'
INPUT_SHA = '6829d554cf5514e49565c7c58c4ffdb6f7768f9999b0eea49f114db023c03763'
SELECTION_SHA = 'e3ac26b63c36a59ea3eb1717b6db553ad481e890a5405723424f30e3f20d3a57'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def read(p):
    return json.loads(p.read_text())

def binding(p):
    return {'path': str(p), 'sha256': sha(p)}

def request(prompt, rows):
    return prompt + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps({'rows': rows}, ensure_ascii=False) + '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'

assert not DEST.exists(), 'Do not overwrite an existing stability plan.'
selection_file = OLD / 'stability_preselection_freeze.json'
assert sha(selection_file) == SELECTION_SHA
selection = read(selection_file)
assert [x['production_batch'] for x in selection['selected']] == [13, 147, 47]
source = R / 'effective_blind_inputs_v14.jsonl'
assert sha(source) == INPUT_SHA
rows = [json.loads(s) for s in source.read_text().splitlines() if s.strip()]
base_path = H / 'candidate03_prompt.txt'
assert sha(base_path) == PROMPT_SHA
base = base_path.read_text()
old_base = (OLD / 'stability-base-repeat-2-batch-0013/frozen_prompt.txt').read_text()
old_order = (OLD / 'stability-order-perturbation-batch-0013/frozen_prompt.txt').read_text()
assert old_order.endswith(old_base)
prefix = old_order[:-len(old_base)]
assert prefix == '本次仅改变逐维核对顺序：读完当前完整单元及全部语境后，依次核对公平性F、创新性I、经济性Ec、有效性E、安全性S。五维的定义、纳入排除边界、证据要求和JSON输出结构均保持后文规定；仍独立判断每维，不以先后顺序推导标签。\n\n'
DEST.mkdir()
sample = []
batch_bindings = []
for item in selection['selected']:
    bi = item['production_batch']
    packet_rows = rows[(bi - 1) * 25:bi * 25]
    assert [r['id'] for r in packet_rows] == item['all_ids']
    old_input = OLD / f'stability-input-batch-{bi:04d}.jsonl'
    assert packet_rows == [json.loads(s) for s in old_input.read_text().splitlines() if s.strip()]
    out = DEST / f'v14-batch-{bi:04d}.jsonl'
    out.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in packet_rows))
    baseline_request = request(base, packet_rows)
    observed_request_path = H / 'full-corpus-candidate03-material-v14-development/batches' / f'batch-{bi:04d}/request.txt'
    if observed_request_path.exists():
        assert observed_request_path.read_text() == baseline_request
    sample.extend(packet_rows)
    batch_bindings.append({**item, 'v14_input': binding(out), 'same_payload_as_old_frozen_sample': True,
        'old_frozen_input': binding(old_input),
        'base_request_sha256': hashlib.sha256(baseline_request.encode()).hexdigest(),
        'order_request_sha256': hashlib.sha256(request(prefix + base, packet_rows).encode()).hexdigest()})
assert len(sample) == len({r['id'] for r in sample}) == 75
sample_path = DEST / 'same_preselected75_v14.jsonl'
sample_path.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in sample))
order_path = DEST / 'candidate03_order_F_I_Ec_E_S.txt'
order_path.write_text(prefix + base)
assert order_path.read_text()[len(prefix):] == base
sample_sha = sha(sample_path)
planned_runs = []
for kind in ['base-repeat-2', 'base-repeat-3', 'order-perturbation']:
    prompt = order_path if kind == 'order-perturbation' else base_path
    name = 'candidate03-stability-' + kind
    planned_runs.append({'condition': kind, 'new_logical_batches': 3, 'new_records': 75,
        'input': binding(sample_path), 'prompt': binding(prompt), 'run_directory': str(H / name),
        'command': ['python3', str(H / 'run_production_v32.py'), '--input', str(sample_path),
        '--expected-input-sha256', sample_sha, '--prompt', str(prompt), '--expected-n', '75',
        '--run-name', name, '--batch-size', '25', '--workers', '3', '--max-attempts', '3',
        '--purpose', 'Preselected candidate03 development stability; fixed same 75 records; retain all first-valid and failed attempts; no production replacement or semantic selection']})
plan = {
    'status': 'FROZEN_PLAN_ONLY_AWAITING_ROOT_REVIEW_NO_ADDITIONAL_CALLS_STARTED',
    'created_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'candidate03 development reproducibility and prompt-order sensitivity; not independent validation or adoption',
    'original_preselection': binding(selection_file), 'original_order_design': binding(OLD / 'prompt_order_perturbation_freeze.json'),
    'selection_basis': 'Exact original preselected ID set and original within-batch order; no reselection from candidate03 outputs.',
    'source': binding(source), 'base_prompt': binding(base_path), 'order_prompt': binding(order_path),
    'sample': binding(sample_path), 'sample_n': 75, 'sample_batch_order': [13, 147, 47],
    'original_seed': selection['seed'], 'batches': batch_bindings,
    'sample_department_counts': {'NMPA': 20, 'NHC': 30, 'NHSA': 22, 'GOV': 3},
    'sample_scope_caution': 'Three intact majority-department batches, including 3 GOV rows; not 25 pure rows per department and not a new validation sample.',
    'baseline': {'run': str(H / 'full-corpus-candidate03-material-v14-development'),
                 'production_batches': [13, 147, 47], 'condition': 'Candidate03 original first-valid full-run outputs only after the full run and binding QA close.'},
    'additional_identical_repetitions': 2, 'additional_order_condition_repetitions': 1,
    'order_manipulation': {'prefix': prefix, 'sequence': ['F', 'I', 'Ec', 'E', 'S'],
                           'entire_candidate03_base_prompt_preserved': True, 'same_schema_and_evidence_requirements': True},
    'planned_new_logical_calls': 9, 'maximum_new_technical_attempts': 27,
    'model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'global_concurrency_ceiling': 3,
    'scheduling': 'Do not start until root reviews this frozen plan; default start after full-corpus calls complete so global concurrency stays at 3. Never restart original PTY 2558.',
    'retry_policy': 'At most 3 identical-request technical attempts per logical batch; first technically valid result retained; all failures and semantic disagreements retained; no metric-based rerun.',
    'planned_runs': planned_runs,
    'frozen_components': {name: binding(H / name) for name in ['run_production_v32.py', 'validate_binary_output.py', 'output_schema_codex_compatible.json']},
    'analysis_predeclared': {
        'unit': '75 IDs, five labels each; all dimensions from intact actual rows',
        'identical_prompt': ['base1 vs repeat2', 'base1 vs repeat3', 'repeat2 vs repeat3', 'all-three exact five-dimensional row agreement', 'all-three agreement separately for S,E,Ec,I,F'],
        'order_sensitivity': ['order vs base1', 'order vs repeat2', 'order vs repeat3'],
        'report': ['paired n', 'raw 00/01/10/11', 'percent agreement', 'Cohen kappa with undefined denominators as null/NA', '0-to-1 and 1-to-0 changes', 'all disagreement IDs and untouched reasons/evidence'],
        'main_denominator': 75, 'pooled_label_count': 375,
        'department_descriptive_only': True,
        'forbidden': ['majority-vote replacement of full-run labels', 'selecting a preferred repeat', 'using candidate02 repeats as candidate03 repeats', 'semantic retries', 'accuracy/adoption inference from constructed controls or stability alone']},
    'prediction_outputs_read_for_this_plan': False,
    'additional_model_calls_started': 0,
}
(DEST / 'candidate03_stability_preanalysis_freeze.json').write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'plan': binding(DEST / 'candidate03_stability_preanalysis_freeze.json'), 'sample': binding(sample_path), 'base_prompt': binding(base_path), 'order_prompt': binding(order_path), 'planned_calls': 9, 'max_attempts': 27}, ensure_ascii=False, indent=2))
