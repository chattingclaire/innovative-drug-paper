#!/usr/bin/env python3
"""Independent mechanical audit of a frozen neutral source candidate.

Only source packets, literal originals, projection code and candidate inventories
are read. No dimensions, prediction files or answers are loaded. Reconstructed
projected bundles stay in memory and are not supplied to a coding engine.
"""
import ast
import copy
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
OWNER = ROOT / '06-coding/rule-v20-semantic-audit-repair-sol'
CODE = OWNER / 'neutral_source_projection.py'
CAND = OWNER / 'neutral-material-projection-candidate'
MANIFEST = CAND / 'release-candidate-manifest.json'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def canon(x):
    return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()

def binding(path):
    p=Path(path);raw=p.read_bytes()
    return {'path':str(p.resolve()),'bytes':len(raw),'sha256':sha(raw)}

def write(name,x):
    with (OUT/name).open('x') as f:
        json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')

manifest=json.loads(MANIFEST.read_text())
assert binding(CODE)==manifest['builder_binding']
for b in manifest['inventory_bindings']:
    assert binding(b['path'])==b
packets=json.loads((CAND/'packet-input-bindings.json').read_text())
routes=json.loads((CAND/'record-material-routes.json').read_text())
assert not json.loads((CAND/'projection-failures.json').read_text())
assert len(packets)==len(routes)==4481
route_by_id={r['source_id']:r for r in routes}
assert len(route_by_id)==4481
packet_root=Path(packets[0]['path']).parent
assert {Path(x['path']).resolve() for x in packets}=={p.resolve() for p in packet_root.glob('*.json')}
ns={'__name__':'read_only_independent_audit','__file__':str(CODE)}
exec(compile(CODE.read_bytes(),str(CODE),'exec'),ns)

originals={}
catalog={}
for line in (CAND/'bound-original-resources.jsonl').read_text().splitlines():
    row=json.loads(line);b=row['original_binding'];raw=Path(b['path']).read_bytes()
    assert b==binding(b['path']) and sha(raw)==row['source_sha256']
    text=raw.decode('utf8',errors='strict');assert text.encode('utf8')==raw==row['text'].encode('utf8')
    assert row['unicode_code_point_interval_half_open']==[0,len(text)]
    assert row['utf8_byte_interval_half_open']==[0,len(raw)]
    assert row['source_sha256'] not in catalog
    catalog[row['source_sha256']]=row
assert len(catalog)==17

counts=Counter();checks=[];sample_packets={};paths=set();document_path_permissions=[]
expected_bundle_keys={'common_source_bundle_version','source_record','source_documents','explicit_or_primary_source_resources','preserved_historical_neutral_source_supplements','source_full_text_resources','source_asset_locations','source_locator_bases','source_reference_index','source_provenance_addenda'}
for pb in packets:
    path=Path(pb['path']);raw=path.read_bytes();assert len(raw)==pb['bytes'] and sha(raw)==pb['sha256']
    packet=json.loads(raw);bundle=packet.get('source_bundle',packet);sid=bundle['source_record']['id']
    assert sid in route_by_id and path.stem==sid and packet['source_id']==sid
    assert set(bundle) in (expected_bundle_keys,expected_bundle_keys|{'source_bundle_extension'})
    assert sha(canon(bundle))==packet['source_bundle_sha256']
    before=canon(bundle)
    projected,receipt=ns['project'](bundle)
    again,again_receipt=ns['project'](bundle)
    assert receipt==again_receipt and canon(projected)==canon(again) and before==canon(bundle)
    assert {'source_id':sid,**receipt}==route_by_id[sid]
    for key in expected_bundle_keys-{'common_source_bundle_version','source_full_text_resources'}:
        assert projected[key]==bundle[key]
    oldn=len(bundle['source_full_text_resources'])
    assert projected['source_full_text_resources'][:oldn]==bundle['source_full_text_resources']
    expected=[];eligible_docs=0
    for doc in bundle['source_documents']:
        snapshot=Path(doc['snapshot'])
        if snapshot.suffix.lower()!='.txt':continue
        eligible_docs+=1;bound=binding(snapshot);raw_original=snapshot.read_bytes()
        assert bound['sha256']==doc['source_sha256'] and bound['bytes']==doc['bytes']
        assert snapshot.is_absolute() and snapshot.resolve().is_relative_to((ROOT/'00-baseline/source-files').resolve())
        assert doc['source_resource_id']=='SOURCE-'+bound['sha256']
        text=raw_original.decode('utf8',errors='strict');assert text.encode()==raw_original
        catalog_row=catalog[bound['sha256']];assert text==catalog_row['text'] and bound==catalog_row['original_binding']
        paths.add(str(snapshot.resolve()));originals[bound['sha256']]=bound
        intervals=[]
        for resource in bundle['source_full_text_resources']:
            if resource.get('kind')!='verbatim_UTF8_snapshot_text' or resource.get('source_sha256')!=bound['sha256']:continue
            a,b=resource['locator']['unicode_code_point_interval_half_open']
            assert type(a) is type(b) is int and 0<=a<b<=len(text)
            assert resource['text']==text[a:b] and sha(text[a:b].encode())==resource['text_utf8_sha256']
            intervals.append((a,b))
        intervals.sort();assert all(a[1]<=b[0] for a,b in zip(intervals,intervals[1:]))
        # Reconstruct independently by the complement of already-delivered
        # literal intervals. No article, record, title or dimension is inspected.
        segments=[];cursor=0
        for a,b in intervals:
            if a>cursor:segments.append((cursor,a))
            cursor=b
        if cursor<len(text):segments.append((cursor,len(text)))
        additions=[z for z in projected['source_full_text_resources'][oldn:] if z['source_sha256']==bound['sha256']]
        assert len(additions)==len(segments)
        for item,(a,b) in zip(additions,segments):
            byte_a=len(text[:a].encode());byte_b=len(text[:b].encode());part=text[a:b]
            loc=item['locator']
            assert loc['unicode_code_point_interval_half_open']==[a,b]
            assert loc['utf8_byte_interval_half_open']==[byte_a,byte_b]
            assert raw_original[byte_a:byte_b]==part.encode()==item['text'].encode()
            # End is exclusive, so the final contained character determines
            # the last physical line. This formula is independent of producer.
            first=text.count('\n',0,a)+1;last=text.count('\n',0,b-1)+1
            assert loc['physical_line_range_1based_inclusive']==[first,last]
            assert loc['snapshot_absolute_path']==bound['path'] and loc['snapshot_sha256']==bound['sha256']
            assert loc['original_archive_absolute_path']==doc.get('original_path')
            assert loc['physical_pages'] is None and loc['PDF_page_or_pixel_locator_available'] is False
            assert item['text_unicode_code_points']==len(part) and item['text_utf8_bytes']==len(part.encode())
            assert item['text_utf8_sha256']==sha(part.encode())
            assert item['source_resource_id']==f"SOURCE-TEXT-GAP-{bound['sha256']}-C{a}-C{b}"
            expected.append((bound['sha256'],a,b))
        complete=sorted(intervals+segments)
        assert complete and complete[0][0]==0 and complete[-1][1]==len(text)
        assert all(a[1]==b[0] for a,b in zip(complete,complete[1:]))
    actual=[(r['source_sha256'],*r['locator']['unicode_code_point_interval_half_open']) for r in receipt['added_resources']]
    assert actual==expected
    counts['records']+=1;counts['records_added']+=bool(expected);counts['resources_added']+=len(expected)
    counts['records_bound_TXT']+=bool(eligible_docs);counts['records_no_TXT']+=not bool(eligible_docs)
    counts['bound_TXT_already_complete']+=bool(eligible_docs) and not bool(expected)
    counts['existing_source_bundle_extension']+='source_bundle_extension' in bundle
    counts['existing_extension_and_new_ranges']+=('source_bundle_extension' in bundle) and bool(expected)
    if 'source_bundle_extension' in bundle and not expected:
        assert projected['source_bundle_extension']==bundle['source_bundle_extension']
    if not expected:assert projected==bundle
    else:
        assert projected['common_source_bundle_version']['status']=='shared_material_interface_candidate_not_released'
        assert projected['common_source_bundle_version']['actual_consumer_read_and_use_status']=='not_recorded'
        assert projected['common_source_bundle_version']['parent_frozen_version']==bundle['common_source_bundle_version']
        assert projected['source_bundle_extension']['parent_bundle_canonical_sha256']==sha(before)
    checks.append({'source_id':sid,'packet_sha256':pb['sha256'],'eligible_TXT_documents':eligible_docs,'added_range_count':len(expected),'added_ranges':actual,'input_canonical_unchanged':True,'two_actual_runs_deterministic':True,'receipt_matches_candidate_route':True,'new_leaf_char_byte_line_SHA_checks':True,'source_permission':'only_preexisting_source_documents_snapshot_bindings_within_frozen_baseline; availability_not_applicability'})
    if sid in {'RECODE25-04592','RECODE25-04587','RECODE25-04599','RECODE25-00044','RECODE25-03478'}:
        sample_packets[sid]={'bundle':bundle,'projected':projected,'receipt':receipt,'path':str(path)}

assert counts['records_added']==1227 and len(originals)==17 and set(originals)==set(catalog)
tree=ast.parse(CODE.read_text());literal_strings=[n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)]
assert not any(re.search(r'RECODE\d+-\d+|A-\d{6}|第[零一二三四五六七八九十百]+条',s) for s in literal_strings)
assert not any(n.func.attr in {'predict','analyze','send','write_stdin'} for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute))
summary={'status':'mechanical_global_checks_passed_candidate_not_released','counts':dict(counts),'bound_original_N':len(originals),'original_paths_N':len(paths),'packet_inventory_exact4481':True,'actual_source_original_SHA_checks':17,'all_char_byte_line_ranges_checked':True,'deterministic_actual_projection_runs':4481*2,'all_routes_match_independent_complement':True,'source_only_bundle_schema_for_all4481':True,'neutral_code_has_no_fixed_record_blind_or_article_identifiers':True,'same_candidate_possible_for_all_coders':'One role-neutral project(bundle) result and sealed global source/route catalog; actual equal release/delivery remains future work.','semantically_read_all17_originals':False,'classification_or_prediction_engine_invoked':False,'old_files_written':False,'limitations':['The candidate catalog is not a final common release or evidence of actual delivery/use.','Source-document permission establishes availability only; downstream applicability requires a current finite relation.','Absolute original snapshot paths need a common portable delivery mapping; preserve source/range SHA identity.']}
write('all4481-mechanical-checks.json',checks)
write('mechanical-summary.json',summary)
write('original17-bindings.json',[originals[k] for k in sorted(originals)])
write('audited-input-bindings.json',{'files':[binding(CODE),binding(MANIFEST),*[binding(x['path']) for x in manifest['inventory_bindings']]],'packet_bindings_file':str(CAND/'packet-input-bindings.json'),'4481_bound_packets_checked':True,'17_originals_binding_file':str(OUT/'original17-bindings.json'),'source_indexes_not_interpreted_as_semantic_reading':True})
write('finite-case-projection-shapes.json',{k:{'packet_path':v['path'],'current_text':v['bundle']['source_record']['text'],'primary_source_ref':v['bundle']['source_record']['source_ref'],'old_leaf_N':len(v['bundle']['source_full_text_resources']),'new_leaf_N':len(v['projected']['source_full_text_resources']),'receipt':v['receipt'],'raw_source_record_unchanged':v['bundle']['source_record']==v['projected']['source_record'],'whole_bundle_unchanged':v['bundle']==v['projected']} for k,v in sample_packets.items()})
print(json.dumps(summary,ensure_ascii=False,indent=2))
