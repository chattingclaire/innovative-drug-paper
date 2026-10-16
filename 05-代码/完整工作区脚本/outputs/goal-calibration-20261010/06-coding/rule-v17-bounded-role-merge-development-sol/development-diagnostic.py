"""One post-seal nonblind development comparison and sklearn crosscheck.
No rule inference imports or calls. No CI, sampling or acceptance decision.
"""
from pathlib import Path
from fractions import Fraction
import hashlib, json, datetime, math
import sklearn
from sklearn.metrics import cohen_kappa_score, precision_score, recall_score, f1_score, accuracy_score, confusion_matrix

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
DIMENSIONS=('S','E','Ec','I','F')

def h(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def binding(path):
    p=Path(path).resolve();return {'path':str(p),'sha256':h(p),'bytes':p.stat().st_size}
def write(name, obj):
    with (OUT/name).open('x',encoding='utf8') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def rows(path):return [(i,json.loads(b),b) for i,b in enumerate(Path(path).read_bytes().splitlines(keepends=True),1) if b.strip()]
def ratio(a,b,reason):
    if b==0:return {'value':None,'exact':None,'NA_reason':reason}
    v=Fraction(a,b);return {'value':float(v),'exact':str(v),'NA_reason':None}
def metrics(tp,fp,fn,tn):
    n=tp+fp+fn+tn
    po=ratio(tp+tn,n,'no binary comparable units')
    expected_n=(tp+fp)*(tp+fn)+(fn+tn)*(fp+tn)
    return {'N_binary':n,'TP':tp,'FP':fp,'FN':fn,'TN':tn,
      'kappa':ratio(n*(tp+tn)-expected_n,n*n-expected_n,'expected agreement=1 or empty binary denominator'),
      'P':ratio(tp,tp+fp,'no candidate positives'), 'R':ratio(tp,tp+fn,'no reference positives'),
      'F1':ratio(2*tp,2*tp+fp+fn,'no positive cases in either vector'), 'Po':po,
      'Ppos':ratio(2*tp,2*tp+fp+fn,'no positive cases in either vector'),
      'Pneg':ratio(2*tn,2*tn+fp+fn,'no negative cases in either vector')}

def main():
    run=OUT/'run77-first';candidate=run/'predictions.jsonl';refdir=ROOT/'06-coding/development-reference77-v14-root-adjudicated-v3';reference=refdir/'reference.jsonl'
    prior_dir=ROOT/'06-coding/rule-v16-inline-heading-development-sol';prior=prior_dir/'run77-first/predictions.jsonl'
    assert h(reference)=='004ef126312de9f022c98e038581892a68e5d6c68ca392b74580ebd9b51e093e'
    assert h(refdir/'seal.json')=='e8b5b9cb53c38068aaac8a1fff15c483211394afe1753e1fe91adce5c1d4d98d'
    assert h(prior)=='f12d76f6592ebcca34199b8df1fcdea550f2959f0eebb76d367f3a37694d5d6b'
    seal=json.loads((run/'seal.json').read_text())
    for b in seal['output_files']+seal['implementation_files']:
        assert h(b['path'])==b['sha256'] and Path(b['path']).stat().st_size==b['bytes']
    cr=rows(candidate);rr=rows(reference);pr=rows(prior);source=rows(run/'delivered-complete-source-bundles.jsonl')
    assert len(cr)==len(rr)==len(pr)==len(source)==77
    ids=[x['id'] for _,x,_ in cr]
    assert ids==[x['id'] for _,x,_ in rr]==[x['id'] for _,x,_ in pr]==[b['source_record']['id'] for _,b,_ in source]
    assert len(set(ids))==77
    old={x['id']:(line,x,raw) for line,x,raw in pr};refs={x['id']:(line,x,raw) for line,x,raw in rr}
    source_map={b['source_record']['id']:(line,b,raw) for line,b,raw in source}
    counts={};checks={};derived=[];changes=[];differences=[]
    for d in DIMENSIONS:
        assigned=len(cr);failed=[];null=[];refnull=[];comparable=[];tp=fp=fn=tn=0
        for line,p,raw in cr:
            rline,r,rraw=refs[p['id']]
            if p['implementation_errors'] or not isinstance(p.get('labels'),dict):failed.append(p['id']);continue
            cv=p['labels'][d];rv=r['labels'][d]
            if cv is None:null.append(p['id'])
            if rv is None:refnull.append(p['id'])
            if cv is None or rv is None:continue
            assert type(cv) is int and cv in (0,1) and type(rv) is int and rv in (0,1)
            comparable.append((rv,cv,p['id']))
            if cv==1 and rv==1:tp+=1
            elif cv==1:fp+=1
            elif rv==1:fn+=1
            else:tn+=1
            if cv!=rv:
                differences.append({'id':p['id'],'dimension':d,'candidate':cv,'reference':rv,'candidate_first_line':line,'candidate_first_row_sha256_including_LF':hashlib.sha256(raw).hexdigest(),'reference_line':rline,'reference_row_sha256_including_LF':hashlib.sha256(rraw).hexdigest(),'candidate_evidence':p['decisions'][d],'reference_dimension_provenance':r.get('dimension_provenance_v3',{}).get(d),'reference_historical_metadata_scope':r.get('historical_metadata_scope')})
        m=metrics(tp,fp,fn,tn);m.update(assigned_N=assigned,judged_N=assigned-len(failed),candidate_null_N=len(null),reference_null_N=len(refnull),technical_failed_N=len(failed),null_ids=null,reference_null_ids=refnull,technical_failed_ids=failed,difference_ids=[x['id'] for x in differences if x['dimension']==d]);counts[d]=m
        yt=[x[0] for x in comparable];yp=[x[1] for x in comparable]
        cm=confusion_matrix(yt,yp,labels=[0,1]).tolist()
        independent={'confusion_matrix_reference_rows_candidate_columns':cm,'kappa':float(cohen_kappa_score(yt,yp)),'P':float(precision_score(yt,yp,zero_division=float('nan'))),'R':float(recall_score(yt,yp,zero_division=float('nan'))),'F1':float(f1_score(yt,yp,zero_division=float('nan'))),'Po':float(accuracy_score(yt,yp)),'Ppos':float(f1_score(yt,yp,pos_label=1,zero_division=float('nan'))),'Pneg':float(f1_score(yt,yp,pos_label=0,zero_division=float('nan')))}
        assert cm==[[tn,fp],[fn,tp]]
        for k in ['kappa','P','R','F1','Po','Ppos','Pneg']:
            v=m[k]['value'];sk=independent[k]
            assert (v is None and math.isnan(sk)) or (v is not None and abs(v-sk)<1e-12),(d,k,v,sk)
            if math.isnan(sk):independent[k]=None
        checks[d]={'passed':True,'sklearn':independent,'one_crosscheck_no_rerun':True}
    consumption={x['id']:x for _,x,_ in rows(run/'actual-source-consumption.jsonl')}
    for line,p,raw in cr:
        oline,o,oraw=old[p['id']];rline,r,rraw=refs[p['id']];sline,b,sraw=source_map[p['id']]
        diff={d:{'old':o['labels'][d],'new':p['labels'][d]} for d in DIMENSIONS if p['labels'][d]!=o['labels'][d]}
        selected=[t for t in p['relation_traces'] if t['details'].get('resolution_path')=='primary_literal_complete_operative_standard']
        if diff:changes.append({'id':p['id'],'changed_dimensions':diff,'current_text':b['source_record']['text'],'selected_standard_relations':selected,'new_decisions':{d:p['decisions'][d] for d in diff},'old_line':oline,'old_row_sha256_including_LF':hashlib.sha256(oraw).hexdigest(),'new_line':line,'new_row_sha256_including_LF':hashlib.sha256(raw).hexdigest()})
        log=consumption[p['id']]['uniform_source_reading_log']
        derived.append({'id':p['id'],'old_labels':o['labels'],'new_labels':p['labels'],'reference_labels':r['labels'],'changed_dimensions':diff,'new_first':{'file':binding(candidate),'line':line,'raw_line_sha256_including_LF':hashlib.sha256(raw).hexdigest()},'old_v16_complete77_first':{'file':binding(prior),'line':oline,'raw_line_sha256_including_LF':hashlib.sha256(oraw).hexdigest(),'execution_is_prior_complete_v16_77':True},'reference':{'file':binding(reference),'line':rline,'raw_line_sha256_including_LF':hashlib.sha256(rraw).hexdigest(),'nonblind_AI_development_reference':True,'historical_manual_metadata_preserved':r.get('manual_sha256')},'source_bundle':{'file':binding(run/'delivered-complete-source-bundles.jsonl'),'line':sline,'canonical_object_sha256':hashlib.sha256(json.dumps(b,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'raw_line_sha256_including_LF':hashlib.sha256(sraw).hexdigest(),'source_ref':b['source_record']['source_ref']},'read_receipt_N':len(log['read_receipts']),'use_receipt_N':len(log['use_receipts']),'selected_new_standard_group_N':len(selected),'candidate_source_requests':p['source_requests'],'candidate_technical_failed':bool(p['implementation_errors'])})
    with (OUT/'derived-rows77.jsonl').open('x',encoding='utf8') as f:
        for x in derived:f.write(json.dumps(x,ensure_ascii=False,allow_nan=False)+'\n')
    caveats=['historically exposed nonprobability fixed development77','AI nonblind ROOT adjudicated reference v3; 74 rows retain actual historical v1.1 provenance, three S are root v1.3/source-v14 adjudication','new rule v17 actual single77 run; prior comparator is complete v16 single77 first','not population performance; no CI; no formal acceptance; not human or semantic gold','no candidate/reference/source/manual changes; no score-driven rerun']
    write('metrics-exact.json',{'status':'sealed-first-rule-run-development-diagnostic','formula_orientation':'candidate versus reference: TP=1/1,FP=1/0,FN=0/1,TN=0/0','assigned_record_N':77,'assigned_dimension_N':385,'dimensions':counts,'caveats':caveats})
    write('sklearn-crosscheck.json',{'sklearn_version':sklearn.__version__,'interpreter':'parallel-metrics/.venv existing','crosscheck_invocation_N':1,'all_passed':True,'dimensions':checks,'no_population_CI':True})
    write('five-dimension-changes.json',{'old_candidate_binding':binding(prior),'new_candidate_binding':binding(candidate),'record_changed_N':len(changes),'dimension_changed_N':sum(len(x['changed_dimensions']) for x in changes),'unchanged_record_N':77-len(changes),'changes':changes,'all385_slots_compared':True})
    write('remaining-disagreements.json',{'reference_binding':binding(reference),'difference_dimension_N':len(differences),'differences':differences,'labels_not_modified_after_diagnostic':True})
    write('diagnostic-provenance.json',{'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':'AI with prior A/source-recovery/nonblind diagnostic history; requested GPT-6.1 Sol ultra; actual provider model/setting unknown', 'requested_model':'gpt-6.1-sol','requested_reasoning_effort':'ultra','actual_provider_model_id':None,'actual_provider_setting':None,'candidate_seal':binding(run/'seal.json'),'candidate':binding(candidate),'reference_seal':binding(refdir/'seal.json'),'reference':binding(reference),'old_candidate':binding(prior),'full_source_packet':json.loads((OUT/'source-scope.json').read_text())['source_packet'],'manual':json.loads((OUT/'source-scope.json').read_text())['manual'],'sklearn_version':sklearn.__version__,'actual_cohort_inference_N':1,'model_calls_N':0,'caveats':caveats})
    print(json.dumps({'full77_exact_fourcells':{d:{k:counts[d][k] for k in ['TP','FP','FN','TN']} for d in DIMENSIONS},'changed_record_N':len(changes),'changed_dimension_N':sum(len(x['changed_dimensions']) for x in changes),'sklearn_version':sklearn.__version__,'all_crosscheck_passed':True},ensure_ascii=False))

if __name__=='__main__':main()
