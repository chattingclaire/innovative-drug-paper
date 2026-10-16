"""Validate a source-reviewed following-list certificate without coding it.

The certificate establishes that a required list is available. It never makes
list text part of the coding unit and never supplies a dimension label.
"""
import hashlib
import json
import re
import unicodedata


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def payload_digest(contexts):
    return digest(json.dumps(contexts, ensure_ascii=False, sort_keys=True))


def compact(value):
    return ''.join(c for c in unicodedata.normalize('NFKC', value)
                   if c.isalnum())


def verified_following_list(record):
    cert = record.get('verified_following_list_v27')
    if not cert:
        return False
    if cert.get('original_unit_sha256') != digest(record['unit_text']):
        return False
    source = record.get('unit_source_sha256') or record.get('source_sha256')
    if not source or cert.get('source_sha256') != source:
        return False
    contexts = cert.get('contexts', [])
    if not contexts or cert.get('contexts_sha256') != payload_digest(contexts):
        return False
    if cert.get('repair_status') != 'supplemented' or cert.get('unresolved_material_gaps') != []:
        return False
    boundary = cert.get('structure_boundary', {})
    if (boundary.get('all_paragraphs_in_interval_included') is not True
            or boundary.get('first_paragraph') != contexts[0].get('paragraph_id')
            or boundary.get('last_paragraph') != contexts[-1].get('paragraph_id')):
        return False
    for c in contexts:
        if (c.get('source_sha256') != source or not c.get('text')
                or not (c.get('pages') or c.get('source_lines'))
                or c.get('verification', {}).get('verified') is not True):
            return False
    target = compact(record['unit_text'])
    positions = [i for i, c in enumerate(contexts) if target in compact(c['text'])]
    if len(positions) != 1:
        return False
    following = contexts[positions[0] + 1:]
    # A complete source-reviewed list must contain structural items, without
    # imposing a semantic first-word vocabulary on those items.
    marker = r'^(?:\([一二三四五六七八九十0-9]+\)|[一二三四五六七八九十0-9]+[、.])'
    items = [c for c in following if re.match(marker, unicodedata.normalize('NFKC', c['text']).strip())]
    return bool(items) and cert.get('source_files_hash_verified') is True
