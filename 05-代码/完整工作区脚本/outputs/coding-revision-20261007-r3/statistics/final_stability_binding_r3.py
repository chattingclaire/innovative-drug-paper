"""Bind actual production originals to extra repeats without choosing outputs."""
from pathlib import Path
import json
import statistical_core_r3 as c
from final_binding_io_r3 import bound
from stability_r3 import summarize_stability,summarize_order_perturbation


def final_stability(manifest,ctx,production_all):
    spec=manifest['stability'];qa=bound(spec['actual_runs_technical_qa'])
    assert qa['status']=='pass_nine_actual_runs_technical_QA'
    pre=bound(qa['bindings']['preselection']);material=bound(qa['bindings']['material'])
    by_run={(row['purpose'],row['production_batch']):row for row in qa['runs']}
    runs={'production':{},'repeat2':{},'repeat3':{}};perturbed={};ids=[];audit=[]
    production_bindings={row['production_batch']:row for row in spec['production_batches']}
    assert set(production_bindings)=={row['production_batch'] for row in material['bindings']}
    for batch in material['bindings']:
        number=batch['production_batch'];ids.extend(batch['all_ids']);pb=production_bindings[number]
        packet=bound(pb['packet']);selected=bound(pb['selection']);raw=bound(pb['selected_raw'])
        meta=bound(pb['selected_metadata'])
        run_root=Path(pb['selection']['path']).parents[2]
        assert str((run_root/selected['selected_relative_path']/'raw_output.json').resolve())==str(Path(pb['selected_raw']['path']).resolve())
        assert selected['status']=='accepted_first_valid_actual_attempt'
        first=next(a['relative_path'] for a in selected['attempts'] if a['status']=='accepted_structural_literal_zero_tools')
        assert selected['selected_relative_path']==first
        assert selected['selected_output_sha256']==pb['selected_raw']['sha256']
        assert meta['raw_output_sha256']==pb['selected_raw']['sha256'] and meta['tool_event_count']==0
        assert selected['selection_uses_metric_or_label_values'] is False
        assert [r['id'] for r in packet['rows']]==batch['all_ids']==[r['id'] for r in raw['rows']]
        # Exact final input row identity, not just label equality or text match.
        for row in packet['rows']:
            assert row==ctx['llm_inputs'][row['id']],(row['id'],'stability_production_material_not_final')
        for row in raw['rows']:
            assert all(production_all[row['id']].get(k)==v for k,v in row.items()),(row['id'],'production_first_output_reconstruction')
            runs['production'][row['id']]=row
        prod_request=Path(pb['request']['path']);assert c.sha(prod_request)==pb['request']['sha256']
        for purpose,name in [('stability-base-repeat-2','repeat2'),('stability-base-repeat-3','repeat3'),('stability-order-perturbation','order')]:
            entry=by_run[purpose,number]
            repeat_packet=bound(entry['packet'])
            assert repeat_packet==packet,(number,purpose,'complete_packet_differs')
            for binding in ('output','selected_raw','input','request','prompt'):
                assert c.sha(entry[binding]['path'])==entry[binding]['sha256']
            if name!='order':assert entry['request']['sha256']==pb['request']['sha256'],(number,'not_identical_full_production_request')
            rows=bound(entry['selected_raw'])['rows']
            target=perturbed if name=='order' else runs[name]
            target.update({row['id']:row for row in rows})
        audit.append({'production_batch':number,'production_bindings':pb,
                      'original_first_valid_output_retained':True,'all_final_material_rows_match':True})
    assert len(ids)==len(set(ids))==75
    assert sum(ctx['groups'][rid] in c.GROUPS for rid in ids)==72
    return {'binding_audit':audit,'final_material_version':ctx['material_version'],
            'identical_prompt_three_runs':summarize_stability(runs,ids,ctx['groups']),
            'prompt_order_sensitivity':summarize_order_perturbation(runs['production'],perturbed,ids,ctx['groups']),
            'production_output_replaced':False,'stability_is_semantic_validity':False}
