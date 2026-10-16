#!/usr/bin/env python3
"""Read-only incremental reception and fixed-snapshot arithmetic audit. No dispatch."""
import collections, datetime, hashlib, json, math, sys, types
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parents[1]
NEW = BASE/'06-coding/native-full4481-transport-recovery-v2-sol'
OLD = BASE/'06-coding/native-full4481-v1-sol'
SNAP = BASE/'07-statistics/original-whole-batch-native-snapshot-20261012T0008-root'
PREV = BASE/'07-statistics/original-whole-batch-native-snapshot-20261011T1515-root'
STAT = BASE/'07-statistics/current-v8-composite-machine-diagnostics-20261012T0012-root'
PREVSTAT = BASE/'07-statistics/current-v8-composite-machine-diagnostics-20261011-root'
OLD_AUDIT = BASE/'08-audits/native-recovery-v2-preflight-sol/collector-independent-audit-20261011-sol'
GUARD = BASE/'08-audits/native-recovery-v2-preflight-sol/strict_reception_guard.py'
DIMS = ('S','E','Ec','I','F')
INPUTS = {}
def bind(p):
    p=Path(p).resolve();r=p.read_bytes()
    return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def reg(p):
    x=bind(p);INPUTS.setdefault(x['path'],x);return x
def exact(x):
    a=reg(x['path']);assert a=={k:x[k] for k in ('path','bytes','sha256')},'bound bytes changed';return a
def pairs(xs):
    d={}
    for k,v in xs:
        assert k not in d,'duplicate key';d[k]=v
    return d
def loads(s):
    return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
def load(p):reg(p);return loads(Path(p).read_bytes())
def lines(p):reg(p);return [loads(x) for x in Path(p).read_bytes().splitlines()]
def save(n,x):
    with (HERE/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def seal_files(p):
    s=load(p)
    for x in s['files']:exact(x)
    return s
def ptr(x,s):
    for k in s[1:].split('/'):
        k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
    return x
def covers(intervals,n):
    cursor=0
    for a,b in sorted(intervals):
        if a>cursor:return False
        cursor=max(cursor,b)
    return cursor>=n
def counts(rows):
    out={d:collections.Counter(str(r['labels'][d]) for r in rows) for d in DIMS}
    return {'selected_record_N':len(rows),'binary_label_N':sum(c['0']+c['1'] for c in out.values()),
        'lawful_null_label_N':sum(c['None'] for c in out.values()),'missing_record_N':4481-len(rows),
        'missing_label_N':5*(4481-len(rows)),'record_output_coverage':len(rows)/4481,
        'complete_binary_record_N':sum(all(r['labels'][d] is not None for d in DIMS) for r in rows),
        'per_dimension':{d:{'positive_N':c['1'],'negative_N':c['0'],'lawful_null_N':c['None'],'missing_N':4481-len(rows)} for d,c in out.items()}}
def agreement(rule, rows):
    result={}
    for d in DIMS:
        c=collections.Counter((rule[r['id']]['labels'][d],r['labels'][d]) for r in rows
            if rule[r['id']]['labels'][d] is not None and r['labels'][d] is not None)
        a,b,c1,z=c[(1,1)],c[(0,1)],c[(1,0)],c[(0,0)];n=a+b+c1+z
        po=(a+z)/n;pe=((a+b)*(a+c1)+(z+b)*(z+c1))/(n*n)
        result[d]={'binary_pair_N':n,'native_output_N':len(rows),'native_missing_N':4481-len(rows),
            'both_1':a,'rule0_native1':b,'rule1_native0':c1,'both_0':z,'Po':po,'Pe':pe,
            'kappa':(po-pe)/(1-pe) if pe!=1 else None,
            'positive_agreement':2*a/(2*a+b+c1) if 2*a+b+c1 else None,
            'negative_agreement':2*z/(2*z+b+c1) if 2*z+b+c1 else None,'is_accuracy':False}
    return result

seal_files(OLD_AUDIT/'output-seal.json')
old_report=load(OLD_AUDIT/'report.json')
assert old_report['state']=='independent_full_snapshot_reconciliation_passed'
assert old_report['derived_counts']['selected_record_N']==2168
seal_files(PREV/'seal.json');seal_files(SNAP/'seal.json');seal_files(STAT/'seal.json');seal_files(PREVSTAT/'seal.json')
coverage=load(SNAP/'coverage.json');old_coverage=load(PREV/'coverage.json')
selections=load(SNAP/'selected-whole-batch-bindings.json');old_selections=load(PREV/'selected-whole-batch-bindings.json')
missing=load(SNAP/'missing-original-batches.json');assert load(SNAP/'packet-quote-issues.json')==[]
rows=lines(SNAP/'selected-records.jsonl');old_rows=lines(PREV/'selected-records.jsonl')
rowmap={r['id']:r for r in rows};oldmap={r['id']:r for r in old_rows}
assert len(rowmap)==len(rows)==2360 and len(oldmap)==2168
assert all(rowmap[s]==r for s,r in oldmap.items()),'prior frozen selected rows changed'
selectionmap={s['batch_id']:s for s in selections};oldselectionmap={s['batch_id']:s for s in old_selections}
assert all(selectionmap[s]==r for s,r in oldselectionmap.items()),'prior selected whole-batch binding changed'
added=[s for s in selections if s['batch_id'] not in oldselectionmap]
assert [s['batch_id'] for s in added]==[f'batch-{i:04}' for i in range(301,317)]
assert len(selections)==316 and len(added)==16
manifest=load(NEW/'manifest.json');original=load(OLD/'run-manifest.json')
for k in ('runner','cli_launcher','validator','instructions','transport_amendment'):exact(manifest[k])
for k in ('original_manifest','recovery_manifest','collector'):exact(coverage[k])
expected=load(exact(original['ordered_source_ids'])['path'])['approved_record_ids']
assert len(expected)==len(set(expected))==4481
assert [r['id'] for r in rows]==[s for s in expected if s in rowmap]
original_batches={x['batch_id']:x for x in original['batches']};recovery_batches={x['batch_id']:x for x in manifest['batches']}
assert {x['batch_id'] for x in missing}==set(original_batches)-set(selectionmap)
assert all(x['source_ids']==original_batches[x['batch_id']]['source_ids'] for x in missing)
assert len(missing)==188 and {s for x in missing for s in x['source_ids']}==set(expected)-set(rowmap)
derived=counts(rows)
for k,v in derived.items():assert coverage[k]==v,k
assert coverage['selected_batch_N']==316
assert coverage['missing_batch_states']==dict(collections.Counter(x['state'] for x in missing))=={'inflight':3,'not_dispatched':185}
assert coverage['actual_selected_modes']=={'optional_first_attempt_field_absent_batch_N':23,'original_batch_N':297,'original_record_N':2132,'transport_recovery_batch_N':19,'transport_recovery_record_N':228,'missing_batch_N':188}
for k in ('formal_validation_complete','full_corpus_complete','thin35_included','selection_by_semantic_metric','first_values_changed','provider_serving_model_independently_verified'):assert coverage[k] is False

profile=load(NEW/'ROOT-controller-v4-binding.json')
for k in ('controller','guard','capacity_sidecar','prepared_manifest'):exact(profile[k])
assert profile['actual_concurrency_cap']==3
execution=load(NEW/'execution-runs/20261011T150825641847Z/start.json')
for k in ('controller','strict_guard','capacity3_sidecar','manifest'):exact(execution[k])
assert execution['mode']=='remaining' and execution['concurrency']==3
assert execution['batch_ids']==[b['batch_id'] for b in manifest['batches']]
controller=Path(profile['controller']['path']).read_text()
assert "assert 1<=args.concurrency<=3" in controller and "ThreadPoolExecutor(max_workers=args.concurrency)" in controller
assert "--ephemeral" in controller and "features.multi_agent=false" in controller and "semantic_scores_not_selection_criteria" in controller
module=types.ModuleType('independent_read_only_guard');module.__file__=str(GUARD)
exec(compile(GUARD.read_bytes(),str(GUARD),'exec'),module.__dict__)
increment_receipts=[];events_audit=[];quotes_N=0;ranges_N=0;nonliteral=[];ordering=[];optional=[];intervals=[]
for selected in added:
    bid=selected['batch_id'];batch=recovery_batches[bid];assignment_path=Path(exact(batch['assignment'])['path'])
    assignment=load(assignment_path);old_assignment=load(exact(original_batches[bid]['assignment'])['path'])
    assert assignment['original_assignment_binding']==original_batches[bid]['assignment']
    for k in ('source_ids','packets','manual','execution_prompt','source_asset_bindings','context_unit'):
        assert assignment[k]==old_assignment[k],f'{bid} conceptual input {k} changed'
    oschema=load(exact(old_assignment['output_schema'])['path']);nschema=load(exact(assignment['output_schema'])['path'])
    oschema['properties']['run_id']['const']=nschema['properties']['run_id']['const'];oschema['properties']['scope']['const']=nschema['properties']['scope']['const']
    assert oschema==nschema,'schema change beyond new run_id/scope'
    selection=load(exact(selected['selection'])['path']);receipt=load(exact(selected['receipt'])['path'])
    first_path=Path(exact(selected['first'])['path']);first=load(first_path);slot=first_path.parent
    assert selection['attempt']==1 and receipt['attempt']==1 and slot.name=='attempt-0001'
    assert selection['first']==selected['first'] and selection['reception']==selected['receipt']
    assert selection['original_valid_results_never_overwritten'] is True and selection['semantic_scores_not_selection_criteria'] is True
    assert receipt['state']=='technical_valid_whole_batch' and receipt['reference_compared'] is False and receipt['first_or_labels_modified'] is False
    assert not (OLD/bid/'root-selection.json').exists(),'recovery overwrites valid original batch'
    strict=module.verify(NEW/'manifest.json',assignment_path,first_path,require_explicit_template_false=True)
    assert strict['first']==selected['first'] and strict['actor_seal']==receipt['actor_seal']
    assert strict['schema_validation']==receipt['validation']['schema_validation']
    seal=load(exact(strict['actor_seal'])['path']);exact(strict['report'])
    assert seal['run_id']==assignment['run_id'] and seal['batch_id']==bid and seal['template_only'] is False and seal['actual_completion_claimed'] is True
    for x in seal['actual_input_bindings']:exact(x)
    if 'attempt_number' not in first:optional.append(bid)
    else:assert first['attempt_number']==1
    dispatch=load(slot/'dispatch-start.json');process=load(slot/'process-completion.json')
    exact(dispatch['prompt']);exact(dispatch['assignment']);exact(process['events']);exact(process['stderr'])
    assert dispatch['run_id']==assignment['run_id'] and dispatch['batch_id']==bid and dispatch['attempt']==1
    assert dispatch['old_attempt_budget_not_modified'] is True
    argv=dispatch['argv'];assert str(Path(argv[0]).resolve())==manifest['cli_launcher']['path'] and '--ephemeral' in argv and '--ignore-user-config' in argv
    assert argv[argv.index('--model')+1]=='gpt-6.1-sol' and 'model_reasoning_effort="ultra"' in argv
    assert 'features.multi_agent=false' in argv and 'features.memories=false' in argv and 'web_search="disabled"' in argv and 'project_doc_max_bytes=0' in argv
    prompt_text=Path(dispatch['prompt']['path']).read_text();assert '实际并发始终不超过3' in prompt_text and '13容量计划已经撤回' in prompt_text
    assert process['actual_process_terminal'] is True and process['returncode']==0 and process['timed_out'] is False
    intervals.extend([(dispatch['at_utc'],1,bid),(process['at_utc'],-1,bid)])
    ev=lines(slot/'cli-events.jsonl')
    outs=[(i,e['item']) for i,e in enumerate(ev) if e['type']=='item.completed' and e.get('item',{}).get('type')=='command_execution']
    writers=[i for i,it in outs if 'first.json' in it.get('command','') and ("open('xb')" in it['command'] or 'open("xb")' in it['command'] or "open('x'" in it['command'])]
    assert writers,'first creation command not observable'
    writer_index=min(writers)
    writer_output=next(it['aggregated_output'] for i,it in outs if i==writer_index)
    assert selected['first']['sha256'] in writer_output,'first creation output hash differs from selected immutable bytes'
    readings=[(i,it) for i,it in outs if i<writer_index and it.get('exit_code')==0]
    file_results=[];required_entries=[]
    required_paths=[str(assignment_path),assignment['manual']['path'],assignment['execution_prompt']['path'],*[p['path'] for p in assignment['packets']]]
    for path in required_paths:
        reg(path);txt=Path(path).read_text();entries=[f for f in first['read_manifest']['files'] if f['path']==path]
        claimed=[r for f in entries for r in f['actual_presented_ranges'] if r['range_kind']=='unicode_code_points']
        assert covers([(r['start'],r['end']) for r in claimed],len(txt))
        checks=[]
        for r in claimed:
            literal=txt[r['start']:r['end']]
            matched=[(i,it['id']) for i,it in readings if literal in it.get('aggregated_output','') and (path in it.get('command','') or path in it.get('aggregated_output',''))]
            checks.append({'start':r['start'],'end':r['end'],'range_length':r['end']-r['start'],'event_refs':matched,'literal_present_in_pre_first_raw_event_output':bool(matched)})
            ranges_N+=1
            if not matched:nonliteral.append({'batch':bid,'path':path,'range':r})
        file_results.append({'path':path,'unicode_length':len(txt),'claimed_full_coverage':True,'range_checks':checks})
        found_indices=[min(i for i,_ in c['event_refs']) for c in checks if c['event_refs']]
        required_entries.append((path,max(found_indices,default=-1),min(found_indices,default=-1)))
    manual_prompt_done=max(last for path,last,first in required_entries if path in (assignment['manual']['path'],assignment['execution_prompt']['path']))
    packet_started=min(first for path,last,first in required_entries if path in {p['path'] for p in assignment['packets']})
    if packet_started<=manual_prompt_done:ordering.append(bid)
    for record,p in zip(first['records'],assignment['packets']):
        packet=load(exact(p)['path']);row=rowmap[record['source_id']]
        assert row['dimensions']==record['dimensions'] and row['first']==selected['first'] and row['technical_receipt']==selected['receipt']
        assert row['selection']==selected['selection'] and row['actor_seal']==strict['actor_seal'] and row['packet']=={k:p[k] for k in ('path','bytes','sha256')}
        for d,x in record['dimensions'].items():
            assert row['labels'][d]==x['value']
            if x['value'] is None:continue
            packet_evidence=[e for e in x['evidence'] if 'pointer' in e];assert packet_evidence
            for e in packet_evidence:
                assert e['quote'] and e['quote'] in ptr(packet,e['pointer'])
                assert (e['role']=='current')==(e['pointer']=='/source_bundle/source_record/text')
                quotes_N+=1
    events_audit.append({'batch_id':bid,'event_binding':reg(slot/'cli-events.jsonl'),'command_completed_N':len(outs),'first_creation_event_index':writer_index,'first_creation_output_hash_equals_selected':True,'broad_first_mentions_with_exclusive_writes_N':len(writers),'mandatory_text_files':file_results,
        'actor_presentation_notes':{k:v for k,v in first['read_manifest'].items() if k not in ('files','actor_id','run_id','batch_id')},
        'raw_event_output_is_not_independent_proof_of_provider_model_context_or_chunk_delivery':True})
    increment_receipts.append({'batch_id':bid,'selected_attempt':1,'record_N':len(first['records']),'strict_independent_result':strict,'dispatch':reg(slot/'dispatch-start.json'),'process':reg(slot/'process-completion.json')})
assert not nonliteral,'required literal range not observable in raw event outputs'
assert not ordering,'packets observed before complete manual/prompt'
assert len(optional)==16,'all16 first.attempt_number absent is optional under frozen schema'
concurrency=0;peak=0
for t,delta,bid in sorted(intervals,key=lambda x:(x[0],x[1])):
    concurrency+=delta;peak=max(peak,concurrency)
assert concurrency==0 and peak<=3

stats=load(STAT/'metrics.json');previous_stats=load(PREVSTAT/'metrics.json')
assert stats['native_coverage']==coverage;exact(stats['native_snapshot_seal']);exact(stats['calculator']);exact(stats['rule_seal']);exact(stats['rule_execution'])
assert stats['rule_seal']==previous_stats['rule_seal'],'rule composite changed between compared statistic snapshots'
rule_seal=load(stats['rule_seal']['path']);pred_binding=next(x for x in rule_seal['files'] if Path(x['path']).name=='predictions.jsonl');exact(pred_binding)
rule={r['id']:r for r in lines(pred_binding['path'])};assert len(rule)==4481
observed=agreement(rule,rows);assert observed==stats['machine_pair_agreement_not_accuracy']
same_rule_old2168=agreement(rule,old_rows)
previous_snapshot=Path(previous_stats['native_snapshot_seal']['path']).parent;seal_files(previous_snapshot/'seal.json')
previous_stat_rows=lines(previous_snapshot/'selected-records.jsonl');assert len(previous_stat_rows)==2276
assert all(rowmap[r['id']]==r for r in previous_stat_rows)
same_rule_old2276=agreement(rule,previous_stat_rows);assert same_rule_old2276==previous_stats['machine_pair_agreement_not_accuracy']
added_since_stat=[r for r in rows if r['id'] not in {x['id'] for x in previous_stat_rows}];assert len(added_since_stat)==84
disagreements=lines(STAT/'machine-pair-disagreements.jsonl')
expected_dis={(r['id'],d) for r in rows for d in DIMS if rule[r['id']]['labels'][d]!=r['labels'][d]}
assert len(disagreements)==len(expected_dis)==stats['machine_disagreement_including_null_N']==721
assert {(r['id'],r['dimension']) for r in disagreements}==expected_dis
for x in disagreements:
    assert x['rule']==rule[x['id']]['labels'][x['dimension']] and x['native']==rowmap[x['id']]['labels'][x['dimension']]
    assert x['not_adjudicated_truth'] is True
assert stats['formal_validation_complete'] is False and stats['paper_writing_gate_open'] is False
save('increment-strict-reception-audit.json',increment_receipts)
save('increment-actual-event-range-audit.json',events_audit)
save('four-grid-and-coverage-audit.json',{'new_counts':derived,'old2168_counts':counts(old_rows),'same_v8_rule_old2168_agreement':same_rule_old2168,
    'previous2276_agreement':same_rule_old2276,'new2360_agreement':observed,'added192_counts':counts([r for r in rows if r['id'] not in oldmap]),
    'added_since_previous_stats_N':84,'added_since_previous_stats_four_grids':agreement(rule,added_since_stat),
    'same_v8_rule_old2168_is_recomputed_comparator_not_historical_v7_metric':True,'agreement_is_not_accuracy':True})
report={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'pass_incremental_technical_reception_and_fixed_snapshot_statistics',
    'snapshot_at_utc':coverage['at_utc'],'statistics_at_utc':stats['at_utc'],'frozen_selected_record_N':2360,'selected_batch_N':316,
    'old300_audit_reused_with_identical_snapshot_rows_and_selection_bindings':True,'newly_independently_strict_checked_batch_N':16,
    'new_batch_ids':[x['batch_id'] for x in added],'new_record_N':192,'new_dimension_N':960,'new_lawful_null_N':0,
    'new_packet_literal_quote_N':quotes_N,'packet_quote_mismatch_N':0,'claimed_required_literal_range_checked_N':ranges_N,
    'mandatory_ranges_absent_from_raw_pre_first_output_N':0,'manual_prompt_before_packet_order_issue_N':0,
    'all16_explicit_seal_flags_present_and_exact':True,'optional_first_attempt_number_absent_new_batch_N':len(optional),
    'optional_field_absence_not_retry_reason':True,'selected_first_attempt_N':16,'new_completed_selected_process_overlap_peak':peak,
    'controller_frozen_hard_cap':3,'v2_prepared_capacity13_plan_retracted_by_sidecar_and_dispatch':True,
    'full_corpus_complete':False,'formal_validation_complete':False,'provider_serving_model_independently_verified':False,
    'actual_provider_model_context_or_chunk_delivery_independently_verified':False,
    'no_model_calls_or_dispatch_or_selection_changes':True,'thin35_and_manual77_not_in_strict_native_collection':True,
    'comparison_previous_stats_N':2276,'comparison_added_N':84,'pair_statistics_exact':True,'machine_disagreement_including_null_N':721,
    'input_file_N':len(INPUTS),'inputs_changed_during_audit':[]}
changed=[x for x in INPUTS.values() if bind(x['path'])!=x];assert not changed
save('input-bindings.json',{'files':list(INPUTS.values()),'file_N':len(INPUTS)})
save('report.json',report)
save('audit-preparation-observations.json',{'inspection_only_failure':'An exploratory read tried slicing read_manifest as a list; it is a dict. KeyError occurred before audit outputs. Corrected inspection used read_manifest.files. No classifier/receiver/model retry or source write occurred.','aggregate_tool_render_truncation':'Some exploratory large raw-event displays were truncated in this audit interface. Evidence checks were recovered as bounded summaries and full programmatic literal comparisons, without claiming full visual inspection of all event text.','audit_attempt01_failure':'Broad writer detection included later report/seal exclusive writes containing first binding. Preserved attempt01 and failure record; attempt02 uses earliest exclusive first creation command plus its exact final first SHA in successful output. This does not imply multiple first writes or justify a production retry.','writes_only_inside_this_directory':True})
table='\n'.join(f"|{d}|{v['binary_pair_N']}|{v['both_1']}|{v['rule0_native1']}|{v['rule1_native0']}|{v['both_0']}|{v['kappa']:.6f}|" for d,v in observed.items())
md=f'''# 固定2360条快照的增量独立核查\n\n通过本次增量技术接收与统计核查。2360/4481条、316原整批、39合法null，缺失2121条；全部仍非正式验证。新增0301–0316共16批192条/960维，均为恢复轮attempt1，严格schema、完整原成员/顺序、四个显式seal标志和真实输入/first/report/process/event字节绑定均通过。{quotes_N}条0/1 packet逐字证据无误差；新增无null。没有改选择、首答或值，没有调用模型。\n\n旧297原批及3恢复pilot的2168条复用已封印独立核查。新快照中这2168条的完整记录及300批选择绑定与旧快照相同；没有重复完整旧原件审计。原手册、execution prompt、packet及既定batch字节/顺序相同，schema仅run_id/scope取新恢复身份。first.attempt_number在新增16批均缺失，但原冻结schema可选；必需receipt、selection及真实attempt-0001路由相互一致，不应因此重试。\n\n继续控制器v4及本轮start记录绑定一致，实际固定3并发，CLI采用隔离0.162.1、fresh ephemeral、忽略用户配置、禁多代理/记忆/检索；请求gpt-6.1-sol/ultra。新16个已完成选择进程的时间重叠峰值{peak}。v2准备原字节中13计划保留，已由冻结sidecar和实际dispatch撤回；本审计没有把准备计划当作执行。后到317/318等不进入本2360固定快照。服务端实际模型身份仍未独立核实。\n\n核验{ranges_N}个申报范围的原文件片段，assignment、完整手册、prompt及192个完整packet的Unicode覆盖均能在first写入前的成功命令raw输出中逐字找到，手册/prompt完成顺序在packet前。演员记录的截断/补读等原说明完整保存在事件核查JSON。日志raw输出与read_manifest的对应可证明工具进程曾产生这些文本，不能独立证明服务端模型实际保留、收到全部工具片段或理解全部上下文；技术接收也不证明语义正确。未将未打开资产、schema紧凑呈现或演员自述包装为独立服务端实读证明。\n\n下表由同一封印v8兼容规则复合结果与固定2360个首答重新计算，逐项与ROOT统计完全相同。仅双侧二元进入四格，null和缺失不填0。\n\n|维度|二元对N|双方1|规则0/LLM1|规则1/LLM0|双方0|κ|\n|---|---:|---:|---:|---:|---:|---:|\n{table}\n\n相较上次封印统计2276条，此次仅增加84条；规则复合seal相同，旧2276条及值未变。与更早独立审计2168条相比增加192条、960二元，null保持39，覆盖从48.3821%至52.6668%。两种比较及各增量四格另存JSON；2168的同v8规则比较是本次重算基线，不能冒称历史v7统计。721个含null机器分歧清单身份和值已核对。κ及正类一致率衡量方法相似程度，不能称为正确率；现有77开发参照没有合入strict生产首答，新200正文未作为本技术核查材料读取。\n\n本结论可用于接受已收集原完整整批的运输/技术来源和该固定快照统计，支持保持v4合同继续运输。不能用于宣称全4481完成、正式独立验证通过、服务模型身份已核实或机器语义标签已核定。未发现要求撤销本次选择或技术重试的阻断问题；继续保留合法null及原失败记录。\n'''
with (HERE/'report.md').open('x',encoding='utf8') as f:f.write(md)
save('seal.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[bind(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='seal.json'],'self_excluded':True})
print(json.dumps({'report':str(HERE/'report.md'),'seal':bind(HERE/'seal.json'),'new_batch_N':16,'record_N':2360,'quote_N':quotes_N,'range_N':ranges_N,'state':report['state']},ensure_ascii=False))
