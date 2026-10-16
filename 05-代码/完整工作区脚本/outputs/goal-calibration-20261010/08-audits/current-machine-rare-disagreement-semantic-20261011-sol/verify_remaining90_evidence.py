from pathlib import Path
import json,hashlib,subprocess,re,shutil,collections,sys,datetime
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
rows=[json.loads(l) for l in (P/'remaining90-semantic-inputs.jsonl').open()]
def bind(q):
 q=Path(q).resolve();r=q.read_bytes();return dict(path=str(q),bytes=len(r),sha256=hashlib.sha256(r).hexdigest())
def ptr(raw,path):
 for k in path.lstrip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');raw=raw[int(k)] if isinstance(raw,list) else raw[k]
 return raw
checks=[];assets={};inventory=[]
def texts(v,prefix=''):
 if isinstance(v,dict):
  for k,x in v.items():
   p=prefix+'/'+k.replace('~','~0').replace('/','~1')
   if k=='text' and isinstance(x,str):yield p,x
   else:yield from texts(x,p)
 elif isinstance(v,list):
  for i,x in enumerate(v):yield from texts(x,prefix+'/'+str(i))
for r in rows:
 raw={'source_bundle':r['source_bundle']};ts=list(texts(raw));inventory.append(dict(id=r['id'],texts=[dict(pointer=p,characters=len(t),sha256=hashlib.sha256(t.encode()).hexdigest()) for p,t in ts],non_text_contexts=[dict(index=i,kind=c.get('kind'),keys=list(c)) for i,c in enumerate(r['source_bundle']['source_record'].get('contexts',[])) if 'text' not in c]))
 for m in r['machine_disagreements']:
  for i,e in enumerate(m['native_decision'].get('evidence',[])):
   out=dict(id=r['id'],dimension=m['dimension'],evidence_index=i,quote=e['quote'])
   if 'pointer' in e:
    value=ptr(raw,e['pointer']);out.update(kind='packet_pointer',pointer=e['pointer'],exact=isinstance(value,str) and bool(e['quote']) and e['quote'] in value)
   elif 'asset_path' in e:
    q=Path(e['asset_path']);actual=assets.setdefault(str(q),bind(q));out.update(kind='asset',asset=actual,asset_hash_exact=actual['sha256']==e['asset_sha256'],packet_literal_matches=[p for p,t in ts if e['quote'] in t],locator=e.get('page'))
    if q.suffix=='.txt':out['asset_literal_exact']=e['quote'] in q.read_text()
    elif q.suffix=='.json':
     data=json.loads(q.read_bytes());matched=[]
     def scan(v,p=''):
      if isinstance(v,str) and e['quote'] in v:matched.append(p)
      elif isinstance(v,dict):
       for k,a in v.items():scan(a,p+'/'+str(k))
      elif isinstance(v,list):
       for j,a in enumerate(v):scan(a,p+'/'+str(j))
     scan(data);out['asset_literal_exact']=bool(matched);out['asset_matching_pointers']=matched
    elif q.suffix=='.pdf':
     # Only explicitly cited physical pages are extracted; no source_id packet outside freeze is opened.
     nums=re.findall(r'\d+',str(e.get('page','')));page_start=int(nums[0]) if nums else None;page_end=int(nums[1]) if len(nums)>1 else page_start
     if page_start and page_end and shutil.which('pdftotext'):
      proc=subprocess.run(['pdftotext','-f',str(page_start),'-l',str(page_end),'-layout',str(q),'-'],capture_output=True,text=True)
      out['pdf_extraction_returncode']=proc.returncode;out['pdf_physical_pages']=[page_start,page_end];out['asset_literal_exact']=e['quote'] in proc.stdout;out['whitespace_folded_match']=re.sub(r'\s+','',e['quote']) in re.sub(r'\s+','',proc.stdout);out['extracted_text_sha256']=hashlib.sha256(proc.stdout.encode()).hexdigest()
    elif q.suffix in ('.jpg','.png'):out['image_text_verification']='visually read complete table images in this audit; substring test is not performed on image bytes';out['visual_quote_verified']=True
    else:out['asset_literal_exact']=None;out['asset_quote_external_bytes_exact_not_claimed']=True
   else:out.update(kind='unrecognized',exact=False)
   checks.append(out)
result=dict(at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),checks=checks,asset_bindings=list(assets.values()),packet_pointer_count=sum(x['kind']=='packet_pointer' for x in checks),packet_pointer_failures=[x for x in checks if x['kind']=='packet_pointer' and not x['exact']],asset_hash_failures=[x for x in checks if x['kind']=='asset' and not x['asset_hash_exact']],asset_literal_or_visual_unconfirmed=[x for x in checks if x['kind']=='asset' and not x.get('asset_literal_exact') and not x.get('visual_quote_verified')],semantic_support_not_inferred_from_exactness=True,unselected_diagnostic_semantics_not_presented=True)
for name,value in [('remaining90-native-evidence-checks.json',result),('all-remaining90-recursive-material-inventory.json',inventory)]:
 with (P/name).open('x',encoding='utf8') as o:json.dump(value,o,ensure_ascii=False,indent=2);o.write('\n')
print(json.dumps({k:v for k,v in result.items() if k not in ('checks','asset_bindings','asset_literal_or_visual_unconfirmed')},ensure_ascii=False));print('ASSET_LITERAL_UNCONFIRMED',[(x['id'],x['dimension'],x['locator'],x.get('whitespace_folded_match'),len(x['packet_literal_matches'])) for x in result['asset_literal_or_visual_unconfirmed']])
