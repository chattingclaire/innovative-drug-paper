"""Clarify validation versus full-corpus attention without changing results."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
import hashlib, json, re, shutil
from lxml import etree as E

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
OUT = WORK / '本轮结果'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p): return {'path': str(Path(p).resolve()), 'sha256': sha(p)}
def plain(p): return ''.join(p.xpath('.//w:t/text()', namespaces=NS))

main = OUT / '创新药评价的注意力配置差异与协调路径.docx'
memo = OUT / '编码复核说明与真人检验事项.docx'
assert sha(main) == '9f817ee2cec4c1696fc2e0b724eea49670e48190911943fe1cfb3b9ed7561489'
assert sha(memo) == '441b742713b1f7abc6b3ae2272a413949d9779ad94122e9807c0335c44e2f874'
archive = HERE / '澄清人工验证用途前记录'
archive.mkdir(exist_ok=False)
for p in [main, memo, OUT / '创新药评价的注意力配置差异与协调路径.pdf',
          OUT / '编码复核说明与真人检验事项.pdf', OUT / '采用文件说明.txt',
          OUT / '后续验证怎么做.md', HERE / '当前采用稿交付封存.json']:
    shutil.copy2(p, archive / p.name)

changes = {}
def edit(path, updates):
    with ZipFile(path) as z:
        parts = {i.filename: (i, z.read(i.filename)) for i in z.infolist()}
    t = E.fromstring(parts['word/document.xml'][1])
    ps = t.findall('w:body/w:p', NS)
    cite = next(deepcopy(r) for r in t.xpath('.//w:rPr[w:vertAlign[@w:val="superscript"]]', namespaces=NS)) if path == main else None
    before_refs = [plain(p) for p in ps if re.match(r'^\[\d+\]', plain(p))]
    before_cites = re.findall(r'\[\d+(?:,\d+)*\]', '\n'.join(plain(p) for p in ps))
    changes[path.name] = []
    for i, new in updates.items():
        p = ps[i]
        old = plain(p)
        assert old != new
        pr = deepcopy(p.find('w:r/w:rPr', NS))
        changes[path.name].append({'paragraph_index': i, 'old': old, 'new': new})
        for x in list(p):
            if x.tag != W + 'pPr': p.remove(x)
        for s in re.split(r'(\[\d+(?:,\d+)*\])', new):
            if not s: continue
            r = E.SubElement(p, W + 'r')
            rp = cite if re.fullmatch(r'\[\d+(?:,\d+)*\]', s) else pr
            if rp is not None: r.append(deepcopy(rp))
            E.SubElement(r, W + 't').text = s
    assert before_refs == [plain(p) for p in ps if re.match(r'^\[\d+\]', plain(p))]
    assert before_cites == re.findall(r'\[\d+(?:,\d+)*\]', '\n'.join(plain(p) for p in ps))
    xml = E.tostring(t, xml_declaration=True, encoding='UTF-8', standalone=True)
    tmp = path.with_suffix('.clarification.docx')
    assert not tmp.exists()
    with ZipFile(tmp, 'x', compression=ZIP_DEFLATED) as z:
        for name, (info, data) in parts.items():
            z.writestr(info, xml if name == 'word/document.xml' else data)
    tmp.replace(path)

with ZipFile(main) as z: main_tree = E.fromstring(z.read('word/document.xml'))
ps = main_tree.findall('w:body/w:p', NS)
edit(main, {
    51: plain(ps[51]).replace('本文将0.80作为逐维编码检查目标，并结合四格、区间及原句核查解释方法差异。',
        '本文将0.80作为开发阶段逐维编码检查的诊断目标，结合四格、区间及原句核查解释方法差异。'),
    57: '180条概率样本用于编码质量检验，同样本注意力分布用于辅助诊断方法差异。样本内按逆入样概率先估计各维编码句次，再除以五维估计句次合计[49]，推断范围为上述剩余规范代表框。全量4481条的部门分布依据两种机器方法的完整编码结果分别计算。内容覆盖比例、注意力占比和维度间的条件比例按第3.3节定义计算。',
    110: plain(ps[110]).replace('编码员A、编码员B的独立编码结果、复核参照及原文依据',
        '编码员A、编码员B的初判、人工审定结果及原文依据')
})
edit(memo, {
    8: 'A、B主要作为抽样句段五维编码的人工审定参照，机器检验报告κ、精确率、召回率、F1、四格与区间。同样本注意力分布与关键条件比例用于辅助检查误差影响，不要求人工样本占比与机器全量占比相同。全文注意力配置由两种机器方法对同一全语料的完整编码结果分别计算；两种机器分布接近也不能取代编码质量验证。'
})

guide = OUT / '后续验证怎么做.md'
txt = guide.read_text()
old = '3. 检查误差对论文结论的影响。在同样本、同一权重与同一分母下，核对五维注意力占比的部门差值、最高维度及关键条件比例。'
new = '3. 辅助检查误差对论文结论的影响。A/B的主要任务是抽样编码质量检验，全文注意力配置由两种机器方法的全量编码分别计算，不要求人工样本占比等于机器全量占比。在同样本、同一权重与各方法统一定义的分母下，可核对五维注意力占比的部门差值、最高维度及关键条件比例。'
assert txt.count(old) == 1
guide.write_text(txt.replace(old, new))
record = {
    'status': 'ROLE_CLARIFICATION_APPLIED_NUMERICAL_RESULTS_UNCHANGED_RENDER_AND_INDEPENDENT_QA_PENDING',
    'only_main_paragraphs_changed': [51, 57, 110], 'only_memo_paragraphs_changed': [8],
    'project_0_80_diagnostic_target_retained': True,
    'AB_human_adjudication_accepted_and_labels_unchanged': True,
    'coding_outputs_statistics_tables_figures_references_unchanged': True,
    'changes': changes, 'current_documents': [bind(main), bind(memo)],
    'previous_documents_preserved': [bind(archive / main.name), bind(archive / memo.name)],
    'guide': bind(guide), 'entrypoint': bind(Path(__file__))
}
(HERE / '人工验证用途澄清记录.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(record['current_documents'], ensure_ascii=False))
