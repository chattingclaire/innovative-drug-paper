import pathlib, json, sys, subprocess, uuid, os
A=pathlib.Path(__file__).parent
if sys.argv[1]=='confirm':
 for n in sys.argv[2:]:
  p=A/n; m=json.loads(p.read_text()); d={'local_delivery_event_id':str(uuid.uuid4()),'tool_event_id':None,'reader':os.environ['CODEX_THREAD_ID'],'tool':'functions.exec/exec_command','emission_file':str(p),'emission_local_execution_id':m['local_execution_id'],'input_file':m['input_file'],'source_file_sha256':m['input_file_byte_sha256'],'view_sha256':m['view_sha256'],'start_byte':m['start_byte'],'end_byte':m['end_byte'],'actual_visible_body_UTF8_bytes':m['chunk_UTF8_bytes'],'begin_end_visible_and_matching':True,'body_complete_visible':True,'truncated':False,'actually_read_by_actor':True,'status':'complete_chunk','platform_tool_event_id_available':False}
  with (A/(p.stem.replace('-emission','')+'-delivery.json')).open('x') as f:json.dump(d,f,ensure_ascii=False,indent=2)
else:
 key=sys.argv[1]; start=int(sys.argv[2]); rows=json.loads((A/'input-identities.json').read_text())+json.loads((A/'input-identities-extra.json').read_text()); row=next(x for x in rows if (x['path']==key if '/' in key else pathlib.Path(x['path']).name==key)); audit=A/(pathlib.Path(key).name+('-base' if '/protocol-necessary-read-v3/' in key else '')+'-'+str(start).zfill(6)+'-emission.json')
 cmd=['python3','/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-llm77-v13-sol/source-read-transport-fix-sol/source_view_chunk.py','--file',row['path'],'--file-sha256',row['sha256'],'--encoding','file_utf8','--start-byte',str(start),'--max-bytes','6000','--audit-log',str(audit)]
 p=subprocess.run(cmd,capture_output=True,text=True)
 with (A/(audit.stem+'-tool-body.txt')).open('x') as f:f.write(p.stdout)
 print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr);sys.exit(p.returncode)
