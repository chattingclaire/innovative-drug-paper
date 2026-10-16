#!/usr/bin/env python3
"""Finite explicit source/schema binding adapter. Binding is not dispatch or campaign approval."""
import argparse, copy, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
import necessary_read_gate as gate
pb = None
BINDING = None
_SOURCE_ROWS = None
_PROFILE_ROWS = None
_SOURCE_OFFSETS = None
_ORIGINAL_PROMPT = None
_ORIGINAL_GROUP = None
_ACTOR_ATTEMPT_ROOT = None

def configure(path, digest):
    global pb, BINDING, _SOURCE_ROWS, _PROFILE_ROWS, _SOURCE_OFFSETS, _ORIGINAL_PROMPT, _ORIGINAL_GROUP
    BINDING = gate.configure(path, digest)
    pb = gate._pb
    # Reuse the sealed freeze/budget primitives, including xb writes and full-order hashes.
    for name in ['require','sha','canonical','file_sha','parse','save_exclusive','within_budget','CONDITIONS']:
        globals()[name] = getattr(pb,name)
    if _ORIGINAL_PROMPT is None: _ORIGINAL_PROMPT = pb.prompt_bytes
    if _ORIGINAL_GROUP is None: _ORIGINAL_GROUP = pb.group_batches
    if 'source_interface_version' not in BINDING: return BINDING
    require(BINDING['source_interface_version'] == 'v14-textleaf', 'unsupported source interface')
    # Metadata only here; no common-source body decoding or source accessor lookup.
    index = parse(gate._checked('source_index').read_bytes())
    require(index['record_N'] == len(index['per_record']), 'source index count differs')
    _SOURCE_ROWS = {row['source_id']:row for row in index['per_record']}
    require(len(_SOURCE_ROWS) == index['record_N'], 'duplicate source ID')
    _PROFILE_ROWS = {}
    with gate._checked('source_profile').open('rb') as stream:
        for raw in stream:
            row = parse(raw); require(row['id'] not in _PROFILE_ROWS, 'duplicate profile ID')
            _PROFILE_ROWS[row['id']] = row
    offset = 0; _SOURCE_OFFSETS = {}
    for row in index['per_record']:
        sid = row['source_id']; profile = _PROFILE_ROWS.get(sid)
        require(profile and profile['new_v14_bundle_sha256'] == row['bundle_canonical_sha256'] and
                profile['new_v14_bundle_utf8_bytes'] == row['bundle_UTF8_bytes'], 'source index/profile differs: ' + sid)
        require(set(row['all_original_root_fields_preserved']) in [set(pb.BUNDLE_KEYS),set(pb.BUNDLE_KEYS)|{'source_bundle_extension'}], 'source roots not preserved')
        _SOURCE_OFFSETS[sid] = (offset,row['bundle_UTF8_bytes']); offset += row['bundle_UTF8_bytes'] + 1
    source = BINDING['common_source_file']
    require(index['common_source_file']['sha256'] == source['sha256'] and
            index['common_source_file']['bytes'] == source['bytes'] and
            Path(index['common_source_file']['absolute_path']).resolve() == Path(source['path']).resolve(),
            'actual shared source file binding differs')
    require(offset == source['bytes'], 'indexed complete JSONL lengths differ')
    # Binding controls do not read/decode unexposed source bodies. The producer seal
    # binds its full byte SHA; actual source bytes are verified before future build.
    require(Path(source['path']).stat().st_size == source['bytes'],'shared source file size differs')
    # Real v15 file is read and schema dialect checked, not merely named in metadata.
    schema_raw = gate._checked('output_item_schema').read_bytes()
    from jsonschema import Draft202012Validator
    Draft202012Validator.check_schema(parse(schema_raw))
    public = parse(gate._checked('public_source_quote_schema').read_bytes())
    output = parse(schema_raw)
    require(output['$defs']['common_public_source_quote'] == public, 'public quote definition differs from original verifier contract')
    pb.prompt_bytes = prompt_bytes
    return BINDING

def lookup(source_id):
    require(_SOURCE_ROWS is not None and source_id in _SOURCE_ROWS, 'source ID outside explicitly frozen index')
    offset,n = _SOURCE_OFFSETS[source_id]
    with Path(BINDING['common_source_file']['path']).open('rb') as stream:
        stream.seek(offset); raw = stream.read(n); separator = stream.read(1)
    row = _SOURCE_ROWS[source_id]
    require(len(raw) == n and separator == b'\n' and sha(raw) == row['bundle_canonical_sha256'], 'actual source slice SHA/length differs')
    bundle = parse(raw)
    require(canonical(bundle) == raw and bundle['source_record']['id'] == source_id, 'source slice not canonical/original ID')
    return bundle

def unwrap_human_packet(wrapper):
    require(set(wrapper) == {'packet_version','blind_id','source_bundle_canonical_sha256',
        'source_bundle_canonical_UTF8_bytes','source_bundle'}, 'human wrapper fields differ; no flattening')
    require(isinstance(wrapper['blind_id'],str) and wrapper['blind_id'], 'human blind ID absent')
    bundle = wrapper['source_bundle']; raw = canonical(bundle)
    require(sha(raw) == wrapper['source_bundle_canonical_sha256'] and
            len(raw) == wrapper['source_bundle_canonical_UTF8_bytes'], 'human wrapper complete bundle differs')
    # Human identity is separate provenance, never a model/source identifier.
    return bundle, {'human_blind_id':wrapper['blind_id'],'source_id':bundle['source_record']['id'],
                    'output_id':'B-'+bundle['source_record']['id'].split('-')[1]}

def make_packet(bundle):
    sid = bundle['source_record']['id']; require(sid in _SOURCE_ROWS, 'source ID outside frozen selection')
    row = _SOURCE_ROWS[sid]; raw = canonical(bundle)
    require(set(bundle) == set(row['all_original_root_fields_preserved']), 'full nested roots changed')
    require(sha(raw) == row['bundle_canonical_sha256'] and len(raw) == row['bundle_UTF8_bytes'], 'full frozen v14 bundle differs')
    require(sha(canonical(bundle['source_record'])) == row['source_record_canonical_sha256'] and
            sha(bundle['source_record']['text'].encode('utf8')) == row['body_UTF8_sha256'] and
            sha(canonical(bundle['source_record']['contexts'])) == row['CTX_object_canonical_sha256'] and
            len(bundle['source_record']['contexts']) == row['CTX_N'], 'current/CTX byte identity differs')
    pb.schema_check(bundle,parse(gate._checked('bundle_schema').read_bytes()))
    row_schema = parse(gate._checked('owner_schema').read_bytes())
    pb.schema_check(bundle['source_record'],row_schema)
    forbidden = row_schema.get('x-source-protocol',{}).get('recursive_forbidden_exact_keys')
    require(isinstance(forbidden,list) and forbidden,'owner forbidden-key protocol unavailable')
    banned = {k.casefold() for k in forbidden} | pb.EXTRA_FORBIDDEN
    for pointer,value in pb.walk(bundle):
        if isinstance(value,dict):
            require(all(k.casefold() not in banned and not k.casefold().startswith('machine_') for k in value), 'forbidden source result key: '+pointer)
    version=bundle['common_source_bundle_version']
    require(version.get('version')=='v12' and version.get('actual_consumer_read_and_use_status')=='not_recorded','fabricated consumer read status')
    pb.resource_integrity(bundle,BINDING['allowed_source_file_roots'])
    assets = pb.verified_assets(bundle,BINDING['allowed_source_file_roots'])
    packet = {'packet_version':'native-full-source-3','source_id':sid,'output_id':'B-'+sid.split('-')[1],
              'source_bundle_sha256':sha(raw),'source_bundle':copy.deepcopy(bundle),'verified_asset_files':assets}
    require(canonical(packet['source_bundle']) == raw,'bundle lost on wrapper construction')
    pb.schema_check(packet,parse(gate._checked('packet_schema').read_bytes()))
    return packet

def prompt_bytes(packets,manual,output_schema,variant='R',display_override=None):
    if 'source_interface_version' not in BINDING:
        return _ORIGINAL_PROMPT(packets,manual,output_schema,variant,display_override)
    require(variant in ['R','W','H'],'unsupported presentation')
    heading = '判读说明' if variant == 'H' else '判读要求'
    rules = gate._checked('reader_instructions').read_text(encoding='utf8')
    uniform = gate._checked('uniform_protocol_text').read_bytes()
    scope = gate._checked('necessary_scope_schema').read_bytes()
    shown = json.dumps(packets if display_override is None else display_override,ensure_ascii=False,sort_keys=True,
        indent=2 if variant == 'W' else None,separators=None if variant == 'W' else (',',':'),allow_nan=False)
    text = (heading+'\n'+rules+'\n完整共同手册（逐字，SHA256：'+sha(manual)+'）：\n'+manual.decode('utf8')+
        '\n统一来源读取协议（逐字，SHA256：'+sha(uniform)+'）：\n'+uniform.decode('utf8')+
        '\n必要范围与阅读收据技术schema（SHA256：'+sha(scope)+'）：\n'+scope.decode('utf8')+
        '\n每条输出技术schema：\n'+output_schema.decode('utf8')+
        '\n完整有序来源文件索引（完整文件交付/可访问/hash核对；必要视图须实际完整读）：\n'+shown+'\n')
    # Same transport repair; full instruction bytes and short wire bytes are distinct.
    overlay = gate._checked('transport_overlay').read_bytes()
    require(_ACTOR_ATTEMPT_ROOT is not None,'future build must explicitly bind actor attempt root')
    wrapper = gate._checked('actor_wrapper_template').read_text(encoding='utf8')
    params={'RUNTIME_DIR':str(Path(gate.__file__).resolve().parent),'RUNTIME_BINDING':str(gate.BINDING_PATH),
            'RUNTIME_BINDING_SHA':file_sha(gate.BINDING_PATH),'ACTOR_ATTEMPT_ROOT':str(_ACTOR_ATTEMPT_ROOT),
            'OUTPUT_SCHEMA_SHA':sha(output_schema),'ADAPTER_BINDINGS':json.dumps({k:BINDING[k] for k in ['adapter_gate','adapter_native_records']},ensure_ascii=False)}
    for key,value in params.items(): wrapper=wrapper.replace('{{'+key+'}}',value)
    require('{{' not in wrapper,'unfilled wrapper parameter')
    return text.encode('utf8')+wrapper.encode('utf8')+overlay

def batch_metrics(packets,manual,output_schema): return pb.batch_metrics(packets,manual,output_schema)
def group_batches(packets,budget,manual,output_schema):
    pb.check_budget(budget)
    ids = [p['source_id'] for p in packets]
    require(ids and len(ids) == len(set(ids)),'frozen global order missing/duplicated')
    for p in packets:
        require(pb.within_budget(batch_metrics([p],manual,output_schema),budget),'single full bundle exceeds operational budget')
    return [[p] for p in packets]

def freeze_inputs(packets, binding, budget, manual, output_schema, destination):
    for p in packets:
        require(sha(canonical(p['source_bundle'])) == p['source_bundle_sha256'], 'source bundle changed before freeze')
        require(p['source_bundle']['source_record']['id'] == p['source_id'] and p['output_id'] == 'B-' + p['source_id'].split('-')[1], 'source/output ID map changed')
        for asset in p['verified_asset_files']:
            require(file_sha(asset['absolute_path']) == asset['sha256'], 'asset bytes changed before freeze')
    groups = group_batches(packets, budget, manual, output_schema)
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)
    manifest = {'version': 'formal-frozen-native-interface-input-1', 'source_version': 'v12', 'source_interface_version': binding.get('source_interface_version','v13-source-addendum'),
                'necessary_read_protocol_version': 'native-necessary-read-v3',
                'reader_instructions_sha256': file_sha(gate._checked('reader_instructions')),
                'uniform_reading_protocol_sha256': file_sha(gate._checked('uniform_protocol')),
                'necessary_scope_schema_sha256': file_sha(gate._checked('necessary_scope_schema')),
                'parent_binding_sha256': file_sha(gate.BINDING_PATH),
                'owner_binding_sha256': sha(canonical(binding)), 'operational_budget_sha256': sha(canonical(budget)),
                'manual_sha256': sha(manual), 'output_item_schema_sha256': sha(output_schema),
                'global_order': [p['source_id'] for p in packets],
                'global_order_sha256': sha(canonical([p['source_id'] for p in packets])),
                'conditions': list(CONDITIONS), 'execution_organization': 'one_record_per_fresh_context_prospective', 'campaign_authorized': False, 'provider_api_call_count': None,
                'model_calls_made_by_builder': 0, 'batches': []}
    save_exclusive(destination / 'owner-binding.json', canonical(binding))
    save_exclusive(destination / 'operational-budget.json', canonical(budget))
    packet_directory = destination / 'packets'; packet_directory.mkdir()
    packet_files = {}
    for p in packets:
        packet_files[p['source_id']] = {
            'R': save_exclusive(packet_directory / (p['source_id'] + '.compact.json'), canonical(p)),
            'W': save_exclusive(packet_directory / (p['source_id'] + '.indented.json'), json.dumps(p, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode())}
    for number, group in enumerate(groups, 1):
        batch_id = f'batch-{number:04d}'; directory = destination / batch_id; directory.mkdir()
        indexes = {v: [{'source_id': p['source_id'], 'output_id': p['output_id'], 'source_bundle_sha256': p['source_bundle_sha256'],
                        'complete_packet_file': packet_files[p['source_id']][v],
                        'context_nodes': len(p['source_bundle']['source_record']['contexts']),
                        'asset_files': p['verified_asset_files']} for p in group] for v in ['R', 'W']}
        displays = {'R': save_exclusive(directory / 'source-index-compact.json', canonical(indexes['R'])),
                    'W': save_exclusive(directory / 'source-index-indented.json', json.dumps(indexes['W'], ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False).encode())}
        prompts = {v: save_exclusive(directory / ('prompt-' + v + '.txt'), prompt_bytes(group, manual, output_schema, v, indexes['W' if v == 'W' else 'R'])) for v in ['R', 'W', 'H']}
        metrics = batch_metrics(group, manual, output_schema)
        metrics['conservative_full_material_presentation_bytes'] = metrics.pop('worst_prompt_bytes')
        metrics['actual_initial_prompt_max_bytes'] = max(e['bytes'] for e in prompts.values())
        manifest['batches'].append({'batch_id': batch_id, 'expected_n': len(group),
                                    'source_ids': [p['source_id'] for p in group], 'output_ids': [p['output_id'] for p in group],
                                    'bundle_bindings': [{'source_id': p['source_id'], 'source_bundle_sha256': p['source_bundle_sha256']} for p in group],
                                    'metrics': metrics, 'display_files': displays, 'prompts': prompts,
                                    'condition_prompt_key': {'R1': 'R', 'R2': 'R', 'R3': 'R', 'W': 'W', 'H': 'H'}})
    for b in manifest['batches']:
        full = b['prompts']['R']
        launch = ('本轮授权任务要求在完整instruction文件。先核实际文件bytes/SHA，再用真实工具按连续UTF8字节边界逐块读取全部instruction；每次仅一块<=6000UTF8 B，单工具及functions.exec输出额度均>=12000tokens，首尾标记完整可见才另记delivery。截断停止并保留失败。hash/emission不等于阅读。\n'
            +'instruction='+full['path']+'\nbytes='+str(full['bytes'])+'\nSHA256='+full['sha256']+'\n'
            +'先全读手册/schema/protocol/index，再逐必要source current/CTX/public view真实读取；metadata只用于定位。代码/必要绑定说明同样有界读取。禁止读参照/性能/其他attempt输出或创建聊天。按原schema/gate保存逐条完整首判和实际read/use；必要缺失保留null/request，技术失败不能填0或拼接。未知遥测保留null。组件冻结不授权campaign或重置既有attempt额度。\n').encode('utf8')
        require(len(launch)<=4000,'short launcher exceeds 4000 UTF8 bytes')
        b['short_launcher_R'] = save_exclusive(destination / b['batch_id'] / 'short-launcher.txt',launch)
        b['actual_initial_prompt_sha256'] = b['short_launcher_R']['sha256']
        b['full_instruction_sha256'] = full['sha256']
    save_exclusive(destination / 'batching-manifest.json', canonical(manifest))
    return manifest

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command',choices=['bind','build'])
    for key in ['binding','binding-sha']: p.add_argument('--'+key,required=True)
    p.add_argument('--authorized-order'); p.add_argument('--order-file-sha'); p.add_argument('--out'); p.add_argument('--actor-attempt-root')
    args = p.parse_args()
    try:
        configure(args.binding,args.binding_sha)
        if args.command == 'bind':
            print(json.dumps({'binding_sha256':pb.file_sha(args.binding),'source_interface':BINDING.get('source_interface_version','legacy-v4'),
                'manual_file_sha256':BINDING['manual']['sha256'],'output_schema_file_sha256':BINDING.get('output_item_schema',{}).get('sha256'),
                'model_calls':0,'semantic_source_reads':0,'campaign_authorized':False},ensure_ascii=False));return 0
        require(args.authorized_order and args.order_file_sha and args.out and args.actor_attempt_root,'build requires explicit order SHA, new input directory and ROOT-approved attempt namespace')
        global _ACTOR_ATTEMPT_ROOT
        _ACTOR_ATTEMPT_ROOT=Path(args.actor_attempt_root)
        require(_ACTOR_ATTEMPT_ROOT.is_absolute(),'attempt namespace requires explicit absolute path')
        require(pb.file_sha(args.authorized_order)==args.order_file_sha,'authorized order file SHA differs')
        order = pb.parse(Path(args.authorized_order).read_bytes())
        require(set(order)=={'ordered_source_ids','source_selection_manifest'},'unsupported order contract')
        e=order['source_selection_manifest'];require(pb.file_sha(e['path'])==e['sha256'],'selection manifest SHA differs')
        ids=order['ordered_source_ids'];require(ids and len(ids)==len(set(ids)),'source order empty/duplicate')
        if 'source_interface_version' not in BINDING:
            parent=pb.parse(gate._checked('parent_binding').read_bytes());row_schema,load=pb.load_owner(parent)
            profile=pb.parse(Path(parent['field_profile']['path']).read_bytes())
            packets=[pb.make_packet(load(s),row_schema,profile,parent['allowed_source_file_roots']) for s in ids]
            output_schema=(pb.ROOT/'output-item.schema.json').read_bytes()
        else:
            require(pb.file_sha(BINDING['common_source_file']['path']) == BINDING['common_source_file']['sha256'], 'actual shared source file SHA differs before build')
            packets=[make_packet(lookup(s)) for s in ids]
            output_schema=gate._checked('output_item_schema').read_bytes()
        manual=gate._checked('manual').read_bytes();budget=pb.parse(gate._checked('operational_budget').read_bytes())
        result=freeze_inputs(packets,BINDING,budget,manual,output_schema,args.out)
        print(json.dumps({'records':len(ids),'batches':len(result['batches']),'model_calls':0,'campaign_authorized':False}));return 0
    except Exception as e:
        print(json.dumps({'technical_input_failure':str(e),'model_calls':0,'labels_generated':False},ensure_ascii=False));return 2
if __name__ == '__main__': raise SystemExit(main())
