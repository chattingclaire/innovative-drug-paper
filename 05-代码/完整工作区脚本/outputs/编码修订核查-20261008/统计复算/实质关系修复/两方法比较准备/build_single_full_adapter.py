"""Create one compatibility manifest from a real complete full4480 rule bundle.

No extra derived QA files, coding/model calls or statistics are created here.
Do not execute until the root has frozen the actual new full execution bundle.
"""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = HERE.parents[2]
NF2 = W / '统计复算/来源读取与图示校正'
MANUAL = '24007a19a7242dc9e906c9704e8c0cc4e0fa513990a18b6651d06ba05043f3f9'
LOCKS = {
    'rule_input': '16b65b1ea5ed895173efb7b6c4bc91e74ddddbfa39d4b4c1b4018a2fe4df033c',
    'llm_input': 'e190cfb53b97f2950d498bd8e53feeec041f61c7a74c30c6024a194c71eeca2f',
    'llm_output': '8742c48d0c9567b346d7127b47280f22611656a20df72df58f2a76586e9ccfe4',
    'frame': 'c6a9d752fe9e0aeb378da68fe942418ce8d769c29e8616ba55fef2cb5ae1b4ec',
}
def sha(b):
    return hashlib.sha256(b).hexdigest()
def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--bundle', required=True)
    ap.add_argument('--expected-bundle-sha256', required=True)
    ap.add_argument('--output-manifest', default=str(HERE / 'single_full_adapter_manifest.json'))
    args = ap.parse_args()
    destination = Path(args.output_manifest).resolve()
    assert destination.is_relative_to(HERE) and not destination.exists(), 'fresh manifest under new preparation directory required'
    bindings = {}
    def read(ref):
        p = Path(ref['path']).resolve(); b = p.read_bytes()
        assert sha(b) == ref['sha256'], f'bound file SHA differs: {p}'
        bindings[str(p)] = {'sha256': sha(b), 'bytes': len(b)}
        return json.loads(b) if p.suffix == '.json' else b
    root_ref = {'path': str(Path(args.bundle).resolve()), 'sha256': args.expected_bundle_sha256}
    root = read(root_ref)
    assert root['status'] == 'complete_same_material_current_methods_bound_not_human_validated'
    assert root['target_n'] == 4481 and root['executed_n'] == 4480 and root['manual_sha256'] == MANUAL
    assert root['label_or_metric_based_selection'] is False
    assert root['rule_execution_scope'] == 'single_complete_actual_full4480_run'
    assert not root.get('rule_patch_ids') and not root.get('rule_recovery_ids') and not root.get('rule_recovery_runs')
    for role, h in LOCKS.items():
        assert root[role]['sha256'] == h, f'fixed common-source role changed: {role}'
    execution = read(root['rule_execution'])
    freeze = read(root['rule_runtime_freeze'])
    assert execution['n'] == 4480 and execution['status_counts'] == {'completed': 4480}
    assert type(execution['n_undetermined']) is int and 0 <= execution['n_undetermined'] <= 4480
    assert execution['input_sha256'] == LOCKS['rule_input'] and execution['output_sha256'] == root['rule_output']['sha256']
    assert execution['manual_sha256'] == MANUAL
    assert all(execution[k] is True for k in ('runtime_unchanged', 'runtime02_unchanged', 'protected_sources_input_base_manual_runner_unchanged', 'no_model_run', 'no_human_labels_or_metrics_used'))
    assert freeze['n'] == 4480 and freeze['manual_sha256'] == MANUAL
    assert freeze['input_sha256'] == LOCKS['rule_input']
    # The real freeze has no runtime_path or LLM-input field; do not invent them.
    assert isinstance(root['rule_runtime_dir'], str) and Path(root['rule_runtime_dir']).is_absolute()
    runtime = Path(root['rule_runtime_dir']).resolve()
    fixed_paths = [p for p, h in freeze['protected_input_source_files_before'].items()
                   if h == freeze['fixed_runtime_record_sha256'] and Path(p).suffix == '.json']
    assert len(fixed_paths) == 1, 'actual fixed-runtime record is missing or ambiguous'
    fixed_ref = {'path': fixed_paths[0], 'sha256': freeze['fixed_runtime_record_sha256']}
    fixed = read(fixed_ref)
    assert Path(fixed['runtime_path']).resolve() == runtime
    locks = freeze['runtime_before']
    assert locks and execution['runtime_before'] == execution['runtime_after'] == locks == fixed['runtime_all_files_sha256']
    tree_sha = sha(json.dumps(locks, ensure_ascii=False, sort_keys=True).encode())
    assert freeze['runtime_before_tree_sha256'] == execution['runtime_before_tree_sha256'] == execution['runtime_after_tree_sha256'] == tree_sha
    for n, h in locks.items():
        assert Path(n).name == n
        read({'path': str(runtime / n), 'sha256': h})
    for ref in root['source_bindings'].values():
        read(ref)
    old = read({'path': str(NF2 / '两方法比较准备/adapter_actual01/adapter_manifest.json'), 'sha256': '2dcf490ed21c43d8888c83fa695cca877b2157ca8c256562d512f5c766555e2a'})
    previous = read({'path': str(NF2 / '两方法比较准备/实际同材料比较01/输入绑定与来源校正核查.json'), 'sha256': '79342d6c560fbb230e8145fb753ea36703e5af63db06eb17a5ac64caa4e60fd7'})
    assert previous['all_technical_binding_checks_pass'] is True and previous['semantic_validity_not_certified'] is True
    for role in LOCKS:
        assert old['files'][role]['sha256'] == root[role]['sha256']
    assert all(sha(Path(p).read_bytes()) == m['sha256'] for p, m in bindings.items())
    files = {role: root[role] for role in ('rule_input', 'rule_output', 'llm_input', 'llm_output', 'frame')}
    files.update({role: old['files'][role] for role in ('first_full_qa', 'llm_lineage', 'visual_qa', 'source_correction_record')})
    files.update({'root_bundle': root_ref, 'rule_execution_qa': root['rule_execution'], 'rule_freeze_record': root['rule_runtime_freeze'], 'rule_fixed_runtime_record': fixed_ref})
    manifest = {
        'status': 'frozen_complete_inputs_outputs_for_comparison', 'target_n': 4481, 'executed_n': 4480,
        'manual_sha256': MANUAL, 'lineage_kind': old['lineage_kind'],
        'source_change_ids': ['RECODE25-03875'], 'source_changes_selected_by_labels_or_metrics': False,
        'rule_execution_complete': True, 'rule_lineage_kind': 'full_actual_execution',
        'rule_execution_scope': 'single_complete_actual_full4480_run',
        'rule_runtime_dir': str(runtime),
        'files': files, 'correction_llm_run': old['correction_llm_run'],
        'derived_adapter_manifest': True, 'not_new_experiment_evidence': True,
        'rule_execution_qa_role_is_raw_actual_execution_not_synthetic_QA': True,
        'one_compatibility_manifest_only_no_new_QA_wrappers': True,
        'reused_previous_LLM_technical_QA_ref': {'path': str(NF2 / '两方法比较准备/实际同材料比较01/输入绑定与来源校正核查.json'), 'sha256': '79342d6c560fbb230e8145fb753ea36703e5af63db06eb17a5ac64caa4e60fd7'},
        'raw_file_bindings_rechecked_while_deriving': bindings,
        'builder_sha256': sha(Path(__file__).read_bytes()),
    }
    destination.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'path': str(destination), 'sha256': sha(destination.read_bytes()), 'derived_compatibility_only': True, 'statistics_executed': False}, ensure_ascii=False))

if __name__ == '__main__':
    main()
