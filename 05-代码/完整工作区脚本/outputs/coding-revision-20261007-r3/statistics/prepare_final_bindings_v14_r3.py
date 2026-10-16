"""Assemble explicit v14 final bindings only after all reference results are ready.

Without --root-confirmed the output is an ineligible ready draft. The explicit
flag is for the root agent after it confirms source, execution and references.
"""
from copy import deepcopy
from pathlib import Path
import argparse
import json
import statistical_core_r3 as c
import final_binding_io_r3 as io
from final_stability_binding_r3 import final_stability


def bd(path):return {'path':str(Path(path).resolve()),'sha256':c.sha(path)}


def main():
    p=argparse.ArgumentParser();p.add_argument('--root-confirmed',action='store_true')
    p.add_argument('--out',type=Path,required=True);args=p.parse_args();assert not args.out.exists()
    root=c.RUN;stage=root/'statistics/T参照66-v14阶段绑定.json'
    refs=c.read(stage);ref_qa_path=root/'reference/A_C_T合并与逐字证据QA-v14.json'
    assert c.read(ref_qa_path)['all_checks_pass'] is True
    llm_dir=root/'llm-v32/full-production-candidate02-material-v14-source-citation-reconciled'
    llm_qa_path=root/'statistics/LLM-v14逐次实际请求与多来源独立执行QA.json'
    rule_qa_path=root/'statistics/规则v33-v14实际执行独立QA.json'
    llm_qa=c.read(llm_qa_path);rule_qa=c.read(rule_qa_path)
    assert llm_qa['all_checks_pass'] and rule_qa['all_checks_pass']
    manifest=deepcopy(refs)
    manifest.update({'stage':'final' if args.root_confirmed else 'ready_v14_root_confirmation_pending',
        'root_final_bindings_confirmed':bool(args.root_confirmed),
        'references_merge_qa':bd(ref_qa_path),'references_stage_binding':bd(stage)})
    manifest['methods']={
        'rules':{'material_version':'v14','frozen_method_id':'rules-v33',
            'output':bd(root/'rules-v33/all_predictions_material_v14.jsonl'),'execution_qa':bd(rule_qa_path)},
        'LLM':{'material_version':'v14','frozen_method_id':'LLM-v32-candidate02',
            'output':bd(llm_dir/'all_predictions.jsonl'),'execution_qa':bd(llm_qa_path),
            'actual_row_provenance':bd(llm_dir/'row_provenance.jsonl')}}
    manifest['robustness_scenarios']=['primary','policy_file_equal','policy_series_equal',
        'leave_one_policy_entry_out','latest_annual_series_member','exclude_joint_publications']
    manifest['method_execution_notes']={
        'rules':'Frozen v33 is the confirmatory baseline. v34/v34.1/v35/v35.1 remain separate development diagnostics.',
        'LLM':'Candidate02 semantic base with citation-isolation-tech01 on batch115; five labels always from one intact actual row, earliest valid exact full request selected.',
        'actual_prompt_sha256_counts':llm_qa['actual_prompt_sha256_counts'],
        'actual_cli_version_counts':llm_qa['actual_cli_version_counts'],
        'all_actual_prompts_byte_identical':False,
        'historical_inner_executable_sha256_available':False,
        'provider_internal_revision':'not exposed; not fabricated',
        'stability_scope':'Three preselected original batches, identical base actual requests. Does not evaluate the technical-suffix batch or CLI-updated batches.'}
    lineage={row['batch']:row for row in c.read(llm_dir/'batch_lineage.json')}
    production=[]
    for number in (13,147,47):
        row=lineage[number];raw=Path(row['selected_raw_path']);attempt=raw.parent
        assert row['technical_version'] is None
        production.append({'production_batch':number,'packet':bd(attempt/'input.json'),
            'selection':bd(row['selection_path']),'selected_raw':bd(raw),
            'selected_metadata':bd(attempt/'run_metadata.json'),'request':bd(attempt/'request.txt')})
    manifest['stability']={'actual_runs_technical_qa':bd(root/'statistics/LLM九组实际重复与顺序微扰技术QA-v11.json'),
        'production_batches':production}
    # Exercise complete reference, method and stability guards before writing.
    validation=deepcopy(manifest);validation['root_final_bindings_confirmed']=True
    ctx=io.context_from_manifest(validation);ref_rows,ref_audit=io.final_references(validation,ctx)
    methods=io.final_methods(validation,ctx);stable=final_stability(validation,ctx,methods['LLM'])
    assert len(ref_rows['candidate'])==240 and len(ref_audit['T']['reviewed_original_ids'])==66
    manifest['readiness_verification']={'all_source_reference_method_and_stability_bindings_checked':True,
        'source_n':4924,'AC_n_each':240,'T_reviewed_n':66,'production_stability_n':75,
        'all_three_stability_batches_exact_final_material':True,'real_human_validation_completed':False,
        'script_sha256':c.sha(Path(__file__))}
    manifest['analysis_code_bindings']=[bd(Path(__file__).parent/name) for name in (
        'run_final_statistics_r3.py','statistical_core_r3.py','statistical_extensions_r3.py',
        'final_binding_io_r3.py','reference_bindings_r3.py','prepare_final_reference_and_third_r3.py',
        'final_stability_binding_r3.py','stability_r3.py','final_attention_r3.py')]
    c.write_json(args.out,manifest)
    print(json.dumps({'status':manifest['stage'],'bindings':str(args.out.resolve()),
        'sha256':c.sha(args.out),'formal_rules':'v33','reference_n':240,'T_reviewed_n':66},ensure_ascii=False))


if __name__=='__main__':main()
