"""Create ONLY new handoff templates/year metadata; no labels or sampling."""
import sys
sys.dont_write_bytecode=True
import json
from collections import Counter
from pathlib import Path
import handoff as h
HERE=h.HERE;ROOT=h.ROOT

def write(name,obj):
    with (HERE/name).open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def jsonl(name,rows):
    with (HERE/name).open('x') as f:
        for row in rows:f.write(json.dumps(row,ensure_ascii=False,allow_nan=False)+'\n')

def main():
    f={
      'human_first':'07-statistics/human200-formal-handoff-root/human_first.py',
      'human_first_bindings':'07-statistics/human200-formal-handoff-root/bindings.json',
      'receiver_bindings':'05-validation/human200-reception-root/bindings.json',
      'receiver_code':'05-validation/human200-reception-root/receive.py',
      'receiver_source_reader':'05-validation/human200-reception-root/bound_xlsx_reader.py',
      'receiver_seal':'05-validation/human200-reception-root/seal.json',
      'statistics_template':'05-validation/human200-reception-root/statistics-input.UNFILLED.template.json',
      'assigned_design':'05-validation/human200-reception-root/assigned-design-metadata.json',
      'draw':'09-delivery/human200-independent-preparation-root/coordinator-private/draw-and-mapping.json',
      'workbook_manifest':'09-delivery/human200-independent-preparation-root/workbook-manifest.json',
      'materials':'09-delivery/human200-independent-preparation-root/material-pages-index.json',
      'blank_A':'05-validation/human200-reception-root/templates/original-blank-A.xlsx',
      'blank_B':'05-validation/human200-reception-root/templates/original-blank-B.xlsx',
      'manual':'03-manual/full4481-common-release-20261010-root/manual.txt',
      'engine':'07-statistics/prospective-engine-domain-sol/metrics_engine.py',
      'year_engine':'07-statistics/prospective-engine-year-independent-audit-sol/metrics_engine_repaired.py',
      'year_engine_contract':'07-statistics/prospective-engine-year-independent-audit-sol/input-contract-repaired.json',
      'year_engine_independent_audit':'07-statistics/prospective-engine-year-independent-audit-sol/audit.json',
      'year_descriptor':'07-statistics/annual-year-input-binding-sol/source-year-binding-descriptor.json',
      'year_accepted_main':'01-review/annual-metadata-integrated-sol/source-id-year-map.jsonl',
      'year_accepted_publication':'01-review/annual-metadata-integrated-sol/source-id-publication-year-map.jsonl',
      'year_accepted_entries':'01-review/annual-metadata-integrated-sol/source-entry-metadata.jsonl',
      'year_accepted_inventory':'01-review/annual-metadata-integrated-sol/annual-source-inventory.json',
      'year_accepted_report':'01-review/annual-metadata-integrated-sol/report.json',
      'year_accepted_seal':'01-review/annual-metadata-integrated-sol/seal.json',
      'year_prepared_full4481':'07-statistics/annual-year-input-binding-sol/full4481-year-map.jsonl',
      'year_source_date_evidence':'07-statistics/annual-year-input-binding-sol/source-entry-date-evidence.jsonl',
      'LLM_manifest':'06-coding/native-full4481-v1-sol/run-manifest.json',
      'LLM_receiver':'06-coding/native-full4481-v1-sol/receive_full4481_batch.py',
      'LLM_validator':'06-coding/native-full4481-v1-sol/validate-structured-batch.py',
      'rule_predictions':'06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl',
      'rule_freeze':'06-coding/rule-full4481-v2-root/run4481-first/freeze.json',
      'rule_seal':'06-coding/rule-full4481-v2-root/run4481-first/seal.json',
      'rule_release':'06-coding/rule-full4481-v2-root/rule-production-release.json',
      'exposure_refresh_impact':'02-methods/prospective-exposure-refresh-root/coordinator-private/historical200-new-candidate-eligibility-impact.json',
      'exposure_refresh_seal':'02-methods/prospective-exposure-refresh-root/output-seal.json',
      'exposure328':'08-audits/ai800-disagreement-semantic-root/complete-review-reception-root/future-development-exposure-overlay.json'
    }
    binds={k:h.binding(ROOT/v) for k,v in f.items()}
    draw=h.load(ROOT/f['draw'])['records'];manifest=h.load(ROOT/f['LLM_manifest'])
    descriptor=h.load(ROOT/f['year_descriptor']);report=h.load(ROOT/f['year_accepted_report'])
    h.require(report['both_maps_one_to_one_complete_unique_4481'] is True and report['fixed_frame_n']==4481,'Accepted full-frame year map not complete')
    for k,key in [('year_accepted_main','main_accepted'),('year_accepted_publication','publication_accepted'),('year_accepted_entries','source_entry_metadata'),('year_accepted_inventory','accepted_inventory'),('year_accepted_report','accepted_report'),('year_accepted_seal','accepted_seal')]:h.require(binds[k]==descriptor['source_year_maps'][key],'Different accepted year artifact')
    h.require(binds['year_prepared_full4481']=={k:v for k,v in descriptor['prepared_maps']['full4481'].items() if k!='rows'},'Different full-frame prepared year map')
    main=h.jsonlines(ROOT/f['year_accepted_main']);pub=h.jsonlines(ROOT/f['year_accepted_publication']);prepared=h.jsonlines(ROOT/f['year_prepared_full4481'])
    frame=manifest['ordered_source_ids'];h.require(len(frame)==4481 and len(set(frame))==4481,'Frozen frame must have4481 unique IDs')
    for rows in (main,pub):h.require(len(rows)==4481 and [r['source_id'] for r in rows]==frame,'Year map exact ordered full-frame join required')
    pby={r['unit_id']:r for r in prepared};mby={r['source_id']:r for r in main};sby={r['source_id']:r for r in pub}
    h.require(len(pby)==4481 and list(pby)==frame,'Prepared full-frame IDs differ')
    projected=[]
    for row in draw:
        rid=row['source_id'];m,p,s=mby[rid],pby[rid],sby[rid]
        h.require(m['id']==rid==p['source_id']==p['original_frame_id'] and m['original_id']==p['original_id'],'Source identity mapping differs')
        h.require(m['department']==row['department']==p['department'] and m['source_entry_id']==p['source_entry_id'] and m['source_entry_identity_sha256']==p['source_entry_identity_sha256'],'Source-entry/department integrity differs')
        h.require(m['policy_year']==p['policy_year'] and s['publication_year']==p['publication_year'],'Accepted date metadata differs')
        projected.append(dict(p,historical_stratum_id=row['stratum'],historical_domain=row['domain'],N_h=row['N_h'],n_h=row['n_h'],pi_exact=row['pi_exact'],weight_exact=row['weight_exact']))
    h.require(len(projected)==200 and len({r['unit_id'] for r in projected})==200,'Old200 scope differs')
    jsonl('old200-source-year-projection.jsonl',projected)
    c={'schema':'historical-human200-machine-reference-handoff-v1','snapshot_id':h.SNAPSHOT,'frozen_inputs':binds,'source_jsonl_sha256':manifest['source_jsonl']['sha256'],'frame_order_sha256':h.canonical(frame),'old_rule_algorithm_version':h.load(ROOT/f['rule_freeze'])['fixed_algorithm_version'],'year200_binding':h.binding(HERE/'old200-source-year-projection.jsonl'),'year_mapping_metadata':{k:descriptor['year_mapping_attestation'][k] for k in ('assignment_basis','sealed','frozen_before_labels','requested_years','no_source_views')},'actual_human_reference_N_at_preparation':0,'actual_machine_results_admitted_at_preparation':0,'real_statistics_runs_at_preparation':0,'updated_rule_candidate_validation_permitted':False}
    c['year_mapping_metadata']['sha256']=binds['year_accepted_main']['sha256']
    write('bindings.json',c)
    # This validates common material identity, not actual human reading/coding.
    identity=h.material_identity(c)
    ref=[]
    for bid,x in identity.items():ref.append({'blind_id':bid,'source_bundle_sha256':x['source_bundle_sha256'],'method_status':'unfilled','dimensions':{d:{'completion_status':'unfilled','value':None,'human_identity_code':None,'null_reason':None,'failure_code':None} for d in h.DIMS}})
    jsonl('reference-original.UNFILLED.template.jsonl',ref)
    write('reference-coordinator-private-mapping.json',{'records':[{'reference_blind_id':bid,**x} for bid,x in identity.items()],'actual_reference_values_created':0})
    review={'status':'UNFILLED_NOT_AN_ACTUAL_EXECUTION_REVIEW','snapshot_id':h.SNAPSHOT,'usage':'historical_frozen_snapshot_only','formal_acceptance_claimed':False,'domain_population_N':{'remaining':1444,'exposed':3037},'old_rule_prediction_binding':binds['rule_predictions'],'rule_freeze_binding':binds['rule_freeze'],'LLM_manifest_binding':binds['LLM_manifest'],'common_manual_sha256':binds['manual']['sha256'],'common_material_index_sha256':binds['materials']['sha256'],'common_source_jsonl_sha256':c['source_jsonl_sha256'],'draw_sha256':binds['draw']['sha256'],'control_or_synthetic':None,'actual_human_adjudication':None,'reference_machine_blinded':None,'reference_before_machine_comparison':None,'whole_LLM_campaign_terminal':None,'machine_snapshot_frozen_before_human_feedback':None,'AI_substitution_used':None,'A_B_agreement_used_as_reference':None,'label_based_machine_attempt_selection':None,'reference_human_identity_codes':None,'actual_user_confirmation':{'source_kind':None,'statement':None},'AB_execution_review_binding':None,'AB_original_submission_bindings':{'A':None,'B':None},'reference_original_binding':None,'LLM_terminal_inventory_binding':None}
    write('review.UNFILLED.template.json',review)
    inv={'status':'UNFILLED_NOT_A_TERMINAL_RECEPTION','all_batches_terminal':None,'reference_or_accuracy_used_in_selection':None,'run_manifest_binding':binds['LLM_manifest'],'record_N':4481,'batch_N':504,'coverage_order_sha256':c['frame_order_sha256'],'batches':[{'batch_id':b['batch_id'],'terminal_state':None,'selection_binding':None,'attempt_receipt_bindings':None,'terminal_evidence_binding':None} for b in manifest['batches']]}
    write('LLM-complete-terminal-inventory.UNFILLED.template.json',inv)
    meta=h.load(ROOT/f['statistics_template'])['metadata'];meta['scope']['frame_ids_sha256']=h.canonical(sorted(frame))
    for stage in ('machine_reference','combined'):
        active=('reference','rule','LLM') if stage=='machine_reference' else ('A','B','reference','rule','LLM')
        rows=[{'unit_id':r['source_id'],'stratum_id':r['stratum'],'department':r['department'],'outputs':{m:None for m in active}} for r in draw]
        m=dict(meta,analysis_stage=stage)
        write(stage+'.UNFILLED.template.json',{'data_role':'sealed_project','bridge_status':'UNFILLED_NOT_EXECUTED_NOT_LAWFUL_NULL','metadata':m,'records':rows})
    exposed=h.load(ROOT/f['exposure328'])['reviewed_current_source_ids'];impact=h.load(ROOT/f['exposure_refresh_impact'])
    overlap=[r for r in draw if r['source_id'] in set(exposed)];remaining=sum(r['domain']=='remaining' for r in overlap)
    h.require(len(overlap)==63 and remaining==29,'Exposure overlap differs from ROOT refresh')
    write('preparation-readback.json',{'status':'templates_and_metadata_only','old200_N':200,'assigned_slots_per_method':1000,'strata_N':len(meta['design']['strata']),'historical_domain_population_N':meta['design']['domain_population_N'],'historical_sample_by_domain':dict(Counter(r['domain'] for r in draw)),'year_projection_rows':200,'full4481_map_rows_actually_join_checked':4481,'unknown_policy_year200_N':sum(r['policy_year'] is None for r in projected),'year_by_department':dict(Counter(r['department']+'|'+str(r['policy_year']) for r in projected)),'selected800_map_read':False,'material_bytes_verified_N':400,'historical200_overlay328_overlap_N':len(overlap),'historical_remaining_overlay328_now_development_N':remaining,'future_domains_preparatory_not_registered':impact['counts']['candidate_domains'],'historical_draw_or_weights_modified':False,'source_dates_reaudited':False,'actual_human_adjudication_N':0,'actual_machine_campaign_received_N':0,'actual_statistics_runs_N':0,'actual_annual_findings_N':0,'formal_acceptance_claimed':False})
    print(json.dumps({'status':'prepared_only','old200_N':200,'actual_human_reference_N':0,'actual_machine_results_read':0,'new_draw_N':0}))

if __name__=='__main__':main()
