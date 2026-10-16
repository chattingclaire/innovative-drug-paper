"""Bound comparison: full actual LLM run plus one source-correction actual run.

Requires a final frozen manifest. Does not run either coder or a model.
"""
import argparse
import hashlib
import json
import sys
import types
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[2]
CHANGED_ID = 'RECODE25-03875'
CORE_SHA = '7ff690e872ef99d3daa1a290876729b6a0d75714627f8fb78da94afded8a243c'
FIRST_QA_SHA = '35236722a052e234204b6d9596d21c9bc251ac57db667de2f1113e41bbcc350a'
ORIGINAL_OUTPUT_SHA = 'e4fb8b2f3dca2e00e816800ae56755231e577822e7286201816f5801b192c1c7'
VISUAL_QA_SHA = '461aa027bf86b3f4abc748dcc5edc23810e7075336c434b9dfab4495407d15b9'
NEW_TEXT_SHA = '3b022a853ce9d6ada782a4db66058c3a3971a5ab4a730c414c12841b5eca7937'
LINEAGE_KIND = 'full_actual_execution_plus_one_source_correction_actual_execution'
RULE_FULL = 'full_actual_execution'
RULE_RECOVERED = 'full_actual_execution_plus_fixed_source_parse_scope_actual_recovery'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_core():
    path = HERE / 'comparison_core.py'
    data = path.read_bytes()
    if sha(data) != CORE_SHA:
        raise ValueError('parameterized kernel SHA differs')
    module = types.ModuleType('source_corrected_comparison_core')
    module.__file__ = str(path)
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


def exact_one_replacement(old_data, new_data, name, core):
    """Retain literal JSONL row bytes, including each original line ending."""
    old_lines, new_lines = old_data.splitlines(keepends=True), new_data.splitlines(keepends=True)
    core.require(len(old_lines) == len(new_lines) == 4480, name + ': physical JSONL row count differs')
    old_rows, new_rows = [json.loads(x) for x in old_lines], [json.loads(x) for x in new_lines]
    core.index_unique(old_rows, name + ' original')
    core.index_unique(new_rows, name + ' final')
    core.require([r['id'] for r in old_rows] == [r['id'] for r in new_rows], name + ': IDs/order differs')
    changed = [i for i, (a, b) in enumerate(zip(old_lines, new_lines)) if a != b]
    core.require(len(changed) == 1 and old_rows[changed[0]]['id'] == CHANGED_ID, name + ': only03875 may change; byte preservation failed')
    pos = changed[0]
    return {'rows': new_rows, 'old_rows': old_rows, 'changed_position_0_based': pos,
            'new_line': new_lines[pos], 'old_line': old_lines[pos],
            'ledger': {'id': CHANGED_ID, 'position_0_based': pos, 'other_rows_byte_identical_n': 4479,
                       'old_line_sha256': sha(old_lines[pos]), 'new_line_sha256': sha(new_lines[pos])}}


def validate_manifest_contract(manifest, core):
    core.require(manifest.get('status') == 'frozen_complete_inputs_outputs_for_comparison', 'manifest is missing final complete freeze; comparison refused')
    core.require(manifest.get('target_n') == 4481 and manifest.get('executed_n') == 4480, 'manifest population differs')
    core.require(manifest.get('manual_sha256') == core.MANUAL_SHA, 'manifest manual differs')
    core.require(manifest.get('lineage_kind') == LINEAGE_KIND, 'manifest must identify full execution plus one correction, not one-single-run')
    core.require(manifest.get('source_change_ids') == [CHANGED_ID], 'unexpected source changes')
    core.require(manifest.get('source_changes_selected_by_labels_or_metrics') is False, 'source selection independence not recorded')
    core.require(manifest.get('rule_execution_complete') is True, 'rule execution is not complete')
    core.require(manifest.get('rule_lineage_kind') in {RULE_FULL, RULE_RECOVERED}, 'rule execution lineage kind missing')
    roles = ['rule_input', 'rule_output', 'llm_input', 'llm_output', 'frame', 'first_full_qa',
             'rule_execution_qa', 'rule_freeze_record', 'llm_lineage', 'visual_qa', 'source_correction_record', 'root_bundle']
    for role in roles:
        ref = manifest.get('files', {}).get(role, {})
        core.require(isinstance(ref.get('path'), str) and core.is_sha256(ref.get('sha256')), 'manifest missing path/SHA for ' + role)
    correction = manifest.get('correction_llm_run', {})
    core.require(isinstance(correction.get('path'), str) and core.is_sha256(correction.get('summary_sha256'))
                 and core.is_sha256(correction.get('output_sha256')), 'correction run final SHA locks missing')
    if manifest['rule_lineage_kind'] == RULE_RECOVERED:
        for role in ['rule_base_output', 'rule_base_qa', 'rule_recovery_scope', 'rule_lineage']:
            ref = manifest.get('files', {}).get(role, {})
            core.require(isinstance(ref.get('path'), str) and core.is_sha256(ref.get('sha256')), 'manifest missing scoped rule lineage file ' + role)
        ids = manifest.get('rule_recovery_ids')
        core.require(isinstance(ids, list) and len(ids) > 0 and len(ids) == len(set(ids))
                     and all(isinstance(x, str) for x in ids), 'invalid frozen rule recovery IDs')
        runs = manifest.get('rule_recovery_runs')
        core.require(isinstance(runs, list) and len(runs) > 0, 'rule recovery run records missing')
        for run in runs:
            for role in ['input', 'output', 'execution_qa', 'runtime_freeze']:
                ref = run.get(role, {})
                core.require(isinstance(ref.get('path'), str) and core.is_sha256(ref.get('sha256')), 'rule recovery lacks ' + role + ' path/SHA')


def audit_rule_scoped_recovery(manifest, final_input_rows, final_output_bytes, core, bindings, data, obj):
    """Audit an authorized fixed parse scope; no label-based scope generation."""
    if manifest['rule_lineage_kind'] == RULE_FULL:
        core.require(not manifest.get('rule_recovery_ids') and not manifest.get('rule_recovery_runs'), 'full-only rule lineage cannot hide recovery records')
        return {'lineage_kind': RULE_FULL, 'scoped_recovery_used': False}
    scope = obj('rule_recovery_scope')
    fixed_ids = manifest['rule_recovery_ids']
    core.require(scope.get('scope_ids') == fixed_ids and scope.get('whole_population_n') == 4480
                 and scope.get('derived_from_source_parse_scan') is True
                 and scope.get('selected_by_labels_or_metrics') is False
                 and scope.get('frozen_before_recovery') is True
                 and scope.get('input_sha256') == manifest['files']['rule_input']['sha256'], 'rule scope lacks the fixed whole-source-scan contract')
    final_inputs = core.index_unique(final_input_rows, 'rule final source input')
    core.require(set(fixed_ids).issubset(final_inputs), 'recovery scope includes units outside4480')
    base_bytes = data('rule_base_output')
    base_lines, final_lines = base_bytes.splitlines(keepends=True), final_output_bytes.splitlines(keepends=True)
    core.require(len(base_lines) == len(final_lines) == 4480, 'rule base/final row counts differ')
    base_rows, final_rows = [json.loads(x) for x in base_lines], [json.loads(x) for x in final_lines]
    core.index_unique(base_rows, 'rule full base');core.index_unique(final_rows, 'rule final composite')
    core.require([r['id'] for r in base_rows] == [r['id'] for r in final_rows] == [r['id'] for r in final_input_rows], 'rule base/final/input IDs or order differ')
    base_qa = obj('rule_base_qa')
    core.require(base_qa.get('all_checks_pass') is True and base_qa.get('actual_execution_complete') is True
                 and base_qa.get('n') == 4480 and base_qa.get('manual_sha256') == core.MANUAL_SHA
                 and base_qa.get('input_sha256') == manifest['files']['rule_input']['sha256']
                 and base_qa.get('output_sha256') == manifest['files']['rule_base_output']['sha256'], 'rule4480 base execution QA differs')
    recovered_lines, run_ledgers = {}, []
    for index, run in enumerate(manifest['rule_recovery_runs'], 1):
        def read(ref):
            return core.read_bound(ref['path'], bindings, ref['sha256'])
        input_bytes, output_bytes = read(run['input']), read(run['output'])
        inputs = [json.loads(x) for x in input_bytes.splitlines()]
        output_lines = output_bytes.splitlines(keepends=True)
        outputs = [json.loads(x) for x in output_lines]
        core.index_unique(inputs, 'scoped recovery input');core.index_unique(outputs, 'scoped recovery output')
        ids = [r['id'] for r in inputs]
        core.require(ids == [r['id'] for r in outputs] and len(ids) > 0 and set(ids).issubset(fixed_ids), 'scoped actual recovery IDs/count differ')
        core.require(not set(ids).intersection(recovered_lines), 'same recovery ID appears in more than one actual run; selection refused')
        for row in inputs:
            core.require(core.canonical(row) == core.canonical(final_inputs[row['id']]), row['id'] + ': scoped recovery input differs from final common source')
        qa = json.loads(read(run['execution_qa']))
        core.require(qa.get('all_checks_pass') is True and qa.get('actual_execution_complete') is True
                     and qa.get('n') == len(ids) and qa.get('ids') == ids
                     and qa.get('input_sha256') == run['input']['sha256'] and qa.get('output_sha256') == run['output']['sha256']
                     and qa.get('manual_sha256') == core.MANUAL_SHA, 'scoped rule execution QA does not bind actual input/output')
        frozen = json.loads(read(run['runtime_freeze']))
        core.require(frozen.get('manual_sha256') == core.MANUAL_SHA and frozen.get('input_sha256') == run['input']['sha256']
                     and frozen.get('ids') == ids and bool(frozen.get('runtime_files_sha256')), 'scoped runtime/source freeze differs')
        for name, expected in frozen['runtime_files_sha256'].items():
            core.require(Path(name).name == name and core.is_sha256(expected), 'invalid scoped runtime file lock')
            core.read_bound(Path(frozen['runtime_path']) / name, bindings, expected)
        for rid, line in zip(ids, output_lines):
            recovered_lines[rid] = line
        run_ledgers.append({'run_number': index, 'ids': ids, 'input': run['input'], 'output': run['output'],
                            'execution_qa': run['execution_qa'], 'runtime_freeze': run['runtime_freeze']})
    core.require(set(recovered_lines) == set(fixed_ids), 'frozen parse scope not exactly covered by actual recovery outputs')
    untouched = 0
    for original, final, row in zip(base_lines, final_lines, final_rows):
        rid = row['id']
        if rid in recovered_lines:
            core.require(final == recovered_lines[rid], rid + ': final row is not the exact scoped actual output bytes')
        else:
            core.require(original == final, rid + ': rule row outside frozen parse scope changed')
            untouched += 1
    lineage = obj('rule_lineage')
    core.require(lineage.get('lineage_kind') == RULE_RECOVERED and lineage.get('replacement_ids') == fixed_ids
                 and lineage.get('selection_by_label_or_metric') is False
                 and lineage.get('base_output_sha256') == manifest['files']['rule_base_output']['sha256']
                 and lineage.get('final_output_sha256') == manifest['files']['rule_output']['sha256']
                 and lineage.get('unchanged_other_row_n') == untouched, 'rule composite lineage differs')
    return {'lineage_kind': RULE_RECOVERED, 'scoped_recovery_used': True, 'fixed_scope_ids': fixed_ids,
            'outside_scope_original_row_bytes_unchanged_n': untouched, 'scope_source_scan_record': manifest['files']['rule_recovery_scope'],
            'recovery_actual_runs': run_ledgers, 'semantic_validity_not_certified': True}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--manifest', required=True)
    ap.add_argument('--expected-manifest-sha256', required=True)
    ap.add_argument('--output-dir', default=str(HERE / 'actual01'))
    args = ap.parse_args()
    script_sha = sha(Path(__file__).read_bytes())
    core = load_core()
    bindings = {str(HERE / 'comparison_core.py'): {'sha256': CORE_SHA, 'bytes': (HERE / 'comparison_core.py').stat().st_size}}
    core.require(core.is_sha256(args.expected_manifest_sha256), 'explicit final manifest SHA required')
    manifest = core.read_json(args.manifest, bindings, args.expected_manifest_sha256)
    validate_manifest_contract(manifest, core)
    destination = Path(args.output_dir).resolve()
    core.require(destination.is_relative_to(HERE) and not destination.exists(), 'output must be fresh under 两方法比较准备')

    def data(role):
        ref = manifest['files'][role]
        return core.read_bound(ref['path'], bindings, ref['sha256'])

    def obj(role):
        return json.loads(data(role))

    root_bundle = obj('root_bundle')
    core.require(root_bundle.get('status') == 'complete_same_material_current_methods_bound_not_human_validated'
                 and root_bundle.get('target_n') == 4481 and root_bundle.get('executed_n') == 4480
                 and root_bundle.get('manual_sha256') == core.MANUAL_SHA
                 and root_bundle.get('label_or_metric_based_selection') is False, 'root final bundle contract differs')
    for role in ['rule_input', 'rule_output', 'llm_input', 'llm_output', 'frame']:
        core.require(root_bundle.get(role) == manifest['files'][role], 'adapter role differs from actual frozen bundle: ' + role)
    for ref in root_bundle['source_bindings'].values():
        core.read_bound(ref['path'], bindings, ref['sha256'])

    # Technical metadata gates precede reading any final prediction file.
    core.require(manifest['files']['first_full_qa']['sha256'] == FIRST_QA_SHA, 'first full QA is not the already verified report')
    first = obj('first_full_qa')
    core.require(first.get('all_checks_pass') is True and first.get('target_n') == 4481
                 and first.get('both_executed_n') == 4480 and first.get('manual_sha256') == core.MANUAL_SHA
                 and first.get('llm_summary', {}).get('output_sha256') == ORIGINAL_OUTPUT_SHA,
                 'original full QA does not bind the specified completed run')
    execution_qa = obj('rule_execution_qa')
    core.require(execution_qa.get('all_checks_pass') is True and execution_qa.get('n') == 4480
                 and execution_qa.get('manual_sha256') == core.MANUAL_SHA
                 and execution_qa.get('input_sha256') == manifest['files']['rule_input']['sha256']
                 and execution_qa.get('output_sha256') == manifest['files']['rule_output']['sha256'], 'final rule execution QA/input/output bindings differ')
    freeze = obj('rule_freeze_record')
    core.require(freeze.get('n') == 4480 and freeze.get('same_manual_sha256') == core.MANUAL_SHA
                 and freeze.get('source_change_ids') == [CHANGED_ID]
                 and freeze.get('source_changes_not_selected_by_metric_or_label') is True
                 and freeze.get('inputs_sha256', {}).get('规则输入4480.jsonl') == manifest['files']['rule_input']['sha256']
                 and freeze.get('inputs_sha256', {}).get('纯来源材料4480.jsonl') == manifest['files']['llm_input']['sha256'], 'final frozen source/runtime record differs')
    runtime = Path(freeze['runtime_path']).resolve()
    core.require(bool(freeze.get('runtime_files_sha256')), 'rule runtime locks missing')
    for name, expected in freeze['runtime_files_sha256'].items():
        core.require(Path(name).name == name and core.is_sha256(expected), 'invalid runtime file lock')
        core.read_bound(runtime / name, bindings, expected)
    correction_ref = manifest['correction_llm_run']
    one_args = types.SimpleNamespace(llm_run=correction_ref['path'], llm_summary=None, llm_output=None,
                                    expected_llm_summary_sha256=correction_ref['summary_sha256'],
                                    expected_llm_output_sha256=correction_ref['output_sha256'])
    one_inputs, one_rows, one_summary, one_plan, one_batches = core.load_complete_llm(one_args, bindings, expected_n=1)
    core.require([r['id'] for r in one_inputs] == [CHANGED_ID] == [r['id'] for r in one_rows], 'correction run is not precisely03875')
    core.require(one_plan.get('prompt_sha256') == first['llm_plan']['prompt_sha256'], 'correction prompt differs from original full execution')

    # Reuse the first technical audit only after all of its bound bytes rehash.
    for path, meta in first['source_files'].items():
        core.read_bound(path, bindings, meta['sha256'])
    original_run = W / 'LLM编码/测量与语义统一/full4480'
    original_input = core.read_bound(original_run / 'frozen_input.jsonl', bindings, first['llm_plan']['input_sha256'])
    original_output = core.read_bound(original_run / 'all_predictions.jsonl', bindings, ORIGINAL_OUTPUT_SHA)
    original_rule_input = core.read_bound(W / '统计复算/测量与语义统一全量/规则输入4480.jsonl', bindings, core.SOURCE_LOCKS['rule_input'])
    source_update = exact_one_replacement(original_input, data('llm_input'), 'LLM source input', core)
    output_update = exact_one_replacement(original_output, data('llm_output'), 'LLM output', core)
    rule_input_update = exact_one_replacement(original_rule_input, data('rule_input'), 'rule source input', core)
    li = core.index_unique(source_update['rows'], 'final LLM input')
    ll = core.index_unique(output_update['rows'], 'final LLM output')
    ri = core.index_unique(rule_input_update['rows'], 'final rule input')
    core.require(core.canonical(li[CHANGED_ID]) == core.canonical(one_inputs[0]), 'final changed source row differs from actual correction frozen input')
    one_output_line = core.read_bound(Path(correction_ref['path']) / 'all_predictions.jsonl', bindings, correction_ref['output_sha256'])
    core.require(output_update['new_line'] == one_output_line and core.canonical(ll[CHANGED_ID]) == core.canonical(one_rows[0]), 'final changed prediction is not the actual correction row bytes')

    core.require(manifest['files']['visual_qa']['sha256'] == VISUAL_QA_SHA, 'independent visual QA differs')
    visual = obj('visual_qa')
    source_correction = obj('source_correction_record')
    core.require(visual.get('all_visual_and_change_checks_pass') is True
                 and visual.get('id') == CHANGED_ID and visual.get('new_unit_text_sha256') == NEW_TEXT_SHA
                 and source_correction.get('id') == CHANGED_ID and source_correction.get('new_text_sha256') == NEW_TEXT_SHA, 'visual correction source binding differs')
    old_text = core.index_unique(source_update['old_rows'], 'original LLM input')[CHANGED_ID]['text']
    core.require(sha(old_text.encode('utf-8')) == source_correction['old_text_sha256'], 'old source text does not match recorded visual correction')
    patched_text = old_text
    core.require(len(source_correction.get('changes', [])) == 2, 'unexpected visual text changes')
    for change in source_correction['changes']:
        core.require(patched_text.count(change['old']) == 1, 'visual patch source span missing/ambiguous')
        patched_text = patched_text.replace(change['old'], change['new'])
    core.require(patched_text == li[CHANGED_ID]['text'] and sha(patched_text.encode('utf-8')) == NEW_TEXT_SHA, 'new source text is not exactly the two visual branch fixes')
    # Bind the visual PDF, corrected candidate and high-dpi regions without a new hosting claim.
    for path, meta in visual['source_bindings'].items():
        if Path(path).suffix in {'.pdf', '.png'} or str(path) == source_correction.get('new_candidate_path'):
            core.read_bound(path, bindings, meta['sha256'])

    lineage = obj('llm_lineage')
    core.require(lineage.get('lineage_kind') == LINEAGE_KIND and lineage.get('replacement_ids') == [CHANGED_ID]
                 and lineage.get('unchanged_other_row_n') == 4479 and lineage.get('selection_by_label_or_metric') is False
                 and lineage.get('original_output_sha256') == ORIGINAL_OUTPUT_SHA
                 and lineage.get('correction_output_sha256') == correction_ref['output_sha256']
                 and lineage.get('final_output_sha256') == manifest['files']['llm_output']['sha256'], 'final LLM lineage does not bind the authorized exact replacement')
    helper_path = W / '统计复算/测量与语义统一全量/规则描述统计/count_rule_descriptive.py'
    helper_bytes = core.read_bound(helper_path, bindings, core.SOURCE_LOCKS['rule_summary_helper'])
    helper = types.ModuleType('source_corrected_bound_descriptive_helper')
    helper.__file__ = str(helper_path)
    exec(compile(helper_bytes, str(helper_path), 'exec'), helper.__dict__)
    core.read_bound(W / '定义溯源核查/测量与计数统一/共用编码手册.md', bindings, core.MANUAL_SHA)
    frame = [json.loads(s) for s in data('frame').splitlines()]
    fi = core.index_unique(frame, 'fixed4481 target frame')
    old_frame_bytes = core.read_bound(W / '人工参照复核/全量目标框验证准备01/source_only_frame_all4481.jsonl', bindings, core.SOURCE_LOCKS['frame'])
    old_fi = core.index_unique([json.loads(s) for s in old_frame_bytes.splitlines()], 'original identity frame')
    core.require(set(fi) == set(old_fi), 'new same-material frame drops/adds identities')
    for rid, f in fi.items():
        core.require(f['analysis_group'] == old_fi[rid]['analysis_group'], rid + ': department identity changed')
        if rid == CHANGED_ID:
            core.require(f['unit_text'] == patched_text and f['unit_text_sha256'] == NEW_TEXT_SHA, 'new same-material frame lacks the visually corrected03875 text')
        else:
            core.require(f['unit_text'] == old_fi[rid]['unit_text'] and f['unit_text_sha256'] == old_fi[rid]['unit_text_sha256'], rid + ': unchanged frame text differs')
    final_rule_bytes = data('rule_output')
    rule_execution_lineage = audit_rule_scoped_recovery(manifest, rule_input_update['rows'], final_rule_bytes, core, bindings, data, obj)
    rules = [json.loads(s) for s in final_rule_bytes.splitlines()]
    rr = core.index_unique(rules, 'final rule output')
    expected = set(fi) - {'RECODE25-00064'}
    core.require(len(fi) == 4481 and len(rules) == 4480 and set(li) == set(ll) == set(ri) == set(rr) == expected, 'populations differ; silent dropping refused')
    core.require([r['id'] for r in rules] == [r['id'] for r in rule_input_update['rows']], 'rule input/output order differs')
    core.require(Counter(f['analysis_group'] for f in frame) == Counter({'NMPA': 1848, 'NHSA': 2100, 'NHC': 533}), 'department frame differs')
    records, unknown, texts = [], [], {}
    for f in frame:
        rid = f['id']
        if rid in expected:
            wrapper = rr[rid]
            core.require(set(wrapper) == {'id', 'status', 'result'} and wrapper['status'] == 'completed', rid + ': rule result incomplete/shape differs')
            result = wrapper['result']
            core.require(result.get('current_manual_sha256') == core.MANUAL_SHA, rid + ': rule manual differs')
            core.require(set(result['labels']) == set(core.DIMS) and all(v is None or type(v) is int and v in (0, 1) for v in result['labels'].values()), rid + ': invalid rule labels')
            core.require((result['judgement_status'] == 'undetermined') == any(v is None for v in result['labels'].values()), rid + ': rule unknown state differs')
            text = li[rid]['text']
            core.require(text == ri[rid]['input']['unit_text'] and sha(text.encode('utf-8')) == result['unit_text_sha256'], rid + ': method current text differs')
            core.require(text == f['unit_text'] and sha(text.encode('utf-8')) == f['unit_text_sha256'], rid + ': new same-material frame current text differs')
            labels = {'rule': dict(result['labels']), 'llm': dict(ll[rid]['labels'])}
            core.require(set(labels['llm']) == set(core.DIMS) and all(type(v) is int and v in (0, 1) for v in labels['llm'].values()), rid + ': invalid LLM labels')
        else:
            text = f['unit_text']
            labels = {m: dict.fromkeys(core.DIMS, None) for m in ['rule', 'llm']}
        texts[rid] = text
        record = {'id': rid, 'group': f['analysis_group'], **labels}
        records.append(record)
        u = {m: [d for d in core.DIMS if labels[m][d] is None] for m in labels}
        if any(u.values()):
            unknown.append({'id': rid, 'group': f['analysis_group'], 'unknown_dimensions': u,
                            'known_labels': {m: {d: v for d, v in labels[m].items() if v is not None} for m in labels},
                            'rule_input_assessment_status': rr[rid]['result'].get('input_assessment_status') if rid in rr else 'source_gap_00064_not_executed',
                            'no_unknown_cells_replaced_by_zero': True})
    analyses = {g: core.compare_group([r for r in records if r['group'] == g], helper) for g in ['NMPA', 'NHSA', 'NHC']}
    analyses['TOTAL'] = core.compare_group(records, helper)
    differences, incomparable = {}, {}
    for d in core.DIMS:
        differences[d], incomparable[d] = [], []
        for r in records:
            rid = r['id']
            base = {'id': rid, 'group': r['group'], 'dimension': d, 'text': texts[rid],
                    'unit_text_sha256': sha(texts[rid].encode('utf-8')), 'rule_label': r['rule'][d], 'llm_label': r['llm'][d]}
            if r['rule'][d] is None or r['llm'][d] is None:
                incomparable[d].append(base)
            elif r['rule'][d] != r['llm'][d]:
                differences[d].append({**base, 'source_position': fi[rid]['source_position'],
                                       'llm_row_execution_origin': str(correction_ref['path']) if rid == CHANGED_ID else str(original_run),
                                       'rule_output_complete': rr[rid], 'llm_output_complete': ll[rid],
                                       'rule_source_input_complete': ri[rid], 'llm_source_input_complete': li[rid],
                                       'rule_reason_note': 'No separate dimension_reasons supplied; full original evidence, flags, suppressions and paths retained; no reason invented.'})
        table = analyses['TOTAL']['binary_agreement_on_dimensionwise_common_determined'][d]
        core.require(len(differences[d]) == table['disagreement_n'] and len(incomparable[d]) + table['paired_determined_n'] == 4481, 'difference/unknown export tally differs')
    core.require(all(sha(Path(p).read_bytes()) == meta['sha256'] for p, meta in bindings.items()), 'bound bytes changed during comparison')
    core.require(sha(Path(__file__).read_bytes()) == script_sha, 'comparison program changed during calculation')
    destination.mkdir(parents=True, exist_ok=False)
    def write(name, value):
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    def jsonl(name, rows):
        (destination / name).write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    write('输入绑定与来源校正核查.json', {'status': LINEAGE_KIND, 'all_technical_binding_checks_pass': True,
          'reused_first_full_qa_sha256': FIRST_QA_SHA, 'original_full_execution_sha256': ORIGINAL_OUTPUT_SHA,
          'source_files': bindings, 'manual_sha256': core.MANUAL_SHA, 'script_sha256': script_sha,
          'manifest': manifest, 'original_full_qa_reused_after_all_bound_files_rehash': True,
          'byte_replacement_ledgers': {n: v['ledger'] for n, v in [('llm_input', source_update), ('llm_output', output_update), ('rule_input', rule_input_update)]},
          'correction_actual_run_summary': one_summary, 'correction_actual_run_plan': one_plan, 'correction_batch_ledger': one_batches,
          'rule_execution_lineage': rule_execution_lineage,
          'target_n': 4481, 'executed_n_each_method': 4480, 'missing00064_five_unknown_retained': True,
          'new_frame_role': 'actual bundle same-material4481 frame; all current texts match both method inputs; old frame used only to verify unchanged identities/departments and4479 text preservation',
          'semantic_validity_not_certified': True, 'python_executable': sys.executable})
    write('两方法描述与一致性.json', {'status': 'descriptive_comparison_not_gold_validation_or_final_publication',
          'llm_lineage_kind': LINEAGE_KIND, 'rule_lineage_kind': manifest['rule_lineage_kind'], 'analyses': analyses, 'unknown_unit_ledger': unknown,
          'unknown_rule_tally_is_calculated_from_actual_labels_not_hardcoded': True,
          'denominator_notes': {'q': 'Each method own all-five-known q and primary same-unit-set all-ten-known q are separate; q denominators are positive label occurrences, not total sentences.',
                                'binary_agreement': 'Per-dimension paired-known four cells/kappa/agreement and the common-all-five set are separate; neither method is gold; no P/R.',
                                'unknown_bounds': 'Reused locked original descriptive formulas; no unknown0 imputation. Logical bounds, not CI or accuracy.',
                                'coverage': 'N-u_d from actual label/null cells; output integer does not establish semantic correctness or full source sufficiency.',
                                'frame': 'All4481 identities remain;00064 all-five unknown. Only03875 current text changes with explicit visual lineage.'},
          'difference_export_counts': {d: len(v) for d, v in differences.items()}, 'coder_or_model_invocations': 0})
    common = [r for r in records if all(r[m][d] is not None for m in ['rule', 'llm'] for d in core.DIMS)]
    jsonl('共同全维可判定单位.jsonl', [{'id': r['id'], 'group': r['group'], 'unit_text_sha256': sha(texts[r['id']].encode('utf-8'))} for r in common])
    for d in core.DIMS:
        jsonl(d + '_二元分歧.jsonl', differences[d])
        jsonl(d + '_待判定未进入二元表.jsonl', incomparable[d])
    write('产物SHA.json', {'source_file_bindings': bindings, 'all_source_bytes_unchanged': True,
                         'files_sha256': {p.name: sha(p.read_bytes()) for p in sorted(destination.iterdir()) if p.is_file()}})
    print(json.dumps({'status': LINEAGE_KIND, 'output_dir': str(destination), 'target_n': 4481,
                      'unknown_rule_n_actual': len([r for r in unknown if r['unknown_dimensions']['rule']]),
                      'common_all_five_n': len(common)}, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, TypeError, KeyError, IndexError, AssertionError) as error:
        print(json.dumps({'status': 'comparison_refused', 'error_type': type(error).__name__, 'reason': str(error)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
