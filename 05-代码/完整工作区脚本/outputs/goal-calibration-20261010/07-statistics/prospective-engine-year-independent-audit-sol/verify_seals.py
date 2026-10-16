"""Read-only verification of this audit's exact input/output bindings."""
from pathlib import Path
import hashlib, json

HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
inp=json.loads((HERE/'input-seal.json').read_text())
out=json.loads((HERE/'output-seal.json').read_text())
checks={str(p):digest(Path(p))==h for p,h in inp['read_only_original_files'].items()}
for group in ('constructed_inputs','constructed_frozen_source_year_maps'):
    checks.update({str(HERE/p):digest(HERE/p)==h for p,h in inp[group].items()})
checks.update({str(HERE/p):digest(HERE/p)==h for p,h in out['files'].items()})
checks['input-seal binding']=digest(HERE/'input-seal.json')==out['input_seal_sha256']
bad=[p for p,ok in checks.items() if not ok]
print(json.dumps({'status':'verified' if not bad else 'mismatch','file_bindings_checked':len(checks),'mismatches':bad},ensure_ascii=False))
if bad:raise SystemExit(1)
