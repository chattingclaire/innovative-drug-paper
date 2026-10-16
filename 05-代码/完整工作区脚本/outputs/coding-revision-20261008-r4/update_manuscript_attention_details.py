"""Synchronize the reviewed complete rule run and add bounded content findings.

Run with the bundled document runtime.  The old document, statistics, labels,
references and failed technical attempts remain preserved.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from fractions import Fraction
from copy import deepcopy
import csv, hashlib, importlib.util, json, re
from lxml import etree as E

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FINAL = ROOT/'outputs/final-three-department-20261008-human-validation-template'
DOC = FINAL/'创新药评价的注意力配置差异与协调路径.docx'
SOURCE = HERE/'rules38-LLM03-synchronized-findings/完整定义构成核查.json'
DETAIL = HERE/'all-pair-attention-detail-analysis-rule38/all60_conditional_department_contrasts.json'
METHODS = ('rules-v38-development','LLM-candidate03-single-unit-reconciled')
DIMS = ('S','E','Ec','I','F')
GROUPS = ('NMPA','NHSA','NHC')
CN = dict(zip(DIMS,('安全性','有效性','经济性','创新性','公平性')))
GN = dict(zip(GROUPS,('药监','医保','卫健')))
MN = dict(zip(METHODS,('自动规则编码','LLM编码')))
NS = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{'+NS['w']+'}'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def plain(p):
    return ''.join(p.xpath('.//w:t/text()',namespaces=NS))


def main():
    assert sha(DOC)=='36b5839a4eb6545bc62bcea90875956438a6dbc0062b94440b1fbaa6c947199e'
    assert sha(SOURCE)=='6d66e26bcc4a0bfd395fcf5ed2641d61738ac4dae759f53177f4defe00886dc1'
    run_review=HERE/'rules-v38-shadow-independent-comparison/independent_full_run_review.json'
    assert sha(run_review)=='378cab14e644e12c187c7547e1e6ebc118a75df0f5fc085983362eaeb2253c65'
    findings=json.loads(SOURCE.read_text());details=json.loads(DETAIL.read_text())
    assert len(details['rows'])==60
    archive=HERE/'manuscript-before-attention-details.docx'
    if archive.exists():
        assert sha(archive)==sha(DOC), 'A failed prewrite attempt may only reuse the identical preserved original.'
    else:
        archive.write_bytes(DOC.read_bytes())
    with ZipFile(DOC) as z: parts={x.filename:(x,z.read(x.filename)) for x in z.infolist()}
    tree=E.fromstring(parts['word/document.xml'][1]);body=tree.find('w:body',NS)
    ps=body.findall('w:p',NS);tables=body.findall('w:tbl',NS)
    old_text=[plain(p) for p in ps]
    old_tables=[E.tostring(t) for t in tables]
    old_refs=[x for x in old_text if re.match(r'^\[\d+\]',x)]
    assert len(tables)==4 and len(old_refs)==66
    normal=deepcopy(ps[39].find('w:r/w:rPr',NS))
    citation=deepcopy(tree.xpath('.//w:r[w:rPr/w:vertAlign[@w:val="superscript"]]/w:rPr',namespaces=NS)[0])
    changes={}

    def set_text(p,text):
        for child in list(p):
            if child.tag!=W+'pPr':p.remove(child)
        for segment in re.split(r'(\[\d+(?:,\d+)*\])',text):
            if not segment:continue
            r=E.SubElement(p,W+'r')
            pr=citation if re.fullmatch(r'\[\d+(?:,\d+)*\]',segment) else normal
            if pr is not None:r.append(deepcopy(pr))
            t=E.SubElement(r,W+'t');t.text=segment

    def rewrite(i,text):
        changes[str(i)]={'old':old_text[i],'new':text}
        set_text(ps[i],text)

    def replace(i,old,new):
        before=plain(ps[i]);assert before.count(old)==1,(i,old)
        text=before.replace(old,new);changes[str(i)]={'old':old_text[i],'new':text}
        set_text(ps[i],text)

    for i in (1,6):
        text=plain(ps[i])
        for a,b in [('46.67','46.60'),('61.37','61.41'),('20.49','20.46')]:
            assert a in text;text=text.replace(a,b)
        rewrite(i,text)
    rewrite(39,'比较采用三类比例。“注意力占比”为本部门某维编码句次除以五维编码句次合计，呈现五维相对配置，精确五项合计100%；“内容覆盖比例”为某维被编码为1的单元数除以本部门全部分析单元数，呈现内容出现范围，各维可交叉，五项无需合计100%；维度间的条件比例为同时涉及两维的单元数除以作为条件的该维单元数，按“安全性单元中的有效性比例”“经济性单元中的公平性比例”等具体名称报告，反向比例另以另一维单元数为分母。条件比例描述给定维度内容中的共同表达，不增加价值维度，也不与五维注意力占比相加。共同表达可包括并列内容要求，具体比较关系与决策用途结合政策原文及访谈判断。文件构成和操作定义边界变化用于检验比较的适用范围。')
    replace(57,'内容覆盖比例、注意力占比和经济性单元中的公平性比例','内容覆盖比例、注意力占比和维度间的条件比例')
    rewrite(66,'全量编码呈现不同的五维注意力配置（表3、图2）。自动规则编码结果中，药监安全性、有效性、经济性、创新性、公平性的注意力占比分别为46.60%、30.68%、0.29%、14.33%、8.10%；医保分别为4.42%、4.32%、61.41%、3.02%、26.83%；卫健分别为29.09%、12.12%、18.79%、3.64%、36.36%。药监关注风险及疗效证据，医保突出经济价值与支付安排，卫健的公平性和安全性在本口径中占比较高。')
    rewrite(72,'两种方法的注意力占比差异与编码句次总量有关。药监安全性在自动规则编码与LLM编码中分别为322次和392次，五维句次合计分别为691次和910次，对应占比为46.60%和43.08%；医保经济性分别为611次和677次，五维合计为995次和1157次，对应占比为61.41%和58.51%。LLM编码识别的上述维度句次更多，但因五维句次合计也更多，其相对占比较低。全量56种文件构成口径中，两种方法均保留医保经济性注意力占比高于卫健的方向；自动规则编码的公平性占比在系列等权时转为医保高于卫健。全量分布与概率样本估计分别对应所收集文本及剩余规范代表框。')
    rewrite(73,'逐句对照显示，语境的使用需落实到当前命题。对于申请人开展药物警戒、识别和管理风险的要求，LLM编码同时赋予创新性；按统一定义，该句规定安全义务，没有独立陈述创新研发支持。2024年续约规则将支付范围调整所致基金预算增幅列为续约条件，自动规则编码结合控制该子项的续约规定识别其保障连续性，LLM编码未赋予公平性。两例分别涉及从文件背景扩大推断和未充分承接父条款条件。具体原句、两方法标签和判定依据列于附录A的配套方法差异记录。')
    rewrite(75,'注意力占比之外，经济性单元中的公平性比例进一步呈现部门差异。医保经济性注意力占比高于卫健，而经济性单元中的公平性比例，自动规则编码中卫健为14/31（45.16%）、医保为125/611（20.46%）；LLM编码中分别为13/30（43.33%）和145/677（21.42%）。在6种定义及56种文件构成口径中，两种方法均保留卫健这一比例更高的方向；文件构成检查中，卫健减医保的差值范围为自动规则编码2.59—34.68个百分点、LLM编码4.93—30.58个百分点。该比例呈现经济性内容中公平性的共同表达，具体用途结合条文判断（表4）。')
    replace(80,'将价格水平、可获得性和可负担性共同纳入可及性评价，并结合机构配备、短缺和家庭支付能力判断；','将价格水平、可获得性和可负担性共同纳入可及性评价，要求必要时依据医保报销判断患者实际支付水平，并以年用药治疗费用占家庭年可支配收入的比重衡量可负担性；')
    replace(87,'经济性与公平性的共同表达，以及相关支付和供应条文，','安全性单元中的有效性比例、经济性单元中的公平性比例，以及相关准入、支付和供应条文，')
    replace(91,'五维注意力占比的部门差异及经济性单元中的公平性比例，','五维注意力占比，以及安全性与有效性、经济性与公平性的共同表达，')
    rewrite(103,'本文基于三部门创新药评价政策文本，在安全性、有效性、经济性、创新性和公平性的统一框架下比较注意力配置。自动规则编码与LLM编码在全量主口径中均显示，药监以安全性、医保以经济性、卫健以公平性为最高注意力占比维度。维度间的条件比例进一步显示，医保安全性单元中的有效性比例较高，卫健经济性单元中的公平性比例较高；结合政策原文与访谈，这些差异对应目录准入条件、患者费用负担及药品供应使用等具体任务。本文将部门注意力配置的比较推进到给定维度内容中的共同表达，据此提出在参照药预沟通中对照评价条件、依托可信评价点衔接补充证据、通过目录落地反馈连接支付与患者获取的协调路径。本文主要考察政策文本表达，尚未直接检验上述配置与实际执行效果之间的关系，后续可结合药品评审、机构配备和患者使用资料开展验证。')
    replace(108,'以及抽样权重、四格、代码、提示词与输入输出记录。','以及抽样权重、四格、代码、提示词与输入输出记录。配套《维度共同表达补充统计表》列示全部10对维度的双向条件比例及部门比较，明确分子、分母和6种定义、56种文件构成口径的方向及范围。')
    extra1='从公平性内容看，公平性单元中的经济性比例则为医保高于卫健：自动规则编码分别为125/267（46.82%）和14/60（23.33%），LLM编码分别为145/299（48.49%）和13/64（20.31%）。这一方向同样在6种定义及56种文件构成口径中保留。以不同维度为分母，呈现的是费用内容中有多少同时涉及保障，以及保障内容中有多少同时涉及费用；两者共同说明部门注意力配置还体现为内容组合的差别。'
    extra2='医保的安全性注意力占比较低，但安全性单元中的有效性比例在两种方法中均高于药监和卫健。自动规则编码中，医保为27/44（61.36%），药监为116/322（36.02%），卫健为12/48（25.00%）；LLM编码中分别为52/69（75.36%）、131/392（33.42%）和10/50（20.00%）。这两个部门比较的方向均在6种定义及56种文件构成口径中保留。《暂行办法》第七条将安全有效与临床必需、价格合理共同列为目录准入条件[36]，《申报指南》要求说明创新带来的疗效或安全性优势[39]。医保调研纪要也将安全性、有效性和经济性列为综合评审的核心内容。较低的安全性注意力占比与较高的上述条件比例共同呈现其文本关注方式，具体条款将安全有效用于准入及价值比较。'
    for anchor,text in ((75,extra1),(80,extra2)):
        p=E.Element(W+'p');pr=ps[anchor].find('w:pPr',NS)
        if pr is not None:p.append(deepcopy(pr))
        set_text(p,text);ps[anchor].addnext(p)

    # Preserve table structure and typography; change the 30 percentage cells only.
    table=tables[2];rows=table.findall('w:tr',NS)
    assert len(rows)==7
    figure_rows=[]
    for i,(group,method) in enumerate((g,m) for g in GROUPS for m in METHODS):
        profile=findings['primary_full4481'][method]['departments'][group]['profile']
        counts={d:int(profile['coding_count'][d]) for d in DIMS};total=sum(counts.values())
        cells=rows[i+1].findall('w:tc',NS);assert len(cells)==7
        for j,d in enumerate(DIMS):
            p=cells[j+2].find('w:p',NS);pr=deepcopy(p.find('w:r/w:rPr',NS))
            for ch in list(p):
                if ch.tag!=W+'pPr':p.remove(ch)
            rr=E.SubElement(p,W+'r')
            if pr is not None:rr.append(pr)
            E.SubElement(rr,W+'t').text=f'{100*counts[d]/total:.2f}'
        figure_rows.append({'group':group,'method_role':'rules' if method==METHODS[0] else 'LLM','denominator':total,
            'dimensions':{d:{'exact_fraction':str(Fraction(counts[d],total))} for d in DIMS}})
    # Reuse the previously verified plotting function with the new exact fractions.
    plot_script=ROOT/'outputs/coding-revision-20261007-r3/manuscript-update-20261008/emit_manuscript_after_adoption_v6.py'
    spec=importlib.util.spec_from_file_location('retained_plot',plot_script);plot=importlib.util.module_from_spec(spec);spec.loader.exec_module(plot)
    figure=HERE/'figure2_attention_current.png';assert not figure.exists()
    plot.plot_attention(figure_rows,figure)
    assert E.tostring(tables[0])==old_tables[0] and E.tostring(tables[1])==old_tables[1] and E.tostring(tables[3])==old_tables[3]
    refs=[plain(p) for p in body.findall('w:p',NS) if re.match(r'^\[\d+\]',plain(p))]
    assert refs==old_refs
    new_xml=E.tostring(tree,xml_declaration=True,encoding='UTF-8',standalone=True)
    temp=DOC.with_suffix('.staging.docx')
    with ZipFile(temp,'w',compression=ZIP_DEFLATED) as z:
        for name,(info,data) in parts.items():
            z.writestr(info,new_xml if name=='word/document.xml' else figure.read_bytes() if name=='word/media/image4.png' else data)
    temp.replace(DOC)
    with ZipFile(DOC) as z:
        for name,(_,data) in parts.items():
            if name not in ('word/document.xml','word/media/image4.png'):assert z.read(name)==data,name
    # All 60 department contrasts are exported, not just the findings selected for discussion.
    output=[]
    for row in details['rows']:
        for method,v in row['methods'].items():
            o={'编码方法':MN[method],'作为条件的维度':CN[row['condition_dimension']],'共同表达的维度':CN[row['cooccurring_dimension']],
                '部门一':GN[row['department_one']],'部门二':GN[row['department_two']]}
            for name,key in [('部门一','one'),('部门二','two')]:
                o[name+'共同表达单元数']=v[key]['both_n'];o[name+'条件维度单元数']=v[key]['condition_positive_n']
                o[name+'条件比例%']=100*v[key]['conditional_share'] if v[key]['conditional_share'] is not None else 'NA'
            o['部门一减部门二百分点']=v['difference_percentage_points']
            for key,label in [('definition6','定义口径'),('composition56','文件构成口径')]:
                a=v[key];o[label+'数']=a['scenario_n'];o[label+'部门一较高数']=a['one_higher_n'];o[label+'部门二较高数']=a['two_higher_n'];o[label+'相等数']=a['equal_n'];o[label+'未定义数']=a['undefined_n']
                o[label+'差值最小百分点'],o[label+'差值最大百分点']=a['difference_percentage_point_range']
            output.append(o)
    sup=FINAL/'维度共同表达补充统计表.csv';assert not sup.exists() and len(output)==120
    with sup.open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(output[0]));writer.writeheader();writer.writerows(output)
    with sup.open(encoding='utf-8-sig',newline='') as f:back=list(csv.DictReader(f))
    for actual,expected in zip(back,output):
        assert all(actual[k]==str(v) for k,v in expected.items())
    (FINAL/'维度共同表达补充统计表说明.txt').write_text('本表为同版4481条全量文本的描述性比较。10对维度各计算两个方向的条件比例，再比较3组部门，得到60项比较；两方法分别列示，共120行。条件比例分母为列明的条件维度单元数，不是部门全部单元数，也不是五维句次合计。共同表达包括并列内容要求，不直接证明关联强度、因果联系或执行效果。六种定义和56种文件构成检查分别计算，不是62次独立检验。文件/系列等权时，各比例按分母非零的文件/系列内部比例求均值，不将其当作合并计数。数据不新增人工标签，不作为独立人工效度验证。\n',encoding='utf-8')
    record={'document':{'path':str(DOC),'sha256':sha(DOC)},'preserved_previous':{'path':str(archive),'sha256':sha(archive)},
        'findings':{'path':str(SOURCE),'sha256':sha(SOURCE)},'detail':{'path':str(DETAIL),'sha256':sha(DETAIL)},
        'reviewed_complete_run':{'path':str(run_review),'sha256':sha(run_review)},'script_sha256':sha(__file__),
        'changed_paragraphs':changes,'inserted_paragraphs':[extra1,extra2],
        'table3_30_percentages_recalculated':True,'table1_table2_table4_unchanged':True,'all66_references_unchanged':True,
        'figure2':{'path':str(figure),'sha256':sha(figure),'source_rows':figure_rows},
        'supplement':{'path':str(sup),'sha256':sha(sup),'rows':len(output),'all_cells_roundtrip_checked':True},
        'old240_machine_labels_and_subtypes_unchanged':findings['provenance']['old240_labels_and_subtypes_identical'],
        'no_reference_label_edits':True,'no_new_human_validation_claim':True,'independent_numeric_and_visual_QA':'PENDING'}
    (HERE/'manuscript_attention_detail_binding.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('changed_paragraphs','inserted_paragraphs','figure2')},ensure_ascii=False))


if __name__=='__main__':main()
