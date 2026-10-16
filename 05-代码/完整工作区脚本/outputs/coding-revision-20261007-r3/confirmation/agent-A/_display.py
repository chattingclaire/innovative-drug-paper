import json,sys,pathlib
p=pathlib.Path(__file__).parent/f'材料-{int(sys.argv[1]):02d}.json';d=json.loads(p.read_text())
def walk(o,path=''):
 if isinstance(o,dict):
  for k,v in o.items(): walk(v,path+'.'+k)
 elif isinstance(o,list):
  if not o: print(path+'=[]')
  for i,v in enumerate(o): walk(v,path+f'[{i}]')
 elif isinstance(o,str) and not (path.endswith(('sha256','source_path','candidate_path','source','source_hash_field','unit_text_sha256','text_sha256','paragraph_id','id','normalization')) or o.startswith('/Users/')): print(path+': '+o)
a=int(sys.argv[2]) if len(sys.argv)>2 else 0;b=int(sys.argv[3]) if len(sys.argv)>3 else 30
for r in d['rows'][a:b]:
 print('\n'+r['id']+' '+r['text']);walk(r['contexts'],'ctx')
