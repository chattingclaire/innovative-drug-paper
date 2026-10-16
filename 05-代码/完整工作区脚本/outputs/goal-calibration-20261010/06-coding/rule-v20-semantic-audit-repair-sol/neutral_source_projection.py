"""Candidate common interface: missing literal ranges of bound UTF-8 originals.

This is preparation, not a dimension predicate. It never reads labels, audit
decisions, document titles as a selection rule, or a private answer file. Every
record with the same existing source-document binding gets the same rule.
The output is a NEW shared material candidate, never the frozen original input.
"""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path

VERSION = 'neutral-bound-UTF8-gap-projection-candidate-1'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def binding(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':sha(raw)}

def bound_original(document):
    """Read only the explicitly delivered source document's sealed TXT bytes."""
    path=Path(document.get('snapshot',''))
    if path.suffix.lower()!='.txt':
        return None
    raw=path.read_bytes();expected=document.get('source_sha256')
    if sha(raw)!=expected or len(raw)!=document.get('bytes'):
        raise ValueError('bound UTF8 original byte mismatch: '+str(path))
    text=raw.decode('utf-8',errors='strict')
    if text.encode('utf-8')!=raw:
        raise ValueError('UTF8 original not byte-roundtrippable')
    return text,binding(path)

def project(bundle):
    """Copy a complete bundle; append only verified missing continuous ranges."""
    out=copy.deepcopy(bundle);added=[];bindings=[]
    for document in bundle['source_documents']:
        original=bound_original(document)
        if original is None:
            continue
        text,origin=original;source_sha=document['source_sha256'];bindings.append(origin)
        intervals=[]
        for resource in bundle['source_full_text_resources']:
            if resource.get('kind')!='verbatim_UTF8_snapshot_text' or resource.get('source_sha256')!=source_sha:
                continue
            a,b=resource['locator']['unicode_code_point_interval_half_open']
            if not 0<=a<b<=len(text) or resource['text']!=text[a:b]:
                raise ValueError('old leaf does not equal bound original range')
            if sha(resource['text'].encode())!=resource['text_utf8_sha256']:
                raise ValueError('old literal leaf hash mismatch')
            intervals.append((a,b))
        intervals.sort()
        if any(a[1]>b[0]for a,b in zip(intervals,intervals[1:])):
            raise ValueError('old leaves overlap; no guessed repair')
        gaps=[];cursor=0
        for a,b in intervals:
            if cursor<a:gaps.append((cursor,a))
            cursor=b
        if cursor<len(text):gaps.append((cursor,len(text)))
        for a,b in gaps:
            part=text[a:b];byte_a=len(text[:a].encode());byte_b=len(text[:b].encode())
            locator={'snapshot_absolute_path':origin['path'],'snapshot_sha256':source_sha,
                     'original_archive_absolute_path':document.get('original_path'),
                     'unicode_code_point_interval_half_open':[a,b],
                     'utf8_byte_interval_half_open':[byte_a,byte_b],
                     'physical_line_range_1based_inclusive':[text[:a].count('\n')+1,text[:b].count('\n')+(0 if text[:b].endswith('\n') else 1)],
                     'physical_pages':None,'PDF_page_or_pixel_locator_available':False,
                     'coordinate_basis':'strict raw UTF8 original; line endings preserved; no normalization'}
            item={'kind':'verbatim_UTF8_snapshot_text','source_resource_id':f'SOURCE-TEXT-GAP-{source_sha}-C{a}-C{b}',
                  'source_sha256':source_sha,'source_version_id':document.get('source_version_id','SOURCEVERSION-'+source_sha),
                  'locator':locator,'text':part,'text_unicode_code_points':len(part),
                  'text_utf8_bytes':len(part.encode()),'text_utf8_sha256':sha(part.encode())}
            out['source_full_text_resources'].append(item)
            added.append({k:v for k,v in item.items()if k!='text'})
    if added:
        previous=copy.deepcopy(bundle['common_source_bundle_version'])
        out['common_source_bundle_version']={'version':VERSION,'status':'shared_material_interface_candidate_not_released',
                                           'parent_frozen_version':previous,'actual_consumer_read_and_use_status':'not_recorded'}
        out['source_bundle_extension']={'version':VERSION,'interface_change':'additional previously unconsumed original literal ranges',
            'selection_rule':'all bound TXT originals and all missing literal ranges; no ID/title/label filtering',
            'intended_consumers':'all rule/LLM/human coders equally after independent common release',
            'parent_bundle_canonical_sha256':sha(json.dumps(bundle,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),
            'original_bindings':bindings,'added_resource_bindings':added,
            'old_frozen_input_was_not_claimed_to_have_consumed_these_ranges':True}
    return out,{'version':VERSION,'original_bindings':bindings,'added_resources':added,
                'material_interface_changed':bool(added),'all_coders_same_visibility_required':True}

def prepare_catalog(packet_directory,output_directory):
    """Build a neutral global resource catalog, not rule-only augmented inputs."""
    source=Path(packet_directory);dest=Path(output_directory);dest.mkdir(exist_ok=False)
    originals={};routes=[];failures=[];input_files=[]
    for path in sorted(source.glob('*.json')):
        raw=path.read_bytes();value=json.loads(raw);bundle=value.get('source_bundle',value)
        input_files.append({'path':str(path.resolve()),'sha256':sha(raw),'bytes':len(raw)})
        try:
            _,receipt=project(bundle)
            for bound in receipt['original_bindings']:
                originals[bound['sha256']]=bound
            routes.append({'source_id':bundle['source_record']['id'],**receipt})
        except Exception as error:
            failures.append({'source_id':bundle['source_record']['id'],'error_type':type(error).__name__,'message':str(error)})
    def write(name,value):
        (dest/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    write('packet-input-bindings.json',input_files);write('record-material-routes.json',routes);write('projection-failures.json',failures)
    with (dest/'bound-original-resources.jsonl').open('x',encoding='utf8')as f:
        for key,bound in sorted(originals.items()):
            text=Path(bound['path']).read_bytes().decode('utf8')
            f.write(json.dumps({'source_sha256':key,'original_binding':bound,'text':text,
                'unicode_code_point_interval_half_open':[0,len(text)],'utf8_byte_interval_half_open':[0,bound['bytes']],
                'available_to':'all coders of a separately released common candidate'},ensure_ascii=False)+'\n')
    write('release-candidate-manifest.json',{'status':'candidate_only_independent_common_release_required',
        'version':VERSION,'builder_binding':binding(__file__),'records_scanned':len(input_files),
        'records_with_additional_original_ranges':sum(r['material_interface_changed']for r in routes),
        'bound_original_N':len(originals),'failure_N':len(failures),
        'record_IDs_used_only_as_routing_identity':True,'source_SHA_used_only_for_source_equality_and_provenance':True,
        'dimensions_or_expected_labels_in_projection':False,'old_frozen_files_modified':False,
        'inventory_bindings':[binding(dest/n)for n in ['packet-input-bindings.json','record-material-routes.json','projection-failures.json','bound-original-resources.jsonl']]})
    return dest/'release-candidate-manifest.json'

if __name__=='__main__':
    import sys
    print(prepare_catalog(sys.argv[1],sys.argv[2]))
