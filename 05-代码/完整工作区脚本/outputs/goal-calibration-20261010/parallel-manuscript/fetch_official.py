from pathlib import Path
import urllib.request,urllib.parse,hashlib,json,re,html
from docx import Document
OUT=Path(__file__).parent/'evidence'
log=[]
def fetch(url,data=None):
    req=urllib.request.Request(url,data=urllib.parse.urlencode(data).encode() if data else None,headers={'User-Agent':'Mozilla/5.0'})
    with urllib.request.urlopen(req,timeout=20) as r:return r.read(),r.status,dict(r.headers)
for name,url in [('submission-format','https://www.qkkxjc.cn/submission-format'),('contribution-invited','https://www.qkkxjc.cn/contribution-invited')]:
    try:
        raw,status,headers=fetch(url); (OUT/(name+'.html')).write_bytes(raw);txt=raw.decode('utf8')
        ids=re.findall(r'id="newsId"[^>]*value="([^"]+)"',txt) or re.findall(r'value="([^"]+)"[^>]*id="newsId"',txt)
        rec={'url':url,'status':status,'sha256':hashlib.sha256(raw).hexdigest(),'newsIds':ids}
        if ids:
            raw2,status2,_=fetch('https://www.qkkxjc.cn/data/news/newsData',{'id':ids[0]});data=json.loads(raw2)
            (OUT/(name+'.json')).write_bytes(raw2)
            content=data['data']['news']['content']; text=html.unescape(re.sub('<[^>]+>','\n',content)); (OUT/(name+'.txt')).write_text(text)
            rec.update({'api_status':status2,'api_sha256':hashlib.sha256(raw2).hexdigest(),'title':data['data']['news']['title'],'text_length':len(text)})
        log.append(rec)
    except Exception as e:log.append({'url':url,'error':str(e)})
url='https://www.qkkxjc.cn/news/exportNewFile?id=69'
try:
    raw,status,h=fetch(url); p=OUT/'official-current-template.docx';p.write_bytes(raw)
    log.append({'url':url,'status':status,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw),'magic':raw[:4].hex(),'content_disposition':h.get('Content-Disposition')})
    d=Document(p);(OUT/'official-current-template.txt').write_text('\n'.join(f'P{i+1:03} {p.text}' for i,p in enumerate(d.paragraphs)))
except Exception as e:log.append({'url':url,'error':str(e)})
(OUT/'official_fetch_log.json').write_text(json.dumps(log,ensure_ascii=False,indent=2));print(json.dumps(log,ensure_ascii=False,indent=2))
