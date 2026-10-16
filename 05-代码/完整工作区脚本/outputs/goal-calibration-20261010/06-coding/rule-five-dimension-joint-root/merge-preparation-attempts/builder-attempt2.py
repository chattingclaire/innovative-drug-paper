"""Create an isolated, explicitly unfinished merge baseline from sealed parents."""
import ast
import copy
import datetime
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CODING=ROOT/'06-coding'
IF=CODING/'rule-v20-semantic-audit-repair-sol/versions/v3'
SE=CODING/'rule-v20-SEEconomic-repair-sol/versions/v2'
BASE=ROOT/'08-audits/five-dimension-merge-interface-sol/source-code-observation-snapshots/baseline'
SUPPLEMENT=ROOT/'08-audits/five-dimension-merge-interface-sol/sealed-SE-v2-supplement'
OUT=CODING/'rule-five-dimension-joint-root/versions/merge-baseline01'

def load(p):return json.loads(Path(p).read_text())
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
def exact(item):assert bind(item['path'])=={k:item[k] for k in ('path','bytes','sha256')},item['path']
def save(p,v):
    with p.open('x',encoding='utf8') as h:json.dump(v,h,ensure_ascii=False,indent=2);h.write('\n')
def representation(node):return ast.dump(node,include_attributes=False)

assert not OUT.exists(),'Do not replace an existing candidate'
ifseal=bind(IF/'delivery-seal.json');seseal=bind(SE/'delivery-seal.json');suppseal=bind(SUPPLEMENT/'output-seal.json')
assert ifseal['sha256']=='0c884db46c85466aba46c962128c4967fe58ba3d77801e5771dda3796387fc7c'
assert seseal['sha256']=='39a87613fc07027fe97a7e739535d6101da0d248c8b84a1c573a6f699cba1d47'
assert suppseal['sha256']=='a75a28ad93414cde2fff9d4694fc647d7b96cb070e519268d9cfb34e83c0ef57'
for folder,filename,key in ((IF,'delivery-seal.json','members'),(SE,'delivery-seal.json','files'),(SUPPLEMENT,'output-seal.json','members')):
    for item in load(folder/filename)[key]:exact(item)
input_paths=[p/(name+'.py') for p in (IF,SE,BASE) for name in ('source_packet','source_receipts','evidence','relations','dimensions')]
input_bindings=[bind(p) for p in input_paths]

def definitions(tree):
    functions={};constants={}
    for n in tree.body:
        if isinstance(n,ast.FunctionDef):functions[n.name]=n
        elif isinstance(n,ast.ClassDef):
            for method in n.body:
                if isinstance(method,ast.FunctionDef):functions[n.name+'.'+method.name]=method
        elif isinstance(n,ast.Assign):
            assert len(n.targets)==1 or all(isinstance(t,ast.Name) for t in n.targets)
            for target in n.targets:
                if isinstance(target,ast.Name):constants[target.id]=n
    return functions,constants

trees={name:{role:ast.parse((path/(name+'.py')).read_text()) for role,path in [('IF',IF),('SE',SE),('BASE',BASE)]} for name in ('relations','dimensions')}
manifest=[];assembled={}
for name,variants in trees.items():
    BF,BC=definitions(variants['BASE']);IFf,IC=definitions(variants['IF']);SF,SC=definitions(variants['SE'])
    Ichange={k for k in IFf if k not in BF or representation(IFf[k])!=representation(BF[k])}
    Schange={k for k in SF if k not in BF or representation(SF[k])!=representation(BF[k])}
    overlap=Ichange&Schange
    assert overlap==({'RelationView.__init__'} if name=='relations' else {'_generic','judge'})
    replacement={k:copy.deepcopy(SF[k]) for k in Schange-overlap}
    if name=='relations':
        node=copy.deepcopy(IFf['RelationView.__init__'])
        index=next(i for i,s in enumerate(node.body) if isinstance(s,ast.For) and isinstance(s.target,ast.Name) and s.target.id=='request')
        extra=ast.parse('self._se_bounded_content()\nself._se_direct_content_parents()\nself._se_complete_lists()\nself._se_operational_references()').body
        node.body[index:index]=extra
        replacement['RelationView.__init__']=node
    else:
        generic=copy.deepcopy(IFf['_generic'])
        loop=next(n for n in generic.body if isinstance(n,ast.For) and isinstance(n.target,ast.Name) and n.target.id=='dim')
        guards=ast.parse('if dim in ("S", "E", "Ec"):\n    continue\nconsumers=set(unit.details.get("affected_dimensions", DIMENSIONS))\nif unit.details.get("only_IF_consumers"):\n    consumers &= {"I", "F"}\nif dim not in consumers:\n    continue').body
        loop.body[0:0]=guards
        replacement['_generic']=generic
        # Keep the I/F dispatch interface. Generic executes only on its old
        # full-consumer path; its local guard now excludes the three SE paths.
        replacement['judge']=copy.deepcopy(IFf['judge'])
    newconstants={k:copy.deepcopy(v) for k,v in SC.items() if k not in IC}
    assert all(k.startswith('SE_') for k in newconstants)
    common_constant_changes={k for k in SC if k in BC and representation(SC[k])!=representation(BC[k]) and k in IC and representation(SC[k])!=representation(IC[k])}
    assert common_constant_changes<={'MANUAL'}
    # The I/F MANUAL already identifies the identical frozen manual for all5.
    tree=copy.deepcopy(variants['IF'])
    effective=definitions(tree)[0]
    result=[]
    for node in tree.body:
        if isinstance(node,ast.FunctionDef):
            if node is not effective[node.name]:continue
            node=copy.deepcopy(replacement.pop(node.name,node))
        elif isinstance(node,ast.ClassDef):
            body=[]
            for method in node.body:
                if isinstance(method,ast.FunctionDef):
                    key=node.name+'.'+method.name
                    if method is not effective[key]:continue
                    method=copy.deepcopy(replacement.pop(key,method))
                body.append(method)
            additions=[k for k in replacement if k.startswith(node.name+'.')]
            body.extend(replacement.pop(k) for k in additions)
            node.body=body
        result.append(node)
    result.extend(newconstants.values())
    assert all('.' not in k for k in replacement)
    result.extend(replacement.values())
    tree.body=result;ast.fix_missing_locations(tree)
    FF,FC=definitions(tree)
    expected_functions=set(IFf)|set(SF)
    assert set(FF)==expected_functions
    for key in expected_functions:
        if key in overlap:origin='manual_shared_interface_merge'
        elif key in Schange:origin='SE_v2_effective_function'
        else:origin='IF_v3_effective_function'
        reference=SF.get(key) if origin=='SE_v2_effective_function' else IFf.get(key) if origin=='IF_v3_effective_function' else None
        if reference is not None:assert representation(FF[key])==representation(reference),key
        manifest.append(dict(module=name,function=key,origin=origin,AST_sha256=hashlib.sha256(representation(FF[key]).encode()).hexdigest()))
    source='"""ROOT joint developer merge baseline; known SE geometry defects remain, not a release."""\n'+ast.unparse(tree)+'\n'
    compile(source,str(OUT/(name+'.py')),'exec')
    assembled[name]=source
for name in ('source_packet','source_receipts','evidence'):
    assert (IF/(name+'.py')).read_bytes()==(SE/(name+'.py')).read_bytes()==(BASE/(name+'.py')).read_bytes()
assert [bind(p) for p in input_paths]==input_bindings
OUT.mkdir(parents=True)
for name,source in assembled.items():
    with (OUT/(name+'.py')).open('x',encoding='utf8') as h:h.write(source)
for name in ('source_packet','source_receipts','evidence','regression_tests'):
    with (OUT/(name+'.py')).open('xb') as h:h.write((IF/(name+'.py')).read_bytes())
save(OUT/'function-selection.json',dict(functions=manifest,constants='IFv3 constants including frozen five-dimensional MANUAL; append all new SE constants',duplicate_function_definitions='one effective function per namespace, no silent shadowing',shared_functions=['RelationView.__init__','_generic','judge'],shared_add_identity='exact SEv2 implementation retained',parent_inputs=input_bindings,parent_delivery_seals=[ifseal,seseal],interface_supplement=suppseal))
save(OUT/'algorithm-bindings.json',dict(status='unfinished_joint_developer_merge_baseline',at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),five_modules=[bind(OUT/(n+'.py')) for n in ('source_packet','source_receipts','evidence','relations','dimensions')],manual=bind(ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt'),definition_changes=False,existing_SE_v2_independent_geometry_failures='5cases/9dimensions retained for general correction; geometry owner working separately',new_neutral_material_projection=False,cohort_predictions_or_formal_acceptance=False))
save(OUT/'pre-execution-seal.json',dict(output_members=[bind(p) for p in sorted(OUT.iterdir()) if p.is_file()],builder=bind(__file__),self_excluded=True))
print(json.dumps(dict(destination=str(OUT),effective_functions=len(manifest),changed_shared_interfaces=3,parent_code_unchanged=True,semantic_execution=0,formal_acceptance=False),ensure_ascii=False))
