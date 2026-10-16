import pathlib,json,sys,subprocess,hashlib
p=pathlib.Path(__file__).parent
sid,pointer,encoding,start=sys.argv[1],sys.argv[2],sys.argv[3],int(sys.argv[4])
row=next(x for x in json.loads((p/'packet-identities.json').read_text()) if x['source_id']==sid)
z=row['packet_file'];reader=json.loads((p/'bootstrap-identity.json').read_text())['files']['reader']['path']
key=hashlib.sha256(pointer.encode()).hexdigest()[:16]
raise SystemExit(subprocess.call([sys.executable,reader,'--file',z['path'],'--file-sha256',z['sha256'],'--pointer','/source_bundle'+pointer,'--encoding',encoding,'--start-byte',str(start),'--max-bytes','6000','--audit-log',str(p/(sid+'-leaf-'+key+'-'+str(start).zfill(6)+'-emission.json'))]))
