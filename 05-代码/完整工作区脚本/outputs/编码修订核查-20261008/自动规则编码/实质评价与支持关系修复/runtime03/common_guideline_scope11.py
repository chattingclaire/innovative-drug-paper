"""Bind a published guideline's object to its actual PDF body component.

This helper authenticates material and resolves an object only.  It emits no
dimension, copies no title/scope label, and does not decide whether the current
sentence supplies scientific guidance.  Its deliberately bounded supported
structure is one published PDF attachment, an introductory self-scope, and an
actual reference-section boundary.  Other structures remain material issues.
"""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unicodedata

from source_context_adapter_v33 import digest, norm
from source_context_adapter_v34 import authenticate_context, authenticate_target


VERSION = 'candidate11-neutral-published-guideline-object-scope'
_INNOVATION_OBJECT = re.compile(r'创新药(?:物)?|改良型新药')
_RESEARCH_OBJECT = re.compile(r'研发|开发|临床试验')
_RESOURCE_TITLE = re.compile(r'指导原则|指南|要点|原则')
_CREATED_RESOURCE = re.compile(
    r'(?:组织)?(?:起草|制定|编制)(?:了)?\s*《(?P<title>[^》]{3,180})》')
_PUBLICATION = re.compile(r'现(?:予|予以|将)?发布|予以发布|自发布之日起施行')
_SELF_SCOPE = re.compile(
    r'本(?:技术)?(?:指导原则|指南)(?:旨在|适用于|的?适用范围|主要针对|主要适用于)[^。；;]*|'
    r'(?<!不)(?<!未)(?:指导|规范|支持|促进)[^。；;]{0,240}?[,，](?:现|特)?(?:制定|编制)本(?:技术)?(?:指导原则|指南)')
_OVERVIEW = re.compile(r'^一[、.]\s*(?:概述|引言|总则|目的|适用范围)$')
_SECOND_SECTION = re.compile(r'^二[、.]')
_REFERENCE_HEADING = re.compile(r'(?:[一二三四五六七八九十]+[、.]\s*)?参考文献')


def _self_scope_matches(text):
    # A quoted policy/resource title cannot supply the declaration's object.
    masked=re.sub(r'《[^》\n]*》',lambda match:' '*len(match.group()),text)
    return _SELF_SCOPE.finditer(masked)


class GuidelineScopeUnavailable(ValueError):
    """A potentially applicable guideline cannot be safely source-bound."""

    def __init__(self, reason, **details):
        self.reason = reason
        self.details = details
        super().__init__('guideline scope unavailable: ' + reason)


def _require(condition, reason, **details):
    if not condition:
        raise GuidelineScopeUnavailable(reason, **details)


def _sha_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _normalized(text):
    return unicodedata.normalize('NFKC', text).strip()


def _pages(paragraph):
    pages = paragraph.get('pages', [])
    _require(isinstance(pages, list) and pages and
             all(type(n) is int and n > 0 for n in pages) and
             pages == sorted(set(pages)), 'paragraph page locator unavailable',
             paragraph_id=paragraph.get('id'))
    return pages


def _actual_authentication(context):
    authenticated = authenticate_context(context)
    auth = authenticated.get('authentication_v34', {})
    _require(auth.get('literal_reproduced_in_current_runtime') is True or
             auth.get('layout_reconstructed_literal_reproduced') is True,
             'literal/layout reproduction unavailable; prior-review fallback rejected',
             paragraph_id=context.get('paragraph_id'))
    return authenticated


def _base_context(record, text, pages, **locator):
    return dict(text=text, text_sha256=digest(text),
                source_path=record.get('unit_source') or record.get('source'),
                source_sha256=record.get('unit_source_sha256') or record.get('source_sha256'),
                candidate_path=record['candidate_file'],
                candidate_sha256=record['candidate_sha256'], pages=pages, **locator)


def _layout_gap_only(value):
    """Allow only an otherwise empty page edge containing its numeric folio."""
    lines = [line.strip() for line in value.splitlines() if norm(line)]
    return not lines or (len(lines) == 1 and
                         re.fullmatch(r'[-—–－]{0,4}\s*\d{1,4}\s*[-—–－]{0,4}', lines[0]) is not None)


def _paragraph_context(record, paragraph, line_map, source_pages):
    try:
        return _paragraph_context_from_pages(record, paragraph, line_map, source_pages)
    except GuidelineScopeUnavailable as error:
        if error.reason != 'bound line absent from actual physical PDF page':
            raise
        source=record.get('unit_source') or record.get('source')
        expected=record.get('unit_source_sha256') or record.get('source_sha256')
        _require(Path(source).suffix.lower()=='.pdf' and _sha_file(source)==expected and
                 _sha_file(record['candidate_file'])==record['candidate_sha256'],
                 'PDF fallback source/candidate binding differs')
        try:
            from pypdf import PdfReader
            pages=[page.extract_text() or '' for page in PdfReader(source).pages]
            context=_paragraph_context_from_pages(record,paragraph,line_map,pages)
        except Exception:
            raise error
        context['authentication_v34']['extraction_method']='pypdf_same_sha_ordered_physical_page_lines'
        context['authentication_v34']['primary_extraction_error']=dict(
            reason=error.reason,details=error.details)
        return context


def _paragraph_context_from_pages(record, paragraph, line_map, source_pages):
    """Reproduce bound candidate lines on their actual physical PDF pages.

    This also covers a paragraph crossing a bare numeric page footer.  Each
    line must independently pass the existing actual-source authenticator;
    same-page gaps are forbidden, and cross-page gaps may contain only a
    standalone numeric folio.  No supplied verification boolean is accepted.
    """
    pages = _pages(paragraph)
    ids = paragraph.get('line_ids')
    _require(isinstance(ids, list) and ids and len(ids) == len(set(ids)),
             'paragraph source-line binding unavailable', paragraph_id=paragraph.get('id'))
    selected = []
    for line_id in ids:
        _require(line_id in line_map, 'candidate source line missing', line_id=line_id)
        line = line_map[line_id]
        _require(line.get('page') in pages and isinstance(line.get('text'), str),
                 'candidate source-line page/text differs', line_id=line_id)
        selected.append(line)
    _require(norm(''.join(line['text'] for line in selected)) == norm(paragraph['text']),
             'paragraph is not reproduced by its bound candidate lines',
             paragraph_id=paragraph.get('id'))
    _require(sorted(set(line['page'] for line in selected)) == pages,
             'paragraph pages differ from bound source lines', paragraph_id=paragraph.get('id'))
    matches, authenticated_lines = [], []
    previous = None
    for line in selected:
        page = line['page']
        _require(page <= len(source_pages), 'source-line physical page exceeds actual PDF', page=page)
        # Retain raw character positions so cross-page gap checks cannot hide
        # an omitted substantive sentence by normalizing it to a label.
        raw = source_pages[page - 1]
        normalized_chars, raw_positions = [], []
        for index, character in enumerate(raw):
            for normalized_character in unicodedata.normalize('NFKC', character):
                if not normalized_character.isspace() and not unicodedata.category(normalized_character).startswith('P'):
                    normalized_chars.append(normalized_character)
                    raw_positions.append(index)
        flat = ''.join(normalized_chars)
        needle = norm(line['text'])
        if not needle:
            punctuation=''.join(c for c in unicodedata.normalize('NFKC',line['text']) if not c.isspace())
            _require(punctuation and all(unicodedata.category(c).startswith('P') for c in punctuation)
                     and previous and previous['page']==page,
                     'standalone punctuation line lacks a preceding same-page source anchor',line_id=line['id'])
            gap_end=(raw_positions[previous['normalized_end']]
                     if previous['normalized_end']<len(raw_positions) else len(raw))
            gap_start=previous['raw_end'];gap=raw[gap_start:gap_end]
            chars,positions=[],[]
            for offset,character in enumerate(gap):
                for normalized_character in unicodedata.normalize('NFKC',character):
                    if not normalized_character.isspace():
                        chars.append(normalized_character);positions.append(gap_start+offset)
            value=''.join(chars)
            _require(value.count(punctuation)==1 and not norm(gap),
                     'standalone punctuation is not unique in the actual bound source gap',line_id=line['id'])
            at=value.index(punctuation);raw_start=positions[at];raw_end=positions[at+len(punctuation)-1]+1
            match=dict(line_id=line['id'],page=page,normalized_start=previous['normalized_end'],
                normalized_end=previous['normalized_end'],raw_start=raw_start,raw_end=raw_end,
                actual_source_page_sha256=digest(raw),punctuation_only=True)
            auth=_base_context(record,line['text'],[page],source_lines=[line['id']])
            auth['authentication_v34']=dict(method='actual_punctuation_in_same_page_bound_gap',
                literal_reproduced_in_current_runtime=True,actual_raw_start=raw_start,actual_raw_end=raw_end,
                actual_source_page_sha256=digest(raw),prior_review_fallback_accepted=False)
            matches.append(match);authenticated_lines.append(auth);previous=match
            continue
        start_at = previous['normalized_end'] if previous and previous['page'] == page else 0
        found = flat.find(needle, start_at)
        _require(needle and found >= 0, 'bound line absent from actual physical PDF page',
                 line_id=line['id'], page=page)
        raw_start = raw_positions[found]
        raw_end = raw_positions[found + len(needle) - 1] + 1
        if previous:
            if previous['page'] == page:
                _require(found == previous['normalized_end'],
                         'substantive source text omitted between bound paragraph lines', line_id=line['id'])
            else:
                _require(page == previous['page'] + 1 and
                         _layout_gap_only(source_pages[previous['page'] - 1][previous['raw_end']:]) and
                         _layout_gap_only(raw[:raw_start]),
                         'cross-page paragraph gap is not solely a numeric page edge', line_id=line['id'])
        context = _base_context(record, line['text'], [page], source_lines=[line['id']])
        auth = _actual_authentication(context)
        match = dict(line_id=line['id'], page=page, normalized_start=found,
                     normalized_end=found + len(needle), raw_start=raw_start, raw_end=raw_end,
                     actual_source_page_sha256=digest(raw))
        matches.append(match)
        authenticated_lines.append(auth)
        previous = match
    context = _base_context(record, paragraph['text'], pages,
                            paragraph_id=paragraph['id'], source_lines=ids)
    context['authentication_v34'] = {
        'method': 'actual_source_ordered_physical_page_lines_reproduced',
        'literal_reproduced_in_current_runtime': False,
        'layout_reconstructed_literal_reproduced': True,
        'layout_reconstruction': {
            'method': 'exact_bound_lines_with_only_numeric_cross_page_edges',
            'matches': matches,
            'authenticated_source_lines': authenticated_lines,
            'raw_extraction_claimed_contiguous': False}}
    return context


def resolve_guideline_scope(record):
    """Return an authenticated object-only scope, None, or a material issue.

    None means that this candidate has no matching innovation-research
    guideline declaration, or that the current unit is the publication notice
    itself (whose actual supply predicate must be assessed in the current
    text).  A matching but unbound/unsupported component raises
    GuidelineScopeUnavailable; callers must preserve that as pending material.
    """
    try:
        return _resolve(record)
    except GuidelineScopeUnavailable:
        raise
    except Exception as error:
        raise GuidelineScopeUnavailable('source authentication failed',
                                        exception_type=type(error).__name__,
                                        exception_message=str(error)) from error


def authenticate_current_guideline_paragraph(record):
    """Authenticate a current publication paragraph without inheriting its body.

    The caller must independently establish the current named resource,
    creation/publication predicates, and innovation-research relation.  This
    wrapper establishes only the exact current paragraph and actual files.
    """
    try:
        source = record.get('unit_source') or record.get('source')
        source_sha = record.get('unit_source_sha256') or record.get('source_sha256')
        cp = record.get('candidate_file')
        _require(source and cp and Path(source).suffix.lower() == '.pdf',
                 'current guideline publication requires an actual PDF source/candidate')
        _require(_sha_file(source) == source_sha and _sha_file(cp) == record.get('candidate_sha256'),
                 'current publication source/candidate bytes differ from bound version')
        if record.get('source'):
            _require(_sha_file(record['source']) == record.get('source_sha256'),
                     'current publication container source bytes differ')
        doc = json.loads(Path(cp).read_text())
        _require(doc.get('source') == source and doc.get('source_sha256') == source_sha,
                 'current publication candidate document source differs')
        authenticate_target(record)
        targets = [unit for unit in doc.get('unit_candidates', []) if unit.get('id') == record.get('unit_id')]
        _require(len(targets) == 1 and targets[0].get('text') == record.get('unit_text'),
                 'current publication unit binding differs')
        target = targets[0]
        paragraphs = [paragraph for paragraph in doc.get('paragraphs', [])
                      if paragraph.get('id') == target.get('paragraph_id')]
        _require(len(paragraphs) == 1 and norm(record['unit_text']) in norm(paragraphs[0]['text']) and
                 target.get('pages', []) == paragraphs[0].get('pages', []),
                 'current publication paragraph membership differs')
        if record.get('pages'):
            _require(record['pages'] == target['pages'], 'current publication pages differ')
        lines = doc.get('lines', [])
        line_map = {line.get('id'): line for line in lines}
        _require(lines and len(line_map) == len(lines), 'current publication source-line inventory unavailable')
        raw = subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', source, '-'],
                             check=True, capture_output=True, text=True).stdout
        pages = raw.split('\f')
        if pages and not pages[-1].strip():
            pages.pop()
        authenticated = _paragraph_context(record, paragraphs[0], line_map, pages)
        authenticated.update(current_unit_id=record.get('unit_id'),
                             current_unit_sha256=digest(record['unit_text']),
                             labels_may_be_copied=False, dimension_assignment=False,
                             role='authenticated_current_publication_paragraph_only')
        return authenticated
    except GuidelineScopeUnavailable:
        raise
    except Exception as error:
        raise GuidelineScopeUnavailable('current publication source authentication failed',
                                        exception_type=type(error).__name__,
                                        exception_message=str(error)) from error


def _resolve(record):
    cp = record.get('candidate_file')
    _require(cp, 'current candidate file absent')
    doc = json.loads(Path(cp).read_text())
    paragraphs = doc.get('paragraphs', [])
    _require(isinstance(paragraphs, list), 'candidate paragraph inventory absent')
    publications = []
    scope_candidates = []
    for index, paragraph in enumerate(paragraphs):
        text = _normalized(paragraph.get('text', ''))
        if _PUBLICATION.search(text):
            for match in _CREATED_RESOURCE.finditer(text):
                title = match.group('title')
                if (_RESOURCE_TITLE.search(title) and _INNOVATION_OBJECT.search(title)
                        and _RESEARCH_OBJECT.search(title)):
                    publications.append((index, paragraph, title))
        if any(_INNOVATION_OBJECT.search(match.group()) and _RESEARCH_OBJECT.search(match.group())
               for match in _self_scope_matches(text)):
            scope_candidates.append((index, paragraph))
    if not publications and not scope_candidates:
        return None
    _require(len(publications) == 1, 'single actual published guideline title unavailable',
             publication_count=len(publications))
    notice_index, notice, title = publications[0]
    source = record.get('unit_source') or record.get('source')
    source_sha = record.get('unit_source_sha256') or record.get('source_sha256')
    _require(source and Path(source).suffix.lower() == '.pdf', 'only actual PDF attachment components supported')
    _require(_sha_file(source) == source_sha and _sha_file(cp) == record.get('candidate_sha256'),
             'current source/candidate bytes differ from bound version')
    if record.get('source'):
        _require(_sha_file(record['source']) == record.get('source_sha256'),
                 'container source bytes differ from bound version')
    _require(doc.get('source') == source and doc.get('source_sha256') == source_sha,
             'candidate document source binding differs from current unit source')
    authenticate_target(record)
    ids = [paragraph.get('id') for paragraph in paragraphs]
    _require(all(isinstance(value, str) and value for value in ids) and len(ids) == len(set(ids)),
             'candidate paragraph locators are not unique')
    targets = [unit for unit in doc.get('unit_candidates', []) if unit.get('id') == record.get('unit_id')]
    _require(len(targets) == 1 and targets[0].get('text') == record.get('unit_text'),
             'current unit is not exactly bound to candidate')
    target = targets[0]
    _require(target.get('paragraph_id') in ids, 'current paragraph absent from candidate')
    target_index = ids.index(target['paragraph_id'])
    if target_index == notice_index:
        return None
    overview_indexes = [index for index, paragraph in enumerate(paragraphs)
                        if index > notice_index and _OVERVIEW.fullmatch(_normalized(paragraph['text']))]
    _require(len(overview_indexes) == 1, 'single independent guideline-body opening unavailable')
    first = overview_indexes[0]
    _require(first == notice_index + 1, 'unresolved component lies between publication and guideline body')
    intro_end = next((index for index in range(first + 1, len(paragraphs))
                      if _SECOND_SECTION.match(_normalized(paragraphs[index]['text']))), None)
    _require(intro_end is not None, 'introductory component boundary unavailable')
    scope_candidates = [(index, paragraph) for index, paragraph in scope_candidates if first < index < intro_end]
    _require(len(scope_candidates) == 1, 'unique self-declared innovation-research scope unavailable in overview')
    _, scope = scope_candidates[0]
    result = subprocess.run(['pdftotext', '-layout', '-enc', 'UTF-8', source, '-'],
                            check=True, capture_output=True, text=True)
    source_pages = result.stdout.split('\f')
    if source_pages and not source_pages[-1].strip():
        source_pages.pop()
    first_page = min(_pages(paragraphs[first]))
    references = [(page,line.strip()) for page,text in enumerate(source_pages,1)
                  if page>first_page for line in text.splitlines()
                  if _REFERENCE_HEADING.fullmatch(_normalized(line))]
    _require(len(references) == 1, 'single actual reference-section page boundary unavailable',
             reference_boundary_pages=[page for page,_ in references])
    end_page,reference_text=references[0]
    lines = doc.get('lines', [])
    _require(isinstance(lines,list) and lines,'candidate layout-line inventory unavailable')
    line_order={line.get('id'):index for index,line in enumerate(lines)}
    reference_lines=[line for line in lines if line.get('page')==end_page and
                     norm(line.get('text',''))==norm(reference_text)]
    _require(len(reference_lines)==1,'actual reference heading candidate locator unavailable')
    reference_line=reference_lines[0];reference_position=line_order[reference_line['id']]
    body_indexes = []
    for index in range(first, len(paragraphs)):
        pages = _pages(paragraphs[index])
        ids=paragraphs[index].get('line_ids') or []
        if min(pages)>end_page or (min(pages)==end_page and ids and
                                  all(line_order.get(key,reference_position)>=reference_position for key in ids)):
            break
        _require(min(pages)>=first_page and max(pages)<=end_page and ids and
                 all(key in line_order and line_order[key]<reference_position for key in ids),
                 'candidate paragraph crosses an independent component boundary', paragraph_id=paragraphs[index]['id'])
        body_indexes.append(index)
    _require(body_indexes and target_index in body_indexes,
             'current unit is outside the authenticated guideline body component')
    interval = [paragraphs[index] for index in body_indexes]
    _require(not any(re.match(r'^(?:附件|附录|附表)(?:[0-9一二三四五六七八九十]+)?(?:[:：\s]|$)',
                              _normalized(paragraph['text'])) for paragraph in interval),
             'nested or additional attachment boundary in candidate body is unsupported')
    _require([min(_pages(paragraph)) for paragraph in interval] ==
             sorted(min(_pages(paragraph)) for paragraph in interval), 'candidate body page order differs')
    _require(isinstance(lines, list) and lines, 'candidate layout-line inventory unavailable')
    line_map = {line.get('id'): line for line in lines}
    _require(len(line_map) == len(lines), 'candidate layout-line locators are not unique')
    attachment_lines = [line for line in lines if norm(line.get('text', '')) == norm('附件:' + title)]
    _require(len(attachment_lines) == 1 and attachment_lines[0].get('page') in _pages(notice),
             'actual same-title attachment link unavailable or ambiguous')
    link = attachment_lines[0]
    publication_attachments = [line for line in lines if line.get('page') in _pages(notice) and
                              re.match(r'^附件(?:[0-9一二三四五六七八九十]+)?[:：]',
                                       _normalized(line.get('text', '')))]
    _require(publication_attachments == [link], 'multiple or unresolved attachments in publication component')
    _require(norm(link['text']) in norm(source_pages[link['page'] - 1]),
             'same-title attachment link absent from actual publication page')
    attachment_context = _actual_authentication(
        _base_context(record, link['text'], [link['page']], source_lines=[link['id']]))
    reference_context=_actual_authentication(_base_context(record,reference_line['text'],
        [end_page],source_lines=[reference_line['id']]))
    current = paragraphs[target_index]
    _require(norm(record['unit_text']) in norm(current['text']) and
             target.get('pages', []) == current.get('pages', []), 'current unit/paragraph membership differs')
    if record.get('pages'):
        _require(record['pages'] == target['pages'], 'current record pages differ from candidate unit')
    notice_context = _paragraph_context(record, notice, line_map, source_pages)
    scope_context = _paragraph_context(record, scope, line_map, source_pages)
    current_context = _paragraph_context(record, current, line_map, source_pages)
    first_context = _paragraph_context(record, interval[0], line_map, source_pages)
    last_context = _paragraph_context(record, interval[-1], line_map, source_pages)
    raw_title_matches = [match for match in _CREATED_RESOURCE.finditer(notice['text'])
                         if norm(match.group('title')) == norm(title)]
    raw_scope_matches = [match for match in _self_scope_matches(scope['text'])
                         if _INNOVATION_OBJECT.search(match.group()) and _RESEARCH_OBJECT.search(match.group())]
    _require(len(raw_title_matches) == len(raw_scope_matches) == 1,
             'literal title/scope anchor cannot be uniquely located in authenticated contexts')
    title_match, scope_match = raw_title_matches[0], raw_scope_matches[0]
    title_anchor = dict(role='actual_published_guideline_title', start=title_match.start('title'),
                        end=title_match.end('title'), text=title_match.group('title'),
                        paragraph_id=notice['id'])
    scope_anchor = dict(role='self_declared_innovation_research_object', start=scope_match.start(),
                        end=scope_match.end(), text=scope['text'][scope_match.start():scope_match.end()],
                        paragraph_id=scope['id'])
    return {
        'kind': 'COMMON11_authenticated_guideline_rnd_object_and_current_guidance',
        'version': VERSION, 'role': 'innovation_research_guideline_object_only',
        'labels_may_be_copied': False, 'dimension_assignment': False,
        'title': title, 'title_context': notice_context, 'attachment_context': attachment_context,
        'context_anchors': [title_anchor, scope_anchor],
        'scope_context': scope_context, 'current_paragraph_context': current_context,
        'source_path': source, 'source_sha256': source_sha,
        'container_source_path': record.get('source'), 'container_source_sha256': record.get('source_sha256'),
        'candidate_path': cp, 'candidate_sha256': record['candidate_sha256'],
        'current_unit_id': record.get('unit_id'), 'current_unit_sha256': digest(record['unit_text']),
        'component_binding': {
            'first_paragraph': interval[0]['id'], 'last_paragraph': interval[-1]['id'],
            'paragraph_ids': [paragraph['id'] for paragraph in interval],
            'candidate_interval_sha256': digest(json.dumps(interval, ensure_ascii=False, sort_keys=True)),
            'first_paragraph_context': first_context, 'last_paragraph_context': last_context,
            'physical_first_body_page': first_page, 'actual_reference_boundary_page': end_page,
            'actual_reference_boundary_context':reference_context,
            'actual_reference_boundary_page_sha256': digest(source_pages[end_page - 1]),
            'current_paragraph_id': current['id'], 'current_unit_is_component_member': True},
        'source_authentication': {
            'method': 'actual_files_candidate_interval_and_ordered_physical_pdf_lines',
            'prior_review_fallback_accepted': False,
            'actual_pdf_physical_page_count': len(source_pages)},
        'context_dependency': {
            'kind': 'COMMON11_authenticated_guideline_rnd_object_and_current_guidance',
            'scope_role': 'innovation_research_guideline_object_only',
            'current_guidance_established_by_this_helper': False,
            'labels_may_be_copied': False,
            'usage': 'The caller must attach independent current-unit scientific-guidance anchors; this dependency authenticates only their research object.'},
        'usage': 'Only identifies the innovation-research object. Current scientific guidance or actual supply must be established independently; general safety reporting and pharmacovigilance duties supply no innovation label.'}
