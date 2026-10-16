"""Seal AI-consensus development reference; never claim human ground truth."""
import copy
import hashlib
import json
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
TRIAL=ROOT/'04-calibration/pilot02'
OUT=ROOT/'06-coding/development-reference41-v11'
assert not OUT.exists()
OUT.mkdir();(OUT/'source-pages').mkdir()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=lambda p:[json.loads(s) for s in p.read_text().splitlines() if s.strip()]
audit=json.loads((TRIAL/'admin/diagnostics.json').read_text())
assert not audit['quality_issues'] and not audit['disagreements_and_pending']
mapping=json.loads((TRIAL/'admin/private_mapping.json').read_text())
by_coder={c:{x['blind_id']:x['frame_id'] for x in mapping if x['coder']==c} for c in 'AB'}
labels={c:{by_coder[c][x['id']]:x for x in rows(TRIAL/c/'labels.jsonl')} for c in 'AB'}
source=[];reference=[]
for p in rows(TRIAL/'A/packet.jsonl'):
    fid=by_coder['A'][p['id']];p=copy.deepcopy(p);p['id']=fid;source.append(p)
    a=labels['A'][fid];b=labels['B'][fid]
    assert a['labels']==b['labels'] and all(v in [0,1] for v in a['labels'].values())
    reference.append({'id':fid,'labels':a['labels'],
                      'reference_role':'AI_consensus_development_only',
                      'evidence_A':a['evidence'],'evidence_B':b['evidence'],
                      'manual_sha256':sha(TRIAL/'A/manual.md'),
                      'initial_judgment_and_discussion_role':'Post-material development rejudgment; both coders have own prior history.'})
    for x in p.get('source_page_attachments',[]):
        dest=OUT/x['relative_path']
        if not dest.exists():shutil.copyfile(TRIAL/'A'/x['relative_path'],dest)
        assert sha(dest)==x['sha256']
source.sort(key=lambda r:r['id']);reference.sort(key=lambda r:r['id'])
for name,contents in [('source.jsonl',source),('reference.jsonl',reference)]:
    (OUT/name).write_text(''.join(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n' for x in contents))
shutil.copyfile(TRIAL/'A/manual.md',OUT/'manual.md')
manifest={'status':'sealed_development_fixture_not_formal_test_or_human_reference','n':41,'dimension_judgments':205,
          'reference_identity':'Two AI independent development rejudgments in agreement; not a new human adjudication.',
          'consensus_rule':'Only both valid equal labels included; here all 41x5 equal. No scores used to change labels.',
          'allowed_use':'Rule/LLM implementation development on these 41 cases and semantic diagnostics; not final validation or human reliability.',
          'inputs':[{'path':str(p),'sha256':sha(p)} for p in [TRIAL/'admin/diagnostics.json',TRIAL/'A/labels.jsonl',TRIAL/'B/labels.jsonl',TRIAL/'A/packet.jsonl',TRIAL/'B/packet.jsonl']],
          'outputs':[{'path':str(OUT/name),'sha256':sha(OUT/name)} for name in ['source.jsonl','reference.jsonl','manual.md']],
          'source_pages':[{'path':str(p),'sha256':sha(p)} for p in sorted((OUT/'source-pages').glob('*'))],
          'runtime_input_restriction':'Runtime reads source/manual/source assets only; reference may be read by a separate development evaluator after predictions are sealed.',
          'human_execution_completed':False,'final_acceptance':False,'prior_files_modified':False}
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'n':41,'source_sha256':sha(OUT/'source.jsonl'),'reference_sha256':sha(OUT/'reference.jsonl'),'identity':'AI development consensus'},ensure_ascii=False))
