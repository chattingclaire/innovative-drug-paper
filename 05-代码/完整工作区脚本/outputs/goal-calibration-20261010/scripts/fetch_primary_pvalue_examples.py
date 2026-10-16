import hashlib
import json
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '02-methods/pvalue-reporting-web-root'
SOURCES = OUT / 'sources'
SOURCES.mkdir(parents=True, exist_ok=True)
requests = [
    ('JPA-2025-6-policy-narratives.pdf', 'https://jpa.sysu.edu.cn/docs/20251219145853201219.pdf'),
    ('APS-2020-public-decision.html', 'https://journal.psych.ac.cn/xlxb/article/2020/0439-755X/0439-755X-52-2-240.shtml'),
]
results = []
for filename, url in requests:
    target = SOURCES / filename
    if target.exists():
        raw = target.read_bytes()
        results.append({'path': str(target), 'url': url, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'status': 'already_saved'})
        continue
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(request, timeout=25) as response:
            raw = response.read()
            content_type = response.headers.get('Content-Type')
        if filename.endswith('.pdf') and not raw.startswith(b'%PDF'):
            raise ValueError('Response is not a PDF')
        target.write_bytes(raw)
        results.append({'path': str(target), 'url': url, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'content_type': content_type, 'status': 'saved'})
    except Exception as error:
        results.append({'url': url, 'status': 'failed', 'error_type': type(error).__name__, 'error': str(error)})
(OUT / 'retrieval.json').write_text(json.dumps({'primary_sources_only': True, 'requests': results}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(results, ensure_ascii=False))
