"""Execute the previously registered R200 rule only after complete H600 results."""
import argparse,collections,copy,hashlib,json,random,re,unicodedata
from pathlib import Path
from datetime import datetime
OUT=Path(__file__).parent
DIMS=('S','E','Ec','I','F')
SEED=2026092604
WORDS={'S':'风险 不良 毒 警戒 禁忌 安全 质量','E':'疗效 获益 治疗 效果 终点 临床 试验',
       'Ec':'价格 费用 基金 成本 支付 报销 预算 负担','I':'创新 新药 原创 改良 机制 靶点 突破 研发 专利 品种 剂型',
       'F':'公平 可及 保障 短缺 供应 配备 困难 基层 偏远 获取 未满足 负担 配送 管理'}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
def require(condition,message):
    if not condition:raise ValueError(message)
def unique_rows(rows,key,name):
    require(isinstance(rows,list),name+' must be a list')
    result={}
    for row in rows:
        require(isinstance(row,dict),name+' row must be an object')
        value=row.get(key)
        require(isinstance(value,str) and value and value not in result,name+' missing/duplicate '+key)
        result[value]=row
    return result
def unique_ids(values,name):
    require(isinstance(values,(list,tuple,set,dict)),name+' must be an ID collection or ID-keyed mapping')
    require(all(isinstance(k,str) and k for k in values),name+' contains invalid ID')
    require(len(values)==len(set(values)),name+' contains duplicate IDs')
    return set(values)
def helper_program(path,expected_sha=None):
    """Execute helper definitions only; never enter either frozen program's main."""
    data=Path(path).read_bytes();fingerprint=hashlib.sha256(data).hexdigest()
    if expected_sha is not None:require(fingerprint==expected_sha,'Frozen helper changed: '+str(path))
    scope={'__name__':'_r200_helper_only','__file__':str(path)}
    exec(compile(data,str(path),'exec'),scope)
    return scope,fingerprint
def content(x,context_container=False):
    if isinstance(x,str):return [x]
    if isinstance(x,list):return [s for v in x for s in content(v,context_container)]
    if isinstance(x,dict):
        strings=[]
        for key,value in x.items():
            if key in {'text','caption','headers','row_cells'}:strings.extend(content(value))
            elif key=='contexts':strings.extend(content(value,True))
            elif context_container and isinstance(value,(dict,list)):strings.extend(content(value))
        return strings
    return []
def broad_hits(row,fields,targets):
    require(isinstance(row.get('unit_text'),str),'Unit text must be a string; empty text remains eligible')
    text=unicodedata.normalize('NFKC','\n'.join([row['unit_text']]+[
        part for field in fields if field not in {'content_role','content_role_basis'}
        for part in content(row.get(field))]))
    return [dim for dim in targets if any(word in text for word in WORDS[dim].split())]
def trigger_dimensions(rows,expected_n=600):
    require(len(unique_rows(rows,'id','H600 normalized rows'))==expected_n,'Complete H600 row count required')
    positive={d:{c:0 for c in ('A','C')} for d in DIMS}
    for row in rows:
        for coder in ('A','C'):
            values=row.get(coder)
            require(isinstance(values,dict) and set(values)==set(DIMS),'H600 exact five labels required')
            for dim,value in values.items():
                require((type(value) is int and value in (0,1)) or (type(value) is str and value=='待定'),'Invalid H600 label; no coercion')
                if type(value) is int and value==1:positive[dim][coder]+=1
    order=sorted((d for d in DIMS if min(positive[d].values())<100),key=lambda d:(min(positive[d].values()),DIMS.index(d)))
    return positive,order
def pick_round_robin(order,pools,n,seen):
    chosen=[];positions={d:0 for d in order}
    while len(chosen)<n:
        changed=False
        for d in order:
            while positions[d]<len(pools[d]) and pools[d][positions[d]] in seen:positions[d]+=1
            if positions[d]<len(pools[d]):
                k=pools[d][positions[d]];positions[d]+=1;seen.add(k);chosen.append(k);changed=True
                if len(chosen)==n:break
        if not changed:break
    return chosen
def select_candidates(eligible_ids,prediction_rows,wide,targets,machine_parser,h600_ids=(),development_ids=()):
    """Pure 80/80/40 draw. Parse all supplied predictions across all five dimensions.

    machine_parser is the frozen holdout_results.machine_labels callable. Pending
    predictions cannot enter a definite-negative bucket but remain in final fill.
    Returned bucket information is private researcher metadata, never coder input.
    """
    eligible=unique_ids(eligible_ids,'eligible')
    require(not eligible & unique_ids(h600_ids,'H600 IDs'),'Eligible pool overlaps H600')
    require(not eligible & unique_ids(development_ids,'development IDs'),'Eligible pool overlaps development exclusions')
    require(isinstance(targets,list) and targets and len(set(targets))==len(targets) and all(d in DIMS for d in targets),'Nonempty unique target dimensions required')
    predictions=unique_rows(prediction_rows,'id','predictions');normalized={};converted=[]
    for key,row in predictions.items():
        values,was_pending=machine_parser(row);normalized[key]=values
        if was_pending:converted.append(key)
    require(eligible<=set(predictions),'Missing eligible prediction')
    require(isinstance(wide,dict) and eligible<=set(wide),'Missing broad-search record')
    for key in eligible:require(isinstance(wide[key],list) and len(wide[key])==len(set(wide[key])) and all(d in targets for d in wide[key]),'Invalid broad-search dimension list')
    allzero={key for key in eligible if all(normalized[key][d]==0 for d in targets)}
    rng=random.Random(SEED)
    def shuffled(ids):
        values=sorted(ids);rng.shuffle(values);return values
    p1={d:shuffled(k for k in eligible if normalized[k][d]==1) for d in targets}
    p2={d:shuffled(k for k in allzero if d in wide[k]) for d in targets}
    p3=shuffled(allzero);seen=set();selected=[];bucket={}
    def add(chosen,group):
        for key in chosen:selected.append(key);bucket[key]=group
    add(pick_round_robin(targets,p1,80,seen),'dictionary_positive')
    add(pick_round_robin(targets,p2,80,seen),'wide_search_dictionary_negative')
    chosen=[k for k in p3 if k not in seen][:40];seen.update(chosen);add(chosen,'random_dictionary_negative')
    n=min(200,len(eligible))
    if len(selected)<n:add(pick_round_robin(targets,p1,n-len(selected),seen),'dictionary_positive_fill')
    if len(selected)<n:add(pick_round_robin(targets,p2,n-len(selected),seen),'wide_search_dictionary_negative_fill')
    if len(selected)<n:
        chosen=[k for k in p3 if k not in seen][:n-len(selected)];seen.update(chosen);add(chosen,'random_dictionary_negative_fill')
    if len(selected)<n:
        chosen=shuffled(eligible-seen)[:n-len(selected)];seen.update(chosen);add(chosen,'remaining_random_fill')
    require(len(selected)==len(set(selected))==n,'Challenge budget/uniqueness mismatch')
    selection_order=list(selected);rng.shuffle(selected)
    return {'selected':selected,'selection_order_before_display_shuffle':selection_order,'bucket':bucket,'n':n,
            'normalized_predictions':normalized,'machine_pending_ids':sorted(eligible & set(converted)),
            'bucket_counts':dict(collections.Counter(bucket.values()))}
def make_blind_record(row,bid,fields,clean_context,clean_assessment):
    return {'id':bid,'text':row['unit_text'],'source_title':row['original_file_stem'],'pages':row['pages'],
            'contexts':{f:clean_context(row[f]) for f in fields if row.get(f)},
            'input_assessment':clean_assessment(row.get('input_assessment',{'status':'not_assessed'})),
            'context_usage':'仅编码text；核验语境解释对象/条件/指代，不继承全部标签。位置相邻不等于有效父级。材料不足保留待定。'}
def guard_prior_attempt(existing):
    require(not any(existing.values()),'Preserve prior challenge, nontrigger report or partial attempt; never redraw')
def main():
    p=argparse.ArgumentParser();p.add_argument('--h600-results',type=Path);p.add_argument('--self-test',action='store_true');a=p.parse_args()
    if a.self_test:
        require(a.h600_results is None,'Synthetic QA accepts no real H600 result path')
        print(json.dumps(self_test(),ensure_ascii=False,indent=2));return
    require(a.h600_results is not None,'Explicit --h600-results required')
    dest=OUT/'R200';partial=OUT/'.R200.partial';nontrigger=OUT/'R200-未触发说明.json'
    guard_prior_attempt({p.name:p.exists() or p.is_symlink() for p in (dest,partial,nontrigger)})
    result_bytes=a.h600_results.read_bytes();result=json.loads(result_bytes)
    result_sha=hashlib.sha256(result_bytes).hexdigest();sampler_sha=sha(Path(__file__))
    require(result['status']=='completed_frozen_ID_join_not_validation_pass','Complete H600 bridge output required')
    require(result['design_and_interval_metadata']['sample_size_matches_H600_plan'] is True,'H600 sample size flag false')
    raw=result['archive']['normalized_rows_without_generated_reference']
    freeze_path=OUT/'最终冻结清单.json';freeze_bytes=freeze_path.read_bytes();freeze=json.loads(freeze_bytes);freeze_sha=hashlib.sha256(freeze_bytes).hexdigest()
    require(freeze['status']=='frozen_for_reference_label_holdout','Final freeze required')
    require(result['archive']['input_snapshot_hashes']['freeze']==freeze_sha,'H600/freeze mismatch')
    files={k:Path(v['path']) for k,v in freeze['files'].items()}
    def verify_snapshots():
        for k,pth in files.items():require(sha(pth)==freeze['files'][k]['sha256'],'Frozen file changed: '+k)
        require(sha(freeze_path)==freeze_sha and sha(a.h600_results)==result_sha,'Freeze/H600 result changed')
        require(sha(Path(__file__))==sampler_sha,'Challenge program changed during execution')
    verify_snapshots()
    require(sha(OUT/'R200-预定挑战集规则.md')==freeze['files']['R200_plan']['sha256'],'Registered R200 rule mismatch')
    pos,targets=trigger_dimensions(raw)
    mapping=result['archive']['sampling_manifest_original']
    sampled=unique_rows(mapping['rows'],'id','H600 mapping')
    require(set(sampled)=={r['id'] for r in raw},'H600 mapping/normalized ID mismatch')
    if not targets:
        verify_snapshots()
        with nontrigger.open('x') as f:json.dump({'status':'not_triggered','positive_counts':pos,'freeze_manifest_sha256':freeze_sha,
            'H600_results_sha256':result_sha,'sampler_sha256':sampler_sha},f,ensure_ascii=False,indent=2)
        print('No R200 triggered');return
    bridge,_=helper_program(files['holdout_results'],freeze['files']['holdout_results']['sha256'])
    projection,_=helper_program(files['sampler'],freeze['files']['sampler']['sha256'])
    eligible=unique_ids(mapping['not_selected_ids'],'remaining H600 pool')
    h600_ids=unique_ids([r['review_id'] for r in mapping['rows']],'sampled original IDs')
    exposure=load(files['exposure']);development_ids=unique_ids(exposure['exclusions'],'development exclusions')
    require(eligible==unique_ids(exposure['provisional_eligible_ids'],'frozen U*')-h600_ids,'Remaining pool differs from frozen U* minus H600')
    allunits=unique_rows(list(map(json.loads,files['corpus'].read_text().splitlines())),'review_id','corpus')
    units={k:r for k,r in allunits.items() if r['count_as_analysis_unit'] is True}
    prediction_rows=load(files['dictionary_predictions'])['rows'];pred=unique_rows(prediction_rows,'id','predictions')
    require(eligible<=set(units)&set(pred),'Remaining IDs absent from analysis corpus/predictions')
    fields=freeze['context_fields'];wide={}
    require(isinstance(fields,list) and fields and len(set(fields))==len(fields) and set(fields)<=set(projection['DEFAULT_CONTEXT_FIELDS']),'Unfrozen context field selection')
    for k in sorted(eligible):
        r=units[k];wide[k]=broad_hits(r,fields,targets)
        require(pred[k]['unit_text_sha256']==hashlib.sha256(r['unit_text'].encode()).hexdigest(),'Candidate prediction/text hash mismatch')
    selection=select_candidates(sorted(eligible),prediction_rows,wide,targets,bridge['machine_labels'],h600_ids,development_ids)
    selected=selection['selected'];n=selection['n'];blind=[];researcher=[]
    for i,k in enumerate(selected,1):
        r=units[k];bid=f'R200-{i:04d}'
        researcher.append({'id':bid,'review_id':k,'candidate_bucket':selection['bucket'][k],'wide_search_dimensions':wide[k],
                           'dictionary_positive_dimensions':[d for d in targets if selection['normalized_predictions'][k][d]==1],
                           'unit_text_sha256':pred[k]['unit_text_sha256'],'inclusion_probability':None})
        blind.append(make_blind_record(r,bid,fields,projection['clean_context'],projection['clean_assessment']))
    partial.mkdir()
    plan={'status':'drawn_challenge_not_representative' if n else 'no_remaining_candidates','n':n,'remaining_pool_N':len(eligible),'targets':targets,'H600_positive_counts':pos,
          'seed':SEED,'bucket_counts':selection['bucket_counts'],'created_at':datetime.now().astimezone().isoformat(),'freeze_manifest_sha256':freeze_sha,
          'H600_results_sha256':result_sha,'sampler_sha256':sampler_sha,'machine_parser_sha256':freeze['files']['holdout_results']['sha256'],
          'probability_scope':'按维度稀有度与多重命中轮转选择，非等概率；不建立代表U*的权重，仅对挑战集合描述，不能合并H600总体指标。'}
    (partial/'抽样清单-研究者.json').write_text(json.dumps({'plan':plan,'rows':researcher,'selection_order_before_display_shuffle':selection['selection_order_before_display_shuffle']},ensure_ascii=False,indent=2))
    for c in (('A','C') if n else ()):
        d=partial/f'agent-{c}';d.mkdir();(d/'五维共用编码协议.md').write_bytes(files['protocol'].read_bytes())
        for batch in range((n+24)//25):
            packet={'protocol_version':freeze['protocol_version'],'purpose':'challenge_AI_independent_not_representative','batch':batch+1,'total_batches':(n+24)//25,'rows':blind[batch*25:(batch+1)*25]}
            (d/f'材料-{batch+1:02d}.json').write_text(json.dumps(packet,ensure_ascii=False,indent=2))
    verify_snapshots()
    for packet in (partial/'agent-A').glob('*'):require(sha(packet)==sha(partial/'agent-C'/packet.name),'A/C challenge packets differ')
    plan['output_files']={str(p.relative_to(partial)):sha(p) for p in partial.rglob('*') if p.is_file()}
    plan['release_status']='ready_for_blind_review' if n else 'no_packets_created'
    (partial/'封存信息.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2));partial.rename(dest)
    print(json.dumps({'drawn':n,'targets':targets,'seed':plan['seed'],'output':str(dest)},ensure_ascii=False))
def self_test():
    """Read only allowed program sources and registered rule; no study data."""
    bridge,bridge_sha=helper_program(OUT/'holdout_results.py')
    projection,projection_sha=helper_program(OUT/'sample_holdout.py')
    machine_parser=bridge['machine_labels'];checks={};rejected={}
    def must_fail(name,call):
        try:call()
        except (ValueError,KeyError,TypeError) as exc:rejected[name]=str(exc)
        else:raise AssertionError('Invalid synthetic input accepted: '+name)
    counts={'S':(99,100),'E':(100,100),'Ec':(0,0),'I':(99,98),'F':(0,1)}
    raw=[{'id':f'synthetic-H-{i:03d}',**{c:{d:1 if i<counts[d][j] else '待定' for d in DIMS}
         for j,c in enumerate(('A','C'))}} for i in range(600)]
    positive,targets=trigger_dimensions(raw)
    require(targets==['Ec','F','I','S'] and positive['S']=={'A':99,'C':100},'Trigger order/threshold failed')
    sufficient=[{'id':str(i),'A':{d:int(i<100) for d in DIMS},'C':{d:int(i<100) for d in DIMS}} for i in range(600)]
    require(trigger_dimensions(sufficient)[1]==[],'Exactly 100 should not trigger')
    malformed=copy.deepcopy(raw);malformed[0]['A']['S']=True
    must_fail('boolean_H600_label',lambda:trigger_dimensions(malformed))
    must_fail('incomplete_H600',lambda:trigger_dimensions(raw[:-1]))
    require(pick_round_robin(['F','S'],{'F':['shared','F-only'],'S':['shared','S-only']},3,set())==['shared','S-only','F-only'],'Round-robin duplicate skipping failed')
    checks['trigger_threshold_tie_order_and_multihit_rotation']='passed'
    def fixture(p=0,w=0,z=0,u=0):
        eligible=[];predictions=[];wide={}
        for prefix,count in [('P',p),('W',w),('Z',z),('U',u)]:
            for i in range(count):
                key=f'{prefix}{i:04d}';eligible.append(key)
                values={d:None if prefix=='U' else int(prefix=='P' and d in ('S','E')) for d in DIMS}
                predictions.append({'id':key,'labels':values,'judgement_status':'undetermined' if prefix=='U' else 'determined',
                                    'input_assessment_status':'context_insufficient' if prefix=='U' else 'sufficient'})
                wide[key]=['S','E'] if prefix=='W' else []
        return eligible,predictions,wide
    def choose(data,**kw):return select_candidates(*data,['S','E'],machine_parser,**kw)
    full=fixture(120,120,120);selection=choose(full)
    require(selection['bucket_counts']=={'dictionary_positive':80,'wide_search_dictionary_negative':80,'random_dictionary_negative':40},'80/80/40 quota failed')
    require(len(selection['selected'])==len(set(selection['selected']))==200,'Multidimension duplicate selected')
    reverse=(list(reversed(full[0])),list(reversed(full[1])),dict(reversed(list(full[2].items()))))
    require(choose(reverse)['selected']==selection['selected'],'Selection depends on input iteration order')
    require(selection['selected']!=selection['selection_order_before_display_shuffle'],'Display order was not reshuffled')
    require(len({selection['bucket'][key] for key in selection['selected'][:20]})==3,'Synthetic display remains grouped by provenance')
    checks['quota_80_80_40_stable_ID_seed_and_display_shuffle']='passed'
    fill_cases=[(fixture(p=250,u=30),{'dictionary_positive':80,'dictionary_positive_fill':120}),
                (fixture(w=250),{'wide_search_dictionary_negative':80,'random_dictionary_negative':40,'wide_search_dictionary_negative_fill':80}),
                (fixture(z=250),{'random_dictionary_negative':40,'random_dictionary_negative_fill':160}),
                (fixture(u=250),{'remaining_random_fill':200})]
    for data,expected in fill_cases:require(choose(data)['bucket_counts']==expected,'Registered shortage fill order failed')
    small=fixture(10,15,30,10);small_result=choose(small)
    require(small_result['n']==65 and set(small_result['selected'])==set(small[0]),'Small pool not fully retained')
    require(small_result['bucket_counts']['remaining_random_fill']==10,'Pending units silently excluded')
    require(choose(fixture())['n']==0 and choose(fixture(u=1))['n']==1,'Empty/singleton remaining pool failed')
    checks['shortage_fill_priority_and_pool_less_than_200_including_pending']='passed'
    must_fail('H600_overlap',lambda:choose(full,h600_ids=[full[0][0]]))
    must_fail('development_overlap',lambda:choose(full,development_ids=[full[0][0]]))
    must_fail('development_mapping_overlap',lambda:choose(full,development_ids={full[0][0]:['synthetic exclusion reason']}))
    must_fail('duplicate_eligible_ID',lambda:choose((full[0]+[full[0][0]],full[1],full[2])))
    must_fail('duplicate_prediction_ID',lambda:choose((full[0],full[1]+[full[1][0]],full[2])))
    invalid_machine=[('boolean_non_target_dimension',lambda r:r['labels'].update(F=True)),
                     ('partial_None',lambda r:r['labels'].update(S=None)),
                     ('null_without_authorized_state',lambda r:r.update(labels={d:None for d in DIMS})),
                     ('binary_undetermined_state',lambda r:r.update(judgement_status='undetermined')),
                     ('missing_judgement_state',lambda r:r.pop('judgement_status'))]
    for name,change in invalid_machine:
        data=copy.deepcopy(full);change(data[1][0]);must_fail(name,lambda data=data:choose(data))
    data=copy.deepcopy(full);extra=copy.deepcopy(data[1][0]);extra['id']='outside-pool';extra['labels']['F']=True;data[1].append(extra)
    must_fail('invalid_prediction_outside_candidate_pool',lambda:choose(data))
    valid_pending=fixture(u=1);valid_pending[1][0]['input_assessment_status']='text_problem'
    require(choose(valid_pending)['machine_pending_ids']==valid_pending[0],'Authorized text-problem pending not retained')
    checks['real_frozen_machine_parser_integration_all_five_dimensions']='passed'
    source={'unit_text':'合成单元','original_file_stem':'synthetic-only','pages':[1],
            'verified_supplemental_context':{'contexts':[{'text':'价格'}],'source':'安全来源字样'},
            'content_role':'研发','content_role_basis':'研发',
            'candidate_bucket':'dictionary_positive','wide_search_dimensions':['S'],
            'dictionary_positive_dimensions':['S'],'input_assessment':{'status':'not_assessed','labels':{'S':1}}}
    fields=['verified_supplemental_context','content_role','content_role_basis']
    require(broad_hits(source,fields,list(DIMS))==['Ec'],'Broad search mixed text with metadata')
    require(content({'contexts':{'branch':{'text':'价格'}}})==['价格'],'Nested context container text lost')
    blind=make_blind_record(source,'R200-0001',fields,projection['clean_context'],projection['clean_assessment'])
    forbidden={'candidate_bucket','wide_search_dimensions','dictionary_positive_dimensions','labels','H600_positive_counts','targets'}
    def keys(value):
        if isinstance(value,dict):return set(value)|set().union(*(keys(v) for v in value.values()))
        if isinstance(value,list):return set().union(*(keys(v) for v in value))
        return set()
    require(not keys(blind)&forbidden and blind['text']==source['unit_text'],'Blind packet leaks selection provenance or changes text')
    checks['broad_search_text_only_and_frozen_blind_projection']='passed'
    for name in ('R200','.R200.partial','R200-未触发说明.json'):
        must_fail('prior_'+name,lambda name=name:guard_prior_attempt({name:True}))
    guard_prior_attempt({'R200':False,'.R200.partial':False,'R200-未触发说明.json':False})
    checks['existing_draw_partial_and_nontrigger_report_block_redraw']='passed'
    return {'status':'passed_synthetic_QA_only','code_sha256':sha(Path(__file__)),
            'registered_rule_sha256':sha(OUT/'R200-预定挑战集规则.md'),
            'helper_program_sha256':{'holdout_results':bridge_sha,'sample_holdout':projection_sha},
            'real_policy_text_read':False,'real_predictions_read':False,'real_A_C_labels_read':False,
            'real_freeze_manifest_read':False,'real_draw_executed':False,'seed':SEED,
            'checks':checks,'rejected_synthetic_cases':rejected,
            'scope':'R200 describes itself only; no U* design weights, pooled H600 estimates, new population CI or generated reference truth.',
            'limitations':['Synthetic selection/projection checks do not verify actual remaining-pool contents or reference quality.',
                           'Production byte/hash checks and filesystem publication are not exercised against real study files.']}

if __name__=='__main__':main()
