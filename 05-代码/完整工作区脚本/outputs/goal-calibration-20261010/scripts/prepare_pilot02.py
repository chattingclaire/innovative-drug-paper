"""Build identical source-only inputs with distinct A/B blind IDs and order."""
import copy
import hashlib
import json
import random
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'01-review/context-projection-sol'
OUT=ROOT/'04-calibration/pilot02'
MANUAL=ROOT/'03-manual/common-manual-v1.1-development.md'
CANONICAL=SOURCE/'canonical_source_context-v2.jsonl'
SUPPLEMENTS=SOURCE/'prospective-common-supplements-source-only-v3.jsonl'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rows(p):return [json.loads(s) for s in p.read_text().splitlines() if s.strip()]
def serialize(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
assert not OUT.exists(), 'Release a new directory instead of overwriting inputs'
assert sha(CANONICAL)=='2f6decdb54a604617339d95fef5531d7ed80fc1100db86760a9e50ffd2910e98'
assert sha(SUPPLEMENTS)=='acea6568d697bd6e01b3453cb6499db754fb538e78021a0fe1a50b3e8eeca53c'
material=rows(CANONICAL)
assert len(material)==41
by_id={r['id']:r for r in material}
for s in rows(SUPPLEMENTS):
    assert s['record_id'] in by_id
    assert hashlib.sha256(s['text'].encode()).hexdigest()==s['text_sha256']
    meta={k:v for k,v in s.items() if k not in {'record_id','supplement_id','text','source_snapshot','source_sha256','text_sha256','locator'}}
    context={'context_id':s['supplement_id'],'kind':'external_source','text':s['text'],
             'source_ref':{'sha256':s['source_sha256'],'locator':s['locator'],'metadata':meta}}
    by_id[s['record_id']]['contexts'].append(context)
instructions='''# 开发补材后独立重判说明

本批41条来自已完成开发首判的同一组记录，材料与手册已版本化修复。两位分别判断同一共同手册/来源，不看另一位结果；本轮是补材后的开发重判，不能称为未曝光最终检验。可以保留自己的既有认识，但不得把旧标签当新依据，不读取旧提交/讨论或admin文件。

只读本目录packet.jsonl、manual.md、instructions.md、source-pages中的附件。不要读取兄弟目录、主目录其他审查、预测/旧答案；不自行搜索外部资料。逐条判断S/E/Ec/I/F为0/1/null。当前和语境关系须直接，不把新补材全部内容继承给当前。CTX编号保留原值；SUP是新增连续原文。没有text的结构节点必须保留并沿其相关CTX阅读。

含source_page_attachments的记录，应实际查看所附完整页，确认图表分支/共同谓词/跨页关系。源文本与图有冲突时以原图核明，记录具体差异，不静默更改材料。

每行labels.jsonl格式：{"id":"P2A001","labels":{"S":0,"E":0,"Ec":0,"I":0,"F":0},"evidence":{"S":{"path":"excluded","current_quote":"当前连续原文","contexts_used":[],"image_sources_used":[],"reason":"原文关系理由"},"E":{...},"Ec":{...},"I":{...},"F":{...}},"material_requests":[]}。
contexts_used每项为{"context_id":"CTX-...或SUP-...","quote":"该节点连续原文","purpose":"实际补足的关系"}；image_sources_used为实际查看附件的attachment_id数组。每个1保存当前连续原文锚点，I3/F具体路径说明所需证据项；0说明最接近内容为何不足。null登记维度与具体材料缺失/规则冲突，不将未知填0。

分别完成后封存labels.jsonl，不覆盖；写submission.json，记录身份AI、实际模型/推理设置、起止时间、输入及全部使用图片SHA、记录数、输入范围偏离和实际查看附件清单。不得协商、按一致率改值，不得称为真人执行或指标验收完成。新意见另存。
'''
admin=OUT/'admin';admin.mkdir(parents=True)
mapping=[];releases=[];source_assets={}
for row in material:
    for asset in row.get('source_page_attachments',[]):
        origin=SOURCE/asset['relative_path']
        assert origin.exists() and sha(origin)==asset['sha256']
        source_assets[asset['attachment_id']]={'origin':origin,'metadata':asset}
for coder,seed in [('A',2026101002),('B',2026101003)]:
    directory=OUT/coder;directory.mkdir()
    pages=directory/'source-pages';pages.mkdir()
    for aid,info in sorted(source_assets.items()):
        dest=pages/(aid+'.png')
        shutil.copyfile(info['origin'],dest)
        assert sha(dest)==info['metadata']['sha256']
    shuffled=copy.deepcopy(material);random.Random(seed).shuffle(shuffled)
    packet=[]
    for index,row in enumerate(shuffled,1):
        original=row['id'];bid=f'P2{coder}{index:03d}'
        content=copy.deepcopy(row);content.pop('id')
        content_hash=hashlib.sha256(serialize(content).encode()).hexdigest()
        row['id']=bid
        for asset in row.get('source_page_attachments',[]):
            asset['relative_path']='source-pages/'+asset['attachment_id']+'.png'
        packet.append(row)
        mapping.append({'coder':coder,'blind_id':bid,'frame_id':original,'source_content_sha256':content_hash,'role':'development_rejudgment'})
    (directory/'packet.jsonl').write_text(''.join(serialize(r)+'\n' for r in packet))
    shutil.copyfile(MANUAL,directory/'manual.md')
    (directory/'instructions.md').write_text(instructions)
    releases.append({'coder':coder,'n':41,'packet_sha256':sha(directory/'packet.jsonl'),
                     'manual_sha256':sha(directory/'manual.md'),'instructions_sha256':sha(directory/'instructions.md'),
                     'source_pages':[{'attachment_id':aid,'sha256':v['metadata']['sha256']} for aid,v in sorted(source_assets.items())]})
a={r['frame_id']:r['source_content_sha256'] for r in mapping if r['coder']=='A'}
b={r['frame_id']:r['source_content_sha256'] for r in mapping if r['coder']=='B'}
assert a==b
(admin/'private_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
design={'status':'development_inputs_released_no_submission_yet','n':41,'model_requested':'gpt-6.1-sol','reasoning_effort_requested':'ultra',
        'identity':'AI','original_submission_overwritten':False,'new_final_holdout_consumed':0,'distinct_blind_ids_and_orders':True,
        'common_content_equal_by_original_id':True,'textless_structure_preserved':True,
        'source_changes':'Original source structures restored; one image transcription condition2→condition7; original pages appended; common finite 2024 mechanism and official explanation added.',
        'sources':[{'path':str(p),'sha256':sha(p)} for p in [CANONICAL,SUPPLEMENTS,MANUAL]],'releases':releases,
        'final_acceptance':False,'historical_first_judgment_files':'pilot01 unchanged'}
(admin/'design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'n':41,'distinct_source_pages':len(source_assets),'releases':[{'coder':x['coder'],'packet_sha256':x['packet_sha256']} for x in releases]},ensure_ascii=False))
