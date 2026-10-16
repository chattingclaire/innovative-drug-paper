"""Final statistics from a root-confirmed explicit SHA-bound manifest.

Usage: python3 run_final_statistics_r3.py --bindings MANIFEST.json
       --bindings-sha256 SHA256 --out NEW_DIRECTORY
Never searches for latest outputs, substitutes legacy labels or chooses runs.
"""
from pathlib import Path
import argparse
import csv
import datetime
import json
import statistical_core_r3 as c
import final_binding_io_r3 as io
from final_attention_r3 import probability_attention,full_machine_attention
from final_stability_binding_r3 import final_stability


def point_undefined_reasons(row):
    tp,fp,fn,tn=row['weighted_confusion'].values();n=tp+fp+fn+tn
    result={}
    for name,metric in row['metrics'].items():
        if metric['estimate'] is not None:continue
        result[name]=('no paired binary observations' if not n else
            'both constant marginals; expected agreement equals1' if name=='kappa' else
            'no predicted positives: TP+FP=0' if name=='precision' else
            'no reference positives: TP+FN=0' if name=='recall' else
            'neither side positive: 2TP+FP+FN=0' if name=='f1' else 'zero denominator')
    return result


def classification(ctx,methods,refs):
    records=[];cache={}
    for component in ('probability_canonical','enriched_challenge'):
        eligible=[rid for rid,row in ctx['sample'].items() if row['component']==component]
        for group,kind in c.groups_and_weights(component):
            ids=sorted(rid for rid in eligible if group=='ALL' or ctx['sample'][rid]['group']==group)
            if not ids:continue
            for name,rows in methods.items():
                for reference,target in refs.items():
                    for dim in c.DIMS:
                        row=c.comparison(ctx,rows,target,dim,ids,component,group,kind,name,reference,cache)
                        row['undefined_point_reasons']=point_undefined_reasons(row)
                        row['material_version']=ctx['material_version'];records.append(row)
    ac=[]
    for component in ('probability_canonical','enriched_challenge'):
        eligible=[rid for rid,row in ctx['sample'].items() if row['component']==component]
        for group,kind in c.groups_and_weights(component):
            ids=sorted(rid for rid in eligible if group=='ALL' or ctx['sample'][rid]['group']==group)
            if not ids:continue
            for dim in c.DIMS:
                row=c.comparison(ctx,refs['A'],refs['C'],dim,ids,component,group,kind,'A_C','symmetric A/C',cache)
                row['undefined_point_reasons']=point_undefined_reasons(row)
                row['symmetric_raw_cells']=dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'),row.pop('raw_confusion').values()))
                row['symmetric_weighted_cells']=dict(zip(('A1_C1','A1_C0','A0_C1','A0_C0'),row.pop('weighted_confusion').values()))
                row['material_version']=ctx['material_version'];ac.append(row)
    return records,ac


def binding_leaves(obj):
    if isinstance(obj,dict):
        if isinstance(obj.get('path'),str) and isinstance(obj.get('sha256'),str):yield obj
        for value in obj.values():yield from binding_leaves(value)
    elif isinstance(obj,list):
        for value in obj:yield from binding_leaves(value)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--bindings',type=Path,required=True)
    parser.add_argument('--bindings-sha256',required=True)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args()
    assert not args.out.exists(),'Write to a new directory; preserve prior stages'
    assert c.sha(args.bindings)==args.bindings_sha256,'Binding manifest SHA mismatch'
    manifest=c.read(args.bindings)
    assert manifest.get('stage')=='final','A stage manifest cannot produce final tables'
    bound_files=list(binding_leaves(manifest))
    assert all(c.sha(entry['path'])==entry['sha256'] for entry in bound_files)
    ctx=io.context_from_manifest(manifest)
    refs,ref_audit=io.final_references(manifest,ctx)
    methods=io.final_methods(manifest,ctx)
    records,ac=classification(ctx,methods,refs)
    attention=probability_attention(ctx,{**refs,**methods})
    full=full_machine_attention(ctx,methods,manifest['robustness_scenarios'])
    stability=final_stability(manifest,ctx,methods['LLM'])
    low=[{k:row[k] for k in ('component','group','weighting','method','reference','dimension','paired_n','raw_confusion')}
         | {'diagnostics':row['point_0_80_diagnostics'],'undefined_point_reasons':row['undefined_point_reasons'],
            'metrics':{name:metric['estimate'] for name,metric in row['metrics'].items()}}
         for row in records if any(value!='at_least_0_80' for value in row['point_0_80_diagnostics'].values())]
    # Verify inputs remained unchanged before publishing any final result files.
    assert all(c.sha(entry['path'])==entry['sha256'] for entry in bound_files)
    provenance={'created_at':datetime.datetime.now().astimezone().isoformat(),
        'binding_manifest_path':str(args.bindings.resolve()),'binding_manifest_sha256':args.bindings_sha256,
        'material_version':ctx['material_version'],'source_scope':'4481 complete three-department machine units; canonical reference inference only947/760/60',
        'human_validation_completed':False,'threshold_0_80_role':'diagnostic work target, not publication line',
        'no_legacy_label_substitution':True,'no_production_run_replacement':True,
        'reference_reviewer_identity_note':manifest.get('reviewer_identity_note'),
        'method_execution_notes':manifest.get('method_execution_notes',{}),
        'script_sha256':c.sha(Path(__file__)),'analysis_notes':c.analysis_notes()}
    args.out.mkdir(parents=True,exist_ok=False)
    files={'provenance.json':provenance,'reference_binding_QA.json':ref_audit,
        'machine_reference_classification.json':{'provenance':provenance,'comparisons':records},
        'A_C_final_before_third_agreement.json':{'provenance':provenance,'comparisons':ac},
        'low_values_and_NA.json':{'provenance':provenance,'records':low},
        'probability_attention_and_paired_department_differences.json':{'provenance':provenance,**attention},
        'full4481_machine_attention_and_file_composition_sensitivity.json':{'provenance':provenance,**full},
        'LLM_identical_request_stability_and_order_sensitivity.json':{'provenance':provenance,**stability}}
    for name,data in files.items():c.write_json(args.out/name,data)
    (args.out/'candidate_reference.jsonl').write_text(''.join(json.dumps(refs['candidate'][rid],ensure_ascii=False)+'\n' for rid in ctx['sample']))
    columns=['component','group','weighting','method','reference','dimension','unit_frame_n','paired_n','excluded_pending_n','left_positive_n','reference_positive_n','TP','FP','FN','TN']
    columns += [field for name in c.METRIC_NAMES for field in (name,name+'_ci95_low',name+'_ci95_high',name+'_undefined_repetitions')]
    with (args.out/'machine_reference_classification.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=columns);writer.writeheader()
        for row in records:
            flat={k:row[k] for k in columns if k in row};flat.update(row['raw_confusion'])
            for name,metric in row['metrics'].items():
                flat[name]=metric['estimate'];flat[name+'_ci95_low']=metric['ci95_primary']['low']
                flat[name+'_ci95_high']=metric['ci95_primary']['high']
                flat[name+'_undefined_repetitions']=metric['ci95_primary']['undefined_repetitions']
            writer.writerow(flat)
    c.write_json(args.out/'output_freeze.json',{'bindings_sha256':args.bindings_sha256,
        'files':{path.name:c.sha(path) for path in args.out.iterdir() if path.is_file()}})
    print(json.dumps({'status':'complete_final_bound_statistics','output':str(args.out),
        'machine_comparison_n':len(records),'A_C_comparison_n':len(ac),'low_or_NA_comparison_n':len(low)},ensure_ascii=False))


if __name__=='__main__':main()
