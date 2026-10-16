"""Seal the residual-frame census and release label-blind full-input packets."""
from pathlib import Path
import hashlib
import json
import random
import shutil
import sys

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'validation-expansion-20260926'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    audit_path=HERE/'新验证框-新增暴露接入.json';audit=json.loads(audit_path.read_text())
    for p,h in audit['input_sha256'].items():assert sha(Path(p))==h,(p,'audit source changed')
    rule_freeze=HERE/'rule_runs/v25-candidate-3/freeze.json'
    rule=json.loads(rule_freeze.read_text())
    for p,h in rule['code_and_input_bindings'].items():assert sha(Path(p))==h,(p,'rule freeze changed')
    residual=set(audit['residual_ids']);assert len(residual)==427
    allrows=[json.loads(s) for s in (HERE/'current_rule_inputs.jsonl').read_text().splitlines()]
    originals={r['id']:r['original_id'] for r in allrows}
    original_to_run={v:k for k,v in originals.items()}
    llm={r['id']:r for r in (json.loads(s) for s in (HERE/'current_llm_inputs.jsonl').read_text().splitlines())}
    current_ref_ids={json.loads(s)['original_id'] for s in (HERE/'current_1268_references.jsonl').read_text().splitlines()}
    assert not residual & current_ref_ids
    order=sorted(residual);random.Random(2026092701).shuffle(order)
    root=HERE/'H427';root.mkdir(exist_ok=False)
    packets=[];mapping=[]
    for i,original_id in enumerate(order,1):
        r=dict(llm[original_to_run[original_id]])
        r['id']=f'H427-{i:04d}'
        packets.append(r)
        mapping.append({'id':r['id'],'original_id':original_id,'rerun_id':original_to_run[original_id],
                        'text_sha256':hashlib.sha256(r['text'].encode()).hexdigest()})
    manifest={}
    for c in ['A','C']:
        dest=root/f'agent-{c}';dest.mkdir()
        shutil.copyfile(HERE/'protocol-v1.3.md',dest/'五维共用编码协议.md')
        shutil.copyfile(OLD/'V600-frozen-inputs/protocol_clarifications.md',dest/'统一澄清.md')
        for i in range(0,len(packets),10):
            batch=i//10+1
            payload={'protocol_version':'CAL-5D-20260926-v1.3','phase':'H427',
                     'purpose':'new_reference_labels_blind_to_both_methods_and_other_coder',
                     'batch':batch,'total_batches':43,'rows':packets[i:i+10]}
            f=dest/f'材料-{batch:02d}.json'
            f.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
            manifest[str(f.relative_to(root))]=sha(f)
    for i in range(1,44):
        assert (root/'agent-A'/f'材料-{i:02d}.json').read_bytes()==(root/'agent-C'/f'材料-{i:02d}.json').read_bytes()
    (root/'admin_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
    freeze={'phase':'H427','purpose':'finite_remaining_frame_census_not_original_population_validation',
            'n':427,'sampling':'census; no random sample selection','display_shuffle_seed':2026092701,
            'python':sys.version,'protocol_version':'CAL-5D-20260926-v1.3',
            'rule_code_frozen':rule,'new_exposure_audit_sha256':sha(audit_path),
            'packet_hashes':manifest,'mapping_sha256':sha(root/'admin_mapping.json'),
            'llm_execution_status':'authentication_pending_no_real_predictions',
            'llm_prompt_and_interface_before_reference_release':{
                'interface_sha256':sha(HERE/'llm_recoder.py'),
                'prompt_sha256':__import__('llm_recoder').sha(__import__('llm_recoder').system_prompt().encode())},
            'prospective_order_note':'Both fresh AI references may be produced while provider authentication is pending. Root must not inspect their labels, reasons, prevalence or compute H427 metrics until LLM model and interface are frozen and predictions sealed; no prompt/rule revision from new reference outputs.',
            'prior_data_not_relabelled':True,'reviewer_identity':'AI, not real human experts',
            'limitations':audit['limitations']}
    (root/'release_freeze.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'released_units':427,'packets_each':43,'identical_A_C_inputs':True,'machine_or_reference_labels_in_packets':False},ensure_ascii=False))

if __name__=='__main__':main()
