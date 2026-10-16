"""Check200 design denominators and refusal of an unfilled real analysis."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path
import numpy as np

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
ENGINE=ROOT/'07-statistics/prospective-engine-domain-sol/metrics_engine.py'


def main():
    b=json.loads((HERE/'bindings.json').read_text())
    expected=next(x for x in b['source_helpers'] if x['path']==str(ENGINE))
    raw=ENGINE.read_bytes()
    if len(raw)!=expected['bytes'] or hashlib.sha256(raw).hexdigest()!=expected['sha256']:raise ValueError('Engine binding changed')
    spec=importlib.util.spec_from_file_location('_registered200_design_only_engine',ENGINE)
    engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
    m=json.loads((HERE/'assigned-design-metadata.json').read_text())
    rows=m['records'];design=m['design']
    payload={'data_role':'synthetic','metadata':{'analysis_stage':'human_first','design':design,
        'scope':{'kind':'full_4481_audit','population_N':4481}},
        'records':[{'unit_id':r['source_id'],'stratum_id':r['stratum'],'department':r['department'],'outputs':{}} for r in rows]}
    # Synthetic role is an in-memory metadata parser device; no labels exist.
    prepared=engine.prepare(payload)
    W=engine.rao_wu_weights(prepared,replicates=5000,seed=20261010)
    if W.shape!=(5000,200) or not np.isfinite(W).all():raise ValueError('New design weight shape/finite failure')
    denominators={}
    for domain,N in [('ALL',4481),('remaining',1444),('exposed',3037)]:
        mask=np.ones(200,dtype=bool) if domain=='ALL' else prepared['unit_domains']==domain
        sums=W@mask.astype(float)
        error=float(np.max(np.abs(sums-N)))
        if error>1e-8:raise ValueError('New design domain denominator mismatch')
        denominators[domain]={'assigned_n':int(mask.sum()),'population_N':N,'max_float_error':error}
    template=json.loads((HERE/'statistics-input.UNFILLED.template.json').read_text())
    refused=None
    try:engine.prepare(template)
    except ValueError as e:refused=str(e)
    if refused is None:raise ValueError('Unfilled real-analysis template must be refused before statistics')
    report={'status':'new200_sampling_weights_verified_unfilled_analysis_refused','engine_binding':expected,
        'python_executable':sys.executable,
        'W_shape':list(W.shape),'W_sha256':hashlib.sha256(np.ascontiguousarray(W).tobytes()).hexdigest(),
        'replicates':5000,'bootstrap_seed':20261010,'bootstrap_seed_not_sampling_seed':True,
        'domain_denominators':denominators,'unfilled_real_template_refusal':refused,
        'analyze_called':False,'actual_human_label_values_read':0,'numerical_accuracy_or_CI_results_generated':0,
        'human_validation_complete':False,'sample_size_sufficiency_claimed':False}
    target=HERE/'checks/design200-weight-and-admission-guards.json'
    with target.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':report['status'],'W_shape':report['W_shape'],'domain_denominators':denominators,
        'accuracy_or_CI_results_generated':0},ensure_ascii=False))


if __name__=='__main__':main()
