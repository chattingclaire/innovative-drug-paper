"""Mechanical v10 actual-run/composite/statistics readback, never classification."""
from pathlib import Path
from fractions import Fraction
import ast, collections, datetime, hashlib, json, re, zipfile
import xml.etree.ElementTree as ET

A=Path(__file__).resolve().parent;B=A.parents[1]
D=B/'06-coding/rule-v10-if-e-affected-original-common-root';RUN=D/'run-affected-first'
M=B/'06-coding/rule-full4481-v10-if-e-delta-merged-root'
P=B/'06-coding/rule-full4481-v9-delta-merged-root'
N=B/'07-statistics/original-whole-batch-native-snapshot-20261012T0205-root'
ST=B/'07-statistics/current-v10-compatible-native2792-diagnostics-root'
BO=B/'07-statistics/rule-v10-attention-null-bounds-diagnostic-root'
YEAR=B/'07-statistics/annual-year-input-binding-sol'
CODE=B/'06-coding/rule-five-dimension-joint-root/versions/joint-v10-if-e-combined-v2-root'
CONTROL=B/'08-audits/v10-if-e-combination-v2-root/actual-finite-controls-one'
DIMS=('S','E','Ec','I','F')
HASHES={'A':'2ad1cad77f599bd25dbcb3002e09994ad895ecc85b2c6f3019600d96f10c5cb4','B':'6329f4d94a1c667464811326d3a7916be6409a2861da676d69b916aee8a20f4f'}

def now():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def load(p):return json.loads(Path(p).read_bytes())
def save(name,x):
    with (A/name).open('x',encoding='utf8') as f:json.dump(x,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
def bind(p):
    p=Path(p).resolve();h=hashlib.sha256();size=0
    with p.open('rb') as f:
        while chunk:=f.read(1024*1024):h.update(chunk);size+=len(chunk)
    return dict(path=str(p),bytes=size,sha256=h.hexdigest())
checked={}
def exact(x):
    if x['path'] not in checked:checked[x['path']]=bind(x['path'])
    assert all(checked[x['path']][k]==x[k] for k in ('bytes','sha256')),x['path']
    return checked[x['path']]
def verify_own_seal(path,keys=('files','output_files','implementation_files','control_inputs')):
    seal=load(path)
    for k in keys:
        for x in seal.get(k,[]):exact(x)
    return seal

# Raw JSON field projection: skipped text/reason/source fields are never decoded.
STR=re.compile(rb'"(?:[^"\\]|\\.)*"',re.S)
TOKEN=re.compile(rb'[\[\]{}"]')
WS=re.compile(rb'\s*')
def skip(raw,i):
    i=WS.match(raw,i).end()
    if raw[i]==34:return STR.match(raw,i).end()
    if raw[i] in (123,91):
        depth=1;i+=1
        while depth:
            m=TOKEN.search(raw,i);assert m
            p=m.start();c=raw[p]
            if c==34:i=STR.match(raw,p).end();continue
            depth+=1 if c in (123,91) else -1;i=p+1
        return i
    m=re.match(rb'[^\s,}\]]+',raw[i:]);assert m
    return i+m.end()
def fields(raw):
    i=WS.match(raw,0).end();assert raw[i]==123;i+=1;out={}
    while True:
        i=WS.match(raw,i).end()
        if raw[i]==125:return out
        key=STR.match(raw,i);assert key
        name=json.loads(key.group());i=WS.match(raw,key.end()).end();assert raw[i]==58
        a=WS.match(raw,i+1).end();end=skip(raw,a);assert name not in out;out[name]=raw[a:end]
        i=WS.match(raw,end).end()
        if raw[i]==44:i+=1
        else:assert raw[i]==125
def project(raw,keys):
    fs=fields(raw);return {k:json.loads(fs[k]) for k in keys}
def prediction(raw):
    fs=fields(raw);sid=json.loads(fs['id']);labels=json.loads(fs['labels'])
    assert set(labels)==set(DIMS) and all(v is None or type(v) is int and v in (0,1) for v in labels.values())
    decisions=fields(fs['decisions']) if 'decisions' in fs else {}
    if decisions:
        assert set(decisions)==set(DIMS)
        assert all(json.loads(fields(decisions[d])['value'])==labels[d] for d in DIMS)
    if 'implementation_errors' in fs:assert json.loads(fs['implementation_errors'])==[]
    return dict(id=sid,labels=labels,raw_decisions=decisions,raw=raw)
def read_predictions(path):
    out={}
    with Path(path).open('rb') as f:
        for raw in f:
            x=prediction(raw);assert x['id'] not in out;out[x['id']]=x
    return out
def eq_dec(a,b):return json.loads(a)==json.loads(b) # mechanical complete-decision comparison, no reason interpretation/output

def ratio(a,b):return None if b==0 else float(Fraction(a,b))
def metric(pairs):
    counts=collections.Counter(pairs);a=counts[(1,1)];b=counts[(0,1)];c=counts[(1,0)];d=counts[(0,0)];n=a+b+c+d
    pe_num=(a+b)*(a+c)+(d+b)*(d+c)
    return dict(N=n,TP=a,FP=b,FN=c,TN=d,reference_positive_N=a+c,reference_negative_N=b+d,prediction_positive_N=a+b,prediction_negative_N=c+d,Po=ratio(a+d,n),Pe=ratio(pe_num,n*n),kappa=ratio((a+d)*n-pe_num,n*n-pe_num) if n else None,Precision=ratio(a,a+b),Recall=ratio(a,a+c),F1=ratio(2*a,2*a+b+c),positive_agreement=ratio(2*a,2*a+b+c),negative_agreement=ratio(2*d,2*d+b+c),specificity=ratio(d,d+b),NPV=ratio(d,d+c))
def equal(actual,wanted,path=''):
    if isinstance(actual,dict):
        assert isinstance(wanted,dict) and set(actual)==set(wanted),(path,'keys')
        for k in actual:equal(actual[k],wanted[k],path+'/'+str(k))
    elif isinstance(actual,list):
        assert isinstance(wanted,list) and len(actual)==len(wanted),(path,'length')
        for i,(a,b) in enumerate(zip(actual,wanted)):equal(a,b,path+'/'+str(i))
    elif isinstance(actual,float):assert wanted is not None and abs(actual-wanted)<1e-12,(path,actual,wanted)
    else:assert actual==wanted,(path,actual,wanted)

def reference_only_ACD(side):
    """Decode only reference ID A, dimension C and numeric D, not B/reasons/other columns."""
    path=B/f'09-delivery/agent-review-20261010/真人4项复核后-v2/编码复核表-{side}.xlsx'
    binding=bind(path);assert binding['sha256']==HASHES[side]
    with zipfile.ZipFile(path) as z:
        wb=ET.fromstring(z.read('xl/workbook.xml'));rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        sheet=next(x for x in wb.iter() if x.tag.rsplit('}',1)[-1]=='sheet' and x.attrib['name']=='编码表')
        rid=sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']
        target=next(x.attrib['Target'] for x in rels if x.attrib['Id']==rid)
        sheetpath=target.lstrip('/') if target.startswith('/') else 'xl/'+target
        raw=z.read(sheetpath);wanted=[];indices=set()
        for row in re.finditer(rb'<(?:[A-Za-z0-9_]+:)?row\b[^>]*\br="(\d+)"[^>]*>(.*?)</(?:[A-Za-z0-9_]+:)?row>',raw,re.S):
            if int(row.group(1))<7:continue
            cells={}
            for cm in re.finditer(rb'<(?:[A-Za-z0-9_]+:)?c\b[^>]*\br="([A-Z]+)\d+"[^>]*(?:/>|>.*?</(?:[A-Za-z0-9_]+:)?c>)',row.group(2),re.S):
                col=cm.group(1).decode('ascii')
                if col not in ('A','C','D'):continue
                cell=ET.fromstring(re.sub(rb'(<\/?)[A-Za-z0-9_]+:',rb'\1',cm.group()));v=cell.find('v');typ=cell.attrib.get('t')
                if typ=='s':
                    if v is not None:cells[col]=('s',int(v.text));indices.add(int(v.text))
                elif typ=='inlineStr':cells[col]=('literal',''.join(t.text or '' for t in cell.iter('t')))
                elif v is not None:
                    val=v.text;cells[col]=('literal',int(val) if re.fullmatch(r'-?\d+',val) else float(val))
            if 'A' in cells:wanted.append(cells)
        strings={}
        if indices:
            shared=z.read('xl/sharedStrings.xml')
            for i,m in enumerate(re.finditer(rb'<(?:[A-Za-z0-9_]+:)?si\b[^>]*>.*?</(?:[A-Za-z0-9_]+:)?si>',shared,re.S)):
                if i in indices:
                    node=ET.fromstring(re.sub(rb'(<\/?)[A-Za-z0-9_]+:',rb'\1',m.group()));strings[i]=''.join(t.text or '' for t in node.iter('t'))
            assert indices<=set(strings)
        out={}
        for row in wanted:
            vals={k:(strings[v] if t=='s' else v) for k,(t,v) in row.items()}
            sid=str(vals['A']).strip();sid=sid if sid.startswith('RECODE25-') else 'RECODE25-'+sid.zfill(5)
            dim=str(vals['C']).split('（')[0].split('(')[0].strip().split()[0];value=vals['D']
            assert dim in DIMS and value in (0,1) and type(value) in (int,float) and (sid,dim) not in out
            out[(sid,dim)]=int(value)
    assert len(out)==385 and len({sid for sid,d in out})==77
    return out,binding

def directed(pred,ref):
    out={}
    for d in DIMS:
        allocation=[(sid,v) for (sid,dim),v in ref.items() if dim==d];pairs=[];missing=[];null=[]
        for sid,v in allocation:
            if sid not in pred:missing.append(dict(id=sid,reference=v))
            elif pred[sid]['labels'][d] is None:null.append(dict(id=sid,reference=v))
            else:pairs.append((v,pred[sid]['labels'][d]))
        m=metric(pairs);m.update(allocated_N=len(allocation),allocated_reference_positive_N=sum(v for _,v in allocation),allocated_reference_negative_N=sum(v==0 for _,v in allocation),missing_N=len(missing),lawful_null_N=len(null),binary_coverage=ratio(len(pairs),len(allocation)),excluded_positive_N=sum(x['reference'] for x in missing+null),excluded_negative_N=sum(x['reference']==0 for x in missing+null),missing=missing,lawful_null=null,conditional_core_targets_passed=all(m[k] is not None and m[k]>=.8 for k in ('kappa','Precision','Recall','F1')),formal_validation_complete=False);out[d]=m
    return out

def bounds(rows,key):
    n=len(rows);p={d:sum(x['labels'][d]==1 for x in rows) for d in DIMS};u={d:sum(x['labels'][d] is None for x in rows) for d in DIMS};pt=sum(p.values());ut=sum(u.values())
    dims={d:dict(positive_N=p[d],negative_N=n-p[d]-u[d],unresolved_N=u[d],positive_assignment_share_among_observed=ratio(p[d],pt),positive_assignment_share_lower_bound=ratio(p[d],pt+ut-u[d]),positive_assignment_share_upper_bound=ratio(p[d]+u[d],pt+u[d]),clause_prevalence_lower_bound=ratio(p[d],n),clause_prevalence_upper_bound=ratio(p[d]+u[d],n)) for d in DIMS}
    stable=[dict(higher_dimension=a,lower_dimension=b,minimum_higher_positive_N=p[a],maximum_lower_positive_N=p[b]+u[b]) for a in DIMS for b in DIMS if a!=b and p[a]>p[b]+u[b]]
    return dict(group=key,clause_N=n,observed_positive_assignment_N=pt,unresolved_assignment_N=ut,dimensions=dims,strict_within_group_rankings_immune_to_unresolved_labels=stable,conditional_on_correct_observed_machine_labels=True)

def main():
    planned=[D/'original-input-lineage-sidecar.json',D/'algorithm-bindings.json',D/'ROOT-pre-inference-adoption-sidecar.json',RUN/'execution.json',RUN/'freeze.json',RUN/'seal.json',M/'seal.json',M/'composite-status.json',ST/'seal.json',ST/'metrics.json',BO/'seal.json',BO/'conditional-bounds.json',N/'seal.json',N/'coverage.json',CONTROL/'pre-execution-seal.json',CONTROL/'output-seal.json']
    save('audit-r02-pre-execution-freeze.json',dict(at_utc=now(),audit=bind(__file__),planned_metadata_bindings=[bind(p) for p in planned],mode='read-only mechanical projection/hash/comparison and integer formula recomputation',no_model_or_classifier=True,no_policy_or_human_reason_interpretation=True,reference_cells_decoded_only=['A IDs','C dimensions','D numeric values'],reuse_old_passed_parent_seal=True))
    # Current seals only; ancestors are bound, not re-audited or semantically read.
    for p in (RUN/'seal.json',M/'seal.json',ST/'seal.json',BO/'seal.json',N/'seal.json'):verify_own_seal(p)
    plan=load(D/'impact-closure-plan.json');lineage=load(D/'original-input-lineage-sidecar.json');alg=load(D/'algorithm-bindings.json');scope=load(D/'frozen-scope.json');execution=load(RUN/'execution.json');freeze=load(RUN/'freeze.json');adopt=load(D/'ROOT-pre-inference-adoption-sidecar.json');status=load(M/'composite-status.json')
    assert alg['algorithm_version']=='joint-v10-if-e-combined-v2-root'
    actual_control=load(CONTROL/'pre-execution-seal.json');assert len(load(CONTROL/'summary.json')['all_failures'])==1
    code=[]
    for x in alg['modules']:
        exact(x);control=next(y for y in actual_control['code'] if Path(y['path']).name==Path(x['path']).name);exact(control);assert x['sha256']==control['sha256']
        assert next(y['sha256'] for y in freeze['implementation_files'] if Path(y['path']).name==Path(x['path']).name)==x['sha256'];code.append(x)
    assert datetime.datetime.fromisoformat(adopt['at_utc'])<datetime.datetime.fromisoformat(execution['started_at_utc'])
    assert datetime.datetime.fromisoformat(freeze['created_at_utc'])<datetime.datetime.fromisoformat(execution['started_at_utc'])<datetime.datetime.fromisoformat(execution['finished_at_utc'])
    assert scope['max_actual_cohort_inference_runs']==freeze['max_actual_cohort_inference_runs']==execution['actual_cohort_inference_runs']==1
    assert execution['actual_record_N']==37 and execution['actual_dimension_N']==execution['retained_decision_N']==185 and execution['technical_failure_dimension_N']==execution['lawful_null_N']==0 and execution['implementation_errors']==[]
    assert execution['no_reference_read'] is True and scope['new_material_adopted'] is False and scope['neutral_projection_GO'] is False
    exact(lineage['original_source']);exact(lineage['subset_source']);raw_parent=Path(lineage['original_source']['path']).read_bytes();raw_subset=Path(lineage['subset_source']['path']).read_bytes();parent_lines=raw_parent.splitlines(keepends=True);subset_lines=raw_subset.splitlines(keepends=True)
    assert len(parent_lines)==4481 and len(subset_lines)==len(lineage['rows'])==37
    po=[];offset=0
    for raw in parent_lines:po.append(offset);offset+=len(raw)
    so=[];offset=0
    for raw in subset_lines:so.append(offset);offset+=len(raw)
    selected=[]
    for i,row in enumerate(lineage['rows']):
        j=row['parent_ordinal_1based']-1;raw=subset_lines[i];assert raw==parent_lines[j]
        assert row['subset_ordinal_1based']==i+1 and row['parent_utf8_start']==po[j] and row['parent_utf8_end']==po[j]+len(raw) and row['subset_utf8_start']==so[i] and row['subset_utf8_end']==so[i]+len(raw)
        assert hashlib.sha256(raw).hexdigest()==row['line_sha256']
        sid=json.loads(fields(fields(raw)['source_record'])['id']);assert sid==row['id'];selected.append(sid)
    assert selected==scope['approved_record_ids']==plan['affected_record_ids']
    del raw_parent,raw_subset,parent_lines,subset_lines
    delta=read_predictions(RUN/'predictions.jsonl');parent=read_predictions(P/'predictions.jsonl');merged=read_predictions(M/'predictions.jsonl');assert list(delta)==selected and len(parent)==len(merged)==4481 and list(parent)==list(merged)
    deliveries=[loadline for loadline in (json.loads(line) for line in (RUN/'input-deliveries.jsonl').read_bytes().splitlines())]
    ledger=[json.loads(line) for line in (RUN/'execution-ledger.jsonl').read_bytes().splitlines()];assert len(deliveries)==len(ledger)==37
    for i,(row,delivery,event) in enumerate(zip(lineage['rows'],deliveries,ledger)):
        assert delivery['source_id']==event['id']==selected[i] and delivery['input_line_1based']==i+1 and delivery['input_line_sha256']==row['line_sha256']
        assert delivery['input_start_utf8_byte']==row['subset_utf8_start'] and delivery['input_end_utf8_byte_exclusive']==row['subset_utf8_end'] and delivery['same_common_JSONL_identity_verified'] is True
        exact(delivery['actual_packet_binding']);assert delivery['source_bundle_sha256']==event['source_bundle_sha256']
        assert event['labels']==delta[selected[i]]['labels'] and event['technical_failure'] is False and event['one_adapter_view_judge_attempt_only'] is True
        assert event['index_1based']==i+1 and execution['started_at_utc']<=event['at_utc']<=execution['finished_at_utc']
    def slots(path,preds,N):
        seen=set()
        with path.open('rb') as f:
            for raw in f:
                fs=fields(raw);s=project(raw,('id','dimension','technical_failure','rules_null','rule_value','rule_executed','status','record_implementation_errors','global_implementation_errors'))
                key=(s['id'],s['dimension']);assert key not in seen;seen.add(key)
                assert s['rule_executed'] is True and s['technical_failure'] is False and s['record_implementation_errors']==s['global_implementation_errors']==[]
                assert s['rule_value']==preds[s['id']]['labels'][s['dimension']] and s['rules_null']==(s['rule_value'] is None)
                assert eq_dec(fs['retained_rule_decision'],preds[s['id']]['raw_decisions'][s['dimension']])
        assert len(seen)==N and seen=={(sid,d) for sid in preds for d in DIMS}
    slots(RUN/'all-dimension-slots.jsonl',delta,185);slots(M/'all-dimension-slots.jsonl',merged,22405)
    origins=[json.loads(line) for line in (M/'execution-origin-lineage.jsonl').read_bytes().splitlines()];old_orig_raw=(P/'execution-origin-lineage.jsonl').read_bytes().splitlines(keepends=True)
    assert len(origins)==len(old_orig_raw)==4481
    labels_changed=[];decisions_changed=[];origin_counts=collections.Counter();raw_immutable_dimension_diff=0
    for i,((sid,z),origin,old_origin_raw) in enumerate(zip(merged.items(),origins,old_orig_raw),1):
        a=parent[sid];actual=delta[sid] if sid in delta else a;assert z['raw']==actual['raw']
        assert origin['id']==sid and origin['corpus_ordinal_1based']==i and origin['actual_prediction_line_sha256']==hashlib.sha256(z['raw']).hexdigest() and origin['prediction_line_bytes']==len(z['raw'])
        origin_counts[origin['actual_inference_algorithm']]+=1
        if sid in delta:assert origin['actual_inference_algorithm']=='joint-v10-if-e-combined-v2-root' and Path(origin['actual_run_directory'])==RUN
        else:
            old=json.loads(old_origin_raw)
            for k in ('id','actual_inference_algorithm','actual_run_directory','actual_prediction_line_sha256','prediction_line_bytes'):assert origin[k]==old[k]
            ib=origin['inherited_parent_origin_binding'];assert ib['record_key']==sid and ib['line_sha256']==hashlib.sha256(old_origin_raw).hexdigest()
        for d in DIMS:
            if a['labels'][d]!=z['labels'][d]:labels_changed.append(dict(id=sid,dimension=d,old=a['labels'][d],new=z['labels'][d]))
            if not eq_dec(a['raw_decisions'][d],z['raw_decisions'][d]):decisions_changed.append(dict(id=sid,dimension=d))
            if d in ('S','Ec'):assert eq_dec(a['raw_decisions'][d],z['raw_decisions'][d]);raw_immutable_dimension_diff+=a['raw_decisions'][d]!=z['raw_decisions'][d]
    assert len(labels_changed)==len(decisions_changed)==8 and collections.Counter(x['dimension'] for x in labels_changed)=={'I':7,'F':1}
    assert dict(origin_counts)==status['actual_execution_algorithm_record_N']
    counts={d:dict(positive_N=sum(x['labels'][d]==1 for x in merged.values()),negative_N=sum(x['labels'][d]==0 for x in merged.values()),lawful_null_N=sum(x['labels'][d] is None for x in merged.values())) for d in DIMS};equal(counts,status['counts']);assert sum(x['lawful_null_N'] for x in counts.values())==241
    save('actual-run-and-composite-readback-r02.json',dict(at_utc=now(),actual37_v15_rawline_ordinal_hash_exact=True,code_same_as_actual225_sealed_snapshot=code,ROOT_adoption_at=adopt['at_utc'],started_at=execution['started_at_utc'],single_actual_pass=True,record_N=37,dimension_N=185,technical_failure_N=0,lawful_null_N=0,composite_record_N=4481,composite_dimension_N=22405,composite_lawful_null_N=241,actual37_and_inherited4444_line_bytes_exact=True,all_slots_complete_decisions_match=True,all4481_S_Ec_full_decisions_equal=True,raw_S_Ec_decision_byte_difference_N=raw_immutable_dimension_diff,origin_counts=dict(origin_counts),actual_label_changes=labels_changed,actual_decision_changes=decisions_changed,counts=counts,parent_previous_audit_reused=True,no_semantic_source_interpretation=True))
    native=read_predictions(N/'selected-records.jsonl');assert len(native)==2792 and set(native)<=set(merged)
    coverage=load(N/'coverage.json');root_metrics=load(ST/'metrics.json');assert coverage==root_metrics['native_coverage']
    assert coverage['selected_record_N']==2792 and coverage['missing_record_N']==1689 and coverage['record_output_coverage']==ratio(2792,4481)
    assert sum(x['labels'][d] is None for x in native.values() for d in DIMS)==39
    assert sum(x['labels'][d] in (0,1) for x in native.values() for d in DIMS)==13921
    for d in DIMS:
        got=dict(positive_N=sum(x['labels'][d]==1 for x in native.values()),negative_N=sum(x['labels'][d]==0 for x in native.values()),lawful_null_N=sum(x['labels'][d] is None for x in native.values()),missing_N=1689);equal(got,coverage['per_dimension'][d])
    ra,ab=reference_only_ACD('A');rb,bb=reference_only_ACD('B');assert ra==rb
    rm=directed(merged,ra);nm=directed(native,ra);equal(rm,root_metrics['development77_rule_metrics']);equal(nm,root_metrics['development77_native_metrics'])
    matched={};machine={}
    for d in DIMS:
        keys=[(sid,dim) for sid,dim in ra if dim==d and sid in native and merged[sid]['labels'][d] is not None and native[sid]['labels'][d] is not None]
        matched[d]=dict(matched_binary_N=len(keys),rules=metric([(ra[k],merged[k[0]]['labels'][d]) for k in keys]),native=metric([(ra[k],native[k[0]]['labels'][d]) for k in keys]))
        m=metric([(merged[s]['labels'][d],native[s]['labels'][d]) for s in native if merged[s]['labels'][d] is not None and native[s]['labels'][d] is not None])
        machine[d]=dict(binary_pair_N=m['N'],native_output_N=2792,native_missing_N=1689,both_1=m['TP'],rule0_native1=m['FP'],rule1_native0=m['FN'],both_0=m['TN'],Po=m['Po'],Pe=m['Pe'],kappa=m['kappa'],positive_agreement=m['positive_agreement'],negative_agreement=m['negative_agreement'],is_accuracy=False)
    equal(matched,root_metrics['development77_same_binary_slots']);equal(machine,root_metrics['machine_pair_agreement_not_accuracy']);equal(counts,root_metrics['rules_counts'])
    disagree=sum(merged[s]['labels'][d]!=native[s]['labels'][d] for s in native for d in DIMS);assert disagree==root_metrics['machine_disagreement_including_null_N']
    old=read_predictions(Path(root_metrics['old_v5_predictions']['path']));trans={d:collections.Counter() for d in DIMS};changeN=0
    for sid in merged:
        for d in DIMS:
            ov=old[sid]['labels'][d];nv=merged[sid]['labels'][d];trans[d][f'{ov}_to_{nv}']+=1;changeN+=ov!=nv
    equal({d:dict(v) for d,v in trans.items()},root_metrics['old_v5_to_current_composite_transitions']);assert changeN==root_metrics['old_v5_to_current_composite_changed_label_N']
    save('reference77-numeric-projection.json',dict(reference_bindings=[ab,bb],only_columns_ACD=True,source_text_or_reasons_decoded=False,A_B_equal=True,numeric_slot_N=385,rows=[dict(id=sid,dimension=d,A=v,B=rb[(sid,d)],rule=merged[sid]['labels'][d],native=None if sid not in native else native[sid]['labels'][d],native_output_present=sid in native) for (sid,d),v in ra.items()]))
    save('independent-integer-statistics-readback.json',dict(at_utc=now(),integer_four_cells_independently_derived=True,float_tolerance=1e-12,all_ROOT_reported_metrics_matched=True,reference_rule=rm,reference_native=nm,same_binary_reference_slots=matched,machine2792_pair_agreement=machine,native_record_N=2792,native_missing_N=1689,native_binary_label_N=13921,native_null_N=39,coverage=ratio(2792,4481),machine_disagreement_including_null_N=disagree,old_v5_to_current_changed_N=changeN,old_v5_transitions={d:dict(v) for d,v in trans.items()},formal_validation_complete=False,no_new_p_CI_or_sample_selection=True))
    metadata=[]
    with (YEAR/'full4481-year-map.jsonl').open('rb') as f:
        for raw in f:metadata.append(project(raw,('unit_id','source_id','department','policy_year','publication_year','component_id','source_entry_id')))
    assert len(metadata)==4481 and [x['unit_id'] for x in metadata]==list(merged)
    groups=collections.defaultdict(list);entries=set()
    for x in metadata:
        assert x['unit_id']==x['source_id'] and x['department'] in ('NMPA','NHSA','NHC') and type(x['policy_year']) is int and type(x['publication_year']) is int and x['component_id'] is None
        entries.add(x['source_entry_id']);z=merged[x['unit_id']]
        for key in (('department',x['department']),('department_year',x['department'],x['policy_year']),('corpus_year',x['policy_year'])):groups[key].append(z)
    overall=bounds(list(merged.values()),['entire_corpus']);grouped=[bounds(v,list(k)) for k,v in sorted(groups.items())];assert len(grouped)==33 and len(entries)==51
    wanted_bounds=load(BO/'conditional-bounds.json');equal(overall,wanted_bounds['overall']);equal(grouped,wanted_bounds['groups'])
    for x in wanted_bounds['inputs']:exact(x)
    save('independent-33group-null-bounds-readback.json',dict(at_utc=now(),group_N=33,source_entry_N=51,overall=overall,groups=grouped,all_counts_conditional_share_prevalence_bounds_and_strict_rankings_matched=True,no_null_imputation=True,not_confidence_intervals=True,no_new_p_CI_or_sample_selection=True,formal_validation_complete=False))
    calc=Path(root_metrics['calculator']['path']);exact(root_metrics['calculator']);exact(wanted_bounds['calculator'])
    baseline=B/'08-audits/compute-sealed-rule-composite-machine-diagnostics-root.py'
    def fns(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_text()).body if isinstance(n,ast.FunctionDef)}
    f=fns(calc);g=fns(baseline);assert all(f[n]==g[n] for n in ('metrics','reference','directed'))
    save('formula-and-input-hashes.json',dict(approved_metric_reference_directed_AST_unchanged=True,base_calculator=bind(baseline),actual_calculator=bind(calc),bounds_calculator=wanted_bounds['calculator'],readback_formulas='Integer TP/FP/FN/TN; Pe numerator=(a+b)(a+c)+(d+b)(d+c); kappa=((a+d)n-Pe_num)/(n²-Pe_num); exact rational ratios converted to float. Null/coverage handling identical to approved functions.',checked_current_bindings=list(checked.values()),reference_numeric_bindings=[ab,bb],ancestor_reaudit=False))
    report={'at_utc':now(),'status':'mechanical_readback_passed','actual_delta_record_N':37,'actual_delta_dimension_N':185,'actual_delta_technical_failure_N':0,'actual_delta_null_N':0,'composite_record_N':4481,'composite_slot_N':22405,'composite_null_N':241,'byte_inherited_record_N':4444,'new_actual_record_N':37,'S_Ec_complete_decision_mismatch_N':0,'label_change_N':8,'label_change_by_dimension':{'I':7,'F':1},'native_record_N':2792,'native_missing_record_N':1689,'native_reference77_integer_metric_mismatch_N':0,'all2792_machine_pair_metric_mismatch_N':0,'group_N':33,'null_bound_mismatch_N':0,'source_or_reference_semantic_review':False,'new200_or_remaining_semantic_read':False,'reference_only_ID_dimension_D_values':True,'model_calls':0,'classifier_calls':0,'formal_validation_complete':False,'development_diagnostic_only':True,'old_parent_audits_reused':True}
    save('report.json',report)
    lines=['# v10 实际局部执行、合并与统计机械读回','',
        '机械读回通过。37条/185项实际执行与已封存225控制使用同一 combined-v2 五模块；ROOT采用侧录早于开始，实际只执行1轮，技术失败0、null0。37行与v15原完整材料的指定ordinal、UTF8字节区间及行哈希逐项相同，未采用v16补材。',
        '', '合并4481条/22405项：37条实际delta原行及4444条parent原行逐字节保留，全部来源台账、slots和保留decisions一致；S/Ec完整决策恒等。真实标签与完整决策各变化8项（I7、F1），全量null仍241。不得称4481都曾由v10重新推理。',
        '', '固定native快照真实UTC '+coverage['at_utc']+'：2792/4481、缺1689；13921二元标签、39合法null。全2792匹配集合的四格、Po/Pe/κ/正负一致率，以及当前77原A/B数值参照的四格、κ、Po、P/R/F1、正负一致率、coverage和同二元子集均由整数重算，与ROOT新报告一致（浮点容差1e-12）。参照385数值项A=B；仅解码编码表A列ID/C列维度/D列数值，包括00529仅数值，不解码政策或理由列。',
        '', '33分组及总语料的阳性/阴性/null计数、阳性标签分母份额、条款患率上下界及严格不变排序均匹配。总阳性标签数'+str(overall['observed_positive_assignment_N'])+'、null241；原51源条目与既有成文日期优先/公开日期回退元数据沿用，不加新p、CI或抽样口径。',
        '', '本轮只进行字节/标识/数值及决策对象恒等比较，没有解释政策正文或人工理由，没有语义读human200/remaining，没有模型或classifier调用。之前parent和native技术/原文审查复用其封印，本轮未重复。输入、真实新执行和统计seals绑定保留在formula-and-input-hashes.json，完整数值复算分别存3个readback JSON。',
        '', '这些仍是披露开发参照、两机器一致性和有条件待定界限，机器互不是真值；native尚缺1689、正式效度/人审验收未完成。条件界限固定观察0/1正确的假设，不覆盖其误判，也不是置信区间。', '']
    with (A/'report.md').open('x',encoding='utf8') as f:f.write('\n'.join(lines))
    save('output-seal.json',dict(at_utc=now(),files=[bind(p) for p in sorted(A.iterdir()) if p.is_file()],self_excluded=True,model_calls=0,classifier_calls=0,formal_validation_complete=False))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
