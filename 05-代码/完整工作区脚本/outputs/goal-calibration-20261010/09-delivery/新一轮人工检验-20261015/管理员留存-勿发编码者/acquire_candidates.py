"""Archive verified public candidate URLs; no sample selection or coding."""
from pathlib import Path
from urllib.request import urlopen, Request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from zoneinfo import ZoneInfo
import hashlib, json

HERE=Path(__file__).resolve().parent
OUT=HERE/'候选来源下载'
URLS=[
    ('NMPA-中药补充申请改革2026-上海药监局转载.html','https://yjj.sh.gov.cn/qtgzwj/20260921/1fb0e70133e14fd5871bd5b7516d576e.html'),
    ('NHC-基本药物优先配备2026-湖南省政府转载.html','https://www.hunan.gov.cn/zqt/zcsd/202608/t20260821_34048515.html'),
    ('NHC-基本药物优先配备2026-国家卫健委原网页.html','https://www.nhc.gov.cn/yaozs/c100098/202608/44dd389b28a34cc2bc80b7b95af816f0.shtml'),
]
def acquire(pair):
    name,url=pair
    p=OUT/name
    if p.exists():
        return {'url':url,'path':str(p),'status':'existing_not_replaced','bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
    result={'url':url,'path':str(p),'downloaded_at':datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),'scope':'candidate_only_not_selected_or_issued'}
    try:
        with urlopen(Request(url,headers={'User-Agent':'Mozilla/5.0'}),timeout=25) as r:
            b=r.read()
            assert len(b)>500
            p.write_bytes(b)
            result.update(status=r.status,final_url=r.url,content_type=r.headers.get('Content-Type'),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    except Exception as e:
        result.update(status='download_failed',error=f'{type(e).__name__}: {e}')
    p.with_suffix(p.suffix+'.receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

if __name__=='__main__':
    OUT.mkdir(exist_ok=True)
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(acquire,URLS))
    print(json.dumps(results,ensure_ascii=False,indent=2))
