"""Record the user's adjudication confirmation; remove unsupported repeatability.

No coding labels, classification values, references or machine outputs are changed.
"""
from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
from copy import deepcopy
import json,hashlib,shutil
from lxml import etree as E

HERE=Path(__file__).resolve().parent;WORK=HERE.parent;OUT=WORK/'本轮结果'
NS={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'};W='{'+NS['w']+'}'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(p.resolve()),'sha256':sha(p)}
def plain(p):return ''.join(p.xpath('.//w:t/text()',namespaces=NS))
main=OUT/'创新药评价的注意力配置差异与协调路径.docx';memo=OUT/'编码复核说明与真人检验事项.docx'
assert sha(main)=='042cf1f7154fa8b2ad915b6cbdb6948e8583a8f164fccff0f5e168868d151705'
assert sha(memo)=='ac7f161cd4ea2238c7a259df8314eb1932f14737b9498a751171d958ac76c046'
profile=WORK.parents[1]/'outputs/coding-revision-20261007-r3/statistics/candidate03_reconciled_execution_profile_v2.py'
assert "'stability_not_evaluated':True" in profile.read_text()
archive=HERE/'接入裁定与清除非同源复测前记录';archive.mkdir(exist_ok=False)
for p in (main,memo,OUT/'创新药评价的注意力配置差异与协调路径.pdf',OUT/'编码复核说明与真人检验事项.pdf',OUT/'采用文件说明.txt',OUT/'后续验证怎么做.md'):
    shutil.copy2(p,archive/p.name)
for name in ('渲染正文','渲染说明'):shutil.move(str(HERE/name),str(archive/name))
changes={}
def edit(path,updates):
    with ZipFile(path)as z:parts={i.filename:(i,z.read(i.filename))for i in z.infolist()}
    t=E.fromstring(parts['word/document.xml'][1]);ps=t.findall('w:body/w:p',NS)
    cite=next((deepcopy(r)for r in t.xpath('.//w:rPr[w:vertAlign[@w:val="superscript"]]',namespaces=NS)),None)
    import re
    changes[path.name]=[]
    for i,new in updates.items():
        p=ps[i];old=plain(p);pr=deepcopy(p.find('w:r/w:rPr',NS))
        changes[path.name].append({'paragraph_index':i,'old':old,'new':new})
        for x in list(p):
            if x.tag!=W+'pPr':p.remove(x)
        for s in re.split(r'(\[\d+(?:,\d+)*\])',new):
            if not s:continue
            r=E.SubElement(p,W+'r');rp=cite if re.fullmatch(r'\[\d+(?:,\d+)*\]',s)else pr
            if rp is not None:r.append(deepcopy(rp))
            E.SubElement(r,W+'t').text=s
    xml=E.tostring(t,xml_declaration=True,encoding='UTF-8',standalone=True)
    tmp=path.with_suffix('.repair.docx');assert not tmp.exists()
    with ZipFile(tmp,'x',compression=ZIP_DEFLATED)as z:
        for name,(info,data)in parts.items():z.writestr(info,xml if name=='word/document.xml'else data)
    tmp.replace(path)
with ZipFile(main)as z:t=E.fromstring(z.read('word/document.xml'))
ps=t.findall('w:body/w:p',NS)
edit(main,{
49:'按规范化正文归并重复单元，先排除既往开发、旧规则回归测试及预留真人验证材料所涉的同文单元组，再剔除跨部门共有组，每组取一个规范代表，形成药监947、医保760、卫健60条抽样框。按部门简单随机不放回各抽60条，共180条，卫健为框内全查；另设药监、医保各30条富集挑战材料。编码员A、编码员B的初判由AI代理按统一五维手册分别完成，现有两套结果经真人裁定后保留，作为人工审定参照。另由AI复核者T在盲态独立会话中复核分歧及一致控制项。按预定规则，T复核的66条采用其全五维判断，其余保留A、B共同判断，形成含AI判读的补充复核参照。',
50:plain(ps[50]).replace('依据两名编码员讨论分歧前的独立结果，以Cohen的κ[46]（扣除机会一致后的名义二元编码一致性）及观察一致率评价编码员间信度','以Cohen的κ[46]（扣除机会一致后的名义二元编码一致性）及观察一致率比较两套人工审定参照的一致性').replace('裁定后复核参照','补充复核参照'),
55:plain(ps[55]).replace('两位编码员自身在该维度的一致性较低','两套人工审定参照在该维度的一致性较低'),
109:'LLM编码使用gpt-5.6-sol，推理强度medium，按完整手册输出五维判断。每批最多25条，在独立批次上下文中处理同版原文及必要语境，不提供参考标签或机器预测。全量编码覆盖4924个分析单元。依Törnberg[66]关于记录任务及提示的建议，完整手册、规则、提示词与输入输出记录随研究资料留存；服务未暴露的参数记为不可得。'
})
edit(memo,{
0:'编码结果与投稿待确认事项',
1:'本说明配套当前《创新药评价的注意力配置差异与协调路径》，不属于论文正文。A、B现有结果已经真人裁定，本文据此使用，不要求重复已完成的裁定。正文表2及本说明表中的指标均由已保存标签实际计算；本说明列明结果的用途及需补齐的实施记录。',
2:'一 当前采用的人工参照与机器结果',
3:'正文统一使用编码员A、编码员B，B对应原归档中的C。A、B初判由AI代理分别完成，用户确认两套现有结果经真人裁定后保留，原标签未改。它们作为人工审定参照，用于评价机器编码。T为另外的AI复核者，含T判读的补充参照单列。统计材料为180条概率样本及60条挑战材料，二者分开计算。',
4:'表中为κ，独立四舍五入到3位；P、R、F1、四格及近似区间见同源补充统计表。旧180条按部门框规模947/760/60各抽60，卫健为框内全查。主区间每次在药监、医保层各有放回抽59个单元并作有限总体校正，卫健层固定，重复5000次；这与另行预留240条的设计不同。',
5:'二 如何使用已经完成的真人裁定',
6:'两种机器方法分别与A、B的人工审定结果比较。A—B的κ描述这两套现有参照之间的一致性，不倒记为未留存实施记录的另一轮独立真人盲评信度。对A/B仍不同的单元，应保留两套判断及真人裁定依据，按共用手册核清分歧；不能按哪套结果让机器分数更高来选择参照。',
7:'请补齐实际审定人员的相关背景、日期、所用手册、所看材料及裁定记录。这是补齐已经完成工作的记录，不是要求重新裁定。若需要形成一个统一人工最终参照，应根据真人对实际分歧的裁定形成，并另行绑定文件。',
8:'机器检验报告κ、精确率、召回率、F1、四格与区间；随后在同样本、同权重及同一分母下比较注意力占比及本文强调的条件比例。不能只因两种机器方法一致就认定正确，也不能仅因一个κ未到0.80就否定全部文本结论。',
9:'如另行开展独立外部验证，再冻结方法、登记既往开发接触范围并确定抽样设计。原预留材料有共享语境接触记录，不直接沿用完全未接触的说法；这些技术记录另存于验证材料登记目录，不与当前人工裁定完成状态混淆。',
10:'当前主口径中，两种机器方法的最高注意力维度相同，15项部门差值比较有14项方向一致，医保—卫健创新性排序不同。需要逐句核查该差异及创新性、公平性的错误类型，并判断是否影响论文具体结论，不为凑一致而改标。',
11:'三 指标的判断方式',
12:'0.80是此前约定的项目检查目标，不是《科学决策》统一发表线。Artstein与Poesio（2008）指出，不宜用一个阈值判断所有用途，发表判断还需考虑标注过程及对下游结果的独立评价。Halterman与Keith（2026）主张按任务设定分类表现目标，并做人工标签评估、行为测试和错误分析；其示例目标为F1超过0.7，不能移作本文κ门槛。',
13:'固定原180条、A/B标签和设计权重下，任意一套二元创新性判定同时对A、B的较小κ最多为0.710311，已有独立精确核查。因此，不可能保持两套参照不变又靠修代码使双方均达到0.80；应核查真实参照分歧与原文，不把人工裁定的完成等同于指标自动通过。',
20:'六 投稿前补齐的资料',
21:'补齐已经完成的真人裁定人员、日期及原始记录；补齐作者顺序、单位中英文名称、通信作者、基金信息及访谈纪要使用授权。保留现有真实低值及其解释，完成正文与配套统计的一致核对。本文只报告实际实施过程，不提前承诺录用或未实施的检验结果。'
})
record={'status':'TEXT_CORRECTIONS_APPLIED_NUMERICAL_SOURCES_UNCHANGED_NEW_RENDER_PENDING',
 'human_adjudication_confirmed_by_user':True,'original_AB_labels_changed':False,'new_independent_blind_human_session_claimed':False,
 'unbound_75_74_73_repeatability_claim_removed':True,'complete03_execution_profile':bind(profile),
 'changes':changes,'preserved_previous_documents':[bind(archive/p.name)for p in (main,memo)],
 'current_documents':[bind(main),bind(memo)],'entrypoint':bind(Path(__file__))}
(HERE/'真人裁定接入与复测来源纠正.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(record['current_documents'],ensure_ascii=False))
