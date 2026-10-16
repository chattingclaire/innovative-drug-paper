import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DIMS = ['S','E','Ec','I','F']

# Each five-character code is an explicit, position-matched judgment in S/E/Ec/I/F order.
PACKET_CODES = {
1:'00100 00000 00000 00100 00101 00000 00000 10000 00000 00000',
2:'00000 10000 11111 00000 00000 11000 01000 00001 10000 01000',
3:'00000 00000 00000 00000 10000 00001 00000 00000 00101 00000',
4:'00100 00100 10000 11000 00000 00000 00100 00100 00000 00100',
5:'10000 00000 00000 00000 00000 00000 00000 00010 00000 00100',
6:'00000 00100 00000 00100 00000 00000 00100 10000 00000 00000',
7:'00000 00000 11100 00001 00000 00000 00000 00000 00000 00000',
8:'01000 00000 01000 00000 00000 00000 10000 01000 00100 00100',
9:'00000 00000 10000 00100 10000 00000 00100 00000 00000 00000',
10:'00000 00000 00000 00100 00000 00100 00001 00000 00000 00000',
11:'00100 00000 00000 00000 00000 00000 00001 00000 01010 00100',
12:'00000 00000 00000 PPPPP 00000 10000 00000 00000 00000 00000',
13:'00010 00001 00000 00000 00001 00001 00000 00000 00100 00000',
14:'00000 00000 00100 00101 00000 00000 00100 00000 00000 00000',
15:'00100 00000 01000 00001 00000 00000 00000 00010 00000 00000',
16:'00100 00000 00000 00000 11111 00101 00000 00010 10000 00100',
17:'00000 00000 00001 10000 00000 00101 00000 10100 00101 00100',
18:'00000 00000 00000 00100 01000 00000 00000 00000 00000 00000',
19:'00100 00101 00000 00000 00101 00000 00100 00000 00010 00000',
20:'00000 10000 00000 00000 00000 00001 00000 00000 00000 00101',
21:'00100 11111 00000 00000 00000 00010 00000 00000 11000 00101',
22:'00100 00010 10100 00000 00000 00000 01000 00000 10000 00000',
23:'PPPPP 00000 00000 00000 00000 00000 10000 00000 00101 00000',
24:'00000 00000 00000 00100 00001 10000 11000 00000 00000 00001',
25:'01010 00010 00100 00100 PPPPP 00000 00000 00000 00000 00000',
26:'10000 00101 00000 00010 00000 10000 11111 00000 10000 00000',
27:'00000 11000 00000 00100 00000 00000 00000 00000 00000 10000',
28:'00101 00000 10000 00000 00000 00000 00000 00000 00010 10000',
29:'00000 00000 00000 10000 00101 00001 00010 00001 00101 00000',
30:'01000 00000 00100 00000 11000 00000 00000 00100 00000 00100',
31:'00000 00000 01000 00000 01000 11100 00000 00000 00101 10000',
32:'00010 00100 00000 00000 00000 00000 00000 10000 10000 00000',
33:'00000 00000 00000 00001 00000 10000 00000 00001 PPPPP 00000',
34:'00000 00010 00000 00000 00010 00000 00000 00100 00000 00001',
35:'00000 00000 00001 10000 00000 00000 00000 11000 00100 00000',
36:'10000 00000 00000 00000 00100 00000 00100 00000 00101 10000',
37:'00010 00001 11000 10000 00000 00000 00001 00000 00101 00000',
38:'00000 00001 10000 01000 00000 00000 11010 PPPPP 00100 00000',
39:'00000 10000 00000 00100 10000 11000 PPPPP 00010 00000 00000',
40:'00100 00000 00000 00000 00000 00000 00100 PPPPP 00100 10000',
41:'00000 00000 11100 00000 00000 00000 00000 00100 00000 10000',
42:'10000 00000 00000 00000 11000 11000 00101 00101 00100 00001',
}

I_TYPES = {
'RECODE25-00693':['attribute'],'RECODE25-03594':['research_support'],
'RECODE25-00013':['qualification_advantage'],'RECODE25-04413':['attribute'],
'RECODE25-01466':['attribute'],'RECODE25-02777':['attribute'],
'RECODE25-01468':['attribute'],'RECODE25-02738':['research_support'],
'RECODE25-03767':['attribute'],'RECODE25-01400':['research_support'],
'RECODE25-04605':['attribute'],'RECODE25-02804':['attribute'],
'RECODE25-02511':['research_support'],'RECODE25-00100':['attribute'],
'RECODE25-03651':['research_support'],'RECODE25-04248':['attribute'],
'RECODE25-02749':['research_support'],'RECODE25-01401':['research_support'],
'RECODE25-03599':['research_support'],'RECODE25-03894':['attribute'],
'RECODE25-03571':['research_support'],'RECODE25-01420':['research_support'],
'RECODE25-04810':['research_support'],
}

F_TYPES = {
'RECODE25-02541':['access','affordability'],'RECODE25-00693':['dimension_information'],
'RECODE25-00322':['access'],'RECODE25-04923':['access'],
'RECODE25-01896':['access','affordability'],'RECODE25-02273':['access'],
'RECODE25-04898':['access'],'RECODE25-04919':['access'],
'RECODE25-03780':['access'],'RECODE25-03274':['access'],
'RECODE25-02318':['access'],'RECODE25-00331':['access'],
'RECODE25-03204':['access'],'RECODE25-00665':['access'],
'RECODE25-01989':['access'],'RECODE25-03874':['access'],
'RECODE25-03767':['dimension_information'],'RECODE25-03754':['access'],
'RECODE25-02052':['access'],'RECODE25-04248':['dimension_information'],
'RECODE25-02637':['access'],'RECODE25-02123':['access'],
'RECODE25-00766':['access'],'RECODE25-00654':['access'],
'RECODE25-03293':['access'],'RECODE25-01554':['access'],
'RECODE25-01234':['access'],'RECODE25-00755':['access'],
'RECODE25-01959':['access'],'RECODE25-02537':['access'],
'RECODE25-02360':['access'],'RECODE25-00553':['access'],
'RECODE25-02535':['access'],'RECODE25-04268':['access'],
'RECODE25-00919':['access'],'RECODE25-03783':['access','affordability'],
'RECODE25-02436':['access'],'RECODE25-02514':['access'],
'RECODE25-03696':['access'],'RECODE25-04229':['access'],
'RECODE25-02137':['access'],'RECODE25-01206':['access'],
'RECODE25-02461':['access'],'RECODE25-01012':['access'],
'RECODE25-04270':['access','affordability'],'RECODE25-04091':[],
}

QUALITY = {'RECODE25-04496':'quality_and_other','RECODE25-04441':'quality_and_other'}
CONTEXT_IDS = {
'RECODE25-04923','RECODE25-01896','RECODE25-01614','RECODE25-04898',
'RECODE25-03780','RECODE25-03274','RECODE25-02318','RECODE25-00331',
'RECODE25-04091','RECODE25-03204','RECODE25-00665','RECODE25-02738',
'RECODE25-03874','RECODE25-01400','RECODE25-03440','RECODE25-03754',
'RECODE25-03033','RECODE25-03796','RECODE25-00867','RECODE25-02273',
}
PENDING_ISSUE = '冒号或引导句后的必要条件、列项或处置情形未随分析单元提供，缺失内容影响整体理解，需补充完整原文。'

POS_REASON = {
'S':'本单元明确涉及药物或用药风险、不良反应、安全评价或风险控制。',
'E':'本单元明确涉及药物疗效、临床获益、生活质量或效果判断证据。',
'Ec':'本单元明确涉及药品价格、费用、支付标准、基金影响或费用承担。',
'I':'本单元明确涉及药物创新属性、创新资格或药物研发创新支持。',
'F':'本单元明确涉及药品保障获取、患者可负担、供应配备或公平性信息要求。',
}
ZERO_REASON = {
'S':'本单元未实质讨论药物或用药安全风险。',
'E':'本单元未实质讨论药物防治效果或临床获益。',
'Ec':'本单元未实质讨论药品价格、治疗费用或支付资源。',
'I':'本单元未实质讨论药物创新属性或研发创新支持。',
'F':'本单元未实质讨论药品保障获取、患者负担或临床管理难度。',
}

def iter_context_text(v):
    if isinstance(v, str):
        return
    if isinstance(v, list):
        for z in v:
            yield from iter_context_text(z)
    elif isinstance(v, dict):
        for k,z in v.items():
            if k in {'text','headers','row_cells','caption','definition','title','note'} and isinstance(z,str):
                yield z
            elif isinstance(z,(dict,list)):
                yield from iter_context_text(z)

def make_row(inp, code):
    pending = code == 'PPPPP'
    labels = {d:('待定' if pending else int(code[i])) for i,d in enumerate(DIMS)}
    reasons = {d:(PENDING_ISSUE if pending else POS_REASON[d] if labels[d] == 1 else ZERO_REASON[d]) for d in DIMS}
    evidence=[]
    if not pending:
        for d in DIMS:
            if labels[d] == 1:
                evidence.append({'dimension':d,'source':'unit','quote':inp['text']})
                if inp['id'] in CONTEXT_IDS:
                    ctx = next(iter_context_text(inp.get('contexts',{})), None)
                    if ctx and ctx != inp['text']:
                        evidence.append({'dimension':d,'source':'context','quote':ctx})
    return {
        'id':inp['id'], 'labels':labels, 'dimension_reasons':reasons,
        'evidence':evidence, 'material_issue':PENDING_ISSUE if pending else '',
        'fairness_subtypes':F_TYPES.get(inp['id'],[]) if labels['F']==1 else [],
        'innovation_subtypes':I_TYPES.get(inp['id'],[]) if labels['I']==1 else [],
        'safety_quality_basis':'undetermined' if pending else (QUALITY.get(inp['id'],'no_quality_basis') if labels['S']==1 else 'no_quality_basis')
    }

for n in range(1,43):
    ip=HERE/f'input-{n:03d}.json'; op=HERE/f'output-{n:03d}.json'
    if op.exists():
        raise SystemExit(f'refusing to overwrite {op.name}')
    rows=json.loads(ip.read_text())['rows']; codes=PACKET_CODES[n].split()
    if len(rows)!=10 or len(codes)!=10: raise SystemExit(f'count {n}')
    out={'protocol_version':'CAL-5D-20260926-v1.3','rows':[make_row(x,c) for x,c in zip(rows,codes)]}
    op.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
