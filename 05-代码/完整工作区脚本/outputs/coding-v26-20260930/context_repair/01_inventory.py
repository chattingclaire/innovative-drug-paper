from pathlib import Path
import json,hashlib,itertools,collections
P=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/autocode-v25-20260927')
O=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/coding-v26-20260930/context_repair')
def rows(p):return [json.loads(x) for x in p.read_text().splitlines() if x.strip()]
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[P/x for x in ['current_rule_inputs.jsonl','current_llm_inputs.jsonl','current_1268_references.jsonl','rule_runs/v25-candidate-3/all_predictions.jsonl','llm_runs/gpt56-sol-v13-native-1/all_predictions.jsonl','H427/admin_mapping.json']]
ri={x['id']:x for x in rows(paths[0])};li={x['id']:x for x in rows(paths[1])};ref=rows(paths[2]);ru={x['id']:x['candidate'] for x in rows(paths[3])};lm={x['id']:x for x in rows(paths[4])};hm={x['id']:x for x in json.loads(paths[5].read_text())}
methods={'A':{},'C':{},'rule':ru,'LLM':lm};frames={'current1268':set(),'H427':set()}
for x in ref:
 frames['current1268'].add(x['id'])
 for c in ['A','C']:methods[c][x['id']]=dict(x['original_references'][c],reference_frame='current1268',record_file=str(paths[2]))
for c in ['A','C']:
 for p in sorted((P/'H427'/('agent-'+c)).glob('结果-*.json')):
  paths.append(p)
  for x in json.loads(p.read_text())['rows']:
   mp=hm[x['id']];rid=mp['rerun_id'];assert rid not in methods[c]
   assert hashlib.sha256(li[rid]['text'].encode()).hexdigest()==mp['text_sha256']
   methods[c][rid]=dict(x,reference_frame='H427',record_file=str(p));frames['H427'].add(rid)
pending={k:{rid for rid,r in rr.items() if any(v not in [0,1] for v in r['labels'].values())} for k,rr in methods.items()}
assert len(frames['H427'])==427 and len(frames['current1268'])==1268 and not frames['H427']&frames['current1268']
mu=pending['rule']|pending['LLM'];assert len(mu)==53
summary={'status':'pending_inventory_only_no_adjudication','definitions':{'pending':'至少一维为待定/null，按单元去重；另列待定维度格数。','coverage':'A/C覆盖current1268+H427的1695个唯一单元；规则和LLM覆盖4924。未获A/C参照的单元不是阴性或已判定。'},'input_hashes':[{'path':str(p),'sha256':h(p)} for p in paths],'counts':{},'pairwise_intersections':{},'all_four_intersection_ids':sorted(set.intersection(*pending.values())),'machine_union_ids':sorted(mu),'machine_union_count':len(mu)}
for k,rr in methods.items():
 summary['counts'][k]={'available_units':len(rr),'pending_units':len(pending[k]),'pending_dimension_cells':sum(sum(v not in [0,1] for v in r['labels'].values()) for r in rr.values()),'by_dimension':{d:sum(r['labels'][d] not in [0,1] for r in rr.values()) for d in ['S','E','Ec','I','F']},'by_reference_frame':{f:len(pending[k]&ids) for f,ids in frames.items()}}
for a,b in itertools.combinations(methods,2):summary['pairwise_intersections'][a+'&'+b]={'count':len(pending[a]&pending[b]),'ids':sorted(pending[a]&pending[b])}
summary['all_pending_union_count']=len(set.union(*pending.values()))
full=[]
for rid in sorted(set.union(*pending.values())):
 x={'id':rid,'original_id':ri[rid]['original_id'],'text':li[rid]['text'],'unit_text_sha256':hashlib.sha256(li[rid]['text'].encode()).hexdigest(),'source_title':li[rid]['source_title'],'pages':li[rid]['pages'],'pending_methods':[k for k in methods if rid in pending[k]],'in_machine_pending_union':rid in mu,'pending_records':{}}
 for k in x['pending_methods']:
  r=methods[k][rid];x['pending_records'][k]={key:r.get(key) for key in ['labels','dimension_reasons','material_issue','input_assessment','issue_reason','rationale','reference_frame','record_file'] if key in r}
 full.append(x)
for name,obj in [('pending_inventory.json',summary),('all_pending_reason_records.json',full),('machine_pending_packets.json',[{'inventory':next(x for x in full if x['id']==rid),'rule_input':ri[rid],'llm_input':li[rid]} for rid in sorted(mu)])]:
 with (O/name).open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({k:summary[k] for k in ['counts','machine_union_count','all_pending_union_count']},ensure_ascii=False))
print('intersections', {k:v['count'] for k,v in summary['pairwise_intersections'].items()},'all4',len(summary['all_four_intersection_ids']))
for x in full:
 if x['in_machine_pending_union']:print(x['id'],x['source_title'],x['pages'],x['text'])
