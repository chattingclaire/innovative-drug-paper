"""Eight receipt-only checks from completed controls; zero judge/view calls."""
import copy,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
from merge_common import bind,load,save
import rule_driver
import receive_boundaries as new

H=Path(__file__).resolve().parent
R=H.parent
E=R.parent/'rule-repair-v14/E-source'

def run():
    manifest=load(H/'algorithm-bindings.json')
    modules=rule_driver.load_frozen_coders(H,manifest['modules'])
    old_path=H/'initial-frozen-preparation/receive_boundaries.py'
    spec=importlib.util.spec_from_file_location('initial_boundary',old_path)
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    fpath=R/'F-residual/attempt01/results.json';spath=R/'S-residual/attempt01/results.json'
    epath=E/'attempt03-corrected/results.json'
    f=next(x for x in load(fpath) if x['name']=='NONHUMAN_missing_requested_list_boundary')
    s=next(x for x in load(spath) if x['name']=='current_treatment_parallel_risk')
    e=next(x for x in load(epath) if x['name']=='independent_S_positive_with_unclosed_standard')
    ecpath=R.parent/'rule-repair-v14/Ec-source/geometry-attempt01/results.json'
    ec=next(x for x in load(ecpath) if x['name']=='finite_definition/explicit_conflicting_components')
    def result(fn):
        try:return {'accepted':True,'value':fn()}
        except (ValueError,KeyError) as error:return {'accepted':False,'error_type':type(error).__name__,'reason':str(error)}
    rows=[]
    def check(name,fn,expected,initial=None):
        actual=result(fn);assert actual['accepted']==expected,(name,actual)
        row={'name':name,'expected_accepted':expected,'actual':actual,'passed':True}
        if initial:row['initial_frozen_behavior']=result(initial)
        rows.append(row)
    def log(record,stops=()):
        return {k:copy.deepcopy(record[k]) for k in ['material_requests','source_requests']}|{
          'actual_text_geometry_events':copy.deepcopy(record['source_events']),
          'uniform_source_protocol_check':{'dependency_stop_reasons':list(stops)}}
    a=f['baseline'];b=f['candidate'];stops=b['routing_proof']['dependency_stop_reasons']
    def source_call(mod,record,actual_stops):
        return mod.source_delta(a,record,log(a),log(record,actual_stops),modules,record['decisions'])
    check('new_F_both_ledgers_and_actual_stop',lambda:source_call(new,b,stops),True)
    for key in ['source_requests','material_requests']:
        bad=copy.deepcopy(b);bad[key]=[q for q in bad[key] if q['path']!='F_requested_qualification_scope']
        check('reject_missing_'+key,lambda bad=bad:source_call(new,bad,stops),False,
              lambda bad=bad:source_call(old,bad,stops))
    missing=[x for x in stops if x!='F_requested_qualification_scope_unresolved']
    check('reject_missing_actual_F_stop_despite_old_E_stop',lambda:source_call(new,b,missing),False,
          lambda:source_call(old,b,missing))
    q=copy.deepcopy(ec['candidate']['material_requests'][0]);q['necessary_dependency']=False
    check('reject_Ec_explicit_not_necessary',lambda:new.validate_new_request(q,modules,ec['candidate']['decisions']),False)
    def pred(x):return dict(x,relation_traces=x.get('relations',[]))
    combined=copy.deepcopy(pred(s['candidate']));dependency=copy.deepcopy(e['candidate']['decisions']['S']['details']['unresolved_material_requests'][0])
    combined['decisions']['S']['details']['unresolved_material_requests'].append(dependency)
    combined['decisions']['S']['details']['material_request_routes'].append(modules['dimensions']._material_request_route(dependency))
    sourcecase=next(x for x in load(R/'S-residual/controls-index.json')['cases'] if x['name']==s['name'])
    bundle={'source_record':{'text':sourcecase['semantic_input']['text']}}
    check('allow_two_registered_S_mechanisms_receipt_composition',lambda:new.conditional_s_basis(pred(s['baseline']),combined,bundle,modules),True,
          lambda:old.conditional_s_basis(pred(s['baseline']),combined,bundle,modules))
    unrelated=copy.deepcopy(combined);unrelated['decisions']['S']['details']['matched_risk_or_content']='药价'
    check('reject_unrelated_S_positive_even_with_necessary_dependency',lambda:new.conditional_s_basis(pred(s['baseline']),unrelated,bundle,modules),False)
    check('retain_existing_independent_S_positive_with_dependency',lambda:new.conditional_s_basis(pred(e['baseline']),pred(e['candidate']),{'source_record':{'text':''}},modules),True)
    output={'status':'PASSED_EIGHT_TARGETED_RECEIPT_CHECKS','checks':rows,
      'source_result_bindings':[bind(p) for p in [fpath,spath,epath,ecpath]],
      'initial_boundary':bind(old_path),'revised_boundary':bind(H/'receive_boundaries.py'),
      'check_script':bind(__file__),'classifier_calls':0,'new_semantic_controls':0,
      'synthetic_composition_is_only_a_receipt_boundary_check_not_a_claim_of_actual_coding':True,
      'old16_or_integrated531_rerun':False}
    save(H/'receiver-revision-checks.json',output)
    print(json.dumps({'check_N':len(rows),'pass_N':sum(x['passed'] for x in rows)},ensure_ascii=False))

if __name__=='__main__':run()
