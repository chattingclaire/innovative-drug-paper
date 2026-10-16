import json,pathlib,hashlib,collections,re
ROOT=pathlib.Path(__file__).resolve().parents[2];OUT=pathlib.Path(__file__).resolve().parent
def read(p):return json.loads(pathlib.Path(p).read_text())
def rows(p):return [json.loads(x) for x in pathlib.Path(p).read_text().splitlines()]
def bind(p):
 p=pathlib.Path(p);return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
def save(n,v):(OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2))
prod=ROOT/'06-coding/rule-full4481-v2-root/run4481-first'
cal=ROOT/'06-coding/rule-v19-v15-development77-first-sol/versions/v4/run77-first'
fr=read(prod/'freeze.json');fc=read(cal/'freeze.json')
hashchecks=[]
for b in fr['implementation_files']:
 x=bind(b['path']);x['bound_sha256']=b['sha256'];x['verified']=x['sha256']==x['bound_sha256'];assert x['verified'];hashchecks.append(x)
pc={pathlib.Path(b['path']).name:b for b in fr['implementation_files']}
cc={pathlib.Path(b['path']).name:b for b in fc['implementation_files']}
semantic_names=['source_packet.py','source_receipts.py','evidence.py','relations.py','dimensions.py']
same_semantic={n:pc[n]['sha256']==cc[n]['sha256'] for n in semantic_names};assert all(same_semantic.values())
pr={r['id']:r for r in rows(prod/'predictions.jsonl')};cr={r['id']:r for r in rows(cal/'predictions.jsonl')}
pd={r['source_record']['id']:r for r in rows(prod/'delivered-complete-source-bundles.jsonl')}
cd={r['source_record']['id']:r for r in rows(cal/'delivered-complete-source-bundles.jsonl')}
assert len(pr)==len(pd)==4481 and len(cr)==len(cd)==77
same77_labels=all(pr[i]['labels']==cr[i]['labels'] for i in cr)
same77_inputs=all(pd[i]==cd[i] for i in cd)
issued=ROOT/'09-delivery/独立真人判读-200条-20261013/管理员留存-勿发编码者'
draw=read(issued/'draw.json');freeze=read(issued/'sampling-freeze.json');blind=read(issued/'blind-assignment.json')
h=read(ROOT/'09-delivery/真人核验确认-200条-20261013/真人核验结果.json')
hum={r['unit_id']:r for r in h['records']};sample={r['unit_id'] for r in draw['records']}
assert sample==set(hum) and len(sample)==200
blind_checks={}
for m in ['A','B']:
 mapping={r['unit_id']:r['original_blind_id'] for r in blind['methods'][m]}
 blind_checks[m]=all(hum[i][m+'_id']==mapping[i] for i in sample)
 assert blind_checks[m]
llm={r['id']:r for r in rows(ROOT/'07-statistics/original-whole-batch-native-full4481-cap13-root/selected-records.jsonl')}
same200_inputs=all(pd[i]==read(llm[i]['packet']['path'])['source_bundle'] for i in sample)
assert same77_labels and same77_inputs and same200_inputs
remaining={i for s in freeze['strata'] for i in s['member_ids']};excluded=set(freeze['excluded_source_ids'])
assert not remaining & excluded and remaining|excluded==set(pr)
def count(ids):return {d:{str(k):v for k,v in collections.Counter(pr[i]['labels'][d] for i in ids).items()} for d in ['I','F']}
frame_counts={name:{'N':len(ids),'counts':count(ids)} for name,ids in [('calibration77',set(cr)),('remaining1151',remaining),('excluded3330',excluded),('independent200',sample),('full4481',set(pr))]}
sample_cells={}
for d in ['I','F']:
 c=collections.Counter();null=[]
 for i in sample:
  p=pr[i]['labels'][d];v=hum[i]['judgments'][d]['value']
  if p is None:null.append({'id':i,'human_value':v});continue
  c[{(1,1):'TP',(1,0):'FP',(0,1):'FN',(0,0):'TN'}[(p,v)]]+=1
 sample_cells[d]={'cells':{k:c[k] for k in ['TP','FP','FN','TN']},'NULL':null,'human_positive_total':sum(hum[i]['judgments'][d]['value'] for i in sample)}
execution=read(prod/'execution.json')
badreads=[p for p in execution['read_paths'] if pathlib.Path(p).name=='reference.jsonl' or '/04-calibration/' in p]
literal_id_hits={}
for n in semantic_names+['rule_driver.py','interface_common.py']:
 text=pathlib.Path(pc[n]['path']).read_text();hits=[{'line':i,'text':l} for i,l in enumerate(text.splitlines(),1) if re.search(r'RECODE25-\d{5}',l)]
 literal_id_hits[n]=hits
report={'date':'2026-10-14','source_prediction_binding':bind(prod/'predictions.jsonl'),'bound_code_checks':hashchecks,
 'semantic_modules_same_as_calibration77':same_semantic,'same77_prediction_values':same77_labels,'same77_complete_input_bundles':same77_inputs,
 'sample200_old_rule_input_equal_old_LLM_packet':same200_inputs,'sample200_unique_IDs_and_human_IDs_match':True,'blind_A_B_ID_mapping_matches':blind_checks,
 'original77_sample_overlap_N':len(set(cr)&sample),'frame_counts':frame_counts,'sample_cells':sample_cells,
 'all_old_positive_I_ids_within_excluded3330':all(i in excluded for i,r in pr.items() if r['labels']['I']==1),
 'all_old_positive_F_ids_within_excluded3330':all(i in excluded for i,r in pr.items() if r['labels']['F']==1),
 'runtime_claim_no_reference_read':execution['no_reference_read'],'reference_reads_observed_in_runtime_log':badreads,'literal_RECODE25_IDs_in_inference_source':literal_id_hits,
 'interpretation_no_override':'现存绑定代码、驱动数据流、日志和11条确定性复现未发现按行政ID回填人工答案；不据此声称所有历史开发从未利用人工信息。冻结文件明确calibration_labels_already_disclosed=true。',
 'small_deterministic_reexecution_N':11,'full_run_performed':False,'rule_or_source_labels_modified':False,
 'human_identity':'按用户纠正认定200为独立真人检验；历史文件相冲突来源描述不采用',
 'sampling_note':'后续剩余框排除已登记开发材料及其既定文本家族；P层以较新规则/LLM任一I/F=1辅助分层。旧版本回溯比较仍按ID对齐，但这个框不是旧4481总体的随机缩影。',
 'bounds':'代码和输入未错配，不代表手册定义全部无争议；本次针对I/F的有限实现追踪，不重新裁定所有人工标签。'}
save('绑定映射与抽样框核查.json',report)
print(json.dumps({k:report[k] for k in ['semantic_modules_same_as_calibration77','same77_prediction_values','same77_complete_input_bundles','sample200_old_rule_input_equal_old_LLM_packet','blind_A_B_ID_mapping_matches','frame_counts','sample_cells']},ensure_ascii=False,indent=2))
