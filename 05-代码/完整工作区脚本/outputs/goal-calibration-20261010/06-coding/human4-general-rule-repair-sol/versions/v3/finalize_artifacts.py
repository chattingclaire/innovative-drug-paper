"""Seal the publication-purpose repair and existing constructed results."""
import ast
import copy
import datetime
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
V2 = HERE.parent / 'v2'
ROOT = next(p for p in HERE.parents if p.name == 'goal-calibration-20261010')
BASE = ROOT / '05-validation/rule-request-routing-repair-sol'
VERSION = 'rule-v19-human4-general-repair-development-candidate-3'
CODE = ['source_packet.py', 'source_receipts.py', 'evidence.py', 'relations.py',
        'dimensions.py', 'rule_driver.py', 'interface_common.py']


def cj(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def binding(path):
    p = Path(path).resolve()
    d = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(d).hexdigest(), 'bytes': len(d)}


def read(path):
    return json.loads(Path(path).read_text())


def write(name, obj):
    with (HERE / name).open('x', encoding='utf8') as f:
        f.write(json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def anchor(name, func):
    p = HERE / name
    node = next(n for n in ast.walk(ast.parse(p.read_text())) if isinstance(n, ast.FunctionDef) and n.name == func)
    return {'path': str(p), 'function': func, 'start_line': node.lineno, 'end_line': node.end_lineno}


def verify_seal(path):
    s = read(path)
    h = s.pop('self_sha256_excluding_field' if 'self_sha256_excluding_field' in s else 'seal_self_sha256')
    assert hashlib.sha256(cj(s).encode()).hexdigest() == h
    assert all(binding(b['path']) == b for b in s['output_files'])


verify_seal(V2 / 'seal.json')
verify_seal(HERE.parents[1] / 'seal.json')
control = read(HERE / 'control-results-attempt11-publication-final.json')
assert control['status'] == 'passed' and control['constructed_case_N'] == 48
assert control['check_N'] == control['passed_check_N'] == 269
assert control['actual_cohort_inference_runs'] == 0
modules = [binding(HERE / n) | {'module': Path(n).stem} for n in CODE[:5]]
assert all(b == next(x for x in control['code_bindings_at_control_import'] if x['module'] == b['module']) for b in modules)
assert control['control_script_binding'] == binding(HERE / 'controls.py')
for name in CODE + ['controls.py', 'finalize_artifacts.py']:
    compile((HERE / name).read_bytes(), str(HERE / name), 'exec')
def helpers(path):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(path.read_text()).body
            if isinstance(n, ast.FunctionDef) and n.name != 'main'}
assert helpers(BASE / 'rule_driver.py') == helpers(HERE / 'rule_driver.py')
unchanged = {n: (BASE / n).read_bytes() == (HERE / n).read_bytes()
             for n in ['source_packet.py', 'source_receipts.py', 'evidence.py', 'interface_common.py']}
assert all(unchanged.values())
assert (V2 / 'relations.py').read_bytes() == (HERE / 'relations.py').read_bytes()
inputs = read(V2 / 'input-bindings.json')
assert all(binding(b['path']) == b for b in inputs['inputs'])
write('input-bindings.json', inputs | {'version_3_no_additional_real_source': True,
                                     'v2_provenance': binding(V2 / 'input-bindings.json'),
                                     'only_additional_input': read(HERE / 'publication-purpose-prior-expectations.json')['independent_bug_reproducer']})
write('algorithm-bindings.json', {'version': 'human4-general-semantic-repair-algorithm-bindings-3',
                                 'algorithm_version': VERSION, 'modules': modules,
                                 'positive_predicate_semantics_modified': True,
                                 'I3_and_F_have_independent_predicates': True,
                                 'publication_purpose_retains_independent_substantive_content': True,
                                 'formal_freeze_or_execution_authorized': False,
                                 'real_cohort_inference_runs': 0, 'AI_development_repair': True,
                                 'calibration_labels_already_disclosed': True, 'blind_validation': False})
write('material-evidence.json', read(V2 / 'material-evidence.json') | {'v2_provenance': binding(V2 / 'material-evidence.json')})
causes = copy.deepcopy(read(V2 / 'root-causes-and-chains.json'))
for cause in causes['root_causes']:
    cause['new_code'] = [anchor(Path(a['path']).name, a['function']) for a in cause['new_code']]
causes['independent_review_S04_repair'] = {'cause': 'publication boundary required 本/该 and missed literal document titles',
                                        'scope': 'current document purpose versus independently enacted content',
                                        'new_code': [anchor('dimensions.py', '_publication_content_spans'),
                                                     anchor('dimensions.py', '_drug_safety_standard')],
                                        'prior_expectations': binding(HERE / 'publication-purpose-prior-expectations.json'),
                                        'genuine_failed_attempt': binding(HERE / 'control-results-attempt08-prior-publication-failure.json')}
write('root-causes-and-chains.json', causes)
expectations = read(V2 / 'pre-run-expectations.json')
write('pre-run-expectations.json', expectations | {'candidate_algorithm_version': VERSION,
                                                  'v2_provenance': binding(V2 / 'pre-run-expectations.json'),
                                                  'S04_scope_prior': binding(HERE / 'publication-purpose-prior-expectations.json')})
for base, filename, label in [(BASE, 'actual-candidate.patch', 'request-routing-candidate'),
                              (V2, 'publication-purpose-repair.patch', 'sealed-candidate-2')]:
    patch = []
    for n in CODE:
        patch.extend(difflib.unified_diff((base / n).read_text().splitlines(True), (HERE / n).read_text().splitlines(True),
                                        fromfile=label + '/' + n, tofile='human4-candidate-3/' + n))
    with (HERE / filename).open('x') as f:
        f.writelines(patch)
read_N = sum(len(c['source_consumer_read_receipts']) for c in control['cases'])
use_N = sum(len(c['source_use_receipts']) for c in control['cases'])
report = {'status': 'sealed_AI_development_candidate_3_pending_independent_fixed_controls_and_ROOT',
          'candidate_algorithm_version': VERSION,
          'driver_version': 'formal-freeze-rule-driver-human4-general-repair-candidate-3',
          'real_cohort_inference_runs': 0, 'development_labels_disclosed': True,
          'blind_validation': False, 'formal_validation_complete': False, 'accuracy_improvement_claimed': False,
          'constructed_case_N': 48, 'check_N': 269, 'passed_check_N': 269,
          'source_read_receipt_N': read_N, 'source_use_receipt_N': use_N,
          'final_control': binding(HERE / 'control-results-attempt11-publication-final.json'),
          'driver': binding(HERE / 'rule_driver.py'), 'algorithm_manifest': binding(HERE / 'algorithm-bindings.json'),
          'v2_seal': binding(V2 / 'seal.json'), 'v2_all_sealed_files_unchanged': True,
          'v1_all_sealed_files_unchanged': True, 'original_21_static_inputs_unchanged': True,
          'driver_non_main_helpers_AST_unchanged': True, 'unchanged_adapters': unchanged,
          'relations_byte_identical_to_v2': True,
          'manual_candidate': read(HERE / 'manual-candidate-binding.json'),
          'independent_review': 'v2 fixed37 found S04; v3 fixed37 plus6 pending, no pass claimed here',
          'real_v15_read_or_run': False, 'kappa_1_target': False}
write('report.json', report)
with (HERE / 'report.md').open('x', encoding='utf8') as f:
    f.write('''v3 修复独立审查发现的具名文件宗旨误判。48 个构造案例、269 项检查全部通过；真实77/800/4481推断均为0。四项开发标签已披露，本交付是AI开发修复，非盲、非正式验证，不宣称准确率提高，也不以κ=1为目标。

原出版边界只识别“制定/印发/发布本或该文件”，使“为…制定具名程序”的纯宗旨落入安全目标正判。v3通用识别具名与书名号文件，先按当前完整命题划定宗旨，再保留独立风险问题、评价/监测要求、触发后果及实际安全检验标准。文件标题里的风险评价词不等于当前设置内容；具体制定药物风险评价/不良反应监测/安全性检验标准仍可S=1。原本/该边界保持，没有硬编码案例名、ID或文本hash。

修复前先验与手册第42/44/62/69/76行引文保存在publication-purpose-prior-expectations.json。attempt08在复制的v2代码上真实执行，46例263检查中259通过、4个宗旨失败；attempt09修复后全部通过。直接检验标准必要控制在attempt10出现1个真实失败并保留；补足当前药物安全标准内容关系后attempt11为48例269检查全通过。完整虚构输入、当前锚点、角色链、请求和read/use receipts均保留，不是实际政策运行。

相对v2只改dimensions的出版内容投影与明确安全标准分支，并同步driver候选3身份；relations和来源adapter未变，驱动非main辅助函数AST、精确资产/材料白名单、来源同版和坐标guard、首轮不可覆盖、单次实际运行护栏均保留。publication-purpose-repair.patch给出与封存v2的最小真实diff；actual-candidate.patch是对原request-routing候选的累计diff。v1、v2全部seal文件及21项旧输入字节复核未改变。

v2的I3/F独立门槛、操作性安全定义和同版实际评估价关系全部保留，四个原0根因及有限材料引文另见root-causes-and-chains.json/material-evidence.json。manualcandidate仍绑定实际SHA 7bb13ef1a5ad3d230abe5e786eb3dccd1ef4dfdc17a8f8ae4cbf2958d7229a65，未称ROOT正式冻结。共同来源v15在本任务未读或run。独立代理将只读v3 seal复跑固定37+6控制；本报告尚不宣称独立通过。ROOT完成来源、手册、代码对齐并另授权前，不运行真实77。
''')
seal = {'status': 'sealed_disclosed_label_AI_development_candidate_3_not_ROOT_formal_freeze',
        'sealed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'algorithm_version': VERSION, 'actual_cohort_inference_runs': 0, 'non_blind_development': True,
        'formal_validation_complete': False,
        'output_files': [binding(p) for p in sorted(HERE.iterdir()) if p.is_file()]}
seal['self_sha256_excluding_field'] = hashlib.sha256(cj(seal).encode()).hexdigest()
write('seal.json', seal)
verify_seal(HERE / 'seal.json')
print(json.dumps({'status': 'sealed', 'algorithm_version': VERSION, 'seal': binding(HERE / 'seal.json'),
                  'driver': binding(HERE / 'rule_driver.py'), 'algorithm_manifest': binding(HERE / 'algorithm-bindings.json'),
                  'dimensions': binding(HERE / 'dimensions.py'), 'constructed_case_N': 48, 'check_N': 269,
                  'real_cohort_inference_runs': 0}, ensure_ascii=False))
