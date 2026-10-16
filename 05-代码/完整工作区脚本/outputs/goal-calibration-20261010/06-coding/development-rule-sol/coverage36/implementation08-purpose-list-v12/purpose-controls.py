"""The three predeclared purpose-boundary controls; no fixture or reference."""
import json
import sys
from pathlib import Path
from relations import RelationView
from dimensions import judge

declared = json.loads(Path(__file__).with_name('purpose-predeclaration.json').read_text())
results = []
for case in declared['controls']:
    unit = {'text': case['text'], 'contexts': []}
    decision = judge(RelationView(unit))
    actual = {d: v['value'] for d, v in decision.items()}
    results.append({'name': case['name'], 'text': case['text'], 'expected': case['expected'],
                    'actual': actual, 'passed': actual == case['expected'], 'decisions': decision})
report = {'controls': results, 'passed': sum(r['passed'] for r in results), 'failed': sum(not r['passed'] for r in results)}
print(json.dumps(report, ensure_ascii=False, indent=2))
sys.exit(0 if report['failed'] == 0 else 1)
