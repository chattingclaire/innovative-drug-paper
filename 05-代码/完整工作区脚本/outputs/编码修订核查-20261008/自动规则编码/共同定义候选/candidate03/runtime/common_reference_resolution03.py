"""Resolve a direct substantive article/clause reference without recursion.

Existing adapters authenticate source/candidate bytes and complete intervals.
This layer narrows a specific 款 to an actual paragraph of the bound source
HTML. Candidate extraction paragraphs alone do not establish legal 款.
No document identity, department, labels or target metrics are consulted.
"""
import copy
import json
import re
from html.parser import HTMLParser
from pathlib import Path

from source_context_adapter_v33 import file_sha, norm

_N = r'[零一二三四五六七八九十百0-9]+'
_ADDRESS = re.compile(r'第(?P<article>' + _N + r')条(?:第(?P<clause>' + _N + r')款)?')
_ARTICLE_START = re.compile(r'^\s*第' + _N + r'条')


class _Paragraphs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.items, self.parts, self.active = [], [], False
        self.table_depth, self.table_positions, self.paragraph_in_tables = 0, [], []
        self.active_in_table = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() == 'table':
            self.table_positions.append(len(self.items))
            self.table_depth += 1
            if self.active:
                self.active_in_table = True
        if tag.lower() == 'p':
            if self.active:
                raise ValueError('Nested paragraph cannot certify clause structure')
            self.active, self.parts = True, []
            self.active_in_table = self.table_depth > 0

    def handle_data(self, data):
        if self.active:
            self.parts.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == 'p' and self.active:
            value = ''.join(self.parts).strip()
            if value:
                self.items.append(value)
                self.paragraph_in_tables.append(self.active_in_table)
            self.active = False
        if tag.lower() == 'table':
            self.table_depth = max(0, self.table_depth - 1)


def _ordinal(value):
    if value.isdigit():
        return int(value)
    digits = {c: i for i, c in enumerate('零一二三四五六七八九')}
    if value in digits:
        return digits[value]
    if '十' in value and value.count('十') == 1 and '百' not in value:
        left, right = value.split('十')
        if (not left or left in digits) and (not right or right in digits):
            return (digits[left] if left else 1) * 10 + (digits[right] if right else 0)
    return None


def _source_clause_structure(contexts, article):
    """Require complete article paragraphs to match actual bound HTML p blocks."""
    if not contexts or len({c.get('source_path') for c in contexts}) != 1:
        return None
    path = Path(contexts[0]['source_path'])
    if path.suffix.lower() != '.json':
        return None  # No claim that PDF extraction paragraphs establish legal clauses.
    source = json.loads(path.read_text())
    html_path, html_sha = source.get('source_html'), source.get('source_sha256')
    if not html_path or not html_sha or file_sha(html_path) != html_sha:
        return None
    parser = _Paragraphs()
    parser.feed(Path(html_path).read_text())
    starts = [i for i, value in enumerate(parser.items)
              if re.match(r'^\s*' + re.escape(article) + r'(?![零一二三四五六七八九十百0-9])', value)]
    if len(starts) != 1:
        return None
    start = starts[0]
    end = next((i for i in range(start + 1, len(parser.items))
                if _ARTICLE_START.match(parser.items[i])), None)
    if end is None:
        return None  # The closing boundary must also be present.
    if (any(parser.paragraph_in_tables[start:end]) or
            any(start <= pos <= end for pos in parser.table_positions)):
        return None  # A table cell or intervening table is never a legal 款.
    actual = parser.items[start:end]
    # Item lists, tables and continuation fragments require a different parser.
    # Refuse rather than treating each extracted line or item as a 款.
    if any(re.match(r'^\s*(?:[（(][一二三四五六七八九十0-9]+[）)]|[0-9]+[、.])', x)
           for x in actual):
        return None
    if len(actual) != len(contexts) or any(norm(a) != norm(c['text']) for a, c in zip(actual, contexts)):
        return None
    return {'method': 'complete_authenticated_article_matches_bound_source_html_paragraphs',
            'source_html_path': html_path, 'source_html_sha256': html_sha,
            'article': article, 'article_html_paragraph_count': len(actual),
            'next_article_text': parser.items[end],
            'usage': 'Exact clause selection only; no recursively cited article or neighboring labels copied.'}


def select_direct_contexts(group, bridge_text):
    """Yield actual contexts belonging only to the current direct reference."""
    address = _ADDRESS.search(bridge_text)
    if not address:
        return []
    article = '第' + address['article'] + '条'
    contexts = group.get('contexts', [])
    if (not contexts or not re.match(r'^\s*' + re.escape(article), contexts[0].get('text', ''))
            or any(not c.get('authentication_v34') for c in contexts)):
        return []
    # Do not choose a recursively cited article merely because its metadata
    # describes the parent article that cited it.
    if any(_ARTICLE_START.match(c['text']) and not re.match(r'^\s*' + re.escape(article), c['text'])
           for c in contexts):
        return []
    clause = address['clause']
    if clause is None:
        return list(contexts)
    if not group.get('complete_interval_authenticated'):
        return []
    ordinal = _ordinal(clause)
    structure = _source_clause_structure(contexts, article)
    if not structure or ordinal is None or not 1 <= ordinal <= len(contexts):
        return []
    chosen = copy.deepcopy(contexts[ordinal - 1])
    chosen['common_exact_clause_selection03'] = {
        **structure, 'clause_ordinal': ordinal,
        'selected_paragraph_id': chosen.get('paragraph_id'),
        'selected_paragraph_text': chosen['text'], 'current_direct_reference': address.group()}
    return [chosen]


def inspect_required_effectiveness(text, *, drug_scope=False):
    """Only an explicit requirement for evidence proving drug effectiveness.

    This supplements unchanged E implementation for a current exact-reference
    obligation. It does not assign E from an isolated heading or model label.
    """
    out = []
    for m in re.finditer(r'[^，,。；;]+', text):
        value = m.group()
        if (re.search(r'用于证明', value) and
                re.search(r'药(?:品|物)(?:安全性[、，,]\s*)?有效性', value) and
                re.search(r'试验数据|临床证据|临床数据', value)):
            out.append({'start': m.start(), 'end': m.end(), 'quote': value,
                        'kind': 'explicit_required_drug_effectiveness_data', 'subtype': 'clinical_evidence',
                        'basis': '当前确指条件实质要求提交证明药品有效性的试验数据；不是从所引全文复制标签。'})
    return out
