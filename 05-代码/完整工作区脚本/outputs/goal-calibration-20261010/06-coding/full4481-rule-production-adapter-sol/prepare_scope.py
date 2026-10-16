"""Mechanical full4481 scope construction only; no coder imports or inference."""
import argparse
import hashlib
import json
from pathlib import Path
from interface_common import parse_json, verify_binding

HERE = Path(__file__).resolve().parent
VERSION = 'full4481-production-provisional-rule-driver-1'


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)}


def exact_binding(value):
    if isinstance(value, str):
        return binding(value)
    if not isinstance(value, dict) or set(value) != {'path', 'sha256', 'bytes'}:
        raise ValueError('exact path/sha256/bytes binding required')
    verify_binding(value)
    return dict(value)


def build_scope(params):
    """Read only explicitly supplied files. Preserve declared source material entries."""
    inventory_binding = exact_binding(params['material_inventory_file'])
    inventory = parse_json(Path(inventory_binding['path']).read_bytes())
    materials = inventory['material_bindings'] if isinstance(inventory, dict) else inventory
    if not isinstance(materials, list):
        raise ValueError('source material inventory must contain a material_bindings list')
    ids_binding = exact_binding(params['ordered_record_ids_file'])
    ids = parse_json(Path(ids_binding['path']).read_bytes())
    if isinstance(ids, dict):
        ids = ids['approved_record_ids']
    if not isinstance(ids, list) or any(not isinstance(x, str) or not x for x in ids):
        raise ValueError('explicit ordered source IDs required')
    if len(ids) != 4481 or len(set(ids)) != 4481:
        raise ValueError('complete unique 4481 source order required')
    paths = {}
    for item in materials:
        if not isinstance(item, dict) or set(item) != {'path', 'sha256', 'bytes'}:
            raise ValueError('inventory entries must be exact path/sha256/bytes bindings')
        path = str(Path(item['path']).resolve())
        if path != item['path'] or not Path(path).is_absolute():
            raise ValueError('inventory paths must be resolved absolute paths')
        if path in paths and paths[path] != item:
            raise ValueError('conflicting source material bindings')
        paths[path] = dict(item)
    scope = {key: params[key] for key in ('authorization_id', 'manual_version',
        'v12_source_base', 'complete_bundles_canonical_sha256')}
    for key in ('source_packet', 'source_package_seal', 'source_manifest',
        'manual', 'prompt', 'protocol', 'source_reading_protocol_code', 'release'):
        scope[key] = exact_binding(params[key])
    scope['algorithm_bindings'] = binding(HERE / 'algorithm-bindings.json')
    for item in [inventory_binding, ids_binding, scope['algorithm_bindings']] + [scope[key]
            for key in ('source_packet', 'source_package_seal', 'source_manifest',
                'manual', 'prompt', 'protocol', 'source_reading_protocol_code', 'release')]:
        if item['path'] in paths and paths[item['path']] != item:
            raise ValueError('supplied binding conflicts with source inventory')
        paths[item['path']] = dict(item)
    output = str(Path(params['output_directory']).resolve())
    if Path(output).exists():
        raise ValueError('first output exists; never overwrite')
    status = params.get('status', 'prepared_not_released')
    if status not in ('prepared_not_released', 'frozen_for_execution'):
        raise ValueError('unsupported mechanical scope status')
    scope.update(driver_version=VERSION, status=status,
        execution_purpose='production_provisional', output_directory=output,
        max_actual_cohort_inference_runs=1, approved_record_ids=ids,
        expected_record_N=4481, expected_dimension_N=22405,
        source_manifest_sha256=scope['source_manifest']['sha256'],
        material_bindings=list(paths.values()),
        source_material_inventory_binding=inventory_binding,
        ordered_record_ids_binding=ids_binding,
        formal_validation_complete=False, human_validation_complete=False,
        calibration_labels_already_disclosed=True, blind_validation=False,
        algorithm_origin='unchanged v4 AI-development disclosed-calibration candidate',
        new2_new4_reference_comparison_authorized=False)
    return scope


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--params', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    params = parse_json(Path(args.params).read_bytes())
    scope = build_scope(params)
    with Path(args.out).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(scope, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps(binding(args.out), ensure_ascii=False))


if __name__ == '__main__':
    main()
