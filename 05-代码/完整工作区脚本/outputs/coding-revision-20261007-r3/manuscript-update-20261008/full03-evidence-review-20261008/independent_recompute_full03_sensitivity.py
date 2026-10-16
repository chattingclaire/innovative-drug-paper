"""Independent exact-arithmetic full03 six-definition/56-composition review.
Uses no statistical-code imports, no model calls and no edits to predictions.
"""
import ast, hashlib, itertools, json
from collections import Counter, defaultdict
from fractions import Fraction
from pathlib import Path

R = Path(__file__).resolve().parents[2]
D = Path(__file__).resolve().parent
METADATA = R.parent/'validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
INPUT = R/'rule_inputs_shared_v14.jsonl'
RULES = R/'rules-v36.2-development/all_predictions_material_v14.jsonl'
LLM = R/'llm-candidate03-development/full-corpus-candidate03-material-v14-single-unit-reconciled-development/all_predictions.jsonl'
MANIFEST = R/'statistics/final_bindings_v14_CONFIRMED_r3.json'
DEFINITION = R/'statistics/definition_boundary_sensitivity_r3.py'
DIMS = ('S','E','Ec','I','F')
GROUPS = ('NMPA','NHSA','NHC')
PAIRS = list(itertools.combinations(DIMS,2))


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def binding(p): return {'path':str(p), 'sha256':sha(p)}
def read(p): return json.loads(p.read_text())
def lines(p): return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def require(ok, message):
    if not ok: raise RuntimeError(message)
def divide(a,b): return Fraction(a,b) if b else None
def mean(xs):
    vals=[v for v in xs if v is not None]
    return sum(vals,Fraction())/len(vals) if vals else None

def raw_profile(ids, labels):
    counts={dim:sum(labels[r][j] for r in ids) for j,dim in enumerate(DIMS)}
    total=sum(counts.values())
    pairs={}
    for a,b in PAIRS:
        ai,bi=DIMS.index(a),DIMS.index(b)
        cells=Counter((labels[r][ai],labels[r][bi]) for r in ids)
        z=[cells[(1,1)],cells[(1,0)],cells[(0,1)],cells[(0,0)]]
        pairs[a+'__'+b]={'a':a,'b':b,'cells':z,'p_b_given_a':divide(z[0],z[0]+z[1]),'p_a_given_b':divide(z[0],z[0]+z[2])}
        require(sum(z)==len(ids),'Four-cell total mismatch')
    return {'unit_n':len(ids),'counts':counts,'total_coding':total,'q':{d:divide(v,total) for d,v in counts.items()},'coverage':{d:divide(v,len(ids)) for d,v in counts.items()},'pairs':pairs}

def summarize(ids, labels, cluster_for=None):
    raw=raw_profile(ids,labels)
    if cluster_for is None: return raw
    grouped=defaultdict(list)
    for rid in ids: grouped[cluster_for[rid]].append(rid)
    clusters={key:raw_profile(values,labels) for key,values in sorted(grouped.items())}
    out={'unit_n':len(ids),'raw_unweighted':raw,'clusters':clusters,'cluster_n':len(clusters),
         'q':{d:mean(c['q'][d] for c in clusters.values()) for d in DIMS},
         'coverage':{d:mean(c['coverage'][d] for c in clusters.values()) for d in DIMS},
         'q_zero_hit_clusters':[key for key,c in clusters.items() if c['total_coding']==0], 'pairs':{}}
    for a,b in PAIRS:
        key=a+'__'+b
        out['pairs'][key]={'a':a,'b':b,'p_b_given_a':mean(c['pairs'][key]['p_b_given_a'] for c in clusters.values()),
                          'p_a_given_b':mean(c['pairs'][key]['p_a_given_b'] for c in clusters.values()),
                          'zero_a_clusters':[k for k,c in clusters.items() if c['pairs'][key]['p_b_given_a'] is None],
                          'zero_b_clusters':[k for k,c in clusters.items() if c['pairs'][key]['p_a_given_b'] is None]}
    return out

def contrasts(groups):
    a,b=groups['NHSA'],groups['NHC']
    pairs={'P_F_given_Ec':(a['pairs']['Ec__F']['p_b_given_a'],b['pairs']['Ec__F']['p_b_given_a']),
           'P_Ec_given_F':(a['pairs']['Ec__F']['p_a_given_b'],b['pairs']['Ec__F']['p_a_given_b'])}
    pairs.update({f'{kind}_{d}':(a[kind][d],b[kind][d]) for kind in ['q','coverage'] for d in DIMS})
    return {key:{'NHSA':v[0],'NHC':v[1],'NHC_minus_NHSA':v[1]-v[0] if None not in v else None} for key,v in pairs.items()}

def to_json(x):
    if isinstance(x,Fraction): return {'exact_fraction':str(x),'value':float(x)}
    if isinstance(x,dict):return {k:to_json(v) for k,v in x.items()}
    if isinstance(x,list):return [to_json(v) for v in x]
    return x


def main():
    expected={INPUT:'fbee2777afe7e437ef1d2e0773e12a41ec3682914510f05f2dad2f31db7b6a6a',
              METADATA:'e35c0b3643093ecc3a41dfd0c3cf50aca27a43aea7fa2b4594d5cf7857ce3fb2',
              RULES:'105d10d7f441ed2c609911aa1f02bcaa4fc695acea35c6164750930a3021cc2b',
              LLM:'29c36d745357872b05311f0456bd823842f312e00de892634a3e654bc318750e',
              MANIFEST:'46582af989d0473655b71ba38f174c2043794b8da9833bca9940aa0cf62c71cd'}
    for p,h in expected.items():require(sha(p)==h,'Changed frozen input '+str(p))
    before={p:sha(p) for p in [*expected,DEFINITION]}
    metadata={Path(x['original_file']).stem:x for x in read(METADATA)['rows']}
    source=lines(INPUT);order=[x['id'] for x in source]
    require(len(order)==len(set(order))==4924,'Source scope')
    stems={x['id']:x['input']['original_file_stem'] for x in source}
    group={rid:metadata[stems[rid]]['analysis_group'] for rid in order}
    require(Counter(group.values())=={'NMPA':1848,'NHSA':2100,'NHC':533,'GOV':443},'Groups')
    selected={g:[r for r in order if group[r]==g] for g in GROUPS}
    allstems=sorted({stems[r] for r in order if group[r] in GROUPS})
    require(len(allstems)==51,'Source entry scope')
    series={r:metadata[stems[r]]['policy_series'] for r in order}
    latest={}
    for stem in allstems:
        mt=metadata[stem]
        if mt['annual_series']:latest[mt['policy_series']]=max(latest.get(mt['policy_series'],-1),mt['year_in_filename'])
    # Read the frozen declaration as literal data; never execute/import its code.
    tree=ast.parse(DEFINITION.read_text());specs=None
    for node in tree.body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SCENARIOS' for t in node.targets): specs=ast.literal_eval(node.value)
    require(list(specs)==['primary','exclude_quality_only_S','exclude_qualification_only_I','exclude_clinical_management_only_F','exclude_dimension_information_only_F','retain_access_affordability_F'],'Definition scenarios differ')
    declared=read(MANIFEST)['robustness_scenarios']
    scenarios=[(s,None) for s in declared if s!='leave_one_policy_entry_out']+([('leave_one_policy_entry_out',s) for s in allstems] if 'leave_one_policy_entry_out' in declared else [])
    require(len(scenarios)==len(set(scenarios))==56,'Composition scenario scope')
    methods={}; originals={}
    for method,p in [('rules-v36.2',RULES),('LLM-candidate03-single-unit-reconciled',LLM)]:
        rows=lines(p);require([x['id'] for x in rows]==order,'Output id/order mismatch')
        obj={x['id']:x.get('prediction',x) for x in rows};originals[method]=obj
        methods[method]={rid:tuple(obj[rid]['labels'][d] for d in DIMS) for rid in order}
        require(all(type(x)==int and x in [0,1] for labs in methods[method].values() for x in labs),'Nonbinary')
        for rid,row in obj.items():
            if row['labels']['I']:require(bool(row['innovation_subtypes']) and set(row['innovation_subtypes'])<={'attribute','research_support','qualification_advantage'},'I subtype')
            if row['labels']['F']:require(bool(row['fairness_subtypes']) and set(row['fairness_subtypes'])<={'access','affordability','clinical_management','dimension_information'},'F subtype')
            if row['labels']['S']:require(row['safety_quality_basis'] in {'quality_only','quality_and_other','no_quality_basis'},'S subtype')
    definitions=[]
    for name,explanation in specs.items():
        result={'scenario':name,'explanation':explanation,'methods':{}}
        for method,labs in methods.items():
            derived={};changes=[]
            for rid,vec in labs.items():
                row=originals[method][rid];new=list(vec);drop=None
                if name=='exclude_quality_only_S' and row.get('safety_quality_basis')=='quality_only':drop=0
                elif name=='exclude_qualification_only_I' and set(row.get('innovation_subtypes',[]))=={'qualification_advantage'}:drop=3
                elif name=='exclude_clinical_management_only_F' and set(row.get('fairness_subtypes',[]))=={'clinical_management'}:drop=4
                elif name=='exclude_dimension_information_only_F' and set(row.get('fairness_subtypes',[]))=={'dimension_information'}:drop=4
                elif name=='retain_access_affordability_F' and not set(row.get('fairness_subtypes',[])).intersection({'access','affordability'}):drop=4
                if drop is not None and new[drop]:new[drop]=0;changes.append({'id':rid,'dimension':DIMS[drop]})
                derived[rid]=tuple(new)
            departments={g:summarize(ids,derived) for g,ids in selected.items()}
            result['methods'][method]={'departments':departments,'contrasts':contrasts(departments),'removed_labels':changes}
        definitions.append(result)
    compositions=[]
    for scenario,omitted in scenarios:
        keep={g:[] for g in GROUPS}
        for g,ids in selected.items():
            for rid in ids:
                stem=stems[rid];mt=metadata[stem]
                if stem==omitted:continue
                if scenario=='exclude_joint_publications' and mt['joint_publication']:continue
                if scenario=='latest_annual_series_member' and mt['annual_series'] and mt['year_in_filename']!=latest[mt['policy_series']]:continue
                keep[g].append(rid)
        cluster=stems if scenario=='policy_file_equal' else series if scenario=='policy_series_equal' else None
        result={'scenario':scenario,'omitted_policy_entry':omitted,'scope_ids':keep,'methods':{}}
        for method,labs in methods.items():
            deps={g:summarize(ids,labs,cluster) for g,ids in keep.items()}
            result['methods'][method]={'departments':deps,'contrasts':contrasts(deps)}
        compositions.append(result)
    summary={}
    for method in methods:
        summary[method]={}
        for scope,records in [('definition6',definitions),('composition56',compositions)]:
            summary[method][scope]={}
            for metric in records[0]['methods'][method]['contrasts']:
                vals=[(rec['scenario'],rec.get('omitted_policy_entry'),rec['methods'][method]['contrasts'][metric]['NHC_minus_NHSA']) for rec in records]
                valid=[v for v in vals if v[2] is not None]
                summary[method][scope][metric]={'n':len(vals),'NHC_higher':sum(v[2]>0 for v in valid),'NHSA_higher':sum(v[2]<0 for v in valid),'equal':sum(v[2]==0 for v in valid),'NA':len(vals)-len(valid),'NHC_minus_NHSA_min_pp':min(v[2] for v in valid)*100,'NHC_minus_NHSA_max_pp':max(v[2] for v in valid)*100,'minimum_cases':[{'scenario':s,'omitted':o} for s,o,v in valid if v==min(t[2] for t in valid)],'maximum_cases':[{'scenario':s,'omitted':o} for s,o,v in valid if v==max(t[2] for t in valid)]}
    require(all(sha(p)==x for p,x in before.items()),'Input changed during review')
    report={'status':'INDEPENDENT_EXACT_ARITHMETIC_FULL03_DEFINITION6_COMPOSITION56_COMPLETE_AWAITING_DRIVER_COMPARISON','script':binding(Path(__file__).resolve()),'inputs':[binding(p) for p in before],
            'scope':'Full4481 excludesGOV443; six definition cases and56 composition cases separately, not336 cross-cases. No statistical code imported or executed; frozenSCENARIOS parsed as literaldata only. No candidate02 data. Existing output subtypes retained without semantic reclassification.',
            'denominators':'P(F|Ec): Ec-positive units; q: sum five-dimensional positives. Equalcluster P is mean within-cluster P across positive-denominator clusters; q averages clusters with any positive dimensions; coverage averages all clusters. Zero denominator cluster names retained. Fraction arithmetic before conversion.',
            'definition6':definitions,'composition56':compositions,'summary':summary,'all_ten_pairs_retained':True,'no_CI_or_significance_or_causal_claim':True,'raw_labels_unchanged':True}
    out=D/'完整03六定义56构成独立复算.json'
    with out.open('x') as f:json.dump(to_json(report),f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'output':binding(out),'summary':to_json({method:{scope:{metric:vals[metric] for metric in ['P_F_given_Ec','q_Ec','q_F','coverage_F']} for scope,vals in groups.items()} for method,groups in summary.items()})},ensure_ascii=False,indent=2))

if __name__=='__main__': main()
