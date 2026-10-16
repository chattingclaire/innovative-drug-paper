"""Small exact-binding/wrapper/quote helpers; no source selection or labels."""
import hashlib, json
from pathlib import Path
BUNDLE_KEYS={'common_source_bundle_version','source_record','source_documents',
'explicit_or_primary_source_resources','preserved_historical_neutral_source_supplements',
'source_full_text_resources','source_asset_locations','source_locator_bases',
'source_reference_index','source_provenance_addenda'}
WRAPPER_KEYS={'packet_version','blind_id','source_bundle_canonical_sha256','source_bundle_canonical_UTF8_bytes','source_bundle'}
def require(ok,reason):
    if not ok:raise ValueError(reason)
def canonical(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode('utf8')
def digest(v):return hashlib.sha256(v).hexdigest()
def parse_json(raw):
    def pairs(entries):
        out={}
        for k,v in entries:
            require(k not in out,'duplicate JSON key: '+k);out[k]=v
        return out
    def bad(v):raise ValueError('nonfinite JSON: '+v)
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=bad)
def verify_binding(b):
    require(isinstance(b,dict),'missing actual binding')
    p=b.get('path',b.get('absolute_path'));require(isinstance(p,str) and Path(p).is_absolute(),'absolute bound path required')
    raw=Path(p).read_bytes();require(type(b.get('bytes')) is int and len(raw)==b['bytes'] and digest(raw)==b.get('sha256'),'file SHA/bytes differs: '+p)
    return raw
def unpack_packet(value):
    if isinstance(value,dict) and set(value)==WRAPPER_KEYS:
        require(value['packet_version']=='full800-v14-role-wrapper-preparation-1','unsupported wrapper version')
        bundle=value['source_bundle'];raw=canonical(bundle)
        require(type(value['source_bundle_canonical_UTF8_bytes']) is int and len(raw)==value['source_bundle_canonical_UTF8_bytes'],'bundle byte count differs')
        require(digest(raw)==value['source_bundle_canonical_sha256'],'bundle SHA differs')
        metadata={'delivery_kind':'full800_wrapper','blind_id':value['blind_id']}
    else:bundle=value;metadata={'delivery_kind':'complete_bare_bundle','blind_id':None}
    require(isinstance(bundle,dict) and set(bundle) in (BUNDLE_KEYS,BUNDLE_KEYS|{'source_bundle_extension'}),'complete ten-root bundle or extension required')
    require(isinstance(bundle.get('source_record'),dict) and isinstance(bundle['source_record'].get('id'),str),'source ID absent')
    metadata.update(source_id=bundle['source_record']['id'],source_bundle_sha256=digest(canonical(bundle)),source_bundle_utf8_bytes=len(canonical(bundle)))
    return bundle,metadata

def pointer_value(bundle,pointer):
    require(isinstance(pointer,str) and pointer.startswith('/'),'original JSON pointer required')
    value=bundle
    for p in pointer[1:].split('/'):
        p=p.replace('~1','/').replace('~0','~')
        if isinstance(value,list):
            require(p.isdigit() and (p=='0' or not p.startswith('0')) and int(p)<len(value),'pointer list index invalid');value=value[int(p)]
        elif isinstance(value,dict):require(p in value,'pointer field absent');value=value[p]
        else:raise ValueError('pointer descends through scalar')
    return value

def verify_source_quote(bundle,anchor):
    require(isinstance(anchor,dict) and set(anchor)=={'source_id','source_bundle_sha256','bundle_pointer','quote','span'},'source quote must have exactly five original fields')
    require(anchor['source_id']==bundle['source_record']['id'] and anchor['source_bundle_sha256']==digest(canonical(bundle)),'source quote original identity differs')
    leaf=pointer_value(bundle,anchor['bundle_pointer']);require(isinstance(leaf,str),'quote leaf is not original string')
    span=anchor['span'];require(isinstance(span,dict) and set(span)=={'start','end'} and all(type(span[k]) is int for k in span),'Unicode span requires integers')
    a,b=span['start'],span['end'];require(0<=a<b<=len(leaf),'Unicode span outside original leaf')
    require(isinstance(anchor['quote'],str) and leaf[a:b]==anchor['quote'],'continuous original Unicode quote differs')
    return leaf
