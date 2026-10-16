"""Independent exact-range readback of fixed exposed controls; no classification.

Only the unchanged source-only adapter resolves frozen source handles. Relation
or dimension modules are never imported or executed. Expects final audit to
create selected-final-attempt.json after actual freeze inspection.
"""
from pathlib import Path
import sys, importlib.util, json, hashlib
sys.dont_write_bytecode=True
G=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
OLD=G/'06-coding/rule-five-dimension-joint-root/versions/joint-v8-target-product-gap-sol'
inputs={}
def bind(p):
    p=Path(p).resolve();b=p.read_bytes();return {'path':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
def load(p):
    s=bind(p);inputs[s['path']]=s;return json.loads(Path(p).read_bytes())
def verify(s):
    b=bind(s['path']);inputs[b['path']]=b
    assert all(b[k]==s[k] for k in ['path','bytes','sha256']),s['path']
def save(name,x):
    with (OUT/name).open('x',encoding='utf8') as f:
        json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
selection=load(OUT/'selected-final-attempt.json')
attempt=Path(selection['path']);pre=load(attempt/'pre-execution-seal.json')
results=load(attempt/'results.json');summary=load(attempt/'summary.json')
freeze=load(G/'08-audits/current-machine-rare-disagreement-semantic-20261011-sol/readable-disagreement-selection-freeze.json')
eligible={r['id'] for r in freeze['eligible_all_records']}
assert len(freeze['eligible_all_records'])==130 and len(eligible)==98
allowed_pairs={(r['id'],r['dimension']) for r in freeze['eligible_all_records']}
controls=[];synthetics={}
for s in pre['controls']:
    verify(s);obj=load(s['path'])
    for c in obj['cases']:
        if 'packet_binding' in c:controls.append(c)
        else:
            assert c['name'] not in synthetics
            synthetics[c['name']]=c
assert len(controls)==130
assert {(c['name'].split('/')[0],c['name'].split('/')[1]) for c in controls}==allowed_pairs
assert len(results)==summary['case_N']==130+len(synthetics)
assert sum(r['hard_assertion'] for r in results)==summary['hard_assertion_case_N']
assert sum(r['hard_assertion'] and r['passed'] for r in results)==summary['hard_passed_N']
assert sum(r['hard_assertion'] and not r['passed'] for r in results)==summary['hard_failed_N']
assert sum(not r['hard_assertion'] for r in results)==summary['pending_N']
assert [r['name'] for r in results if not r['passed']]==[r['name'] for r in summary['all_failures']]
adapter_path=OLD/'source_packet.py';inputs[str(adapter_path)]=bind(adapter_path)
spec=importlib.util.spec_from_file_location('independent_source_handle_adapter',adapter_path)
adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
units={};packet_inventory=[];checks=[];used={};control_by_name={c['name']:c for c in controls}
for row in results:
    assert not row.get('error'),row['name']
    if row['name'] in control_by_name:
        ctrl=control_by_name[row['name']]
        assert row['packet_binding']==ctrl['packet_binding']
        rid=row['name'].split('/')[0];assert rid in eligible
        if rid not in units:
            verify(ctrl['packet_binding']);packet=load(ctrl['packet_binding']['path'])
            assert packet['source_id']==packet['source_bundle']['source_record']['id']==rid
            u=adapter.semantic_unit(packet['source_bundle'])
            assert 'id' not in u and 'id' not in u['source_bundle']['source_record']
            assert u['text']==packet['source_bundle']['source_record']['text']
            units[rid]=u
            packet_inventory.append(dict(ctrl['packet_binding'],source_id=rid,actual_output_id=packet['output_id']))
        u=units[rid]
    else:
        ctrl=synthetics[row['name']];u=ctrl['semantic_input'];rid='synthetic:'+row['name']
    assert row['expected']==ctrl['expected'] and row['hard_assertion']==ctrl['hard_assertion']
    assert row['passed']==all(row['candidate']['values'][d]==v for d,v in row['expected'].items())
    assert row['SEEc_complete_decisions_equal']==all(row['candidate']['decisions'][d]==row['baseline']['decisions'][d] for d in ['S','E','Ec'])
    assert row['SEEc_complete_decisions_equal'],row['name']
    by_id={}
    for c in u.get('contexts',[]):
        cid=c['context_id']
        assert cid not in by_id or by_id[cid]==c
        by_id[cid]=c
    def quote(q,scope):
        cid=q.get('context_id')
        if not cid:return
        assert cid in by_id,(rid,cid)
        c=by_id[cid];a=q['start'];b=q['end']
        assert type(a) is int and type(b) is int and 0<=a<b<=len(c['text']),(rid,cid,a,b)
        assert q['text']==c['text'][a:b] and q['source_ref']==c['source_ref'],(rid,cid,scope)
        origin=u.get('derived_context_origins',{}).get(cid,{})
        k=(rid,cid,a,b,q['text'],json.dumps(q['source_ref'],sort_keys=True,ensure_ascii=False))
        checks.append({'case':row['name'],'side':scope,'context_id':cid,'start':a,'end':b,'quote_sha256':hashlib.sha256(q['text'].encode()).hexdigest(),'exact_text_and_source_ref':True})
        used[k]={'id':rid,'context_id':cid,'source_bundle_pointer':origin.get('source_bundle_pointer'),
                 'start':a,'end':b,'quote_sha256':hashlib.sha256(q['text'].encode()).hexdigest(),
                 'context_text_sha256':hashlib.sha256(c['text'].encode()).hexdigest(),'source_ref':q['source_ref']}
    def current(q,scope):
        if q is None:return
        a=q['start'];b=q['end']
        assert type(a) is int and type(b) is int and 0<=a<b<=len(u['text'])
        assert q['text']==u['text'][a:b],(row['name'],scope)
    def nested_quotes(value,scope):
        if isinstance(value,dict):
            if {'context_id','start','end','text','source_ref'}<=set(value):quote(value,scope)
            for key,child in value.items():nested_quotes(child,scope+'/'+key)
        elif isinstance(value,list):
            for i,child in enumerate(value):nested_quotes(child,scope+'/'+str(i))
    for side in ['candidate','baseline']:
        state=row[side]
        assert set(state['decisions'])=={'S','E','Ec','I','F'}
        assert state['values']=={d:q['value'] for d,q in state['decisions'].items()}
        for d,q in state['decisions'].items():
            current(q['current_anchor'],side+':'+d)
            current(q['current_proposition'],side+':'+d)
            for e in q['context_evidence']:quote(e,side+':decision:'+d)
        for rel in state['relations']:
            current(rel['current_anchor'],side+':relation')
            for q in rel['context_evidence']:quote(q,side+':relation:'+rel['kind'])
            nested_quotes(rel['details'],side+':relation_details:'+rel['kind'])
        for d,q in state['decisions'].items():nested_quotes(q['details'],side+':decision_details:'+d)
save('finite-control-exact-quotes-readback.json',{'final_attempt':selection,'actual_packet_N':len(units),
     'real_dimension_pair_N':130,'synthetic_case_N':len(synthetics),'case_N':len(results),
     'hard_passed_N':summary['hard_passed_N'],'hard_failed_N':summary['hard_failed_N'],'pending_N':summary['pending_N'],
     'all_original_failures':summary['all_failures'],'exact_quote_check_N':len(checks),'unique_quote_N':len(used),
     'all_context_quotes_and_current_spans_exact':True,'all_SEEc_complete_decisions_identical':True,
     'source_only_adapter_replayed_not_classifier':True,'candidate_relation_or_dimension_code_executed':False,
     'semantic_correctness_or_external_original_certified':False,'checks':checks})
save('actual-opened-exposed-packets-and-used-quote-resources.json',{'packet_bindings':packet_inventory,
     'unique_used_quote_resources':list(used.values()),'all_packet_ids_in_frozen98_from130':True,
     'all_packet_bodies_already_exposed_no_human200_or_remaining_opened':True,
     'external_original_files_cited_in_source_ref_not_opened':True,
     'purpose':'structural exact-range receipt checking; no repeated semantic adjudication or prediction'})
for s in inputs.values():assert bind(s['path'])==s
save('finite-quote-input-bindings.json',{'inputs':list(inputs.values()),'unchanged_before_after':True})
print(json.dumps({'packet_N':len(units),'case_N':len(results),'exact_quote_check_N':len(checks),'unique_quote_N':len(used),'classifier_executed':False}))
