"""True main/attempt paths with subprocess.run replaced; synthetic strings only."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('c09_runtime_under_test',HERE/'run_candidate09.py')
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
checks=[]
def check(name,condition):
    checks.append({'name':name,'passed':bool(condition)})
    assert condition,name

def stageA_output(rows,material=False):
    out=[]
    for i,row in enumerate(rows):
        leaf={'paths':['/contexts/paragraph_context/0/text'],'status':'not_used','proposition_ids':[],
          'unit_quotes':[],'context_quote':'合成语境。','contribution':'仅用于技术模拟。'}
        prop={'proposition_id':'p1','subject_or_object':'合成对象','actions_attributes_and_qualifiers':'合成陈述',
          'conditional_outcome':'无条件结果','unit_quotes':[row['text']]}
        out.append({'id':row['id'],'current_propositions':[]if material and i==0 else[prop],
          'context_records':[leaf],'material_status':'material_issue'if material and i==0 else'sufficient',
          'material_note':'仅用于技术模拟。'})
    return {'stage':'current_proposition_context_record','rows':out}

def stageB_output(rows,material=False):
    return {'protocol_version':'CAL-5D-20260926-v1.3','execution_version':'LLM-binary-v32',
      'release_stage':'final_binary_labels','rows':[{'id':x['id'],'labels':{d:0 for d in ['S','E','Ec','I','F']},
        'dimension_reasons':{d:'技术模拟。'for d in ['S','E','Ec','I','F']},'evidence':[],
        'fairness_subtypes':[],'innovation_subtypes':[],'safety_quality_basis':'no_quality_basis'}for x in rows],
      'issue_records':[{'id':rows[0]['id'],'status':'material_issue','description':'技术模拟材料标记。'}]if material else[]}

class Fixture:
    def __init__(self,root):
        self.home=Path(root)/'candidate09';self.home.mkdir()
        self.old={k:getattr(r,k)for k in ['HERE','INPUT_BINDING','DESIGN_FREEZE']}
        r.HERE=self.home;r.INPUT_BINDING=self.home/'initial11_input_binding.json';r.DESIGN_FREEZE=self.home/'design_freeze.json'
        self.rows=[{'id':f'MOCK-C09-{i:02d}','text':f'合成材料单元{i:02d}。',
          'contexts':{'paragraph_context':[{'text':'合成语境。'}]}}for i in range(1,12)]
        self.ip=self.home/'mock11.json';self.ip.write_text(json.dumps({'rows':self.rows},ensure_ascii=False))
        self.ib={'candidate':r.CANDIDATE,'scope':r.SCOPE,'n':11,'input_path':str(self.ip),'input_sha256':r.sha(self.ip)}
        r.INPUT_BINDING.write_text(json.dumps(self.ib))
        freeze={'candidate':r.CANDIDATE,'scope':r.SCOPE,'n':11,'model':r.MODEL,'reasoning_effort':r.EFFORT,
          'stageA_and_B_separately_authorized':True,'max_attempts_per_stage':3,'files':[],'sources':[]}
        r.DESIGN_FREEZE.write_text(json.dumps(freeze))
        self.calls=[];self.model_calls=[];self.mode='valid';self.real_run=subprocess.run
        subprocess.run=self.fake_run
    def restore(self):
        subprocess.run=self.real_run
        for k,v in self.old.items():setattr(r,k,v)
    def fake_run(self,command,**kwargs):
        self.calls.append(command)
        if command[-1]=='--version':
            if self.mode=='version_error':raise RuntimeError('MOCK_VERSION_FAILURE')
            return SimpleNamespace(returncode=0,stdout='MOCK_CLI_VERSION_ONLY\n',stderr='')
        self.model_calls.append(kwargs['input'])
        marker='--- 本批完整原始输入与路径库存 ---'if '--- 本批完整原始输入与路径库存 ---'in kwargs['input']else'--- 同一完整原始输入与封存StageA原记录 ---'
        packet=json.loads(kwargs['input'].split(marker+'\n',1)[1][:-len(r.TRAILER)])
        isA='context_path_inventory'in packet
        raw=stageA_output(packet['rows'],self.mode=='A_material')if isA else stageB_output(packet['rows'],self.mode=='B_material')
        if self.mode=='two_bad_then_valid'and len(self.model_calls)<3:
            raw['rows'][0]['current_propositions'][0]['unit_quotes']=['不在原文中的模拟引文']
        if self.mode=='all_bad':raw['rows'][0]['current_propositions'][0]['unit_quotes']=['不在原文中的模拟引文']
        output=Path(command[command.index('--output-last-message')+1]);output.write_text(json.dumps(raw,ensure_ascii=False))
        event_raw=copy.deepcopy(raw)
        if self.mode=='event_mismatch':event_raw['rows'][0]['material_note']='不同模拟消息'
        events=[{'type':'thread.started'},{'type':'turn.started'},
          {'type':'item.completed','item':{'type':'agent_message','text':json.dumps(event_raw,ensure_ascii=False)}},
          {'type':'turn.completed','usage':{'input_tokens':1,'output_tokens':1}}]
        if self.mode=='two_messages':events.insert(3,copy.deepcopy(events[2]))
        if self.mode=='source_changed':self.ip.write_text('CHANGED_SYNTHETIC_SOURCE')
        return SimpleNamespace(returncode=0,stdout=''.join(json.dumps(x,ensure_ascii=False)+'\n'for x in events),stderr='MOCK_ONLY')
    def auth(self,stage,extra=None):
        a={'status':'AUTHORIZED_BOUNDED_EXECUTION','candidate':r.CANDIDATE,'authorized_stage':stage,
          'scope':r.SCOPE,'n':11,'model':r.MODEL,'reasoning_effort':r.EFFORT,'batch_size':11,'workers':1,
          'max_attempts':3,'design_freeze_sha256':r.sha(r.DESIGN_FREEZE),'input_binding_sha256':r.sha(r.INPUT_BINDING),
          'input_sha256':self.ib['input_sha256'],'allow_other_scopes':False,'allow_semantic_retries':False,
          'allow_automatic_next_stage':False}
        if extra:a.update(extra)
        p=self.home/f'mock_authorization_{stage}.json';p.write_text(json.dumps(a));return p
    def runA(self):return r.main(['--stage','A','--execute','--authorization-file',str(self.auth('A'))])
    def Bauth(self,gate_changes=None):
        seal_path=self.home/'runs'/r.RUN_NAMES['A']/'stageA_seal.json';seal=json.loads(seal_path.read_text())
        gate={'status':'PASS_ROOT_STAGEA_SEMANTIC_REVIEW','candidate':r.CANDIDATE,'approved_for_stageB':True,
          'reviewed_rows':11,'confirmed_semantic_errors':0,'original_stageA_not_edited':True,
          'stageA_seal_sha256':r.sha(seal_path),'stageA_output_sha256':seal['all_records']['sha256'],
          'input_sha256':self.ib['input_sha256'],
          'review_opinion':'DO_NOT_SEND_PRIVATE_REVIEW_SENTINEL','expected_labels':{'MOCK':'DO_NOT_SEND_EXPECTED_SENTINEL'}}
        if gate_changes:gate.update(gate_changes)
        gp=self.home/'mock_semantic_gate.json';gp.write_text(json.dumps(gate))
        return self.auth('B',{'stageA_seal':r.binding(seal_path),'stageA_semantic_gate':r.binding(gp)})

def fixture_test(name,fn):
    with tempfile.TemporaryDirectory(prefix='c09-no-model-selftest-')as temp:
        f=Fixture(temp)
        try:fn(f)
        finally:f.restore()

def main():
    source_before={str(p):r.sha(p)for p in [HERE/'stageA_prompt.txt',HERE/'stageB_prompt.txt',HERE/'prompt_lock.json',
      HERE/'run_candidate09.py',HERE/'selftest_runtime_no_model.py',HERE/'runtime/run_production_v32.py',
      HERE/'runtime/stageA_context_inventory.py',HERE/'runtime/validate_stageA.py',HERE/'runtime/stageA_output_schema.json',
      HERE/'runtime/validate_binary_output.py',HERE/'runtime/output_schema_codex_compatible.json']}
    def valid(f):
        check('A_real_main_mock_exit0',f.runA()==0)
        check('A_first_valid_one_request',len(f.model_calls)==1)
        check('A_never_auto_starts_B',not(f.home/'runs'/r.RUN_NAMES['B']).exists())
        ajson=f.home/'runs'/r.RUN_NAMES['A']/'all_stageA_records.json';seal=json.loads(ajson.with_name('stageA_seal.json').read_text())
        check('A_original_rows_canonical_SHA_per_ID',seal['row_record_sha256']=={x['id']:r.row_sha(x)for x in json.loads(ajson.read_text())['rows']})
        auth=f.Bauth()
        check('B_separately_authorized_mock_exit0',r.main(['--stage','B','--execute','--authorization-file',str(auth)])==0)
        check('two_distinct_model_requests',len(f.model_calls)==2)
        request=f.model_calls[-1]
        check('gate_review_opinion_not_in_B_request','DO_NOT_SEND_PRIVATE_REVIEW_SENTINEL'not in request)
        check('expected_labels_not_in_B_request','DO_NOT_SEND_EXPECTED_SENTINEL'not in request and 'expected_labels'not in request)
        bpacket=json.loads((f.home/'runs'/r.RUN_NAMES['B']/'input_packet.json').read_text())
        check('B_packet_exact_allowed_top_keys',set(bpacket)=={'rows','stageA_records'})
        check('B_original_material_not_deleted',r.canonical(bpacket['rows'])==r.canonical(f.rows))
        check('B_exact_A_records_SHA',all(x['record_sha256']==r.row_sha(x['record'])for x in bpacket['stageA_records']))
        check('B_first_valid_one_request',len(list((f.home/'runs'/r.RUN_NAMES['B']/'attempts').iterdir()))==1)
    fixture_test('valid',valid)
    def retries(f):
        f.mode='two_bad_then_valid';check('two_fail_then_third_valid_exit0',f.runA()==0)
        check('two_fail_then_third_valid_three_requests',len(f.model_calls)==3)
        check('technical_retries_identical_requests',len(set(f.model_calls))==1)
        check('all_three_attempts_preserved',len(list((f.home/'runs'/r.RUN_NAMES['A']/'attempts').iterdir()))==3)
    fixture_test('retries',retries)
    for mode in ['all_bad','event_mismatch','two_messages']:
        def invalid(f,mode=mode):
            f.mode=mode;check(mode+'_exit2',f.runA()==2)
            check(mode+'_max3',len(f.model_calls)==3)
            receipt=json.loads((f.home/'runs'/r.RUN_NAMES['A']/'final_stage_scope_receipt.json').read_text())
            check(mode+'_B_NOT_RUN',receipt['stage_states']['B']['state']=='NOT_RUN')
        fixture_test(mode,invalid)
    def materialA(f):
        f.mode='A_material';check('A_material_technical_accepted',f.runA()==0)
        check('A_material_not_technical_retried',len(f.model_calls)==1)
        auth=f.Bauth();n=len(f.model_calls)
        try:r.main(['--stage','B','--execute','--authorization-file',str(auth)]);ok=False
        except AssertionError:ok=True
        check('A_material_blocks_B_even_mock_PASS_gate',ok and len(f.model_calls)==n)
    fixture_test('materialA',materialA)
    def materialB(f):
        f.runA();auth=f.Bauth();f.mode='B_material'
        check('B_material_stops_exit2',r.main(['--stage','B','--execute','--authorization-file',str(auth)])==2)
        check('B_material_no_semantic_retry',len(f.model_calls)==2)
    fixture_test('materialB',materialB)
    def version_error(f):
        f.mode='version_error'
        try:f.runA();ok=False
        except RuntimeError:ok=True
        check('startup_failure_no_model_request',ok and len(f.model_calls)==0)
        receipt=json.loads((f.home/'runs'/r.RUN_NAMES['A']/'final_stage_scope_receipt.json').read_text())
        check('startup_failure_scope_receipt_B_NOT_RUN',receipt['stage_states']['B']['state']=='NOT_RUN')
    fixture_test('version_error',version_error)
    def plan_only(f):
        check('A_plan_only_main_exit0',r.main(['--stage','A','--plan-only'])==0)
        check('plan_only_zero_subprocess_calls',len(f.calls)==0)
        try:r.main(['--stage','B','--plan-only']);ok=False
        except AssertionError:ok=True
        check('B_plan_not_assembled_without_gate_and_auth',ok and len(f.calls)==0)
    fixture_test('plan',plan_only)
    def missingauth(f):
        try:r.main(['--stage','A','--execute']);ok=False
        except AssertionError:ok=True
        check('execute_no_auth_zero_CLI',ok and len(f.calls)==0)
        invocations=[json.loads(p.read_text())for p in(f.home/'invocation-records').glob('*.json')]
        check('pre_execution_rejection_persisted',len(invocations)==1 and invocations[0]['status']=='REJECTED_OR_FAILED_PRESERVED')
        check('pre_execution_rejection_both_stages_NOT_RUN',all(v['state']=='NOT_RUN'for v in invocations[0]['stage_states'].values()))
        auth=f.auth('A',{'n':12})
        try:r.main(['--stage','A','--execute','--authorization-file',str(auth)]);ok=False
        except AssertionError:ok=True
        check('wrong_scope_n_zero_CLI',ok and len(f.calls)==0)
    fixture_test('auth',missingauth)
    for name,change in [('negative_gate',{'approved_for_stageB':False}),('gate_wrong_output',{'stageA_output_sha256':'0'*64}),
      ('gate_unreviewed',{'reviewed_rows':10}),('gate_error_present',{'confirmed_semantic_errors':1})]:
        def badgate(f,change=change,name=name):
            f.runA();auth=f.Bauth(change);n=len(f.model_calls)
            try:r.main(['--stage','B','--execute','--authorization-file',str(auth)]);ok=False
            except AssertionError:ok=True
            check(name+'_blocks_B',ok and len(f.model_calls)==n)
        fixture_test(name,badgate)
    def tamper(f):
        f.runA();auth=f.Bauth();p=f.home/'runs'/r.RUN_NAMES['A']/'all_stageA_records.json'
        d=json.loads(p.read_text());d['rows'][0]['material_note']='人工修改模拟';p.write_text(json.dumps(d))
        try:r.main(['--stage','B','--execute','--authorization-file',str(auth)]);ok=False
        except AssertionError:ok=True
        check('edited_A_not_allowed_to_continue_B',ok and len(f.model_calls)==1)
    fixture_test('tamper',tamper)
    def immutable(f):
        f.runA();n=len(f.model_calls)
        try:f.runA();ok=False
        except AssertionError:ok=True
        check('same_A_run_cannot_restart',ok and len(f.model_calls)==n)
    fixture_test('immutable',immutable)
    def source_changed(f):
        f.mode='source_changed'
        try:f.runA();ok=False
        except AssertionError:ok=True
        run=f.home/'runs'/r.RUN_NAMES['A']
        check('changed_source_forbids_successful_seal',ok and not(run/'stageA_seal.json').exists())
        check('changed_source_preserves_attempt_no_retry',len(f.model_calls)==1 and(run/'attempts/attempt-01/run_metadata.json').exists())
        receipt=json.loads((run/'final_stage_scope_receipt.json').read_text())
        check('changed_source_recorded_false_and_B_NOT_RUN',receipt['source_input_unchanged']is False and receipt['stage_states']['B']['state']=='NOT_RUN')
    fixture_test('source_changed',source_changed)
    check('locked_sources_unchanged',all(r.sha(p)==s for p,s in source_before.items()))
    report={'status':'PASS','checks_n':len(checks),'checks':checks,'real_CLI_invocations':0,'real_model_calls':0,
      'mock_driver':'actual main and frozen run_attempt; subprocess.run replaced in temporary synthetic-only fixtures',
      'locked_source_bindings':source_before,'source_files_modified':False}
    p=HERE/'selftest_runtime_no_model_result.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','checks_n':len(checks),'report':r.binding(p),'real_CLI_invocations':0,'real_model_calls':0},ensure_ascii=False))

if __name__=='__main__':main()
