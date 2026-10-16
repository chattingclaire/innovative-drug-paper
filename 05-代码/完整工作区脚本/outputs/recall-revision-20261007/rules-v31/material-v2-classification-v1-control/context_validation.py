"""Validate a source-reviewed following-list certificate without coding it.

The certificate establishes that a required list is available. It never makes
list text part of the coding unit and never supplies a dimension label.
"""
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from functools import lru_cache
import subprocess


def digest(value):
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def payload_digest(contexts):
    return digest(json.dumps(contexts, ensure_ascii=False, sort_keys=True))


def compact(value):
    return ''.join(c for c in unicodedata.normalize('NFKC', value)
                   if c.isalnum())


def validate_added_parents(record):
    """Reject altered v28 source certificates before object scope is resolved.

    Source-file bytes and structural membership are checked by preparation;
    these checks bind each supplied parent to this input and source version.
    Earlier context formats are unchanged.
    """
    for c in record.get('verified_parent_context', []) + record.get('verified_scope_qualifications_v28', []):
        if c.get('repair_version') not in {'v28','v31-source-list-predicate','v31-source-object-scope'}:
            continue
        checks = (
            c.get('original_unit_sha256') == digest(record['unit_text']),
            c.get('source_sha256') == (record.get('unit_source_sha256') or record.get('source_sha256')),
            c.get('candidate_sha256') == record.get('candidate_sha256'),
            c.get('unit_id') == record.get('unit_id'),
            bool(c.get('text')),
            c.get('text_sha256') == digest(c.get('text', '')),
            bool(c.get('paragraph_id')),
            bool(c.get('pages') or c.get('source_lines')),
            c.get('verification', {}).get('verified') is True,
        )
        if not all(checks):
            raise ValueError('source parent context certificate does not match input/source')
        if c.get('repair_version') in {'v31-source-list-predicate','v31-source-object-scope'}:
            if (_file_digest(c.get('source_path','')) != c.get('source_sha256')
                    or _file_digest(c.get('candidate_path','')) != c.get('candidate_sha256')
                    or Path(c.get('source_path','')).resolve() != Path(record.get('unit_source') or record.get('source','')).resolve()
                    or Path(c.get('candidate_path','')).resolve() != Path(record.get('candidate_file','')).resolve()):
                raise ValueError('v31 parent source/candidate file binding is invalid')
            parents=[p for p in _candidate_document(c['candidate_path']).get('paragraphs',[]) if p.get('id')==c['paragraph_id']]
            if (len(parents)!=1 or parents[0].get('text')!=c['text']
                    or parents[0].get('pages',[])!=c.get('pages',[])
                    or (parents[0].get('line_ids') or parents[0].get('source_lines') or [])!=c.get('source_lines',[])):
                raise ValueError('v31 parent text/pages/lines do not match bound candidate paragraph')
            units=[u for u in _candidate_document(c['candidate_path']).get('unit_candidates',[]) if u.get('id')==record['unit_id']]
            if len(units)!=1 or units[0].get('text')!=record['unit_text']:
                raise ValueError('v31 parent target unit text/id does not match bound candidate unit')
    validate_table_header(record)


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


@lru_cache(maxsize=128)
def _file_digest(path):
    p=Path(path)
    if not path or not p.is_file():raise ValueError('verified context source file missing')
    return hashlib.sha256(p.read_bytes()).hexdigest()

@lru_cache(maxsize=8)
def _table_source_text(path):
    p=Path(path)
    if p.suffix.lower()=='.doc':
        return subprocess.run(['textutil','-convert','txt','-stdout',str(p)],
                              check=True,capture_output=True,text=True).stdout
    if p.suffix.lower() in {'.txt','.md'}:return p.read_text()
    raise ValueError('table header source text extractor unavailable for this format')

def validate_table_header(record):
    """Verify supplied source header/column order; never supply dimension tags."""
    cert=record.get('verified_table_header')
    shared=record.get('llm_v29_shared_context',{})
    if cert is None:
        if shared.get('verified_table_header') is not None:
            raise ValueError('table header missing from rule material')
        return
    if not isinstance(cert,dict):raise ValueError('table header certificate must be an object')
    if shared.get('verified_table_header') != cert:
        raise ValueError('table header differs across shared materials')
    text=cert.get('text');cells=cert.get('header_cells')
    if (not isinstance(text,str) or not text.strip() or not isinstance(cells,list)
            or len(cells)!=4 or any(not isinstance(c,str) or not c.strip() for c in cells)
            or text.splitlines()[-4:] != cells):
        raise ValueError('table header text and column order are invalid')
    if len(re.split(r'\s*\|\s*',record.get('unit_text','')))!=len(cells):
        raise ValueError('table row cannot be mapped to the supplied source columns')
    source=cert.get('source_path','')
    if (not source or Path(source).resolve()!=Path(record.get('unit_source') or record.get('source','')).resolve()
            or cert.get('source_sha256')!=(record.get('unit_source_sha256') or record.get('source_sha256'))
            or _file_digest(source)!=cert.get('source_sha256')):
        raise ValueError('table header source file/hash binding is invalid')
    if compact(text) not in compact(_table_source_text(source)):
        raise ValueError('table header literal text/order absent from bound source')


@lru_cache(maxsize=128)
def _candidate_document(path):
    return json.loads(Path(path).read_text())
