"""Approved synthetic8 and separate prior09 15/22/20; no real unit prediction."""
import ast,copy,hashlib,json,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE/'runtime'))
import policy_coding_v27 as coder
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
phase=sys.argv[1];assert phase in {'before','after'}
output=HERE/('constructed_execution10_'+phase+'.json');assert not output.exists()
contract=json.loads((HERE/'implementation_contract_before10.json').read_text())
design=json.loads(Path(contract['approved_design']['path']).read_text())
old09=json.loads((HERE.parent/'candidate09/implementation_contract_before09.json').read_text())
fixture=HERE.parent/'candidate08/independent_review08/run_independent08.py'
nodes=[n for n in ast.parse(fixture.read_text()).body if isinstance(n,ast.FunctionDef) and n.name in {'prose','verify'}];assert len(nodes)==2
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(fixture),'exec'))
old22=json.loads(Path(old09['regressions'][0]['design_path']).read_text())['cases']
old20=json.loads(Path(old09['regressions'][1]['design_path']).read_text())['cases']
code_before={str(p):sha(p) for p in sorted((HERE/'runtime').glob('*.py'))};checks=[]
with tempfile.TemporaryDirectory(prefix='candidate10-'+phase+'-') as temp:
 for group,cases in [('new10',design['predeclared_constructs_not_executed']),('old09_15_regression',old09['cases']),('old08_22_regression',old22),('old07_20_regression',old20)]:
  for i,case in enumerate(cases):
   case_type='coverage_observation' if case['name'] in contract['case_classes']['coverage_observation'] and group=='new10' else 'source_error' if case.get('expected_source_error') else 'semantic'
   record=prose(Path(temp)/(group+'-'+str(i)),case['text'],case['prefix'])
   if case.get('expected_source_error'):
    Path(record['source']).write_text(case['text'],encoding='utf-8');record['source_sha256']=record['unit_source_sha256']=sha(record['source'])
   before=copy.deepcopy(record);result=None;error=None
   try:result=coder.code_unit(record)
   except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
   technical=verify(record,result) if result else None
   added_context_checks=[]
   if result:
    for e in result['evidence']:
     dep=e.get('context_dependency') or {}
     if dep.get('scope_mechanism10'):
      paragraph=next(p['text'] for p in record['paragraph_context'] if p['paragraph_id']==dep['paragraph_id'])
      for a in dep['antecedent_relation_anchors']:
       lo,hi=a['start_in_paragraph'],a['end_in_paragraph']
       added_context_checks.append({'role':a['role'],'passed':type(lo) is int and type(hi) is int and 0<=lo<hi<=len(paragraph) and paragraph[lo:hi]==a['text'] and dep['antecedent_start_in_paragraph']<=lo<hi<=dep['antecedent_end_in_paragraph']})
      added_context_checks.append({'role':'only_E_object_scope','passed':e['dimension']=='E' and dep['scope_usage']=='current drug object only; no preceding S/E labels or evidence inherited'})
      if group=='new10' and case_type=='semantic' and case['expected'].get('E')==1:
       roles={a['role'] for a in e.get('current_relation_anchors',[])}
       added_context_checks.append({'role':'current_example_trial_and_option_anchors','passed':{'current_explicit_method_example','current_example_trial_reference','current_no_effective_option_proposition'}<=roles})
   tech_ok=bool(technical and technical['passed'] and all(a['passed'] for a in added_context_checks))
   observation=None
   if case_type=='coverage_observation':
    fallback_triggered=bool(result and any((e.get('context_dependency') or {}).get('scope_mechanism10') for e in result['evidence']))
    observation={'original_predeclared_expected_preserved':case['expected'],'interpretation':'Original0 is a limited-coverage observation, not normative semantic gold. Only absence of the new fallback is checked.','new_fallback_triggered':fallback_triggered,'operational_contract_satisfied':error is None and result is not None and not fallback_triggered and record==before and tech_ok}
    passed=None
   elif case_type=='source_error':passed=bool(error and error['type']=='ValueError' and result is None and record==before)
   else:passed=bool(error is None and result is not None and record==before and tech_ok and all(result['labels'][d]==v for d,v in case['expected'].items()))
   checks.append({'group':group,'name':case['name'],'case_type':case_type,'expected':case['expected'],'passed':passed,'observation':observation,'error':error,'input_unchanged':record==before,'technical':technical,'antecedent_context_anchor_checks':added_context_checks,'actual_labels':result['labels'] if result else None,'prediction':result,'source_sha256':sha(record['source']),'candidate_sha256':sha(record['candidate_file'])})
code_after={str(p):sha(p) for p in sorted((HERE/'runtime').glob('*.py'))};assert code_before==code_after
pres=json.loads((HERE/'preservation_before10.json').read_text())['files_sha256'];assert all(sha(p)==h for p,h in pres.items())
summary=[]
for group in ['new10','old09_15_regression','old08_22_regression','old07_20_regression']:
 cases=[c for c in checks if c['group']==group]
 summary.append({'group':group,'n':len(cases),'semantic_n':sum(c['case_type']=='semantic' for c in cases),'semantic_pass_n':sum(c['case_type']=='semantic' and c['passed'] is True for c in cases),'source_error_n':sum(c['case_type']=='source_error' for c in cases),'source_error_pass_n':sum(c['case_type']=='source_error' and c['passed'] is True for c in cases),'observation_n':sum(c['case_type']=='coverage_observation' for c in cases),'observation_contract_satisfied_n':sum(c['case_type']=='coverage_observation' and c['observation']['operational_contract_satisfied'] for c in cases)})
report={'phase':phase,'at_utc':datetime.now(timezone.utc).isoformat(),'runtime_version':coder.VERSION,'contract_sha256':sha(HERE/'implementation_contract_before10.json'),'approved_design_sha256':sha(contract['approved_design']['path']),'runner_sha256':sha(__file__),'fixture_code_sha256':sha(fixture),'runtime_sha256_before':code_before,'runtime_sha256_after':code_after,'code_unchanged_during_execution':True,'previous_files_unchanged':True,'previous_file_n':len(pres),'actual_temporary_TXT_JSON':True,'authenticators_mocked':False,'real03049_or_other_real_prediction':False,'real21_33_full_model_calls':False,'summary':summary,'checks':checks,'all_scored_cases_passed':all(c['passed'] is True for c in checks if c['case_type']!='coverage_observation'),'all_observation_contracts_satisfied':all(c['observation']['operational_contract_satisfied'] for c in checks if c['case_type']=='coverage_observation')}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'phase':phase,'summary':summary,'failures':[{'group':c['group'],'name':c['name'],'expected':c['expected'],'actual':c['actual_labels'],'error':c['error']} for c in checks if c['passed'] is False],'report_sha256':sha(output)},ensure_ascii=False))
