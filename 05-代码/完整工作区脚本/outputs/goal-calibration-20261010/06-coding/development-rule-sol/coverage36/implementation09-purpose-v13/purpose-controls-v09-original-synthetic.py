"""Only the three predeclared purpose controls, no actual fixture/reference."""
import json
import sys
from pathlib import Path
from relations import RelationView
from dimensions import judge

d = json.loads(Path(__file__).with_name('v09-purpose-branch-predeclaration.json').read_text())
results = []
for c in d['purpose_controls']:
    decisions = judge(RelationView({'text': c['text'], 'contexts': []}))
    actual = {key: value['value'] for key, value in decisions.items()}
    results.append(dict(c, actual=actual, passed=actual == c['expected'], decisions=decisions))
r = {'controls': results, 'passed': sum(c['passed'] for c in results), 'failed': sum(not c['passed'] for c in results)}
print(json.dumps(r, ensure_ascii=False, indent=2))
sys.exit(0 if not r['failed'] else 1)
