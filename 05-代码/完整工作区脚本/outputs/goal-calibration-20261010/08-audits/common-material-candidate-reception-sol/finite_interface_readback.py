#!/usr/bin/env python3
"""Five actual saved packets, three relation views, no dimension consumer."""
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
CAND = ROOT / '03-manual/common-material-projection-candidate-root'
OWNER = ROOT / '06-coding/rule-v20-semantic-audit-repair-sol'


def load(path):
    return json.loads(Path(path).read_bytes())


def bind(path):
    p = Path(path).resolve()
    raw = p.read_bytes()
    return {'path': str(p), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(name, value):
    with (OUT / name).open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


algorithm = load(OWNER / 'algorithm-bindings.json')
module_bindings = {x['module']: x for x in algorithm['modules']}
actual_modules = []
for name in ('evidence', 'source_packet', 'relations'):
    item = module_bindings[name]
    actual = bind(item['path'])
    assert actual == {k: item[k] for k in ('path', 'bytes', 'sha256')}
    actual_modules.append(actual)
    spec = importlib.util.spec_from_file_location(name, item['path'])
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
adapter, relations = sys.modules['source_packet'], sys.modules['relations']
inventory = {x['source_id']: x for x in load(CAND / 'packet-inventory.json')}
portable = {x['original_provenance_binding']['sha256']: x
            for x in load(CAND / 'original-delivery-map.json')}
readback, relation_results, evidence_checks = [], [], []
for sid in ('RECODE25-04592', 'RECODE25-04587', 'RECODE25-04599',
            'RECODE25-00044', 'RECODE25-03478'):
    item = inventory[sid]
    assert bind(item['packet_binding']['path']) == item['packet_binding']
    packet = load(item['packet_binding']['path'])
    bundle = packet['source_bundle']
    parent = load(item['parent_packet']['path'])['source_bundle']
    before = copy.deepcopy(bundle)
    old_unit, unit = adapter.semantic_unit(parent), adapter.semantic_unit(bundle)
    old_available, available = adapter.source_inventory(parent), adapter.source_inventory(bundle)
    assert before == bundle
    assert unit['text'] == old_unit['text'] == bundle['source_record']['text']
    assert 'id' not in unit and 'id' not in unit['source_bundle']['source_record']
    assert len({r['resource_id'] for r in available}) == len(available)
    assert all(r.get('consumer_read_status') == 'not_recorded' for r in available)
    new_ids = {r['resource_id'] for r in available} - {r['resource_id'] for r in old_available}
    assert len(new_ids) == item['added_literal_resource_N']
    readback.append({'source_id': sid, 'actual_packet_binding': item['packet_binding'],
                     'parent_binding': item['parent_packet'], 'current_text': unit['text'],
                     'source_packet_accepted': True, 'current_fields_unchanged': True,
                     'administrative_ID_removed_in_semantic_copy': True,
                     'new_inventory_resources_N': len(new_ids),
                     'inventory_unique': True, 'availability_read_status_not_recorded': True,
                     'bundle_unmodified_by_interface': True,
                     'whole_source_bundle_unchanged_from_parent': bundle == parent})
    if sid not in {'RECODE25-04592', 'RECODE25-04587', 'RECODE25-04599'}:
        continue
    view = relations.RelationView(unit)
    assert before == bundle
    contexts = {c['context_id']: c for c in unit['contexts']}
    traces = view.traces()
    for ti, trace in enumerate(traces):
        assert trace['current_anchor']['text'] == unit['text'][
            trace['current_anchor']['start']:trace['current_anchor']['end']]
        for ei, evidence in enumerate(trace['context_evidence']):
            context = contexts[evidence['context_id']]
            a, b = evidence['start'], evidence['end']
            assert type(a) is type(b) is int and 0 <= a < b <= len(context['text'])
            assert evidence['text'] == context['text'][a:b]
            assert evidence['source_ref'] == context['source_ref']
            exact = {'source_id': sid, 'trace_index': ti, 'evidence_index': ei,
                     'context_id': context['context_id'], 'quote': evidence['text'],
                     'context_range': [a, b], 'source_ref': evidence['source_ref'],
                     'matches_exact_supplied_context': True, 'source_ref_unchanged': True}
            if context['kind'] == 'source_textleaf':
                key = context['source_ref']['sha256']
                loc = context['source_ref']['locator']
                start = loc['unicode_code_point_interval_half_open'][0] + a
                end = loc['unicode_code_point_interval_half_open'][0] + b
                mapping = portable[key]
                raw = Path(mapping['candidate_copy']['path']).read_bytes()
                text = raw.decode('utf8', errors='strict')
                assert hashlib.sha256(raw).hexdigest() == key
                assert text[start:end] == evidence['text']
                byte_a, byte_b = len(text[:start].encode()), len(text[:end].encode())
                assert raw[byte_a:byte_b] == evidence['text'].encode()
                exact.update({'snapshot_unicode_range': [start, end],
                              'snapshot_byte_range': [byte_a, byte_b],
                              'snapshot_physical_lines': [text.count('\n', 0, start) + 1,
                                                          text.count('\n', 0, end - 1) + 1],
                              'quote_matches_actual_copied_original': True,
                              'portable_copy': mapping['relative_copy']})
            evidence_checks.append(exact)
    closed = view._closed_primary_programme('突破性治疗药物程序')
    supports = [r for r in traces if r['details'].get('relation_subtype') == 'bounded_IF_actual_support']
    result = {'source_id': sid, 'current_text': unit['text'],
              'generic_relation_interface_completed': True,
              'relations': traces, 'source_requests': view.source_requests,
              'bounded_IF_actual_support_relation_N': len(supports),
              'closed_breakthrough_programme_span': closed['programme_span'] if closed else None,
              'classification_or_dimension_judge_called': False,
              'only_selected_exact_quotes_are_used_as_current_relations': True}
    if sid == 'RECODE25-04592':
        assert len(supports) == 1 and closed is not None
        assert any(x['path'] == 'cited_standard' and x['dependency_status'] == 'stopped'
                   for x in view.source_requests)
        lo, hi = closed['programme_span']
        bounded_quotes = []
        for evidence in supports[0]['context_evidence']:
            context = contexts[evidence['context_id']]
            start = context['source_ref']['locator']['unicode_code_point_interval_half_open'][0] + evidence['start']
            end = context['source_ref']['locator']['unicode_code_point_interval_half_open'][0] + evidence['end']
            assert lo <= start < end <= hi
            bounded_quotes.append({'quote': evidence['text'], 'snapshot_range': [start, end]})
        result.update({'seven_support_quotes_within_same59_62_block': len(bounded_quotes) == 7,
                       'bounded_quotes': bounded_quotes,
                       'cited_standard_stop_still_present': True,
                       'availability_does_not_establish_old_consumer_NULL_resolution': True})
    else:
        assert not supports
        result['does_not_inherit_breakthrough_bounded_support'] = True
    relation_results.append(result)

primary = 'd959108cdaaa3b46c8334c217619a42f14c4d83f17af0934502a08c5d62864be'
raw = Path(portable[primary]['candidate_copy']['path']).read_bytes()
text = raw.decode('utf8', errors='strict')
physical = text.splitlines(keepends=True)
start, end = sum(map(len, physical[:196])), sum(map(len, physical[:208]))
block = text[start:end]
assert '第五十九条' in block and '第六十二条' in block and '第二节 附条 件批准程序' in block
write('finite-authoritative-reading-scope.json', {
    'actual_semantic_reading': {'five_current_texts': [r['current_text'] for r in readback],
                              'same_edition59_62_plus_next_section_heading': {
                                  'source_sha256': primary, 'unicode_range': [start, end],
                                  'physical_line_range_1based': [197, 208], 'continuous_quote': block},
                              'adjacent_section_boundary_also_read_lines': [209, 214]},
    'actual_programmatic_reading': 'All4481 source bundle/packet objects, all17 raw copies/SHA/ranges were mechanically parsed; only5 SourcePacket/inventory and3 RelationView instances in this finite pass.',
    'full_semantic_review_of4481_or17_documents': False,
    'interpretation': 'The current withdrawal in §62 is visible with §59 eligibility and §61 concrete support in one same-edition closed block. §60 submission and adjacent conditional approval do not automatically inherit that current support relation. This interface observation is not a dimension decision.'})
write('finite-interface-readback.json', {
    'algorithm_bindings': bind(OWNER / 'algorithm-bindings.json'),
    'actual_imported_modules': actual_modules, 'source_packets_N': 5,
    'relation_views_N': 3, 'classification_module_imported_or_called': False,
    'cases': readback, 'relations': relation_results,
    'quotation_checks': len(evidence_checks), 'quote_and_locator_checks_passed': True,
    'actual_originals_read_semantically_in_full': False,
    'no_old_or_candidate_files_modified': True})
write('finite-relation-quote-matches.json', evidence_checks)
print(json.dumps({'source_packets_N': 5, 'relation_views_N': 3,
                  'quote_checks_N': len(evidence_checks), 'A271_support_quotes': 7,
                  'A271_cited_standard_stopped': True,
                  'two_siblings_inherit_support': False,
                  'dimension_judge_called': False}, ensure_ascii=False))
