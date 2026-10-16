"""Combine two sealed, disjoint semantic patches; never execute classification."""
import ast, copy, datetime, hashlib, json
from pathlib import Path

R=Path(__file__).resolve().parents[1]
VERS=R/'06-coding/rule-five-dimension-joint-root/versions'
BASE=VERS/'joint-v9-generic-relationship-sol'
IF=VERS/'joint-v10-generic-relationship-sol'
E=VERS/'joint-v9-e-outcome-candidate-sol'
OUT=VERS/'joint-v10-if-e-combined-v2-root'
A=R/'08-audits/v10-if-e-combination-v2-root'
NAMES=('source_packet','source_receipts','evidence','relations','dimensions')
def bind(p):
 p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def save(p,x):
 with p.open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def dump(n):return ast.dump(n,include_attributes=False)
def named(t):
 out={}
 for n in t.body:
  if isinstance(n,(ast.FunctionDef,ast.ClassDef)):out[n.name]=n
  elif isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):out[n.targets[0].id]=n
 return out
def literal_lines(text,node):return ''.join(text.splitlines(keepends=True)[node.lineno-1:node.end_lineno])
def verify_seal(p):
 x=json.loads(p.read_bytes())
 for k in ('files','members','output_files'):
  for b in x.get(k,[]):assert bind(b['path'])=={q:b[q] for q in ('path','bytes','sha256')}
 return x
IF_SEAL=R/'08-audits/v10-generic-relationship-repair-sol/output-seal.json'
E_SEAL=R/'08-audits/e-complete-response-coverage-repair-sol/output-seal.json'
verify_seal(IF_SEAL);verify_seal(E_SEAL)
assert not OUT.exists() and not A.exists()
OUT.mkdir();A.mkdir()
proof=[]
for name in NAMES[:3]:
 assert (BASE/(name+'.py')).read_bytes()==(IF/(name+'.py')).read_bytes()==(E/(name+'.py')).read_bytes()
 (OUT/(name+'.py')).write_bytes((BASE/(name+'.py')).read_bytes())
for module,owner,method in [('relations','RelationView','__init__'),('dimensions',None,'judge')]:
 texts={k:(p/(module+'.py')).read_text() for k,p in [('base',BASE),('IF',IF),('E',E)]}
 trees={k:ast.parse(v) for k,v in texts.items()};maps={k:named(v) for k,v in trees.items()}
 added=set(maps['E'])-set(maps['base'])
 expected={'E_OUTCOME_ENTRY','_e_outcome_gate'} | ({'_e_current_outcome_consume'} if module=='dimensions' else set())
 assert added==expected and not (added & set(maps['IF']))
 oldfunc=maps['base'][method] if owner is None else named(maps['base'][owner])[method]
 efunc=maps['E'][method] if owner is None else named(maps['E'][owner])[method]
 iffunc=maps['IF'][method] if owner is None else named(maps['IF'][owner])[method]
 extra=[n for n in efunc.body if dump(n) not in {dump(q) for q in oldfunc.body}]
 assert len(extra)==1 and isinstance(extra[0],ast.If)
 assert isinstance(extra[0].test,ast.Call) and isinstance(extra[0].test.func,ast.Name) and extra[0].test.func.id=='_e_outcome_gate'
 reverted=copy.deepcopy(efunc);reverted.body=[n for n in reverted.body if dump(n)!=dump(extra[0])]
 assert dump(reverted)==dump(oldfunc)
 # Source preservation: exactly one guarded call is inserted, with no rewriting
 # of any existing IF code; all E definitions are copied verbatim from its seal.
 lines=texts['IF'].splitlines(keepends=True)
 if owner:
  insertion=iffunc.end_lineno
 else:
  # Map the original E insertion to its next unchanged old statement,
  # rather than assuming that finish is evaluated by the final return.
  ei=next(i for i,n in enumerate(efunc.body) if dump(n)==dump(extra[0]))
  assert ei+1<len(efunc.body)
  following=efunc.body[ei+1]
  mapped=[n for n in iffunc.body if dump(n)==dump(following)]
  assert len(mapped)==1 and isinstance(mapped[0],ast.Assign)
  assert isinstance(mapped[0].value,ast.Call) and isinstance(mapped[0].value.func,ast.Attribute) and mapped[0].value.func.attr=='finish'
  insertion=mapped[0].lineno-1
 lines.insert(insertion,literal_lines(texts['E'],extra[0]))
 combined=''.join(lines)
 first_class=next(n for n in ast.parse(combined).body if isinstance(n,ast.ClassDef))
 top_defs=[maps['E']['E_OUTCOME_ENTRY'],maps['E']['_e_outcome_gate']]
 block='\n\n'.join(literal_lines(texts['E'],n).rstrip() for n in top_defs)+'\n\n'
 clines=combined.splitlines(keepends=True);clines.insert(first_class.lineno-1,block);combined=''.join(clines)
 if owner:
  newmethod=named(maps['E'][owner])['_e_current_outcome_relationships']
  assert '_e_current_outcome_relationships' not in named(maps['IF'][owner])
  combined+='\n'+literal_lines(texts['E'],newmethod)+'\n'
 else:combined+='\n'+literal_lines(texts['E'],maps['E']['_e_current_outcome_consume'])+'\n'
 restored=ast.parse(combined)
 restored.body=[n for n in restored.body if not (isinstance(n,ast.FunctionDef) and n.name in added) and not (isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in added)]
 rm=named(restored)
 func=rm[method] if owner is None else named(rm[owner])[method]
 func.body=[n for n in func.body if dump(n)!=dump(extra[0])]
 if owner:rm[owner].body=[n for n in rm[owner].body if not isinstance(n,ast.FunctionDef) or n.name!='_e_current_outcome_relationships']
 assert dump(restored)==dump(trees['IF'])
 (OUT/(module+'.py')).write_text(combined)
 proof.append({'module':module,'E_additions':sorted(added),'E_call_owner':(owner+'.' if owner else '')+method,
               'remove_only_literal_E_additions_restores_complete_IF_AST':True,
               'IF_parent':bind(IF/(module+'.py')),'E_parent':bind(E/(module+'.py')),'combined':bind(OUT/(module+'.py'))})
gate=(IF/'static_gate.py').read_text().replace('def gate(raw):','def if_gate(raw):')
etext=(E/'relations.py').read_text();em=named(ast.parse(etext))
gate+='\n'+literal_lines(etext,em['E_OUTCOME_ENTRY'])+'\n'+literal_lines(etext,em['_e_outcome_gate'])+'\n\ndef gate(raw):\n    return if_gate(raw) or _e_outcome_gate(raw)\n'
ast.parse(gate);(OUT/'static_gate.py').write_text(gate)
save(A/'literal-combination-proof.json',{'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'candidate_directory':str(OUT),'IF_parent_seal':bind(IF_SEAL),'E_parent_seal':bind(E_SEAL),
 'proofs':proof,'allowed_mutable_dimensions':['E','I','F'],'immutable_dimensions':['S','Ec'],
 'shared_three_modules_byte_identical':True,'existing_manual_prompt_materials_unchanged':True,
 'E_only_current_endpoint_list_never_consumed_by_IF':True,
 'IF_new_relation_kind_never_consumed_by_E_or_legacy_units':True,
 'no_classification_or_model_execution':True,'ROOT_code_read_review_required_before_actual_selection':True})
print(json.dumps({'candidate':str(OUT),'semantic_modules_written':5,'classifier_calls':0}))
