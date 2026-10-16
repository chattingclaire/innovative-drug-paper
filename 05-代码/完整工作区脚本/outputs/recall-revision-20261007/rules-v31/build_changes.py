from pathlib import Path
import json,collections,hashlib
ROOT=Path(__file__).resolve().parent
BASE=ROOT.parents[1]/'final-three-department-20261007'/'rules-v30'
meta=json.loads((ROOT/'all_predictions.run.json').read_text())
inputs={r['id']:r['input'] for r in map(json.loads,Path(meta['input_path']).read_text().splitlines())}
old={r['id']:r['prediction'] for r in map(json.loads,(BASE/'all_predictions.jsonl').read_text().splitlines())}
changes=[]
for r in map(json.loads,(ROOT/'all_predictions.jsonl').read_text().splitlines()):
 p=r['prediction'];before=old[r['id']]
 for d in p['labels']:
  if p['labels'][d]!=before['labels'][d]:
   changes.append({'id':r['id'],'dimension':d,'old':before['labels'][d],'new':p['labels'][d],
     'text':inputs[r['id']]['unit_text'],
     'evidence':[e for e in p['evidence'] if e['dimension']==d],
     'suppressions':[e for e in p.get('suppressions',[]) if d in e.get('dimensions',[]) and e['rule'].startswith('V31')],
     'input':inputs[r['id']]})
(ROOT/'changes_by_id_dimension.json').write_text(json.dumps(changes,ensure_ascii=False,indent=2)+'\n')
counts=collections.Counter((x['dimension'],x['old'],x['new']) for x in changes)
print(json.dumps({'n':len(changes),'counts':[dict(d=d,old=a,new=b,n=n) for (d,a,b),n in counts.items()],
 'input_sha256':meta['input_sha256'],'prediction_sha256':meta['prediction_sha256']},ensure_ascii=False))
for x in changes:print(x['id'],x['dimension'],x['old'],x['new'],x['text'])
