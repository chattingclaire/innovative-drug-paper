"""First sealed candidate-rule pass on the preliminary remaining frame only.

No human labels, model calls, source edits, sampling, or classifier changes.
This is an input/execution and sample-preparation audit, not validation.
"""
from pathlib import Path
import hashlib
import json
import sys
from collections import Counter
from datetime import datetime
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
BASE = HERE.parents[2]
OUT = HERE / '剩余句段首次机器核查'
FROZEN = HERE / '冻结版本'

def digest(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert not OUT.exists(), 'First pass already exists; do not silently rerun.'
    lock = json.loads((HERE / '方法与标准冻结.json').read_text())
    for b in lock['snapshots']:
        assert digest(b['snapshot']['path']) == b['snapshot']['sha256']
    audit = json.loads((HERE / '剩余样本初核.json').read_text())
    allowed = {x['source_id'] for x in audit['remaining_metadata']}
    assert len(allowed) == 923
    source = BASE / '06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl'
    assert digest(source) == '3691404b9990e5c1eef0fc632c5123dcfbbaf1321887724ad7ad165a5d16a2b7'
    overrides = json.loads((FROZEN / 'rule/semantic-overrides.json').read_text())
    selected = [r for r in map(json.loads, source.read_text().splitlines()) if r['id'] in allowed]
    assert len(selected) == 923 and {r['id'] for r in selected} == allowed
    OUT.mkdir()
    sys.path.insert(0, str(FROZEN / 'rule'))
    from relations import RelationView
    from dimensions import judge
    from evidence import validate_decisions
    rows = []
    enriched = []
    with (OUT / 'first-inputs.jsonl').open('w') as inputs, (OUT / 'first-predictions.jsonl').open('w') as results:
        for r in selected:
            rid = r['id']
            unit = overrides.get(rid, r['semantic_unit'])
            if rid in overrides:
                enriched.append(rid)
            inputs.write(json.dumps({'id':rid,'semantic_unit':unit},ensure_ascii=False)+'\n')
            item = {'id':rid, 'implementation_error':None, 'labels':None, 'decisions':None}
            try:
                view = RelationView(unit)
                decisions = judge(view)
                validate_decisions(view.unit, decisions)
                item.update(labels={d:v['value'] for d,v in decisions.items()},decisions=decisions)
            except Exception as exc:
                item['implementation_error'] = f'{type(exc).__name__}: {exc}'
            results.write(json.dumps(item,ensure_ascii=False)+'\n')
            rows.append(item)
    summary = {
        'created_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
        'purpose':'feasibility_only_no_human_comparison_no_sampling',
        'N':len(rows), 'independent_validation_completed':False,
        'source_overlap':'All remaining records come from sources with prior development records; no claim of unseen-document validation.',
        'remaining_eligibility':'Preliminary sentence-level remainder; prior context use still requires audit.',
        'counts':{d:dict(Counter(str(r['labels'][d]) for r in rows if r['labels'] is not None)) for d in ['S','E','Ec','I','F']},
        'technical_errors':[{'id':r['id'],'error':r['implementation_error']} for r in rows if r['implementation_error']],
        'existing_overrides_applied':enriched,
        'inputs_sha256':digest(OUT/'first-inputs.jsonl'),
        'predictions_sha256':digest(OUT/'first-predictions.jsonl'),
        'frozen_method_lock_sha256':digest(HERE/'方法与标准冻结.json'),
        'no_human_reference_loaded':True, 'no_LLM_calls':True,
        'no_full4481_rerun':True, 'no_rule_changes':True,
        'rule_positive_is_not_human_truth':True,
    }
    (OUT/'首次核查记录.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='technical_errors'},ensure_ascii=False,indent=2))
    print('technical_error_N',len(summary['technical_errors']))

if __name__=='__main__':
    main()
