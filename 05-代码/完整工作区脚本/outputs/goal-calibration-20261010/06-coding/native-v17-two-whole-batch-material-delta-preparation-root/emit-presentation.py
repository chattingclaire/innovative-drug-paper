"""Bounded literal presentation helper. No model, interpretation or receipt claim."""
import argparse, hashlib, json
from pathlib import Path

def binding(path):
    p=Path(path).resolve(); raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def allowed(assignment):
    a=json.loads(Path(assignment).read_bytes()); result={str(Path(assignment).resolve()):binding(assignment)}
    for key,value in a.items():
        if key=='common_source_jsonl_identity_only':continue
        if isinstance(value,dict) and {'path','bytes','sha256'}<=set(value):result[value['path']]={k:value[k] for k in ('path','bytes','sha256')}
    for value in a['packets']+a['source_asset_bindings']:result[value['path']]={k:value[k] for k in ('path','bytes','sha256')}
    return result

def main():
    p=argparse.ArgumentParser();p.add_argument('--assignment',required=True);p.add_argument('--path',required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True);x=p.parse_args()
    bound=allowed(x.assignment).get(str(Path(x.path).resolve()));assert bound and binding(x.path)==bound,'Unbound or changed file'
    text=Path(x.path).read_bytes().decode('utf8');assert 0<=x.start<x.end<=len(text) and x.end-x.start<=6500,'Bounded Unicode interval required'
    event='present:'+bound['sha256']+':'+str(x.start)+':'+str(x.end)
    print('PRESENTATION '+json.dumps(dict(**bound,start=x.start,end=x.end,range_kind='unicode_code_points',presentation_event=event),ensure_ascii=False,separators=(',',':')))
    print(text[x.start:x.end],end='');print('\nEND_PRESENTATION '+event)

if __name__=='__main__':main()
