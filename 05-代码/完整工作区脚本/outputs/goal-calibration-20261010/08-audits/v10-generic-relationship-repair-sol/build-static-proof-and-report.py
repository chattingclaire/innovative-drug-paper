from pathlib import Path
import ast,json,hashlib,importlib.util,sys,datetime
sys.dont_write_bytecode=True
A=Path(__file__).resolve().parent;R=A.parents[1];V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-generic-relationship-sol';OLD=V.parent/'joint-v9-generic-relationship-sol';NAMES=['evidence','source_packet','source_receipts','relations','dimensions']
def bind(p):
 p=p.resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
spec=importlib.util.spec_from_file_location('selector_static_proof',V/'select_static_impact.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
oldspecs=[bind(OLD/(n+'.py')) for n in NAMES];newspecs=[bind(V/(n+'.py')) for n in NAMES];assert m.prove_code(oldspecs,newspecs)
# Full call closure, exact function binding and all explicit self writes.
tree=ast.parse((V/'relations.py').read_text());cl=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='RelationView');methods={x.name:x for x in cl.body if isinstance(x,ast.FunctionDef)};seen={}
def walk(name):
 if name in seen or name not in methods:return
 fn=methods[name];calls=sorted({x.func.attr for x in ast.walk(fn) if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and isinstance(x.func.value,ast.Name)and x.func.value.id=='self'});writes=[];mutators=[]
 for x in ast.walk(fn):
  if isinstance(x,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
   ts=x.targets if isinstance(x,ast.Assign)else[x.target]
   for t in ts:
    if isinstance(t,ast.Attribute)and isinstance(t.value,ast.Name)and t.value.id=='self':writes.append(t.attr)
  if isinstance(x,ast.Call)and isinstance(x.func,ast.Attribute)and isinstance(x.func.value,ast.Attribute)and isinstance(x.func.value.value,ast.Name)and x.func.value.value.id=='self':mutators.append({'attribute':x.func.value.attr,'method':x.func.attr})
 seen[name]={'line':fn.lineno,'source_sha256':hashlib.sha256(ast.get_source_segment((V/'relations.py').read_text(),fn).encode()).hexdigest(),'calls':calls,'self_attribute_assignments':writes,'self_attribute_method_calls':mutators}
 for n in calls:walk(n)
walk('_v10_bounded_relationships')
allowed={'_add':{'source_relation_traces'}}
for n,row in seen.items():
 assert set(row['self_attribute_assignments'])<=allowed.get(n,set()),(n,row)
 assert all(x['method'] in {'get','rstrip','strip','split'} or (x['attribute']=='relations' and x['method']=='append') for x in row['self_attribute_method_calls']),(n,row)
# Fixed export/source equality of entry constants and full guard positions.
gatespec=importlib.util.spec_from_file_location('static_export',V/'static_gate.py');g=importlib.util.module_from_spec(gatespec);gatespec.loader.exec_module(g)
assert g.V10_REPAIR_ENTRY==m.V10_REPAIR_ENTRY
for n in NAMES:assert (V/(n+'.py')).read_bytes()==(A/'attempt02-controls/code-snapshot'/(n+'.py')).read_bytes()
proof={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'old_modules':oldspecs,'candidate_modules':newspecs,'unchanged_evidence_packet_receipts_bytes':True,'strip_only_v10_restores_exact_v9_AST':True,'constructor_last_guard_exact':True,'consumer_guard_before_finish_exact':True,'new_builder_first_statement_guard':ast.dump(methods['_v10_bounded_relationships'].body[0],include_attributes=False),'normalized_gate_source_and_selector_and_export_identical':True,'call_closure':seen,'old_shared_methods_only_quote_geometry_lookup_and_add':True,'new_relation_kind':'v10_IF_relationship','old_units_enumerates_fixed_kinds':['parent_predicate','substantive_list','cited_standard','named_mechanism','policy_explanation','price_arrangement'],'old_object_evidence_reads_only_parent_anaphor_kinds':True,'new_accumulator_consumer_only_validated_nonempty_IF_subset':True,'final_five_module_bytes_equal_latest_executed_snapshot':True,'author_static_body_review_only_not_independent_approval':True}
save(A/'ast-isolation-proof.json',proof)
(A/'side-effect-contract.md').write_text('新增 guard 在 RelationView 构造器的冻结 v9 尾部之后；新 builder 的首个可执行语句再次 gate，judge 的 v9 消费者之后、finish 之前只经同一 gate 调用 v10 消费者。静态 selector 与 static_gate.py 的模式、NFKC/CJK 空白规范化和源码入口完全一致。gate 为 false 时没有新增 helper 调用，因而没有新关系、请求、来源事件、receipt 或 decision 变化。新函数/常量/纯 import 无 eager defaults、装饰器、全局缓存、I/O 或动态执行。\n\n新增关系只能通过 _v10_emit→_add 写入 relations 与 source_relation_traces；_add 的上下文引文及 used_views 是旧只读 _quote/context_anchor/_used_views 链。所有新增 builder 和调用的旧几何/current/closed programme helper 是只读或局部容器写入；完整调用树和原函数 sha 位于 ast-isolation-proof.json。没有写入 unit、contexts、by_id、origins、material_requests、source_requests、source_view_events、_read_keys 或 primary cache。\n\n旧 _units 只消费六个固定 kind；object_evidence 只使用原 parent/anaphor 路径，均不能看到 v10_IF_relationship。v9 显式消费者只枚举 v9_IF_relationship，仍按原逻辑运行。新消费者在全旧路径之后对合法非空去重 I/F 子集调用原 acc.add，不添加 S/E/Ec 候选、不撤销旧依据、不改原 exclusions、requests 或边界。因此即使 gate 内 records，S/E/Ec 完整 decision 也必须逐字相同。进入 gate 不能据关键词判断为1；每个 builder 仍独立核操作谓词、对象、条件、同阶段服务与有限治理边。\n\n入口闭包：全部 records 只由当前 normalized text 的静态 gate 提名；语境、定义、完整工作方案/条文、正例及 null 的其他单位在进入 gate 后才能被新机制消费。因此无需按当前机器0/native1、开发ID或某个语境关键词筛选。所有 gate 内记录的全部旧/新 units 和全部依据链必须实际重算；未进 gate 且 baseline/wrapper 完整性成立的记录可复用。输入或代码绑定、静态 body 证明、生产 caller/receipt wrapper 或 baseline 完整性不成立则不准局部复用，保守全4481 fallback。\n\n作者未执行全4481 selector 或 classifier。作者契约 approved=false，ROOT/A 必须以独立封存审核及实际 v9 全量 baseline 机械证明决定是否认可部分闭包。\n')
results=json.loads((A/'attempt02-controls/results.json').read_bytes());summary=json.loads((A/'attempt02-controls/summary.json').read_bytes())
failed=[{'name':c['name'],'expected':c['expected'],'actual':c.get('actual'),'baseline':{d:c['old_values'][d] for d in c['expected']},'reason':('01402 原冻结投影缺少所需持有人对象；本轮明确不消费补材，材料变更需独立路径。' if c['name']=='RECODE25-01402/I' else '原句要求比较完全应答率，手册支持E=1；旧E内容匹配遗漏该指标，v8/v9继承未修，本轮IF隔离保留。')} for c in results if c['hard_assertion']and not c['passed']]
save(A/'remaining-hard-failures.json',failed)
seven=[]
for i,d in [('00093','F'),('00381','I'),('00649','I'),('01382','I'),('01731','I'),('01743','I'),('01757','I')]:
 c=next(x for x in results if x['name']==f'RECODE25-{i}/{d}');q=c['candidate']['decisions'][d];seven.append({'name':c['name'],'fixed_expected':c['expected'],'actual':c['actual'],'old_value':c['old_values'][d],'new_basis_path':q['basis_path'],'current_anchor':q['current_anchor'],'literal_context_evidence':q['context_evidence'],'role_receipt':q['details'],'packet_binding':c['packet_binding'],'status':'development evidence closure only; not gold or formal accuracy'})
save(A/'seven-current-relationship-evidence.json',seven)
attempts=[]
for p in sorted(A.glob('attempt*-controls')):
 attempts.append({'directory':str(p),'summary':json.loads((p/'summary.json').read_bytes()),'seal':bind(p/'output-seal.json'),'all_failure_records_retained':True})
save(A/'all-attempts-report.json',{'actual_local_candidate_control_executions':len(attempts),'maximum_authorized':3,'no_other_classifier_or_model_call':True,'attempts':attempts})
print(json.dumps({'AST_exact_v9_restore':True,'call_closure_N':len(seen),'final_code_exact_latest_run':True,'actual_attempts':len(attempts),'hard_failed_N':summary['hard_failed_N']},ensure_ascii=False))
