"""Constructed structural regression checks, not policy validation data."""
import copy
import hashlib
import json
import tempfile
from pathlib import Path

from common_reference_resolution03 import select_direct_contexts, inspect_required_effectiveness
from source_context_adapter_v34 import authenticate_context
from common_definition_stage import _payment_context_premise_only


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    with tempfile.TemporaryDirectory() as temp:
        d = Path(temp)
        first = '第七条 药品应提交用于证明药品安全性、有效性的全部试验数据。'
        second = '该药品年度基金支出预算不超过一百万元。'
        last = '第八条 药品的其他管理事项。'
        html = d / 'source.html'
        html.write_text('<html><body>' + ''.join('<p>' + x + '</p>' for x in (first, second, last)) + '</body></html>')
        source = d / 'source.json'
        source.write_text(json.dumps({'source_html': str(html), 'source_sha256': sha(html),
                                     'normative_paragraphs': [first, second, last]}, ensure_ascii=False))
        candidate = d / 'candidate.json'
        candidate.write_text(json.dumps({'paragraphs': [{'id': 'p1', 'text': first}, {'id': 'p2', 'text': second}]}))
        contexts = []
        for i, text in enumerate((first, second)):
            contexts.append(authenticate_context({'text': text, 'paragraph_id': 'p' + str(i + 1),
                'source_path': str(source), 'source_sha256': sha(source),
                'candidate_path': str(candidate), 'candidate_sha256': sha(candidate),
                'source_lines': ['normative_paragraphs:' + str(i)]}))
        group = {'contexts': contexts, 'complete_interval_authenticated': True,
                 'reference_address': '第七条第一/第二款'}
        saved = copy.deepcopy(group)
        a = select_direct_contexts(group, '符合本办法第七条第一款的')
        assert len(a) == 1 and a[0]['text'] == first
        assert a[0]['common_exact_clause_selection03']['clause_ordinal'] == 1
        b = select_direct_contexts(group, '符合第七条第二款情形')
        assert len(b) == 1 and b[0]['text'] == second
        assert select_direct_contexts(group, '符合第七条第三款的') == []
        recursive = copy.deepcopy(group)
        recursive['contexts'][0]['text'] = first.replace('第七条', '第五条')
        assert select_direct_contexts(recursive, '符合第七条第一款的') == []
        incomplete = copy.deepcopy(group)
        incomplete['complete_interval_authenticated'] = False
        assert select_direct_contexts(incomplete, '符合第七条第一款的') == []
        html.write_text(html.read_text().replace(second, '其他不符的实际段落。'))
        assert select_direct_contexts(group, '符合第七条第一款的') == []
        assert group == saved
        e = inspect_required_effectiveness(first)
        assert len(e) == 1 and first[e[0]['start']:e[0]['end']] == e[0]['quote']
        assert inspect_required_effectiveness('提交药品有效性专家组的名单及联系方式。') == []
        assert inspect_required_effectiveness('第七条 质量可控性的全部试验数据。') == []
        # An actual HTML table paragraph must never become a legal second 款.
        table_html, table_source = d / 'table.html', d / 'table_source.json'
        table_html.write_text('<p>' + first + '</p><table><tr><td><p>' + second +
                              '</p></td></tr></table><p>' + last + '</p>')
        table_source.write_text(json.dumps({'source_html': str(table_html), 'source_sha256': sha(table_html),
                                           'normative_paragraphs': [first, second, last]}, ensure_ascii=False))
        table_group = copy.deepcopy(group)
        for c in table_group['contexts']:
            c.update({'source_path': str(table_source), 'source_sha256': sha(table_source)})
            c.update(authenticate_context(c))
        assert select_direct_contexts(table_group, '符合第七条第二款的') == []
        for value, want in [
            ('(2)调整医保支付范围的药品:原支付范围满足条件(1)的情况下', True),
            ('原医保支付范围满足条件(1)的情况下,因调整支付范围所致未来基金支出预算增幅不超过100%。', True),
            ('确定新的医保支付范围,并测算药品基金支出预算。', False)]:
            a = value.index('医保支付范围')
            assert _payment_context_premise_only(value, {'start': a, 'end': a + len('医保支付范围')}) == want
    print(json.dumps({'structural_constructed_checks': 7, 'effectiveness_boundary_checks': 3,
                      'payment_noun_premise_checks': 3,
                      'passed': True, 'reference_labels_loaded': False}))


if __name__ == '__main__':
    main()
