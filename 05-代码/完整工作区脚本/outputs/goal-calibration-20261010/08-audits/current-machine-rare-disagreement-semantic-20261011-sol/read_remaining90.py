"""Read only frozen original exposed/non-human200 packets; no classification execution."""
from pathlib import Path
import json,hashlib,datetime,collections,sys
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent;B=P.parent.parent
f=json.loads((P/'readable-disagreement-selection-freeze.json').read_text())
done={(x['id'],x['dimension']) for x in json.loads((P/'phase01-first40/semantic-reviews40.json').read_text())}
rest=[x for x in f['eligible_all_records'] if (x['id'],x['dimension']) not in done]
pop=json.loads((P/'population-membership-metadata.json').read_text());allowed=set(pop['exposed_ids_in_frame_order'])-set(pop['human200_source_ids_excluded'])
assert len(rest)==90 and all(x['id'] in allowed for x in rest)
ids=list(dict.fromkeys(x['id'] for x in rest));wanted={(x['id'],x['dimension']) for x in rest}
def bind(q):
 q=Path(q).resolve();r=q.read_bytes();return dict(path=str(q),bytes=len(r),sha256=hashlib.sha256(r).hexdigest())
diag=B/'07-statistics/current-v7-machine-diagnostics-20261011T1543-root/machine-pair-disagreements.jsonl'
selected={}
for l in diag.open():
 r=json.loads(l)
 if (r['id'],r['dimension']) in wanted:selected[(r['id'],r['dimension'])]=r
assert set(selected)==wanted
rows=[];receipts=[];resources={}
for sid in ids:
 items=[x for x in rest if x['id']==sid];binding=items[0]['packet'];assert bind(binding['path'])==binding
 raw=json.loads(Path(binding['path']).read_bytes());sb=raw['source_bundle']
 for item in items:
  assert item['packet']==binding and bind(item['native_first']['path'])==item['native_first']
  assert selected[(sid,item['dimension'])]['packet']==binding
 rows.append(dict(id=sid,packet=binding,source_bundle=sb,machine_disagreements=[selected[(sid,x['dimension'])] for x in items]))
 receipt=dict(id=sid,packet=binding,dimensions=[x['dimension'] for x in items],current_text_characters=len(sb['source_record']['text']),contexts=[dict(index=i,keys=list(c),text_characters=len(c.get('text',''))) for i,c in enumerate(sb['source_record'].get('contexts',[]))],source_bundle_keys=list(sb),read_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
 receipt['full_text_resources']=[]
 for i,r in enumerate(sb.get('source_full_text_resources',[])):
  text=r.get('text','');h=hashlib.sha256(text.encode()).hexdigest();resources.setdefault(h,dict(sha256=h,characters=len(text),resource=r,used_by=[]))['used_by'].append(sid)
  receipt['full_text_resources'].append(dict(index=i,sha256=h,characters=len(text)))
 receipts.append(receipt)
with (P/'remaining90-semantic-inputs.jsonl').open('x',encoding='utf8') as o:
 for r in rows:o.write(json.dumps(r,ensure_ascii=False)+'\n')
for name,value in [('remaining90-packet-read-receipts.json',dict(unique_source_id_N=len(ids),dimension_N=len(rest),packet_checks=receipts,remaining_or_human200_packet_opened_N=0,metadata_parser_only_for_unselected_diagnostic_rows=True,models_called=0,classification_runs=0)),('remaining90-unique-source-resources.json',list(resources.values()))]:
 with (P/name).open('x',encoding='utf8') as o:json.dump(value,o,ensure_ascii=False,indent=2);o.write('\n')
print(json.dumps(dict(N=len(rest),unique_records=len(ids),unique_text_resources=len(resources),resource_chars=sum(r['characters'] for r in resources.values()),policies=[(sid,[r.get('title',r.get('source_name',r.get('resource_name',''))) for r in rows[i]['source_bundle'].get('source_full_text_resources',[])]) for i,sid in enumerate(ids)]),ensure_ascii=False))
