from pathlib import Path
import json,hashlib,copy,random
HERE=Path(__file__).resolve().parent
DIMS=['S','E','Ec','I','F']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def strings(x):
 if isinstance(x,str):yield x
 elif isinstance(x,dict):
  for v in x.values():yield from strings(v)
 elif isinstance(x,list):
  for v in x:yield from strings(v)
mapping=json.loads((HERE/'admin/PRIVATE_mapping.json').read_text());lookup={(r['coder'],r['blind_id']):r['original_id'] for r in mapping}
sources={};all_refs={};first_refs={};errors=[];pending=[]
for coder in ['A','C']:
 folder=HERE/'confirmation'/f'agent-{coder}';first={};material={}
 for n in range(1,11):
  ip=folder/f'材料-{n:02d}.json';op=folder/f'结果-{n:02d}.json';d=json.loads(op.read_text());inp=json.loads(ip.read_text())['rows']
  assert d['input_packet_sha256']==sha(ip) and d['coder']==coder and d['operational_version']=='v1.4'
  assert [r['id'] for r in d['rows']]==[r['id'] for r in inp]
  sources[str(op)]=sha(op);sources[str(ip)]=sha(ip)
  for r,s in zip(d['rows'],inp):first[r['id']]=copy.deepcopy(r);material[r['id']]=s
 assert len(first)==300
 for p in sorted(folder.glob('录入更正*.json')):
  c=json.loads(p.read_text());assert c['labels_changed'] is False and c['type']=='clerical_correction'
  assert set(c['corrected_dimension_reasons'])==set(DIMS)
  first[c['id']]['dimension_reasons']=c['corrected_dimension_reasons'];sources[str(p)]=sha(p)
 final=copy.deepcopy(first)
 for version in ['v4','v5','v6']:
  ip=folder/f'补充材料-{version}.json';op=folder/f'补料复核-{version}.json'
  d=json.loads(op.read_text());inp=json.loads(ip.read_text())['rows'];assert d['input_packet_sha256']==sha(ip)
  assert [r['id'] for r in d['rows']]==[r['id'] for r in inp]
  sources[str(op)]=sha(op);sources[str(ip)]=sha(ip)
  for r,s in zip(d['rows'],inp):final[r['id']]=copy.deepcopy(r);material[r['id']]=s
 for bid,r in final.items():
  labs=r['labels'];reason=r['dimension_reasons'];s=material[bid]
  assert set(labs)==set(DIMS) and set(reason)==set(DIMS),(coder,bid)
  assert all(type(v)is int and v in (0,1) for v in labs.values()),(coder,bid,'nonbinary_final',labs)
  assert all(isinstance(x,str) and x.strip() for x in reason.values())
  found=set()
  for e in r['evidence']:
   q=e['quote'];dim=e['dimension'];source=e['source']
   if source=='unit':
    if q not in s['text']:errors.append(f'{coder}/{bid}/{dim}:nonliteral_unit')
    else:found.add(dim)
   elif source=='context':
    if not any(q in t for t in strings(s['contexts'])):errors.append(f'{coder}/{bid}/{dim}:nonliteral_context')
   else:errors.append(f'{coder}/{bid}:unknown_evidence_source')
  for dim in DIMS:
   if labs[dim]==1 and dim not in found:errors.append(f'{coder}/{bid}/{dim}:missing_unit_evidence')
  for dim,key,allowed in [('I','innovation_subtypes',{'attribute','research_support','qualification_advantage'}),('F','fairness_subtypes',{'access','affordability','clinical_management','dimension_information'})]:
   sub=r[key]
   if bool(sub)!=bool(labs[dim]) or any(x not in allowed for x in sub):errors.append(f'{coder}/{bid}/{dim}:subtype')
 first_refs[coder]={lookup[(coder,bid)]:{**r,'id':lookup[(coder,bid)],'blind_id':bid} for bid,r in first.items()}
 all_refs[coder]={lookup[(coder,bid)]:{**r,'id':lookup[(coder,bid)],'blind_id':bid} for bid,r in final.items()}
 for name,rows in [(f'agent_{coder}_first.jsonl',first_refs[coder]),(f'agent_{coder}_final_v6.jsonl',all_refs[coder])]:
  p=HERE/'reference'/name;p.parent.mkdir(exist_ok=True);p.write_text(''.join(json.dumps(rows[rid],ensure_ascii=False)+'\n' for rid in sorted(rows)))
assert not errors,errors
raw={r['id']:r for r in (json.loads(x) for x in (HERE/'effective_blind_inputs_v6.jsonl').read_text().splitlines())}
disagree=[rid for rid in all_refs['A'] if all_refs['A'][rid]['labels']!=all_refs['C'][rid]['labels']]
agree=sorted(set(all_refs['A'])-set(disagree));audit=random.Random(2026100751).sample(agree,min(24,len(agree)))
packet=[];amap=[]
for n,rid in enumerate(sorted(disagree)+audit,1):
 bid=f'ADJ2-{n:04d}';amap.append({'blind_id':bid,'original_id':rid,'selection':'disagreement' if rid in disagree else 'random_agreement_audit'})
 packet.append({**raw[rid],'id':bid,'first_judgments':{'A':{k:all_refs['A'][rid][k] for k in ['labels','dimension_reasons','evidence','innovation_subtypes','fairness_subtypes']},'C':{k:all_refs['C'][rid][k] for k in ['labels','dimension_reasons','evidence','innovation_subtypes','fairness_subtypes']}}})
for i in range(0,len(packet),20):dump(HERE/'adjudication'/f'材料-{i//20+1:02d}.json',{'rows':packet[i:i+20]})
dump(HERE/'admin/adjudication_mapping_PRIVATE.json',amap)
dump(HERE/'reference/agent_reference_QA.json',{'n_per_coder':300,'final_binary_labels_per_coder':1500,'unresolved_pending':0,'final_material_version':'v6','first_outputs_preserved':True,'source_sha256':sources,'structural_literal_errors':errors,'disagreement_units':len(disagree),'agreement_audit_n':len(audit),'adjudication_n':len(packet),'semantic_correctness_proven_by_literal_QA':False,'human_validation_completed':False})
print(json.dumps({'n':300,'disagreement_units':len(disagree),'agreement_audit_n':len(audit),'adjudication_n':len(packet),'literal_errors':errors},ensure_ascii=False))
