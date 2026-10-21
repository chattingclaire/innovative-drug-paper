import json,pathlib,sys,os,subprocess,hashlib
A=pathlib.Path(__file__).parent
sid=sys.argv[1];i=int(sys.argv[2]);start=int(sys.argv[3])
x=json.loads((A/'original-view-mappings.json').read_text())[sid]['original_body_CTX_view_carriers'][i];q=x['exact_view_carrier'];v=pathlib.Path(q['path']).read_bytes();assert len(v)==q['bytes'] and hashlib.sha256(v).hexdigest()==q['sha256']==x['view_sha256']
a=A/(sid+'-v'+str(i).zfill(3)+'-'+str(start).zfill(6)+'-emission.json');cmd=['python3','/PROJECT_ROOT/outputs/goal-calibration-20261010/06-coding/native-llm77-v13-sol/source-read-transport-fix-sol/source_view_chunk.py','--file',q['path'],'--file-sha256',q['sha256'],'--encoding','file_utf8','--start-byte',str(start),'--max-bytes','6000','--audit-log',str(a)]
p=subprocess.run(cmd,capture_output=True,text=True)
with (A/(a.stem+'-tool-body.txt')).open('x') as f:f.write(p.stdout)
print(p.stdout,end='');print(p.stderr,end='',file=sys.stderr);sys.exit(p.returncode)
