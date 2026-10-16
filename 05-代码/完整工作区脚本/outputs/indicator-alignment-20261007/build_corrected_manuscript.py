from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile
from lxml import etree as E
import json, re, hashlib

ROOT = Path(__file__).resolve().parent
BASE = ROOT.parent / 'manuscript-completion-20261006'
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
def W(x): return '{'+NS['w']+'}'+x
def plain(x): return ''.join(x.xpath('.//w:t/text()', namespaces=NS))
def replace(p, text, refs=True):
    pr=p.find('w:pPr',NS); rp=None
    for r in p.findall('w:r',NS):
        q=r.find('w:rPr',NS)
        if q is not None and q.find('w:vertAlign',NS) is None:
            rp=deepcopy(q);break
    for child in list(p):
        if child is not pr:p.remove(child)
    for part in re.split(r'(\[\d+(?:[,–—-]\d+)*\])',text) if refs else [text]:
        if not part:continue
        r=E.SubElement(p,W('r'))
        if rp is not None:r.append(deepcopy(rp))
        if refs and re.fullmatch(r'\[\d+(?:[,–—-]\d+)*\]',part):
            q=r.find('w:rPr',NS)
            if q is None:q=E.SubElement(r,W('rPr'))
            v=E.SubElement(q,W('vertAlign'));v.set(W('val'),'superscript')
        for n,line in enumerate(part.split('\n')):
            if n:E.SubElement(r,W('br'))
            t=E.SubElement(r,W('t'));t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=line
def cellset(c,text):
    ps=c.findall('w:p',NS)
    if not ps:ps=[E.SubElement(c,W('p'))]
    replace(ps[0],text,False)
    for p in ps[1:]:c.remove(p)
def cloned(p,text):
    q=deepcopy(p);replace(q,text);return q
def rowset(row,values):
    cells=row.findall('w:tc',NS)
    assert len(cells)==len(values)
    for c,t in zip(cells,values):cellset(c,str(t))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

stats_path=ROOT.parent/'attention-share-audit-20261007/注意力占比-原定义重算.json'
stats=json.loads(stats_path.read_text())
primary=stats['primary']
groups=['NMPA','NHSA','NHC','GOV','ALL']
names=['药品监管','医保','卫生健康','中央综合','总体']
dims=['S','E','Ec','I','F']
cn=['安全性','有效性','经济性','创新性','公平性']

updates={
1:'摘要：基于2017—2026年55个政策来源条目，结合意义单元编码与专家访谈，考察创新药评价的注意力配置及跨环节衔接。以各维度编码句次占五维编码句次合计的比重衡量注意力占比。抽样参照估计显示，药监来源安全性与有效性合计约77%，医保来源经济性占64%—69%，卫健来源安全性与公平性合计约60%—62%；三者呈现不同的文本关注结构。规则、LLM与参照编码均保留药监安全性、医保经济性占比最高的描述特征。政策条文与访谈进一步表明，同名维度在评价对象、比较方案、证据要求和决策用途上存在差别，注册创新身份、上市获益风险与支付比较价值不能直接换算。协调应明确评价结论的适用条件，推动证据复用、补充研究衔接与评审理由共享。',
6:'Abstract: Drawing on 55 policy source entries from 2017 to 2026, this study combines meaning-unit coding and expert interviews to examine attention allocation and coordination in innovative drug evaluation. Attention share is defined as the coded occurrences of one dimension divided by the total coded occurrences of all five dimensions. Estimates from the sampled reference codings show that safety and efficacy together account for approximately 77% in regulatory sources, economic considerations account for 64–69% in reimbursement sources, and safety and fairness together account for approximately 60–62% in health administration sources. Rule-based, LLM and reference codings retain the descriptive patterns of safety having the largest share in regulatory sources and economic considerations having the largest share in reimbursement sources. Policy provisions and interviews further indicate differences in evaluation objects, comparators, evidence requirements and decision purposes within shared dimensions. Innovation status in registration, benefit–risk assessment for marketing authorization and comparative value for reimbursement cannot be directly converted into one another. Coordination should clarify the conditions under which conclusions apply across stages, support evidence reuse and supplementary studies, and share assessment reasons.',
25:'既有研究讨论政府注意力的测量路径、内容与限度[22]。文宏[23]通过检索政府工作报告中关键词所在句段并计数，测量基本公共服务注意力；练宏[24]强调注意力配置受到组织、制度和社会环境影响。本文将注意力配置差异操作化为不同部门在同一组评价维度之间的相对关注结构差别，以“注意力占比”衡量：某维度编码句次除以该部门五维编码句次合计。同一句段可涉及多个维度，每个维度至多计一次；五维注意力占比合计为100%。这一归一化定义为本文的操作选择，不将其归于上述文献。',
39:'据此，本文以五维注意力占比比较关注结构，结合条文与访谈解释评价内容及决策用途，并报告五项操作定义边界敏感性。四套编码均另检验来源条目和年度系列等权、仅保留年度系列最新成员、剔除联合文本及逐条目剔除的描述性变化；各情景重新计算分子和五维合计。这些检验不替代主分析的抽样区间，也不识别政策效应。',
47:'本文以具有政策含义的句段为分析单元，区分实质内容与标题、目录、来源及辅助语境，修复截断、表格串行和重复提取。冻结语料含4924个分析单元、621个仅供回查的语境单元；后者不独立计数，也不向各单元复制标签。每单元每维至多计一次，可多标签；某维编码为1的句段累计为该维编码句次。注意力占比的分母为同一来源组五维编码句次合计，表示五维框架内部的相对关注分布，合计为100%；五维合计为零时占比无定义，不填0。主分析保留A/C各自首次判读的0、1和待定，按原抽样权重估计已确定编码句次后求比；待定保留并另报补全范围。规则与LLM全量分布另列。某维编码句次除以全部分析单元数仅称“维度内容覆盖比例”，不代替注意力占比，也不与实际评审权重混同。',
49:'本研究将五维编码分别视为二元分类任务，报告A/C协商前一致性，以及规则、LLM相对各参照的分类表现。Cohen’s κ用于扣除边际分布决定的机会一致[39]，同时报告观察一致率及混淆矩阵；参照Kristensen-McLachlan等[40]的报告方式，以精确率、召回率和F1检验编码为1的内容识别，避免多数0类抬高整体一致率。κ≥0.80是本项目后设的开发工作目标，Landis和Koch[41]的解释区间并非统一发表标准。现有A/C为agent首次独立判读，不能作为已完成的真人金标准。',
56:'总体估计沿用既定1268个唯一抽样单元及29层权重：从1531条框按25层抽600条，从3393条补集按四来源组抽668条，各层以总体数/样本数加权。先估计每维编码为1的句次，再除以五维估计句次合计（表3）；总体先合并四组句次后求比，不平均各组占比。A/C分别估计，H427不并入总体估计。各层计数界采用有限总体超几何检验反演[44]；两位参照、五维、29层及确定编码和确定编码加待定两端点形成固定580项家族，以Bonferroni原理[45]获得至少95%的同时覆盖计数区域。在该区域上分别以本维下界、其他维上界求占比下界，以本维上界、其他维下界求上界，再求组间差值界。允许待定任意补全后，只有A/C均在同方向严格排除零，才记共同支持的方向（表4）。该保守变换为本研究构造；原计数区域保留，固定单元数比例的区间不能直接用于注意力占比。',
57:'表3 各来源组五维注意力占比估计',
58:'Table 3 Estimated Attention Shares across Five Dimensions by Source Group',
59:'注：五维占比单位为%；各行分母为“五维加权编码句次”，每行五维合计为100%，独立四舍五入可能产生0.01—0.02个百分点的合计误差。药监、医保、卫健、中央综合的总体单元数分别为1848、2100、533、443，抽样数分别为436、394、227、211。A/C使用同一1268条样本，按原29层权重分别估计，不合并为双倍样本。表中为已确定编码的比率点估计，待定补全范围与变换后的同时界另存；A/C数值差异不是置信区间。综合政策不代表单一部门。资料来源：冻结语料及两位agent首次独立判读。',
65:'表3呈现各部门在五维框架内部的注意力占比分布。药监来源安全性为45.71%和46.65%，有效性为30.93%和30.04%，两维合计约77%；医保来源经济性为69.40%和64.01%；卫健来源安全性为28.89%和28.24%，公平性为30.77%和34.04%，两维合计约60%—62%（依次为A、C）。这些是两份参照的分别估计，数值范围不是置信区间。按新比率从同时计数区域重新推导后，60项单参照部门比较在确定编码及允许待定补全两种处理中均未严格排除零，30项比较亦无共同支持方向（表4）。因此可描述当前文本的关注结构，不能将点估计推广为统计上确定的部门排序或实际赋权。图2展示完整五维分布。',
66:'表4 注意力占比部门比较的同时区间结果汇总',
67:'Table 4 Simultaneous Interval Results for Between-Group Comparisons of Attention Shares',
68:'注：每维包括四来源组之间6个预定比较，单元格为差值界严格排除零的比较数。“确定编码”比较各维已确定编码句次构成的占比；“含待定”允许各维待定任意补全为0或1，分子与五维合计同步变化；“共同方向”要求A、C的后一类差值界在同方向排除零。两类界均由固定580项同时计数区域变换得到，未沿用固定单元数比例的区间。全部60项单参照比较及30项共同判断见配套统计。零共同方向不等于组间没有差异。',
70:'图2 四来源组五维注意力占比分布',
71:'Figure 2 Distribution of Attention Shares across Five Dimensions in Four Source Groups',
72:'注：每条堆叠柱为一位参照在一个来源组的五维注意力占比，分母为该组五维加权编码句次合计，柱长均为100%。A/C为agent首次独立参照；图示为已确定编码的点估计，未把待定记作0类判定，未将两位参照的数值范围当作置信区间。同时区间的部门比较见表4，待定补全范围与完整同时界见配套统计。资料来源：表3对应的原权重重算结果。',
73:'医保来源创新性注意力占比在A/C下为7.31%和7.51%，高于安全性的3.40%和3.49%、有效性的1.82%和1.61%。该描述限于本文的编码句次分布，不说明创新性在实际评审中获得更高权重。经济性在四套编码中均为医保来源占比最高的维度，与价格、费用、支付及基金使用内容较多相对应；这一联系仍需结合文本范围和操作定义解释，不能仅凭比例确定实际决策中各维的重要性。',
74:'A/C的五项定义边界敏感性均按注意力占比重新计算：排除仅质量安全、仅创新资格比较优势、仅临床管理、仅未细分公平信息要求，或仅保留保障获取与可负担依据时，被调整维度的句次及五维合计同时变化，其他维度占比也随之变化。五项情景均未反转三专业部门15项同维度跨部门点估计方向；药监安全性、医保经济性占比最高的特征保留。这是口径敏感性描述，不是新增显著性检验。卫健的五维分布只表示所选框架内部的相对关注，不能据此覆盖其全部评价活动。',
76:'表5给出两条机器方法在全量语料中的五维注意力占比。药监来源安全性在当前规则与旧LLM中分别为48.63%和44.41%，有效性为33.89%和30.94%；医保来源经济性为62.94%和51.90%，均为各自组内最高维度。卫健来源安全性与公平性在规则中同为30.07%，旧LLM中分别为35.32%和31.65%，A/C则为公平性略高；其组内次序不宜强行统一。两条机器方法在三专业部门15项同维度跨部门比较中有14项点估计方向一致，允许旧LLM待定任意补全后仍为14项。例外是公平性：规则为医保21.75%低于卫健30.07%，旧LLM为医保34.51%高于卫健31.65%。这些是固定语料的描述，不能替代A/C主分析的同时比较。',
77:'表5 自动规则与LLM全量编码的五维注意力占比',
78:'Table 5 Attention Shares across Five Dimensions from Full-Corpus Rule-Based and LLM Coding',
79:'注：五维占比单位为%；每行分母为“五维编码句次”，每行五维合计为100%，独立四舍五入可能产生0.01—0.02个百分点的合计误差。规则为v28.2，LLM为此前gpt-5.6-sol封存结果，并非v29重跑。两者对应同一4924条分析单元；规则待定为0，旧LLM仍有49条五维待定，表内用已确定编码句次求比，逐维待定补全范围另报，不将待定改判为0。总体合并四组句次后求比。数据描述固定语料，版本与上下文差异见4.1节；不沿用抽样主分析的区间。',
80:'四套编码的五项定义边界情景均重新归一化，三专业部门15项跨部门点估计方向均未反转；旧LLM有3条公平性编码为1但缺子类型，相关情景转为待定而不改判为0。来源条目等权、年度系列等权及仅保留最新年度成员均未反转这15项方向；剔除联合文本时，规则的医保—卫健创新性出现1项反转，旧LLM的创新性和公平性出现2项反转，A/C未反转。逐条目剔除中，规则无方向反转，旧LLM有3次，A/C各有1次，后两者均涉及药监—医保创新性。药监安全性、医保经济性组内占比最高的特征在上述情景中保留；卫健安全性与公平性的先后随部分口径变化。条目等权对零编码句次不填0；A/C实际覆盖54个条目，补充情景仅作描述性敏感性。',
104:'本文结合政策文本编码与专家访谈，比较创新药评价的注意力分布与决策用途。按五维编码句次归一化的抽样参照估计，药监来源安全性与有效性合计约77%，医保来源经济性占64%—69%，卫健来源安全性与公平性合计约60%—62%。药监安全性、医保经济性占比最高的描述特征在规则、LLM与参照编码及所检验的敏感性情景中保留；卫健安全性与公平性的相对次序不稳定。政策条文进一步表明，注册创新身份、上市获益风险与支付比较价值分别服务于不同决策，同名维度的参照对象和证据要求也存在差别。创新药评价的协调应明确结论的适用条件，将目标人群、比较方案、证据要求与不确定性纳入结论对照，推动证据复用、补充研究衔接和评审理由共享。上述占比描述纳入文本的关注结构，不能直接换算为实际评审权重。',
105:'本文将注意力配置的比较区分为两个层面：一是以五维编码句次合计为分母的注意力占比，描述既定框架内的相对关注结构；二是同一维度所指向的评价内容与决策用途，用于理解评价结论跨环节使用的条件。将二者结合，有助于区分共同关注、判断条件差异与测量框架的覆盖限制，避免从注意力占比直接推断部门偏好或协调障碍。相应的实践建议是明确评价结论的适用范围，加强证据衔接和评审理由共享。',
106:'本研究的测量限于纳入公开文本的五维注意力分布，不代表个人认知或实际评审权重；文件体裁、年度材料及来源归属可能影响占比。五维框架对其他评价环节存在覆盖限制，框架内占比低不等于该部门不重视。变换后的保守同时界未形成跨部门共同支持方向，描述性结构不能代替显著性结论。两份访谈提供解释线索，不能代表部门统一立场或验证句段标签，药监环节也缺少一对一访谈。当前A/C为agent参照，规则改善及其区间属于已接触材料的开发复核；独立真人验证尚待实施。旧LLM尚未完成修订重跑，底层revision和temperature不可得，片内上下文与模板理由也限制复现。相关不确定性不由较高κ消除。',
110:'操作定义边界。五项情景分别排除仅质量安全、仅创新资格比较优势、仅临床管理、仅未细分公平信息要求，或仅保留保障获取及可负担；混合独立依据保留。原A/C与当前规则、旧LLM分别按自身子类型计算；每次先调整计数，再以新的五维合计求注意力占比，不沿用固定单元数比例的变动幅度。旧LLM的3条F编码为1但缺子类型，相关情景转待定而不填0。全部情景的计数、待定范围和点估计方向分别保存。',
122:'范围与去重。纯药品清单、临床用药手册、DRG／DIP分组规范、年度药品审评报告及无实质评价内容的结果公告不纳入。公告所附方案、指南和规则按实质内容判断，不因公告仅列附件而漏收正文。官方问答与政策正文分别标记；同一附件重复发布时记录发布关系，不重复追加全文。四套编码均已按五维编码句次分母重算条目等权、年度系列、排除联合文本及逐条目剔除；未另行检验排除官方问答。A/C仍用原权重，其条目层面有1个药监来源无抽中单元；文件等权仅对可得且五维确定编码句次大于零的条目求均值，零句次及仅待定条目另列，不对缺失占比填0。来源组分布仍须结合材料构成解释。',
}

src=BASE/'论文完整修订稿-待补真人验证.docx'
dst=ROOT/'论文修订稿-指标统一版-待补真人验证.docx'
with ZipFile(src) as z:
    parts={i.filename:z.read(i.filename) for i in z.infolist()}
doc=E.fromstring(parts['word/document.xml']);body=doc.find('w:body',NS)
ps=body.findall('w:p',NS);ts=body.findall('w:tbl',NS)
assert len(ps)==175 and len(ts)==6
changes=[]
for i,text in updates.items():
    if i == 76:
        text=text.replace('医保来源经济性为62.94%和51.90%，均为各自组内最高维度。','医保来源经济性为62.94%和51.90%。两种方法中，药监均以安全性、医保均以经济性占比最高。')
    changes.append({'paragraph_index_before':i,'before':plain(ps[i]),'after':text})
    replace(ps[i],text)
# Terminology in remaining diagnostic prose: the binary target is explicitly defined.
for i in [50,54]:
    text=plain(ps[i]).replace('阳性比例','编码为1的比例').replace('阳性判定边界','编码为1的判定边界')
    replace(ps[i],text)
# Classification precedes DOI in the journal's current template.
body.remove(ps[4]);ps[3].addprevious(ps[4])

table3=[['来源组','参照','五维加权\n编码句次']+cn]
for g,n in zip(groups,names):
    for coder in ['A','C']:
        r=primary[coder+'_AI_reference'][g]
        table3.append([n,coder,f"{r['weighted_five_dimension_known_hit_sum']['value']:.2f}"]+
                      [f"{r['dimensions'][d]['attention_share']['value']*100:.2f}" for d in dims])
assert len(ts[2].findall('w:tr',NS))==len(table3)
for row,vals in zip(ts[2].findall('w:tr',NS),table3):rowset(row,vals)
table4=[['维度','A确定\n编码','C确定\n编码','A含\n待定','C含\n待定','共同\n方向']]+[[n,'0','0','0','0','0'] for n in cn]
for row,vals in zip(ts[3].findall('w:tr',NS),table4):rowset(row,vals)
table5=[['来源组','方法','五维\n编码句次']+cn]
for g,n in zip(groups,names):
    for method,label in [('rules_v28_2','规则v28.2'),('llm_gpt56_sol_v13_original','旧LLM')]:
        r=primary[method][g]
        table5.append([n,label,f"{r['weighted_five_dimension_known_hit_sum']['value']:.0f}"]+
                      [f"{r['dimensions'][d]['attention_share']['value']*100:.2f}" for d in dims])
for row,vals in zip(ts[4].findall('w:tr',NS),table5):rowset(row,vals)

# Restore source-derived three-line table borders hidden by cell-level nil overrides.
for ti in [1,4,5]:
    rows=ts[ti].findall('w:tr',NS)
    for row,edge,size in [(rows[0],'top','8'),(rows[-1],'bottom','8'),(rows[0],'bottom','4')]:
        for cell in row.findall('w:tc',NS):
            cp=cell.find('w:tcPr',NS)
            if cp is None:cp=E.SubElement(cell,W('tcPr'))
            borders=cp.find('w:tcBorders',NS)
            if borders is None:borders=E.SubElement(cp,W('tcBorders'))
            line=borders.find('w:'+edge,NS)
            if line is None:line=E.SubElement(borders,W(edge))
            line.set(W('val'),'single');line.set(W('sz'),size);line.set(W('color'),'000000')

# Keep all five kappa rows together; a single fairness row must not be isolated.
for ri,row in enumerate(ts[5].findall('w:tr',NS)):
    for p in row.xpath('.//w:p',namespaces=NS):
        pr=p.find('w:pPr',NS)
        if pr is None:pr=E.SubElement(p,W('pPr'))
        kn=pr.find('w:keepNext',NS)
        if kn is None:kn=E.SubElement(pr,W('keepNext'))
        kn.set(W('val'),'1' if ri<5 else '0')
for p in [ps[117],ps[118]]:
    pr=p.find('w:pPr',NS)
    if pr is None:pr=E.SubElement(p,W('pPr'))
    kn=pr.find('w:keepNext',NS)
    if kn is None:kn=E.SubElement(pr,W('keepNext'))
    kn.set(W('val'),'1')

# Add the ratio-bound construction as a compact, source-derived appendix paragraph.
tech='A5 注意力占比的不确定性。设某组各维已确定编码句次为c，待定句次为p，则维度d的描述性补全下界为本维c除以“本维c加其他维(c+p)合计”，上界为本维(c+p)除以“本维(c+p)加其他维c合计”；该范围不是置信区间。对抽样误差，先由原580项同时计数区域合并各层得到每维下界L与上界U，待定处理时U取确定编码加待定的计数上界。注意力占比下界为本维L除以“本维L加其他维U合计”，上界为本维U除以“本维U加其他维L合计”。本语料各组下界合计均大于零；组间差值取一组占比下界减另一组上界及反向组合。该变换保留原覆盖事件的保证，但较保守，不涵盖共同误判或构念效度问题。'
ps[120].addprevious(cloned(ps[112],tech))
parts['word/document.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
parts['word/media/image4.png']=(ROOT/'图2-五维注意力占比分布.png').read_bytes()
# Clear inherited stale counts; the renderer will supply actual pagination separately.
if 'docProps/app.xml' in parts:
    app=E.fromstring(parts['docProps/app.xml'])
    for x in list(app):
        if E.QName(x).localname in ['Pages','Words','Characters','CharactersWithSpaces','Paragraphs','Lines']:app.remove(x)
    parts['docProps/app.xml']=E.tostring(app,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(src) as z, ZipFile(dst,'w') as out:
    for info in z.infolist():out.writestr(info,parts[info.filename])

# Update the existing separate pending-items document without claiming human execution.
msrc=BASE/'待确认事项.docx';mdst=ROOT/'待确认事项-指标统一版.docx'
with ZipFile(msrc) as z:mparts={i.filename:z.read(i.filename) for i in z.infolist()}
mdoc=E.fromstring(mparts['word/document.xml']);mb=mdoc.find('w:body',NS);mps=mb.findall('w:p',NS)
memo_updates={
1:'截至2026年10月7日，正文已恢复原定义：注意力占比为某维度编码句次除以同组五维编码句次合计，五维合计100%。固定单元数分母的内容覆盖比例不作主指标。表3—5、图2、区间及敏感性均已重算，摘要至结论已同步；原标签、权重和κ不变。旧LLM尚未修订重跑，真人验证尚未实施。',
4:'A/C估计中，药监安全性与有效性合计约77%，医保经济性占64%—69%，卫健安全性与公平性合计约60%—62%，范围不是置信区间。药监安全性、医保经济性占比最高的特征在四套编码及敏感性中保留；卫健两维次序不稳定。30项跨部门比较无同时界共同支持方向，不宜推广为确定排序。文本占比不等于实际赋权，条文与访谈另支持区分注册创新身份、上市获益风险及支付比较价值的用途。',
9:'四套编码已完成五项定义边界、条目与系列等权、年度最新成员、排除联合文本及逐条目剔除，均重算五维合计。图2改为100%堆叠图，图1保留。两机器同向比较改为14/15，例外是医保—卫健公平性。A/C抽中54个条目，零句次及仅待定条目另列。旧标签、权重、模型版本和开发材料地位保持原记录。',
11:'已核验新官网https://www.qkkxjc.cn/及2026年投稿格式：9000—15000字为宜，中文摘要约300字、关键词3—8个、双向匿名。本版分类号置于DOI前，作者单位待补。全文LibreOffice统计约1.85万字，含前置、附录及参考文献，图中文字未另计；须确认期刊计入范围，不能声称篇幅已全部合规。其他格式差异见期刊核验报告。',
12:'文献存在、著录与支持范围分别核对，经典理论不直接证明本文的部门因果关系。κ、精确率、召回率、F1、bootstrap、有限总体计数界及同时覆盖各有依据；五维归一化、580项家族及其比率变换是本文操作选择。描述性待定补全范围不是置信区间，完整核验与未确认项另存。',
13:'原45条存在及核心著录可确认，44条已取得发表原文、出版社信息或原始记录。原[22]全文未取得，仅作背景，句段计数由已读原[23]支撑；原[36]只作词典例证。新增6条方法文献已核对，编号对照另存。未发现编造，不代表每句论述均获全文证实。',
14:'原45条中32篇期刊论文涉及25种刊，未命中已取得的2025及历史2023官方预警名单；年度名单不能累积合并。投稿前仍须核对2026更新与编辑部适用口径，本项不等于全量撤稿检索。',
}
for i,t in memo_updates.items():replace(mps[i],t,False)
for t in mb.findall('w:tbl',NS):
    for p in t.xpath('.//w:p',namespaces=NS):
        if '阳性数' in plain(p):replace(p,plain(p).replace('阳性数','编码为1的数量'),False)
mparts['word/document.xml']=E.tostring(mdoc,xml_declaration=True,encoding='UTF-8',standalone=True)
if 'docProps/app.xml' in mparts:
    app=E.fromstring(mparts['docProps/app.xml'])
    for x in list(app):
        if E.QName(x).localname in ['Pages','Words','Characters','CharactersWithSpaces','Paragraphs','Lines']:app.remove(x)
    mparts['docProps/app.xml']=E.tostring(app,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(msrc) as z,ZipFile(mdst,'w') as out:
    for info in z.infolist():out.writestr(info,mparts[info.filename])

audit={'operation':'restore_original_attention_share_estimand','source_docx':str(src),'source_sha256':sha(src),
       'output_docx':str(dst),'output_sha256':sha(dst),'stats_path':str(stats_path),'stats_sha256':sha(stats_path),
       'raw_labels_modified':False,'frozen_weights_modified':False,'kappa_values_modified':False,
       'paragraph_changes':changes,'table3':table3,'table4':table4,'table5':table5,
       'figure_replaced':'word/media/image4.png','reference_count':51,'memo':str(mdst),
       'only_package_parts_changed':['word/document.xml','word/media/image4.png','docProps/app.xml']}
(ROOT/'manuscript_revision_audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2))
print(json.dumps({'main':str(dst),'memo':str(mdst),'paragraph_updates':len(updates),'abstract_chinese_characters':len(updates[1])-3},ensure_ascii=False))
