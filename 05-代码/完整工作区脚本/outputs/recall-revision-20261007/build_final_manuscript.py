"""Preserve the delivered journal manuscript; bind prose/tables to actual results.

Default requires sealed rules v31 and genuine LLM v30 on completed material v3.
--preview permits an internal layout proof, explicitly marked incomplete.
No labels or statistical results are changed by this document builder.
"""
from pathlib import Path
from copy import deepcopy
from zipfile import ZipFile
from fractions import Fraction
from lxml import etree as E
import json, re, hashlib, argparse
from final_prose import UPDATES, REMOVE_PARAGRAPHS, REMOVE_TABLES, CONTENT_TABLE, NEW_REFERENCES

OUT=Path(__file__).resolve().parent
BASE=OUT.parent/'indicator-alignment-20261007'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','wp':'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
def W(s):return '{'+NS['w']+'}'+s
def plain(x):return ''.join(x.xpath('.//w:t/text()',namespaces=NS))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def replace(p,text,refs=True):
    text=text.replace('\u2060','')
    pr=p.find('w:pPr',NS);rp=None
    for r in p.findall('w:r',NS):
        q=r.find('w:rPr',NS)
        if q is not None and q.find('w:vertAlign',NS) is None:rp=deepcopy(q);break
    for c in list(p):
        if c is not pr:p.remove(c)
    for part in re.split(r'(\[\d+(?:[,–—-]\d+)*\])',text) if refs else [text]:
        if not part:continue
        r=E.SubElement(p,W('r'))
        if rp is not None:r.append(deepcopy(rp))
        if refs and re.fullmatch(r'\[\d+(?:[,–—-]\d+)*\]',part):
            q=r.find('w:rPr',NS)
            if q is None:q=E.SubElement(r,W('rPr'))
            for v in q.findall('w:vertAlign',NS):q.remove(v)
            E.SubElement(q,W('vertAlign')).set(W('val'),'superscript')
        for n,line in enumerate(part.split('\n')):
            if n:E.SubElement(r,W('br'))
            t=E.SubElement(r,W('t'));t.set('{http://www.w3.org/XML/1998/namespace}space','preserve');t.text=('\u2060' if refs and re.fullmatch(r'\[\d+(?:[,–—-]\d+)*\]',part) else '')+line
def cellset(c,t):
    ps=c.findall('w:p',NS) or [E.SubElement(c,W('p'))]
    replace(ps[0],str(t),False)
    for p in ps[1:]:c.remove(p)
def toggle(p,tag,value):
    pr=p.find('w:pPr',NS)
    if pr is None:pr=E.SubElement(p,W('pPr'))
    e=pr.find('w:'+tag,NS)
    if e is None:e=E.SubElement(pr,W(tag))
    e.set(W('val'),str(value))
def tablefill(t,values,widths):
    rows=t.findall('w:tr',NS);template=deepcopy(rows[-1])
    for row in rows:t.remove(row)
    grid=t.find('w:tblGrid',NS)
    if grid is not None:t.remove(grid)
    grid=E.Element(W('tblGrid'))
    for width in widths:E.SubElement(grid,W('gridCol')).set(W('w'),str(width))
    t.insert(1,grid)
    for ri,vals in enumerate(values):
        row=deepcopy(template)
        cells=row.findall('w:tc',NS)
        while len(cells)<len(vals):row.append(deepcopy(cells[-1]));cells=row.findall('w:tc',NS)
        for c in cells[len(vals):]:row.remove(c)
        trp=row.find('w:trPr',NS)
        if trp is None:trp=E.SubElement(row,W('trPr'))
        for h in trp.findall('w:trHeight',NS):trp.remove(h)
        for h in trp.findall('w:tblHeader',NS):trp.remove(h)
        if ri==0:E.SubElement(trp,W('tblHeader'))
        for ci,(c,text) in enumerate(zip(row.findall('w:tc',NS),vals)):
            cellset(c,text);cp=c.find('w:tcPr',NS)
            if cp is None:cp=E.SubElement(c,W('tcPr'))
            tw=cp.find('w:tcW',NS)
            if tw is None:tw=E.SubElement(cp,W('tcW'))
            tw.set(W('w'),str(widths[ci]));tw.set(W('type'),'dxa')
            for tag in ['tcBorders','shd','vAlign']:
                for q in cp.findall('w:'+tag,NS):cp.remove(q)
            E.SubElement(cp,W('vAlign')).set(W('val'),'center')
            borders=E.SubElement(cp,W('tcBorders'))
            for edge in ['top','bottom','left','right','insideH','insideV']:
                q=E.SubElement(borders,W(edge));q.set(W('val'),'nil')
            for edge,size in ([('top','8'),('bottom','4')] if ri==0 else [('bottom','8')] if ri==len(values)-1 else []):
                q=borders.find('w:'+edge,NS);q.set(W('val'),'single');q.set(W('sz'),size);q.set(W('color'),'000000')
            for p in c.findall('w:p',NS):
                toggle(p,'keepNext',1 if ri==0 else 0)
                pr=p.find('w:pPr',NS)
                for old in pr.findall('w:ind',NS):pr.remove(old)
                jc=pr.find('w:jc',NS)
                if jc is None:jc=E.SubElement(pr,W('jc'))
                jc.set(W('val'),'left' if len(values[0])==4 and ci>0 else 'center')
                for r in p.findall('w:r',NS):
                    rp=r.find('w:rPr',NS)
                    if rp is None:rp=E.SubElement(r,W('rPr'))
                    for old in rp.findall('w:b',NS):rp.remove(old)
                    if ri==0:E.SubElement(rp,W('b'))
                    for tag in ['sz','szCs']:
                        q=rp.find('w:'+tag,NS)
                        if q is None:q=E.SubElement(rp,W(tag))
                        q.set(W('val'),'21')
                    co=rp.find('w:color',NS)
                    if co is None:co=E.SubElement(rp,W('color'))
                    co.set(W('val'),'000000')
        t.append(row)
def citation_ids(token):
    ids=[]
    for segment in token[1:-1].split(','):
        nums=re.split('[–—-]',segment)
        ids.extend(range(int(nums[0]),int(nums[-1])+1))
    return ids
def citation_token(ids):
    values=sorted(set(ids));runs=[];i=0
    while i<len(values):
        j=i
        while j+1<len(values) and values[j+1]==values[j]+1:j+=1
        runs.append(str(values[i]) if i==j else str(values[i])+'-'+str(values[j]));i=j+1
    return '['+','.join(runs)+']'
def write_parts(src,dst,parts):
    with ZipFile(src) as z,ZipFile(dst,'w') as out:
        for info in z.infolist():out.writestr(info,parts[info.filename])

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--preview',action='store_true');args=parser.parse_args()
    target=OUT/'preview' if args.preview else OUT;target.mkdir(exist_ok=True)
    a=json.loads((OUT/'三部门注意力分布与敏感性.json').read_text())
    s=json.loads((OUT/'三部门编码指标.json').read_text())
    def source_digest(data,path):
        hashes={str((OUT.parents[1]/Path(k)).resolve()):v for k,v in data['source_sha256'].items()}
        return hashes[str(Path(path).resolve())]
    rule=a['method_bindings']['rule']['method'];llm='llm_gpt56_sol_v30'
    assert rule=='rules_v31' and s['method_bindings']['rule']['method']==rule
    complete=llm in a['primary'] and any(r['method']==llm for r in s['records'])
    if not args.preview:assert complete,'Cannot write a final manuscript before the actual full LLM run is sealed and recomputed'
    assert a['method_bindings']['rule']==s['method_bindings']['rule'],'Statistics must bind identical rule version/input/output'
    for x in [a,s]:
        for key in ['inputs','rules']:
            path=Path(x['method_bindings']['rule'][key]);assert source_digest(x,path)==sha(path)
    if complete:
        la=a['method_bindings']['llm'];ls=s['method_bindings']['llm'];assert la['path']==ls['path'] and la['path']
        lp=Path(la['path']);assert source_digest(a,lp)==source_digest(s,lp)==sha(lp)
        fm=json.loads((lp.parent/'final_manifest.json').read_text())
        assert fm['status']=='complete_validated_full_corpus' and fm['n']==4924 and fm['predictions_sha256']==sha(lp)
        eq=json.loads((OUT/'最终LLM执行独立核验.json').read_text())
        assert eq['status']=='passed' and eq['predictions_sha256']==sha(lp)
        assert eq['shared_rule_input_sha256']==sha(Path(a['method_bindings']['rule']['inputs']))
        assert eq['selected_tool_event_count']==0 and not eq['mechanically_edited_output_selected']
        qa=json.loads((OUT/'三部门数据独立QA.json').read_text())
        assert qa['status']=='passed' and qa['target_sha256']==sha(OUT/'三部门注意力分布与敏感性.json')
        # The independent metric QA is also tied to the exact current source JSON.
        mq=json.loads((OUT/'三部门编码指标核验.json').read_text())
        assert mq['status']=='passed' and mq['target_sha256']==sha(OUT/'三部门编码指标.json'),mq
    p=a['primary'];dims=['S','E','Ec','I','F'];groups=['NMPA','NHSA','NHC'];cn=['安全性','有效性','经济性','创新性','公平性']
    names={'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
    def q(g,d,m=rule):return Fraction(p[m][g]['dimensions'][d]['attention_share']['exact_fraction'])*100
    def f(x):return f'{float(x):.2f}'
    def metric(m,d,ref='C',group='ALL',frame='main1057'):
        return next(r for r in s['records'] if (r['method'],r['dimension'],r['reference'],r['group'],r['frame'])==(m,d,ref,group,frame))
    def kval(m,d,ref='C'):return metric(m,d,ref)['metrics']['kappa']['estimate']
    methods=[rule]+([llm] if complete else [])+['A_AI_reference','C_AI_reference']
    stable=all(a['sensitivities'][m]['primary_dominant_dimensions']['NMPA']==['S'] and a['sensitivities'][m]['primary_dominant_dimensions']['NHSA']==['Ec'] for m in methods)
    crossing=('A/C参照与大语言模型平行编码均保留药监安全性和医保经济性占比最高的特征。' if complete and stable else 'A/C参照保留药监安全性和医保经济性占比最高的特征。' if stable else '平行编码的分布差异见表3。')
    u=dict(UPDATES)
    u[5]='Differences in Attention Allocation in Innovative Drug Evaluation and Coordination Pathways'
    u[46]=u[46].replace('以gpt-5.6-sol作平行测量','以大语言模型（large language model，LLM）gpt-5.6-sol作平行测量')
    u[43]=u[43].replace('DRG/DIP技术规范','按疾病诊断相关分组和按病种分值付费的技术规范')
    u[50]=u[50].replace('保留TP、FP、FN、TN及各维可配对数。','保留两者均为1（TP）、模型1而参照0（FP）、模型0而参照1（FN）、两者均为0（TN）的四格计数及各维可配对数。')
    u[49]=u[49].replace('表2报告开发复核表现。','表2报告开发复核表现。首次参照标签及其可见材料保留，分歧核查区分材料语境差异、操作边界和判读偏差。')
    u[59]=u[59].replace('规则及LLM为全量句次','规则及LLM为全量已确定编码句次')
    u[1]=f'摘要：基于2017—2026年药监、医保、卫健三个部门的51个政策来源条目，采用统一五维规范开展句段编码，结合政策原文与专家访谈，分析创新药评价的注意力配置及协调路径。以各维度编码句次占五维编码句次合计的比重衡量注意力占比。全量规则编码显示，药监安全性占{f(q("NMPA","S"))}%，有效性占{f(q("NMPA","E"))}%；医保经济性占{f(q("NHSA","Ec"))}%；卫健安全性占{f(q("NHC","S"))}%，公平性占{f(q("NHC","F"))}%。{crossing}原文比较表明，三部门共同关注安全、有效及临床价值，在目标人群、参照方案、证据要求和结论用途上存在差别。协调应以同一适应症和人群为基础，建立评价结论对照，衔接补充研究，并共享评审理由与使用反馈。'
    u[6]=f'Abstract: Using 51 policy source entries issued within the drug regulation, medical insurance and health administration systems from 2017 to 2026, this study applies a shared five-dimensional codebook and combines sentence-level coding with policy interpretation and expert interviews. Attention share is the coded occurrences of each dimension divided by the total occurrences across all five dimensions. Full-corpus rule-based coding shows that safety accounts for {f(q("NMPA","S"))}% and efficacy for {f(q("NMPA","E"))}% in drug regulation; economic considerations account for {f(q("NHSA","Ec"))}% in medical insurance; safety accounts for {f(q("NHC","S"))}% and fairness for {f(q("NHC","F"))}% in health administration. '+('The A/C references and parallel LLM coding retain safety as the largest share in drug regulation and economic considerations in medical insurance. ' if complete and stable else '')+'Policy provisions identify shared concerns with safety, efficacy and clinical value, alongside differences in target populations, comparators, evidence requirements and decision purposes. Coordination should align conclusions for the same indication and population, connect supplementary evidence requirements, and share assessment reasons and feedback from clinical use.'
    u[6]=u[6].replace('parallel LLM coding','parallel large language model (LLM) coding')
    ac='、'.join(f'{kval("A_C",d):.3f}' for d in dims)
    rks=[kval(rule,d,r) for d in dims for r in ['A','C']]
    u[54]=f'A/C在安全性、有效性、经济性、创新性、公平性上的κ依次为{ac}。自动规则相对A/C的逐维κ为{min(rks):.3f}—{max(rks):.3f}。'
    if complete:
        lks=[kval(llm,d,r) for d in dims for r in ['A','C'] if kval(llm,d,r) is not None]
        u[54]+=f'LLM对应κ为{min(lks):.3f}—{max(lks):.3f}（表2）。'
        ni=[metric(llm,'I',r,'NMPA')['metrics']['kappa']['estimate'] for r in ['A','C']]
        nf=[metric(llm,'F',r,'NHSA')['metrics']['kappa']['estimate'] for r in ['A','C']]
        ne=metric(llm,'E','C','NHSA')['metrics']['kappa']['estimate']
        u[54]+=f'分部门看，LLM药监创新性对A/C的κ为{ni[0]:.3f}/{ni[1]:.3f}，医保公平性为{nf[0]:.3f}/{nf[1]:.3f}，医保有效性对C为{ne:.3f}。'
    rare_k=metric(rule,'Ec','A','NMPA')['metrics']['kappa']['estimate'];nhsa_k=metric('A_C','E','C','NHSA')['metrics']['kappa']['estimate']
    for reference in ['A','C']:
        rare=metric(rule,'Ec',reference,'NMPA')
        assert rare['confusion']['TP']+rare['confusion']['FN']==2
        assert rare['confusion']['FN']==1
        assert rare['metrics']['kappa']['estimate']==rare_k
    u[54]+=f'逐部门检验中，药监经济性两份参照各确认2条，规则对A/C的κ均为{rare_k:.3f}，其中1条分歧在于一般医保数据定义是否构成药品经济性内容；医保有效性A/C的κ为{nhsa_k:.3f}，1条分歧在于纳入诊疗方案的申报资格是否构成有效性依据。低频类别中这类分歧对κ影响较大，相应四格与原文一并记录，区分漏识别与编码边界差异。'
    rule_vectors={g:'、'.join(f'{f(q(g,d))}%' for d in dims) for g in groups}
    u[65]=f'三部门五维注意力占比存在差异（表3、图2）。按安全性、有效性、经济性、创新性、公平性的顺序，药监分别为{rule_vectors["NMPA"]}；医保分别为{rule_vectors["NHSA"]}；卫健分别为{rule_vectors["NHC"]}。各维的政策内容及用途结合原文分别分析。'
    u[73]=f'部门差异具体表现为：药监安全性比医保高{f(q("NMPA","S")-q("NHSA","S"))}个百分点，有效性高{f(q("NMPA","E")-q("NHSA","E"))}个百分点；医保经济性比药监高{f(q("NHSA","Ec")-q("NMPA","Ec"))}个百分点、比卫健高{f(q("NHSA","Ec")-q("NHC","Ec"))}个百分点；卫健公平性比药监高{f(q("NHC","F")-q("NMPA","F"))}个百分点、比医保高{f(q("NHC","F")-q("NHSA","F"))}个百分点。创新性在三个部门分别为{f(q("NMPA","I"))}%、{f(q("NHSA","I"))}%、{f(q("NHC","I"))}%，需结合注册分类、研发支持与临床需求的具体内容理解。安全性与有效性同时出现于三部门，关注比例和所服务的判断环节不同。'
    u[74]=f'A/C分别估计五维加权注意力占比，完整结果见表3。以下数值依次对应A、C：药监安全性为{f(q("NMPA","S","A_AI_reference"))}%、{f(q("NMPA","S","C_AI_reference"))}%；医保经济性为{f(q("NHSA","Ec","A_AI_reference"))}%、{f(q("NHSA","Ec","C_AI_reference"))}%；卫健安全性为{f(q("NHC","S","A_AI_reference"))}%、{f(q("NHC","S","C_AI_reference"))}%，公平性为{f(q("NHC","F","A_AI_reference"))}%、{f(q("NHC","F","C_AI_reference"))}%。'
    tests=[]
    for m in methods:
        sm=a['sensitivities'][m]
        tests.extend([sm['primary_dominant_dimensions']]+list(sm['scenario_dominant_dimensions'].values())+[r['dominant_dimensions'] for r in sm['leave_one_policy_file_out']])
    kept=all(t['NMPA']==['S'] and t['NHSA']==['Ec'] for t in tests)
    if kept:u[74]+='来源及定义边界检验与逐条目剔除均保留药监安全性、医保经济性占比最高的特征。'
    else:u[74]+='来源及定义边界检验的具体变化见配套统计。'
    u[74]+='卫健安全性与公平性的相对次序随口径变化；在规则与A/C结果中，剔除联合文本或2022年加强用药安全管理文件时，经济性超过安全性，提示临床经济分析在其关注结构中的位置。'
    # This local interpretation is retained only when the actual new data
    # reproduce it; it does not assert the same ordering for the LLM.
    for method in [rule,'A_AI_reference','C_AI_reference']:
        nonjoint=a['sensitivities'][method]['scenarios']['exclude_all_joint_publications']['NHC']['dimensions']
        assert Fraction(nonjoint['Ec']['attention_share']['exact_fraction'])>Fraction(nonjoint['S']['attention_share']['exact_fraction'])
        removal=next(x for x in a['sensitivities'][method]['leave_one_policy_file_out'] if '加强用药安全' in str(x))
        assert removal['distribution']['NHC']['dimensions']['Ec']['attention_share']['value']>removal['distribution']['NHC']['dimensions']['S']['attention_share']['value']
    u[72]+='图内数值保留1位小数，表3保留2位小数；显示值独立舍入。'
    u[104]=f'本文比较了药监、医保、卫健三个部门的创新药评价政策。全量规则编码中，药监安全性占{f(q("NMPA","S"))}%，有效性占{f(q("NMPA","E"))}%；医保经济性占{f(q("NHSA","Ec"))}%；卫健安全性占{f(q("NHC","S"))}%，公平性占{f(q("NHC","F"))}%。{crossing}政策原文进一步显示，三部门共同关注临床价值，却在人群、参照方案、证据要求和用途上有所区别。注册创新身份、上市获益风险及支付比较价值应分别注明判断条件，临床使用结果则为后续评价提供反馈。'
    if complete:
        pairs={m:{(tuple(r['pair']),r['dimension']):r['observed_direction'] for r in a['comparisons'][m]} for m in methods}
        same=sum(pairs[rule][k]==pairs[llm][k] for k in pairs[rule])
        u[74]+=f'LLM与规则在三部门15项同维度比较中有{same}项点估计方向一致。'
        stability=OUT/'llm-v30/stability_comparison_v30.json'
        assert stability.exists(),'Real stability comparison is required before reporting it'
        stability_data=json.loads(stability.read_text())
        repeat=next(x for x in stability_data['comparisons'] if x['comparison_identity']=='strict_same_prompt_same_36_row_batch_repeat')
        order=next(x for x in stability_data['comparisons'] if x['comparison_identity']=='equivalent_prompt_dimension_order_perturbation_same_36_row_batch')
        u[111]='LLM以gpt-5.6-sol执行，推理强度medium，采用固定代码本及结构化输出；每批最多25条、独立新上下文，共197批覆盖全部4924个单元，其中三部门4481条进入主比较。规则与LLM读取同版原文、列表条件、对象范围和表头，不提供参考标签或其他方法预测。依Törnberg[42]关于任务与提示记录的建议，保存实际请求、首输出及执行中断、结构或逐字引文校验失败后的同请求重跑记录，不按标签或指标选择结果。另对预先冻结的三部门各12条样本，以同一36条批次进行同提示重复及维度顺序扰动，五维标签完全一致率分别为'+f"{repeat['all_five_labels_exact_agreement']*100:.2f}%、{order['all_five_labels_exact_agreement']*100:.2f}%"+'。服务未暴露的底层revision和temperature记为不可得。'
        u[111]=u[111].replace('共197批覆盖全部4924个单元','最终选中197批覆盖全部4924个单元')
        u[111]=u[111].replace('规则与LLM读取同版原文','源语境补全后对受影响批整批重跑，其余批逐单元核对同材。规则与LLM读取同版原文')
    else:u[111]='内部排版预览：新LLM全量执行尚未闭合，本稿不填旧LLM数值；封存后将用真实输出重算表2、表3及跨方法比较。'
    src=BASE/'论文修订稿-指标统一版-待补真人验证.docx'
    with ZipFile(src) as z:parts={i.filename:z.read(i.filename) for i in z.infolist()}
    doc=E.fromstring(parts['word/document.xml']);body=doc.find('w:body',NS);ps=body.findall('w:p',NS);ts=body.findall('w:tbl',NS)
    assert len(ps)==176 and len(ts)==6
    refs={int(re.match(r'\[(\d+)\]',plain(pp))[1]):re.sub(r'^\[\d+\]\s*','',plain(pp)) for pp in ps[125:]}
    refs.update(NEW_REFERENCES)
    u[10]=plain(ps[10]).replace('纳入医保目录的药品，也未必能够在医疗机构得到充分配备和使用','纳入医保目录的药品，在医疗机构实际使用中仍可能面临障碍')
    # The study context is already stated in the sentences. Remove redundant
    # defensive tails without strengthening the underlying literature claims.
    u[17]=plain(ps[17]).replace('；该便利样本未作组间权重差异检验。','。').replace('，但其决策影响证据有限。','。')
    u[19]=plain(ps[19]).replace('这些发现具有抗生素领域的特定背景，不能直接推广到所有创新药。','')
    u[20]=plain(ps[20]).replace('，不能仅由部门身份或职责推定。','。')
    for i,t in u.items():
        assert not re.search(r'\{[A-Z_]+\}',t),f'Unfilled prose: {i}'
        replace(ps[i],t)
    for i in [32,36,51,57,70,77]:
        for r in ps[i].findall('w:r',NS):
            rp=r.find('w:rPr',NS)
            if rp is None:rp=E.SubElement(r,W('rPr'))
            rf=rp.find('w:rFonts',NS)
            if rf is None:rf=E.SubElement(rp,W('rFonts'))
            for key in ['ascii','hAnsi','eastAsia']:rf.set(W(key),'宋体')
            for key in ['asciiTheme','hAnsiTheme','eastAsiaTheme']:rf.attrib.pop(W(key),None)
            sz=rp.find('w:sz',NS)
            if sz is None:sz=E.SubElement(rp,W('sz'))
            sz.set(W('val'),'21')
    # Keep the full three-department comparison together on the next page.
    toggle(ps[57],'pageBreakBefore',1)
    if args.preview:replace(ps[0],plain(ps[0])+' 内部排版预览')
    for i in REMOVE_PARAGRAPHS:body.remove(ps[i])
    for i in REMOVE_TABLES:body.remove(ts[i])
    tab2=[['维度','方法','κ（A/C）','P（A/C）','R（A/C）','F1（A/C）']]
    for d,n in zip(dims,cn):
        for m,label in [(rule,'自动规则'),(llm,'LLM')]:
            vals=[]
            for key in ['kappa','precision','recall','f1']:
                if m==llm and not complete:vals.append('待闭合');continue
                x=[metric(m,d,r)['metrics'][key]['estimate'] for r in ['A','C']]
                vals.append('/'.join('—' if y is None else f'{y*100:.1f}' if key in ('precision','recall') else f'{y:.3f}' for y in x))
            tab2.append([n,label]+vals)
    tablefill(ts[1],tab2,[1000,1100,2200,1900,1900,1900])
    tab3=[['部门','方法','五维\n编码句次']+cn]
    for g in groups:
        for m,label in [(rule,'自动规则')]+([(llm,'LLM')] if complete else [])+[('A_AI_reference','A'),('C_AI_reference','C')]:
            x=p[m][g];num=x['weighted_five_dimension_known_hit_sum']['value']
            tab3.append([names[g],'规则' if label=='自动规则' else label,f'{num:.2f}' if m.endswith('_reference') else f'{num:.0f}']+[f(q(g,d,m)) for d in dims])
    tablefill(ts[2],tab3,[800,1000,1160]+[1440]*5)
    tablefill(ts[4],CONTENT_TABLE,[1050,3000,3000,3000])
    # Keep retained diagram aspect ratios; files are newly drawn scientific figures.
    from PIL import Image
    for idx,part,filename in [(35,'word/media/image3.png','图1-制度逻辑与注意力分析框架.png'),(69,'word/media/image4.png','图2-三部门五维注意力占比.png')]:
        fp=OUT/filename;parts[part]=fp.read_bytes();iw,ih=Image.open(fp).size
        for extent in ps[idx].xpath('.//wp:extent | .//a:xfrm/a:ext',namespaces=NS):
            extent.set('cy',str(round(int(extent.get('cx'))*ih/iw)))
    # Citations follow first appearance in actual document order, including tables.
    for pp in ps[125:]:body.remove(pp)
    pattern=r'\[\d+(?:[,–—-]\d+)*\]';order=[]
    for block in body:
        for pp in ([block] if block.tag==W('p') else block.xpath('.//w:p',namespaces=NS)):
            for token in re.findall(pattern,plain(pp)):
                for rid in citation_ids(token):
                    assert rid in refs,f'Missing reference {rid}'
                    if rid not in order:order.append(rid)
    remap={rid:i+1 for i,rid in enumerate(order)}
    for pp in body.xpath('.//w:p',namespaces=NS):
        old=plain(pp)
        if re.search(pattern,old):replace(pp,re.sub(pattern,lambda x:citation_token([remap[rid] for rid in citation_ids(x[0])]),old))
    sect=body.find('w:sectPr',NS)
    for rid in order:
        pp=deepcopy(ps[125]);replace(pp,f'[{remap[rid]}] '+refs[rid],False)
        if sect is not None:body.insert(body.index(sect),pp)
        else:body.append(pp)
    parts['word/document.xml']=E.tostring(doc,xml_declaration=True,encoding='UTF-8',standalone=True)
    if 'docProps/app.xml' in parts:
        app=E.fromstring(parts['docProps/app.xml'])
        for x in list(app):
            if E.QName(x).localname in ['Pages','Words','Characters','CharactersWithSpaces','Paragraphs','Lines']:app.remove(x)
        parts['docProps/app.xml']=E.tostring(app,xml_declaration=True,encoding='UTF-8',standalone=True)
    dst=target/'论文修订稿-三部门版.docx';write_parts(src,dst,parts)
    # Separate author memo, using the supplied memo's typography.
    msrc=BASE/'待确认事项-指标统一版.docx'
    with ZipFile(msrc) as z:mparts={i.filename:z.read(i.filename) for i in z.infolist()}
    md=E.fromstring(mparts['word/document.xml']);mb=md.find('w:body',NS);mps=mb.findall('w:p',NS)
    contents=[
        '三部门论文校核与待确认事项',
        '版本日期：2026年10月7日。本文档供作者校核。正文只使用本轮三部门范围、最新规则及'+('已完成的新LLM全量结果。' if complete else '尚待闭合的新LLM运行；当前为内部排版预览。'),
        '一 已完成的计算',
        '主比较为药监17、医保24、卫健10个来源条目，共4481个分析单元。4个中央文件共443单元作共同制度背景。主配对参照1057条、补充历史框411条分别计算，不合并充当代表性样本。',
        '注意力占比采用某维编码句次／同部门五维编码句次合计，各行100%。规则和LLM使用全量句次；A/C按原分层设计权重分别估计。正文的百分比、百分点差、表2、表3与图2由统计JSON生成，表4据政策证据矩阵整理。',
        '各维、各部门和全体配对分别报告κ、观察一致率、四格表及机器对A/C的精确率、召回率、F1；置信区间按来源文件聚类bootstrap 5000次。分母为0的指标记未定义，不填0。敏感性包括5项边界、条目与系列等权、年度最新、剔除联合文本及51次逐条目剔除。',
        '本轮从薄弱比较的50个分歧单元及40个随机对照组成90条开发审读包。独立AI先封存首次判断，再回源补齐4条材料缺口另存复核。全量校验另定位5条列表语境缺口，统一补料后对两个受影响批共50条整批重跑并无条件采用。两种方法使用同版材料，原A/C标签保留。这些审读用于诊断和开发，不充当真人裁定或新独立信度样本。详见独立盲审、材料补全及实际调用留痕文件。',
        '二 A/C与实际真人验证',
        '现有A/C为AI agent独立首次判读，已用于方法开发。正文据实写明这一身份；采用与双编码员相同的统计公式并不改变标注来源。没有收到真人A/C首次独立提交及裁定记录，不能写成已完成人工信效度验证。',
        '此前36条双AI盲审的首次提交继续封存；本轮90条开发审读和模型稳定性使用各自实际材料与运行记录，不替换原A/C，不计作真人验证。',
        '作者补齐时，应在当前规则、代码本和提示词封存后，另行锁定未参与调试的样本，由实际两名领域编码员独立阅读完整句段及必要语境；记录背景、日期、原始标签和理由，先计算协商前一致性，再保存分歧裁定。机器以实际裁定参考计算P/R/F1及区间。新数据替换对应统计和方法身份，不能只替换正文名称。',
        '三 需要作者确认',
        '请确认作者顺序、单位中英文名称、基金项目和通信作者信息。当前正文沿用匿名稿，符合双向匿名送审准备；署名页须另补真实资料。',
        '请确认访谈与会议材料的使用授权及匿名方式。文稿保留两份专家访谈和研讨材料的实际范围；没有将访谈充作句段标签验证。原文证据矩阵与访谈核查记录分别保存。',
        '《科学决策》现行格式为中文题名与摘要在前、英文对应内容在后，中文摘要约300字、关键词3—8个，9000—15000字为宜。最新篇幅及逐页排版结果以本目录最终QA为准；未填作者资料不应称为已可直接投稿。',
        '四 统计结论的使用',
        f'主规则描述为药监安全性{f(q("NMPA","S"))}%，有效性{f(q("NMPA","E"))}%；医保经济性{f(q("NHSA","Ec"))}%；卫健安全性{f(q("NHC","S"))}%，公平性{f(q("NHC","F"))}%。五维分别报告，不设置跨维合成指标。结论讨论文本注意力配置与条文所示的评价条件，不由文本占比推断实际评审赋权或因果效应。',
        '整体逐维κ较高不意味着所有部门类别同样稳定。规则药监经济性、医保有效性，LLM药监创新性、医保公平性，以及补充框的具体分歧均保留在统计和逐条核查中；不以达到固定κ阈值反改参照。没有通用的κ≥0.80期刊发表保证。',
        '原580项同时计数区域、比率界及全部无共同排零方向结果保留在原配套统计，不因改以固定语料全量描述为主而删除。新正文不沿用旧版本数值或把描述差异称为显著。',
        '五 证据与复核位置',
        '本目录包含三部门编码与注意力指标.xlsx、三部门编码指标.json、三部门注意力分布与敏感性.json、政策内容与协调路径.md、policy_evidence_matrix.json、指标依据与理论对齐.md、两条方法的封存代码及真实LLM输入输出。来源哈希、独立核验与最终文稿QA用于追溯。',
    ]
    for c in list(mb):
        if c.tag!=W('sectPr'):mb.remove(c)
    ms=mb.find('w:sectPr',NS)
    for i,t in enumerate(contents):
        template=mps[0] if i==0 else mps[2] if re.match('[一二三四五] ',t) else mps[1]
        pp=deepcopy(template);replace(pp,t,False);toggle(pp,'keepNext',1 if i==0 or re.match('[一二三四五] ',t) else 0)
        if ms is not None:mb.insert(mb.index(ms),pp)
        else:mb.append(pp)
    mparts['word/document.xml']=E.tostring(md,xml_declaration=True,encoding='UTF-8',standalone=True)
    mdst=target/'校核与待确认事项.docx';write_parts(msrc,mdst,mparts)
    bound=[src,msrc,Path(__file__),OUT/'final_prose.py',OUT/'三部门注意力分布与敏感性.json',OUT/'三部门编码指标.json',OUT/'policy_evidence_matrix.json',OUT/'指标依据与理论对齐.md',OUT/'图表数据与来源.json']
    if complete:bound.extend([OUT/'最终LLM执行独立核验.json',OUT/'llm-v30/stability_comparison_v30.json',OUT/'independent_blind_review.json',OUT/'independent_blind_supplement_review.json',OUT/'independent_blind_material_gap_recheck.json',OUT/'renewal_object_scope_v2_manifest.json'])
    if complete:bound.extend([OUT/'safety_population_context_v3_manifest.json',OUT/'source_safety_population_v3_QA.json',OUT/'source_safety_population_v3_independent_QA.json',OUT/'指标依据与理论对齐.json'])
    manifest={'status':'preview_incomplete' if not complete else 'actual_results_bound','rule':a['method_bindings']['rule'],'llm_complete':complete,'source_sha256':{str(x):sha(x) for x in bound},'output_sha256':{str(x):sha(x) for x in [dst,mdst]},'reference_stable_to_final':remap,'unused_old_references':[k for k in refs if k not in remap],'paragraph_changes':{str(i):t for i,t in u.items()},'tables':{'2':tab2,'3':tab3,'4':CONTENT_TABLE},'abstract_chinese_characters':len(re.findall('[\u4e00-\u9fff]',u[1]))}
    (target/'文稿生成与证据绑定.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
    print(json.dumps({'status':manifest['status'],'outputs':[str(dst),str(mdst)],'references':len(order),'abstract_chinese_characters':manifest['abstract_chinese_characters']},ensure_ascii=False))

if __name__=='__main__':main()
