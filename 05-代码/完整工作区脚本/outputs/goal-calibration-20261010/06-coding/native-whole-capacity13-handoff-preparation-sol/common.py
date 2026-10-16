"""Nonsemantic native handoff helpers. No stop/signal/model actions here."""
import datetime,fcntl,hashlib,json,re,subprocess,sys,types
from pathlib import Path
sys.dont_write_bytecode=True
if not __debug__:raise RuntimeError('Binding assertions require Python without optimization')
H=Path(__file__).resolve().parent;B=H.parents[1]
OLD=B/'06-coding/native-full4481-v1-sol';CAMPAIGN=B/'06-coding/native-full4481-transport-recovery-v2-sol'
V4=B/'08-audits/recover-native-whole-batches-v4-root.py';GUARD=B/'08-audits/native-recovery-v2-preflight-sol/strict_reception_guard.py'
def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):
 def unique(xs):
  out={}
  for k,v in xs:assert k not in out;out[k]=v
  return out
 def reject(x):raise ValueError(x)
 return json.loads(Path(p).read_bytes(),object_pairs_hook=unique,parse_constant=reject)
def bind(p):
 p=Path(p).resolve();raw=p.read_bytes();return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def exact(b):assert bind(b['path'])=={k:b[k] for k in ('path','bytes','sha256')},b['path']
def save(p,x):
 with Path(p).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def frozen_module(p,name):
 m=types.ModuleType(name);m.__file__=str(p);exec(compile(Path(p).read_bytes(),str(p),'exec'),m.__dict__);return m
def profile():
 doc=load(H/'transport-contract.json')
 for b in doc['frozen_inputs']:exact(b)
 s=load(H/'seal.json')
 for b in s['files']:exact(b)
 return doc
def processes():
 raw=subprocess.check_output(['/bin/ps','-axo','pid=,ppid=,pgid=,stat=,lstart=,command='],text=True);rows=[]
 for line in raw.splitlines():
  m=re.match(r'\s*(\d+)\s+(\d+)\s+(\d+)\s+(\S+)\s+(.{24})\s+(.*)',line)
  if m:rows.append(dict(pid=int(m[1]),ppid=int(m[2]),pgid=int(m[3]),stat=m[4],lstart=m[5],command=m[6]))
 return rows
def relevant(rows,prior=None):
 known={(r['pid'],r['lstart']) for r in (prior or {}).get('owned_processes',[])};groups=set((prior or {}).get('tracked_pgids',[]))
 roots={r['pid'] for r in rows if (r['pid'],r['lstart']) in known or r['pgid'] in groups or str(V4) in r['command'] or 'recover-native-whole-batches-v4-root.py --mode remaining' in r['command'] or ('isolated-codex-cli-0.162.1-root' in r['command'] and str(CAMPAIGN) in r['command'])}
 while True:
  extended=roots|{r['pid'] for r in rows if r['ppid'] in roots}
  if extended==roots:break
  roots=extended
 return [r for r in rows if r['pid'] in roots]
def history(manifest):
 result=[]
 for item in manifest['batches']:
  directory=Path(item['assignment']['path']).parent;selected=directory/'root-selection-v3.json';slots=[]
  for a in range(1,4):
   slot=directory/f'attempt-{a:04d}';files=sorted(p for p in slot.iterdir() if p.is_file());completion=slot/'process-completion.json';receipt=slot/'root-reception-v3.json'
   slots.append({'attempt':a,'path':str(slot),'any_existing_file':bool(files),'filenames':[p.name for p in files],'dispatch_start':bind(slot/'dispatch-start.json') if (slot/'dispatch-start.json').exists() else None,'process_completion':bind(completion) if completion.exists() else None,'recorded_returncode':load(completion).get('returncode') if completion.exists() else None,'root_receipt':bind(receipt) if receipt.exists() else None,'recorded_receipt_state':load(receipt).get('state') if receipt.exists() else None,'budget_consumed':bool(files),'unknown_original_outcome':bool(files) and not completion.exists()})
  used=[s['attempt'] for s in slots if s['budget_consumed']];assert used==list(range(1,len(used)+1)),('Nonprefix attempt history',item['batch_id'])
  result.append({'batch_id':item['batch_id'],'source_ids':item['source_ids'],'selection':bind(selected) if selected.exists() else None,'slots':slots,'consumed_N':len(used),'remaining_N':3-len(used)})
 return result
def last_slot_risk(state):return [r['batch_id'] for r in state if not r['selection'] and r['slots'][2]['any_existing_file'] and not r['slots'][2]['process_completion']]
def verify_static(doc):
 manifest=load(CAMPAIGN/'manifest.json');assert manifest['max_total_technical_attempts']==3 and len(manifest['batches'])==207
 for k in ('runner','cli_launcher','validator','instructions','transport_amendment'):exact(manifest[k])
 ids=[]
 for item in manifest['batches']:
  exact(item['assignment']);exact(item['old_assignment']);a=load(item['assignment']['path']);o=load(item['old_assignment']['path']);assert a['source_ids']==o['source_ids']==item['source_ids'] and a['packets']==o['packets'] and a['source_asset_bindings']==o['source_asset_bindings'];exact(a['output_schema']);exact(a['attempt_output_routing']);ids+=a['source_ids']
 assert len(ids)==len(set(ids))==2349
 # Dependency availability is checked now, before any future CLI dispatch.
 import jsonschema
 return manifest
