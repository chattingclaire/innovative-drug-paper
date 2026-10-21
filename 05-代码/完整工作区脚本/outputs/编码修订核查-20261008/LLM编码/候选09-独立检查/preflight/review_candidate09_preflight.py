"""Independent offline preflight. Only self-created mock strings; no real CLI."""
import sys
sys.dont_write_bytecode = True
import copy, datetime, hashlib, importlib.util, json, subprocess, tempfile
from pathlib import Path
from types import SimpleNamespace

PROJECT = Path('/PROJECT_ROOT')
HERE = Path(__file__).resolve().parent
CAND = HERE.parent.parent / '候选09-分步判读'
CHECKS = []
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def binding(p): return {'path':str(Path(p).resolve()),'sha256':sha(p),'bytes':Path(p).stat().st_size}
def check(name, value):
    CHECKS.append({'name':name,'passed':bool(value)})
    if not value: raise AssertionError(name)
def load(name,p):
    spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m; spec.loader.exec_module(m); return m
def json_write(p,o): Path(p).write_text(json.dumps(o,ensure_ascii=False)+'\n')

manifest_path=CAND/'preparation_manifest.json'
manifest=json.loads(manifest_path.read_text())
before=[binding(p['path']) for p in manifest['files']+manifest['sources']]
for item in manifest['files']+manifest['sources']:
    check('frozen_source:'+item['path'], binding(item['path'])==item)
check('manifest_final_SHA',sha(manifest_path)=='95f0768a30b9c8c5624db4270ca593682c96a62be625736f434cca3fa44b79c7')
lock=json.loads((CAND/'prompt_lock.json').read_text())
v13=Path(lock['manual_sources'][0]['path']).read_text()
v14=Path(lock['manual_sources'][1]['path']).read_text().split('## 版本与验证纪律')[0]
suffix='\n--- 冻结的完整v1.3手册原文 ---\n\n'+v13+'\n--- 冻结的v1.4实质操作部分原文 ---\n\n'+v14
check('suffix_byte_exact',(CAND/'manual_suffix_UNCHANGED.txt').read_bytes()==suffix.encode())
for p in lock['prompts']:
    data=Path(p['path']).read_bytes()
    check('locked_prompt_SHA:'+Path(p['path']).name,hashlib.sha256(data).hexdigest()==p['sha256'])
    check('full_manual_suffix:'+Path(p['path']).name,data.endswith(suffix.encode()))
    prefix=data[:-len(suffix.encode())].decode()
    check('no_case_ID_or_threshold:'+Path(p['path']).name,all(s not in prefix for s in ['RECODE25-','C05-NEW-','0.80']))
prior=CAND.parent/'候选08-命题与证据判定'/'runtime-unchanged-v2'
for name in ['run_production_v32.py','validate_binary_output.py','output_schema_codex_compatible.json']:
    check('original_B_byte_identical:'+name,(CAND/'runtime'/name).read_bytes()==(prior/name).read_bytes())
plan=json.loads((CAND/'offline_plan.json').read_text())
check('fixed_model',plan['model']=='gpt-5.6-sol' and plan['reasoning_effort']=='medium')
check('eleven_rows_two_logical_six_technical',plan['n']==11 and plan['design_total_logical_requests_if_both_separately_authorized']==2 and plan['design_total_max_technical_attempts']==6)
check('each_stage_single_batch_max3',all(x['logical_requests']==1 and x['batch_size']==11 and x['workers']==1 and x['max_identical_technical_attempts']==3 for x in plan['stages']))
fidelity=HERE.parent/'independent_known11_input_fidelity_metadata.json'
fd=json.loads(fidelity.read_text())
check('independent_input_fidelity_final_SHA',sha(fidelity)=='faa5b6e9fc28b474ab05033ef3340ef91cccff6edbda13d3b1587c3e46dcd6f2')
check('input_fidelity_PASS',str(fd['status']).startswith('PASS'))

r=load('independent_c09_preflight_target',CAND/'run_candidate09.py')
mock_observations=[]
class Fixture:
    def __init__(self,tmp,mode='good'):
        self.mode=mode; self.calls=[]; self.versions=0; self.root=Path(tmp)
        self.old={k:getattr(r,k) for k in ['HERE','INPUT_BINDING','DESIGN_FREEZE']}
        r.HERE=self.root; r.INPUT_BINDING=self.root/'input_binding.json'; r.DESIGN_FREEZE=self.root/'freeze.json'
        self.rows=[{'id':f'INDEPENDENT-MOCK-{i:02d}','text':f'甲记录第{i}项。','contexts':{'paragraph_context':[{'text':'该附注只用于自造技术检查。'}]}} for i in range(11)]
        self.ip=self.root/'self_created.jsonl'; self.ip.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in self.rows))
        self.ib={'candidate':r.CANDIDATE,'scope':r.SCOPE,'n':11,'input_path':str(self.ip),'input_sha256':sha(self.ip)}
        json_write(r.INPUT_BINDING,self.ib)
        json_write(r.DESIGN_FREEZE,{'candidate':r.CANDIDATE,'scope':r.SCOPE,'n':11,'model':r.MODEL,'reasoning_effort':r.EFFORT,'stageA_and_B_separately_authorized':True,'max_attempts_per_stage':3,'files':[],'sources':[]})
        self.real_subprocess=subprocess.run; subprocess.run=self.fake_subprocess
    def close(self):
        subprocess.run=self.real_subprocess
        for k,v in self.old.items():setattr(r,k,v)
    def fake_subprocess(self,cmd,**kw):
        if cmd[-1]=='--version':
            self.versions+=1; return SimpleNamespace(returncode=0,stdout='INDEPENDENT_FAKE_VERSION\n',stderr='')
        check('mock_command_fixed_model',cmd[cmd.index('--model')+1]=='gpt-5.6-sol' and 'model_reasoning_effort="medium"'in cmd)
        req=kw['input']; isA='--- 本批完整原始输入与路径库存 ---\n'in req
        marker='--- 本批完整原始输入与路径库存 ---\n' if isA else '--- 同一完整原始输入与封存StageA原记录 ---\n'
        packet=json.loads(req.split(marker,1)[1][:-len(r.TRAILER)])
        self.calls.append({'stage':'A'if isA else'B','request':req,'packet':packet,'command':cmd})
        check('mock_full_original_rows',packet['rows']==self.rows)
        if isA:
            out={'stage':'current_proposition_context_record','rows':[]}
            for row in self.rows:
                out['rows'].append({'id':row['id'],'current_propositions':[{'proposition_id':'p1','subject_or_object':'甲','actions_attributes_and_qualifiers':'记录事项','conditional_outcome':'未写条件','unit_quotes':[row['text']]}],
                    'context_records':[{'paths':['/contexts/paragraph_context/0/text'],'status':'not_used','proposition_ids':[],'unit_quotes':[],'context_quote':'该附注只用于自造技术检查。','contribution':'这是无语义效度结论的技术模拟。'}],
                    'material_status':'sufficient','material_note':'这是自造技术模拟。'})
            if self.mode in ['always_invalid','event_mismatch','two_messages'] or (self.mode=='retry' and len(self.calls)<3):
                if self.mode in ['always_invalid','retry']:out['rows'][0]['current_propositions'][0]['unit_quotes']=['字面不存在的模拟引文']
            if self.mode in ['material','invalid_material']:
                out['rows'][0]['material_status']='material_issue'
                if self.mode=='invalid_material':out['rows'][0]['current_propositions'][0]['unit_quotes']=['不存在的引文']
            if self.mode=='semantic_wrong_but_structural':out['rows'][0]['current_propositions'][0]['actions_attributes_and_qualifiers']='这是假定语义错误，验证器不得依据其质量挑选其他输出。'
        else:
            out={'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v32','release_stage':'final_binary_labels','rows':[{'id':x['id'],'labels':{d:0 for d in ['S','E','Ec','I','F']},'dimension_reasons':{d:'自造技术模拟。'for d in ['S','E','Ec','I','F']},'evidence':[],'fairness_subtypes':[],'innovation_subtypes':[],'safety_quality_basis':'no_quality_basis'}for x in self.rows],'issue_records':[]}
        Path(cmd[cmd.index('--output-last-message')+1]).write_text(json.dumps(out,ensure_ascii=False))
        event_obj=copy.deepcopy(out)
        if self.mode=='event_mismatch':event_obj['rows'][0]['material_note']='另一对象'
        events=[{'type':'item.completed','item':{'type':'agent_message','text':json.dumps(event_obj,ensure_ascii=False)}},{'type':'turn.completed'}]
        if self.mode=='two_messages':events.insert(0,copy.deepcopy(events[0]))
        if self.mode=='source_changed':self.ip.write_text('更改自造来源')
        return SimpleNamespace(returncode=0,stdout=''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in events),stderr='INDEPENDENT_MOCK_ONLY')
    def auth(self,stage,extra=None):
        a={'status':'AUTHORIZED_BOUNDED_EXECUTION','candidate':r.CANDIDATE,'authorized_stage':stage,'scope':r.SCOPE,'n':11,'model':r.MODEL,'reasoning_effort':r.EFFORT,'batch_size':11,'workers':1,'max_attempts':3,'design_freeze_sha256':sha(r.DESIGN_FREEZE),'input_binding_sha256':sha(r.INPUT_BINDING),'input_sha256':self.ib['input_sha256'],'allow_other_scopes':False,'allow_semantic_retries':False,'allow_automatic_next_stage':False}
        if extra:a.update(extra)
        p=self.root/f'auth-{stage}.json';json_write(p,a);return p
    def run(self,stage='A',auth=None):return r.main(['--stage',stage,'--execute','--authorization-file',str(auth or self.auth(stage))])
    def b_auth(self,fail_gate=False):
        sp=self.root/'runs'/r.RUN_NAMES['A']/'stageA_seal.json'; s=json.loads(sp.read_text())
        gp=self.root/'ROOT_GATE.json'
        json_write(gp,{'status':'PASS_ROOT_STAGEA_SEMANTIC_REVIEW','candidate':r.CANDIDATE,'approved_for_stageB':not fail_gate,'reviewed_rows':11,'confirmed_semantic_errors':0,'original_stageA_not_edited':True,'stageA_seal_sha256':sha(sp),'stageA_output_sha256':s['all_records']['sha256'],'input_sha256':self.ib['input_sha256'],'review_opinion':'PRIVATE_GATE_SENTINEL','expected_labels':'PRIVATE_EXPECTATION_SENTINEL'})
        return self.auth('B',{'stageA_seal':binding(sp),'stageA_semantic_gate':binding(gp)})

def scenario(mode,fn):
    with tempfile.TemporaryDirectory(prefix='independent-c09-preflight-')as tmp:
        f=Fixture(tmp,mode)
        try:fn(f)
        finally:
            mock_observations.append({'scenario':mode,'mock_request_count':len(f.calls),'mock_version_queries':f.versions,'request_SHA256':[hashlib.sha256(x['request'].encode()).hexdigest()for x in f.calls],'real_CLI_invocations':0,'real_model_calls':0})
            f.close()
def good(f):
    check('A_first_valid_exit0',f.run()==0)
    check('A_one_request_no_automatic_B',len(f.calls)==1 and not(f.root/'runs'/r.RUN_NAMES['B']).exists())
    ap=f.root/'runs'/r.RUN_NAMES['A']/'all_stageA_records.json'; ah=sha(ap)
    auth=f.b_auth();check('B_separate_authorization_exit0',f.run('B',auth)==0)
    bp=f.calls[-1]['packet']
    check('B_only_rows_and_A_records',set(bp)=={'rows','stageA_records'})
    check('B_gate_and_private_expectation_absent',all(s not in f.calls[-1]['request']for s in ['PRIVATE_GATE_SENTINEL','PRIVATE_EXPECTATION_SENTINEL','review_opinion','expected_labels']))
    check('B_same_original_and_sameID_A_record_hashes',bp['rows']==f.rows and all(x['record_sha256']==r.row_sha(x['record'])for x in bp['stageA_records']) and [x['id']for x in bp['stageA_records']]==[x['id']for x in f.rows])
    check('A_original_not_edited_by_B',sha(ap)==ah)
    n=len(f.calls)
    try:f.run();blocked=False
    except AssertionError:blocked=True
    check('existing_run_cannot_restart',blocked and len(f.calls)==n)
scenario('good',good)
def retry(f):
    check('third_technical_valid_only',f.run()==0 and len(f.calls)==3)
    check('retry_exact_identical_request',len({x['request']for x in f.calls})==1)
    check('all_failed_attempts_preserved',len(list((f.root/'runs'/r.RUN_NAMES['A']/'attempts').iterdir()))==3)
scenario('retry',retry)
for mode in ['always_invalid','event_mismatch','two_messages']:
    def failure(f):
        check(f.mode+'_max3_exit2',f.run()==2 and len(f.calls)==3)
        receipt=json.loads((f.root/'runs'/r.RUN_NAMES['A']/'final_stage_scope_receipt.json').read_text())
        check(f.mode+'_B_explicit_NOT_RUN',receipt['stage_states']['B']['state']=='NOT_RUN')
    scenario(mode,failure)
def mat(f):
    check('material_first_valid_no_retry',f.run()==0 and len(f.calls)==1)
    auth=f.b_auth()
    try:f.run('B',auth);blocked=False
    except AssertionError:blocked=True
    check('material_blocks_B_even_gate_PASS',blocked and len(f.calls)==1)
scenario('material',mat)
scenario('invalid_material',lambda f:check('failed_attempt_material_flag_stops_retries',f.run()==2 and len(f.calls)==1))
scenario('semantic_wrong_but_structural',lambda f:check('no_semantic_retry_or_quality_selection',f.run()==0 and len(f.calls)==1))
def gate_failure(f):
    f.run();auth=f.b_auth(True)
    try:f.run('B',auth);blocked=False
    except AssertionError:blocked=True
    check('root_negative_gate_blocks_B_before_CLI',blocked and len(f.calls)==1 and f.versions==1)
scenario('gate_failure',gate_failure)
def source_change(f):
    try:f.run();blocked=False
    except AssertionError:blocked=True
    check('changed_source_forbids_successful_seal',blocked and len(f.calls)==1 and not(f.root/'runs'/r.RUN_NAMES['A']/'stageA_seal.json').exists())
scenario('source_changed',source_change)

for item in before:check('source_unchanged:'+item['path'],binding(item['path'])==item)
report={'status':'PASS_INDEPENDENT_OFFLINE_PROMPT_AND_TECHNICAL_PREFLIGHT_NOT_EXECUTION_AUTHORIZATION','created_at_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'candidate':r.CANDIDATE,'scope':r.SCOPE,'blocking_findings':[],'real_CLI_invocations':0,'real_model_calls':0,'source_files_modified':False,
 'preparation_manifest_sha256':sha(manifest_path),'source_bindings':before+[binding(manifest_path),binding(fidelity),binding(__file__)],
 'checks_total':len(CHECKS),'checks_passed':sum(x['passed']for x in CHECKS),'checks':CHECKS,'mock_observations':mock_observations,
 'prompt_semantic_review':{'A':'Read full locked task prefix: all current objects/actions/attributes/qualifiers/conditions/outcomes preserved; no final five labels; context path inventory is provenance only; genuine parents and references distinguished from adjacent independent definitions and theme. No observed handbook conflict.','B':'Read full locked task prefix: full original rows and contexts remain primary; sealed A records are provisional model opinions, not verified facts or new sources. All dimensions/reasons/evidence/subtypes/quality/issues independently assessed; no gate or expected labels in packet. No observed handbook conflict.','manual':'Full v1.3 text and v1.4 substantive part before version/validation discipline are byte-exact in both prompts. No manual definition changed.','expectations':'Private expected relations/partial labels were not supplied to author; review has not altered either prompt.'},
 'input_fidelity':{'report':binding(fidelity),'scope':'11 selected source rows incl original line-ending bytes, all fields and key order; 63/63 independently verified, no source alteration.'},
 'protection':{'current_IDs':'Nine real current IDs outside reserved267. This is not a claim of zero protected contexts.','context_member':'RECODE25-02822','registered_context_hits':4,'human_review_status':'Protected original text remains unread by this reviewer. Only registered metadata and redacted projections used.','future_review_gap':'If StageA materially uses this protected sentence, report the semantic review gap before claiming complete context assessment. Actual execution visibility must be separately recorded after authorized run.'},
 'budget':{'rows_per_stage':11,'one_batch_each':True,'max_logical_requests_if_both_separately_authorized':2,'max_technical_attempts_per_stage':3,'max_total_technical_attempts':6,'stageB_requires_new_root_gate_and_authorization':True},
 'limits':['Offline mock tests establish executable admission and provenance behavior, not semantic success of actual outputs.','StageA path/literal completeness does not prove all propositions or relations correct; root must review original raw A without edits before B.','Known11 are previously exposed development examples, not external human validation.','The protected-context semantic gap remains explicit; no new protected original read occurred.','Candidate08 FAIL and current Rule39/LLM03 adoption remain unchanged; no automatic146/240/4924 run or adoption.']}
out=HERE/'candidate09_independent_preflight.json'
with out.open('x')as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'status':report['status'],'checks':len(CHECKS),'report':binding(out),'real_CLI_invocations':0,'real_model_calls':0},ensure_ascii=False))
