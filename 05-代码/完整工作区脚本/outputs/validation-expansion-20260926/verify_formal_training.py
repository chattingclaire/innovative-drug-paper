from pathlib import Path
from datetime import datetime
import json, hashlib
OUT = Path(__file__).parent
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
load = lambda p: json.loads(p.read_text())
data = {}; inputs = {}; confirmations = {}
for coder in 'AC':
    d = OUT / 'formal-preparation' / f'agent-{coder}'
    packet = load(d / '构造培训材料.json')
    raw = load(d / f'培训提交-{coder}.json')
    assert raw['coder'] == coder and raw['protocol_acknowledged'] is True
    assert raw['protocol_version'] == packet['protocol_version'] == 'CAL-5D-20260926-v1.3'
    rows = {r['id']:r for r in raw['rows']}
    assert len(rows) == len(raw['rows']) == 15
    assert set(rows) == {r['id'] for r in packet['rows']}
    for r in rows.values():
        assert set(r['labels']) == set(('S','E','Ec','I','F'))
        assert all(v in (0,1,'待定') for v in r['labels'].values())
        assert all(r['dimension_reasons'].get(k) for k in r['labels'])
    data[coder] = rows
    inputs[coder] = {p.name:sha(p) for p in d.glob('*') if p.is_file()}
    confirmations[coder] = load(d / '培训理解确认.json')
assert inputs['A']['构造培训材料.json'] == inputs['C']['构造培训材料.json']
assert inputs['A']['五维共用编码协议.md'] == inputs['C']['五维共用编码协议.md']
diffs = []
for k in data['A']:
    for field in ('labels','fairness_subtypes','innovation_subtypes','safety_quality_basis'):
        if data['A'][k][field] != data['C'][k][field]:
            diffs.append({'id':k,'field':field,'A':data['A'][k][field],'C':data['C'][k][field]})
report = {'created_at':datetime.now().astimezone().isoformat(),
          'purpose':'pre_holdout_synthetic_training_not_reliability_or_validity',
          'same_five_dimension_judgements':sum(data['A'][k]['labels']==data['C'][k]['labels'] for k in data['A']),
          'n_synthetic_examples':15,'original_submission_differences':diffs,'input_and_submission_hashes':inputs,
          'feedback':{'path':str(OUT/'formal-preparation/共同培训反馈-v1.3.md'),'sha256':sha(OUT/'formal-preparation/共同培训反馈-v1.3.md')},
          'independent_post_training_acknowledgements':confirmations,
          'roles':{'A':'fresh AI context; v1.3 and synthetic training only before H600',
                   'C':'continuing AI reviewer; previous development exposure retained and excluded from holdout pool'},
          'original_submissions_overwritten':False,'actual_human_coders':False,
          'shared_model_errors_independent':False,
          'formal_rows_drawn':False}
p = OUT / 'formal-preparation/共同培训核验.json'
if p.exists():raise RuntimeError('Do not overwrite training audit')
p.write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps({'same_five_dimension_judgements':report['same_five_dimension_judgements'],'original_differences':diffs,'both_acknowledged':True},ensure_ascii=False))
