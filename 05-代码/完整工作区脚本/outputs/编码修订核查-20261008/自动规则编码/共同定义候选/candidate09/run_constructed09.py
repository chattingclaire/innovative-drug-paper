"""Only mechanism09 constructs and original22/20 mechanical regressions."""
import ast,copy,hashlib,json,sys,tempfile
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'))
import policy_coding_v27 as coder
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
phase=sys.argv[1];assert phase in {'before','after'}
output=HERE/('constructed_execution09_'+phase+'.json');assert not output.exists()
contract=json.loads((HERE/'implementation_contract_before09.json').read_text())
fixture=HERE.parent/'candidate08/independent_review08/run_independent08.py'
tree=ast.parse(fixture.read_text());nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {'prose','verify'}]
assert len(nodes)==2
exec(compile(ast.Module(body=nodes,type_ignores=[]),str(fixture),'exec'))
old22=json.loads(Path(contract['regressions'][0]['design_path']).read_text())['cases']
old20=json.loads(Path(contract['regressions'][1]['design_path']).read_text())['cases']
code_before={str(p):sha(p) for p in sorted((HERE/'runtime').glob('*.py'))}
checks=[]
with tempfile.TemporaryDirectory(prefix='candidate09-'+phase+'-') as temp:
 for group,cases in [('new09',contract['cases']),('independent08_22_regression',old22),('independent07_20_regression',old20)]:
  for i,case in enumerate(cases):
   record=prose(Path(temp)/(group+'-'+str(i)),case['text'],case['prefix'])
   if case.get('expected_source_error'):
    Path(record['source']).write_text(case['text'],encoding='utf-8');record['source_sha256']=record['unit_source_sha256']=sha(record['source'])
   before=copy.deepcopy(record);result=None;error=None
   try:result=coder.code_unit(record)
   except Exception as exc:error={'type':type(exc).__name__,'message':str(exc)}
   technical=verify(record,result) if result else None
   if case.get('expected_source_error'):
    passed=bool(error and error['type']=='ValueError' and result is None and record==before)
   else:
    passed=bool(error is None and result is not None and record==before and technical['passed'] and all(result['labels'][d]==v for d,v in case['expected'].items()))
   mechanism={}
   if result is not None and group=='new09':
    if case['name'].startswith('non_drug_'):
     mechanism['active_drug_objects_not_non_drug_substring']=all(record['unit_text'][a['start']-1:a['start']]!='非' for e in result['evidence'] if e['dimension']=='E' for a in e.get('current_relation_anchors',[]) if a['role']=='current_drug_object')
    if case['name'] in {'biaoshu_truth_E','biaoshu_truth_I','format_check_and_improvement_truth'}:
     mechanism['actual_biaoshu_truth_reference_anchor']=any(a['role']=='current_explicit_quoted_proposition_reference' and '表述' in a['text'] for e in result['evidence'] for a in e.get('current_relation_anchors',[]))
    if case['name'] in {'copy_completion_other_verb','spelling_check_I','referenced_wording_check_without_copy','format_check_and_effect_truth','format_check_and_improvement_truth','format_check_and_external_effect'}:
     mechanism['explicit_wording_check_relationship_recorded']=bool(result.get('quoted_format_operations09',result.get('quoted_format_operations08')))
    passed=passed and all(mechanism.values())
   checks.append({'group':group,'name':case['name'],'expected':case['expected'],'expected_source_error':bool(case.get('expected_source_error')),'passed':passed,'error':error,'input_unchanged':record==before,'technical':technical,'mechanism_checks':mechanism,'actual_labels':result['labels'] if result else None,'prediction':result,'source_sha256':sha(record['source']),'candidate_sha256':sha(record['candidate_file'])})
code_after={str(p):sha(p) for p in sorted((HERE/'runtime').glob('*.py'))};assert code_before==code_after
pres=json.loads((HERE/'candidate08_preservation_before09.json').read_text())['files_sha256'];assert all(sha(p)==h for p,h in pres.items())
summary=[{'group':group,'n':sum(c['group']==group for c in checks),'pass_n':sum(c['group']==group and c['passed'] for c in checks)} for group in ['new09','independent08_22_regression','independent07_20_regression']]
report={'phase':phase,'at_utc':datetime.now(timezone.utc).isoformat(),'runtime_version':coder.VERSION,'contract_sha256':sha(HERE/'implementation_contract_before09.json'),'fixture_code_sha256':sha(fixture),'runner_sha256':sha(__file__),'runtime_sha256_before':code_before,'runtime_sha256_after':code_after,'code_unchanged_during_execution':True,'original08_files_unchanged':True,'original08_preserved_n':len(pres),'actual_temporary_TXT_JSON':True,'authenticators_mocked':False,'real_policy_or_labels_read':False,'real21_33_full_model_calls':False,'summary':summary,'checks':checks,'all_passed':all(c['passed'] for c in checks)}
output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'phase':phase,'summary':summary,'failures':[{'group':c['group'],'name':c['name'],'expected':c['expected'],'actual':c['actual_labels'],'mechanism_checks':c['mechanism_checks'],'error':c['error']} for c in checks if not c['passed']],'report_sha256':sha(output)},ensure_ascii=False))
