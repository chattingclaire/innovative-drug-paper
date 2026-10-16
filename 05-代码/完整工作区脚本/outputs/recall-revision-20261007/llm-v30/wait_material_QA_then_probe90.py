"""Authorized conditional probe launcher; never starts whole-corpus production."""
from pathlib import Path
import hashlib,json,subprocess,sys,time
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
EXPECTED_INPUT='6fa91f237c8762fb117cb6c920d6a689dd65ee35f3b938db2f0a569bf9b965b8'
EXPECTED_PROMPT='5b8afc4459839ceb77bb3e1ff78e42f6bf81379c3316cb1ef6d776fca90d285d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def scalars(x):
 if isinstance(x,dict):
  for z in x.values():yield from scalars(z)
 elif isinstance(x,list):
  for z in x:yield from scalars(z)
 else:yield x
def strip_blind_identifiers(x):
 if isinstance(x,dict):return {k:strip_blind_identifiers(v) for k,v in x.items() if k not in {'id','unit_id'}}
 if isinstance(x,list):return [strip_blind_identifiers(v) for v in x]
 return x
def material_key(r):return json.dumps(strip_blind_identifiers(r),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def main():
 qa=BASE/'source_context_completion_final_QA.json';full=BASE/'effective_blind_inputs_v30.jsonl';packet=BASE/'blind90_completed_material.jsonl';prompt=HERE/'完整系统提示词-v30-候选02.txt';assert sha(prompt)==EXPECTED_PROMPT
 print(json.dumps({'status':'waiting_for_source_context_QA','expected_full_input_sha256':EXPECTED_INPUT,'no_model_calls_yet':True}),flush=True)
 deadline=time.time()+1800
 while time.time()<deadline:
  if qa.exists():
   try:d=json.loads(qa.read_text())
   except (ValueError,OSError):time.sleep(3);continue
   states=[str(v).lower() for v in scalars(d) if isinstance(v,str)]
   if any(x in {'passed','pass','success'} or x.startswith('passed_') for x in states) and EXPECTED_INPUT in list(scalars(d)) and sha(full)==EXPECTED_INPUT:break
  time.sleep(5)
 else:raise SystemExit('Source QA gate did not pass in 30 minutes; no model calls started.')
 source_rows=[json.loads(l) for l in full.read_text().splitlines() if l.strip()];probe_rows=[json.loads(l) for l in packet.read_text().splitlines() if l.strip()];assert len(source_rows)==4924 and len(probe_rows)==90 and len({r['id'] for r in probe_rows})==90
 source_keys={material_key(r) for r in source_rows};assert all(material_key(r) in source_keys for r in probe_rows),'blind probe materials differ from frozen complete input'
 proof={'status':'passed','complete_input_sha256':sha(full),'blind90_input_sha256':sha(packet),'source_context_QA_sha256':sha(qa),'candidate02_prompt_sha256':sha(prompt),'n':90,'all_90_materials_exactly_equal_except_blind_id_and_unit_id_metadata':True,'ignored_fields':['id','unit_id'],'private_mapping_not_read':True,'reference_labels_or_machine_answers_not_read_for_this_material_comparison':True}
 (HERE/'completed90_material_identity_QA.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n');print(json.dumps(proof),flush=True)
 cmd=[sys.executable,str(HERE/'run_production_v30.py'),'--input',str(packet),'--expected-input-sha256',sha(packet),'--prompt',str(prompt),'--expected-n','90','--run-name','completed-material90-candidate02','--workers','4','--max-attempts','3'];proc=subprocess.run(cmd);raise SystemExit(proc.returncode)
if __name__=='__main__':main()
