from pathlib import Path
from zipfile import ZipFile
from copy import deepcopy
from lxml import etree as E
import json, re, hashlib

BASE = Path('/PROJECT_ROOT')
M = BASE / 'outputs/goal-calibration-20261010/08-manuscript'
OC = M / 'original-continuation'
OUT = M / 'submission-20261013'
WORK = OUT / '_work'
SOURCE = OC / '创新药评价的注意力配置差异与协调路径-原稿格式修订.docx'
TARGET = OUT / '创新药评价的注意力配置差异与协调路径-交稿版.docx'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == 'e769e3b3dd753328637dcd4c1d2c81d8f65b1f16ce96524533af90e0dbaf1780'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def W(n): return '{'+NS['w']+'}'+n
def txt(n): return ''.join(n.xpath('.//w:t/text()', namespaces=NS))
def norm(s): return s.replace('\u2060','')
with ZipFile(SOURCE) as z:
    infos=z.infolist(); package={i.filename:z.read(i.filename) for i in infos}
root=E.fromstring(package['word/document.xml']); body=root.find('w:body',NS)
ps=body.findall('w:p',NS); tables=body.findall('w:tbl',NS)
assert len(ps)==181 and len(tables)==4
original=[txt(p) for p in ps]; original_xml=[E.tostring(p) for p in ps]
changes=[]

def props(parent, name):
    n=parent.find('w:'+name,NS)
    if n is None: n=E.SubElement(parent,W(name))
    return n

def setval(parent,name,value): props(parent,name).set(W('val'),str(value))

def set_text(p, value, cite=True):
    rp=None
    for r in p.findall('w:r',NS):
        pr=r.find('w:rPr',NS)
        if pr is not None and pr.find('w:vertAlign',NS) is None:
            rp=deepcopy(pr); break
    if rp is None: rp=E.Element(W('rPr'))
    for n in rp.findall('w:vertAlign',NS): rp.remove(n)
    for child in list(p):
        if child.tag != W('pPr'): p.remove(child)
    parts=re.split(r'(\[\d+(?:[-,]\d+)*\])',norm(value)) if cite else [value]
    for s in parts:
        if not s: continue
        run=E.SubElement(p,W('r')); rpr=deepcopy(rp); run.append(rpr)
        if cite and re.fullmatch(r'\[\d+(?:[-,]\d+)*\]',s):
            setval(rpr,'vertAlign','superscript')
        t=E.SubElement(run,W('t')); t.text=('\u2060'+s) if cite and re.fullmatch(r'\[\d+(?:[-,]\d+)*\]',s) else s
        if s.startswith(' ') or s.endswith(' '):t.set('{http://www.w3.org/XML/1998/namespace}space','preserve')

def replace_p(i,value):
    before=txt(ps[i-1]); set_text(ps[i-1],value)
    changes.append({'paragraph':i,'before':before,'after':value})

def replace_span(i, old, new):
    before=norm(txt(ps[i-1])); old=norm(old)
    assert before.count(old)==1,(i,old,before)
    replace_p(i,before.replace(old,norm(new)))

prep=(OC/'stability-local-insertion-preparation.md').read_text()
for i in [2,7,67,72,73,74,76,77,81,83,103,106]:
    section=re.search(r'### P%03d｜.*?(?=\n### |\n## |\Z)'%i,prep,re.S).group()
    old=re.search(r'原句：\s*\n> (.*?)\n\n拟替换句：',section,re.S).group(1)
    new=re.search(r'拟替换句：\s*\n(.*?)\n\n整合注',section,re.S).group(1)
    replace_span(i,old,new)

method=json.loads((WORK/'methods-replacements.json').read_text())['replacements']
method['P048']=method['P048'].replace('五维分别作0/1判断，','五维分别作0/1判断，信息不足者保留待定；').replace('自动规则编码的全量结果用于主描述，LLM编码作平行测量；','两种编码方法的全量结果并列报告，以共同方向识别部门配置差异，分歧结合人工核验与政策语境解释；')
method['P051']=method['P051'].replace('总体和各部门按维度报告四格、参照正类比例及上述指标；','按维度报告总体四格及分类指标；')
method['P052']=method['P052'].replace('本文以0.80作为逐维编码检查的诊断目标','本文以0.80作为开发阶段逐维编码检查的诊断目标')
method['P055']=method['P055'].replace('原始与加权四格、参照正类比例、观察一致率、待定数量及近似95%区间见配套《编码检验补充统计表》。','原始四格、待定数量、原始κ与F1及加权指标的近似95%区间见附录C。')
method['P058']=method['P058'].replace('所得分布对应1151条抽样框。','所得分布对应1151条抽样框，见附录C。')
for key,value in method.items(): replace_p(int(key[1:]),value)
replace_span(39,'符合该维定义记为1，否则记为0','符合该维定义记为1，不符合记为0；信息不足而无法判断时保留待定')
replace_span(40,'维度间的条件比例为同时涉及两维的单元数除以作为条件的该维单元数','维度间的条件比例仅在相关两维均可判定的单元中计算，为同时涉及两维的单元数除以作为条件的该维单元数')
replace_span(40,'文件构成和操作定义边界变化用于检验比较的适用范围。','来源构成、汇总方式和待定信息的变化用于检验比较的适用范围。')
# DOI and article number are assigned by the journal, not author-entered placeholders.
replace_span(4,'　　文章编号：','')
body.remove(ps[4])

def set_cell(cell,value):
    p=cell.find('w:p',NS); assert p is not None
    set_text(p,str(value),cite=False)
    for q in list(cell.findall('w:p',NS))[1:]:cell.remove(q)

compact=json.loads((WORK/'validation/table2-compact.json').read_text())
comparison=json.loads((WORK/'validation/comparison.json').read_text())
lookup={(r['dimension'],r['method']):r for r in compact['rows']}
dim_names={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
ordered=[lookup[(d,m)] for d in dim_names for m in ['rule','LLM']]
main_data=[['维度','编码方法','κ','P','R','F1']]
for r in ordered:
    main_data.append([r['name'],'自动规则编码' if r['method']=='rule' else 'LLM编码']+[f"{r['weighted'][k]:.3f}" for k in ['kappa','Precision','Recall','F1']])
for row,values in zip(tables[1].findall('w:tr',NS),main_data):
    cells=row.findall('w:tc',NS);assert len(cells)==6
    for cell,value in zip(cells,values):set_cell(cell,value)

t3=json.loads((OC/'current-result-assets/table3-preparation.json').read_text())
for patch in t3['numeric_cell_patches']:
    cell=tables[2].findall('w:tr',NS)[patch['row_1based']-1].findall('w:tc',NS)[patch['cell_1based']-1]
    assert txt(cell)==patch['old_text'];set_cell(cell,patch['new_text'])
for p in t3['paragraph_patches']:replace_p(p['paragraph_index_1based'],p['new_text'])
found=0
for cell in tables[3].findall('.//w:tc',NS):
    if '目录保障短板、管理难度及供应支付渠道' in txt(cell):
        set_cell(cell,txt(cell).replace('目录保障短板、管理难度及供应支付渠道','目录保障短板、患者获取及供应支付条件'));found+=1
assert found==1

image_path=OC/'current-result-assets/figure2-current.png'
assert hashlib.sha256(image_path.read_bytes()).hexdigest()=='48feb92c207515e3cb30a54f4abc1b00e8f4123a0f5e38b8eee4535653005361'
package['word/media/image4.png']=image_path.read_bytes()
inline=root.xpath('.//wp:inline[.//a:blip[@r:embed="rId4"]]',namespaces=NS)[0]
extent=inline.find('wp:extent',NS);cy=str(round(int(extent.get('cx'))*1140/2520));extent.set('cy',cy)
for n in inline.xpath('.//a:xfrm/a:ext',namespaces=NS):n.set('cy',cy)

def new_p(value,template=108,keep=False):
    p=deepcopy(ps[template-1]);set_text(p,value)
    ppr=props(p,'pPr');setval(ppr,'keepNext',int(keep));setval(ppr,'keepLines',0)
    for br in ppr.findall('w:pageBreakBefore',NS):ppr.remove(br)
    return p

stable='在固定800条材料上进行三轮同条件重复，并分别改变输入材料的JSON展示格式和请求首行的等义表述。三轮在五维均可比较的441条共同记录中，有401条五维判断完全一致，原始一致率为90.93%，按原抽样逆概率加权后为90.12%；五维加权注意力份额的极差为0.86—3.50个百分点。各条件的有效覆盖、待定及公平性的配对差异见附录C。'
ps[57].addnext(new_p(stable,48))

def make_table(data,widths):
    table=E.Element(W('tbl')); tpr=deepcopy(tables[1].find('w:tblPr',NS));table.append(tpr)
    grid=E.SubElement(table,W('tblGrid'))
    for w in widths:E.SubElement(grid,W('gridCol')).set(W('w'),str(w))
    for ri,values in enumerate(data):
        assert len(values)==len(widths)
        tr=E.SubElement(table,W('tr'));trpr=E.SubElement(tr,W('trPr'));E.SubElement(trpr,W('cantSplit'))
        if ri==0:E.SubElement(trpr,W('tblHeader'))
        for value,width in zip(values,widths):
            tc=E.SubElement(tr,W('tc'));tcpr=E.SubElement(tc,W('tcPr'))
            tW=E.SubElement(tcpr,W('tcW'));tW.set(W('type'),'dxa');tW.set(W('w'),str(width));setval(tcpr,'vAlign','center')
            borders=E.SubElement(tcpr,W('tcBorders'))
            for edge in ['top','bottom','left','right','insideH','insideV']:
                b=E.SubElement(borders,W(edge));b.set(W('val'),'nil')
                if (ri==0 and edge in ['top','bottom']) or (ri==len(data)-1 and edge=='bottom'):
                    b.set(W('val'),'single');b.set(W('sz'),'4' if ri==0 and edge=='bottom' else '8');b.set(W('color'),'000000')
            p=E.SubElement(tc,W('p'));pp=E.SubElement(p,W('pPr'));setval(pp,'keepNext',int(ri==0 or ri==len(data)-1));setval(pp,'jc','center');setval(pp,'snapToGrid',0)
            sp=props(pp,'spacing');sp.set(W('before'),'0');sp.set(W('after'),'0');sp.set(W('line'),'240');sp.set(W('lineRule'),'auto')
            r=E.SubElement(p,W('r'));rp=E.SubElement(r,W('rPr'));fonts=E.SubElement(rp,W('rFonts'))
            for attr,val in [('ascii','Times New Roman'),('hAnsi','Times New Roman'),('eastAsia','宋体')]:fonts.set(W(attr),val)
            setval(rp,'sz',21);setval(rp,'szCs',21)
            if ri==0:setval(rp,'b',1)
            E.SubElement(r,W('t')).text=str(value)
    return table

appendix=[]
def add_para(s,template=108,keep=False):appendix.append(new_p(s,template,keep))
def caption(cn,en):add_para(cn,53,True);add_para(en,54,True)
add_para('附录C 编码检验与重复稳定性',107,True)
add_para('200条人工核验样本在安全性、有效性、经济性、创新性和公平性上分别有27、13、20、32、16个阳性判断。表C1列出机器判断与人工核验参照的原始对照，抽样权重见附录B。')
caption('表C1 人工核验样本的原始对照','Table C1 Unweighted Comparison with the Human-Reviewed Reference')
c1=[['维度','方法','二元N','待定','TP/FP/FN/TN','κ','F1']]
for r in ordered:c1.append([r['name'],'规则' if r['method']=='rule' else 'LLM',r['N_binary'],r['N_null'],'/'.join(map(str,r['raw_TP_FP_FN_TN'])),f"{r['raw']['kappa']:.3f}",f"{r['raw']['F1']:.3f}"])
appendix.append(make_table(c1,[1250,1100,1000,900,3150,1300,1300]))
add_para('注：TP为两者均判1，FP为机器判1而参照判0，FN为机器判0而参照判1，TN为两者均判0。每行二元N与待定数之和为200，技术失败为0。待定不进入该维度的二元四格；表2为相应设计加权指标。',55)
caption('表C2 设计加权分类指标的近似95%区间','Table C2 Approximate 95% Intervals for Design-Weighted Classification Metrics')
c2=[['维度','方法','κ','P','R','F1']]
for r in ordered:
    intervals=[]
    for k in ['kappa','Precision','Recall','F1']:
        v=r['weighted_CI95'][k]
        intervals.append('—' if v is None else f'{v[0]:.3f}–{v[1]:.3f}')
    c2.append([r['name'],'规则' if r['method']=='rule' else 'LLM']+intervals)
appendix.append(make_table(c2,[1250,950,1950,1950,1950,1950]))
add_para('注：按分层抽样设计进行5000次有限总体校正重抽样，所有方法与维度使用同一组重复权重。“—”表示重抽样分布退化，未据此报告总体指标区间。区间反映固定核验结果下的抽样变化。创新性LLM的κ区间上下限舍入后均为0.936，未舍入值为0.935680与0.935712。',55)
add_para('公平性LLM的原始四格中仅有1项漏判和1项误判。漏判所在层的逆入样概率权重为595/86，误判所在全查层的权重为1，因此加权召回率由原始0.938降为0.684；其近似95%区间为0.429—0.967。这一差异来自分层权重与分歧所在位置。')
caption('表C3 同一样本的加权覆盖比例与注意力占比（%）','Table C3 Design-Weighted Coverage and Attention Shares in the Same Sample (%)')
att=comparison['same_sample_design_weighted_attention']
c3=[['维度','人工p','人工q','规则p','规则q','LLM p','LLM q']]
for d,name in dim_names.items():
    vals=[name]
    for method_name in ['human_confirmed','rule','LLM']:
        rec=att[method_name][d]
        vals += [f"{100*rec[k]:.2f}" for k in ['known_hit_coverage','known_hit_attention_share']]
    c3.append(vals)
appendix.append(make_table(c3,[1300,1450,1450,1450,1450,1450,1450]))
add_para('注：p以1151条抽样框为分母，q以各方法五维已判定阳性的加权合计为分母；两种机器方法的待定维度另行保留。各列不合并为4481条全库的部门分布。',55)
caption('表C4 固定800条材料的重复及请求敏感性覆盖','Table C4 Coverage of Repeated Coding and Request-Sensitivity Checks')
c4=[['条件','计划条数','技术有效','其中待定','技术失败','未调用'],['R1：重复1',800,529,2,271,0],['R2：重复2',800,503,0,297,0],['R3：重复3',800,505,2,295,0],['W：输入格式',800,491,2,309,0],['H：等义措辞',800,540,1,260,0]]
appendix.append(make_table(c4,[2300,1540,1540,1540,1540,1540]))
add_para('注：R1—R3使用相同请求；W改变输入材料的JSON展示格式，H改变请求首行的等义表述。待定数为技术有效记录中至少一维待定的条数，技术失败与未调用不补作0。三轮技术有效交集为443条，排除2条待定后五维共同分母为441条。',55)
add_para('三轮441条共同记录中，401条五维完全一致。安全性、有效性、经济性、创新性和公平性的加权注意力份额极差依次为0.86、1.18、1.36、3.50和3.35个百分点。公平性在R1/R2、R1/R3、R2/R3中的共同二元分母分别为489、467、441，原始κ为0.822、0.872、0.780，按抽样权重计算的κ为0.506、0.872、0.632。')
add_para('W/R1和H/R1的五维共同分母分别为464和501，完全一致记录分别为438和475，加权完全一致率分别为95.80%和94.54%。上述结果对应固定材料及各比较条件的共同有效记录。')
for element in appendix:ps[114].addprevious(element)

# Verify preserved theoretical prose, references, and unaffected package parts.
changed_ids={x['paragraph'] for x in changes}
for i,p in enumerate(ps,1):
    if i not in changed_ids and i!=5:assert E.tostring(p)==original_xml[i-1],i
assert [txt(p) for p in ps[114:]]==original[114:]
assert len(ps[115:])==66
all_text=txt(body)
for old in ['46.53%','57.53%','45.16%','43.33%','20.03%','21.42%','有14项','6种定义','56种','4924','gpt-5.6-sol','60条挑战','180条概率','κ（A/B）']:
    assert old not in all_text,old
assert '{{' not in all_text
package['word/document.xml']=E.tostring(root,encoding='UTF-8',xml_declaration=True,standalone=True)
with ZipFile(TARGET,'w') as z:
    for info in infos:z.writestr(info,package[info.filename])
with ZipFile(SOURCE) as z:
    changed_parts=[name for name in z.namelist() if z.read(name)!=package[name]]
assert set(changed_parts)=={'word/document.xml','word/media/image4.png'}
record={'source':str(SOURCE),'output':str(TARGET),'sha256':hashlib.sha256(TARGET.read_bytes()).hexdigest(),'original_theoretical_paragraphs_preserved':True,'all_66_references_preserved':True,'figure1_preserved':True,'no_machine_reexecution':True,'current200_reference_role':'AI_assisted_human_confirmed','changes':changes,'appendix_tables':4,'visual_review':'pending'}
(WORK/'integration-record.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
(WORK/'submission-text.txt').write_text('\n'.join(txt(el) for el in body))
print(json.dumps({k:v for k,v in record.items() if k!='changes'},ensure_ascii=False))
