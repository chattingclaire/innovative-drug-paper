"""After actual frozen statistics arrive: independently check all420 and primary CIs.

Only local independent analytical modules are imported. No author metric function.
"""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter
import argparse,json,datetime,math,hashlib
import independent_numeric_core as n
import independent_resampling_core as b

ROOT=Path('/PROJECT_ROOT')
HERE=Path(__file__).resolve().parent
KEYS=('component','group','weighting','method','reference','dimension')
RULE='rules-v39';LLM='LLM-candidate03-single-unit-reconciled'

class Audit:
    def __init__(self):self.checks=Counter();self.failures=[];self.bindings={}
    def check(self,wanted,actual,where,kind='numeric'):
        self.checks[kind]+=1
        if isinstance(wanted,Q):wanted=float(wanted)
        if wanted is None:ok=actual is None
        elif type(wanted) in (int,float):ok=type(actual) in (int,float) and math.isfinite(actual) and math.isclose(wanted,actual,rel_tol=1e-12,abs_tol=1e-12)
        else:ok=wanted==actual
        if not ok:self.failures.append({'where':where,'independent':wanted,'actual':actual})
    def bind(self,p,expected=None):
        p=Path(p);h=n.sha(p)
        if expected is not None:self.check(expected,h,str(p),'sha')
        self.bindings[str(p)]=h;return p
    def read(self,p):return json.loads(self.bind(p).read_text())

def leaves(x):
    if isinstance(x,dict):
        if 'path'in x and 'sha256'in x:yield x
        else:
            for v in x.values():yield from leaves(v)
    elif isinstance(x,list):
        for v in x:yield from leaves(v)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--author-directory',type=Path,required=True)
    ap.add_argument('--author-freeze',type=Path,required=True);ap.add_argument('--author-freeze-sha256',required=True)
    ap.add_argument('--report',type=Path,required=True);ap.add_argument('--skip-ci',action='store_true')
    args=ap.parse_args();assert not args.report.exists(),'Never overwrite a completed/failed review'
    audit=Audit();prep=audit.read(HERE/'independent_review_preparation.json')
    sources=prep['source_bindings_hash_checked']
    for leaf in leaves(sources):audit.bind(leaf['path'],leaf['sha256'])
    for p,h in prep['entry_files'].items():audit.bind(p,h)
    audit.bind(args.author_freeze,args.author_freeze_sha256)
    # Output freeze variants may have path+sha leaves or a relative files mapping.
    frozen=json.loads(args.author_freeze.read_text())
    for leaf in leaves(frozen):audit.bind(leaf['path'],leaf['sha256'])
    if isinstance(frozen.get('files'),dict):
        for rel,h in frozen['files'].items():
            if isinstance(h,str):audit.bind(args.author_directory/rel,h)
    assert not audit.failures,'Binding failed before individual labels are loaded'
    design_data=audit.read(sources['sampling_design']['path'])
    design={r['original_id']:r for r in design_data['sample']};assert len(design)==240
    assert design_data['frame_N_by_group']=={'NMPA':947,'NHSA':760,'NHC':60}
    assert Counter((r['component'],r['group']) for r in design.values())==Counter({
      ('probability_canonical','NMPA'):60,('probability_canonical','NHSA'):60,('probability_canonical','NHC'):60,
      ('enriched_challenge','NMPA'):30,('enriched_challenge','NHSA'):30})
    for rid,row in design.items():
        if row['component']=='probability_canonical':
            assert row['sample_n']==60
            audit.check(Q(row['sample_n'],row['canonical_frame_N']),row['inclusion_probability'],'design/pi','design')
            audit.check(n.design_weight(design,rid,'eligible_design_weighted'),row['analysis_weight'],'design/weight','design')
        else:audit.check(None,row['analysis_weight'],'challenge/no_design_weight','design')
    metadata={Path(r['original_file']).stem:r for r in audit.read(sources['metadata']['path'])['rows']}
    material=n.material_metadata_only(sources['material_rule_inputs']['path'],metadata)
    assert len(material)==4924
    assert Counter(r['group'] for r in material.values())==Counter({'NMPA':1848,'NHSA':2100,'NHC':533,'GOV':443})
    for rid,row in design.items():assert row['group']==material[rid]['group']
    methods={RULE:n.machine_numeric_jsonl(sources['rule39']['path'])[0],LLM:n.machine_numeric_jsonl(sources['original_LLM03']['path'])[0]}
    assert all(len(x)==4924 and set(x)==set(material) for x in methods.values())
    refs={name:n.label_only_jsonl(spec['path']) for name,spec in sources['references'].items()}
    refs['candidate']=n.label_only_jsonl(sources['candidate_reference_existing']['path'])
    assert all(set(x)==set(design) for x in refs.values())
    assert all(n.binary(v) for rows in refs.values() for row in rows.values() for v in row.values())
    third=n.label_only_jsonl(sources['T66_existing_merged']['path'])
    policy=audit.read(sources['T_resolution_policy']['path'])
    assert policy['resolution_policy']=='third_for_every_reviewed_dimension'
    assert set(third)==set(policy['mixed_original_id_order']) and len(third)==66
    # Independently reconstruct the declared all-dimensions policy, including
    # T's preselected agreement-QC cases. Never display individual reference values.
    candidate_mismatch=0
    for rid in design:
        if rid in third:target=third[rid]
        else:
            assert refs['A'][rid]==refs['C'][rid]
            target=refs['A'][rid]
        candidate_mismatch+=sum(refs['candidate'][rid][d]!=target[d] for d in n.DIMS)
    audit.check(0,candidate_mismatch,'candidate_reference/policy_dimension_mismatch_n','reference_policy')
    author_machine=audit.read(args.author_directory/'machine_reference_classification.json')['comparisons']
    ac_name='A_C_before_third_agreement.json'
    if not (args.author_directory/ac_name).exists():ac_name='A_C_final_before_third_agreement.json'
    author_ac=audit.read(args.author_directory/ac_name)['comparisons']
    published=author_machine+author_ac
    computed=n.all420(methods,refs,design)
    lookup={tuple(r[k] for k in KEYS):r for r in published}
    audit.check(420,len(published),'420/source_n','grid');audit.check(420,len(lookup),'420/unique_keys','grid')
    audit.check(set(tuple(r[k] for k in KEYS) for r in computed),set(lookup),'420/key_grid','grid')
    assert not audit.failures,'Source/grid mismatch before arithmetic comparison'
    factors={};factor_records=[];safe=[];primary80=[]
    for row in computed:
        key=tuple(row[k] for k in KEYS);target=lookup[key];prefix='/'.join(map(str,key));symmetric=row['method']=='A_C'
        for field in ('unit_frame_n','paired_n','excluded_pending_n','left_positive_n','reference_positive_n'):
            audit.check(row[field],target[field],prefix+'/'+field,'counts')
        for field in ('paired_ids','excluded_ids'):
            audit.check(row[field]==target[field],True,prefix+'/'+field+'_mechanical_equality','ID_sets')
        cell_names=('A1_C1','A1_C0','A0_C1','A0_C0') if symmetric else n.CELLS
        for field,targetfield in [('raw_confusion','symmetric_raw_cells' if symmetric else 'raw_confusion'),('weighted_confusion','symmetric_weighted_cells' if symmetric else 'weighted_confusion')]:
            for k,tk in zip(n.CELLS,cell_names):audit.check(row[field][k],target[targetfield][tk],prefix+'/'+targetfield+'/'+tk,'four_cells')
        audit.check(set(row['metrics']),set(target['metrics']),prefix+'/metric_names','grid')
        for metric,value in row['metrics'].items():audit.check(value,target['metrics'][metric]['estimate'],prefix+'/'+metric,'point')
        component,group,weighting=key[:3];ids=n.scope_ids(design,component,group)
        mechanism=('department_unit_rescaled_SRSWOR' if component=='probability_canonical' else 'department_unit_conditional_WR') if ids else None
        audit.check(mechanism,target['primary_bootstrap_mechanism'],prefix+'/primary_mechanism','CI_mechanism')
        cluster_counts={g:len({material[rid]['source'] for rid in ids if design[rid]['group']==g}) for g in n.GROUPS}
        if ids:
            audit.check(cluster_counts,target['source_file_clusters_by_department'],prefix+'/source_file_clusters','CI_mechanism')
        else:
            audit.check(True,target.get('absent_stratum'),prefix+'/absent_stratum','absent_stratum')
            audit.check(('enriched_challenge','NHC'),(component,group),prefix+'/absent_scope','absent_stratum')
            audit.check(False,'source_file_clusters_by_department' in target,prefix+'/no_attempted_clusters','absent_stratum')
            for metric in row['metrics']:
                for field in ('ci95_primary','ci95_source_file_conditional_sensitivity'):
                    expected={'low':None,'high':None,'defined_repetitions':0,'undefined_repetitions':0,
                              'not_run_reason':'no NHC challenge sample; no repetitions attempted'}
                    audit.check(expected,target['metrics'][metric][field],prefix+'/'+metric+'/'+field,'absent_stratum')
        if ids and not args.skip_ci:
            left=refs['A'] if symmetric else methods[row['method']]
            right=refs['C'] if symmetric else refs[row['reference']]
            weights=[float(n.design_weight(design,rid,weighting)) for rid in ids]
            for mech,field in [(mechanism,'ci95_primary'),('department_source_file_conditional_WR','ci95_source_file_conditional_sensitivity')]:
                cache_key=(component,group,mech,tuple(ids))
                if cache_key not in factors:
                    factors[cache_key],record=b.resampling_factors(ids,design,material,component,mech)
                    factor_records.append({'component':component,'group':group,**record})
                reproduced=b.fixed_comparison_intervals(left,right,row['dimension'],ids,weights,factors[cache_key])
                for metric in row['metrics']:
                    for ci_key,value in reproduced[metric].items():audit.check(value,target['metrics'][metric][field][ci_key],prefix+'/'+metric+'/'+field+'/'+ci_key,'CI_fixed_reproduction')
        numeric={k:v for k,v in row.items() if k not in ('paired_ids','excluded_ids')}
        safe.append(n.pack(numeric))
        if component=='probability_canonical' and group=='ALL' and weighting=='eligible_design_weighted' and row['method'] in methods and row['reference'] in ('A','C'):
            primary80.append({k:row[k] for k in KEYS}|{'four_cells':n.pack(row['weighted_confusion']),
              'metrics':n.pack({k:row['metrics'][k] for k in ('kappa','precision','recall','f1')}),
              'display_three_decimals':{k:format(float(row['metrics'][k]),'.3f') if row['metrics'][k] is not None else 'NA' for k in ('kappa','precision','recall','f1')}})
    assert len(primary80)==20
    for p,h in audit.bindings.items():audit.check(h,n.sha(p),p+'/unchanged','read_only')
    report={'status':'PASS_INDEPENDENT_NUMERIC_CHECKS' if not audit.failures else 'FAIL_RETAINED',
     'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
     'scope':'All420 comparison records from original probability180 and separate challenge60; labels fixed; C display alias B.',
     'checks':dict(audit.checks),'failures':audit.failures,'comparison_n':420,'independently_recomputed_420':safe,
     'independent_primary80':n.pack(primary80),'candidate_reference_policy_dimension_mismatch_n':candidate_mismatch,
     'fixed_resampling_records':factor_records,'CI_fixed_reproduction':'NOT_RUN' if args.skip_ci else 'PASS' if not audit.failures else 'SEE_FAILURES',
     'CI_coverage_or_semantic_truth_validity':'NOT_ESTABLISHED','source_bindings':audit.bindings,
     'author_statistical_functions_imported':False,'new_classifier_or_model_calls':0,'source_files_modified':False,
     'no_individual_reserved_text_predictions_or_reference_labels_displayed':True,
     'identity':'Original A/C AI submissions retrospectively reviewed by user without edits; T AI review. Not new independent blind human labels.',
     'script_sha256':n.sha(__file__)}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':report['status'],'report':str(args.report),'sha256':n.sha(args.report),'failure_n':len(audit.failures),'comparison_n':420,'checks':dict(audit.checks)},ensure_ascii=False))

if __name__=='__main__':main()
