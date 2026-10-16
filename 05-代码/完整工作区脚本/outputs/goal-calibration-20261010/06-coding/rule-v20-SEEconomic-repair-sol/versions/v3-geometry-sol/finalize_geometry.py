"""Verify finite source/evidence/input preservation, then seal this new candidate."""
import ast,copy,difflib,hashlib,json
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;BASE=P.parent/'v2';ROOT=P.parents[5]
AUD=ROOT/'outputs/goal-calibration-20261010/08-audits/SE-Ec-v2-independent-controls-sol'
FINAL=P/'runs/attempt05-root-position-review';INITIAL=P/'runs/baseline-v2-before-edit'
MODULES=['source_packet','source_receipts','evidence','relations','dimensions']
def bind(p):
    p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def write(name,v):
    with (P/name).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def effective(path):
    tree=ast.parse(path.read_text());d={}
    for n in tree.body:
        if isinstance(n,ast.FunctionDef):d[n.name]=n
        elif isinstance(n,ast.ClassDef):
            for f in n.body:
                if isinstance(f,ast.FunctionDef):d[n.name+'.'+f.name]=f
    return d
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
input_binding=json.loads((P/'input-bindings.json').read_text())
checked=[]
for item in input_binding['base_seals']+input_binding['base_five_modules']+input_binding['independent_controls']+input_binding['original156_scripts']+input_binding['original156_artifacts']+[input_binding['manual'],input_binding['independent_seal']]:
    assert bind(item['path'])==item;checked.append(item)
base_seal=json.loads((BASE/'delivery-seal.json').read_text())
for item in base_seal['files']:assert bind(item['path'])==item
audseal=json.loads((AUD/'output-seal.json').read_text())
for item in audseal['output_members']:assert bind(item['path'])==item
diffs=[];shared=[]
for file in ['relations.py','dimensions.py']:
    a=effective(BASE/file);b=effective(P/file);lines=(P/file).read_text().splitlines(True);oldlines=(BASE/file).read_text().splitlines(True)
    assignments=lambda path:[ast.dump(n,include_attributes=False) for n in ast.parse(path.read_text()).body if isinstance(n,(ast.Assign,ast.AnnAssign))]
    assert assignments(BASE/file)==assignments(P/file)
    for k in sorted(set(a)|set(b)):
        before=ast.dump(a[k],include_attributes=False) if k in a else None;after=ast.dump(b[k],include_attributes=False) if k in b else None
        if before!=after:
            oldtext=''.join(oldlines[a[k].lineno-1:a[k].end_lineno]) if k in a else ''
            newtext=''.join(lines[b[k].lineno-1:b[k].end_lineno]) if k in b else ''
            diffs.append({'file':file,'function':k,'status':'added' if k not in a else 'changed','old_line':a[k].lineno if k in a else None,'new_line':b[k].lineno if k in b else None,'calls':sorted({ast.unparse(n.func) for n in ast.walk(b[k]) if isinstance(n,ast.Call)}),'effective_function_diff':''.join(difflib.unified_diff(oldtext.splitlines(True),newtext.splitlines(True),fromfile='sealed-SEv2/'+k,tofile='SEv3-geometry/'+k))})
    names=['RelationView.__init__','RelationView._add','RelationView._parents','RelationView._standards'] if file=='relations.py' else ['_units','_generic','judge','_innovation','_fairness']
    for k in names:
        same=ast.dump(a[k],include_attributes=False)==ast.dump(b[k],include_attributes=False);assert same
        shared.append({'file':file,'function':k,'unchanged_effective_AST':same})
for n in ['source_packet','source_receipts','evidence']:assert bind(P/(n+'.py'))['sha256']==bind(BASE/(n+'.py'))['sha256']
write('function-diff.json',{'changes':diffs,'changed_or_added_effective_function_N':len(diffs),'shared_unchanged':shared,'top_level_constant_changes':[],'IF_logic_unchanged':True})
for n in ['relations.py','dimensions.py']:
    (P/(n+'.patch')).write_text(''.join(difflib.unified_diff((BASE/n).read_text().splitlines(True),(P/n).read_text().splitlines(True),fromfile='sealed-SEv2/'+n,tofile='SEv3-geometry/'+n)))
summary=json.loads((FINAL/'summary.json').read_text());assert summary['original_case_N']==156
originalfail=[c for s in summary['original156'] for c in s['failures']];assert len(originalfail)==4
allow={'independent_legacy20':['complete_explicit_article_three_dimensions'],'independent_new20':['direct_payment_child_condition'],'geometry_new12':['near_safety_parent','near_payment_parent']}
for k,s in summary['suite_summaries'].items():assert [c['name'] for c in s['failures']]==allow.get(k,[])
assert summary['suite_summaries']['independent_legacy20']['passed_N']==19
stable=[]
for entry in summary['original156']:
    path=Path(entry['input_capture']['path']);old=INITIAL/path.name
    assert bind(path)['sha256']==bind(old)['sha256'];stable.append({'file':path.name,'input_sha256_unchanged':True,'case_N':entry['case_N']})
first=json.loads((INITIAL/'independent43-and-new12.json').read_text());last=json.loads((FINAL/'independent43-and-new12.json').read_text())
old_cases={(c['suite'],c['name']):c for c in first}
for c in last:
    if (c['suite'],c['name']) in old_cases:
        old=old_cases[c['suite'],c['name']];assert c['received_unit']==old['received_unit'];assert c['expected']==old['expected']
write('finite-input-preservation.json',{'original156_received_unit_files':stable,'original43_and_initial12_received_inputs_and_expectations_unchanged':True,'refinement_only_interface_envelope_addendum':bind(P/'refinement-interface-addendum.json')})
# Validate every actual positive context quote against the exact received unit.
quotes=[];materials={};source_ids=set()
for s in summary['original156']:
    file=FINAL/(s['script'][:-3]+'.json');x=json.loads(file.read_text());cases=x.get('tests',x.get('cases',[x]));units=json.loads((FINAL/(s['script'][:-3]+'-received-units.json')).read_text())
    assert len(cases)==len(units)
    for c,u in zip(cases,units):
        path=c.get('input_binding',{}).get('path') or c.get('material_path')
        if path:
            p=Path(path);packet=json.loads(p.read_text());sid=packet['source_record']['id'];source_ids.add(sid);materials[str(p)]={'binding':bind(p),'source_id':sid,'blind_id':p.stem,'scope':'frozen_current_and_supplied_contexts_consumed_by_original_finite_regression; no new original document read'}
            original_sha=c.get('input_binding',{}).get('sha256') or c.get('material_sha256');assert bind(p)['sha256']==original_sha
        for dim,d in c['decisions'].items():
            if d['value']!=1:continue
            contexts={z['context_id']:z for z in u['contexts']}
            for item in [d]+d.get('details',{}).get('additional_evidence',[]):
                for q in item['context_evidence']:
                    ctx=contexts[q['context_id']];assert ctx['text'][q['start']:q['end']]==q['text'];assert ctx['source_ref']==q['source_ref']
                    quotes.append({'suite':s['script'],'case':c['name'],'dimension':dim,'quote':q,'exact_literal_and_source_ref':True})
for c in last:
    assert c['evidence_valid'];u=c['received_unit'];contexts={z['context_id']:z for z in u['contexts']}
    for dim,d in c['decisions'].items():
        if d['value']!=1:continue
        for item in [d]+d.get('details',{}).get('additional_evidence',[]):
            for q in item['context_evidence']:
                ctx=contexts[q['context_id']];assert ctx['text'][q['start']:q['end']]==q['text'];assert ctx['source_ref']==q['source_ref'];quotes.append({'suite':c['suite'],'case':c['name'],'dimension':dim,'quote':q,'exact_literal_and_source_ref':True})
old_materials=json.loads((BASE/'actual-read-and-quote-validation.json').read_text())['materials'];old_paths={v['path'] if 'path' in v else v['material_path'] for v in old_materials}
assert len(materials)==34 and set(materials)<=old_paths
write('source-read-exposure-log.json',{'identity':'non_human_AI_rule_development','actual_material_N':len(materials),'source_ids_read':sorted(source_ids),'materials':list(materials.values()),'new_actual_source_ids':[],'new_original_source_document_read_N':0,'prior_exposure_binding':bind(BASE/'actual-read-and-quote-validation.json'),'synthetic_new_control_N':28,'not_new_policy_records':True,'no_formal_LLM_or_old800_expectation_read':True})
positionproof=[]
for name in ['root-position-controls-fixed.json','preceding-position-controls-fixed.json']:
    for c in json.loads((P/name).read_text())['cases']:
        docs={d['sha256']:d['text'] for d in c['synthetic_documents']}
        for sha,text in docs.items():assert hashlib.sha256(text.encode()).hexdigest()==sha
        for ctx in c['synthetic_bundle']['source_record']['contexts']:
            ref=ctx['source_ref'];iv=ref['locator'].get('unicode_code_point_interval_half_open')
            if not iv:continue
            assert docs[ref['sha256']][iv[0]:iv[1]]==ctx['text']
            positionproof.append({'file':name,'case':c['name'],'context_id':ctx['context_id'],'source_sha256':ref['sha256'],'original_char_interval':iv,'literal':ctx['text'],'exact_full_synthetic_source_literal':True,'not_real_policy_source':True})
write('literal-quote-validation.json',{'quote_N':len(quotes),'checks':quotes,'all_exact_supplied_literals':True,'new_position_control_full_source_checks':positionproof,'not_relationship_truth_certification':True,'not_claiming_unread_external_originals':True})
manual=json.loads((P/'manual-basis-bound.json').read_text());raw=Path(manual['binding']['path']).read_bytes();txt=raw.decode()
for q in manual['quotes']:assert txt[q['start']:q['end']]==q['quote'];assert raw[len(txt[:q['start']].encode()):len(txt[:q['end']].encode())].decode()==q['quote']
history=[]
for p in sorted((P/'runs').iterdir()):
    file=p/'summary.json' if (p/'summary.json').exists() else p/'slice-results.json'
    history.append({'run':p.name,'output_binding':bind(file),'code_snapshots':[bind(p/'code-snapshot'/(n+'.py')) for n in MODULES]})
write('execution-history.json',{'runs':history,'all_failures_preserved':True,'original_156_scripts_unchanged':True,'old_expected_unchanged':True,'notes':['baseline full finite replay saved before any classifier edit','attempt01: five independent error types repaired but raw printed item ID and synthetic parent span order caused positive regressions; preserved','attempt02: printed item mapping/local parent scope restored; four supplementary fixtures rejected because outer source bundle fields missing; preserved','attempt03: only fixture outer envelope completed separately, no text/geometry/expected change','consistency-before-fix: only3 new fixed metadata contradiction controls; all3 failed, saved','attempt04: intermediate matching output still ignored conflicting parent source spans; explicitly superseded after ROOT independent reread','attempt05: ROOT source position correction makes known span conflicts mandatory; original43 and original12 expectations unchanged; corrected literal-order counterparts pass','preceding-position-final: only2 new reversed-source preceding-span controls, classifier SHA identical to attempt05'],'runner_history_limit':'Five classifier modules and full received inputs are snapshotted per run; wrapper source later gained additional control suites. Do not claim immutable historical wrapper bytes.'})
write('remaining-boundaries-and-null.json',{'original_four_expectation_differences':originalfail,'independent_duplicate_legacy_difference':summary['suite_summaries']['independent_legacy20']['failures'],'independent_parent_fixture_conflict_difference':summary['suite_summaries']['independent_new20']['failures'],'derived_two_parent_fixture_conflict_differences':summary['suite_summaries']['geometry_new12']['failures'],'unresolved_standard_and_source_receipts_not_blanket_removed':True,'ROOT_independent_reread_correction':'Same-SHA current[0,15] and parent[16,35] actually place current before parent, contradicting parent p1/seq1 → current p2/seq2. No separate composite coordinate system is declared. Final generic parent binding rejects this conflict instead of skipping spans. Previous intermediate 20/20 output is not final evidence of correctness.','parent_relation_vs_position_proof':'Explicit target+same-source/component is structural relation evidence; source span precedence or ancestor containment, when supplied, is an independent mandatory consistency check. Physical precedence alone does not make a parent. Missing span pairs retain frozen bounded structural role, graded without claiming independent source-order verification.','corrected_order_controls':'Consistent parent→current literal text, paragraph/sequence and source spans pass for safety and payment. Reverse parent controls and reverse price/dose preceding controls do not inherit. Original conflicting fixtures/expectations are never overwritten.','role_only_scope_limit':'Known source/component/target/sequence/paragraph/span contradictions reject the relation. Unknown coordinates do not create a new material threshold for the frozen local role interface.','future_common_interface_needs':['true original coordinates for role-only local parent and preceding projections','closed complete A450 renewal condition interface, shared across all coders','unique same-version cited standard closure and exact request-resolution receipts in joint integration'],'not_formal_accuracy':True})
write('merge-dependencies.json',{'changed_effective_functions':[{'file':x['file'],'function':x['function']} for x in diffs],'shared_unchanged':shared,'integration':'Merge only SE geometry helpers and dedicated SE relation/predicate guards onto ROOT joint candidate. Keep IFv3 __init__/_add/_units/judge and exact receipt resolver; retain SEv2 precise quote/consumer identity and boundary-evidence-only handling.','new_helpers_required_by_SE_consumer':'dimensions._se_parent_consumer_scope → RelationView._se_parent_binding → _se_current_geometry_contexts/_se_same_geometry/_se_next_geometry/_se_geometry_value','no_new_material_or_manual_release':True,'no_new_classifier_reference_title_or_record_id_whitelist':True})
five=[bind(P/(n+'.py')) for n in MODULES];payload={'manual_sha256':manual['binding']['sha256'],'five_module_sha256':[x['sha256'] for x in five]};algo=hashlib.sha256(canonical(payload)).hexdigest()
write('algorithm-bindings.json',{'version':'SEv3-geometry-sol-nonhuman-candidate','manual':manual['binding'],'five_modules':five,'algorithm_sha256':algo,'algorithm_digest_definition':payload,'only_SE_geometry_changes':True,'shared_interfaces_unchanged':shared,'no_common_material_change':True})
slice=json.loads((P/'runs/preceding-position-final/slice-results.json').read_text());assert all(c['passed'] for c in slice['results'])
for n in MODULES:assert bind(P/'runs/preceding-position-final/code-snapshot'/(n+'.py'))['sha256']==bind(P/(n+'.py'))['sha256']
write('regression-reception.json',{'identity':'non_human_development_replay_not_independent_accuracy','original156_case_N':156,'original156_matching_N':152,'original156_known_NULL_differences_N':4,'independent43_case_N':43,'independent43_matching_N':41,'independent43_known_duplicate_missing_closure_difference_N':1,'independent43_source_position_conflict_difference_N':1,'independent_new5_error_types_fixed':True,'new28_matching_N':26,'new28_case_N':28,'new28_preserved_conflicting_parent_fixture_difference_N':2,'actual_execution_case_total_in_final_bulk_run':225,'additional_meaningful_preceding_position_slice_N':2,'new_exceptions_N':0,'original156_new_regressions_N':0,'final_summary_binding':bind(FINAL/'summary.json'),'final_preceding_slice_binding':bind(P/'runs/preceding-position-final/slice-results.json'),'full77_800_4481_runs_N':0,'all_earlier_failures_preserved':True,'source_exposure_new_N':0,'ROOT_position_review_changes_recorded':True})
write('preservation-readback.json',{'SEv2_delivery_members_verified_N':len(base_seal['files']),'independent_audit_members_verified_N':len(audseal['output_members']),'input_bindings_verified_N':len(checked),'frozen_three_modules_unchanged':True,'manual_unchanged':True,'old77_800_and_production_outputs_untouched':True})
write('candidate-seal.json',{'status':'sealed_SEv3_geometry_candidate_nonhuman','at_utc':datetime.now(timezone.utc).isoformat(),'algorithm_sha256':algo,'five_modules':five,'manual':manual['binding'],'regression':bind(P/'regression-reception.json'),'new_controls':[bind(P/n) for n in ['geometry-controls-fixed-before-edit.json','refinement-controls-fixed.json','refinement-controls-interface-complete.json','consistency-controls-fixed.json','root-position-controls-fixed.json','preceding-position-controls-fixed.json']],'root_joint_integration_required':True})
members=[bind(p) for p in sorted(P.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and p.name!='delivery-seal.json']
write('delivery-seal.json',{'status':'sealed_all_candidate_outputs_excluding_self','algorithm_sha256':algo,'files':members,'file_N':len(members),'self_excluded':True})
for x in members:assert bind(x['path'])==x
print(json.dumps({'algorithm_sha256':algo,'candidate_seal':bind(P/'candidate-seal.json'),'delivery_seal':bind(P/'delivery-seal.json'),'members':len(members),'functions':len(diffs),'quotes':len(quotes),'actual_materials':len(materials),'new_source_ids':[]},ensure_ascii=False,indent=2))
