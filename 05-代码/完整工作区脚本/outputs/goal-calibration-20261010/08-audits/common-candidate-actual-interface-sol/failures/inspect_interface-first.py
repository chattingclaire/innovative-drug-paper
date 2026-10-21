"""Six source-only adapter identities; never import classifier or labels."""
from __future__ import annotations
import copy
import hashlib
import json
import unicodedata
from pathlib import Path

ROOT = Path('/PROJECT_ROOT')
BASE = ROOT / 'outputs/goal-calibration-20261010'
OUT = Path(__file__).resolve().parent
IDS = ['RECODE25-00036', 'RECODE25-00038', 'RECODE25-00045']
ADAPTER = BASE / '06-coding/rule-five-dimension-joint-root/versions/joint-v2-geometry01/source_packet.py'
ADAPTER_SHA = '637332307d059e7f03af94441aaf4a012843c0541b549a2820b386b370c80611'
SOURCE = BASE / '00-baseline/source-files/980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt'
SOURCE_SHA = '980acf76a2fb9b9537e89e6c223462549e984b39e6b1d9a54443e2dadce37036'
EXPOSURE = BASE / '02-methods/prospective-exposure-refresh-root/coordinator-private/future-frame-candidate.jsonl'
VERSIONS = {'old': BASE / '06-coding/full4481-common-v15-production-preparation-sol/packets',
            'candidate': BASE / '03-manual/common-material-projection-candidate-root/packets'}
OBSERVED_DERIVED_IDS = ['CTX-DERIVED-9cf1968272b142fa07b62518',
    'CTX-DERIVED-df4b0f4feeb38e33d97cdb3f', 'CTX-DERIVED-51e44f2184b7a580905acf18',
    'CTX-DERIVED-c5d0cffb93ce8dc3111bb6aa', 'CTX-DERIVED-10e80cbea9072900ae27a339']

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()

def binding(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}

def save(name, value):
    p = OUT / name
    if p.exists():
        raise RuntimeError('Preserve prior output; refusing overwrite: ' + str(p))
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')

def normalized_with_map(text):
    normalized, positions = [], []
    for i, char in enumerate(text):
        for part in unicodedata.normalize('NFKC', char):
            if not part.isspace():
                normalized.append(part)
                positions.append(i)
    return ''.join(normalized), positions

def main():
    assert sha(ADAPTER.read_bytes()) == ADAPTER_SHA
    # The seven permitted interactive semantic_unit calls have already been
    # consumed. This durable pass verifies raw bytes, quotes and locators only;
    # it does not import or call the adapter again. Semantic observations below
    # are the previously inspected six identities, plus one locator reread.
    source_bytes = SOURCE.read_bytes()
    assert sha(source_bytes) == SOURCE_SHA
    source_text = source_bytes.decode('utf8', errors='strict')
    lines = source_text.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    normalized_source, source_map = normalized_with_map(source_text)
    exposures = {}
    for line in EXPOSURE.read_text(encoding='utf8').splitlines():
        row = json.loads(line)
        rid = row.get('record_id', row.get('id'))
        if rid in IDS:
            exposures[rid] = row
    assert set(exposures) == set(IDS), 'Exact three historical exposed IDs must exist'
    save('exposure-three-metadata.json', exposures)
    inputs = [binding(ADAPTER), binding(SOURCE), binding(EXPOSURE)]
    receipts, reports = [], []
    source_quotes = []
    for name, first, last, purpose in [
        ('same_version_component_title', 1, 2, 'Identify the actual same-version programme component'),
        ('eligibility_standard_complete_literal_region', 7, 17, 'All supplied conditions and members, including safety advantage member'),
        ('eligibility_next_section_boundary', 18, 18, 'Literal next heading after supplied eligibility standard'),
        ('termination_current_and_members', 30, 34, 'Current p0028, total predicate and all three literal termination members'),
        ('termination_next_paragraph_boundary', 35, 36, 'Literal next paragraph then next section after supplied members'),
        ('current_00045', 38, 38, 'Current p0036 actual line'),
    ]:
        start, end = offsets[first-1], offsets[last]
        quote = source_text[start:end]
        source_quotes.append({'quote_id': name, 'purpose': purpose, 'text': quote,
            'text_utf8_sha256': sha(quote.encode()), 'source_file': str(SOURCE),
            'source_sha256': SOURCE_SHA, 'physical_line_range_1based_inclusive': [first,last],
            'unicode_code_point_interval_half_open': [start,end],
            'utf8_byte_interval_half_open': [len(source_text[:start].encode()),len(source_text[:end].encode())]})
    for rid in IDS:
        pair = {}
        for version, directory in VERSIONS.items():
            p = directory / (rid + '.json')
            before = binding(p)
            raw = json.loads(p.read_bytes())
            bundle = raw['source_bundle']
            assert bundle['source_record']['id'] == rid
            assert bundle['source_record']['source_ref']['sha256'] == SOURCE_SHA
            assert sha(canonical(bundle)) == raw['source_bundle_sha256']
            assert binding(p) == before
            inputs.append(before)
            leaf_receipts = []
            last_char = last_byte = last_line = 0
            for i, leaf in enumerate(bundle['source_full_text_resources']):
                assert leaf['kind'] == 'verbatim_UTF8_snapshot_text'
                loc = leaf['locator']
                c0,c1 = loc['unicode_code_point_interval_half_open']
                b0,b1 = loc['utf8_byte_interval_half_open']
                l0,l1 = loc['physical_line_range_1based_inclusive']
                assert c0 == last_char and b0 == last_byte and l0 == last_line + 1
                assert leaf['text'] == source_text[c0:c1] == ''.join(lines[l0-1:l1])
                assert leaf['text'].encode() == source_bytes[b0:b1]
                assert sha(leaf['text'].encode()) == leaf['text_utf8_sha256']
                assert c1-c0 == leaf['text_unicode_code_points']
                assert b1-b0 == leaf['text_utf8_bytes']
                assert leaf['source_sha256'] == loc['snapshot_sha256'] == SOURCE_SHA
                assert loc['snapshot_absolute_path'] == str(SOURCE)
                archive = Path(loc['original_archive_absolute_path'])
                assert archive.read_bytes() == source_bytes
                if binding(archive) not in inputs:
                    inputs.append(binding(archive))
                leaf_receipts.append({'raw_bundle_pointer': '/source_full_text_resources/' + str(i),
                    'resource_id': leaf['source_resource_id'], 'previously_observed_derived_context_id': OBSERVED_DERIVED_IDS[i],
                    'text_sha256': leaf['text_utf8_sha256'], 'locator': loc,
                    'previously_observed_semantic_structure': {
                        'source_resource_id':leaf['source_resource_id'],
                        'source_bundle_pointer':'/source_full_text_resources/' + str(i),
                        'source_version_id':leaf['source_version_id'],
                        'source_paragraph_id':leaf['source_resource_id']},
                    'semantic_observation_basis':'Prior actual pure semantic_unit conversion; not another execution in this mechanical readback',
                    'previously_observed_semantic_locator_equal_to_raw':True,
                    'previously_observed_inventory_consumption_scope':'complete_literal_text_view',
                    'previously_observed_view_sha256':leaf['text_utf8_sha256'],
                    'same_version_original_bytes_and_literal_text_verified': True})
                last_char,last_byte,last_line = c1,b1,l1
            assert last_char == len(source_text) and last_byte == len(source_bytes) and last_line == len(lines)
            current = bundle['source_record']['text']
            target,_ = normalized_with_map(current)
            at = normalized_source.find(target)
            assert at >= 0 and normalized_source.find(target,at+1) == -1
            start,end = source_map[at],source_map[at+len(target)-1]+1
            original_current = source_text[start:end]
            assert normalized_with_map(original_current)[0] == target
            current_location = {'current_canonical_text': current,
                'canonical_literal_substring_present': current in source_text,
                'mapping_method': 'NFKC per code point then whitespace removal; one unique match; raw source remains unchanged',
                'actual_original_quote': original_current,
                'original_quote_sha256': sha(original_current.encode()),
                'source_file': str(SOURCE), 'source_sha256': SOURCE_SHA,
                'physical_line_1based': source_text[:start].count('\n')+1,
                'unicode_code_point_interval_half_open':[start,end],
                'utf8_byte_interval_half_open':[len(source_text[:start].encode()),len(source_text[:end].encode())],
                'original_current_source_ref': bundle['source_record']['source_ref']}
            receipt = {'adapter_identity': rid + ':' + version, 'record_id':rid,'version':version,
                'input':before,'raw_bundle_canonical_sha256':raw['source_bundle_sha256'],
                'adapter':binding(ADAPTER),
                'prior_interactive_calls_for_identity':2 if rid == 'RECODE25-00036' and version == 'candidate' else 1,
                'calls_in_this_persistent_execution':0,'raw_input_bytes_unchanged':True,
                'source_only':True,'judge_calls':0,'RelationView_calls':0,
                'raw_contexts':len(bundle['source_record']['contexts']),
                'previously_observed_semantic_contexts':10, 'previously_observed_derived_contexts':5,
                'fulltext_resources':len(leaf_receipts),'source_reference_index':bundle['source_reference_index'],
                'current':current_location,'leaf_readback':leaf_receipts}
            receipts.append(receipt)
            pair[version] = (raw,bundle,receipt)
        old,new = pair['old'],pair['candidate']
        assert old[1] == new[1]
        assert new[0]['common_material_candidate_provenance']['parent_packet'] == old[2]['input']
        raw_record = old[1]['source_record']
        relevant_quote_ids = ['same_version_component_title', 'eligibility_standard_complete_literal_region',
                              'eligibility_next_section_boundary', 'termination_current_and_members',
                              'termination_next_paragraph_boundary']
        if rid.endswith('00045'):
            relevant_quote_ids.append('current_00045')
        reports.append({'record_id':rid, 'historically_exposed_ID_confirmed':True,
            'old_new_source_bundle_equal':True,
            'prior_semantic_contexts_equal':True,
            'complete_semantic_unit_equality':'Deterministic source adapter applied to equal bundles implies equality; prior actual six conversions inspected contexts; no complete saved unit comparison claimed',
            'candidate_provenance':new[0]['common_material_candidate_provenance'],
            'raw_source_bundle_canonical_sha256':old[2]['raw_bundle_canonical_sha256'],
            'current':old[2]['current'],'original_source_relations':raw_record.get('source_relations',[]),
            'available_standard_quote_ids':relevant_quote_ids,
            'standard_raw_visibility':{'eligibility':'/source_full_text_resources/0/text physical lines 7–17; next heading at 18',
                'termination':'/source_full_text_resources/1/text physical lines 31–34; next paragraph at 35'},
            'standard_semantic_visibility':{'eligibility':'source_textleaf CTX-DERIVED-9cf1968272b142fa07b62518 text and semantic source_bundle resource 0',
                'termination':'source_textleaf CTX-DERIVED-df4b0f4feeb38e33d97cdb3f text and semantic source_bundle resource 1'},
            'literal_standard_terminal_boundary_available':True,
            'missing_structured_interface':[
                'source_reference_index is empty; no explicit current-to-standard reference address supplied',
                'textleaf structure supplies resource/pointer/version only; no component_id, heading_path or normative paragraph sequence',
                'no supplied ordered standard child/member group and independently bound closure receipt',
                'raw component_identity candidate only points to p0004 general applicability scope; it does not explicitly index the conditions or termination members',
                'whole literal leaf boundaries are character chunks and cannot themselves prove normative component/section/member boundaries'],
            'assessment':'Three selected packets already expose the same-version complete literal standard and its actual next text boundary in both interfaces. No source-interface enrichment occurred for these selected IDs. Availability alone does not establish relation applicability or classifier consumption.',
            'dimension_expectations':None,'classification':None,'nonhuman_reviewer':True})
    save('adapter-execution-receipts.json', receipts)
    save('source-quotes-verified.json', source_quotes)
    save('interface-findings.json', reports)
    save('input-bindings.json', inputs)
    save('readback-scope.json',{'record_ids':IDS,'unique_packet_adapter_identities':6,
        'persistent_execution_adapter_calls':0,
        'prior_interactive_source_only_calls':7,
        'prior_interactive_unique_identities':6,
        'prior_repeat_reason':'Candidate RECODE25-00036 source leaf locator and derived-origin inspection',
        'total_semantic_unit_calls_in_owner_task':7,
        'actual_policy_ids_added':0,'judge_calls':0,'RelationView_calls':0,
        'machine_predictions_read':0,'other_policy_originals_opened':0,
        'real_human_results_created':0,'statistics_candidate_modified':False,
        'inspection_identity':'GPT-6.1 Sol nonhuman source-interface audit; not formal labels or human adjudication'})
    print(json.dumps({'source_only_adapter_identities':6,'current_records':3,
        'old_new_equal':3,'literal_leaf_checks':30,'current_unique_normalized_matches':6,
        'source_bytes':len(source_bytes),'source_lines':len(lines),'judge_calls':0},ensure_ascii=False))

if __name__ == '__main__':
    main()
