import json, hashlib, datetime, concurrent.futures
from pathlib import Path
import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent
URLS = {
1: 'https://www.nhc.gov.cn/yzygj/c100068/202305/68bcfaf610d94c638f64c53aff5de994.shtml',
2: 'https://www.nhc.gov.cn/yzygj/c100068/202002/fdb7240014db4d49827ca25bbb41b177.shtml',
3: 'https://www.nhc.gov.cn/yzygj/c100068/202207/6e8c919b5590431082f198665950bdca.shtml',
4: 'https://www.nhc.gov.cn/yzygj/c100068/201807/03df2450431348e18feb3701c199262d.shtml',
5: 'https://www.nhc.gov.cn/yaozs/c100098/202411/d7281a7478714afea007a19598094961.shtml',
6: 'https://www.nhc.gov.cn/yzygj/c100068/202301/64caf647a2bb4ae6b33363447d8771b9.shtml',
7: 'https://www.nhc.gov.cn/yaozs/c100097/201904/6bc8f273684845d3ab76fed841eb42d2.shtml',
8: 'https://www.nhc.gov.cn/yaozs/c100097/202107/d2a45e6ae041423f950b3865e43f5ef6.shtml',
9: 'https://www.nhc.gov.cn/yzygj/c100068/202109/1721a2c993a04e309f6055c092e64186.shtml',
10: 'https://www.nhsa.gov.cn/art/2022/6/29/art_62_8340.html',
11: 'https://www.nhsa.gov.cn/art/2022/6/29/art_62_8340.html',
12: 'https://www.nhsa.gov.cn/art/2021/5/10/art_37_5023.html',
13: 'https://www.nhsa.gov.cn/art/2020/7/31/art_37_3387.html',
14: 'https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypqtggtg/20250912092255131.html',
15: 'https://www.nmpa.gov.cn/xxgk/fgwj/gzwj/gzwjyp/20240731184417109.html',
16: 'https://www.nmpa.gov.cn/xxgk/fgwj/gzwj/gzwjyp/20240207173908137.html',
17: 'https://www.nmpa.gov.cn/xxgk/fgwj/gzwj/gzwjyp/20240802085401168.html',
18: 'https://www.nmpa.gov.cn/xxgk/fgwj/xzhgfxwj/20200708151701834.html',
19: 'https://www.nmpa.gov.cn/xxgk/ggtg/ypggtg/ypqtggtg/20260515145324185.html',
20: 'https://www.nmpa.gov.cn/xxgk/fgwj/xzhgfxwj/20260608103856150.html',
}

def fetch(entry):
    i = entry['index']
    if i not in URLS:
        return None
    url = URLS[i]
    directory = Path(entry['directory'])/'evidence'
    existing = directory/'primary-http-retrieval.json'
    if existing.exists():
        return json.loads(existing.read_text())
    now = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()
    record = {'index':i, 'url':url,'attempted_at':now,'method':'requests.get; one direct request; no repeated failure loop'}
    try:
        r=requests.get(url,timeout=25)
        raw=directory/'primary-http-response.html'
        raw.write_bytes(r.content)
        r.encoding=r.apparent_encoding
        soup=BeautifulSoup(r.text,'html.parser')
        for s in soup(['script','style']): s.decompose()
        txt=directory/'primary-http-visible-text.txt'
        txt.write_text(soup.get_text('\n',strip=True))
        record.update({'status_code':r.status_code,'final_url':r.url,'content_type':r.headers.get('content-type'),'raw_saved':str(raw),'raw_sha256':hashlib.sha256(r.content).hexdigest(),'text_saved':str(txt),'text_sha256':hashlib.sha256(txt.read_bytes()).hexdigest(),'title':soup.title.get_text() if soup.title else None,'meta':[str(m) for m in soup.find_all('meta') if any(k in str(m).lower() for k in ['date','title','url','time'])]})
    except Exception as e:
        record['error']=type(e).__name__+': '+str(e)
    (directory/'primary-http-retrieval.json').write_text(json.dumps(record,ensure_ascii=False,indent=2))
    return record

if __name__=='__main__':
    entries=json.loads((ROOT/'working-entries.json').read_text())
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(fetch,entries))
    records=[r for r in results if r]
    (ROOT/'http-retrievals.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
    for r in records: print(r['index'],r.get('status_code'),r.get('title'),r.get('error'))
