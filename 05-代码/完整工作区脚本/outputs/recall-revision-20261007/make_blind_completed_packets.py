import json
from pathlib import Path

p=Path(__file__).resolve().parent
rows={x['id']:x for x in map(json.loads,(p/'effective_blind_inputs_v30.jsonl').read_text().splitlines())}
allrows=[]; missing=[]
for pkt,mp in [('blind_review_packet.json','blind_mapping_PRIVATE.json'),('blind_review_supplement_packet.json','blind_supplement_mapping_PRIVATE.json')]:
    packet=json.loads((p/pkt).read_text())
    mapping={x['blind_id']:x['original_id'] for x in json.loads((p/mp).read_text())}
    new=[]
    for old in packet['rows']:
        r=json.loads(json.dumps(rows[mapping[old['id']]]));r['id']=old['id']
        # Only change the audit identifier. No text, labels, or evidence are added.
        for c in r['contexts'].get('verified_parent_context',[]):
            if 'unit_id' in c:c['unit_id']=old['id']
        for c in r['contexts'].get('verified_context_certificates',{}).get('verified_parent_context',[]):
            if 'unit_id' in c:c['unit_id']=old['id']
        new.append(r);allrows.append(r)
        if r['id'] in ['RECALL-BLIND-023','RECALL-BLIND-054','RECALL-BLIND-055','RECALL-BLIND2-011']:missing.append(r)
    (p/(Path(pkt).stem+'_completed.json')).write_text(json.dumps({**packet,'scope':packet['scope']+'; source context completion; original first decisions sealed','rows':new},ensure_ascii=False,indent=2)+'\n')
(p/'blind90_completed_material.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in allrows))
(p/'blind4_material_gap_completed.json').write_text(json.dumps({'manual_path':packet['manual_path'],'scope':'Rejudge only four previously unclassifiable material gaps; sealed first judgments preserved; no reference answers or machine output provided','rows':missing},ensure_ascii=False,indent=2)+'\n')
print('created',len(allrows),len(missing))
