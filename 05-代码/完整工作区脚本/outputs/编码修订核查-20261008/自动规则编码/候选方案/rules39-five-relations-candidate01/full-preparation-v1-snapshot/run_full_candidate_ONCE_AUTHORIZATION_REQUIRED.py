"""Prepared only. Invoke once only after root's explicit full-run authorization.

All4924 are processed mechanically from identical frozen v14 source inputs.
Reserved target outputs are excluded from semantic artifacts; source/raw
predictions are preserved. Missing material remains undetermined in N=4924.
"""
from pathlib import Path
import collections
import hashlib
import json
import sys
import time
from reserved_context_redactor import ReservedRedactor,digest_file,normalized_with_offsets

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=Path(__file__).resolve().parent
OUT=BASE/'full-run01'
DIMS=('S','E','Ec','I','F')

def save(path,obj):
    with path.open('x') as f:f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')

def guarded_context_fragments(obj,guard):
    # Derived context quotes can be shorter than the reserved full unit.
    # Conservatively hide any nontrivial derived quote wholly contained in a
    # reserved normalized unit, in addition to the exact full-sentence guard.
    if isinstance(obj,list):return [guarded_context_fragments(x,guard) for x in obj]
    if not isinstance(obj,dict):return obj
    out={}
    for k,v in obj.items():
        if k in {'cited_text','antecedent_text','context_text'} and isinstance(v,str):
            n,_=normalized_with_offsets(v)
            if len(n)>=8 and any(n in needle for _,needle in guard.needles):
                v='[可能源自预留原句的语境片段已机械遮蔽]'
        if k=='text' and isinstance(v,str) and 'paragraph_id' in obj and 'start' in obj and 'end' in obj and 'source_sha256' in obj:
            n,_=normalized_with_offsets(v)
            if len(n)>=8 and any(n in needle for _,needle in guard.needles):v='[可能源自预留原句的引用锚点已机械遮蔽]'
        out[k]=guarded_context_fragments(v,guard)
    return out

def main():
    start=time.time();freeze=json.loads((BASE/'full_execution_dependency_freeze.json').read_text())
    for path,sha in freeze['absolute_file_sha256'].items():assert digest_file(path)==sha,path
    if OUT.exists():raise FileExistsError('Refusing to overwrite any previous full-run directory')
    OUT.mkdir()
    guard=ReservedRedactor(ROOT);reserved={rid for rid,_ in guard.needles}
    sys.path.insert(0,str(BASE/'runtime'));import policy_coding_v27
    inputfile=ROOT/'outputs/coding-revision-20261007-r3/rule_inputs_shared_v14.jsonl'
    oldfile=ROOT/'outputs/coding-revision-20261008-r4/rules-v38-shadow-full-v14/all_predictions_material_v14_shadow.jsonl'
    old={json.loads(line)['id']:json.loads(line)['prediction'] for line in oldfile.open()}
    assert len(old)==4924
    n=0;ids=set();positive=collections.Counter();determined=collections.Counter();statuses=collections.Counter();missing=[]
    changes=[];change_cells=collections.Counter();reserved_changed_units=0;reserved_changed_cells=collections.Counter();reserved_target_n=0
    rawfile=OUT/'all_predictions_material_v14_shadow_MACHINE_RAW_NO_SEMANTIC_READING.jsonl'
    redfile=OUT/'all_predictions_material_v14_shadow_REDACTED_PRIVATE.jsonl'
    with rawfile.open('x') as raw,redfile.open('x') as red:
        for line in inputfile.open():
            row=json.loads(line);rid=row['id'];assert rid not in ids;ids.add(rid)
            p=policy_coding_v27.code_unit(row['input']);n+=1
            for e in p.get('evidence',[]):assert row['input']['unit_text'][e['start']:e['end']]==e['text']
            statuses[p.get('judgement_status')]+=1
            if p.get('judgement_status')=='undetermined':
                # Metadata only; no omitted row or synthetic negative.
                missing.append({'id':rid,'input_assessment_status':p.get('input_assessment_status'),'reason':p.get('input_assessment_reason') or row['input'].get('input_assessment',{}).get('reason'),'current_reference_gate_v39':p.get('current_reference_gate_v39'),'completeness_gate_v34_reason':(p.get('completeness_gate_v34') or {}).get('reason')})
            for d in DIMS:
                value=p['labels'][d]
                if type(value) is int and value in (0,1):determined[d]+=1;positive[d]+=value
            prediction={'id':rid,'original_id':row['original_id'],'prediction':p}
            raw.write(json.dumps(prediction,ensure_ascii=False)+'\n')
            if rid in reserved:
                reserved_target_n+=1
                red.write(json.dumps({'id':rid,'original_id':row['original_id'],'reserved_target':True,'prediction':'[预留目标单元输出仅保存机器原件，不供语义审读]'},ensure_ascii=False)+'\n')
            else:
                safe=guarded_context_fragments(guard.walk(prediction,rid,'$.prediction'),guard)
                red.write(json.dumps(safe,ensure_ascii=False)+'\n')
            label_delta={d:{'before':old[rid]['labels'][d],'after':p['labels'][d]} for d in DIMS if old[rid]['labels'][d]!=p['labels'][d]}
            fieldnames=sorted(k for k in set(old[rid])|set(p) if k!='version' and old[rid].get(k)!=p.get(k))
            for d in label_delta:change_cells[d]+=1
            if fieldnames:
                if rid in reserved:
                    reserved_changed_units+=1
                    for d in label_delta:reserved_changed_cells[d]+=1
                else:
                    detail={'id':rid,'original_id':row['original_id'],'input':row['input'],'label_changes':label_delta,'changed_fields':fieldnames,'before':old[rid],'after':p}
                    changes.append(guarded_context_fragments(guard.walk(detail,rid,'$.nonreserved_change'),guard))
            if n%500==0:print(json.dumps({'mechanically_completed':n,'status_counts':dict(statuses)},ensure_ascii=False),flush=True)
    assert n==4924 and ids==set(old) and reserved_target_n==267
    save(OUT/'nonreserved_all_field_changes_REDACTED_PRIVATE.json',{'nonversion_changed_units':changes,'version_changes_reported_separately':True})
    save(OUT/'material_issue_METADATA_ONLY.json',{'total_n':n,'undetermined_n':len(missing),'records':missing,'no_undetermined_dropped_from_input_n':True})
    save(OUT/'reserved_aggregate_METADATA_ONLY.json',{'reserved_target_n':reserved_target_n,'nonversion_changed_units':reserved_changed_units,'label_changed_cells':dict(reserved_changed_cells),'semantic_target_outputs_hidden':True,'not_used_for_development':True,'context_contact_n':len(guard.contacts),'context_owner_n':len({c['owner'] for c in guard.contacts}),'context_reserved_member_n':len({c['reserved_id'] for c in guard.contacts}),'guard_bindings':guard.bindings,'derived_fragment_guard':'derived context quotes/anchors normalized length>=8 that are wholly contained in a reserved full normalized sentence are conservatively hidden; target reserved predictions entirely withheld from semantic artifacts'})
    summary={'status':'FULL_MECHANICAL_RUN_COMPLETE_REVIEW_REQUIRED','input_n':n,'unique_n':len(ids),'source_input_sha256':digest_file(inputfile),'source38_output_sha256':digest_file(oldfile),'raw_output_sha256':digest_file(rawfile),'redacted_output_sha256':digest_file(redfile),'status_counts':dict(statuses),'positive_counts':dict(positive),'determined_denominators':dict(determined),'undetermined_n':len(missing),'nonreserved_nonversion_changed_unit_n':len(changes),'total_label_changed_cells':dict(change_cells),'reserved_target_n':267,'reserved_changed_unit_n':reserved_changed_units,'reserved_changed_label_cells':dict(reserved_changed_cells),'no_reference_labels_consumed':True,'no_model_calls':True,'elapsed_seconds':round(time.time()-start,3),'independent_validation_claim':False}
    save(OUT/'full_run_summary.json',summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
