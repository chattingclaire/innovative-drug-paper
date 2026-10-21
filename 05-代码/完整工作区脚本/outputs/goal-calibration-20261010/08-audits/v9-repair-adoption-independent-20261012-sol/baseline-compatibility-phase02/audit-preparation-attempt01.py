"""Metadata and static-AST inheritance audit, no new packet bodies/classifier."""
import ast
import copy
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone

G=Path('/PROJECT_ROOT/outputs/goal-calibration-20261010')
O=G/'08-audits/v9-repair-adoption-independent-20261012-sol/baseline-compatibility-phase02'
V=G/'06-coding/rule-five-dimension-joint-root/versions'
P=G/'08-audits/v8-bounded-execution-independent-20261011-sol'
bindings={}
def bind(p):
    p=Path(p);h=hashlib.sha256();n=0
    with p.open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk);n+=len(chunk)
    x={'path':str(p),'bytes':n,'sha256':h.hexdigest()};bindings[str(p)]=x;return x
def read(p):
    bind(p);return json.loads(Path(p).read_text())
def save(n,x):
    (O/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def verified(q):
    z=bind(q['path']);assert z==q;return z

m=read(G/'08-audits/v9-static-selection-manifest-root/full4481-identity-manifest.json')
ms=read(G/'08-audits/v9-static-selection-manifest-root/preparation-seal.json')
for q in ms['files']+ms['source_metadata']:verified(q)
f=read(G/'06-coding/rule-full4481-final-v7-root/frozen-scope.json')
p=read(G/'06-coding/rule-full4481-final-v7-root/packet-bindings.json')
ids=[r['id'] for r in m['records']]
assert len(ids)==len(set(ids))==4481
assert len({r['output_id'] for r in m['records']})==4481
assert ids==m['approved_record_ids']==f['approved_record_ids']==p['ordered_source_ids']
verified(f['packet_bindings'])
prior_bindings=read(P/'execution-readback/input-bindings.json')
previous={x['path']:x for x in prior_bindings['files']}
for r,q in zip(m['records'],p['packets']):
    packet={k:q[k] for k in ('path','bytes','sha256')}
    assert r=={'id':q['source_id'],'output_id':q['output_id'],'packet_binding':packet}
    assert previous[packet['path']]==packet
# No actual packet body is reopened. Every manifest binding is exactly the
# packet binding independently checked in the frozen v8 execution audit.

prep=read(P/'preparation-readback/report.json')
exe=read(P/'execution-readback/report.json')
delivery=read(P/'delivery-seal.json')
for q in delivery['members']:
    if q['path'] in {str(P/'preparation-readback/report.json'),str(P/'execution-readback/report.json'),str(P/'execution-readback/input-bindings.json')}:
        verified(q)
assert prep['four_modules_byte_unchanged'] is True
assert prep['outside_changed_if_body_byte_unchanged'] is True
assert prep['restored_old_body_AST_identical'] is True
assert prep['old_final_and_candidate_decisions_all_identical'] is True
assert prep['all_reference_marker_hits_included'] is True
assert prep['original_line_and_packet_bytes_preserved'] is True
assert prep['affected_record_N']==7 and prep['unaffected_reusable_record_N']==4474
assert exe['inherited_v7_record_N']==4474
assert exe['inherited_v7_slots_byte_identical_N']==22370
assert exe['actual_delta_slots_byte_identical_N']==35
assert exe['merged_record_N']==4481 and exe['merged_slot_N']==22405
assert exe['complete_decision_change_N_v7_to_v8']==2
assert exe['classifier_imports_or_calls_N']==0

v7seal=read(V/'joint-v7-relation-content-sol/seal.json')
v8seal=read(V/'joint-v8-target-product-gap-sol/output-seal.json')
module_bindings=[]
for n in ['evidence','source_packet','source_receipts','relations','dimensions']:
    old=V/'joint-v7-relation-content-sol'/f'{n}.py';new=V/'joint-v8-target-product-gap-sol'/f'{n}.py'
    ob=bind(old);nb=bind(new)
    assert ob in v7seal['files'] and nb in v8seal['files']
    module_bindings.append({'module':n,'v7':ob,'v8':nb})
    if n!='dimensions':assert ob['bytes']==nb['bytes'] and ob['sha256']==nb['sha256']
ot=ast.parse((V/'joint-v7-relation-content-sol/dimensions.py').read_text())
nt=ast.parse((V/'joint-v8-target-product-gap-sol/dimensions.py').read_text())
def branch(t):
    fun=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='_fairness')
    xs=[x for x in ast.walk(fun) if isinstance(x,ast.If) and '境外已上市' in ast.dump(x.test) and 'GAPS' in ast.dump(x.test)]
    assert len(xs)==1;return xs[0]
ob=branch(ot);nb=branch(nt)
assert ast.dump(ob.test,include_attributes=False)==ast.dump(nb.test,include_attributes=False)
assert len(ob.body)==1 and isinstance(ob.body[0],ast.Expr)
call=ob.body[0].value
assert isinstance(call,ast.Call) and isinstance(call.func,ast.Attribute) and isinstance(call.func.value,ast.Name)
assert call.func.value.id=='acc' and call.func.attr=='boundary'
assert ast.literal_eval(call.args[0])=='F' and ast.literal_eval(call.args[2])=='单品种未上市与按需优先机会'
nb.body=copy.deepcopy(ob.body)
assert ast.dump(nt,include_attributes=False)==ast.dump(ot,include_attributes=False)

merged=G/'06-coding/rule-full4481-v8-delta-merged-root'
status=read(merged/'composite-status.json');seal=read(merged/'seal.json')
for q in seal['files']+seal['ancestor_seals']:verified(q)
assert status['actual_record_N']==4481 and status['actual_dimension_N']==22405
assert status['technical_failure_dimension_N']==0
assert status['actual_v7_full_inference_record_N']==4481
assert status['actual_v8_delta_inference_record_N']==7
assert status['inherited_v7_record_N']==4474
assert status['all4481_actually_inferred_under_v8'] is False
pred=next(q for q in seal['files'] if Path(q['path']).name=='predictions.jsonl')
assert previous[pred['path']]==pred
assert previous[str(merged/'seal.json')]==bindings[str(merged/'seal.json')]
affected=[r['id'] for r in prep['affected_records']]
assert len(affected)==len(set(affected))==7

report={'created_utc':datetime.now(timezone.utc).isoformat(),'status':'current_v8_compatible_mixed_baseline_and_manifest_verified_candidate_still_pending','full_manifest_record_N':4481,'exact_ordered_ids_and_packet_bindings_equal_v7_and_previous_independent_readback':True,'unselected_packet_bodies_reopened_N':0,'opaque_sealed_result_file_hashes_rechecked':'bytes only, no new semantic interpretation/classification','four_v7_v8_modules_bytes_equal':True,'dimensions_only_old_unconditional_F_boundary_body_changed':True,'restoring_old_F_body_AST_equals_all_v7_dimensions':True,'old_branch_always_emits_exact_boundary_marker':True,'previous_independent_full_marker_closure_ids':affected,'inherited_v7_record_N':4474,'actual_v8_delta_record_N':7,'baseline_all4481_actually_inferred_v8':False,'reusable_old_v7_semantics_compatible_with_exact_frozen_v8':'Prior sealed audit proved complete old-branch marker closure across all original v7 final/candidate records. Since only this one body changed and every execution of its unchanged test emits the exact marker, every possible v8 semantic effect is inside seven actual delta records; all other records retain equivalent v7 bytes. Current file/manifest/code hashes agree with that prior proof.','baseline_prediction_binding':pred,'module_bindings':module_bindings,'source_input_bindings_changed':False,'candidate_adoption_approved':False,'remaining':['Inspect actual candidate bodies and every side effect','Prove guarded AST removal equals exact frozenv8 and IF-only record-local mutations','Bind actual complete selector contract; ROOT executes selector, no independent classifier run'],'classification_runs':0,'new_labels_or_gold':False,'formal_validation':False}
save('report.json',report)
(O/'report.md').write_text('# v9混合基线承接复核\n\n完整4481静态manifest的顺序ID、原output_id及packet指纹逐项等于冻结v7原包元数据，并等于此前独立v8执行审计已核指纹。本次未重开未选原包正文。\n\nv7与v8四模块字节相同；恢复唯一F边界分支body后，全dimensions AST相同。原分支条件不变，进入时必定记录同一边界标记；此前完整独立审计已证明该标记影响闭包是7项，且7项实际重算。当前合并来源仍为4474原v7＋7实际v8，22405槽位，0技术失败；密封结果字节指纹和证明报告均未变化。因此该混合基线可作为冻结v8语义的兼容基线，并不等于4481实际全跑v8。\n\n候选尚未审定。本报告只证明原混合基线与完整manifest承接；仍须核实际v9入口、代码副作用及全影响契约，再由ROOT执行selector和生产。没有分类调用、标签改写或正式验证声明。\n')
save('input-bindings.json',{'files':list(bindings.values()),'all_unchanged':True,'unselected_packet_body_reads':0})
for q in list(bindings.values()):verified(q)
members=[bind(p) for p in sorted(O.iterdir()) if p.is_file() and p.name!='output-seal.json']
save('output-seal.json',{'created_utc':datetime.now(timezone.utc).isoformat(),'members':members,'member_count':len(members),'candidate_adoption_approved':False})
print(json.dumps({'report':bind(O/'report.json'),'seal':bind(O/'output-seal.json'),'mixed_baseline_compatible':True,'candidate_adoption_approved':False},ensure_ascii=False,indent=2))
