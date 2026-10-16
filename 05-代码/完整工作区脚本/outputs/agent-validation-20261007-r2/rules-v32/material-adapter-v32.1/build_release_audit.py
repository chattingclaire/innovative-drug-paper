"""Release actual source-material runs without loading reference labels."""
import copy
import datetime
import hashlib
import json
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = BASE.parent
RT = OUT / 'runtime'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def rows(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines()]


def save(name, value):
    path = OUT / name
    assert not path.exists(), path
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
    return path


def bind(path):
    return {'path': str(path), 'sha256': sha(path)}


def main():
    freeze_path = OUT / 'candidate_freeze.json'
    freeze = read(freeze_path)
    for path, digest in freeze['all_runtime_py_sha256'].items():
        assert sha(path) == digest, path
    old_freeze = read(BASE / 'candidate_freeze.json')
    for path, digest in old_freeze['production_runtime_sha256'].items():
        assert sha(path) == digest, path
    paths = {
        'v32_v3': BASE / 'all_predictions.jsonl',
        'v32_v4': BASE / 'material-v4-original-code/all_predictions.jsonl',
        'v32_v6': BASE / 'material-v6-original-code/all_predictions.jsonl',
        'v321_v4': OUT / 'all_predictions_material_v4.jsonl',
        'v321_v6': OUT / 'all_predictions_material_v6.jsonl',
    }
    predictions = {k: rows(p) for k, p in paths.items()}
    final = predictions['v321_v6']
    ids = [r['id'] for r in final]
    assert len(ids) == len(set(ids)) == 4924
    for key, values in predictions.items():
        assert [r['id'] for r in values] == ids, key
        manifest = read(paths[key].with_suffix('.run.json'))
        assert manifest['n'] == 4924 and manifest['pending_n'] == 0
        assert manifest['prediction_sha256'] == sha(paths[key])
        assert manifest['input_sha256'] == sha(manifest['input_path'])
        assert manifest['reference_labels_loaded'] is False
        assert all(sha(path) == digest for path, digest in manifest['runtime_code_sha256'].items())
    final_run_path = paths['v321_v6'].with_suffix('.run.json')
    final_run = read(final_run_path)
    assert final_run['version'] == freeze['version']
    assert final_run['input_path'] == freeze['input_path']
    assert final_run['input_sha256'] == freeze['input_sha256']
    for path, digest in final_run['runtime_code_sha256'].items():
        assert freeze['all_runtime_py_sha256'][path] == digest
    inputs = rows(freeze['input_path'])
    old_inputs = rows(ROOT.parent / 'recall-revision-20261007/rule_inputs_v31_shared_v3.jsonl')
    assert [r['id'] for r in inputs] == ids == [r['id'] for r in old_inputs]
    material_changed = [r['id'] for r, old in zip(inputs, old_inputs) if r != old]
    assert all(r['input']['unit_text'] == old['input']['unit_text'] for r, old in zip(inputs, old_inputs))
    assert material_changed == read(ROOT / 'material_v6_manifest.json')['total_affected_ids_from_v3']
    table_ids = {r['id'] for r in inputs if r['input'].get('verified_table_context_v4')}
    assert len(table_ids) == 18 and len(material_changed) == 23
    effects = {}
    for title, before, after in [
        ('original_v32_material_v3_to_v4', 'v32_v3', 'v32_v4'),
        ('original_v32_material_v3_to_v6', 'v32_v3', 'v32_v6'),
        ('adapter_only_on_same_v6_material', 'v32_v6', 'v321_v6'),
        ('same_adapter_material_v4_to_v6', 'v321_v4', 'v321_v6'),
    ]:
        changes = []
        for old, new, inp in zip(predictions[before], predictions[after], inputs):
            a, b = old['prediction']['labels'], new['prediction']['labels']
            if a != b:
                dims = [d for d in a if a[d] != b[d]]
                changes.append({'id': new['id'], 'dimensions': dims, 'old_labels': a, 'new_labels': b,
                                'unit_text': inp['input']['unit_text'],
                                'source_certificate': inp['input'].get('verified_table_context_v4'),
                                'new_adapter_evidence': [e for e in new['prediction']['evidence'] if e['rule'].startswith('V321_')]})
        effects[title] = {'before': bind(paths[before]), 'after': bind(paths[after]),
                          'label_changed_unit_n': len(changes), 'changes': changes}
    assert effects['original_v32_material_v3_to_v4']['label_changed_unit_n'] == 0
    assert effects['original_v32_material_v3_to_v6']['label_changed_unit_n'] == 0
    assert effects['same_adapter_material_v4_to_v6']['label_changed_unit_n'] == 0
    adapter_changes = effects['adapter_only_on_same_v6_material']['changes']
    assert len(adapter_changes) == 13
    assert all(c['id'] in table_ids and c['dimensions'] == ['I'] and c['old_labels']['I'] == 0 and c['new_labels']['I'] == 1 for c in adapter_changes)
    active = Counter()
    basis = {}
    adapter_hits = []
    for pred, inp, original_v32 in zip(final, inputs, predictions['v32_v6']):
        result = pred['prediction']; text = inp['input']['unit_text']
        assert result['unit_text_sha256'] == hashlib.sha256(text.encode()).hexdigest()
        assert result['judgement_status'] != 'undetermined'
        assert {d: result['labels'][d] for d in ['S', 'E', 'Ec', 'F']} == {d: original_v32['prediction']['labels'][d] for d in ['S', 'E', 'Ec', 'F']}
        for evidence in result['evidence']:
            assert text[evidence['start']:evidence['end']] == evidence['text']
            rule = evidence['rule']; active[rule] += 1
            basis.setdefault(rule, set()).add(evidence.get('protocol_basis', 'Legacy declaration linked by source-rule index to the frozen v1.3 dimension.'))
            if rule.startswith('V321_'):
                adapter_hits.append(pred['id'])
                assert evidence['context_dependency']['raw_row_cells'] == inp['input']['verified_table_context_v4'][0]['raw_row_cells']
    assert len(adapter_hits) == len(set(adapter_hits)) == 18 and set(adapter_hits) == table_ids
    previous = read(BASE / 'active_rule_source_index.json')
    indexed = {r['rule']: copy.deepcopy(r) for r in previous['rules']}
    new_rule = freeze['only_new_rule']
    new_source = RT / 'table_material_adapter_v321.py'
    source_lines = new_source.read_text().splitlines()
    line = next(i + 1 for i, x in enumerate(source_lines) if "view.add('" + new_rule + "'" in x)
    indexed[new_rule] = {'rule': new_rule, 'implementation_source_declarations': [
        {'path': str(new_source), 'sha256': sha(new_source), 'line': line, 'lookup': 'exact_rule_literal'}]}
    declarations = []
    for rule in sorted(active):
        item = indexed[rule]
        item['actual_evidence_occurrences'] = active[rule]
        item['protocol_basis_recorded'] = sorted(basis[rule])
        for declaration in item['implementation_source_declarations']:
            copied = RT / Path(declaration['path']).name
            declaration['path'] = str(copied); declaration['sha256'] = sha(copied)
            declaration_line = copied.read_text().splitlines()[declaration['line'] - 1]
            if declaration['lookup'] == 'explicit_dynamic_dimension_suffix':
                assert rule in {'V27_F_dimension_evaluation_list', 'V27_I_dimension_evaluation_list'}
                assert "'V27_'+dim+'_dimension_evaluation_list'" in declaration_line
            else:
                assert rule in declaration_line
        declarations.append(item)
    index_path = save('active_rule_source_index.json', {'status': 'all_actual_active_evidence_rules_have_source_declarations',
                     'active_rule_count': len(declarations), 'manual': previous['manual'],
                     'operation_note': previous['operation_note'], 'rules': declarations})
    effect_path = save('actual_material_and_adapter_effects.json', {
        'interpretation': 'Actual prediction differences only; no reference-label accuracy or metric selection.',
        'material_changed_n_v3_to_v6': 23, 'unit_text_changed_n': 0, 'effects': effects})
    qa_path = save('actual_execution_QA.json', {
        'status': 'passed_actual_4924_material_adapter_execution', 'n': 4924,
        'all_source_bound_adapter_rows_n': 18, 'adapter_label_changed_n': 13,
        'no_label_changes_outside_authenticated_rows': True,
        'all_S_E_Ec_F_unchanged': True, 'all_literal_evidence_spans_verified': True,
        'all_frozen_runtime_hashes_unchanged': True, 'all_old_v32_code_frozen': True,
        'all_same_ids_and_original_unit_text': True, 'no_pending_units': True,
        'new_confirmation_results_or_metrics_read': False,
        'input': bind(Path(freeze['input_path'])), 'prediction': bind(paths['v321_v6']),
        'run': bind(final_run_path), 'freeze': bind(freeze_path),
        'development_regression_tests': 227,
        'development_test_results': bind(RT / 'semantic_test_results.json')})
    release = {
        'status': 'frozen_actual_4924_source_material_adapter_not_untouched_confirmatory_validation',
        'version': freeze['version'], 'source_material_version': 'v6', 'n': 4924,
        'released_at': datetime.datetime.now().astimezone().isoformat(),
        'input_path': freeze['input_path'], 'input_sha256': freeze['input_sha256'],
        'llm_material_path': freeze['llm_material_path'], 'llm_material_sha256': freeze['llm_material_sha256'],
        'prediction_path': str(paths['v321_v6']), 'prediction_sha256': sha(paths['v321_v6']),
        'run_manifest_path': str(final_run_path), 'run_manifest_sha256': sha(final_run_path),
        'freeze_path': str(freeze_path), 'freeze_sha256': sha(freeze_path),
        'QA_path': str(qa_path), 'QA_sha256': sha(qa_path),
        'change_path': str(effect_path), 'change_sha256': sha(effect_path),
        'rule_source_index_path': str(index_path), 'rule_source_index_sha256': sha(index_path),
        'production_runtime_sha256': freeze['production_code_sha256'],
        'material_manifests_sha256': freeze['material_manifests_sha256'],
        'source_table_visual_QA': bind(OUT / 'source_table_material_independent_QA.json'),
        'no_new_agent_labels_or_metrics_read': True,
        'reference_labels_modified': False, 'semantic_constructs_unchanged': True,
    }
    release_path = save('release_manifest.json', release)
    report = '''数据保护表格材料适配 v32.1 实际交付

最终输入为 v6，共4924单元；原文、ID均未改变。23条语境增补由源文材料缺陷引起，其中18条为三张数据保护附表的真实表题与四列，另5条为条件列表。冻结原v32分别在v4和v6完整运行，相对原v3标签均零改变。

v32.1只增加材料适配器：校验结构化原文、candidate、源图SHA、表题、四列、原表行索引及原单元文字，再将当前行“数据保护期”列解释为已经冻结的专有权利期限或实际适用范围。不给予保护的行同样讨论权利适用边界，不把破折号转成0年，不传播表题到其他正文。

全量实际结果：18行获得源绑定表列证据，其中13行I从0变1，另5行I原已为1；其余4906条标签不变，S/E/Ec/F在4924条中全部不变。额外条件列表对当前规则标签零影响。全部4060条证据文字及2547条抑制文字的原句定位有效。

227项开发回归通过，包括原219项适用回归和8项表列材料/篡改检查。它们检验实现与材料完整性，不能当成独立准确率或真人效度。该版本是在盲评发现真实材料缺口后形成的物料适配，不能称从未接触确认材料的语义修订；执行过程未读取新agent标签、盲评输出或指标，也未改变任何参照标签。

旧v31、v32/v3及原码v4/v6结果保留。最终统计应绑定release_manifest.json中v6预测与实际run的SHA，不使用v3或v4结果替代。
'''
    (OUT / '材料适配与实际变更.md').write_text(report)
    print(json.dumps({'release': bind(release_path), 'prediction': bind(paths['v321_v6']),
                      'run': bind(final_run_path), 'QA': bind(qa_path),
                      'active_rules': len(declarations), 'changed_labels': len(adapter_changes)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
