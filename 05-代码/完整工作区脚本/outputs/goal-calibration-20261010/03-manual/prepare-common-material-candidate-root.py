"""Prepare an equal-visibility source-only candidate; no coding or release."""
import copy
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
OWNER=ROOT/'06-coding/rule-v20-semantic-audit-repair-sol'
CAT=OWNER/'neutral-material-projection-candidate'
AUDIT=ROOT/'08-audits/neutral-common-projection-independent-sol'
OLD=ROOT/'03-manual/full4481-common-release-20261010-root'
DEST=ROOT/'03-manual/common-material-projection-candidate-root'

def bind(p):
    p=Path(p).resolve();raw=p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}

def exact(b):assert bind(b['path'])=={k:b[k]for k in('path','bytes','sha256')},b['path']

def load(p):return json.loads(Path(p).read_text())

def canonical(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def save(p,v):
    with Path(p).open('x',encoding='utf8')as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

manifest=load(CAT/'release-candidate-manifest.json')
assert manifest['records_scanned']==4481 and manifest['failure_N']==0
exact(manifest['builder_binding'])
for member in manifest['inventory_bindings']:exact(member)
audit_seal=load(AUDIT/'output-seal.json')
for member in audit_seal['output_members']:exact(member)
freeze=load(OLD/'common-input-freeze.json')
for field in('manual','prompt','protocol'):exact(freeze[field])
spec=importlib.util.spec_from_file_location('sealed_neutral_common_projection',manifest['builder_binding']['path'])
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
inputs=load(CAT/'packet-input-bindings.json');routes=load(CAT/'record-material-routes.json')
assert len(inputs)==len(routes)==4481
by_id={str(r['source_id']):r for r in routes};assert len(by_id)==4481
# Every source-only input is verified before any new packet is created.
for item in inputs:exact(item)
DEST.mkdir(exist_ok=False);packets=DEST/'packets';packets.mkdir();originals=DEST/'bound-UTF8-originals';originals.mkdir()
pre={'status':'preparation_only_not_common_release_or_execution','at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'projection':manifest['builder_binding'],'catalog':bind(CAT/'release-candidate-manifest.json'),'catalog_independent_audit':bind(AUDIT/'output-seal.json'),'old_common_freeze':bind(OLD/'common-input-freeze.json'),'builder':bind(__file__),'label_or_prediction_files_read':False,'old_primary_runtime_changed':False,'new_model_dispatch_N':0}
save(DEST/'preparation-provenance.json',pre)
original_delivery=[]
for line in(CAT/'bound-original-resources.jsonl').read_text().splitlines():
    item=json.loads(line);binding=item['original_binding'];exact(binding)
    path=originals/(item['source_sha256']+'.txt')
    shutil.copyfile(binding['path'],path)
    assert bind(path)['sha256']==binding['sha256']
    original_delivery.append({'original_provenance_binding':binding,'candidate_copy':bind(path),'relative_copy':str(path.relative_to(DEST)),'locator_rewritten':False,'scope':'separate portable source mapping; existing provenance locators retained'})
assert len(original_delivery)==17
packet_inventory=[];changed=0;old_prefix_matches=0;largest={'bytes':0,'source_id':None}
for item in inputs:
    raw=Path(item['path']).read_bytes();old=json.loads(raw);bundle=old['source_bundle']
    assert old['source_bundle_sha256']==canonical(bundle)
    projected,receipt=module.project(bundle)
    sid=str(bundle['source_record']['id'])
    assert receipt=={k:v for k,v in by_id[sid].items()if k!='source_id'}
    assert projected['source_record']==bundle['source_record']
    old_n=len(bundle['source_full_text_resources'])
    assert projected['source_full_text_resources'][:old_n]==bundle['source_full_text_resources']
    # Only the neutral resource extension/version fields can change the bundle.
    unchanged_keys=set(bundle)-{'source_full_text_resources','common_source_bundle_version','source_bundle_extension'}
    assert all(projected[k]==bundle[k]for k in unchanged_keys)
    new=copy.deepcopy(old)
    new['packet_version']='common-neutral-UTF8-projection-preparation-1'
    new['source_bundle']=projected;new['source_bundle_sha256']=canonical(projected)
    new['common_material_candidate_provenance']={'status':'candidate_not_released','parent_packet':item,'projection_version':module.VERSION,'material_interface_changed':receipt['material_interface_changed'],'actual_consumer_read_or_execution_recorded':False,'source_only':True}
    output=packets/Path(item['path']).name
    save(output,new)
    bound=bind(output)
    reread=load(output)
    assert canonical(reread['source_bundle'])==reread['source_bundle_sha256']
    assert reread['source_bundle']['source_record']==bundle['source_record']
    packet_inventory.append({'source_id':sid,'output_id':old['output_id'],'relative_packet':str(output.relative_to(DEST)),'packet_binding':bound,'parent_packet':item,'source_bundle_sha256':new['source_bundle_sha256'],'added_literal_resource_N':len(receipt['added_resources']),'material_interface_changed':receipt['material_interface_changed']})
    changed+=bool(receipt['material_interface_changed']);old_prefix_matches+=1
    if bound['bytes']>largest['bytes']:largest={'bytes':bound['bytes'],'source_id':sid}
assert changed==1227 and old_prefix_matches==4481
save(DEST/'packet-inventory.json',packet_inventory)
save(DEST/'original-delivery-map.json',original_delivery)
common_files=[]
for field,filename in(('manual','manual.txt'),('prompt','execution-prompt.txt'),('protocol','common-execution-protocol.txt')):
    source=freeze[field];destination=DEST/filename;shutil.copyfile(source['path'],destination)
    assert bind(destination)['sha256']==source['sha256']
    common_files.append({'role':field,'parent_binding':source,'candidate_copy':bind(destination)})
inventory_binding=bind(DEST/'packet-inventory.json')
roles={role:inventory_binding for role in('human_A','human_B','rule','LLM','adjudication_reference')}
save(DEST/'equal-visibility-role-bindings.json',{'status':'prepared_only_no_actual_role_delivery','shared_packet_inventory':inventory_binding,'role_inventory_bindings':roles,'same_source_record_and_full_material_for_all_roles':True,'human_independence_or_model_execution_claimed':False,'existing_human77_human200_AI800_and_primary4481_inputs_unchanged':True})
summary={'status':'complete_source_only_common_material_candidate_prepared_not_released','records':4481,'records_with_added_original_ranges':changed,'records_unchanged_material_content':4481-changed,'bound_original_files_copied':17,'source_record_and_old_resource_prefix_equality_N':old_prefix_matches,'projection_failures':0,'largest_candidate_packet':largest,'common_manual_prompt_protocol_copies':common_files,'inventory':inventory_binding,'role_visibility':bind(DEST/'equal-visibility-role-bindings.json'),'original_map':bind(DEST/'original-delivery-map.json'),'actual_new_human_results':0,'actual_new_rule_or_LLM_coding_runs':0,'old_primary_input_or_runtime_modified':False,'actual_release_or_coder_delivery':False,'labels_in_projection_or_candidate_packets':False,'necessary_followup':['independently inspect consumers for actually applicable relation and source consumption; literal availability alone cannot resolve old NULL','freeze any future common material release separately, and use equal inputs in comparisons','rebuild batch-size/resource budgets for changed packets instead of using old fixed assignments','update future sampling exposure and bind future reference/stability/statistics to the new material version; do not retroactively alter old frames or treat old predictions as this version','confirm portable original mapping before delivery outside the current machine'],'not_a_complete_validation_or_acceptance':True}
save(DEST/'summary.json',summary)
(DEST/'说明.txt').write_text('已准备4481条共同材料候选包，其中1227条补入同版UTF-8原件此前未进入字面材料接口的连续范围。材料投影不读取标签，也不改变当前条款、手册或既有资源。人工A/B、规则、LLM及裁定参照绑定同一候选目录；目前没有向这些角色实际派发或编码。正在运行的旧全量LLM、旧77条、旧800条和旧200条盲包保持原版。新增文字可用不等于已消费、适用于当前条款或自动解决待定。正式采用前仍需共同发布、消费者核验、新版分批预算和后续检验/抽样版本绑定。原件复制映射保留原始来源路径；外部机器交付前应按映射处理可移植访问。\n',encoding='utf8')
members=[bind(DEST/name)for name in('preparation-provenance.json','packet-inventory.json','original-delivery-map.json','equal-visibility-role-bindings.json','summary.json','说明.txt','manual.txt','execution-prompt.txt','common-execution-protocol.txt')]
save(DEST/'output-seal.json',{'status':'candidate_preparation_sealed_not_released','output_members':members,'packet_inventory_covers_all_4481_files':True,'original_map_covers_all17copies':True,'parent_manifest':bind(CAT/'release-candidate-manifest.json'),'independent_projection_audit':bind(AUDIT/'output-seal.json'),'self_excluded':True})
print(json.dumps({k:v for k,v in summary.items()if k not in ('necessary_followup','common_manual_prompt_protocol_copies')},ensure_ascii=False))
