import pathlib,json,os,sys,subprocess,hashlib,uuid
A=pathlib.Path(__file__).parent;s=json.loads((A/'queue-state.json').read_text());q=json.loads((A/'base-view-queue.json').read_text())
if s['pending']:
 p=A/s['pending'];m=json.loads(p.read_text());d={'local_delivery_event_id':str(uuid.uuid4()),'tool_event_id':None,'reader':os.environ['CODEX_THREAD_ID'],'tool':'functions.exec/exec_command','emission_file':str(p),'emission_local_execution_id':m['local_execution_id'],'input_file':m['input_file'],'source_file_sha256':m['input_file_byte_sha256'],'view_sha256':m['view_sha256'],'start_byte':m['start_byte'],'end_byte':m['end_byte'],'actual_visible_body_UTF8_bytes':m['chunk_UTF8_bytes'],'begin_end_visible_and_matching':True,'body_complete_visible':True,'truncated':False,'actually_read_by_actor':True,'status':'complete_chunk'}
 with (A/(p.stem.replace('-emission','')+'-delivery.json')).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2)
 s['pending']=None
if s['index']>=len(q):
 (A/'queue-state.json').write_text(json.dumps(s));print('ALL_BASE_VIEWS_ACTOR_CONFIRMED');sys.exit(0)
i=s['index'];x=q[i];f=x['file'];raw=pathlib.Path(f['path']).read_bytes();assert len(raw)==f['bytes'] and hashlib.sha256(raw).hexdigest()==f['sha256']==x['view_sha256']
a=A/('base-q'+str(i).zfill(3)+'-'+str(s['start']).zfill(6)+'-emission.json');cmd=['python3','/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-llm77-v13-sol/source-read-transport-fix-sol/source_view_chunk.py','--file',f['path'],'--file-sha256',f['sha256'],'--encoding','file_utf8','--start-byte',str(s['start']),'--max-bytes','6000','--audit-log',str(a)]
p=subprocess.run(cmd,capture_output=True,text=True)
print('ORIGINAL_VIEW_BINDINGS '+json.dumps({'queue_index':i,'source_sha256':x['source_sha256'],'view':x['view'],'bindings':[{'source_id':b['source_id'],'resource_id':b['resource_id'],'original_bundle_pointer':b['original_bundle_pointer']} for b in x['bindings']], 'original_locator_and_fields_file':str(A/'base-view-queue.json')},ensure_ascii=False,separators=(',',':')))
with (A/(a.stem+'-tool-body.txt')).open('x') as f:f.write(p.stdout)
print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr)
if p.returncode:sys.exit(p.returncode)
m=json.loads(a.read_text());s['pending']=a.name
if m['view_EOF_after_this_chunk']:s['index']+=1;s['start']=0
else:s['start']=m['end_byte']
(A/'queue-state.json').write_text(json.dumps(s))
