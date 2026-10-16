"""Post-run administrative receipts, never classifier inputs."""
import json,hashlib,datetime,difflib,collections
from pathlib import Path
HERE=Path(__file__).resolve().parent;BASE=HERE.parents[1];CODING=HERE.parent;V2=HERE/'versions/v2';DIM=('S','E','Ec','I','F');NAMES=('source_packet','source_receipts','evidence','relations','dimensions')
def bind(p):
 p=Path(p).resolve();raw=p.read_bytes();return{'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def read(p):return json.loads(Path(p).read_text())
def rows(p):return[json.loads(t)for t in Path(p).read_text().splitlines()if t]
def write(p,v):
 with Path(p).open('x',encoding='utf8')as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def match(b):return bind(b['path'])['sha256']==b['sha256']
report=HERE/'delivery';report.mkdir(exist_ok=False)
old_paths={'77':CODING/'rule-v19-v15-development77-first-sol/versions/v4/run77-first/predictions.jsonl','800':CODING/'rule-full4481-v2-root/run4481-first/predictions.jsonl'}
cohort_summary={};all_after={}
for cohort,oldpath in old_paths.items():
 out=HERE/f'development{cohort}-run-once';before={r['id']:r for r in rows(oldpath)};after=rows(out/'predictions.jsonl');bundles={b['source_record']['id']:b for b in rows(out/'delivered-complete-source-bundles.jsonl')};changes=[];nulls=[];counts=collections.Counter()
 for r in after:
  sid=r['id'];all_after[sid]=r;current=bundles[sid]['source_record']['text']
  for d in DIM:
   prev=before[sid]['labels'][d];value=r['labels'][d]
   if prev!=value:
    counts[d,str(prev),str(value)]+=1;changes.append({'source_id':sid,'dimension':d,'baseline_value':prev,'candidate_v1_value':value,'current_text':current,'candidate_decision':r['decisions'][d],'bundle_canonical_sha256':r['bundle_canonical_sha256']})
   if value is None:nulls.append({'source_id':sid,'dimension':d,'prior_value':prev,'candidate_v1_value':None,'current_text':current,'candidate_decision':r['decisions'][d],'material_requests':r['material_requests'],'source_requests':r['source_requests']})
 write(report/f'development{cohort}-all-changes.json',changes);write(report/f'development{cohort}-all-null-dimensions.json',nulls)
 failures=read(out/'technical-failures.json');write(report/f'development{cohort}-technical-failures.json',failures)
 output_checks=[{'binding':b,'same_sha_now':match(b)}for b in read(out/'output-bindings.json')]
 source_checks=[{'binding':b,'same_sha_now':match(b)}for b in read(HERE/f'development{cohort}-scope.json')['material_bindings']]
 code_checks=[{'binding':b,'same_sha_now':match(b)}for b in read(out/'execution.json')['code_bindings']]
 write(report/f'development{cohort}-binding-checks.json',{'outputs':output_checks,'source_materials':source_checks,'sealed_v1_code':code_checks})
 cohort_summary[cohort]={'actual_full_cohort_runs':1,'record_N':len(after),'dimension_N':5*len(after),'changed_dimension_N':len(changes),'transition_counts':[{'dimension':d,'before':a,'after':b,'N':n}for(d,a,b),n in counts.items()],'null_dimension_N':len(nulls),'technical_failure_record_N':len(failures),'S_E_Ec_label_change_N':sum(n for(d,a,b),n in counts.items()if d in ('S','E','Ec')),'all_bound_outputs_source_and_v1_code_unchanged':all(c['same_sha_now']for c in output_checks+source_checks+code_checks),'baseline_binding':bind(oldpath),'candidate_prediction_binding':bind(out/'predictions.jsonl'),'not_accuracy_or_independent_validation':True}
# All exposed semantic uncertainties remain in a separate register. Their audit
# values are not overridden by any candidate output.
auditroot=BASE/'08-audits/ai800-disagreement-semantic-root';joined=read(auditroot/'joined-review.json')['rows'];positive=read(auditroot/'full4481-rule-positive-review-sol/reviews.json');negative=read(auditroot/'common-negative30-root/reviews.json');questions=read(auditroot/'full4481-rule-positive-review-sol/scope-question-supplement.json')
boundaries=[]
for path,rs in [(auditroot/'joined-review.json',joined),(auditroot/'full4481-rule-positive-review-sol/reviews.json',positive),(auditroot/'common-negative30-root/reviews.json',negative)]:
 for a in rs:
  if a.get('review_value')is None or a.get('needs_human_review'):
   d=a.get('dimension',a.get('dim'));sid=a['source_id'];r=all_after.get(sid)
   boundaries.append({'source_id':sid,'dimension':d,'audit_review_value_preserved':a.get('review_value'),'assessment_preserved':a.get('assessment'),'audit_input_binding':bind(path),'question':a.get('human_review_question')or a.get('reason')or a.get('explanation')or a.get('assessment'),'candidate_v1_value_if_development_member':r['labels'][d]if r else 'not run','not_new_independent_reference':True})
write(report/'all-exposed-boundaries-register.json',{'items':boundaries,'scope_question_supplement':bind(auditroot/'full4481-rule-positive-review-sol/scope-question-supplement.json'),'audit_values_changed':False,'manual_boundaries_are_not_expected_labels':True})
# Compare v1 against disclosed AI omission findings only after inference.
omissions=[]
for a in joined:
 if a.get('assessment')!='规则遗漏依据' or a.get('rule')!=0:continue
 sid=a['source_id'];d=a['dimension'];r=all_after[sid]
 omissions.append({'source_id':sid,'dimension':d,'audit_value':a['review_value'],'candidate_v1_value':r['labels'][d],'current_text':a['current_text'],'audit_reason':a.get('reason'),'audit_exposed_AI_development_not_gold':True})
write(report/'v1-audit-supported-omission-status.json',{'items':omissions,'N':len(omissions),'candidate_1_N':sum(a['candidate_v1_value']==1 for a in omissions),'candidate_0_N':sum(a['candidate_v1_value']==0 for a in omissions),'formal_accuracy':False})
# Targeted v2 actual cases retain exact source binding/quotation evidence.
v2results=read(V2/'regression-run-013/results.json');residual_ids={a['source_id']for a in omissions if a['candidate_v1_value']==0}
targeted=[]
for a in v2results:
 if a['name'].startswith('source fixture '):
  sid='RECODE25-'+a['name'].split()[-1]
  if sid in residual_ids:targeted.append({'source_id':sid,**a})
write(report/'v2-remaining-v1-omission-targeted-evidence.json',{'actual_targeted_results':targeted,'full77_or800_v2_run':False,'no_projection_consumed':True,'not_independent_truth':True})
# Module diffs retain baseline and both candidate identities.
for version,where in [('v1',HERE),('v2',V2)]:
 for name in NAMES:
  baseline=CODING/'full4481-rule-production-adapter-sol'/(name+'.py');candidate=where/(name+'.py')
  delta=''.join(difflib.unified_diff(baseline.read_text().splitlines(True),candidate.read_text().splitlines(True),fromfile=str(baseline.resolve()),tofile=str(candidate.resolve())))
  (report/f'{version}-{name}-vs-frozen.patch').write_text(delta)
for name in ['relations','dimensions']:
 delta=''.join(difflib.unified_diff((HERE/(name+'.py')).read_text().splitlines(True),(V2/(name+'.py')).read_text().splitlines(True),fromfile='sealed-v1/'+name+'.py',tofile='targeted-only-v2/'+name+'.py'))
 (report/f'v2-{name}-vs-v1.patch').write_text(delta)
frozen=read(HERE/'input-bindings-before-repair.json');frozen_checks=[{'binding':b,'same_sha_now':match(b)}for b in frozen['baseline_inputs']]
write(report/'frozen-inputs-unchanged-check.json',{'checks':frozen_checks,'all_same_SHA':all(c['same_sha_now']for c in frozen_checks)})
v2binding={'version':'rule-v20-I-F-semantic-development-candidate-2-targeted-only','modules':[dict(bind(V2/(n+'.py')),module=n)for n in NAMES],'manual_binding':bind(BASE/'03-manual/full4481-common-release-20261010-root/manual.txt'),'definitions_changed':False,'full77_or800_v2_run':False,'formal_execution_authorized':False,'new_material_projection_runtime_used':False,'record_ID_or_sourceSHA_or_policy_title_or_expected_label_positive_whitelist':False,'test_labels_excluded_from_inference_semantic_units':True}
write(V2/'algorithm-bindings.json',v2binding)
regression_summary=read(V2/'regression-run-013/summary.json');neg_summary=read(V2/'negative30-diagnostic-once/summary.json');assert all(match(b)for b in regression_summary['code_bindings']+neg_summary['code_bindings'])
history=[]
for path in sorted(HERE.glob('regression-run-*/summary.json'))+sorted(V2.glob('regression-run-*/summary.json')):
 a=read(path);history.append({'path':str(path.resolve()),'binding':bind(path),'test_N':a['test_N'],'pass_N':a['pass_N'],'failure_N':a['failure_N'],'code_snapshot_available':(path.parent/'code-snapshot').is_dir()})
write(report/'development-execution-history.json',{'regression_results_preserved':history,'v2_fixture_loader_failure':bind(V2/'regression-run-010/execution-failed.json'),'initial_preparation_failure':{'scope':'prepare_development_runs administrative loader','reason':'BASE parents index error, corrected before any cohort execution','cohort_executed':False},'initial_exploratory_inline_cases':{'fixture_N_from_session_notes':13,'exact_code_binding_and_standalone_result_not_captured':'original tool transcript only; cannot call it sealed reproducible evidence'},'full_cohort_executions':cohort_summary})
summary={'identity':'nonhuman AI disclosed I/F rule-development delivery','manual_definition_sha256':v2binding['manual_binding']['sha256'],'manual_changed':False,'v1_whole_cohort_evidence':cohort_summary,'v2_targeted_test_N':regression_summary['test_N'],'v2_targeted_pass_N':regression_summary['pass_N'],'v2_targeted_failure_N':regression_summary['failure_N'],'v2_full77_or800_run_N':0,'negative30_already_exposed_check':{k:neg_summary[k]for k in ['record_N','dimension_N','audit_resolved_N','audit_unresolved_unscored_N','resolved_directional_disagreement_N']},'v1_41_audit_supported_omissions_candidate1_N':sum(a['candidate_v1_value']==1 for a in omissions),'v1_remaining0_N':sum(a['candidate_v1_value']==0 for a in omissions),'v2_targeted_prior_remaining_omission_values':[{'source_id':a['source_id'],'dimension':a['dimension'],'candidate_v2_value':a.get('actual'),'pass':a['passed']}for a in targeted],'A271_old_input_NULL_preserved':True,'neutral_projection_future_common_release_only':bind(HERE/'neutral-material-projection-candidate/release-candidate-manifest.json'),'future_projection_consumer_pending':'A271 projected bounded support can resolve §59–62 but old cited_standard stopped request remains; independent bridge audit does not claim dependency fully relieved','no_formal_LLM_partial_outputs_read':True,'not_formal_accuracy_not_human_reference':True,'frozen_input_SHA_checks_passed':all(c['same_sha_now']for c in frozen_checks),'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
write(report/'summary.json',summary)
print(json.dumps(summary,ensure_ascii=False,indent=2))
