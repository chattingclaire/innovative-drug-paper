"""Fresh isolated expert sessions: source rereview only, never metric selection."""
from pathlib import Path
import hashlib, json, subprocess, tempfile, datetime, sys, shutil
import jsonschema

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
CLI=Path('/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex')
sys.path.insert(0,str(ROOT/'llm-v32'))
from run_production_v32 import event_audit

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def strings(x):
    if isinstance(x,str):yield x
    elif isinstance(x,list):
        for y in x:yield from strings(y)
    elif isinstance(x,dict):
        for y in x.values():yield from strings(y)

def compatible(s):
    if isinstance(s,list):return [compatible(x) for x in s]
    if not isinstance(s,dict):return s
    d={k:compatible(v) for k,v in s.items() if k not in ('$schema','uniqueItems','title')}
    if 'const' in d:
        v=d.pop('const');d['enum']=[v];d.setdefault('type','string' if isinstance(v,str) else 'integer')
    if 'oneOf' in d:d['anyOf']=d.pop('oneOf')
    if d.get('type')=='object' and 'properties' not in d:
        # Issues may be free text or object in the validation schema. The CLI
        # shape uses its supported free-text alternative, preserving meaning.
        return {'type':'string'}
    if 'enum' in d and 'type' not in d:d['type']='string' if all(isinstance(x,str) for x in d['enum']) else 'integer'
    return d

def main():
    coder,kind=sys.argv[1:3]
    assert coder in ('C','T') and kind in ('替代来源复读','新增首次')
    directory=HERE/('agent-'+coder)
    packetpath=directory/(kind+'材料-v14.json')
    schemapath=directory/(kind+'结果schema-v14.json')
    taskpath=directory/(kind+'任务说明-v14.md')
    resultpath=directory/(kind+'结果-v14.json')
    qapath=directory/(kind+'QA-v14.json')
    run=directory/(kind+'-隔离专家实际执行-v14')
    assert not run.exists() and not resultpath.exists() and not qapath.exists()
    run.mkdir()
    packet=json.loads(packetpath.read_text());schema=json.loads(schemapath.read_text())
    cli_schema=compatible(schema)
    cli_schema['properties']['rows']['items']['properties']['issues']={'type':'array','items':{'type':'string'}}
    write(run/'cli_output_schema.json',cli_schema)
    request=('你是政策文本内容分析领域的独立专家AI评审。请直接阅读本请求全部材料后逐条进行语义判断。'
             '这是新的隔离会话，你没有旧判断、其他评审答案或机器答案。你不是人类，不声称真人验证。'
             '只输出规定JSON；本请求已包含全部需要内容，禁止调用工具、读文件、运行代码或检索。'
             '任务说明中的只读文件均已原样嵌入如下，实际文件路径只是来源留痕，不得访问。\n\n'
             +taskpath.read_text()+'\n\n--- 完整手册 ---\n'
             +(ROOT/'protocol/完整五维手册-v1.3.md').read_text()+'\n\n--- 共用操作说明 ---\n'
             +(ROOT/'protocol/共用操作说明-v1.4.md').read_text()+'\n\n--- 本次材料真实SHA256 ---\n'
             +sha(packetpath)+'\n\n--- 本次无答案材料 ---\n'+packetpath.read_text()
             +'\n\n按材料原顺序返回完整五维判断。每条引文只能逐字来自该条自己的text或contexts，不能串用其他条。'
             '有实质来源缺口可明确待定；材料完整时逐维给出个人0/1及理由。返回coder='+coder
             +'，material_version=v14，input_packet_sha256='+sha(packetpath)+'。')
    (run/'request.txt').write_text(request)
    plan={'created_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
          'requested_model':'gpt-5.6-sol','reasoning_effort':'medium','role':coder,'kind':kind,
          'identity':'fresh isolated AI expert session; replacement reviewer; not original reviewer or human',
          'packet':{'path':str(packetpath),'sha256':sha(packetpath)},'validation_schema_sha256':sha(schemapath),
          'cli_schema_sha256':sha(run/'cli_output_schema.json'),'request_sha256':sha(run/'request.txt'),
          'runner_sha256':sha(Path(__file__)),'cli_version':subprocess.check_output([str(CLI),'--version'],text=True).strip(),
          'max_attempts':3,'selection':'first structurally valid, exact packet/order, literal evidence, zero-tools actual output',
          'accuracy_or_metric_based_selection':False,'other_answers_supplied':False,
          'underlying_model_independence_not_claimed':True}
    write(run/'plan.json',plan)
    attempts=[]
    for index in range(1,4):
        a=run/('attempt-%02d'%index);a.mkdir();out=a/'raw_output.json'
        with tempfile.TemporaryDirectory(prefix='policy-expert-v14-') as cwd:
            cmd=[str(CLI),'exec','-','--model','gpt-5.6-sol','--cd',cwd,'-c','model_reasoning_effort="medium"',
                 '-c','web_search="disabled"','--skip-git-repo-check','--ephemeral','--ignore-user-config','--ignore-rules',
                 '--sandbox','read-only','--output-schema',str((run/'cli_output_schema.json').resolve()),
                 '--output-last-message',str(out.resolve()),'--json']
            proc=subprocess.run(cmd,input=request,text=True,capture_output=True,timeout=1800)
        (a/'events.jsonl').write_text(proc.stdout);(a/'stderr.txt').write_text(proc.stderr)
        audit=event_audit(proc.stdout);write(a/'tool_event_audit.json',audit)
        errors=[];evidence_checks=[]
        if proc.returncode:errors.append('execution_exit_'+str(proc.returncode))
        if audit['tool_or_unknown_item_event_count']:errors.append('tools_or_unknown_events')
        result=None
        try:
            result=json.loads(out.read_text());jsonschema.Draft202012Validator(schema).validate(result)
            assert result['input_packet_sha256']==sha(packetpath)
            assert [x['id'] for x in result['rows']]==[x['id'] for x in packet['rows']]
            for row,source in zip(result['rows'],packet['rows']):
                for e in row['evidence']:
                    pool=[source['text']] if e['source']=='unit' else list(strings(source['contexts']))
                    assert e['quote'] and any(e['quote'] in s for s in pool),(row['id'],'nonliteral',e)
                    evidence_checks.append({'id':row['id'],**e,'literal':True})
                for d in ('S','E','Ec','I','F'):
                    if row['labels'][d]==1:assert any(e['dimension']==d and e['source']=='unit' for e in row['evidence'])
        except Exception as e:errors.append(str(e))
        metadata={'attempt':index,'exit_code':proc.returncode,'command':cmd,'request_sha256':sha(run/'request.txt'),
                  'raw_output_sha256':sha(out) if out.exists() else None,'events_sha256':sha(a/'events.jsonl'),
                  'status':'accepted' if not errors else 'failed_preserved','errors':errors,'tool_audit':audit}
        write(a/'metadata.json',metadata);attempts.append(metadata)
        print(coder,kind,index,metadata['status'],errors,flush=True)
        if not errors:
            shutil.copyfile(out,resultpath)
            write(qapath,{'all_checks_pass':True,'n':len(packet['rows']),'AI_identity':plan['identity'],
                          'requested_model':'gpt-5.6-sol','observed_model_fields':audit['observed_model_fields'],
                          'provider_internal_revision':'not_exposed','plan':str(run/'plan.json'),
                          'plan_sha256':sha(run/'plan.json'),'selected_first_valid_attempt':index,
                          'result_sha256':sha(resultpath),'packet_sha256':sha(packetpath),'evidence_checks':evidence_checks,
                          'read_scope':'Only task/handbooks/own current blank packet embedded in request; no tools or external reads',
                          'kind':kind,'completed_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()})
            write(run/'summary.json',{'status':'complete','attempts':attempts,'selected':index});return
    write(run/'summary.json',{'status':'failed_preserved','attempts':attempts});sys.exit(2)

if __name__=='__main__':main()
