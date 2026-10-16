"""Compare independently computed exact fractions with actual same-version driver outputs."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,math
D=Path(__file__).resolve().parent
R=D.parents[1]
A=D/'完整03六定义56构成独立复算.json'
FOLDER=R/'methods-20261008/rules-v36.2-plus-LLM03-reconciled-development-findings-v3'
B=FOLDER/'完整定义构成核查.json'
read=lambda p:json.loads(p.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bind=lambda p:{'path':str(p),'sha256':sha(p)}
checks=0
pairs=0

def eq(a,b,where):
    global checks
    checks+=1
    if isinstance(a,dict) and 'exact_fraction'in a:a=float(F(a['exact_fraction']))
    if a is None or b is None:
        if a is not b:raise ValueError((where,a,b))
    elif isinstance(a,(float,int)) and isinstance(b,(float,int)):
        if not math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-11):raise ValueError((where,a,b))
    elif a!=b:raise ValueError((where,a,b))

def rawpair(a,b,where):
    global pairs
    pairs+=1
    z=a['cells']; keys=['both_n','a_only_n','b_only_n','neither_n']
    for k,v in zip(keys,z):eq(v,b[k],where+'/'+k)
    eq(a['a'],b['dimension_a'],where+'/a');eq(a['b'],b['dimension_b'],where+'/b')
    eq(sum(z),b['unit_n'],where+'/n')
    for k in ['p_b_given_a','p_a_given_b']:eq(a[k],b[k],where+'/'+k)
    eq(z[0]+z[1],b['a_positive'],where+'/a_positive');eq(z[0]+z[2],b['b_positive'],where+'/b_positive')
    expected=float(F(z[0]*z[3],z[1]*z[2])) if z[1]*z[2] else None
    eq(expected,b['OR'],where+'/OR')

def profile(a,b,where):
    eq(a['unit_n'],b['unit_n'],where+'/n')
    for d in ['S','E','Ec','I','F']:
        eq(a['q'][d],b['attention_share'][d],where+'/q/'+d)
        eq(a['coverage'][d],b['coverage'][d],where+'/coverage/'+d)
    if 'counts'in a:
        eq(a['counts'],b['coding_count'],where+'/counts');eq(a['total_coding'],b['five_dimension_coding_count'],where+'/total')
    else:
        eq(a['cluster_n'],b['equal_cluster_n'],where+'/clusters')
        eq(sorted(a['q_zero_hit_clusters']),sorted(b['zero_hit_cluster_names_excluded_from_average']),where+'/zeroq')
        eq(a['cluster_n']-len(a['q_zero_hit_clusters']),b['defined_cluster_n'],where+'/definedq')
        profile(a['raw_unweighted'],b['raw_unweighted_profile_for_audit'],where+'/raw')

def department(a,b,where):
    global pairs
    profile(a,b['profile'],where+'/profile')
    bp={p['dimension_a']+'__'+p['dimension_b']:p for p in b['all10_pairs']}
    eq(set(a['pairs']),set(bp),where+'/pair_set')
    for name,z in a['pairs'].items():
        p=bp[name]
        if 'cells'in z:rawpair(z,p,where+'/'+name)
        else:
            pairs+=1
            for k in ['p_b_given_a','p_a_given_b']:eq(z[k],p[k],where+'/'+name+'/'+k)
            eq(sorted(z['zero_a_clusters']),sorted(p['zero_a_clusters_excluded']),where+'/'+name+'/zeroa')
            eq(sorted(z['zero_b_clusters']),sorted(p['zero_b_clusters_excluded']),where+'/'+name+'/zerob')
            eq(a['cluster_n']-len(z['zero_a_clusters']),p['defined_a_clusters'],where+'/'+name+'/defineda')
            eq(a['cluster_n']-len(z['zero_b_clusters']),p['defined_b_clusters'],where+'/'+name+'/definedb')
            eq(set(a['clusters']),set(p['cluster_counts']),where+'/'+name+'/clusters')
            for cluster,c in a['clusters'].items():rawpair(c['pairs'][name],p['cluster_counts'][cluster],where+'/'+name+'/'+cluster)
            mixture=[sum((F(c['pairs'][name]['cells'][j],c['unit_n'])for c in a['clusters'].values()),F())/len(a['clusters'])for j in range(4)]
            for v,k in zip(mixture,['both_n','a_only_n','b_only_n','neither_n']):eq(float(v),p['equal_cluster_cell_mixture'][k],where+'/'+name+'/mixed/'+k)
            expected=float(mixture[0]*mixture[3]/(mixture[1]*mixture[2])) if mixture[1]*mixture[2] else None
            eq(expected,p['OR'],where+'/'+name+'/mixedOR')

def main():
    eq(sha(B),'5d8e65d15638e957ca6f91c410f3203e1f9ade2349fd9afcaa64e29b16e62709','formal_sha')
    eq(sha(A),'09acb5d3ce797d0b103888624c25bc643916dbcd032d30f96672861a667ae92f','independent_sha')
    own,official=read(A),read(B)
    for scope in ['definition6','composition56']:
        eq(len(own[scope]),len(official[scope]),scope+'/length')
        for x,y in zip(own[scope],official[scope]):
            eq(x['scenario'],y['scenario'],scope+'/scenario')
            if scope=='composition56':eq(x['omitted_policy_entry'],y['omitted_policy_entry'],scope+'/omitted');eq(x['scope_ids'],y['scope_ids'],scope+'/scope_ids')
            eq(set(x['methods']),set(y['methods']),scope+'/methodset')
            for m,o in x['methods'].items():
                f=y['methods'][m]['full4481'] if scope=='definition6' else y['methods'][m]
                for g,a in o['departments'].items():department(a,f['departments'][g],scope+'/'+x['scenario']+'/'+m+'/'+g)
                if scope=='definition6':eq(o['removed_labels'],[{'id':z['id'],'dimension':z['dimension']}for z in y['methods'][m]['removed_labels']],scope+'/'+x['scenario']+'/'+m+'/removed')
                for metric,z in o['contrasts'].items():
                    key='attention_share_'+metric[2:] if metric.startswith('q_')else metric
                    for g in ['NHSA','NHC']:eq(z[g],f['contrasts'][key][g],scope+'/'+x['scenario']+'/'+m+'/'+metric+'/'+g)
    aux=read(D/'八叙述字段辅助点值与重复性独立核对.json')
    for role,key in [('rules','rules-v36.2'),('LLM','LLM-candidate03-single-unit-reconciled')]:
        for g,a in aux['probability180']['profiles'][role].items():
            b=official['same180_primary'][key]['departments'][g]['profile']
            eq(a['counts'],b['coding_count'],'same180/'+role+'/'+g+'/counts')
            for d,v in a['q_exact'].items():eq(float(F(v)),b['attention_share'][d],'same180/'+role+'/'+g+'/'+d)
    for name,h in read(FOLDER/'output_freeze.json')['files'].items():eq(sha(FOLDER/name),h,'freeze/'+name)
    qa=read(FOLDER/'核查QA.json');eq(qa['all_checks_pass'],True,'officialQA')
    out={'status':'PASS_INDEPENDENT_EXACT_ARITHMETIC_VERSUS_ACTUAL03_DRIVER','scope':'All6definitions,all56compositions,3departments,2methods,5qand5coverage,all10paircellsandconditionals,clusterzero-denominatorlists,derivedlabelremovals,andmachine_same180pointprofiles. Raw/mixed4cellOR independently derived as extra arithmetic check. NoCIbootstrap replay or semantic-validity claim.',
         'inputs':[bind(A),bind(B),bind(FOLDER/'output_freeze.json'),bind(FOLDER/'核查QA.json'),bind(D/'八叙述字段辅助点值与重复性独立核对.json')],
         'numeric_identity_or_binding_checks':checks,'pair_records_including_cluster_details':pairs,'script':bind(Path(__file__).resolve()),
         'no_candidate02_data_or_statistical_function_import':True,'no_method_adoption_or_label_change':True}
    p=D/'正式03六定义56构成逐项独立对照QA.json'
    with p.open('x')as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({**out,'output':bind(p)},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
