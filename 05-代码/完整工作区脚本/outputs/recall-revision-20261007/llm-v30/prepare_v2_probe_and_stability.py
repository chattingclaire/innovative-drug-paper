"""Exact material refresh only, without reading the private blind mapping or any labels."""
from pathlib import Path
import copy,json,hashlib,shutil
HERE=Path(__file__).resolve().parent;BASE=HERE.parent
V1='6fa91f237c8762fb117cb6c920d6a689dd65ee35f3b938db2f0a569bf9b965b8';V2='0c05b1dbd43a74943bb1deafd26b1dbb1963bef0505dda501d83cdf1bfed9955'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def load(p):return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]
def stripids(x):
 if isinstance(x,dict):return {k:stripids(v) for k,v in x.items() if k not in {'id','unit_id'}}
 if isinstance(x,list):return [stripids(v) for v in x]
 return x
def key(r):return json.dumps(stripids(r),ensure_ascii=False,sort_keys=True,separators=(',',':'))
def paths(x,y,path=''):
 out=[]
 if isinstance(x,dict) and isinstance(y,dict):
  for k in sorted(set(x)|set(y)):
   if k not in x or k not in y:out.append(path+'.'+k)
   elif x[k]!=y[k]:out.extend(paths(x[k],y[k],path+'.'+k))
 elif isinstance(x,list) and isinstance(y,list):
  if len(x)!=len(y):out.append(path+'.list_length')
  else:
   for i,(a,b) in enumerate(zip(x,y)):
    if a!=b:out.extend(paths(a,b,path+f'[{i}]'))
 elif x!=y:out.append(path)
 return out
def restore_prior_blind_metadata(old,new,bid):
 if isinstance(old,dict) and isinstance(new,dict):
  for k,v in old.items():
   if k in new:
    if k=='unit_id' and v==bid:new[k]=bid
    else:restore_prior_blind_metadata(v,new[k],bid)
 elif isinstance(old,list) and isinstance(new,list):
  for a,b in zip(old,new):restore_prior_blind_metadata(a,b,bid)
def main():
 v1p=BASE/'effective_blind_inputs_v30.jsonl';v2p=BASE/'effective_blind_inputs_v30_v2.jsonl';probe=BASE/'blind90_completed_material.jsonl';assert sha(v1p)==V1 and sha(v2p)==V2
 one=load(v1p);two=load(v2p);assert len(one)==len(two)==4924;v2byid={r['id']:r for r in two};lookup={}
 for r in one:lookup.setdefault(key(r),[]).append(r['id'])
 out=HERE/'material-v2';out.mkdir(exist_ok=True);new90=[];affected=[];changes=[]
 for old in load(probe):
  candidates=lookup[key(old)];assert len({key(v2byid[rid]) for rid in candidates})==1,'ambiguous textual match has differing v2 materials'
  new=copy.deepcopy(v2byid[candidates[0]]);new['id']=old['id'];restore_prior_blind_metadata(old,new,old['id']);new90.append(new)
  if key(old)!=key(new):affected.append(new);changes.append({'blind_id':old['id'],'changed_paths':paths(stripids(old),stripids(new)),'unit_text_unchanged':old['text']==new['text']})
 assert len(new90)==90 and all(a['text']==b['text'] for a,b in zip(load(probe),new90))
 for name,rs in [('blind90_completed_material_v2.jsonl',new90),('affected_blind90_v2.jsonl',affected)]:
  p=out/name;data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rs)
  if p.exists():assert p.read_text()==data
  else:p.write_text(data)
 report={'status':'exact_material_comparison_complete','v1_full_sha256':V1,'v2_full_sha256':V2,'probe_v1_sha256':sha(probe),'probe_v2_sha256':sha(out/'blind90_completed_material_v2.jsonl'),'affected_probe_sha256':sha(out/'affected_blind90_v2.jsonl'),'total_probe_n':90,'affected_n':len(affected),'unchanged_n':90-len(affected),'all_unit_texts_unchanged':True,'private_mapping_not_read':True,'no_labels_or_machine_outputs_read_for_material_refresh':True,'changes':changes};write(out/'probe_material_v1_v2_comparison.json',report)
 # Freeze IDs as before, refresh sample material only. Preserve previous preparation.
 st=HERE/'stability-v30';hist=HERE/'stability-v30-v1-preparation'
 if not hist.exists():shutil.copytree(st,hist)
 plan=json.loads((hist/'sample_and_execution_plan.json').read_text());ids=[rid for group in ['NMPA','NHSA','NHC'] for rid in plan['ids'][group]];sample=st/'same_batch_36.jsonl';fresh=[v2byid[rid] for rid in ids];oldsample=load(hist/'same_batch_36.jsonl');sample.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in fresh));plan['full_input_sha256']=V2;plan['full_input_path']=str(v2p.resolve());plan['sample_sha256']=sha(sample);plan['material_policy']='All 36 records refreshed from final v2 completed input; v1 preparation preserved separately and no old outputs used.';plan['v1_preparation_preserved']=str(hist.resolve());plan['material_change_n_vs_v1']=sum(key(a)!=key(b) for a,b in zip(oldsample,fresh));write(st/'sample_and_execution_plan.json',plan)
 print(json.dumps({'probe_material_comparison':report,'stability_36_material_change_n':plan['material_change_n_vs_v1'],'stability_v2_sample_sha256':plan['sample_sha256']},ensure_ascii=False))
if __name__=='__main__':main()
