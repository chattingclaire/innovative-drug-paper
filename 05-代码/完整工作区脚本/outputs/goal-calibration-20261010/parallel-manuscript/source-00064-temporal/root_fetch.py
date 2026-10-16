#!/usr/bin/env python3
"""Save public source carriers with retrieval results, never frame labels."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from html.parser import HTMLParser
import json
import hashlib

BASE = Path(__file__).resolve().parent
SOURCES = BASE / 'sources'
SOURCES.mkdir(exist_ok=True)
ITEMS = [
 ('root-2020-nov-notice.html', 'https://www.ccfdie.org/zryyxxw/zxdt/webinfo/2020/11/1602453958504309.htm'),
 ('root-2020-nov-notice-cn.html', 'https://www.ccfdie.org/cn/yjxx/yphzp/webinfo/2020/11/1602453958453674.htm'),
 ('root-2020-apr-program-draft-notice.html', 'https://www.ccfdie.org/zryyxxw/zxdt/webinfo/2020/05/1588976781930435.htm'),
 ('root-2020-july82-nmpa.html', 'https://www.nmpa.gov.cn/zhuanti/ypqxgg/ggzhcfg/20200708151701834.html'),
 ('root-2020-nov-official-attachment-response.html', 'https://www.cde.org.cn/attachmentout.do?id=2d5823dc4a735684&mothed=list'),
]


class TextParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.lines = []; self.skip = 0; self.links=[]
    def handle_starttag(self, tag, attrs):
        if tag in ['script','style']:
            self.skip += 1
        if tag == 'a':
            self.links += [v for k,v in attrs if k == 'href']
    def handle_endtag(self, tag):
        if tag in ['script','style'] and self.skip:
            self.skip -= 1
    def handle_data(self, data):
        if not self.skip and data.strip():
            self.lines.append(data.strip())


def fetch(item):
    filename, url = item
    record = {'requested_url': url, 'retrieved_at': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat()}
    request = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read(); record.update(http_status=response.status, final_url=response.url,
                                                  content_type=response.headers.get('Content-Type',''))
    except HTTPError as error:
        body = error.read(); record.update(http_status=error.code, final_url=error.url, content_type=error.headers.get('Content-Type',''))
    except Exception as error:
        record.update(status='failed', error=repr(error)); return record
    destination = SOURCES / filename; destination.write_bytes(body)
    record.update(path=str(destination), bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    text = None
    for encoding in ['utf-8', 'gb18030']:
        try:
            text=body.decode(encoding); record['text_encoding']=encoding; break
        except UnicodeDecodeError:
            continue
    if text:
        parser=TextParser(); parser.feed(text)
        txt=destination.with_suffix('.txt'); txt.write_text('\n'.join(parser.lines)+'\n')
        record.update(text_path=str(txt), text_sha256=hashlib.sha256(txt.read_bytes()).hexdigest(), links=parser.links)
        substantive = any(w in '\n'.join(parser.lines) for w in ['国家药监局药审中心关于发布', '药品审评中心公开征求', '国家药监局关于发布《突破性治疗药物审评工作程序'])
        blocked = record['http_status'] != 200 or not substantive
        record['status'] = 'blocked_or_non_substantive_response' if blocked else 'downloaded_substantive_notice'
        record['read_scope'] = '仅核通知标题、日期、稿别和原附件链接；响应不含所援指南正文'
    else:
        record['status'] = 'non_text_response_not_yet_inspected'
    return record


with ThreadPoolExecutor(max_workers=5) as pool:
    results=list(pool.map(fetch,ITEMS))
(BASE/'root-retrieval-log.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
print(json.dumps([{k:r.get(k) for k in ['requested_url','http_status','status','bytes']} for r in results],ensure_ascii=False))
