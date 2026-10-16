"""Exclusive copy of the actor's own complete structured candidate bytes; no editing."""
import argparse, hashlib, json
from pathlib import Path

def main():
    p=argparse.ArgumentParser();p.add_argument('--assignment',required=True);p.add_argument('--first-path',required=True);p.add_argument('--input-file',required=True);x=p.parse_args()
    a=json.loads(Path(x.assignment).read_bytes());routing=json.loads(Path(a['attempt_output_routing']['path']).read_bytes());first=Path(x.first_path).resolve();source=Path(x.input_file).resolve()
    matches=[r for r in routing['routes'] if Path(r['first_path']).resolve()==first and r['batch_id']==a['batch_id']];assert len(matches)==1
    assert source.parent==first.parent and source!=first,'Only own-slot staging candidate allowed'
    raw=source.read_bytes();assert raw,'Empty candidate'
    with first.open('xb') as f:f.write(raw)
    print('FIRST_CREATED '+str(first)+' '+hashlib.sha256(raw).hexdigest())

if __name__=='__main__':main()
