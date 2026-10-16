"""Same-PDF page FULLSOURCE extension of exact sealed v14. No coding or read/use inference."""
from pathlib import Path
import argparse, copy, hashlib, importlib.util, json, sys
sys.dont_write_bytecode = True
OUT=Path(__file__).resolve().parent
MANIFEST_SHA='6691df51df2d7ea85047ce6fdc74a016b4b7f0644bc816e4370699422ed82ef9'
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
    """The original v14/base inventory handles FULLSOURCE; availability is no read/use event."""
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
