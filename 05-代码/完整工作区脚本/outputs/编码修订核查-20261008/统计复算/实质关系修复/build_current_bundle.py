"""Bind one actual full rule execution to unchanged, previously verified LLM results."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[1]
PREVIOUS = HERE.parent / '来源读取与图示校正/当前同材料结果/同材料结果绑定.json'
PREVIOUS_SHA = 'b001d8df5a304604f0ebe33865369768c7ed92dd1ba576378816810ca20bb9f7'
FIXED = W / '自动规则编码/实质评价与支持关系修复/运行前固定记录03.json'
RUNTIME = W / '自动规则编码/实质评价与支持关系修复/runtime03'
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def read(path):
    return json.loads(Path(path).read_text())

def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def main():
    destination = HERE / '当前同材料结果'
    assert not destination.exists(), 'Preserve previous actual assemblies.'
    assert sha(PREVIOUS) == PREVIOUS_SHA
    old = read(PREVIOUS)
    # Historical source records remain provenance, not newly selected predictions.
    bindings = dict(old['source_bindings'])
    def bind(path, expected=None):
        path = Path(path).resolve()
        h = sha(path)
        assert expected is None or h == expected, str(path)
        ref = {'path': str(path), 'sha256': h}
        bindings[str(path)] = ref
        return ref

    ex_path = HERE / '规则全量输出4480.execution.json'
    freeze_path = HERE / '运行前冻结.json'
    qa_path = HERE / '执行与字面核查.json'
    output_path = HERE / '规则全量输出4480.jsonl'
    ex, frozen, qa, fixed = map(read, (ex_path, freeze_path, qa_path, FIXED))
    assert ex['n'] == frozen['n'] == qa['n'] == 4480
    assert ex['status_counts'] == {'completed': 4480}
    assert ex['runtime_unchanged'] and ex['protected_sources_input_base_manual_runner_unchanged']
    assert frozen['runtime_before'] == ex['runtime_before'] == ex['runtime_after'] == fixed['runtime_all_files_sha256']
    assert ex['runtime_before_tree_sha256'] == ex['runtime_after_tree_sha256'] == fixed['runtime_tree_sha256']
    assert frozen['manual_sha256'] == ex['manual_sha256'] == old['manual_sha256']
    assert ex['input_sha256'] == frozen['input_sha256'] == old['rule_input']['sha256']
    assert ex['output_sha256'] == qa['output_sha256'] == sha(output_path)
    assert qa['ids_unique_and_order_match'] and qa['n_literal_error_rows'] == 0
    assert qa['unexpected_SE_Ec_change_ids'] == []
    assert ex['no_model_run'] and ex['no_human_labels_or_metrics_used']
    for name, h in ex['runtime_after'].items():
        bind(RUNTIME / name, h)
    for role in ('rule_input', 'llm_input', 'llm_output', 'frame', 'llm_lineage'):
        bind(old[role]['path'], old[role]['sha256'])
    current = rows(output_path)
    inputs = rows(old['rule_input']['path'])
    llm = rows(old['llm_output']['path'])
    frame = {r['id']: r for r in rows(old['frame']['path'])}
    assert len(current) == len(inputs) == len(llm) == 4480
    assert [r['id'] for r in current] == [r['id'] for r in inputs] == [r['id'] for r in llm]
    assert set(frame) - {r['id'] for r in current} == {'RECODE25-00064'}
    for output, input_row in zip(current, inputs):
        result = output['result']
        text = input_row['input']['unit_text']
        assert output['status'] == 'completed'
        assert result['current_manual_sha256'] == old['manual_sha256']
        assert text == frame[output['id']]['unit_text']
        assert result['unit_text_sha256'] == hashlib.sha256(text.encode()).hexdigest()
        assert set(result['labels']) == set(DIMS)
        assert all(v is None or type(v) is int and v in (0, 1) for v in result['labels'].values())
        assert all(e['display_quote'] == text for e in result['evidence'])
    # Recheck actual source bindings once per file, never inside a row loop.
    for ref in bindings.values():
        assert sha(ref['path']) == ref['sha256'], ref['path']
    destination.mkdir()
    manifest = {key: old[key] for key in (
        'status', 'target_n', 'executed_n', 'manual_sha256', 'rule_input',
        'llm_input', 'llm_output', 'frame', 'llm_lineage', 'llm_execution_scope',
        'llm_replaced_source_ids', 'unchanged_llm_rows_n', 'known_source_unknown_ids',
        'source_correction', 'complete_original_llm_execution_QA', 'one_row_actual_execution')}
    manifest.update({
        'previous_bundle': bind(PREVIOUS, PREVIOUS_SHA),
        'rule_output': bind(output_path, ex['output_sha256']),
        'rule_execution': bind(ex_path),
        'rule_runtime_freeze': bind(freeze_path),
        'rule_runtime_fixed_record': bind(FIXED),
        'rule_runtime_dir': str(RUNTIME),
        'rule_execution_scope': 'single_complete_actual_full4480_run',
        'rule_patch_ids': [],
        'rule_partially_unknown_ids': [r['id'] for r in current if any(v is None for v in r['result']['labels'].values())],
        'rule_structural_literal_checks': bind(qa_path),
        'rule_changes_from_previous': bind(HERE / '全量前后标签差异.jsonl'),
        'rule_changed_label_ids': qa['changed_ids'],
        'unchanged_llm_output_bytes': True,
        'assembly_code': bind(__file__),
        'original_references_and_formal_paper_edited': False,
        'label_or_metric_based_selection': False,
        'new_independent_human_validation': False,
        'source_bindings': bindings,
    })
    path = destination / '同材料结果绑定.json'
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'bundle': str(path), 'sha256': sha(path),
        'n': 4480, 'rule_output_sha256': ex['output_sha256'],
        'rule_changes': qa['changed_ids'],
        'partially_unknown_ids': manifest['rule_partially_unknown_ids']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
