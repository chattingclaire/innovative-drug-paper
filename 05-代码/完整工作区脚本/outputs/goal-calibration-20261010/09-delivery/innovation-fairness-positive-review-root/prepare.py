from pathlib import Path
import json,hashlib,html

HERE=Path(__file__).resolve().parent
GOAL=HERE.parents[1]
AI=GOAL.parent/'ai-audit800-20261010'
AUDIT=GOAL/'08-audits/ai800-disagreement-semantic-root'
RULE=GOAL/'06-coding/rule-full4481-v2-root/run4481-first'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,x):
 with (HERE/name).open('x',encoding='utf-8') as f:f.write(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def fmt(v):return '待定' if v is None or v=='未定' else v

reviews=json.loads((AUDIT/'joined-review.json').read_text())['rows']
for r in json.loads((AUDIT/'remaining-positive271-sol/reviews.json').read_text()):
 reviews.append({'source_id':r['source_id'],'dimension':r['dimension'],'review_value':r['review_value'],
   'assessment':r['assessment'],'reason':r['explanation'],'detailed_review_file':str(AUDIT/'remaining-positive271-sol/reviews.json'),
   'needs_human_review':r['needs_human_review']})
review={(r['source_id'],r['dimension']):r for r in reviews}
assert len(review)==68
ais={r['source_id']:r for r in map(json.loads,(AI/'AI原始判读-800条.jsonl').read_text().splitlines())}
rules={r['id']:r for r in map(json.loads,(RULE/'predictions.jsonl').read_text().splitlines())}
metadata=json.loads((AI/'checks/sample-metadata.json').read_text())['records']
years={r['unit_id']:r for r in map(json.loads,(GOAL/'07-statistics/annual-year-input-binding-sol/full4481-year-map.jsonl').read_text().splitlines())}
positive_ids={sid for sid,r in rules.items() if r['labels']['I']==1 or r['labels']['F']==1}
bundles={}
for l in (RULE/'delivered-complete-source-bundles.jsonl').open():
 r=json.loads(l);sid=r['source_record']['id']
 if sid in positive_ids:bundles[sid]=r
assert len(bundles)==81

(HERE/'materials').mkdir(exist_ok=True)
links=[]
for sid,p in bundles.items():
 sr=p['source_record'];loc=json.dumps(sr['source_ref'],ensure_ascii=False,indent=2)
 parts=[f'<h1>{html.escape(sid)}</h1><h2>当前固定命题</h2><p>{html.escape(sr["text"])}</p>',
        f'<details><summary>当前来源位置</summary><pre>{html.escape(loc)}</pre></details>',
        '<h2>原包语境</h2>']
 for c in sr['contexts']:
  parts.append(f'<h3>{html.escape(c.get("context_id",""))}</h3><p>{html.escape(c.get("text",""))}</p>')
 parts.append('<h2>原包完整来源资源</h2>')
 for i,r in enumerate(p['source_full_text_resources']):
  parts.append(f'<details><summary>来源资源 {i}</summary><pre>{html.escape(json.dumps(r,ensure_ascii=False,indent=2))}</pre></details>')
 parts.append('<h2>原件入口</h2>')
 for doc in p['source_documents']:
  raw=doc.get('snapshot')
  if raw:
   path=Path(raw);exists=path.exists();links.append({'source_id':sid,'target':str(path),'exists':exists})
   if exists:parts.append(f'<p><a href="{html.escape(path.as_uri(),quote=True)}">{html.escape(path.name)}</a></p>')
   else:parts.append(f'<p>原件路径当前不可打开：{html.escape(str(path))}</p>')
 for asset in p['source_asset_locations']:
  raw=asset.get('absolute_path',asset.get('snapshot'))
  if raw and Path(raw).is_absolute() and Path(raw).exists():
   path=Path(raw);parts.append(f'<p><a href="{html.escape(path.as_uri(),quote=True)}">原图页：{html.escape(path.name)}</a></p>')
 parts.append('<p>这是原冻结规则材料的查看页。原文和语境保留；原件可用不代表当前句可继承全文标签。</p>')
 page='<!doctype html><html lang="zh"><meta charset="utf-8"><title>'+sid+'</title><style>body{max-width:1100px;margin:32px auto;font:16px/1.8 system-ui;color:#20252b}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.7 system-ui}p{white-space:pre-wrap}details{padding:10px;border-bottom:1px solid #ddd}a{color:#14549b}</style>'+''.join(parts)+'</html>'
 (HERE/'materials'/f'{sid}.html').write_text(page,encoding='utf-8')

sample=[]
for d in ['I','F']:
 for sid,a in sorted(ais.items(),key=lambda kv:kv[1]['blind_id']):
  if not (a['judgments'][d]['value']==1 or rules[sid]['labels'][d]==1):continue
  r=review[sid,d];bid=a['blind_id'];m=metadata[bid]
  packet=json.loads((AI/'source-A/coder-A/materials'/f'{bid}.json').read_text())
  material=AI/'source-A/coder-A/materials'/f'{bid}.html';assert material.exists()
  j=a['judgments'][d]
  values=[bid,sid,'创新性' if d=='I' else '公平性',m['department'],a['judgments'][d]['value'],fmt(rules[sid]['labels'][d]),
   fmt(r['review_value']),r['assessment'],packet['source_record']['text'],r['reason'],j['evidence']+'\n位置：'+j['locator'],str(material),str(r['detailed_review_file'])]
  assert all(not isinstance(v,str) or len(v)<=32767 for v in values)
  sample.append({'values':values,'link':material.as_uri(),'needs_human_review':r['needs_human_review'],'dimension':d})
assert len(sample)==68 and sum(r['dimension']=='I' for r in sample)==50
full=[]
for d in ['I','F']:
 for sid,p in sorted(bundles.items()):
  pred=rules[sid]
  if pred['labels'][d]!=1:continue
  dec=pred['decisions'][d];r=review.get((sid,d));material=HERE/'materials'/f'{sid}.html'
  reason=dec.get('reason','');evidence=json.dumps({'current_anchor':dec.get('current_anchor'),'context_evidence':dec.get('context_evidence')},ensure_ascii=False)
  values=[sid,'创新性' if d=='I' else '公平性',years[sid]['department'],1,
   fmt(r['review_value']) if r else '未复审',r['assessment'] if r else '规则阳性已提取，语义复审进行中',
   p['source_record']['text'],reason,evidence,str(material)]
  assert all(not isinstance(v,str) or len(v)<=32767 for v in values)
  full.append({'values':values,'link':material.as_uri(),'dimension':d})
assert len(full)==102 and sum(r['dimension']=='I' for r in full)==61
save('workbook-input.json',{'sheets':[
 {'name':'800条全部阳性','headers':['原盲号','原记录号','维度','部门','原AI值','原规则值','AI复审建议','复审结论','当前完整命题','AI复审说明','原AI证据与定位','完整材料路径','复审证据文件'],
  'rows':sample,'body_column':'I','source_column':'A','context':'800条AI辅助抽检全部阳性：I50项、F18项，共68项/57条材料；非真人参照。原值保留，AI复审建议单列。'},
 {'name':'4481条规则全部阳性','headers':['原记录号','维度','部门','原规则值','已有AI复审建议','复审状态','当前完整命题','原规则理由','原规则证据','完整材料路径'],
  'rows':full,'body_column':'G','source_column':'A','context':'全量固定规则首答全部阳性：I61项、F41项，共102项/81条材料。与前表部分重叠，不能相加为样本量。正式LLM全量仍运行，未填部分结果。'}]})
save('input-and-material-reception.json',{'AI_initial_sha256':sha(AI/'AI原始判读-800条.jsonl'),
 'rule_predictions_sha256':sha(RULE/'predictions.jsonl'),'review_inputs':[{'path':str(p),'sha256':sha(p)} for p in [AUDIT/'joined-review.json',AUDIT/'remaining-positive271-sol/reviews.json']],
 'counts':{'sample800_I':50,'sample800_F':18,'sample800_unique':57,'full4481_rule_I':61,'full4481_rule_F':41,'full4481_rule_unique':81},
 'actual_complete_LLM_results_included':False,'original_source_predictions_modified':False,'source_links':links})
print(json.dumps({'sample_positive_slots':68,'full_rule_positive_slots':102,'source_pages':81,'existing_source_links':sum(r['exists'] for r in links)},ensure_ascii=False))
