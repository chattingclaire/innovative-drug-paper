"""Finite read-only artifact audit. Never imports or executes the rule runtime."""
from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import copy
import hashlib
import json
import re

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
BASE = ROOT / '06-coding/development-rule-sol/coverage36'
OUT = ROOT / '06-coding/root-machine-review/rule-v06-v07-source-quality-sol'
VERSIONS = ['implementation06-source-v12', 'implementation07-source-v12-receipts']
SCOPES = ['old41', 'old36', 'renewal2', 'supplement4']
DIMS = ['S', 'E', 'Ec', 'I', 'F']
SOURCE = ROOT / '01-review/context-projection-sol/full-frame-preflight'
checks, issues, observations, source_checks = [], [], [], []
digest_cache = {}

def cj(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def h(obj):
    return sha(cj(obj).encode())

def load(path):
    return json.loads(Path(path).read_bytes())

def rows(path):
    return [json.loads(line) for line in Path(path).read_bytes().splitlines() if line.strip()]

def actual(path):
    p = Path(path)
    if p not in digest_cache:
        data = p.read_bytes()
        digest_cache[p] = {'path': str(p), 'sha256': sha(data), 'bytes': len(data),
                           'mtime_utc': datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()}
    return digest_cache[p]

def expect(condition, kind, evidence):
    if not condition:
        issues.append({'kind': kind, 'evidence': evidence})
    return bool(condition)

def binding(entry, origin):
    try:
        a = actual(entry['path'])
        match = a['sha256'] == entry['sha256'] and ('bytes' not in entry or a['bytes'] == entry['bytes'])
        checks.append({'origin': origin, 'expected': entry, 'actual': a, 'match': match})
        expect(match, 'artifact_binding_mismatch', {'origin': origin, 'path': entry['path']})
        return match
    except OSError as exc:
        checks.append({'origin': origin, 'expected': entry, 'match': False, 'error': str(exc)})
        expect(False, 'artifact_missing', {'origin': origin, 'path': entry['path'], 'error': str(exc)})
        return False

def pointer(obj, path):
    for key in path.strip('/').split('/'):
        key = key.replace('~1', '/').replace('~0', '~')
        obj = obj[int(key)] if isinstance(obj, list) else obj[key]
    return obj

def selected_rows(path, strings, predicate):
    # Raw line selection precedes JSON decoding; no full 4481-frame decoding.
    needles = [x.encode() for x in strings]
    out = []
    for line in Path(path).read_bytes().splitlines():
        if not any(n in line for n in needles):
            continue
        obj = json.loads(line)
        if predicate(obj):
            out.append(obj)
    return out

def default_source_parts(ids):
    selected = selected_rows(SOURCE/'canonical_source_context-v12.jsonl', ids, lambda r: r['id'] in ids)
    expect(len(selected) == len(ids), 'finite_canonical_record_count', {'decoded': len(selected), 'expected': len(ids)})
    source_ids = {r['source_ref']['sha256'] for r in selected}
    source_ids |= {c['source_ref']['sha256'] for r in selected for c in r['contexts']}
    docs = selected_rows(SOURCE/'source-document-identities-v12.jsonl', source_ids,
                         lambda d: d['source_sha256'] in source_ids)
    hist = selected_rows(SOURCE.parent/'prospective-common-supplements-source-only-v3.jsonl', ids,
                         lambda z: z['record_id'] in ids)
    refs = {z['source_resource_id'] for r in selected for z in r.get('source_references', [])}
    hist_sha = {z['source_sha256'] for z in hist}
    library = selected_rows(SOURCE/'source-library/library-v12.jsonl', source_ids | refs | hist_sha,
        lambda d: d['source_resource_id'] in refs or d.get('source_sha256') in source_ids
                  or d.get('snapshot_sha256') in source_ids | hist_sha)
    asset_ids = {a['sha256'] for r in selected for a in r.get('source_attachments', [])}
    asset_ids |= {a['sha256'] for d in library for a in d.get('source_page_assets', [])}
    assets = selected_rows(SOURCE/'source-assets-manifest-v12.jsonl', asset_ids, lambda a: a['sha256'] in asset_ids)
    index = selected_rows(SOURCE/'source-library/reference-index-v12.jsonl', ids, lambda z: z['record_id'] in ids)
    texts = {d['source_sha256']: load(SOURCE/d['source_text_resource']['relative_path']) for d in docs if d.get('source_text_resource')}
    locators = load(SOURCE/'source-asset-locator-bases-v12.json')
    result = {}
    for r in selected:
        needed = {r['source_ref']['sha256']} | {c['source_ref']['sha256'] for c in r['contexts']}
        rd = [d for d in docs if d['source_sha256'] in needed]
        rh = [z for z in hist if z['record_id'] == r['id']]
        rr = {z['source_resource_id'] for z in r.get('source_references', [])}
        old = {z['source_sha256'] for z in rh}
        rl = [d for d in library if d['source_resource_id'] in rr or d.get('source_sha256') in needed
              or d.get('snapshot_sha256') in needed | old]
        ai = {a['sha256'] for a in r.get('source_attachments', [])}
        ai |= {a['sha256'] for d in rl for a in d.get('source_page_assets', [])}
        result[r['id']] = {
            'common_source_bundle_version': {'version':'v12',
                'canonical_sha256':'c417474ecbd801f1ea0f784f96dad23bf88b7ac00b12780e3ce67c3cbb8f2764',
                'material_manifest_sha256':'0fa14322edbd614496b014be77144701d052ebde6d41383b788b9e6712b63797',
                'actual_consumer_read_and_use_status':'not_recorded'},
            'source_record': r, 'source_documents': rd, 'explicit_or_primary_source_resources': rl,
            'preserved_historical_neutral_source_supplements': rh,
            'source_full_text_resources': [texts[d['source_sha256']] for d in rd if d.get('source_text_resource')],
            'source_asset_locations': [a for a in assets if a['sha256'] in ai],
            'source_locator_bases': locators,
            'source_reference_index': [z for z in index if z['record_id'] == r['id']],
            'source_provenance_addenda': [load(SOURCE/'renewal-official-provenance-addendum-v11.json')]
                if any(d.get('source_sha256') == 'd76f3d33e1ea70990992a99ae76371fcc1f99da93078e72b4376265679167a73' for d in rl) else []}
    return result

def raw_views(bundle):
    # Expected source/view identities come directly from unchanged source objects.
    r = bundle['source_record']; s = r['source_ref']['sha256']; out = {}
    def add(rid, doc, source_sha, views, location, source_pointer):
        item = {'resource_id':rid, 'source_document_id':doc, 'source_sha256':source_sha,
                'available_views':views, 'locator':location, 'raw_source_pointer':source_pointer}
        if rid in out:
            expect(out[rid]['source_sha256'] == source_sha and out[rid]['available_views'] == views,
                   'raw_duplicate_identity_conflict', {'id':r['id'],'resource_id':rid})
        else: out[rid] = item
    add('BODY-'+r['id'], 'SOURCE-'+s, s, {'text':sha(r['text'].encode())}, r['source_ref']['locator'], '/source_record/text')
    for i,c in enumerate(r['contexts']):
        views = {'geometry':h(c['structure'])}
        fields = {k:c[k] for k in ['text','title','caption','headers','row_cells'] if k in c}
        if fields: views['text']=h(fields)
        add(c['context_id'], c['source_ref']['source_resource_id'], c['source_ref']['sha256'], views,
            c['source_ref']['locator'], f'/source_record/contexts/{i}')
    for i,d in enumerate(bundle['explicit_or_primary_source_resources']):
        ds=d.get('source_sha256',d.get('snapshot_sha256'))
        add(d['source_resource_id'],d['source_resource_id'],ds,{'document_bundle':h(d)},
            {'document_resource_id':d['source_resource_id']},f'/explicit_or_primary_source_resources/{i}')
        for j,z in enumerate(d.get('source_visual_text_resources',[])):
            expect(sha(z['text'].encode()) == z['text_sha256'], 'visual_transcription_text_sha', {'id':r['id'],'resource_id':z['source_resource_id']})
            add(z['source_resource_id'],z['source_document_resource_id'],z['source_sha256'],{'text':z['text_sha256']},
                z['source_locator'],f'/explicit_or_primary_source_resources/{i}/source_visual_text_resources/{j}')
        for j,z in enumerate(d.get('source_display_regions',[])):
            add(z['region_id'],'SOURCE-'+z['source_sha256'],z['source_sha256'],{'geometry':h(z)},
                {k:z[k] for k in ['physical_page','coordinate_system','bbox_points_xyxy']},f'/explicit_or_primary_source_resources/{i}/source_display_regions/{j}')
    for i,z in enumerate(bundle['preserved_historical_neutral_source_supplements']):
        add('HISTORICALSOURCE-'+h(z)[:20],'SOURCE-'+z['source_sha256'],z['source_sha256'],{'text':h(z)},z.get('source_locator',{}),f'/preserved_historical_neutral_source_supplements/{i}')
    for i,z in enumerate(bundle['source_full_text_resources']):
        add('FULLSOURCE-'+h(z)[:20],z.get('source_resource_id'),z.get('source_sha256'),{'text':h(z)},
            {'representation':'source_full_text_resource_payload'},f'/source_full_text_resources/{i}')
    for i,a in enumerate(bundle['source_asset_locations']):
        source_sha=a.get('source_pdf_sha256',s)
        add(a['attachment_id'],'SOURCE-'+source_sha,source_sha,{'image':a['sha256']},
            {'absolute_path':a['absolute_path'],'physical_page':a.get('physical_page')},f'/source_asset_locations/{i}')
    return out

def source_audit(bundle, log, unit, version, scope):
    rid=bundle['source_record']['id']; where={'version':version,'scope':scope,'id':rid}
    raw=raw_views(bundle)
    before=len(issues)
    if log.get('source_reading_status') == 'technical_failure':
        return {'identity':where,'status':'preserved_recorded_technical_failure','actual_pixel_read_N':log['image_read_N']}
    l=log['uniform_source_reading_log']; pmap={x['resource_id']:x for x in log['inventory']}
    expect(set(pmap) == set(raw), 'producer_inventory_resource_set', where)
    for k,item in raw.items():
        if k not in pmap:continue
        for field in ['source_sha256','source_document_id','available_views']:
            expect(pmap[k].get(field)==item[field], 'producer_inventory_raw_identity', dict(where,resource_id=k,field=field))
        expect(pmap[k].get('consumer_read_status')=='not_recorded','producer_inventory_read_status',dict(where,resource_id=k))
    if version.startswith('implementation07'):
        expect(l['producer_source_inventory']==log['inventory'],'producer_inventory_preservation',where)
    resolved=copy.deepcopy(pmap)
    deltas=l.get('source_identity_resolution_delta',[])
    for d in deltas:
        resource=d['resource_id']; original=raw[resource]; payload=pointer(bundle,d['source_bundle_pointer'])
        original_sha=payload.get('source_sha256',payload.get('source_pdf_sha256'))
        expect(resource=='FULLSOURCE-'+h(payload)[:20] and d['payload_canonical_view_sha256']==h(payload),'fullsource_raw_view_identity',where)
        expect(original['source_sha256'] is None and d['producer_value'] is None and d['resolved_value']==original_sha,'fullsource_explicit_identity_delta',where)
        expect(payload['source_resource_id']=='SOURCE-'+original_sha and original['source_document_id']==payload['source_resource_id'],'fullsource_document_identity',where)
        docs=[z for z in bundle['source_documents'] if z['source_resource_id']==payload['source_resource_id'] and z['source_sha256']==original_sha]
        expect(len(docs)==1,'fullsource_unique_document_identity',where)
        if len(docs)==1:
            doc=docs[0]; meta=doc['source_text_resource']
            expect(d['source_snapshot_binding']['path']==doc['snapshot'] and d['source_snapshot_binding']['sha256']==original_sha,'fullsource_snapshot_proof',where)
            expect(d['source_payload_file_binding']['path']==str(SOURCE/meta['relative_path']) and d['source_payload_file_binding']['sha256']==meta['sha256'],'fullsource_payload_file_proof',where)
            expect(load(SOURCE/meta['relative_path'])==payload,'fullsource_original_payload_content',where)
            expect(d['raw_source_text_resource_metadata']==meta,'fullsource_raw_metadata_preserved',where)
        expect(d['read_use_status_changed'] is False and d['pixel_reading_claimed'] is False,'identity_delta_does_not_grant_read',where)
        resolved[resource]['source_sha256']=original_sha
    inv={x['resource_id']:x for x in l['source_inventory']}
    expect(inv==resolved,'resolved_inventory_only_explicit_delta',where)
    reads=l['read_receipts']; read_map={r['receipt_id']:r for r in reads}
    expect(len(read_map)==len(reads),'unique_read_receipt_id',where)
    events=l['actual_text_geometry_events']; evset={(x['resource_id'],x['view'],x['source_sha256'],x['view_sha256']) for x in events}
    for rr in reads:
        key=rr['resource_id']; exp=resolved.get(key)
        expect(exp is not None,'receipt_unknown_resource',dict(where,resource_id=key))
        if exp:
            expect(rr['source_sha256']==exp['source_sha256'] and rr['view_sha256']==exp['available_views'].get(rr['view']),
                'receipt_raw_source_view_binding',dict(where,resource_id=key,view=rr['view']))
        expect((key,rr['view'],rr['source_sha256'],rr['view_sha256']) in evset,'receipt_without_actual_program_event',dict(where,resource_id=key))
        expect(rr['view'] in ['text','geometry','document_bundle'] and rr['pixel_interpretation'] is False,'receipt_pixel_overclaim',where)
        expect(rr['record_id']==rid and rr['run_id']=='run-'+scope+'-01' and rr['read_attestation']=='recorded' and rr['delivery_status']=='complete','read_receipt_schema',where)
    for u in l['use_receipts']:
        rr=read_map.get(u['read_receipt_id'])
        expect(rr is not None and rr['resource_id']==u['resource_id'] and rr['view']==u['view'] and u['use_status']=='used','use_without_matching_read',where)
    expect(log['source_relation_traces']==l.get('source_relation_traces',log['source_relation_traces']), 'trace_log_consistency',where)
    expect(log['image_read_N']==0 and l['image_read_N']==0 and log['source_producer_pixel_read_not_inherited'] is True,'pixel_claim_or_producer_inheritance',where)
    if unit:
        semantic=unit['semantic_unit']; rb=copy.deepcopy(bundle); rb['source_record'].pop('id')
        for f in ['preserved_historical_neutral_source_supplements','source_reference_index']:
            for z in rb[f]:z.pop('record_id',None)
        expect(semantic['source_bundle']==rb,'semantic_bundle_original_minus_declared_admin_ids',where)
        expect(semantic['text']==bundle['source_record']['text'] and semantic['source_ref']==bundle['source_record']['source_ref'],'semantic_current_body_preserved',where)
        expect(semantic['contexts'][:len(bundle['source_record']['contexts'])]==bundle['source_record']['contexts'],'semantic_original_contexts_preserved',where)
        cmap={c['context_id']:c for c in semantic['contexts']}
        for cid,o in semantic['derived_context_origins'].items():
            src=pointer(bundle,o['source_bundle_pointer']); c=cmap[cid]
            expect(c['text']==src['text'] and c['source_ref']['sha256']==o['source_sha256'],'derived_context_exact_raw_origin',dict(where,context_id=cid))
            item=raw.get(o['origin_inventory_resource_id'])
            expect(item is not None and item['available_views'].get(o['origin_inventory_view'])==o['origin_inventory_view_sha256'],'derived_context_original_view_binding',dict(where,context_id=cid))
    return {'identity':where,'status':'passed' if len(issues)==before else 'mechanical_mismatch',
            'producer_resource_N':len(raw),'program_event_N':len(events),'read_receipt_N':len(reads),
            'use_receipt_N':len(l['use_receipts']),'explicit_identity_delta_N':len(deltas),
            'available_image_resource_N':sum('image' in x['available_views'] for x in raw.values()),
            'actual_pixel_read_N':0,'image_required_N':sum(x.get('required_view')=='image' for x in l['requirements'])}

def main():
    declared=load(BASE/VERSIONS[0]/'finite-execution-scope-before-source.json')
    ids=declared['scopes']['old41']+declared['scopes']['old36']
    defaults=default_source_parts(ids)
    snapshot=rows(BASE/VERSIONS[0]/'complete-source-bundles-v12.jsonl')
    expect([b['source_record']['id'] for b in snapshot]==ids,'finite_snapshot_order',{})
    expect(all(defaults[b['source_record']['id']]==b for b in snapshot),'finite_snapshot_default_v12_objects',{})
    summaries=[]
    for version in VERSIONS:
        vp=BASE/version; scope=load(vp/'source-scope-v12.json')
        expect(sha((cj(snapshot)+'\n').encode())==scope['complete_bundles_canonical_sha256'],'prepared_bundle_canonical_sha',{'version':version})
        totals=Counter(); uid=set(); timeline=[]; failures=[]
        for sn in SCOPES:
            rp=vp/('run-'+sn+'-01'); fr=load(rp/'freeze.json'); ex=load(rp/'execution.json'); seal=load(rp/'seal.json')
            for name,o in [('freeze',fr),('seal',seal)]:
                for field in ['implementation_files','material_bindings','control_inputs','output_files']:
                    for e in o.get(field,[]):binding(e,version+'/'+sn+'/'+name+'/'+field)
            for field in ['implementation_files','material_bindings','control_inputs']:
                expect(fr[field]==seal[field],'freeze_and_seal_binding_difference',{'version':version,'scope':sn,'field':field})
            times=[fr['created_at_utc'],ex['started_at_utc'],ex['finished_at_utc'],seal['sealed_at_utc']]
            order=all(datetime.fromisoformat(a)<=datetime.fromisoformat(b) for a,b in zip(times,times[1:]))
            expect(order,'freeze_execution_seal_time_order',{'version':version,'scope':sn,'timestamps':times})
            timeline.append({'scope':sn,'timestamps':dict(zip(['freeze','start','finish','seal'],times)),'declared_time_order':order})
            pred=rows(rp/'predictions.jsonl'); slots=rows(rp/'all-dimension-slots.jsonl'); delivered=rows(rp/'delivered-complete-source-bundles.jsonl')
            logs=rows(rp/'actual-source-consumption.jsonl'); units=rows(rp/'effective-semantic-units.jsonl')
            expected=declared['scopes'][sn]; pm={p['id']:p for p in pred}; um={u['id']:u for u in units}; lm={l['id']:l for l in logs}
            expect([p['id'] for p in pred]==expected and len(pm)==len(expected),'prediction_finite_ID_schema',{'version':version,'scope':sn})
            expect([b['source_record']['id'] for b in delivered]==expected,'delivered_ID_order',{'version':version,'scope':sn})
            expect(len(slots)==len(expected)*5,'dimension_slot_count',{'version':version,'scope':sn})
            expect(len(lm)==len(logs)==len(expected),'consumption_record_count',{'version':version,'scope':sn})
            expect([(x['id'],x['dimension']) for x in slots]==[(i,d) for i in expected for d in DIMS],'dimension_slot_identity_order',{'version':version,'scope':sn})
            for b in delivered:
                rid=b['source_record']['id']; expect(b==defaults[rid],'delivered_default_v12_object_difference',{'version':version,'scope':sn,'id':rid})
                source_checks.append(source_audit(b,lm[rid],um.get(rid),version,sn))
            failed=[p for p in pred if p['implementation_errors']]
            for p in pred:
                if p['implementation_errors']:
                    expect(p['labels'] is None and p['decisions'] is None,'failed_prediction_retained_as_coding_value',{'version':version,'scope':sn,'id':p['id']})
                    failures.append({'scope':sn,'id':p['id'],'implementation_errors':p['implementation_errors'],
                        'labels':p['labels'],'decisions':p['decisions'],'candidate_diagnostic_dimension_keys':list(p.get('candidate_decisions_diagnostic_only',{}))})
                else:
                    expect(isinstance(p['labels'],dict) and set(p['labels'])==set(DIMS) and set(p['decisions'])==set(DIMS), 'retained_prediction_five_dimension_schema',{'version':version,'scope':sn,'id':p['id']})
                    expect(all(p['labels'][d]==p['decisions'][d]['value'] for d in DIMS),'label_decision_value_difference',{'version':version,'scope':sn,'id':p['id']})
            for s in slots:
                p=pm[s['id']];where={'version':version,'scope':sn,'id':s['id'],'dimension':s['dimension']}
                if s['technical_failure']:
                    expect(s['status']=='technical_failure' and s['rule_value'] is None and s['rules_null'] is False and s['comparison_eligible'] is False,'technical_failure_miscounted_null_or_zero',where)
                    expect(s['retained_rule_decision']==p.get('candidate_decisions_diagnostic_only',{}).get(s['dimension']),'diagnostic_candidate_not_preserved',where)
                else:
                    expect(s['retained_rule_decision']==p['decisions'][s['dimension']] and s['rule_value']==p['labels'][s['dimension']],'retained_slot_decision_difference',where)
                expect(s['source_bundle_sha256']==h(defaults[s['id']]) and s['source_record']==defaults[s['id']]['source_record'],'slot_source_bundle_identity',where)
            dc=sum(len(p['labels']) for p in pred if isinstance(p['labels'],dict)); tf=sum(s['technical_failure'] for s in slots); rn=sum(s['rules_null'] for s in slots)
            expect(ex['output_record_n']==seal['prediction_n']==len(pred) and ex['decision_n']==seal['decision_n']==dc and ex['technical_failure_dimension_n']==seal['technical_failure_dimension_n']==tf and ex['rules_null_n']==seal['rules_null_n']==rn,'run_declared_actual_count_difference',{'version':version,'scope':sn})
            expect(seal['implementation_error_n']==len(ex['implementation_errors'])==len(failed),'run_error_declaration_difference',{'version':version,'scope':sn})
            expect(seal['prediction_sha256']==actual(rp/'predictions.jsonl')['sha256'],'prediction_top_seal_hash',{'version':version,'scope':sn})
            expect(ex['actual_image_pixel_read_N']==seal['actual_pixel_read_N']==0,'execution_pixel_claim',{'version':version,'scope':sn})
            expect(all(Path(p).name!='reference.jsonl' and '/04-calibration/' not in p for p in ex['read_paths']),'reference_or_calibration_audit_read_path',{'version':version,'scope':sn})
            totals.update(records=len(pred),slots=len(slots),valid_decisions=dc,technical_failure_slots=tf,rules_null=rn,record_errors=len(failed),semantic_units=len(units));uid.update(pm)
        summaries.append({'version':version,'counts':dict(totals),'unique_ID_N':len(uid),'timelines':timeline,'recorded_failures':failures})
        for fn in ['pre-run-tree-freeze.json','v06-final-delivery-bindings.json','v07-final-delivery-bindings.json']:
            f=vp/fn
            if f.exists():
                for e in load(f).get('files',[]):binding(e,version+'/'+fn)
    copied=[]
    for fn in ['source_packet.py','relations.py','evidence.py','dimensions.py']:
        left=actual(BASE/VERSIONS[0]/fn); right=actual(BASE/VERSIONS[1]/fn)
        same=left['sha256']==right['sha256'] and left['bytes']==right['bytes']; expect(same,'copied_semantic_module_difference',{'file':fn})
        copied.append({'file':fn,'v06':left,'v07':right,'byte_identical':same})
    result={'created_at_utc':datetime.now(timezone.utc).isoformat(),'status':'mechanical_review_pass' if not issues else 'mechanical_findings_present',
        'scope':{'versions':VERSIONS,'named_scopes':SCOPES,'no_runtime_import_or_execution':True,'no_reference_or_other_model_answers_decoded':True,'no_performance_computation':True},
        'versions':summaries,'binding_check_N':len(checks),'unique_artifact_hashed_N':len(digest_cache),
        'binding_mismatch_N':sum(not x['match'] for x in checks),'default_v12_source_objects_checked_N':len(defaults),
        'source_output_checks_N':len(source_checks),'copied_module_checks':copied,
        'issues':issues,'evidence_limits':['Timestamps and runtime event logs are local artifact attestations; no external timestamp or process trace certifies historical execution.',
          'Actual read receipts establish the declared program traversal/normalization of text, geometry and source identity; they do not certify human comprehension or semantic correctness.',
          'Original image bytes were integrity-hashed; no pixel image decoding or interpretation is evidenced by this runtime.',
          'Image requirements are conditional. All available image resources are not automatically required.',
          'The audit does not compute agreement, accuracy, generalization or independent human validation.']}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'mechanical-results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    (OUT/'binding-checks.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in checks)+'\n')
    (OUT/'source-object-and-receipt-checks.jsonl').write_text('\n'.join(json.dumps(x,ensure_ascii=False) for x in source_checks)+'\n')
    print(json.dumps({'status':result['status'],'versions':[{'version':x['version'],'counts':x['counts'],'unique_ID_N':x['unique_ID_N']} for x in summaries], 'binding_check_N':len(checks),'binding_mismatch_N':result['binding_mismatch_N'],'issue_N':len(issues),'issues':issues[:20]},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
