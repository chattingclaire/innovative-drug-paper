import json,pathlib,sys,subprocess
p=pathlib.Path(__file__).parent
inputs=json.loads((p/'input-identities.json').read_text())+json.loads((p/'additional-input-identities.json').read_text())+json.loads((p/'inherited-input-identities.json').read_text())
key,start=sys.argv[1],int(sys.argv[2])
x=next(x for x in inputs if x['key']==key)
reader=next(x for x in inputs if x['key']=='reader')['path']
log=p/(key+'-'+str(start).zfill(6)+'-emission.json')
raise SystemExit(subprocess.call([sys.executable,reader,'--file',x['path'],'--file-sha256',x['sha256'],'--encoding','file_utf8','--start-byte',str(start),'--max-bytes','6000','--audit-log',str(log)]))
