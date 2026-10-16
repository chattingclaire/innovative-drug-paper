"""Byte/object identity check of existing common materials; no label files."""
import sys
sys.dont_write_bytecode=True
import json
import handoff as h

def main():
    c=h.load(h.HERE/'bindings.json');manifest=h.load(h.verify(c['frozen_inputs']['LLM_manifest']))
    source=h.verify(manifest['source_jsonl']);frame=h.frozen_frame(manifest)
    allrows=h.jsonlines(source);h.require([r['source_record']['id'] for r in allrows]==frame,'Source full frame/order differs')
    by={r['source_record']['id']:r for r in allrows}
    draw=h.load(h.verify(c['frozen_inputs']['draw']))['records'];selected={r['source_id'] for r in draw}
    pages=h.load(h.verify(c['frozen_inputs']['materials']))['pages'];human=[]
    for page in pages:
        b=page['json'];p=h.verify(b);bundle=h.load(p);rid=bundle['source_record']['id']
        h.require(rid in selected and bundle==by[rid],'Human and frozen full-frame common source differ')
        human.append({'side':page['side'],'blind_id':page['blind_id'],'source_id':rid,'raw_binding':b,'full_source_bundle_canonical_sha256':h.canonical(by[rid]),'object_equal':True})
    assignments=[];packets=[]
    for batch in manifest['batches']:
        if not set(batch['source_ids'])&selected:continue
        a=h.load(h.verify(batch['assignment']));assignments.append(batch['assignment'])
        for item in a['packets']:
            if item['source_id'] not in selected:continue
            b={k:item[k] for k in ('path','bytes','sha256')};packet=h.load(h.verify(b));rid=item['source_id']
            h.require(packet['source_id']==rid and packet['source_bundle']==by[rid] and packet['source_bundle_sha256']==item['source_bundle_sha256']==h.canonical(by[rid]),'Native packet/common full source differ')
            packets.append({'source_id':rid,'packet_binding':b,'source_bundle_sha256':packet['source_bundle_sha256'],'object_equal':True})
    h.require(len(human)==400 and len(packets)==200 and {p['source_id'] for p in packets}==selected,'Exact old200 common source coverage required')
    delivered=h.ROOT/'06-coding/rule-full4481-v2-root/run4481-first/delivered-complete-source-bundles.jsonl'
    rb=h.binding(delivered);rule_seal=h.load(h.verify(c['frozen_inputs']['rule_seal']))
    h.require(rb in rule_seal['output_files'],'Delivered rule common bundles not covered by original seal')
    rrows=h.jsonlines(delivered);h.require([r['source_record']['id'] for r in rrows]==frame,'Rule delivered frame/order differs')
    h.require(all(r==by[r['source_record']['id']] for r in rrows if r['source_record']['id'] in selected),'Rule delivered common bundle differs for old200')
    receipt={'status':'existing_material_identity_only_not_read_or_judgment_receipt','full_source_binding':manifest['source_jsonl'],'full_frame_rows':4481,'old200_common_material_rows':200,'human_material_bytes_and_object_equality_N':400,'native_packet_bytes_and_object_equality_N':200,'rule_delivered_selected_object_equality_N':200,'rule_delivered_binding':rb,'assignment_bindings':assignments,'human_members':human,'native_members':packets,'actual_human_judgments_N':0,'actual_machine_label_files_read_N':0,'semantic_date_or_policy_reaudit_claimed':False}
    with (h.HERE/'common-material-identity-receipt.json').open('x') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    with (h.HERE/'bindings-before-common-material-proof.json').open('x') as f:json.dump(c,f,ensure_ascii=False,indent=2);f.write('\n')
    c['frozen_inputs']['machine_full_common_source']=manifest['source_jsonl'];c['frozen_inputs']['rule_delivered_common_source']=rb
    c['common_material_identity_receipt_binding']=h.binding(h.HERE/'common-material-identity-receipt.json')
    (h.HERE/'bindings.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'human_common_N':400,'native_packet_N':200,'rule_common_N':200,'actual_machine_labels_read':0}))

if __name__=='__main__':main()
