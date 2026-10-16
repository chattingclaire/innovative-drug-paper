"""One bounded current list -> actual member -> expressly named article path.

The fixed manual's necessary-context rules 2 and 3 permit this relation.
No labels from another unit are accepted, and cited articles are never further
expanded. Authentication is the existing adapter's job; this layer additionally
binds the law's actual source title and the complete exact article interval.
"""
import copy
import hashlib
import re

import common_definition_stage as common
import common_definition_delta06 as delta
import common_scope09
import rules_se
from common_reference_resolution03 import _ordinal, select_direct_contexts
from source_context_adapter_v33 import candidate, file_sha, norm
from source_context_adapter_v34 import authenticated_source_text, alternative_pdf_text

VERSION = 'common-cited-list-substantive-conditions-12'
MANUAL_SHA256 = common.RULES_SHA256
_N = r'[零一二三四五六七八九十百0-9]+'
_ADDRESS = re.compile(r'第(?P<article>' + _N + r')条(?:第(?P<clause>' + _N + r')款)?')
_START = re.compile(r'^\s*第(?P<article>' + _N + r')条')
_MEMBER = re.compile(r'(?<!不)符合\s*《(?P<title>[^》\n]+)》\s*'
    r'(?P<addresses>第' + _N + r'条(?:第' + _N + r'款)?'
    r'(?:\s*[、，,及和]\s*第' + _N + r'条(?:第' + _N + r'款)?)*)'
    r'\s*(?:规定的?|所列的?)(?:实质)?(?:条件|要求|情形)?(?:的)?(?:药品|药物)')
_ADMIN = re.compile(r'申报|申请|填报|报送|上传|提交材料|材料目录|文件名|格式|详见|参见|下载|查阅')


def _sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def current_condition_lead(text):
    """A substantive disposition/evaluation's actual condition list lead."""
    if _ADMIN.search(text) or not re.search(r'[:：]\s*$', text):
        return None
    if not re.search(r'情况|情形|条件|要求', text):
        return None
    action = re.search(r'(?:将|应当|应|予以|可以|可)?(?:重点)?考虑(?:调出|纳入)'
                       r'|(?:调出|纳入)[^。；;\n]{0,15}(?:重点)?考虑的(?:情况|情形|条件)'
                       r'|(?:评价|评估|比较)[^。；;\n]{0,25}(?:以下|下列)(?:条件|要求)', text)
    if not action:
        return None
    if not (re.search(r'(?:以下|下列)(?:情况|情形|条件|要求)', text)
            or re.search(r'(?:调出|纳入)[^。；;\n]{0,15}考虑的(?:情况|情形|条件)', text)):
        return None
    return {'start': 0, 'end': len(text), 'text': text,
            'action_start': action.start(), 'action_end': action.end(), 'action_text': action.group()}


def _title_binding(contexts, title):
    """Match a standalone actual document title before its first legal article.

    A filename, supplied title metadata, or a quoted law in the body cannot
    establish document identity. PDF title lines are read from actual bytes.
    """
    if not contexts or len({(c['source_path'], c['source_sha256']) for c in contexts}) != 1:
        return None
    path, sha = contexts[0]['source_path'], contexts[0]['source_sha256']
    if file_sha(path) != sha:
        raise ValueError('COMMON12: cited source changed after adapter authentication')
    raw = alternative_pdf_text(path) or authenticated_source_text(path)
    first = re.search(r'^\s*第一条', raw, re.M)
    if not first:
        first = re.search(r'^\s*第1条', raw, re.M)
    if not first:
        return None
    titles = [m for m in re.finditer(r'[^\r\n\f]+', raw[:first.start()])
              if norm(m.group()) == norm(title)]
    if not titles:
        return None
    m = titles[0]
    return {'method': 'actual_standalone_document_title_before_first_legal_article',
            'title': title, 'actual_title_text': m.group(),
            'source_path': path, 'source_sha256': sha,
            'start_in_actual_extraction': m.start(), 'end_in_actual_extraction': m.end(),
            'actual_source_extraction_sha256': _sha(raw)}


def _complete_article(all_contexts, ordinal):
    """Certify the full exact candidate interval, including its next boundary."""
    if ordinal is None or not all_contexts or len({c['candidate_path'] for c in all_contexts}) != 1:
        return None
    paragraphs = candidate(all_contexts[0]['candidate_path']).get('paragraphs', [])
    starts = [(i, m) for i, p in enumerate(paragraphs)
              if (m := _START.match(p.get('text', ''))) and _ordinal(m['article']) == ordinal]
    if len(starts) != 1:
        return None
    start, match = starts[0]
    end = next((i for i in range(start + 1, len(paragraphs))
                if _START.match(paragraphs[i].get('text', ''))), None)
    if end is None:
        return None
    actual = paragraphs[start:end]
    lookup = {(c.get('paragraph_id'), c.get('text')): c for c in all_contexts
              if c.get('authentication_v34')}
    if any((p.get('id'), p.get('text')) not in lookup for p in actual):
        return None
    selected = [lookup[(p['id'], p['text'])] for p in actual]
    if len({(c['source_path'], c['source_sha256']) for c in selected}) != 1:
        return None
    source = alternative_pdf_text(selected[0]['source_path']) or authenticated_source_text(selected[0]['source_path'])
    if norm(paragraphs[end]['text']) not in norm(source):
        return None
    boundary = {'method': 'all_actual_candidate_article_paragraphs_and_next_boundary_verified',
        'first_paragraph_id': actual[0]['id'], 'last_paragraph_id': actual[-1]['id'],
        'next_paragraph_id': paragraphs[end]['id'], 'next_paragraph_text': paragraphs[end]['text'],
        'complete_paragraph_count': len(actual),
        'candidate_path': selected[0]['candidate_path'],
        'candidate_sha256': selected[0]['candidate_sha256']}
    return {'contexts': selected, 'complete_interval_authenticated': True,
            'article_address': '第' + match['article'] + '条', 'actual_interval': boundary}


def _content_evidence(text):
    """Use existing fixed-manual current-content implementations only.

    No unit, file, department, adjacent label, or reference material reaches
    these detectors. S/E first use existing rules_se; the unchanged common
    migration and final E/I clarifications then apply their usual boundaries.
    """
    local = {'unit_text': text}
    # The existing common stage would otherwise try to resolve a missing
    # parent object. This bounded path accepts only the content's own object.
    masked = re.sub(r'《[^》]*》', lambda m: ' ' * len(m.group()), text)
    if not re.search(r'药品|药物|用药|该药|本品|制剂|药费|药价', masked):
        return []
    result = {'evidence': [], 'judgement_status': 'determined', 'drug_object_in_unit': True}
    result = rules_se.revise(local, result)
    result = common.revise(local, result)
    result = delta.revise(local, result)
    result = common_scope09.revise(local, result)
    return result['evidence']


def _source_anchor(context, start=0, end=None):
    end = len(context['text']) if end is None else end
    return {'start': start, 'end': end, 'text': context['text'][start:end],
            'paragraph_id': context.get('paragraph_id'),
            'paragraph_sha256': _sha(context['text']),
            'source_path': context['source_path'], 'source_sha256': context['source_sha256'],
            'candidate_path': context['candidate_path'], 'candidate_sha256': context['candidate_sha256'],
            'pages': context.get('pages', []), 'source_lines': context.get('source_lines', []),
            'source_authentication': copy.deepcopy(context['authentication_v34'])}


def revise(record, result):
    if result.get('judgement_status') == 'undetermined':
        return result
    text = record['unit_text']
    lead = current_condition_lead(text)
    if not lead:
        return result
    groups = record.get('typed_contexts_v34', [])
    lists = [g for g in groups if g.get('field') == 'complete_following_list_v11'
             and g.get('role') == 'current_following_conditions_only']
    references = [g for g in groups if g.get('field') in
                  {'explicitly_cited_articles_v10', 'explicitly_cited_qualifications_v12'}]
    audit = []
    for actual_list in lists:
        for member in actual_list.get('contexts', [])[1:]:
            if not member.get('authentication_v34') or _ADMIN.search(member['text']):
                continue
            for relation in _MEMBER.finditer(member['text']):
                for reference in references:
                    title = _title_binding(reference.get('contexts', []), relation['title'])
                    if not title:
                        continue
                    for address in _ADDRESS.finditer(relation['addresses']):
                        article = _complete_article(reference['contexts'], _ordinal(address['article']))
                        if not article:
                            continue
                        canonical = article['article_address']
                        if address['clause']:
                            canonical += '第' + address['clause'] + '款'
                        selected = select_direct_contexts(article, '符合' + canonical + '规定的条件')
                        for content in selected:
                            for detected in _content_evidence(content['text']):
                                anchor = _source_anchor(content, detected['start'], detected['end'])
                                dependency = {'kind': 'common_current_list_member_exact_named_article_three_anchors',
                                    'max_relation_edges': 2, 'recursive_cited_article_expansion': False,
                                    'current_unit_sha256': _sha(text),
                                    'current_list_lead': {**_source_anchor(actual_list['contexts'][0]), **lead},
                                    'actual_list_member_reference': _source_anchor(member, *relation.span()),
                                    'actual_named_document_title_binding': title,
                                    'exact_article_address': canonical,
                                    'complete_actual_article_interval': article['actual_interval'],
                                    'complete_actual_article_contexts': [_source_anchor(c) for c in article['contexts']],
                                    'cited_substantive_content': anchor,
                                    'existing_concept_detector_rule': detected['rule']}
                                evidence = copy.deepcopy(detected)
                                evidence.update({'rule': 'COMMON12_' + detected['dimension'] + '_exact_cited_list_condition',
                                    'start': lead['start'], 'end': lead['end'], 'text': text,
                                    'protocol_basis': common.PROTOCOL, 'rule_release': VERSION,
                                    'common_rules_sha256': MANUAL_SHA256,
                                    'context_dependency': dependency,
                                    'cited_substantive_anchors': [anchor],
                                    'current_relation_anchors': [lead],
                                    'common_definition_basis': '固定手册必要语境第2/3条：当前实质清单确指认证成员，成员明确符合具体法规条文；按实际条文现有概念detector重新识别实质内容，有限两条关系，不复制标签。'})
                                evidence.pop('matching_text', None)
                                result['evidence'].append(evidence)
                                audit.append({'dimension': detected['dimension'], 'article': canonical,
                                              'source_paragraph_id': content['paragraph_id'],
                                              'existing_detector_rule': detected['rule']})
    if audit:
        result['common_cited_list_conditions12'] = {'version': VERSION, 'manual_sha256': MANUAL_SHA256,
            'source_only_detector_events': audit, 'reference_labels_loaded': False,
            'other_unit_dimension_labels_used': False}
    return result
