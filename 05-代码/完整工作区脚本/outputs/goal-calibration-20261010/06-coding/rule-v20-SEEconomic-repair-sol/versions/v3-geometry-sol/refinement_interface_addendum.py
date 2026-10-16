"""Repair only missing outer fixture envelope; leave texts/geometry/expected fixed."""
import copy,hashlib,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
P=Path(__file__).resolve().parent
from source_packet import BUNDLE_KEYS
old=P/'refinement-controls-fixed.json';data=json.loads(old.read_text());fixed=copy.deepcopy(data)
changes=[]
for c in fixed['cases']:
    b=c.get('synthetic_bundle',{})
    missing=sorted(BUNDLE_KEYS-set(b))
    if not missing:continue
    for key in missing:b[key]={'status':'synthetic_development_fixture'} if key=='common_source_bundle_version' else {} if key in ('source_locator_bases',) else []
    changes.append({'name':c['name'],'added_envelope_fields':missing,'original_expected':c['expected'],'expected_changed':False,'source_text_or_geometry_changed':False})
with (P/'refinement-controls-interface-complete.json').open('x',encoding='utf8') as f:json.dump(fixed,f,ensure_ascii=False,indent=2);f.write('\n')
with (P/'refinement-interface-addendum.json').open('x',encoding='utf8') as f:json.dump({'original_path':str(old),'original_sha256':hashlib.sha256(old.read_bytes()).hexdigest(),'attempt02_four_PacketInterfaceError_preserved':True,'changes':changes,'algorithm_not_changed':True},f,ensure_ascii=False,indent=2);f.write('\n')
