import json,pathlib,sys,hashlib,subprocess
p=pathlib.Path(__file__).parent
sid,idx,start=sys.argv[1],int(sys.argv[2]),int(sys.argv[3])
row=next(x for x in json.loads((p/'packet-identities.json').read_text()) if x['source_id']==sid)
index=json.loads(pathlib.Path(row['view_index_file']['path']).read_bytes())
x=index['original_body_CTX_view_carriers'][idx];z=x['exact_view_carrier']
data=pathlib.Path(z['path']).read_bytes()
assert len(data)==z['bytes'] and hashlib.sha256(data).hexdigest()==z['sha256']==x['view_sha256']
bundle=json.loads(pathlib.Path(row['packet_file']['path']).read_bytes())['source_bundle']
v=bundle
for part in x['original_bundle_pointer'].strip('/').split('/'):
 part=part.replace('~1','/').replace('~0','~');v=v[int(part)] if isinstance(v,list) else v[part]
if x['original_fields'] is not None:v={k:v[k] for k in x['original_fields'] if k in v}
orig=v.encode('utf-8') if isinstance(v,str) and x['view']=='text' and x['original_fields'] is None else json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
assert orig==data
reader=json.loads((p/'bootstrap-identity.json').read_text())['files']['reader']['path']
raise SystemExit(subprocess.call([sys.executable,reader,'--file',z['path'],'--file-sha256',z['sha256'],'--encoding','file_utf8','--start-byte',str(start),'--max-bytes','6000','--audit-log',str(p/(sid+'-view-'+str(idx)+'-'+str(start).zfill(6)+'-emission.json'))]))
