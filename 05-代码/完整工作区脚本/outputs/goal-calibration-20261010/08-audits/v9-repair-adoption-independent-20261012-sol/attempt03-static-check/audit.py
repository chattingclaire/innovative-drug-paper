"""Independent read-only AST/evidence readback. Never imports a classifier."""
from pathlib import Path
import ast, copy, hashlib, json, datetime

G=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
C=G/'06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol'
A=C/'attempt03-frozen-controls'
OLD=G/'06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol'
MODULES=['evidence','source_packet','source_receipts','relations','dimensions']
inputs={}
def bind(p):
    p=Path(p).resolve(); b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):
    q=bind(p); inputs[q['path']]=q; return Path(p).read_bytes()
def data(p): return json.loads(read(p))
def dump(n): return ast.dump(n,include_attributes=False)
def verify(s):
    got=bind(s['path']); inputs[got['path']]=got
    assert all(got[k]==s[k] for k in ['path','bytes','sha256']),s['path']
def write(name,value):
    p=OUT/name
    assert not p.exists(),str(p)
    p.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

sealed=data(A/'output-seal.json')
members=sealed.get('files',sealed.get('outputs',sealed.get('members')))
assert isinstance(members,list)
for s in members: verify(s)
pre=data(A/'pre-execution-seal.json')
for key in ['controls','candidate_modules','old_modules','baseline_modules','code_snapshot']:
    for s in pre.get(key,[]): verify(s)
summary=data(A/'summary.json')
results=data(A/'results.json')
assert len(results)==summary['case_N']
failures=[r for r in results if not r.get('passed')]
assert len(failures)==summary['failed_N']
assert all(r['SEEc_complete_decisions_equal'] for r in results)
for r in results:
    if r.get('gate_outside_complete_decisions_equal') is not None:
        assert r['gate_outside_complete_decisions_equal']

inventory=[]; proof=[]; gate_values=[]
for name in MODULES:
    b=read(OLD/(name+'.py')); a=read(A/'code-snapshot'/(name+'.py'))
    if name not in ['relations','dimensions']:
        assert b==a
        proof.append({'module':name,'byte_identical':True})
        continue
    before=ast.parse(b); after=ast.parse(a)
    tree=copy.deepcopy(after); new=[]; guards=[]; retained=[]
    for node in tree.body:
        if isinstance(node,ast.Assign) and len(node.targets)==1 and isinstance(node.targets[0],ast.Name) and node.targets[0].id=='V9_REPAIR_ENTRY':
            gate_values.append(ast.literal_eval(node.value)); continue
        if isinstance(node,ast.FunctionDef) and node.name.startswith('_v9_'):
            new.append(node); continue
        if name=='relations' and isinstance(node,ast.ClassDef) and node.name=='RelationView':
            old_members=[]
            for method in node.body:
                if isinstance(method,ast.FunctionDef) and method.name.startswith('_v9_'):
                    new.append(method); continue
                if isinstance(method,ast.FunctionDef) and method.name=='__init__':
                    expected=ast.parse('if _v9_repair_gate(self.norm):\n self._v9_bounded_relationships()').body[0]
                    assert dump(method.body[-1])==dump(expected)
                    guards.append({'caller':'RelationView.__init__','last_statement':True})
                    method.body.pop()
                old_members.append(method)
            node.body=old_members
        if name=='dimensions' and isinstance(node,ast.FunctionDef) and node.name=='judge':
            expected=ast.parse('if _v9_repair_gate(view.norm):\n _v9_IF_consume(acc, view)').body[0]
            matches=[i for i,q in enumerate(node.body) if dump(q)==dump(expected)]
            assert len(matches)==1
            i=matches[0]
            assert dump(node.body[i+1])==dump(ast.parse('decisions=acc.finish()').body[0])
            guards.append({'caller':'judge','immediately_before_finish':True})
            node.body.pop(i)
        retained.append(node)
    tree.body=retained
    assert len(guards)==1
    assert dump(before)==dump(tree),name+' old AST differs'
    expected_gate=ast.parse('def _v9_repair_gate(text):\n return bool(re.search(V9_REPAIR_ENTRY, text))').body[0]
    assert len([q for q in new if q.name=='_v9_repair_gate' and dump(q)==dump(expected_gate)])==1
    for n in new:
        assert not n.decorator_list
        assert not any(isinstance(x,(ast.Global,ast.Nonlocal,ast.Import,ast.ImportFrom)) for x in ast.walk(n))
        for default in n.args.defaults+[x for x in n.args.kw_defaults if x is not None]:
            assert not any(isinstance(x,ast.Call) for x in ast.walk(default))
        calls=sorted({ast.unparse(x.func) for x in ast.walk(n) if isinstance(x,ast.Call)})
        assert not any(q in {'eval','exec','open','globals','locals','setattr','delattr','__import__','compile'} for q in calls)
        mutations=[]
        for x in ast.walk(n):
            if isinstance(x,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
                targets=x.targets if isinstance(x,ast.Assign) else [x.target]
                mutations += [ast.unparse(q) for q in targets if isinstance(q,(ast.Attribute,ast.Subscript))]
        inventory.append({'module':name,'function':n.name,'line':n.lineno,'calls':calls,'attribute_or_subscript_writes':mutations})
    proof.append({'module':name,'old_AST_identical_after_exact_extension_removal':True,'new_function_N':len(new),'guard':guards[0]})
assert len(gate_values)==2 and gate_values[0]==gate_values[1]

focus_names={'RECODE25-01391/I','RECODE25-01430/I','RECODE25-01435/I','RECODE25-01436/I','RECODE25-02229/I','RECODE25-02235/I','RECODE25-01482/F','mixed_self_data_and_innovator_reliance','negative_identity_advantage_opportunity','named_other_beneficiary_no_keyword'}
focus=[]
for r in results:
    if r['name'] not in focus_names: continue
    focus.append({'name':r['name'],'expected_development_only':r['expected'],'old_values':r['old_values'],'new_values':r['new_values'],'passed':r['passed'],
                  'new_relationship_paths':[q['details']['v9_semantic_path'] for q in r['candidate']['relations'] if q['kind']=='v9_IF_relationship']})
write('ast-restoration-and-new-body-inventory.json',{'proof':proof,'frozen_gate':gate_values[0],'new_body_inventory':inventory})
write('finite-controls-readback.json',{'case_N':len(results),'hard_assertion_N':summary['hard_assertion_case_N'],'pending_N':summary['pending_N'],'hard_passed_N':summary.get('hard_passed_N'),'hard_failed_N':summary.get('hard_failed_N'),'all_failed_cases':summary['all_failures'],'focus':focus,'SEEc_complete_decisions_all_equal':True,'outside_gate_reported_controls_all_equal':True,'not_gold_or_accuracy':True,'classifier_executed_by_this_auditor':False})
report={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'intermediate_sealed_attempt03_readback_not_final_candidate_adoption',
        'candidate_final_adoption_approved':False,'selector_contract_approved':False,'scope_proof':'All additions consist of literal gate, new definitions and one guarded call in each changed module. Removing exactly those restores v8 AST; three other modules are byte identical. Outside current gate therefore has the prior behavior for unchanged packet, adapters and wrapper.',
        'mutation_review':'Relations new bodies call _add only through _v9_emit with new kind v9_IF_relationship. _add appends this relation and relation traces; current contexts, by_id, packet, material/source requests are not modified. Existing _units consumes six fixed old kinds, excluding this new kind. New dimension bodies mutate record-local I/F positive lists and I/F exclusions or use acc.add/boundary only for I/F; there is no new S/E/Ec predicate mutation.',
        'remaining_obligations':['Wait for final candidate source/delivery seal and bind this proof to its actual bytes; this proof binds attempt03 snapshot only.','New _v9_supplied_qualification_parent currently needs a proven current-to-parent governing edge; same source/component alone is not a direct-predicate proof, especially missing-current fallback.','Preserve all 36 hard failures and 15 pending cases; do not report all fixed controls passed. A failed synthetic E expectation is in unchanged old E, not a v9 change.','Check final selector constant/current normalization equals both guarded callers and old evidence matching_view. ROOT alone executes full static selection and classifier.'],
        'semantic_limits':'The frozen 130 are exposed development disagreements and the audit positions are AI semantic diagnostics, not human adjudication or independent accuracy. Unproved mother object/stage intersections and recorded boundaries remain pending. I is innovation; Ec is economics.',
        'read_scope':'No new packet opened during this phase. Candidate attempt result metadata parsed for all181 cases; substantive candidate/old decision quotations inspected only for seven previously opened focused records plus fixed synthetic controls. No external source file cited in those results was opened. No human200/remaining body/reference read.',
        'machine_or_reference_files_modified':False,'whole_population_classifier_run':False,'formal_validation_passed':False,'paper_final_acceptance':False}
write('report.json',report)
md='''# v9 第三轮候选独立静态读回

本报告绑定已封存 attempt03，尚不批准最终候选采用或静态选择契约。审计没有运行分类器，也没有打开新增原包、200或remaining正文。

五模块中三个字节不变；另外两个仅删除新增定义、入口常量与各一处准确受控调用，即恢复旧v8的完整AST。新关系只进入独占kind及trace，旧六种unit入口不消费它；新增消费者只改变记录内I/F候选与边界。因此，入口外等价证明可成立，但须绑定最终源码、相同原包及封装。

181固定控制包含166硬断言和15待定；硬断言130通过、36失败，失败完整保留。没有S/E/Ec完整decision差异、入口外差异或受限母对象未证阳性报告。七条已核重点原包及反例的实际旧新值另列，不把开发预期作为金标签。

尚需核查新增父谓词路径的当前—父句直接关系。相同来源或组件不能代替治理边证明，尤其当前段落缺失时。最终源码、封印和selector尚待独立绑定，不据本次中间结果执行采用。
'''
p=OUT/'report.md';assert not p.exists();p.write_text(md)
for s in inputs.values(): assert bind(s['path'])==s
write('input-bindings.json',{'inputs':list(inputs.values()),'unchanged_before_after':True})
members=[bind(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='output-seal.json']
write('output-seal.json',{'files':members,'readonly_inputs_unchanged':True,'candidate_adoption_approved':False})
print(json.dumps({'report':bind(OUT/'report.json'),'seal':bind(OUT/'output-seal.json'),'inputs_N':len(inputs),'members_N':len(members)},ensure_ascii=False))
