"""Mechanical packet/version alignment; no labels, source prose or model calls."""
import hashlib, json
from pathlib import Path

if not __debug__:
    raise RuntimeError('Binding assertions require Python without optimisation')

def load(path): return json.loads(Path(path).read_bytes())
def binding(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def flat(spec): return {k:spec[k] for k in ('path','bytes','sha256')}
def exact(spec):
    actual=binding(spec['path']);assert actual==flat(spec),spec['path']
    return actual
def packet_match(native_packet, rule_packet):
    """Exact binding or independently hash-verified byte-identical packet."""
    a=exact(native_packet);b=exact(rule_packet)
    return a==b or (a['bytes'],a['sha256'])==(b['bytes'],b['sha256'])

def load_alignment(status, rule_ids, development_manifest, development_seal):
    specs=status['material_delta_bindings']
    assert set(specs)=={'seal','correspondence','packet_bindings','byteproof'}
    for spec in specs.values():exact(spec)
    total=load(specs['seal']['path']);members={}
    for spec in total['files']:
        members[str(Path(spec['path']).resolve())]=exact(spec)
    for key in ('correspondence','packet_bindings','byteproof'):
        assert members[specs[key]['path']]==flat(specs[key])
    correspondence=load(specs['correspondence']['path'])
    proof=load(specs['byteproof']['path']);packets=load(specs['packet_bindings']['path'])
    assert correspondence['record_N']==len(rule_ids)==len(packets)==4481
    rows=correspondence['records']
    assert [r['source_id'] for r in rows]==[p['source_id'] for p in packets]==list(rule_ids)
    assert len(set(rule_ids))==4481
    assert status['source_common_v15']==proof['old_common']
    assert status['source_common_v16']==proof['new_common']
    exact(proof['old_common']);exact(proof['new_common'])
    assert proof['current_source_record_contexts_unchanged'] is True
    assert proof['other_4480_lines_including_terminators_byte_equal'] is True
    assert proof['other_4480_packet_bindings_exact_reused'] is True
    changed=[];current={};prior={};by_id={}
    for ordinal,(row,packet) in enumerate(zip(rows,packets),1):
        sid=row['source_id'];assert row['frame_ordinal_1based']==ordinal
        assert row['new_packet_binding']==packet
        assert packet['frame_ordinal_1based']==ordinal and packet['source_id']==sid
        exact(row['old_packet_binding']);exact(packet)
        if row['common_line_byte_same']:
            assert row['old_common_line_sha256']==row['new_common_line_sha256']
        if row['packet_binding_same']:
            assert row['old_packet_binding']==row['new_packet_binding']
        if not row['common_line_byte_same'] or not row['packet_binding_same']:changed.append(sid)
        current[sid]=flat(packet);prior[sid]=flat(row['old_packet_binding']);by_id[sid]=row
    assert changed==correspondence['changed_source_ids']==status['material_changed_record_ids']
    assert correspondence['unchanged_common_line_N']==sum(r['common_line_byte_same'] for r in rows)
    assert correspondence['reused_old_packet_binding_N']==sum(r['packet_binding_same'] for r in rows)
    # The disclosed development material is independently version-bound, rather
    # than silently assumed to have received the new source extension.
    dev_binding=binding(development_manifest);dev=load(development_manifest)
    ds=load(development_seal)
    dev_members={str(Path(b['path']).resolve()):flat(b) for b in ds['members']}
    assert dev_members[dev_binding['path']]==dev_binding
    assert dev['version']=='shared-source-development77/v15'
    dev_ids=dev['global_order'];assert len(dev_ids)==len(set(dev_ids))==77
    assert [p['source_id'] for p in dev['packet_bindings']]==dev_ids
    ref_exclusions={};dev_packets={}
    for item in dev['packet_bindings']:
        sid=item['source_id'];exact(item['packet']);row=by_id[sid]
        assert item['source_bundle_sha256']==row['old_packet_binding']['source_bundle_sha256']
        dev_packets[sid]=item
        if item['source_bundle_sha256']!=row['new_packet_binding']['source_bundle_sha256']:
            ref_exclusions[sid]={'id':sid,'reason':'frozen_development_v15_material_not_updated_to_current_rule_material',
                'development_packet_binding':flat(item['packet']),
                'development_v15_canonical_bundle_sha256':item['source_bundle_sha256'],
                'old_population_packet_binding':prior[sid],'current_rule_packet_binding':current[sid]}
    provenance={'material_delta_bindings':specs,'material_changed_record_ids':changed,
        'full_current_packet_N':len(packets),'current_source_record_contexts_and_unit_order_unchanged':True,
        'development_material_manifest':dev_binding,'development_material_seal':binding(development_seal),
        'development_material_version':dev['version'],'development_ID_N':len(dev_ids),
        'development_material_mismatch_N':len(ref_exclusions),
        'development_material_mismatch':list(ref_exclusions.values()),
        'attention_v2_year_department_engine_unchanged_and_usable_on_same_unit_identities':True,
        'source_alignment_not_semantic_validation':True}
    return {'current_packets':current,'prior_packets':prior,'development_ids':dev_ids,
            'reference_exclusions':ref_exclusions,'provenance':provenance}

def align_native(native, current_packets):
    aligned={};excluded={}
    for sid,record in native.items():
        rule_packet=current_packets[sid]
        if packet_match(record['packet'],rule_packet):aligned[sid]=record
        else:excluded[sid]={'id':sid,'reason':'native_rule_packet_material_mismatch',
            'native_packet_binding':flat(record['packet']),'current_rule_packet_binding':rule_packet}
    return aligned,excluded

def directed_aligned(directed, ratio, dims, pred, reference, exclusions):
    """Keep the old directed calculator; isolate material exclusions explicitly."""
    comparable_ref={k:v for k,v in reference.items() if k[0] not in exclusions}
    result=directed(pred,comparable_ref)
    for dim,m in result.items():
        allocated=[(sid,v) for (sid,d),v in reference.items() if d==dim]
        mismatch=[dict(exclusions[sid],reference=v) for sid,v in allocated if sid in exclusions]
        m.update(source_aligned_allocated_N=m['allocated_N'],allocated_N=len(allocated),
            allocated_reference_positive_N=sum(v for _,v in allocated),
            allocated_reference_negative_N=sum(v==0 for _,v in allocated),
            material_mismatch_N=len(mismatch),material_mismatch=mismatch,
            material_mismatch_positive_N=sum(x['reference'] for x in mismatch),
            material_mismatch_negative_N=sum(x['reference']==0 for x in mismatch),
            source_aligned_binary_coverage=m['binary_coverage'],binary_coverage=ratio(m['N'],len(allocated)),
            excluded_positive_N=m['excluded_positive_N']+sum(x['reference'] for x in mismatch),
            excluded_negative_N=m['excluded_negative_N']+sum(x['reference']==0 for x in mismatch))
    return result
