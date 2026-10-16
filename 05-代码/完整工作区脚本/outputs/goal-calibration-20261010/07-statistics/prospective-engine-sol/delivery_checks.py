"""Delivery/CLI provenance checks on only this explicitly synthetic delivery."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
import metrics_engine as e
HERE=Path(__file__).resolve().parent
def main():
    cli=json.loads((HERE/'synthetic-cli-output.json').read_text())
    api=json.loads((HERE/'synthetic-toy-output.json').read_text())
    environment=json.loads((HERE/'execution-environment.json').read_text())
    contract=json.loads((HERE/'future-input-template.json').read_text())['metadata']['statistical_contract_binding']
    checks={
        'CLI_synthetic_role':cli['data_role']=='synthetic',
        'CLI_engine_hash_current':cli['execution_provenance']['engine_sha256']==e.sha256(HERE/'metrics_engine.py'),
        'CLI_input_hash_current':cli['execution_provenance']['input_sha256']==e.sha256(HERE/'synthetic-toy-input.json'),
        'CLI_fixed_parameters':cli['design']['bootstrap_replicates']==5000 and cli['design']['seed']==20261010,
        'CLI_numeric_targets_match_API':cli['numeric_targets']==api['numeric_targets'],
        'CLI_never_formal_acceptance':cli['project_review']['formal_acceptance'] is False,
        'QA_engine_hash_current':json.loads((HERE/'engine-QA.json').read_text())['engine_sha256']==e.sha256(HERE/'metrics_engine.py'),
        'unknown_policy_snapshot_bound':e.sha256(HERE/'inputs'/'unknown-and-denominator-policy.json')==json.loads((HERE/'execution-environment.json').read_text())['unknown_policy']['sha256'],
        'v2_contract_snapshot_bound':e.sha256(HERE/'inputs'/'validation-design-v2.json')==environment['statistical_contract_v2']['sha256'],
        'v2_contract_method_note_snapshot_bound':e.sha256(HERE/'inputs'/'统计契约说明与勘误.md')==environment['statistical_contract_v2']['method_note_sha256'],
        'CLI_main_interval_parameters_match_v2_choice':cli['design']['bootstrap_replicates']==contract['replicates']==5000 and cli['design']['seed']==contract['seed']==20261010,
    }
    for name,comp in cli['comparisons'].items():
        for domain,dimensions in comp['domains'].items():
            for dim,row in dimensions.items():
                other=api['comparisons'][name]['domains'][domain][dim]
                checks[f'CLI_point_and_tables_{name}_{domain}_{dim}']=all(row[k]==other[k] for k in ('raw','design_weighted','raw_metrics','design_weighted_metrics','weighted_four_exact_fractions'))
    try:e.prepare(json.loads((HERE/'future-input-template.json').read_text()))
    except e.DataError:checks['unfilled_unsealed_future_template_rejected']=True
    else:checks['unfilled_unsealed_future_template_rejected']=False
    if not all(checks.values()):raise AssertionError({k:v for k,v in checks.items() if not v})
    out={'status':'passed','recorded_at_UTC':datetime.now(timezone.utc).isoformat(),
         'check_count':len(checks),'checks':checks,'engine_sha256':e.sha256(HERE/'metrics_engine.py'),
         'CLI_output_sha256':e.sha256(HERE/'synthetic-cli-output.json'),
         'real_project_labels_or_text_read':False,'scope':'synthetic CLI serialization, point tables and provenance only'}
    (HERE/'CLI-QA.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'passed','check_count':len(checks)}))
if __name__=='__main__':main()
