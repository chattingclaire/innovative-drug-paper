"""Historical frozen200 handoff; no coding, adjudication, sampling or promotion.

A trusted ROOT review citing actual human execution is required before labels
are opened. SHA/JSON flags bind evidence; they do not authenticate people.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DIMS = ('S','E','Ec','I','F')
SNAPSHOT = 'historical-human200-manual5ea7-rule-v19-first-native4481-v1'


def require(ok, message):
    if not ok: raise ValueError(message)


def binding(path):
    p = Path(path).resolve(); raw = p.read_bytes()
    return {'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}


def verify(b):
    require(isinstance(b,dict) and set(b)=={'path','bytes','sha256'}, 'Exact file binding required')
    require(binding(b['path'])==b, 'Frozen bytes changed: '+str(b['path']))
    return Path(b['path']).resolve()


def load(p):
    def no_duplicates(items):
        result = {}
        for k,v in items:
            require(k not in result, 'Duplicate JSON key: '+k); result[k]=v
        return result
    return json.loads(Path(p).read_text(),object_pairs_hook=no_duplicates,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Invalid JSON number: '+x)))


def jsonlines(p):
    return [load_line(x) for x in Path(p).read_text().splitlines() if x.strip()]


def load_line(s):
    # The same strict duplicate/NaN policy applies to raw JSONL submissions.
    def pairs(items):
        out={}
        for k,v in items: require(k not in out,'Duplicate JSON key'); out[k]=v
        return out
    return json.loads(s,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(ValueError('Invalid JSON number')))


def canonical(x):
    return hashlib.sha256(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def module(name, b):
    spec=importlib.util.spec_from_file_location(name,verify(b))
    obj=importlib.util.module_from_spec(spec);spec.loader.exec_module(obj);return obj


def contract():
    c=load(HERE/'bindings.json')
    for k,b in c['frozen_inputs'].items(): verify(b)
    verify(c['year200_binding']);verify(c['common_material_identity_receipt_binding'])
    proof=load(verify(c['common_material_identity_receipt_binding']))
    require(proof.get('old200_common_material_rows')==200 and proof.get('human_material_bytes_and_object_equality_N')==400 and proof.get('native_packet_bytes_and_object_equality_N')==200 and proof.get('rule_delivered_selected_object_equality_N')==200,'Bound common material receipt incomplete')
    for b in proof['assignment_bindings']:verify(b)
    for row in proof['native_members']:verify(row['packet_binding'])
    require(c['snapshot_id']==SNAPSHOT,'Historical snapshot mismatch')
    require(c['actual_human_reference_N_at_preparation']==0,'Preparation cannot claim actual human reference')
    return c


def snapshot_gate(review,c):
    # Reject a new rule version/domain before any human/reference/machine label I/O.
    require(review.get('snapshot_id')==SNAPSHOT,'Updated rule versions need a new registered draw/material/design contract')
    require(review.get('usage')=='historical_frozen_snapshot_only','Old200 cannot validate updated candidates')
    require(review.get('formal_acceptance_claimed') is False,'This handoff never grants formal acceptance')
    require(review.get('domain_population_N')=={'remaining':1444,'exposed':3037},'Historical domain contract is immutable')
    require(review.get('old_rule_prediction_binding')==c['frozen_inputs']['rule_predictions'],'Updated rule predictions rejected')
    require(review.get('rule_freeze_binding')==c['frozen_inputs']['rule_freeze'],'Updated semantic algorithm rejected')
    require(review.get('LLM_manifest_binding')==c['frozen_inputs']['LLM_manifest'],'Different machine campaign rejected')
    require(review.get('common_manual_sha256')==c['frozen_inputs']['manual']['sha256'],'Manual differs')
    require(review.get('common_material_index_sha256')==c['frozen_inputs']['materials']['sha256'],'Human common material differs')
    require(review.get('common_source_jsonl_sha256')==c['source_jsonl_sha256'],'Machine common source differs')
    require(review.get('draw_sha256')==c['frozen_inputs']['draw']['sha256'],'Draw/weights differ')


def actual_gate(review,c):
    snapshot_gate(review,c)
    require(review.get('status')=='ROOT_reviewed_actual_human200_reference_and_complete_machine_snapshot','Actual review is unfilled')
    require(review.get('control_or_synthetic') is False,'Synthetic controls cannot become actual judgments')
    for key in ('actual_human_adjudication','reference_machine_blinded','reference_before_machine_comparison',
                'whole_LLM_campaign_terminal','machine_snapshot_frozen_before_human_feedback'):
        require(review.get(key) is True,'Actual evidence not established: '+key)
    for key in ('AI_substitution_used','A_B_agreement_used_as_reference','label_based_machine_attempt_selection'):
        require(review.get(key) is False,'Forbidden substitution/selection: '+key)
    codes=review.get('reference_human_identity_codes')
    require(isinstance(codes,list) and codes and len(set(codes))==len(codes) and all(isinstance(x,str) and x.strip() for x in codes),'Actual adjudicator identities required')
    evidence=review.get('actual_user_confirmation',{})
    require(evidence.get('source_kind')=='direct_user_confirmation' and isinstance(evidence.get('statement'),str) and evidence['statement'].strip(),'Actual user confirmation required; do not infer it from flags')
    for key in ('AB_execution_review_binding','reference_original_binding','LLM_terminal_inventory_binding'):
        require(isinstance(review.get(key),dict),'Actual reviewed original binding required: '+key)


def frozen_frame(manifest):
    doc=load(verify(manifest['ordered_source_ids']))
    require(set(doc)=={'approved_record_ids','frame_order_UTF8_LF_sha256','preserves_original_FRAME4481_order'} and doc['preserves_original_FRAME4481_order'] is True,'Exact frozen frame wrapper required')
    frame=doc['approved_record_ids']
    require(isinstance(frame,list) and len(frame)==4481 and len(set(frame))==4481,'Frozen full4481 ID list required')
    require(hashlib.sha256(('\n'.join(frame)+'\n').encode()).hexdigest()==doc['frame_order_UTF8_LF_sha256'],'Original frame UTF8 LF order differs')
    require([rid for b in manifest['batches'] for rid in b['source_ids']]==frame,'Batches disagree with frozen full frame')
    return frame


def initial_projection(directory,ab_review,c):
    # Same bound_xlsx_reader inspect contract as frozen human_first; this local
    # projection fixes only its manifest-binding-versus-list dereference defect.
    rb=load(verify(c['frozen_inputs']['receiver_bindings']))
    for k in ('vendor','code','draw','workbook_manifest','materials'):verify(rb[k])
    helper=module('_frozen200_original_xlsx_reader',rb['vendor'])
    draw=load(verify(rb['draw']))['records'];pages=load(verify(rb['materials']))['pages']
    cells={}
    for side in ('A','B'):
        template=helper.read_xlsx(verify(rb['template_inputs'][side]).read_bytes())['独立初判']['cells']
        bundle={p['blind_id']:p['source_bundle_sha256'] for p in pages if p['side']==side}
        control={'spec':{'worksheet':'独立初判'},'cells':template,'source':set(bundle),'bundle':bundle,'bids':set(bundle)}
        checked,derived=helper.inspect(side,(directory/('original-'+side+'.xlsx')).read_bytes(),control)
        require(checked.get('content_valid') is True and checked.get('fully_completed') is True,'Original A/B re-read incomplete')
        require(derived==jsonlines(directory/('derived-'+side+'.jsonl')),'Derived A/B changed original initial bytes')
        cells[side]={(x['blind_id'],x['dimension']):x for x in derived}
        require(len(cells[side])==1000,'Duplicate A/B normalized slot')
    rows=[]
    for row in draw:
        outputs={}
        for side in ('A','B'):
            labels={}
            for dim in DIMS:
                cell=cells[side][row[side+'_blind_id'],dim];st=cell['completion_status'];v=cell['value']
                require((st=='filled' and type(v) is int and v in (0,1)) or (st=='lawful_null' and v is None),'Incomplete A/B retained and refused; no imputation')
                labels[dim]=v
            outputs[side]={'status':'completed','labels':labels}
        rows.append({'unit_id':row['source_id'],'stratum_id':row['stratum'],'department':row['department'],'outputs':outputs})
    require(len(rows)==200 and len({r['unit_id'] for r in rows})==200,'Old200 assignments differ')
    meta=load(verify(c['frozen_inputs']['statistics_template']))['metadata'];meta['analysis_stage']='human_first'
    frame=frozen_frame(load(verify(c['frozen_inputs']['LLM_manifest'])));meta['scope']['frame_ids_sha256']=canonical(sorted(frame))
    meta['identities']={side:{'kind':'human','verified':True,'independent_initial':True,'identity_code':ab_review['human_identity_codes'][side]} for side in ('A','B')}
    meta['identities']['reference']={};meta['identity_and_source_evidence_reviewed']=True
    for flag in ('common_manual','common_materials','design_before_answers','initial_submissions_before_discussion'):meta['freeze_attestations'][flag]=True
    for side in ('A','B'):meta['input_seals'][side]={'sealed':True,'sha256':binding(directory/('original-'+side+'.xlsx'))['sha256'],'joined_projection_sha256':canonical([{'unit_id':r['unit_id'],'output':r['outputs'][side]} for r in sorted(rows,key=lambda x:x['unit_id'])])}
    require(ab_review.get('common_manual_sha256')==c['frozen_inputs']['manual']['sha256'],'A/B actual review manual differs')
    for key,bkey in (('common_manual','manual'),('common_materials','materials'),('design','draw')):meta['artifact_seals'][key]={'sealed':True,'sha256':c['frozen_inputs'][bkey]['sha256']}
    return {'data_role':'sealed_project','metadata':meta,'records':rows}


def human_initial(receive_dir,review,c):
    first=module('_frozen_human_first200',c['frozen_inputs']['human_first'])
    reviewed=verify(review['AB_execution_review_binding'])
    ab_review,report,seal=first.reviewed_receive(Path(receive_dir),reviewed)
    payload=initial_projection(Path(receive_dir).resolve(),ab_review,c)
    require(review.get('AB_original_submission_bindings')==ab_review['original_submission_bindings'],'Adjudication review must retain exact A/B originals')
    return payload,ab_review,report


def material_identity(c):
    draw=load(verify(c['frozen_inputs']['draw']))['records']
    pages=load(verify(c['frozen_inputs']['materials']))['pages']
    by={(x['side'],x['blind_id']):x for x in pages}
    result={}
    for i,row in enumerate(draw,1):
        a,b=(by[side,row[side+'_blind_id']] for side in ('A','B'))
        require(a['source_bundle_sha256']==b['source_bundle_sha256'],'A/B do not share byte-identical common material')
        for page in (a,b):
            p=verify(page['json']);require(page['source_bundle_sha256']==binding(p)['sha256'],'Material bundle identity mismatch')
            require(load(p)['source_record']['id']==row['source_id'],'Material source ID differs')
        result['R-'+str(i).zfill(6)]={'unit_id':row['source_id'],'source_bundle_sha256':a['source_bundle_sha256']}
    return result


def value(v):
    require(v is None or (type(v) is int and v in (0,1)),'Only integer0/1 or explicit null; bool/string prohibited')
    return v


def reference_output(row,identity,codes):
    require(row.get('source_bundle_sha256')==identity['source_bundle_sha256'],'Reference material binding differs')
    require(set(row.get('dimensions',{}))==set(DIMS),'All five reference slots must remain present')
    ms=row.get('method_status');require(ms in ('completed','execution_failure','not_returned'),'Unfilled reference template is not an execution')
    cells=row['dimensions'];labels={};ds={}
    for dim in DIMS:
        cell=cells[dim];status=cell.get('completion_status');v=value(cell.get('value'))
        require('value' in cell,'Missing value is not a lawful null')
        if ms=='not_returned':
            require(status=='not_returned' and v is None,'Whole not-returned state must cover every slot');continue
        if ms=='execution_failure':
            require(status=='execution_failure' and v is None and isinstance(cell.get('failure_code'),str) and cell['failure_code'].strip(),'Whole failure retains explicit failure evidence');continue
        require(status in ('filled','lawful_null','execution_failure'),'Per-dimension unreturned is unsupported by registered engine; retain raw and refuse')
        if status=='filled':require(type(v) is int and v in (0,1),'Filled reference must be0/1')
        if status=='lawful_null':require(v is None and isinstance(cell.get('null_reason'),str) and cell['null_reason'].strip(),'Lawful NULL requires actual human reason')
        if status in ('filled','lawful_null'):require(cell.get('human_identity_code') in codes,'Reference is not attributed to reviewed actual human')
        if status=='execution_failure':
            require(v is None and isinstance(cell.get('failure_code'),str) and cell['failure_code'].strip(),'Dimension failure is not semantic null');ds[dim]='execution_failure'
        labels[dim]=v
    if ms=='not_returned': return None
    if ms=='execution_failure':return {'status':'execution_failure','labels':None,'failure_code':'actual_reference_whole_method_failure'}
    out={'status':'completed','labels':labels}
    if ds:out['dimension_status']=ds
    return out


def reference_projection(review,c):
    identity=material_identity(c);raw=verify(review['reference_original_binding']);rows=jsonlines(raw)
    require(len(rows)==200,'Reference original must preserve exactly200 assigned method rows/1000 slots')
    require([x.get('blind_id') for x in rows]==list(identity),'Reference assigned order/IDs changed')
    return {identity[r['blind_id']]['unit_id']:reference_output(r,identity[r['blind_id']],review['reference_human_identity_codes']) for r in rows}


def rule_projection(c):
    # Only called after actual/full-campaign gates. No candidate rerun or choice.
    rows=jsonlines(verify(c['frozen_inputs']['rule_predictions']))
    manifest=load(verify(c['frozen_inputs']['LLM_manifest']))
    require([r.get('id') for r in rows]==frozen_frame(manifest),'Historical rule must cover exact full4481 in frozen order')
    freeze=load(verify(c['frozen_inputs']['rule_freeze']))
    require(freeze.get('fixed_algorithm_version')==c['old_rule_algorithm_version'],'Historical algorithm identity changed')
    out={}
    for r in rows:
        if r.get('labels') is None:
            require(r.get('implementation_errors'),'Absent rule labels without execution-failure evidence')
            out[r['id']]={'status':'execution_failure','labels':None,'failure_code':'archived_rule_implementation_error'}
        else:
            require(set(r['labels'])==set(DIMS),'Five rule dimensions required')
            labels={d:value(r['labels'][d]) for d in DIMS}
            require(all(labels[d]==r['decisions'][d]['value'] for d in DIMS),'Rule labels differ from archived decisions')
            out[r['id']]={'status':'completed','labels':labels}
    return out


def terminal_inventory_gate(inventory,review,c):
    require(inventory.get('status')=='ROOT_received_complete_terminal_native4481_campaign','Partial or running LLM labels prohibited')
    require(inventory.get('all_batches_terminal') is True and inventory.get('reference_or_accuracy_used_in_selection') is False,'Full terminal earliest-technical reception required')
    require(inventory.get('run_manifest_binding')==c['frozen_inputs']['LLM_manifest'],'Whole campaign identity differs')
    require(inventory.get('record_N')==4481 and inventory.get('batch_N')==504,'Whole4481/504 required')
    require(inventory.get('coverage_order_sha256')==c['frame_order_sha256'],'Campaign ordered frame differs')
    manifest=load(verify(c['frozen_inputs']['LLM_manifest']))
    entries=inventory.get('batches',[])
    require(len(entries)==504 and [e.get('batch_id') for e in entries]==[x['batch_id'] for x in manifest['batches']],'Every frozen batch must have exactly one terminal entry')
    require(all(e.get('terminal_state') in ('technical_valid_whole_batch','technical_attempts_exhausted','terminal_not_returned') for e in entries),'Running/unfilled batch is forbidden')
    # Inspect only statuses and receipts here. No first.json labels before ALL terminal.
    return manifest,entries


def llm_projection(review,c):
    ip=verify(review['LLM_terminal_inventory_binding']);inventory=load(ip)
    manifest,entries=terminal_inventory_gate(inventory,review,c)
    validator=module('_frozen_native4481_validator',manifest['strict_technical_validator'])
    out={};receipts=[];valid_plans=[]
    for batch,entry in zip(manifest['batches'],entries):
        directory=Path(batch['assignment']['path']).parent;ids=batch['source_ids'];state=entry['terminal_state']
        verify(batch['assignment'])
        if state=='technical_valid_whole_batch':
            selection_path=verify(entry['selection_binding']);require(selection_path==directory/'root-selection.json','Use frozen ROOT earliest whole-batch selection')
            s=load(selection_path);n=s.get('selected_attempt_number')
            require(type(n) is int and 1<=n<=3,'Illegal attempt index')
            require(s.get('cross_attempt_record_combination') is False and s.get('label_based_selection') is False and s.get('all_actual_attempts_retained') is True,'Record/label selection forbidden')
            require(s.get('batch_id')==batch['batch_id'] and s.get('run_id')==manifest['run_id'],'Selection identity differs')
            prior_bindings=[]
            for prior in range(1,n):
                p=directory/f'root-attempt-reception-{prior:04d}-v2.json';pr=load(p)
                require(pr.get('state')=='technical_invalid_whole_batch','Earlier valid attempt cannot be skipped')
                for b in pr.get('attempt_files',[]):verify(b)
                receipts.append(binding(p));prior_bindings.append(binding(p))
            rp=verify(s['technical_reception']);r=load(rp)
            require(rp==directory/f'root-attempt-reception-{n:04d}-v2.json' and r.get('state')=='technical_valid_whole_batch','Valid frozen reception missing')
            require(r.get('assignment')==batch['assignment'] and r.get('validator')==manifest['strict_technical_validator'],'Wrong receiver/assignment')
            for b in r.get('attempt_files',[]):verify(b)
            first=verify(s['original_whole_batch_first']);mirror=verify(s['canonical_whole_byte_mirror'])
            require(first==directory/f'attempt-{n:04d}'/'first.json' and mirror==directory/'first.json','Unexpected attempt/mirror path')
            require(binding(first)['sha256']==binding(mirror)['sha256'],'Canonical mirror changed original bytes')
            actor=load(verify(s['original_actor_seal']));verify(s['original_report'])
            require(actor.get('first_binding')==binding(first) and actor.get('actual_completion_claimed') is True and actor.get('template_only',False) is False,'Actor original seal differs')
            require(entry.get('attempt_receipt_bindings')==prior_bindings+[binding(rp)],'Terminal inventory must bind every prior/current whole attempt')
            valid_plans.append((directory,first,ids))
            for rid in ids:out[rid]='awaiting_whole_campaign_reception_validation'
            receipts.append(binding(rp))
        elif state=='technical_attempts_exhausted':
            require(not (directory/'root-selection.json').exists(),'Cannot mark a valid selected batch failed')
            expected=[]
            for n in range(1,4):
                p=directory/f'root-attempt-reception-{n:04d}-v2.json';r=load(p)
                require(r.get('state')=='technical_invalid_whole_batch' and r.get('assignment')==batch['assignment'],'All three whole attempts must actually fail')
                for b in r.get('attempt_files',[]):verify(b)
                expected.append(binding(p));receipts.append(binding(p))
            require(entry.get('attempt_receipt_bindings')==expected,'Exhausted attempt inventory differs')
            for rid in ids:out[rid]={'status':'execution_failure','labels':None,'failure_code':'whole_batch_three_technical_attempts_exhausted'}
        else:
            require(not (directory/'root-selection.json').exists(),'A received valid batch cannot become unreturned')
            terminal=load(verify(entry.get('terminal_evidence_binding')))
            require(terminal.get('status')=='ROOT_reviewed_terminal_not_returned' and terminal.get('run_id')==manifest['run_id'] and terminal.get('batch_id')==batch['batch_id'],'Actual terminal nonreturn evidence required')
            require(terminal.get('all_actor_tasks_terminated') is True and terminal.get('source_ids')==ids,'No running/unattributed nonreturn allowed')
            prior=[]
            for n in range(1,4):
                p=directory/f'root-attempt-reception-{n:04d}-v2.json'
                if not p.exists():break
                r=load(p);require(r.get('state')=='technical_invalid_whole_batch','Terminal nonreturn must retain previous whole failures')
                for b in r.get('attempt_files',[]):verify(b)
                prior.append(binding(p));receipts.append(binding(p))
            require(len(prior)<3,'Three terminal invalid attempts must remain execution_failure')
            require(not any((directory/f'root-attempt-reception-{n:04d}-v2.json').exists() for n in range(len(prior)+1,4)),'Noncontiguous attempt receipts forbidden')
            require(entry.get('attempt_receipt_bindings')==prior,'Prior failure receipts cannot be hidden')
            for rid in ids:out[rid]=None
    # Every batch's terminal original receipt is now checked. Only now open labels.
    for directory,first,ids in valid_plans:
        validator.verify(directory/'assignment.json',first)
        rows=load(first)['records'];require([r['source_id'] for r in rows]==ids,'Whole-batch IDs/order differ')
        for row in rows:out[row['source_id']]={'status':'completed','labels':{d:value(row['dimensions'][d]['value']) for d in DIMS}}
    require(list(out)==frozen_frame(manifest),'No selected-record subset or duplicate full-frame output')
    return out,{'inventory':binding(ip),'actual_terminal_receipts':receipts,'selection_policy':'frozen earliest technically valid whole batch; no label choice'}


def year_join(payload,c):
    rows=jsonlines(verify(c['year200_binding']));by={r['unit_id']:r for r in rows}
    require(len(rows)==200 and len(by)==200,'Year projection must exactly cover old200')
    for r in payload['records']:r['policy_year']=by[r['unit_id']]['policy_year']
    mapping=copy.deepcopy(c['year_mapping_metadata']);mapping['joined_projection_sha256']=canonical({'assignment_basis':mapping['assignment_basis'],'requested_years':sorted(mapping['requested_years']),'no_source_views':sorted(mapping['no_source_views']),'records':[{'unit_id':r['unit_id'],'policy_year':r['policy_year']} for r in sorted(payload['records'],key=lambda x:x['unit_id'])]})
    payload['metadata']['year_mapping']=mapping
    return payload


def build(receive_dir,review,c,stage,annual):
    actual_gate(review,c)
    # Full terminal gate BEFORE reference or any machine label read.
    terminal_inventory_gate(load(verify(review['LLM_terminal_inventory_binding'])),review,c)
    payload,ab_review,report=human_initial(receive_dir,review,c)
    reference=reference_projection(review,c);rule=rule_projection(c);llm,trace=llm_projection(review,c)
    for r in payload['records']:
        r['outputs'].update(reference=reference[r['unit_id']],rule=rule[r['unit_id']],LLM=llm[r['unit_id']])
        if stage=='machine_reference':r['outputs']={k:v for k,v in r['outputs'].items() if k not in ('A','B')}
    meta=payload['metadata'];meta['analysis_stage']=stage
    meta['identities']['reference']={'kind':'human_adjudication','credible':True,'blinded_to_machines':True,'identity_code':'|'.join(review['reference_human_identity_codes'])}
    meta['freeze_attestations']['reference_before_machine_comparison']=True
    meta['freeze_attestations']['final_rule_and_LLM_before_test_feedback']=True
    active=('reference','rule','LLM') if stage=='machine_reference' else ('A','B','reference','rule','LLM')
    rawbindings={'reference':review['reference_original_binding'],'rule':c['frozen_inputs']['rule_predictions'],'LLM':review['LLM_terminal_inventory_binding']}
    for method in active:
        if method in rawbindings:meta['input_seals'][method]={'sealed':True,'sha256':rawbindings[method]['sha256'],'joined_projection_sha256':canonical([{'unit_id':r['unit_id'],'output':r['outputs'][method]} for r in sorted(payload['records'],key=lambda x:x['unit_id'])])}
    meta['artifact_seals']['rule_protocol']={'sealed':True,'sha256':c['frozen_inputs']['rule_release']['sha256']}
    meta['artifact_seals']['LLM_protocol']={'sealed':True,'sha256':c['frozen_inputs']['LLM_manifest']['sha256']}
    if annual:year_join(payload,c)
    return payload,trace


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('mode',choices=('validate','analyze'))
    ap.add_argument('--review',type=Path,required=True);ap.add_argument('--receive-dir',type=Path,required=True)
    ap.add_argument('--stage',choices=('machine_reference','combined'),default='combined')
    ap.add_argument('--annual',action='store_true');ap.add_argument('--output-dir',type=Path,required=True)
    args=ap.parse_args();c=contract();review=load(args.review)
    output=args.output_dir.resolve();require(output.is_relative_to(HERE) and output!=HERE and not output.exists(),'Use a new output directory under this handoff')
    payload,trace=build(args.receive_dir,review,c,args.stage,args.annual)
    eb=c['frozen_inputs']['year_engine' if args.annual else 'engine'];engine=module('_registered200_statistics',eb)
    prep=engine.prepare(payload)
    output.mkdir(parents=True,exist_ok=False)
    def write(name,obj):
        with (output/name).open('x') as f:json.dump(obj,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')
    write('bound-statistical-input.json',payload);write('machine-original-reception-trace.json',trace)
    if args.mode=='analyze':write('historical-snapshot-statistics.json',engine.analyze(payload,replicates=5000,seed=20261010,guard_mode='single_category'))
    write('seal.json',{'status':'reviewed_historical_snapshot_'+args.mode,'created_at_utc':datetime.now(timezone.utc).isoformat(),'snapshot_id':SNAPSHOT,'review_binding':binding(args.review),'code':binding(__file__),'engine':eb,'replicates':5000 if args.mode=='analyze' else 0,'stage':args.stage,'annual':args.annual,'ROOT_review_is_trusted_human_attestation_not_cryptographic_identity':True,'formal_acceptance_claimed':False,'updated_candidate_validation_permitted':False,'members':[binding(p) for p in sorted(output.iterdir()) if p.is_file()]})
    print(json.dumps({'status':'historical_snapshot_'+args.mode,'assigned_N':len(prep['records']),'actual_new_human_judgments_created':0,'formal_acceptance':False}))

if __name__=='__main__':main()
