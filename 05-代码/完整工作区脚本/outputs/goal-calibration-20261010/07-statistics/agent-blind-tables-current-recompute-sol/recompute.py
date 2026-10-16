#!/usr/bin/env python3
"""Recompute saved AI tables only; no coding, imputation, model or source edits."""
from pathlib import Path
from fractions import Fraction
from collections import Counter
import json, hashlib, datetime, math, warnings

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
OUT=Path(__file__).resolve().parent
DIMS=['S','E','Ec','I','F']
INPUTS={}
MISSING='unfilled_or_execution_failure'

def digest(b):return hashlib.sha256(b).hexdigest()
def binding(p):
    p=Path(p);b=p.read_bytes();return {'path':str(p),'sha256':digest(b),'bytes':len(b)}
def load(rel,lines=False):
    p=ROOT/rel;b=p.read_bytes();INPUTS[str(p)]=binding(p)
    if lines:
        return [(json.loads(x),{'file':str(p),'line':i+1,'raw_line_sha256_including_LF':digest(x)}) for i,x in enumerate(b.splitlines(keepends=True)) if x.strip()]
    return json.loads(b)
def save(name,obj):
    p=OUT/name
    if p.exists():raise RuntimeError('Do not overwrite first output: '+str(p))
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return binding(p)
def val(labels,dim):
    if dim not in labels:return MISSING
    x=labels[dim]
    if x is None:return None
    if type(x) is not int or x not in (0,1):raise ValueError('invalid saved label')
    return x
def metric(n,d,why):
    if not d:return {'value':None,'exact':None,'NA_reason':why,'numerator':n,'denominator':d}
    f=Fraction(n,d);return {'value':float(f),'exact':str(f),'NA_reason':None,'numerator':n,'denominator':d}

CHECKS=[]
def compare(name,rows,mode,assigned,notes):
    # rows=(id,left-labels,right-labels,department). Left=A or machine; right=B or reference.
    result={'name':name,'role':mode,'assigned_records_N':assigned,'saved_pairs_N':len(rows),'failed_or_unfilled_records_outside_saved_pairs_N':assigned-len(rows),'version_scope_notes':notes,'probability_sample':False,'design_weights_applied':False,'CI95':None,'CI_reason':'Historically exposed, nonprobability AI development data; frozen statistical contract disallows population CI. No new conditional/binomial CI invented.','dimensions':{},'departments':{}}
    for dim in DIMS:
        pairs=[(sid,val(l,dim),val(rr,dim)) for sid,l,rr,dep in rows]
        binary=[(sid,l,rr) for sid,l,rr in pairs if l in (0,1) and rr in (0,1)]
        a=sum(l==1 and rr==1 for _,l,rr in binary);b=sum(l==1 and rr==0 for _,l,rr in binary);c=sum(l==0 and rr==1 for _,l,rr in binary);d=sum(l==0 and rr==0 for _,l,rr in binary);n=a+b+c+d
        pe_num=(a+b)*(a+c)+(c+d)*(b+d)
        counts={'a':a,'b':b,'c':c,'d':d}
        if mode=='machine_vs_reference':counts.update(TP=a,FP=b,FN=c,TN=d)
        else:counts.update(A1_B1=a,A1_B0=b,A0_B1=c,A0_B0=d)
        ms={'Po':metric(a+d,n,'no jointly binary pair'),'Pe':metric(pe_num,n*n,'no jointly binary pair'),'kappa':metric((a+d)*n-pe_num,n*n-pe_num,'Pe=1 (constant agreeing marginals)' if n else 'no jointly binary pair'),'Ppos':metric(2*a,2*a+b+c,'no positive class in either side'),'Pneg':metric(2*d,2*d+b+c,'no negative class in either side')}
        if mode=='machine_vs_reference':
            ms.update(precision=metric(a,a+b,'machine has no positive predictions'),recall=metric(a,a+c,'reference has no positive cases'),F1=metric(2*a,2*a+b+c,'neither machine nor reference has positives'),specificity=metric(d,b+d,'reference has no negative cases'),NPV=metric(d,c+d,'machine has no negative predictions'))
        state=lambda x:'null' if x is None else str(x)
        grid={f'{l}|{rr}':0 for l in ['0','1','null'] for rr in ['0','1','null']}
        for sid,l,rr in pairs:
            if l!=MISSING and rr!=MISSING:grid[f'{state(l)}|{state(rr)}']+=1
        entry={'assigned_N':assigned,'saved_pair_N':len(rows),'joint_binary_N':n,'joint_binary_coverage_over_assigned':metric(n,assigned,'empty assigned scope'),'left_counts':{str(v):sum(l==v for _,l,rr in pairs) for v in [0,1]},'right_counts':{str(v):sum(rr==v for _,l,rr in pairs) for v in [0,1]},'class_counts_scope':'saved comparison rows, including null; incomplete candidates excluded from class counts, retained as failures','left_null_N':sum(l is None for _,l,rr in pairs),'right_null_N':sum(rr is None for _,l,rr in pairs),'left_failed_or_unfilled_N':sum(l==MISSING for _,l,rr in pairs)+(assigned-len(rows)),'right_failed_or_unfilled_N':sum(rr==MISSING for _,l,rr in pairs)+(0 if mode=='machine_vs_reference' else assigned-len(rows)),'reference_exists_for_unfinished_candidates':mode=='machine_vs_reference','null_pair_ids':[sid for sid,l,rr in pairs if l is None or rr is None],'full_3x3':grid,'four_cells':counts,'metrics':ms,'left_positive_rate_binary':metric(a+b,n,'no binary pairs'),'right_positive_rate_binary':metric(a+c,n,'no binary pairs'),'positive_rate_difference_left_minus_right':metric(b-c,n,'no binary pairs'),'difference_ids':[sid for sid,l,rr in binary if l!=rr],'false_positive_ids':[sid for sid,l,rr in binary if l==1 and rr==0] if mode=='machine_vs_reference' else None,'false_negative_ids':[sid for sid,l,rr in binary if l==0 and rr==1] if mode=='machine_vs_reference' else None}
        targets=['kappa','precision','recall','F1'] if mode=='machine_vs_reference' else ['kappa']
        entry['development_point_target_status']={k:'NA' if ms[k]['value'] is None else ('>=0.80' if ms[k]['value']>=.8 else '<0.80') for k in targets}
        entry['formal_acceptance']=False
        result['dimensions'][dim]=entry
        CHECKS.append({'comparison':name,'dim':dim,'mode':mode,'binary_rows':binary,'metrics':ms,'cells':counts})
    # Department diagnostics do not form new thresholds.
    for dep in sorted({x[3] for x in rows}):
        subset=[x for x in rows if x[3]==dep]
        result['departments'][dep]={'saved_N':len(subset),'dimensions':{}}
        for dim in DIMS:
            pair=[(val(l,dim),val(rr,dim)) for sid,l,rr,de in subset]
            pair=[(l,rr) for l,rr in pair if l in (0,1) and rr in (0,1)]
            a=sum(l==1 and rr==1 for l,rr in pair);b=sum(l==1 and rr==0 for l,rr in pair);c=sum(l==0 and rr==1 for l,rr in pair);d=sum(l==0 and rr==0 for l,rr in pair);n=len(pair);pe=(a+b)*(a+c)+(c+d)*(b+d)
            result['departments'][dep]['dimensions'][dim]={'joint_binary_N':n,'cells':{'a':a,'b':b,'c':c,'d':d},'Po':metric(a+d,n,'no pairs'),'Pe':metric(pe,n*n,'no pairs'),'kappa':metric((a+d)*n-pe,n*n-pe,'Pe=1 or no pairs'),'Ppos':metric(2*a,2*a+b+c,'no positives'),'Pneg':metric(2*d,2*d+b+c,'no negatives'),'CI95':None}
    return result

mapped=load('04-calibration/development77-v11/mapped-labels.json')
aggregate=load('04-calibration/development77-v11/aggregate.json')
order=[x['frame_id'] for x in mapped];department={x['frame_id']:x['department'] for x in mapped}
assert len(order)==len(set(order))==77
events={sid:{'A':[],'B':[]} for sid in order};by_round={}

def saved_round(round_name,has_blind_map=True):
    mapping=load(f'04-calibration/{round_name}/admin/private_mapping.json') if has_blind_map else None
    result={}
    for coder in ['A','B']:
        base=f'04-calibration/{round_name}/{coder}'
        sub_rel=base+'/submission.json'
        if not (ROOT/sub_rel).exists():sub_rel=base+'/first-complete-submission.json'
        submission=load(sub_rel)
        labels=load(base+'/labels.jsonl',True)
        packets={}
        if (ROOT/(base+'/packet.jsonl')).exists():packets={x['id']:(x,loc) for x,loc in load(base+'/packet.jsonl',True)}
        manual_path=ROOT/(base+'/manual.md')
        manual= binding(manual_path) if manual_path.exists() else {'sha256':submission.get('manual_sha256', '6ffc7b35a5cbe1c1f90c81d24d1508dba7adefe5e7bbd058c284d76e14b8a70f'),'version':'v1.1 development'}
        if manual_path.exists():INPUTS[str(manual_path)]=manual
        result[coder]={}
        for row,loc in labels:
            blind=row.get('id',row.get('blind_id'))
            if mapping is None:
                if blind.startswith('RECODE25-'):sid=blind
                else:
                    aliases=submission['output_aliases_in_order'];ids=submission['source_ids_in_judgment_order']
                    assert len(aliases)==len(ids) and blind in aliases
                    sid=ids[aliases.index(blind)]
            else:
                matches=[x for x in mapping if x['blind_id']==blind and x.get('coder',coder)==coder]
                assert len(matches)==1
                sid=matches[0]['frame_id']
            assert sid in events and sid not in result[coder]
            packet,packetloc=packets.get(blind,(None,None))
            identity_fields={k:submission[k] for k in submission if any(w in k.lower() for w in ['identity','model','reasoning','history','exposure','role','coder'])}
            event={'round':round_name,'coder':coder,'saved_blind_id':blind,'labels':row['labels'],'evidence':row.get('evidence',{}),'source_requests':row.get('source_requests',row.get('material_requests',[])),'first_output':loc,'first_output_file_binding':INPUTS[loc['file']],'submission':INPUTS[str(ROOT/sub_rel)],'identity_as_saved':identity_fields,'provider_identity_independently_known':False,'manual':manual,'source_packet':packetloc,'source_packet_file_binding':INPUTS.get(packetloc['file']) if packetloc else None,'current_text_as_read_in_that_round':packet.get('text') if packet else None,'source_bundle_sha256_as_saved':row.get('source_bundle_sha256'),'development_not_human_or_new_holdout':True}
            events[sid][coder].append(event);result[coder][sid]=event
    assert set(result['A'])==set(result['B'])
    by_round[round_name]=result

for name in ['pilot01','pilot02','coverage01']:saved_round(name)
for name in ['renewal-rejudge-v11','source-impact4-v12']:saved_round(name,False)

base={}
latest={}
for sid in order:
    batch=next(x['batch'] for x in mapped if x['frame_id']==sid)
    base[sid]={coder:by_round[batch][coder][sid] for coder in ['A','B']}
    for coder in ['A','B']:
        assert base[sid][coder]['labels']==next(x[coder] for x in mapped if x['frame_id']==sid)
    latest[sid]={coder:events[sid][coder][-1] for coder in ['A','B']}

# Actual saved predictions and actual AI reference rows; no semantic changes.
refs={x['id']:(x,loc) for x,loc in load('06-coding/development-reference77-v14-root-adjudicated-v3/reference.jsonl',True)}
oldrefs={x['id']:(x,loc) for x,loc in load('06-coding/development-reference77-v12-root-adjudicated-v2/reference.jsonl',True)}
rule_rows=load('06-coding/rule-v17-bounded-role-merge-development-sol/run77-first/predictions.jsonl',True)
rule={x['id']:(x,loc) for x,loc in rule_rows}
rulederived={x['id']:x for x,_ in load('06-coding/rule-v17-bounded-role-merge-development-sol/derived-rows77.jsonl',True)}
native38derived=load('06-coding/root-machine-review/native38-v13-short-development-diagnostic-sol/derived-rows.jsonl',True)
partialderived=load('06-coding/root-machine-review/existing-rule77-and-partial7-v14-reference-v3-development-sol/partial7-derived-rows.jsonl',True)
native38={};partial7={}
for container,items,pathkey,idkey in [(native38,native38derived,'candidate_first_file','source_id'),(partial7,partialderived,'original_first','id')]:
    for derived,loc in items:
        p=Path(derived[pathkey]['path']); b=p.read_bytes()
        assert digest(b)==derived[pathkey]['sha256'] and len(b)==derived[pathkey]['bytes']
        INPUTS[str(p)]=binding(p); item=json.loads(b)
        assert item['labels']==derived['candidate_labels']
        container[derived[idkey]]={'item':item,'original_first':INPUTS[str(p)],'derived_provenance':loc,'manual_sha256':item.get('manual_sha256'),'technical_state':'pending_full_platform_selection' if container is native38 else 'per_record_mechanically_valid_partial_failed_batch','identity':'AI native runtime; not human', 'runtime_thread_id':derived.get('runtime_thread_id',derived.get('attempt_uuid'))}
assert len(native38)==38 and len(partial7)==7 and len(rule)==77

bundles={}
for bundle,loc in load('06-coding/rule-v17-bounded-role-merge-development-sol/run77-first/delivered-complete-source-bundles.jsonl',True):
    record=bundle['source_record'];sid=record['id']
    canonical=json.dumps(bundle,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    bundles[sid]={'current_text':record['text'],'contexts':record['contexts'],'source_ref':record.get('source_ref'),'pages':record.get('pages'),'source_relations':record.get('source_relations'),'bundle_file':loc['file'],'bundle_line':loc['line'],'bundle_sha256':digest(canonical),'raw_line_sha256':loc['raw_line_sha256_including_LF'],'source_record_pointer':'/source_record','contexts_pointer':'/source_record/contexts','source_locator_bases':bundle.get('source_locator_bases'),'source_asset_locations':bundle.get('source_asset_locations'),'source_version':bundle.get('common_source_bundle_version'),'text_or_metadata_extraction_not_new_image_view':True}
assert set(bundles)==set(order)

def evidence_fields(ev):
    return {'reason':ev.get('rationale',ev.get('reason')),'current_quote':ev.get('current_quote'),'context_quotes':ev.get('context_quotes',ev.get('contexts_used',[])),'path':ev.get('path'),'complete_original_evidence':ev}
def flatten_event(event,dim):
    return {'value':val(event['labels'],dim),'round':event['round'],'evidence':evidence_fields(event['evidence'].get(dim,{})),'first_output':event['first_output'],'manual':event['manual'],'source_packet':event['source_packet'],'source_bundle_sha256_as_saved':event.get('source_bundle_sha256_as_saved'),'actual_identity':'AI; original saved identity retained in record history'}

records=[];long=[]
for sid in order:
    ref,ref_loc=refs[sid]
    history={coder:events[sid][coder] for coder in ['A','B']}
    machines={'rule_v17':{'labels':rule[sid][0]['labels'],'first_output':rule[sid][1],'evidence':rule[sid][0].get('decisions'),'source_provenance':rulederived[sid]['source_bundle'],'identity':'rule program; one complete77 run'},'native38':native38.get(sid),'partial7':partial7.get(sid)}
    rec={'id':sid,'department':department[sid],'source':bundles[sid],'A':{'original':base[sid]['A'],'latest':latest[sid]['A'],'history':history['A']},'B':{'original':base[sid]['B'],'latest':latest[sid]['B'],'history':history['B']},'AI_reference':{'labels':ref['labels'],'role':ref.get('reference_role'),'manual_sha256':ref.get('manual_sha256'),'saved_row':ref,'row_location':ref_loc,'reference_is_not_A_or_B':True},'machine_candidates':machines,'human_review':{coder:{'values':{dim:None for dim in DIMS},'reasons':{dim:None for dim in DIMS},'name':None,'date':None} for coder in ['A','B']}}
    records.append(rec)
    for dim in DIMS:
        long.append({'id':sid,'department':department[sid],'dimension':dim,'current_text':bundles[sid]['current_text'],'source_file':bundles[sid]['bundle_file'],'source_line':bundles[sid]['bundle_line'],'source_record_pointer':'/source_record','contexts_pointer':'/source_record/contexts','A':{'original':flatten_event(base[sid]['A'],dim),'latest':flatten_event(latest[sid]['A'],dim),'earliest_saved':flatten_event(events[sid]['A'][0],dim)},'B':{'original':flatten_event(base[sid]['B'],dim),'latest':flatten_event(latest[sid]['B'],dim),'earliest_saved':flatten_event(events[sid]['B'][0],dim)},'AI_reference':{'value':ref['labels'][dim],'reason_and_revision_metadata':{k:v for k,v in ref.items() if k not in ['labels','evidence_A','evidence_B']},'A_source_evidence_as_saved':ref.get('evidence_A',{}).get(dim),'B_source_evidence_as_saved':ref.get('evidence_B',{}).get(dim),'row_location':ref_loc},'human_A_value':None,'human_A_reason':None,'human_A_name':None,'human_A_date':None,'human_B_value':None,'human_B_reason':None,'human_B_name':None,'human_B_date':None})
review_binding=save('review-rows.json',{'schema_version':'agent-current-review-table-v1','role':'真实AI开发表与修改链供真人事后复核；不是新真人独立首判','N_records':77,'N_long_rows':385,'manual_source_version_notes':'基础pilot02+coverage01手册1.1；续约2/补材4仅实际source新版AI重判。其他71不改；v3 ROOT非盲参照另列，不拷贝入A/B。当前原文语境为实际v14 delivered bundle，历史各轮原句/packet另存。','records':records,'long_rows':long,'human_review_status':'真人值/理由/姓名/日期全部空；未执行，不作为null标签或0。'})
print(json.dumps({'review_rows_ready':review_binding,'N':77,'long_N':385},ensure_ascii=False),flush=True)

comparisons=[]
def ab_round(name):
    rr=by_round[name];ids=[sid for sid in order if sid in rr['A']]
    return [(sid,rr['A'][sid]['labels'],rr['B'][sid]['labels'],department[sid]) for sid in ids]
for name in ['pilot01','pilot02','coverage01','renewal-rejudge-v11','source-impact4-v12']:
    rows=ab_round(name)
    comparisons.append(compare('A_B_'+name,rows,'AI_A_vs_AI_B',len(rows),'Actual saved same-round AI firsts; later development round does not replace original blind-round claim.'))
comparisons.append(compare('A_B_development77_base_v11',[(sid,base[sid]['A']['labels'],base[sid]['B']['labels'],department[sid]) for sid in order],'AI_A_vs_AI_B',77,'Actual pilot02 41 + coverage01 36; same manual1.1 but historically exposed, AI development.'))
comparisons.append(compare('A_B_latest_actual_development_composite77',[(sid,latest[sid]['A']['labels'],latest[sid]['B']['labels'],department[sid]) for sid in order],'AI_A_vs_AI_B',77,'Mixed actual latest source rounds, not same-run firsts:71 base +2 renewal +4 sourceimpact; no v3 adjudication copied to A/B.'))
machine_sets=[('rule_v17_complete77',rule,77),('native38_complete_format_subset',native38,77),('native_partial7_saved_subset',partial7,16)]
for name,items,assigned in machine_sets:
    ids=[sid for sid in order if sid in items]
    candidate=lambda sid:items[sid][0]['labels'] if name.startswith('rule') else items[sid]['item']['labels']
    rows=[(sid,candidate(sid),refs[sid][0]['labels'],department[sid]) for sid in ids]
    comparisons.append(compare(name+'_vs_AI_reference_v3',rows,'machine_vs_reference',assigned,'AI nonblind mixed historical/root-adjudicated development reference; no human gold. Native subsets not spliced into77; missing firsts never imputed0.'))
    if not name.startswith('rule'):
        comparisons.append(compare(name+'_vs_historical_AI_reference_v2',[(sid,candidate(sid),oldrefs[sid][0]['labels'],department[sid]) for sid in ids],'machine_vs_reference',assigned,'Historical reference retained separately. Candidate first bytes unchanged; reference revision is not model improvement.'))
# Implementation agreement only; left is rule, right native. Neither is truth.
for name,items in [('native38',native38),('partial7',partial7)]:
    comparisons.append(compare('rule17_vs_'+name+'_implementation_agreement',[(sid,rule[sid][0]['labels'],items[sid]['item']['labels'],department[sid]) for sid in order if sid in items],'machine_implementation_agreement',len(items),'Same-ID saved outputs with different actual execution/source/manual histories; agreement diagnostic only.'))

policy=load('02-methods/unknown-and-denominator-policy.json')
contract=load('02-methods/prospective-statistical-contract-v2/validation-design-v2.json')
# One existing sklearn process (this one) crosschecks all jointly binary vectors.
import sklearn
from sklearn.metrics import cohen_kappa_score, precision_score, recall_score, f1_score, confusion_matrix
cross=[]
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    for check in CHECKS:
        bb=check['binary_rows']; y=[rr for sid,l,rr in bb];pred=[l for sid,l,rr in bb]
        n=len(bb);ms=check['metrics'];c=check['cells'];expected=[c['d'],c['c'],c['b'],c['a']]
        cm=confusion_matrix(pred,y,labels=[0,1]).ravel().tolist() if n else [0,0,0,0]
        # sklearn rows=pred columns=y; equivalent matrix d,c,b,a.
        assert cm==expected,(check['comparison'],check['dim'],cm,expected)
        k=cohen_kappa_score(y,pred,labels=[0,1]) if n else float('nan')
        ex=ms['kappa']['value'];assert (math.isnan(k) and ex is None) or (ex is not None and abs(k-ex)<1e-12)
        vals={'kappa':None if math.isnan(k) else float(k)}
        if check['mode']=='machine_vs_reference':
            funcs={'precision':precision_score,'recall':recall_score,'F1':f1_score}
            for key,fn in funcs.items():
                v=float(fn(y,pred,zero_division=0));ex=ms[key]['value']
                if ex is not None:assert abs(v-ex)<1e-12
                vals[key]=None if ex is None else v
        cross.append({'comparison':check['comparison'],'dim':check['dim'],'N_binary':n,'confusion_matrix_rows_left_columns_right':cm,'sklearn_values_NA_normalized_by_exact_denominators':vals,'passed':True})
save('sklearn-crosscheck.json',{'sklearn_version':sklearn.__version__,'process_count':1,'checks':cross,'all_passed':True,'NA_contract':'sklearn zero_division values never substitute exact denominator NA.'})

missing=[{'indicator':'800 A/B agreement, classification, weighted fourcells/CI','status':'NA','reason':'800正式A/B表仍空，无真实独立人类首件或参照；空占位不作为semantic null或0。没有可信reference，规则800不能算classification。'}, {'indicator':'Probability-sample CI for development77/native38/partial7','status':'not_applicable','reason':'非概率且历史曝光；既有contract明确开发资料不报总体CI。没有人为添加条件二项CI。'}, {'indicator':'Full77 native classification','status':'NA','reason':'native38完整候选与partial7失败批部分首件不同实际批/版本；不拼77，其他39或9未完成保持失败。'}, {'indicator':'LLM independent repeated full frozen runs / pairwise stability','status':'not_computed','reason':'缺同版本三次完整独立重复；技术retry、不同版本修复不能当稳定性重复。'}, {'indicator':'Rule same-input repeated byte stability','status':'not_computed_here','reason':'冻结版本只有本轮一实际run；未重跑生成新数据。'}, {'indicator':'Final4481 departmental attention and downstream robustness','status':'not_computed','reason':'可信真人参照/最终验证与必要全库重编码未实际完成；77非概率开发阳性数不能代总体部门占比。'}, {'indicator':'Material source/semantic correctness, real human identity','status':'not_established_by_arithmetic','reason':'本轮只复算保存值，不新增源语义裁定；真人复核值/姓名仍为空。'}]
metrics={'version':'all-current-agent-tables-arithmetic-v1','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'identity':'AI arithmetic-only nonblind recomputation; not human validation','requested_model':'gpt-6.1-sol ultra','actual_provider_identity_unknown':True,'formulas':contract['formula_contract'],'denominator_policy':policy['coding_states'],'confidence_interval_contract_as_saved':contract['confidence_intervals'],'comparisons':comparisons,'uncomputed_or_NA':missing,'review_rows':review_binding,'human_independent_coding_completed':False,'formal_acceptance':False,'no_new_labels_or_adjudications':True,'no_new_model_runs_or_retries':True,'input_bindings':list(INPUTS.values())}
save('metrics-all-available.json',metrics)
save('input-bindings.json',{'inputs':list(INPUTS.values()),'count':len(INPUTS),'script':binding(__file__),'full_sha_bytes_checked_for_loaded_candidate_firsts':True,'scope':'Loaded arithmetic/source review inputs only; no broad all-frame QA.'})

lines=['现有Agent编码表的实际复算已完成。77条基础A/B、补材复判和最新混合表分开保存；所有真人新值/理由/姓名/日期仍为空。本次无新的语义判断或模型任务。','','| 比较 | N保存/分配 | S κ | E κ | Ec κ | I κ | F κ |','|---|---:|---:|---:|---:|---:|---:|']
for x in comparisons:
    vals=[x['dimensions'][d]['metrics']['kappa']['value'] for d in DIMS]
    lines.append('| '+x['name']+' | '+str(x['saved_pairs_N'])+'/'+str(x['assigned_records_N'])+' | '+' | '.join('NA' if v is None else f'{v:.6f}' for v in vals)+' |')
lines+=['','A/B四格行=A、列=B，a=A1B1、b=A1B0、c=A0B1、d=A0B0；A/B均不是truth。机器行=候选、列=实际AI开发参照，TP=a、FP=b、FN=c、TN=d。Specificity=TN/(FP+TN)，NPV=TN/(FN+TN)。逐维详细四格、类别/待定/失败/覆盖、Po/Pe/Ppos/Pneg、分类指标、NA理由和真实差错ID均在metrics-all-available.json。','','最新A/B混合表只将续约2条与source-impact4的实际后续提交覆盖显示；其余71条保留原1.1提交。原首件全部保存，混合修订结果不是原独立盲评κ。ROOT v3非盲裁定另列，未复制入A/B。','','规则17、native38、partial7分别使用实际原预测。native38技术selection仍pending，partial7是失败批中的逐记录技术有效部分；它们不能拼成完整77。v3参照74条历史metadata保留，只有3个S为ROOT1.3/source14开发裁定，不能冒称真人gold或同版全部新参照。','','开发点估计达到.80只称该保存数据上的数值状态；没有正式人类检验/验收结论。非概率曝光开发资料不套抽样权重，按既有统计契约不报告总体95%CI。800正式空表无A/B首件及可信参照，分类/概率CI仍NA。','','复核数据review-rows.json包含77条完整原文CTX与实际源定位、385逐维行、双方原值与真实最新修订值/证据/身份版本、原first定位；真人复核字段为空。ROOT可制作分别A/B表与原文语境sheet。','','既有sklearn '+sklearn.__version__+'在单一进程对所有比较逐维四格/κ及适用P/R/F1交叉复算；不以软件默认zero_division代NA。','','未计算项目：']
lines += ['- '+x['indicator']+'：'+x['reason'] for x in missing]
p=OUT/'report.md';assert not p.exists();p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
files=[binding(OUT/x) for x in ['recompute.py','preparation-failed-script.py','preparation-failure.json','review-rows.json','metrics-all-available.json','input-bindings.json','sklearn-crosscheck.json','report.md']]
seal=save('seal.json',{'seal_type':'actual-arithmetic-and-human-review-data-first-delivery','created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'files':files,'member_N':len(files),'original_labels_or_reference_or_source_modified':False,'new_coding_or_model_calls':0,'human_review_executed':False,'formal_acceptance':False,'seal_excludes_itself':True})
print(json.dumps({'seal':seal,'comparisons_N':len(comparisons),'crosschecks_N':len(cross),'saved_review_rows_N':len(long),'complete':True},ensure_ascii=False))
