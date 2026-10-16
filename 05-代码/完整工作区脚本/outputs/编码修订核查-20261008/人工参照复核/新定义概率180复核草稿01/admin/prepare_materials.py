from pathlib import Path
import collections, copy, hashlib, html, json, random, secrets, shutil

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
OUT = Path(__file__).resolve().parent.parent
PF = ROOT/'outputs/编码修订核查-20261008/LLM编码/统一判据编码准备'
DESIGN = ROOT/'outputs/coding-revision-20261007-r3/admin/confirmation_sampling_PRIVATE.json'
MANUAL = ROOT/'outputs/编码修订核查-20261008/定义溯源核查/共同判据定稿/共用编码手册.md'
FILES = {'design': DESIGN, 'manual': MANUAL,
 'rule': PF/'共同材料修订01/rule_inputs_shared_material_revision01.jsonl',
 'llm': PF/'共同材料修订01/effective_blind_inputs_material_revision01.jsonl',
 'view': PF/'纯来源候选投影01/source_only_candidates01.jsonl',
 'sidecar': PF/'纯来源候选投影01/provenance_sidecars01.jsonl'}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def tsha(s): return hashlib.sha256(s.encode()).hexdigest()
def dump(p,j):
 assert not p.exists(),p
 p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def pointer(obj, p):
 if not p:return obj
 for k in p.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~')
  obj=obj[int(k)] if isinstance(obj,list) else obj[k]
 return obj
def chunks(s): return [s[i:i+360] for i in range(0,len(s),360)] or ['']
def remap(x,m):
 if isinstance(x,dict):return {k:remap(v,m) for k,v in x.items()}
 if isinstance(x,list):return [remap(v,m) for v in x]
 return m.get(x,x) if isinstance(x,str) else x
def declared_paths(obj):
 found=[]
 if isinstance(obj,dict):
  for k,v in obj.items():
   if k in ['source','source_path','unit_source','candidate_file','candidate_path','image_path','png_path'] and isinstance(v,str) and v.startswith('/'):
    found.append({'role':k,'path':v})
   elif k=='locator' and isinstance(v,dict):
    found.extend({'role':'locator.'+q['role'],'path':q['path']} for q in declared_paths(v))
 return found

fhash={k:{'path':str(p),'sha256':sha(p)} for k,p in FILES.items()}
assert fhash['design']['sha256']=='728040e34f5c4ee67b3d24f78b2870965d4405713f05cf35af0a558b31169636'
assert fhash['manual']['sha256']=='5abee1f2448cd8a54403d2ac615fea8ebc3c162e78c907029322ec0e85a9556c'
design=json.loads(DESIGN.read_text())
sample=[copy.deepcopy(r) for r in design['sample'] if r['component']=='probability_canonical']
challenge_ids={r['original_id'] for r in design['sample'] if r['component']=='enriched_challenge'}
ids={r['original_id'] for r in sample};assert len(sample)==len(ids)==180 and len(challenge_ids)==60 and not ids&challenge_ids
assert collections.Counter(r['group'] for r in sample)=={'NMPA':60,'NHSA':60,'NHC':60}
data={}
for name in ['rule','llm','view','sidecar']:
 data[name]={r['id']:r for r in map(json.loads,FILES[name].read_text().splitlines()) if r['id'] in ids}
 assert set(data[name])==ids

seeds={x:secrets.randbits(128) for x in ['A','B']}
orders={}
for x in seeds:
 orders[x]=sorted(ids);random.Random(seeds[x]).shuffle(orders[x])
assert orders['A']!=orders['B']
mapping={'seeds':seeds,'random_generator':'Python random.Random(MT19937); independent fixed saved seeds; ordering only, not new sampling','input_bindings':fhash,'original_probability_design_rows':sample,'coders':{}}
selected_issues=[];leaf_inventory=[];changed_sha=[];source_link_checks={};payload={}
for coder in ['A','B']:
 package=OUT/coder;package.mkdir(exist_ok=True)
 mapping['coders'][coder]=[];units=[]
 for n,rid in enumerate(orders[coder],1):
  raw=data['rule'][rid];llm=data['llm'][rid];view=data['view'][rid];side=data['sidecar'][rid]
  assert view['text']==raw['input']['unit_text']==llm['text']
  assert raw['input']['llm_v29_shared_context']==llm['contexts']
  did=next(s for s in sample if s['original_id']==rid)
  if did['unit_text_sha256']!=tsha(view['text']) and coder=='A':changed_sha.append(rid)
  anon=f'{coder}{n:03d}'
  node_map={v['context_id']:f'{anon}-C{k:03d}' for k,v in enumerate(view['contexts'],1)}
  allmap={**node_map,rid:anon}
  graph=remap(copy.deepcopy(view),allmap)
  node_by_id={v['context_id']:v for v in graph['contexts']}
  occurrences=[];lineage=[]
  for k,leaf in enumerate(side['policy_leaves'],1):
   rawtext=pointer(llm,leaf['raw_pointer']);assert isinstance(rawtext,str)
   assert tsha(rawtext)==leaf['text_sha256'] and len(rawtext)==leaf['character_n']
   nid=node_map.get(leaf['context_id'])
   projected=graph['text'] if nid is None else node_by_id[nid][leaf['output_field']]
   assert projected==rawtext
   sb=leaf['source_binding'];links=[]
   if sb.get('source_path'):links.append({'role':'source_path','path':sb['source_path'],'declared_sha256':sb.get('source_sha256'),'identity':'声明来源身份完整，实际位置待核'})
   if sb.get('candidate_path'):links.append({'role':'candidate_path','path':sb['candidate_path'],'declared_sha256':sb.get('candidate_sha256'),'identity':'段落候选定位，非原文认证'})
   # Preserve local declarations explicitly; do not fill identity from a generic source.
   parent=pointer(llm,leaf['raw_pointer'].rsplit('/',1)[0])
   declared=declared_paths(parent)
   for issue in sb.get('identity_issues',[]):
    declared+=declared_paths(pointer(llm,issue['raw_pointer']))
   for link in declared:
    if not any(z['path']==link['path'] for z in links):links.append({**link,'declared_sha256':None,'identity':'原字段声明，身份有缺项，待核'})
   for link in links:
    link['uri']=Path(link['path']).as_uri();source_link_checks[link['path']]=Path(link['path']).is_file()
   occurrence_id=f'{anon}-T{k:03d}'
   occurrences.append({'occurrence_id':occurrence_id,'node_id':nid,'field':leaf['output_field'],'text':rawtext,'text_sha256':leaf['text_sha256'],'source_links':links,'actual_source_position_verified':False})
   lineage.append({'occurrence_id':occurrence_id,'original_context_id':leaf['context_id'],'raw_pointer':leaf['raw_pointer'],'text_sha256':leaf['text_sha256'],'source_binding':sb})
  notes=[];supplement=[]
  nonbinding=[z for z in side['issues'] if z['category']!='external_binding']
  for k,issue in enumerate(nonbinding,1):
   note={'issue_id':f'{anon}-Q{k:02d}','category':issue['category'],'code':issue['code'],'state':'待材料管理员核查，非编码答案'}
   notes.append(note)
   if coder=='A':selected_issues.append({'record_id':rid,**issue})
   if issue['code']=='ambiguous_boundary_requires_literal_binding':
    value=pointer(llm,issue['raw_pointer']);assert isinstance(value,str)
    supplement.append({'item_id':f'{anon}-U{len(supplement)+1:02d}','role':'原声明边界文字，未完成字面绑定','text':value,'text_sha256':tsha(value),'source_position_verified':False})
    lineage.append({'unbound_supplement_id':supplement[-1]['item_id'],'raw_pointer':issue['raw_pointer'],'text_sha256':tsha(value)})
   elif issue['category']=='candidate_view':
    value=pointer(llm,issue['raw_pointer'])
    # Known selected gaps contain no omitted policy prose; never promote opinions.
    assert value is None or value==[] or (isinstance(value,dict) and set(value)=={'unit_id','candidate_sha256'}),(rid,issue['raw_pointer'])
  units.append({'anonymous_id':anon,'source_only_view':graph,'text_occurrences':occurrences,'unbound_declared_material':supplement,'material_notes':notes,'source_position_check_status':'待root实际源位置核查；本包不作认证结论'})
  mapping['coders'][coder].append({'anonymous_id':anon,'design_id':rid,'current_RECODE_id':raw['id'],'original_source_id':raw['original_id'],'current_text_sha256':tsha(view['text']),'node_id_map':node_map,'leaf_lineage':lineage})
  if coder=='A':leaf_inventory.extend({'id':rid,**x} for x in lineage)
 reviewer={'package':coder,'status':'草稿：待材料及版式核查，尚未发出或填写','identity':'AI代理整理材料；不是已经完成的真人复核','manual_sha256':fhash['manual']['sha256'],'unit_count':180,'dimensions':['S','E','Ec','I','F'],'units':units}
 dump(package/'完整材料.json',reviewer)
 shutil.copyfile(MANUAL,package/'共用编码手册.md')
 instructions='''# 新定义复核填写说明\n\n草稿：待材料管理员完成来源位置与版式核查后再发。现有真人裁定记录保持；本包是新定义下复核准备，不是已经完成的新独立盲评。\n\n1. 使用本包所附固定手册，按匿名编号阅读完整当前原文与必要语境；每个单位分别填写 S、E、Ec、I、F 五维。\n2. 判定只填0或1；尚未完成或材料不足时留空。0只用于材料完整且未找到相应判据证据，不用于缺字、来源缺项或关键指代缺失。\n3. 每维填写理由及原文引文；如依赖语境，写明语境编号、对象/指代/条件关系。不要把标题或父段全部维度传给当前句。\n4. 发现材料问题请在“材料问题”单列记录，标明影响维度、位置和需要补充的内容；受影响判定留空等待同源补料。原文、原标签均不由填写者覆盖。\n5. 两位分别独立保存提交，不查看对方当前结果；既往接触旧答案的事实按实填写，不以本表隐藏答案推定过去未见。\n6. 在“填写说明”记录实际身份、经验、执行日期、手册使用、培训与讨论、历史答案接触。未知事实留空或由人员实填“未知”，不要按生成时间代填。\n7. 原文超出单格时按片段号顺序连续阅读；HTML/JSON保留完整文字和层次。源链接为实际声明路径，路径存在与SHA相符也不等于文字位置已认证。\n8. 完成后交回本人的xlsx；管理员封存首次提交和SHA，材料补充及后续裁定另存，不覆盖首次提交。\n'''
 (package/'填写说明.md').write_text(instructions,encoding='utf-8')
 esc=lambda v:html.escape(str(v))
 parts=['<!doctype html><meta charset="utf-8"><title>新定义复核材料 '+coder+'</title><style>body{font:17px/1.65 system-ui;max-width:1100px;margin:32px auto;padding:0 24px;color:#18202a}section{border-top:2px solid #b4c4d1;margin:44px 0;padding-top:24px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:15px/1.6 system-ui;background:#f4f6f8;padding:14px}a{color:#1859a0}li{overflow-wrap:anywhere}.warn{background:#fff2cc;padding:14px}.context{margin:18px 0;padding:12px;border-left:3px solid #ccd5dd}h1{font-size:26px}h2{font-size:23px}h3{font-size:18px}</style><h1>新定义复核材料 '+coder+'</h1><p class="warn">草稿 · 待材料与来源位置核查；未填写任何编码答案。必要语境用于解释当前对象、指代和条件，不自动传播维度。</p><p><a href="共用编码手册.md">固定手册</a> · <a href="填写说明.md">填写说明</a></p>']
 for u in units:
  a=u['anonymous_id'];g=u['source_only_view'];parts.append(f'<section id="{a}"><h2>{a}</h2><h3>当前原文</h3><pre>{esc(g["text"])}</pre><p>原页码：{esc(g.get("pages",[]))}</p>')
  occ={v['node_id']:v for v in u['text_occurrences']}
  def links_html(o):
   return '<ul>'+''.join(f'<li>{esc(v["role"])} · <a href="{esc(v["uri"])}">{esc(v["path"])}</a> · {esc(v["identity"])}</li>' for v in o.get('source_links',[]))+'</ul>'
  parts.append(links_html(occ.get(None,{})))
  for node in g['contexts']:
   parts.append(f'<div class="context" id="{esc(node["context_id"])}"><h3>{esc(node["context_id"])} · {esc(node["kind"])}</h3>')
   if 'text' in node:parts.append('<pre>'+esc(node['text'])+'</pre>')
   parts.append('<details open><summary>原结构/顺序/父子/表格定位</summary><pre>'+esc(json.dumps({k:v for k,v in node.items() if k!='text'},ensure_ascii=False,indent=2))+'</pre></details>')
   parts.append(links_html(occ.get(node['context_id'],{}))+'</div>')
  for z in u['unbound_declared_material']:parts.append(f'<div class="warn"><b>{esc(z["item_id"])}：{esc(z["role"])}</b><pre>{esc(z["text"])}</pre></div>')
  if u['material_notes']:parts.append('<p class="warn">材料接口待核事项（非判定）：'+esc(json.dumps(u['material_notes'],ensure_ascii=False))+'</p>')
  parts.append('</section>')
 (package/'完整材料.html').write_text('\n'.join(parts),encoding='utf-8')
 payload[coder]=reviewer
dump(OUT/'admin/PRIVATE_mapping_and_design.json',mapping)
dump(OUT/'admin/selected_nonbinding_issues.json',selected_issues)
dump(OUT/'admin/leaf_lineage_PRIVATE.json',leaf_inventory)
dump(OUT/'admin/builder_payload.json',{'manual':MANUAL.read_text(),'manual_sha256':fhash['manual']['sha256'],'packages':payload})
qa={'sample_n':180,'group_counts':dict(collections.Counter(r['group'] for r in sample)),'challenge_excluded_n':60,'input_join_all_exact':True,'old_design_current_text_sha_changed_ids':changed_sha,'current_material_used_without_old_text_reversion':True,'orders_differ':True,'order_overlap_same_position':sum(a==b for a,b in zip(orders['A'],orders['B'])),'projected_policy_leaf_occurrences':sum(len(u['text_occurrences']) for u in payload['A']['units']),'preserved_declared_unbound_boundary_n':sum(len(u['unbound_declared_material']) for u in payload['A']['units']),'nonbinding_issue_records':sum(bool(u['material_notes']) for u in payload['A']['units']),'source_links':source_link_checks,'missing_source_link_paths':[p for p,ok in source_link_checks.items() if not ok],'max_current_character_n':max(len(u['source_only_view']['text']) for u in payload['A']['units']),'all_input_files_unchanged':all(sha(FILES[k])==v['sha256'] for k,v in fhash.items()),'read_label_files':0,'actual_source_authentication_verified':False,'formal_human_packet_ready':False}
assert qa['all_input_files_unchanged']
dump(OUT/'admin/extraction_QA.json',qa)
print(json.dumps({k:v for k,v in qa.items() if k!='source_links'},ensure_ascii=False))
