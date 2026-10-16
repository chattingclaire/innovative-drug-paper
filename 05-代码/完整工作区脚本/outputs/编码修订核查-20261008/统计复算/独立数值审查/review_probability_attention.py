"""Independent same180 attention and paired differences, fixed replicates only."""
from pathlib import Path
from itertools import combinations
import argparse,json,datetime
import numpy as np
import independent_numeric_core as n
import independent_resampling_core as b
from review_full4481 import Audit,leaves

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药');HERE=Path(__file__).resolve().parent
RULE='rules-v39';LLM='LLM-candidate03-single-unit-reconciled'

def qarray(hits):
    den=hits.sum(axis=1)
    return np.divide(hits,den[:,None],out=np.full_like(hits,np.nan),where=den[:,None]>0)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--author',type=Path,required=True);ap.add_argument('--author-sha256',required=True)
    ap.add_argument('--report',type=Path,required=True);args=ap.parse_args();assert not args.report.exists()
    audit=Audit();prep=audit.read(HERE/'independent_review_preparation.json');sources=prep['source_bindings_hash_checked']
    for leaf in leaves(sources):audit.bind(leaf['path'],leaf['sha256'])
    target=audit.read(args.author,args.author_sha256);assert not audit.failures
    design={r['original_id']:r for r in audit.read(sources['sampling_design']['path'])['sample']}
    metadata={Path(r['original_file']).stem:r for r in audit.read(sources['metadata']['path'])['rows']}
    material=n.material_metadata_only(sources['material_rule_inputs']['path'],metadata)
    rows={name:n.label_only_jsonl(spec['path']) for name,spec in sources['references'].items()}
    rows['candidate']=n.label_only_jsonl(sources['candidate_reference_existing']['path'])
    rows[RULE]=n.machine_numeric_jsonl(sources['rule39']['path'])[0]
    rows[LLM]=n.machine_numeric_jsonl(sources['original_LLM03']['path'])[0]
    idsall=n.scope_ids(design,'probability_canonical','ALL');assert len(idsall)==180
    assert all(n.binary(v[d]) for r in rows.values() for rid,v in r.items() if rid in idsall for d in n.DIMS)
    scopes=[(g,w) for c,g,w in n.SCOPES if c=='probability_canonical'];assert len(scopes)==8
    methods=set(rows)
    wanted={(g,w,name) for g,w in scopes for name in rows}
    actual={(r['group'],r['weighting'],r['method']) for r in target['profiles']}
    audit.compare(wanted==actual,True,'same180/profile_grid','grid');assert len(target['profiles'])==40
    factor_cache={};boot_cache={};points={};records=[];profiles=[]
    def factors(group,ids,mechanism):
        key=(group,tuple(ids),mechanism)
        if key not in factor_cache:
            factor_cache[key],record=b.resampling_factors(ids,design,material,'probability_canonical',mechanism)
            records.append({'group':group,**record})
        return factor_cache[key]
    def boot(group,weighting,name,mechanism):
        key=(group,weighting,name,mechanism)
        if key not in boot_cache:
            ids=n.scope_ids(design,'probability_canonical',group)
            hit=np.asarray([[rows[name][rid][d] for d in n.DIMS] for rid in ids],float)
            weights=np.asarray([float(n.design_weight(design,rid,weighting)) for rid in ids])
            boot_cache[key]=qarray((factors(group,ids,mechanism)*weights)@hit)
        return boot_cache[key]
    for r in target['profiles']:
        group,weighting,name=r['group'],r['weighting'],r['method'];ids=n.scope_ids(design,'probability_canonical',group)
        weights={rid:n.design_weight(design,rid,weighting) for rid in ids}
        p=n.profile(rows[name],ids,weights);points[group,weighting,name]=p
        prefix='/'.join((group,weighting,name))
        expected={'component':'probability_canonical','unit_frame_n':len(ids),'complete_support_n':len(ids),
         'excluded_pending_or_common_support_n':0,'full_frame_attention_share_defined':True,
         'weighted_five_dimension_coding_count_on_support':p['five_dimension_coding_count'],
         'primary_bootstrap_mechanism':'department_unit_rescaled_SRSWOR'}
        audit.compare(expected,r,prefix,'same180_profile')
        audit.compare(r['complete_support_ids']==ids,True,prefix+'/complete_ID_support_equal','metadata_sets')
        for j,d in enumerate(n.DIMS):
            raw_count=sum(rows[name][rid][d] for rid in ids);q=p['attention_share'][d]
            e={'weighted_known_coding_count':p['coding_count'][d],'raw_known_coding_count':raw_count,
             'pending_n':0,'weighted_pending_count':0,'attention_share':q,
             'attention_share_missing_label_bounds':{'low':q,'high':q},
             'attention_share_on_common_complete_support':{'estimate':q,
              'ci95_primary':b.percentile_interval(boot(group,weighting,name,'department_unit_rescaled_SRSWOR')[:,j]),
              'ci95_source_file_conditional_sensitivity':b.percentile_interval(boot(group,weighting,name,'department_source_file_conditional_WR')[:,j])},
             'known_label_hit_rate_diagnostic':p['coverage'][d]}
            audit.compare(e,r['dimensions'][d],prefix+'/'+d,'same180_point_CI')
        profiles.append({'group':group,'weighting':weighting,'method':name,'profile':n.pack(p)})
    pairnames=[(RULE,'A'),(RULE,'C'),(RULE,'candidate'),(LLM,'A'),(LLM,'C'),(LLM,'candidate'),(RULE,LLM),('A','C')]
    pairgrid={(g,w,a,c) for g,w in scopes for a,c in pairnames}
    actualgrid={(r['group'],r['weighting'],r['method_one'],r['method_two']) for r in target['paired_method_differences']}
    audit.compare(pairgrid==actualgrid,True,'paired64/grid','grid');assert len(target['paired_method_differences'])==64
    paired=[]
    for r in target['paired_method_differences']:
        group,w,a,c=r['group'],r['weighting'],r['method_one'],r['method_two'];ids=n.scope_ids(design,'probability_canonical',group)
        audit.compare({'difference_direction':'method_one_minus_method_two','complete_support_n':len(ids),
         'excluded_pending_or_common_support_n':0,'primary_bootstrap_mechanism':'department_unit_rescaled_SRSWOR'},r,'paired64/meta','same180_paired')
        out={}
        for j,d in enumerate(n.DIMS):
            x,y=points[group,w,a]['attention_share'][d],points[group,w,c]['attention_share'][d]
            q={'estimate':x-y if x is not None and y is not None else None,
             'ci95_primary':b.percentile_interval(boot(group,w,a,'department_unit_rescaled_SRSWOR')[:,j]-boot(group,w,c,'department_unit_rescaled_SRSWOR')[:,j])}
            audit.compare(q,r['dimensions'][d],'paired64/'+group+'/'+w+'/'+a+'/'+c+'/'+d,'same180_paired');out[d]=q
        paired.append({'group':group,'weighting':w,'method_one':a,'method_two':c,'dimensions':n.pack(out)})
    deptgrid={(name,a,c) for name in rows for a,c in combinations(n.GROUPS,2)}
    actualgrid={(r['method'],r['department_one'],r['department_two']) for r in target['department_differences']}
    audit.compare(deptgrid==actualgrid,True,'department15/grid','grid');assert len(target['department_differences'])==15
    full_factors=factors('ALL',idsall,'department_unit_rescaled_SRSWOR')
    dept_boot={}
    weights=np.asarray([float(n.design_weight(design,rid,'eligible_design_weighted')) for rid in idsall])
    for name,labels in rows.items():
        hits=np.asarray([[labels[rid][d] for d in n.DIMS] for rid in idsall],float)
        for g in n.GROUPS:
            mask=np.asarray([design[rid]['group']==g for rid in idsall])
            dept_boot[name,g]=qarray((full_factors[:,mask]*weights[mask])@hits[mask])
    department=[]
    for r in target['department_differences']:
        name,a,c=r['method'],r['department_one'],r['department_two'];out={}
        audit.compare({'difference_direction':'department_one_minus_department_two','primary_bootstrap_mechanism':'department_unit_rescaled_SRSWOR','unit_frame_n_per_department':60},r,'department15/meta','same180_department')
        for j,d in enumerate(n.DIMS):
            x,y=points[a,'unweighted',name]['attention_share'][d],points[c,'unweighted',name]['attention_share'][d]
            q={'difference_percentage_points':100*(x-y) if x is not None and y is not None else None,
             'ci95_percentage_points':b.percentile_interval(100*(dept_boot[name,a][:,j]-dept_boot[name,c][:,j]))}
            audit.compare(q,r['dimensions'][d],'department15/'+name+'/'+a+'/'+c+'/'+d,'same180_department');out[d]=q
        department.append({'method':name,'department_one':a,'department_two':c,'dimensions':n.pack(out)})
    for p,h in audit.bindings.items():audit.compare(h,n.sha(p),p+'/unchanged','read_only')
    report={'status':'PASS_INDEPENDENT_NUMERIC_CHECKS' if not audit.failures else 'FAIL_RETAINED',
     'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':dict(audit.counts),'failures':audit.failures,
     'same_probability_n':180,'profiles_n':40,'paired_method_differences_n':64,'department_differences_n':15,
     'profiles':profiles,'paired_method_differences':paired,'department_differences':department,
     'fixed_resampling_records':records,'source_bindings':audit.bindings,'source_files_modified':False,
     'author_statistical_functions_imported':False,'new_model_or_classifier_calls':0,
     'CI_coverage_or_label_truth_validity':'NOT_ESTABLISHED',
     'scope':'Original probability180 only; does not pool challenge60 or imply all4481 population performance. C displayed B; T remains AI.',
     'no_individual_reserved_text_predictions_or_reference_labels_displayed':True,'script_sha256':n.sha(__file__)}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':report['status'],'report':str(args.report),'sha256':n.sha(args.report),'failure_n':len(audit.failures),'checks':dict(audit.counts)},ensure_ascii=False))

if __name__=='__main__':main()
