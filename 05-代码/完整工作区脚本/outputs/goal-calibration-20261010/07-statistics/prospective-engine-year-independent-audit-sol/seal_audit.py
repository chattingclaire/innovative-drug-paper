"""Seal only this independent audit delivery; never change reviewed originals."""
from pathlib import Path
import difflib, hashlib, json

HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original=HERE.parent/'prospective-engine-year-sol/metrics_engine.py'
repair=HERE/'metrics_engine_repaired.py'
(HERE/'repair.patch').write_text(''.join(difflib.unified_diff(original.read_text().splitlines(True),repair.read_text().splitlines(True),fromfile=str(original),tofile=str(repair))))
inputs=json.loads((HERE/'input-seal.json').read_text())
input_names=set(inputs['constructed_inputs'])|set(inputs['constructed_frozen_source_year_maps'])|{'input-seal.json'}
paths=sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and str(p.relative_to(HERE)) not in input_names and p.name!='output-seal.json')
seal={'schema':'file-sha256-seal-v1','role':'independent_ai_technical_audit_and_repair_candidate',
      'files':{str(p.relative_to(HERE)):digest(p) for p in paths},
      'input_seal_sha256':digest(HERE/'input-seal.json'),'self_excluded_to_avoid_recursive_hash':True,
      'original_code_modified':False,'real_label_gold_or_actual_year_statistics_inputs':0}
(HERE/'output-seal.json').write_text(json.dumps(seal,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'output_files_sealed':len(paths),'input_seal_sha256':seal['input_seal_sha256']},ensure_ascii=False))
