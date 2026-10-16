import sys,json,hashlib,subprocess,uuid
from pathlib import Path
plan_path,plan_sha,index=sys.argv[1],sys.argv[2],int(sys.argv[3])
p=Path(plan_path); raw=p.read_bytes(); assert hashlib.sha256(raw).hexdigest()==plan_sha
plan=json.loads(raw); root=Path(plan['attempt_directory'])
unacked=[q for q in root.glob('v*-raw-tool-return.json') if not q.with_name(q.name.replace('-raw-tool-return.json','-read.json')).exists()]
assert len(unacked)<=1
for q in unacked:
    r=json.loads(q.read_text())['raw_tool_return']; out=r['output']
    first,bodytail=out.split('\n',1); body,last=bodytail.rsplit('\nEND_SOURCE_VIEW_CHUNK ',1)
    a=json.loads(first.removeprefix('BEGIN_SOURCE_VIEW_CHUNK ')); z=json.loads(last.strip()); assert a==z
    assert r.get('exit_code')==0 and 'truncated' not in out.lower() and len(body.encode())==a['chunk_UTF8_bytes'] and hashlib.sha256(body.encode()).hexdigest()==a['chunk_sha256']
    receipt={'raw_tool_return_file':str(q),'emission_file':str(root/q.name.replace('-raw-tool-return.json','-emission.json')),'local_delivery_event_id':str(uuid.uuid4()),'real_tool_event_id':None,'actual_delivery_complete':True,'actual_semantic_read_complete':True,'reader':root.name,'metadata':a}
    with q.with_name(q.name.replace('-raw-tool-return.json','-read.json')).open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
v=plan['views'][index]
previous=sorted(root.glob(f'v{index:03d}-*-emission.json'))
start=json.loads(previous[-1].read_text())['end_byte'] if previous else 0
cmd=[sys.executable,plan['reader'],'--file',v['file'],'--file-sha256',v['sha256'],'--encoding',v['encoding'],'--start-byte',str(start),'--max-bytes','6000','--audit-log',str(root/f'v{index:03d}-{start:06d}-emission.json')]
if v.get('pointer') is not None:cmd+=['--json-pointer',v['pointer']]
proc=subprocess.run(cmd); sys.exit(proc.returncode)
