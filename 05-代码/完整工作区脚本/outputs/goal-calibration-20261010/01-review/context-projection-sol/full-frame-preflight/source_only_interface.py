"""ID lookup: rule and model receive identical canonical source bytes."""
from pathlib import Path
import argparse,json,hashlib
OUT=Path(__file__).resolve().parent
P=OUT/'canonical_source_context-v7.jsonl'
SHA='007342cd7f89681258bb5fbd31a3c6ae6b8f6cd6f013f97329aa0dcdee799974'
p=argparse.ArgumentParser();p.add_argument('interface',choices=['rule','model','unit']);p.add_argument('id');p.add_argument('--with-source-registry',action='store_true');a=p.parse_args()
b=P.read_bytes();assert hashlib.sha256(b).hexdigest()==SHA
allrows={r['id']:r for r in map(json.loads,b.decode().splitlines())};assert len(allrows)==4481
if a.id not in allrows:p.error('ID is outside the4481 allowlist')
r=allrows[a.id]
if a.interface=='unit':r={k:r[k] for k in ['id','text','pages','source_ref']}
if a.with_source_registry:
 needed={r['source_ref']['sha256']}|{n['source_ref']['sha256'] for n in r.get('contexts',[])}
 docs=[x for x in map(json.loads,(OUT/'source-document-identities-v7.jsonl').read_text().splitlines()) if x['source_sha256'] in needed]
 r={'source_material':r,'source_documents':docs}
# The rule/model selectors change no field, source text, metadata, or order.
print(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')))
