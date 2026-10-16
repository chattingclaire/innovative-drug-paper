"""All-frame technical prebatch metadata; no formal sample or model calls.

Reads only frame-render-costs.json and budget-source-metadata.json, then uses
the packet builder's budget predicates. No source accessor, policy body, model,
candidate output, old test or formal execution sample is loaded.

Exact nonempty array bytes from the collector:
  R/H: sum(R_array_element_bytes) + (n - 1) + 2
  W:   sum(W_array_element_bytes) + 2 * (n - 1) + 4
The fixed prefix already equals len(prompt_bytes([], ...)) minus two bytes.
"""
import sys
sys.dont_write_bytecode = True

import collections
import datetime
import hashlib
import json
from pathlib import Path

import packet_builder as pb

ROOT = Path(__file__).resolve().parent
COST_PATH = ROOT / 'frame-render-costs.json'
ASSET_PATH = ROOT / 'budget-source-metadata.json'
EXPECTED_COST_SHA = 'fedb5c1e3b0f18f64cf945d1bbaca2cd2bc9ea3594d3bfc05ee8ed0430d7f2e3'
EXPECTED_ASSET_SHA = 'f9edc15bfb3838a3902322b286b3cba5ec499567c1e0d738978ac67bd9abed90'
OUTPUT_NAMES = ('operational-budget.json', 'budget-basis.json',
                'all-frame-technical-prebatch-plan.json')
ASSET_ENTRY_KEYS = {'sha256', 'absolute_path', 'bytes', 'mime_type', 'width', 'height'}
HASH_FIELDS = ('manual_sha256', 'instructions_sha256', 'output_schema_sha256',
               'scope_schema_sha256', 'source_binding_sha256', 'source_shape_sha256',
               'asset_metadata_sha256')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def load_metadata(path, expected):
    raw = path.read_bytes()
    require(sha(raw) == expected, 'Metadata file SHA changed: ' + path.name)
    return pb.parse(raw), {'path': str(path), 'sha256': sha(raw), 'bytes': len(raw)}


def positive_int(value, name, allow_zero=False):
    require(type(value) is int and value >= (0 if allow_zero else 1),
            'Unsupported integer metadata: ' + name)


def budget():
    value = {
        'budget_kind': 'frozen_operational_budget',
        'basis': ('Technical all-frame byte, CTX and SHA-deduplicated asset controls. '
                  'Keep the previous record ceiling of 41 and use original-frame '
                  'continuous longest-fitting prefixes. Exact collector R/W/H '
                  'bytes plus a fixed 512 KiB output reserve must fit 1.5 MiB. '
                  'These controls do not assert provider capacity, consumer reading, '
                  'formal sampling or model execution.'),
        'limits': {
            'max_units': 41,
            'max_prompt_and_output_bytes': 1572864,
            'reserve_output_bytes': 524288,
            'max_context_nodes': 128,
            'max_asset_count': 16,
            'max_asset_total_bytes': 7340032,
            'max_asset_individual_bytes': 2097152,
            'max_asset_total_pixels': 57000000,
        },
        'actual_backend_limits': {
            'context_tokens': None, 'input_tokens': None,
            'output_tokens': None, 'asset_limits': None,
        },
    }
    pb.check_budget(value)
    return value


def prepare_rows(cost, source):
    require(set(cost['fixed_prompt_prefix_bytes']) == {'R', 'W', 'H'},
            'All three actual fixed prompt prefixes are required')
    for variant, size in cost['fixed_prompt_prefix_bytes'].items():
        positive_int(size, 'fixed_prompt_prefix_bytes/' + variant)
    for field in HASH_FIELDS:
        require(pb.valid_sha(cost.get(field)), 'Missing exact binding: ' + field)
    require(cost['asset_metadata_sha256'] == EXPECTED_ASSET_SHA,
            'Collector asset metadata binding differs')
    metadata_inputs = {Path(item['path']).name: item['sha256']
                       for item in source['inputs']}
    require(cost['source_binding_sha256'] == metadata_inputs['frame-bundle-bindings.jsonl'],
            'Collector frame binding differs')
    require(cost['source_shape_sha256'] == metadata_inputs['field-shape-counts.json'],
            'Collector sealed source shape differs')
    require(cost.get('semantic_source_text_emitted') is False and
            cost.get('actual_model_calls') == 0 and
            cost.get('provider_capacity_inferred') is False,
            'Collector is not explicitly technical metadata only')
    require(source.get('frame_n') == 4481 and source.get('model_calls') == 0 and
            source.get('real_lookup_calls') == 0 and
            source.get('policy_body_title_or_label_values_emitted') is False,
            'Asset inventory is not the authorized metadata-only full frame')
    require(not source.get('gaps'), 'Unresolved asset metadata gaps must not be guessed')
    records = cost['ordered_records']
    metadata = source['ordered_records']
    require(len(records) == len(metadata) == 4481, 'All4481 ordered records required')
    require(len({record['id'] for record in records}) == 4481, 'Duplicate frame ID')
    assets = source['asset_lookup']
    for key, wrapper in assets.items():
        entry = wrapper['entry']
        require(set(entry) == ASSET_ENTRY_KEYS, 'Asset entry shape differs: ' + key)
        require(pb.valid_sha(entry['sha256']) and Path(entry['absolute_path']).is_absolute(),
                'Asset identity/location unsupported')
        require(key == entry['sha256'] + '@' + entry['absolute_path'],
                'Asset lookup key differs from explicit SHA/path')
        for name in ('bytes', 'width', 'height'):
            positive_int(entry[name], 'asset/' + name)
        require(wrapper['pixels'] == entry['width'] * entry['height'],
                'Asset pixel product differs')
    for ordinal, (record, original) in enumerate(zip(records, metadata), 1):
        require(record['id'] == original['source_id'] and
                original['frame_ordinal_1based'] == ordinal,
                'Original4481 frame order changed')
        require(record['source_bundle_sha256'] == original['new_bundle_sha256'] and
                record['source_bundle_bytes'] == original['bundle_utf8_bytes'] and
                record['context_nodes'] == original['context_nodes'],
                'Bundle byte/SHA/CTX binding differs at ordinal ' + str(ordinal))
        for field in ('source_bundle_bytes', 'R_array_element_bytes', 'W_array_element_bytes',
                      'current_quote_json_bytes', 'minimum_output_reserve_bytes', 'context_nodes'):
            positive_int(record[field], field)
        require(type(record['extension_available']) is bool, 'Extension flag must remain Boolean')
        require(record['minimum_output_reserve_bytes'] ==
                5 * record['current_quote_json_bytes'] + 8192,
                'Exact quote plus operational output reserve formula differs')
        keys = record['verified_asset_keys']
        require(isinstance(keys, list) and len(keys) == len(set(keys)) and
                set(keys) == set(original['verified_asset_keys']) and
                all(key in assets for key in keys),
                'Verified asset delivery differs at ordinal ' + str(ordinal))
        require(original['asset_cost_coverage_complete'] is True,
                'Incomplete asset cost coverage at ordinal ' + str(ordinal))
    return records, assets, cost['fixed_prompt_prefix_bytes']


def metrics(records, assets, prefixes, limits):
    n = len(records)
    require(n > 0, 'Budget metrics require a nonempty continuous group')
    compact = sum(record['R_array_element_bytes'] for record in records)
    indented = sum(record['W_array_element_bytes'] for record in records)
    arrays = {'R': compact + (n - 1) + 2,
              'H': compact + (n - 1) + 2,
              'W': indented + 2 * (n - 1) + 4}
    prompts = {variant: prefixes[variant] + arrays[variant] for variant in arrays}
    asset_keys = list(dict.fromkeys(key for record in records
                                   for key in record['verified_asset_keys']))
    by_sha = {}
    for key in asset_keys:
        entry = assets[key]['entry']
        if entry['sha256'] in by_sha:
            require(all(by_sha[entry['sha256']][field] == entry[field]
                        for field in ('bytes', 'mime_type', 'width', 'height')),
                    'Same-SHA costs differ across records or aliases')
        else:
            by_sha[entry['sha256']] = entry
    unique = list(by_sha.values())
    result = {
        'units': n,
        'source_bundle_bytes': sum(record['source_bundle_bytes'] for record in records),
        'prompt_bytes_by_variant': prompts,
        'worst_prompt_bytes': max(prompts.values()),
        'minimum_output_reserve_bytes': sum(record['minimum_output_reserve_bytes']
                                            for record in records),
        'current_quote_json_bytes': sum(record['current_quote_json_bytes'] for record in records),
        'context_nodes': sum(record['context_nodes'] for record in records),
        'asset_count': len(unique),
        'asset_location_count': len(asset_keys),
        'asset_total_bytes': sum(entry['bytes'] for entry in unique),
        'asset_individual_bytes': max([entry['bytes'] for entry in unique] or [0]),
        'asset_total_pixels': sum(entry['width'] * entry['height'] for entry in unique),
    }
    result['worst_prompt_plus_fixed_output_reserve_bytes'] = (
        result['worst_prompt_bytes'] + limits['reserve_output_bytes'])
    return result, asset_keys


def violations(value, limits):
    failed = []
    if value['units'] > limits['max_units']:
        failed.append('max_units')
    if value['minimum_output_reserve_bytes'] > limits['reserve_output_bytes']:
        failed.append('reserve_output_bytes')
    if value['worst_prompt_bytes'] + limits['reserve_output_bytes'] > limits['max_prompt_and_output_bytes']:
        failed.append('max_prompt_and_output_bytes')
    for name in ('context_nodes', 'asset_count', 'asset_total_bytes',
                 'asset_individual_bytes', 'asset_total_pixels'):
        if value[name] > limits['max_' + name]:
            failed.append('max_' + name)
    return failed


def group_records(records, assets, prefixes, allocation):
    limits = allocation['limits']
    single_metrics = []
    blockers = []
    for ordinal, record in enumerate(records, 1):
        value, _ = metrics([record], assets, prefixes, limits)
        failed = violations(value, limits)
        require(pb.within_budget(value, allocation) == (not failed),
                'Prebatch predicate diverges from packet_builder.within_budget')
        single_metrics.append(value)
        if failed:
            blockers.append({'frame_ordinal_1based': ordinal, 'source_id': record['id'],
                             'violations': failed, 'metrics': value})
    if blockers:
        return [], single_metrics, blockers
    groups = []
    current = []
    start = 1
    for ordinal, record in enumerate(records, 1):
        candidate = current + [record]
        value, _ = metrics(candidate, assets, prefixes, limits)
        failed = violations(value, limits)
        require(pb.within_budget(value, allocation) == (not failed),
                'Prebatch predicate diverges from packet_builder.within_budget')
        if current and failed:
            groups.append(make_group(current, start, assets, prefixes, limits,
                                     {'source_id': record['id'], 'violations': failed}))
            current = [record]
            start = ordinal
        else:
            current = candidate
    if current:
        groups.append(make_group(current, start, assets, prefixes, limits, None))
    flattened = [uid for group in groups for uid in group['source_ids']]
    require(flattened == [record['id'] for record in records], 'Prebatch lost or reordered records')
    for number, group in enumerate(groups, 1):
        group['technical_prebatch_id'] = 'technical-prebatch-' + str(number).zfill(4)
    return groups, single_metrics, []


def make_group(records, start, assets, prefixes, limits, next_blocker):
    value, keys = metrics(records, assets, prefixes, limits)
    require(not violations(value, limits), 'A reported group exceeds its frozen budget')
    return {'frame_start_1based': start, 'frame_end_1based': start + len(records) - 1,
            'source_ids': [record['id'] for record in records],
            'source_bundle_bindings': [{'source_id': record['id'],
                                       'source_bundle_sha256': record['source_bundle_sha256']}
                                      for record in records],
            'metrics': value, 'verified_asset_keys': keys,
            'next_record_would_exceed': next_blocker}


def write_exclusive(name, value):
    raw = canonical(value) + b'\n'
    path = ROOT / name
    with path.open('xb') as handle:
        handle.write(raw)
    return {'path': str(path), 'sha256': sha(raw), 'bytes': len(raw)}


def main():
    # Preserve every first output, including partial writes after a filesystem
    # failure. A later run must never repair or overwrite any prior report.
    require(all(not (ROOT / name).exists() for name in OUTPUT_NAMES),
            'Existing first budget/prebatch reports preserved; do not overwrite')
    cost, cost_binding = load_metadata(COST_PATH, EXPECTED_COST_SHA)
    source, asset_binding = load_metadata(ASSET_PATH, EXPECTED_ASSET_SHA)
    allocation = budget()
    records, assets, prefixes = prepare_rows(cost, source)
    groups, single, blockers = group_records(records, assets, prefixes, allocation)
    numeric_fields = ('source_bundle_bytes', 'worst_prompt_bytes',
                      'worst_prompt_plus_fixed_output_reserve_bytes',
                      'minimum_output_reserve_bytes', 'current_quote_json_bytes',
                      'context_nodes', 'asset_count', 'asset_location_count',
                      'asset_total_bytes', 'asset_individual_bytes', 'asset_total_pixels')
    single_max = {field: max(value[field] for value in single) for field in numeric_fields}
    single_max['prompt_bytes_by_variant'] = {
        variant: max(value['prompt_bytes_by_variant'][variant] for value in single)
        for variant in ('R', 'W', 'H')}
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state = ('technical_prebatch_ready_no_formal_sample' if not blockers
             else 'blocked_complete_single_bundle_exceeds_operational_budget')
    provenance = {'created_at_utc': timestamp, 'scope': 'all4481 technical metadata only',
                  'formal_sample_selected': False, 'formal_sample_manifest': None,
                  'formal_coding_inputs_frozen': False, 'model_calls': 0,
                  'new_source_reads': 0, 'source_lookup_calls': 0,
                  'provider_capacity_claimed': False, 'actual_backend_limits': allocation['actual_backend_limits']}
    basis = {**provenance, 'state': state, 'cost_file': cost_binding,
             'asset_metadata_file': asset_binding,
             'packet_builder_sha256': sha((ROOT / 'packet_builder.py').read_bytes()),
             'collector_bindings': {field: cost[field] for field in HASH_FIELDS},
             'operational_budget_sha256': sha(canonical(allocation)),
             'fixed_prompt_prefix_bytes': prefixes,
             'formulas': {'compact_R_or_H_array_bytes': 'sum(R_array_element_bytes)+(n-1)+2',
                          'indented_W_array_bytes': 'sum(W_array_element_bytes)+2*(n-1)+4',
                          'variant_prompt_bytes': 'fixed_prompt_prefix_bytes[variant]+array_bytes',
                          'minimum_output_reserve_bytes': 'sum(record.minimum_output_reserve_bytes)=5*sum(current_quote_json_bytes)+8192*n',
                          'prompt_and_output_guard': 'max(R,W,H prompt bytes)+524288<=1572864',
                          'asset_cost': 'union verified_asset_keys; SHA dedup costs, all paths retained'},
             'frame_record_count': len(records), 'complete_single_record_budget_pass_count': len(records) - len(blockers),
             'max_single_metrics': single_max, 'single_record_blockers': blockers,
             'technical_group_count': len(groups),
             'group_size_histogram': dict(sorted(collections.Counter(group['metrics']['units'] for group in groups).items())),
             'limitations': ['Byte/pixel/CTX controls are operating limits, not provider capacity guarantees.',
                             'The 8192-byte per-record allowance is a mechanical output reserve, not an output-length guarantee.',
                             'This full-frame technical partition does not select or inspect a formal experiment sample.',
                             'Collector supplied exact rendering bytes and quote JSON escaping; this script never reads policy text.']}
    order = [record['id'] for record in records]
    plan = {**provenance, 'state': state,
            'plan_kind': 'all_frame_continuous_longest_prefix_technical_prebatch',
            'cost_file': cost_binding, 'asset_metadata_file': asset_binding,
            'operational_budget_sha256': sha(canonical(allocation)),
            'global_order': order, 'global_order_sha256': sha(canonical(order)),
            'frame_record_count': len(order), 'covered_record_count': sum(group['metrics']['units'] for group in groups),
            'original_order_coverage_complete': not blockers and
                [uid for group in groups for uid in group['source_ids']] == order,
            'single_record_blockers': blockers, 'technical_group_count': len(groups),
            'asset_metadata_lookup_path': str(ASSET_PATH),
            'asset_entry_location': 'asset_lookup[verified_asset_key][entry]; pixels are wrapper metadata',
            'batches': groups}
    outputs = [write_exclusive(OUTPUT_NAMES[0], allocation),
               write_exclusive(OUTPUT_NAMES[1], basis),
               write_exclusive(OUTPUT_NAMES[2], plan)]
    print(json.dumps({'state': state, 'frame_records': len(records),
                      'single_record_budget_pass_count': len(records) - len(blockers),
                      'single_record_blocker_count': len(blockers),
                      'technical_group_count': len(groups),
                      'group_size_histogram': basis['group_size_histogram'],
                      'original_order_coverage_complete': plan['original_order_coverage_complete'],
                      'max_single_metrics': single_max, 'outputs': outputs,
                      'formal_sample_selected': False, 'model_calls': 0}, ensure_ascii=False))
    return 2 if blockers else 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (ValueError, OSError, KeyError, TypeError) as exc:
        # stdout/stderr and the calling chat retain this first-failure summary;
        # no candidate/report is overwritten and no automatic retry is run.
        print(json.dumps({'state': 'technical_prebatch_failure_preserved',
                          'error_type': type(exc).__name__, 'detail': str(exc),
                          'formal_sample_selected': False, 'model_calls': 0},
                         ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
