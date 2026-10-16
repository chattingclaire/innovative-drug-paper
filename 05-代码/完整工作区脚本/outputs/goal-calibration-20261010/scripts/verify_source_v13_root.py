"""Finite independent binding and actual accessor check of sealed source v13."""
from pathlib import Path
import hashlib, importlib.util, json, sys
from datetime import datetime, timezone
from html.parser import HTMLParser
sys.dont_write_bytecode = True
root=Path(__file__).resolve().parents[1]
out=root/'01-review/context-projection-sol/source-interface-v13-addendum'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def cj(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
sealraw=(out/'delivery-seal.json').read_bytes()
assert sha(sealraw)=='c34f1365ed771c7e36ef1d941591e3b715844e34cdc9eb8fd20e05880a3b6620'
seal=json.loads(sealraw)
entries=seal['output_files']+[seal[k] for k in ('base_v12_interface','base_v12_canonical','base_v12_material_manifest','source_addendum_original')]+seal['source_original_files']
checks=[]
for e in entries:
    raw=Path(e['absolute_path']).read_bytes()
    assert sha(raw)==e['sha256'] and len(raw)==e['bytes']
    checks.append({'path':e['absolute_path'],'sha256':e['sha256'],'bytes':len(raw)})
reg=json.loads((out/'source-resource-registry.json').read_bytes())
class Visible(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[]
    def handle_data(self,data):self.parts.append(data)
paragraph_checks=[]
for p in reg['paragraph_resources']:
    loc=p['source_locator']; jloc=loc['structured_snapshot']; hloc=loc['raw_html']; span=hloc['locator']
    value=json.loads(Path(jloc['absolute_path']).read_bytes())
    for token in jloc['json_pointer'].split('/')[1:]:
        token=token.replace('~1','/').replace('~0','~')
        value=value[int(token)] if isinstance(value,list) else value[token]
    assert value==p['text']
    html=Path(hloc['absolute_path']).read_bytes().decode('utf-8')
    outer=html[span['unicode_character_start_zero_based']:span['unicode_character_end_exclusive']]
    assert sha(outer.encode())==span['outer_html_sha256_utf8']
    parser=Visible();parser.feed(outer)
    assert ''.join(parser.parts).strip()==p['text']
    assert sha(p['text'].encode())==p['text_sha256']
    paragraph_checks.append({'resource_id':p['source_resource_id'],'JSON_and_raw_HTML_literal_match':True,'text_sha256':p['text_sha256']})
rows=[json.loads(x) for x in (out/'frame-bundle-bindings.jsonl').read_bytes().splitlines()]
canonical=[json.loads(x) for x in Path(seal['base_v12_canonical']['absolute_path']).read_bytes().splitlines()]
assert len(rows)==len(canonical)==4481
assert len({r['id'] for r in rows})==4481
for r,c in zip(rows,canonical):
    assert r['id']==c['id']
    assert sha(cj(c))==r['source_record_object_sha256']
    assert sha(c['text'].encode())==r['body_utf8_sha256']
    assert sha(cj(c['contexts']))==r['unchanged_context_object_sha256']
assert sum(r['extension_available'] for r in rows)==59
assert sum(r['new_bundle_utf8_bytes'] for r in rows)==69477394
assert sum(r['old_bundle_utf8_bytes'] for r in rows)==66160650
assert sum(len(c['contexts']) for c in canonical)==27534
framehash=sha(('\n'.join(r['id'] for r in rows)+'\n').encode())
assert framehash==seal['frame_ID_order_UTF8_LF_SHA']
profile=json.loads((out/'field-shape-counts.json').read_bytes())
assert profile['frame_N']==4481 and len(profile['field_paths'])==1298
assert profile['frame_ID_order_LF_sha256']==framehash
spec=importlib.util.spec_from_file_location('root_sealed_source_v13',out/'source_only_interface_v13.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
sample_ids=['RECODE25-01423','RECODE25-00889','RECODE25-00064','RECODE25-00001']
byid={r['id']:r for r in rows}
role_checks=[]
for rid in sample_ids:
    calls=[module.lookup(rid,role) for role in ('rule','model','human')]
    encoded=[cj(c) for c in calls]
    assert encoded[0]==encoded[1]==encoded[2]
    assert sha(encoded[0])==byid[rid]['new_bundle_sha256']
    assert len(encoded[0])==byid[rid]['new_bundle_utf8_bytes']
    inv=module.source_inventory(calls[0])
    assert len({i['resource_id'] for i in inv})==len(inv)
    role_checks.append({'id':rid,'actual_role_calls':3,'default_bytes_identical':True,'actual_bundle_sha256':sha(encoded[0]),'inventory_n':len(inv)})
report={'created_at_utc':datetime.now(timezone.utc).isoformat(),
 'source_v13_seal_sha256':sha(sealraw),'file_bindings_checked':checks,
 'original_nine_paragraph_checks':paragraph_checks,
 'all4481_canonical_ID_body_context_binding_checks':True,
 'frame_id_order_sha256':framehash,'old_context_n':27534,
 'producer_all4481_bundle_three_role_claim_sealed':True,
 'root_actual_accessor_three_role_checks':role_checks,
 'root_actual_three_role_checks_are_four_selected_records_not_all4481':True,
 'all4481_profile_and_byte_totals_bound':True,
 'affected_record_n':59,'other_record_n':4422,'new_total_utf8_bytes':69477394,
 'actual_coding_or_semantic_validation':False,'joint_final_freeze':False}
dest=root/'logs/root-source-v13-binding-20261010.json'
dest.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'report':str(dest),'file_bindings_n':len(checks),'paragraph_checks_n':9,'frame_n':4481,'root_actual_role_calls':12,'status':'passed'},ensure_ascii=False))
