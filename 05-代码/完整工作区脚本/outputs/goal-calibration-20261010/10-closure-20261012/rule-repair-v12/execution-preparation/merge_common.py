"""Mechanical binding/JSON byte helpers; never semantic coding."""
import datetime,hashlib,json,re
from pathlib import Path
DIMS=('S','E','Ec','I','F')
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):
 def unique(pairs):
  d={}
  for k,v in pairs:assert k not in d;d[k]=v
  return d
 def reject(x):raise ValueError(x)
 return json.loads(Path(p).read_bytes(),object_pairs_hook=unique,parse_constant=reject)
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def bind(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':sha(raw)}
def exact(b):assert bind(b['path'])=={k:b[k] for k in ('path','bytes','sha256')},b['path']
def save(p,x):
 with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def seal(p):
 s=load(p)
 for k in ('files','output_files','implementation_files','control_inputs'):
  for b in s.get(k,[]):exact(b)
 return s
def rows(p,key='id'):
 out={}
 for i,raw in enumerate(Path(p).read_bytes().splitlines(keepends=True),1):
  x=json.loads(raw);rid=x[key] if isinstance(key,str) else tuple(x[k] for k in key);assert rid not in out;out[rid]=(i,raw,x)
 return out
STR=re.compile(rb'"(?:[^"\\]|\\.)*"',re.S);TOKEN=re.compile(rb'[\[\]{}"]');WS=re.compile(rb'\s*')
def skip(raw,i):
 i=WS.match(raw,i).end()
 if raw[i]==34:return STR.match(raw,i).end()
 if raw[i] in (123,91):
  depth=1;i+=1
  while depth:
   m=TOKEN.search(raw,i);p=m.start();c=raw[p]
   if c==34:i=STR.match(raw,p).end();continue
   depth+=1 if c in (123,91) else -1;i=p+1
  return i
 return i+re.match(rb'[^\s,}\]]+',raw[i:]).end()
def spans(raw):
 i=WS.match(raw,0).end();assert raw[i]==123;i+=1;out={}
 while True:
  i=WS.match(raw,i).end()
  if raw[i]==125:return out
  k=STR.match(raw,i);name=json.loads(k.group());i=WS.match(raw,k.end()).end();assert raw[i]==58
  a=WS.match(raw,i+1).end();end=skip(raw,a);out[name]=(a,end);i=WS.match(raw,end).end()
  if raw[i]==44:i+=1
  else:assert raw[i]==125
def replace(raw,updates,additions=None):
 ranges=spans(raw)
 assert set(updates)<=set(ranges), 'Cannot silently add an update field'
 assert not set(additions or {}) & set(ranges), 'Cannot duplicate an existing field'
 for key,(a,b) in sorted(ranges.items(),key=lambda z:z[1][0],reverse=True):
  if key in updates:raw=raw[:a]+updates[key]+raw[b:]
 if additions:
  end=raw.rfind(b'}');raw=raw[:end]+b', '+json.dumps(additions,ensure_ascii=False,allow_nan=False).encode()[1:-1]+raw[end:]
 return raw
def pointer(x,p):
 for k in p.lstrip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');x=x[int(k)] if isinstance(x,list) else x[k]
 return x
