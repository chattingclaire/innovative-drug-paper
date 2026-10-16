"""One-time metadata/template SHA binding, without opening packet/source bodies."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SOURCE = ROOT / '05-validation/full800-common-v15-prerelease-sol'
DELIVERY = ROOT / '09-delivery/formal800-human-workbooks-prerelease-sol'
LEGACY = ROOT / '05-validation/formal-freeze-interface-v1-sol'


def binding(p):
    raw = p.read_bytes()
    return {'path': str(p.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


inputs = {'workbook_manifest': DELIVERY / 'workbook-manifest.json', 'delivery_seal': DELIVERY / 'seal.json',
          'source_seal': SOURCE / 'seal.json', 'mapping': SOURCE / 'coordinator-private/mapping.json',
          'draw_contract': SOURCE / 'coordinator-private/draw-contract.json',
          'readiness_report': ROOT / '05-validation/formal-freeze-interface-readiness-sol/report.md',
          'old_sidecar_schema': LEGACY / 'submission-sidecar.schema.json'}
for side in 'AB':
    inputs['template_' + side] = DELIVERY / ('coder-' + side) / ('formal800-' + side + '-pre-release.xlsx')
    for key, name in [('labels', 'labels.blank.jsonl'), ('submission', 'submission.blank.json'), ('index', 'packet-index.json')]:
        inputs[key + '_' + side] = SOURCE / ('coder-' + side) / name
output = {'version': 'formal800-xlsx-reception-bindings-1',
          'inputs': {key: binding(p) for key, p in inputs.items()},
          'dependencies': {key: binding(LEGACY / (key + '.py')) for key in ('interface_common', 'human_receiver')},
          'read_scope': 'metadata, schemas, blank forms, exact template comparison only; source body/77 labels not semantically read'}
with (HERE / 'bindings.json').open('x') as f:
    f.write(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'bound_input_N': len(inputs), 'source_body_files_opened': 0}))
