"""Synchronize one adopted document from whole, reviewed coding runs.

Original documents, raw labels, failed candidates and sealed reports stay intact.
Run only after the independent numerical review of the actual new statistics.
"""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
import argparse, csv, hashlib, importlib.util, json, re
from lxml import etree as E

BASE = Path(__file__).resolve().parents[3]
WORK = BASE / 'outputs/编码修订核查-20261008'
OLD = BASE / 'outputs/final-three-department-20261008-human-validation-template'
OUT = WORK / '本轮结果'
NS = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
W = '{' + NS['w'] + '}'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
GROUPS = ('NMPA', 'NHSA', 'NHC')
CN = dict(zip(DIMS, ('安全性', '有效性', '经济性', '创新性', '公平性')))
GN = {'ALL': '总体', 'NMPA': '药监', 'NHSA': '医保', 'NHC': '卫健'}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_text())


def plain(p):
    return ''.join(p.xpath('.//w:t/text()', namespaces=NS))


def main():
    ap = argparse.ArgumentParser()
    for name in ('classification', 'agreement', 'findings', 'details', 'numeric_review'):
        ap.add_argument('--' + name.replace('_', '-'), type=Path, required=True)
    args = ap.parse_args()
    numeric = read(args.numeric_review)
    assert numeric.get('status', '').startswith('PASS') and not numeric.get('failures'), 'Actual independent numeric review required.'
    adoption = read(WORK / '整套编码采用记录.json')
    assert adoption['status'] == 'WHOLE_RULE39_ADOPTED_FOR_SYNCHRONIZED_RECALCULATION_LLM03_RETAINED_COMPLETE'
    for item in ('rules', 'LLM'):
        assert sha(adoption[item]['path']) == adoption[item]['sha256']
    source = OLD / '创新药评价的注意力配置差异与协调路径.docx'
    memo_source = OLD / '编码复核说明与真人检验事项.docx'
    assert sha(source) == '4d61c921a8ea9837f9d31eb4cd09ace0af1839b51e2793232ee0f402ede905e0'
    assert sha(memo_source) == 'a3582879ccb64853a76891f0d5ec85817c6d49dfe395afa513024136e187e768'
    classification = read(args.classification)['comparisons']
    agreement = read(args.agreement)['comparisons']
    findings, details = read(args.findings), read(args.details)
    assert len(classification) == 360 and len(agreement) == 60 and len(details['rows']) == 60
    methods = list(findings['primary_full4481'])
    rule = next(m for m in methods if 'rule' in m.lower())
    llm = next(m for m in methods if 'llm' in m.lower())
    assert len(methods) == 2 and rule != llm
    names = {rule: '自动规则编码', llm: 'LLM编码', 'A_C': '编码员A—编码员B'}

    def row(m, ref, d):
        matches = [r for r in classification if (r['method'], r['reference'], r['dimension'], r['component'], r['group'], r['weighting']) ==
                   (m, ref, d, 'probability_canonical', 'ALL', 'eligible_design_weighted')]
        assert len(matches) == 1
        return matches[0]

    def metric(m, ref, d, k):
        return row(m, ref, d)['metrics'][k]['estimate']

    def f3(v):
        return 'NA' if v is None else f'{v:.3f}'

    def prof(m, g):
        return findings['primary_full4481'][m]['departments'][g]['profile']

    def count(m, g, d):
        return int(prof(m, g)['coding_count'][d])

    def total(m, g):
        return sum(count(m, g, d) for d in DIMS)

    def share(m, g, d):
        return 100 * count(m, g, d) / total(m, g)

    def conditional(m, g, a, b):
        dep = findings['primary_full4481'][m]['departments'][g]
        pair = next(p for p in dep['all10_pairs'] if {p['dimension_a'], p['dimension_b']} == {a, b})
        n, den = int(pair['both_n']), count(m, g, a)
        return n, den, 100 * n / den

    def condtext(m, g, a, b):
        n, den, pct = conditional(m, g, a, b)
        return f'{n}/{den}（{pct:.2f}%）'

    def detail(a, b, one, two):
        return next(r for r in details['rows'] if (r['condition_dimension'], r['cooccurring_dimension'], r['department_one'], r['department_two']) == (a, b, one, two))

    # Every cross-scenario statement below must still hold on the actual adopted run.
    for a, b, one, two in [('Ec', 'F', 'NHSA', 'NHC'), ('F', 'Ec', 'NHSA', 'NHC'), ('S', 'E', 'NMPA', 'NHSA'), ('S', 'E', 'NHSA', 'NHC')]:
        assert detail(a, b, one, two)['same_primary_direction_in_all_definition_and_composition_scenarios']
    for m in methods:
        for g, d in [('NMPA', 'S'), ('NHSA', 'Ec'), ('NHC', 'F')]:
            assert count(m, g, d) == max(count(m, g, x) for x in DIMS)
        assert all(r['methods'][m]['departments']['NHSA']['profile']['attention_share']['Ec'] > r['methods'][m]['departments']['NHC']['profile']['attention_share']['Ec'] for r in findings['composition56'])

    target = OUT / source.name
    memo_target = OUT / memo_source.name
    assert OUT.is_dir() and not target.exists() and not memo_target.exists()
    with ZipFile(source) as z:
        parts = {i.filename: (i, z.read(i.filename)) for i in z.infolist()}
    tree = E.fromstring(parts['word/document.xml'][1])
    body = tree.find('w:body', NS)
    ps, tables = body.findall('w:p', NS), body.findall('w:tbl', NS)
    previous = [plain(p) for p in ps]
    old_refs = [t for t in previous if re.match(r'^\[\d+\]', t)]
    assert len(tables) == 4 and len(old_refs) == 66
    normal = deepcopy(ps[39].find('w:r/w:rPr', NS))
    cite = deepcopy(tree.xpath('.//w:r[w:rPr/w:vertAlign[@w:val="superscript"]]/w:rPr', namespaces=NS)[0])
    changes = {}

    def set_text(p, text):
        for child in list(p):
            if child.tag != W + 'pPr':
                p.remove(child)
        for segment in re.split(r'(\[\d+(?:,\d+)*\])', text):
            if segment:
                r = E.SubElement(p, W + 'r')
                pr = cite if re.fullmatch(r'\[\d+(?:,\d+)*\]', segment) else normal
                if pr is not None:
                    r.append(deepcopy(pr))
                E.SubElement(r, W + 't').text = segment

    def rewrite(i, text):
        changes[str(i)] = {'old': previous[i], 'new': text}
        set_text(ps[i], text)

    for i in (1, 6):
        text = previous[i]
        for before, after in [('46.60', f'{share(rule,"NMPA","S"):.2f}'), ('61.41', f'{share(rule,"NHSA","Ec"):.2f}'), ('20.46', f'{conditional(rule,"NHSA","Ec","F")[2]:.2f}')]:
            assert text.count(before) == 1
            text = text.replace(before, after)
        rewrite(i, text)
    rewrite(49, previous[49].replace('编码员A、编码员B的初始判读及裁定者T的复核', '编码员A、编码员B的独立编码及裁定者T的复核'))
    rewrite(50, '依照任务验证原则[45]，依据两名编码员讨论分歧前的独立结果，以Cohen的κ[46]（扣除机会一致后的名义二元编码一致性）及观察一致率评价编码员间信度；另分别检验自动规则编码、LLM编码与编码员A、编码员B及裁定后复核参照的一致性。参照Kristensen-McLachlan等[47]，以精确率（P）、召回率（R）及F1评价相对于所列参照的分类表现。以各维标签1为正类，P为机器判为1的单元中参照同为1的比例，R为参照判为1的单元中机器同为1的比例，F1为二者的调和均值。总体和各部门按维度报告四格、参照正类比例及上述指标。概率样本按部门抽样框规模/60加权四格。近似95%区间采用部门层内重标bootstrap[48]：每层每次有放回抽取59个单元并作有限总体校正，卫健层为框内全查、重复权重恒为1；5000次重算指标后取2.5%与97.5%分位数。')
    kr = [metric(rule, r, d, 'kappa') for r in ('A', 'C') for d in ('S', 'E', 'Ec')]
    kl = [metric(llm, r, d, 'kappa') for r in ('A', 'C') for d in ('S', 'E', 'Ec')]
    ab = [next(r for r in agreement if (r['dimension'], r['component'], r['group'], r['weighting']) ==
               (d, 'probability_canonical', 'ALL', 'eligible_design_weighted'))['metrics']['kappa']['estimate'] for d in DIMS]
    rewrite(55, '编码员A与编码员B在安全性、有效性、经济性、创新性、公平性上的κ依次为' + '、'.join(f3(v) for v in ab) + '。'
            + f'安全性、有效性、经济性方面，自动规则编码与A、B的κ为{min(kr):.3f}—{max(kr):.3f}，LLM编码为{min(kl):.3f}—{max(kl):.3f}。'
            + f'创新性方面，自动规则编码对A、B的κ分别为{metric(rule,"A","I","kappa"):.3f}、{metric(rule,"C","I","kappa"):.3f}，LLM编码为{metric(llm,"A","I","kappa"):.3f}、{metric(llm,"C","I","kappa"):.3f}；'
            + '两位编码员自身在该维度的一致性较低，机器方法的表现需结合参照分歧解释。'
            + f'公平性方面，自动规则编码对A、B的κ为{metric(rule,"A","F","kappa"):.3f}、{metric(rule,"C","F","kappa"):.3f}，LLM编码为{metric(llm,"A","F","kappa"):.3f}、{metric(llm,"C","F","kappa"):.3f}。'
            + f'以A为参照，LLM编码的F1高于自动规则编码（{metric(llm,"A","F","f1"):.3f}对{metric(rule,"A","F","f1"):.3f}）；以B为参照则较低（{metric(llm,"C","F","f1"):.3f}对{metric(rule,"C","F","f1"):.3f}），方法排序随参照变化。')
    distributions = ['、'.join(f'{share(rule,g,d):.2f}%' for d in DIMS) for g in GROUPS]
    rewrite(66, f'全量编码呈现不同的五维注意力配置（表3、图2）。自动规则编码结果中，药监安全性、有效性、经济性、创新性、公平性的注意力占比分别为{distributions[0]}；医保分别为{distributions[1]}；卫健分别为{distributions[2]}。药监关注风险及疗效证据，医保突出经济价值与支付安排，卫健的公平性和安全性在本口径中占比较高。')
    directional_comparisons = []
    for one,two in combinations(GROUPS,2):
        for d in DIMS:
            differences = [share(m,one,d)-share(m,two,d) for m in methods]
            directional_comparisons.append((one,two,d,(differences[0]>0)-(differences[0]<0)==(differences[1]>0)-(differences[1]<0)))
    assert [(one,two,d) for one,two,d,same in directional_comparisons if not same] == [('NHSA','NHC','I')]
    rewrite(71, '在3组部门配对与5个维度组成的15项注意力占比差比较中，自动规则编码与LLM编码有14项点估计方向一致。'
            + f'创新性的医保—卫健比较方向不同：自动规则编码分别为{share(rule,"NHSA","I"):.2f}%、{share(rule,"NHC","I"):.2f}%，LLM编码分别为{share(llm,"NHSA","I"):.2f}%、{share(llm,"NHC","I"):.2f}%。'
            + '主口径中，两种方法的安全性、有效性和创新性注意力占比均以药监最高，经济性以医保最高，公平性以卫健最高。')
    fair_reversals = [r['scenario'] for r in findings['composition56'] if
                     r['methods'][rule]['departments']['NHSA']['profile']['attention_share']['F'] >
                     r['methods'][rule]['departments']['NHC']['profile']['attention_share']['F']]
    assert fair_reversals == ['policy_series_equal']
    rewrite(72, '方法间的注意力占比差异同时受维度编码句次与五维合计影响。'
            + f'药监安全性在自动规则编码与LLM编码中分别为{count(rule,"NMPA","S")}/{total(rule,"NMPA")}（{share(rule,"NMPA","S"):.2f}%）和{count(llm,"NMPA","S")}/{total(llm,"NMPA")}（{share(llm,"NMPA","S"):.2f}%）；'
            + f'医保经济性分别为{count(rule,"NHSA","Ec")}/{total(rule,"NHSA")}（{share(rule,"NHSA","Ec"):.2f}%）和{count(llm,"NHSA","Ec")}/{total(llm,"NHSA")}（{share(llm,"NHSA","Ec"):.2f}%）。'
            + '前一比较中LLM编码识别的安全性句次更多而相对占比较低，后一比较中经济性句次和相对占比均较高。全量56种文件构成口径中，两种方法均保留医保经济性注意力占比高于卫健的方向；自动规则编码的公平性占比在系列等权时转为医保高于卫健。全量分布与概率样本估计分别对应所收集文本及剩余规范代表框。')
    ranges = {}
    for m in methods:
        lo, hi = detail('Ec', 'F', 'NHSA', 'NHC')['methods'][m]['composition56']['difference_percentage_point_range']
        ranges[m] = f'{-hi:.2f}—{-lo:.2f}'
    rewrite(75, '注意力占比之外，经济性单元中的公平性比例进一步呈现部门差异。医保经济性注意力占比高于卫健，而经济性单元中的公平性比例，'
            + f'自动规则编码中卫健为{condtext(rule,"NHC","Ec","F")}、医保为{condtext(rule,"NHSA","Ec","F")}；LLM编码中分别为{condtext(llm,"NHC","Ec","F")}和{condtext(llm,"NHSA","Ec","F")}。'
            + f'在6种定义及56种文件构成口径中，两种方法均保留卫健这一比例更高的方向；文件构成检查中，卫健减医保的差值范围为自动规则编码{ranges[rule]}个百分点、LLM编码{ranges[llm]}个百分点。该比例呈现经济性内容中公平性的共同表达，具体用途结合条文判断（表4）。')
    rewrite(76, '从公平性内容看，公平性单元中的经济性比例则为医保高于卫健：'
            + f'自动规则编码分别为{condtext(rule,"NHSA","F","Ec")}和{condtext(rule,"NHC","F","Ec")}，LLM编码分别为{condtext(llm,"NHSA","F","Ec")}和{condtext(llm,"NHC","F","Ec")}。'
            + '这一方向同样在6种定义及56种文件构成口径中保留。以不同维度为分母，呈现的是费用内容中有多少同时涉及保障，以及保障内容中有多少同时涉及费用；两者共同说明部门注意力配置还体现为内容组合的差别。')
    rewrite(82, '医保的安全性注意力占比较低，但安全性单元中的有效性比例在两种方法中均高于药监和卫健。'
            + f'自动规则编码中，医保为{condtext(rule,"NHSA","S","E")}，药监为{condtext(rule,"NMPA","S","E")}，卫健为{condtext(rule,"NHC","S","E")}；LLM编码中分别为{condtext(llm,"NHSA","S","E")}、{condtext(llm,"NMPA","S","E")}和{condtext(llm,"NHC","S","E")}。'
            + '这两个部门比较的方向均在6种定义及56种文件构成口径中保留。《暂行办法》第七条将安全有效与临床必需、价格合理共同列为目录准入条件[36]，《申报指南》要求说明创新带来的疗效或安全性优势[39]。医保调研纪要也将安全性、有效性和经济性列为综合评审的核心内容。较低的安全性注意力占比与较高的上述条件比例共同呈现其文本关注方式，具体条款将安全有效用于准入及价值比较。')
    rewrite(110, previous[110].replace('附录保存编码员A、编码员B及裁定者T的原始判读、替代复读与复核参照来源', '配套材料保存编码员A、编码员B的独立编码结果、复核参照及原文依据'))

    # Change cell text without rebuilding table structure, fonts or widths.
    def cell_text(cell, text):
        p = cell.find('w:p', NS)
        pr = deepcopy(p.find('w:r/w:rPr', NS))
        for c in list(p):
            if c.tag != W + 'pPr':
                p.remove(c)
        r = E.SubElement(p, W + 'r')
        if pr is not None:
            r.append(pr)
        E.SubElement(r, W + 't').text = text

    rows = tables[1].findall('w:tr', NS)
    for i, (d, m) in enumerate((d,m) for d in DIMS for m in (rule,llm)):
        cells = rows[i+1].findall('w:tc', NS)
        for j, k in enumerate(('kappa', 'precision', 'recall', 'f1')):
            cell_text(cells[j+2], '/'.join(f3(metric(m,r,d,k)) for r in ('A','C')))
    figure_rows = []
    rows = tables[2].findall('w:tr', NS)
    for i, (g,m) in enumerate((g,m) for g in GROUPS for m in (rule,llm)):
        cells = rows[i+1].findall('w:tc', NS)
        for j,d in enumerate(DIMS):
            cell_text(cells[j+2], f'{share(m,g,d):.2f}')
        figure_rows.append({'group':g, 'method_role':'rules' if m == rule else 'LLM', 'denominator':total(m,g),
                            'dimensions':{d:{'exact_fraction':str(Fraction(count(m,g,d),total(m,g)))} for d in DIMS}})
    for before, after in [('价格、治疗费、支付范围、基金影响与续约','价格、治疗费、支付范围内费用、基金影响与续约'), ('创新带来的疗效安全优势、注册类别支持','创新带来的疗效安全优势、产品属性变化')]:
        matches = [c for c in tables[3].xpath('.//w:tc',namespaces=NS) if plain(c) == before]
        assert len(matches) == 1
        cell_text(matches[0], after)
    plot_path = BASE / 'outputs/coding-revision-20261007-r3/manuscript-update-20261008/emit_manuscript_after_adoption_v6.py'
    spec = importlib.util.spec_from_file_location('retained_attention_plot', plot_path)
    plot = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(plot)
    figure = Path(__file__).parent / '注意力占比采用结果.png'
    assert not figure.exists()
    plot.plot_attention(figure_rows, figure)
    assert [plain(p) for p in body.findall('w:p', NS) if re.match(r'^\[\d+\]',plain(p))] == old_refs
    fulltext = ''.join(tree.xpath('.//w:t/text()',namespaces=NS))
    assert all(s not in fulltext for s in ('待填','Pending','首次标签','编码员C','candidate07','rules-v39'))
    xml = E.tostring(tree, xml_declaration=True, encoding='UTF-8', standalone=True)
    with ZipFile(target, 'x', compression=ZIP_DEFLATED) as z:
        for name,(info,data) in parts.items():
            z.writestr(info, xml if name == 'word/document.xml' else figure.read_bytes() if name == 'word/media/image4.png' else data)

    # Preserve the separate factual implementation note, update exposure scope.
    with ZipFile(memo_source) as z:
        mp = {i.filename:(i,z.read(i.filename)) for i in z.infolist()}
    mt = E.fromstring(mp['word/document.xml'][1]);mps = mt.findall('w:body/w:p', NS)
    mtexts = [plain(p) for p in mps]
    mtexts[6] = '1 确认实际人员所用手册、材料及是否看过既有答案。原预留240条及全部原件保持不改。既往逐句审读的共享语境中已观察到17个预留族成员、涉及12族；既往模型请求的共享语境中已观察到59个成员、涉及52族。两者分别记录人工审读与模型可见范围，完整句匹配只是已发现接触的下限，不能据未命中排除部分引文或改写内容。另有01353、01361两条预留目标曾在逐句差异审查中暴露，其中01353用于修复。不能简单删掉已知目标便把余下材料称为原设计下完全未接触的独立样本；实施前需核实真实接触记录，重新落实独立判读范围和相应抽样估计。'
    mtexts[7] = mtexts[7].replace('保存首次标签','保存讨论分歧前的独立编码结果')
    mtexts[13] = mtexts[13].replace('保留首次判读','保留两名编码员的独立结果')
    mtexts[1] = mtexts[1].replace('独立首次盲评','独立盲评')
    mtexts[3] = mtexts[3].replace('独立首次判读','独立判读')
    mtexts[21] = mtexts[21].replace('独立首次判读','独立判读')
    for p,text in zip(mps,mtexts):
        if text != plain(p):
            set_text(p,text)
    mxml = E.tostring(mt, xml_declaration=True, encoding='UTF-8', standalone=True)
    with ZipFile(memo_target,'x',compression=ZIP_DEFLATED) as z:
        for name,(info,data) in mp.items():
            z.writestr(info,mxml if name=='word/document.xml' else data)

    # Export all420 same-source classification records, with explicit reference names.
    metric_names = {'kappa':'κ','agreement':'观察一致率','precision':'精确率P','recall':'召回率R','f1':'F1','left_positive_rate':'左侧编码1比例','right_positive_rate':'右侧编码1比例'}
    header = ['材料','部门','权重','比较方法','参照','维度','有效配对数','左侧编码1单元数','右侧编码1单元数']
    for kind in ('未加权','设计加权'):
        header += [kind+x for x in ('左1右1','左1右0','左0右1','左0右0')]
    for label in metric_names.values():
        header += [label,label+'近似95%区间下限',label+'近似95%区间上限',label+'区间有效重复数',label+'区间未定义重复数']
    refs = {'A':'编码员A','C':'编码员B','candidate':'复核参照（含AI复核者T判读）','symmetric A/C':'编码员A与编码员B的对称比较'}
    export = []
    for r in classification + agreement:
        o = {'材料':{'probability_canonical':'概率样本','enriched_challenge':'挑战材料'}[r['component']], '部门':GN[r['group']],
             '权重':{'unweighted':'等额样本描述','eligible_design_weighted':'部门抽样设计加权'}[r['weighting']],
             '比较方法':names[r['method']], '参照':refs[r['reference']], '维度':CN[r['dimension']],
             '有效配对数':r['paired_n'],'左侧编码1单元数':r['left_positive_n'],'右侧编码1单元数':r['reference_positive_n']}
        for kind,key in [('未加权','raw_confusion'),('设计加权','weighted_confusion')]:
            cells = r['symmetric_raw_cells' if kind=='未加权' else 'symmetric_weighted_cells'] if r['method']=='A_C' else r[key]
            for label,v in zip(('左1右1','左1右0','左0右1','左0右0'),cells.values()):
                o[kind+label] = v
        for key,label in metric_names.items():
            suffixes = ('','近似95%区间下限','近似95%区间上限','区间有效重复数','区间未定义重复数')
            if key not in r['metrics']:
                for suffix in suffixes:o[label+suffix]='不适用'
            else:
                metric_item=r['metrics'][key];ci=metric_item['ci95_primary']
                for suffix,v in zip(suffixes,(metric_item['estimate'],ci['low'],ci['high'],ci['defined_repetitions'],ci['undefined_repetitions'])):
                    o[label+suffix] = 'NA' if v is None else v
        export.append(o)
    classification_csv=OUT/'编码检验补充统计表.csv'
    with classification_csv.open('x',encoding='utf-8-sig',newline='') as f:
        cw=csv.DictWriter(f,fieldnames=header);cw.writeheader();cw.writerows(export)
    with classification_csv.open(encoding='utf-8-sig',newline='') as f:
        back=list(csv.DictReader(f))
    assert len(back)==420 and all(actual[k]==str(expected[k]) for actual,expected in zip(back,export) for k in header)
    detail_export=[]
    for r in details['rows']:
        for m,v in r['methods'].items():
            o={'编码方法':names[m],'作为条件的维度':CN[r['condition_dimension']],'共同表达的维度':CN[r['cooccurring_dimension']],'部门一':GN[r['department_one']],'部门二':GN[r['department_two']]}
            for label,key in [('部门一','one'),('部门二','two')]:
                o[label+'共同表达单元数']=v[key]['both_n'];o[label+'条件维度单元数']=v[key]['condition_positive_n'];o[label+'条件比例%']=100*v[key]['conditional_share'] if v[key]['conditional_share'] is not None else 'NA'
            o['部门一减部门二百分点']=v['difference_percentage_points']
            for key,label in [('definition6','定义口径'),('composition56','文件构成口径')]:
                a=v[key];o[label+'数']=a['scenario_n'];o[label+'部门一较高数']=a['one_higher_n'];o[label+'部门二较高数']=a['two_higher_n'];o[label+'相等数']=a['equal_n'];o[label+'未定义数']=a['undefined_n'];o[label+'差值最小百分点'],o[label+'差值最大百分点']=a['difference_percentage_point_range']
            detail_export.append(o)
    assert len(detail_export)==120
    detail_csv=OUT/'维度共同表达补充统计表.csv'
    with detail_csv.open('x',encoding='utf-8-sig',newline='') as f:
        cw=csv.DictWriter(f,fieldnames=list(detail_export[0]));cw.writeheader();cw.writerows(detail_export)
    for name in ('编码检验补充统计表说明.txt','维度共同表达补充统计表说明.txt'):
        text=(OLD/name).read_text()
        (OUT/name).write_text(text.replace('不新增判读或重新挑选结果','仅采用整套已核查编码，未按分数挑选单条标签'),encoding='utf-8')
    bindings=[source,memo_source,args.classification,args.agreement,args.findings,args.details,args.numeric_review,WORK/'整套编码采用记录.json',Path(__file__),plot_path]
    record={'status':'DOCUMENTS_AND_STATISTICS_SYNCHRONIZED_RENDER_AND_DELIVERY_REVIEW_PENDING',
            'original_sources_preserved':True,'all_project_targets_met':False,'new_independent_human_validation_completed':False,
            'table2_comparison_values':80,'table3_percentages':30,'classification_csv_records':420,'conditional_csv_records':120,
            'whole_rule39_and_whole_LLM03':True,'paragraph_changes':changes,
            'source_bindings':[{'path':str(p.resolve()),'sha256':sha(p)} for p in bindings],
            'output_bindings':[{'path':str(p.resolve()),'sha256':sha(p)} for p in OUT.iterdir() if p.is_file()]}
    record_path=Path(__file__).parent/'正文与配套统计同步核查.json'
    assert not record_path.exists()
    record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'path':str(target),'sha256':sha(target),'memo_sha256':sha(memo_target),'classification_records':420,'conditional_records':120,'requires_actual_render_review':True},ensure_ascii=False))


if __name__ == '__main__':
    main()
