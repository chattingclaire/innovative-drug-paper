"""Execute only the already frozen secondary analysis after complete primary output.

This post-freeze orchestration file defines no metric, transformation or labels.
All inferential modules are loaded from hash-verified frozen bytes. First receipt
bytes, complete primary archive and current snapshot must agree before execution.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import types
from datetime import datetime, timezone


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('freeze', 'holdout', 'receipts', 'primary', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    require(all(p.is_absolute() for p in vars(args).values()), 'Absolute paths required')
    partial = args.output.with_name('.' + args.output.name + '.partial')
    require(not os.path.lexists(args.output) and not os.path.lexists(partial), 'Refusing existing output')
    freeze_raw = args.freeze.read_bytes()
    freeze = json.loads(freeze_raw)
    bridge_path = Path(freeze['files']['results_bridge']['path'])
    bridge_raw = bridge_path.read_bytes()
    require(sha(bridge_raw) == freeze['files']['results_bridge']['sha256'], 'Frozen bridge changed')
    bridge = types.ModuleType('_frozen_v600_bridge')
    bridge.__file__ = str(bridge_path)
    exec(compile(bridge_raw, str(bridge_path), 'exec'), bridge.__dict__)
    # The frozen parser now verifies duplicate/nonfinite JSON as well.
    bridge.read_json(freeze_raw, 'freeze')
    primary_raw = args.primary.read_bytes()
    primary = bridge.read_json(primary_raw, 'completed primary')
    require(primary.get('status') == 'completed_frozen_paired_ID_join_not_validation_pass'
            and primary.get('phase') == 'V600', 'Complete V600 primary output required')
    bundle, tracked, inventory = bridge.load_snapshot(args.freeze, args.holdout)
    payload, archive = bridge.assemble(bundle)
    original_archive = primary['archive']
    extra = {'runtime', 'filesystem_snapshot_manifest', 'input_inventory'}
    require(set(original_archive) == set(archive) | extra, 'Unexpected primary archive inventory')
    require({k: v for k, v in original_archive.items() if k not in extra} == archive,
            'Current assembled archive differs from completed primary originals')
    require(original_archive['filesystem_snapshot_manifest'] == tracked
            and original_archive['input_inventory'] == inventory, 'Primary/current file snapshot differs')
    require(primary['paired_statistics']['sample_n'] == len(payload['rows'])
            and primary['paired_statistics']['population_N'] == payload['population_N'],
            'Primary/current design differs')
    receipt_hashes = {}
    require(bridge.inventories(args.receipts)['results'] == inventory['results'], 'First receipt inventory differs')
    binding_raw = (args.receipts / '接收绑定.json').read_bytes()
    binding = bridge.read_json(binding_raw, 'receipt binding')
    require(binding['freeze_sha256'] == sha(bundle['freeze'])
            and binding['seal_sha256'] == sha(bundle['seal'])
            and binding['holdout'] == str(args.holdout.resolve()), 'First receipt binding differs')
    receipt_hashes[str(args.receipts / '接收绑定.json')] = sha(binding_raw)
    for relative, raw in bundle['results'].items():
        path = args.receipts / relative
        record_path = args.receipts / 'receipt-records' / relative
        received, record_raw = path.read_bytes(), record_path.read_bytes()
        record = bridge.read_json(record_raw, 'first receipt record')
        require(received == raw and record['sha256'] == sha(raw)
                and record['byte_count'] == len(raw) and record['file'] == relative
                and record['binding'] == binding, 'First receipt original changed')
        receipt_hashes[str(path)] = sha(received)
        receipt_hashes[str(record_path)] = sha(record_raw)
    frozen = bundle['frozen']
    survey = bridge.source_module(frozen['survey_metrics'], 'survey_metrics', numpy_allowed=True)
    paired = bridge.source_module(frozen['paired_version_metrics'], 'paired_version_metrics',
                                  {'survey_metrics': survey}, numpy_allowed=True)
    sensitivity = bridge.source_module(frozen['paired_sensitivity'], 'paired_sensitivity')
    require(paired.base is survey, 'Frozen survey injection failed')
    output = sensitivity.analyze(payload, archive, paired_metrics=paired)
    bridge.check_unchanged(tracked, {p: sha(Path(p).read_bytes()) for p in tracked})
    bridge.check_unchanged(inventory, bridge.inventories(args.holdout))
    bridge.check_unchanged(receipt_hashes, {p: sha(Path(p).read_bytes()) for p in receipt_hashes})
    require(args.primary.read_bytes() == primary_raw, 'Primary output changed during secondary execution')
    output.update(source_primary_sha256=sha(primary_raw), freeze_manifest_sha256=sha(bundle['freeze']),
                  created_at=datetime.now(timezone.utc).isoformat(),
                  executor_sha256=sha(Path(__file__).read_bytes()),
                  frozen_module_hashes={k: sha(frozen[k]) for k in
                      ('results_bridge', 'survey_metrics', 'paired_version_metrics', 'paired_sensitivity')},
                  first_receipt_hashes=receipt_hashes)
    bridge.publish_json(args.output, output)
    print(json.dumps({'output': str(args.output), 'status': output['status'],
                      'scenarios': {k: v['status'] for k, v in output['scenarios'].items()}}, ensure_ascii=False))


if __name__ == '__main__':
    main()
