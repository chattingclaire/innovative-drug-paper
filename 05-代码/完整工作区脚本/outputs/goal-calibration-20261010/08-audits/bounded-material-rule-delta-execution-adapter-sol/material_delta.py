"""Bounded, source-only v15/v16 byte checks; never import a classifier or gate."""
import hashlib, json
from pathlib import Path

if not __debug__:
    raise RuntimeError('Binding assertions require Python without optimisation')

ALLOWED_CHANGED_IDS = ['RECODE25-01402']

def load(path): return json.loads(Path(path).read_bytes())
def bind(path):
    path=Path(path).resolve();raw=path.read_bytes()
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def exact(binding):
    actual=bind(binding['path'])
    assert actual=={k:binding[k] for k in ('path','bytes','sha256')},binding['path']
    return Path(binding['path']).read_bytes()
def flat(binding): return {k:binding[k] for k in ('path','bytes','sha256')}
def cli_bindings(args):
    return {name:bind(getattr(args,'material_'+argument)) for name,argument in
            [('seal','seal'),('correspondence','correspondence'),
             ('packet_bindings','packet_bindings'),('byteproof','byteproof')]}

def validate_material(bindings, original_scope, original_packet_plan):
    """Verify the single authorized material delta and both complete byte streams."""
    assert set(bindings)=={'seal','correspondence','packet_bindings','byteproof'}
    for b in bindings.values():exact(b)
    seal=load(bindings['seal']['path']);sealed={}
    for b in seal['files']:
        exact(b);sealed[str(Path(b['path']).resolve())]=flat(b)
    assert seal['state']=='prepared_not_adopted_not_executed'
    assert seal['new_production_GO'] is False and seal['model_calls']==seal['classifier_calls']==0
    for b in bindings.values():
        if b!=bindings['seal']:assert sealed[b['path']]==b
    assert set(seal['mandatory_members'])<=set(sealed)
    input_paths=[p for p in sealed if Path(p).name=='input-seal.json'];assert len(input_paths)==1
    input_seal=load(input_paths[0])
    for b in input_seal['files']:exact(b)
    assert input_seal['former_manual_prompt_protocol_unchanged'] is True
    assert input_seal['actual_calls']=={'classifier':0,'model':0}
    proof=load(bindings['byteproof']['path'])
    correspondence=load(bindings['correspondence']['path'])
    packets=load(bindings['packet_bindings']['path'])
    assert isinstance(packets,list) and len(packets)==4481
    assert correspondence['record_N']==4481
    assert correspondence['changed_source_ids']==ALLOWED_CHANGED_IDS
    assert correspondence['unchanged_common_line_N']==correspondence['reused_old_packet_binding_N']==4480
    assert correspondence['new_packet_physically_produced_N']==1
    assert proof['old_common']==original_scope['source_packet']
    old=exact(proof['old_common']);new=exact(proof['new_common'])
    assert sealed[proof['new_common']['path']]==proof['new_common']
    old_lines=old.splitlines(keepends=True);new_lines=new.splitlines(keepends=True)
    ids=original_scope['approved_record_ids']
    assert len(ids)==len(set(ids))==len(old_lines)==len(new_lines)==4481
    assert original_packet_plan['ordered_source_ids']==ids and original_packet_plan['packet_N']==4481
    rows=correspondence['records'];assert len(rows)==4481
    old_packets=original_packet_plan['packets']
    assert len(old_packets)==4481 and [p['source_id'] for p in packets]==ids
    changed=[];dual=[];old_pos=new_pos=0
    for ordinal,(rid,a,b,row,op,np) in enumerate(zip(ids,old_lines,new_lines,rows,old_packets,packets),1):
        assert json.loads(a)['source_record']['id']==json.loads(b)['source_record']['id']==rid
        assert row['source_id']==rid and row['frame_ordinal_1based']==ordinal
        declared_old=row['old_packet_binding']
        assert set(declared_old)==set(op)|{'frame_ordinal_1based','source_bundle_utf8_bytes'}
        assert {k:declared_old[k] for k in op}==op
        op=declared_old
        assert np==row['new_packet_binding']
        assert op['frame_ordinal_1based']==np['frame_ordinal_1based']==ordinal
        assert op['source_id']==np['source_id']==rid and op['output_id']==np['output_id']
        exact(op);exact(np)
        old_sha=hashlib.sha256(a).hexdigest();new_sha=hashlib.sha256(b).hexdigest()
        assert row['old_common_line_sha256']==old_sha and row['new_common_line_sha256']==new_sha
        material_changed=a!=b
        assert row['common_line_byte_same']==(not material_changed)
        assert row['packet_binding_same']==(op==np)
        assert row['new_packet_physically_produced']==material_changed
        if material_changed:
            changed.append(rid);assert op!=np and rid in ALLOWED_CHANGED_IDS
            assert flat(op)==proof['original_packet'] and flat(np)==proof['new_packet']
            oa=json.loads(a);nb=json.loads(b)
            assert oa['source_record']==nb['source_record']
            # Every context field, whatever its existing schema name, is
            # included in the exact unchanged-field comparison below.
            assert set(nb)-set(oa)<={'source_bundle_extension'}
            for key in oa:
                if key not in ('explicit_or_primary_source_resources','source_bundle_extension'):
                    assert oa[key]==nb[key],key
            resources=oa['explicit_or_primary_source_resources']
            assert nb['explicit_or_primary_source_resources'][:len(resources)]==resources
            assert len(nb['explicit_or_primary_source_resources'])==len(resources)+1
            old_extension=oa.get('source_bundle_extension',{})
            new_extension=nb.get('source_bundle_extension',{})
            assert set(new_extension)-set(old_extension)=={'v16_finite_article6_same_version'}
            assert all(new_extension[k]==v for k,v in old_extension.items())
            assert json.loads(exact(op))['source_bundle']==oa
            assert json.loads(exact(np))['source_bundle']==nb
        else:assert a==b and op==np
        dual.append({'id':rid,'original_ordinal_1based':ordinal,'material_changed':material_changed,
                     'v15':{'ordinal_1based':ordinal,'utf8_start':old_pos,'utf8_end':old_pos+len(a),
                            'line_bytes':len(a),'line_sha256':old_sha,'packet_binding':op},
                     'v16':{'ordinal_1based':ordinal,'utf8_start':new_pos,'utf8_end':new_pos+len(b),
                            'line_bytes':len(b),'line_sha256':new_sha,'packet_binding':np}})
        old_pos+=len(a);new_pos+=len(b)
    assert changed==ALLOWED_CHANGED_IDS
    ordinals=[r['original_ordinal_1based'] for r in dual if r['material_changed']]
    assert proof['old_new_common_line_changed_ordinal_1based']==ordinals==[1402]
    assert proof['other_4480_lines_including_terminators_byte_equal'] is True
    assert proof['other_4480_packet_bindings_exact_reused'] is True
    frames=[exact(proof[k]).splitlines(keepends=True) for k in ('old_frame_bindings','new_frame_bindings')]
    assert len(frames[0])==len(frames[1])==4481
    assert [i for i,(a,b) in enumerate(zip(*frames),1) if a!=b]==ordinals
    assert proof['old_new_frame_binding_changed_ordinal_1based']==ordinals
    assert proof['classifiers_executed']==proof['models_called']==0
    assert proof['source_snapshot_original_equal_bytes'] is True and proof['no_old_file_modified'] is True
    assert proof['current_source_record_contexts_unchanged'] is True
    return {'bindings':bindings,'old_source':proof['old_common'],'new_source':proof['new_common'],
            'old_lines':old_lines,'new_lines':new_lines,'packets':packets,'dual_rows':dual,
            'changed_record_ids':changed,'changed_ordinal_1based':ordinals,
            'unchanged_line_and_packet_N':4480,'classifier_executed':False}

def validate_union(selection, contract, material, ids):
    """Verify a frozen pure-code nomination union; do not evaluate any gate."""
    for obj in (selection,contract):
        assert obj['material_delta_bindings']==material['bindings']
        assert obj['material_changed_record_ids']==material['changed_record_ids']
        assert obj['selection_never_filters_old_zero_one_or_null'] is True
    gate_ids=selection['code_gate_record_ids'];assert len(gate_ids)==len(set(gate_ids))
    assert set(gate_ids)<=set(ids) and gate_ids==[r for r in ids if r in set(gate_ids)]
    assert contract['candidate_code_selector_binding']==selection['candidate_code_selector_binding']
    exact(contract['candidate_code_selector_binding'])
    assert contract['static_gate_binding']==selection['gate_source_binding']
    exact(contract['static_gate_binding'])
    assert contract['manual_static_audit']['pure_current_text_gate_and_material_union_verified'] is True
    expected=[r for r in ids if r in set(gate_ids)|set(material['changed_record_ids'])]
    actual=[r['id'] for r in selection['affected_records']]
    if selection['full_fallback_reasons']:assert actual==ids
    else:assert actual==expected
    assert actual and selection['selected_N']==len(actual)
    assert selection['reusable_N']==4481-len(actual)
    return actual

def subset_lineage(material, selected_ids):
    selected=set(selected_ids);raw=[];rows=[];cursor=0
    for full,row in zip(material['new_lines'],material['dual_rows']):
        if row['id'] not in selected:continue
        raw.append(full)
        rows.append(dict(row,subset_ordinal_1based=len(raw),subset_utf8_start=cursor,
                         subset_utf8_end=cursor+len(full),subset_line_sha256=row['v16']['line_sha256']))
        cursor+=len(full)
    assert [r['id'] for r in rows]==selected_ids
    return b''.join(raw),rows
