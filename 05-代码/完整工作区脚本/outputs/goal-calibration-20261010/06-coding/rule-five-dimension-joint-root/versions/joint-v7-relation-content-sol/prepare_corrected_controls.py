from pathlib import Path
import json,copy,hashlib,datetime
P=Path(__file__).resolve().parent
old=P/'relation-controls-fixed-before-edit.json';data=json.loads(old.read_bytes());cases=data['cases'];original=copy.deepcopy(cases[5]['semantic_input']);changes=[]
for c in cases:
 if c['name']=='original source relation 00005':c['expected']['Ec']=0
 if not c['name'].startswith('table exception guard '):continue
 variation=c['name'].removeprefix('table exception guard ');u=copy.deepcopy(original);byid={c['context_id']:c for c in u['contexts']};drop=set()
 for container in u['contexts']:
  if container.get('kind')!='cited_reference':continue
  child_ids=[cid for g in container.get('structure',{}).get('child_groups',[]) if g.get('position')=='contexts' for cid in g.get('ordered_context_ids',[])]
  head=byid[child_ids[0]]['text'] if child_ids else '';number=7 if head.startswith('第七条') else 6 if head.startswith('第六条') else None
  boundary_ids=[cid for g in container.get('structure',{}).get('child_groups',[]) if g.get('position')=='structure_boundary' for cid in g.get('ordered_context_ids',[])]
  if variation=='missing sixth article' and number==6:drop.update([container['context_id']]+child_ids+boundary_ids)
  if variation=='missing seventh boundary' and number==7:drop.update(boundary_ids)
  if variation=='missing sixth boundary' and number==6:drop.update(boundary_ids)
  if variation=='foreign sixth article' and number==6:
   for child in u['contexts']:
    if child['context_id'] in [container['context_id']]+child_ids+boundary_ids:child['source_ref']['sha256']='b'*64
  if variation=='reordered seventh clauses' and number==7:
   for g in container['structure']['child_groups']:
    if g.get('position')=='contexts':g['ordered_context_ids']=list(reversed(g['ordered_context_ids']))
 u['contexts']=[c for c in u['contexts'] if c['context_id'] not in drop]
 changes.append({'name':c['name'],'old_input_sha256':hashlib.sha256(json.dumps(c['semantic_input'],ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'new_input_sha256':hashlib.sha256(json.dumps(u,ensure_ascii=False,sort_keys=True).encode()).hexdigest(),'expected_unchanged':True,'removed_context_ids':sorted(drop)})
 c['semantic_input']=u
out=P/'relation-controls-corrected-fixed-before-third-edit.json'
with out.open('x') as f:json.dump({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':'corrected disclosed development fixtures, not independent validation','original_fixed_file_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'fixture_error':'Sixth article reference address also contains the words 第七条, so the old mutator selected it as article seven and three intended missing/swap mutations were empty. Corrected using actual first original member heading; original inputs and failed runs retained. No expected table labels changed. Added Ec=0 to original 00005 control to catch quote-identity overlap.','changes':changes,'expected_not_classifier_input':True,'cases':cases},f,ensure_ascii=False,indent=2)
print('corrected',len(changes),'table fixtures; fixed',len(cases),'cases')
