"""Seal existing finite execution evidence. Never execute a classifier here."""
import ast
import collections
import difflib
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

P = Path(__file__).resolve().parent
G = P.parents[3]
B = P.parent / 'joint-v2-geometry01'
NAMES = ('source_packet.py', 'source_receipts.py', 'evidence.py', 'relations.py', 'dimensions.py')
DIMS = ('S', 'E', 'Ec', 'I', 'F')
MANUAL = G / '03-manual/full4481-common-release-20261010-root/manual.txt'

def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}

def load(path):
    return json.loads(Path(path).read_bytes())

def save(name, data):
    if (P / name).exists():
        assert cj(load(P / name)) == cj(data), 'Partial finalizer output differs: ' + name
        return
    with (P / name).open('x', encoding='utf8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def cj(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def verify_binding(value):
    actual = bind(value['path'])
    return actual['sha256'] == value['sha256'] and actual['bytes'] == value['bytes']

def functions(tree):
    out = {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out[node.name] = node
        elif isinstance(node, ast.ClassDef):
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out[node.name + '.' + child.name] = child
    return out

def syntax_hash(node):
    return hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()

now = datetime.now(timezone.utc).isoformat()
assert bind(MANUAL)['sha256'] == '5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
baseline = load(P / 'baseline-input-bindings.json')
assert verify_binding(baseline['baseline_preseal'])
assert all(verify_binding(v) for v in baseline['baseline_members'])
audit = load(P / 'independent20-reception-bindings.json')
assert verify_binding(audit['seal']) and all(verify_binding(v) for v in audit['members'])
fixed = load(P / 'control-pre-edit-seal.json')
assert all(verify_binding(fixed[k]) for k in ('builder', 'controls', 'manual_basis'))
for value in fixed['baseline_modules']:
    historical = bind(P / 'baseline-code-snapshot' / Path(value['path']).name)
    assert historical['sha256'] == value['sha256'] and historical['bytes'] == value['bytes']

function_rows = []
constant_rows = []
module_rows = []
for name in NAMES:
    old_text = (P / 'baseline-code-snapshot' / name).read_text()
    new_text = (P / name).read_text()
    old_tree, new_tree = ast.parse(old_text), ast.parse(new_text)
    old, new = functions(old_tree), functions(new_tree)
    effective = []
    for key in sorted(set(old) | set(new)):
        status = 'added' if key not in old else 'removed' if key not in new else 'unchanged' if syntax_hash(old[key]) == syntax_hash(new[key]) else 'changed'
        row = {'module': name, 'function': key, 'status': status,
               'baseline_AST_sha256': syntax_hash(old[key]) if key in old else None,
               'candidate_AST_sha256': syntax_hash(new[key]) if key in new else None,
               'baseline_lines_inclusive': [old[key].lineno, old[key].end_lineno] if key in old else None,
               'candidate_lines_inclusive': [new[key].lineno, new[key].end_lineno] if key in new else None}
        function_rows.append(row)
        if status != 'unchanged':
            effective.append(key)
    old_const = [n for n in old_tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))]
    new_const = [n for n in new_tree.body if isinstance(n, (ast.Assign, ast.AnnAssign))]
    assert [syntax_hash(n) for n in old_const] == [syntax_hash(n) for n in new_const]
    constant_rows.append({'module': name, 'all_top_level_assignment_AST_unchanged': True, 'assignment_count': len(old_const)})
    module_rows.append({'module': name, 'baseline': bind(P / 'baseline-code-snapshot' / name), 'candidate': bind(P / name), 'effective_function_changes': effective})
    if old_text != new_text and not (P / (name + '.relative-to-joint-v2.patch')).exists():
        with (P / (name + '.relative-to-joint-v2.patch')).open('x', encoding='utf8') as f:
            f.writelines(difflib.unified_diff(old_text.splitlines(keepends=True), new_text.splitlines(keepends=True), fromfile='joint-v2-geometry01/' + name, tofile='joint-v3-interface-sol/' + name))
assert (P / 'regression_tests.py').read_bytes() == (P / 'baseline-code-snapshot/regression_tests.py').read_bytes()
save('function-diff.json', {'identity': 'nonhuman function-level mechanical comparison', 'modules': module_rows, 'functions': function_rows, 'constants': constant_rows,
     'shared_add_units_generic_source_modules_unchanged': [r for r in function_rows if r['function'] in ('RelationView._add', '_units', '_generic') or r['module'] in NAMES[:3]],
     'no_top_level_constant_changes': True})
with (P / 'function-diff.md').open('w', encoding='utf8') as f:
    f.write('候选相对 joint-v2-geometry01 的有效函数变化（非真人机械比对）。所有顶层常量 AST 不变。\n\n|文件|函数|变化|当前行|\n|---|---|---|---|\n')
    for r in function_rows:
        if r['status'] != 'unchanged':
            f.write('|%s|%s|%s|%s|\n' % (r['module'], r['function'], r['status'], r['candidate_lines_inclusive']))
    f.write('\n_add 身份规范、_units 边界引文排除、_generic 内部消费者交集及三个来源/证据模块均未改变。judge 改为逐项调用内部已分维授权的 generic；未将关系权限统一扩大为五维。\n')

raw_manual = MANUAL.read_text()
manual_lines = raw_manual.splitlines(keepends=True)
quotes = []
for line in (9, 11, 15, 29, 30, 33, 40, 41, 46, 50, 52, 124, 127, 139, 158, 170, 214):
    a = sum(map(len, manual_lines[:line-1])); text = manual_lines[line-1].rstrip('\r\n'); b = a + len(text)
    assert raw_manual[a:b] == text
    ua, ub = len(raw_manual[:a].encode()), len(raw_manual[:b].encode())
    assert MANUAL.read_bytes()[ua:ub].decode() == text
    quotes.append({'line': line, 'text': text, 'unicode_code_point_interval_half_open': [a, b], 'utf8_byte_interval_half_open': [ua, ub], 'source_binding': bind(MANUAL)})
save('manual-basis-final.json', {'manual': bind(MANUAL), 'quotes': quotes, 'definition_changed': False,
     'prior_manual_path_explanation': 'pre-edit 笔记引用候选材料目录的逐字同SHA手册；本候选最终绑定原冻结release手册。未接入候选材料或改手册。'})

run_dirs = [x for x in P.iterdir() if x.is_dir() and (x.name.startswith(('baseline-', 'attempt', 'final-'))) and (x / 'summary.json').exists()]
runs = []
for directory in sorted(run_dirs):
    summary = load(directory / 'summary.json')
    for name in NAMES:
        if directory.name.startswith('final-'):
            assert bind(directory / 'code-snapshot' / name)['sha256'] == bind(P / name)['sha256']
    if not (directory / 'output-seal.json').exists():
        members_before_open = [bind(x) for x in sorted(directory.rglob('*')) if x.is_file()]
        with (directory / 'output-seal.json').open('x', encoding='utf8') as f:
            json.dump({'identity': 'post-execution byte reception of unchanged original75 script outputs; not a pre-execution seal', 'output_members': members_before_open, 'self_excluded': True}, f, ensure_ascii=False, indent=2)
            f.write('\n')
    seal = load(directory / 'output-seal.json')
    failed_members = [v for v in seal['output_members'] if not verify_binding(v)]
    corrected_receipt = None
    if failed_members:
        # First finalizer opened this receipt before collecting original75 members,
        # so it accidentally bound its empty self. Preserve that failed artifact.
        assert all(Path(v['path']) == directory / 'output-seal.json' and v['bytes'] == 0 for v in failed_members)
        assert all(verify_binding(v) for v in seal['output_members'] if v not in failed_members)
        corrected_receipt = directory / 'post-execution-corrected-receipt.json'
        if not corrected_receipt.exists():
            receipt_members = [bind(x) for x in sorted(directory.rglob('*')) if x.is_file()]
            with corrected_receipt.open('x', encoding='utf8') as f:
                json.dump({'identity': 'post-execution corrected readback receipt; classifier outputs/code unchanged', 'reason': 'First documentation finalizer accidentally included empty own receipt before completing its write. Old faulty receipt retained, no classification rerun.', 'original_faulty_receipt': bind(directory / 'output-seal.json'), 'failed_self_member': failed_members, 'output_members': receipt_members, 'self_excluded': True}, f, ensure_ascii=False, indent=2)
                f.write('\n')
        assert all(verify_binding(v) for v in load(corrected_receipt)['output_members'])
    runs.append({'run': directory.name, 'summary': summary, 'summary_binding': bind(directory / 'summary.json'), 'results_binding': bind(directory / 'results.json'), 'output_seal': bind(directory / 'output-seal.json'),
                 'pre_execution_seal': bind(directory / 'pre-execution-seal.json') if (directory / 'pre-execution-seal.json').exists() else None,
                 'code_snapshot': [bind(directory / 'code-snapshot' / name) for name in NAMES],
                 'corrected_readback_receipt': bind(corrected_receipt) if corrected_receipt else None})

parent_controls_path = B / 'joint-parent235-root-replay01/controls-fixed-before-joint-execution.json'
parent_old_path = B / 'joint-parent235-root-replay01/results.json'
parent_controls = load(parent_controls_path)['cases']
parent_old = load(parent_old_path)
parent_new = load(P / 'final-parent235/results.json')
assert len(parent_controls) == len(parent_old) == len(parent_new) == 235
changed = []
for i, (control, old, new) in enumerate(zip(parent_controls, parent_old, parent_new)):
    assert new['name'] == old['name'] == control['name'] and new['suite'] == old['suite'] == control['suite']
    assert cj(new['expected']) == cj(old['expected']) == cj(control['expected'])
    assert cj(new['semantic_input']) == cj(control['semantic_input'])
    assert cj(new['operations']) == cj(control.get('post_view_operations', []))
    before = {d: old['decisions'][d]['value'] for d in DIMS}
    after = {d: new['decisions'][d]['value'] for d in DIMS}
    if before == after:
        continue
    changed_dims = [d for d in DIMS if before[d] != after[d]]
    assert set(changed_dims) <= {'I', 'F'}
    new_requests = [r for r in new['material_requests'] if r.get('stop_scope') == 'exact current operative reference; no absence-as-zero']
    assert new_requests and all(set(r['dimensions']) <= {'I', 'F'} for r in new_requests)
    for dimension in changed_dims:
        assert before[dimension] == 0 and after[dimension] is None
        assert any(dimension in r['dimensions'] for r in new_requests)
    contexts = new['semantic_input']['contexts']
    reference_kinds = sorted({r.get('reference', '') for r in new_requests})
    if any('章节' in r for r in reference_kinds):
        category = '确指章节地址/同源范围未唯一闭合'
        why = '当前将本文件确指章节整体条件作为药品申请条件，未限定为单一非I/F议题；地址、成员或同源末界不成立时，该范围可能具有I/F内容，不能由已供局部内容宣称整范围I/F均不在场。'
    elif any('款' in r for r in reference_kinds):
        category = '确指款次内容或本款边界未闭合'
        why = '当前以确指款是否满足决定申请/实质待遇；只登记该款I/F消费者，不借兄弟款补条件。该款不在包内、款次不一致或自己的真实末界未核明时，未知不能填0。'
    else:
        category = '确指整条缺成员/末界/同源闭合'
        why = '当前明确要求符合确指整条实质条件且没有仅安全/疗效/价格等范围限定；已供局部成员不足以证明整条I/F无内容。该条未唯一完整闭合时，仅新增这条操作性标准的I/F未知依赖。'
    if before['I'] == 1 and after['I'] == 1:
        why += ' 当前基础创新资格—保护期分支已独立表达I，故I=1保持；未知例外不覆盖已知基础分支。例外原文的儿科研究身份并未被直接当F=1；未知只表示本款完整范围尚未证实。'
    if all(before[d] == after[d] == 1 for d in ('S', 'E', 'Ec')):
        why += ' 另一已供条文已独立建立S/E/Ec阳性，这三维保持1；没有把一条未知依赖清空全部可判分支。'
    changed.append({'index_zero_based': i, 'suite': new['suite'], 'name': new['name'], 'original_expected': new['expected'], 'before_five_values': before, 'after_five_values': after,
                    'changed_dimensions': changed_dims, 'category': category, 'reason': why, 'current_text': new['semantic_input']['text'],
                    'current_source_ref': new['semantic_input']['source_ref'], 'contexts_as_supplied': contexts, 'new_IF_operational_requests': new_requests,
                    'all_material_requests_retained': new['material_requests'], 'all_source_requests_retained': new['source_requests'],
                    'original_control_artifact': control['original_control_artifact'], 'final_results_location': {'binding': bind(P / 'final-parent235/results.json'), 'array_index': i},
                    'manual_basis_lines': [40, 41, 50, 214], 'is_independent_truth': False})
assert len(changed) == 29

new18 = load(P / 'final-controls18/results.json')
controls18 = load(P / 'controls18-fixed-before-edit.json')['cases']
assert len(new18) == len(controls18) == 18
for result, control in zip(new18, controls18):
    assert cj(result['expected']) == cj(control['expected'])
    assert cj(result['semantic_input']) == cj(control['synthetic_input'])
original20_path = G / '08-audits/five-dimension-joint-independent-controls-sol/controls20-fixed-before-execution.json'
original20 = load(original20_path)['cases']; result20 = load(P / 'final-independent20/results.json')
assert len(original20) == len(result20) == 20
for control, result in zip(original20, result20):
    assert cj(control['expected_values_fixed_before_execution']) == cj(result['expected'])
special20 = next(r for r in result20 if r['name'] == 'article10_supplied_article12_still_stopped')
assert special20['decisions']['S']['value'] == 1 and special20['decisions']['I']['value'] is None and special20['decisions']['F']['value'] is None
assert any('12' in r.get('reference', '') for r in special20['material_requests'])
assert any(r.get('dependency_status') == 'resolved' and r.get('reference_article') == 10 for r in special20['source_requests'])
save('dependency-consumer-review.json', {'identity': '非真人开发语义解释；原预期不是金标准', 'rules': [
    '新增未知只由本次 _se_operational_references 已定位的当前操作性确指标准触发。未将所有旧material/source请求改成I/F或五维。',
    '当前明示安全/疗效/经济等主题限定时，I/F消费者取主题交集；typed affected_dimensions 与 only_IF_consumers 仍取交集。',
    '完整闭合只使实际被援引内容可见，不直接赋值；明确款次仅消费该款，下一款/下一条只能作边界。',
    '未知没有捐出阳性。已知分支1不被另一未知分支清空，resolved第10条不清除stopped第12条。'],
    'changed_parent235_case_N': len(changed), 'changed_parent235_cases': changed,
    'original20_S_expectation_boundary': {'original_expected': special20['expected'], 'actual_values': {d: special20['decisions'][d]['value'] for d in DIMS},
       'current_and_supplied_contexts': special20['semantic_input'], 'S_known_evidence': special20['decisions']['S'], 'material_requests': special20['material_requests'], 'source_requests': special20['source_requests'],
       'reason': '完整同版第10条明示药物过敏风险指标，应S=1；第12条未供，I/F保持NULL。保留原S=NULL预期及实际差异，不为匹配清空独立S证据。', 'manual_basis_lines': [9, 40, 41, 214]},
    'protection_exception_reason': next(r for r in changed if r['index_zero_based'] == 171),
    'manual_binding': bind(MANUAL)})

source75 = load(P / 'final-original75/results.json')
packet_bindings = {r['binding']['path']: r['binding'] for r in source75 if r.get('binding')}
assert all(verify_binding(v) for v in packet_bindings.values())
actual_ids75 = sorted(Path(k).stem for k in packet_bindings)
original_artifacts = {c['original_control_artifact']['binding']['path']: c['original_control_artifact']['binding'] for c in parent_controls}
assert all(verify_binding(v) for v in original_artifacts.values())
save('source-reading-log.json', {'identity': '非真人有限开发来源读取记录', 'new_actual_source_ids': [], 'new_policy_semantic_reads_outside_authorized_prior_fixtures': [],
    'new18_and_independent20_are_synthetic': True, '75_existing_packet_fixture_source_ids': actual_ids75, '75_packet_byte_bindings': list(packet_bindings.values()),
    '235_existing_finite_control_artifacts': list(original_artifacts.values()), '235_identity_removed_interface': '235 semantic_input 已按原固定接口移除记录ID；不由案例名称推断新source_id，具体来源沿原固定控制artifact/index追踪。',
    'actual_sources_already_development_exposed': True, 'main_full_LLM_partial_results_read': False, 'hidden12_read': False,
    'classifier_source_ref_absolute_paths': '仅作引用溯源；18/20/235分类阶段 open 审计钩子拒绝任何文件访问，0尝试。75只复用原脚本既定冻结packet夹具加载；未新增原件读取。',
    'new_material_release_adopted': False})

final_summaries = {name: load(P / name / 'summary.json') for name in ('final-controls18', 'final-independent20', 'final-parent235', 'final-original75')}
failure_rows = []
for suite in ('final-controls18', 'final-independent20', 'final-parent235'):
    for i, row in enumerate(load(P / suite / 'results.json')):
        if not row['passed']:
            failure_rows.append({'suite': suite, 'index_zero_based': i, 'name': row['name'], 'expected': row['expected'], 'actual_values': {d: row['decisions'][d]['value'] for d in DIMS},
                                 'mismatches': row['mismatches'], 'results_location': {'binding': bind(P / suite / 'results.json'), 'array_index': i}, 'original_expected_unchanged': True})
save('finite-runs-reception.json', {'runs': runs, 'all_attempts_preserved': True, 'final_summaries': final_summaries,
   'fixed_controls_binding': fixed['controls'], 'original20_binding': bind(original20_path), 'parent235_original_controls_binding': bind(parent_controls_path),
   'expected_values_and_semantic_inputs_unchanged_verified': True, 'classifier_open_attempts_18_20_235': [], 'all_failed_final_controls': failure_rows,
   'first_failure_paths': [str(P / 'baseline-controls18/results.json'), str(P / 'attempt01-controls18/results.json'), str(P / 'attempt01-independent20/results.json'), str(P / 'attempt02-parent235/results.json')],
   'not_formal_accuracy_or_independent_test': True})
algorithm = {'status': 'sealed_joint_developer_candidate_not_a_formal_release', 'at_utc': now, 'five_modules': [bind(P / n) for n in NAMES],
    'manual': bind(MANUAL), 'definition_changes': False, 'baseline_preseal': baseline['baseline_preseal'], 'independent20_output_seal': audit['seal'],
    'regression_tests_original75': bind(P / 'regression_tests.py'), 'new18_fixed_pre_edit': fixed['controls'], 'new18_pre_edit_seal': bind(P / 'control-pre-edit-seal.json'),
    'typed_subset_and_only_IF_intersection_preserved': True, 'source_packet_evidence_receipts_unchanged': True, 'new_neutral_material_projection': False,
    'new_cohort_77_800_4481_run': False, 'main_full_LLM_partial_results_read': False, 'hidden12_read': False, 'cohort_predictions_or_formal_acceptance': False,
    'new_actual_source_ids': []}
if (P / 'algorithm-bindings.json').exists():
    sealed_algorithm = load(P / 'algorithm-bindings.json')
    assert sealed_algorithm['five_modules'] == algorithm['five_modules'] and sealed_algorithm['manual'] == algorithm['manual']
    assert verify_binding(sealed_algorithm['baseline_preseal'])
    assert all(verify_binding(v) for v in sealed_algorithm['common_frozen_input_bindings'])
    assert verify_binding(bind(P / 'pre-execution-seal.json'))
else:
    save('algorithm-bindings.json', algorithm)
save('summary.json', {'identity': '非真人AI开发候选，不是人审/独立真值/正式准确率', 'candidate': str(P), 'baseline': str(B), 'GO': False,
     'finite_results': {'fixed18': {'case_N': 18, 'matched': 18}, 'original20': {'case_N': 20, 'matched': 19}, 'original235': {'case_N': 235, 'matched': 227}, 'original75': {'case_N': 75, 'matched': 75}},
     'exceptions_18_20_235': 0, 'quote_validation_passed_18_20_235': 273, '75_pass_N': 75, 'final_failure_cases': failure_rows,
     'parent235_before_to_after_changed_case_N': 29, 'new_parent235_expected_mismatch_N': 1,
     'remaining': ['原20 S预期NULL/实际1解释边界', '既有有限输入缺闭合NULL、foreign F边界、payment原件坐标冲突原差异', 'protection例外完整款范围未闭合导致F=NULL，I基础分支1保持'],
     'scope': '仅18/20/235/75有限已暴露开发回归；没有77/800/4481、新模型、采样或新材料部署。', 'new_actual_source_ids': [], 'original_expectations_and_frozen_inputs_preserved': True})
with (P / 'README.md').open('x', encoding='utf8') as f:
    f.write('joint-v3-interface-sol 已封存为非真人开发候选，GO=false。手册和材料均保持原冻结版本，尚未部署。\n\n')
    f.write('实现当前创新研发对象—实际反馈/相对普通程序缩短时限、同版同阶段具名反馈有限承接、完整确指条款的I/F实际内容消费，以及文件名/签章形式排除。未把所有关系权限改成五维；_add身份规范、_units、_generic与三来源/证据模块不变。\n\n')
    f.write('款次1/一/第一款正规化只解释同一已供接口标签；原文条款冲突拒绝承接，完整原件成员、同源同组件和真实下一条/款边界仍必须成立。未改控制来制造闭合。\n\n')
    f.write('有限开发回放：新18为18/18；原20为19/20；原235为227/235；原75为75/75。原预期全保留。这些计数不能作为正式准确率。原20剩余S=NULL预期/实际1来自已供第10条过敏风险，I/F仍因第12条缺失而NULL。\n\n')
    f.write('原235相对基线29条仅I/F从0转NULL，详见dependency-consumer-review.json。未知仅指向当前实质申请/待遇援引的确切标准；已知S/E/Ec或I分支1保持。新增protection例F=NULL差异保留：引用例外款虽有一句儿科研究文字但无本款完整末界，不能据局部句宣称F=0，也没有按儿科身份赋F=1。其原I=1基础分支保持。既有缺闭合、foreign边界及payment坐标冲突差异未硬调。\n\n')
    f.write('baseline-controls18及attempt01/02/03均保留第一次与中间失败和代码快照；final-*为当前算法字节执行结果。18/20/235分类时任何open访问都会阻断，实际0访问尝试；source_ref合成原件路径未用来补输入。隐藏12未读取，新增真实source_id为0。\n\n')
    f.write('algorithm-bindings.json给五模块精确字节；function-diff.json/.md与两patch给有效函数变化；finite-runs-reception.json给全部运行及失败位置；source-reading-log.json给旧开发夹具来源。ROOT另行独立审查后再决定后续候选冻结，不能将本候选视作共同材料新release或正式验收。\n')

save('candidate-seal.json', {'status': 'sealed_not_deployed', 'at_utc': now, 'algorithm_binding': bind(P / 'algorithm-bindings.json'), 'modules': [bind(P / n) for n in NAMES],
     'manual': bind(MANUAL), 'baseline_preseal': baseline['baseline_preseal'], 'fixed_controls18': fixed['controls'], 'original20': bind(original20_path), 'original235': bind(parent_controls_path),
     'finite_final_execution_seals': [bind(P / n / 'output-seal.json') for n in final_summaries], 'self_excluded': True})
members = [bind(x) for x in sorted(P.rglob('*')) if x.is_file() and '__pycache__' not in x.parts and x.suffix != '.pyc' and x.name != 'delivery-seal.json']
assert all(verify_binding(v) for v in members)
save('delivery-seal.json', {'status': 'sealed_nonhuman_development_candidate_no_GO', 'at_utc': now, 'output_members': members, 'member_N': len(members), 'self_excluded': True,
    'readback_all_members_passed_before_sealing': True, 'main_LLM_labels_or_hidden12_read': False, 'new_actual_source_ids': []})
final = load(P / 'delivery-seal.json')
assert all(verify_binding(v) for v in final['output_members'])
print(json.dumps({'candidate': str(P), 'member_N': len(members), 'algorithm_binding': bind(P / 'algorithm-bindings.json'), 'candidate_seal': bind(P / 'candidate-seal.json'), 'delivery_seal': bind(P / 'delivery-seal.json'), 'final_counts': '18/18;19/20;227/235;75/75', 'new_actual_source_ids': []}, ensure_ascii=False))
