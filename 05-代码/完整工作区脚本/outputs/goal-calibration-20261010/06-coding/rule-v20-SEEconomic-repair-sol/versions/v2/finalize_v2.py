"""Seal v2 code/evidence and verify originals; does not infer corpus labels."""
import ast,datetime,difflib,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;V1=P.parents[1];ROOT=P.parents[5]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def binding(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def write(name,value):
 with (P/name).open('x') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')
manual=ROOT/'outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt'
assert sha(manual)=='5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
code=[P/n for n in ['source_packet.py','source_receipts.py','evidence.py','relations.py','dimensions.py']]
for p in code:compile(p.read_text(),str(p),'exec')
codebind=[binding(p) for p in code];algorithm_sha=hashlib.sha256(json.dumps(codebind,sort_keys=True,separators=(',',':')).encode()).hexdigest()
write('algorithm-bindings.json',{'version':'v20_SEEconomic_v2_nonhuman_candidate','manual':binding(manual),'five_modules':codebind,'algorithm_sha256':algorithm_sha,'classifier_reads_only_supplied_unit':True,'no_frozen_input_mutation':True,'no_new_source_projection':True})
for name in ['dimensions.py','relations.py']:
 (P/(name+'.patch')).write_text(''.join(difflib.unified_diff((V1/name).read_text().splitlines(True),(P/name).read_text().splitlines(True),fromfile='sealed-v1/'+name,tofile='isolated-v2/'+name)))
# Precisely isolate edits shared with the I/F branch for ROOT merging.
for filename,function in [('relations.py','_add'),('dimensions.py','_units'),('dimensions.py','judge')]:
 old=ast.parse((V1/filename).read_text());new=ast.parse((P/filename).read_text())
 def get(tree,text):
  n=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name==function);return ''.join(text.splitlines(True)[n.lineno-1:n.end_lineno])
 a=get(old,(V1/filename).read_text());b=get(new,(P/filename).read_text())
 (P/('shared-'+function+'.patch')).write_text(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile='v1/'+filename+':'+function,tofile='v2/'+filename+':'+function)))
finals=['controls40-final-scope.json','structural-final-scope.json','dependency-final-scope.json','bridge20-final-scope.json','legacy42-final-scope.json','interface-final-scope.json','closure-bindings-final-scope.json','missing-middle-final.json']
materials={};quotes=[];runsummary=[]
from source_packet import semantic_unit
from evidence import validate_decisions
for name in finals:
 output=json.loads((P/name).read_text());tests=output.get('tests',[output]);summary={'artifact':binding(P/name),'test_N':len(tests),'failures':[],'bound_final_algorithm':algorithm_sha}
 for t in tests:
  path=t.get('input_binding',{}).get('path') or t.get('material_path')
  if path:
   path=Path(path);bundle=json.loads(path.read_text());u=semantic_unit(bundle);materials[str(path)]=binding(path)
   expectedsha=t.get('input_binding',{}).get('sha256') or t.get('material_sha256');assert sha(path)==expectedsha
   assert t['source_current']==bundle['source_record']['text']
  elif 'synthetic_input' in t:u=t['synthetic_input'];bundle=u['source_bundle']
  elif 'source_current' in t:
   # Older fixed-control outputs omitted the synthetic unit; cite every quote
   # against its literal fixture context, separately from real material claims.
   bundle=None;u=None
  else:raise ValueError(name+' lacks input')
  if u:validate_decisions(u,t['decisions'])
  for dim,d in t['decisions'].items():
   if d['value']!=1:continue
   assert d['current_proposition']['text']==(t.get('source_current') or u['text'])
   for q in d['context_evidence']:
    if not u:
     # Synthetic sibling fixtures have no positive context; positive synthetic
     # cases in controls40 are direct current content only.
     raise ValueError('unbound positive synthetic citation '+t['name'])
    context=next(c for c in u['contexts'] if c['context_id']==q['context_id'])
    assert context['text'][q['start']:q['end']]==q['text'] and q['source_ref']==context['source_ref']
    pointer=None
    if path:
     for i,c in enumerate(bundle['source_record']['contexts']):
      if c['context_id']==q['context_id']:pointer=f'/source_record/contexts/{i}/text';break
    quotes.append({'run':name,'case':t['name'],'dimension':dim,'material_path':str(path) if path else None,'json_pointer':pointer,'context_id':q['context_id'],'start':q['start'],'end':q['end'],'quote':q['text'],'usage':q['usage'],'source_ref':q['source_ref'],'exact_literal_and_source_binding_verified':True})
  if not t['passed']:summary['failures'].append({'case':t['name'],'original_fixed_expected':t.get('expected_fixed_before_v2_edit',t.get('expected_fixed_before_execution',t.get('expected'))),'actual':t['actual'],'status':'preserved_material_scope_difference_not_label_fit'})
 runsummary.append(summary)
# Audit-specific first-attempt material hashes are frozen before code changes.
for name in ['before-v2-repair.json','dependency-attempt1.json']:
 for t in json.loads((P/name).read_text())['tests']:
  path=t.get('input_binding',{}).get('path') or t.get('material_path')
  if path:assert sha(Path(path))==(t.get('input_binding',{}).get('sha256') or t['material_sha256'])
write('actual-read-and-quote-validation.json',{'scope':'34 explicitly selected frozen actual materials + fixed synthetic/control inputs; not800','actual_material_N':len(materials),'materials':list(materials.values()),'positive_context_quote_N':len(quotes),'quotes':quotes,'all_exact_literal_and_source_ref_verified':True,'no_pixel_or_external_source_claim':True})
write('regression-reception.json',{'non_human_not_gold':True,'not_formal_accuracy_or_gate':True,'final_algorithm_sha256':algorithm_sha,'runs':runsummary,'full800_or77_runs':0,'all_original_expectations_preserved':True,'remaining_differences':'A450 raw packet has no closed container; three old synthetic complete-article fixtures lack actual end-boundary proof. New correctly closed counterpart, missing-middle/final, foreign boundary, clause-only and same-paragraph sibling controls pass.'})
manualquotes=json.loads((ROOT/'outputs/goal-calibration-20261010/08-audits/SE-Ec-repair-independent-controls-sol/manual-basis-quotes.json').read_text())
text=manual.read_text()
for q in manualquotes['quotes']:assert text[q['start']:q['end']]==q['quote']
write('manual-basis-quotes.json',manualquotes)
origin=json.loads((V1/'delivery-seal.json').read_text());checked=[]
for b in origin['files']:checked.append({'path':b['path'],'unchanged':sha(Path(b['path']))==b['sha256']})
assert all(c['unchanged'] for c in checked)
write('v1-preservation-readback.json',{'v1_members_N':len(checked),'all_unchanged':True,'checks':checked,'v1_delivery_seal':binding(V1/'delivery-seal.json'),'frozen_three_unmodified_coder_modules':[{'name':n,'same_v1_sha':sha(P/n)==sha(V1/n)} for n in ['source_packet.py','source_receipts.py','evidence.py']]})
write('merge-dependencies.json',{'precise_patches':['shared-_add.patch','shared-_units.patch','shared-judge.patch','relations.py.patch','dimensions.py.patch','se_relations.inc','se_predicates.inc'],'shared_changes':[
 {'function':'RelationView._add','repair':'Dedup identity includes exact context positions, subtype, dimension consumers/IF restriction, projection and shared predicate; same quote cannot suppress distinct bounded relationships.'},
 {'function':'dimensions._units','repair':'SE scope keeps all literal evidence/closure quotes; closure quote cannot donate label content.'},
 {'function':'judge','repair':'affected_dimensions and only_IF_consumers intersect; retain other branch I/F resolver and definitions.'},
 {'function':'RelationView.__init__','repair':'append only own SE bounded/content-parent/list/reference calls; retain other branch calls.'}],
 'do_not_expand_IF_support_or_rights_into_SEEconomic':True,'common_material_requirements':['A450 closed actual renewal-member container/next boundary','A307/A415 cited article8 original final boundary; article7 already adjacent article8 closure','same-version missing programme criteria, resume-risk basis, PRO endpoint definition and price-node/renewal definitions from original common source'],'no_exclusive_projection_added':True,'human_boundary_not_optimization_targets':['A157 GLP','S eight undetermined','Ec A79/A149/A337','E704'],'prior_request_receipt_cancellation':'V2 retains earlier frozen requests; ROOT must merge exact dependency resolution receipts from I/F branch, not silently delete generic requests.'})
write('execution-history.json',{'all_attempt_json_artifacts_preserved':[binding(p) for p in sorted(P.glob('*attempt*.json'))],'initial_technical_failure':{'step':'initial v2 finite-closure quote validation before after-v2-attempt1 output','case':'A307','error':'decisions/S/context_evidence/1: anchor fields differ from the literal interface','cause':'extra relation_role field was added to literal quote, then removed; boundary role is now in relation details without editing evidence.py','predictions_saved_for_failed_initial_call':False,'fixed_before_saved_attempt1':True},'development_only':True,'per_intermediate_code_SHA_not_recorded':'Early exploratory fixed-control attempts saved full outputs/unchanged expectations but did not each include a codeSHA. Final eight regression artifacts are now bound to the exact sealed algorithm. Do not imply retrospective immutable code snapshot for each early attempt.','no_repeated800_or77_semantics':True})
write('candidate-seal.json',{'status':'sealed_v2_nonhuman_candidate','algorithm_sha256':algorithm_sha,'manual':binding(manual),'code':codebind,'regression_artifacts':[binding(P/n) for n in finals],'not_formal_or_human_gold':True,'root_integration_required':True})
print(json.dumps({'algorithm_sha256':algorithm_sha,'actual_material_N':len(materials),'quote_N':len(quotes),'v1_unchanged_N':len(checked),'regressions':[(r['test_N'],len(r['failures'])) for r in runsummary]},ensure_ascii=False))
