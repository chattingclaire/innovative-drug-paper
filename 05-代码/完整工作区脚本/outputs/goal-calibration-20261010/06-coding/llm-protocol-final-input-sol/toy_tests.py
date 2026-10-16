"""Constructed-source mechanical tests; never produce candidate coding labels.

Only this file, toy-test-results.run03.json and constructed files in toy-fixtures are
written. Real source lookup, owner binding, models and candidate bodies are not
used. The v11 row schema is used solely as an authorized toy shape schema; every
toy complete bundle declares v12. freeze_inputs writes are captured in memory.
"""
import sys
sys.dont_write_bytecode = True

import copy
import datetime
import hashlib
import json
import struct
import zlib
from pathlib import Path
from unittest.mock import patch

import packet_builder as pb
import native_records as nr

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / 'toy-fixtures'
ASSETS = FIXTURES / 'constructed-assets'
OUTSIDE = FIXTURES / 'constructed-outside-allowed-root'
RESULTS = []
MANUAL = '构造手册：仅检查机械输入契约。'.encode('utf-8')
# A toy technical schema is displayed as prompt text, never a coding output.
TOY_OUTPUT_SCHEMA = b'{"type":"object","properties":{"technical_receipt":{"type":"string"}}}'


def ensure(condition, message='assertion failed'):
    if not condition:
        raise AssertionError(message)


def case(name, callback):
    try:
        callback()
    except Exception as exc:
        RESULTS.append({'name': name, 'passed': False,
                        'error_type': type(exc).__name__, 'detail': str(exc)})
    else:
        RESULTS.append({'name': name, 'passed': True})


def reject(callback):
    try:
        callback()
    except (pb.InputFailure, OSError):
        return
    raise AssertionError('mechanical guard accepted the invalid constructed input')


def png(width=2, height=3):
    def chunk(kind, raw):
        return struct.pack('>I', len(raw)) + kind + raw + struct.pack('>I', zlib.crc32(kind + raw) & 0xffffffff)
    rows = b''.join(b'\0' + b'\x12\x34\x56' * width for _ in range(height))
    return (b'\x89PNG\r\n\x1a\n' +
            chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)) +
            chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


def write_constructed(path, raw):
    ensure(path.resolve().is_relative_to(FIXTURES.resolve()), 'toy write escaped fixtures')
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        ensure(path.read_bytes() == raw, 'existing constructed asset differs')
    else:
        with path.open('xb') as handle:
            handle.write(raw)


def fixture_bundle():
    image_path = ASSETS / 'page.png'
    snapshot_path = ASSETS / 'snapshot.pdf'
    full_path = ASSETS / 'full-text-resource-with-source-sha.json'
    write_constructed(image_path, png())
    write_constructed(OUTSIDE / 'page.png', png())
    write_constructed(snapshot_path, b'%PDF-1.4\n% wholly constructed snapshot bytes\n%%EOF\n')
    snapshot_sha = pb.file_sha(snapshot_path)
    image_sha = pb.file_sha(image_path)
    source_id = 'SOURCE-' + snapshot_sha
    ref = {'sha256': snapshot_sha, 'source_resource_id': source_id,
           'locator': {'physical_pages': [1], 'paragraph_id': 'TOY-P1',
                       'regions': [{'physical_page': 1, 'bbox_px_xyxy': [0, 0, 2, 3],
                                    'page_asset': 'page.png'}]}}
    resource = {'source_resource_id': 'TOY-RESOURCE-P1', 'kind': 'original_prose',
                'text': '甲🙂乙e\u0301丙；原文例示。',
                'text_sha256': pb.sha('甲🙂乙e\u0301丙；原文例示。'.encode()),
                'source_ref': copy.deepcopy(ref), 'unknown_status': 'unknown',
                'example_role': {'role': 'illustrative', 'printed_surface': '例示'}}
    full_text = {'source_resource_id': 'TOY-FULL-TEXT', 'source_sha256': snapshot_sha,
                 'text': '完整构造来源。',
                 'text_sha256': pb.sha('完整构造来源。'.encode()), 'status': None}
    write_constructed(full_path, pb.canonical(full_text))
    visual_text = '构造图示例：甲🙂乙。'
    visual = {'source_resource_id': 'SOURCEVISUAL-TOY-1',
              'kind': 'bounded_visual_source_text', 'source_sha256': snapshot_sha,
              'source_document_resource_id': source_id, 'physical_page': 1,
              'printed_page': None, 'slide_region_id': 'SLIDE-TOY-1',
              'role': 'right_side_example', 'text': visual_text,
              'text_sha256': pb.sha(visual_text.encode()),
              'representation': 'original_continuous_prose',
              'section_heading_verbatim': None,
              'source_locator': {'coordinate_system': 'PDF_points',
                                  'bbox_points_xyxy': [0, 0, 2, 3], 'bbox_status': 'unknown',
                                  'original_page_asset_absolute_path': str(image_path),
                                  'original_page_asset_sha256': image_sha,
                                  'new_300dpi_asset_absolute_path': str(image_path),
                                  'new_300dpi_asset_sha256': image_sha},
              'source_review_provenance': {'method': 'constructed', 'unknown_status': None},
              'uncertain_characters': []}
    contexts = [
        {'context_id': 'CTX-TOY-A', 'kind': 'paragraph', 'source_document': 'TOY-DOC',
         'text': '构造当前句。', 'title': '原标题', 'caption': '原图注',
         'headers': ['首列', '第二列'], 'row_cells': ['甲', '乙'],
         'structure': {'related_context_ids': ['CTX-TOY-B'],
                       'child_groups': [{'ordered_context_ids': ['CTX-TOY-B']}],
                       'original_status': 'unknown', 'examples': [{'role': 'illustrative'}]},
         'source_ref': copy.deepcopy(ref)},
        {'context_id': 'CTX-TOY-B', 'kind': 'source_graph_or_table_geometry',
         'source_document': 'TOY-DOC',
         'structure': {'parent_context_id': 'CTX-TOY-A', 'follows_context_id': None,
                       'nodes': [{'node_id': 'n1', 'printed_text': '原节点'}],
                       'edges': [{'from': 'n1', 'to': 'n2', 'printed_operator': '未知'}],
                       'merged_cells': [{'context_id': 'CTX-TOY-A', 'row_start': 0,
                                         'row_end_exclusive': 2, 'column_start': 0,
                                         'column_end_exclusive': 1}],
                       'table_cells': [{'row': 0, 'column': 0, 'bbox': [0, 0, 1, 1]}],
                       'image_sha256': image_sha}, 'source_ref': copy.deepcopy(ref)}]
    row = {'id': 'RECODE25-00001', 'text': '构造当前句。', 'pages': [1],
           'source_ref': copy.deepcopy(ref), 'contexts': contexts,
           'source_attachments': [{'attachment_id': 'TOY-IMAGE', 'sha256': image_sha,
                                   'physical_page': 1, 'relative_path': 'page.png'}],
           'source_references': [{'source_resource_id': 'TOY-RESOURCE-P1',
                                  'context_id': 'CTX-TOY-A', 'literal_reference': '原文引用'}],
           'source_relations': [{'printed_operator': '未知', 'from': 'n1', 'to': 'n2'}],
           'body_source_representation': {'representation': 'original_continuous_prose',
                                          'status': None}}
    bundle = {
        'source_record': row,
        'source_documents': [{'source_resource_id': source_id, 'source_sha256': snapshot_sha,
                              'snapshot': str(snapshot_path),
                              'source_text_resource': {'relative_path': full_path.name,
                                                       'sha256': pb.file_sha(full_path)},
                              'printed_year_status': 'unknown'}],
        'explicit_or_primary_source_resources': [{'source_resource_id': source_id,
                                                 'snapshot': str(snapshot_path),
                                                 'snapshot_sha256': snapshot_sha,
                                                 'source_texts': [resource],
                                                 'source_visual_text_resources': [visual],
                                                 'source_display_regions': [
                                                     {'region_id': 'SLIDE-TOY-1',
                                                      'source_sha256': snapshot_sha,
                                                      'physical_page': 1,
                                                      'children_resource_ids': ['SOURCEVISUAL-TOY-1'],
                                                      'unknown_status': None}]}],
        'preserved_historical_neutral_source_supplements': [
            {'source_resource_id': 'TOY-HISTORICAL-NEUTRAL', 'source_sha256': snapshot_sha,
             'text': '原有中性补充。',
             'unknown_status': None, 'role': 'illustrative'}],
        'source_full_text_resources': [full_text],
        'source_asset_locations': [{'absolute_path': str(image_path), 'sha256': image_sha,
                                   'physical_page': 1, 'source_pdf_sha256': snapshot_sha}],
        'source_locator_bases': {'canonical_row_attachment_relative_path_base': str(ASSETS),
                                 'page_region_base': str(ASSETS)},
        'common_source_bundle_version': {'version': 'v12',
                                         'actual_consumer_read_and_use_status': 'not_recorded',
                                         'owner_extra_unknown_status': None},
        'source_reference_index': [{'source_resource_id': 'TOY-RESOURCE-P1',
                                    'context_id': 'CTX-TOY-A'}],
        'source_provenance_addenda': [{'status': 'unknown', 'example_role': 'illustrative',
                                      'raw': {'a/b~c': '甲🙂乙e\u0301丙'},
                                      'original_path': str(snapshot_path)}]}
    ensure(tuple(bundle) == pb.BUNDLE_KEYS, 'fixture does not contain the ten ordered v12 root keys')
    return bundle


def altered(bundle, change):
    value = copy.deepcopy(bundle)
    change(value)
    return value


def budget():
    return {'budget_kind': 'frozen_operational_budget', 'basis': 'constructed deterministic test budget',
            'limits': {**{k: 10000000 for k in pb.BUDGET_KEYS}, 'reserve_output_bytes': 100,
                       'max_units': 41},
            'actual_backend_limits': {'context_tokens': None, 'input_tokens': None,
                                      'output_tokens': None, 'asset_limits': None}}


def receipt(number=1, state='complete_format_valid', **extra):
    h = lambda text: pb.sha(text.encode())
    result = {'attempt': number, 'state': state, 'initial_prompt_sha256': PROMPT_SHA,
              'creation_request_artifact_sha256': h('creation-' + str(number)),
              'thread_id': 'toy-thread-' + str(number), 'fresh_thread': True,
              'additional_user_messages': [], 'candidate_sha256': h('opaque candidate receipt only'),
              'candidate_seal_sha256': h('candidate seal'),
              'format_check_artifact_sha256': h('mechanical format receipt'),
              'read_log_sha256': h('read log'), 'history_log_sha256': h('history log'),
              'known_input_truncation': False, 'known_output_truncation': False,
              'known_compaction': False, 'visible_read_complete': True}
    if state == 'creation_failed':
        result['thread_id'] = None
    result.update(extra)
    return result


def gate_records():
    records = []
    for condition in pb.CONDITIONS:
        for batch_id in ['toy-batch-1', 'toy-batch-2']:
            records.append({'condition': condition, 'batch_id': batch_id,
                            'batching_manifest_sha256': COMMON_SHA,
                            'seal_sha256': pb.sha((condition + batch_id + 'seal').encode()),
                            'state': 'first_complete_valid_sealed',
                            'selected_candidate_sha256': pb.sha(b'opaque sealed candidate receipt'),
                            'attempt_thread_ids': [condition + '-' + batch_id]})
    return records


def run():
    global PROMPT_SHA, COMMON_SHA
    PROMPT_SHA = pb.sha(b'unchanged constructed initial prompt')
    COMMON_SHA = pb.sha(b'constructed common batch binding')
    bundle = fixture_bundle()
    row_schema = pb.parse((ROOT / 'source-row-v11.schema.json').read_bytes())
    profile = pb.shape_profile([bundle])
    roots = [str(ASSETS)]
    make = lambda value: pb.make_packet(value, row_schema, profile, roots)
    packet = make(bundle)
    case('complete_v12_ten_roots_and_lossless_copy', lambda: ensure(
        packet['source_bundle'] == bundle and packet['source_bundle'] is not bundle and
        packet['source_bundle_sha256'] == pb.sha(pb.canonical(bundle))))
    case('all_original_fields_geometry_unknown_and_example_roles_preserved', lambda: ensure(
        pb.canonical(packet['source_bundle']) == pb.canonical(bundle)))
    case('constructed_png_dimensions_verified', lambda: ensure(
        len(packet['verified_asset_files']) == 1 and
        (packet['verified_asset_files'][0]['width'], packet['verified_asset_files'][0]['height']) == (2, 3)))
    case('private_new_deep_field_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_provenance_addenda'][0]['raw'].update({'private_new_field': 'private'})))))
    for key in pb.BUNDLE_KEYS:
        case('missing_root_' + key, lambda key=key: reject(lambda: make(altered(bundle, lambda b: b.pop(key)))))
    for key in row_schema['required']:
        case('missing_row_key_' + key, lambda key=key: reject(lambda: make(altered(bundle, lambda b:
            b['source_record'].pop(key)))))
    case('unsupported_root_field', lambda: reject(lambda: make(altered(bundle, lambda b: b.update({'private_root': {}})))))
    case('v11_declared_bundle_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['common_source_bundle_version'].update({'version': 'v11'})))))
    case('fabricated_consumer_read_status_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['common_source_bundle_version'].update({'actual_consumer_read_and_use_status': 'fully_read'})))))
    case('duplicate_CTX_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_record']['contexts'][1].update({'context_id': 'CTX-TOY-A'})))))
    case('deep_ordered_CTX_edge_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_record']['contexts'][0]['structure']['child_groups'][0].update({'ordered_context_ids': ['CTX-MISSING']})))))
    case('parent_CTX_edge_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_record']['contexts'][1]['structure'].update({'parent_context_id': 'CTX-MISSING'})))))
    case('explicit_resource_missing_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['explicit_or_primary_source_resources'][0].update({'source_texts': []})))))
    case('document_closure_missing_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b.update({'source_documents': []})))))
    case('full_text_resource_missing_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b.update({'source_full_text_resources': []})))))
    case('source_asset_location_missing_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b.update({'source_asset_locations': []})))))
    case('asset_relative_absolute_path_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_asset_locations'][0].update({'absolute_path': 'page.png'})))))
    case('asset_outside_frozen_root_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_asset_locations'][0].update({'absolute_path': str(OUTSIDE / 'page.png')})))))
    case('asset_SHA_mismatch_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_asset_locations'][0].update({'sha256': '0' * 64})))))
    case('document_snapshot_SHA_mismatch_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_documents'][0].update({'source_sha256': '0' * 64})))))
    case('resource_text_SHA_mismatch_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['explicit_or_primary_source_resources'][0]['source_texts'][0].update({'text_sha256': '0' * 64})))))
    case('continuous_resource_text_shape_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['explicit_or_primary_source_resources'][0]['source_texts'][0].update({'text': ['甲', '乙']})))))
    case('region_unbound_asset_locator_blocked', lambda: reject(lambda: make(altered(bundle, lambda b:
        b['source_record']['source_ref']['locator']['regions'][0].update({'page_asset': 'not-present.png'})))))
    forbidden = row_schema['x-source-protocol']['recursive_forbidden_exact_keys'] + sorted(pb.EXTRA_FORBIDDEN) + ['machine_result']
    for key in forbidden:
        # Establish the shape before checking, proving the recursive forbidden
        # guard acts even when a dangerous field exists in a profile.
        dangerous = {'outer': [{'middle': {'deep': {key: {'technical': 'constructed'}}}}]}
        case('recursive_forbidden_' + key, lambda dangerous=dangerous: reject(lambda:
            pb.check_profile(dangerous, pb.shape_profile([dangerous]), forbidden)))
    case('forbidden_casefold_blocked', lambda: reject(lambda: pb.check_profile(
        {'outer': {'Semantic_Certificate': {}}},
        pb.shape_profile([{'outer': {'Semantic_Certificate': {}}}]), forbidden)))
    for name, raw in [('duplicate_top_JSON_key', '{"x":1,"x":2}'),
                      ('duplicate_deep_JSON_key', '{"x":[{"a":1,"a":2}]}'),
                      ('nonfinite_NaN', '{"x":NaN}'), ('nonfinite_Infinity', '{"x":Infinity}'),
                      ('nonfinite_negative_Infinity', '{"x":-Infinity}')]:
        case(name, lambda raw=raw: reject(lambda: pb.parse(raw)))
    case('canonical_nonfinite_blocked', lambda: reject(lambda: pb.canonical({'x': float('nan')})))
    anchor = {'source_id': packet['source_id'], 'source_bundle_sha256': packet['source_bundle_sha256'],
              'bundle_pointer': '/source_provenance_addenda/0/raw/a~1b~0c',
              'quote': '🙂乙', 'span': {'start': 1, 'end': 3}}
    case('continuous_Unicode_escaped_pointer_quote', lambda: ensure(pb.verify_source_quote(packet, anchor)))
    case('continuous_resource_original_leaf_quote', lambda: ensure(pb.verify_source_quote(packet,
        {**anchor, 'bundle_pointer': '/explicit_or_primary_source_resources/0/source_texts/0/text'})))
    for name, change in [
        ('quote_wrong_source_id', lambda a: a.update({'source_id': 'RECODE25-99999'})),
        ('quote_wrong_bundle_SHA', lambda a: a.update({'source_bundle_sha256': '0' * 64})),
        ('quote_wrong_span', lambda a: a.update({'span': {'start': 0, 'end': 2}})),
        ('quote_noncontinuous_stitch', lambda a: a.update({'quote': '甲乙', 'span': {'start': 0, 'end': 3}})),
        ('quote_negative_span', lambda a: a.update({'span': {'start': -1, 'end': 1}})),
        ('quote_empty_span', lambda a: a.update({'span': {'start': 1, 'end': 1}})),
        ('quote_boolean_span', lambda a: a.update({'span': {'start': True, 'end': 3}})),
        ('quote_unknown_pointer', lambda a: a.update({'bundle_pointer': '/source_provenance_addenda/0/no-such'})),
        ('quote_nontext_leaf', lambda a: a.update({'bundle_pointer': '/source_record/pages'})),
        ('quote_extra_field', lambda a: a.update({'private': 'not allowed'})),
        ('quote_missing_field', lambda a: a.pop('span'))]:
        case(name, lambda change=change: reject(lambda: pb.verify_source_quote(packet, altered(anchor, change))))
    case('quote_Unicode_normalization_not_coerced', lambda: reject(lambda: pb.verify_source_quote(packet,
        {**anchor, 'quote': 'é', 'span': {'start': 3, 'end': 5}})))
    case('quote_JSON_pointer_leading_zero_index_blocked', lambda: reject(lambda: pb.verify_source_quote(packet,
        {**anchor, 'bundle_pointer': '/source_provenance_addenda/00/raw/a~1b~0c'})))
    tampered = copy.deepcopy(packet)
    tampered['source_bundle']['source_provenance_addenda'][0]['raw']['a/b~c'] = '甲🙂乙更改'
    case('quote_tampered_bundle_binding_blocked', lambda: reject(lambda: pb.verify_source_quote(tampered, anchor)))

    good_budget = budget()
    case('configured_operational_budget', lambda: pb.check_budget(good_budget))
    for key in pb.BUDGET_KEYS:
        case('unconfigured_budget_' + key, lambda key=key: reject(lambda: pb.check_budget(
            altered(good_budget, lambda b: b['limits'].update({key: None})))))
    case('unknown_backend_capacity_remains_null', lambda: reject(lambda: pb.check_budget(altered(good_budget,
        lambda b: b['actual_backend_limits'].update({'context_tokens': 1000000})))))
    case('single_unit_budget_overflow_blocked', lambda: reject(lambda: pb.group_batches([packet],
        altered(good_budget, lambda b: b['limits'].update({'max_context_nodes': 1})), MANUAL, TOY_OUTPUT_SCHEMA)))
    packets = []
    for number in range(1, 6):
        b = copy.deepcopy(bundle)
        b['source_record']['id'] = f'RECODE25-{number:05d}'
        packets.append(make(b))
    by_context = altered(good_budget, lambda b: b['limits'].update({'max_context_nodes': 4}))
    groups = pb.group_batches(packets, by_context, MANUAL, TOY_OUTPUT_SCHEMA)
    case('longest_continuous_prefix_grouping', lambda: ensure(
        [[p['source_id'] for p in g] for g in groups] ==
        [[p['source_id'] for p in packets[:2]], [p['source_id'] for p in packets[2:4]], [packets[4]['source_id']]]))
    case('grouping_is_globally_order_preserving', lambda: ensure([p for g in groups for p in g] == packets))
    case('duplicate_global_order_blocked', lambda: reject(lambda: pb.group_batches(
        [packet, packet], good_budget, MANUAL, TOY_OUTPUT_SCHEMA)))
    limit_bytes = max(pb.batch_metrics(packets[i:i+2], MANUAL, TOY_OUTPUT_SCHEMA)['worst_prompt_bytes']
                      for i in [0, 2]) + good_budget['limits']['reserve_output_bytes']
    by_bytes = altered(good_budget, lambda b: b['limits'].update({'max_prompt_and_output_bytes': limit_bytes}))
    case('longest_prefix_respects_worst_presentation_byte_budget', lambda: ensure(
        [len(g) for g in pb.group_batches(packets, by_bytes, MANUAL, TOY_OUTPUT_SCHEMA)] == [2, 2, 1]))

    memory = {}
    def capture(path, raw):
        key = str(path)
        ensure(key not in memory, 'in-memory exclusive output duplicate')
        memory[key] = raw
        return {'path': str(Path(path).resolve()), 'sha256': pb.sha(raw), 'bytes': len(raw)}
    with patch.object(pb, 'save_exclusive', capture), patch.object(Path, 'mkdir', lambda *a, **k: None):
        manifest = pb.freeze_inputs(packets, {'constructed_binding_only': True}, by_context,
                                    MANUAL, TOY_OUTPUT_SCHEMA, FIXTURES / 'memory-only-freeze')
    case('five_conditions_share_identical_batches', lambda: ensure(
        manifest['conditions'] == list(pb.CONDITIONS) and len(manifest['batches']) == len(groups) and
        all(b['condition_prompt_key'] == {'R1': 'R', 'R2': 'R', 'R3': 'R', 'W': 'W', 'H': 'H'}
            for b in manifest['batches'])))
    case('R_repetitions_use_same_prompt_bytes', lambda: ensure(all(
        len({b['prompts'][b['condition_prompt_key'][c]]['sha256'] for c in ['R1', 'R2', 'R3']}) == 1
        for b in manifest['batches'])))
    for index, group in enumerate(groups):
        R = pb.prompt_bytes(group, MANUAL, TOY_OUTPUT_SCHEMA, 'R')
        W = pb.prompt_bytes(group, MANUAL, TOY_OUTPUT_SCHEMA, 'W')
        H = pb.prompt_bytes(group, MANUAL, TOY_OUTPUT_SCHEMA, 'H')
        delimiter = '\n完整有序来源文件索引（每个文件必须实际完整读取）：\n'.encode()
        r_prefix, r_source = R.split(delimiter, 1)
        w_prefix, w_source = W.split(delimiter, 1)
        case('W_only_JSON_indentation_batch_' + str(index), lambda r_prefix=r_prefix,w_prefix=w_prefix,
             r_source=r_source,w_source=w_source: ensure(r_prefix == w_prefix and
                 pb.parse(r_source) == pb.parse(w_source) and r_source != w_source))
        case('H_only_first_line_batch_' + str(index), lambda R=R,H=H: ensure(
            R.split(b'\n', 1)[1] == H.split(b'\n', 1)[1] and
            R.split(b'\n', 1)[0] == '判读要求'.encode() and H.split(b'\n', 1)[0] == '判读说明'.encode()))
    case('builder_telemetry_unavailable_and_no_model_calls', lambda: ensure(
        manifest['provider_api_call_count'] is None and manifest['model_calls_made_by_builder'] == 0))
    ledger = nr.blank_ledger()
    case('native_unknown_provider_all_null', lambda: nr.check_telemetry(ledger))
    case('empty_native_telemetry_blocked', lambda: reject(lambda: nr.check_telemetry(
        altered(ledger, lambda v: v.update({'telemetry': {}})))))
    case('invented_actual_provider_blocked', lambda: reject(lambda: nr.check_telemetry(altered(ledger,
        lambda v: v['telemetry'].update({'actual_provider_model_identity': 'invented-provider'})))))
    case('assignment_not_actual_provider_identity', lambda: ensure(
        ledger['assignment']['requested']['model'] == 'gpt-6.1-sol' and
        ledger['assignment']['actual_tool_request'] is None and
        ledger['telemetry']['actual_provider_model_identity'] is None))

    select = lambda receipts: nr.select_technical_receipts(receipts, PROMPT_SHA)
    case('no_attempt_means_not_executed', lambda: ensure(select([])['state'] == 'not_executed'))
    case('first_format_valid_whole_batch_receipt_selected', lambda: ensure(
        select([receipt()])['selected_attempt'] == 1))
    case('creation_failed_then_first_valid_receipt', lambda: ensure(select(
        [receipt(1, 'creation_failed'), receipt(2)])['selected_attempt'] == 2))
    case('creation_failed_cannot_invent_thread', lambda: reject(lambda: select(
        [receipt(1, 'creation_failed', thread_id='invented')])) )
    case('format_failed_then_first_valid_receipt', lambda: ensure(select(
        [receipt(1, 'format_failed'), receipt(2)])['selected_attempt'] == 2))
    case('no_feedback_or_correction_message', lambda: reject(lambda: select(
        [receipt(1, 'format_failed'), receipt(2, additional_user_messages=['please repair'])])))
    case('no_changed_retry_prompt', lambda: reject(lambda: select(
        [receipt(1, 'format_failed'), receipt(2, initial_prompt_sha256='0' * 64)])))
    case('no_reused_retry_thread', lambda: reject(lambda: select(
        [receipt(1, 'format_failed'), receipt(2, thread_id='toy-thread-1')])))
    case('no_unconfirmed_fresh_thread', lambda: reject(lambda: select([receipt(fresh_thread=False)])))
    case('no_partial_attempt_candidate_stitch_state', lambda: reject(lambda: select(
        [receipt(1, 'partial_spliced_candidate')])) )
    case('no_declared_cross_attempt_candidate_stitch', lambda: reject(lambda: select(
        [receipt(candidate_is_assembled_from_multiple_attempts=True,
                 candidate_piece_attempts=[1, 2])])) )
    case('success_keeps_all_later_attempt_deviations', lambda: ensure(select(
        [receipt(), receipt(2), receipt(3, 'creation_failed')]) == {
            'selected_attempt': 1, 'events': [{'attempt': 1, 'state': 'complete_format_valid', 'selected': True},
                {'attempt': 2, 'state': 'protocol_deviation_after_first_valid', 'selected': False},
                {'attempt': 3, 'state': 'protocol_deviation_after_first_valid', 'selected': False}],
            'state': 'first_complete_valid'}))
    case('more_than_three_attempts_blocked', lambda: reject(lambda: select([receipt(n) for n in range(1, 5)])))
    for key in ['candidate_sha256','candidate_seal_sha256','format_check_artifact_sha256',
                'read_log_sha256','history_log_sha256']:
        case('valid_receipt_missing_' + key, lambda key=key: reject(lambda: select([receipt(**{key: None})])))
    for key in ['known_input_truncation','known_output_truncation','known_compaction']:
        case('valid_receipt_rejects_' + key, lambda key=key: reject(lambda: select([receipt(**{key: True})])))
    case('valid_receipt_needs_visible_complete_read', lambda: reject(lambda: select([receipt(visible_read_complete=False)])))
    gate = lambda records, ids=['toy-batch-1','toy-batch-2']: nr.all_batches_sealed_gate(records, ids, COMMON_SHA)
    case('all_five_conditions_all_batches_sealed', lambda: ensure(gate(gate_records())))
    case('sealed_technical_failure_is_complete_gate_member', lambda: ensure(gate(altered(gate_records(),
        lambda r: r[0].update({'state': 'technical_failure_sealed', 'selected_candidate_sha256': None})))) )
    case('missing_condition_batch_blocks_gate', lambda: reject(lambda: gate(gate_records()[:-1])))
    case('duplicate_condition_batch_blocks_gate', lambda: reject(lambda: gate(gate_records()[:-1] + [gate_records()[0]])))
    case('unsealed_condition_blocks_gate', lambda: reject(lambda: gate(altered(gate_records(),
        lambda r: r[0].update({'state': 'complete_format_valid'})))))
    case('wrong_common_batch_binding_blocks_gate', lambda: reject(lambda: gate(altered(gate_records(),
        lambda r: r[0].update({'batching_manifest_sha256': '0' * 64})))))
    case('missing_selected_candidate_blocks_gate', lambda: reject(lambda: gate(altered(gate_records(),
        lambda r: r[0].update({'selected_candidate_sha256': None})))))
    case('missing_seal_blocks_gate', lambda: reject(lambda: gate(altered(gate_records(),
        lambda r: r[0].update({'seal_sha256': None})))))
    case('cross_condition_batch_thread_reuse_blocks_gate', lambda: reject(lambda: gate(altered(gate_records(),
        lambda r: r[1].update({'attempt_thread_ids': r[0]['attempt_thread_ids']})))))
    case('duplicate_frozen_batch_id_blocks_gate', lambda: reject(lambda: gate(gate_records(), ['toy-batch-1','toy-batch-1'])))
    report = {'test_kind': 'label_free_constructed_mechanical_contract_tests',
              'completed_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'actual_coding_outputs_constructed': False, 'candidate_bodies_constructed': False,
              'model_called': False, 'real_lookup_called': False, 'real_source_consumed': False,
              'dont_write_bytecode': sys.dont_write_bytecode,
              'toy_owner_schema': 'source-row-v11.schema.json', 'toy_bundle_version': 'v12',
              'core_file_sha256': {name: pb.file_sha(ROOT / name)
                                   for name in ['packet_builder.py','native_records.py']},
              'test_count': len(RESULTS), 'passed_count': sum(v['passed'] for v in RESULTS),
              'failed_count': sum(not v['passed'] for v in RESULTS), 'tests': RESULTS,
              'freeze_writes_captured_in_memory': True,
              'disk_write_scope': ['toy_tests.py', 'toy-test-results.run03.json', 'toy-fixtures/constructed-assets',
                                   'toy-fixtures/constructed-outside-allowed-root']}
    with (ROOT / 'toy-test-results.run03.json').open('x', encoding='utf-8') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    print(json.dumps({k:report[k] for k in ['test_count','passed_count','failed_count']}, ensure_ascii=False))
    for result in RESULTS:
        if not result['passed']:
            print(json.dumps(result, ensure_ascii=False))
    return 1 if report['failed_count'] else 0


if __name__ == '__main__':
    raise SystemExit(run())
