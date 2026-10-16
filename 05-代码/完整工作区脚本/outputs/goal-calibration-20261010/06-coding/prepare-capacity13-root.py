from pathlib import Path
import ast
import datetime
import difflib
import hashlib
import json

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OLD = ROOT / '06-coding/full4481-cli-fixed-batch-scheduler-v2-root'
NEW = ROOT / '06-coding/full4481-cli-fixed-batch-scheduler-v3-capacity13-root'

def bind(p):
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def save(p, v):
    with p.open('x', encoding='utf-8') as f:
        json.dump(v, f, ensure_ascii=False, indent=2)
        f.write('\n')

seal = json.loads((OLD / 'seal.json').read_text())
for name in ('scheduler.py', 'input-bindings.json'):
    p = OLD / name
    expected = next(x for x in seal['output_members'] if x['path'] == str(p))
    assert bind(p) == expected
old_code = (OLD / 'scheduler.py').read_text()
replacements = {'max_concurrent_cli=3, input_bindings=': 'max_concurrent_cli=13, input_bindings=',
                'len(active) < 3:': 'len(active) < 13:'}
new_code = old_code
for before, after in replacements.items():
    assert new_code.count(before) == 1
    new_code = new_code.replace(before, after)
ast.parse(new_code)
old_config = json.loads((OLD / 'input-bindings.json').read_text())
new_config = json.loads(json.dumps(old_config))
assert old_config['max_concurrent_cli'] == 3
new_config['max_concurrent_cli'] = 13
new_config['version'] = 'full4481-fixed-batch-scheduler-input-bindings-3-capacity13'
for k in old_config:
    if k not in {'max_concurrent_cli', 'version'}:
        assert old_config[k] == new_config[k]
NEW.mkdir(exist_ok=False)
(NEW / 'scheduler.py').write_text(new_code, encoding='utf-8')
save(NEW / 'input-bindings.json', new_config)
amendment = {
    'artifact_type': 'ROOT_nonsemantic_CLI_capacity_amendment',
    'prepared_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'old_capacity': 3, 'new_capacity': 13,
    'user_authorization': 'Earlier user explicitly requested parallel execution of 13 batches; Goal permits parallel tasks.',
    'scope': 'Same fixed 504 primary full4481 batches. Dispatch only from unused technically ready slots after old owned children terminate.',
    'old_controller_and_inputs': [bind(OLD / name) for name in ('scheduler.py','input-bindings.json','seal.json')],
    'code_diff': list(difflib.unified_diff(old_code.splitlines(), new_code.splitlines(), fromfile='v2-capacity3', tofile='v3-capacity13', lineterm='')),
    'changed_config_keys': ['version','max_concurrent_cli'],
    'batch_assignment_and_all_core_inputs_unchanged': True,
    'runner_receiver_attempt_limit_and_whole_first_selection_unchanged': True,
    'model_prompt_manual_materials_and_label_criteria_unchanged': True,
    'old_controller_in_place_edited': False,
    'transition_rule': 'Signal only live old controller to drain. Confirm its actual terminal handle and zero owned runners, inspect all launched attempt receptions, and confirm no other coding CLI live before new GO.',
    'failure_rule': 'Preserve all actual attempts. No model-output comparison or label-driven retry. Any uncertain technical state stops new dispatch.',
    'actual_model_processes_started_by_preparation': 0, 'GO_issued': False,
}
save(NEW / 'CLI-concurrency-amendment-13.json', amendment)
(NEW / 'README.txt').write_text('容量13的非语义调度副本。手册、prompt、模型请求、504批固定材料、三次技术尝试上限与首个完整有效批次选择均不变。准备并不等于运行。旧控制器只排空既有子进程，经ROOT核验终止和所有实际接收后，才允许新GO。未完成的批次不算完成；NULL不补0。\n', encoding='utf-8')
save(NEW / 'seal.json', {
    'artifact_type': 'ROOT_capacity13_preparation_seal',
    'input_members': [bind(OLD / name) for name in ('scheduler.py','input-bindings.json','seal.json')],
    'output_members': [bind(NEW / name) for name in ('scheduler.py','input-bindings.json','CLI-concurrency-amendment-13.json','README.txt')],
    'AST_passed': True, 'only_two_capacity_literals_changed': True,
    'core_inputs_and_fixed_batches_exactly_preserved': True,
    'actual_model_processes_started': 0, 'GO_issued': False,
})
print(json.dumps({'directory': str(NEW), 'scheduler': bind(NEW/'scheduler.py'), 'seal': bind(NEW/'seal.json'), 'GO_issued':False}, ensure_ascii=False))
