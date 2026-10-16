from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request,urlopen
import ssl,hashlib,datetime,json
OUT=Path(__file__).parent
URLS={
'old-domain':'https://www.kxjcm.com/',
'contribution-invited':'https://www.qkkxjc.cn/contribution-invited',
'submission-format':'https://www.qkkxjc.cn/submission-format',
'format-attachment69':'https://www.qkkxjc.cn/news/exportNewFile?id=69',
'article-current':'https://www.qkkxjc.cn/article/current',
'2026-07-003':'https://www.qkkxjc.cn/article/doi/10.27034/j.cnki.ISSN1006-4885.2026.07.003',
'2026-07-010':'https://www.qkkxjc.cn/article/doi/10.27034/j.cnki.ISSN1006-4885.2026.07.010'}
def fetch(kv):
 key,url=kv;r={'key':key,'url':url,'read_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'attempts':[]}
 for verify in (True,False):
  if not verify and not r.get('ssl_error'):break
  try:
   req=Request(url,headers={'User-Agent':'Mozilla/5.0'})
   with urlopen(req,timeout=12,context=ssl.create_default_context() if verify else ssl._create_unverified_context()) as f:
    b=f.read();ctype=f.headers.get('Content-Type','');ext='.docx' if b[:2]==b'PK' else '.html';p=OUT/(key+ext);p.write_bytes(b)
    r.update({'final_url':f.url,'http_status':f.status,'content_type':ctype,'content_disposition':f.headers.get('Content-Disposition'),'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'tls_verified':verify,'success':True});r['attempts'].append({'verify':verify,'result':'success'});break
  except Exception as e:
   msg=str(e);r['attempts'].append({'verify':verify,'error':msg});r['ssl_error']='CERTIFICATE_VERIFY_FAILED' in msg or isinstance(getattr(e,'reason',None),ssl.SSLError);r['success']=False
 return r
results=list(ThreadPoolExecutor(max_workers=4).map(fetch,URLS.items()))
(OUT/'primary_fetch_manifest.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
for r in results:print(json.dumps(r,ensure_ascii=False))
