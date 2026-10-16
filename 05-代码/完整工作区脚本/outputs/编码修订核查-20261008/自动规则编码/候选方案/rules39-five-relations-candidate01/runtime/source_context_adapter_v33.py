"""Authenticate supplied source contexts and expose bounded semantic roles.

No identifier, department, filename meaning, reference label, or target score
is inspected. Source paths/IDs are used only to bind exact source structure.
Scope resolves an object; it never supplies a positive dimension by itself.
"""
import copy
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import unicodedata

VERSION = 'v33-source-context-adapter-20261007-candidate01'


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def norm(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text)
                   if not c.isspace() and not unicodedata.category(c).startswith('P'))


@lru_cache(maxsize=256)
def file_sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


@lru_cache(maxsize=256)
def candidate(path):
    return json.loads(Path(path).read_text())


@lru_cache(maxsize=256)
def source_text(path):
    p = Path(path)
    if p.suffix.lower() == '.pdf':
        from pypdf import PdfReader
        return '\n'.join(re.sub(r'(?m)^\s*—\s*\d+\s*—\s*$', '',
                               page.extract_text() or '') for page in PdfReader(p).pages)
    if p.suffix.lower() in {'.txt', '.md'}:
        return p.read_text()
    raise ValueError('source adapter: unsupported authenticated source type')


def require(value, message):
    if not value:
        raise ValueError('source adapter: ' + message)


def bind_target(record, cert):
    sp = record.get('unit_source') or record.get('source')
    sh = record.get('unit_source_sha256') or record.get('source_sha256')
    cp = record.get('candidate_file')
    ch = record.get('candidate_sha256')
    require(sp and cp and cert.get('source_path') == sp, 'source path mismatch')
    require(cert.get('source_sha256') == sh == file_sha(sp), 'source SHA mismatch')
    require(cert.get('candidate_path') == cp, 'candidate path mismatch')
    require(cert.get('candidate_sha256') == ch == file_sha(cp), 'candidate SHA mismatch')
    doc = candidate(cp)
    units = [u for u in doc.get('unit_candidates', []) if u.get('id') == record.get('unit_id')]
    require(len(units) == 1 and units[0].get('text') == record.get('unit_text'),
            'target unit is not exactly bound to source candidate')
    return doc, units[0]


def bound_parent(record, item, role, certificate_field):
    return {**item, 'paragraph_id': item.get('paragraph_id') or item.get('id'),
            'repair_version': 'v33-source-adapter', 'semantic_role': role,
            'source_context_certificate_field': certificate_field,
            'unit_id': record['unit_id'],
            'original_unit_sha256': digest(record['unit_text']),
            'text_sha256': digest(item['text']),
            'candidate_path': record['candidate_file'],
            'candidate_sha256': record['candidate_sha256'],
            'verification': {'verified': True, 'method': 'actual source/candidate/target binding'}}


def prepare(record):
    """Return an internal adapted view; input material is never mutated."""
    out = copy.deepcopy(record)
    shared = record.get('llm_v29_shared_context', {})
    certificates = shared.get('verified_context_certificates', {})
    log = []
    scopes = record.get('verified_scope_context_v8')
    if scopes is not None:
        require(scopes == shared.get('verified_scope_context_v8'), 'shared scope differs')
        cert = certificates.get('verified_scope_context_v8')
        require(isinstance(cert, dict) and isinstance(scopes, list) and scopes, 'scope certificate missing')
        doc, target = bind_target(record, cert)
        paragraphs = doc.get('paragraphs', [])
        first = [i for i,p in enumerate(paragraphs) if p.get('id') == cert.get('first_paragraph')]
        last = [i for i,p in enumerate(paragraphs) if p.get('id') == cert.get('last_paragraph')]
        require(len(first) == len(last) == 1 and first[0] <= last[0], 'scope interval invalid')
        interval = paragraphs[first[0]:last[0]+1]
        require(len(interval) == len(scopes), 'scope interval is incomplete')
        require(last[0]+1 < len(paragraphs) and
                paragraphs[last[0]+1]['text'] == cert.get('next_structure'), 'scope end boundary differs')
        actual_source = norm(source_text(cert['source_path']))
        for given, actual in zip(scopes, interval):
            require(given.get('id') == actual.get('id') and given.get('text') == actual.get('text'),
                    'scope paragraph mismatch')
            require(given.get('pages', []) == actual.get('pages', []) and
                    given.get('line_ids', []) == actual.get('line_ids', []), 'scope locator mismatch')
            require(given.get('source_sha256') == cert['source_sha256'] and
                    given.get('candidate_sha256') == cert['candidate_sha256'], 'scope member version mismatch')
            require(norm(given['text']) in actual_source, 'scope is absent from actual source')
        # Only an explicit object declaration is bridged into legacy object
        # resolution. Conditions/deadlines remain in a separate typed role.
        declarations = [p for p in scopes if re.search(r'适用范围[:：]', p['text'])
                        and re.search(r'药品|药物|创新药|新药', p['text'])]
        derived = [bound_parent(record, p, 'drug_object_scope_only', 'verified_scope_context_v8')
                   for p in declarations]
        out['verified_parent_context'] = out.get('verified_parent_context', []) + derived
        out['verified_adapted_source_scope_v33'] = {
            'contexts': scopes, 'certificate': cert,
            'usage': 'Object and actual current eligibility/reference only; never copy scope labels.'}
        log.append({'field': 'verified_scope_context_v8', 'source_authenticated': True,
                    'paragraphs': len(scopes), 'object_declarations_exposed': len(derived),
                    'semantic_roles': ['drug_object_scope_only', 'current_support_eligibility']})
    full_list = record.get('verified_parent_list_v8')
    if full_list is not None:
        require(full_list == certificates.get('verified_parent_list_v8'), 'shared parent-list certificate differs')
        doc, target = bind_target(record, full_list)
        structure = full_list.get('complete_source_structure')
        require(isinstance(structure, list) and len(structure) >= 2, 'parent list incomplete')
        parents = record.get('verified_parent_context', [])
        require(parents == shared.get('verified_parent_context') and len(parents) == 1,
                'source-list parent differs between methods')
        require(parents[0].get('text') == structure[0].get('text'), 'wrong list parent')
        require(any(p.get('text') == record['unit_text'] for p in structure[1:]), 'target not a list child')
        source = norm(source_text(full_list['source_path']))
        position = 0
        for p in structure:
            require(p.get('source_path') == full_list['source_path'] and
                    p.get('source_sha256') == full_list['source_sha256'], 'list member source mismatch')
            position = source.find(norm(p['text']), position)
            require(position >= 0, 'source list order/content mismatch')
            position += len(norm(p['text']))
        loc = parents[0].get('paragraph_id')
        bound = [p for p in doc['paragraphs'] if p.get('id') == loc]
        require(len(bound) == 1 and bound[0]['text'] == parents[0]['text'], 'parent candidate locator mismatch')
        out['verified_parent_context'] = [bound_parent(record, {**parents[0],
            'pages': bound[0].get('pages', []), 'source_lines': bound[0].get('source_lines', [])},
            'current_list_predicate', 'verified_parent_list_v8')]
        out['verified_adapted_parent_list_v33'] = full_list
        log.append({'field': 'verified_parent_list_v8', 'source_authenticated': True,
                    'members': len(structure), 'semantic_roles': ['current_list_predicate']})
    declaration = record.get('verified_document_object_v9')
    if declaration is not None:
        require(declaration == certificates.get('verified_document_object_v9'), 'shared document-object certificate differs')
        require(declaration.get('repair_version') == 'v9-source-object-declaration', 'unknown document-object certificate')
        doc, target = bind_target(record, declaration)
        require(declaration.get('current_unit_id') == record.get('unit_id') and
                declaration.get('current_unit_sha256') == digest(record['unit_text']), 'document object target binding mismatch')
        require(declaration.get('container_source_path') == record.get('source') and
                declaration.get('container_source_sha256') == record.get('source_sha256') == file_sha(record['source']),
                'container source binding mismatch')
        paragraphs = doc.get('paragraphs', [])
        positions = {p['id']: i for i,p in enumerate(paragraphs)}
        first = positions.get(declaration.get('component_first_paragraph'))
        last = positions.get(declaration.get('component_last_paragraph'))
        require(first is not None and last is not None and first <= last, 'document-object component interval invalid')
        component_ids = {p['id'] for p in paragraphs[first:last+1]}
        require(target.get('paragraph_id') in component_ids, 'target outside declared source component')
        boundary = paragraphs[last+1]['text'] if last+1<len(paragraphs) else 'EOF'
        require(boundary == declaration.get('next_component_boundary_text'), 'document-object end boundary differs')
        contexts = declaration.get('contexts')
        require(isinstance(contexts, list) and contexts and contexts == shared.get('verified_document_object_v9'),
                'document-object contexts differ between methods')
        source = norm(source_text(declaration['source_path']))
        derived = []
        for p in contexts:
            require(p.get('role') == 'verified_document_body_object_only', 'document object role invalid')
            actual = [x for x in paragraphs[first:last+1] if x['id'] == p.get('paragraph_id')]
            require(len(actual)==1 and actual[0]['text']==p.get('text') and
                    actual[0].get('pages',[])==p.get('pages',[]), 'document-object paragraph mismatch')
            require(p.get('source_path') == declaration['source_path'] and p.get('source_sha256') == declaration['source_sha256']
                    and p.get('candidate_path') == declaration['candidate_path'] and p.get('candidate_sha256') == declaration['candidate_sha256'],
                    'document-object context versions differ')
            require(norm(p['text']) in source, 'body object declaration absent from actual source')
            require(re.search(r'药品|药物|用药',p['text']), 'body declaration has no medicine object')
            derived.append(bound_parent(record,p,'drug_object_scope_only','verified_document_object_v9'))
        out['verified_parent_context'] = out.get('verified_parent_context', []) + derived
        out['verified_adapted_document_object_v33'] = declaration
        log.append({'field':'verified_document_object_v9','source_authenticated':True,
                    'object_declarations_exposed':len(derived),'semantic_roles':['drug_object_scope_only']})
    out['source_context_adaptation_log_v33'] = log
    return out
