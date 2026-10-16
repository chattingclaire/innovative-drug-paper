from pathlib import Path
from urllib.request import Request,urlopen
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor
import ssl,hashlib,datetime,json
D=Path(__file__).parent
requests=[]
for key,id in [('submission-format',79),('contribution-invited',4)]:requests.append((key+'-current.json','https://www.qkkxjc.cn/data/news/newsData',urlencode({'id':id}).encode()))
for key,filename in [('2026-07-003','2026-0674'),('2026-07-010','2026-0550')]:
 for ext in ['xml','pdf']:requests.append((key+'.'+ext,'https://www.qkkxjc.cn/fileKXJC/journal/article/kxjc/2026/7/'+filename+'.'+ext,None))
def fetch(t):
 name,url,data=t;r={'name':name,'url':url,'read_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 try:
  req=Request(url,data=data,headers={'User-Agent':'Mozilla/5.0','Content-Type':'application/x-www-form-urlencoded'} if data else {'User-Agent':'Mozilla/5.0'})
  with urlopen(req,timeout=15,context=ssl._create_unverified_context()) as f:b=f.read();r.update({'status':f.status,'final_url':f.url,'bytes':len(b),'content_type':f.headers.get('Content-Type'),'sha256':hashlib.sha256(b).hexdigest(),'path':str(D/name),'tls_verified':False});(D/name).write_bytes(b)
 except Exception as e:r['error']=str(e)
 return r
r=list(ThreadPoolExecutor(max_workers=4).map(fetch,requests));(D/'source_details_fetch_manifest.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
for x in r:print(json.dumps(x,ensure_ascii=False))
