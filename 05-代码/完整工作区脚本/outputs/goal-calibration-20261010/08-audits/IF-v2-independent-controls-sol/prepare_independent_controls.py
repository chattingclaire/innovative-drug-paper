"""Fix independent synthetic expectations from manual and preserved originals."""
from pathlib import Path
import copy
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
V2 = ROOT / '06-coding/rule-v20-semantic-audit-repair-sol/versions/v2'
MANUAL = ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def bind(path):
    data = path.read_bytes()
    return {'path':str(path),'sha256':sha(data),'bytes':len(data)}


def write_new(name, data):
    with (HERE/name).open('x', encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2,allow_nan=False);f.write('\n')


def ctx(cid, kind, text, ref, structure=None):
    return {'context_id':cid,'kind':kind,'text':text,'source_ref':copy.deepcopy(ref),'structure':structure or {}}


def unit(text, *, raw=None, extra=None):
    raw = text if raw is None else raw
    source_sha = sha(raw.encode())
    ref = {'sha256':source_sha,'source_resource_id':'SOURCE-SYN-'+source_sha,'locator':{}}
    contexts = [ctx('CTX-SYN-CURRENT','paragraph',text,ref)]
    if raw != text:
        leafref = copy.deepcopy(ref)
        leafref['locator']={'unicode_code_point_interval_half_open':[0,len(raw)],
                            'utf8_byte_interval_half_open':[0,len(raw.encode())]}
        contexts.append(ctx('CTX-SYN-FULL','source_textleaf',raw,leafref))
    contexts.extend(extra(ref) if extra else [])
    return {'text':text,'source_ref':ref,'contexts':contexts,
            'source_bundle':{'source_record':{'text':text,'contexts':copy.deepcopy(contexts)},
                             'source_documents':[],'explicit_or_primary_source_resources':[],
                             'source_full_text_resources':[],
                             'preserved_historical_neutral_source_supplements':[],
                             'source_reference_index':[]},'derived_context_origins':{}}


def main():
    authority = []
    specifications = [
        ('NMPA-breakthrough-scope', '980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt',4,17),
        ('NMPA-postadmission-services', '980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt',25,29),
        ('NMPA-withdrawal', '980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt',30,39),
        ('NMPA-need-branches', '980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt',155,175),
        ('NMPA-review-services', '980acf76a2fb9b95-NMPA-突破性治疗等三程序-2020-附件正文.txt',177,189),
        ('NMPA-continuous-59-62', 'd959108cdaaa3b46-NMPA-药品注册管理办法-2020-正文.txt',197,207),
        ('NMPA-next-programme', 'd959108cdaaa3b46-NMPA-药品注册管理办法-2020-正文.txt',208,225),
        ('NMPA-pilot-resources', 'ab19a319be3fae7b-NMPA-优化创新药临床试验审评审批试点-2024.txt',6,17),
        ('NMPA-pilot-action-vs-organization', 'ab19a319be3fae7b-NMPA-优化创新药临床试验审评审批试点-2024.txt',35,46),
    ]
    for key, filename, first, last in specifications:
        path = ROOT/'00-baseline/source-files'/filename
        text=path.read_text();lines=text.splitlines(keepends=True)
        quote=''.join(lines[first-1:last]);start=sum(map(len,lines[:first-1]));end=start+len(quote)
        authority.append({'basis_id':key,'source':bind(path),'line_interval_inclusive':[first,last],
                          'unicode_code_point_interval_half_open':[start,end],
                          'utf8_byte_interval_half_open':[len(text[:start].encode()),len(text[:end].encode())],
                          'current_continuous_quote':quote,'quote_exact_match':quote==text[start:end],
                          'fixture_is_not_this_real_original':True})
    manual_text=MANUAL.read_text()
    manual_rules=[
        '创新/改良研发须是该安排的对象选择条件、支持目标或实际适用依据；须保存对象、当前支持安排及二者关系。',
        '公共指南对申请人普遍提出设计、风险管理或证据形成规范，只有规范内容本身符合I1/I2/I4时才有I；不得把指南的普遍指导作用转称I3。',
        '仅记载身份或历史状态，不能展开全部待遇。',
        '当前记录明确陈述在某时期设立或实施同一具名安排，并直接连接支持对象或内容，可补该时期同版本的必要定义和直接机制',
        '当前说明疾病严重程度，不因它属于创新药程序条件而自动获得I。',
        '境内无获批对应治疗选项或现实供应不足，并与针对性申请机会或资源安排直接相连',
        '三者不互相推定。',
        '备注中的确切援引不能删除本行另一列的基础安排。',
        '纯手续分支不继承另一分支的评价内容。',
        '所需片段缺失登记补材，不记0。',
        '一般管理创新',
    ]
    manual_quotes=[]
    for q in manual_rules:
        at=manual_text.index(q)
        manual_quotes.append({'quote':q,'line':manual_text[:at].count('\n')+1,'start':at,'end':at+len(q),'exact_match':True})
    write_new('authority-and-manual-basis.json',{'manual':bind(MANUAL),'manual_quotes':manual_quotes,
              'authority_quotes':authority,'not_legal_advice_or_new_standard':True,
              'raw_originals_read_scope':'specified continuous ranges only; full file bytes read for SHA, not semantic reading of all lines'})

    cases=[]
    def add(name,text,expect,reason,*,raw=None,extra=None,basis=None):
        cases.append({'name':name,'synthetic_only':True,'synthetic_input':unit(text,raw=raw,extra=extra),
                      'expected':{'I':expect[0],'F':expect[1]},'manual_reason':reason,
                      'authority_basis_ids':basis or [],'is_human_reference':False})
    add('direct_innovation_feedback',
        '对正在研发新靶点创新药的申请人，专门技术团队可以提供下一步研究方案反馈，无需先取得上市许可。',
        (1,0),'明确创新研发对象与可用研究方案反馈服务直接相连；未表达公平缺口。',basis=['NMPA-postadmission-services'])
    add('communication_forms_only',
        '创新药项目的沟通形式可以为电话、视频或书面，文件名须使用统一申报编号。',
        (0,0),'当前仅列沟通载体和文件命名，不设服务/反馈内容或可用支持机会。',basis=['NMPA-postadmission-services'])
    add('general_safety_obligation',
        '创新药申请人应收集严重不良反应资料并更新风险管理计划。',
        (0,0),'一般安全义务不由创新身份或政策指导转为I3。',basis=['NMPA-pilot-resources'])
    service='对纳入探索创新研发程序的项目，药审中心在临床试验关键阶段优先安排技术沟通，并反馈下一步研究方案。'
    programme=('探索创新研发程序\n一、适用范围\n'
               '本程序适用创新药和改良型新药研发项目；用于尚无有效治疗手段疾病的项目可申请本程序的优先技术服务。\n'
               '二、工作程序\n'+service+'\n三、工作要求\n项目负责人应保留反馈记录。\n')
    add('named_postadmission_priority_service',service,(1,1),
        '同版同一具名安排的创新研发对象、所需治疗缺口与当前优先技术服务直接相连，混合对象不扩散。',
        raw=programme,basis=['NMPA-breakthrough-scope','NMPA-postadmission-services'])
    history='该药物于2021年已纳入探索创新研发程序，现仅更新名单中的项目编号。'
    add('historical_identity_not_current_support',history,(0,0),
        '仅历史纳入身份及名单编号更新，当前没有设立、实施或限制支持的行动。',
        raw=programme+history+'\n',basis=['NMPA-withdrawal'])
    add('withdrawal_missing_same_edition_scope',
        '该药物临床试验不能满足探索创新审评程序条件，药审中心应终止其优先研究方案反馈服务。',
        (None,None),'当前实际资格—支持撤回确指同版标准，关键对象/条件原文未交付，不能据名称硬判0或1。',
        basis=['NMPA-withdrawal'])
    add('negative_support_action_direct',
        '对尚无有效治疗手段疾病的创新药研发项目，药审中心不再提供优先研究方案反馈机会。',
        (1,1),'撤回明确创新研发资源及缺口连接的优先机会仍表达I/F议题，不推定撤回所有治疗。',basis=['NMPA-withdrawal'])
    add('work_organization_innovation',
        '药品审评办公室创新排班组织方式，采用新颖的会议值班流程。',
        (0,0),'新颖对象是办公室排班与组织方式，不是药物技术或实际创新研发支持。',basis=['NMPA-pilot-action-vs-organization'])
    add('negative_drug_novelty_evidence',
        '尚无证据证明该创新药具有新的作用机制，应与已上市同类药比较其机制新颖性。',
        (1,0),'否定证据充分性仍是药物技术新颖性评价；无公平措施或障碍。')
    parent='符合下列条件的药品，可以申请临床试验支持：'
    def parent_extra(member_other=None):
        def build(ref):
            result=[ctx('CTX-SYN-PARENT','preceding_paragraph',parent,ref)]
            if member_other:result.append(ctx('CTX-SYN-SIBLING','following_paragraph',member_other,ref))
            return result
        return build
    add('first_disease_condition_no_inheritance','（一）用于防治严重危及生命的疾病。',(0,0),
        '直接父句仅补申请谓词；当前疾病严重程度不继承兄弟创新属性或治疗缺口。',
        extra=parent_extra('（二）具有新作用机制的创新药，且尚无有效治疗选项。'),basis=['NMPA-breakthrough-scope'])
    add('first_innovation_qualification','（一）具有新作用机制的创新药。',(1,0),
        '当前明确创新属性与直接完整父句的支持申请后果组合；兄弟缺口不继承。',
        extra=parent_extra('（二）患者无其他有效治疗选项。'),basis=['NMPA-breakthrough-scope'])
    gap_parent='符合下列条件的药品，可以申请优先审评支持：'
    add('first_no_approved_option_opportunity','（一）境内尚无药物获批用于该疾病。',(0,1),
        '已表达无获批对应治疗选项，直接父句赋优先申请机会；不推定创新属性。',
        extra=lambda ref:[ctx('CTX-SYN-PARENT','preceding_paragraph',gap_parent,ref)],basis=['NMPA-need-branches'])
    add('second_form_member_not_inherit_first','（二）申请人须核对材料文件的页码。',(0,0),
        '第二项纯文件核对不倒借前一成员的治疗缺口或创新条件。',
        extra=lambda ref:[ctx('CTX-SYN-PARENT','parent_paragraph',gap_parent,ref),
                          ctx('CTX-SYN-FIRST','preceding_paragraph','（一）境内尚无药物获批用于该疾病的创新药。',ref)],basis=['NMPA-need-branches'])
    add('foreign_single_unlisted_not_no_options',
        '对临床急需、境外已上市境内未上市的罕见病药品，申请人可以申请优先审评审批；境内已有其他获批治疗选项且供药充足，本条未按治疗保障缺口分配机会。',
        (0,0),'单品未上市不等于无获批对应治疗选项。当前还明确其他选项及供药存在，无公平缺口，不从罕见病身份猜I。',basis=['NMPA-need-branches','NMPA-review-services'])
    add('no_approved_options_target_priority',
        '对境内尚无药物获批用于该适应症且患者无法取得对应治疗的项目，给予优先审评申请机会。',
        (0,1),'获批治疗选项缺口与针对性优先机会直接相连，未必是创新研发对象。',basis=['NMPA-need-branches'])
    tabletext='创新药 | 6年；其中符合第七条第二款的，可延长2年'
    def table_extra(ref):
        cells=tabletext.split('|');headers=['药品对象','数据保护期'];rid='CTX-SYN-ROW'
        row=ctx(rid,'table_row',tabletext,ref,{'row_cell_column_pairs':[{'cell_index':i,'header_index':i,'column_index':i} for i in range(2)]})
        row['row_cells']=cells;row['headers']=headers
        out=[row]
        for i,c in enumerate(cells):out.append(ctx('CTX-SYN-CELL-'+str(i),'table_row_cell',c,ref,{'parent_context_id':rid,'column_index':i}))
        out.append(ctx('CTX-SYN-RIGHT-HEADER','table_header_cell',headers[1],ref,{'parent_context_id':rid,'column_index':1}))
        out.append(ctx('CTX-SYN-EXCEPTION','cited_article','第七条第二款 已完成特定儿科研究的该药品，可延长数据保护期两年。',ref,{'article':'第七条','clause':'第二款'}))
        return out
    add('protection_base_and_exception_separate',tabletext,(1,0),
        '本行创新药基础保护待遇已直接成立I4；儿科研究例外不删除基础、不借创新资格给全部例外或兄弟行。',extra=table_extra)
    add('bare_right_registration_identity',
        '该仿制药持有人确认已有数据保护登记编号，填写编号字段。',(0,0),
        '仅权利登记身份与编号字段，缺当前创新资格—待遇关系，不借其他药定义。',
        extra=lambda ref:[ctx('CTX-SYN-OTHER-RIGHT','source_paragraph','创新药符合新颖技术条件时给予数据保护期。',ref)])
    review='药审中心应核验探索创新研发程序的纳入条件，不满足的终止研究方案反馈支持。'
    standard=('探索创新研发程序\n一、适用范围和适用条件\n'
              '申请适用探索创新研发程序的药品，应当同时满足以下条件：\n'
              '1.该药物具有新作用机制，属于创新药。\n'
              '2.须证明拟开展的临床试验用于其创新研发。\n'
              '二、工作程序\n'+review+'\n本程序提供下一步研究方案意见并反馈给申请人。\n')
    def standard_extra(ref):
        return [ctx('CTX-SYN-STANDARD','source_paragraph','申请适用探索创新研发程序的药品，应当同时满足以下条件：',ref)]
    add('complete_same_edition_qualification',review,(1,0),
        '操作性核验与待遇终止可有限使用完整同版资格；本组明确药物新机制与创新研发，不含公平缺口。',
        raw=standard,extra=standard_extra,basis=['NMPA-continuous-59-62','NMPA-withdrawal'])
    add('missing_same_edition_qualification',review,(None,None),
        '同一当前核验—终止命题缺所确指资格原文，尚不知道完整组各维内容，不记已知0。',
        extra=standard_extra,basis=['NMPA-continuous-59-62'])
    next_duty='对纳入附条件批准程序的药品，申请人应当在上市后提交常规安全性研究资料。'
    two_programmes=(programme+'第二节 附条 件批准程序\n一、适用范围\n本程序适用有条件上市的药品。\n二、工作要求\n'+next_duty+'\n')
    add('next_programme_not_inherit_prior_support',next_duty,(0,0),
        '后一个实际含内部空格的程序边界结束前一创新支持范围；上市后常规资料义务不借兄弟程序I/F。',
        raw=two_programmes,basis=['NMPA-next-programme'])
    if len(cases)!=20:raise ValueError('exactly twenty controls required')
    controls={'status':'synthetic_expected_fixed_before_execution','case_N':20,'formal_records_used':0,
              'is_human_reference':False,'all_current_and_contexts_synthetic':True,
              'actual_source_texts_used_only_as_prejudgment_basis_not_formal_inputs':True,
              'manual':bind(MANUAL),'cases':cases}
    write_new('controls-fixed-before-execution.json',controls)
    alg=V2/'algorithm-bindings.json'
    expected=json.loads(alg.read_text())
    verified=[]
    for m in expected['modules']+[expected['manual_binding']]:
        a=bind(Path(m['path']))
        if a['sha256']!=m['sha256'] or a['bytes']!=m['bytes']:raise ValueError('sealed input changed '+m['path'])
        verified.append(a)
    write_new('pre-execution-seal.json',{'controls':bind(HERE/'controls-fixed-before-execution.json'),
              'authority_and_manual_basis':bind(HERE/'authority-and-manual-basis.json'),
              'algorithm_bindings':bind(alg),'verified_modules_and_manual':verified,'case_N':20,
              'synthetic_only':True,'expected_may_not_be_changed_after_results':True,
              'v2_full77_or800_called':False,'neutral_projection_called':False})
    print(json.dumps({'case_N':20,'controls':bind(HERE/'controls-fixed-before-execution.json'),
                      'preseal':bind(HERE/'pre-execution-seal.json')},ensure_ascii=False))


if __name__=='__main__':main()
