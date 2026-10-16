from pathlib import Path
import collections, copy, hashlib, html, json, shutil

OUT = Path(__file__).resolve().parent.parent
BASE = OUT.parent/'新定义概率180复核草稿01'
W = OUT.parents[1]
SOURCE = W/'LLM编码/统一判据编码准备/共用纯来源材料02/source_only_with_scope02.jsonl'
PROVENANCE = SOURCE.with_name('provenance_with_scope02.jsonl')
MANUAL = W/'定义溯源核查/共同判据定稿/共用编码手册.md'
STATUS = '待必要来源补全核验'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
tsha = lambda s: hashlib.sha256(s.encode()).hexdigest()
def dump(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
def remap(value, mapping):
    if isinstance(value, dict): return {k:remap(v,mapping) for k,v in value.items()}
    if isinstance(value, list): return [remap(v,mapping) for v in value]
    return mapping.get(value,value) if isinstance(value,str) else value
def links(binding):
    result=[]
    for role, sk in [('source_path','source_sha256'),('candidate_path','candidate_sha256')]:
        if binding.get(role):
            p=binding[role]
            result.append({'role':role,'path':p,'declared_sha256':binding.get(sk),
                           'identity':'当前材料声明来源；待必要来源补全核验','uri':Path(p).as_uri()})
    return result

assert sha(SOURCE)=='7eb8323f81bbed844cc19d9859e1c5faf432f18094201130e91d91e5743ecfa1'
assert sha(MANUAL)=='5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c'
mapping=json.loads((BASE/'admin/PRIVATE_mapping_and_design.json').read_text())
ids={r['design_id'] for r in mapping['coders']['A']}
source={r['id']:r for r in map(json.loads,SOURCE.read_text().splitlines()) if r['id'] in ids}
provenance={r['id']:r for r in map(json.loads,PROVENANCE.read_text().splitlines()) if r['id'] in ids}
assert len(ids)==180 and set(source)==set(provenance)==ids
assert collections.Counter(r['group'] for r in mapping['original_probability_design_rows'])=={'NMPA':60,'NHSA':60,'NHC':60}
bindings={'manual':{'path':str(MANUAL),'sha256':sha(MANUAL)},'source_only':{'path':str(SOURCE),'sha256':sha(SOURCE)},'provenance':{'path':str(PROVENANCE),'sha256':sha(PROVENANCE)}}
payload={}; changes=[]
for coder in ['A','B']:
    folder=OUT/coder;folder.mkdir(parents=True,exist_ok=True)
    old_pack=json.loads((BASE/coder/'完整材料.json').read_text())
    old_by={u['anonymous_id']:u for u in old_pack['units']}
    units=[]
    for record in mapping['coders'][coder]:
        rid=record['design_id'];anon=record['anonymous_id'];raw=source[rid];prov=provenance[rid]
        old=old_by[anon]
        node_map=copy.deepcopy(record['node_id_map'])
        next_id=max([int(x.rsplit('C',1)[1]) for x in node_map.values()] or [0])+1
        for node in raw['contexts']:
            if node['context_id'] not in node_map:
                node_map[node['context_id']]=f'{anon}-C{next_id:03d}';next_id+=1
        graph=remap(copy.deepcopy(raw),{**node_map,rid:anon})
        # Every current policy text occurrence comes from the current source-only graph.
        occurrences=[]
        policy_by=collections.defaultdict(list)
        for leaf in prov['policy_leaves']:policy_by[leaf['context_id']].append(leaf)
        added={f['context_id']:f for f in prov.get('added_component_fragments',[])}
        for node_id,field,text in [(None,'text',raw['text'])]+[(n['context_id'],'text',n['text']) for n in raw['contexts'] if 'text' in n]:
            leaf=next((x for x in policy_by[node_id] if x['output_field']==field and x['text_sha256']==tsha(text)),None)
            fragment=added.get(node_id)
            if leaf:binding=copy.deepcopy(leaf['source_binding'])
            elif fragment:
                binding={'source_path':fragment['source']['path'],'source_sha256':fragment['source']['sha256'],
                         'candidate_path':fragment.get('candidate',{}).get('path'),'candidate_sha256':fragment.get('candidate',{}).get('sha256')}
            else:binding={}
            occurrences.append({'occurrence_id':f'{anon}-T{len(occurrences)+1:03d}',
                'node_id':node_map.get(node_id),'field':field,'text':text,'text_sha256':tsha(text),
                'source_links':links(binding),'source_binding':binding,'actual_source_position_verified':False})
        material_notes=[]
        for kind in ['omitted_optional_pointers','nonpolicy_boundary_pointers']:
            for value in prov.get(kind,[]):
                material_notes.append({'issue_id':f'{anon}-Q{len(material_notes)+1:02d}',
                    'category':kind,'code':json.dumps(value,ensure_ascii=False),'state':STATUS})
        units.append({'anonymous_id':anon,'source_only_view':graph,'text_occurrences':occurrences,
                      'unbound_declared_material':[], 'material_notes':material_notes,
                      'source_provenance':remap(copy.deepcopy(prov),{**node_map,rid:anon}),
                      'source_position_check_status':STATUS})
        if coder=='A':
            # Comparison is a material change list only, with no coding judgments.
            old_graph=old['source_only_view']
            if graph!=old_graph:
                changes.append({'original_id':rid,'anonymous_id':anon,
                    'current_text_changed':graph['text']!=old_graph['text'],
                    'old_context_n':len(old_graph['contexts']),'current_context_n':len(graph['contexts']),
                    'contexts_or_source_structure_changed':graph['contexts']!=old_graph['contexts']})
        record['node_id_map']=node_map
        record['current_text_sha256']=tsha(raw['text'])
        record.pop('leaf_lineage',None)
    package={'package':coder,'status':STATUS,'identity':'AI代理同步材料与空白表格；既有真人事后审定事实保留；新手册下实际人工复核情况待用户确认',
             'manual_sha256':bindings['manual']['sha256'],'unit_count':180,'dimensions':['S','E','Ec','I','F'],
             'source_material_version':'共用纯来源材料02/source_only_with_scope02.jsonl','source_material_sha256':bindings['source_only']['sha256'],
             'units':units}
    dump(folder/'完整材料.json',package)
    shutil.copyfile(MANUAL,folder/'共用编码手册.md')
    instruction=(BASE/coder/'填写说明.md').read_text()
    instruction=instruction.replace('草稿：待材料管理员完成来源位置与版式核查后再发。现有真人裁定记录保持；本包是新定义下复核准备，不是已经完成的新独立盲评。',
        '同步02：待必要来源补全核验。既有真人事后审定事实保留；人工是否已按新手册复核尚待用户回答。本包只同步材料并提供空白填写栏。')
    (folder/'填写说明.md').write_text(instruction,encoding='utf-8')
    esc=lambda v:html.escape(str(v))
    parts=['<!doctype html><meta charset="utf-8"><title>新定义复核同步02 '+coder+'</title><style>body{font:17px/1.65 system-ui;max-width:1100px;margin:32px auto;padding:0 24px;color:#18202a}section{border-top:2px solid #b4c4d1;margin:44px 0;padding-top:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 system-ui;background:#f4f6f8;padding:14px}a{color:#1859a0}li{overflow-wrap:anywhere}.warn{background:#fff2cc;padding:14px}.context{margin:18px 0;padding:12px;border-left:3px solid #ccd5dd}h1{font-size:26px}h2{font-size:23px}h3{font-size:18px}</style><h1>新定义复核同步02 '+coder+'</h1><p class="warn">待必要来源补全核验。所有标签、理由及引文填写栏保持空白。既有真人事后审定事实保留；新手册下实际人工复核情况待用户确认。</p><p><a href="共用编码手册.md">固定手册</a> · <a href="填写说明.md">填写说明</a></p>']
    for unit in units:
        a=unit['anonymous_id'];g=unit['source_only_view'];occ={o['node_id']:o for o in unit['text_occurrences']}
        def links_html(o):
            return '<ul>'+''.join(f'<li>{esc(v["role"])} · <a href="{esc(v["uri"])}">{esc(v["path"])}</a> · {esc(v["identity"])}</li>' for v in o.get('source_links',[]))+'</ul>'
        parts.append(f'<section id="{a}"><h2>{a}</h2><h3>当前原文</h3><pre>{esc(g["text"])}</pre><p>原页码：{esc(g.get("pages",[]))}</p>'+links_html(occ.get(None,{})))
        for node in g['contexts']:
            parts.append(f'<div class="context" id="{esc(node["context_id"])}"><h3>{esc(node["context_id"])} · {esc(node["kind"])}</h3>')
            if 'text' in node:parts.append('<pre>'+esc(node['text'])+'</pre>')
            parts.append('<details open><summary>原结构/顺序/父子/表格定位</summary><pre>'+esc(json.dumps({k:v for k,v in node.items() if k!='text'},ensure_ascii=False,indent=2))+'</pre></details>'+links_html(occ.get(node['context_id'],{}))+'</div>')
        parts.append('<details><summary>当前来源结构</summary><pre>'+esc(json.dumps(unit['source_provenance'],ensure_ascii=False,indent=2))+'</pre></details></section>')
    (folder/'完整材料.html').write_text('\n'.join(parts),encoding='utf-8')
    payload[coder]=package
mapping['input_bindings_sync02']=bindings
dump(OUT/'admin/PRIVATE_mapping_and_design.json',mapping)
dump(OUT/'admin/builder_payload.json',{'manual':MANUAL.read_text(),'manual_sha256':bindings['manual']['sha256'],'packages':payload})
special={q:any(rid.endswith(q) for rid in ids) for q in ['00064','00929','01258']}
manifest={'status':STATUS,'sample_n':180,'group_counts':{'NMPA':60,'NHSA':60,'NHC':60},'challenge_n':0,
          'order_and_anonymous_ids':'沿用草稿01；不重抽样、不扩样本','bindings':bindings,'special_sample_membership':special,
          'blank_label_cells_per_coder':900,'blank_reason_and_quote_ranges':'判读!D6:G905',
          'human_review_status':'既有真人事后审定事实保留；新手册下实际人工复核情况待用户确认',
          'material_changes':changes}
dump(OUT/'delivery_manifest02.json',manifest)
lines=['# 材料同步02改变清单','',STATUS+'。','',
       '- 180条原概率样本及A/B原顺序、匿名编号沿用；每部门60条；不混入60条挑战样本。',
       '- 当前正文、全部语境节点及来源结构同步到共用纯来源材料02；固定手册字节保持不变。',
       '- A/B各900项标签以及理由、引文、语境说明栏全部留空；未复制旧标签。',
       '- 既有真人事后审定事实保留；是否已经按新手册人工复核尚待用户回答。',
       '- 样本不含00064、00929、01258；00064外引历史版本及00929可能待补直接条文不在本批180条中。',
       '- 01原目录保留。本次只同步材料，不形成新判定、模型结果或来源最终验证结论。','',
       '有正文/语境结构变化的单位：','']
for item in changes:lines.append(f'- {item["original_id"]}：正文'+('有变化' if item['current_text_changed'] else '相同')+f'；语境节点 {item["old_context_n"]} → {item["current_context_n"]}。')
(OUT/'材料同步02改变清单.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps({'directory':str(OUT),'sample_n':180,'special_sample_membership':special,'changed_material_units':len(changes),'source_sha256':sha(SOURCE)},ensure_ascii=False))
