"""Select already exposed material for three-department development coverage."""
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'04-calibration/coverage01/admin'
OUT.mkdir(parents=True, exist_ok=True)
assert not (OUT/'selection.json').exists()
frame_path = ROOT/'00-baseline/source-only-frame.jsonl'
exposure_path = ROOT/'01-review/exposure-ids.json'
mapping_path = ROOT/'04-calibration/pilot01/admin/private_mapping.json'
frame = [json.loads(s) for s in frame_path.read_text().splitlines() if s.strip()]
direct = set(json.loads(exposure_path.read_text())['direct_exposure_ids'])
previous = {r['frame_id'] for r in json.loads(mapping_path.read_text())}
seed = 'goal-calibration-20261010-three-department-development-coverage01'
selected=[]
for department in ['NMPA','NHSA','NHC']:
    pool = [r for r in frame if r['id'] in direct-previous and r['analysis_group']==department]
    # A deterministic label-blind ordering; no population inference is claimed.
    pool.sort(key=lambda r: hashlib.sha256((seed+'|'+r['id']).encode()).hexdigest())
    docs=Counter(); families=set(); chosen=[]
    for r in pool:
        family = r['normalized_text_family']['family_id']
        doc = r['source_document_stem']
        if family in families or docs[doc]>=3:
            continue
        chosen.append({'frame_id':r['id'],'department':department,'source_document_stem':doc,
                       'family_id':family,'unit_sha256':r['unit_text_sha256']})
        docs[doc]+=1;families.add(family)
        if len(chosen)==12:
            break
    assert len(chosen)==12
    selected.extend(chosen)
assert len({x['frame_id'] for x in selected})==36
assert {x['frame_id'] for x in selected}<=direct
assert not ({x['frame_id'] for x in selected}&previous)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
result={'status':'development_selection_only_no_labels_or_population_estimation',
        'selection_method':'Each department 12; SHA-based fixed ordering, distinct text families, maximum 3 units per source document; only prior directly exposed units; no label/keyword balancing.',
        'ordering_seed':seed,'n':36,'department_counts':dict(Counter(x['department'] for x in selected)),
        'purpose':'Check common manual across three departments, especially supplement pilot01 NHC n=1. This is purposive development coverage, not new final holdout.',
        'inputs':[{'path':str(p),'sha256':sha(p)} for p in [frame_path,exposure_path,mapping_path]],
        'records':selected,'new_holdout_consumed':0,'human_coding_executed':False,
        'labels_or_prediction_files_read':False}
(OUT/'selection.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'n':36,'department_counts':result['department_counts'],'source_documents':len({x['source_document_stem'] for x in selected})},ensure_ascii=False))
