"""Finite compatibility receiver; no draw, prepare, coding, or identity certification."""
import argparse, datetime, hashlib, importlib.util, json, os, re, shutil, sys, tempfile
from pathlib import Path
sys.dont_write_bytecode=True
from interface_common import canonical, digest, parse_json, pointer_value, require, unpack_packet, verify_binding, verify_source_quote
HERE=Path(__file__).resolve().parent
DIMS=('S','E','Ec','I','F')
VERSION='full800-wrapper-human-receiver-1'
SUB_KEYS={'version','completion_status','packet_file_sha256','manual_sha256','record_N','dimensions_N','actual_actor_type','executor_code','identity_registry_sha256','actual_started_at','actual_submitted_at','labels_sha256','independence_declaration','AI_assistance','prior_development_exposure','image_view_records','source_read_or_use_attestation','human_coding_completed','sidecar_sha256'}
DIM_KEYS={'value','evidence_path','current_quote','context_quotes','source_quotes','reason','material_request'}
PATHS={'S':{'S_content','S_information'},'E':{'E_content','E_information'},'Ec':{'Ec_content','Ec_information'},'I':{'I1','I2','I3','I4'},'F':{'F_general','F_specific'}}

def exact(v,keys,where):require(isinstance(v,dict) and set(v)==set(keys),'missing/extra fields: '+where)
def nonempty(v,where):require(isinstance(v,str) and bool(v.strip()),'nonempty string required: '+where)
def load(path):return parse_json(Path(path).read_bytes())
def lines(raw):
    out=[]
    for line in raw.splitlines():require(bool(line.strip()),'blank JSONL line');out.append(parse_json(line))
    return out

def timevalue(v):
    nonempty(v,'time');t=datetime.datetime.fromisoformat(v.replace('Z','+00:00'));require(t.tzinfo is not None,'timezone required');return t

def legacy():
    entry=load(HERE/'compatibility-bindings.json')['legacy_workflow'];verify_binding(entry)
    spec=importlib.util.spec_from_file_location('_sealed_human_workflow',entry['path']);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def bind_path(path):
    p=Path(path).resolve();raw=p.read_bytes();return {'path':str(p),'sha256':digest(raw),'bytes':len(raw)}

def context_fragments(c):return legacy().text_fragments(c)
def context_quote_locations(context,prefix):
    out=[]
    def walk(v,ptr):
        if isinstance(v,list):
            for i,x in enumerate(v):walk(x,ptr+'/'+str(i))
        elif isinstance(v,dict) and isinstance(v.get('text'),str):out.append((ptr+'/text',v['text']))
    for key in ('text','title','caption'):
        if isinstance(context.get(key),str):out.append((prefix+'/'+key,context[key]))
    for key in ('headers','row_cells'):walk(context.get(key),prefix+'/'+key)
    return out

def continuous(q,texts):nonempty(q,'quote');require(any(q in t for t in texts),'not a continuous original quote')

def inspect_release(path,expected_sha):
    raw=Path(path).read_bytes();require(digest(raw)==expected_sha,'release SHA differs');r=parse_json(raw)
    exact(r,{'version','status','round_id','side','purpose','packet_manifest','packet_file','manual','manual_version','source_asset_index','identity_registry','executor_code','actual_actor_type'},'release')
    require(r['version']==VERSION and r['status']=='frozen_for_execution','explicit prospective release required')
    require(r['purpose'] in ('independent_validation','AI_draft','human_posthoc_review','synthetic_fixture'),'unknown actual purpose')
    m=parse_json(verify_binding(r['packet_manifest']))
    require(m.get('packet_version')=='full800-v14-role-wrapper-preparation-1' and m.get('side')==r['side'],'wrong original packet version/side')
    require(m['packet_file']['sha256']==r['packet_file']['sha256'] and m['packet_file']['bytes']==r['packet_file']['bytes'],'release changed original packet binding')
    verify_binding(r['manual']);nonempty(r['manual_version'],'actual manual version')
    if r['purpose']!='synthetic_fixture':
        formal=load(HERE/'formal-manual-binding.json')
        require(r['manual']['sha256']==formal['manual']['sha256'] and r['manual']['bytes']==formal['manual']['bytes'] and r['manual_version']==formal['manual_version'],'release manual differs from actual frozen component')
    require(m['source_asset_index']['sha256']==r['source_asset_index']['sha256'] and m['source_asset_index']['bytes']==r['source_asset_index']['bytes'],'original asset index changed')
    assets=parse_json(verify_binding(r['source_asset_index']))
    registry=parse_json(verify_binding(r['identity_registry']))
    nonempty(r['executor_code'],'assigned executor');nonempty(r['actual_actor_type'],'actual actor type')
    actors=registry.get('actors');require(isinstance(actors,list),'identity registry actors required')
    matches=[a for a in actors if a.get('executor_code')==r['executor_code']]
    require(len(matches)==1 and matches[0].get('actual_actor_type')==r['actual_actor_type'] and matches[0].get('assigned_side')==r['side'],'actual actor registry assignment mismatch')
    purpose_actor={'independent_validation':'real_human_independent','AI_draft':'AI_draft','human_posthoc_review':'real_human_posthoc_review','synthetic_fixture':'synthetic_toy'}
    require(r['actual_actor_type']==purpose_actor[r['purpose']],'AI/human identity cannot be relabeled by purpose')
    return r,m,assets

def read_new_packet(r,m):
    raw=verify_binding(r['packet_file']);packets=lines(raw)
    require(len(packets)==m['record_N'] and m['dimension_blank_N']==len(packets)*5,'original manifest count differs')
    seen=set();out={};sha_set=[]
    for p in packets:
        b,meta=unpack_packet(p);bid=p.get('blind_id');require(re.fullmatch(r['side']+r'-[0-9]{6}',bid or '') is not None and bid not in seen,'blind ID wrong/repeated')
        seen.add(bid);sha_set.append(meta['source_bundle_sha256']);out[bid]=(p,b)
    require(digest(canonical(sorted(sha_set)))==m['common_bundle_multiset_SHA256'],'original full bundle multiset differs')
    return out

def read_events(bundle,record,actor,start,end):
    exact(record,{'blind_id','path_evidence','source_read_events','source_use_events','image_view_events'},'sidecar record')
    for key in ('source_read_events','source_use_events','image_view_events'):require(isinstance(record[key],list),'event array required')
    reads={}
    for e in record['source_read_events']:
        exact(e,{'event_id','actor_code','bundle_pointer','view','view_sha256','occurred_at','delivery_status','actual_read_attestation'},'source read event')
        require(e['event_id'] not in reads and e['actor_code']==actor,'duplicate/foreign source read actor')
        require(start<=timevalue(e['occurred_at'])<=end,'source read time outside actual execution')
        require(e['delivery_status']=='complete' and e['actual_read_attestation'] is True,'incomplete/unattested source read')
        value=pointer_value(bundle,e['bundle_pointer']);require(e['view'] in ('text','geometry','document_bundle'),'pixel claim must be separate image event')
        require((e['view']=='text' and isinstance(value,str)) or (e['view']!='text' and isinstance(value,(dict,list))),'source view type differs')
        raw=value.encode('utf8') if e['view']=='text' else canonical(value)
        require(digest(raw)==e['view_sha256'],'source read original view hash differs');reads[e['event_id']]=e
    uses=[]
    for u in record['source_use_events']:
        exact(u,{'read_event_id','dimension','use'},'source use event');require(u['read_event_id'] in reads and u['dimension'] in DIMS,'use has no actual same-record read event');nonempty(u['use'],'source use explanation');uses.append(u)
    return reads,uses

def source_used(pointer,dimension,reads,uses):
    return any(u['dimension']==dimension and (reads[u['read_event_id']]['bundle_pointer']==pointer or
        (reads[u['read_event_id']]['view']=='document_bundle' and pointer.startswith(reads[u['read_event_id']]['bundle_pointer']+'/'))) for u in uses)

def check_images(bundle,record,assets,actor,start,end):
    index={a['sha256']:a for a in assets['files']};seen=set()
    for e in record['image_view_events']:
        exact(e,{'event_id','actor_code','source_asset_sha256','bundle_pointer','occurred_at','actual_pixel_view_attestation','location','note'},'image view event')
        require(e['event_id'] not in seen and e['actor_code']==actor,'duplicate/foreign image event');seen.add(e['event_id'])
        require(start<=timevalue(e['occurred_at'])<=end and e['actual_pixel_view_attestation'] is True,'unattested pixel event or time outside execution')
        require(e['source_asset_sha256'] in index,'image asset not available in bound original index')
        origin=pointer_value(bundle,e['bundle_pointer'])
        def values(v):
            if isinstance(v,dict):return [z for q in v.values() for z in values(q)]
            if isinstance(v,list):return [z for q in v for z in values(q)]
            return [v]
        require(e['source_asset_sha256'] in values(origin),'image SHA not bound to this original record pointer')
        a=index[e['source_asset_sha256']]
        require(a.get('image_pixels') is not None,'indexed asset not an image')
        verify_binding({'path':a['prepared_absolute_path'],'sha256':a['sha256'],'bytes':a['bytes']})
        nonempty(e['location'],'image location');nonempty(e['note'],'actual image observation')
    return {e['event_id']:e for e in record['image_view_events']}

def dimension(d,dim,bundle,side,reads,uses,images):
    exact(d,DIM_KEYS,'dimension');v=d['value'];require(v is None or type(v) is int and v in (0,1),'label must be integer 0/1/null')
    continuous(d['current_quote'],[bundle['source_record']['text']]);nonempty(d['reason'],'dimension reason');nonempty(d['evidence_path'],'evidence path')
    require(source_used('/source_record/text',dim,reads,uses),'current quote lacks saved actual source read/use event')
    paths=d['evidence_path'].split('+');require(len(set(paths))==len(paths) and set(paths)<=(PATHS[dim] if v==1 else {'not_met'} if v==0 else {'unknown'}),'label/path mismatch')
    contexts={c['context_id']:(i,c) for i,c in enumerate(bundle['source_record']['contexts'])}
    require(isinstance(d['context_quotes'],list) and isinstance(d['source_quotes'],list),'quote arrays required')
    for q in d['context_quotes']:
        exact(q,{'context_id','quote'},'context quote');require(q['context_id'] in contexts,'invented CTX');i,c=contexts[q['context_id']]
        continuous(q['quote'],context_fragments(c))
        locations=context_quote_locations(c,'/source_record/contexts/'+str(i))
        require(any(q['quote'] in text and source_used(ptr,dim,reads,uses) for ptr,text in locations),'CTX quote lacks saved same-view read/use')
    for q in d['source_quotes']:
        verify_source_quote(bundle,q);require(source_used(q['bundle_pointer'],dim,reads,uses),'public source quote lacks saved actual same-view read/use')
    needed=()
    if v==1 and 'I3' in paths:needed=('support_object','support_arrangement','direct_relation')
    if v==1 and 'F_specific' in paths:needed=('patient_drug_object','fairness_relation','current_arrangement_or_evaluation')
    p=side['path_evidence'].get(dim,{})
    permitted={'support_object','support_arrangement','direct_relation','patient_drug_object','fairness_relation','current_arrangement_or_evaluation'}
    require(isinstance(p,dict) and set(p)<=permitted and set(needed)<=set(p),'I3/specific F necessary relationship evidence missing')
    for role,a in p.items():
        nonempty(a.get('explanation'),'path relationship explanation');kind=a.get('kind')
        if kind=='current':
            exact(a,{'kind','quote','explanation'},'current path');continuous(a['quote'],[bundle['source_record']['text']]);require(a['quote'] in d['current_quote'],'path quote not in actual current quote')
        elif kind=='context':
            exact(a,{'kind','context_id','quote','explanation'},'CTX path');nonempty(a['quote'],'CTX path quote');require(any(q['context_id']==a['context_id'] and a['quote'] in q['quote'] for q in d['context_quotes']),'path CTX not in actual quote list')
        elif kind=='public':
            exact(a,{'kind','source_quote','explanation'},'public path');verify_source_quote(bundle,a['source_quote']);require(a['source_quote'] in d['source_quotes'],'public path not in actual quote list')
        elif kind=='image':
            exact(a,{'kind','event_id','quote_or_geometry','explanation'},'image path');require(a['event_id'] in images,'image path has no actual pixel event');nonempty(a['quote_or_geometry'],'image path observation')
        else:raise ValueError('unknown path source kind')
    req=d['material_request'];require(v is not None or isinstance(req,dict),'lawful null needs actual material request')
    if req is not None:
        exact(req,{'type','current_reference_quote','needed_material','why_decisive'},'material request');require(req['type'] in ('missing_source','unresolved_reference','unresolved_structure','rule_conflict'),'unknown request type')
        continuous(req['current_reference_quote'],[bundle['source_record']['text']]);nonempty(req['needed_material'],'missing material');nonempty(req['why_decisive'],'why missing material decisive')
    return int(req is not None)

def verify_new(packet_dir,labels_path,submission_path,sidecar_path,release_path,release_sha):
    r,m,assets=inspect_release(release_path,release_sha)
    require(Path(packet_dir).resolve()==Path(r['packet_manifest'].get('path',r['packet_manifest'].get('absolute_path'))).resolve().parent,'wrong assigned packet directory')
    packets=read_new_packet(r,m);sub=load(submission_path);exact(sub,SUB_KEYS,'submission')
    require(sub['version'] in ('full800-v14-human-submission-preparation-1','full800-v14-human-submission-1') and sub['completion_status']=='complete','unfilled/unknown submission cannot be first judgment')
    for key,expected in [('packet_file_sha256',r['packet_file']['sha256']),('manual_sha256',r['manual']['sha256']),('record_N',len(packets)),('dimensions_N',len(packets)*5),('executor_code',r['executor_code']),('actual_actor_type',r['actual_actor_type']),('identity_registry_sha256',r['identity_registry']['sha256'])]:require(sub[key]==expected,'submission binding differs: '+key)
    labels_raw=Path(labels_path).read_bytes();side_raw=Path(sidecar_path).read_bytes();require(digest(labels_raw)==sub['labels_sha256'] and digest(side_raw)==sub['sidecar_sha256'],'original submitted bytes differ')
    start=timevalue(sub['actual_started_at']);end=timevalue(sub['actual_submitted_at']);require(start<=end,'submission before start')
    nonempty(sub['prior_development_exposure'],'honest exposure declaration')
    require(sub['source_read_or_use_attestation'] is True,'actual source reading/use declaration missing')
    exact(sub['AI_assistance'],{'label_drafting_used','description'},'AI assistance');require(type(sub['AI_assistance']['label_drafting_used']) is bool,'actual AI involvement must be explicit');nonempty(sub['AI_assistance']['description'],'AI involvement description')
    exact(sub['independence_declaration'],{'own_first_judgment','machine_answers_unseen','peer_answers_unseen','no_discussion_before_seal'},'independence declaration');require(all(type(v) is bool for v in sub['independence_declaration'].values()),'declaration must report actual bools')
    if r['purpose']=='independent_validation':
        require(all(sub['independence_declaration'].values()) and sub['AI_assistance']['label_drafting_used'] is False and sub['human_coding_completed'] is True,'AI draft/posthoc cannot be independent human first')
    else:require(type(sub['human_coding_completed']) is bool,'actual human completion flag required')
    if r['actual_actor_type'] in ('AI_draft','synthetic_toy'):require(sub['human_coding_completed'] is False,'AI/toy cannot claim human completed')
    side=load(sidecar_path);exact(side,{'version','packet_file_sha256','manual_sha256','labels_sha256','actor_code','rows'},'sidecar')
    require(side['version']==VERSION and side['packet_file_sha256']==sub['packet_file_sha256'] and side['manual_sha256']==sub['manual_sha256'] and side['labels_sha256']==sub['labels_sha256'] and side['actor_code']==sub['executor_code'],'sidecar binding differs')
    rows=lines(labels_raw);require(len(rows)==len(packets) and len(side['rows'])==len(rows),'complete row/sidecar count differs')
    require([x['blind_id'] for x in rows]==list(packets) and [x['blind_id'] for x in side['rows']]==list(packets),'first row order missing/repeated/different')
    requests=0;image_records=[]
    for row,s in zip(rows,side['rows']):
        exact(row,{'blind_id','source_bundle_canonical_sha256','completion_status','dimensions'},'label row');p,b=packets[row['blind_id']]
        require(row['completion_status']=='complete','unfilled null placeholders are not actual decisions')
        require(row['source_bundle_canonical_sha256']==p['source_bundle_canonical_sha256'],'label source bundle SHA differs');exact(row['dimensions'],DIMS,'five dimensions');exact(s['path_evidence'],DIMS,'path evidence dimensions')
        reads,uses=read_events(b,s,sub['executor_code'],start,end);images=check_images(b,s,assets,sub['executor_code'],start,end)
        for dim in DIMS:requests+=dimension(row['dimensions'][dim],dim,b,s,reads,uses,images)
        image_records.extend(dict(e,blind_id=row['blind_id']) for e in s['image_view_events'])
    require(sub['image_view_records']==image_records,'submission image record list differs from saved events')
    for dependency in ('packet_manifest','packet_file','manual','source_asset_index','identity_registry'):verify_binding(r[dependency])
    return {'format_status':'passed','interface_version':VERSION,'record_count':len(rows),'dimension_count':len(rows)*5,'material_request_count':requests,'actual_actor_type_declared':r['actual_actor_type'],'purpose':r['purpose'],'release_binding':bind_path(release_path),'manual_binding':r['manual'],'labels_sha256':digest(labels_raw),'submission_sha256':digest(Path(submission_path).read_bytes()),'sidecar_sha256':digest(side_raw),'identity_and_actual_reading_external_audit':'pending; declared events plus hash do not prove human authorship or pixel viewing','semantic_accuracy':'not_evaluated','human_validation_complete':False,'formal_validation_complete':False}

def seal_new(args):
    result=verify_new(args.packet_dir,args.labels,args.submission,args.sidecar,args.release,args.release_sha256)
    dest=Path(args.destination).resolve();require(not dest.exists(),'first seal exists; never overwrite')
    dest.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=dest.parent/('.'+dest.name+'.first-seal.lock');fd=os.open(lock,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o400);os.close(fd)
    stage=Path(tempfile.mkdtemp(prefix='.seal-',dir=dest.parent))
    try:
        for name,path,sha in [('labels.jsonl',args.labels,result['labels_sha256']),('submission.json',args.submission,result['submission_sha256']),('submission-sidecar.json',args.sidecar,result['sidecar_sha256'])]:
            raw=Path(path).read_bytes();require(digest(raw)==sha,'submitted original changed after verify');p=stage/name;p.write_bytes(raw);p.chmod(0o400)
        require(digest(Path(args.release).read_bytes())==result['release_binding']['sha256'],'release changed after verify')
        release_bytes=Path(args.release).read_bytes();(stage/'release.json').write_bytes(release_bytes);(stage/'release.json').chmod(0o400)
        result.update(sealed_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),overwrite_allowed=False,original_first_bytes_preserved=True)
        p=stage/'seal.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');p.chmod(0o400)
        require(not dest.exists(),'concurrent first seal exists');os.rename(stage,dest)
    except BaseException:
        shutil.rmtree(stage,ignore_errors=True);lock.unlink(missing_ok=True);raise
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['verify','seal']);parser.add_argument('--interface',choices=['legacy','v14-wrapper'],required=True)
    for flag in ['packet-dir','labels','submission']:parser.add_argument('--'+flag,required=True)
    for flag in ['release','release-sha256','sidecar','destination']:parser.add_argument('--'+flag)
    a=parser.parse_args()
    try:
        if a.interface=='legacy':
            require(not any([a.release,a.release_sha256,a.sidecar]),'legacy interface does not take new release/sidecar')
            if a.command=='seal':require(a.destination,'seal destination required');result=legacy().seal(a.packet_dir,a.labels,a.submission,a.destination)
            else:result=legacy().verify(a.packet_dir,a.labels,a.submission)
        else:
            require(all([a.release,a.release_sha256,a.sidecar]),'new interface needs real release SHA and sidecar')
            if a.command=='seal':require(a.destination,'seal destination required');result=seal_new(a)
            else:result=verify_new(a.packet_dir,a.labels,a.submission,a.sidecar,a.release,a.release_sha256)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ValueError,OSError,KeyError,TypeError) as e:
        print(json.dumps({'status':'rejected','reason':str(e),'human_validation_complete':False,'formal_validation_complete':False},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
