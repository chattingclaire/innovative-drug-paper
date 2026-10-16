"""One execution of fixed small TOY controls; no actual source labels."""
import sys
sys.dont_write_bytecode=True
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import scope_admission as a
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]

def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def same(x,y,message):a.require(x==y,message)

def main():
    plan=a.strict_json((HERE/'controls-fixed-before-execution.json').read_text())
    engine=module('dynamic_candidate_engine',HERE/'metrics_engine.py');base=module('frozen_year_base',HERE/'frozen_year_core.py')
    old=module('frozen_old_core',ROOT/'07-statistics/prospective-engine-domain-sol/metrics_engine.py')
    outputs=[];cases=[]
    for case in plan['cases']:
        payload=a.load(case['input_binding']);mode=case['mode'];cid=case['case_id'];expected=case['expected'];item={'case_id':cid,'input_binding':case['input_binding'],'expected':expected,'mode':mode}
        try:
            if mode=='bad_replicates':engine.analyze(payload,4999,20261010,'single_category')
            elif mode=='legacy_compare':
                current=engine.analyze(payload,5000,20261010,'single_category');b=base.analyze(payload,5000,20261010,'single_category');o=old.analyze(payload,5000,20261010,'single_category')
                same(current,b,'Legacy full output differs from frozen annual engine');same(current,o,'Legacy full output differs from frozen original core')
                item.update(observed='entire_analyze_return_exact',passed=True,old_and_year_core_full_result_equal=True);outputs.append({'case_id':cid,'synthetic_only':True,'result':current})
            elif mode=='analyze':
                result=engine.analyze(payload,5000,20261010,'single_category');c=result['comparisons']['rule_vs_reference']['domains']['ALL']['S']
                same(c['raw']['binary_four_order_a_b_c_d'],[1,1,1,1],'Raw machine rows/reference columns altered')
                same(c['design_weighted']['binary_four_order_a_b_c_d'],[300.,300.,330.5,330.5],'Actual registered N_h/n_h weights altered')
                prep=engine.prepare(payload);same(list(map(int,prep['failure_causes']['rule'][:,0])),[0,0,0,0,0,2,1,3],'Missing/whole/dimension failure causes altered')
                same(int(prep['states']['reference'][4,0]),2,'Semantic null imputed')
                same(result['design']['replicate_weight_generation_count'],1,'More than one W generated')
                a.require(result['project_review']['formal_acceptance'] is False and result['registered_scope_admission']['synthetic_only'] is True,'Toy scope became real admission')
                item.update(observed=expected,passed=True,W_sha256=result['design']['shared_replicate_weights_sha256'],raw=[1,1,1,1],weighted=[300,300,330.5,330.5]);outputs.append({'case_id':cid,'synthetic_only':True,'result':result})
            elif mode=='zero_error':
                p=copy.deepcopy(payload)
                for r in p['records']:
                    for method in r['outputs']:r['outputs'][method]={'status':'completed','labels':dict.fromkeys(engine.DIMS,0)}
                current=engine.analyze(p,5000,20261010,'single_category');b=base.analyze(p,5000,20261010,'single_category')
                for key in ('comparisons','attention','numeric_targets','numeric_targets_by_analysis_scope','design'):same(current[key],b[key],'Sparse/zero-error numerical output differs: '+key)
                for name in ('A_vs_B','rule_vs_reference','LLM_vs_reference'):
                    for dim in engine.DIMS:
                        c=current['comparisons'][name]['domains']['ALL'][dim]
                        a.require(c['design_weighted_metrics']['kappa'] is None and c['design_weighted_metrics']['Precision'] is None,'Undefined sparse denominator filled as one')
                        same(c['finite_guard'],b['comparisons'][name]['domains']['ALL'][dim]['finite_guard'],'Finite population boundary guard changed')
                item.update(observed=expected,passed=True);outputs.append({'case_id':cid,'synthetic_only':True,'executed_input':p,'result':current})
            elif mode=='annual':
                p=copy.deepcopy(payload);desc=a.load(p['metadata']['synthetic_registration_fixture']);year=a.rows(desc['year_source_map']);by={r['unit_id']:r['policy_year'] for r in year};yc=a.load(desc['year_metadata'])
                for r in p['records']:r['policy_year']=by[r['unit_id']]
                ym={k:yc[k] for k in ('assignment_basis','frozen_before_labels','requested_years','no_source_views')};ym.update(sealed=True,sha256=desc['year_source_map']['sha256']);ym['joined_projection_sha256']=engine.canonical_hash(engine.year_projection(p['records'],ym));p['metadata']['year_mapping']=ym
                annual=engine.analyze(p,5000,20261010,'single_category');plain=engine.analyze(payload,5000,20261010,'single_category');b=base.analyze(p,5000,20261010,'single_category')
                same(annual['design']['shared_replicate_weights_sha256'],plain['design']['shared_replicate_weights_sha256'],'Year redraw or weight change')
                for key in ('comparisons','attention','numeric_targets','numeric_targets_by_analysis_scope','design','year_metadata'):same(annual[key],b[key],'Year algorithm differs from exact frozen core: '+key)
                same(annual['year_metadata']['unknown_policy_year_assigned_n'],1,'Unknown year dropped or assigned')
                a.require(annual['year_metadata']['annual_numeric_or_CI_gate_added'] is False,'New annual CI gate added')
                item.update(observed=expected,passed=True,W_sha256=annual['design']['shared_replicate_weights_sha256']);outputs.append({'case_id':cid,'synthetic_only':True,'executed_input':p,'result':annual})
            else:
                prep=engine.prepare(payload)
                if expected.startswith('reject'):raise AssertionError('Unexpected acceptance')
                receipt=prep['registered_scope_admission'];same(receipt['synthetic_only'],True,'Synthetic admission impersonates ROOT')
                same(receipt['actual_ROOT_admission'],False,'Unapproved scope became actual registration')
                if cid=='valid_remaining_registered_synthetic':same(prep['population_N'],1261,'Remaining scope extrapolated to full4481');same(prep['domain_population_N'],{'remaining':1261},'Exposed domain included in remaining-only estimand')
                item.update(observed=expected,passed=True,admission_receipt=receipt)
        except Exception as e:
            rejected=isinstance(e,(ValueError,OSError,KeyError,TypeError)) and expected.startswith('reject')
            item.update(observed='rejected' if rejected else 'failed',passed=rejected,error={'type':type(e).__name__,'message':str(e)})
        cases.append(item)
    result={'status':'fixed_small_synthetic_and_blank_control_execution','plan_binding':a.binding(HERE/'controls-fixed-before-execution.json'),'engine_binding':a.binding(HERE/'metrics_engine.py'),'admission_binding':a.binding(HERE/'scope_admission.py'),'base_core_binding':a.binding(HERE/'frozen_year_core.py'),'old_core_binding':a.binding(ROOT/'07-statistics/prospective-engine-domain-sol/metrics_engine.py'),'execution_code_binding':a.binding(__file__),'cases':cases,'cases_N':len(cases),'passed_N':sum(c['passed'] for c in cases),'failed_N':sum(not c['passed'] for c in cases),'actual_ROOT_scope_adoption_N':0,'actual_draw_or_human_results_N':0,'actual_machine_labels_read_N':0,'actual_statistics_N':0,'synthetic_answer_rows_max':8}
    with (HERE/'control-results-first.json').open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    with (HERE/'synthetic-small-results-first.json').open('x') as f:json.dump({'data_role':'synthetic_only','outputs':outputs,'actual_human_or_machine_results':False},f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    print(json.dumps({'cases':len(cases),'passed':result['passed_N'],'failed':result['failed_N'],'actual_results':0}))

if __name__=='__main__':main()
