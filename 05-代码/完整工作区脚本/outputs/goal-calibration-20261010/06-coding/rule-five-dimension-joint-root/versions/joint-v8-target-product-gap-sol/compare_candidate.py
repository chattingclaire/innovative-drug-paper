"""Finite comparisons and static reachability proof; writes only beside itself."""
from pathlib import Path
import ast, copy, datetime, difflib, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
P = Path(__file__).resolve().parent
OLD = P.parent / 'joint-v7-relation-content-sol'
NAMES = ('evidence', 'source_packet', 'source_receipts', 'relations', 'dimensions')
REF = '单品种未上市与按需优先机会'
def bind(p):
    p = Path(p).resolve(); b = p.read_bytes()
    return dict(path=str(p), bytes=len(b), sha256=hashlib.sha256(b).hexdigest())
def load(p): return json.loads(Path(p).read_bytes())
def save(n,x):
    with (P/n).open('x',encoding='utf8') as f:
        json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def mods(code):
    m={}
    for n in NAMES:
        s=importlib.util.spec_from_file_location(n,code/(n+'.py'));v=importlib.util.module_from_spec(s);sys.modules[n]=v;s.loader.exec_module(v);m[n]=v
    return m
def requests(value,path='$'):
    out=[]
    if isinstance(value,dict):
        if value.get('reference')==REF and value.get('request_kind')=='unresolved_manual_relation_boundary':out.append(path)
        for k,v in value.items():out += requests(v,path+'/'+str(k))
    elif isinstance(value,list):
        for i,v in enumerate(value):out += requests(v,path+'/'+str(i))
    return out

# Code bytes outside the original if-body, not merely labels, must be exact.
old=(OLD/'dimensions.py').read_text();new=(P/'dimensions.py').read_text()
needle="    if re.search('境外已上市[^。；;]{0,8}境内未上市', text) and opportunity and (not any((re.search(pattern, text) for pattern in GAPS.values()))):\n"
end="    if unit.kind == 'named_mechanism' and unit.details.get('relation_subtype') == 'bounded_IF_actual_support'"
a=old.index(needle);b=old.index(end,a);aa=new.index(needle);bb=new.index(end,aa)
assert old[:a+len(needle)]==new[:aa+len(needle)] and old[b:]==new[bb:]
assert old.count(needle)==new.count(needle)==1
ot=ast.parse(old);nt=ast.parse(new)
of=next(n for n in ot.body if isinstance(n,ast.FunctionDef) and n.name=='_fairness')
nf=next(n for n in nt.body if isinstance(n,ast.FunctionDef) and n.name=='_fairness')
ob=next(n for n in of.body if isinstance(n,ast.If) and any(isinstance(k,ast.Constant) and k.value==REF for k in ast.walk(n)))
nb=next(n for n in nf.body if isinstance(n,ast.If) and any(isinstance(k,ast.Constant) and k.value==REF for k in ast.walk(n)))
assert ast.dump(ob.test)==ast.dump(nb.test) and ast.dump(ast.Module(body=ob.orelse,type_ignores=[]))==ast.dump(ast.Module(body=nb.orelse,type_ignores=[]))
nb.body=copy.deepcopy(ob.body)
assert ast.dump(ot)==ast.dump(nt)
for n in NAMES[:-1]: assert (OLD/(n+'.py')).read_bytes()==(P/(n+'.py')).read_bytes()
proof={'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'four_non_dimension_modules_byte_identical':True,'dimensions_prefix_suffix_outside_original_if_body_byte_identical':True,'all_AST_identical_after_restoring_only_old_if_body':True,'outer_branch_condition_byte_and_AST_identical':True,'no_changed_source_relation_or_evidence_code':True,'no_ID_reference_department_score_features_added':True,'original_boundary_reference':REF,'retention':{'positive_F':'details.unresolved_semantic_boundaries','null_F':'needed_material and rule_conflict.boundary_requests','zero_F':'impossible when this original boundary was reached, because Accumulator.finish tests boundary before zero','implementation_exception':'not a complete decision; must not be silently eligible for partial reuse'},'closure':'Any successful v7 record whose full decisions have no original boundary request cannot reach the only changed body. Same semantic input and same five modules outside that body therefore produce byte-JSON-equivalent decisions and requests. Every record with an original boundary request must be recomputed, including F=1 and unchanged-value evidence changes.','prerequisites':['entire sealed v7 corpus output with all records and full five decisions','correct code hash and identical canonical packets','complete intact details/needed_material/rule_conflict per record','exclude no-output or technical-failure records from reuse','fixed candidate hashes and unchanged remainder','freeze all affected IDs only after v7 full4481 seal'], 'whole4481_executed':False,'complete_affected_population_frozen':False,'incomplete_or_lossy_output_fallback':'Reconstruct complete old serialized decisions from its existing per-record receipts; if completeness and code/input binding cannot be proved, perform whole v8 recomputation.'}
save('static-impact-proof.json',proof)
(P/'dimensions.diff').write_text(''.join(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='sealed-v7/dimensions.py',tofile='candidate-v8/dimensions.py')))

# Baseline targeted replay writes in candidate only; fixed expectations stay untouched.
m=mods(P/'v7-before-edit-code-snapshot');cs=load(P/'candidate-controls-fixed-before-edit.json')['cases'];baseline=[]
for c in cs:
    u=copy.deepcopy(c['semantic_input']);before=copy.deepcopy(u)
    v=m['relations'].RelationView(u);ds=m['dimensions'].judge(v);m['evidence'].validate_decisions(u,ds);assert u==before
    baseline.append({'name':c['name'],'expected':c['expected'],'actual':{d:ds[d]['value'] for d in c['expected']},'decisions':ds,'relations':v.traces(),'material_requests':v.material_requests,'structural_address_issues':v.structural_address_issues})
save('v7-targeted-control-baseline.json',baseline)

comparisons=[]
for name,oldpath,newpath in [('development77','final-development/records77.json','attempt02-development/records77.json'),('legacy22','final-controls/results.json','attempt02-legacy22/results.json'),('counterpairs18','final-development/counterpairs.json','attempt02-development/counterpairs.json'),('original75','final-original75/results.json','attempt02-original75/results.json'),('parent235','final-parent235/results.json','attempt02-parent235/results.json')]:
    os=load(OLD/oldpath);ns=load(P/newpath);assert len(os)==len(ns);deltas=[];outscope=[]
    for i,(o,n) in enumerate(zip(os,ns)):
        assert o.get('id',o.get('name',o.get('case')))==n.get('id',n.get('name',n.get('case')))
        ods=o.get('decisions',{});nds=n.get('decisions',{})
        changed=[d for d in ods if ods[d]!=nds[d]]
        paths=requests(o)
        for d in changed:
            item={'index':i,'record':o.get('id',o.get('name',o.get('case'))),'dimension':d,'old':ods[d]['value'],'new':nds[d]['value'],'old_boundary_paths':paths,'old_decision':ods[d],'new_decision':nds[d]}
            deltas.append(item)
            if d!='F' or not paths:outscope.append(item)
        for k in ('source_requests','material_requests','relations','source_relation_traces','traces','structural_address_issues'):
            if k in o and k in n:assert o[k]==n[k],(name,i,k)
    assert not outscope
    comparisons.append({'suite':name,'N':len(os),'old_input':bind(OLD/oldpath),'new_output':bind(P/newpath),'changed_dimension_N':len(deltas),'other_four_dimensions_exact_json_unchanged':True,'out_of_impact_closure_N':0,'changes':deltas,'new_failed_case_indices':[i for i,r in enumerate(ns) if r.get('passed') is False],'old_failed_case_indices':[i for i,r in enumerate(os) if r.get('passed') is False]})
target=load(P/'attempt02-targeted-controls/results.json');td=[]
for i,(o,n) in enumerate(zip(baseline,target)):
    changes=[d for d in o['decisions'] if o['decisions'][d]!=n['decisions'][d]]
    assert all(d=='F' for d in changes)
    if changes:assert requests(o)
    td.append({'name':n['name'],'expected':n['expected'],'old':o['actual'],'new':n['actual'],'pass':n['passed'],'changed_dimensions':changes,'old_boundary_paths':requests(o)})
save('targeted-old-new-comparison.json',td)
save('finite-replay-comparison.json',comparisons)
freeze=load(P/'pre-edit-freeze.json');bad=[x for x in freeze['protected_inputs'] if bind(x['path'])!=x];assert not bad
save('protected-input-readback.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'N':len(freeze['protected_inputs']),'mismatch_N':0,'candidate_code':[bind(P/(n+'.py')) for n in NAMES]})
print(json.dumps({'protected_N':len(freeze['protected_inputs']),'static_scope_pass':True,'finite_deltas':{x['suite']:x['changed_dimension_N'] for x in comparisons},'targeted_pass_N':sum(r['pass'] for r in td),'targeted_failures':[{k:r[k] for k in ('name','expected','old','new')} for r in td if not r['pass']]},ensure_ascii=False))
