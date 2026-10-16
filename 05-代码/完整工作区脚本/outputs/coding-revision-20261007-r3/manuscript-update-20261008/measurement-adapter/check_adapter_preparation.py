"""Preparation checks only: synthetic arithmetic/guards, never an adoption run."""
from pathlib import Path
from fractions import Fraction as F
import importlib.util, json, hashlib, tempfile, subprocess, sys

D=Path(__file__).parent
spec=importlib.util.spec_from_file_location('measurement_adapter',D/'assemble_manuscript_payload_r3.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
checks={}
def check(name,value):
    assert value,name
    checks[name]=True
def rejected(name,call):
    try: call()
    except a.GateError: checks[name]=True
    else: raise AssertionError(name)

check('31_automatic_plus8_manual_unique',len(a.AUTO)==31 and len(a.MANUAL)==8 and len(set(a.AUTO+a.MANUAL))==39)
m=a.exact_metrics([F(4),F(2),F(1),F(3)])
check('synthetic_nontrivial_exact_metrics',m=={'kappa':F(2,5),'precision':F(2,3),'recall':F(4,5),'f1':F(8,11)})
check('all_negative_zero_denominators_NA',all(x is None for x in a.exact_metrics([F(0),F(0),F(0),F(60)]).values()))
check('rare_perfect_point_not_undefined',a.exact_metrics([F(1),F(0),F(0),F(59)])['kappa']==1)
check('null_never_formatted_as_one',a.number_text(None)=='NA')
check('negative_kappa_retained',a.exact_metrics([F(0),F(1),F(1),F(0)])['kappa']==-1)
check('fraction_direction_exact_tie_policy',a.sign(F(0))==0 and a.sign(F(1,10**30))==1 and a.sign(F(-1,10**30))==-1)
rows={g:{d:1 if d in ('S','Ec','F') else 0 for d in a.DIMS} for g in a.GROUPS}
profiles=a.full_profiles({'rules':rows,'LLM':rows},{g:g for g in a.GROUPS})
check('synthetic_profiles_six_rows',len(profiles)==6)
check('every_exact_q_row_sums_one',all(sum(F(z['exact_fraction']) for z in p['dimensions'].values())==1 for p in profiles))
check('joint_and_condition_denominator',all(p['Ec_F']['joint']==p['Ec_F']['Ec']==1 and p['Ec_F']['P_F_given_Ec']['exact_fraction']=='1' for p in profiles))
check('percent_rounding_does_not_force_display_sum100',all(a.number_text(100*F(p['dimensions']['S']['exact_fraction']),2)=='33.33' for p in profiles))
rejected('pending_binary_label_rejected',lambda:a.labels({'x':{'labels':{d:(None if d=='E' else 0) for d in a.DIMS}}},['x']))
rejected('boolean_not_integer_label',lambda:a.labels({'x':{'labels':{d:False for d in a.DIMS}}},['x']))
with tempfile.TemporaryDirectory(prefix='adapter-unit-',dir=D) as tmp:
    f=Path(tmp)/'tiny.txt';f.write_text('synthetic only')
    b={'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()};io=a.BoundIO();io.verify(b)
    f.write_text('changed synthetic only')
    rejected('SHA_mismatch_rejected',lambda:io.verify(b))
    rejected('input_changed_before_delivery_rejected',io.unchanged)
    f=Path(tmp)/'rows.jsonl';f.write_text('{"id":"x"}\n{"id":"x"}\n')
    rejected('duplicate_prediction_ID_rejected',lambda:a.BoundIO().rows({'path':str(f),'sha256':a.digest(f)}))
    # Only the genuine PENDING configuration is used end-to-end.
    proc=subprocess.run([sys.executable,str(D/'assemble_manuscript_payload_r3.py'),'--adoption',str(D/'采用方法_PENDING.json'),'--out',str(Path(tmp)/'gate'),'--check-only'],capture_output=True,text=True)
    gate=json.loads((Path(tmp)/'gate/gate_report.json').read_text())
    check('pending_gate_returns_exit2',proc.returncode==2)
    check('pending_gate_opens_no_prediction_or_statistics',gate['prediction_or_statistical_files_opened'] is False)
    check('pending_gate_lists39_unresolved_fields',len(gate['remaining_fields'])==39)
    check('pending_gate_produces_no_payload_or_DOCX',not list(Path(tmp).rglob('*.docx')) and not list(Path(tmp).rglob('manuscript_measurement_payload.json')))
report={'status':'PASS_PREPARATION_ONLY','checks':checks,'check_n':len(checks),'full_adopted_method_run_performed':False,'actual_payload_independent_QA_performed':False,'synthetic_tests_are_not_statistical_evidence':True,'no_DOCX_generated_or_modified':True,'no_candidate03_results_read':True,'script':{'path':str((D/'assemble_manuscript_payload_r3.py').resolve()),'sha256':a.digest(D/'assemble_manuscript_payload_r3.py')},'checker':{'path':str(Path(__file__).resolve()),'sha256':a.digest(__file__)}}
(D/'preparation_QA.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
