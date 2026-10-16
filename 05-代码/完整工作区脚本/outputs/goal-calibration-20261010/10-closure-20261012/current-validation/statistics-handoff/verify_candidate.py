"""Read-only candidate seal verifier, without importing the handoff or reading labels."""
from pathlib import Path
import argparse,hashlib,json
def bind(path):
    path=Path(path).resolve();h=hashlib.sha256();n=0
    with path.open('rb')as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block);n+=len(block)
    return {'path':str(path),'bytes':n,'sha256':h.hexdigest()}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expected-seal-sha',required=True);a=p.parse_args()
    here=Path(__file__).resolve().parent;seal=here/'output-seal.json'
    if bind(seal)['sha256']!=a.expected_seal_sha:raise ValueError('External seal SHA differs')
    data=json.loads(seal.read_text())
    for row in data['members']+data['upstream_bindings']:
        if bind(row['path'])!=row:raise ValueError('Bound file changed: '+row['path'])
    if json.loads((here/'ROOT-registry.UNADOPTED.json').read_text())['registrations']!={}:raise ValueError('Unadopted candidate registry must remain empty')
    print(json.dumps({'status':'all_bindings_verified','members':len(data['members']),'upstream':len(data['upstream_bindings']),'actual_statistics_executed':False}))
if __name__=='__main__':main()
