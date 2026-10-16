"""Explicit, hash-checked first-submission/reread binding; never edit judgments.

No globbing, latest-file selection, machine-output access or label imputation.
The caller must bind exact result/material/schema/mapping paths and SHA256s.
First submissions and subsequent rereads remain distinct source records.
"""
from copy import deepcopy
from pathlib import Path
import hashlib
import json
import jsonschema

DIMS = ('S', 'E', 'Ec', 'I', 'F')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound_json(binding):
    path = Path(binding['path'])
    if sha(path) != binding['sha256']:
        raise ValueError(f'SHA256 mismatch: {path}')
    return json.loads(path.read_text())


def mapping_index(mapping_binding):
    rows = bound_json(mapping_binding)
    index = {(r['coder'], r['blind_id']): r for r in rows}
    if len(index) != len(rows):
        raise ValueError('Duplicate coder/blind ID in mapping')
    return index


def load_submission(result_binding, packet_binding, schema_binding, coder,
                    material_version, mapping, expected_blind_ids=None):
    result = bound_json(result_binding)
    packet = bound_json(packet_binding)
    schema = bound_json(schema_binding)
    jsonschema.Draft202012Validator(schema).validate(result)
    if result['coder'] != coder or result['material_version'] != material_version:
        raise ValueError('Wrong coder or material version')
    if result['input_packet_sha256'] != packet_binding['sha256']:
        raise ValueError('Result does not bind this exact input packet')
    if packet['material_version'] != material_version:
        raise ValueError('Packet material version mismatch')
    result_ids = [r['id'] for r in result['rows']]
    packet_ids = [r['id'] for r in packet['rows']]
    if result_ids != packet_ids or len(set(result_ids)) != len(result_ids):
        raise ValueError('Result order/coverage differs from exact packet')
    if expected_blind_ids is not None and result_ids != expected_blind_ids:
        raise ValueError('Bound expected reread order differs from result')
    out = {}
    for row, source in zip(result['rows'], packet['rows']):
        entry = mapping[(coder, row['id'])]
        text_sha = hashlib.sha256(source['text'].encode()).hexdigest()
        if text_sha != entry['unit_text_sha256']:
            raise ValueError('Current unit text changed from frozen mapping')
        rid = entry['original_id']
        if rid in out:
            raise ValueError('Duplicate original ID within submission')
        out[rid] = {'row': deepcopy(row), 'provenance': {
            'coder': coder, 'blind_id': row['id'], 'material_version': material_version,
            'result_path': str(Path(result_binding['path']).resolve()),
            'result_sha256': result_binding['sha256'],
            'packet_path': str(Path(packet_binding['path']).resolve()),
            'packet_sha256': packet_binding['sha256'],
            'unit_text_sha256': text_sha,
        }}
    return out


def merge_coder(first_submissions, reread_submissions, expected_original_ids,
                expected_reread_original_ids):
    """Inputs are outputs of load_submission, in an explicitly bound sequence."""
    first = {}
    for packet in first_submissions:
        if first.keys() & packet.keys():
            raise ValueError('Duplicate first-submission original ID')
        first.update(packet)
    if set(first) != set(expected_original_ids):
        raise ValueError('First-submission coverage mismatch')
    reread = {}
    for packet in reread_submissions:
        if reread.keys() & packet.keys():
            raise ValueError('Repeated reread ID: explicit revision policy required')
        reread.update(packet)
    if set(reread) != set(expected_reread_original_ids):
        raise ValueError('Reread coverage must equal bound changed-material IDs')
    if not set(reread) <= set(first):
        raise ValueError('Reread outside original sample')
    final, audit = {}, {}
    for rid in expected_original_ids:
        chosen = reread.get(rid, first[rid])
        final[rid] = {'id': rid, **deepcopy(chosen['row'])}
        # The analysis key is the original ID; retain the original blind ID.
        final[rid]['blind_id'] = final[rid]['id']
        final[rid]['id'] = rid
        changes = [d for d in DIMS if first[rid]['row']['labels'][d]
                   != chosen['row']['labels'][d]]
        audit[rid] = {'first': deepcopy(first[rid]['provenance']),
                      'effective': deepcopy(chosen['provenance']),
                      'reread_applied': rid in reread,
                      'label_change_dimensions': changes}
    return final, audit


def require_symmetric_reread(a_audit, c_audit, expected_ids):
    actual_a = {rid for rid, row in a_audit.items() if row['reread_applied']}
    actual_c = {rid for rid, row in c_audit.items() if row['reread_applied']}
    if actual_a != actual_c or actual_a != set(expected_ids):
        raise ValueError('A/C reread changed-material coverage is not symmetric')
    return True


def assemble_candidate(a, c, third, reviewed_ids, resolution_policy):
    """Explicit policy required after root binds third-agent review design.

    agreement_keep_disagreement_third: keep an A/C binary agreement; otherwise
    use the independently authored third label. Random agreement reviews are QC.
    third_for_every_reviewed_dimension: third labels replace all reviewed rows.
    Neither policy silently treats unresolved labels as agreement or binary.
    """
    policies = {'agreement_keep_disagreement_third', 'third_for_every_reviewed_dimension'}
    if resolution_policy not in policies:
        raise ValueError('An explicit supported resolution policy is required')
    if set(a) != set(c) or set(third) != set(reviewed_ids):
        raise ValueError('A/C/third review coverage mismatch')
    binary = lambda v: type(v) is int and v in (0, 1)
    needed = {rid for rid in a if any(
        not (binary(a[rid]['labels'][d]) and binary(c[rid]['labels'][d])
             and a[rid]['labels'][d] == c[rid]['labels'][d]) for d in DIMS)}
    if not needed <= set(reviewed_ids):
        raise ValueError('Third review misses disagreement or pending cases')
    candidate = {}
    for rid in a:
        labels, source = {}, {}
        for d in DIMS:
            av, cv = a[rid]['labels'][d], c[rid]['labels'][d]
            agree = binary(av) and binary(cv) and av == cv
            use_third = (not agree or (rid in third and
                         resolution_policy == 'third_for_every_reviewed_dimension'))
            labels[d] = third[rid]['labels'][d] if use_third else av
            source[d] = 'independent_third' if use_third else 'A_C_agreement'
        candidate[rid] = {'id': rid, 'labels': labels,
                          'dimension_label_source': source,
                          'reference_status': 'AI-agent candidate; not human gold'}
    return candidate
