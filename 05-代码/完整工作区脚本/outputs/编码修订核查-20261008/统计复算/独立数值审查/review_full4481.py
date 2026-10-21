"""Independent full-corpus and sensitivity numerical review, aggregate only."""
from pathlib import Path
from fractions import Fraction as Q
from itertools import combinations
from collections import Counter
import argparse,json,datetime,math,hashlib
import numpy as np
import independent_numeric_core as n
import independent_resampling_core as b

ROOT=Path('/PROJECT_ROOT');HERE=Path(__file__).resolve().parent
RULE='rules-v39';LLM='LLM-candidate03-single-unit-reconciled'
DEFS=('primary','exclude_quality_only_S','exclude_qualification_only_I','exclude_clinical_management_only_F','exclude_dimension_information_only_F','retain_access_affordability_F')

class Audit:
    def __init__(self):self.counts=Counter();self.failures=[];self.bindings={}
    def compare(self,expected,actual,path,kind='point'):
        self.counts[kind]+=1
        if isinstance(expected,dict):
            if not isinstance(actual,dict) or not set(expected)<=set(actual):
                self.failures.append({'where':path,'issue':'missing expected object keys'});return
            for k,v in expected.items():self.compare(v,actual[k],path+'/'+str(k),kind)
            return
        if isinstance(expected,(list,tuple)):
            if not isinstance(actual,(list,tuple)) or len(expected)!=len(actual):
                self.failures.append({'where':path,'issue':'sequence length mismatch'});return
            if path.endswith(('/zero_a_clusters_excluded','/zero_b_clusters_excluded')):expected,actual=sorted(expected),sorted(actual)
            for i,(x,y) in enumerate(zip(expected,actual)):self.compare(x,y,path+'/'+str(i),kind)
            return
        if expected is None:ok=actual is None
        elif isinstance(expected,(int,float,Q)) and not isinstance(expected,bool):ok=type(actual) in (int,float) and math.isfinite(actual) and math.isclose(float(expected),actual,rel_tol=1e-12,abs_tol=1e-12)
        else:ok=expected==actual
        if not ok:self.failures.append({'where':path,'independent':float(expected) if isinstance(expected,Q) else expected,'actual':actual})
    def bind(self,path,expected=None):
        p=Path(path);h=n.sha(p)
        if expected:self.compare(expected,h,str(p),'sha')
        self.bindings[str(p)]=h;return p
    def read(self,path,expected=None):return json.loads(self.bind(path,expected).read_text())

def leaves(x):
    if isinstance(x,dict):
        if 'path'in x and 'sha256'in x:yield x
        else:
            for v in x.values():yield from leaves(v)

def contrasts(deps):
    vals={}
    for metric,key in [('P_F_given_Ec','p_b_given_a'),('P_Ec_given_F','p_a_given_b'),('OR','OR')]:
        values=[next(p for p in deps[g]['all10_pairs'] if (p['dimension_a'],p['dimension_b'])==('Ec','F'))[key] for g in ('NHSA','NHC')]
        vals[metric]=values
    for kind in ('attention_share','coverage'):
        for d in n.DIMS:vals[kind+'_'+d]=[deps[g]['profile'][kind][d] for g in ('NHSA','NHC')]
    return {k:{'NHSA':x,'NHC':y,'NHSA_minus_NHC':x-y if x is not None and y is not None else None} for k,(x,y) in vals.items()}

def data(labels,scope,material,metadata,cluster=None):
    deps=n.group_findings(labels,scope,material,metadata,cluster)
    return {'departments':deps,'contrasts':contrasts(deps)}

def conditional(record,group,condition,cooccurring):
    a,c=sorted((condition,cooccurring),key=n.DIMS.index)
    pair=next(p for p in record['departments'][group]['all10_pairs'] if (p['dimension_a'],p['dimension_b'])==(a,c))
    return pair['p_b_given_a'] if condition==a else pair['p_a_given_b']

def range_summary(values):
    defined=[v for v in values if v is not None]
    return {'scenario_n':len(values),'one_higher_n':sum(float(v)>1e-12 for v in defined),
     'two_higher_n':sum(float(v)<-1e-12 for v in defined),'equal_n':sum(abs(float(v))<=1e-12 for v in defined),
     'undefined_n':len(values)-len(defined),
     'difference_percentage_point_range':[100*min(defined),100*max(defined)] if defined else None}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--findings',type=Path,required=True);ap.add_argument('--findings-sha256',required=True)
    ap.add_argument('--attention',type=Path,required=True);ap.add_argument('--attention-sha256',required=True)
    ap.add_argument('--conditional-details',type=Path);ap.add_argument('--conditional-details-sha256')
    ap.add_argument('--report',type=Path,required=True);args=ap.parse_args()
    assert not args.report.exists(),'Never overwrite a completed/failed independent audit'
    audit=Audit();prep=audit.read(HERE/'independent_review_preparation.json');sources=prep['source_bindings_hash_checked']
    for leaf in leaves(sources):audit.bind(leaf['path'],leaf['sha256'])
    for p,h in prep['entry_files'].items():audit.bind(p,h)
    findings=audit.read(args.findings,args.findings_sha256);attention=audit.read(args.attention,args.attention_sha256)
    details=audit.read(args.conditional_details,args.conditional_details_sha256) if args.conditional_details else None
    assert not audit.failures,'Hash mismatch before computing any labels'
    metadata={Path(r['original_file']).stem:r for r in audit.read(sources['metadata']['path'])['rows']}
    material=n.material_metadata_only(sources['material_rule_inputs']['path'],metadata)
    design={r['original_id']:r for r in audit.read(sources['sampling_design']['path'])['sample']}
    raw={};subtypes={}
    for name,source in [(RULE,sources['rule39']),(LLM,sources['original_LLM03'])]:
        raw[name],subtypes[name],hashes=n.machine_numeric_jsonl(source['path'])
        assert len(raw[name])==4924 and set(raw[name])==set(material)
        for rid,h in hashes.items():
            if h is not None:assert h==material[rid]['unit_text_sha256']
    fullscope={g:sorted(rid for rid,m in material.items() if m['group']==g) for g in n.GROUPS}
    probability={g:n.scope_ids(design,'probability_canonical',g) for g in n.GROUPS}
    assert [len(fullscope[g]) for g in n.GROUPS]==[1848,2100,533]
    assert [len(probability[g]) for g in n.GROUPS]==[60,60,60]
    primary={k:data(v,fullscope,material,metadata) for k,v in raw.items()}
    same180={k:data(v,probability,material,metadata) for k,v in raw.items()}
    for name in raw:
        audit.compare(primary[name],findings['primary_full4481'][name],'primary/'+name)
        audit.compare(same180[name],findings['same180_primary'][name],'same180/'+name)
        role='rules' if name==RULE else 'LLM'
        for g in n.GROUPS:
            target=attention['primary'][role][g]
            audit.compare({k:v for k,v in primary[name]['departments'][g]['profile'].items() if k in target},target,'attention-primary/'+role+'/'+g)
    audit.compare(list(DEFS),[r['scenario'] for r in findings['definition6']],'six_definitions/order','scope')
    definition_records=[];removals={}
    for sc,target in zip(DEFS,findings['definition6']):
        current={}
        for name,original in raw.items():
            derived={rid:dict(v) for rid,v in original.items()};removed=[]
            for rid,sub in subtypes[name].items():
                it=set(sub['innovation_subtypes'] or []);ft=set(sub['fairness_subtypes'] or []);drop=None
                if sc=='exclude_quality_only_S' and sub['safety_quality_basis']=='quality_only':drop='S'
                elif sc=='exclude_qualification_only_I' and it=={'qualification_advantage'}:drop='I'
                elif sc=='exclude_clinical_management_only_F' and ft=={'clinical_management'}:drop='F'
                elif sc=='exclude_dimension_information_only_F' and ft=={'dimension_information'}:drop='F'
                elif sc=='retain_access_affordability_F' and not ft&{'access','affordability'}:drop='F'
                if drop and derived[rid][drop]:derived[rid][drop]=0;removed.append((rid,drop))
            removed_counts={g:{d:sum(material[rid]['group']==g and dim==d for rid,dim in removed) for d in n.DIMS} for g in n.GROUPS}
            t=target['methods'][name]
            audit.compare(removed_counts,t['removed_labels_by_group_dimension'],'definition/'+sc+'/'+name+'/removed','definition')
            audit.compare(set(removed)=={(r['id'],r['dimension']) for r in t['removed_labels']},True,'definition/'+sc+'/'+name+'/removed_ID_set_equal','metadata_sets')
            x=data(derived,fullscope,material,metadata);small=data(derived,probability,material,metadata)
            audit.compare(x,t['full4481'],'definition/'+sc+'/'+name+'/full','definition')
            audit.compare(small,t['same180'],'definition/'+sc+'/'+name+'/same180','definition')
            current[name]=x;removals[sc+'/'+name]=removed_counts
        definition_records.append(current)
    stems=sorted({material[r]['stem'] for ids in fullscope.values() for r in ids});assert len(stems)==51
    latest={}
    for stem in stems:
        m=metadata[stem]
        if m['annual_series']:latest[m['policy_series']]=max(latest.get(m['policy_series'],m['year_in_filename']),m['year_in_filename'])
    cases=[(s,None) for s in ('primary','policy_file_equal','policy_series_equal','latest_annual_series_member','exclude_joint_publications')]+[('leave_one_policy_entry_out',stem) for stem in stems]
    assert len(cases)==56
    audit.compare(cases,[(r['scenario'],r['omitted_policy_entry']) for r in findings['composition56']],'composition56/identity','scope')
    composition_records=[];scope_counts=[]
    for i,(sc,omit) in enumerate(cases):
        scope={g:[rid for rid in fullscope[g] if material[rid]['stem']!=omit and not(sc=='exclude_joint_publications' and metadata[material[rid]['stem']]['joint_publication']) and not(sc=='latest_annual_series_member' and metadata[material[rid]['stem']]['annual_series'] and metadata[material[rid]['stem']]['year_in_filename']!=latest[metadata[material[rid]['stem']]['policy_series']])] for g in n.GROUPS}
        t=findings['composition56'][i]
        audit.compare(all(set(scope[g])==set(t['scope_ids'][g]) for g in n.GROUPS),True,'composition/'+str(i)+'/scope_ID_sets_equal','metadata_sets')
        cluster='policy_file' if sc=='policy_file_equal' else 'policy_series' if sc=='policy_series_equal' else None
        current={}
        for name,labels in raw.items():
            x=data(labels,scope,material,metadata,cluster);audit.compare(x,t['methods'][name],'composition/'+str(i)+'/'+name,'composition')
            role='rules' if name==RULE else 'LLM'
            ta=attention['robustness'][i]['methods'][role]
            for g in n.GROUPS:
                audit.compare({k:v for k,v in x['departments'][g]['profile'].items() if k in ta[g]},ta[g],'attention-composition/'+str(i)+'/'+role+'/'+g,'composition')
            current[name]=x
        composition_records.append(current);scope_counts.append({'scenario':sc,'omitted_policy_entry':omit,'n_by_group':{g:len(v) for g,v in scope.items()}})
    summary={}
    for name in raw:
        summary[name]={}
        for kind,records in [('definition6',definition_records),('composition56',composition_records)]:
            summary[name][kind]={}
            for metric in primary[name]['contrasts']:
                values=[r[name]['contrasts'][metric]['NHSA_minus_NHC'] for r in records]
                defined=[v for v in values if v is not None];scale=1 if metric=='OR' else 100
                expected={'scenario_n':len(values),'NHSA_higher_n':sum(float(v)>1e-12 for v in defined),
                 'NHC_higher_n':sum(float(v)<-1e-12 for v in defined),'equal_n':sum(abs(float(v))<=1e-12 for v in defined),
                 'NA_n':len(values)-len(defined),'NHSA_minus_NHC_range':[scale*min(defined),scale*max(defined)] if defined else None,
                 'range_units':'OR units' if metric=='OR' else 'percentage points'}
                audit.compare(expected,findings['summary'][name][kind][metric],'summary/'+name+'/'+kind+'/'+metric,'direction_summary')
                summary[name][kind][metric]=expected
    table30=[];condition8=[]
    for name,record in primary.items():
        for g in n.GROUPS:
            prof=record['departments'][g]['profile']
            for dim in n.DIMS:
                share=prof['attention_share'][dim]
                table30.append({'method':name,'group':g,'dimension':dim,'coding_count':prof['coding_count'][dim],
                 'five_dimension_denominator':prof['five_dimension_coding_count'],'unit_denominator':prof['unit_n'],
                 'attention_percent':100*share,'display_2dp':format(float(100*share),'.2f')})
            if g in ('NHSA','NHC'):
                p=next(v for v in record['departments'][g]['all10_pairs'] if (v['dimension_a'],v['dimension_b'])==('Ec','F'))
                for condition,co,den,value in [('Ec','F',p['a_positive'],p['p_b_given_a']),('F','Ec',p['b_positive'],p['p_a_given_b'])]:
                    condition8.append({'method':name,'group':g,'condition_dimension':condition,'cooccurring_dimension':co,
                     'both_n':p['both_n'],'condition_positive_n':den,'conditional_share':value,'display_percent_2dp':format(float(100*value),'.2f') if value is not None else 'NA'})
    assert len(table30)==30 and len(condition8)==8
    all60=[]
    if details is not None:
        assert len(details['rows'])==60
        for row in details['rows']:
            condition,co=row['condition_dimension'],row['cooccurring_dimension'];one,two=row['department_one'],row['department_two'];rec={}
            for name in raw:
                nums=[]
                for g in (one,two):
                    ids=fullscope[g];both=sum(raw[name][rid][condition]*raw[name][rid][co] for rid in ids);den=sum(raw[name][rid][condition] for rid in ids)
                    nums.append({'both_n':both,'condition_positive_n':den,'conditional_share':n.ratio(both,den)})
                delta=nums[0]['conditional_share']-nums[1]['conditional_share'] if all(x['conditional_share'] is not None for x in nums) else None
                out={'one':nums[0],'two':nums[1],'difference_percentage_points':100*delta if delta is not None else None}
                for kind,scenarios in [('definition6',definition_records),('composition56',composition_records)]:
                    values=[]
                    for scenario in scenarios:
                        x,y=[conditional(scenario[name],g,condition,co) for g in (one,two)]
                        values.append(x-y if x is not None and y is not None else None)
                    out[kind]=range_summary(values)
                audit.compare(out,row['methods'][name],'all60/'+condition+'/'+co+'/'+one+'/'+two+'/'+name,'all_condition_denominators')
                rec[name]=out
            def sign(v):return None if v is None else 1 if float(v)>1e-10 else -1 if float(v)<-1e-10 else 0
            signs=[sign(v['difference_percentage_points']) for v in rec.values()]
            same=signs[0] is not None and signs[0]==signs[1]
            stable=same and signs[0]!=0
            for name in raw:
                base_sign=sign(rec[name]['difference_percentage_points'])
                for scenarios in (definition_records,composition_records):
                    for scenario in scenarios:
                        x,y=[conditional(scenario[name],g,condition,co) for g in (one,two)]
                        stable=stable and sign(x-y if x is not None and y is not None else None)==base_sign
            minimum=min(v[side]['condition_positive_n'] for v in rec.values() for side in ('one','two'))
            audit.compare(same,row['two_method_primary_direction_same'],'all60/'+condition+'/'+co+'/'+one+'/'+two+'/same_direction','all_condition_denominators')
            audit.compare(stable,row['same_primary_direction_in_all_definition_and_composition_scenarios'],'all60/'+condition+'/'+co+'/'+one+'/'+two+'/stable_direction','all_condition_denominators')
            audit.compare(minimum,row['minimum_primary_condition_positive_n'],'all60/'+condition+'/'+co+'/'+one+'/'+two+'/minimum_denominator','all_condition_denominators')
            all60.append({'condition_dimension':condition,'cooccurring_dimension':co,'department_one':one,'department_two':two,'methods':rec})
    paired_intervals=[];cluster_records=[]
    for g in n.GROUPS:
        ids=fullscope[g];sources_sorted=sorted({material[rid]['source'] for rid in ids});k=len(sources_sorted)
        seed=b.fixed_seed('full_corpus_paired_source_file',g)
        t=next(row for row in attention['cluster_bindings'] if row['group']==g)
        audit.compare(sources_sorted,t['source_names'],'bootstrap/'+g+'/source_names','CI_binding')
        audit.compare(seed,t['seed'],'bootstrap/'+g+'/seed','CI_binding')
        rng=np.random.default_rng(seed);multiplicities=rng.multinomial(k,np.full(k,1/k),size=b.B)
        boot={};point={}
        for name,labels in raw.items():
            arr=np.asarray([[sum(labels[rid][d] for rid in ids if material[rid]['source']==source) for d in n.DIMS] for source in sources_sorted],float)
            hits=multiplicities@arr;den=hits.sum(axis=1)
            boot[name]=np.divide(hits,den[:,None],out=np.full_like(hits,np.nan),where=den[:,None]>0)
            total=arr.sum(axis=0);point[name]=total/total.sum()
        for j,dim in enumerate(n.DIMS):
            out={'group':g,'dimension':dim,'unit_n':len(ids),'source_file_cluster_n':k,'difference_direction':'LLM_minus_rules',
             'difference_percentage_points':100*(point[LLM][j]-point[RULE][j]),
             'ci95_source_file_conditional_percentage_points':b.percentile_interval(100*(boot[LLM][:,j]-boot[RULE][:,j]))}
            actual=next(row for row in attention['paired_file_composition_sensitivity'] if row['group']==g and row['dimension']==dim)
            audit.compare(out,actual,'bootstrap/'+g+'/'+dim,'CI_fixed_reproduction');paired_intervals.append(out)
        cluster_records.append({'group':g,'policy_entry_n':len({material[rid]['stem'] for rid in ids}),'actual_source_file_n':k,'seed':seed,'replicates':b.B})
    for p,h in audit.bindings.items():audit.compare(h,n.sha(p),p+'/unchanged','read_only')
    report={'status':'PASS_INDEPENDENT_NUMERIC_CHECKS' if not audit.failures else 'FAIL_RETAINED',
     'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':dict(audit.counts),'failures':audit.failures,
     'full_scope_n':4481,'same_probability_scope_n':180,'table30':n.pack(table30),'eight_Ec_F_conditions':n.pack(condition8),
     'primary_exact_profiles_and_all10_pairs':n.pack(primary),'same180_exact_profiles_and_all10_pairs':n.pack(same180),
     'definition6_removed_aggregates':removals,'composition56_scope_counts':scope_counts,'independent_direction_and_range_summary':n.pack(summary),
     'all60_conditional_department_contrasts':n.pack(all60),'source_file_paired_interval_records':paired_intervals,'cluster_records':cluster_records,
     'source_bindings':audit.bindings,'author_statistical_functions_imported':False,'source_files_modified':False,'new_classifier_or_model_calls':0,
     'no_per_reserved_unit_text_or_prediction_or_reference_label_displayed':True,
     'CI_coverage_or_label_truth_validity':'NOT_ESTABLISHED','limits':['六定义及56文件构成是敏感性口径，不是62次独立验证。','文件条目51与实际来源文件簇不同；各自估计量与分母分别核对。','固定5000次重采样复现不证明区间覆盖率或语义正确性。'],
     'script_sha256':n.sha(__file__)}
    args.report.parent.mkdir(parents=True,exist_ok=True);args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':report['status'],'report':str(args.report),'sha256':n.sha(args.report),'failure_n':len(audit.failures),'checks':dict(audit.counts)},ensure_ascii=False))

if __name__=='__main__':main()
