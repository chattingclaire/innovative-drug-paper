from pathlib import Path
import ast
R=Path(__file__).resolve().parents[2]
A=Path(__file__).resolve().parent
V=R/'06-coding/rule-five-dimension-joint-root/versions/joint-v11-protected-data-role-sol'
B=V.parent/'joint-v10-if-e-combined-v2-root'
s=(B/'run_finite_controls.py').read_text()
s=s.replace("V=O.parent/'joint-v9-generic-relationship-sol'","OLDV9=O.parent/'joint-v9-generic-relationship-sol';V=O.parent/'joint-v10-if-e-combined-v2-root'")
s=s.replace("AUD=R/'08-audits/v10-if-e-combination-v2-root'","AUD=R/'08-audits/v11-protected-data-role-repair-sol'")
s=s.replace("extra=[V/'supplemental-controls","extra=[OLDV9/'supplemental-controls").replace(",V/'supplemental-controls",",OLDV9/'supplemental-controls")
needle="# Entire authorized selection is fixed; failures and pending examples retained."
s=s.replace(needle,"extra.append(AUD/'new-role-controls-fixed-before-edit.json');roles=json.loads(extra[-1].read_bytes());raw['cases'].extend(roles['real_cases']);synthetics['cases'].extend(roles['cases'])\n"+needle)
s=s.replace("SEc_complete_decisions_equal","SEEcF_complete_decisions_equal").replace("for d in ['S','Ec']","for d in ['S','E','Ec','F']").replace("SEc_complete_decision_mismatch","SEEcF_complete_decision_mismatch")
s=s.replace("if r['kind']!='v10_IF_relationship'","if r['kind']!='v11_protected_data_I_relationship'")
s=s.replace("'input_unchanged':v.unit==before","'input_unchanged':v.unit==before,'private_v11_I_requests':copy.deepcopy(getattr(v,'v11_protected_data_requests',[]))")
s=s.replace("path.startswith(('v9_','v10_'))","path.startswith(('v9_','v10_','v11_'))")
needle=" results.append(row)"
extension=""" if c.get('must_not_add_v11_positive') and 'candidate' in row:
  row['no_unproved_v11_positive']=not any(r['kind']=='v11_protected_data_I_relationship' for r in row['candidate']['relations'])
  row['passed']=row['passed'] and row['no_unproved_v11_positive']
 if 'candidate' in row:
  row['private_v11_request_I_only']=all(d['kind']=='v11_protected_data_I_dependency' and d['affected_dimensions']==['I'] and d['request']['dimensions']==['I'] and d['request']['affected_dimensions']==['I'] for d in row['candidate']['private_v11_I_requests'])
  row['gate_outside_private_request_empty']=None if pure.gate(b['source_record']['text']) else not row['candidate']['private_v11_I_requests']
 results.append(row)"""
assert s.count(needle)==2
s=s.replace(needle,extension,1)
extension2=extension.replace("pure.gate(b['source_record']['text'])","pure.gate(c['semantic_input']['text'])")
s=s.replace(needle,extension2,1) if False else s
# Locate the still-original append in the synthetic section only.
i=s.index("for c in synthetics['cases']:");s=s[:i]+s[i:].replace(needle,extension2,1)
s=s.replace("'new_E_counter_control_N':24","'new_E_counter_control_N':24,'new_v11_role_control_N':16,'local_execution_limit':2,'production_classifier_calls':0,'model_calls':0,'private_v11_request_non_I':[c['name'] for c in results if c.get('private_v11_request_I_only') is False],'unproved_v11_positive':[c['name'] for c in results if c.get('no_unproved_v11_positive') is False]")
s=s.replace("'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'controls'","'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'gate':bind(O/'static_gate.py'),'driver':bind(Path(__file__)),'controls'",1)
# No control execution here.
ast.parse(s);(V/'run_finite_controls.py').write_text(s)
print('finite driver prepared; classifier executions=0')
