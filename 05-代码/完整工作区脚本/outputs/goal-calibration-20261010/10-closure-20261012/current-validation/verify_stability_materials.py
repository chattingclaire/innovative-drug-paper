"""Verify frozen stability material compatibility, without reading results."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RUN = ROOT / '06-coding/current-freeze-stability-external-capture-v2-sol/prepared-fixed800-87-v2'
V16 = ROOT / '01-review/source-interface-v16-article6-addendum-sol'


def bind(path):
    data = path.read_bytes()
    return {'path': str(path), 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def verified(binding):
    path = Path(binding['path'])
    actual = bind(path)
    assert all(actual[k] == binding[k] for k in ('path', 'bytes', 'sha256')), str(path)
    return path


def load(path):
    return json.loads(path.read_text())


def main():
    manifest = load(RUN / 'run-manifest.json')
    ids = load(verified(manifest['ordered_source_ids']))
    current_rows = load(V16 / 'packet-bindings-v16.json')
    current = {r['source_id']: r for r in current_rows}
    correspondence = load(V16 / 'full4481-material-correspondence.json')
    changed = set(correspondence['changed_source_ids'])
    assert len(ids) == len(set(ids)) == 800
    assert len(current_rows) == len(current) == 4481 and set(ids) <= set(current)
    assert changed == {'RECODE25-01402'} and not changed.intersection(ids)
    verified(manifest['manual'])
    verified(manifest['execution_prompt'])
    read_ids = []
    for batch in manifest['batches']:
        raw = load(verified(batch['assignments']['raw']))
        formatted = load(verified(batch['assignments']['W']))
        assert raw['source_ids'] == formatted['source_ids'] == batch['members']
        assert len(raw['packets']) == len(formatted['packets']) == batch['expected_N']
        for assignment in (raw, formatted):
            assert assignment['manual'] == manifest['manual']
            assert assignment['execution_prompt'] == manifest['execution_prompt']
        for a, w in zip(raw['packets'], formatted['packets']):
            source_id = a['source_id']
            assert source_id == w['source_id']
            assert a == current[source_id], source_id
            for key in ('source_bundle_sha256', 'source_bundle_utf8_bytes', 'output_id'):
                assert w[key] == a[key], (source_id, key)
            # Compare parsed JSON mechanically; never display or interpret text.
            assert load(verified(a)) == load(verified(w)), source_id
            read_ids.append(source_id)
    assert read_ids == ids
    result = {
        'at_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'Frozen input compatibility only, not repeat-stability results or accuracy acceptance',
        'script': bind(Path(__file__).resolve()),
        'sources': {p.name: bind(p) for p in (
            RUN / 'run-manifest.json', Path(manifest['ordered_source_ids']['path']),
            V16 / 'packet-bindings-v16.json', V16 / 'full4481-material-correspondence.json',
            V16 / 'byte-and-source-interface-proof.json')},
        'manual': manifest['manual'], 'execution_prompt': manifest['execution_prompt'],
        'batch_N': len(manifest['batches']), 'record_N': len(ids),
        'current_v16_raw_packet_bindings_equal_N': len(ids),
        'raw_and_W_actual_packet_hashes_verified_N': 2 * len(ids),
        'raw_and_W_parsed_objects_identical_N': len(ids),
        'current_v16_material_change_in_stability_sample': [],
        'results_or_labels_opened': False, 'models_called': False,
        'running_files_changed': False, 'stability_statistics_calculated': False,
        'formal_validation_complete': False,
        'limit': 'Does not authenticate serving-model identity, executions, selected outputs, or technical validity.',
    }
    (HERE / 'stability-material-compatibility.json').write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('sources', 'script', 'manual', 'execution_prompt')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
