"""Read both result JSONs; never import the root implementation."""
from pathlib import Path
from fractions import Fraction
import hashlib,json

P=Path(__file__).resolve().parent
def bind(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
own=json.loads((P/'independent-reversal-threshold-results.json').read_text())
root=json.loads((P/'root_exact_label_sensitivity.json').read_text())
checks=[]
def check(name,value):checks.append({'check':name,'pass':bool(value)})
for b in root['inputs']+own['input_bindings']:
    check('input_sha:'+b['path'],bind(Path(b['path']))['sha256']==b['sha256'])
cellmap={'joint':'Ec1_F1','Ec_only':'Ec1_F0','F_only':'Ec0_F1','neither':'Ec0_F0'}
for method in ('rules','LLM'):
    a,b=own['methods'][method],root['results'][method]
    for group in ('NHSA','NHC'):
        check(method+'/'+group+'/four_cells',all(b['actual_four_cells'][group][k]==a['observed'][group][v] for k,v in cellmap.items()))
    for rmode,imode in [('fixed_Ec_F_only','fixed_Ec_F_flips'),('allow_Ec_and_F_changed_unit_cost','Ec_and_F_unit_cost')]:
        r=b['modes'][rmode];i=a[imode]
        check(method+'/'+rmode+'/non_strict_minimum',r['minimum_units_to_erase_strict_NHC_higher']==i['NHC_le_NHSA']['minimum_units'])
        check(method+'/'+rmode+'/strict_minimum',r['minimum_units_to_strictly_reverse']==i['NHC_lt_NHSA']['minimum_units'])
        for point in r['exhaustive_budget_curve_until_strict_reversal']:
            budget=point['max_changed_units']
            if imode=='fixed_Ec_F_flips':
                h,c=a['observed']['NHSA'],a['observed']['NHC']
                eh,ec=h['Ec1_F1']+h['Ec1_F0'],c['Ec1_F1']+c['Ec1_F0']
                possibilities=[(Fraction(ac,ec)-Fraction(ah,eh),abs(ac-c['Ec1_F1']),abs(ah-h['Ec1_F1']))
                    for ah in range(max(0,h['Ec1_F1']-budget),min(eh,h['Ec1_F1']+budget)+1)
                    for ac in range(max(0,c['Ec1_F1']-budget),min(ec,c['Ec1_F1']+budget)+1)
                    if abs(ah-h['Ec1_F1'])+abs(ac-c['Ec1_F1'])<=budget]
                gap,kc,kh=min(possibilities)
            else:
                record=i['lower_bound_certificate'][budget]
                gap=Fraction(record['minimum_possible_NHC_minus_NHSA']['exact'])
                kh,kc=record['best_allocation']['NHSA'],record['best_allocation']['NHC']
            check(method+'/'+rmode+f'/budget{budget}/gap',Fraction(point['minimum_NHC_minus_NHSA'])==gap)
            check(method+'/'+rmode+f'/budget{budget}/allocation',point['budget_split_NHC_NHSA']==[kc,kh])

result={'status':'PASS' if all(x['pass'] for x in checks) else 'FAIL',
  'independent_scripts_not_imported_from_each_other':True,
  'inputs':[bind(P/'independent-reversal-threshold-results.json'),bind(P/'root_exact_label_sensitivity.json')],
  'script':bind(Path(__file__).resolve()),'check_n':len(checks),'checks':checks,
  'scope_limit':'Only the adopted full-corpus primary unweighted count definition and NHSA/NHC P(F|Ec). It does not cover the six alternative definitions, 56 file-composition/weighting scenarios or the probability180 reference frame.',
  'interpretation_limit':'8/7 are the minimum number of hypothetical adversarial unit-label changes needed to remove the direction under the specified cost. They are not actually located errors, measured error rates, confidence probabilities, confidence intervals, or a validity guarantee. No human/future-human text was read and no row was relabeled.',
  'minimum_non_strict_and_strict':{'rules':8,'LLM':7},
  'equality_distinguished':'No equality occurs at the minimum non-strict thresholds; the attaining examples strictly reverse direction. Separate equality minima are 139/158 with Ec fixed and 10/12 with both labels changeable.'}
out=P/'independent-root-crosscheck.json'
assert not out.exists()
out.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'status':result['status'],'check_n':len(checks),'result':bind(out)},ensure_ascii=False))
assert result['status']=='PASS'
