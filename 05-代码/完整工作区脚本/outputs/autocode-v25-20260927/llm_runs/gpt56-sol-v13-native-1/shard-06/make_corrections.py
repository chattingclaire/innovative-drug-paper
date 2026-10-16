import json
from pathlib import Path

here=Path(__file__).resolve().parent
fixes={
    13:('RECODE25-03258',['access']),
    16:('RECODE25-02777',['dimension_information']),
    19:('RECODE25-03784',['access']),
}
for n,(row_id,value) in fixes.items():
    src=here/f'output-{n:03d}.json'
    dst=here/f'correction-{n:03d}-01.json'
    if dst.exists():
        raise SystemExit(f'refusing to overwrite {dst.name}')
    data=json.loads(src.read_text())
    row=next(r for r in data['rows'] if r['id']==row_id)
    old=row['fairness_subtypes']
    row['fairness_subtypes']=value
    data['correction_record']={
        'source_output':src.name,
        'reason':'结构校验发现F=1但公平性子类型数组为空；依据原已完成判断补录，不改变五维标签。',
        'changes':[{'id':row_id,'field':'fairness_subtypes','old':old,'new':value}],
    }
    # correction_record is retained separately because schema disallows extra top-level fields.
    record=data.pop('correction_record')
    dst.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    (here/f'correction-{n:03d}-01.record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
