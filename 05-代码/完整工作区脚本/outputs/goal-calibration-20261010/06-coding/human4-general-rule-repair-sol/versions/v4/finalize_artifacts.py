"""Seal one modal projection repair without any real cohort execution."""
import ast
import datetime
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V3 = HERE.parent / 'v3'
ROOT = next(p for p in HERE.parents if p.name == 'goal-calibration-20261010')
BASE = ROOT / '05-validation/rule-request-routing-repair-sol'
VERSION = 'rule-v19-human4-general-repair-development-candidate-4'
FILES = ['source_packet.py', 'source_receipts.py', 'evidence.py', 'relations.py',
         'dimensions.py', 'rule_driver.py', 'interface_common.py']


def binding(path):
    p = Path(path).resolve()
    d = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(d).hexdigest(), 'bytes': len(d)}


def read(path):
    return json.loads(Path(path).read_text())


def cj(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def write(name, obj):
    with (HERE / name).open('x', encoding='utf8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


seal3 = read(V3 / 'seal.json')
h = seal3.pop('self_sha256_excluding_field')
assert hashlib.sha256(cj(seal3).encode()).hexdigest() == h
assert all(binding(b['path']) == b for b in seal3['output_files'])
control = read(HERE / 'control-results-attempt13-modal-final.json')
assert control['status'] == 'passed' and control['constructed_case_N'] == 49
assert control['check_N'] == control['passed_check_N'] == 272
modules = [binding(HERE / n) | {'module': Path(n).stem} for n in FILES[:5]]
assert all(b == next(x for x in control['code_bindings_at_control_import'] if x['module'] == b['module']) for b in modules)
assert binding(HERE / 'controls.py') == control['control_script_binding']
for n in FILES + ['controls.py', 'finalize_artifacts.py']:
    compile((HERE / n).read_bytes(), str(HERE / n), 'exec')
def helpers(path):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name != 'main'}
assert helpers(V3 / 'rule_driver.py') == helpers(HERE / 'rule_driver.py')
unchanged = {n: (V3 / n).read_bytes() == (HERE / n).read_bytes()
             for n in ['source_packet.py', 'source_receipts.py', 'evidence.py', 'relations.py', 'interface_common.py']}
assert all(unchanged.values())
inputs = read(V3 / 'input-bindings.json')
assert all(binding(b['path']) == b for b in inputs['inputs'])
write('input-bindings.json', inputs | {'v3_provenance': binding(V3 / 'input-bindings.json'),
                                     'v4_only_additional_TOY_bug': read(HERE / 'modal-prior-expectations.json')['bug_binding'],
                                     'new_real_sources_read_or_run': False})
write('algorithm-bindings.json', {'version': 'human4-general-semantic-repair-algorithm-bindings-4',
                                 'algorithm_version': VERSION, 'modules': modules,
                                 'formal_freeze_or_execution_authorized': False,
                                 'real_cohort_inference_runs': 0, 'AI_development_repair': True,
                                 'calibration_labels_already_disclosed': True, 'blind_validation': False,
                                 'relative_to_v3': 'only retain 需要/需 + substantive action in current publication content projection'})
write('evidence-and-prior-bindings.json', {'v3_seal': binding(V3 / 'seal.json'),
                                         'original_four_root_causes_and_chains': binding(V3 / 'root-causes-and-chains.json'),
                                         'allowed_material_evidence': binding(V3 / 'material-evidence.json'),
                                         'real_run_prior_expectations': binding(V3 / 'pre-run-expectations.json'),
                                         'new_single_branch_prior': binding(HERE / 'modal-prior-expectations.json'),
                                         'old_actual_failed_control': binding(HERE / 'control-results-attempt12-prior-modal-failure.json')})
for base, name, label in [(V3, 'modal-repair.patch', 'sealed-v3'), (BASE, 'actual-candidate.patch', 'request-routing-candidate')]:
    patch = []
    for n in FILES:
        patch.extend(difflib.unified_diff((base / n).read_text().splitlines(True), (HERE / n).read_text().splitlines(True),
                                        fromfile=label + '/' + n, tofile='human4-candidate-4/' + n))
    with (HERE / name).open('x') as f:
        f.writelines(patch)
report = {'status': 'sealed_development_candidate_4_pending_fixed43_independent_review_and_ROOT',
          'algorithm_version': VERSION, 'driver_version': 'formal-freeze-rule-driver-human4-general-repair-candidate-4',
          'real_cohort_inference_runs': 0, 'AI_development_repair': True,
          'labels_disclosed': True, 'blind_validation': False, 'formal_validation_complete': False,
          'accuracy_improvement_claimed': False, 'kappa_1_target': False,
          'constructed_case_N': 49, 'check_N': 272, 'passed_check_N': 272,
          'v3_all_sealed_files_unchanged': True, 'original_21_static_inputs_unchanged': True,
          'driver_non_main_helpers_AST_unchanged': True, 'unchanged_modules_vs_v3': unchanged,
          'final_control': binding(HERE / 'control-results-attempt13-modal-final.json'),
          'manual_candidate': read(HERE / 'manual-candidate-binding.json'),
          'single_point_change': 'needs modal independent content branch; generic and all other predicates unchanged',
          'independent_fixed43_status': 'pending v4 review; v3 failed P03 preserved'}
write('report.json', report)
with (HERE / 'report.md').open('x', encoding='utf8') as f:
    f.write('''v4单点保留出版宗旨句内“需要/需 + 实质动作”的独立内容要求，generic和其他维度谓词未改。P03当前“需要评价药物安全性”交原有评价判据消费；纯宗旨与文件后文不因此借成标签。v3原seal全部字节不变。

先验和独立原失败绑定见modal-prior-expectations.json。复制v3后的真实attempt12为49例272检查中271通过、仅P03失败；修改后attempt13的49例272检查全部通过。原48控制保持，只加固定P03。modal-repair.patch仅有该一行语义变化及候选4身份同步。原四项根因、有限材料引文及真实运行先验指向已封存v3文件，见evidence-and-prior-bindings.json。

这是标签已披露的AI开发修复，非盲、非正式验证，不宣称准确率提升。manualcandidate仍绑定7bb13ef1a5ad3d230abe5e786eb3dccd1ef4dfdc17a8f8ae4cbf2958d7229a65。独立代理将复跑同一43固定集；此seal未宣称独立通过。真实77/800/4481运行均为0，待ROOT对齐并另行授权。
''')
seal = {'status': 'sealed_disclosed_label_AI_development_candidate_4_not_ROOT_formal_freeze',
        'sealed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'algorithm_version': VERSION, 'actual_cohort_inference_runs': 0, 'non_blind_development': True,
        'formal_validation_complete': False,
        'output_files': [binding(p) for p in sorted(HERE.iterdir()) if p.is_file()]}
seal['self_sha256_excluding_field'] = hashlib.sha256(cj(seal).encode()).hexdigest()
write('seal.json', seal)
print(json.dumps({'seal': binding(HERE / 'seal.json'), 'driver': binding(HERE / 'rule_driver.py'),
                  'manifest': binding(HERE / 'algorithm-bindings.json'), 'dimensions': binding(HERE / 'dimensions.py'),
                  'constructed_case_N': 49, 'check_N': 272, 'real_cohort_inference_runs': 0}, ensure_ascii=False))
