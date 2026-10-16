"""Seal version 2 static bindings and existing TOY results; no inference."""
import ast
import copy
import datetime
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if p.name == 'goal-calibration-20261010')
V1 = HERE.parents[1]
BASE = ROOT / '05-validation/rule-request-routing-repair-sol'
VERSION = 'rule-v19-human4-general-repair-development-candidate-2'
NAMES = ('source_packet', 'source_receipts', 'evidence', 'relations', 'dimensions')
CODE_FILES = tuple(n + '.py' for n in NAMES) + ('rule_driver.py', 'interface_common.py')


def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def binding(path):
    p = Path(path).resolve()
    data = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def read(path):
    return json.loads(Path(path).read_text())


def write(name, value):
    with (HERE / name).open('x', encoding='utf8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def anchor(name, func):
    p = HERE / name
    node = next(n for n in ast.walk(ast.parse(p.read_text()))
                if isinstance(n, ast.FunctionDef) and n.name == func)
    return {'path': str(p), 'function': func, 'start_line': node.lineno, 'end_line': node.end_lineno}


final_control = read(HERE / 'control-results-attempt07-independent-gates-final.json')
assert final_control['status'] == 'passed'
assert final_control['constructed_case_N'] == 35
assert final_control['check_N'] == final_control['passed_check_N'] == 228
assert final_control['actual_cohort_inference_runs'] == 0
modules = [binding(HERE / (n + '.py')) | {'module': n} for n in NAMES]
control_bindings_match = all(item == next(b for b in final_control['code_bindings_at_control_import']
                                        if b['module'] == item['module']) for item in modules)
assert control_bindings_match
assert binding(HERE / 'controls.py') == final_control['control_script_binding']
syntax = {}
for name in CODE_FILES + ('controls.py', 'finalize_artifacts.py'):
    p = HERE / name
    compile(p.read_bytes(), str(p), 'exec')
    syntax[name] = True

def helpers(path):
    return {n.name: ast.dump(n, include_attributes=False)
            for n in ast.parse(path.read_text()).body
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name != 'main'}

driver_helpers_unchanged = helpers(BASE / 'rule_driver.py') == helpers(HERE / 'rule_driver.py')
assert driver_helpers_unchanged
unchanged_adapters = {n: (BASE / n).read_bytes() == (HERE / n).read_bytes()
                      for n in ('source_packet.py', 'source_receipts.py', 'evidence.py', 'interface_common.py')}
assert all(unchanged_adapters.values())
inputs = read(V1 / 'input-bindings.json')
unchanged_inputs = [{'before': b, 'after': binding(b['path'])} for b in inputs['inputs']]
assert all(c['before'] == c['after'] for c in unchanged_inputs)
write('input-bindings.json', inputs | {'provenance': binding(V1 / 'input-bindings.json'),
                                    'version_2_uses_no_additional_real_source': True})
write('input-bindings-post-check.json', {'checked': len(unchanged_inputs),
                                       'every_bound_input_unchanged': True, 'checks': unchanged_inputs})
write('algorithm-bindings.json', {'version': 'human4-general-semantic-repair-algorithm-bindings-2',
                                 'algorithm_version': VERSION, 'modules': modules,
                                 'positive_predicate_semantics_modified': True,
                                 'dependency_routing_and_null_scope_modified': True,
                                 'I3_and_F_have_independent_predicates': True,
                                 'formal_freeze_or_execution_authorized': False,
                                 'real_cohort_inference_runs': 0, 'AI_development_repair': True,
                                 'calibration_labels_already_disclosed': True, 'blind_validation': False})
material_evidence = read(V1 / 'material-evidence.json')
write('material-evidence.json', material_evidence | {'provenance': binding(V1 / 'material-evidence.json'),
                                                  'version_2_extra_real_source_read': False})
causes = copy.deepcopy(read(V1 / 'root-causes-and-chains.json'))
for item in causes['root_causes']:
    item['new_code'] = [anchor(Path(a['path']).name, a['function']) for a in item['new_code']]
    if item['target'] == '00138-I':
        item['chain'] = ('当前对已纳入品种实际沟通 → 同源完整同程序唯一位置 → 实際适用范围的创新/改良对象分支'
                         ' → 纳入后具体技术资料反馈或实际技术审评优先沟通机会 → 当前同一实际服务'
                         ' → I3对象—可用安排—直接联系；优先不是I3普遍必要条件。')
    if item['target'] == '00138-F':
        item['chain'] += ' F不以是否出现技术资料反馈段或创新对象为必要条件，须独立满足缺口—当前服务优先机会关系。'
causes['version_1_root_review_refinement'] = {'joint_priority_and_feedback_gate_was_too_strict': True,
                                           'genuine_failing_control': binding(HERE / 'control-results-attempt05-prior-decoupling-failure.json'),
                                           'prior_expectations': binding(HERE / 'dimension-decoupling-prior-expectations.json')}
write('root-causes-and-chains.json', causes)
expectations = read(V1 / 'pre-run-expectations.json')
expectations['provenance'] = binding(V1 / 'pre-run-expectations.json')
expectations['candidate_algorithm_version'] = VERSION
expectations['independent_I3_F_expectations'] = read(HERE / 'dimension-decoupling-prior-expectations.json')['expected_independent_cases']
write('pre-run-expectations.json', expectations)

for base, filename, label in ((BASE, 'actual-candidate.patch', 'request-routing-candidate'),
                              (V1, 'dimension-decoupling.patch', 'preserved-candidate-1')):
    patch = []
    for name in CODE_FILES:
        patch.extend(difflib.unified_diff((base / name).read_text().splitlines(True),
                                        (HERE / name).read_text().splitlines(True),
                                        fromfile=label + '/' + name, tofile='human4-candidate-2/' + name))
    with (HERE / filename).open('x') as stream:
        stream.writelines(patch)

v1_seal = read(V1 / 'seal.json')
v1_files_unchanged = all(binding(b['path']) == b for b in v1_seal['output_files'])
assert v1_files_unchanged
write('preserved-history-bindings.json', {'previous_candidate_seal': binding(V1 / 'seal.json'),
                                        'previous_candidate_all_sealed_files_unchanged': True,
                                        'before_dimension_decoupling_snapshot': binding(V1 / 'snapshots/before-dimension-decoupling/snapshot-bindings.json'),
                                        'attempt05_genuine_failure': binding(HERE / 'control-results-attempt05-prior-decoupling-failure.json'),
                                        'attempt06_result': binding(HERE / 'control-results-attempt06-dimension-decoupled.json'),
                                        'attempt07_final_result': binding(HERE / 'control-results-attempt07-independent-gates-final.json')})
read_N = sum(len(c['source_consumer_read_receipts']) for c in final_control['cases'])
use_N = sum(len(c['source_use_receipts']) for c in final_control['cases'])
report = {'status': 'sealed_AI_development_candidate_2_pending_ROOT_alignment_and_independent_review',
          'created_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'candidate_algorithm_version': VERSION,
          'driver_version': 'formal-freeze-rule-driver-human4-general-repair-candidate-2',
          'real_cohort_inference_runs': 0, 'development_labels_disclosed': True,
          'blind_validation': False, 'formal_validation_complete': False, 'human_validation_complete': False,
          'accuracy_improvement_claimed': False, 'kappa_1_target': False,
          'constructed_case_N': 35, 'check_N': 228, 'passed_check_N': 228,
          'final_control': binding(HERE / 'control-results-attempt07-independent-gates-final.json'),
          'source_receipt_N': read_N, 'source_use_receipt_N': use_N,
          'driver_non_main_helpers_AST_unchanged': driver_helpers_unchanged,
          'four_adapter_and_evidence_modules_byte_identical': unchanged_adapters,
          'syntax_compiles_without_inference': syntax,
          'final_control_import_bindings_match_algorithm': control_bindings_match,
          'all_bound_old_inputs_still_unchanged': True, 'prior_candidate_1_seal_still_valid': True,
          'new_source_v15_read_or_run_in_this_task': False,
          'source_read_limits': 'constructed receipts only; no real native protocol or cohort execution',
          'independent_technical_review': 'pending; no independent review claimed in this seal',
          'version_1_error_disposition': 'preserved; genuine failure and independent-gate correction in version 2',
          'manual_candidate_binding': binding(HERE / 'manual-candidate-binding.json'),
          'driver': binding(HERE / 'rule_driver.py'),
          'algorithm_manifest': binding(HERE / 'algorithm-bindings.json')}
write('report.json', report)
text = f'''v2 通用候选修复已封存，35 个构造案例、228 项检查全部通过。真实 77、800、4481 推断运行均为 0。四项真人复核标签在开发前已披露为 1；本交付是 AI 开发修复，非盲、非正式验证，不以 κ=1 为目标，也不宣称候选比原机器准确。ROOT 尚需独立复核、统一手册与来源版本，并另行授权一次真实 77。

四个原 0 根因和有限证据链见 `root-causes-and-chains.json`，必要同版材料静态引文和来源 SHA 见 `material-evidence.json`。00005-S 只把当前操作性临床优势申请条件接到同版完整定义中的具体药物安全优势分支；03876-Ec 只把当前目录药品分支的实际价格节点接到同版评估价和现场协商；00138-I/F 只把当前对已纳入品种的实际服务接到同一程序、同一阶段的具体可用安排。02573-Ec 的分类及基本药物优先未明示价格、费用或支付标准，先验保持 0。

ROOT 对 v1 指出 I3 被额外要求优先沟通、F 被额外要求技术资料反馈。旧顶层代码、报告、seal、attempt03/04 保留原字节，`snapshots/before-dimension-decoupling` 另存快照。v2 的 `control-results-attempt05-prior-decoupling-failure.json` 保存修改前新反例真实首轮失败（31 案例、181 检查、176 通过），不是事后生成的失败说明。`dimension-decoupling-prior-expectations.json` 保存修正前手册引文、代码 SHA 与手算预期。attempt06 修正后 31 案例、195 检查通过；attempt07 加上名称与排除范围等必要边界，35 案例、228 检查通过。

I3 现在独立要求：实际适用的创新/改良对象分支、当前具体可用技术支持、二者直接相连。支持可为纳入后技术资料反馈，或明确技术审评阶段的实际优先沟通机会；优先不是 I3 普遍必要条件。F 独立要求可辨认治疗缺口与当前同一服务被按需优先配置相连，不依赖技术资料反馈或创新对象。手册候选第124/127/139/155/170/172行的依据全文保存在修正先验文件，手册实际 SHA 为 7bb13ef1a5ad3d230abe5e786eb3dccd1ef4dfdc17a8f8ae4cbf2958d7229a65，仍是 human4 澄清候选，未称 ROOT 正式冻结。

| 构造情形 | I | F |
|---|---:|---:|
|实际创新对象与纳入后技术资料反馈，未优先配置|1|0|
|实际创新对象、治疗缺口及当前优先技术审评沟通，无技术资料段|1|1|
|实际对象无创新/改良，但有治疗缺口及当前优先技术沟通|0|1|
|完整材料有创新对象和缺口，但无当前具体支持/优先机会|0|0|
|程序名称含创新，实际对象普通或明确排除创新，但缺口优先服务真实|0|1|

控制还覆盖名称 alone、无实际措施、一般宗旨、申请前不补纳入后、形式清单、其他药品、缺口无配置、配置无缺口、完整定义含 S/无 S/缺失、评估价与仅资格/阶段/成功状态、错版及无关价格对象、独立 S/E 保持和价格请求只路由 Ec。闭合完整源没有所需实质条件时判语义 0；真正缺确指来源时依法请求/null。已递交来源坐标错误作为技术失败保留，不改称 0/null。

最终控制保存完整虚构 bundle、手算先验、旧/新五维值、实际引文、角色关系、材料请求，以及 {read_N} 条消费者 read receipts、{use_N} 条 use receipts。receipt 来自实际构造执行的 source_view_events，按 inventory 的 resource/view/SHA 和先读后用链接核验。价格控制采用正常 FULLSOURCE payload+paragraphs，未把 PDF SHA 冒充 UTF8 snapshot SHA。没有真实素材 read/use receipts，也未启动真实 native protocol。

`actual-candidate.patch` 是 v2 对原 request-routing 候选真实差异；`dimension-decoupling.patch` 是 v2 对保留 v1 的真实差异。改动局限两个语义模块和驱动候选身份/开发限制。source_packet/source_receipts/evidence/interface_common 字节与基准相同；驱动非 main 辅助函数 AST 一致。精确资产/材料白名单、来源同版及坐标 guard、异常快照、首轮不覆盖和单次真实运行护栏保留。算法没有政策/条款 ID、文本哈希或标签白名单；SHA 只用于来源身份完整性。

21 项旧输入绑定均未改变。此任务未读取或运行共同来源 v15；03876 原旧包缺同版评估价时，预期只 Ec=null 并请求 price_arrangement。ROOT 需共同发布必要物理页8/9/20/21来源后，才能把同版完整材料纳入所有方法。商保推荐目录不自动推实际医保支付、承保或患者可负担。后续独立技术审查由另一代理只读此 seal 后另存报告；本 seal 尚不声称独立验收完成。
'''
with (HERE / 'report.md').open('x', encoding='utf8') as stream:
    stream.write(text)
files = [binding(p) for p in sorted(HERE.iterdir()) if p.is_file()]
seal = {'status': 'sealed_disclosed_label_AI_development_candidate_2_not_ROOT_formal_freeze',
        'sealed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'algorithm_version': VERSION, 'actual_cohort_inference_runs': 0,
        'code_semantics_modified': True, 'non_blind_development': True,
        'formal_validation_complete': False, 'output_files': files}
seal['self_sha256_excluding_field'] = hashlib.sha256(cj(seal).encode()).hexdigest()
write('seal.json', seal)
print(json.dumps({'status': 'sealed', 'algorithm_version': VERSION, 'constructed_case_N': 35,
                  'check_N': 228, 'read_receipt_N': read_N, 'use_receipt_N': use_N,
                  'real_cohort_inference_runs': 0, 'seal_binding': binding(HERE / 'seal.json'),
                  'driver': binding(HERE / 'rule_driver.py'),
                  'algorithm_manifest': binding(HERE / 'algorithm-bindings.json')}, ensure_ascii=False))
