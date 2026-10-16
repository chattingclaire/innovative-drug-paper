"""Small constructed compatibility checks only; never opens research packets."""
import copy, json, pathlib, sys, tempfile, types
sys.dont_write_bytecode=True
from interface_common import BUNDLE_KEYS, canonical, digest, unpack_packet, verify_source_quote
import human_receiver as h
HERE=pathlib.Path(__file__).resolve().parent
results=[]
def check(name,fn,reject=False):
    try:
        fn()
        if reject:raise AssertionError('expected rejection did not occur')
        results.append({'name':name,'passed':True,'expected':'reject' if reject else 'accept'})
    except (ValueError,OSError,KeyError,TypeError) as e:
        if not reject:raise
        results.append({'name':name,'passed':True,'expected':'reject','actual_reason':str(e)})
def js(p,x):p.write_bytes(json.dumps(x,ensure_ascii=False,indent=2).encode()+b'\n')
def bind(p):return h.bind_path(p)
with tempfile.TemporaryDirectory(prefix='.constructed-check-',dir=HERE) as tmp:
    p=pathlib.Path(tmp);manual=p/'toy-manual.txt';manual.write_text('仅构造格式检查，非真实手册。\n')
    current='本条仅为构造当前文字。';public='示例药品🧪对象与支持机会、患者机会安排。'
    b={k:[] for k in BUNDLE_KEYS};b['common_source_bundle_version']={'version':'toy'};b['source_record']={'id':'RECODE25-99999','text':current,'contexts':[]};b['explicit_or_primary_source_resources']=[{'text':public}]
    br=canonical(b);wrapper={'packet_version':'full800-v14-role-wrapper-preparation-1','blind_id':'A-000001','source_bundle_canonical_sha256':digest(br),'source_bundle_canonical_UTF8_bytes':len(br),'source_bundle':b}
    check('bare_bundle_preserved',lambda: (unpack_packet(b)[0]==b) or (_ for _ in []).throw(AssertionError()))
    check('five_root_wrapper_preserves_all_ten_root_values',lambda: (unpack_packet(wrapper)[0]==b) or (_ for _ in []).throw(AssertionError()))
    wrong=copy.deepcopy(wrapper);wrong['source_bundle_canonical_sha256']='0'*64
    check('wrong_nested_bundle_hash_rejected',lambda:unpack_packet(wrong),True)
    packet=p/'packet.jsonl';packet.write_bytes(canonical(wrapper)+b'\n');asset=p/'assets.json';js(asset,{'files':[]})
    manifest=p/'packet-manifest.json';js(manifest,{'packet_version':wrapper['packet_version'],'side':'A','packet_file':dict(absolute_path=str(packet),**{k:v for k,v in bind(packet).items() if k!='path'}),'record_N':1,'dimension_blank_N':5,'common_bundle_multiset_SHA256':digest(canonical([digest(br)])),'source_asset_index':bind(asset)})
    registry=p/'identity.json';js(registry,{'actors':[{'executor_code':'ToyA','actual_actor_type':'synthetic_toy','assigned_side':'A'}]})
    release=p/'release.json';r={'version':h.VERSION,'status':'frozen_for_execution','round_id':'toy-format-only','side':'A','purpose':'synthetic_fixture','packet_manifest':bind(manifest),'packet_file':bind(packet),'manual':bind(manual),'manual_version':'toy-only','source_asset_index':bind(asset),'identity_registry':bind(registry),'executor_code':'ToyA','actual_actor_type':'synthetic_toy'};js(release,r)
    q={'source_id':b['source_record']['id'],'source_bundle_sha256':digest(br),'bundle_pointer':'/explicit_or_primary_source_resources/0/text','quote':public[2:8],'span':{'start':2,'end':8}}
    check('continuous_unicode_public_quote_with_emoji',lambda:verify_source_quote(b,q))
    labels=p/'labels.jsonl';side=p/'sidecar.json';sub=p/'submission.json'
    dimensions={d:{'value':0,'evidence_path':'not_met','current_quote':current,'context_quotes':[],'source_quotes':[],'reason':'构造0理由，只核格式。','material_request':None} for d in h.DIMS}
    for d,path in [('I','I3'),('F','F_specific')]:dimensions[d].update(value=1,evidence_path=path,source_quotes=[q],reason='构造正路径证据，只核字段与原文位置。')
    row={'blind_id':'A-000001','source_bundle_canonical_sha256':digest(br),'completion_status':'complete','dimensions':dimensions}
    path={d:{} for d in h.DIMS}
    for d,roles in [('I',('support_object','support_arrangement','direct_relation')),('F',('patient_drug_object','fairness_relation','current_arrangement_or_evaluation'))]:
        path[d]={role:{'kind':'public','source_quote':q,'explanation':'构造角色 '+role+'，非语义裁定。'} for role in roles}
    start='2000-01-01T00:00:00+00:00';readtime='2000-01-01T00:00:01+00:00';end='2000-01-01T00:00:02+00:00'
    read=[{'event_id':key,'actor_code':'ToyA','bundle_pointer':ptr,'view':'text','view_sha256':digest(text.encode()),'occurred_at':readtime,'delivery_status':'complete','actual_read_attestation':True} for key,ptr,text in [('TOY-C','/source_record/text',current),('TOY-P',q['bundle_pointer'],public)]]
    events={'blind_id':'A-000001','path_evidence':path,'source_read_events':read,'source_use_events':[{'read_event_id':'TOY-C','dimension':d,'use':'仅构造当前引文使用'} for d in h.DIMS]+[{'read_event_id':'TOY-P','dimension':d,'use':'仅构造公共引文使用'} for d in ['I','F']],'image_view_events':[]}
    def save(row_value=row,event_value=events,sub_changes=None):
        labels.write_bytes(canonical(row_value)+b'\n')
        sc={'version':h.VERSION,'packet_file_sha256':bind(packet)['sha256'],'manual_sha256':bind(manual)['sha256'],'labels_sha256':bind(labels)['sha256'],'actor_code':'ToyA','rows':[event_value]};js(side,sc)
        sm={'version':'full800-v14-human-submission-1','completion_status':'complete','packet_file_sha256':bind(packet)['sha256'],'manual_sha256':bind(manual)['sha256'],'record_N':1,'dimensions_N':5,'actual_actor_type':'synthetic_toy','executor_code':'ToyA','identity_registry_sha256':bind(registry)['sha256'],'actual_started_at':start,'actual_submitted_at':end,'labels_sha256':bind(labels)['sha256'],'independence_declaration':{'own_first_judgment':False,'machine_answers_unseen':False,'peer_answers_unseen':False,'no_discussion_before_seal':False},'AI_assistance':{'label_drafting_used':True,'description':'synthetic shape fixture only, never research labels'},'prior_development_exposure':'synthetic fixture, no human execution','image_view_records':[],'source_read_or_use_attestation':True,'human_coding_completed':False,'sidecar_sha256':bind(side)['sha256']}
        if sub_changes:sm.update(sub_changes)
        js(sub,sm)
    def verify():return h.verify_new(p,labels,sub,side,release,bind(release)['sha256'])
    save();check('new_wrapper_submission_public_I3_F_and_synthetic_identity',verify)
    save(sub_changes={'manual_sha256':'0'*64});check('wrong_manual_sha_rejected',verify,True)
    save(sub_changes={'actual_actor_type':None});check('missing_actual_identity_rejected',verify,True)
    bad=copy.deepcopy(row);bad['completion_status']='unfilled'
    for d in h.DIMS:bad['dimensions'][d]={'value':None,'evidence_path':None,'current_quote':None,'context_quotes':[],'source_quotes':[],'reason':None,'material_request':None}
    save(bad);check('unfilled_null_placeholder_not_first',verify,True)
    bad_events=copy.deepcopy(events);bad_events['path_evidence']['I'].pop('direct_relation');save(event_value=bad_events);check('missing_I3_relation_evidence_rejected',verify,True)
    bad_events=copy.deepcopy(events);bad_events['path_evidence']['F'].pop('fairness_relation');save(event_value=bad_events);check('missing_specific_F_relation_evidence_rejected',verify,True)
    bad=copy.deepcopy(row);bad['dimensions']['I']['source_quotes'][0]['bundle_pointer']='/absent';save(bad);check('wrong_public_pointer_rejected_by_receiver',verify,True)
    bad_events=copy.deepcopy(events);bad_events['source_use_events']=[e for e in bad_events['source_use_events'] if e['read_event_id']!='TOY-P'];save(event_value=bad_events);check('public_quote_without_actual_same_view_use_rejected',verify,True)
    nullrow=copy.deepcopy(row);nullrow['dimensions']['S'].update(value=None,evidence_path='unknown',material_request={'type':'missing_source','current_reference_quote':current,'needed_material':'构造缺材','why_decisive':'构造原因'});save(nullrow);check('lawful_null_with_concrete_request_retained',verify)
    nullrow['dimensions']['S']['material_request']=None;save(nullrow);check('null_without_request_rejected',verify,True)
    save();sealed=p/'sealed';args=types.SimpleNamespace(packet_dir=p,labels=labels,submission=sub,sidecar=side,release=release,release_sha256=bind(release)['sha256'],destination=sealed)
    check('first_seal_preserves_original_bytes',lambda:h.seal_new(args))
    assert (sealed/'labels.jsonl').read_bytes()==labels.read_bytes() and (sealed/'submission-sidecar.json').read_bytes()==side.read_bytes()
    check('first_seal_cannot_overwrite',lambda:h.seal_new(args),True)
    # Actual leaf text scope must support the exact CTX quote as well as object scopes.
    ctxb=copy.deepcopy(b);ctxb['source_record']['contexts']=[{'context_id':'CTX-TOY','text':'构造连续语境。'}]
    ctxs=copy.deepcopy(events);ctxs['source_read_events']=[read[0],{'event_id':'TOY-CTX','actor_code':'ToyA','bundle_pointer':'/source_record/contexts/0/text','view':'text','view_sha256':digest('构造连续语境。'.encode()),'occurred_at':readtime,'delivery_status':'complete','actual_read_attestation':True}];ctxs['source_use_events']=[{'read_event_id':'TOY-C','dimension':'S','use':'构造当前文字'},{'read_event_id':'TOY-CTX','dimension':'S','use':'构造语境叶文字'}]
    ctxd=copy.deepcopy(row['dimensions']['S']);ctxd['context_quotes']=[{'context_id':'CTX-TOY','quote':'连续语境'}]
    def ctxcheck():
        reads,uses=h.read_events(ctxb,ctxs,'ToyA',h.timevalue(start),h.timevalue(end));return h.dimension(ctxd,'S',ctxb,ctxs,reads,uses,{})
    check('real_CTX_text_leaf_read_and_use_accepted',ctxcheck)
    # One fresh small legacy fixture, directly delegates original workflow; no old suite.
    old=p/'legacy';old.mkdir();w=h.legacy();(old/'manual.md').write_bytes(manual.read_bytes());oldrows=[];oldlabels=[]
    for i in [1,2]:
        x={'unit_text':current,'unit_source_ref':{'source_sha256':'0'*64,'source_locator':{'paragraph_ids':[1]},'provenance_status':'binary_source_verified'},'source_title':None,'contexts':[],'attachments':[],'packet_version':w.VERSION,'manual_version':'toy','blind_id':'A-'+str(i).zfill(6),'material_status':'ready','neutral_material_note':None};x['content_sha256']=w.content_sha(x);oldrows.append(x)
        lab=w.blank_row(x);lab['completion_status']='complete'
        for d in h.DIMS:lab['dimensions'][d].update(value=0,evidence_path='not_met',current_quote=current,reason='synthetic legacy compatibility only')
        oldlabels.append(lab)
    w.put_lines(old/'packet.jsonl',oldrows);m={'schema_version':w.VERSION,'purpose':'toy','round_id':'toy','parent_round_id':None,'side':'A','executor_code':'ToyA','identity_registry_sha256':'0'*64,'manual_version':'toy','manual_sha256':w.sha_file(old/'manual.md'),'packet_sha256':w.sha_file(old/'packet.jsonl'),'record_count':2,'dimension_count':10,'assets':[],'content_set_sha256':w.sha_bytes(w.canonical(sorted(x['content_sha256'] for x in oldrows)))};w.put_json(old/'packet-manifest.json',m);w.put_lines(old/'labels.jsonl',oldlabels)
    sm={'schema_version':w.VERSION,'state':'complete','purpose':'toy','round_id':'toy','executor_code':'ToyA','actual_actor_type':'synthetic_toy','identity_registry_sha256':'0'*64,'manual_sha256':m['manual_sha256'],'packet_sha256':m['packet_sha256'],'labels_sha256':w.sha_file(old/'labels.jsonl'),'record_count':2,'dimension_count':10,'started_at':start,'submitted_at':end,'independence_declaration':{'own_first_judgment':True,'machine_answers_unseen':True,'peer_answers_unseen':True,'no_discussion_before_seal':True},'AI_assistance':{'label_drafting_used':False,'description':'synthetic legacy shape checks'},'prior_development_exposure':'synthetic','material_request_count':0,'image_view_attestation':True};w.put_json(old/'submission.json',sm)
    check('unchanged_legacy_verify_delegation',lambda:w.verify(old,old/'labels.jsonl',old/'submission.json'))
report={'scope':'18 finite constructed interface checks only; no cohort/engine/native/model execution','cases':results,'all_passed':all(x['passed'] for x in results),'research_source_body_reads':0,'model_calls':0,'rule_inference_runs':0,'real_human_submissions':0,'events_are_synthetic_shape_fixtures_not_actual_read_or_use_receipts':True}
(HERE/'finite-check-results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'passed':len(results),'actual_research_runs':0}))
