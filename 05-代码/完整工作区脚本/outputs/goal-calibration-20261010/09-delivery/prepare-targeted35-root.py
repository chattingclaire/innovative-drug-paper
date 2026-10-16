from pathlib import Path
import collections
import hashlib
import html
import json
import os

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药/outputs/goal-calibration-20261010')
SOURCE=ROOT/'08-audits/ai800-disagreement-semantic-root/complete-review-reception-root/targeted-human-calibration-items.json'
OUT=ROOT/'09-delivery/targeted-calibration35-root'
items=json.loads(SOURCE.read_text())['items']
assert len(items)==35 and len({x['source_id'] for x in items})==34
OUT.mkdir(exist_ok=False);(OUT/'materials').mkdir()
manual=ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt'
(OUT/'manual.txt').write_bytes(manual.read_bytes())
inputs=[SOURCE,manual];groups=collections.defaultdict(list)
for x in items:groups[x['source_id']].append(x)
escape=lambda s:html.escape(str(s))
for sid,group in groups.items():
    material=Path(group[0]['material_files'][0]);inputs.append(material)
    obj=json.loads(material.read_text());bundle=obj.get('source_bundle',obj)
    assert bundle['source_record']['id']==sid and bundle['source_record']['text']==group[0]['complete_current']
    parts=['<!doctype html><meta charset="utf-8"><title>'+sid+'核定材料</title>',
        '<style>body{font:16px/1.65 Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 20px;color:#17202a}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f6f8;padding:14px}h2{font-size:21px}a{color:#175ca8}</style>',
        '<h1>'+sid+' 核定材料</h1><p>本页用于开发校准，已展示机器原值与AI复审建议。<a href="../manual.txt">查看共同编码手册</a></p>',
        '<h2>当前完整命题</h2><pre>'+escape(bundle['source_record']['text'])+'</pre>',
        '<p>原文位置：'+escape(json.dumps(bundle['source_record'].get('source_ref'),ensure_ascii=False))+'</p>']
    for x in group:
        parts.append('<h2>'+escape(x['dimension'])+' 需要核定的问题</h2>')
        for s in x['original_judgments_and_AI_review_suggestions']:
            value=s['review_value']
            parts.append('<p>原辅助AI值：'+escape(s['ai_original'])+'。原规则值：'+escape(s['rule_original'])+'。AI复审建议：'+escape('未定' if value is None else value)+'。</p><pre>'+escape(s['reason'])+'</pre>')
            if s['specific_question']:
                question=s['specific_question']
                if isinstance(question,dict):question=question['issue']
                parts.append('<p>'+escape(question)+'</p>')
    parts.append('<h2>同一材料包提供的语境</h2>')
    for c in bundle['source_record'].get('contexts',[]):
        parts.append('<h3>'+escape(c.get('context_id',c.get('kind','语境')))+'</h3><p>'+escape(json.dumps(c.get('source_ref',c.get('locator')),ensure_ascii=False))+'</p><pre>'+escape(c.get('text',''))+'</pre>')
    # The full provided packet remains accessible without claiming all resources were consumed.
    parts.append('<details><summary>完整原材料包及来源信息</summary><pre>'+escape(json.dumps(bundle,ensure_ascii=False,indent=2))+'</pre></details>')
    sources=[]
    for doc in bundle.get('source_documents',[]):
        source_sha=doc.get('source_sha256',doc.get('sha256',doc.get('source_ref',{}).get('sha256')))
        if source_sha:
            candidates=list((ROOT.parent/'ai-audit800-20261010/source-A/shared-source/source-files').glob(source_sha+'.*'))
            for p in candidates:
                if p.is_file() and hashlib.sha256(p.read_bytes()).hexdigest()==source_sha:
                    sources.append(p);inputs.append(p)
    if sources:
        parts.append('<h2>同版原件</h2><p>下列原件已核字节SHA。阅读范围由当前确指关系决定，不能继承无关兄弟条款。</p>')
        for p in dict.fromkeys(sources):parts.append('<p><a href="'+escape(p.as_uri())+'">'+escape(p.name)+'</a></p>')
    (OUT/'materials'/f'{sid}.html').write_text('\n'.join(parts),encoding='utf-8')
rows=[]
for x in items:
    suggestions=x['original_judgments_and_AI_review_suggestions']
    s=suggestions[0];v=s['review_value'];v=v if type(v) is int else None
    reason=s['reason'];question=s['specific_question'] or s['assessment']
    if isinstance(question,dict):question=question['issue']
    if s['assessment'].endswith('待核') and v is not None:question='暂定建议'+str(v)+'，尚未核定。'+str(question)
    rows.append({'values':[x['source_id'].replace('RECODE25-',''),x['dimension'],x['complete_current'],v,reason,question,s['ai_original'],s['rule_original']],
                 'source_id':x['source_id'],'material_url':(OUT/'materials'/f"{x['source_id']}.html").as_uri()})
value={'sheet':'定向核定','headers':['条款（点击看材料）','维度','当前完整命题','0或1','判断理由','待核问题','原辅助AI值','原规则值'],
       'title':'编码定向核定：34条、35项',
       'instructions':'D、E列是AI建议，请真人核定后直接改值和理由。空白为未定。点击A列查看原文、语境和共同手册。',
       'identity_note':'用于本轮开发校准，已显示机器答案，不作为新一轮独立盲评或正式准确率样本。',
       'rows':rows}
(OUT/'workbook-input.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
bindings=[]
for p in dict.fromkeys(inputs):
    raw=p.read_bytes();bindings.append({'path':str(p),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(OUT/'input-and-material-bindings.json').write_text(json.dumps({'inputs':bindings,'material_pages':34,'dimension_rows':35,'actual_human_review_results':0},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
os.symlink('/Users/rainbow/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules',OUT/'node_modules')
print(json.dumps({'directory':str(OUT),'rows':len(rows),'unresolved_blank_D':sum(x['values'][3] is None for x in rows)},ensure_ascii=False))
