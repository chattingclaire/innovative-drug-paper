"""Mechanical source-only v15 projection. No coding dispatch or label access."""
from pathlib import Path
import copy, datetime, hashlib, importlib.util, json, os, subprocess, sys
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
V14 = ROOT / '01-review/context-projection-sol/source-interface-v14-textleaf'
INPUT77 = ROOT / '06-coding/development77-native-inputs-v14'
SOURCE_SHA = '64ac48e58753780279df45a96c595f6415e84fef087a316b66f26def2cd5658c'
PDF = ROOT / '00-baseline/source-files/64ac48e587537802-NHSA-常用问答-2026版.pdf'
PAGES = (8, 9, 20, 21)
REPORT_INPUT = ROOT / 'logs/remaining4-calibration-delivery/report-inputs.json'
NATIVE_META = ROOT / '06-coding/native-llm77-v16-sol/run-manifest.json'
V18_SCOPE = ROOT / '06-coding/rule-v18-overall-health-boundary-development-root/source-scope.json'
ADAPTER_DIR = ROOT / '05-validation/rule-request-routing-repair-sol'
EXT_KEY = 'v15_same_pdf_physical_page_text'

def H(raw): return hashlib.sha256(raw).hexdigest()
def canonical(value): return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
def parse(path): return json.loads(Path(path).read_bytes())
def binding(path):
    path=Path(path).resolve(); raw=path.read_bytes()
    return {'path':str(path),'sha256':H(raw),'bytes':len(raw)}
def checked(entry):
    path=Path(entry.get('path',entry.get('absolute_path'))).resolve(); raw=path.read_bytes()
    assert H(raw)==entry['sha256'] and len(raw)==entry['bytes'], str(path)
    return raw

def save(path,raw):
    path=Path(path); assert path.resolve().is_relative_to(OUT)
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as handle: handle.write(raw)
def savejson(path,value): save(path,canonical(value))
def imported(name,path):
    spec=importlib.util.spec_from_file_location(name,path); module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module;spec.loader.exec_module(module);return module

def forbidden_check(value,forbidden):
    if isinstance(value,dict):
        assert not (set(value)&forbidden), str(set(value)&forbidden)
        for item in value.values(): forbidden_check(item,forbidden)
    elif isinstance(value,list):
        for item in value: forbidden_check(item,forbidden)

# Only source bindings/manual metadata from the old scope are selected.
scope=parse(V18_SCOPE)
SOURCE_BASE=Path(scope['v12_source_base']).resolve()
old_material_bindings=copy.deepcopy(scope['material_bindings']); assert len(old_material_bindings)==13
for entry in old_material_bindings: checked(entry)
manual=copy.deepcopy(scope['manual']);checked(manual)
seal=parse(V14/'seal.json');v14_members={Path(e['absolute_path']).name:e for e in seal['members']}
for entry in seal['members']: checked(entry)
for name in ('source_only_interface_v14.py','common-frame-bundles-v14.jsonl','frame-bundle-bindings-v14.jsonl'):
    assert name in v14_members
assert H(PDF.read_bytes())==SOURCE_SHA
batch_metadata=parse(INPUT77/'batching-manifest.json')
global_order=copy.deepcopy(batch_metadata['global_order']); assert len(global_order)==len(set(global_order))==77
native=parse(NATIVE_META)
# Deliberately do not access run results, first judgments or label fields.
native_metadata={'manual':copy.deepcopy(native['manual']),'record_N':native['record_N'],
                 'global_order':copy.deepcopy(native['global_order']),
                 'batches':[{k:copy.deepcopy(b[k]) for k in ('batch_id','expected_N','assignment_path','assignment_sha256','source_ids')} for b in native['batches']]}
assert native_metadata['manual']==manual and native_metadata['record_N']==77
assert native_metadata['global_order']==global_order
assert len(native_metadata['batches'])==13 and sum([b['source_ids'] for b in native_metadata['batches']],[])==global_order
assert all(len(b['source_ids'])==b['expected_N'] for b in native_metadata['batches'])
order_lf=('\n'.join(global_order)+'\n').encode('utf-8')
assert H(order_lf)==batch_metadata['global_order_UTF8_LF_sha256']

# Read only the four material blocks and PDF/image binding entries.
report=parse(REPORT_INPUT)
blocks={b['key']:b for b in report['blocks'] if b.get('key') in {'03876补材'+str(p) for p in PAGES}}
assert set(blocks)=={'03876补材'+str(p) for p in PAGES}
material_pdf_image_entries=[b for b in report['bindings'] if b.get('path') in {str(PDF),report['image_path']}]
assert len(material_pdf_image_entries)==2
for e in material_pdf_image_entries:
    assert H(Path(e['path']).read_bytes())==e['sha256']
report_material_bindings=[binding(e['path']) for e in material_pdf_image_entries]
pdftotext='/opt/homebrew/bin/pdftotext'
version=subprocess.run([pdftotext,'-v'],capture_output=True,check=True)
version_text=(version.stderr+version.stdout).decode('utf-8',errors='strict').splitlines()[0]
extractions=[];paragraphs=[]
for page in PAGES:
    args=[pdftotext,'-f',str(page),'-l',str(page),'-layout',str(PDF),'-']
    extracted=subprocess.run(args,check=True,capture_output=True).stdout
    text=extracted.decode('utf-8',errors='strict');block=blocks['03876补材'+str(page)]
    assert block['path']==str(PDF) and text==block['text']
    assert H(extracted)==block['text_sha256'] and text.count('\f')==1 and text.endswith('\f')
    text_path=OUT/'extracted-pages'/f'{SOURCE_SHA[:16]}-physical-page-{page:02d}.utf8.txt'
    save(text_path,extracted)
    locator={'kind':'original_PDF_physical_page_text','physical_page':page,
             'source_pdf_sha256':SOURCE_SHA,'extraction_method':'pdftotext_layout',
             'fullpage_text_utf8_sha256':H(extracted),'fullpage_text_utf8_bytes':len(extracted),
             'fullpage_text_includes_formfeed':True}
    paragraphs.append({'source_paragraph_id':f'SOURCEPARAGRAPH-{SOURCE_SHA}-physical-page-{page:02d}',
                       'source_sha256':SOURCE_SHA,'representation':'original_same_PDF_full_physical_page_text',
                       'text':text,'source_locator':locator})
    extractions.append({'physical_page':page,'command_arguments':args,'output_file':binding(text_path),
                        'original_material_block':{'key':block['key'],'path':block['path'],
                                                   'text_sha256':block['text_sha256'],'text_utf8_bytes':len(block['text'].encode('utf-8'))},
                        'exact_text_and_UTF8_byte_equality_including_formfeed':True,
                        'formfeed_count':text.count('\f')})
payload={'source_resource_id':'SOURCE-'+SOURCE_SHA,'source_sha256':SOURCE_SHA,
         'source_pdf_sha256':SOURCE_SHA,'representation':'original_same_PDF_physical_page_text_payload',
         'physical_pages':list(PAGES),'extraction_method':'pdftotext_layout','paragraphs':paragraphs}
payload_path=OUT/'source-library/nhsa-common-qa-physical-pages-8-9-20-21-v15.json'
savejson(payload_path,payload);payload_binding=binding(payload_path);payload_view_sha=H(canonical(payload))
source_text_metadata={'relative_path':os.path.relpath(payload_path,SOURCE_BASE),'relative_path_base':str(SOURCE_BASE),
                      'sha256':payload_binding['sha256'],'bytes':payload_binding['bytes'],'source_pdf_sha256':SOURCE_SHA}
assert (SOURCE_BASE/source_text_metadata['relative_path']).resolve()==payload_path
extract_chain={'version':'original-PDF-four-physical-pages-extract-chain/v15','original_pdf':binding(PDF),
               'pdftotext_version':version_text,'encoding':'UTF-8','normalization_applied':False,
               'physical_pages':list(PAGES),'page_extractions':extractions,'payload_file':payload_binding,
               'payload_canonical_view_sha256':payload_view_sha,
               'original_material_block_container_byte_binding':binding(REPORT_INPUT),
               'original_PDF_and_image_bindings_only':report_material_bindings,
               'no_rows_questions_or_target_coding_fields_accessed':True,
               'consumer_read_and_use_created':False}
extract_path=OUT/'pdf-extract-chain-v15.json';savejson(extract_path,extract_chain)
manifest={'version':'source-interface/v15-same-PDF-physical-page-text',
          'base_interface':{'absolute_path':str(V14/'source_only_interface_v14.py'),
                            'sha256':v14_members['source_only_interface_v14.py']['sha256'],
                            'bytes':v14_members['source_only_interface_v14.py']['bytes']},
          'base_source_interface_seal':binding(V14/'seal.json'),
          'base_frame_bundles':binding(V14/'common-frame-bundles-v14.jsonl'),
          'base_frame_bundle_bindings':binding(V14/'frame-bundle-bindings-v14.jsonl'),
          'binding_source_pdf_sha256':SOURCE_SHA,'original_pdf':binding(PDF),
          'payload_file':payload_binding,'payload_canonical_view_sha256':payload_view_sha,
          'source_text_resource_metadata':source_text_metadata,'v12_source_base':str(SOURCE_BASE),
          'page_extractions':extractions,'extract_chain_file':binding(extract_path),
          'availability_binding':'exact original PDF SHA in source_documents; no record-ID, keyword or coding filter',
          'common_source_bundle_version_policy':'preserve original base identity exactly; extension recorded separately',
          'consumer_read_status':'not_recorded','consumer_use_status':'not_recorded',
          'semantic_applicability_granted':False}
manifest_path=OUT/'source-extension-manifest-v15.json';savejson(manifest_path,manifest)
manifest_binding=binding(manifest_path)
wrapper=r"""\
\"\"\"Same-PDF page FULLSOURCE extension of exact sealed v14. No coding or read/use inference.\"\"\"
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
OUT=Path(__file__).resolve().parent
MANIFEST_SHA=__MANIFEST_SHA__
EXT_KEY='v15_same_pdf_physical_page_text'
def cj(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def _sha(raw): return hashlib.sha256(raw).hexdigest()
def _checked(entry):
    path=Path(entry.get('path',entry.get('absolute_path'))).resolve();raw=path.read_bytes()
    if _sha(raw)!=entry['sha256'] or len(raw)!=entry['bytes']: raise ValueError('sealed source byte SHA/size mismatch: '+str(path))
    return raw
_raw=(OUT/'source-extension-manifest-v15.json').read_bytes()
if _sha(_raw)!=MANIFEST_SHA: raise ValueError('v15 source extension manifest SHA mismatch')
_manifest=json.loads(_raw);_interface=_manifest['base_interface'];_checked(_interface)
_spec=importlib.util.spec_from_file_location('sealed_v14_source_accessor',_interface['absolute_path'])
_base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_base)
_registry_cache=None

def extension_registry():
    global _registry_cache
    if _registry_cache is None:
        pdf_sha=_manifest['binding_source_pdf_sha256'];_checked(_manifest['original_pdf'])
        if _manifest['original_pdf']['sha256']!=pdf_sha: raise ValueError('original PDF identity differs')
        payload=json.loads(_checked(_manifest['payload_file']));_checked(_manifest['extract_chain_file'])
        if payload.get('source_resource_id')!='SOURCE-'+pdf_sha or payload.get('source_sha256')!=pdf_sha or payload.get('source_pdf_sha256')!=pdf_sha:
            raise ValueError('FULLSOURCE payload original PDF identity differs')
        if _sha(cj(payload).encode('utf-8'))!=_manifest['payload_canonical_view_sha256']: raise ValueError('payload canonical SHA mismatch')
        pages=_manifest['page_extractions']
        if len(payload.get('paragraphs',[]))!=len(pages): raise ValueError('full physical page resource count differs')
        for paragraph,page in zip(payload['paragraphs'],pages):
            raw=_checked(page['output_file']);locator=paragraph['source_locator']
            if paragraph['text'].encode('utf-8')!=raw or paragraph['source_sha256']!=pdf_sha:
                raise ValueError('full physical page text bytes or PDF identity differ')
            if locator['kind']!='original_PDF_physical_page_text' or locator['physical_page']!=page['physical_page'] or locator['source_pdf_sha256']!=pdf_sha:
                raise ValueError('full physical page locator differs')
            if locator['fullpage_text_utf8_sha256']!=_sha(raw) or locator['fullpage_text_utf8_bytes']!=len(raw): raise ValueError('page text SHA/size differs')
            if _sha(raw)!=page['original_material_block']['text_sha256'] or len(raw)!=page['original_material_block']['text_utf8_bytes']:
                raise ValueError('original material block byte binding differs')
        metadata=_manifest['source_text_resource_metadata']
        path=(Path(_manifest['v12_source_base'])/metadata['relative_path']).resolve()
        if path!=Path(_manifest['payload_file']['path']).resolve() or metadata['sha256']!=_manifest['payload_file']['sha256'] or metadata['bytes']!=_manifest['payload_file']['bytes'] or metadata['source_pdf_sha256']!=pdf_sha:
            raise ValueError('source text resource relative locator or byte binding differs')
        _registry_cache=payload
    return _registry_cache

def extend_bundle(old_bundle):
    pdf_sha=_manifest['binding_source_pdf_sha256']
    matches=[i for i,d in enumerate(old_bundle['source_documents']) if d.get('source_sha256')==pdf_sha]
    if not matches: return old_bundle
    if len(matches)!=1: raise ValueError('original PDF document identity is not unique')
    payload=extension_registry();result=copy.deepcopy(old_bundle);index=matches[0]
    doc=result['source_documents'][index]
    if doc.get('source_resource_id')!='SOURCE-'+pdf_sha: raise ValueError('original PDF document resource ID differs')
    if 'source_text_resource' in doc: raise ValueError('existing source text resource metadata would be overwritten')
    doc['source_text_resource']=copy.deepcopy(_manifest['source_text_resource_metadata'])
    result['source_full_text_resources'].append(copy.deepcopy(payload))
    extension=result.setdefault('source_bundle_extension',{})
    if EXT_KEY in extension: raise ValueError('v15 source extension already present')
    extension[EXT_KEY]={
        'version':_manifest['version'],'base_accessor_version':'source_only_interface_v14',
        'old_v14_bundle_sha256':_sha(cj(old_bundle).encode('utf-8')),
        'extension_manifest':{'absolute_path':str(OUT/'source-extension-manifest-v15.json'),'sha256':MANIFEST_SHA,'bytes':len(_raw)},
        'source_pdf_sha256':pdf_sha,'payload_file':copy.deepcopy(_manifest['payload_file']),
        'payload_canonical_view_sha256':_manifest['payload_canonical_view_sha256'],
        'available_added_physical_page_N':len(payload['paragraphs']),
        'availability_scope':'same original PDF SHA across source document identities',
        'semantic_applicability_granted':False,'consumer_read_status':'not_recorded','consumer_use_status':'not_recorded'}
    return result

def lookup(record_id,selector='model',bundle=True):
    old=_base.lookup(record_id,selector,bundle=bundle)
    if selector=='unit' or not bundle: return old
    return extend_bundle(old)

def source_inventory(bundle):
    \"\"\"The original v14/base inventory handles FULLSOURCE; availability is no read/use event.\"\"\"
    return _base.source_inventory(bundle)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('interface',choices=['rule','model','human','unit']);parser.add_argument('id')
    parser.add_argument('--record-only',action='store_true');parser.add_argument('--inventory',action='store_true');args=parser.parse_args()
    try:
        result=lookup(args.id,args.interface,bundle=not args.record_only)
        if args.inventory:
            if args.record_only or args.interface=='unit': raise ValueError('inventory needs complete bundle')
            result=source_inventory(result)
    except (ValueError,KeyError) as error: parser.error(str(error))
    print(cj(result))
"""
# Raw template uses escaped triple quotes to keep the generator self-contained.
wrapper=wrapper.replace('\\"','"').removeprefix('\\\n').replace('__MANIFEST_SHA__',repr(manifest_binding['sha256']))
wrapper_path=OUT/'source_only_interface_v15.py';save(wrapper_path,wrapper.encode('utf-8'))
compile(wrapper,str(wrapper_path),'exec')
v15=imported('source_only_interface_v15_projection',wrapper_path)
assert v15.extension_registry()==payload

# One pass over sealed source-only bundles: identity/order/hash checks and projection.
old_frame=[json.loads(line) for line in (V14/'frame-bundle-bindings-v14.jsonl').read_bytes().splitlines() if line]
assert len(old_frame)==4481 and len({e['id'] for e in old_frame})==4481
frame_binding_rows=[];changed_ids=[];selected_new={};selected_old={};frame_order=[];primary_N=0;docmatch_N=0;contextmatch_N=0
frame_out=OUT/'common-frame-bundles-v15.jsonl'
with frame_out.open('xb') as target, (V14/'common-frame-bundles-v14.jsonl').open('rb') as source:
    for index,line in enumerate(source):
        old=json.loads(line);rid=old['source_record']['id'];rawold=canonical(old);entry=old_frame[index]
        assert entry['id']==rid and entry['frame_ordinal_1based']==index+1
        assert H(rawold)==entry['new_v14_bundle_sha256'] and len(rawold)==entry['new_v14_bundle_utf8_bytes']
        assert H(canonical(old['source_record']))==entry['source_record_object_sha256']
        frame_order.append(rid)
        primary_N+=old['source_record']['source_ref']['sha256']==SOURCE_SHA
        matched=[i for i,d in enumerate(old['source_documents']) if d.get('source_sha256')==SOURCE_SHA]
        docmatch_N+=bool(matched);contextmatch_N+=any(c['source_ref']['sha256']==SOURCE_SHA for c in old['source_record']['contexts'])
        new=v15.extend_bundle(old);rawnew=canonical(new);changed=rawnew!=rawold
        assert changed==bool(matched)
        for key,value in old.items():
            if key not in {'source_documents','source_full_text_resources','source_bundle_extension'}: assert canonical(new[key])==canonical(value), (rid,key)
        assert new['source_full_text_resources'][:len(old['source_full_text_resources'])]==old['source_full_text_resources']
        assert new['source_record']==old['source_record'] and new['common_source_bundle_version']==old['common_source_bundle_version']
        new_docs=copy.deepcopy(new['source_documents'])
        if changed:
            assert len(matched)==1
            assert new_docs[matched[0]].pop('source_text_resource')==source_text_metadata
            assert new['source_full_text_resources'][len(old['source_full_text_resources']):]==[payload]
            old_extension=copy.deepcopy(new['source_bundle_extension']);old_extension.pop(EXT_KEY)
            assert old_extension==old.get('source_bundle_extension',{})
            changed_ids.append(rid)
        else: assert rawnew==rawold
        assert new_docs==old['source_documents']
        target.write(rawnew+b'\n')
        frame_binding_rows.append({'frame_ordinal_1based':index+1,'id':rid,'primary_source_sha256':entry['primary_source_sha256'],
                                  'old_v14_bundle_sha256':H(rawold),'old_v14_bundle_utf8_bytes':len(rawold),
                                  'new_v15_bundle_sha256':H(rawnew),'new_v15_bundle_utf8_bytes':len(rawnew),
                                  'source_record_object_sha256':H(canonical(new['source_record'])),
                                  'old_current_source_record_and_contexts_exact':True,'base_bundle_identity_exact':True,
                                  'old_source_full_text_resources_prefix_N':len(old['source_full_text_resources']),
                                  'added_FULLSOURCE_payload_N':int(changed),'added_physical_page_N':4 if changed else 0,
                                  'source_document_metadata_changed_pointers':[f'/source_documents/{i}/source_text_resource' for i in matched],
                                  'original_asset_fields_exact':True,'projection_status':'mechanical_source_projection_only',
                                  'actual_coding_or_consumer_read_run':False})
        if rid in global_order: selected_new[rid]=new;selected_old[rid]=old
assert len(frame_order)==len(set(frame_order))==4481
assert primary_N==docmatch_N==contextmatch_N==len(changed_ids)==224
assert len(selected_new)==77
save(OUT/'frame-bundle-bindings-v15.jsonl',b''.join(canonical(e)+b'\n' for e in frame_binding_rows))
savejson(OUT/'changed-source-record-ids-v15.json',{'source_pdf_sha256':SOURCE_SHA,'frame_N':4481,'same_source_N':len(changed_ids),
                                                 'record_ids_in_frame_order':changed_ids,'selection_basis':'exact original source PDF SHA only'})

DEV=OUT/'development77';DEV.mkdir(exist_ok=False)
old77=[json.loads(line) for line in (INPUT77/'common-source-bundles-v14.jsonl').read_bytes().splitlines() if line]
assert [b['source_record']['id'] for b in old77]==global_order
assert all(b==selected_old[b['source_record']['id']] for b in old77)
source77_path=DEV/'common-source-bundles-v15.jsonl'
save(source77_path,b''.join(canonical(selected_new[rid])+b'\n' for rid in global_order))
packet_bindings=[];shared=[];old_asset_files={};packet_unchanged_field_checks=0
for rid in global_order:
    old_path=INPUT77/'packets'/f'{rid}.compact.json';old_packet=parse(old_path)
    assert old_packet['source_id']==rid and old_packet['source_bundle']==selected_old[rid]
    assert old_packet['source_bundle_sha256']==H(canonical(selected_old[rid]))
    new_packet=copy.deepcopy(old_packet);new_packet['source_bundle']=copy.deepcopy(selected_new[rid]);new_packet['source_bundle_sha256']=H(canonical(selected_new[rid]))
    for key,value in old_packet.items():
        if key not in {'source_bundle','source_bundle_sha256'}:
            assert canonical(new_packet[key])==canonical(value);packet_unchanged_field_checks+=1
    for asset in old_packet['verified_asset_files']:
        ap=Path(asset['absolute_path']).resolve();raw=ap.read_bytes()
        assert H(raw)==asset['sha256'] and len(raw)==asset['bytes'];old_asset_files[str(ap)]=binding(ap)
    packet_path=DEV/'packets'/f'{rid}.compact.json';savejson(packet_path,new_packet)
    packet_bindings.append({'source_id':rid,'packet':binding(packet_path),'original_packet':binding(old_path),
                            'source_bundle_sha256':new_packet['source_bundle_sha256'],'other_packet_fields_byte_equivalent':True})
    shared.append({'source_id':rid,'common_bare_bundle_sha256':new_packet['source_bundle_sha256'],
                   'rule_input_bundle_sha256':new_packet['source_bundle_sha256'],
                   'native_input_bundle_sha256':new_packet['source_bundle_sha256'],
                   'shared_input_assignment_only_actual_read_or_use_not_claimed':True})

# Preserve packet version. The new schema adds only the documented nested extension.
old_packet_schema_path=ROOT/'06-coding/protocol-necessary-read-v3/packet.schema.json'
packet_schema=parse(old_packet_schema_path);old_extension_schema=copy.deepcopy(packet_schema['properties']['source_bundle']['properties']['source_bundle_extension'])
sha_schema={'type':'string','pattern':'^[a-f0-9]{64}$'}
file_schema={'type':'object','additionalProperties':False,'required':['path','sha256','bytes'],
             'properties':{'path':{'type':'string','pattern':'^/'},'sha256':sha_schema,'bytes':{'type':'integer','minimum':0}}}
ext_fields={'version':{'const':manifest['version']},'base_accessor_version':{'const':'source_only_interface_v14'},
            'old_v14_bundle_sha256':sha_schema,'extension_manifest':{'type':'object','additionalProperties':False,
            'required':['absolute_path','sha256','bytes'],'properties':{'absolute_path':{'type':'string','pattern':'^/'},'sha256':sha_schema,'bytes':{'type':'integer','minimum':1}}},
            'source_pdf_sha256':{'const':SOURCE_SHA},'payload_file':file_schema,'payload_canonical_view_sha256':{'const':payload_view_sha},
            'available_added_physical_page_N':{'const':4},'availability_scope':{'type':'string'},
            'semantic_applicability_granted':{'const':False},'consumer_read_status':{'const':'not_recorded'},'consumer_use_status':{'const':'not_recorded'}}
new_ext_schema={'type':'object','additionalProperties':False,'required':[EXT_KEY],
                'properties':{**copy.deepcopy(old_extension_schema['properties']),EXT_KEY:{'type':'object','additionalProperties':False,'required':list(ext_fields),'properties':ext_fields}},
                'allOf':[{'if':{'required':['version']},'then':{'required':old_extension_schema['required']}}]}
packet_schema['properties']['source_bundle']['properties']['source_bundle_extension']={'oneOf':[old_extension_schema,new_ext_schema]}
packet_schema['x-v15-source-extension-change']='Only the nested same-PDF source extension is added; the base packet version and all other schema fields are preserved.'
schema_path=DEV/'packet.schema.v15.json';savejson(schema_path,packet_schema)
source_schema_path=SOURCE_BASE/'current-source-schema-v12.json';source_schema=parse(source_schema_path)
forbidden=set(source_schema['x-source-protocol']['recursive_forbidden_exact_keys'])
forbidden_check(payload,forbidden);forbidden_check(manifest['source_text_resource_metadata'],forbidden)

# Delivery metadata reflects the 13 actual historical assignment groups, with no execution scope.
batches=[]
packet_by_id={e['source_id']:e for e in packet_bindings}
for old_batch in native_metadata['batches']:
    batches.append({'batch_id':old_batch['batch_id'],'expected_N':old_batch['expected_N'],
                    'source_ids':copy.deepcopy(old_batch['source_ids']),
                    'original_assignment_metadata_only':{'path':old_batch['assignment_path'],'sha256':old_batch['assignment_sha256'],
                                                         'content_not_opened':True},
                    'packet_files':[packet_by_id[rid]['packet'] for rid in old_batch['source_ids']]})
changed77=[rid for rid in global_order if rid in changed_ids]
dev_manifest={'version':'shared-source-development77/v15','delivery_kind':'source-only-input-projection; not an inference scope',
              'record_N':77,'global_order':global_order,'global_order_UTF8_LF_sha256':H(order_lf),
              'global_order_canonical_json_sha256':H(canonical(global_order)),
              'order_metadata_source':binding(INPUT77/'batching-manifest.json'),
              'historical_13_batch_assignment_metadata_source':binding(NATIVE_META),
              'manual':manual,'source77_JSONL':binding(source77_path),'source_interface':binding(wrapper_path),
              'source_extension_manifest':manifest_binding,'v12_source_base':str(SOURCE_BASE),
              'packet_schema':binding(schema_path),'batches':batches,'batch_sizes':[b['expected_N'] for b in batches],
              'changed_same_source_record_ids_in_global_order':changed77,
              'source_input_bindings_for_both_machines':{'rule':binding(source77_path),'native':binding(source77_path)},
              'shared_bundle_hashes':shared,'packet_bindings':packet_bindings,
              'no_execution_prompt_or_run_scope_created':True,'consumer_read_status':'not_recorded','consumer_use_status':'not_recorded'}
dev_manifest_path=DEV/'delivery-manifest.json';savejson(dev_manifest_path,dev_manifest)

# Exact material whitelist: old 13 entries retained, plus only source/interface inputs.
new_binding_paths=[PDF,payload_path,wrapper_path,manifest_path,extract_path,frame_out,OUT/'frame-bundle-bindings-v15.jsonl',
                   OUT/'changed-source-record-ids-v15.json',source77_path,schema_path,dev_manifest_path,V14/'source_only_interface_v14.py',
                   V14/'seal.json',INPUT77/'batching-manifest.json',NATIVE_META,ADAPTER_DIR/'source_packet.py',ADAPTER_DIR/'source_receipts.py']
new_binding_paths.extend(Path(p['output_file']['path']) for p in extractions)
new_binding_paths.extend(Path(e['packet']['path']) for e in packet_bindings)
new_binding_paths.extend(Path(e['path']) for e in report_material_bindings)
material_bindings=copy.deepcopy(old_material_bindings);bound_paths={str(Path(e['path']).resolve()) for e in material_bindings}
for path in new_binding_paths:
    entry=binding(path)
    if entry['path'] not in bound_paths:material_bindings.append(entry);bound_paths.add(entry['path'])
for e in material_bindings:checked(e)
assert material_bindings[:13]==old_material_bindings
material_manifest={'version':'common-material-bindings/v15-source-only','v12_source_base':str(SOURCE_BASE),
                   'old_v18_13_material_bindings_preserved_exactly':True,'base_material_binding_N':13,
                   'material_binding_N':len(material_bindings),'material_bindings':material_bindings,
                   'source_packet_bindings_for_both_machines':{'rule':binding(source77_path),'native':binding(source77_path)},
                   'source_identity_whitelist_policy':'exact absolute resolved path, SHA256 and byte count; no source applicability or reading inferred',
                   'no_reference_label_input':True,'no_actual_run_scope_created':True}
material_manifest_path=OUT/'common-material-bindings-v15.json';savejson(material_manifest_path,material_manifest)

# Structural adapter and identity-receipt checks only. Never call dimensions/relations/driver.
import jsonschema
validator=jsonschema.Draft202012Validator(packet_schema);source_validator=jsonschema.Draft202012Validator(source_schema)
packet_adapter=imported('v15_source_packet_structure_only',ADAPTER_DIR/'source_packet.py')
receipt_adapter=imported('v15_source_receipts_identity_only',ADAPTER_DIR/'source_receipts.py')
resource_index=[];identity_results=[];adapter_results=[];unique_fullsources=set();identity_delta_N=0
for rid in global_order:
    packet=parse(DEV/'packets'/f'{rid}.compact.json');validator.validate(packet);source_validator.validate(packet['source_bundle']['source_record'])
    new=selected_new[rid];old=selected_old[rid]
    inventory=v15.source_inventory(new);adapter_inventory=packet_adapter.source_inventory(new)
    assert canonical(inventory)==canonical(adapter_inventory)
    old_inventory=v15._base.source_inventory(old);newmap={e['resource_id']:e for e in inventory}
    assert len(newmap)==len(inventory)
    assert all(canonical(newmap[e['resource_id']])==canonical(e) for e in old_inventory)
    resolved,deltas=receipt_adapter.resolve_inventory(new,inventory,material_bindings,SOURCE_BASE)
    identity_delta_N+=len(deltas)
    assert inventory==adapter_inventory
    assert all(e.get('consumer_read_status','not_recorded')=='not_recorded' and e.get('consumer_use_status','not_recorded')=='not_recorded' for e in inventory)
    for e in inventory:
        if e['resource_id'].startswith('FULLSOURCE-'):unique_fullsources.add(e['resource_id'])
    semantic=packet_adapter.semantic_unit(new)
    # This is an adapter transformation only: the original source_record stays exact.
    assert semantic['text']==old['source_record']['text'] and semantic['pages']==old['source_record']['pages']
    source_origins=[o for o in semantic['derived_context_origins'].values()
                    if o['source_sha256']==SOURCE_SHA and o['source_bundle_pointer'].startswith('/source_full_text_resources/')]
    if rid in changed77:
        expected_id='FULLSOURCE-'+payload_view_sha[:20]
        assert expected_id in newmap and newmap[expected_id]['source_sha256']==SOURCE_SHA
        assert newmap[expected_id]['available_views']=={'text':payload_view_sha}
        assert len(source_origins)==4
        assert {o['source_bundle_pointer'] for o in source_origins}=={f'/source_full_text_resources/{len(old["source_full_text_resources"])}/paragraphs/{i}' for i in range(4)}
        assert all(o['origin_inventory_resource_id']==expected_id and o['origin_inventory_view_sha256']==payload_view_sha for o in source_origins)
    else:assert not source_origins
    inventory_path=DEV/'inventories'/f'{rid}.inventory.json';savejson(inventory_path,inventory)
    resource_index.append({'record_id':rid,'source_bundle_sha256':H(canonical(new)),'inventory_file':binding(inventory_path),
                           'available_resource_N':len(inventory),'actual_read_status':'not_recorded','actual_use_status':'not_recorded'})
    identity_results.append({'record_id':rid,'FULLSOURCE_inventory_N':sum(e['resource_id'].startswith('FULLSOURCE-') for e in inventory),
                             'explicit_identity_deltas':deltas,'resolved_inventory_sha256':H(canonical(resolved)),
                             'original_producer_inventory_retained':True,'no_read_or_use_receipt_created':True})
    adapter_results.append({'record_id':rid,'source_record_schema_valid':True,'packet_schema_valid':True,
                            'generic_inventory_equals_wrapper_inventory':True,'old_inventory_entries_exact':True,
                            'added_same_PDF_paragraph_context_N':len(source_origins),'semantic_adapter_transform_only':True})
savejson(DEV/'source-resource-index.json',{'fixed_record_ids_in_input_order':global_order,'records':resource_index,
                                        'availability_only_no_consumer_read_or_use':True})
savejson(OUT/'source-receipt-identity-checks-v15.json',{'checks':identity_results,'existing_identity_delta_N':identity_delta_N,
                                                     'material_bindings':binding(material_manifest_path),'actual_read_or_use_event_N':0})
savejson(OUT/'source-adapter-contract-checks-v15.json',{'checks':adapter_results,'adapter_source_files':[binding(ADAPTER_DIR/'source_packet.py'),binding(ADAPTER_DIR/'source_receipts.py')],
                                                      'actual_coding_invocation_N':0,'packet_version_preserved':'native-full-source-3'})

# Limited live accessor role checks, in addition to full-frame mechanical projection.
role_checks=[]
for rid in (changed77[0], next(rid for rid in global_order if rid not in changed77)):
    for selector in ('rule','model','human'):
        actual=v15.lookup(rid,selector);assert actual==selected_new[rid]
        assert v15.source_inventory(actual)==packet_adapter.source_inventory(actual)
        role_checks.append({'record_id':rid,'selector':selector,'source_bundle_sha256':H(canonical(actual)),
                            'matches_mechanical_projection':True,'accessor_only_not_machine_execution':True})
    assert v15.lookup(rid,'model',bundle=False)==selected_old[rid]['source_record']
    unit=v15.lookup(rid,'unit');assert unit=={k:selected_old[rid]['source_record'][k] for k in ('id','text','pages','source_ref')}
# Reverify unchanged source PDF, old base seal/files and all material bindings.
assert H(PDF.read_bytes())==SOURCE_SHA
for e in material_bindings:checked(e)
for e in seal['members']:checked(e)
qa={'version':'source-only-QA/v15','frame_N':4481,'frame_order_UTF8_LF_sha256':H(('\n'.join(frame_order)+'\n').encode('utf-8')),
    'same_source_document_N':docmatch_N,'same_source_primary_N':primary_N,'same_source_context_N':contextmatch_N,
    'changed_bundle_N':len(changed_ids),'unchanged_bundle_N':4481-len(changed_ids),
    'old_current_body_context_pages_units_order_asset_fields_exact':True,'base_bundle_version_identity_exact':True,
    'only_changes':'same-PDF FULLSOURCE payload appended; matching source document source_text_resource added; nested v15 extension added',
    'new_FULLSOURCE_resource_id':'FULLSOURCE-'+payload_view_sha[:20],'source_document_resource_id':'SOURCE-'+SOURCE_SHA,
    'paragraph_N':4,'all_four_extractions_exact_including_formfeed':True,'source_pdf_bytes_unchanged':True,
    'development77_N':77,'development77_changed_N':len(changed77),'development77_changed_ids':changed77,
    'development77_order_preserved':True,'historical_native_batch_N':13,'historical_native_batch_sizes':[b['expected_N'] for b in batches],
    'same_new_bundle_hash_for_both_machine_inputs_N':77,'packet_other_field_byte_equivalence_checks_N':packet_unchanged_field_checks,
    'unique_existing_verified_asset_file_N':len(old_asset_files),'asset_fields_unchanged':True,
    'wrapper_base_v14_exact_binding':binding(V14/'source_only_interface_v14.py'),
    'source_adapter_schema_checks_N':77,'FULLSOURCE_identity_resolution_checks_N':77,
    'unique_FULLSOURCE_identity_N':len(unique_fullsources),'existing_identity_delta_N':identity_delta_N,
    'old_v18_13_material_entries_exact':True,'exact_binding_whitelist_paths_verified_N':len(material_bindings),
    'relative_source_payload_path':source_text_metadata,'limited_accessor_role_checks':role_checks,
    'actual_4481_or_77_coding_run_N':0,'actual_consumer_read_receipt_N':0,'actual_consumer_use_receipt_N':0,
    'scope_created_for_execution':False,'label_or_prediction_file_opened':False,
    'scope_note':'4481 traversal is mechanical source projection, not coding. Additional text availability does not establish actual machine reading or use.'}
qa_path=OUT/'source-only-QA-v15.json';savejson(qa_path,qa)
report_result={'status':'sealed source-only v15 extension and shared development77 inputs; no coding execution',
               'source_pdf_sha256':SOURCE_SHA,'physical_pages':list(PAGES),'payload_file':payload_binding,
               'payload_canonical_view_sha256':payload_view_sha,'source_interface':binding(wrapper_path),
               'source_extension_manifest':manifest_binding,'common_material_bindings':binding(material_manifest_path),
               'frame_binding_file':binding(OUT/'frame-bundle-bindings-v15.jsonl'),'frame_bundles':binding(frame_out),
               'development77_source':binding(source77_path),'development77_delivery_manifest':binding(dev_manifest_path),
               'qa':binding(qa_path),'frame_N':4481,'changed_N':224,'development77_N':77,'development77_changed_N':5,
               'new_source_shape':{'source_full_text_resources_suffix':['one FULLSOURCE-compatible payload with four paragraphs'],
                                   'paragraph_fields':list(paragraphs[0]),'source_locator_fields':list(paragraphs[0]['source_locator']),
                                   'source_document_addition':{'source_text_resource':source_text_metadata},
                                   'source_bundle_extension_addition_key':EXT_KEY},
               'new_source_files':[binding(PDF),payload_binding]+[e['output_file'] for e in extractions],
               'limitations':['source availability only; no actual machine read/use proven','all4481 traversal is mechanical projection only','old packet schema has v13-only extension; consume the new v15 schema for new nested extension'],
               'no_gold_or_machine_label_inputs':True,'no_actual_inference_scope_created':True}
savejson(OUT/'report.json',report_result)
readme=f"""# v15 同版 PDF 公共文本源接口\n\n本目录只做源材料封存与机械投影。原 PDF SHA 为 `{SOURCE_SHA}`；物理页 8、9、20、21 使用 `pdftotext -f/-l -layout` 重新抽取，全文 UTF-8 字节与既有四个补材块完全相同，包含页末 formfeed。未读问句、目标编码、开发标签、Gold 或机器预测；未运行 77、800 或 4481 编码。\n\n新增 `source_full_text_resources` 是一个可被旧通用 FULLSOURCE inventory 与 receipt adapter 消费的完整 payload，`paragraphs` 为四个整页全文。`source_sha256` 和 `source_pdf_sha256` 都绑定原 PDF；整页 UTF-8 SHA 单独存放在页 locator 中。没有使用 PDF 不适用的 `verbatim_UTF8_snapshot_text`。\n\n`source_documents` 仅新增该 PDF 的 `source_text_resource` 文件绑定。relative_path 以旧 scope 的 v12_source_base（{SOURCE_BASE}）解析，真实指向本目录 source-library 的封存 payload JSON。`common_source_bundle_version` 保留原 identity；已有 extension 原样保留并新增 `{EXT_KEY}`。仅新增 source availability，不授予语义适用性，也不建立实际阅读或使用记录。\n\n机械遍历原 4481 束，224 个同 PDF 束新增资源，其余 4257 束的 canonical bytes 不变。77 个固定输入仍使用既有全局顺序，5 束改变；13 个批次使用 native-v16 的实际历史 source-ID assignment 元数据。两个机器都指向同一裸 JSONL 和相同逐束 SHA，尚未实际消费。packet_version 与原包其他字段、资产绑定保持原值。\n\n入口：source_only_interface_v15.py；新增材料：source-library/nhsa-common-qa-physical-pages-8-9-20-21-v15.json；共同 whitelist：common-material-bindings-v15.json（完整保留旧 v18 的 13 项绑定）；77 bare inputs：development77/common-source-bundles-v15.jsonl；compact packets：development77/packets；新 packet schema：development77/packet.schema.v15.json；完整 mechanical projection：common-frame-bundles-v15.jsonl 与 frame-bundle-bindings-v15.jsonl。\n\n有限验证：77 packet/source schema、通用 adapter 结构转换、原 FULLSOURCE 精确身份解析、真实源基路径与 whitelist 文件 SHA/bytes、6 个 endpoint 只读 source accessor 调用。无 dimensions/relations/driver 编码调用。source-only-QA-v15.json、report.json 与 seal.json 给出真实绑定与限制。seal 排除自身。\n"""
save(OUT/'README.md',readme.encode('utf-8'))
report_md=f"""# v15 源材料机械投影报告\n\n封存完成：原 PDF 物理页 8/9/20/21 的完整抽取文本公共可见。四页逐字、逐 UTF-8 byte 与原补材块一致，包括 formfeed；原 PDF bytes 未变。\n\n源接口以 exact SHA/bytes 绑定原 v14 accessor，采用旧 FULLSOURCE payload + paragraphs 结构。新增 payload canonical SHA：`{payload_view_sha}`；inventory ID：`FULLSOURCE-{payload_view_sha[:20]}`。源文档 metadata 中 relative_path 以旧 v12_source_base 解析，且处于共同 exact material whitelist 中。\n\n4481 束机械投影：同源 224 束改变，4257 束不变；原 body/context/页码/单位/order/source assets 及 base bundle identity 精确保留。77 束维持固定顺序，其中 5 束新增公共资源；13 个历史 native assignment 组保持 source-ID 顺序。两个机器输入指向同一个新 source JSONL 与 77 个相同的 bundle SHA。\n\n新增材料可用不等于实际机器已读。4481 遍历是机械投影，不是编码。本交付没有执行任何真实 inference，没有产生 actual reading/use receipt，也未创建 actual run scope。\n\nsource-only-QA-v15.json 记录 77 个 packet/source schema、adapter 与 FULLSOURCE identity 检查；common-material-bindings-v15.json 保留旧 v18 原 13 material entries 并绑定新 PDF/payload/wrapper/77 source。development77/packet.schema.v15.json 只扩展 nested v15 source extension 的容许形状，旧 schema/source/packet 文件只读。\n"""
save(OUT/'report.md',report_md.encode('utf-8'))
members=[]
for path in sorted(OUT.rglob('*')):
    if path.is_file(): members.append({'relative_path':str(path.relative_to(OUT)),**binding(path)})
seal_result={'seal_type':'v15_same_PDF_physical_page_FULLSOURCE_mechanical_projection_and_shared77_input',
             'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
             'members':members,'member_N':len(members),'seal_excludes_itself':True,
             'source_input_bindings':{'base_v14_accessor':binding(V14/'source_only_interface_v14.py'),'base_v14_seal':binding(V14/'seal.json'),
                                      'base_v14_frame_bundle_bindings':binding(V14/'frame-bundle-bindings-v14.jsonl'),
                                      'base77_source':binding(INPUT77/'common-source-bundles-v14.jsonl'),
                                      'order_metadata':binding(INPUT77/'batching-manifest.json'),
                                      'native_manual_order_batch_assignment_metadata':binding(NATIVE_META),
                                      'v18_scope_source_binding_metadata':binding(V18_SCOPE),'original_pdf':binding(PDF)},
             'frame_N':4481,'same_source_changed_N':224,'shared77_N':77,'shared77_changed_N':5,
             'actual_coding_invocation_N':0,'actual_read_or_use_receipt_N':0,'old_files_modified':False}
savejson(OUT/'seal.json',seal_result)
for entry in members:checked(entry)
print(json.dumps({'status':'success','out':str(OUT),'seal':binding(OUT/'seal.json'),'report':binding(OUT/'report.json'),
                  'payload':payload_binding,'payload_canonical_view_sha256':payload_view_sha,'new_FULLSOURCE_id':'FULLSOURCE-'+payload_view_sha[:20],
                  'source77':binding(source77_path),'material_bindings':binding(material_manifest_path),
                  'frame_N':4481,'changed_N':224,'dev77_changed_N':5,'member_N':len(members)},ensure_ascii=False))
