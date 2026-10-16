"""Actual4924 schema/context seam only; no statistics, model calls, adoption or DOCX."""
from pathlib import Path
import ast,hashlib,importlib.util,json,sys,datetime
P=Path(__file__).resolve().parent;R=P.parents[1];M=R/'manuscript-update-20261008';S=R/'statistics';sys.path.insert(0,str(S))
import candidate03_reconciled_execution_profile_v2 as profile
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
bind=lambda p:{'path':str(Path(p).resolve()),'sha256':sha(p)}
def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
def fs(path):
 tree=ast.parse(path.read_text());out={}
 for node in tree.body:
  if isinstance(node,ast.FunctionDef):out[node.name]=ast.dump(node,include_attributes=False)
  elif isinstance(node,ast.ClassDef):
   for child in node.body:
    if isinstance(child,ast.FunctionDef):out[node.name+'.'+child.name]=ast.dump(child,include_attributes=False)
 return out

def main():
 output=P/'actual_context_and_dual_ID_seam_QA.json';assert not output.exists(),'Preserve any prior actual seam result'
 full_binding={'path':str(R/'llm-candidate03-development/full-corpus-candidate03-material-v14-single-unit-reconciled-development/full_development_binding.json'),'sha256':'51ff6fe7febd6f23c823dffe3d1224716ceda4e9594e2c86ab49b1d42ff4ee9d'}
 report={'status':'RUNNING_ACTUAL_CONTEXT_SCHEMA_SEAM_ONLY','started_at':datetime.datetime.now().astimezone().isoformat(),'script':bind(__file__),'full_execution_binding':full_binding,'statistics_computed':False,'DOCX_created':False,'formal_adoption':False,'labels_changed':False}
 try:
  a=load('schema_adapter_v3',M/'measurement-adapter-v3/assemble_manuscript_payload_r3.py');n=load('schema_numeric_v3',M/'measurement-adapter-v3/independent_verify_adopted_payload.py')
  full,*_=profile.closed_header(full_binding);io=a.BoundIO();execution=profile.verify_complete(full_binding,io)
  base=json.loads((R/'methods-20261008/development-complete-bindings/rules-v36.2-development-bindings.json').read_text());cfg={'reference_manifest':base['reference_manifest'],'candidate_reference':base['existing_candidate_reference'],'material_version':'v14'}
  manifest,rule,blind,groups,sample,refs=a.context(cfg,io)
  rulebinding=base['methods']['rules-v36.2']['output'];rules=a.BoundIO.rule_predictions(io,rulebinding,rule)
  rule_labels=a.labels(rules,rule);llmrows=io.rows(full['output']);llm_labels=a.labels(llmrows,rule)
  assert all(row['prediction']['unit_text_sha256']==a.sha_text(blind[rid]['text']) for rid,row in rules.items())
  n_io=n.Inputs();n.reconciled_execution_header({'execution_profile':profile.PROFILE,'method_id':profile.METHOD,'execution_binding':full_binding,'output':full['output']},n_io)
  source2,blind2,groups2,probability2,weights2,refs2=n.context_inputs(cfg,manifest,n_io)
  rules2=n_io.rule_prediction_records(rulebinding,source2);nrule=n.extract_labels(rules2,source2)
  llm2=n_io.records(full['output'],labels=True);nllm=n.extract_labels(llm2,source2)
  assert rule==source2 and blind==blind2 and groups==groups2 and rules==rules2
  assert rule_labels==nrule and llm_labels==nllm and all(refs[k]==refs2[k] for k in ('A','C'))
  assert set(probability2)=={rid for rid,x in sample.items() if x['component']=='probability_canonical'}
  assert all(weights2[rid]==a.F(sample[rid]['canonical_frame_N'],60) for rid in probability2)
  maps=[(rid,x['original_id']) for rid,x in sorted(rule.items())]
  assert len(maps)==len(set(x[0] for x in maps))==len(set(x[1] for x in maps))==4924 and set(rule)==set(blind)
  olda,newa=fs(M/'measurement-adapter-v2/assemble_manuscript_payload_r3.py'),fs(M/'measurement-adapter-v3/assemble_manuscript_payload_r3.py')
  oldn,newn=fs(M/'measurement-adapter-v2/independent_verify_adopted_payload.py'),fs(M/'measurement-adapter-v3/independent_verify_adopted_payload.py')
  diff_a=[k for k in olda if olda[k]!=newa[k]];diff_n=[k for k in oldn if oldn[k]!=newn[k]]
  assert diff_a==['context','assemble'] and diff_n==['context_inputs','verify']
  assert olda['BoundIO.rows']==newa['BoundIO.rows'] and oldn['Inputs.records']==newn['Inputs.records']
  oldfreeze=json.loads((R/'methods-20261008/candidate03-reconciled-statistics-preparation-v2/preparation_freeze.json').read_text())
  assert all(sha(b['path'])==b['sha256'] for b in oldfreeze['required_code_bindings'])
  io.unchanged();n_io.unchanged()
  report.update(status='PASS_ACTUAL_CONTEXT_SCHEMA_SEAM_ONLY',all_schema_seam_checks_pass=True,actual_execution_reconstruction=execution,source_n=len(rule),canonical_id_unique_n=len({x[0] for x in maps}),original_source_id_unique_n=len({x[1] for x in maps}),blind_input_one_to_one_n=len(blind),rule_prediction_pairs_exactly_matched_n=len(rules),rule_original_review_id_matches_n=len(rule),source_and_rule_prediction_pair_canonical_sha256=hashlib.sha256(json.dumps(maps,ensure_ascii=False,separators=(',',':')).encode()).hexdigest(),A_C_reference_n_each=240,candidate_reference_n=240,probability_n=180,challenge_n=60,all_prediction_labels_binary_and_complete=True,independent_checker_context_and_rule_mapping_equal=True,independent_checker_weight_and_AC_reference_equal=True,strict_LLM_reference_readers_AST_unchanged=True,all_v2_frozen21_code_SHA_unchanged=True,v3_changed_existing_adapter_functions=diff_a,v3_changed_existing_checker_functions=diff_n,v3_added_adapter_methods=sorted(set(newa)-set(olda)),v3_added_checker_methods=sorted(set(newn)-set(oldn)),bindings=[bind(M/'measurement-adapter-v3/assemble_manuscript_payload_r3.py'),bind(M/'measurement-adapter-v3/independent_verify_adopted_payload.py'),bind(S/'prepare_candidate03_reconciled_development_bindings_v3.py'),manifest['material']['rule_inputs'],manifest['material']['llm_inputs'],rulebinding],limits='Actual execution/source/reference/schema seam only. No manuscript payload has been assembled, no numerical QA or5000 statistics has been performed, and no method has been adopted.')
 except Exception as exc:
  report.update(status='FAIL_ACTUAL_CONTEXT_SCHEMA_SEAM',all_schema_seam_checks_pass=False,error_type=type(exc).__name__,error=str(exc));raise
 finally:
  report['ended_at']=datetime.datetime.now().astimezone().isoformat();output.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 print(json.dumps({'status':report['status'],'report':bind(output),'n':report.get('source_n')},ensure_ascii=False))
if __name__=='__main__':main()
