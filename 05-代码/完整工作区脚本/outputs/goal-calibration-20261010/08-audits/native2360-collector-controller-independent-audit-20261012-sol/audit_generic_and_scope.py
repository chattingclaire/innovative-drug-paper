#!/usr/bin/env python3
"""Supplement to sealed incremental audit. No classification or source mutation."""
import ast, csv, datetime, hashlib, json
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1]
OUT=HERE/'supplement-generic-and-reading-scope';OUT.mkdir()
INPUTS={}
def bind(p):
    p=Path(p).resolve();r=p.read_bytes();return {'path':str(p),'bytes':len(r),'sha256':hashlib.sha256(r).hexdigest()}
def reg(p):
    x=bind(p);INPUTS[x['path']]=x;return x
def load(p):reg(p);return json.loads(Path(p).read_bytes())
def exact(x):assert reg(x['path'])=={k:x[k] for k in ('path','bytes','sha256')}
def save(n,x):
    with (OUT/n).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def outputs(p):
    x=load(p)
    for b in x['files']:exact(b)
    return x
original_audit_seal=reg(HERE/'seal.json');outputs(HERE/'seal.json')
proof=load(BASE/'08-audits/generic-composite-statistical-adapter-preparation-20261012-root.json')
equivalence=load(BASE/'08-audits/generic-composite-statistical-equivalence-20261012-root.json')
for k in ('old_verified_calculator','generic_calculator'):exact(proof[k])
for k in ('old_result','generic_result'):exact(equivalence[k])
old_script=Path(proof['old_verified_calculator']['path']);new_script=Path(proof['generic_calculator']['path'])
oldtree=ast.parse(old_script.read_text());newtree=ast.parse(new_script.read_text())
oldfunc={n.name:n for n in oldtree.body if isinstance(n,ast.FunctionDef)};newfunc={n.name:n for n in newtree.body if isinstance(n,ast.FunctionDef)}
same={name:ast.dump(node,include_attributes=False)==ast.dump(newfunc[name],include_attributes=False) for name,node in oldfunc.items() if name!='main'}
assert len(same)==10 and all(same.values()) and set(same)==set(proof['unchanged_AST_functions'])
newfunctions=set(newfunc)-set(oldfunc);assert newfunctions=={'verify_composite_seal','verify_prediction_origins'}
def assignments(tree):
    return {n.targets[0].id:ast.dump(n.value,include_attributes=False) for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.targets[0],ast.Name)}
oldassign=assignments(oldtree);newassign=assignments(newtree)
for name in ('ROOT','DIMS','OLD','EXPECTED_SHA'):assert oldassign[name]==newassign[name]
old_metrics=load(equivalence['old_result']['path']);new_metrics=load(equivalence['generic_result']['path'])
old_dir=Path(equivalence['old_result']['path']).parent;new_dir=Path(equivalence['generic_result']['path']).parent
outputs(old_dir/'seal.json');outputs(new_dir/'seal.json')
normalized=dict(new_metrics)
normalized['old_v5_to_v8_composite_changed_label_N']=normalized.pop('old_v5_to_current_composite_changed_label_N')
normalized['old_v5_to_v8_composite_transitions']=normalized.pop('old_v5_to_current_composite_transitions')
allowed_changed={'at_utc','identity','calculator'}
differences={k:{'old':old_metrics.get(k),'new':normalized.get(k)} for k in set(old_metrics)|set(normalized) if old_metrics.get(k)!=normalized.get(k)}
assert set(differences)==allowed_changed
old_csv=old_dir/'development77-comparison.csv';new_csv=new_dir/'development77-comparison.csv'
reg(old_csv);reg(new_csv)
old_rows=list(csv.reader(old_csv.open(encoding='utf-8-sig')));new_rows=list(csv.reader(new_csv.open(encoding='utf-8-sig')))
assert len(old_rows)==len(new_rows)==386 and old_rows[1:]==new_rows[1:]
assert old_rows[0][:4]==new_rows[0][:4] and old_rows[0][5:]==new_rows[0][5:]
assert old_rows[0][4]=='rules_v8_compatible_composite' and new_rows[0][4]=='rules_current_compatible_composite'
same_outputs=[]
for old_name,new_name in [('machine-pair-disagreements.jsonl','machine-pair-disagreements.jsonl'),('old-v5-to-v8-composite-label-changes.jsonl','old-v5-to-current-composite-label-changes.jsonl')]:
    o=reg(old_dir/old_name);n=reg(new_dir/new_name)
    assert o['sha256']==n['sha256'] and o['bytes']==n['bytes'];same_outputs.append({'old':o,'new':n,'identical_bytes':True})
for key in ('rule_execution','rule_seal','native_snapshot_seal','reference_bindings','old_v5_predictions'):
    assert old_metrics[key]==new_metrics[key]
assert new_metrics['native_coverage']['selected_record_N']==2360
assert new_metrics['formal_validation_complete'] is False and new_metrics['paper_writing_gate_open'] is False

# Metadata-only exclusion-chain clarification; never open human200 workbooks.
draw=load(BASE/'09-delivery/human200-independent-preparation-root/coordinator-private/draw-and-mapping.json')
old_selection=load(BASE/'07-statistics/original-whole-batch-native-snapshot-20261011T1515-root/selected-whole-batch-bindings.json')
new_selection=load(BASE/'07-statistics/original-whole-batch-native-snapshot-20261012T0008-root/selected-whole-batch-bindings.json')
old_batches={x['batch_id'] for x in old_selection};added_ids={s for x in new_selection if x['batch_id'] not in old_batches for s in x['source_ids']}
overlap=sorted(added_ids&set(draw['source_ids_sorted']));assert len(overlap)==7
scope={'reading_purpose':'Frozen whole-batch technical provenance, literal packet evidence and arithmetic only; no semantic coding of human200 or remaining.',
    'new192_production_ids_also_human200_allocated_N':len(overlap),'overlap_source_ids':overlap,
    'production_packet_bytes_programmatically_loaded_for_strict_receiver_and_literal_comparison':True,
    'human200_workbook_or_answers_opened':False,'human200_semantic_diagnosis_or_new_label_assignment_performed':False,
    'claim_packet_text_never_read_at_program_level':False,
    'correction_to_original_report_md':'The sentence 新200正文未作为本技术核查材料读取 is too broad. The technical receiver necessarily loaded all192 production packets, including these7. No human200 workbook/answers were opened and none of those7 was semantically reviewed, scored or added to the130 semantic selection. Do not cite the old sentence as a no-packet-read assertion.',
    'original_130_40_90_semantic_seals_unchanged_and_human200_excluded':True,
    'root_message_percentage_correction':'An interim message erroneously said51.27%; 2276/4481 is50.7922%, 2360/4481 is52.6668%, 2168/4481 is48.3821%. The sealed numeric JSON used exact counts.'}
result={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'state':'pass_same_inputs_generic_statistical_equivalence',
    'unchanged_AST_functions':same,'statistical_and_reference_functions_AST_identical':True,'new_functions':sorted(newfunctions),
    'metric_differences_after_transition_key_normalization':differences,'statistical_value_difference_N':0,
    'same385_reference_comparison_rows':True,'same_machine_disagreement_and_label_change_bytes':same_outputs,
    'same_rule_and_native_snapshot_input_seals':True,'classification_runs_by_auditor':0,
    'changes':'--rule-composite replaces hardcodedv8 path; recursive input/output ancestor seal checks; each actual prediction line matches lineage ordinal/id/bytes/SHA/decisions; neutral version field names/descriptions. No formula change.',
    'limitation':'The calculator verifies bindings and line identity; it cannot establish semantic validity or impact-closure legitimacy by itself. Each future composite still needs its separately frozen adoption/impact-closure proof and honest actual inference origins. It does not mean all4481 were inferred under the new version.',
    'original_increment_audit_seal':original_audit_seal,'reading_scope_correction':scope}
save('report.json',result);save('input-bindings.json',{'files':list(INPUTS.values())})
text='''# 参数化统计器与阅读范围补充\n\n同一v8规则复合结果、同一2360原完整整批LLM快照下，新通用统计器与原统计器的统计值0差异。10个原辅助函数（包括metrics/reference/directed）AST全部相同；385行参照比较数据一致；机器分歧和原v5标签迁移清单原字节相同。统计JSON仅时间、版本中性描述、calculator绑定及迁移字段名称不同。没有重跑分类器或调用模型。\n\n接口从硬编码v8目录变为--rule-composite。新增递归封印核验及4481条预测行的序号、ID、字节数、SHA、决策和值一致检查，仍要求完整4481/22405及技术失败0。此入口自身不能证明语义正确或局部影响闭包充分；以后版本仍需独立封印采用依据、影响闭包及每条真实执行来源，不能把复用结果声称为新版本全量重算。\n\n需更正初版report.md一句：新增192个生产packet的技术接收确实在程序中载入全文以验证schema、绑定与逐字证据，其中7个source_id与human200抽样重叠（只用coordinator元数据识别）。因此不能说其正文在程序层面完全未读取。没有打开human200工作簿或真人答案，没有对这7条作语义审查、评分、分类或增加新标签；原130语义审查仍排除全部human200。该技术接收范围是本轮新增16完整batch，不是扩大语义开发范围。原审计封印保持不变，应同时引用本更正。\n\n仍通过2360固定快照的增量技术接收和统计核验；未发现要求重试或撤销选择的阻断。日志raw范围可对应产生文本，但模型实际完整上下文、provider服务身份与语义正确性仍未独立证明。coverage为2360/4481=52.6668%，39合法null、2121缺失、正式验证false。\n'''
with (OUT/'report.md').open('x',encoding='utf8') as f:f.write(text)
changed=[x for x in INPUTS.values() if bind(x['path'])!=x];assert not changed
save('seal.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':[bind(p) for p in sorted(OUT.iterdir()) if p.is_file()],'self_excluded':True})
print(json.dumps({'supplement':str(OUT),'seal':bind(OUT/'seal.json'),'statistical_difference_N':0,'reading_scope_overlap_N':7},ensure_ascii=False))
