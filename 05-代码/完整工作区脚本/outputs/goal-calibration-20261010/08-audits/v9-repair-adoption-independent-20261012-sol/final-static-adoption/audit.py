"""Final independent audit preparation; AST parsing/readback only, never classifies.

Run only after candidate output-seal.json is delivered and code frozen. Output
names are create-only; failed preparations must be preserved separately.
"""
import ast, copy, hashlib, json, datetime
from pathlib import Path
G=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
C=G/'06-coding/rule-five-dimension-joint-root/versions/joint-v9-generic-relationship-sol'
D=G/'08-audits/v9-generic-relationship-repair-design-sol/final-candidate-delivery-20261012-sol'
OLD=G/'06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol'
M=['evidence','source_packet','source_receipts','relations','dimensions']
inputs={}
def bind(p):
    p=Path(p).resolve();b=p.read_bytes()
    return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def read(p):
    s=bind(p);inputs[s['path']]=s;return Path(p).read_bytes()
def load(p):return json.loads(read(p))
def verify(s):
    b=bind(s['path']);inputs[b['path']]=b
    assert all(b[k]==s[k] for k in ['path','bytes','sha256']),s
    return b
def save(name,value):
    with (OUT/name).open('x',encoding='utf8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def dump(n):return ast.dump(n,include_attributes=False)
def literal_assignment(tree,name):
    found=[q.value for q in tree.body if isinstance(q,ast.Assign) and len(q.targets)==1 and isinstance(q.targets[0],ast.Name) and q.targets[0].id==name]
    assert len(found)==1,name
    return ast.literal_eval(found[0])

seal=load(D/'output-seal.json'); freeze=load(D/'candidate-freeze.json')
members=seal['files'];sealed={str(Path(s['path']).resolve()):s for s in members}
assert len(sealed)==len(members)
for s in members:verify(s)
def required_member(p,role):
    s=bind(p);assert s['path'] in sealed,(role,s['path'])
    assert sealed[s['path']]==s,(role,s['path'])
    return dict(s,required_role=role)
required=[required_member(C/(m+'.py'),'actual_'+m+'_module') for m in M]
required += [required_member(D/'candidate-freeze.json','candidate_freeze'),required_member(C/'select_static_impact.py','actual_static_selector'),required_member(C/'run_finite_controls.py','actual_control_runner')]
required += [required_member(s['path'],'final_delivery_explicit_required_member') for s in seal['required_member_bindings'] if str(Path(s['path']).resolve()) not in {q['path'] for q in required}]
assert len(seal['required_member_bindings'])==46
for s in seal['input_bindings']:verify(s)
assert {Path(s['path']).stem for s in freeze['candidate_modules']}==set(M)
for s in freeze['candidate_modules']:
    verify(s);assert s['path']==str(C/(Path(s['path']).stem+'.py'))

AST=[];body_inventory=[];gates=[]
pure_old_relation_calls={'self._closed_primary_programme','self._current_source','self._quote','self._primary_role_quotes','self._se_parent_binding','self._se_geometry_value','self._se_same_geometry','self._se_current_geometry_contexts'}
for m in M:
    old=read(OLD/(m+'.py'));new=read(C/(m+'.py'))
    if m not in ['relations','dimensions']:
        assert old==new;AST.append({'module':m,'byte_identical':True});continue
    before=ast.parse(old);after=ast.parse(new);t=copy.deepcopy(after)
    gates.append(literal_assignment(t,'V9_REPAIR_ENTRY'))
    route=[];retained=[];guards=0
    for n in t.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id=='V9_REPAIR_ENTRY':continue
        if isinstance(n,ast.FunctionDef) and n.name.startswith('_v9_'):
            route.append(n);continue
        if m=='relations' and isinstance(n,ast.ClassDef) and n.name=='RelationView':
            methods=[]
            for q in n.body:
                if isinstance(q,ast.FunctionDef) and q.name.startswith('_v9_'):
                    route.append(q);continue
                if isinstance(q,ast.FunctionDef) and q.name=='__init__':
                    expect=ast.parse('if _v9_repair_gate(self.norm):\n self._v9_bounded_relationships()').body[0]
                    assert dump(q.body[-1])==dump(expect);q.body.pop();guards+=1
                methods.append(q)
            n.body=methods
        if m=='dimensions' and isinstance(n,ast.FunctionDef) and n.name=='judge':
            expect=ast.parse('if _v9_repair_gate(view.norm):\n _v9_IF_consume(acc, view)').body[0]
            positions=[i for i,q in enumerate(n.body) if dump(q)==dump(expect)]
            assert len(positions)==1;i=positions[0]
            assert dump(n.body[i+1])==dump(ast.parse('decisions=acc.finish()').body[0]);n.body.pop(i);guards+=1
        retained.append(n)
    t.body=retained
    assert guards==1 and dump(before)==dump(t),m
    assert len({q.name for q in route})==len(route)
    for q in route:
        assert not q.decorator_list
        assert not any(isinstance(x,(ast.Global,ast.Nonlocal,ast.Import,ast.ImportFrom)) for x in ast.walk(q))
        for d in q.args.defaults+[x for x in q.args.kw_defaults if x is not None]:
            assert not any(isinstance(x,ast.Call) for x in ast.walk(d))
        calls=sorted({ast.unparse(x.func) for x in ast.walk(q) if isinstance(x,ast.Call)})
        assert not any(x in {'open','eval','exec','__import__','globals','locals','setattr','delattr','compile'} for x in calls)
        if m=='relations':
            self_calls={x for x in calls if x.startswith('self.')}
            unexpected={x for x in self_calls if not x.startswith('self._v9_') and x not in pure_old_relation_calls and x != 'self._se_parent_binding(c).get' and x not in {'self.unit.get','self.bundle.get','self.by_id.get','self.origins.get','self.text.split','self._add'} and not x.startswith("self.unit.get(") and not x.startswith("self.origins.get(")}
            assert not unexpected,(q.name,unexpected)
            if 'self._add' in calls:
                assert q.name=='_v9_emit'
                add=[x for x in ast.walk(q) if isinstance(x,ast.Call) and ast.unparse(x.func)=='self._add']
                assert len(add)==1 and ast.literal_eval(add[0].args[0])=='v9_IF_relationship'
        writes=[]
        for x in ast.walk(q):
            if isinstance(x,(ast.Assign,ast.AnnAssign,ast.AugAssign)):
                targets=x.targets if isinstance(x,ast.Assign) else [x.target]
                writes += [ast.unparse(z) for z in targets if isinstance(z,(ast.Attribute,ast.Subscript))]
        if m=='relations':assert not any(z.startswith('self.') for z in writes)
        if m=='dimensions':assert set(z for z in writes if z.startswith('acc.')) <= {"acc.positive['I']","acc.positive['F']"}
        body_inventory.append({'module':m,'function':q.name,'line':q.lineno,'calls':calls,'attribute_subscript_assignment_targets':writes})
    AST.append({'module':m,'complete_old_AST_restored':True,'isolated_guard_N':guards,'new_definitions':[q.name for q in route]})
assert len(gates)==2 and gates[0]==gates[1]
selector=ast.parse(read(C/'select_static_impact.py'))
assert literal_assignment(selector,'V9_REPAIR_ENTRY')==gates[0]
imports=[]
for q in ast.walk(selector):
    if isinstance(q,ast.Import):imports += [x.name for x in q.names]
    if isinstance(q,ast.ImportFrom):imports.append(q.module)
assert set(imports)<={'pathlib','argparse','ast','hashlib','json','re','unicodedata'},imports
save('independent-AST-and-new-body-inventory.json',{'AST':AST,'frozen_gate':gates[0],'new_function_inventory':body_inventory,'selector_imports':imports,'classifier_imported_or_executed':False})
save('candidate-required-member-bindings.json',{'candidate_delivery':bind(D/'output-seal.json'),'required_members':required,'all_required_actual_members_present_and_equal':True,'membership_checks_complete_but_final_readiness_requires_manual_new_body_and_control_review':True})
save('input-bindings-initial.json',{'inputs':list(inputs.values()),'no_other_packet_body_opened':True,'classifier_executed':False})
print(json.dumps({'output':str(OUT),'candidate_member_N':len(members),'independent_AST_ok':True,'automatic_result_is_not_semantic_or_production_approval':True},ensure_ascii=False))
