import pathlib,json,sys,subprocess
p=pathlib.Path(__file__).parent
row=next(x for x in json.loads((p/'packet-identities.json').read_text()) if x['source_id']==sys.argv[1])
file=row['view_index_file'];start=int(sys.argv[2])
reader=json.loads((p/'bootstrap-identity.json').read_text())['files']['reader']['path']
raise SystemExit(subprocess.call([sys.executable,reader,'--file',file['path'],'--file-sha256',file['sha256'],'--encoding','file_utf8','--start-byte',str(start),'--max-bytes','6000','--audit-log',str(p/(sys.argv[1]+'-index-'+str(start).zfill(6)+'-emission.json'))]))
