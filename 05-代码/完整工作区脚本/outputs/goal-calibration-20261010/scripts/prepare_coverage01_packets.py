"""Prepare already-exposed cross-department development coverage, without labels."""
import copy
import hashlib
import json
import random
import shutil
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'01-review/context-projection-sol/coverage01'
CANONICAL=SOURCE/'canonical_source_context-v2.jsonl'
OUT=ROOT/'04-calibration/coverage01'
MANUAL=ROOT/'03-manual/common-manual-v1.1-development.md'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
serialize=lambda x:json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
assert sha(CANONICAL)=='a5e53a0a7d008145e89f03b256fdc0aa52f733eb3d4cd1b6f9e4196987107e4f'
assert not (OUT/'A').exists() and not (OUT/'B').exists()
material=[json.loads(s) for s in CANONICAL.read_text().splitlines() if s.strip()]
selection=json.loads((OUT/'admin/selection.json').read_text())
selected={x['frame_id']:x for x in selection['records']}
assert len(material)==36 and {x['id'] for x in material}==set(selected)
asset_fields=['source_page_attachments','source_image_attachments']
assets={}
for r in material:
    for field in asset_fields:
        for image in r.get(field,[]):
            origin=(SOURCE/image['relative_path']).resolve()
            assert origin.exists() and sha(origin)==image['sha256']
            aid=image['attachment_id']
            if aid in assets:assert assets[aid]['sha256']==image['sha256']
            assets[aid]={'origin':origin,'sha256':image['sha256'],'filename':aid+origin.suffix.lower()}
instructions=(ROOT/'04-calibration/pilot02/A/instructions.md').read_text()
instructions=instructions.replace('# 开发补材后独立重判说明','# 三部门开发覆盖独立判读说明')
instructions=instructions.replace('本批41条来自已完成开发首判的同一组记录，材料与手册已版本化修复。两位分别判断同一共同手册/来源，不看另一位结果；本轮是补材后的开发重判，不能称为未曝光最终检验。可以保留自己的既有认识，但不得把旧标签当新依据，不读取旧提交/讨论或admin文件。','本批36条是历史已用于开发的材料，按来源多样性补充共同手册的三部门执行覆盖。两位分别判断同一v1.1手册与来源，不看另一位结果，不读取旧答案或admin选择记录。本次不是未曝光最终检验；同目录首判只保存一次，后续意见另存。')
instructions=instructions.replace('含source_page_attachments的记录','含source_page_attachments或source_image_attachments的记录')
instructions=instructions.replace('P2A001','C1A001')
mapping=[];releases=[]
for coder,seed in [('A',2026101036),('B',2026101037)]:
    directory=OUT/coder;directory.mkdir();(directory/'source-pages').mkdir()
    for aid,asset in assets.items():
        dest=directory/'source-pages'/asset['filename'];shutil.copyfile(asset['origin'],dest)
        assert sha(dest)==asset['sha256']
    packet=copy.deepcopy(material);random.Random(seed).shuffle(packet)
    for index,r in enumerate(packet,1):
        original=r['id'];bid=f'C1{coder}{index:03d}';r['id']=bid
        for field in asset_fields:
            for image in r.get(field,[]):image['relative_path']='source-pages/'+assets[image['attachment_id']]['filename']
        content=copy.deepcopy(r);content.pop('id')
        mapping.append({'coder':coder,'blind_id':bid,'frame_id':original,'department':selected[original]['department'],
                        'source_content_sha256':hashlib.sha256(serialize(content).encode()).hexdigest(),
                        'role':'prior_exposed_cross_department_development'})
    (directory/'packet.jsonl').write_text(''.join(serialize(r)+'\n' for r in packet))
    shutil.copyfile(MANUAL,directory/'manual.md');(directory/'instructions.md').write_text(instructions)
    releases.append({'coder':coder,'n':36,'packet_sha256':sha(directory/'packet.jsonl'),
                     'manual_sha256':sha(directory/'manual.md'),'instructions_sha256':sha(directory/'instructions.md'),
                     'source_images':[{'attachment_id':a,'sha256':x['sha256']} for a,x in sorted(assets.items())]})
assert {x['frame_id']:x['source_content_sha256'] for x in mapping if x['coder']=='A'}=={x['frame_id']:x['source_content_sha256'] for x in mapping if x['coder']=='B'}
admin=OUT/'admin'
(admin/'private_mapping.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n')
design={'status':'development_inputs_released_no_submission_yet','n':36,'department_counts':selection['department_counts'],
        'model_requested':'gpt-6.1-sol','reasoning_effort_requested':'ultra','identity':'AI',
        'source_path':str(CANONICAL),'source_sha256':sha(CANONICAL),'manual_sha256':sha(MANUAL),
        'selection_sha256':sha(admin/'selection.json'),'new_final_holdout_consumed':0,
        'common_content_equal_by_original_id':True,'original_structure_and_textless_nodes_preserved':True,
        'source_repair':'Two guide boundary identities repaired; table source group/merged-cell geometry added, without dimension annotations.',
        'releases':releases,'final_acceptance':False}
(admin/'design.json').write_text(json.dumps(design,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'n':36,'distinct_source_images':len(assets),'common_content_equal':True},ensure_ascii=False))
