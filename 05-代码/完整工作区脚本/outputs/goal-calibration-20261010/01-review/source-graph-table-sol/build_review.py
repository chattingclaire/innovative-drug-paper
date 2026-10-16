#!/usr/bin/env python3
"""Serialize manually inspected source-only findings; no coding or sampling."""
import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
JOB_PATH = ROOT / '01-review/context-projection-sol/full-frame-preflight/grouped-source-review-jobs-v6.jsonl'
CANONICAL_PATH = ROOT / '01-review/context-projection-sol/full-frame-preflight/canonical_source_context-v7.jsonl'
JOB_SHA = 'bf5e2a3c2b1fd6502c3a33185e87091d84f47857ff29634ca3a764aef47102d8'
CANONICAL_SHA = '007342cd7f89681258bb5fbd31a3c6ae6b8f6cd6f013f97329aa0dcdee799974'
JOBS = [json.loads(l) for l in (OUT / 'selected-jobs.jsonl').read_text().splitlines()]
OCCS = [json.loads(l) for l in (OUT / 'selected-canonical-fields.jsonl').read_text().splitlines()]
ADDITIONAL_BINDING = json.loads((OUT/'additional-input-binding.json').read_text())
JOBS.append(json.loads((OUT/'additional-selected-job.json').read_text()))
OCCS.extend(json.loads(l) for l in (OUT/'additional-selected-canonical-fields.jsonl').read_text().splitlines())

def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()

def dump(p, v):
    p.write_text(json.dumps(v, ensure_ascii=False, indent=2) + '\n')

def edge(a, b, label=None, style='connector', head='not_visible'):
    return {'from': a, 'to': b, 'label': label, 'line_style': style, 'arrowhead': head}

def page_asset(i):
    j = JOBS[i]
    return f"pages/{j['actual_primary_source_sha256'][:16]}-physical-{j['physical_pages'][0]:03d}.png"

def literal(label, **kw):
    return dict(text=label, representation='visible_label_linebreak_normalized', **kw)

def workflow(i, dates, year):
    lines = JOBS[i]['full_source_field_text'].splitlines()
    rows = [x.split(' | ', 1) for x in lines if ' | ' in x and not x.startswith('工作流程')]
    names = ['准备', '申报', '专家评审', '谈判/竞价/价格协商', '公布结果']
    out = {
        'type': 'workflow_with_two_columns', 'caption': '图1：工作流程图',
        'column_headers': [literal('工作流程'), literal('主要内容')],
        'rows': [], 'edges': [], 'merge_geometry': {
            'grid_cell_merges': [],
            'observed': '不是普通全网格表。左侧五个阶段框与右侧五组项目对应；右侧各组以横向虚线分隔。一个左阶段框对应该组全部右侧项目，不按换行拆成独立阶段。'
        },
        'annual_identity': year,
        'unverified_external_targets': [],
    }
    for n, ((stage, contents), name, date) in enumerate(zip(rows, names, dates), 1):
        if i == 0 and name == '专家评审':
            contents = contents.replace('完善评审数据库：', '完善评审数据库。', 1)
        out['rows'].append({
            'row_id': f'stage{n}', 'left_cell': literal(f'{name}（{date}）'),
            'right_cell_text': contents,
            'right_text_representation': '图内该组全部文字的标点/项目分隔规范化抄录；不是原文连续句，分号常代替原图独立项目。',
            'content_membership': '全部右侧文字属于本阶段；专家评审的①②③仅属于专家评审项目，不是五阶段全图编号。',
        })
        if n < 5:
            out['edges'].append(edge(f'stage{n}', f'stage{n+1}', style='blue_solid', head='downward'))
    out['version_specific_visible_content'] = (
        ['商保价格协商成功后签署承诺书；出现现场价格协商；基本目录谈判失败后进入价格协商。', '发布2026年基本目录和商保创新药目录。']
        if i == 0 else
        ['商保价格协商成功后签署协议；协商规则、具体协议条款将在征求相关方意见后另行确定；基本目录谈判失败后进入价格协商。', '发布2025年基本目录和商保创新药目录。']
    )
    return out

FACTS = {}
FACTS[0] = workflow(0, ['4-5月', '6-7月', '7-8月', '8-9月', '10-11月'], 2026)
FACTS[1] = workflow(1, ['6-7月', '7月', '8-9月', '9-10月', '10-11月'], 2025)

OUTSIDE26 = [
    '2021年1月1日（含、下同）至2026年6月10日（含、下同）期间，经国家药监部门批准上市或已完成技术审评的新通用名药品',
    '2021年1月1日至2026年6月10日期间，经国家药监部门批准或已完成技术审评，适应症或功能主治发生重大变化，且针对此次变更获得药品批准证明文件的药品',
    '2020年1月1日后国家药监部门附条件批准上市且于2023年1月1日至2026年5月31日期间转为常规批准的新通用名药品（不含新适应症或功能主治）',
    '纳入现行版《国家基本药物目录》的药品',
    '纳入《商业健康保险创新药品目录》（2025年）的药品',
    '纳入鼓励仿制药品目录或鼓励研发申报儿童药品清单，且于2026年6月10日前，经国家药监部门批准上市或已完成技术审评的药品',
    '2026年6月10日前，经国家药监部门批准上市或已完成技术审评的罕见病治疗药品',
    '2020年1月1日（含）以后谈判准入的品种，因未能成功续约而被调出目录的，首个同通用名药品于2021年1月1日至2026年5月31日期间获批上市',
]
OUTSIDE25 = [
    '2020年1月1日（含、下同）至2025年6月30日（含、下同）期间，经国家药监部门批准上市的新通用名药品',
    '2020年1月1日至2025年6月30日期间，经国家药监部门批准，适应症或功能主治发生重大变化，且针对此次变更获得药品批准证明文件的药品',
    '纳入《国家基本药物目录（2018年版）》的药品',
    '纳入鼓励仿制药品目录或鼓励研发申报儿童药品清单，且于2025年6月30日前，经国家药监部门批准上市的药品',
    '2025年6月30日前，经国家药监部门批准上市的罕见病治疗药品',
]

def basic_directory(i, year):
    is26 = year == 2026
    prefix = '①②③④⑤⑥⑦⑧' if is26 else [None] * 5
    outside = OUTSIDE26 if is26 else OUTSIDE25
    # These explicit memberships and logical operators were read from the image.
    # Numeric node IDs are identifiers here, not invented source numbering.
    adjust = (
        ['2026年12月31日协议到期且不申请调整医保支付范围的谈判药品',
         '2026年12月31日协议到期且适应症或功能主治未发生重大变化，因适应症或功能主治与医保支付范围不一致，主动申请调整支付范围的谈判药品',
         '2021年1月1日至2026年6月10日期间，经国家药监部门批准或已完成技术审评，适应症或功能主治发生重大变化，主动申请调整医保支付范围的药品']
        if is26 else
        ['2025年12月31日协议到期且不申请调整医保支付范围的谈判药品',
         '2025年12月31日协议到期且适应症或功能主治未发生重大变化，因适应症或功能主治与医保支付范围不一致，主动申请调整支付范围的谈判药品',
         '2020年1月1日至2025年6月30日期间，经国家药监部门批准，适应症或功能主治发生重大变化，主动申请调整医保支付范围的药品']
    )
    removal = (
        ['未按协议约定保障市场供应的谈判药品',
         '近3年未向医保定点医疗机构供应或医保信息平台上无交易量的常规目录药品',
         '说明书中禁忌/不良反应/注意事项内容为“尚不明确”，且未在规定时间内完善的中成药',
         '其他：《暂行办法》中第九、十条规定的药品']
        if is26 else
        ['近3年未向医疗机构供应的常规目录药品', '未按协议约定保障供应的谈判药品', '其他：《暂行办法》中第九、十条规定的药品']
    )
    simple_conditions = [
        {'source_number': '①', 'text': '独家药品'},
        {'source_number': '②', 'alternatives_by_agreement_status': [
            {'status_label': '协议到期', 'text': '本协议期实际发生的纳入支付范围的药品费用未超过预算的200%'},
            {'status_label': '协议未到期', 'text': '目录调整当年实际发生的纳入支付范围的药品费用未超过当年纳入支付范围的药品费用预算的200%'}]},
        {'source_number': '③', 'alternatives_by_agreement_status': [
            {'status_label': '协议到期', 'text': '未来两年纳入支付范围的药品费用预算增幅合理'},
            {'status_label': '协议未到期', 'text': '未来一年因调整支付范围所致的纳入医保支付范围的药品费用预算增幅不超过100%'}]},
        {'source_number': '④', 'text': '市场环境未发生重大变化'},
    ]
    routine_second = ('连续纳入目录谈判药品部分达8年且调整当年协议到期的药品，确定支付标准后纳入' if is26 else '连续纳入目录谈判药品部分达8年的药品，按续约规则处理后纳入')
    renegotiate = [
        '不符合【简易续约】条件的药品' if is26 else '不符合【纳入常规目录管理】和【简易续约】条件的药品',
        '主动申请重新谈判的1类化药药品、1类治疗生物制品、1类中药',
        '调整支付范围的药品，不同意按照《续约规则》中的（二）调整支付标准',
    ]
    out = {
        'type': 'branched_flow_diagram', 'caption': '图2：基本目录申报全流程示意图', 'annual_identity': year,
        'stage_bands': ['申报阶段', '专家评审阶段', '谈判/竞价阶段', '公布结果阶段'],
        'root_label': '基本目录调整',
        'visible_labels_note': '下列节点抄录去掉图内换行；括号、引号与多余书名号的原版字形须以原图为准。结构中的节点ID/关系键为中性表示，不是原图新增文字。',
        'membership_groups': [
            {'group_id': 'outside', 'label': '目录外药品', 'heading': '调整范围',
             'pointer': '详见《工作方案》和《申报指南》',
             'leaves': [literal(t, node_id=f'outside_{n}', source_number=prefix[n-1]) for n,t in enumerate(outside,1)],
             'numbering_note': '原图八项有①至⑧。' if is26 else '原图五项没有①至⑤；本文件的node_id不代表原图条件编号。'},
            {'group_id': 'inside_adjust', 'label': '目录内药品', 'subgroup_label': '调整',
             'leaves': [literal(t, node_id=f'adjust_{n}', source_number='①②③'[n-1] if is26 else None) for n,t in enumerate(adjust,1)]},
            {'group_id': 'inside_remove', 'label': '目录内药品', 'subgroup_label': '调出',
             'leaves': [literal(t, node_id=f'remove_{n}', source_number=None) for n,t in enumerate(removal,1)]},
        ],
        'review_nodes': [literal(x) for x in (['拟谈判/竞价调入','拟直接调入','拟价格协商','未通过评审'] if is26 else ['拟谈判/竞价调入','拟直接调入','未通过评审'])],
        'branch_relations': [
            edge('outside', '拟谈判/竞价调入'), edge('outside','拟直接调入'), edge('outside','未通过评审'),
            edge('未通过评审','不调入'),
            edge('inside_adjust','药品所属类别'), edge('药品所属类别','谈判药品'), edge('药品所属类别','非谈判药品'),
            edge('谈判药品','拟按续约规则处理'), edge('非谈判药品','按专家评审意见处理'),
            edge('inside_remove','拟直接调出'),
            edge('拟按续约规则处理','纳入常规目录乙类管理'), edge('拟按续约规则处理','简易续约'), edge('拟按续约规则处理','重新谈判'),
        ],
        'negotiation': {
            'parent': '拟谈判/竞价调入', 'label': '谈判新增',
            'measurement_siblings': ['药经组测算','基金组测算'],
            'result_label': '形成医保底价，开展现场谈判',
            'comparisons': [
                {'condition_text': '企业可接受价格≤医保底价', 'outcome': '谈判成功：该药品纳入目录'},
                {'condition_text': '企业可接受价格＞医保底价', 'outcome': '谈判失败：该药品不纳入目录'}],
        },
        'competitive_bidding': {
            'parent': '拟谈判/竞价调入', 'label': '竞价新增', 'member_note': '非独家药品', 'pointer': '详见《竞价规则》',
            'comparison_box': '企业报价与医保底价比较',
            'comparisons': [
                {'condition_text': '有一家企业报价≤医保底价', 'outcome': '竞价成功：该通用名纳入目录'},
                {'condition_text': '所有企业报价＞医保底价', 'outcome': '竞价失败：该通用名不纳入目录'}],
            'collaborative_management': {
                'label':'协同管理', 'text':'挂网价超过竞价确定支付标准1.8倍予以黄标，3倍予以红标',
                'attached_to':'竞价成功分支', 'visual_geometry':'橙色大括号由竞价成功结果旁接至协同管理框'} if is26 else None,
        },
        'direct_admission_example': literal('如：符合条件且通过专家评审的，国家组织集中带量采购中选药品和政府定价药品（如麻醉药品、一类精神药品等）'),
        'renewal': {
            'parent': '拟按续约规则处理', 'pointer': '详见《续约规则》',
            'routine': {'label':'纳入常规目录乙类管理', 'operator_text':'*需满足任一条条件', 'operator':'any',
                        'members':[literal('非独家药品',node_id='routine_nonexclusive'), literal(routine_second,node_id='routine_8years')]},
            'simple': {'label':'简易续约', 'operator_text':'*需同时满足以下条件', 'operator':'all', 'conditions':simple_conditions,
                       'payment_scope_branches': [
                           {'scope_label':'不调整支付范围','steps':['以比值A为基准，确定支付标准的下调比例']},
                           {'scope_label':'调整支付范围','steps':['先计算原支付范围的下调比例，形成初步支付标准','确定比值B，在初步支付标准上进行调整，形成最终支付标准']}],
                       'membership_note':'②中的两种协议状态是同一编号内的对应情形；③同理。不得将这些状态另计为并列①②③④之外的条件。'},
            'renegotiation': {'label':'重新谈判','shared_condition':'独家药品','operator_text':'*需满足任一条条件','operator':'any',
                              'members':[literal(x,source_number=None) for x in renegotiate]},
        },
        'publication_box': literal('发布最新版基本目录'),
        'connector_note':'四阶段以左至右版面表达；大多数灰色支路是折线/括线，未看见箭头头部。当前线性文本中的→是关系表示，不是声称原图每条线有箭头。图中的彩色括线确定一组成员，不能把同一阶段全部文字继承给每一条叶支路。',
        'merge_geometry': {'spreadsheet_cell_merges': [], 'observed':'流程图的浅色阶段底带和支路括线，不是合并表格单元格。'},
        'unverified_external_targets': ['《工作方案》','《申报指南》','《续约规则》','《竞价规则》','《暂行办法》第九、十条'],
    }
    if is26:
        out['branch_relations'].append(edge('outside','拟价格协商'))
        out['branch_relations'].append(edge('拟价格协商','图3','详见图3'))
        out['unverified_external_targets'].append('图3')
        out['renewal']['routine']['market_branches'] = {
            'attached_only_to_node_id':'routine_8years',
            'not_attached_to':'routine_nonexclusive',
            'branches': [
                {'label':'市场环境未发生重大变化','calculation_heading':'下调比例计算方式取方法1和方法2中的高值',
                 'methods':['方法1：按简易续约规则确定下调比例','方法2：本协议期实际发生的纳入支付范围的年均实际药品费用＞3亿元的，支付标准下调10个百分点']},
                {'label':'市场环境发生重大变化','outcome':'通过重新谈判确定支付标准'},
            ],
        }
    else:
        out['typography_note'] = '目录外基本药物项在原图可见多余/叠写书名号字形；本文件使用正式名称的规范化表示。未把原图作者的排版符号当作实质错字，未以未查验的其他版本替换。具体符号见faq25-members裁图。'
    return out

FACTS[2] = basic_directory(2,2026)
FACTS[3] = basic_directory(3,2025)
FACTS[4] = {
    'type':'branched_flow_diagram','caption':'评价流程简图',
    'visible_labels':[literal(x) for x in ['药品临床综合评价信息平台','主题遴选','评价实施','结果应用转化','项目委托','结果递交','结果验收','质量控制']],
    'edges':[
        edge('主题遴选','评价实施',style='solid',head='downward'),
        edge('评价实施','结果应用转化',style='solid',head='downward'),
        edge('评价实施','implementation_container',style='solid',head='rightward'),
        edge('质量控制','implementation_container',style='solid',head='leftward'),
        edge('结果应用转化','application_container',style='solid',head='downward'),
        edge('药品临床综合评价信息平台','outer_process_container',style='solid',head='bidirectional'),
        edge('A类','A_recommendation',style='solid',head='rightward'),
        edge('B类','B_recommendation',style='solid',head='rightward'),
        edge('C类','C_recommendation',style='solid',head='rightward'),
        edge('D类','D_recommendation',style='solid',head='rightward'),
    ],
    'containers':[
        {'node_id':'outer_process_container','border':'dashed','members':['主题遴选','评价实施','结果应用转化','implementation_container','质量控制','application_container','A_recommendation','B_recommendation','C_recommendation','D_recommendation']},
        {'node_id':'implementation_container','border':'dashed','members':['项目委托','结果递交','结果验收'],'internal_edges':[],
         'note':'三个模块在同一虚线框内；没有画出项目委托→结果递交→结果验收的逐个连线。质量控制指向该共同框，平台双向箭头指向最外流程框。'},
        {'node_id':'application_container','border':'dashed','members':['A类','B类','C类','D类'],
         'note':'四类证据/结果框在左侧共同虚线容器内；各自向右箭头连接四个建议框。建议框在该左侧容器之外，但仍在最外流程框之内。'},
    ],
    'application_members':[
        {'label':'A类','condition_text':'证据充分、结果确定','recommendation_text':'建议可直接按程序转化为基本临床用药管理相关政策结果'},
        {'label':'B类','condition_text':'证据比较充分、结果明确','recommendation_text':'建议按程序有条件转化为基本临床用药管理相关政策结果'},
        {'label':'C类','condition_text':'有一定证据支持、部分结果明确','recommendation_text':'建议在一定区域范围内或特定医疗机构内按程序转化为基本临床用药管理相关政策结果'},
        {'label':'D类','condition_text':'证据不足、结果不确定','recommendation_text':'不建议转化政策结果'},
    ],
    'merge_geometry':{'grid_cell_merges':[],'observed':'虚线共同容器与分支框，不是表格合并单元格。'},
    'unverified_external_targets':[],
}

def bid_example():
    return {
        'type':'geometric_price_examples','caption':'图4 竞价药品医保支付标准确定示例图',
        'axis_labels':[literal('医保支付意愿70%'),literal('医保支付意愿100%')],
        'row_labels':[literal(f'情形{x}') for x in range(1,6)],
        'rows':[
            {'row':'情形1','left_to_right':['企业A报价','企业B报价','医保支付意愿70%','医保支付意愿100%'], 'output':'医保支付标准=医保支付意愿的70%'},
            {'row':'情形2','left_to_right':['企业B报价','医保支付意愿70%','企业A报价','医保支付意愿100%'], 'output':'医保支付标准=医保支付意愿的70%'},
            {'row':'情形3','left_to_right':['医保支付意愿70%','企业A报价','企业B报价','医保支付意愿100%'], 'output':'医保支付标准=企业A报价'},
            {'row':'情形4','left_to_right':['医保支付意愿70%','企业A报价','医保支付意愿100%','企业B报价'], 'output':'医保支付标准=企业A报价'},
            {'row':'情形5','left_to_right':['医保支付意愿70%','医保支付意愿100%','企业A报价','企业B报价'], 'output':'竞价失败'},
        ],
        'geometry': '五个独立横向浅色带；70%与100%的两条纵向虚线贯穿五带，企业报价位置在各横带中独立标示，结果在各带右侧。结果指示用可见箭头；不可将相邻横带的报价或结果串联。',
        'quotation_note':'严格不等关系来自相对位置，原图未印P、0.7P或这些不等式。原图A/B出现于企业A报价/企业B报价的标签中。P及等式/不等式在旧转写中是解释用符号，不能作为原文连续引文。',
        'unverified_or_unstated':['报价恰等于70%或100%时的规则并未由本示例图单独展示。','图上空间间距不表示未印出的价格数值。'],
        'merge_geometry':{'grid_cell_merges':[],'observed':'五个示例横带，不是合并表格单元格。'},
        'unverified_external_targets':[],
    }

FACTS[5] = bid_example()
FACTS[6] = bid_example()
FACTS[5]['annual_identity'] = 2026
FACTS[6]['annual_identity'] = 2025
FACTS[7] = {
    'type':'styled_branched_flow_diagram','caption':'图1 支持药物监管决策的真实世界研究路径（实线所示）',
    'nodes':[
        literal('研究目的',node_id='purpose'),literal('研究方案',node_id='protocol'),literal('RWD',node_id='rwd'),
        literal('不适用RWD',node_id='inapplicable'),literal('适用RWD',node_id='applicable'),literal('自然人群',node_id='natural'),
        literal('临床人群',node_id='clinical'),literal('RWE',node_id='rwe_upper_black'),literal('RWE',node_id='rwe_middle_red'),
        literal('RWE',node_id='rwe_lower_black'),literal('有效RWE',node_id='valid'),literal('无效RWE',node_id='invalid'),literal('其它',node_id='other'),
    ],
    'edges':[
        edge('purpose','protocol',style='red_solid',head='leftward'),
        edge('protocol','rwd','数据收集',style='red_solid',head='leftward'),
        edge('rwd','applicable','数据治理与适用性评估',style='red_solid',head='downward'),
        edge('rwd','inapplicable','数据治理与适用性评估',style='black_dashed',head='downward'),
        edge('applicable','natural',style='red_solid',head='not_visible'),
        edge('natural','clinical',style='red_solid',head='downward'),
        edge('natural','rwe_upper_black','分析',style='black_dashed',head='rightward'),
        edge('clinical','analysis_junction','分析',style='red_solid',head='rightward'),
        edge('analysis_junction','rwe_middle_red',style='red_solid',head='rightward_after_upward_elbow'),
        edge('rwe_middle_red','valid','证据充分',style='red_solid',head='rightward'),
        edge('rwe_middle_red','invalid','证据不充分',style='red_solid',head='rightward'),
        edge('analysis_junction','rwe_lower_black',style='black_dashed',head='rightward_after_downward_elbow'),
        edge('rwe_lower_black','other',style='black_dashed',head='rightward'),
    ],
    'geometry_notes':[
        '三个RWE框位置不同，不能因为文字相同合并为同一节点。',
        '实线/虚线按原图区分；无效RWE并没有连向“其它”的箭头。',
        '自然人群直至上方黑框RWE的虚线和临床人群分析支路至下方黑框RWE的虚线各有独立连接，不能混入红色中框路径。',
    ],
    'merge_geometry':{'grid_cell_merges':[],'observed':'节点矩形与实/虚线支路，没有表格合并单元格。'},
    'unverified_external_targets':[],
}
FACTS[8] = {
    'type':'timeline_diagram','caption':'图2 已有人用经验中药临床研发的路径之一',
    'nodes':[literal('回顾性观察性研究',node_id='retrospective'),literal('前瞻性观察性研究',node_id='prospective_main'),
             literal('探索性RCT',node_id='exploratory_rct'),literal('确证性RCT',node_id='confirmatory_after_exploration'),
             literal('确证性RCT',node_id='direct_confirmatory'),literal('前瞻性观察性研究',node_id='prospective_long')],
    'relative_time_markers':{
        'representation':'本文件用t0至t5给可见垂直对齐位置起匿名ID；原图没有印这些t编号，也没有数字化时长。',
        'order':['t0','t1','t2','t3','t4','t5'],
    },
    'bars_and_arrows':[
        {'node_id':'retrospective','color':'blue','span':['t0','t1'],'arrow_style':'blue_solid_rightward'},
        {'node_id':'prospective_main','color':'yellow','span':['t1','t4'],'arrow_style':'black_solid_rightward'},
        {'node_id':'exploratory_rct','color':'green','span':['t2','t3'],'arrow_style':'green_dashed_rightward'},
        {'node_id':'confirmatory_after_exploration','color':'green','span':['t3','t4'],'arrow_style':'green_solid_rightward'},
        {'node_id':'direct_confirmatory','color':'green','span':['t2','t4'],'arrow_style':'green_solid_rightward'},
        {'node_id':'prospective_long','color':'yellow','span':['t1','t5'],'arrow_style':'black_solid_t1_to_t4_then_dashed_rightward_to_t5'},
    ],
    'relationships':'上方绿色“探索性RCT/确证性RCT”一行与另一绿色“确证性RCT”一行是两种并行展示的RCT安排，均开始于前瞻性条启动之后。长前瞻性条在另一行延续越过RCT末端。图中文字未给全部研究必需先做探索性RCT或必需延续至最长条终点的要求。',
    'merge_geometry':{'grid_cell_merges':[],'observed':'条形时间结构，无表格合并单元格。'},
    'unverified_external_targets':[],
}
FACTS[9] = {
    'type':'timeline_diagram','caption':'图3 已有人用经验中药临床研发的路径之二',
    'nodes':[literal('回顾性观察性研究',node_id='retrospective'),literal('PCT',node_id='pct')],
    'bars':[{'node_id':'retrospective','color':'blue','order':1,'arrow':'blue_solid_rightward'},
            {'node_id':'pct','color':'yellow','order':2,'arrow':'black_solid_rightward'}],
    'relation':'回顾性观察性研究条的末端与PCT条起点相接。',
    'scope_note':'本图没有探索性RCT/确证性RCT、数字化时长或额外临床条件；不把同页上方图2或正文的话补为图3节点。',
    'merge_geometry':{'grid_cell_merges':[],'observed':'两条顺序时间条，无表格合并单元格。'},
    'unverified_external_targets':[],
}

LIVER_CELLS = [
    '例：肝毒性',
    '大鼠重复给药毒性试验中，某剂量可导致大鼠肝胆相关指标ALT、AST、GGT升高；犬重复给药毒性试验中，某剂量可导致犬ALT、AST、GGT升高，组织病理学检查可见部分动物肝脏纤维结缔组织增生。',
    'II期临床试验中，共报告XX例次ALT升高，XX例次AST升高，严重程度均为CTCAE 2-3级，转归均为好转/痊愈。',
    '1、持续和加强监测。在试验中明确肝功能监测周期。在后续研发过程中，可根据获得的安全性数据进行调整，必要时加强监测。\n2、制修订相关临床试验文件。如试验方案中：\n-制定入排标准，明确入组受试者时对肝功能指标的要求，排除肝脏相关重要疾病史受试者。\n-制定剂量调整、暂停用药、永久停药规则。如有额外的治疗措施也应明确。\n3、明确相关暂停/终止临床试验标准。\n……',
]
INFUSION_CELLS = [
    '例：输液反应',
    '在大鼠重复给药毒性试验中观察了伴随刺激性，某剂量皮下注射大鼠给药部位多见不同程度的炎症反应，病变包括皮下水肿、肌纤维出血、皮下出血、皮下和/或肌纤维炎症细胞浸润、皮下结缔组织增生。',
    '如适用，可列出。',
    '1、持续和加强监测。明确给药期间及给药后某一时间段内对受试者进行症状、体征密切监测。重点关注发热、寒战、恶心、呕吐、瘙痒等。\n2、制修订相关临床试验文件。如试验方案中：\n-制定入排标准，排除已知或怀疑对本研究药物任一组分过敏者，或过敏体质者。\n-制定剂量调整、暂停用药、永久停药规则。输注研究药物过程中，若受试者出现输液反应、过敏反应等情况，通常应立即停止输注并给予相应救治措施。如有额外的治疗措施也应明确。\n3、明确相关暂停/终止临床试验标准。\n……',
]

def risk_table(i, cells, section, section_page):
    return {
        'type':'four_column_table_row','section_heading':literal(section),
        'section_heading_physical_page':section_page,
        'column_headers':[literal(x) for x in ['风险','非临床数据','临床数据','控制措施']],
        'header_physical_page':section_page,
        'cells':[{'column_index':n,'column_header':h,'text':t,'representation':'单元文字抄录，图内自动换行/字间空白已规范化；省略点和罗马数字保留字形含义，不声称还原PDF内部Unicode码点。'} for n,(h,t) in enumerate(zip(['风险','非临床数据','临床数据','控制措施'],cells),1)],
        'merge_geometry':{'merged_cells':[],'vertical_boundaries':'四列有连续竖线；本行中没有跨列合并。控制措施的1、2（含两个短横线子项）、3和省略点全部在第4列。',
                          'cross_page_relationship':'上页同一表头/节标题续行，不因本页未重复列头而改变列序。'},
        'row_geometry_region_220dpi':[275,220,1544,1920] if i==10 else [275,220,1544,2330],
        'geometry_region_note':'上述边界为读图用约数，格式[x0,y0,x1,y1]。字形与准确边线以所附原图为准。',
        'source_author_typography_note':('XX是原文占位符，未作为实际样本数字；II/罗马字形不推断原PDF的字符编码。' if i==10 else '“观察了伴随刺激性”是原件文字；本次不作语法润色。“如适用，可列出。”属于第3列临床数据。'),
        'not_this_row_heading':'4.1.2重要的潜在风险' if i==10 else None,
        'unverified_external_targets':[],
    }
FACTS[10] = risk_table(10,LIVER_CELLS,'4.1.1重要的已识别风险',17)
FACTS[11] = risk_table(11,INFUSION_CELLS,'4.1.2重要的潜在风险',18)
FACTS[12] = {
    'type':'branched_flow_diagram','caption':'图3：商保创新药目录申报全流程示意图','annual_identity':2025,
    'root_label':'商保创新药目录调整',
    'stage_bands':['申报阶段','专家评审阶段','价格谈判/协商阶段','公布结果阶段'],
    '申报阶段':{
        'column_headers':['申报条件','申报目录类别'],'pointer':'详见《工作方案》',
        'shared_parent':'基本目录外独家药品',
        'conditions':[
            literal('2020年1月1日至2025年6月30日（含）期间，经国家药监部门批准上市的新通用名药品，仅因转产、再注册等单纯更改通用名的药品除外。',source_number='条件1'),
            literal('2025年6月30日（含）前经国家药监部门批准上市，说明书适应症或功能主治中包含有国家卫生健康委《第一批罕见病目录》《第二批罕见病目录》所收录罕见病的药品。',source_number='条件5'),
        ],
        'condition_geometry':'左侧基本目录外独家药品框经灰色分支括线连接条件1、条件5；两项右侧黑色共同大括号。保留1/5原编号，不改成1/2。',
        'operator_printed':False,'logical_operator_from_this_figure':None,
        'operator_note':'原图没有印“或”或“且”。当前线性文本的“或”不是图内原文字，图本身仅能直接证实共同父节点和两项成员；逻辑连接若需作为具体条件必须核同版《工作方案》，本次未扩查。',
        'application_category_boxes':[
            literal('《商保创新药目录》'),literal('《基本目录》《商保创新药目录》')],
        'category_note':'图中两个彩色申报类别框，并非印有“或”的一条连续句。',
    },
    'expert_review':{
        'column_headers':['专家评审','商保专家评审'],
        'suggestion_nodes':[
            literal('建议仅纳入《基本目录》',node_id='basic_only'),
            literal('建议仅纳入《商保创新药目录》',node_id='commercial_only'),
            literal('建议纳入《基本目录》（先），《商保创新药目录》（后）',node_id='basic_then_commercial')],
        'commercial_review_node':literal('形成最终建议名单',node_id='final_commercial_list'),
        'edges':[edge('basic_only','谈判',style='black_dashed',head='rightward'),
                 edge('commercial_only','final_commercial_list',style='blue_solid',head='rightward'),
                 edge('basic_then_commercial','final_commercial_list',style='blue_solid',head='rightward')],
        'shared_node_scope':'形成最终建议名单这一纵向框接受中/下两条蓝色箭头；不把该商保专家评审节点共用到上方仅基本目录建议。',
    },
    'negotiation_and_consultation':[
        {'branch':'basic_only','node':literal('谈判'),'pointer':'详见图2'},
        {'branch':'commercial_only','node':literal('价格协商'),
         'outcomes':[literal('协商成功：纳入《商保创新药目录》'),literal('协商失败：该药品不纳入')]},
        {'branch':'basic_then_commercial','node':literal('先谈判'),
         'outcomes':[{'condition':'谈判成功','outcome':'纳入《基本目录》'},
                     {'condition':'谈判失败','next_node':'谈判失败，再价格协商','outcomes':[
                         literal('协商成功：纳入《商保创新药目录》'),literal('协商失败：该药品不纳入')]}]},
    ],
    'publication_node':literal('发布商保创新药目录'),
    'connector_note':'向右的蓝色实箭头与上方黑色虚箭头实际可见；价格协商和先谈判后续结果为灰色括线支路，不把所有线写成可见箭头。阶段底带及纵向形成名单框不是表格合并单元格。',
    'merge_geometry':{'grid_cell_merges':[],'observed':'四阶段底带、条件括号、纵向共同节点，没有表格合并单元格。'},
    'unverified_external_targets':['《工作方案》中条件1/条件5的确切逻辑连接'],
    'verified_pointer_to_separately_reviewed_job':{
        'pointer_text':'详见图2','target_job_id':'SOURCEJOB-a61e41fae482e493cf77',
        'same_source_sha256':'7f5b1829d0030b3402f85d288edf764bc3195bb99ca1c419dd8605342eb70d68',
        'target_physical_page':9,'note':'同版图2作为原12任务之一已单独核验；未把图2全部文字自动并入图3各分支。'},
    'current_linearized_relation_needing_confirmation':['条件1与条件5间的“或”：原图未印逻辑词，单凭大括号未验证具体OR含义；本次不据此改写原body，也不认定为已确认错误。'],
}

# Crop rectangles are exact Poppler input coordinates at the stated render DPI.
crop_specs = {
    'crops/faq25-members.png':(3,9,440,[960,600,940,1080]),
    'crops/faq25-renewal.png':(3,9,440,[2560,1680,1960,860]),
    'crops/faq26-renewal.png':(2,10,440,[2480,1700,1820,860]),
    'crops/rwe-rct.png':(8,12,440,[1700,1940,1000,560]),
    'crops/risk-header-p17.png':(10,17,440,None),
    'crops/risk-infusion-controls-p19.png':(11,19,440,[2240,400,900,4500]),
}
header_y = int((699.877360-5)*220/72)
header_h = int((744.803280+10-(699.877360-5))*220/72)
crop_specs['crops/risk-header-p17.png'] = (10,17,440,[400,header_y*2,3200,header_h*2])

def asset_manifest():
    sources = {}
    for j in JOBS:
        sources[j['actual_primary_source_sha256']] = j['actual_primary_snapshot']
    # The byte identity is rechecked here solely for already-selected files.
    source_rows = []
    for expected, name in sources.items():
        p = Path(name)
        b = p.read_bytes()
        actual = sha_bytes(b)
        assert actual == expected
        source_rows.append({'path':name,'sha256':actual,'bytes':len(b),'identity_verified':True})
    assets = []
    for p in sorted(list((OUT/'pages').glob('*.png'))+list((OUT/'crops').glob('*.png'))):
        b=p.read_bytes(); w,h=struct.unpack('>II',b[16:24]); rel=str(p.relative_to(OUT))
        if rel in crop_specs:
            i,page,dpi,rect = crop_specs[rel]
            source_sha = JOBS[i]['actual_primary_source_sha256']
            view_status='actually_viewed_crop'
            viewed_scope = '4.1.1节标题及四列标题；没有查看该页其余内容' if page==17 else '指定图表局部文字/关系放大裁图'
        else:
            prefix=p.name.split('-physical-')[0]; page=int(p.stem.split('-physical-')[1]); dpi=220; rect=None
            source_sha=next(x for x in sources if x.startswith(prefix))
            view_status='rendered_but_full_page_not_viewed' if page==17 and source_sha.startswith('2cfe') else 'actually_viewed_full_page'
            viewed_scope='仅相应header裁图实际查看' if view_status.startswith('rendered') else '指定图/表完整原页'
        assets.append({'asset_path':rel,'absolute_path':str(p),'sha256':sha_bytes(b),'bytes':len(b),'width_px':w,'height_px':h,
                       'source_sha256':source_sha,'physical_page':page,'render_dpi':dpi,'crop_xywh_at_render_dpi':rect,
                       'renderer':'pdftoppm (Poppler)','view_tool':'tools.view_image','view_detail':'original',
                       'view_status':view_status,'actual_view_scope':viewed_scope})
    return {'schema':'source-page-asset-manifest/v1','created_at_utc':datetime.now(timezone.utc).isoformat(),
            'source_pdfs':source_rows,'assets':assets,'viewed_primary_physical_page_N':12,'viewed_adjacent_header_page_N':1,
            'rendered_physical_page_N':13,'full_page_actually_viewed_N':12,'actually_viewed_crop_N':6,
            'note':'第17页完整PNG仅渲染，没有全页阅读；实际查看的是risk-header-p17.png裁图。PNG SHA是资产字节SHA，不是原PDF页本身的字节SHA。PDF字节SHA加物理页、区域构成来源定位。'}

def make_review():
    assert len(JOBS)==13 and len(OCCS)==30
    assert all(sha_bytes(j['full_source_field_text'].encode())==j['text_sha256'] for j in JOBS)
    assert all(o['text_sha256']==sha_bytes(o['value'].encode()) for o in OCCS)
    records = {o['record_id'] for o in OCCS}
    assert len(records)==15
    reviews=[]; patches=[]
    printed=[1,3,7,8,24,15,21,4,12,12,15,16,9]
    notes={
        0:['当前文字已含“工作流程 | 主要内容”。月份连字符、项目分隔和图题冒号作了规范化；“完善评审数据库：”的原图句读是“完善评审数据库。”，无实质含义变更。'],
        1:['当前文字未显式保留原图“工作流程”“主要内容”双列表头，建议补结构字段，不替换正文。','2025时间范围、签署协议/另定协商规则与2026版不同，各按本PDF核验。'],
        2:['需保留目录外①至⑧、目录内调整①至③与简易续约①至④的独立编号范围。','8年条件下的市场变化分支仅接8年叶节点，不能共用给非独家药品。','当前“续约分支一/二/三”等为线性化的说明文字，不是图上完整原文连续句。'],
        3:['2025目录外五项及目录内调整三项未印编号；不得借用2026①至⑧。','重新谈判首项是“不符合【纳入常规目录管理】和【简易续约】条件的药品”，不替换成2026表述。','额外书名号字形保留原图证据，未作实质文字修复。'],
        4:['评价实施模块内三项没有逐个顺序箭头；平台双向箭头连最外流程框。'],
        5:['五种情形位置/结果分别验证；不补恰等于阈值时的规则。'],
        6:['P/0.7P和不等式是旧转写解释用符号，图上原标签是医保支付意愿70%/100%与企业报价标签。'],
        7:['三个RWE节点分开，保留红色实线、黑色虚线及无箭头头部的连接。'],
        8:['确证性RCT字样及绿色实/虚线经放大原图查看；长前瞻性条单独记录。'],
        9:['仅图3两条时间结构；不把同页图2的RCT节点或正文条件继承为本图原字。'],
        10:['肝毒性归4.1.1重要的已识别风险，标题与四列头在物理17页，实际只读该标题裁图。','物理18页底部的4.1.2属于后一表，不是肝毒性行标题。'],
        11:['输液反应归4.1.2重要的潜在风险，节标题与四列头在物理18页底部。','剂量调整/暂停/永久停药文字确实在第4列第2项第二子项中；已放大该单元核实。'],
        12:['新增授权的v6误分类图任务；实际另查2025 PDF物理第10页（印刷9），没有复用2026物理第10页。','条件编号是1和5；当前文字的“或”不是图内显式逻辑词。原图共同父节点/成员可证实，具体OR尚未由本图单独证实。','仅商保/基本先商保后两支进入形成最终建议名单；仅基本目录一支用黑虚箭头进入谈判并指向图2。'],
    }
    for i,j in enumerate(JOBS):
        occurrences=[o for o in OCCS if o['job_id']==j['job_id']]
        assert len(occurrences)==j['occurrence_N']
        assert all(o['text_sha256']==j['text_sha256'] for o in occurrences)
        bindings=[]
        for o in occurrences:
            bindings.append({
                'record_id':o['record_id'],'context_id':o['context_id'],'field':o['field'],
                'existing_locator':o['occurrence_locator'],'existing_pages':o['occurrence_pages'],
                'canonical_source_ref':o['canonical_source_ref'],'canonical_structure':o['canonical_structure'],
                'verified_physical_pages':j['physical_pages'],'verified_printed_pages':[printed[i]],
                'text_sha256':o['text_sha256'],'exact_text_sha_match':True,
                'preserve_existing_locator_fields':True,
            })
        assets=[page_asset(i)] + [rel for rel,(ci,pg,dpi,rect) in crop_specs.items() if ci==i]
        if i==11:
            assets.append(page_asset(10))
        structure=FACTS[i]
        review={
            'job_id':j['job_id'],'source_sha256':j['actual_primary_source_sha256'],'source_path':j['actual_primary_snapshot'],
            'physical_pages':j['physical_pages'],'printed_pages':[printed[i]],'fragment_types':j['fragment_types'],
            'original_current_field_text_sha256':j['text_sha256'],'original_current_field_text':j['full_source_field_text'],
            'current_field_representation':'table_cell_linearization' if i in [0,1,10,11] else 'diagram_derived_description',
            'is_original_continuous_prose_quote':False,
            'comparison':{'status':'source_supported_geometry_with_one_unverified_logical_word' if i==12 else 'source_supported_normalized_transcription_and_geometry',
                          'substantive_word_or_column_or_condition_error_confirmed':False,
                          'literal_byte_or_typography_identity_claimed':False,
                          'note':('当前节点文字、分支归属与顺序已核；“或”的逻辑词未在原图印出，未由该图单独证实。' if i==12 else '当前字段文字与指示关系已结合原图核对；它是规范化/图解表示，不能以原图未有的连续句结构主张literal匹配。')},
            'neutral_source_structure':structure,'actual_evidence_assets':assets,'occurrence_bindings':bindings,
            'actual_source_region':{'primary_asset':page_asset(i),'region':'整张指定原页；目标为'+structure.get('caption',structure.get('section_heading',{}).get('text','')),
                                   'full_page_viewed':True,'local_magnifications':[x for x in assets if x.startswith('crops/')]},
            'review_notes':notes[i],
            'material_gap_status':'referenced_target_full_text_not_checked_in_this_scope' if structure.get('unverified_external_targets') else 'no_confirmed_source_relation_gap_for_this_graph_or_table',
            'scope_limit':'只核该图/表原件和必要跨页表头；没有验证其所援引制度全文，没有推断任何编码维度。',
            'owner_integration_required':True,
            'actual_read_canonical_version':'v8' if i==12 else 'v7',
            'actual_read_canonical_sha256':ADDITIONAL_BINDING['canonical_sha256'] if i==12 else CANONICAL_SHA,
        }
        reviews.append(review)
        patches.append({
            'schema':'neutral-source-geometry-patch/v1','patch_id':f'NEUTRAL-GRAPH-TABLE-{i+1:02d}',
            'job_id':j['job_id'],'base_canonical_sha256':ADDITIONAL_BINDING['canonical_sha256'] if i==12 else CANONICAL_SHA,'job_manifest_sha256':JOB_SHA,
            'source_sha256':j['actual_primary_source_sha256'],'expected_old_text_sha256':j['text_sha256'],
            'operation':'attach_source_representation_geometry_headers_and_verified_locator',
            'replace_body_or_context_text':False,'substantive_transcription_replacement':None,
            'targets':bindings,
            'additions':{'source_representation':review['current_field_representation'],'is_original_continuous_prose_quote':False,
                         'physical_pages':j['physical_pages'],'printed_pages':[printed[i]],
                         'source_structure':structure,'evidence_assets':assets,
                         'source_content_verification_status':'verified_nodes_and_geometry_with_unverified_or_word' if i==12 else 'verified_normalized_source_text_and_geometry',
                         'without_dimension_decision':True,
                         'source_region':review['actual_source_region']},
            'integration_note':'由主源owner以原SHA守卫统合；保留每个目标的context_id、parent_context_id、position、paragraph_id、line/page差异。新增表头/节标题可用上下文或结构表示，不静默拼成所有节点共用的原文句。统合公共输入后所有方法获得同版材料。',
            'owner_integration_required':True,
        })
    return {
        'schema':'source-graph-table-review/v1','reviewer':{'identity':'AI','agent':'pilot01_a_sol','model':'GPT-6.1 Sol','reasoning_setting':'ultra','execution':'source-only AI visual review, not human coding'},
        'completed_at_utc':datetime.now(timezone.utc).isoformat(),
        'input_bindings':{'job_manifest_path':str(JOB_PATH),'job_manifest_sha256':JOB_SHA,
                          'canonical_path':str(CANONICAL_PATH),'actual_read_canonical_sha256':CANONICAL_SHA,
                          'canonical_read_scope':'Only selected 14 records and their 28 target occurrence fields; no other bodies, labels or predictions.',
                          'additional_authorized_canonical_binding':ADDITIONAL_BINDING,
                          'skill_path':'/Users/rainbow/.codex/plugins/cache/openai-primary-runtime/pdf/26.909.12148/skills/pdf/SKILL.md'},
        'counts':{'unique_jobs':13,'diagram_jobs':9,'table_geometry_jobs':4,'occurrences':30,'distinct_records':15,
                  'source_pdfs':5,'primary_physical_pages_actually_viewed':12,'adjacent_header_physical_pages_actually_viewed':1,
                  'full_pages_actually_viewed':12,'crop_assets_actually_viewed':6,'rendered_png_assets':19,
                  'exact_current_text_sha_matches':30,'confirmed_substantive_text_replacements':0,'neutral_metadata_patches':13,
                  'figure_unverified_explicit_logical_connector_jobs':1},
        'selection':{'fragment_types':['diagram_branch_and_geometry_transcription','flattened_table_row_requires_original_cell_geometry'],
                     'additional_authorized_job':'SOURCEJOB-c9ecdc96c974ab6b6920; originally misclassified as source_literal_or_column_or_unicode_difference_requires_page_check',
                     'not_reviewed':'The other 170 scanned-PDF jobs, any labels/reference/predictions and unrelated source text.'},
        'review_method':'核原PDF字节SHA；按物理页用Poppler渲染；实际view_image原页和必要放大裁图；核13个当前textSHA及30处相等绑定；由AI逐图判读记录原节点、列头、列值、合并/共同容器、箭头、条件编号和跨页位置。代码只整理已判读事实和核哈希，不生成编码。',
        'global_findings':[
            '未发现实质错字、错列或错条件编号，正文和上下文字段保持原SHA；13个中性补丁均为结构/来源表示与定位补足。',
            '2025工作流程图原有两列头而当前字段省略；风险表两行缺跨页节标题/表头绑定，原图已核实。',
            '图解文本和表格线性化不是原文连续句；通过原节点/单元、关系、版本和原图资产提供可回查证据。',
            '指向其他规则/图3的字样只确认指针，没有扩查援引目标，也没有依据其假定结构。',
            '新增2025图3条件1/5间的“或”不是原图显式词；共同父节点与两项成员关系已核实，具体逻辑连接未由本图单独核实，交主源owner按同版工作方案处理。',
        ],
        'source_material_requests':[
            {'job_id':'SOURCEJOB-c9ecdc96c974ab6b6920',
             'current_linearized_word':'或（条件1/条件5之间）',
             'verified_from_current_figure':'基本目录外独家药品共同父节点、条件1/条件5文字及编号、共同括线成员归属。',
             'not_verified_from_current_figure':'OR/AND逻辑词：原图未显式印出。',
             'specific_needed_source':'同版2025《工作方案》/《申报指南》的商保申报条件1及条件5与其共同逻辑条款，使用既有原件快照并保留另源SHA/页/原文。',
             'status':'pending_main_source_owner_separate_source_confirmation',
             'integration_rule':'即使另源确认OR，仍标为另源条文逻辑依据；不得追认成该图所印原字。'}],
        'reviews':reviews,
        'delivery_status':'Complete source-only review for selected scope; patches require main source owner integration. Not a whole-corpus material certification or human validation.',
    }, patches

def markdown(review):
    c=review['counts']
    s=['# 指定图表来源核验（AI）','',
       '已完成 13 个唯一任务（9 图、4 表）的 30 处来源绑定，涉及 15 条记录和 5 份 PDF。实际查看 12 个指定物理页，另查看同源物理第 17 页的风险表头裁图。未生成五维判断，未改动 canonical。', '',
       '未发现实质错字、错列或错编号。13 条中性补丁补足源图表示、节点/单元关系、表头、跨页节标题和实际页定位；正文及上下文字段不替换。图解线性化没有被认证为原文连续引文。新增2025图3条件1/5之间的“或”未由原图显式文字证实，保留为主源owner需核同版工作方案的具体关系。', '',
       '执行身份为 AI，模型 GPT-6.1 Sol，ultra。本交付不是真人编码、整体材料认证或最终独立检验。', '',
       '## 输入与范围','',
       f'- job v6 SHA：`{JOB_SHA}`',
       f'- 实际读取的 canonical v7 SHA：`{CANONICAL_SHA}`',
       f"- 新增单个图任务读取的 canonical v8 SHA：`{ADDITIONAL_BINDING['canonical_sha256']}`；仅该任务的2处字段。",
       '- 仅阅读选中任务对应记录/字段及对应原件的必要物理页，未读预测、参照或其他人工答案。',
       '- 原PDF字节、13个textSHA、30个绑定逐项核验；每个occurrence的原CTX、父关系、段落和位置在JSON中分别保留。',
       '- 未处理其余170个扫描PDF任务。', '',
       '## 实际查看清单','',
       '| PDF SHA前16位 | 指定物理页（括号为印刷页） | 额外查看 |',
       '|---|---|---|',
       '|64ac48e587537802|4(1)、10(7)、18(15)|第10页续约支路裁图|',
       '|7f5b1829d0030b34|4(3)、9(8)、10(9)、22(21)|第9页目录外成员、续约支路裁图；第10页为新增图3|',
       '|460121b411d754f9|26(24)|无|',
       '|81e4dbb0b83972d6|4(4)、12(12)|第12页RCT字样裁图|',
       '|2cfe67011c96edde|18(15)、19(16)|第17页4.1.1标题/列头裁图；第19页控制措施列裁图|','',
       '共19个PNG资产：13张页渲染、6张实际查看的裁图。物理17页的完整PNG只渲染，未全页阅读；实际查看范围是标题/列头裁图。资产字节SHA、DPI、裁图坐标和查看状态均在 source-page-assets-manifest.json。', '',
       '## 逐任务结果','']
    for r in review['reviews']:
        st=r['neutral_source_structure']; bind=r['occurrence_bindings']
        s += [f"### {r['job_id']}",'',
              f"{st.get('caption',st.get('section_heading',{}).get('text',''))}；物理页 {r['physical_pages']}、印刷页 {r['printed_pages']}；{len(bind)} 处 occurrence。",'',
              f"原PDF SHA：`{r['source_sha256']}`；当前字段 textSHA：`{r['original_current_field_text_sha256']}`。",'',
              '当前字段为源图/表的规范化表示；没有确认实质文字修复。'+('其中条件间“或”的具体逻辑需要同版确指材料，本图只验证成员关系。' if r['job_id']==JOBS[12]['job_id'] else ''),'']
        s += ['- '+n for n in r['review_notes']] + ['']
        if st.get('unverified_external_targets'):
            s += ['仅核实原图上的确指名称，未查援引目标全文：'+ '、'.join(st['unverified_external_targets'])+'。','']
        s += ['实际图证据：'+ '、'.join(f'[{Path(x).name}]({x})' for x in r['actual_evidence_assets'])+'。','',
              '完整当前字段文字（保留原SHA；下文不是重新宣称原文连续句）：','', '```text',r['original_current_field_text'],'```','',
              '节点/单元、箭头/支路、条件运算、跨页表头的完整机用表示见同名JSON的 neutral_source_structure；30处独立绑定见 occurrence_bindings。','']
    s += ['## 统合说明','',
          'neutral-patches.jsonl 每条带 base canonical SHA、expected_old_text_sha256 和精确 occurrence 目标，仅请求追加中性结构/定位，不改 body 或 context text。主源 owner 统合后应向规则方法、LLM 与未来真人编码提供同版公共输入。', '',
          '现存标点、行间空白、月份连字符与图题冒号规范化并非逐字节原文身份；对原图书名号叠写、罗马数字码点等未作外部校改。图中未印的阈值相等情况、每条线的箭头头部、数值时长或外部规则不得由本次核验补猜。','']
    return '\n'.join(s)

if __name__ == '__main__':
    if (OUT/'SEALED.json').exists():
        raise SystemExit('Delivery sealed; do not overwrite. New work requires a separate version/round.')
    # Guard fixed source-manifest bytes without parsing other jobs/canonical bodies.
    assert sha_bytes(JOB_PATH.read_bytes()) == JOB_SHA
    assert sha_bytes(CANONICAL_PATH.read_bytes()) == CANONICAL_SHA
    assert sha_bytes(Path(ADDITIONAL_BINDING['canonical_path']).read_bytes()) == ADDITIONAL_BINDING['canonical_sha256']
    review,patches=make_review()
    dump(OUT/'source-page-assets-manifest.json',asset_manifest())
    dump(OUT/'source-graph-table-review.json',review)
    (OUT/'source-graph-table-review.md').write_text(markdown(review)+'\n')
    (OUT/'neutral-patches.jsonl').write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in patches))
    print(json.dumps({'status':'built','jobs':len(patches),'occurrences':30,'assets':19},ensure_ascii=False))
