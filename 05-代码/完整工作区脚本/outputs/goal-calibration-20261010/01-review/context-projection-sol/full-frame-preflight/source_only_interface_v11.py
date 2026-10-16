"""Neutral source lookup. rule/model/human selectors return identical bytes."""
from pathlib import Path
import argparse,json,hashlib,copy
OUT=Path(__file__).resolve().parent
SHA='5eaeddcfda5e0953fd31bea2d7bef20b9304ef40af277d94a586f9579406b8b6'
def readrows(p):return list(map(json.loads,p.read_text().splitlines()))
def sf(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def lookup(record_id,selector='model',bundle=True):
 assert selector in ['rule','model','human','unit']
 p=OUT/'canonical_source_context-v11.jsonl';assert sf(p)==SHA
 data={r['id']:r for r in readrows(p)};assert len(data)==4481
 if record_id not in data:raise ValueError('ID outside the4481 source frame')
 r=copy.deepcopy(data[record_id])
 if selector=='unit':return {k:r[k] for k in ['id','text','pages','source_ref']}
 if not bundle:return r
 seal=json.loads((OUT/'delivery-seal-v11.json').read_text());expected={Path(x['path']).name:x['sha256'] for x in seal['files']}
 for name in ['source-document-identities-v11.jsonl','source-library/library-v11.jsonl','source-assets-manifest-v11.jsonl']:
  assert sf(OUT/name)==expected[Path(name).name]
 needed={r['source_ref']['sha256']}|{n['source_ref']['sha256'] for n in r['contexts']}
 docs=[x for x in readrows(OUT/'source-document-identities-v11.jsonl') if x['source_sha256'] in needed]
 references={x['source_resource_id'] for x in r.get('source_references',[])}
 historical=[x for x in readrows(OUT.parent/'prospective-common-supplements-source-only-v3.jsonl') if x['record_id']==record_id]
 # Preserve earlier agreed neutral supplements even when source-only resources
 # are now stored in the document library rather than extra SUPP context nodes.
 historical_sha={x['source_sha256'] for x in historical}
 lib=[x for x in readrows(OUT/'source-library/library-v11.jsonl') if x['source_resource_id'] in references or x.get('source_sha256') in needed or x.get('snapshot_sha256') in needed or x.get('snapshot_sha256') in historical_sha]
 text_resources=[]
 for d in docs:
  e=d.get('source_text_resource')
  if e:
   p=OUT/e['relative_path'];assert sf(p)==e['sha256'];text_resources.append(json.loads(p.read_text()))
 assets=readrows(OUT/'source-assets-manifest-v11.jsonl');asset_ids={a['sha256'] for a in r.get('source_attachments',[])}
 for x in lib:
  asset_ids.update(a['sha256'] for a in x.get('source_page_assets',[]))
 used=[a for a in assets if a['sha256'] in asset_ids]
 return {'source_record':r,'source_documents':docs,'explicit_or_primary_source_resources':lib,'preserved_historical_neutral_source_supplements':historical,'source_full_text_resources':text_resources,'source_asset_locations':used,'source_locator_bases':json.loads((OUT/'source-asset-locator-bases-v11.json').read_text())}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('interface',choices=['rule','model','human','unit']);p.add_argument('id');p.add_argument('--record-only',action='store_true',help='Return the canonical row only; separately stored required source resources are not expanded.');a=p.parse_args()
 try:r=lookup(a.id,a.interface,bundle=not a.record_only)
 except ValueError as e:p.error(str(e))
 print(json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':')))
