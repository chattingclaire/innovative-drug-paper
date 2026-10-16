"""Freeze complete intact historical development rows and compare 02845 requests.

Reads all-corpus files only mechanically to select the already exposed 240 IDs.
No reserved unit is exposed in an output or given a semantic review here.
"""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PRIOR = PROJECT / 'outputs/coding-revision-20261007-r3/llm-candidate03-development'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canon(obj):
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def lines(path):
    return [json.loads(s) for s in Path(path).read_text().splitlines() if s.strip()]


def bind(path):
    return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def save_new(path, data):
    data = data if isinstance(data, bytes) else data.encode()
    if path.exists():
        assert path.read_bytes() == data
    else:
        path.write_bytes(data)


def dump_new(path, obj):
    save_new(path, json.dumps(obj, ensure_ascii=False, indent=2) + '\n')


def main():
    freeze = read(HERE / 'candidate05_development_freeze.json')
    ids = [r['id'] for r in lines(freeze['exposed240_input']['path'])]
    excluded = set(read(freeze['human_reserved_exclusion_metadata']['path'])['all_registered_members_of_reserved_families_unit_ids'])
    assert len(ids) == 240 and not excluded.intersection(ids)
    target_ids = set(ids)
    history = HERE / 'historical-frozen'
    history.mkdir(exist_ok=True)
    sources = {
        'old_candidate03_exposed240_rows': PRIOR / 'exposed240-first-run/all_predictions.jsonl',
        'old_candidate04_exposed240_rows': PRIOR / 'exposed240-candidate04-first-run/all_predictions.jsonl',
        'current_full_candidate03_exposed240_rows': PRIOR / 'full-corpus-candidate03-material-v14-single-unit-reconciled-development/all_predictions.jsonl'
    }
    frozen = {}
    for name, source in sources.items():
        byid = {r['id']: r for r in lines(source) if r['id'] in target_ids}
        assert set(byid) == target_ids
        destination = history / (name + '_PRIVATE.jsonl')
        if name.startswith('old_'):
            assert [r['id'] for r in lines(source)] == ids
            save_new(destination, source.read_bytes())
        else:
            save_new(destination, ''.join(json.dumps(byid[rid], ensure_ascii=False) + '\n' for rid in ids))
        assert [r['id'] for r in lines(destination)] == ids
        assert all(r == byid[r['id']] for r in lines(destination))
        frozen[name] = bind(destination)
    provenance_source = PRIOR / 'full-corpus-candidate03-material-v14-single-unit-reconciled-development/row_provenance.jsonl'
    provenance = {r['id']: r for r in lines(provenance_source) if r['id'] in target_ids}
    assert set(provenance) == target_ids
    prov_dest = history / 'current_full_candidate03_exposed240_provenance_PRIVATE.jsonl'
    save_new(prov_dest, ''.join(json.dumps(provenance[rid], ensure_ascii=False) + '\n' for rid in ids))
    frozen['current_full_candidate03_240_row_provenance'] = bind(prov_dest)

    old_attempt = PRIOR / 'exposed240-first-run/batches/batch-0007/attempts/attempt-01'
    current_attempt = Path(provenance['RECODE25-02845']['actual_attempt_path'])
    assert current_attempt.name == 'attempt-01' and 'batch-0114' in str(current_attempt)
    prompt = (PRIOR / 'candidate03_prompt.txt').read_text()
    packet_old = read(old_attempt / 'input.json')
    packet_current = read(current_attempt / 'input.json')
    row_old = next(r for r in packet_old['rows'] if r['id'] == 'RECODE25-02845')
    row_current = next(r for r in packet_current['rows'] if r['id'] == 'RECODE25-02845')
    assert row_old == row_current
    comparison = {'status': 'SAME_UNIT_AND_FULL_PROMPT_CROSS_REQUEST_REVERSAL_NOT_ISOLATED_REPEAT_EXPERIMENT',
                  'id': 'RECODE25-02845', 'unit_objects_equal': row_old == row_current,
                  'unit_object_canonical_sha256': canon(row_old),
                  'field_comparisons': {k: {'equal': row_old[k] == row_current[k], 'canonical_sha256': canon(row_old[k])} for k in row_old},
                  'text_contexts_certificates_and_usage_unchanged': True,
                  'same_complete_prompt_sha256': sha(PRIOR / 'candidate03_prompt.txt'),
                  'citation_isolation_tech01_in_common_prompt': 'citation-isolation-tech01' in prompt,
                  'calls': {}}
    for name, attempt, packet in [('old_exposed240', old_attempt, packet_old), ('current_full_corpus', current_attempt, packet_current)]:
        request = (attempt / 'request.txt').read_text()
        prefix = request.split('\n\n--- 本批冻结盲法输入 ---\n')[0]
        suffix = '\n\n只根据上述给定材料直接返回规定JSON。禁止外部检索、读取文件、调用任何工具、运行命令或代码。不从ID推断答案。'
        assert prefix == prompt
        assert request == prompt + '\n\n--- 本批冻结盲法输入 ---\n' + json.dumps(packet, ensure_ascii=False) + suffix
        metadata = read(attempt / 'run_metadata.json')
        output = next(r for r in read(attempt / 'raw_output.json')['rows'] if r['id'] == 'RECODE25-02845')
        comparison['calls'][name] = {
            'attempt_path': str(attempt.resolve()), 'input': bind(attempt / 'input.json'),
            'request': bind(attempt / 'request.txt'), 'raw_output': bind(attempt / 'raw_output.json'),
            'metadata': bind(attempt / 'run_metadata.json'), 'events': bind(attempt / 'events.jsonl'),
            'batch_size': len(packet['rows']), 'target_position_1based': next(i + 1 for i, r in enumerate(packet['rows']) if r['id'] == 'RECODE25-02845'),
            'complete_prefix_equals_candidate03_prompt': True, 'extra_technical_appendix_beyond_common_prompt': False,
            'request_sha256': metadata['request_sha256'], 'requested_model': metadata['requested_model'],
            'reasoning_effort': metadata['reasoning_effort'], 'cli_version': metadata['cli_version'],
            'cli_binary_sha256': metadata['cli_binary_sha256'], 'actual_command': metadata['command'],
            'provider_internal_model_revision': metadata.get('provider_internal_model_revision', 'not_exposed'),
            'labels': output['labels'], 'I_reason': output['dimension_reasons']['I']}
    old_call, cur_call = comparison['calls'].values()
    comparison['equal_cli_version_binary_model_and_effort'] = all(old_call[k] == cur_call[k] for k in ['requested_model', 'reasoning_effort', 'cli_version', 'cli_binary_sha256'])
    comparison['entire_request_identical'] = old_call['request_sha256'] == cur_call['request_sha256']
    comparison['batch_member_overlap_count'] = len({r['id'] for r in packet_old['rows']} & {r['id'] for r in packet_current['rows']})
    comparison['interpretation_limit'] = [
        'The material and complete prompt are equal for the target unit; this excludes a target-material change and an extra full-corpus citation appendix for this target call.',
        'Other batch records, target position, independent execution occasion, temporary CLI working directory and output paths differ.',
        'No isolated experiment varies batch composition or order alone. No identical full-request repeat is being compared here.',
        'Execution dates/occasion and provider internal model revision are not controlled; the recorded CLI model name is not a server revision guarantee.',
        'The reversal establishes cross-request variation under the same unit material and semantic instructions; it cannot identify a single cause or justify voting/relabeling.'
    ]
    comparison_path = HERE / 'historical_02845_request_comparison.json'
    dump_new(comparison_path, comparison)
    frozen['historical_02845_request_comparison'] = bind(comparison_path)
    manifest = {'status': 'FROZEN_BEFORE_CANDIDATE05_CALLS', 'development_only': True,
                'all240_intact_historical_rows_preserved': True, 'no_dimensions_spliced': True,
                'reserved_member_intersection': [], 'frozen_files': frozen,
                'original_sources': {name: bind(path) for name, path in sources.items()},
                'provenance_source': bind(provenance_source),
                'selection': 'Use old240 IDs only; preserve original complete rows. Historical labels are comparator outputs, not truth.'}
    dump_new(HERE / 'historical_comparison_freeze.json', manifest)
    print(json.dumps({'status': manifest['status'], 'frozen_histories': 3, 'intact_rows_per_history': 240,
                      'actual_model_calls': 0, '02845_entire_request_identical': comparison['entire_request_identical'],
                      '02845_unit_and_full_prompt_equal': True}, ensure_ascii=False))


if __name__ == '__main__':
    main()
