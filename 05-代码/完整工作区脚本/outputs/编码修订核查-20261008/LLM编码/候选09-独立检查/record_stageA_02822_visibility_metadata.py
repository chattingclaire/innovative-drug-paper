"""Mechanical exposure addendum; no protected sentence is displayed or copied."""
import sys
sys.dont_write_bytecode=True
import datetime,hashlib,importlib.util,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
CAND=HERE.parent/'候选09-分步判读'
RUN=CAND/'runs/initial11-stageA-first-run'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(Path(p).resolve()),'sha256':sha(p),'bytes':Path(p).stat().st_size}
meta_path=HERE/'known11_source_extraction_and_protection_metadata.json'
meta=json.loads(meta_path.read_text())
original_path=HERE/'known11_inputs_ORIGINAL_FIELDS_PRIVATE_FROZEN.jsonl'
original=[json.loads(line)for line in original_path.read_text().splitlines()if line.strip()]
packet=json.loads((RUN/'input_packet.json').read_text())
attempt=RUN/'attempts/attempt-01'
ap=json.loads((attempt/'input.json').read_text())
canonical=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
assert canonical(packet['rows'])==canonical(original)==canonical(ap['rows'])
assert (RUN/'request.txt').read_bytes()==(attempt/'request.txt').read_bytes()
spec=importlib.util.spec_from_file_location('c09_visibility_readonly_helpers',CAND/'run_candidate09.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
assert (RUN/'request.txt').read_text()==r.make_request('A',packet,(CAND/'stageA_prompt.txt').read_text())
occ=[]
for item in meta['reserved_context_occurrences']:
    match=re.fullmatch(r'root\[(\d+)\]\.(.*)',item['locator']);index=int(match.group(1));value=packet['rows'][index]
    tokens=re.findall(r'([^.\[\]]+)|\[(\d+)\]',match.group(2))
    for key,num in tokens:value=value[int(num)]if num else value[key]
    assert isinstance(value,str)and hashlib.sha256(value.encode()).hexdigest()==item['context_sha256']
    assert packet['rows'][index]['id']==item['current_development_unit_id']
    occ.append({**item,'actual_packet_locator':item['locator'].replace('root','rows',1),'actual_request_locator':'JSON packet '+item['locator'].replace('root','rows',1),'whole_context_hash_verified':True,'original_reserved_span_not_re_read_or_re_matched':True})
assert len(occ)==4 and {x['reserved_unit_id']for x in occ}=={'RECODE25-02822'}
run_plan=json.loads((RUN/'run_plan.json').read_text())
out={'status':'ACTUAL_STAGEA_REQUEST_PROTECTED_CONTEXT_VISIBILITY_METADATA_REGISTERED_EXECUTION_IN_PROGRESS',
 'created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'candidate':'candidate09-two-step','scope':'initial11-known-development','stage':'A',
 'protected_unit_id':'RECODE25-02822','occurrence_count':4,'current_development_unit_ids':['RECODE25-02830','RECODE25-02845'],
 'occurrences':occ,
 'actual_request_visibility':{'material_included_in_full_actual_request':True,'actual_attempt':1,'root_reported_process_session':62314,'root_reported_actual_StageA_started':True,'provider_internal_reading_or_attention':'not observable; no claim of internal consumption or semantic use','stage_terminal_status':'not asserted by this in-progress addendum'},
 'human_semantic_review':{'this_reviewer_read_protected_original_sentence':False,'sentence_displayed_or_serialized_in_this_report':False,'source_sentence_not_used_for_expectation_or_prompt_design':True,'only_metadata_hash_and_path_checks':True,'semantic_gap':'If StageA materially uses this sentence, do not claim full semantic context review from a redacted projection; report the gap first.'},
 'scope_caution':'Nine current real IDs outside267 does not imply that the complete request has no reserved context material. This addendum separates model-request visibility from human semantic reading.',
 'prior_registration':{'source_metadata':bind(meta_path),'prior_registered_metadata_02822':meta['prior_registered_metadata_02822']},
 'source_bindings':[bind(p)for p in [original_path,meta_path,CAND/'run_candidate09.py',CAND/'design_freeze.json',RUN/'input_packet.json',RUN/'request.txt',RUN/'run_plan.json',attempt/'input.json',attempt/'request.txt']],
 'root_authorization_binding':run_plan['authorization'],
 'real_CLI_invocations_by_this_reviewer':0,'real_model_calls_by_this_reviewer':0,'original_frozen_files_modified':False}
p=HERE/'exposure_addenda/candidate09_StageA_actual_request_02822_visibility_metadata.json'
p.parent.mkdir(exist_ok=True)
with p.open('x')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'report':bind(p),'occurrences':4,'protected_text_displayed':False,'real_CLI_invocations_by_this_reviewer':0,'real_model_calls_by_this_reviewer':0},ensure_ascii=False))
