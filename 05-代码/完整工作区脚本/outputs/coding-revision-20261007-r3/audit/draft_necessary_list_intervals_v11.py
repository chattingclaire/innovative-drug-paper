from pathlib import Path
import json,re,unicodedata
BASE=Path(__file__).resolve().parents[1]
def rank(t):
 t=unicodedata.normalize('NFKC',t.strip())
 if re.match(r'^第[一二三四五六七八九十百零]+[章节]',t):return 0
 if re.match(r'^第[一二三四五六七八九十百零]+条',t):return 1
 if re.match(r'^[一二三四五六七八九十]+[、.]',t):return 2
 if re.match(r'^\([一二三四五六七八九十]+\)',t):return 3
 if re.match(r'^\d+[、.](?!\d)',t):return 4
 if re.match(r'^\d+\.\d+',t):return 4
 if re.match(r'^\(\d+\)',t):return 5
 if t.startswith('•'):return 6
 return None
preview=set('00321 00596 00916 00937 00996 01016 01046 01088 01194 01233 01250 01797 01944 01963 02147 02163 02250 02299 02592 02614 02832 02908 03164 03655 04271 04287 03701 00054'.split())
rows=[json.loads(x) for x in (BASE/'rule_inputs_shared_v10.jsonl').read_text().splitlines()];out=[]
for row in rows:
 r=row['input'];cs=r['llm_v29_shared_context'];f=cs.get('structured_following_units',[])
 if not f:continue
 rid=row['id'];short=rid[-5:]
 if short in preview:continue
 ps=json.loads(Path(r['candidate_file']).read_text())['paragraphs'];idx={p['id']:i for i,p in enumerate(ps)};i=next(idx[p['paragraph_id']] for p in cs['paragraph_context'] if p.get('paragraph_id') in idx)
 cert=r.get('verified_following_list_v27')
 if cert:
  j=idx[cert['contexts'][-1]['paragraph_id']];mode='reuse_source_reviewed_certificate'
 else:
  own=rank(r['unit_text']);scope=own
  if scope is None:
   hs=[rank(p['text']) for p in ps[:i] if p.get('type')=='heading_candidate' and rank(p['text']) is not None];scope=hs[-1] if hs else None
  if scope is None:
   first=next((rank(p['text']) for p in ps[i+1:] if rank(p['text']) is not None),None);scope=first-1 if first is not None else 0
  j=len(ps)-1
  for k,p in enumerate(ps[i+1:],i+1):
   rk=rank(p['text'])
   if rk is not None and rk<=scope:j=k-1;break
  mode='draft_scope_rank_'+str(scope)
 out.append({'id':rid,'start_paragraph_id':ps[i]['id'],'end_paragraph_id':ps[j]['id'],'next_boundary_paragraph_id':ps[j+1]['id'] if j+1<len(ps) else None,'head':r['unit_text'],'n':j-i,'next':ps[j+1]['text'] if j+1<len(ps) else None,'mode':mode,'candidate_file':r['candidate_file']})
(BASE/'audit/draft_necessary_list_intervals_v11.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for x in out:print(x['id'],x['start_paragraph_id'],x['end_paragraph_id'],x['n'],x['mode'],x['head'][:55],'NEXT',str(x['next'])[:85])
