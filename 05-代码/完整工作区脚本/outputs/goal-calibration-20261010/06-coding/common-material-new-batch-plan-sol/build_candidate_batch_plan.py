"""Source/byte-only actual candidate batches. No dispatch, labels or sampling."""
import collections,hashlib,json
from datetime import datetime,timezone
from pathlib import Path

P=Path(__file__).resolve().parent
ROOT=P.parents[3]
G=ROOT/'outputs/goal-calibration-20261010'
C=G/'03-manual/common-material-projection-candidate-root'
A=G/'08-audits/common-material-candidate-reception-sol'
OLD=G/'06-coding/full4481-common-v15-production-preparation-sol'
MAX_RECORDS=12
PACKET_BYTE_LIMIT=260000
ROLES=['human_A','human_B','rule','LLM','adjudication_reference']

def strict(raw):
    def pairs(items):
        result={}
        for k,v in items:
            if k in result:raise ValueError('duplicate JSON key: '+k)
            result[k]=v
        return result
    return json.loads(raw.decode('utf8'),object_pairs_hook=pairs,parse_constant=lambda v:(_ for _ in ()).throw(ValueError(v)))
def canonical(value):return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf8')
def bind(path,raw=None):
    path=Path(path).resolve();raw=path.read_bytes() if raw is None else raw
    return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def checked(item):
    assert bind(item['path'])==item,item['path']
    return item
def load(path):return strict(Path(path).read_bytes())
def write(name,value):
    path=P/name;path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2).encode()+b'\n')
    return bind(path)
def distribution(values):return {'min':min(values),'max':max(values),'sum':sum(values)}

assert not (P/'batch-plan.json').exists(),'immutable new candidate already prepared'
assert bind(C/'packet-inventory.json')['sha256']=='621bf212ac4c13c2290a4d2117a3c2d432719cd7af6ede65bb13ee8ec6575ae1'
assert bind(A/'output-seal.json')['sha256']=='9e671f12dfb521136891e68a540d4c1f099cceb9a537c0d26bfbcd1c30aeb198'
audit=load(A/'output-seal.json')
for x in audit['output_members']:checked(x)
checked(audit['candidate_input_seal'])
candidate_seal=load(C/'output-seal.json')
for x in candidate_seal['output_members']:checked(x)
inventory=load(C/'packet-inventory.json');frame=load(OLD/'frame-order.json');historical=load(OLD/'batch-plan.json')
assert len(inventory)==4481 and historical['batch_N']==504
order=frame['source_ids'];assert len(order)==len(set(order))==4481
assert [x['source_id'] for x in inventory]==order
assert [sid for b in historical['batches'] for sid in b['source_ids']]==order
assert historical['max_records']==MAX_RECORDS and historical['packet_byte_limit']==PACKET_BYTE_LIMIT
roles=load(C/'equal-visibility-role-bindings.json');invbinding=bind(C/'packet-inventory.json')
assert roles['shared_packet_inventory']==invbinding
assert set(roles['role_inventory_bindings'])==set(ROLES)
assert all(v==invbinding for v in roles['role_inventory_bindings'].values())
assert roles['status']=='prepared_only_no_actual_role_delivery'
assert roles['human_independence_or_model_execution_claimed'] is False
originals=load(C/'original-delivery-map.json');assert len(originals)==17
original_checks=[]
for x in originals:
    a=checked(x['original_provenance_binding']);b=checked(x['candidate_copy'])
    assert a['sha256']==b['sha256'] and a['bytes']==b['bytes']
    assert Path(a['path']).read_bytes()==Path(b['path']).read_bytes()
    original_checks.append({'original':a,'candidate_copy':b,'exact_bytes_equal':True,'no_locator_rewrite':not x['locator_rewritten']})
core=[bind(C/n) for n in ['manual.txt','execution-prompt.txt','common-execution-protocol.txt']]
assert core[0]['sha256']=='5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
baseline=[bind(OLD/n) for n in ['batch-plan.json','packet-bindings.json','frame-order.json','prepare-full4481.py','input-bindings.json']]
old_records=[];candidate_records=[];payloads=[]
for i,item in enumerate(inventory,1):
    checked(item['parent_packet']);checked(item['packet_binding'])
    raw=Path(item['packet_binding']['path']).read_bytes();packet=strict(raw)
    assert packet['source_id']==item['source_id'] and packet['output_id']==item['output_id']
    assert packet['source_bundle']['source_record']['id']==item['source_id']
    assert hashlib.sha256(canonical(packet['source_bundle'])).hexdigest()==packet['source_bundle_sha256']==item['source_bundle_sha256']
    assert set(packet)=={'output_id','packet_version','source_bundle','source_bundle_sha256','source_id','verified_asset_files','common_material_candidate_provenance'}
    line=canonical(packet)+b'\n'
    assert len(line)<=PACKET_BYTE_LIMIT,item['source_id']
    record={'frame_ordinal_1based':i,'source_id':item['source_id'],'output_id':item['output_id'],'candidate_packet_binding':item['packet_binding'],'source_bundle_sha256':item['source_bundle_sha256'],'compact_whole_packet_line_bytes':len(line),'compact_whole_packet_line_sha256':hashlib.sha256(line).hexdigest(),'material_interface_changed':item['material_interface_changed'],'added_literal_resource_N':item['added_literal_resource_N']}
    candidate_records.append(record);payloads.append(line);old_records.append({'source_id':item['source_id'],'frame_ordinal_1based':i,'parent_packet_binding':item['parent_packet']})
    if i%1000==0:print('verified source-only packets',i,flush=True)
old_by_id={r['source_id']:r for r in old_records}
for b in historical['batches']:
    assert sum(old_by_id[sid]['parent_packet_binding']['bytes'] for sid in b['source_ids'])==b['packet_bytes']
input_bindings=write('input-bindings.json',{'state':'source_byte_only_candidate_plan_not_release','candidate_inventory':invbinding,'candidate_output_seal':bind(C/'output-seal.json'),'independent_audit_seal':bind(A/'output-seal.json'),'independent_budget_summary':bind(A/'compact-budget-summary.json'),'candidate_role_inventory_bindings':bind(C/'equal-visibility-role-bindings.json'),'original_delivery_map':bind(C/'original-delivery-map.json'),'frame_order':bind(OLD/'frame-order.json'),'historical504_plan':bind(OLD/'batch-plan.json'),'original_serializer':bind(OLD/'prepare-full4481.py'),'core_candidate_bindings':core,'whole_packet_meter':'canonical JSON ensure_ascii=False sort_keys=True separators=(comma,colon) + one LF, UTF8; retains full candidate preparation envelope','max_records':MAX_RECORDS,'packet_byte_limit':PACKET_BYTE_LIMIT,'model_runs':0,'sampling_created':False,'labels_or_main_LLM_files_read':False,'candidate_material_adopted':False})
write('historical504-preservation-bindings.json',{'old504_plan_and_preparation_files':baseline,'old4481_packet_bindings':old_records,'no_old_assignments_rewritten':True})
write('17-original-binding-checks.json',{'checks':original_checks,'actual_originals_N':17,'all_bound_original_bytes_equal':True})
write('pre-generation-seal.json',{'builder_binding':bind(Path(__file__)),'input_bindings':input_bindings,'original_preservation':bind(P/'historical504-preservation-bindings.json'),'candidate_packet_records':candidate_records,'no_mutation_or_execution_authorized':True})
# Contiguous greedy grouping uses source order, count and actual complete-line
# bytes only; no grouping by department, title, value, label or expected result.
groups=[];current=[];total=0
for record,line in zip(candidate_records,payloads):
    if current and (len(current)==MAX_RECORDS or total+len(line)>PACKET_BYTE_LIMIT):groups.append(current);current=[];total=0
    current.append((record,line));total+=len(line)
if current:groups.append(current)
plan=[]
for index,group in enumerate(groups,1):
    batch_id=f'candidate-batch-{index:04d}';folder=P/'batches'/batch_id;folder.mkdir(parents=True,exist_ok=False)
    full=b''.join(line for _,line in group)
    source_path=folder/'source-inputs.jsonl'
    with source_path.open('xb') as f:f.write(full)
    filebinding=bind(source_path)
    assert filebinding['bytes']==sum(r['compact_whole_packet_line_bytes'] for r,_ in group)<=PACKET_BYTE_LIMIT
    assert len(group)<=MAX_RECORDS
    rows=[];start=0
    for record,line in group:
        rows.append({**record,'batch_byte_interval_half_open':[start,start+len(line)]});start+=len(line)
    record={'batch_id':batch_id,'state':'candidate_plan_inputs_written_not_dispatched','record_N':len(rows),'source_ids':[r['source_id'] for r in rows],'output_ids':[r['output_id'] for r in rows],'frame_ordinals_1based':[r['frame_ordinal_1based'] for r in rows],'source_only_complete_inputs':filebinding,'actual_compact_whole_packet_bytes':len(full),'records':rows,'external_originals_global_binding':bind(P/'17-original-binding-checks.json'),'core_text_bytes_separate_from_packet_budget':sum(x['bytes'] for x in core),'packet_plus_common_core_bytes_for_information':len(full)+sum(x['bytes'] for x in core),'model_token_capacity_verified':False}
    write(f'batches/{batch_id}/bindings.json',record);plan.append(record)
    if index%150==0:print('written complete candidate input batches',index,flush=True)
flat=[sid for b in plan for sid in b['source_ids']];assert flat==order and len(flat)==len(set(flat))==4481
# Actual file readback, with each JSONL record reloaded and compared to its whole
# original candidate packet. No inference or substantive classification occurs.
readbacks=[]
for b in plan:
    checked(b['source_only_complete_inputs']);raw=Path(b['source_only_complete_inputs']['path']).read_bytes();lines=raw.splitlines(keepends=True);assert len(lines)==b['record_N']
    for line,r in zip(lines,b['records']):
        packet=strict(line);original=strict(Path(r['candidate_packet_binding']['path']).read_bytes());assert packet==original
        assert line==canonical(original)+b'\n';assert len(line)==r['compact_whole_packet_line_bytes'];assert hashlib.sha256(line).hexdigest()==r['compact_whole_packet_line_sha256']
    readbacks.append({'batch_id':b['batch_id'],'record_N':len(lines),'actual_file_bytes':len(raw),'within_12_and_260000':len(lines)<=MAX_RECORDS and len(raw)<=PACKET_BYTE_LIMIT,'full_packet_values_preserved':True,'binding':bind(Path(b['source_only_complete_inputs']['path']))})
for x in baseline:checked(x)
for item in inventory:checked(item['parent_packet']);checked(item['packet_binding'])
for x in original_checks:checked(x['original']);checked(x['candidate_copy'])
for x in core:checked(x)
write('historical504-preservation-readback.json',{'all_baseline_preparation_files_unchanged':True,'all_old4481_input_packet_bytes_unchanged':True,'historical_batch_N':504,'source_record_N':4481,'candidate4481_packet_files_unchanged':True,'original17_files_unchanged':True,'no_main_LLM_outputs_read':True})
write('batch-plan.json',{'state':'sealed_candidate_plan_pending_future_freezes_not_deployed','record_N':4481,'batch_N':len(plan),'max_records':MAX_RECORDS,'packet_byte_limit':PACKET_BYTE_LIMIT,'order_binding':bind(OLD/'frame-order.json'),'shared_candidate_inventory':invbinding,'source_only_complete_inputs_file_format':'JSONL; every line is the whole original candidate packet in the inherited compact serializer + LF','batching':'greedy contiguous original FRAME4481 order by count/complete compact packet bytes only','batches':plan,'historical504_unchanged':True,'deployment_or_dispatch_N':0})
write('actual-input-readback.json',{'record_N':len(flat),'unique_N':len(set(flat)),'each_source_once':collections.Counter(flat)==collections.Counter({s:1 for s in order}),'same_frozen_order':flat==order,'batch_N':len(plan),'all_within_budget':all(r['within_12_and_260000'] for r in readbacks),'readbacks':readbacks,'classification_or_sampling_run_N':0})
write('equal-role-planned-input-bindings.json',{'status':'plan_only_no_actual_role_delivery','candidate_inventory':invbinding,'same_prepared_inventory_for_five_roles':True,'role_bindings':{role:{'candidate_inventory':invbinding,'complete_batch_plan':bind(P/'batch-plan.json')} for role in ROLES},'same_full_source_packets_for_every_role':True,'human_or_model_independence_claimed':False,'release_adopted':False})
prior=load(A/'compact-budget-summary.json')['current_candidate_compact_full_preparation_envelope']
stats={'packet_bytes':distribution([r['compact_whole_packet_line_bytes'] for r in candidate_records]),'actual_batch_file_bytes':distribution([b['actual_compact_whole_packet_bytes'] for b in plan]),'batch_record_N_distribution':dict(sorted(collections.Counter(str(b['record_N']) for b in plan).items(),key=lambda x:int(x[0])))}
summary={'status':'actual_source_input_files_prepared_candidate_only_not_GO','at_utc':datetime.now(timezone.utc).isoformat(),'record_N':4481,'actual_batch_N':len(plan),'prior_reported_simulated_batch_N':prior['group_N_simulated'],'same_meter_actual_equals_prior659':len(plan)==prior['group_N_simulated']==659,'actual_packet_bytes_sum_equals_prior':stats['packet_bytes']==prior['packet_bytes'],'max_records':MAX_RECORDS,'packet_byte_limit':PACKET_BYTE_LIMIT,**stats,'complete_candidate_packet_envelope_kept':True,'material_changed_record_N':sum(r['material_interface_changed'] for r in candidate_records),'original_files_verified_N':17,'five_role_common_inventory_identical':True,'original504_inputs_retained_and_readback_verified':True,'actual_model_rule_or_human_coding_N':0,'sample_creation_N':0,'main_full_LLM_labels_read':False,'GO':False,'not_a_new_release':True,'required_before_any_GO':['ROOT must freeze a separate new common material release with five-role equal visibility and complete packet/original bindings','ROOT must freeze corresponding prompt/execution protocol and integrated algorithm version; copied old core bytes here are candidate inputs only','Historical primary LLM run must have ended before considering any new-release GO','ROOT must explicitly accept the candidate interfaces, resource/byte limitations, dependency and exposure bookkeeping'],'budget_limit':'260000 limits assigned whole compact packet bytes plus their LF, not provider tokens/context. Common core text and externally available originals/assets are bound separately. No runtime capacity or actual source reading by future coders is certified.'}
write('summary.json',summary)
lines=['# 共同材料候选的实际批次计划','',f'本候选实际写出 {len(plan)} 批 source-only 完整输入，原 4481 顺序各出现一次。沿用每批至多 12 条、完整压缩包合计 260000 UTF-8 字节预算；与此前仅模拟的 659 批一致。','',f"完整批次输入合计 {stats['actual_batch_file_bytes']['sum']:,} 字节；最大一批 {stats['actual_batch_file_bytes']['max']:,} 字节。17 份原件及五方共同 inventory 已绑定并核验，历史 504 批及其 4481 输入文件保持原字节。",'', '这只是新目录中的准备计划，没有部署、模型／规则判读、抽样或实际角色交付。材料候选原 envelope 与语境逐字段保留；未读取主全量 LLM 标签。每批 source-inputs.jsonl 是完整原候选包的压缩 JSON 行，bindings.json 给每条来源与字节区间／SHA。','', '考虑 GO 前，须由 ROOT 另行冻结共同材料、提示／执行协议及算法版本，并且历史主 LLM 已终结。现有 manual/prompt/protocol 的绑定仅是候选准备依据。260000 不是模型 token/context 容量保证；共同指令及外部原件／资产字节单独列明。','', '| 批次 | 条数 | 完整输入字节 | 原顺序区间 |','|---|---:|---:|---|']
lines.extend(f"| [{b['batch_id']}](batches/{b['batch_id']}/bindings.json) | {b['record_N']} | {b['actual_compact_whole_packet_bytes']} | {b['frame_ordinals_1based'][0]}–{b['frame_ordinals_1based'][-1]} |" for b in plan)
with (P/'manifest.md').open('x',encoding='utf8') as f:f.write('\n'.join(lines)+'\n')
members=[bind(x) for x in sorted(P.rglob('*')) if x.is_file() and x.name!='output-seal.json' and '__pycache__' not in x.parts]
seal=write('output-seal.json',{'status':'sealed_actual_batch_plan_candidate_only_not_release_or_deployment','at_utc':datetime.now(timezone.utc).isoformat(),'candidate_inventory':invbinding,'independent_reception_seal':bind(A/'output-seal.json'),'batch_N':len(plan),'record_N':4481,'output_members':members,'member_N':len(members),'self_excluded':True,'GO':False})
for x in members:checked(x)
print(json.dumps({'actual_batch_N':len(plan),'record_N':4481,'sum_input_bytes':stats['actual_batch_file_bytes']['sum'],'max_batch_bytes':stats['actual_batch_file_bytes']['max'],'seal':seal,'member_N':len(members),'GO':False},ensure_ascii=False,indent=2))
