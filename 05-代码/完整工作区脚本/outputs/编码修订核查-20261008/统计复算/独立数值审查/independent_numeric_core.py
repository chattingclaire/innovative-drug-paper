"""Independent integer/Fraction analytical implementation. No project statistics import.

Inputs may contain reserved units: loaders extract labels/metadata mechanically;
never print or serialize individual labels, text, reasons or evidence.
"""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter,defaultdict
from itertools import combinations
import hashlib,json,math

DIMS=('S','E','Ec','I','F')
GROUPS=('NMPA','NHSA','NHC')
PAIRS=tuple(combinations(DIMS,2))
CELLS=('TP','FP','FN','TN')
SCOPES=tuple((component,group,weighting)
 for component in ('probability_canonical','enriched_challenge')
 for group in ('ALL',*GROUPS)
 for weighting in (('unweighted','eligible_design_weighted') if component=='probability_canonical' else ('unweighted',)))

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def binary(v):return type(v) is int and v in (0,1)
def ratio(a,b):return Q(a,b) if b else None
def mean(vals):return sum(vals,Q(0))/len(vals) if vals else None
def pack(x):
    if isinstance(x,Q):return {'exact_fraction':str(x),'estimate':float(x)}
    if isinstance(x,dict):return {k:pack(v) for k,v in x.items()}
    if isinstance(x,(list,tuple)):return [pack(v) for v in x]
    return x

def label_only_jsonl(p):
    result={}
    with Path(p).open() as stream:
        for line in stream:
            if not line.strip():continue
            row=json.loads(line);rid=row['id'];assert rid not in result
            actual=row.get('prediction',row)
            result[rid]={d:actual['labels'][d] for d in DIMS}
    return result

def machine_numeric_jsonl(p):
    labels={};subtypes={};input_hash={}
    with Path(p).open() as stream:
        for line in stream:
            if not line.strip():continue
            row=json.loads(line);rid=row['id'];assert rid not in labels
            prediction=row.get('prediction',row)
            labels[rid]={d:prediction['labels'][d] for d in DIMS}
            assert all(binary(v) for v in labels[rid].values())
            subtypes[rid]={k:prediction.get(k) for k in ('fairness_subtypes','innovation_subtypes','safety_quality_basis')}
            input_hash[rid]=prediction.get('unit_text_sha256')
    return labels,subtypes,input_hash

def material_metadata_only(p,metadata):
    result={}
    with Path(p).open() as stream:
        for line in stream:
            if not line.strip():continue
            row=json.loads(line);rid=row['id'];assert rid not in result
            i=row['input'];stem=i['original_file_stem'];m=metadata[stem]
            result[rid]={'group':m['analysis_group'],'stem':stem,
             'source':i.get('unit_source') or i['source'],
             'unit_text_sha256':hashlib.sha256(i['unit_text'].encode()).hexdigest()}
    return result

def direct_metrics(cells):
    tp,fp,fn,tn=map(Q,cells);n=tp+fp+fn+tn
    pe_num=(tp+fp)*(tp+fn)+(fn+tn)*(fp+tn)
    return {'kappa':ratio(n*(tp+tn)-pe_num,n*n-pe_num),
     'agreement':ratio(tp+tn,n),'precision':ratio(tp,tp+fp),
     'recall':ratio(tp,tp+fn),'f1':ratio(2*tp,2*tp+fp+fn),
     'left_positive_rate':ratio(tp+fp,n),'right_positive_rate':ratio(tp+fn,n)}

def scope_ids(design,component,group):
    return sorted(rid for rid,r in design.items() if r['component']==component and (group=='ALL' or r['group']==group))
def design_weight(design,rid,weighting):
    if weighting=='unweighted':return Q(1)
    assert weighting=='eligible_design_weighted' and design[rid]['component']=='probability_canonical'
    return Q(design[rid]['canonical_frame_N'],design[rid]['sample_n'])

def classification(left,right,dimension,ids,design,weighting,symmetric=False):
    raw=[0]*4;weighted=[Q(0)]*4;paired=[];excluded=[]
    for rid in ids:
        x,y=left[rid][dimension],right[rid][dimension]
        if not binary(x) or not binary(y):excluded.append(rid);continue
        k=2*(1-x)+(1-y);raw[k]+=1;weighted[k]+=design_weight(design,rid,weighting);paired.append(rid)
    metrics=direct_metrics(weighted)
    if symmetric:metrics={k:v for k,v in metrics.items() if k in ('kappa','agreement','left_positive_rate','right_positive_rate')}
    return {'unit_frame_n':len(ids),'paired_n':len(paired),'excluded_pending_n':len(excluded),
     'paired_ids':paired,'excluded_ids':excluded,'left_positive_n':raw[0]+raw[1],
     'reference_positive_n':raw[0]+raw[2],'raw_confusion':dict(zip(CELLS,raw)),
     'weighted_confusion':dict(zip(CELLS,weighted)),'weighted_denominator':sum(weighted),'metrics':metrics}

def all420(methods,refs,design):
    assert len(methods)==2 and set(refs)=={'A','C','candidate'}
    out=[]
    for component,group,weighting in SCOPES:
        ids=scope_ids(design,component,group)
        for name,labels in methods.items():
            for ref,right in refs.items():
                for dim in DIMS:
                    out.append({'component':component,'group':group,'weighting':weighting,'method':name,
                     'reference':ref,'dimension':dim,**classification(labels,right,dim,ids,design,weighting)})
        for dim in DIMS:
            out.append({'component':component,'group':group,'weighting':weighting,'method':'A_C',
             'reference':'symmetric A/C','dimension':dim,**classification(refs['A'],refs['C'],dim,ids,design,weighting,True)})
    assert len(out)==420
    return out

def profile(labels,ids,weights=None):
    counts={d:sum((Q(labels[r][d])*(weights[r] if weights else 1) for r in ids),Q(0)) for d in DIMS}
    total=sum(counts.values());n=sum((weights[r] for r in ids),Q(0)) if weights else len(ids)
    return {'unit_n':len(ids),'coding_count':counts,'five_dimension_coding_count':total,
     'attention_share':{d:ratio(counts[d],total) for d in DIMS},
     'coverage':{d:ratio(counts[d],n) for d in DIMS},
     'within_department_rank':{d:1+sum(v>counts[d] for v in counts.values()) if total else None for d in DIMS}}

def pair_from_cells(cells,a,b,kind):
    n11,n10,n01,n00=cells;n=sum(cells);na=n11+n10;nb=n11+n01
    return {'dimension_a':a,'dimension_b':b,'cell_type':kind,
     **dict(zip(('both_n','a_only_n','b_only_n','neither_n'),cells)),
     'n_or_probability_mass':n,'a_positive':na,'b_positive':nb,
     'p_b_given_a':ratio(n11,na),'p_a_given_b':ratio(n11,nb),
     'a_base':ratio(na,n),'b_base':ratio(nb,n),
     'p_b_given_non_a':ratio(n01,n01+n00),'p_a_given_non_b':ratio(n10,n10+n00),
     'OR':ratio(n11*n00,n10*n01),'OR_NA':not bool(n10*n01),
     'OR_exact':str(ratio(n11*n00,n10*n01)) if n10*n01 else None,'both_unit_fraction':ratio(n11,n)}

def raw_pair(labels,ids,a,b):
    cells=[0]*4
    for rid in ids:cells[2*(1-labels[rid][a])+(1-labels[rid][b])]+=1
    return {**pair_from_cells(cells,a,b,'raw_counts'),'unit_n':len(ids)}

def cluster_partition(ids,material,metadata,kind):
    cl=defaultdict(list)
    for rid in ids:
        stem=material[rid]['stem'];cl[stem if kind=='policy_file' else metadata[stem]['policy_series']].append(rid)
    return dict(cl)

def cluster_profile(labels,ids,material,metadata,kind):
    cl=cluster_partition(ids,material,metadata,kind);p={k:profile(labels,v) for k,v in cl.items()}
    defined={k:v for k,v in p.items() if v['five_dimension_coding_count']}
    shares={d:mean([v['attention_share'][d] for v in defined.values()]) for d in DIMS}
    return {'unit_n':len(ids),'equal_cluster_n':len(cl),'defined_cluster_n':len(defined),
     'zero_hit_cluster_names_excluded_from_average':sorted(set(cl)-set(defined)),
     'attention_share':shares,'within_department_rank':{d:1+sum(v>shares[d] for v in shares.values()) if shares[d] is not None else None for d in DIMS},
     'coverage':{d:mean([v['coverage'][d] for v in p.values()]) for d in DIMS},
     'raw_unweighted_profile_for_audit':profile(labels,ids)}

def cluster_pair(labels,ids,a,b,material,metadata,kind):
    cl=cluster_partition(ids,material,metadata,kind);p={k:raw_pair(labels,v,a,b) for k,v in cl.items()}
    av=[v['p_b_given_a'] for v in p.values() if v['p_b_given_a'] is not None]
    bv=[v['p_a_given_b'] for v in p.values() if v['p_a_given_b'] is not None]
    cellnames=('both_n','a_only_n','b_only_n','neither_n')
    mixture=[mean([Q(v[k],v['unit_n']) for v in p.values()]) if p else Q(0) for k in cellnames]
    mix=pair_from_cells(mixture,a,b,'equal_cluster_mean_cell_probabilities')
    return {'dimension_a':a,'dimension_b':b,'unit_n':len(ids),'cell_type':'cluster_conditionals_mean; not pooled4cellOR',
     'equal_cluster_n':len(cl),'p_b_given_a':mean(av),'p_a_given_b':mean(bv),
     'defined_a_clusters':len(av),'defined_b_clusters':len(bv),
     'zero_a_clusters_excluded':sorted(k for k,v in p.items() if v['p_b_given_a'] is None),
     'zero_b_clusters_excluded':sorted(k for k,v in p.items() if v['p_a_given_b'] is None),
     'cluster_counts':p,'equal_cluster_cell_mixture':mix,'OR':mix['OR']}

def group_findings(labels,scope,material,metadata,cluster_kind=None):
    return {g:{'profile':cluster_profile(labels,ids,material,metadata,cluster_kind) if cluster_kind else profile(labels,ids),
     'all10_pairs':[cluster_pair(labels,ids,a,b,material,metadata,cluster_kind) if cluster_kind else raw_pair(labels,ids,a,b) for a,b in PAIRS]}
     for g,ids in scope.items()}

def synthetic_arithmetic_checks():
    # Check undefined cases and asymmetric positives independently of any real label.
    assert direct_metrics([0,0,0,0])==dict.fromkeys(('kappa','agreement','precision','recall','f1','left_positive_rate','right_positive_rate'))
    assert direct_metrics([0,0,0,10])['kappa'] is None
    assert direct_metrics([10,0,0,0])['kappa'] is None
    r=direct_metrics([4,1,2,3]);assert r['precision']==Q(4,5) and r['recall']==Q(2,3) and r['f1']==Q(8,11)
    assert r['kappa']==Q(2,5)
    p=pair_from_cells([3,1,2,4],'Ec','F','test');assert p['p_b_given_a']==Q(3,4) and p['p_a_given_b']==Q(3,5) and p['OR']==6
    assert pair_from_cells([0,0,0,4],'Ec','F','test')['p_b_given_a'] is None
    assert len(SCOPES)==12
    return {'NA_zero_denominator_and_degenerate_kappa':'PASS','asymmetric_P_R_F1_kappa_exact':'PASS','conditional_denominators_and_OR':'PASS','twelve_scope_grid':'PASS','real_labels_used':False}
