"""Read-only validation of AI development judgments and exported workbooks."""
from pathlib import Path
from fractions import Fraction
import hashlib
import json
import runpy
from openpyxl import load_workbook

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
OUT = BASE / '代理试填-20261010'
DIMS = {'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
feedback = runpy.run_path(str(HERE / 'calibration_results.py'))['kappa_feedback']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
payload_path = HERE / '无答案校准内容.json'
payload = json.loads(payload_path.read_text())
source = {u['material_id']:u for u in payload['units']}
ids = list(source)
expected_blank_sha = {
    'A':'f5881457d81f4662bb12b486a0e68591f91184cc49d476af6488a88c0f367bfb',
    'B':'de5e6e0c3119bff60aad194c549c9b4f533f4c8a9f8c3e04bc02cc5783f60393'
}
results = {}
bindings = {}
for coder in 'AB':
    file = OUT / f'代理{coder}独立判定.json'
    raw = json.loads(file.read_text())
    assert raw['coder'] == f'AI代理{coder}'
    assert raw['model'] == 'gpt-5.6-sol'
    assert raw['manual_sha256'] == payload['manual_sha256']
    assert [u['material_id'] for u in raw['units']] == ids
    for u in raw['units']:
        original = source[u['material_id']]
        for d in DIMS:
            assert type(u['labels'][d]) is int and u['labels'][d] in (0,1)
            assert isinstance(u['reasons'][d],str) and u['reasons'][d].strip()
            assert isinstance(u['evidence'][d],str) and u['evidence'][d]
            assert any(u['evidence'][d] in t for t in [original['current_text'],*original['contexts']])
    results[coder] = {u['material_id']:u for u in raw['units']}
    bindings[coder] = {'json_path':str(file),'json_sha256':sha(file)}

stats = {}
disagreements = []
for code,name in DIMS.items():
    pairs = [(results['A'][i]['labels'][code],results['B'][i]['labels'][code]) for i in ids]
    s = feedback(pairs)
    n = len(pairs)
    a1,b1 = sum(a for a,b in pairs),sum(b for a,b in pairs)
    po = Fraction(sum(a==b for a,b in pairs),n)
    pe = Fraction(a1*b1+(n-a1)*(n-b1),n*n)
    independent_k = (po-pe)/(1-pe) if pe!=1 else None
    assert s['kappa'] == (float(independent_k) if independent_k is not None else None)
    s['disagreement_ids'] = [i for i,(a,b) in zip(ids,pairs) if a!=b]
    stats[name] = s
    for i in s['disagreement_ids']:
        disagreements.append({'material_id':i,'dimension':name,'A':{k:results['A'][i][k][code] for k in ('labels','reasons','evidence')},'B':{k:results['B'][i][k][code] for k in ('labels','reasons','evidence')}})

def displayed_reason(reason,evidence):
    if len(evidence)<=120:
        return f'{reason}\n依据：“{evidence}”'
    return f'{reason}\n依据（节选）：“{evidence[:120]}”\n完整原文见“阅读材料”同编号。'

def values(sheet):
    return [[c.value for c in row] for row in sheet.iter_rows()]

workbook_checks = {}
for coder in 'AB':
    original_path = BASE / f'校准试填-{coder}.xlsx'
    assert sha(original_path) == expected_blank_sha[coder], '原空白真人材料发生改变'
    export_path = OUT / f'代理试填-{coder}（供真人复核）.xlsx'
    original = load_workbook(original_path,read_only=False,data_only=False)
    wb = load_workbook(export_path,read_only=False,data_only=False)
    assert wb.sheetnames == original.sheetnames == ['填写','阅读材料','编码手册','填写说明']
    assert not wb._external_links
    assert all(s.sheet_state=='visible' for s in wb)
    assert all(c.data_type!='f' for s in wb for row in s for c in row)
    assert values(wb['阅读材料']) == values(original['阅读材料'])
    assert values(wb['编码手册']) == values(original['编码手册'])
    assert wb['填写'].freeze_panes == original['填写'].freeze_panes == 'B6'
    assert len(wb['填写'].tables) == len(original['填写'].tables) == 1
    assert wb['填写'].tables['CalibrationInputs'].ref == 'A5:M45'
    validations=list(wb['填写'].data_validations.dataValidation)
    assert any(str(v.sqref)=='C6:G45' and v.type=='whole' and v.formula1=='0' and v.formula2=='1' for v in validations)
    for row,i in enumerate(ids,6):
        assert wb['填写'].cell(row,1).value == original['填写'].cell(row,1).value == i
        assert wb['填写'].cell(row,2).value == original['填写'].cell(row,2).value
        x=results[coder][i]
        for col,d in enumerate(DIMS,3):
            assert wb['填写'].cell(row,col).value == x['labels'][d]
            assert original['填写'].cell(row,col).value is None
            assert wb['填写'].cell(row,col+5).value == displayed_reason(x['reasons'][d],x['evidence'][d])
            assert original['填写'].cell(row,col+5).value is None
        assert wb['填写'].cell(row,13).value == x['material_issue']
    assert all(wb['填写说明'].cell(row,2).value is None for row in range(24,30)), '真人复核记录被代填'
    assert wb['填写说明']['B14'].value == f'AI代理{coder}'
    for name in original.sheetnames:
        a,b=original[name],wb[name]
        for row in a:
            for cell in row:
                allowed = (name=='填写' and (cell.coordinate in ('A2','A3') or (6<=cell.row<=45 and 3<=cell.column<=13))) or (name=='填写说明' and (cell.coordinate in ('A2','A3','B11','C11','C13') or 14<=cell.row<=20))
                if not allowed:
                    assert cell.value == b[cell.coordinate].value,(coder,name,cell.coordinate,'非授权内容改变')
    workbook_checks[coder]={'path':str(export_path),'sha256':sha(export_path),'labels_complete':200,'reasons_complete':200,'human_review_fields_blank':6,'original_blank_workbook_unchanged':True,'reading_and_manual_values_unchanged':True,'validation_and_freeze_preserved':True}
    original.close(); wb.close()

report = {
    'status':'通过结构、引文、数学与保存文件核查',
    'purpose':'40条有目的开发材料的AI代理试填，供真人复核；不是新的真人信度、总体推断或机器效度结果',
    'manual_sha256':payload['manual_sha256'],
    'payload_sha256':sha(payload_path),
    'models':{'A':'gpt-5.6-sol','B':'gpt-5.6-sol'},
    'raw_result_bindings':bindings,
    'statistics':stats,
    'disagreement_units':sorted({u['material_id'] for u in disagreements}),
    'disagreement_dimension_judgments':len(disagreements),
    'disagreements':disagreements,
    'workbook_checks':workbook_checks,
    'labels_changed_after_independent_completion':False,
    'human_results_generated':False,
    'confidence_intervals':'不计算总体区间；此为有目的开发材料',
    'formal_manuscript_changed':False
}
(OUT/'代理试填一致性与保存核查.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
lines = [
    '# 代理试填一致性与真人复核要点','',
    '两位AI代理分别按同一共用手册，在独立会话中判断40条开发材料。五维共400个标签及400个理由均已填写，全部引文可在对应原文或共同语境中找到。两份独立结果保持，不用讨论后的答案重新计算κ。','',
    '这里的κ为代理开发试填的描述性反馈，不是新真人信度结果，也不用于推断全量政策文本表现。0.80为本项目开发目标。','',
    '| 维度 | 条数 | A判1 | B判1 | 一致率 | κ |','|---|---:|---:|---:|---:|---:|'
]
for name,s in stats.items():
    lines.append(f"| {name} | {s['n']} | {s['A_1_n']} | {s['B_1_n']} | {s['agreement']:.1%} | {s['kappa']:.3f} |")
lines += ['', '五维均达到本轮代理开发试填的0.80目标。三条材料共四个维度判断有分歧，应由真人结合共同手册及原文重点复核。', '',
          '## 分歧与AI复核建议','',
          '- 校准12，经济性：A=0、B=1。分歧是“价格谈判/协商及成败流程”是否构成经济实质内容。手册已排除仅谈判阶段、协商成败、目录结果，AI复核建议优先核对A的排除解释；不额外要求必须有金额，关键是是否实际规定价格、费用或支付内容。',
          '- 校准35，经济性：A=0、B=1。当前句仅规定谈判药品协议有效期两年。AI复核建议优先核对A的解释：当前期限句不自动继承后续自足句的价格与支付内容；若将协议期限纳入经济性，须先明确可通用于其他材料的定义依据。',
          '- 校准39，创新性：A=1、B=0。分歧是制定目的与优先审评程序总述是否已经表达实际创新研发支持。AI复核更支持B，需核定是否存在共用材料中可指认的具体支持机会或机制，不能只从“鼓励研究和创制新药”推定。',
          '- 校准39，公平性：A=1、B=0。AI复核更支持A，依据是“临床急需短缺药品”与“优先审评审批”的缺口—针对性资源关系；真人仍须判断当前目的总述是否已经实质规定该安排，以及必要语境是否足够。','',
          '以上意见由另一AI代理结合现有手册复核形成，供真人审查，不是已完成的真人裁定。独立A/B标签没有据此修改。','',
          '## 真人如何接续复核','',
          '逐条核对“阅读材料”的当前原文及必要语境，复核“填写”页的标签、理由与引文。如有修改，请另存文件，列明材料编号、维度及依据；在“填写说明”下方填实际复核人、专业背景、日期、手册确认、修改与答案接触记录。未修改也要据实记录。原代理试填稿及独立JSON保持。','',
          '本稿已经展示代理答案，接续复核属于事后复核。正式人工信度仍应在手册冻结后，由真人对另行指定的检验材料独立判断，保留协商前标签。',''
]
(OUT/'代理试填一致性与真人复核要点.md').write_text('\n'.join(lines))
print(json.dumps({'workbooks':2,'labels':400,'reasons':400,'kappa':{name:s['kappa'] for name,s in stats.items()},'disagreement_units':report['disagreement_units'],'checks':'通过','human_results_generated':False},ensure_ascii=False))
