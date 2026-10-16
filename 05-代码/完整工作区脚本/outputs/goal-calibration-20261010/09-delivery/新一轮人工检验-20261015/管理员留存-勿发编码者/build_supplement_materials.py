"""Prepare one common source packet and blinded human views. No judging."""
from pathlib import Path
import json,hashlib,shutil,random,html,re,sys,secrets
from datetime import datetime,timezone

HERE=Path(__file__).resolve().parent
PREP=HERE/'追加三份文件来源准备'; SRC=HERE/'候选来源下载'
OUT=HERE.parent/'补充判读-122条'; ADMIN=OUT/'管理员留存-勿发编码者'
ADMIN.mkdir(parents=True,exist_ok=True)
assert not (ADMIN/'READY.json').exists(),'Released packet is immutable'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def h(s):return hashlib.sha256(s.encode()).hexdigest()
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def cj(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
docs=json.loads((PREP/'sources.json').read_text());dm={d['code']:d for d in docs}
targets=[json.loads(l) for l in (PREP/'targets.jsonl').read_text().splitlines()]
assert len(targets)==122
sys.path.insert(0,str(HERE/'冻结版本/rule'));sys.dont_write_bytecode=True
from source_packet import semantic_unit,source_inventory
freeze=json.loads((HERE/'方法与标准冻结.json').read_text())
for x in freeze['snapshots']:assert sha(Path(x['snapshot']['path']))==x['snapshot']['sha256']

def appendix_text(d):
    tr=d.get('attachment_transcription',{})
    if 'text' in tr:return tr['text']
    if not tr:return ''
    parts=[]
    for i in [1,2]:
        parts += [tr[f'table{i}_title'],'｜'.join(tr[f'table{i}_headers'])]
        parts += ['｜'.join(row) for row in tr[f'table{i}_rows']]
    return '\n'.join(parts)

packets=[];mechanical=[]
for r in targets:
    d=dm[r['document_code']];s=d['source_sha256'];pi=r['paragraph_index'];pid=f'{d["code"]}-P{pi:03}'
    para=d['paragraphs'][pi];assert r['text'] in para
    context={'context_id':'CTX-'+pid,'kind':'paragraph','text':para,'source_document':'SOURCE-'+s,'source_ref':{'sha256':s,'source_resource_id':'SOURCE-'+s,'locator':{'paragraph_id':pid,'sequence_index':pi}},'structure':{'paragraph_id':pid,'sequence_index':pi}}
    row={'id':r['id'],'text':r['text'],'contexts':[context],'pages':[],'source_ref':{'sha256':s,'source_resource_id':'SOURCE-'+s,'locator':{'paragraph_ids':[pid],'source_unit_id':r['id'],'paragraph_index':pi,'sentence_index':r['sentence_index']}},'source_attachments':[]}
    resources=[{'source_resource_id':'FULLTEXT-'+s,'source_sha256':s,'paragraphs':[{'text':p,'source_paragraph_id':f'{d["code"]}-P{i:03}','source_locator':{'paragraph_id':f'{d["code"]}-P{i:03}','sequence_index':i},'role':'original_source_paragraph','representation':d['representation']} for i,p in enumerate(d['paragraphs'])]}]
    at=appendix_text(d)
    if at:
        ash=d['attachment_checks'][0]['sha256']
        resources.append({'source_resource_id':'APPENDIX-'+ash,'source_sha256':ash,'paragraphs':[{'text':at,'source_paragraph_id':d['code']+'-ANNEX','source_locator':{'attachment':d['attachments'][0]},'role':'source_attachment_transcription','representation':d['attachment_transcription']['method']}]})
    bundle={'common_source_bundle_version':{'version':'supplement122-v1','scope':'three_additional_documents_no_4481_replacement'},'source_record':row,'source_documents':[{'source_resource_id':'SOURCE-'+s,'source_sha256':s,'snapshot':str((SRC/d['source_file']).resolve()),'title':d['title'],'url':d['url'],'representation':d['representation']}],'explicit_or_primary_source_resources':[],'preserved_historical_neutral_source_supplements':[],'source_full_text_resources':resources,'source_asset_locations':[{'attachment_id':d['code']+'-ATTACH-'+str(i),'absolute_path':str((SRC/a).resolve()),'sha256':sha(SRC/a),'kind':'official_original_attachment'} for i,a in enumerate(d['attachments'])],'source_locator_bases':{'base':str(SRC.resolve())},'source_reference_index':[],'source_provenance_addenda':[]}
    unit=semantic_unit(bundle);inv=source_inventory(bundle)
    assert unit['text']==r['text'] and unit['contexts'][0]['text']==para
    packets.append({'id':r['id'],'source_bundle':bundle,'semantic_unit':unit})
    mechanical.append({'id':r['id'],'source_bundle_sha256':h(cj(bundle)),'current_text_in_bound_paragraph':True,'source_inventory_count':len(inv),'all_current_source_bytes_verified':sha(SRC/d['source_file'])==s})
(ADMIN/'common-inputs.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in packets))
dump(ADMIN/'mechanical-input-checks.json',mechanical)
dump(ADMIN/'sources.json',docs)

seedfile=ADMIN/'blind-seeds.json'
if seedfile.exists():seeds=json.loads(seedfile.read_text())
else:seeds={side:secrets.randbits(64) for side in ['A','B']};dump(seedfile,seeds)
mapping={}
CSS='body{font:17px/1.85 Arial,"PingFang SC",sans-serif;color:#202a32;max-width:960px;margin:36px auto;padding:0 22px}h1{font-size:26px;line-height:1.5}h2{font-size:20px;margin-top:32px}a{color:#165d9b}p{margin:12px 0}.current{padding:18px 24px;background:#fff7df;border-left:5px solid #b88719}.meta{font-size:14px;color:#536372}.sourcepara{border-bottom:1px solid #dde3e8;padding:10px 0}pre{white-space:pre-wrap;font:inherit}img{max-width:100%;height:auto}li{margin:7px 0}table{border-collapse:collapse;width:100%}td,th{border:1px solid #bbc6ce;padding:8px;text-align:left}th{background:#eef2f6}'
def page(title,body):return '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title><style>'+CSS+'</style><body>'+body+'</body></html>'
for side in ['A','B']:
    folder=OUT/('编码者'+side);(folder/'材料').mkdir(parents=True,exist_ok=True);(folder/'来源').mkdir(exist_ok=True);(folder/'原件').mkdir(exist_ok=True)
    order=targets.copy();random.Random(seeds[side]).shuffle(order)
    mapping[side]=[]
    shutil.copy2(HERE/'冻结版本/common/manual.txt',folder/'共同编码手册.txt')
    for d in docs:
        # Byte-exact snapshots are supplied, while the reading view has no remote scripts.
        names=[d['source_file']]+d['attachments']
        for name in names:shutil.copy2(SRC/name,folder/'原件'/name)
        body=f'<h1>{html.escape(d["title"])}</h1><p class="meta">{html.escape(d["number"])}；{html.escape(d["agency"])}；成文日期 {d["signed_date"]}；首次公布 {d["publication_date"]}</p><p><a href="{html.escape(d["primary_url"],quote=True)}">官方网页</a> · <a href="../原件/{html.escape(d["source_file"],quote=True)}">保存件</a></p>'
        for i,p in enumerate(d['paragraphs']):body+=f'<div class="sourcepara" id="p{i}"><span class="meta">{d["code"]}-P{i:03}</span><p>{html.escape(p)}</p></div>'
        if d['attachments']:
            body+='<h2>配套附件</h2>'
            for name in d['attachments']:
                body+=f'<p><a href="../原件/{html.escape(name,quote=True)}">{html.escape(name)}</a></p>'
                if name.endswith('.jpg'):body+=f'<img alt="官方附件原图" src="../原件/{html.escape(name,quote=True)}">'
            body+='<h2>附件文字视图</h2><p class="meta">用于检索及核对，保留原件。表格合并单元格按行展开。</p><pre>'+html.escape(appendix_text(d))+'</pre>'
        (folder/'来源'/f'{d["code"]}.html').write_text(page(d['title'],body))
    links=[]
    for i,r in enumerate(order):
        blind=f'{side}-{i+1:03}';d=dm[r['document_code']];pi=r['paragraph_index'];locator=f'材料/{blind}.html'
        mapping[side].append({'blind_id':blind,'id':r['id'],'material_locator':locator,'text_sha256':h(r['text'])})
        body=f'<p><a href="../开始阅读.html">返回目录</a></p><h1>材料 {blind}</h1><h2>当前待判句段</h2><div class="current">{html.escape(r["text"])}</div><p>分别判断安全性、有效性、经济性、创新性、公平性。按共同手册限定语境，不把整份文件的议题都归给本句。</p><h2>所在完整段落</h2><p class="meta">{d["code"]}-P{pi:03}</p><p>{html.escape(d["paragraphs"][pi])}</p><h2>来源及完整语境</h2><p>{html.escape(d["title"])}</p><p><a href="../来源/{d["code"]}.html#p{pi}">打开全文及附件，定位当前段落</a></p><p><a href="../共同编码手册.txt">共同编码手册</a></p>'
        (folder/locator).write_text(page('材料 '+blind,body));links.append(f'<li><a href="{locator}">{blind}</a>　{html.escape(r["text"][:45])}{"…" if len(r["text"])>45 else ""}</li>')
    guide=f'''编码者{side}填写说明

本包122条，每条判断安全性S、有效性E、经济性Ec、创新性I、公平性F，共610项。

1. 解压全部文件，保持文件夹结构。先读“共同编码手册.txt”，打开“开始阅读.html”查看材料。
2. Excel每条占五行，按S、E、Ec、I、F填写黄色的判定及理由栏。符合判据填1；材料充分而不符合填0。不要改编号、维度、行序及原文。
3. 理由写明当前原文依据。用到语境时，注明来源段落号及相关引文，不按文件题名或部门猜标签。
4. 确有材料缺失、指代无法解析或规则冲突时，判定留空，理由以“待定：”开头写清原因。完全空白表示尚未填写，不是0。
5. 首次提交前独立完成，不看另一人的答案或机器结果，不用AI代填、不先讨论后改成一致。疑问先记录，交回后统一处理。
6. 完成后保存原始Excel并填写“提交说明.txt”，将两份文件交回。后续修改另存版本，保留首次提交件。

共同手册原字节保留，部分开头或末尾说明涉及旧4481条及历史版本；本次执行材料范围以本说明为准，判定定义不变。本包的来源身份可见，盲法指互不查看另一位及机器答案。
'''
    (folder/'填写说明.txt').write_text(guide)
    (folder/'提交说明.txt').write_text(f'编码者{side}首次提交说明\n\n姓名或代号：\n开始判读日期时间：\n完成判读日期时间：\n是否本人独立完成、未用AI代填：\n首次提交前是否看过另一位或机器的答案：\n首次提交前是否讨论或据此改过答案：\n材料缺失、补材或其他情况：\n\n请如实填写。首次答案和后续讨论版本分别保留。\n')
    intro=f'<h1>编码者{side}判读材料</h1><p>122条材料，共610项判断。</p><p><a href="补充判读-{side}-122条.xlsx">打开填写表</a> · <a href="共同编码手册.txt">共同编码手册</a> · <a href="提交说明.txt">提交说明</a></p><details><summary>填写方法</summary><pre>{html.escape(guide)}</pre></details><h2>材料目录</h2><ol>'+''.join(links)+'</ol>'
    (folder/'开始阅读.html').write_text(page('编码者'+side+'判读材料',intro))
dump(ADMIN/'blind-assignment.json',mapping)
protocol={'created_at_utc':datetime.now(timezone.utc).isoformat(),'status':'prepared_not_issued','purpose':'冻结方法在三份追加政策文件正文上的补充检验；不估计原4481条全量准确率，不进行部门注意力比较','source_selection':'选择与药品审评、药品使用及医保价值评价直接相关且不在原55项分析来源清单的完整正式正文。不是随机来源抽样，也不是2026年7月后新增政策集合。未按机器或新人工答案筛选句段。','unit_scope':'三份正式文件正文的句段；独立标题、署名、日期、收文对象和结束公告语不作为目标；同段短小的编号子标题作为语境。配套解读和图表附件完整提供作语境，不新增为目标。','source_count':3,'unit_count':122,'decision_slots_per_coder':610,'targets_per_source':{'D1':16,'D2':75,'D3':31},'human_workflow':'两人独立初判；保留首次答案；收齐后记录分歧及裁决，先冻结参照再对照机器。不得为达0.8改答案、改规则或替换样本。','metrics':'按维度报告有效参照数、正例数、TP/FP/FN/TN、待定数、Cohen kappa、precision、recall、F1及A/B一致性。0分母指标记不可估计。非概率选择的三文件检验不套原1151条抽样权重，不外推总体置信区间。','version_limit':'新检验只对应冻结的第六轮规则与冻结LLM执行方案，不能替代旧4481结果的验证或把旧结果改称新版结果。','code_freeze':str(HERE/'方法与标准冻结.json'),'code_freeze_sha256':sha(HERE/'方法与标准冻结.json'),'common_manual_sha256':freeze['manual_sha256'],'first_machine_outputs_not_yet_generated':True,'new_human_results_received':False,'old4481_unchanged':True,'common_inputs_sha256':sha(ADMIN/'common-inputs.jsonl'),'material_preparation_checks':'正文、附件、相同可用语境和盲号映射机械核验；规则semantic_unit及source_inventory适配通过，未调用judge或LLM。'}
dump(ADMIN/'protocol.json',protocol)
(OUT/'给研究者的说明.md').write_text('''# 补充判读材料

本包共122条，来自临床急需境外已上市药品审评、儿童用药供应保障、真实世界医保综合价值评价试点三份正式文件。两位编码者每人填写610项判断。

用途是核验冻结后的方法在这些追加材料上的表现。三份文件不属于原55项分析来源，且不是随机抽取；因此不并入原4481条，不将结果当成原4481条的准确率，也不据此比较部门注意力。它们是在原研究时间范围内发布的文件，不称为时间外推检验。

本包不重填旧200条。旧200条最初是独立真人判读；由于其后参与新版规则修复，对新版只提供开发诊断。原4481条保持旧版结果，后续正文必须区分版本。

把编码者A与编码者B材料分别给两个人，首次提交前各自独立完成。每份都包含空白表、原文、完整语境、附件、相同手册与提交说明。研究者保留管理员目录，勿把映射表和未来机器答案交给编码者。

收齐两份原始答案和提交说明后，先核对完整性及两人分歧；需要讨论的，保留讨论前后版本。参照结果冻结后再作机器对照。新材料可能仍有分歧，也可能某些维度正例不足；必须如实报告，不能先保证超过0.8。

目前这是已准备的材料包，只有在READY.json生成并完成打包检查后才可发放。当前没有新人工检验成绩。
''')
print(json.dumps({'units':len(targets),'human_views':len(targets)*2,'source_adapter_checks':len(mechanical),'machine_predictions':0},ensure_ascii=False))
