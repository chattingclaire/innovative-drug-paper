"""Read-only independent reconstruction of a dimension-explicit final seal."""
import argparse
import copy
import json
from pathlib import Path
from execution_integrity_v6 import audit_run, sha, read, lines

HERE = Path(__file__).resolve().parent
ROUND = HERE.parent


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--sealed', required=True)
    args = parser.parse_args(); sealed = Path(args.sealed).resolve()
    manifest_path = sealed / 'final_manifest.json'; manifest = read(manifest_path)
    assert manifest['status'] == 'complete_actual_execution_dimension_explicit' and manifest['n'] == 4924
    version = manifest['material_version']
    assert manifest['references_or_metrics_used_to_select_outputs'] is False
    assert manifest['all_original_197_batches_attempt_audited'] is True
    assert manifest['requested_model'] == 'gpt-5.6-sol' and manifest['reasoning_effort'] == 'medium'
    for key in ['source_sha256', 'outputs_sha256', 'material_manifests_sha256']:
        for path, digest in manifest[key].items(): assert sha(path) == digest, path
    material_path = ROUND / f'effective_blind_inputs_{version}.jsonl'
    rule_path = ROUND / f'rule_inputs_shared_{version}.jsonl'
    material = lines(material_path); rules = lines(rule_path)
    assert len(material) == len(rules) == 4924
    assert all(a['id'] == b['id'] and a['text'] == b['input']['unit_text']
               and a['contexts'] == b['input']['llm_v29_shared_context'] for a, b in zip(material, rules))
    by_id = {r['id']: r for r in material}; cache = {}

    def audit(run):
        run = str(Path(run).resolve())
        if run not in cache: cache[run] = audit_run(run)
        return cache[run]

    original = audit(HERE / 'production-25')
    assert original['completed_batch_count'] == original['plan']['batch_count'] == 197
    assert not original['all_material_issue_records']
    lineage = read(sealed / 'selected_actual_execution_lineage.json')
    rebuilt_if = []; selected_raw_hashes = {}; original_groups = []; if_input = []
    for entry in lineage['if']:
        run = entry['run']; current = audit(run); selected = current['selected'][entry['batch_index']]
        index = entry['original_batch_index']; original_groups.append(index)
        assert current['plan']['prompt_sha256'] == original['plan']['prompt_sha256']
        assert selected['raw_path'] == entry['raw_path'] and sha(selected['raw_path']) == entry['raw_output_sha256']
        assert selected['selection_sha256'] == entry['selection_sha256']
        assert selected['attempts'] == entry['all_attempts']
        for inp in selected['input']: assert inp == by_id[inp['id']]
        rebuilt_if.extend(selected['output']['rows']); if_input.extend(selected['input'])
        selected_raw_hashes[selected['raw_path']] = sha(selected['raw_path'])
        if index in manifest['changed_batches_unconditional']:
            assert entry['reason'] == 'changed_input_complete_batch_unconditional'
            assert selected['input'] == material[(index - 1) * 25:index * 25]
        elif index in manifest['technical_repair_original_batches']:
            assert entry['reason'] == 'entire_three_failure_original_batch_five_row_technical_retry'
        else:
            assert entry['reason'] == 'exact_final_input_equality' and Path(run).resolve() == (HERE / 'production-25').resolve()
    assert if_input == material
    assert sorted(set(original_groups)) == list(range(1, 198))
    assert len(lineage['if']) == manifest['selected_I_F_actual_call_n']
    assert len(set(original_groups)) == manifest['selected_I_F_batch_n'] == 197
    assert rebuilt_if == lines(sealed / 'all_predictions_if_actual.jsonl')
    seec = {}; refreshed = set()
    old = ROUND.parent / 'recall-revision-20261007/llm-v30'
    old_prompt_sha = sha(old / '完整系统提示词-v30-候选03.txt')
    for entry in lineage['se_ec_material_refresh']:
        actual = audit(entry['run']); selected = actual['selected'][entry['batch_index']]
        assert actual['plan']['prompt_sha256'] == old_prompt_sha
        assert selected['raw_path'] == entry['raw_path'] and sha(selected['raw_path']) == entry['raw_output_sha256']
        for inp, row in zip(selected['input'], selected['output']['rows']):
            assert inp == by_id[inp['id']] and inp['id'] == row['id'] and row['id'] not in seec
            refreshed.add(row['id']); seec[row['id']] = row
        selected_raw_hashes[selected['raw_path']] = sha(selected['raw_path'])
    retained_keys = [k for k in lineage if k.startswith('se_ec_retained_') and k.endswith('_row_sources')]
    assert len(retained_keys) == 1
    retained = lineage[retained_keys[0]]
    for rid, entry in retained.items():
        attempt = Path(entry['raw_path']).parent; run = attempt.parents[3]
        index = int(attempt.parents[1].name.split('-')[1])
        actual = audit(run); selected = actual['selected'][index]
        assert actual['plan']['prompt_sha256'] == old_prompt_sha
        assert selected['raw_path'] == entry['raw_path'] and sha(selected['raw_path']) == entry['raw_sha256']
        packet_rows = {i['id']: i for i in selected['input']}; output_rows = {r['id']: r for r in selected['output']['rows']}
        assert packet_rows[rid] == by_id[rid] and rid not in seec
        seec[rid] = output_rows[rid]; selected_raw_hashes[selected['raw_path']] = sha(selected['raw_path'])
    assert len(refreshed) == manifest['S_E_Ec_same_prompt_material_batch_rerun_n']
    assert len(retained) == manifest['S_E_Ec_original_actual_retained_n']
    assert len(seec) == 4924 and set(seec) == set(by_id)
    final = lines(sealed / 'all_predictions_composite.jsonl')
    assert [r['id'] for r in final] == [r['id'] for r in material]
    for expected_if, actual in zip(rebuilt_if, final):
        rid = actual['id']; source = seec[rid]
        assert actual['labels'] == {**{d: source['labels'][d] for d in ['S', 'E', 'Ec']}, **expected_if['labels']}
        assert actual['dimension_reasons'] == {**{d: source['dimension_reasons'][d] for d in ['S', 'E', 'Ec']}, **expected_if['dimension_reasons']}
        assert actual['evidence'] == [e for e in source['evidence'] if e['dimension'] in ['S', 'E', 'Ec']] + expected_if['evidence']
        assert actual['innovation_subtypes'] == expected_if['innovation_subtypes']
        assert actual['fairness_subtypes'] == expected_if['fairness_subtypes']
        assert actual['safety_quality_basis'] == source['safety_quality_basis']
        assert actual['material_version'] == version
        assert actual['se_ec_actual_source'] in selected_raw_hashes
    # Failed five-row technical repair attempts stay auditable but are never
    # selected when a subsequent full material replacement is required.
    repair_runs = []
    for plan_path in HERE.glob('technical-repair-original-*/technical_repair_plan.json'):
        run = plan_path.parent / 'actual-five-row-retry'
        if (run / 'execution_summary.json').exists():
            audited = audit(run); repair_runs.append({'plan_path': str(plan_path), 'plan_sha256': sha(plan_path),
                                                     'run': str(run), 'failed_batches': audited['failed_batches']})
    audit_summaries = [{'run': a['run'], 'plan_sha256': a['plan_sha256'],
                        'completed_batch_count': a['completed_batch_count'], 'accepted_batch_count': len(a['selected']),
                        'actual_attempt_count': a['all_actual_attempt_count'],
                        'all_attempt_tool_events': a['all_attempt_tool_events'],
                        'failed_batch_indices': [f['batch'] for f in a['failed_batches']],
                        'observed_model_fields': a['observed_model_fields']} for a in cache.values()]
    result = {'status': 'passed', 'scope': 'Independent actual-call/material/dimension-block reconstruction; no semantic accuracy or human validation claim.',
              'n': 4924, 'material_version': version, 'selected_I_F_original_batch_groups': 197,
              'selected_I_F_actual_call_count': len(lineage['if']), 'S_E_Ec_refreshed_n': len(refreshed),
              'S_E_Ec_retained_n': len(retained), 'all_original_197_batches_audited': True,
              'all_selected_first_valid_actual_attempt': True, 'all_selected_tool_event_count': 0,
              'all_4924_actual_selected_row_material_exactly_final': True,
              'all_4924_dimension_blocks_reconstructed_from_unmodified_actual_raw': True,
              'raw_json_equals_actual_final_message_event': True,
              'requested_model': 'gpt-5.6-sol', 'reasoning_effort': 'medium', 'provider_internal_revision': 'not_exposed',
              'raw_selected_model_name_exposure': 'May be absent in CLI events; requested model parameter is verified, not an unexposed backend revision.',
              'agent_reference_or_metric_access': False, 'failed_technical_repair_runs_preserved': repair_runs,
              'all_actual_audited_runs': audit_summaries,
              'final_manifest_path': str(manifest_path), 'final_manifest_sha256': sha(manifest_path),
              'prediction_path': str(sealed / 'all_predictions_composite.jsonl'), 'prediction_sha256': sha(sealed / 'all_predictions_composite.jsonl'),
              'effective_input_path': str(material_path), 'effective_input_sha256': sha(material_path),
              'rule_input_path': str(rule_path), 'rule_input_sha256': sha(rule_path),
              'selected_raw_response_sha256': selected_raw_hashes, 'verifier_sha256': sha(__file__),
              'attempt_reconstructor_sha256': sha(HERE / 'execution_integrity_v6.py')}
    path = ROUND / f'最终LLM执行独立核验-v31-{version}.json'
    assert not path.exists(), ('independent QA already frozen', path)
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'QA_path': str(path), 'QA_sha256': sha(path), 'n': 4924,
                      'composite_sha256': result['prediction_sha256']}, ensure_ascii=False))


if __name__ == '__main__': main()
