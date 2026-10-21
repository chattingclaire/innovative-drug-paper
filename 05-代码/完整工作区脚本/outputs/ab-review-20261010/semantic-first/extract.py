import json
from pathlib import Path
import openpyxl
root=Path('/PROJECT_ROOT')
out=root/'outputs/ab-review-20261010/semantic-first'
base=root/'outputs/goal-calibration-20261010/09-delivery/agent-review-20261010'
w={k:openpyxl.load_workbook(base/f'编码复核表-{k}.xlsx') for k in 'AB'}
records=[]
for i in range(39):
    start=7+i*5
    rows={k:[list(w[k]['编码表'].iter_rows(min_row=r,max_row=r,values_only=True))[0] for r in range(start,start+5)] for k in 'AB'}
    id=rows['A'][0][0]
    ctx=[{'row':r,'context_id':v[1],'kind':v[2],'locator':v[3],'text':v[4],'source':v[5]} for r,v in enumerate(w['A']['原文语境'].values,1) if v[0]==id]
    records.append({'index':i,'id':id,'coding_start_row':start,'A':rows['A'],'B':rows['B'],'contexts':ctx})
(out/'extracted.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
for a in range(0,39,6):
    lines=[]
    for r in records[a:a+6]:
        lines.append(f'\n### INDEX {r["index"]} {r["id"]} 编码 rows {r["coding_start_row"]}-{r["coding_start_row"]+4}')
        lines.append('当前: '+r['contexts'][0]['text'])
        seen=set([r['contexts'][0]['text']])
        for c in r['contexts'][1:]:
            if c['text'] and c['text'] not in seen:
                lines.append(f'语境 row {c["row"]} {c["context_id"]} {c["kind"]} {c["locator"]}: {c["text"]}')
                seen.add(c['text'])
        for k in 'AB':
            lines.append(k+' '+','.join(f'{z[2]}={z[3]}' for z in r[k]))
            for z in r[k]: lines.append(f'{k} {z[2]}: {z[4]}')
    (out/f'materials-{a:02d}.txt').write_text('\n'.join(lines))
print([(r['index'],r['id']) for r in records])
