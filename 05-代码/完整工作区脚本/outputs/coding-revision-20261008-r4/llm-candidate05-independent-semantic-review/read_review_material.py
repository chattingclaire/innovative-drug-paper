import json,pathlib,sys
base=pathlib.Path(__file__).resolve().parent.parent/'llm-candidate05-preparation'
mode=sys.argv[1];start=int(sys.argv[2]);end=int(sys.argv[3])
file='candidate05_all_changes_PRIVATE.json' if mode=='changes' else 'candidate05_all62_controls_PRIVATE.json'
d=json.loads((base/file).read_text());rows=d['rows' if mode=='changes' else 'tests']
def texts(x,path='',seen=None):
 if seen is None:seen=set()
 if isinstance(x,dict):
  if isinstance(x.get('text'),str) and x['text'] not in seen:
   seen.add(x['text']);print(path+': '+x['text'])
  for k,v in x.items():
   if k!='text':texts(v,path+'/'+k,seen)
 elif isinstance(x,list):
  for j,v in enumerate(x):texts(v,path+'/'+str(j),seen)
for idx,r in enumerate(rows[start:end],start):
 inp=r['input'];print('\n====',idx,inp['id']);print('TEXT',inp['text']);texts(inp.get('contexts',{}))
 actual=r['candidate05_intact_actual_row' if mode=='changes' else 'actual_row'];print('05',json.dumps(actual,ensure_ascii=False))
 if mode=='changes':
  for name,h in r['historical_intact_rows'].items():
   print('HISTORY',name,h['labels']);print('changed reasons',json.dumps({k:h['dimension_reasons'][k] for k in r['changed_dimensions_vs_each_history'][name]},ensure_ascii=False))
 else:print('EXPECTED',r['labels'],'rationale',r['rationale'],'diff',r['different_dimensions'])
