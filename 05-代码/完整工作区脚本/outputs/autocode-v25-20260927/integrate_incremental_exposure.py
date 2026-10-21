"""Add 141 registered historical exposures to the frozen 477-unit audit.

No labels or predictions are inspected; policy strings are compared in process
and never printed or placed in the report. No sampling is performed.
"""
from collections import Counter,defaultdict
from pathlib import Path
import hashlib,json,re,unicodedata

ROOT=Path('/PROJECT_ROOT')
OUT=ROOT/'outputs/autocode-v25-20260927'
OLD=ROOT/'outputs/validation-expansion-20260926'
FRAME=OUT/'方法与新验证框评估.json'
REGISTER=OUT/'历史LLM核查新增暴露登记.json'
POLICY_FIELDS={'text','caption','headers','row_cells','definition','title','note'}
def sha(raw):return hashlib.sha256(raw).hexdigest()
def shatext(s):return sha(s.encode())
def norm(s):return re.sub(r'\s+','',unicodedata.normalize('NFKC',s)).strip('。.!！?？;；')
def json_pointer(obj,pointer):
    for key in pointer.strip('/').split('/'):
        obj=obj[int(key)] if isinstance(obj,list) else obj[key.replace('~1','/').replace('~0','~')]
    return obj
def relation(target,exposed):
    if not target or not exposed:return None
    if target==exposed:return 'normalized_equal'
    if len(target)>=20 and target in exposed:return 'whole_target_min20_contained_in_exposure'
    if len(exposed)>=20 and exposed in target:return 'exposure_min20_contained_in_target'
    return None
def grams(s):return {s[j:j+5] for j in range(len(s)-4)}

def audit():
    tracked={};cache={}
    def read(path,expected=None):
        path=Path(path).resolve();raw=path.read_bytes();h=sha(raw)
        assert expected is None or h==expected,'Source hash mismatch'
        assert str(path) not in tracked or tracked[str(path)]==h,'Changing input'
        tracked[str(path)]=h
        return raw
    def load(path,expected=None):
        path=str(Path(path).resolve())
        if path not in cache:cache[path]=json.loads(read(path,expected))
        elif expected:assert tracked[path]==expected
        return cache[path]
    previous=load(FRAME);register=load(REGISTER)
    candidates=set(previous['residual_ids'])
    assert len(candidates)==477
    assert shatext('\n'.join(sorted(candidates)))==previous['residual_id_list_sha256']
    vf=load(OLD/'V600-最终冻结清单.json')
    corpus_meta=vf['files']['corpus']
    raw=read(corpus_meta['path'],corpus_meta['sha256'])
    units={r['review_id']:r for r in (json.loads(l) for l in raw.splitlines()) if r['count_as_analysis_unit'] is True}
    assert len(units)==4924 and candidates<=units.keys()
    effective=lambda r:r.get('unit_source_sha256') or r['source_sha256']
    for i in candidates:
        md=previous['residual_metadata'][i]
        assert shatext(units[i]['unit_text'])==md['unit_text_sha256']
        assert effective(units[i])==md['effective_source_sha256']
    registry_hashes={m['path']:m['sha256'] for m in register['source_hashes']}

    # Register exact old sentences plus each actually displayed preview/hidden
    # field; recombination is allowed ONLY after proving these fields form the
    # same documented transformation of this one source sentence.
    bodies=defaultdict(list);exposure_by_id={};display_transform_checks=[]
    def addbody(text,origin):
        n=norm(text)
        if n:bodies[n].append({**origin,'raw_text_sha256':shatext(text)})
    for e in register['entries']:
        path=e['original_source'];obj=load(path,registry_hashes.get(path))
        src=json_pointer(obj,e['original_json_pointer'])
        assert src['id']==e['historical_sentence_id']
        sentence=src['sent']
        assert shatext(sentence)==e['original_text_sha256']
        assert src['file']==e['source_filename']
        sid=e['historical_sentence_id'];stem=Path(src['file']).stem
        origin={'historical_sentence_id':sid,'old_source_entry':stem,'exposure_status':e['status'],
                'original_source':path,'original_json_pointer':e['original_json_pointer']}
        addbody(sentence,{**origin,'field':'original_sentence_conservative_registration'})
        exposure_by_id[sid]={'old_source_entry':stem,'original_text_sha256':e['original_text_sha256'],
                            'registered_status':e['status']}
        if e.get('display_fields')==['preview','hidden']:
            displayed=json_pointer(load(e['display_source'],registry_hashes.get(e['display_source'])),e['display_json_pointer'])
            assert displayed['id']==sid
            assert shatext(displayed['preview'])==e['preview_sha256']
            assert shatext(displayed['hidden'])==e['hidden_sha256']
            transformed=re.sub(r'\s+','',sentence)
            transformed=re.sub(r'(?<=[一-鿿])\d{1,3}(?=[一-鿿])','',transformed)
            assert transformed==displayed['preview']+displayed['hidden'],'Display transform mismatch'
            display_transform_checks.append(sid)
            for field in ['preview','hidden']:
                addbody(displayed[field],{**origin,'field':field,'display_source':e['display_source'],
                                         'display_json_pointer':e['display_json_pointer']+'/'+field})
            addbody(transformed,{**origin,'field':'verified_same_sentence_preview_plus_hidden'})
    assert len(exposure_by_id)==141 and len(display_transform_checks)==139

    # Extract only the same displayed policy fields as the inherited audit.
    # No interpretation of dimensions and no prediction/reference files.
    def scan_contexts(x,src,path='contexts',paragraph=None):
        result=[];tokens=set();refs=set()
        if isinstance(x,dict):
            src=x.get('source_sha256',src)
            paragraph=x.get('paragraph_id',paragraph)
            if x.get('paragraph_id'):tokens.add((src,x['paragraph_id']))
            if x.get('source_unit_id'):refs.add((src,x['source_unit_id']))
            refs|={(src,v) for v in x.get('separately_existing_unit_ids',[])}
            for key,val in x.items():
                if key in POLICY_FIELDS:
                    def strings(v,fp):
                        if isinstance(v,str):yield v,fp
                        elif isinstance(v,list):
                            for j,z in enumerate(v):yield from strings(z,fp+f'[{j}]')
                    for text,fp in strings(val,path+'.'+key):
                        if norm(text):result.append({'normalized':norm(text),'field':fp,'raw_sha256':shatext(text),
                                                    'source_sha256':src,'paragraph_id':paragraph})
                if isinstance(val,(dict,list)):
                    b,t,r=scan_contexts(val,src,path+'.'+key,paragraph);result+=b;tokens|=t;refs|=r
        elif isinstance(x,list):
            for j,val in enumerate(x):
                b,t,r=scan_contexts(val,src,path+f'[{j}]',paragraph);result+=b;tokens|=t;refs|=r
        return result,tokens,refs
    normal={i:norm(r['unit_text']) for i,r in units.items()}
    contexts={};tokens={};refs={}
    for i,r in units.items():
        contexts[i],tokens[i],refs[i]=scan_contexts({k:r[k] for k in vf['context_fields'] if k in r},effective(r))

    # Direct same-source mapping creates explicit source+paragraph anchors.
    # A document-name match alone never excludes another paragraph.
    shown_paragraphs=defaultdict(list);direct_units=defaultdict(list);old_mapping=defaultdict(list)
    body_items=list(bodies.items())
    for i,r in units.items():
        for exposed,origins in body_items:
            unit_rel=relation(normal[i],exposed)
            same_origins=[o for o in origins if o['old_source_entry']==r['original_file_stem']]
            if unit_rel in {'normalized_equal','whole_target_min20_contained_in_exposure'}:
                direct_units[i].append({'relation':unit_rel,'exposure_normalized_sha256':shatext(exposed),'origins':origins})
            if same_origins and unit_rel:
                for o in same_origins:
                    old_mapping[o['historical_sentence_id']].append({'review_id':i,'location':'unit_text','relation':unit_rel,
                                                                   'target_normalized_sha256':shatext(normal[i])})
            if not same_origins:continue
            for c in contexts[i]:
                rel=relation(c['normalized'],exposed)
                if not rel:continue
                for o in same_origins:
                    old_mapping[o['historical_sentence_id']].append({'review_id':i,'location':c['field'],'relation':rel,
                                                                   'target_normalized_sha256':shatext(c['normalized'])})
                if c['paragraph_id']:
                    token=(c['source_sha256'],c['paragraph_id'])
                    shown_paragraphs[token].append({'mapping_review_id':i,'field':c['field'],'relation':rel,
                                                   'exposure_normalized_sha256':shatext(exposed),'origins':same_origins})

    reasons=defaultdict(list)
    for i in sorted(candidates):
        for exposed,origins in body_items:
            rel=relation(normal[i],exposed)
            if rel:
                reasons[i].append({'reason':'new_exposure_overlaps_candidate_unit','relation':rel,
                                   'candidate_unit_text_sha256':shatext(units[i]['unit_text']),
                                   'exposure_normalized_sha256':shatext(exposed),'origins':origins})
            for c in contexts[i]:
                rel=relation(c['normalized'],exposed)
                if rel:
                    reasons[i].append({'reason':'new_exposure_overlaps_candidate_attached_context','relation':rel,
                                       'field':c['field'],'context_raw_sha256':c['raw_sha256'],
                                       'context_source_sha256':c['source_sha256'],'paragraph_id':c['paragraph_id'],
                                       'exposure_normalized_sha256':shatext(exposed),'origins':origins})
        shared=sorted(tokens[i]&shown_paragraphs.keys())
        if shared:
            reasons[i].append({'reason':'shares_explicit_source_paragraph_mapped_from_new_exposure',
                               'groups':[{'source_sha256':s,'paragraph_id':p,'mappings':shown_paragraphs[(s,p)]} for s,p in shared]})
        matching_refs=[(s,u) for s,u in refs[i] if any(effective(units[j])==s and units[j]['unit_id']==u for j in direct_units)]
        if matching_refs:
            reasons[i].append({'reason':'explicit_context_reference_to_directly_exposed_unit',
                               'references':[{'source_sha256':s,'unit_id':u} for s,u in sorted(matching_refs)]})

    # One-hop legacy near rule applied to both candidate body and attached
    # policy contexts. Near/group hits are never promoted to further seeds.
    near_seeds={b:list(os) for b,os in bodies.items()}
    for i,matches in direct_units.items():
        near_seeds.setdefault(normal[i],[]).append({'field':'directly_exposure_contained_current_unit',
                                                  'review_id':i,'direct_matches':matches})
    targets={};posting=defaultdict(set)
    for i in sorted(candidates):
        ts=[{'normalized':normal[i],'field':'unit_text','raw_sha256':shatext(units[i]['unit_text']),
             'source_sha256':effective(units[i]),'paragraph_id':None}]+contexts[i]
        for n,c in enumerate(ts):
            if len(c['normalized'])<30:continue
            target_id=(i,n);g=grams(c['normalized']);targets[target_id]=(c,g)
            for v in g:posting[v].add(target_id)
    for b,origins in near_seeds.items():
        if len(b)<30:continue
        bg=grams(b)
        for (i,n),inter in Counter(key for v in bg for key in posting.get(v,())).items():
            c,g=targets[(i,n)];length_ratio=min(len(b),len(c['normalized']))/max(len(b),len(c['normalized']))
            dice=2*inter/(len(bg)+len(g))
            if b!=c['normalized'] and length_ratio>=.75 and dice>=.85:
                reasons[i].append({'reason':'new_exposure_or_direct_visible_unit_near_duplicate',
                                   'target_field':c['field'],'target_raw_sha256':c['raw_sha256'],
                                   'source_sha256':c['source_sha256'],'paragraph_id':c['paragraph_id'],
                                   'seed_normalized_sha256':shatext(b),'length_ratio':length_ratio,'dice':dice,
                                   'origins':origins})

    # Deterministic de-duplication preserves non-exclusive substantive reasons.
    reasons={i:[json.loads(s) for s in sorted({json.dumps(v,ensure_ascii=False,sort_keys=True) for v in rs})]
             for i,rs in sorted(reasons.items()) if rs}
    residual=candidates-reasons.keys()
    counts=Counter(k for rs in reasons.values() for k in {r['reason'] for r in rs})
    relation_counts=Counter(r['relation'] for rs in reasons.values() for r in rs if 'relation' in r)
    mapped=set(old_mapping)
    mapped_summaries={}
    for sid in sorted(exposure_by_id):
        matches=[json.loads(s) for s in sorted({json.dumps(m,ensure_ascii=False,sort_keys=True) for m in old_mapping[sid]})]
        mapped_summaries[str(sid)]={**exposure_by_id[sid],'same_source_textual_mapping_found':bool(matches),
                                   'mapped_current_ids':sorted({m['review_id'] for m in matches}),'mappings':matches}
    # Subset the original groups; additions can remove group members, never
    # increase the prior eligible set. Recompute components to avoid implying
    # connectivity through a now-removed bridging unit.
    parent={i:i for i in residual}
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    def union(a,b):
        a,b=find(a),find(b)
        if a!=b:parent[max(a,b)]=min(a,b)
    owners={}
    for i in sorted(residual):
        for token in [('paragraph',*t) for t in tokens[i]]+[('normalized_text',shatext(normal[i]))]:
            if token in owners:union(i,owners[token])
            else:owners[token]=i
    comps=defaultdict(list)
    for i in sorted(residual):comps[find(i)].append(i)
    groups=[{'group_id':shatext('\n'.join(ids)),'n':len(ids),'ids':ids} for ids in sorted(comps.values())]
    def describe(ids):
        md=previous['residual_metadata']
        return {'n':len(ids),'department_counts':dict(sorted(Counter(md[i]['group'] for i in ids).items())),
                'department_year_counts':dict(sorted(Counter(md[i]['group']+'|'+md[i]['year'] for i in ids).items())),
                'document_entries':len({md[i]['source_entry'] for i in ids}),
                'effective_sources':len({md[i]['effective_source_sha256'] for i in ids})}
    report={
      'status':'incremental_registered_exposure_audit_not_sampled_not_final_frozen_validation',
      'audit_version':'v25-141-historical-exposure-addendum-1','date':'2026-09-27',
      'prior_audit_path':str(FRAME),'prior_audit_sha256':tracked[str(FRAME.resolve())],
      'prior_477_not_overwritten':True,'input_exposure_register':str(REGISTER),
      'registered_old_sentence_n':141,'confirmed_displayed_n':register['counts']['confirmed_displayed'],
      'conservatively_possible_display_n':register['counts']['possible_display_registered_conservatively'],
      'normalized_exposure_bodies':len(bodies),'display_transform_checks_n':len(display_transform_checks),
      'original_candidate_n':len(candidates),'original_candidate_id_list_sha256':previous['residual_id_list_sha256'],
      'additional_excluded_n':len(reasons),'additional_excluded_ids':sorted(reasons),
      'nonexclusive_exclusion_reason_counts':dict(sorted(counts.items())),
      'text_match_relation_occurrences':dict(sorted(relation_counts.items())),
      'additional_exclusions':reasons,'residual':describe(residual),
      'residual_ids':sorted(residual),'residual_id_list_sha256':shatext('\n'.join(sorted(residual))),
      'residual_metadata':{i:previous['residual_metadata'][i] for i in sorted(residual)},
      'residual_context_groups':groups,'residual_context_group_count':len(groups),
      'largest_residual_context_group':max((g['n'] for g in groups),default=0),
      'old_sentence_mapping_n':len(mapped),'old_sentence_without_exact_or_containment_same_source_mapping_ids':sorted(set(exposure_by_id)-mapped),
      'historical_sentence_mappings':mapped_summaries,
      'same_source_mapped_paragraph_groups_n':len(shown_paragraphs),'directly_visible_current_unit_seed_n':len(direct_units),
      'rules':{
        'normalization':previous['rules']['normalization'],
        'exposure_fields':'For all 141 conservatively registered entries, original sentence; for 139 truncated audit entries also preview, hidden, and recombination only after exact original documented-transform check.',
        'text_overlap':'Equality; entire target of >=20 normalized chars in exposed body; or entire exposed fragment of >=20 normalized chars in target. Candidate unit and every supplied policy context field are checked separately. No unrelated fields concatenated.',
        'source_paragraph':'Same original source filename stem plus actual text equality/full containment mapping to current supplied context carrying paragraph_id; anchor is exact effective/context source_sha256+paragraph_id. Document-name match alone insufficient.',
        'near':previous['rules']['near'],
        'near_extension_to_context':'Same fixed thresholds apply to attached policy context bodies as well as target unit. Seeds are registered display/original bodies and complete current unit bodies directly contained in them; no recursive propagation from near/group matches.',
        'unmatched':'Unmapped historical IDs remain explicitly listed. Source/page-level blanket removal is not silently substituted for unit/paragraph rules.',
        'labels':'No AI/reference/prediction files loaded; historical source may contain irrelevant columns, but only id/sent/file were accessed for this audit.'},
      'limitations':[
        'This is closure against a conservative known exposure register, not a guarantee all historical exposure has been inventoried.',
        'The 117 possibly displayed old IDs were deliberately treated as exposed because the earlier tool output was truncated; this can remove more units than a perfect display log would.',
        'Old OCR text, line-number deletion, punctuation, splitting/merging, source revisions and absent context IDs can prevent exact/full containment mapping. Unmapped IDs are listed and must not be called proved non-overlap.',
        'One-hop 5-gram Dice thresholds are legacy deterministic heuristics, not proof against paraphrase or semantic leakage.',
        'Only exact same-source paragraph anchors with textual support propagate; page/document blanket exclusions are not main-rule substitutes. Remaining units may still be within documents already seen.',
        'Attached context overlap is conservatively excluded even when it might be background rather than decisive for a label; this audit does not interpret labels.',
        'No sample or reference labels have been produced. Any later additional exposure requires another additive audit before freezing or sampling.'],
      'input_sha256':dict(sorted(tracked.items())),
      'verification':{'prior_frame_unchanged':True,'remaining_plus_excluded_equals_original':residual|reasons.keys()==candidates,
                      'remaining_disjoint_excluded':not(residual&reasons.keys()),'text_or_context_displayed_to_model':False,
                      'sampling_performed':False,'reference_labels_read':False,'predictions_read':False,
                      'all_input_hashes_rechecked':True},
    }
    assert report['verification']['remaining_plus_excluded_equals_original']
    assert not residual&reasons.keys()
    assert all(sha(Path(p).read_bytes())==h for p,h in tracked.items())
    return report

def save(report):
    path=Path(__file__).resolve();report['reproduction_python']=str(path)
    report['reproduction_python_sha256']=sha(path.read_bytes())
    (OUT/'新验证框-新增暴露接入.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    lines=['# 新验证框：141条新增暴露接入','',
           '本次只执行机械暴露映射，不抽样、不读取参照或预测标签、不向模型展示候选正文或语境。原477条审核保持原文件不变；本报告为追加审核。','',
           f'**原候选477条，新增排除{report["additional_excluded_n"]}条，剩余{report["residual"]["n"]}条。** 剩余清单仅表示对已登记暴露按既定规则闭合，不证明历史上从未见过其语义内容，也不是已冻结验证样本。','',
           '## 输入与规则','',
           f'- 原审核：[方法与新验证框评估]({FRAME})；SHA256 `{report["prior_audit_sha256"]}`。',
           f'- 新暴露：[141条登记]({REGISTER})：24条可确认显示、117条因旧工具输出截断保守视为暴露。',
           '- 与原审核相同的NFKC、去所有空白、端点句末标点规范化。比较原句，以及139条截断审计的preview、hidden与经核验可拼回同一句的转换后文本。',
           '- 比较候选正文和实际附带政策语境字段：相等；目标完整片段≥20字包含于暴露文本；暴露完整片段≥20字包含于目标。反向包含另留理由，不把已显示片段所在的大单元当未暴露。',
           '- 同源段落要求原文件stem相同、原文能明确映射到带paragraph_id的实际语境；再按source SHA+paragraph_id排除共享者。不是按同文件名整篇排除。',
           '- 明显近重复沿用两段均≥30字、长度比≥0.75、字符5-gram集合Dice≥0.85；仅从已登记正文/片段与直接完整包含的现行单元一跳比较，近重复或段落排除项不递归充当种子。','',
           '## 排除结果','',
           '| 非互斥排除理由 | 候选条数 |','|---|---:|']
    lines += [f'| {k} | {v} |' for k,v in report['nonexclusive_exclusion_reason_counts'].items()]
    lines += ['',f'141个旧ID中，{report["old_sentence_mapping_n"]}个在同源现行正文/语境找到相等或完整包含映射；未找到这种明确映射的旧ID有{len(report["old_sentence_without_exact_or_containment_same_source_mapping_ids"])}个，已在JSON逐个保留。未映射不等于证明与剩余框不重叠。', '',
              f'剩余分部门计数：`{json.dumps(report["residual"]["department_counts"],ensure_ascii=False)}`。剩余上下文连接组{report["residual_context_group_count"]}组，最大组{report["largest_residual_context_group"]}条。', '',
              f'剩余ID清单SHA256：`{report["residual_id_list_sha256"]}`。完整剩余ID、非互斥逐条理由、源文件哈希、历史ID映射、语境字段及匹配指标见[结构化结果]({OUT/"新验证框-新增暴露接入.json"})，不包含政策原文。','',
              '## 可复跑与残余限制','',
              f'运行：`python3 "{path}"`。脚本SHA256 `{report["reproduction_python_sha256"]}`。所有输入按登记哈希核验；原477审核未覆写。','',
              '旧OCR断词、插入行号、分拆合并、来源修订和缺少段落ID可能使真实语义重叠无法精确映射；固定Dice阈值也不是语义泄漏保证。剩余仍是同语料范围内的单元及语境隔离候选，不是来源层面的外部验证。117条保守暴露可能使排除偏多，但不以扩大验证框为由恢复。后续另有暴露时继续追加登记，冻结规则及输入前不抽样。']
    (OUT/'新验证框-新增暴露接入.md').write_text('\n'.join(lines)+'\n')

if __name__=='__main__':
    result=audit();save(result)
    print(json.dumps({k:result[k] for k in ['original_candidate_n','additional_excluded_n','residual','nonexclusive_exclusion_reason_counts','old_sentence_mapping_n','residual_context_group_count','residual_id_list_sha256']},ensure_ascii=False))
