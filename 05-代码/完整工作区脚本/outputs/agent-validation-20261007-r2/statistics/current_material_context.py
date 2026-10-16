"""Bind final v8 dual materials without changing the completed v6 A/C record."""
from statistical_core import *

def load_current_context():
    ctx=load_context()
    rp=RUN/'rule_inputs_shared_v8.jsonl';lp=RUN/'effective_blind_inputs_v8.jsonl';mp=RUN/'material_v8_manifest.json'
    assert sha(rp)=='e43300eed535cc1e0bb055830a9f2a0123ec17db7536333d6f1ca518283fdd11'
    assert sha(lp)=='820d4cc554975e59e8e839a2bf12b381e76c1b32175cd97524104f340351e4e4'
    rules=jsonl(rp);llm=jsonl(lp);manifest=read(mp)
    assert set(rules)==set(llm)==set(ctx['inputs']) and len(rules)==4924
    changed=[]
    for rid,row in rules.items():
        assert row['input']['unit_text']==ctx['inputs'][rid]['input']['unit_text']==llm[rid]['text']
        assert row['input']['llm_v29_shared_context']==llm[rid]['contexts']
        if llm[rid]!=ctx['llm_inputs'][rid]:changed.append(rid)
    previous=read(RUN/'material_v7_manifest.json')
    assert sorted(changed)==sorted(set(manifest['affected_ids_incremental'])|set(previous['affected_ids_incremental']))
    sample_changed=sorted(set(changed)&set(ctx['sample']))
    assert len(changed)==61 and sample_changed==sorted(manifest['current_reference_incremental_ids']) and len(sample_changed)==4
    assert manifest['total_changed_from_v3']==84 and manifest['unit_text_changes']==0
    ctx.update(inputs=rules,llm_inputs=llm,final_material_version='v8',
        v6_to_final_sample_material_identity=False,v6_to_final_changed_ids=changed,
        final_source_reread_sample_ids=sample_changed)
    ctx['source_paths'] += [rp,lp,mp,Path(__file__)]
    return ctx
