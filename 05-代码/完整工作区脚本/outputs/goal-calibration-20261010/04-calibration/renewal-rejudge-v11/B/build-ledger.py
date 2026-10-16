"""Record the actual reading and first-output history; no classification work."""
import datetime
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[2]
sha = lambda raw: hashlib.sha256(raw).hexdigest()
canonical = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
design_path = OUT.parent / 'admin/design.json'
design = json.loads(design_path.read_text())
source_path = Path(design['source']['path'])
resource_path = Path(design['resource']['path'])
resource = json.loads(resource_path.read_text())
rows = {r['id']: r for r in map(json.loads, source_path.read_bytes().splitlines())}
id_map = json.loads((OUT / 'id-map.json').read_text())
first = json.loads((OUT / 'first-complete-output.json').read_text())
records = []
for uid in design['order_B']:
    row = rows[uid]
    contexts = []
    for c in row['contexts']:
        contexts.append({'context_id': c['context_id'], 'kind': c['kind'],
                         'canonical_context_sha256': sha(canonical(c)),
                         'has_text': 'text' in c,
                         'text_sha256': sha(c['text'].encode('utf-8')) if 'text' in c else None,
                         'full_text_read': 'text' in c,
                         'full_metadata_read': True,
                         'text_read_method': 'exact shared-resource text plus asserted exact field equality and all per-row differences' if c['kind'] == 'same_snapshot_referenced_source_paragraph' else 'original CTX text/structure displayed completely'})
    records.append({'source_id': uid, 'current_text': row['text'], 'full_current_read': True,
                    'source_ref': row['source_ref'], 'contexts': contexts,
                    'attachments': row['source_attachments'], 'source_references': row['source_references']})

assets = []
for a in design['source_page_assets']:
    p = Path(a['path'])
    raw = p.read_bytes()
    assert sha(raw) == a['sha256'] and raw.startswith(b'\x89PNG\r\n\x1a\n')
    assets.append({**a, 'actual_sha256': sha(raw), 'bytes': len(raw),
                   'actually_viewed': True, 'view_tool': 'tools.view_image + image forwarding in functions.exec',
                   'requested_detail': 'original', 'source_png_dimensions': [1819, 2573],
                   'render_dpi_declared_in_common_material': 220,
                   'display_dimensions_observed_in_tool': [1334, 1888],
                   'view_note': 'App display resized the original-detail request; source text and page grouping remained legible.',
                   'view_timestamp_utc': None})

resource_reads = []
for i, r in enumerate(resource['source_texts']):
    assert sha(r['text'].encode()) == r['text_sha256']
    resource_reads.append({'resource_index': i, 'source_resource_id': r['source_resource_id'],
                           'text_sha256': r['text_sha256'], 'canonical_resource_sha256': sha(canonical(r)),
                           'full_text_and_metadata_read': True,
                           'read_batch': '0-5' if i < 6 else '6-17' if i < 18 else '18-28' if i < 29 else '29-36',
                           'source_ref': r['source_ref']})

ledger = {
    'assembled_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'ledger_kind': 'Actual native AI development reading, input and output history',
    'identity': {'coder': 'AI', 'assigned_model': 'GPT-6.1 Sol', 'assigned_reasoning_effort': 'ultra',
                 'actual_provider_model': None, 'actual_provider_request_count': None,
                 'actual_provider_reasoning_setting': None,
                 'provider_telemetry_note': 'The native Codex session does not expose actual backend routing or provider request telemetry; assignment is not independent verification.',
                 'human_coder': False},
    'exposure': {'previous_own_developmental_judgments': True,
                 'historically_exposed_AI_development_rejudgment': True,
                 'shared_conversational_context_across_two_units': True,
                 'old_answer_files_reread_for_this_rejudgment': False,
                 'A_rules_nativeLLM_ROOT_comparisons_or_other_answers_read': False,
                 'external_browsing_or_research': False,
                 'human_independent_validation': False,
                 'unseen_final_holdout_validation': False},
    'authorization': {'design_path': str(design_path), 'design_sha256': sha(design_path.read_bytes()),
                      'write_root': str(OUT), 'order': design['order_B'],
                      'source_seal_read': False, 'original_pdf_directly_read_or_hashed': False,
                      'PDF_sha_is_declared_source_binding': True},
    'inputs': {'manual': {**design['manual'], 'actual_sha256': sha(Path(design['manual']['path']).read_bytes()),
                           'fully_read': True,
                           'reading_note': 'Full manual read in preparation; truncated initial combined output replaced by complete line ranges 1-78, 79-155, 156-230 and explicit reread of 96-111.'},
               'source': {**design['source'], 'actual_sha256': sha(source_path.read_bytes()), 'bytes': len(source_path.read_bytes()), 'all_rows_read': True},
               'resource': {**design['resource'], 'actual_sha256': sha(resource_path.read_bytes()), 'bytes': len(resource_path.read_bytes()),
                            'metadata_and_geometry_fully_read': True, 'all_37_resources_read': True},
               'output_schema': {'path': str(BASE / '06-coding/llm-protocol-sol/schemas/output.schema.json'),
                                  'sha256': sha((BASE / '06-coding/llm-protocol-sol/schemas/output.schema.json').read_bytes()),
                                  'read_for_format_only': True, 'modified': False},
               'adapter': {'path': str(BASE / '06-coding/llm-protocol-sol/adapter.py'),
                           'sha256': sha((BASE / '06-coding/llm-protocol-sol/adapter.py').read_bytes()),
                           'read_for_hash_and_response_validation_contract_only': True,
                           'old_source_adapter_executed': False, 'old_runner_executed': False},
               'records': records, 'source_resources': resource_reads, 'page_assets': assets},
    'reading_events_in_actual_sequence': [
        {'event': 'Preparation: current common manual and own output schema read; no labels written.'},
        {'event': 'Authorized design received, fully read and hash verified; planned order 00902 then 00900.'},
        {'event': 'Design/manual/source/resource/all nine PNG byte hashes verified independently; two current records and old CTX displayed completely.'},
        {'event': 'Resource indices 0-5 fully displayed without truncation.', 'shell_chunk_id': 'bf3048'},
        {'event': 'Original PNG pages 1-3 actually viewed.'},
        {'event': 'Resource indices 6-17 fully displayed without truncation.', 'shell_chunk_id': 'd03f3a'},
        {'event': 'Original PNG pages 4-6 actually viewed.'},
        {'event': 'Resource indices 18-28 fully displayed without truncation.', 'shell_chunk_id': 'e35bf0'},
        {'event': 'Original PNG pages 7-9 actually viewed.'},
        {'event': 'Resource indices 29-36 and complete source_geometry fully displayed without truncation.'},
        {'event': 'Attempted equality of 38 restored CTX across the two rows failed because context IDs and related-context bindings are legitimately row-specific. No source or output changed.'},
        {'event': 'Exploratory restored-CTX metadata output was truncated. Replaced by lossless factored reading: asserted every common field equals its completely read resource, displayed every per-row ID and related-context difference plus complete geometry CTX, attachments and source references. No fields omitted.'},
        {'event': 'Relevant common manual standard-reference/counting paragraphs reread; own adapter contract read for output format and continuous-span checks.'},
        {'event': 'Local source-ID to schema-alias mapping exclusively saved before the first completed output.', 'timestamp_utc': id_map['frozen_at_utc']},
        {'event': 'Ten independent dimension decisions authored in order 00902 then 00900; complete labels and evidence saved once.', 'timestamp_utc': first['first_complete_output_saved_at_utc']},
        {'event': 'Mechanical-only helper asked to verify schema, bindings and exact spans after the first output; no label values or semantic suggestions requested.'},
    ],
    'reading_event_timestamp_note': 'Individual tool-read timestamps were not captured; null timestamps and sequence descriptions are retained instead of inventing times. Ledger assembly is after first output.',
    'execution': {'method': 'Native Codex AI, current conversational session',
                  'separate_HTTP_coding_API_calls_made_by_this_task': 0,
                  'native_provider_request_count': None,
                  'formal_source_adapter_validation_claimed': False,
                  'output_projection_only': id_map['hash_convention'],
                  'first_complete_attempt': 1, 'complete_record_count': 2, 'complete_dimension_count': 10,
                  'semantic_reruns': 0, 'favorable_result_selection': False, 'hidden_overwrites': False,
                  'preserved_preparation_file': 'preparation.json',
                  'first_complete_output': first,
                  'helper_role': 'Mechanical integrity checks only; no additional coder or independent human evidence.'},
}
with (OUT / 'read-input-output-ledger.json').open('x', encoding='utf-8') as f:
    json.dump(ledger, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'file': 'read-input-output-ledger.json', 'sha256': sha((OUT / 'read-input-output-ledger.json').read_bytes())}))
