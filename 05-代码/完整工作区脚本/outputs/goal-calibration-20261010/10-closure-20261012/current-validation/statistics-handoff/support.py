"""Pinned dependencies and byte-preserving I/O; no source/label reads on import."""
from pathlib import Path
import hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BINDINGS_SHA = 'f01f380d40971683cf1e4ef2892f02e7def807dd6f0f80bba349d92810178b15'
REGISTRY_SHA = 'fc932b74f24f7e4cde4bc5ac5c088962592e18857b2889b0f9c85118d34cf47f'

def require(value, message):
    if not value: raise ValueError(message)

def binding(path):
    path=Path(path).resolve(); h=hashlib.sha256(); size=0
    with path.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''): h.update(chunk); size+=len(chunk)
    return {'path':str(path),'bytes':size,'sha256':h.hexdigest()}

def verify(b):
    require(isinstance(b,dict) and set(b)=={'path','bytes','sha256'} and Path(b['path']).is_absolute(),'Exact absolute original binding required')
    require(binding(b['path'])==b,'Original binding changed: '+b['path'])
    return Path(b['path'])

def load(p):
    def pairs(items):
        d={}
        for k,v in items: require(k not in d,'Duplicate JSON key'); d[k]=v
        return d
    return json.loads(Path(p).read_text(),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))

def jsonlines(p):
    return [load_line(line)for line in Path(p).read_text().splitlines()if line.strip()]

def load_line(line):
    def pairs(items):
        d={}
        for k,v in items: require(k not in d,'Duplicate JSONL key'); d[k]=v
        return d
    return json.loads(line,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('Nonfinite JSON')))

def canonical(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def dependencies():
    p=HERE/'bindings.json'; require(binding(p)['sha256']==BINDINGS_SHA,'Dependency external pin changed')
    data=load(p)['inputs']
    for b in data.values(): verify(b)
    return data

def module(name,b):
    p=verify(b); spec=importlib.util.spec_from_file_location(name,p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def save_new(p,value):
    with Path(p).open('x',encoding='utf-8')as f: json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
