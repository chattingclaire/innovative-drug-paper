"""Display already-redacted source text and all actual output fields; no coding or model call."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
rows = json.loads((HERE / '../execution-audit/candidate07_all240_comparison_REDACTED_PRIVATE.json').read_text())['rows']
prior_context_texts = set()
def prior_walk(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key in ['text', 'usage'] and isinstance(value, str): prior_context_texts.add(value)
            elif isinstance(value, (dict, list)): prior_walk(value)
    elif isinstance(obj, list):
        for value in obj: prior_walk(value)
for row in rows[:int(sys.argv[1])]: prior_walk(row['input']['contexts'])
for i in range(int(sys.argv[1]), int(sys.argv[2])):
    row = rows[i]
    seen, contexts = set(), []
    def walk(obj, path='contexts'):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key in ['text', 'usage'] and isinstance(value, str):
                    if value not in seen:
                        seen.add(value)
                        contexts.append([path + '.' + key, ('[same exact text read earlier: ' + value[:22] + '…]') if value in prior_context_texts else value])
                        prior_context_texts.add(value)
                elif isinstance(value, (dict, list)):
                    walk(value, path + '.' + key)
        elif isinstance(obj, list):
            for j, value in enumerate(obj):
                walk(value, path + f'[{j}]')
    walk(row['input']['contexts'])
    print(i, row['id'], row['input']['source_title'], row['input']['text'])
    print('CONTEXT_TEXTS', json.dumps(contexts, ensure_ascii=False, separators=(',', ':')))
    actual = row['candidate07_intact_actual_row']
    print('OUTPUT S/E/Ec/I/F', list(actual['labels'].values()), 'REASONS', list(actual['dimension_reasons'].values()))
    print('EVIDENCE', json.dumps([[e['dimension'], e['source'], e['quote']] for e in actual['evidence']], ensure_ascii=False), 'F', actual['fairness_subtypes'], 'I', actual['innovation_subtypes'], 'Q', actual['safety_quality_basis'])
    if row['candidate07_issue_records']: print('ISSUES', json.dumps(row['candidate07_issue_records'], ensure_ascii=False))
