"""Post-freeze descriptive audit; reference labels never enter inference."""
from pathlib import Path
from collections import Counter
import datetime,hashlib,json,re
R=Path(__file__).resolve().parent;B=R.parent
D=('S','E','Ec','I','F')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text())
def jl(p):return {r['id']:r for r in map(json.loads,Path(p).read_text().splitlines())}
def save(name,x):(R/name).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def binding(p):return {'path':str(Path(p).resolve()),'sha256':sha(p)}
freeze=read(R/'candidate_freeze.json');ip=Path(freeze['input']['path'])
oldpath=Path(freeze['parent_prediction']['path']);newpath=R/'all_predictions_material_v14.jsonl'
inputs=jl(ip);old=jl(oldpath);new=jl(newpath);run=read(newpath.with_suffix('.run.json'))
assert list(inputs)==list(old)==list(new) and len(inputs)==4924
reasons={
 'V362_F_verified_actual_renewal_condition':'来源验证父条款将当前实质条件直接连接药品实际简易续约及明确有效期，构成原保障连续性条件；不是申请或重新谈判机会。不从父句复制Ec等其他维度。',
 'V362_S_explicit_drug_treatment_safety_control':'当前安全管理谓词明确支配含化疗的并列治疗对象；化疗为药物治疗。仅取该药物治疗安全依据，不把手术/一般服务质量统一纳入。依据属other_safety。'}
changes=[];flip=Counter()
for rid,r in new.items():
 a=old[rid]['prediction'];z=r['prediction']
 changed=[d for d in D if a['labels'][d]!=z['labels'][d]]
 if not changed:continue
 entries=[]
 for d in changed:
  es=[e for e in z['evidence'] if e['dimension']==d and e['rule'].startswith('V362_')]
  assert es
  entries.append({'dimension':d,'old':a['labels'][d],'new':z['labels'][d],
                  'reasons':sorted({reasons[e['rule']] for e in es}),'evidence':es})
  flip[d]+=1
 changes.append({'id':rid,'text':inputs[rid]['input']['unit_text'],'dimension_changes':entries})
assert dict(flip)=={'S':1,'F':25}
save('all_changes_vs_v36.1.json',{'stage':'development_only','old':binding(oldpath),'new':binding(newpath),
  'changed_unit_n':len(changes),'changed_dimension_n':sum(flip.values()),'flip_counts':dict(flip),'records':changes})

manifest_path=B/'statistics/final_bindings_v14_CONFIRMED_r3.json';manifest=read(manifest_path)
ref_bindings={**manifest['references'],'candidate':binding(B/'statistics/final-v14/candidate_reference.jsonl')}
assert ref_bindings['candidate']['sha256']==read(B/'statistics/final-v14/output_freeze.json')['files']['candidate_reference.jsonl']
refs={}
for k,spec in ref_bindings.items():
 assert sha(spec['path'])==spec['sha256'];refs[k]=jl(spec['path'])
assert len(refs['A'])==240 and set(refs['A'])==set(refs['C'])==set(refs['candidate'])
sampling=manifest['sampling_design'];assert sha(sampling['path'])==sampling['sha256']
design=read(sampling['path']);sample={r['original_id']:r for r in design['sample']}
comparisons={}
affected=[]
for name,ref in refs.items():
 counters={};changes_ref=[]
 for component in ['probability_canonical','enriched_challenge']:
  chosen=[rid for rid in ref if sample[rid]['component']==component]
  dims={}
  for d in D:
   transition=Counter();before=Counter();after=Counter()
   for rid in chosen:
    y=ref[rid]['labels'][d];a=old[rid]['prediction']['labels'][d];z=new[rid]['prediction']['labels'][d]
    before[('TP' if y else 'FP') if a else ('FN' if y else 'TN')]+=1
    after[('TP' if y else 'FP') if z else ('FN' if y else 'TN')]+=1
    typ='improved' if a!=y and z==y else 'regressed' if a==y and z!=y else 'unchanged_agreement' if z==y else 'unchanged_disagreement'
    transition[typ]+=1
    if a!=z:changes_ref.append({'id':rid,'dimension':d,'old':a,'new':z,'reference':y,'transition':typ,'component':component})
   dims[d]={'n':len(chosen),'old_confusion':dict(before),'new_confusion':dict(after),'transitions':dict(transition)}
  counters[component]=dims
 comparisons[name]={'components':counters,'changed_case_dimensions':changes_ref,
                    'improved_n':sum(x['transition']=='improved' for x in changes_ref),
                    'regressed_n':sum(x['transition']=='regressed' for x in changes_ref)}
 affected.extend(x['id'] for x in changes_ref)
save('complete_exposed240_improvements_regressions_PRIVATE.json',{'stage':'post_exposure_development_only',
 'human_gold':False,'sample_n':240,'reference_bindings':ref_bindings,'sampling_design_binding':sampling,
 'interpretation':'Complete 240×5 transition accounting against each AI reference. Probability180/challenge60 remain separate; no population accuracy or independent validation claim.',
 'comparisons':comparisons,'changed_units_outside_reference_n':sum(x['id'] not in refs['A'] for x in changes),
 'no_labels_modified':True})

metadata=manifest['metadata'];assert sha(metadata['path'])==metadata['sha256']
meta={Path(r['original_file']).stem:r for r in read(metadata['path'])['rows']}
group={rid:meta[r['input']['original_file_stem']]['analysis_group'] for rid,r in inputs.items()}
tables={}
for g in ['NMPA','NHSA','NHC','GOV']:
 ids=[rid for rid in inputs if group[rid]==g]
 counts={d:sum(new[rid]['prediction']['labels'][d] for rid in ids) for d in D}
 cells={f'F{f}_Ec{e}':sum(new[rid]['prediction']['labels']['F']==f and new[rid]['prediction']['labels']['Ec']==e for rid in ids) for f in (0,1) for e in (0,1)}
 tables[g]={'n':len(ids),'five_dimension_counts':counts,'F_Ec_four_cells':cells};assert sum(cells.values())==len(ids)
save('frozen_metadata_group_counts_and_F_Ec.json',{'status':'postfreeze_descriptive_development_output','metadata':metadata,'prediction':binding(newpath),
 'group_assignment':'Exact original_file_stem join to metadata original_file stem; analysis_group used without title-prefix inference.',
 'three_department_n':4481,'GOV_n':443,'tables':tables})

checks={
 'all_4924_unique_ids_and_order_unchanged':list(inputs)==list(old)==list(new),
 'original_ids_unchanged':all(inputs[rid]['original_id']==old[rid]['original_id']==new[rid]['original_id'] for rid in inputs),
 'all_five_dimensions_binary':all(set(r['prediction']['labels'])==set(D) and all(type(v) is int and v in (0,1) for v in r['prediction']['labels'].values()) for r in new.values()),
 'zero_pending':run['pending_n']==0,
 'input_sha_unchanged':sha(ip)==freeze['input']['sha256']==run['input_sha256'],
 'all_original_text_sha_unchanged':all(r['prediction']['unit_text_sha256']==hashlib.sha256(inputs[rid]['input']['unit_text'].encode()).hexdigest() for rid,r in new.items()),
 'all_literal_evidence_and_suppressions':all(inputs[rid]['input']['unit_text'][e['start']:e['end']]==e['text'] for rid,r in new.items() for e in r['prediction']['evidence']+r['prediction']['suppressions'] if all(k in e for k in ('start','end','text'))),
 'new_code_frozen':all(sha(p)==s for p,s in freeze['production_code_sha256'].items()),
 'v36_1_code_frozen':all(sha(p)==s for p,s in read(freeze['parent_freeze']['path'])['production_code_sha256'].items()),
 'v36_1_freeze_and_output_unchanged':sha(freeze['parent_freeze']['path'])==freeze['parent_freeze']['sha256'] and sha(oldpath)==freeze['parent_prediction']['sha256'],
 'all_source_candidate_files_unchanged':all(sha(p)==s for p,s in run['actual_source_and_candidate_sha256'].items()),
 'manuals_unchanged':all(sha(p)==s for p,s in freeze['manuals'].items()),
 'frozen33_controls_unchanged':sha(freeze['preimplementation_controls']['path'])==freeze['preimplementation_controls']['sha256'],
 'frozen33_controls_pass':read(R/'constructed_controls_results.json')['all_checks_pass'],
 'inherited67_controls_pass':read(R/'inherited67_controls.json')['all_checks_pass'],
 'inherited19_controls_pass':read(R/'legacy_v35_controls.json')['all_checks_pass'],
 'source_binding9_controls_pass':read(R/'source_binding_controls.json')['all_checks_pass'],
 'E_Ec_I_labels_all_unchanged':all(old[rid]['prediction']['labels'][d]==r['prediction']['labels'][d] for rid,r in new.items() for d in ['E','Ec','I']),
 'graph_case_labels_unchanged':old['RECODE25-02072']['prediction']['labels']==new['RECODE25-02072']['prediction']['labels'],
 'only_authorized_S_F_new_rules':all(e['rule'] in reasons for r in new.values() for e in r['prediction']['evidence'] if e['rule'].startswith('V362')),
 'new_S_is_other_safety_not_quality_extension':all(e['safety_basis']=='other_safety' for r in new.values() for e in r['prediction']['evidence'] if e['rule']=='V362_S_explicit_drug_treatment_safety_control'),
 'complete_reference_transition_accounting':all(sum(z['transitions'].values())==z['n'] for x in comparisons.values() for ds in x['components'].values() for z in ds.values()),
 'all_reference_files_unchanged':all(sha(s['path'])==s['sha256'] for s in ref_bindings.values()),
 'all_groups_from_frozen_metadata':sum(x['n'] for x in tables.values())==4924,
}
code=(R/'runtime/rules_bounded_v36_2.py').read_text()
checks['new_code_no_case_department_or_reference_values']=not re.search(r'RECODE25-|NMPA|NHSA|NHC|PRIVATE|statistics/|reference\[',code)
checks['new_semantic_module_no_reference_file_io']=not re.search(r'\bopen\(|read_text\(|read_bytes\(|json\.load',code)
assert all(checks.values()),checks
save('final_QA.json',{'all_checks_pass':True,'check_n':len(checks),'checks':checks,'n':4924,'changed_unit_n':len(changes),'changed_dimension_n':sum(flip.values()),
 'run_literal_checks':run['checks'],'not_independent_validation':True,'new_output':binding(newpath),
 'source_authentication':'Actual source/candidate SHA and target binding plus supplied parent authentication; semantic IDs never select labels.',
 'parser_notes':'Existing pypdf wrong-pointing-object warnings did not cause authentication or full-run checks to fail.'})
save('final_candidate_binding.json',{'status':'sealed_bounded_development_candidate_no_further_automatic_rule_changes',
 'version':freeze['version'],'runtime_dir':str(R/'runtime'),'freeze':binding(R/'candidate_freeze.json'),
 'prediction':binding(newpath),'run':binding(newpath.with_suffix('.run.json')),'input':binding(ip),'QA':binding(R/'final_QA.json'),
 'changes':binding(R/'all_changes_vs_v36.1.json'),'complete_development_comparison':binding(R/'complete_exposed240_improvements_regressions_PRIVATE.json'),
 'reproduce_script':binding(R/'reproduce_v36_2.sh'),'not_independent_validation':True,
 'exposed240_used_for_development':True,'reference_labels_edited':False,'scope_closed':True,'audit_script_sha256':sha(__file__)})
print(json.dumps({'n':4924,'changed_unit_n':len(changes),'changes_by_dimension':dict(flip),'QA_check_n':len(checks),
                 'new_sha256':sha(newpath),'freeze_sha256':sha(R/'candidate_freeze.json'),
                 'development_transitions':{n:{k:x[k] for k in ['improved_n','regressed_n']} for n,x in comparisons.items()},
                 'group_counts':tables},ensure_ascii=False))
