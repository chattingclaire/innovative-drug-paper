"""Rebuild local schema artifacts from the four authorized inputs; no model calls."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent.parent
INPUTS = {
    'manual': BASE / '03-manual/common-manual-v1.1-development.md',
    'source_schema': BASE / '01-review/packet-source-schema-sol.json',
    'goal': BASE / '完整Goal指令.md',
    'methods_matrix': BASE / 'parallel-metrics/完整方法指标矩阵.json',
}

def write(name, value):
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

def obj(properties):
    return {'type': 'object', 'additionalProperties': False,
            'required': list(properties), 'properties': properties}

STR = {'type': 'string', 'minLength': 1}
SHA = {'type': 'string', 'pattern': '^[a-f0-9]{64}$'}
STRS = {'type': 'array', 'items': STR, 'uniqueItems': True}
SPAN = obj({'start': {'type': 'integer', 'minimum': 0},
            'end': {'type': 'integer', 'minimum': 1}})
ANCHOR = obj({'source_kind': {'enum': ['current', 'context']},
              'context_id': {'type': ['string', 'null']}, 'field_path': STR,
              'quote': STR, 'span': SPAN})
CTX_QUOTE = obj({'context_id': STR, 'field_path': STR, 'quote': STR,
                 'span': SPAN, 'purpose': STR})
I3 = obj({'rd_object': ANCHOR, 'available_support': ANCHOR, 'direct_relation': STR})
F = obj({'patient_drug_object': ANCHOR, 'fairness_relation': ANCHOR,
         'arrangement_or_evaluation': ANCHOR,
         'relation_type': {'enum': ['need_gap', 'unequal_access', 'patient_affordability']}})
PATHS = {
    'S': ['S_drug_risk', 'S_general_evaluation', 'S_substantive_information'],
    'E': ['E_drug_effect', 'E_general_evaluation', 'E_substantive_information'],
    'Ec': ['Ec_treatment_payment_resource', 'Ec_general_evaluation', 'Ec_substantive_information'],
    'I': ['I1', 'I2', 'I3', 'I4', 'I_general_evaluation', 'I_substantive_information'],
    'F': ['F_general_evaluation', 'F_substantive_information', 'F_specific'],
}

def main():
    manifest = []
    for role, path in INPUTS.items():
        raw = path.read_bytes()
        manifest.append({'role': role, 'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'bytes': len(raw)})
    write('authorized-inputs.json', manifest)
    (ROOT / 'snapshots').mkdir(exist_ok=True)
    (ROOT / 'snapshots/common-manual-v1.1-development.md').write_bytes(INPUTS['manual'].read_bytes())
    common = json.loads(INPUTS['source_schema'].read_text(encoding='utf-8'))
    (ROOT / 'schemas').mkdir(exist_ok=True)
    (ROOT / 'schemas/common-source.schema.json').write_bytes(INPUTS['source_schema'].read_bytes())
    strict = copy.deepcopy(common)
    strict['$id'] = 'urn:innovation-policy:source-reader-profile:proposal:sol'
    strict['x-status'] = 'proposed_shared_amendment_not_frozen'
    # The loose original nested values are never accepted as arbitrary objects.
    primitive = {'type': ['string', 'number', 'boolean', 'null']}
    simple = {'anyOf': [primitive, {'type': 'array', 'items': primitive}]}
    strict['$defs']['structure']['properties'] = {k: copy.deepcopy(simple) for k in common['$defs']['structure']['properties']}
    for k in ['related_context_ids', 'text_child_context_ids', 'table_text_context_ids', 'scope_context_ids']:
        strict['$defs']['structure']['properties'][k] = copy.deepcopy(STRS)
    for k in ['parent_context_id', 'follows_context_id']:
        strict['$defs']['structure']['properties'][k] = {'type': ['string', 'null']}
    for k in ['headers', 'row_cells']:
        strict['$defs']['context']['properties'][k] = {'anyOf': [{'type': ['string', 'null']}, {'type': 'array', 'items': {'type': ['string', 'null']}}]}
    write('schemas/conservative-reader-profile.schema.json', strict)
    proposal = copy.deepcopy(strict)
    proposal['$id'] = 'urn:innovation-policy:source-common-amendment:proposal:sol'
    proposal['properties']['unit_source_ref'] = {'$ref': '#/$defs/source_ref'}
    proposal['required'].append('unit_source_ref')
    proposal['$defs']['context']['properties']['kind']['enum'].append('table_group_row')
    proposal['$defs']['attachment']['properties']['kind']['enum'].append('original_table')
    proposal['$defs']['structure']['properties']['merged_cells'] = {'type': 'array', 'items': obj({
        'row_start': {'type': 'integer', 'minimum': 0}, 'row_end_exclusive': {'type': 'integer', 'minimum': 1},
        'column_start': {'type': 'integer', 'minimum': 0}, 'column_end_exclusive': {'type': 'integer', 'minimum': 1}, 'context_id': STR})}
    write('schemas/common-source-amendment-proposal.schema.json', proposal)
    evidence = {}
    for d, paths in PATHS.items():
        evidence[d] = obj({'paths': {'type': 'array', 'minItems': 1, 'uniqueItems': True,
                          'items': {'enum': paths + ['excluded', 'material_missing', 'rule_conflict']}},
                          'current_quote': STR, 'current_span': SPAN,
                          'contexts_used': {'type': 'array', 'items': CTX_QUOTE},
                          'structural_context_ids_used': STRS, 'image_sources_used': STRS,
                          'reason': STR, 'innovation_support': {'anyOf': [{'type': 'null'}, I3]},
                          'fairness_specific': {'anyOf': [{'type': 'null'}, F]}})
    output = obj({'blind_id': {'type': 'string', 'pattern': '^[AB]-[0-9]{4,6}$'},
                  'content_sha256': SHA, 'manual_sha256': SHA,
                  'labels': obj({d: {'type': ['integer', 'null'], 'enum': [0, 1, None]} for d in PATHS}),
                  'evidence': obj(evidence),
                  'material_requests': {'type': 'array', 'items': obj({
                      'dimension': {'enum': list(PATHS)}, 'kind': {'enum': ['material_missing', 'rule_conflict']},
                      'detail': STR, 'context_ids': STRS})}})
    output['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
    output['$id'] = 'urn:innovation-policy:llm-output:sol:proposal'
    write('schemas/output.schema.json', output)
    asset = obj({'asset_version': STR, 'assets': {'type': 'array', 'items': obj({
        'attachment_id': STR, 'relative_path': STR, 'sha256': SHA,
        'mime_type': {'enum': ['image/png', 'image/jpeg', 'image/webp', 'application/pdf']}})}})
    write('schemas/shared-assets-proposal.schema.json', asset)
    receipt = obj({'model_evidence_source': STR, 'actual_model_identity': STR,
                   'actual_reasoning_configuration': STR, 'request_id': {'type': ['string', 'null']},
                   'context_id': STR, 'parameters_observed': {'type': 'object'},
                   'delivered_attachments': {'type': 'array', 'items': obj({'attachment_id': STR, 'sha256': SHA})}})
    write('schemas/transport-receipt.schema.json', receipt)

if __name__ == '__main__':
    main()
