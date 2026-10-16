"""Metadata-only exposure exclusions and frozen finite semantic-review selection."""
from pathlib import Path
import collections, datetime, hashlib, json, sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent.parent
INPUTS={}
def bind(q):
 q=Path(q).resolve();r=q.read_bytes();return {'path':str(q),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def register(q):
 x=bind(q);INPUTS[x['path']]=x;return x
def load(q):register(q);return json.loads(Path(q).read_bytes())
def check(x):
 q=x.get('path',x.get('absolute_path'));actual=register(q)
 assert actual['bytes']==x['bytes'] and actual['sha256']==x['sha256'],q
 return actual
def save(n,x):
 with (P/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
allocation=load(B/'02-methods/human-small-sample-prospective-allocation-root/allocation-comparison.json')
draw_binding=allocation['inputs'][0];check(draw_binding);draw=load(draw_binding['path'])
meta_binding=next(x for x in draw['input_bindings'] if x['absolute_path'].endswith('/metadata-and-fixed-labels.jsonl'))
exp_binding=next(x for x in draw['input_bindings'] if x['absolute_path'].endswith('/exposure-ids.json'))
check(meta_binding);check(exp_binding)
exp=load(exp_binding['absolute_path']);exposed=set(exp['excluded_ids'])
assert len(exposed)==3037 and exp['summary']['eligible_holdout_N']==1444
metadata=[]
with Path(meta_binding['absolute_path']).open() as f:
 for line in f:
  row=json.loads(line);metadata.append({k:row[k] for k in ['id','exposure','department','family']})
assert len(metadata)==4481 and len({x['id'] for x in metadata})==4481
assert {x['id'] for x in metadata if x['exposure'] in ('direct','family_only')}==exposed
remaining={x['id'] for x in metadata if x['exposure']=='remaining'}
assert len(remaining)==1444 and not exposed&remaining
human_binding=load(B/'05-validation/human200-reception-root/bindings.json')['draw'];check(human_binding)
human=load(human_binding['path']);assigned=load(B/'05-validation/human200-reception-root/assigned-design-metadata.json')
human_ids=set(human['source_ids_sorted']);assert len(human_ids)==200
assert human_ids=={x['source_id'] for x in human['records']}=={x['source_id'] for x in assigned['records']}
assert assigned['design']['domain_population_N']=={'remaining':1444,'exposed':3037}
assert all(x['domain']==('exposed' if x['source_id'] in exposed else 'remaining') for x in human['records'])
diag=B/'07-statistics/current-v7-machine-diagnostics-20261011T1543-root';seal=load(diag/'seal.json')
for binding in seal['files']:check(binding)
all_meta=[]
with (diag/'machine-pair-disagreements.jsonl').open() as f:
 for line in f:
  row=json.loads(line)
  # Remaining and human200 semantic content never leaves this metadata parser.
  all_meta.append({k:row[k] for k in ['id','dimension','rule','native','packet','native_first']})
order={x['id']:i for i,x in enumerate(metadata)}
eligible=[];excluded=collections.Counter();null_positive=[]
for row in all_meta:
 if row['dimension'] not in ('I','F'):continue
 if row['id'] not in exposed:excluded['remaining_domain']+=1;continue
 if row['id'] in human_ids:excluded['human200_source_id']+=1;continue
 if (row['rule'],row['native']) not in ((0,1),(1,0)):
  excluded['not_binary_one_sided_positive']+=1
  if 1 in (row['rule'],row['native']) and None in (row['rule'],row['native']):null_positive.append(row)
  continue
 row['domain']='exposed';row['frame_order_1based']=order[row['id']]+1
 assert row['packet']['path']==str(B/'06-coding/full4481-common-v15-production-preparation-sol/packets'/(row['id']+'.json'))
 eligible.append(row)
eligible.sort(key=lambda x:(x['frame_order_1based'],x['dimension']))
selected={d:[x for x in eligible if x['dimension']==d][:20] for d in ('I','F')}
save('population-membership-metadata.json',{'exposed_N':3037,'remaining_N':1444,'exposed_ids_in_frame_order':[x['id'] for x in metadata if x['id'] in exposed],'remaining_ids_in_frame_order':[x['id'] for x in metadata if x['id'] in remaining],'human200_source_ids_excluded':sorted(human_ids),'new_human200_body_or_answers_opened':False,'domain_definition':'original frozen prospective allocation domain; later exposure refresh is not used to enlarge review access'})
save('readable-disagreement-selection-freeze.json',{'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'selection_rule':'I/F machine disagreements with exact (rule,native)=(1,0) or (0,1), original exposed3037 domain only, exclude all200 assigned source_ids; sort by original metadata frame order, first20 per dimension','eligible_N':len(eligible),'eligible_by_dimension':dict(collections.Counter(x['dimension'] for x in eligible)),'eligible_all_records':eligible,'excluded_metadata_counts':dict(excluded),'positive_vs_lawful_null_metadata_not_in_binary_review':null_positive,'selected_first20_by_dimension':selected,'semantic_packet_reads_before_this_freeze':0,'not_entire_eligible_semantic_review_if_above20':True,'labels_are_disagreements_not_truth':True,'model_calls':0,'classification_runs':0})
save('metadata-input-seal.json',{'files':list(INPUTS.values()),'N':len(INPUTS),'human200_body_read':False,'remaining_packet_body_read':False})
assert all(bind(x['path'])==x for x in INPUTS.values())
print(json.dumps({'eligible_N':len(eligible),'by_dimension':dict(collections.Counter(x['dimension'] for x in eligible)),'selected':{d:[x['id'] for x in rows] for d,rows in selected.items()},'excluded':dict(excluded),'positive_vs_null_N':len(null_positive)},ensure_ascii=False))
