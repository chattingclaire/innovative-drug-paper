"""Finite v14 shared77 R inputs. No actor/model dispatch or judgment access."""
from pathlib import Path
import copy, datetime, hashlib, json, os, sys
sys.dont_write_bytecode = True
DEST = Path(__file__).resolve().parent
GOAL = DEST.parent.parent
CODING = DEST.parent
V3 = CODING / 'protocol-necessary-read-v3'
V4 = CODING / 'protocol-necessary-read-v4'
SOURCE = GOAL / '01-review/context-projection-sol/source-interface-v14-textleaf'
SOURCE77 = SOURCE / 'development77-common-v14'
PREP = CODING / 'native-llm77-v14-transport-preparation-sol'
HELPER = CODING / 'native-llm77-v13-sol/source-read-transport-fix-sol/source_view_chunk.py'
ATTEMPTS = CODING / 'native-llm77-v14-sol/attempts'
EXPECTED = {SOURCE / 'seal.json': '628bbec47f94546cf228ebd1f8fefbd8b8f1673164c0fef127f65abfe3f5f4aa',
            SOURCE77 / 'delivery-seal.json': 'cb7607d35a1ffa17c5dfdfda6e734144e45716021470b4279fcf180f68cf7458',
            PREP / 'seal.json': '43db6337b50af4a17fc56ef40246eee3ac08a1370ee754969738f6f15e359730',
            V4 / 'delivery-seal.json': 'f576ed1ad1116f70f20b13397f4010ebed7af24e479ccbf421290351e6b2788d',
            HELPER: '835e92166096faf12265800c4d981ce5f7c74c248d77770d66fb341fc460266b'}
def sha(b): return hashlib.sha256(b).hexdigest()
def canonical(x): return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')
def parse(p): return json.loads(Path(p).read_bytes())
def entry(p):
 p=Path(p);b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':sha(b)}
def save(p,b):
 p.parent.mkdir(parents=True,exist_ok=True)
 with p.open('xb') as f:f.write(b)
def savejson(p,x): save(p,canonical(x))
for p,h in EXPECTED.items(): assert sha(p.read_bytes())==h, str(p)
sealed_checked=[]
for p in [SOURCE/'seal.json',SOURCE77/'delivery-seal.json',PREP/'seal.json',V4/'delivery-seal.json']:
 s=parse(p)
 for e in s.get('members',s.get('files',[])):
  q=Path(e.get('absolute_path',e.get('path')));assert sha(q.read_bytes())==e['sha256'] and q.stat().st_size==e['bytes'];sealed_checked.append(entry(q))
sys.path.insert(0,str(V4))
import necessary_read_gate as gate
import native_records as records
pb=gate._pb
source_raw=(SOURCE77/'common-source-bundles.jsonl').read_bytes()
bundles=[json.loads(l) for l in source_raw.splitlines() if l]
ids=[b['source_record']['id'] for b in bundles]
assert len(ids)==len(set(ids))==77
assert ids==parse(SOURCE77/'source-resource-index.json')['fixed_record_ids_in_input_order']
assert sha(('\n'.join(ids)+'\n').encode())=='096de8c3d1f133e2604799dda43dcd4848f503393581d95112271b4e385f5ed2'
frame={z['id']:z for z in map(json.loads,(SOURCE/'frame-bundle-bindings-v14.jsonl').read_text().splitlines())}
old_batch_manifest=CODING/'development77-native-inputs-v3/batching-manifest.json'
old_batches=parse(old_batch_manifest)['batches']
assert [b['expected_n'] for b in old_batches]==[13,2,3,22,10,11,16]
assert sum([b['source_ids'] for b in old_batches],[])==ids
save(DEST/'common-source-bundles-v14.jsonl',source_raw)
packet_schema=parse(V3/'packet.schema.json')
assets_checked={};packet_entries={};compact_rows={};carrier_count=0;unique_carriers={};inventory_sizes=[];requirement_sizes=[]
for b in bundles:
 rid=b['source_record']['id'];raw=canonical(b);f=frame[rid]
 assert sha(raw)==f['new_v14_bundle_sha256'] and len(raw)==f['new_v14_bundle_utf8_bytes']
 old_packet=parse(CODING/'development77-native-inputs-v3/packets'/f'{rid}.compact.json')
 asset_files=copy.deepcopy(old_packet['verified_asset_files'])
 for a in asset_files:
  key=(a['sha256'],a['absolute_path'])
  if key not in assets_checked:
   p=Path(a['absolute_path']);v=p.read_bytes();assert sha(v)==a['sha256'] and len(v)==a['bytes']
   mime,w,h=pb.image_dimensions(v);assert (mime,w,h)==(a['mime_type'],a['width'],a['height']);assets_checked[key]=copy.deepcopy(a)
 packet={'packet_version':'native-full-source-3','source_id':rid,'output_id':'B-'+rid.split('-')[1],
         'source_bundle_sha256':sha(raw),'source_bundle':copy.deepcopy(b),'verified_asset_files':asset_files}
 pb.schema_check(packet,packet_schema);gate.packet_identity(packet)
 path=DEST/'packets'/f'{rid}.compact.json';savejson(path,packet)
 inventory=gate.owner_inventory(b);requirements=gate.base_requirements(packet,inventory)
 ip=DEST/'inventories'/f'{rid}.inventory.json';rp=DEST/'requirements'/f'{rid}.requirements.json'
 savejson(ip,inventory);savejson(rp,requirements);inventory_sizes.append(ip.stat().st_size);requirement_sizes.append(rp.stat().st_size)
 invmap={x['resource_id']:x for x in inventory}
 carriers=[]
 objects=[('BODY-'+rid,'text',b['source_record']['text'].encode('utf-8'),'/source_record/text')]
 for i,c in enumerate(b['source_record']['contexts']):
  pointer=f'/source_record/contexts/{i}'
  fields={k:c[k] for k in ['text','title','caption','headers','row_cells'] if k in c}
  objects.append((c['context_id'],'geometry',canonical(c['structure']),pointer+'/structure'))
  if fields:objects.append((c['context_id'],'text',canonical(fields),pointer))
 for resource,view,rawview,pointer in objects:
  assert sha(rawview)==invmap[resource]['available_views'][view]
  key=sha(rawview);vp=DEST/'view-carriers'/f'{key}.utf8'
  if key not in unique_carriers:save(vp,rawview);unique_carriers[key]=entry(vp)
  carrier_count+=1
  carriers.append({'resource_id':resource,'source_sha256':invmap[resource]['source_sha256'],'view':view,
                   'view_sha256':key,'scope_pointer':None,'original_bundle_pointer':pointer,
                   'original_fields':['text','title','caption','headers','row_cells'] if view=='text' and resource.startswith('CTX-') else None,
                   'exact_view_carrier':entry(vp),'helper_encoding':'file_utf8','locator':copy.deepcopy(invmap[resource]['locator']),
                   'carrier_is_original_view_bytes_not_new_source':True})
 leafviews=[]
 for i,z in enumerate(b['source_full_text_resources']):
  if z.get('kind')!='verbatim_UTF8_snapshot_text':continue
  pointer=f'/source_full_text_resources/{i}/text'
  view={'resource_id':z['source_resource_id'],'source_sha256':z['source_sha256'],'view':'text','view_sha256':z['text_utf8_sha256'],
        'scope_pointer':pointer,'locator':{'source_bundle_pointer':pointer},'encoding':'utf8_text'}
  gate.validate_added_view(b,view)
  leafviews.append({'additional_view':view,'packet_file_pointer':'/source_bundle'+pointer,'text_UTF8_bytes':z['text_utf8_bytes']})
 compactinventory=[{'resource_id':x['resource_id'],'source_sha256':x.get('source_sha256'),
                    'available_views':x['available_views'],'original_inventory_locator_pointer':f'/{i}/locator'} for i,x in enumerate(inventory)]
 compactrequirements=[{k:q[k] for k in ['requirement_id','resource_id','view','scope_pointer','source_relation_kind','dependency_dimensions']}|
                      {'source_basis_bundle_pointers':q['source_basis']['bundle_pointers']} for q in requirements]
 viewdata={'source_id':rid,'source_bundle_sha256':packet['source_bundle_sha256'],'full_original_inventory_file':entry(ip),
           'full_original_base_requirements_file':entry(rp),'compact_inventory':compactinventory,'compact_base_requirements':compactrequirements,
           'original_body_CTX_view_carriers':carriers,'new_original_text_leaf_additional_views':leafviews,
           'actual_delivery_read_use_status':'not_recorded','legacy_v4_inventory_unchanged':True}
 vp=DEST/'view-indexes'/f'{rid}.compact.json';savejson(vp,viewdata)
 packet_entries[rid]={'source_id':rid,'output_id':packet['output_id'],'source_bundle_sha256':packet['source_bundle_sha256'],**entry(path)}
 compact_rows[rid]={'source_id':rid,'output_id':packet['output_id'],'source_bundle_sha256':packet['source_bundle_sha256'],
                    'complete_packet_file':entry(path),'compact_view_index_file':entry(vp),'context_nodes':len(b['source_record']['contexts']),
                    'asset_files':asset_files,'v14_changed_from_v13':f['added_bundle_utf8_bytes']>0,
                    'original_body_and_CTX_preserved':True}
runtime_names=['manual-v1.3.txt','output-item.schema.json','necessary-source-scope.schema.json','source-quote.schema.json',
               'source-reading-protocol-v12.json','source-reading-protocol-v12.md','native-reader-instructions.txt']
binding={'version':'native-development77-v14-external-input-binding','source_material_version':'v14-textleaf',
         'source_owner_seal':entry(SOURCE/'seal.json'),'source77_seal':entry(SOURCE77/'delivery-seal.json'),
         'source77_actual_JSONL':entry(DEST/'common-source-bundles-v14.jsonl'),'v14_frame_bindings':entry(SOURCE/'frame-bundle-bindings-v14.jsonl'),
         'unchanged_v4_runtime_seal':entry(V4/'delivery-seal.json'),'unchanged_v4_native_binding':entry(V4/'native-binding.json'),
         'gate':entry(V4/'necessary_read_gate.py'),'native_records':entry(V4/'native_records.py'),
         'packet_builder_inherited':entry(V3/'packet_builder.py'),'bounded_helper':entry(HELPER),
         'transport_preparation_seal':entry(PREP/'seal.json'),'transport_overlay':entry(PREP/'transport-overlay.txt'),
         'required_read_files':{n:entry(V3/n) for n in runtime_names},'runtime_README':entry(V4/'README.md'),
         'original_batch_manifest':entry(old_batch_manifest),'attempt_root':str(ATTEMPTS),
         'new_material_validation':'actual v14 frame SHA+bytes; v3 validate_bundle/load_owner/frame check not invoked for v14',
         'old_v4_native_binding':'unchanged runtime provenance; not a current v14 packet or source binding',
         'source_inventory_rule':'original v4 inventory/base requirements unchanged; new literal leaves use seven-field additional_views with real ancestor ID/SHA',
         'actual_delivery_status':None,'actual_read_or_use_receipts_created':0,'actual_model_calls':0}
savejson(DEST/'runtime-source-binding.json',binding)
old_wrapper=(CODING/'native-llm77-v13-sol/preparation/actor-wrapper-v2.txt').read_text()
a=old_wrapper.index('启动后通过真实执行工具读取');z=old_wrapper.index('\n\n机械核对',a)
bootstrap=('短launcher已通过真实工具核CODEX_THREAD_ID为非空canonical UUID，并排他创建本轮attempt目录及bootstrap-identity.json。'
           '此处重新核环境UUID、已保存bootstrap同UUID/本次真实工具证据；仅允许继续刚创建的自己的目录，禁止复用旧attempt。'
           '再排他写identity.json，reader和scope_run_id用该runtime UUID；原生AI，外部creation-return匹配待ROOT核实，provider/wire/token未知留null。'
           'bootstrap缺失、目录来源不明、身份不符或写入失败时保留技术失败并停止，不重建或猜身份。')
wrapper=old_wrapper[:a]+bootstrap+old_wrapper[z:]
wrapper=wrapper.replace(str(CODING/'native-llm77-v13-sol/attempts'),str(ATTEMPTS))
wrapper += ('\n\n本轮外部冻结输入绑定以runtime-source-binding.json及本批source-index-compact.json为准。'
            'v4 native-binding.json中的旧v3输入seal/manifest仅是继承runtime出处，不能作v14来源验真；不得调用旧v3 make_packet/validate_bundle/load_owner来冒称本轮v14已过旧帧检查。'
            '实际完整packet schema与源全SHA沿本轮外部绑定核验，check_saved_scopes向原v4 native_records传本批新externally_frozen_packet_file_bindings。'
            '初始full指令、手册/schema/protocol及必需代码/材料均6000B有界读；程序可选introspection/debug若不涉及必要身份/来源，可记录optional-debug而不阻断，不得洗掉真实必要截断。\n')
save(DEST/'actor-runtime-instructions.txt',wrapper.encode('utf-8'))
overlay=(PREP/'transport-overlay.txt').read_text();overlay=overlay.replace('v14与新packet尚未实际冻结时，不猜其SHA/索引。','本轮v14与packet已经实际冻结；仅使用本批实际索引的SHA/指针。')
overlay=overlay.replace('ROOT在真实v14 inputs确定后选择需运行的新批次；本准备模型调用0，不默认全7/RWH','ROOT依据本次实际v14输入选择需运行的新批次；本准备模型调用0，不默认全7/RWH')
save(DEST/'transport-overlay-bound.txt',overlay.encode('utf-8'))
batch_entries=[]
for oldbatch in old_batches:
 bid=oldbatch['batch_id'];bids=oldbatch['source_ids'];bd=DEST/bid
 rows=[compact_rows[rid] for rid in bids];index=bd/'source-index-compact.json';savejson(index,rows)
 required=[binding['required_read_files'][n] for n in runtime_names if n!='native-reader-instructions.txt']
 required += [entry(DEST/'runtime-source-binding.json'),binding['runtime_README'],entry(index),entry(DEST/'actor-runtime-instructions.txt'),entry(DEST/'transport-overlay-bound.txt')]
 instruction=('判读要求\n'+(V3/'native-reader-instructions.txt').read_text()+'\n本轮真实冻结v14 R输入；只处理本批'+str(len(bids))+'条，完整顺序='+','.join(bids)+'。\n'
              '以下独立真实原文件是完整任务的必读内容，先按bytes/SHA核身份，使用已封存helper每工具6000B、至少12000tokens，连续读到EOF后才能逐条判读；不能把hash/解析当阅读：\n'
              +canonical(required).decode()+'\n完整手册必须是manual-v1.3.txt的逐字全内容；输出/必要范围/public quote schema完全原版，统一来源protocol完整原版。\n'
              +wrapper+'\n'+overlay+'\n本批packet与小索引的完整文件绑定见source-index-compact.json；inventory/requirements只读本条compact_view_index，不打印完整源、source_basis/canonical串。'
              '保存full inventory/requirements文件不等于阅读；当前/CTX的原精确view carrier沿本条索引按必需逐view完整读。必要公共/确指/几何/原图依据源结构选择，额外leaf按原7字段绑定。'
              'read/delivery日志仅由actor真实工具返回保存，emission不代complete；批内同一必要view实际完整读入可按原身份共享。\n'
              '本轮requested GPT-6.1 Sol ultra；实际telemetry未知留null，不声称人类/原图/全批首轮已完成。只判本批原来源，不读取旧输出或其他批次答案。\n')
 ip=bd/'instruction-R.txt';save(ip,instruction.encode('utf-8'));ie=entry(ip)
 launch=(PREP/'short-launcher.template.txt').read_text().replace('<ROOT_BIND_ABSOLUTE_INSTRUCTION_PATH>',ie['path']).replace('<ROOT_BIND_BYTES>',str(ie['bytes'])).replace('<ROOT_BIND_SHA256>',ie['sha256'])
 launch=launch.replace('用 --encoding file_utf8',('先真实工具读os.environ.get("CODEX_THREAD_ID")并核非空canonical UUID；排他创建 '+str(ATTEMPTS)+'/该UUID/（exist_ok=False），保存bootstrap-identity.json，未知tool event ID留null，不能复用旧目录。随后使用该目录下新唯一emission文件；完整instruction会核此bootstrap并补真实identity。\n用 --encoding file_utf8'))
 launch=launch.replace('placeholder未被ROOT替换并绑定时本模板不能派发。','本批路径/bytes/SHA已由同一实际文件冻结；是否派发由ROOT另定。')
 assert '<ROOT_BIND_' not in launch
 lp=bd/'short-launcher.txt';save(lp,launch.encode('utf-8'));assert lp.stat().st_size<=4000
 batch_entries.append({'batch_id':bid,'expected_n':len(bids),'source_ids':bids,'output_ids':[compact_rows[r]['output_id'] for r in bids],
                       'externally_frozen_packet_file_bindings':[packet_entries[r] for r in bids],
                       'source_index':entry(index),'complete_R_instruction':ie,'actual_short_initial_prompt':entry(lp),
                       'changed_v14_source_ids':[r for r in bids if compact_rows[r]['v14_changed_from_v13']],
                       'delivery_read_status':None,'model_calls':0})
manifest={'version':'development77-native-v14-frozen-R-inputs','global_order':ids,'global_order_sha256':sha(canonical(ids)),
          'global_order_UTF8_LF_sha256':sha(('\n'.join(ids)+'\n').encode()),'record_N':77,'batch_sizes':[13,2,3,22,10,11,16],
          'batches':batch_entries,'source_interface_version':'v14-textleaf','source77_JSONL':entry(DEST/'common-source-bundles-v14.jsonl'),
          'runtime_source_binding':entry(DEST/'runtime-source-binding.json'),'manual':binding['required_read_files']['manual-v1.3.txt'],
          'output_item_schema':binding['required_read_files']['output-item.schema.json'],'scope_schema':binding['required_read_files']['necessary-source-scope.schema.json'],
          'requested_model':{'model':'gpt-6.1-sol','thinking':'ultra'},'provider_telemetry':None,
          'only_R_inputs_frozen':True,'W_H_execution_plan_generated':False,'selected_batches_for_dispatch':None,'model_calls':0,
          'no_read_receipt_or_label_created':True,'old_attempts_unchanged':True}
savejson(DEST/'batching-manifest.json',manifest)
ledger=records.blank_ledger();ledger['inherited_development77_inputs_unchanged']=False
ledger['plan'].update({'conditions':['R1'],'ordered_batches':[b['batch_id'] for b in batch_entries],
                       'manual_sha256':binding['required_read_files']['manual-v1.3.txt']['sha256'],
                       'batching_manifest_sha256':sha((DEST/'batching-manifest.json').read_bytes()),'global_order_sha256':manifest['global_order_sha256'],
                       'necessary_scope_schema_sha256':binding['required_read_files']['necessary-source-scope.schema.json']['sha256'],
                       'uniform_reading_protocol_sha256':binding['required_read_files']['source-reading-protocol-v12.json']['sha256'],
                       'externally_frozen_packet_file_bindings':[packet_entries[r] for r in ids]})
ledger['v14_actual_input_binding_sha256']=sha((DEST/'runtime-source-binding.json').read_bytes());ledger['selected_batches_for_dispatch']=None
records.check_telemetry(ledger);savejson(DEST/'execution-ledger.blank.json',ledger)
# One finite mechanical QA on the generated77 and7 inputs; no old source profile/frame validation or suite.
for b in batch_entries:
 idx=parse(b['source_index']['path']);assert [x['source_id'] for x in idx]==b['source_ids']
 for f in b['externally_frozen_packet_file_bindings']:
  p=parse(f['path']);assert entry(f['path'])['sha256']==f['sha256'];pb.schema_check(p,packet_schema);gate.packet_identity(p)
  assert p['source_bundle_sha256']==frame[f['source_id']]['new_v14_bundle_sha256']
 for k in ['source_index','complete_R_instruction','actual_short_initial_prompt']:
  e=b[k];assert entry(e['path'])==e
 launch=Path(b['actual_short_initial_prompt']['path']).read_text();assert b['complete_R_instruction']['sha256'] in launch and str(b['complete_R_instruction']['bytes']) in launch
for p,h in EXPECTED.items():assert sha(p.read_bytes())==h
qa={'state':'actual_v14_native_R_inputs_frozen_not_dispatched','record_N':77,'batch_N':7,'same77_order_same7batch_sizes':True,
    'v14_fullSHA_bytes_actual_bindings_N':77,'packet_schema_and_source_identity_checks_N':77,'v3_v13_frame_validator_used':False,
    'old_v13_profile_rebuilt_or_used_to_certify_v14':False,'compact_indexes_have_no_source_text_or_source_basis_canonical_dumps':True,
    'original_full_inventory_requirements_preserved_N':77,'v4_inventory_remains_legacy_canonical_objects':True,
    'literal_new_leaf_additional_view_template_N':sum(len(parse(compact_rows[r]['compact_view_index_file']['path'])['new_original_text_leaf_additional_views']) for r in ids),
    'exact_base_view_carrier_bindings_N':carrier_count,'deduplicated_exact_view_carrier_file_N':len(unique_carriers),
    'carrier_hash_checks_match_original_inventory':True,'carrier_creation_is_not_actor_read':True,'unique_asset_path_SHA_checks_N':len(assets_checked),
    'short_initial_prompt_bytes':[b['actual_short_initial_prompt']['bytes'] for b in batch_entries],
    'complete_instruction_file_bytes':[b['complete_R_instruction']['bytes'] for b in batch_entries],
    'source_index_bytes':[b['source_index']['bytes'] for b in batch_entries],
    'changed_source_IDs_by_batch':{b['batch_id']:b['changed_v14_source_ids'] for b in batch_entries if b['changed_v14_source_ids']},
    'old_b4_b7_38_is_not_new77_first_run':True,'model_calls':0,'coding_chats_created':0,'actual_read_or_use_receipts_created':0,
    'delivery_status':None,'capacity_or_provider_token_guarantee':None,'W_H_plan_created':False,'necessary_source_reading_strict':True,
    'optional_code_introspection_is_nonblocking_only_if_not_necessary_source_or_binding':True}
savejson(DEST/'render-input-preflight.json',qa)
readme=('真实v14共同77按原顺序及7批13/2/3/22/10/11/16已冻结。仅R完整指令及≤4000B短启动；无W/H计划、模型调用或标签。'
        'manual1.3/输出schema/必要范围schema/v4 gate/native_records完全原版。新frame/packet来源验证使用v14真实SHA，不调用旧v3 v13-frame验证。\n\n'
        '各批instruction-R是完整任务，逐字完整手册/schema/protocol独立文件按真实bytes/SHA绑定，必须实际6000B连续读完；短launcher字节SHA与long instruction SHA分别记录。'
        '全文packet/原inventory/基础requirements完整保存，compact索引不重复灌正文/source_basis。基础view carriers字节精确等于原库存SHA，不是新来源，也不是阅读收据。'
        'v4库存仍按封存旧helper产生，新5字面叶另给真实SOURCE-TEXT祖先ID/SHA的7字段additional view，不混用合成FULLSOURCE/canonical对象SHA。\n\n'
        '本轮仅准备。真实emission、delivery、read、use由actor真实工具返回各自保存；当前delivery/telemetry未知，读账为空。'
        '源变化仅b1九条及b5的00138；旧b4/b7共38首件不等于新77首轮。ROOT另定需启动批次，旧终止attempt及首件不改。\n')
save(DEST/'README.md',readme.encode('utf-8'))
files=[entry(p) for p in sorted(DEST.rglob('*')) if p.is_file() and p.name!='delivery-seal.json']
seal={'seal_type':'actual-development77-native-v14-R-input-freeze','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
      'files':files,'member_count':len(files),'source_v14_seal':entry(SOURCE/'seal.json'),'source77_seal':entry(SOURCE77/'delivery-seal.json'),
      'unchanged_runtime_v4_seal':entry(V4/'delivery-seal.json'),'transport_preparation_seal':entry(PREP/'seal.json'),
      'records':77,'batches':7,'batch_sizes':[13,2,3,22,10,11,16],'actual_model_calls':0,'actual_read_receipts_created':0,
      'coding_chats_created':0,'delivery_status':None,'provider_telemetry':None,'W_H_plan_generated':False,'seal_excludes_itself':True}
savejson(DEST/'delivery-seal.json',seal)
print(json.dumps({'directory':str(DEST),'seal':entry(DEST/'delivery-seal.json'),'member_count':len(files),
                  'batching_manifest':entry(DEST/'batching-manifest.json'),'short_bytes':qa['short_initial_prompt_bytes'],
                  'instruction_bytes':qa['complete_instruction_file_bytes'],'source_index_bytes':qa['source_index_bytes'],
                  'carriers':len(unique_carriers),'assets':len(assets_checked),'model_calls':0},ensure_ascii=False))
