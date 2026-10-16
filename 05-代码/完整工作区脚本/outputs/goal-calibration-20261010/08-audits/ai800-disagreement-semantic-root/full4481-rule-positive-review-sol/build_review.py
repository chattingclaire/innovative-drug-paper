"""Non-human semantic audit; reads frozen inputs, writes only this new audit directory.
Judgments below were entered after actual source reading, not inferred from scores.
"""
import json, hashlib
from pathlib import Path
from collections import Counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = ROOT / 'outputs/goal-calibration-20261010'
SCOPE = json.loads((HERE / 'scope.json').read_text())
MANUAL = BASE / '03-manual/full4481-common-release-20261010-root/manual.txt'
RULEDIR = BASE / '06-coding/rule-full4481-v2-root/run4481-first'
CODEDIR = BASE / '06-coding/full4481-rule-production-adapter-sol'
META = BASE / '07-statistics/annual-year-input-binding-sol/full4481-year-map.jsonl'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def jwrite(name, obj): (HERE/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
assert sha(MANUAL) == '5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b'
metadata = {x['unit_id']:x for x in map(json.loads,META.open())}
pred = {x['id']:x for x in map(json.loads,(RULEDIR/'predictions.jsonl').open())}
manual_lines = MANUAL.read_text().splitlines()
CASES = {}
def case(ids, dimension, value, path, reason, contexts=(), human=False, question=None):
    for num in ids.split():
        key=('RECODE25-'+num,dimension)
        assert key not in CASES,key
        CASES[key]=dict(review_value=value,semantic_path=path,reason=reason,
                        contexts=list(contexts),needs_human_review=human,
                        human_review_question=question)

# Current operative scope and direct eligibility predicates; OR branches stay separate.
case('00005','I',1,'I1/I4','当前直接以创新药/改良型新药及无有效手段或明确临床优势为适用对象和比较资格，并开放突破性治疗申请；这是资格—申请机会关系，不是由程序名称继承。')
case('00005','F',1,'F按需机会','当前明示“尚无有效防治手段”分支并据此开放突破性治疗申请，构成治疗选项缺口—按需申请机会；另一临床优势分支不自动具有缺口含义。')
case('00006','I',1,'I1/I4','当前实质要求满足完整条件以申请突破性治疗程序；完整成员含相对现有治疗的临床优势，且同版范围明确创新/改良对象。非纯结构引导，也不把每个疾病解释成员都视作创新。',tuple(range(6,15)))
case('00006','F',1,'F按需机会','当前规定适用程序必须满足完整条件；完整成员之一明确无有效防治手段并要求提供有效防治手段，直接联系申请机会。比较优势的其他分支不随之获得公平含义。',tuple(range(6,15)))
case('00009','F',1,'F按需机会','当前自身的无有效防治手段分支，与直接父句的突破性治疗程序适用条件结合，表达按所需治疗缺口配置申请机会；不是因为临床显著改善自动记F。',(3,))
case('00010','F',1,'F按需机会','当前在无有效治疗分支规定提供重要结局上有临床意义的有效选项；直接父句将其设为突破性治疗申请的实质条件，故为缺口—机会关系，并非推定安慰剂试验不公平。',(3,4))
case('00036 00038','I',1,'I3/I4','当前规定发现/论证不符合纳入条件时终止同一突破性治疗程序。有限补全同版创新/改良对象、完整纳入比较条件和优先研发沟通的撤回关系；00038的未交书面说明分支不单独继承创新内容，记录因资格失败分支成立。',(0,3))
case('00036 00038','F',1,'F按需机会限制','当前实际终止同一按需支持机会；同版范围及完整标准含“无有效防治手段”分支，终止后优先沟通撤回。只表达该分支的机会限制，不认定所有退出品种均因缺口条件失败。00038事务时限分支不单独成为F。',(0,3))
case('00045','I',1,'I3','当前在研发沟通及阶段性资料审核中实质审核并终止同一突破性治疗资格；同版原文明确创新/改良研发对象、优先配置研发指导资源及终止后撤回优先沟通，满足对象—可用支持—直接限制联系。',(3,))
case('00045','F',1,'F按需机会限制','当前审核并终止具名程序，有限补全同版无有效治疗分支及优先研发资源撤回桥梁，表达按需机会的限制。不是将新的临床优势不足或安全终止理由统称为缺药。',(3,))
case('00047','I',1,'I3','当前向已纳入突破性治疗的创新/改良研发品种开放附条件批准和优先申请机会，同版对象范围与当前申请直接相连。规则主路径I1过于概括，本审核依据当前真实支持机会成立，不宣称全部相关条件等同创新条件。',(3,))
case('00047','F',1,'F按需机会','当前实际对纳入突破性治疗的品种开放附条件批准/优先申请机会，同版突破性对象范围包含无有效防治手段分支。只保留该缺口对象分支与当前新增申请机会的联系，不把全部突破性品种或泛称“相关条件”改写成短缺，也不把另行指南未提供的条件补成现有原文。',(3,))
case('00087 00088','F',1,'F按需机会','当前总领或其直接成员把临床急需短缺药品列为可以申请优先审评的对象，保障缺口与针对性申请机会直接连接；创新、重大传染病和罕见病其他分支不因此全具有公平关系。',(2,))
case('00097 00098','F',1,'F按需机会条件','当前识别临床急需短缺对象，或规定其须列入国家短缺清单并经组织确定；完整同段及直接父谓词把这些实质缺口确认条件用于优先申请资格，非孤立名单身份或纯收件。',(0,3,4))
case('00110 00118','F','未定','F缺口边界','当前确有临床急需境外新药名单对象及优先申请/直接纳入安排，但“该品种境内未上市”不等于“境内无获批对应治疗选项”。已读同版优先程序完整范围，未找到对这个特定名单分支的治疗选项/供药保障缺口定义，不能从罕见病、急需、未上市或名单标题补出。规则将其归入no_domestic_approved_option存在扩大含义；需统一名单资格与现手册缺口门槛，暂不把完整但未明的关系当0或1。',(0,2),True,'同版临床急需境外新药名单资格能否用确指原文建立本分支实际所需治疗保障缺口？仅品种境内未上市能否纳入，须依现手册统一。')
case('00138','I',1,'I3','当前实质对已纳入优先程序的品种实施研发技术沟通，同版完整范围含实际创新/改良适用分支，纳入后技术审评优先沟通及补充技术资料咨询机会直接对应当前服务。不能用申报前机制替代，也不声称全部纳入对象都是创新。')
case('00138','F',1,'F按需优先技术服务','当前实施纳入后的技术沟通，同版范围包含临床急需短缺、无有效儿童治疗选项等缺口分支，同阶段审评沟通明确可优先安排。该链支撑具体F；普通沟通、罕见病或创新身份本身不充分。')
case('00186','I',0,'I3不成立','当前仅说改良型新药研发可参考另一公共技术指南，未设置项目可使用的资源、专门服务、反馈、便利或申请机会，也未自足表达技术新颖/实质改良资格。不得把普遍指南引用转称实际研发支持。',(0,),True,'是否同意将一般可参考公共指南与I3实际服务/支持机会分开？现手册明确排除前者。')
case('00344','I',1,'概括创新评价','当前明确将创新性等药品价值维度用于临床综合评价，药品对象及评价动作齐备；按概括评价路径纳入，不补写已实现技术创新。',(0,))
case('00349','I',0,'一般管理创新排除','“创新性、系统性”修饰药品使用监测和临床综合评价这项工作，未评价药品技术新颖性/创新价值，也未设置创新研发支持。药品一词与创新性词同句不能替代语义对象核实。',(0,),True,'确认创新性修饰工作组织而非药品属性；规则的药品对象匹配未消除修饰对象错误。')
case('00650 00693 00791 01149 01150 01258 01309 02777 02922 03710 03767 04248','I',1,'概括创新评价/信息','当前以申报药品/药品价值为对象，直接规定创新价值评价、比较或创新性信息内容。按概括评价/信息路径成立，不需要补造具体技术优势；申报内容或公示内容明确包括该维实质信息，区别于仅栏目名、字段非空和无内容的材料流转。',(0,))
case('00650 00693 00791 01258 01309 02777 02922 03710 03767 04248','F',1,'概括公平评价/信息','当前明确以药品价值或申报药品为对象，要求公平性评价/比较或提供相应信息内容，按第一类概括公平路径成立。原文未说明具体公平机制，不能据此补写收入差异、短缺、地域障碍或已经改善公平。',(0,))
case('00652 00887 00902 00908 01602 01620 01629 01694 01712 01721 03358 03393 03402 03712','I',1,'I4分类到实质待遇','当前把依法批准的1类化学药、1类治疗用生物制品、1类中药设为重新谈判申请或续约降价比例待遇条件。按手册§九对应药类和时期，1类创新分类与实质权利直接相连，属于I4制度使用；含中药3类的混合记录仅1类分支支撑，3类经典名方不等同技术创新，也不改称研发支持。',(0,3))
case('00900 01618 01710 03391','I',1,'I4分类到实质待遇','当前实质规定满足完整条件之一可纳入重新谈判范围；读完整两成员后，第二分支以依法批准1类化学药、生物制品和中药的创新资格决定可主动谈判支付标准。第一普通分支不继承创新，中药3类混合分支不冒称创新。',(8,9))
case('00739 03846','I',1,'I1创新价值否定关系','当前实质区分空白对照与申报药品创新价值/创新分级，明确前者不代表后者很高。否定判断仍表达创新价值议题；不将目录空白推成治疗空白或创新程度高。',(0,2))
case('01154','F',1,'F可负担性评价','当前规定可及性评价涉及药品可负担性，完整同段以治疗费用占居民可支配收入体现该指标，直接讨论患者能否负担药品，不因价格或一般可及性词自动判F。',(0,))
case('01157','F',1,'F可负担性证据','当前明确以人均年用药治疗费用占城乡居民家庭可支配收入比例体现可负担性，费用—支付能力关系自足成立；不补造具体收入群体或已改善结果。')
case('01423 01433','I',1,'I4确指改良数据保护','完整表格当前备注把符合第七条第二款者的保护期设为4年；同版第七条第二款直接按第六条执行，第六条完整保护范围限定为证明较已知药品有明显临床优势的新临床试验数据并排除BA/BE/疫苗免疫原性。只有这一确指改良保护分支支撑I，基础境外上市/原研身份或6年待遇本身不作创新证据。',(13,14,18,19,20,21))
case('01459','I',1,'I1/I4创新申请资格','当前本身规定申请关爱计划需同时满足实质条件，完整成员要求较强创新性，包括新作用机制/新靶点或创新联系下的明显临床优势，决定支持申请资格。不是由罕见病名称或笼统研发目的继承。',tuple(range(6,12)))
case('01459','F',1,'F对应适应症选项缺口—机会','当前实质设定支持申请资格，完整成员之一明确境内尚无药物获批拟开发的罕见疾病适应症，直接联系试点申请机会。这是对应治疗适应症的获批选项缺口，区别于仅单一品种未上市；F不扩展至已有治疗优势的其他OR分支。',tuple(range(6,12)))
case('01729','I',1,'I3明确设立同版支持安排','当前“决定开展”具名改革试点并直接连接支持创新药研发，包内同版方案明确1类创新药对象、30个工作日审评及技术服务。复核手册第46行后，目的/背景位置不能单独排除；当前有独立设立行动，可按第44/46行有限补全同版对象和直接可用机制，满足I3。未复制方案全部安全义务或后续新版条件。')
case('01730','I',1,'I3实际研发办理便利','当前明确对创新药临床试验实现30工作日内完成审评审批并缩短启动用时，创新研发对象—具体加快办理便利—直接关系自足成立，不因工作目标文体位置排除。')
case('02233','I',1,'I3明确陈述同版历史实施','当前明确陈述2024年组织开展具名试点并直接联系支持创新药研发；包内2024同版方案有1类创新对象及30日实际通道。复核手册第46行后，过去/完成时态及背景位置不能单独排除，当前已有实施行动及对象，可补该时期定义与直接机制。仅计曾实施的支持议题，不证明今天仍能申请，不倒灌2025新条件。',(0,))
case('02269','I',1,'I3明确授权实施支持安排','当前经审核同意在北京上海开展具名试点并要求依同版方案实施，明确授权行动不是名单状态或未承接历史。包内显式原文限定1类创新药临床试验对象，设30工作日审评、申报前沟通和培训等可用便利，实施与支持直接相连。')
case('02504','I',1,'I3研发数据服务','当前提出探索为创新药研发提供必要医保数据服务，同段进一步明示适配研发数据产品及合理确定研发方向/管线；这是可使用服务安排，探索性不等于仅宗旨，也未证明效果已经产生。',(0,))
case('03474','I',1,'I2操作障碍—具体设计改良','完整同段明确老年患者剂量调整、手指灵活性影响掰断操作的使用局限；当前通过掰断便利性数据改善片剂易碎性或开发适宜规格/剂型，具体改变与缓解操作障碍直接连接。按冻结I2操作化纳入，不因指南面向创新药记I3，也不宣称已证优效。',(0,2))
case('03782','I',1,'I1创新程度/价值条件','当前商保目录明确聚焦创新程度高且具临床价值的创新药品，并将该创新属性与推荐多层保障目录对象选择联系起来。属于创新价值/程度实质关注，不只凭目录名称，也不把价格高当创新。',(0,))
case('04157','I',1,'I3提前开放研发机会','当前允许拟附条件批准创新药在探索性试验完成前适用具名工作规范，实质提前开放研发支持机会；同版范围和规范时限/单独序列、早期沟通机制补足对象与可用支持。不从“创新药”身份单独推出。',(2,5,6,7,8,9,10,12,13))
case('04162','I',1,'I3专门稳定审评服务','当前组建团队，完整同段明示其负责申报前沟通至受理后技术审评全过程并尽量稳定；同版范围把儿童/罕见病/突破性创新研发明确纳入，专门服务对象与团队职责相连。不是只看到“团队”或监管机构主语。',(0,5,6,7,8,9,10))
case('04413','I',1,'I1创新程度用于分类','当前以药品产品创新程度组织制定细化注册分类及相应资料要求，明确药物创新程度是制度分类依据，属于创新分类/价值关注；不将单纯公布动作当创新，也不宣称每类都是创新。',(2,))
case('04586','I',1,'I1/I4资格—机会','当前法律条款直接将创新/改良对象及无有效手段或创新联系下明显临床优势设为突破性程序申请条件，实质创新/改良资格—机会关系成立。')
case('04586','F',1,'F无有效选项—机会','当前“尚无有效防治手段”分支与可申请突破性程序直接连接，构成明确治疗选项缺口—按需机会。另一比较临床优势分支不自动记F。')
case('04604','F',1,'F短缺—优先申请','当前实质开放优先申请，完整范围含临床急需短缺药品，缺口与申请机会直接相连。其他创新/罕见病/疫苗分支不因并列自动具有F。',(5,6,7,8,9,10))
case('04605','F',1,'F短缺—优先申请','当前成员自身明示临床急需短缺药品，与直接父句可申请优先程序组合，缺口与申请机会直接相连。其他创新/罕见病分支不因并列自动具有F，不借兄弟项获得标签。',(2,))
case('04613','F',1,'F同版短缺分支—政策支持','当前实质向已纳入优先程序的品种给予完整政策支持；同包冻结原件第68条明确临床急需短缺对象，当前第70条优先安排核查检验等支持与同一程序直接对应。该真实短缺分支支撑F；第70条罕见病境外药未上市分支不自行推定境内无治疗选项。所用第68条定义取自同包原件，当前JSON只列第70条成员，消费差异另记。',(5,6,7,8))
case('04915','F',1,'F原文明定现实供药缺口纠正','当前改善偏远配送及用药衔接；包内同政策官方解释明确偏远地区配送积极性低、药品供应不稳定时常断供，且直接说明措施针对该问题。现实所需药品保障缺口—配送纠正关系成立，非由偏远/基层身份或效率词猜测公平。',(0,))

def at(obj,pointer):
    for part in pointer.strip('/').split('/'):
        if part: obj=obj[int(part)] if isinstance(obj,list) else obj[part]
    return obj
def evidence(item,bundle,pointer,quote=None,usage='必要同版语境'):
    obj=at(bundle,pointer)
    full=obj if isinstance(obj,str) else obj['text']
    text=full if quote is None else quote
    assert text in full,(item['source_id'],pointer,text)
    a=full.index(text)
    return dict(file=item['packet_file'],json_pointer='/source_bundle'+pointer,
                text=text,local_unicode_span_half_open=[a,a+len(text)],
                resource_id=obj.get('context_id',obj.get('source_resource_id')) if isinstance(obj,dict) else None,
                locator=obj.get('source_ref',{}).get('locator',obj.get('locator',obj.get('structure'))) if isinstance(obj,dict) else None,
                usage=usage)
def extra(item,bundle,ptr,quote,usage='具名安排同版定义/实际机制'):
    return evidence(item,bundle,ptr,quote,usage)
def select(item,bundle,c):
    out=[];seen=set();current=bundle['source_record']['text']
    for i in c['contexts']:
        ctx=bundle['source_record']['contexts']
        if i<len(ctx) and ctx[i].get('text') and ctx[i]['text'] not in seen and ctx[i]['text']!=current:
            out.append(evidence(item,bundle,f'/source_record/contexts/{i}'));seen.add(ctx[i]['text'])
    return out

rows=[]
for index,item in enumerate(SCOPE['items'],1):
    sid,dim=item['source_id'],item['dimension'];b=json.loads(Path(item['packet_file']).read_text())['source_bundle']
    assert sha(item['packet_file'])==item['packet_sha256']
    curr=b['source_record']['text'];pr=item['prior_review']
    base=dict(audit_index_1based=index,source_id=sid,dimension=dim,rule=1,
        reviewer='AI-Codex semantic audit (non-human)',is_true_human_review=False,
        review_not_blind_to_rule_judgment=True,not_an_accuracy_gold_standard=True,
        packet_file=item['packet_file'],packet_sha256=item['packet_sha256'],
        source_bundle_sha256=item['source_bundle_sha256'],current_text_sha256=item['current_text_sha256'],
        current_text=curr,current_quote=curr,
        current_location=dict(file=item['packet_file'],json_pointer='/source_bundle/source_record/text',source_ref=b['source_record']['source_ref']),
        department=metadata[sid]['department'],policy_year=metadata[sid]['policy_year'],
        metadata_only_not_label_evidence=True,manual_file=str(MANUAL),manual_sha256=sha(MANUAL),
        rule_basis_path=pred[sid]['decisions'][dim]['basis_path'],
        original_rule_evidence=dict(current_anchor=pred[sid]['decisions'][dim]['current_anchor'],context_evidence=pred[sid]['decisions'][dim]['context_evidence']))
    if pr:
        old=pr['row'];assert old.get('current_text',old.get('current_original'))==curr,(sid,'old current')
        base.update(review_value=old['review_value'],assessment='规则阳性有据' if old['review_value']==1 else old['assessment'],
            reason=old.get('reason',old.get('explanation')),needs_human_review=old.get('needs_human_review',False),
            review_mode='引用此前非真人实际核源审查；本轮未冒称重新逐条阅读',
            prior_review=dict(file=pr['review_file'],row_0based=pr['review_row_0based'],sha256=sha(pr['review_file']),
                prior_material_file=item['prior_source_material_file'],prior_material_sha256=item['prior_source_material_sha256'],
                full_canonical_source_bundle_exact_equal=True,original_review=old),
            used_context_quotes=old.get('actual_context_evidence',[]),
            prior_context_trace_status='旧I审查列实际引用；旧F审查只有available_contexts_for_trace_not_all_used，保留原记录，不将全部可见语境冒充实际使用',
            manual_clauses=old.get('manual_clauses',old.get('manual_basis')),
            human_review_question=None)
        if sid in ['RECODE25-00126','RECODE25-04615'] and dim=='F':
            base['newly_identified_boundary_question']='本轮发现同类边界：仅品种境内未上市与境内无获批对应治疗选项需分开；旧审查值与出处原样保留，没有覆盖。请真人与00110/00118一并核定。'
            base['needs_human_review']=True
        rows.append(base);continue
    c=CASES[(sid,dim)];base.update({k:v for k,v in c.items() if k!='contexts'})
    value=c['review_value'];base['assessment']='规则阳性有据' if value==1 else '规则过度纳入' if value==0 else '手册边界待核'
    base['review_mode']='本轮实际阅读完整当前命题及下列必要语境，独立语义判断'
    used=select(item,b,c)
    n=sid[-5:]
    if n=='00006': used.append(extra(item,b,'/source_full_text_resources/0','药物临床试验期间，用于防治严重危及生命或者严重影响生存质量的疾病且尚无有效防治手段或者与现有治疗手段相比有足够证据表明具有明显临床优势的创新药或者改良型新药等，申请人可以在Ⅰ、Ⅱ期临床试验阶段,通常不晚于Ⅲ期临床试验开展前申请适用突破性治疗药物程序。'))
    if n in ['00036','00038','00045','00047']:
        used.append(extra(item,b,'/source_full_text_resources/0',b['source_full_text_resources'][0]['text'][b['source_full_text_resources'][0]['text'].index('一、适用范围和适用条件'):b['source_full_text_resources'][0]['text'].index('二、工作程序')],'完整同版对象及纳入标准，OR逐支保留'))
        used.append(extra(item,b,'/source_full_text_resources/0','（四）临床试验研制指导。药审中心对纳入突破性治疗药物程序的药物优先配置资源进行沟通交流，加强指导并促进药物研发。申请人做好准备工作后提出与药审中心进行沟通交流的申请。'))
        used.append(extra(item,b,'/source_full_text_resources/1','（三）对于已终止突破性治疗药物程序的品种，自终止之日起，药审中心不再优先安排相关沟通交流，沟通交流时限按照《药物研发与技术审评沟通交流管理办法》及《药品注册审评一般性技术问题咨询管理规范》相关要求执行。'))
    if n=='00047':
        text=b['source_full_text_resources'][2]['text'];start=text.index('一、适用条件');end=text.index('二、工作程序',start)
        used.append(extra(item,b,'/source_full_text_resources/2',text[start:end],'当前另行开放附条件申请所对应的同版完整范围'))
    if n in ['00087','04604']:
        for i,x in enumerate(b['source_record']['contexts']):
            if x.get('kind')=='ordered_members' and x.get('text') and x['text']!=curr and x['text'] not in {e['text'] for e in used}:used.append(evidence(item,b,f'/source_record/contexts/{i}'))
    if n=='00138':
        text=b['source_full_text_resources'][2]['text'];start=text.index('一、适用范围');used.append(extra(item,b,'/source_full_text_resources/2',text[start:],'同一优先程序完整混合对象范围'))
        text=b['source_full_text_resources'][3]['text'];end=text.index('三、工作程序');used.append(extra(item,b,'/source_full_text_resources/3',text[:end],'同版完整适用条件；不将所有分支统称缺口'))
        text=b['source_full_text_resources'][4]['text'];start=text.index('四、工作要求');end=text.index('本工作程序所规定的期限',start)
        used.append(extra(item,b,'/source_full_text_resources/4',text[start:end],'纳入后同阶段技术沟通及优先安排，不借申报前机制'))
        used.append(extra(item,b,'/source_full_text_resources/4','药审中心在审评中发现需要与申请人进行沟通交流的，可根据具体情况优先安排。','当前纳入后技术审评沟通的明确优先机会'))
        start=text.index('（八）经沟通交流确认，补充提交技术资料。');end=text.index('（九）综合审评。',start)
        used.append(extra(item,b,'/source_full_text_resources/4',text[start:end],'纳入后可申请补充技术资料咨询机会'))
    if n in ['01729','02233','02269']:
        ptr='/explicit_or_primary_source_resources/0/source_texts/0';text=at(b,ptr)['text']
        for quote in ['试点项目范围为1类创新药（细胞和基因治疗产品、疫苗产品等除外）临床试验申请。','经确认的试点项目，药审中心在受理临床试验申请后30个工作日内完成审评审批，并通过药审中心网站通知申请人审批结果。']:
            used.append(extra(item,b,ptr,quote))
        base['same_version_binding']=dict(document_date=b['explicit_or_primary_source_resources'][0].get('document_date'),snapshot_sha256=b['explicit_or_primary_source_resources'][0].get('snapshot_sha256'),scope='2024试点；未倒灌2025新条件')
        if n in ['01729','02233']:
            base['independent_review_discussion']=dict(initial_review_value='未定',initial_question='目的/背景或历史实施表述是否可有限展开具名研发支持？',initial_needs_human_review=True,
                root_independent_reading='ROOT指出当前冻结手册第46行明确规定时态和背景不能单独决定标签；其独立核源认为这两句有明确设立/实施行动与创新研发对象。',
                reviewer_followup='本审核实际再读同SHA手册第38—47行，确认第46行明确允许此时期同版机制补全；因此本轮审核值1，保留初始疑问及讨论记录，不改手册、原规则或原表。',
                decisive_manual_line=dict(line_1based=46,text=manual_lines[45]),final_review_value=1,
                temporal_claim_limit='仅表示该时期设立/曾实施的支持议题，不证明当下仍可申请。')
    if n=='04613':
        doc=b['source_documents'][0];f=Path(doc['snapshot']);raw=f.read_text();a=raw.index('第六十八条');z=raw.index('第六十九条',a);q=raw[a:z];assert sha(f)==doc['source_sha256']
        used.append(dict(file=str(f),json_pointer=None,text=q,local_unicode_span_half_open=[a,z],
            locator=dict(source_sha256=sha(f),physical_line_range_1based_inclusive=[raw[:a].count('\n')+1,raw[:z].count('\n')]),
            usage='同包同版原件第68条；超出此条bounded JSON的文本接口，明示消费差异'))
        base['source_consumption_difference']='第68条完整对象定义实际取自source_documents所列同包原件；当前JSON的source_full_text_resources为空且contexts仅有第70条支持范围，不声称其文本原已在当前JSON可消费。规则主证据为70日未上市分支；本审核支持F的替代依据为同版真实短缺分支。'
    if n=='04915':
        ptr='/explicit_or_primary_source_resources/0/source_texts/3';used.append(extra(item,b,ptr,'三是基层医疗卫生机构数量多、药品用量少、配送成本高，中西部和偏远地区尤为突出，企业配送积极性不高，药品供应不稳定、时常断供。','同政策官方解释的实际供应缺口'))
        used.append(extra(item,b,'/explicit_or_primary_source_resources/0/source_texts/6',at(b,'/explicit_or_primary_source_resources/0/source_texts/6')['text'],'同政策解释明确措施所针对问题'))
        used.append(extra(item,b,'/explicit_or_primary_source_resources/0/source_texts/11',at(b,'/explicit_or_primary_source_resources/0/source_texts/11')['text'],'官方解释与当前偏远配送措施直接映射'))
    base['used_context_quotes']=used
    lineids=[39,44,46,118,122,125,127,129] if dim=='I' else [39,44,46,147,149,151,155,158,166,170,172]
    if c['semantic_path'].startswith('I2'):lineids=[39,44,118,123,127,131,137,170]
    base['manual_clauses']=[dict(line_1based=i,text=manual_lines[i-1]) for i in lineids]
    if dim=='I' and c['semantic_path'].startswith('I3'):
        base['I3_evidence_check']=dict(object='按上述当前/同版适用原文明确的创新或改良研发项目',available_arrangement=curr,direct_connection=c['reason'])
    elif c['semantic_path'].startswith('I2'):
        base['I2_evidence_check']=dict(existing_or_proposed_use_obstacle='同段明确老年患者手指灵活性/合并症影响掰断操作，且需要剂量减半或调整',specific_product_change='当前参考掰断便利性数据改善片剂易碎性或开发不同强度/其他规格剂型',linked_improvement='明确针对上述剂量调整和掰断便利性障碍，未推定已证疗效优势',not_I3_by_guideline_title=True)
    elif dim=='F' and not c['semantic_path'].startswith('概括'):
        base['F_evidence_check']=dict(patient_drug_object='当前及所列语境中的所需药品治疗',gap_or_affordability_relation=c['reason'],arrangement_or_evaluation=curr,branches_not_extended=True)
        if n in ['00005','00006','00009','00010','00036','00038','00045','00047']:
            base['F_evidence_check']['gap_type']='no_effective_treatment_option'
        elif n=='01459':base['F_evidence_check']['gap_type']='no_domestic_approved_target_indication_option'
        elif n in ['01154','01157']:base['F_evidence_check']['gap_type']='patient_affordability'
        elif n in ['00110','00118']:base['F_evidence_check']['gap_type']='not_established_from_product_not_marketed_status'
        else:base['F_evidence_check']['gap_type']='actual_supply_gap_or_explicit_shortage_eligibility_branch'
    rows.append(base)

assert len(rows)==102 and len({(r['source_id'],r['dimension']) for r in rows})==102
new_keys={(x['source_id'],x['dimension']) for x in SCOPE['items'] if not x['prior_review']}
assert set(CASES)==new_keys,(set(CASES)-new_keys,new_keys-set(CASES))
jwrite('reviews.json',rows)
(HERE/'reviews.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows))
inputs=[MANUAL,META,RULEDIR/'predictions.jsonl',RULEDIR/'delivered-complete-source-bundles.jsonl',RULEDIR/'actual-source-consumption.jsonl',CODEDIR/'dimensions.py',CODEDIR/'relations.py',CODEDIR/'source_packet.py',CODEDIR/'rule_driver.py']
jwrite('input-bindings.json',dict(reviewer='non-human AI audit',frozen_inputs=[dict(file=str(p),sha256=sha(p)) for p in inputs],packets=[{k:x[k] for k in ['source_id','dimension','packet_file','packet_sha256','source_bundle_sha256','current_text_sha256']} for x in SCOPE['items']],original_files_modified=False,formal_LLM_partial_results_read=False,new_Codex_CLI_launched=False))
summary=dict(N=102,unique_records=81,rule_positive_by_dimension=dict(Counter(r['dimension'] for r in rows)),new_actual_read_dimension_items=89,prior_reviews_reused_dimension_items=13,
    assessment_counts=dict(Counter(r['assessment'] for r in rows)),review_value_counts=dict(Counter(str(r['review_value']) for r in rows)),
    by_dimension={d:dict(Counter(str(r['review_value']) for r in rows if r['dimension']==d)) for d in ['I','F']},
    human_review_dimension_items=[dict(source_id=r['source_id'],dimension=r['dimension'],review_value=r['review_value'],question=r.get('human_review_question') or r.get('newly_identified_boundary_question')) for r in rows if r['needs_human_review']],
    audit_is_nonhuman=True,no_human_accuracy_or_target_score_inference=True,
    note='89项本轮实际读完整当前及必要语境；13项引用此前核源审查并核相同整个source_bundle。未定不是0；本审核不是金标准，原规则值未覆盖。')
jwrite('summary.json',summary)
code_notes=[
 dict(source_ids=['RECODE25-00186'],dimension='I',rule_path='I3_actual_innovative_research_support',file=str(CODEDIR/'dimensions.py'),lines_1based=[94,95,720,723,780,783],explanation='SUPPORT含技术指导、SUPPORT_ACTION含可以；公共指南排除还要求起草/制定/提供指导等表达，本句普通“可以参考”未落入该排除，遂把公共引用误作可用支持。原规则decision的I3_arrangement确为技术指导，support_action为可以。'),
 dict(source_ids=['RECODE25-00349'],dimension='I',rule_path='general_evaluation_or_information',file=str(CODEDIR/'dimensions.py'),lines_1based=[460,464,471,473,476],explanation='通用路径匹配创新性、评价和药品对象，但未充分辨认创新性修饰工作而非药物产品；原规则正文锚点完整，语义误纳不是漏读当前。'),
 dict(source_ids=['RECODE25-00110','RECODE25-00118'],dimension='F',rule_path='F_need_linked_opportunity_allocation',file=str(CODEDIR/'dimensions.py'),lines_1based=[104,106,822,824],explanation='no_domestic_approved_option正则把“境外已上市…境内未上市…药品”与境内尚无药物获批目标适应症放在同类；两项原decision直接标为该缺口且无必要语境。品种未上市与选项不存在不等价，审核保留未定。'),
 dict(source_ids=['RECODE25-01729','RECODE25-02233','RECODE25-02269'],dimension='I',rule_path='I3_actual_innovative_research_support',file=str(CODEDIR/'relations.py'),lines_1based=[14,1470,1486,1508,1510,1516],explanation='ACTION识别决定开展/组织开展/同意开展；具名机制解析同版对象及直接时限/沟通机会。按冻结手册第46行，历史实施或目的/背景位置本身不排除，审查保留复核讨论后支持I3，不据此宣称今天仍能申请。'),
 dict(source_ids=['RECODE25-04613'],dimension='F',rule_path='F_need_linked_opportunity_allocation',file=str(CODEDIR/'dimensions.py'),lines_1based=[106,822],explanation='规则主证据为本JSON完整第70条的70日未上市罕见病分支。审核另取同包原件第68条真实临床急需短缺资格补当前支持，明确此定义不在本条JSON文本接口；两种来源消费与判据须分开。')]
for note in code_notes:
    lines=Path(note['file']).read_text().splitlines()
    note['file_sha256']=sha(note['file']);note['actual_code_lines']=[dict(line_1based=i,text=lines[i-1]) for i in note['lines_1based']]
code_log=dict(identity='非真人只读代码/既有判读日志核查，未重跑规则',observations=code_notes,decision_log=str(RULEDIR/'predictions.jsonl'),decision_log_sha256=sha(RULEDIR/'predictions.jsonl'))
for line in (RULEDIR/'actual-source-consumption.jsonl').open():
    x=json.loads(line)
    if x['id']=='RECODE25-04613':
        code_log['source_consumption_difference_04613']=dict(file=str(RULEDIR/'actual-source-consumption.jsonl'),sha256=sha(RULEDIR/'actual-source-consumption.jsonl'),id=x['id'],reader=x['reader'],available_resource_N=len(x['inventory']),resource_ids=[e['resource_id'] for e in x['inventory']],recorded_read_resources=list(dict.fromkeys(e['resource_id'] for e in x['actual_text_geometry_events'])),uniform_source_protocol_check=x['uniform_source_protocol_check'],audit_interpretation='只有BODY/CTX资源；同包metadata所列原件第68条未进入本记录文本资源inventory。原件确实存在并由本审核另行读取，不能冒称规则实际已读。')
        break
jwrite('rule-code-observations.json',code_log)
print(json.dumps(summary,ensure_ascii=False,indent=2))
