"""Pure source adapter: reject unknown fields; preserve every source node and byte."""
import copy
import hashlib
import json
from pathlib import Path
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
GRAPH_LIST = {'related_context_ids', 'text_child_context_ids', 'table_text_context_ids', 'scope_context_ids'}
GRAPH_SINGLE = {'parent_context_id', 'follows_context_id'}
FORBIDDEN = {'labels', 'label', 'prediction', 'predictions', 'expected', 'gold', 'reference_label',
             'rule_hit', 'score', 'confidence', 'dimension_reasons', 'innovation_subtypes',
             'fairness_subtypes', 'stratum', 'weight', 'pi', 'coder_answer', 'development_rationale'}

class ContractError(ValueError):
    pass

def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def schema_check(value, filename):
    schema = json.loads((ROOT / 'schemas' / filename).read_text(encoding='utf-8'))
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(list(e.path)))
    if errors:
        raise ContractError('; '.join(f'{list(e.path)}: {e.message}' for e in errors[:5]))

def reject_result_keys(value, path='$'):
    # Strings are source text. Do not scan or censor their vocabulary/instructions.
    if isinstance(value, dict):
        for key, child in value.items():
            if key.lower() in FORBIDDEN or key.lower().startswith('machine_'):
                raise ContractError(f'forbidden result metadata at {path}.{key}')
            reject_result_keys(child, f'{path}.{key}')
    elif isinstance(value, list):
        for i, child in enumerate(value):
            reject_result_keys(child, f'{path}[{i}]')

def content_hash(packet):
    # Exact convention in the authorized common schema; absent optional keys stay absent.
    keys = ('unit_text', 'source_title', 'contexts', 'attachments')
    if any(k not in packet for k in keys):
        raise ContractError('common hash interface needs explicit source_title and attachments; no silent defaults')
    return sha(canonical({k: packet[k] for k in keys}))

def binding_hash(packet):
    # Additional whole-packet binding covers the proposed current source_ref, status and version.
    return sha(canonical(packet))

def adapt(packet, *, toy_amendment=False):
    reject_result_keys(packet)
    schema_check(packet, 'common-source.schema.json' if not toy_amendment else 'common-source-amendment-proposal.schema.json')
    if not toy_amendment:
        schema_check(packet, 'conservative-reader-profile.schema.json')
    if content_hash(packet) != packet['content_sha256']:
        raise ContractError('source content hash mismatch')
    ids = [c['context_id'] for c in packet['contexts']]
    if len(set(ids)) != len(ids) or any(not x for x in ids):
        raise ContractError('duplicate/empty context ID')
    known = set(ids)
    attachment_ids = [a['attachment_id'] for a in packet.get('attachments', [])]
    if len(attachment_ids) != len(set(attachment_ids)):
        raise ContractError('duplicate attachment ID')
    for c in packet['contexts']:
        st = c['structure']
        for key in GRAPH_LIST:
            for target in st.get(key, []):
                if target not in known:
                    raise ContractError(f'dangling context edge: {target}')
        for key in GRAPH_SINGLE:
            if st.get(key) is not None and st[key] not in known:
                raise ContractError(f'dangling context edge: {st[key]}')
        if 'image_evidence_ref' in st and st['image_evidence_ref'] not in attachment_ids:
            raise ContractError('unknown image_evidence_ref')
        for cell in st.get('merged_cells', []):
            if cell['context_id'] not in known or cell['row_start'] >= cell['row_end_exclusive'] or cell['column_start'] >= cell['column_end_exclusive']:
                raise ContractError('invalid merged-cell geometry/reference')
    # No flattening, inference, CTX deletion, reordering, renaming or missing/null coercion.
    return copy.deepcopy(packet)

def verify_ref(ref, assets):
    if ref['provenance_status'] == 'unresolved' or not ref['source_sha256']:
        raise ContractError('unresolved source provenance')
    loc = ref['source_locator']
    if not any(v not in (None, '', []) for k, v in loc.items() if k not in {'source_url', 'snapshot_attachment_id'}):
        raise ContractError('source locator lacks a physical/paragraph/article/cell position')
    aid = loc.get('snapshot_attachment_id')
    if not aid or aid not in assets or assets[aid]['sha256'] != ref['source_sha256']:
        raise ContractError('source provenance lacks verified common source bytes')

def verify_assets(packet, manifest, asset_root):
    schema_check(manifest, 'shared-assets-proposal.schema.json')
    root = Path(asset_root).resolve()
    entries = manifest['assets']
    assets = {a['attachment_id']: a for a in entries}
    if len(assets) != len(entries):
        raise ContractError('duplicate common asset ID')
    expected = {a['attachment_id']: a for a in packet.get('attachments', [])}
    if set(assets) != set(expected):
        raise ContractError('common asset IDs differ from source attachments')
    verified = []
    signatures = {'image/png': b'\x89PNG\r\n\x1a\n', 'image/jpeg': b'\xff\xd8', 'application/pdf': b'%PDF-'}
    for aid, item in assets.items():
        rel = Path(item['relative_path'])
        path = (root / rel).resolve()
        if rel.is_absolute() or not path.is_relative_to(root):
            raise ContractError('asset path escapes common asset root')
        raw = path.read_bytes()
        if sha(raw) != item['sha256'] or item['sha256'] != expected[aid]['sha256']:
            raise ContractError('asset hash mismatch')
        mime = item['mime_type']
        valid = raw.startswith(signatures[mime]) if mime in signatures else raw.startswith(b'RIFF') and raw[8:12] == b'WEBP'
        if not valid:
            raise ContractError('asset MIME signature mismatch')
        verified.append({'attachment_id': aid, 'sha256': item['sha256'], 'mime_type': mime, 'path': str(path)})
    # These checks bind declared provenance to bytes/locations, not to human certification of authenticity.
    if 'unit_source_ref' not in packet:
        raise ContractError('common interface gap: explicit current-unit source_ref required')
    for ref in [packet['unit_source_ref']] + [c['source_ref'] for c in packet['contexts']] + [a['source_ref'] for a in packet.get('attachments', [])]:
        verify_ref(ref, assets)
    return verified

def source_string(packet, context_id, field_path):
    matches = [c for c in packet['contexts'] if c['context_id'] == context_id]
    if len(matches) != 1:
        raise ContractError('unknown or ambiguous quoted CTX')
    parts = field_path.split('/')
    if parts[0] not in {'text', 'title', 'caption', 'headers', 'row_cells'}:
        raise ContractError('quote must address an original text slot')
    value = matches[0].get(parts[0])
    for part in parts[1:]:
        if not isinstance(value, list) or not part.isdigit() or int(part) >= len(value):
            raise ContractError('unknown original text leaf')
        value = value[int(part)]
    if not isinstance(value, str):
        raise ContractError('quote addresses a textless node')
    return value

def check_span(text, quote, span):
    start, end = span['start'], span['end']
    if start >= end or end > len(text) or text[start:end] != quote:
        raise ContractError('quote is not the exact continuous Unicode code-point span')

def validate_response(response, packet, manual_sha, delivered_ids):
    schema_check(response, 'output.schema.json')
    if response['blind_id'] != packet['blind_id'] or response['content_sha256'] != packet['content_sha256'] or response['manual_sha256'] != manual_sha:
        raise ContractError('response identity/version binding mismatch')
    known = {c['context_id'] for c in packet['contexts']}
    for d, label in response['labels'].items():
        if label is not None and type(label) is not int:
            raise ContractError('label must be a JSON integer 0/1, not boolean or float')
        e = response['evidence'][d]
        check_span(packet['unit_text'], e['current_quote'], e['current_span'])
        if e['current_span'] != {'start': 0, 'end': len(packet['unit_text'])}:
            raise ContractError('current quote must preserve the full current proposition')
        for q in e['contexts_used']:
            check_span(source_string(packet, q['context_id'], q['field_path']), q['quote'], q['span'])
        if not set(e['structural_context_ids_used']) <= known or not set(e['image_sources_used']) <= set(delivered_ids):
            raise ContractError('unknown structure or undelivered image citation')
        paths = set(e['paths'])
        if label == 0 and paths != {'excluded'}:
            raise ContractError('zero requires excluded path')
        if label == 1 and paths & {'excluded', 'material_missing', 'rule_conflict'}:
            raise ContractError('positive has incompatible evidence path')
        requests = [r for r in response['material_requests'] if r['dimension'] == d]
        if label is None:
            if len(paths) != 1 or not paths <= {'material_missing', 'rule_conflict'} or not requests or any(r['kind'] not in paths for r in requests):
                raise ContractError('semantic null requires a matching substantive pending reason/request')
        elif requests:
            raise ContractError('material request must match a semantic-null dimension')
        for r in requests:
            if not set(r['context_ids']) <= known:
                raise ContractError('unknown material-request CTX')
        i3 = e['innovation_support']
        fs = e['fairness_specific']
        if (d == 'I' and label == 1 and 'I3' in paths) != (i3 is not None):
            raise ContractError('I3 requires object/support/relation fields exclusively in I3')
        if (d == 'F' and label == 1 and 'F_specific' in paths) != (fs is not None):
            raise ContractError('specific F requires object/relation/current arrangement fields')
        anchors = ([i3['rd_object'], i3['available_support']] if i3 else []) + ([fs['patient_drug_object'], fs['fairness_relation'], fs['arrangement_or_evaluation']] if fs else [])
        used = {(q['context_id'], q['field_path'], q['quote'], q['span']['start'], q['span']['end']) for q in e['contexts_used']}
        for a in anchors:
            if a['source_kind'] == 'current':
                if a['context_id'] is not None or a['field_path'] != 'unit_text':
                    raise ContractError('current anchor path mismatch')
                check_span(packet['unit_text'], a['quote'], a['span'])
            else:
                check_span(source_string(packet, a['context_id'], a['field_path']), a['quote'], a['span'])
                if (a['context_id'], a['field_path'], a['quote'], a['span']['start'], a['span']['end']) not in used:
                    raise ContractError('support/fairness anchor missing from actually used CTX quotes')
    return copy.deepcopy(response)
