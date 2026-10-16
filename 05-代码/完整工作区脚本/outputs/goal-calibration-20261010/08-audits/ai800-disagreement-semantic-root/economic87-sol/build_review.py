"""同一非真人AI复审者的Ec逐条核源结果；只在本次新目录保存。"""
import csv
import hashlib
import json
import subprocess
from collections import Counter
from pathlib import Path

ROOT=Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
BASE=ROOT/'outputs/ai-audit800-20261010'
OUT=Path(__file__).parent
MAT=BASE/'source-A/coder-A/materials'
SRC=BASE/'source-A/shared-source/source-files'
MAN=ROOT/'outputs/goal-calibration-20261010/03-manual/full4481-common-release-20261010-root/manual.txt'
CSV=BASE/'与规则法分歧清单.csv'
AIF=BASE/'AI原始判读-800条.jsonl'
RULE=ROOT/'outputs/goal-calibration-20261010/06-coding/rule-full4481-v2-root/run4481-first/predictions.jsonl'
NHSA20='bc3433f6a2c82561d29c2d6520411f027aac032b5deb87021cdd3a24e28bf4f0'
PLAN19='e3806c85b274ffd86c41b9780a316babd2f8a51f40c25b099a22132fa8cbcef9'
BID22='1c8a39cbe59f7f3da49ed1251a79b5ac29d768bee67126bcc190a2a5555a53ac'
RENEW22='ec242f41dc57add17fe1dc6fae86bb37029ea42d0351cf30d64c043890a2a674'
SCOPE21='6254faa98540ffcc445c6f5bbc877b0da6a07b5a05e3b3c3e9d209c297ce33ae'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
EXPECTED={
 str(MAN):'5ea7ab74d30fb79c4cbd1d7d6b2ae40c4f52a52360075f3552199de949f9cc7b',
 str(CSV):'f6893dc63ad3df54fb42f92e8ad5fd34d2c241b817a657d618d88cfe730ed257',
 str(AIF):'4d7273fc624f78073fa5c87d0abf649b3930f1b772f0f415f2b192192a751cc2',
 str(RULE):'3ce3f8d0cce25010312d3c697c8f84ed91e6f3e406f62f4962511f1a728e5552',
}
for p,sha in EXPECTED.items():assert digest(Path(p))==sha,p
DIS=[r for r in csv.DictReader(CSV.open(encoding='utf-8-sig')) if r['维度']=='Ec']
AI={r['source_id']:r for r in map(json.loads,AIF.open())}
RULES={r['id']:r for r in map(json.loads,RULE.open())}
assert len(DIS)==87

# 值、实际额外语境索引、手册操作路径、独立理由；null保存未定，不强填0。
C={
 'A-000008':(1,[],'价格测算与准入价格门槛','当前组织专家测算并以医保支付意愿作为通用名药品准入门槛，是实际形成价格/支付标准内容。按程序的并列形式不抹除这一经济安排；不要求写出金额或已经准入。'),
 'A-000012':(1,[],'基金支付能力与药品范围调整直接关系','当前统筹基金支付能力实际开展药品目录调整，是药品支付资源约束参与范围选择的关系，不仅是提高基金效率的宗旨。后半优化、公平目标不补出具体支付水平，也不推定患者可负担。'),
 'A-000016':(1,[],'确指经济数据准确性要求','“相关数据”明确承接同段每月反馈的药品费用和医保基金支出，当前要求其获取科学、及时、准确。是指定经济信息质量要求，非只与医保部门保持沟通或确认文件收到。'),
 'A-000034':(1,[],'概括药品经济评价与基金影响','当前要求两组专家从基金影响和药物经济学评价对谈判/竞价药品提出意见，经济评价内容与药品对象自足。专家组成不是单独依据，亦不是只出现经济学栏目名。'),
 'A-000036':(1,[],'药品报价条件与准入后果','当前报价均超100元这一明示价格门槛导致不入围、不纳入，是否定价格条件的实际后果。不能只因结尾是目录结果而清零，也不把构造政策例当真实市场报价。'),
 'A-000053':(0,[],'支付标准到期身份与甲乙分类排除','当前仅以支付标准到期为时间条件，经评审转入常规乙类，没有规定本句价格或分担规则。后句暂执行原标准是独立支付命题，不能倒借；外部乙类报销常识也不能补成Ec。'),
 'A-000058':(1,[],'实际组织药品谈判竞价','当前由国家医保经办机构组织经济学等专家实际开展药品准入谈判/竞价，同条完整分支核明这是决定目录或支付范围的具体磋商安排。不是仅列谈判阶段或协商成败；并不推定已经形成价格或成功。'),
 'A-000064':(1,[3],'指定药品基金支出的实质统计','当前明确医保部门统计基金实际支出，同段保留计算公式，父范围明确为协议期谈判药品续约。形成的是指定药品支付支出信息，非统计机构流程本身；不从目录身份推费用。'),
 'A-000070':(1,[3],'基金实际支出争议的补证核验','当前以企业与医保对药品基金实际支出分歧为条件，允许补充数据及协商，是经济核算证据内容的校核。补交步骤服务于已明确费用内容，不能按一般资料递交统一排除。'),
 'A-000072':(1,[],'实际药品报价形成','当前企业实际报价形成药品价格信息，同时提交承诺书。Ec依据是报价行为及同段明确竞价药品对象，非承诺书签章或后句成功纳入；无需报价已被接受。'),
 'A-000079':(None,[],'申报手续与既有支付协议续约条件边界','当前无论是否调整支付标准/范围均须目录申报，否则无法续约，可严格读为通用申报前置手续，未核验或授权任何支付内容。另一读法认为“不能续约”实质限制既有谈判支付安排的延续，符合条件—待遇关系。完整同段仅解释申报条件及身份，没有为本句明写费用/支付后果；也不能借平行续约计算条款补值。现手册对这种普通申报义务加既有支付协议不能续约的关系仍需统一，保存null。'),
 'A-000093':(1,[],'授权申请调整支付范围并确定新标准','当前直接准许按适应症等申请改变医保支付范围，并经程序确定新标准/范围和补充协议。是实质支付变更的机会及机制，非单纯目录申请身份；无需最后获批或写新金额。'),
 'A-000097':(1,[],'药品费用支付责任','当前医疗机构按合同及时结清企业款项，同段明确是药品供需和医保结算服务。规定药品供应费用支付义务，非一般行政收费；只补款项对象，不借前段特例付费。'),
 'A-000100':(1,[],'实际控制谈判药品降价幅度','当前通过优化续约规则合理控制协议期药品降价幅度，直接设价格调整安排。稳定新药预期是目的，不是Ec唯一依据；不把后句1类药重谈机制复制给当前。'),
 'A-000104':(1,[],'指定药品基金影响和经济学评估','当前要求从职工/居民基金影响及药物经济学评价提出谈判/竞价药品意见，属于明确经济内容评估。不是机构人员名录或仅经济栏目。'),
 'A-000135':(1,[],'指定药品基金影响和经济学评估','当前两组分别评价医保基金影响和药物经济学并形成药品评估意见，实质内容充分。不由“分组”这一组织形式单独赋Ec，依据是明确的评价对象及维度。'),
 'A-000138':(1,[3],'成员与父谓词构成费用支付条件','当前诊断/治疗目的承接父条：目录药品费用符合条件可由基金支付。这个成员实际限制费用获得支付的适用用途，形成条件—支付后果；不是孤立药品用途身份，也不自动赋E。'),
 'A-000140':(1,[],'药品基金支付情况监测','当前实际要求监测目录内谈判药品并及时掌握基金支付情况，是支付经济信息监测。可及性目标不代替经济依据，也不推为患者负担已下降。'),
 'A-000149':(None,[],'研究参照方法与经济评价内容边界','当前说明提前确定参照药给后续药物经济学研究提供基础。可读为建立特定经济评价比较基础；严格读法则只评价研究工具/时间的用途，未要求或开展成本、费用、预算等经济内容评价，也没有具体经济比较关系。完整同段后面实际参照药预沟通/确定安排是独立命题，不能倒借。需统一经济研究参照选择与仅一般方法步骤的界线，保存null。'),
 'A-000152':(1,[],'操作性价格/经济条件援引','当前目录内调整范围明确要求符合用药办法第9/10条。完整同版条件有药物经济性评估及同治疗领域价格/费用明显偏高、其他不符合经济性条件，实际用于资格。不是从目录名称推医保支付，也不把所有撤证或欺诈分支称经济。'),
 'A-000156':(1,[],'经济证据不足与概括药物经济评估','当前指出RCT药物经济学效益证据缺乏，并要求真实世界更全面评价和决策调整。实质评价药物经济内容，证据未定不清零；不因RWD方法名称自动赋Ec。'),
 'A-000184':(1,[],'药品基金支付情况监测','当前要求对谈判药品监测并掌握基金支付情况，属于指定经济信息形成。只用同段识别对象，不借前句确认支付标准或后文续约机制。'),
 'A-000207':(1,[],'价格和药品销售金额信息内容','当前明确要求药品市场/预期价格、挂网和给定时期销售金额，含规格及非独家限定。是价格/销售金额实质信息内容，不是经济栏目名或字段不能为空；价格未定时介绍预期仍属内容。'),
 'A-000208':(1,[],'饮片支付范围及排除的实质定义','当前界定饮片部分收载基金支付与不得纳入支付的范围，有明确支付责任/范围。虽然在目录组成说明中，命题仍有独立支付内容；不把西药/中成药的纯组成兄弟句全部赋Ec。'),
 'A-000213':(1,[],'药品配置使用指标与机构基金支付挂钩','当前把备药率、非医保用药率与机构基金支付挂钩，实质设药品使用—支付资源条件。属于Ec支付安排，不是基金安全宗旨，也不推定患者药费或健康产出。'),
 'A-000224':(0,[3],'申报类别与支付变更授权分开','当前主动申请调整范围描述已在申请的谈判药品，与父句仅组成目录内药品可按程序申报（单选）资格。没有授权本项支付变更、核验范围或须申报方可变更的具体后果；既有申请身份不能把普通目录申报升为Ec。'),
 'A-000230':(1,[],'明确实施药品医保支付条件限定','当前虽含安全和基金效益目的，但同时明确目录对部分药品医保支付条件施加限定。支付限制本身满足Ec，不需列具体金额；未从笼统安全目的推S，亦不把后文全部限定复制来。'),
 'A-000233':(1,[1,2],'药品经济评估的实际组织','当前组织专家以医保数据及药物经济学开展评估并提出意见；同版谈判阶段明确药品经济评估形成医保支付标准。是实施经济评价而非一般提交谈判材料；只补评估药品对象，不将其他阶段结果继承。'),
 'A-000239':(0,[3],'支付范围对象分类标题排除','当前仅标题“不调整支付范围的药品”，没有规定保持范围、价格或费用规则。父续约范围只说明对象，后文分档降幅不可倒借；标题的否定身份不等于实际不调整的制度安排。'),
 'A-000251':(1,[1,2],'基金测算与药物经济学评估','当前明确实施基金测算及药物经济学评估、提出意见；前段及标题补谈判药品对象。是具体经济评价要求，非仅测算专家构成或一般研究方法。'),
 'A-000252':(1,[],'价格测算与准入支付意愿','当前形成该通用名药品医保支付意愿作为准入门槛，价格/支付内容直接明示。程序措辞不改变门槛实质，未要求具体数字才计Ec。'),
 'A-000273':(1,[],'成本效果/效用和最小成本证据','当前鼓励在时间精力有限时提供较全面最小成本分析替代常见成本效用/效果材料，明确药品经济测算内容。并非只提交文件；保留条件，也不说不同经济方法必等效。'),
 'A-000276':(0,[3],'主动支付调整身份与目录申报分类','当前在时间、批准、适应症变化限定下描述主动申请支付范围调整的药品；父仅允许目录申报（单选）。未设置支付改变的授权/限制或内容核验，前兄弟因不一致调整条款也不能借来。'),
 'A-000280':(1,[],'实质条件—目录后果及经济评价成员','当前以完整五项条件经评审决定直接调出，具有实质条件—待遇后果，非纯冒号引导。第（三）项明确经济性因素参与风险收益评估，Ec成立；不凭目录结果或全部五项身份赋值。'),
 'A-000289':(1,[],'同版确指经济准入条件','当前明确要求符合方案第二部分（一）完整目录外条件，其中确指第7/8条；价格合理及无法单独收费排除是经济标准。实际标准链已核，不由普通目录身份推支付，也不借2021新版本。'),
 'A-000293':(0,[],'纯权责内容引导与兄弟支付后果分开','当前仅说明协议权利职责在下文列出，未自身设支付标准、价格、实质信息要求或条件—机会后果。已完整读四个成员，支付变更和费用准确性各为独立命题；不能因权责列表中存在经济内容把纯引导计Ec。'),
 'A-000295':(1,[],'明确否定基本医保支付责任','当前同时说商保目录供参考及基本医保不支付，后者直接划定药品支付责任边界，否定仍是Ec。前者不能解读成商业保险必承保；不借后文病例支付例外反写本句已获支付。'),
 'A-000307':(1,[],'完整经济准入标准与申报机会','当前用第7/8条及完整七项作为申报机会条件；同版价格合理与无法单独收费排除是实际经济内容标准。普通申报形式不抹除被操作性援引的经济条件，也不将各名单/时间成员独立经济化。'),
 'A-000310':(1,[2],'确指医保支付标准测算内容沟通','当前就药品测算思路/重点沟通，直接承接前项基金/经济学评估及医保支付标准意见。沟通内容为指定经济测算，不是仅面对面形式或一般企业诉求；不把企业意见当最终价格。'),
 'A-000333':(0,[],'到期目录乙类转换排除','当前只规定到期经评审进入常规乙类，支付标准是对象时间身份，未在本句确定费用分担或新价。后句暂执行现行标准不可倒借，甲乙分类自身按手册排除。'),
 'A-000337':(0,[],'版本呈现要求与实质经济信息控制的边界（初判0）','当前要求同时递交两版PPT，第二版去除经济/价格费用信息并按指定名称命名。按当前主行为，属于材料呈现/版本与公示操作，没有经济评价或价格内容核验，保留初判0；但明确删去指定经济内容也可能被读为实质信息披露限制。与“费用字段不能为空”不能简单等同，需统一版本删项是否达到经济信息安排门槛，已标需复核；不从标准版名称补出实际费用要求。'),
 'A-000342':(1,[],'价格测算与准入支付意愿','当前医保方实际提出通用名药品支付意愿作为准入门槛，直接价格测算安排。没有数字及含程序用语均非排除理由。'),
 'A-000348':(1,[],'药品价格协商意见责任','当前专家组成同时明确负责对药品提出价格协商意见，是实际价格评估职责。Ec来自价格内容，不来自商保/经济专家身份或目录已承保。'),
 'A-000377':(1,[],'药品自费率的费用考核口径限定','当前明确商保目录药品不计入基本医保自费率等指标，改变药品费用考核口径。是费用资源管理安排，非目录身份本身；不等于患者无需自费、基本医保支付或商业保险实际承保。'),
 'A-000383':(1,[],'药品支付标准降幅公式','当前用A/B既有降幅及扣减确定续约最终降幅；同段明确为药品医保支付标准。是价格调整算法，非抽象统计方法或仅续约阶段，保留复合公式与前一年扣减限定。'),
 'A-000392':(1,[],'实际竞价药品报价','当前企业按要求报价并提交承诺书，报价是药品价格信息形成。承诺书形式不抹除并列的经济行为，亦不借后文纳入结果定值。'),
 'A-000401':(1,[],'政策举例的药品支付价格测算','当前政策构造例明确测算医保支付意愿100元，属于药品价格门槛内容；不是仅企业数或竞价参与身份。只计政策文本中的经济关系，不当作实际药品成交数据。'),
 'A-000415':(1,[],'完整经济准入标准与申报资格','当前用第7/8条及八项范围作为2026申报条件，价格合理及不能单独收费标准实际用于准入。完整同版成员/排除已核，多选只是形式；不将目录名称或每个批准日期独立赋Ec。'),
 'A-000437':(1,[],'明确报价门槛与否定准入','当前在构造例中两家报价均高于100元便不入围及不纳入，明确价格—后果。不是仅列成败或目录结果，否定仍有经济议题。'),
 'A-000446':(1,[],'药品个人自付比例的实质决定权','当前省级/统筹医保部门决定乙类个人先行自付比例，直接规定费用分担内容的决定主体。与纯甲乙类别划分不同，不需已给具体比例。'),
 'A-000450':(1,[3],'完整药费/预算/价格条件—简易续约机会','当前满足完整五项可获得两年简易续约，经济条件明示药费不超预算200%、未来预算增幅及市场价格重大变化。完整条件含独家和常规目录排除均保留，Ec依据是实际经济标准使用而非续约名称或期限本身。'),
 'A-000452':(1,[],'同版价格结果有效期的实际限制','当前设同一非独家竞价结果两年有效期。核2022规则完整相关条款：竞价结果形成支付标准，且企业在竞价有效期内承诺供药价不超过报价；期限实际限定该价格约束。不是行政证件有效期或纯目录结果身份，未展开集中采购一般援引或其他并行义务。'),
 'A-000478':(1,[2,3],'药物试验相关治疗费用承担','当前申办者承担药物临床试验参与者损害诊疗费及赔偿，明确费用责任及治疗对象。不是科研项目经费或纯伦理手续，费用损害救济已明示；Ec成立不要求S的药物损害因果也已确定。'),
 'A-000481':(1,[],'当前负担要求的经济含义有限解释','当前要求减轻药物临床试验受试者负担，同一连续段具体解释包括儿童随访导致监护人误工、收入损失等经济负担。可有限用这个说明解释当前“负担”的范围，而不是把下句访视规划新措施倒借。药物治疗试验参与的患者/家庭资源成本有明确联系，非一般研究项目经费；不把所有不便利都经济化。'),
 'A-000489':(1,[],'形成医保底价并实际磋商','当前根据测算形成基本目录医保底价并开展谈判/竞价，价格形成机制自足。结果确认书及失败签署的手续分支不取消底价内容，失败亦不证明价格被接受。'),
 'A-000513':(1,[],'竞价药品价格信息形成','当前企业实际报价与承诺书并列，属于价格信息形成。程序要求不能把报价统一归形式，不依赖其后的成功支付结果。'),
 'A-000534':(1,[2],'同版同一价格谈判的实际职责','当前组成专家并赋与药品企业现场谈判职责，实际实施同一药品价格磋商安排。同版2019方案明确该谈判组形成全国医保支付标准，补的是当前已表达谈判的直接机制；非一般专家身份或只阶段名称，也不把谈判成功目录结果单独当经济。'),
 'A-000536':(1,[3],'不符合确指标准与简易续约条件','当前成员把不符合常规目录管理条件作为简易续约的必要资格条件；核2022同版完整常规目录两项标准，包含连续两协议未调整支付标准/范围。是经济条件实际用于另一续约机会，否定不清零；非借其他简易续约兄弟费用项，也不声称药品两项均失败。'),
 'A-000557':(1,[],'协商形成药品结算价','当前直接通过协商合理确定商保目录药品结算价并探索价格保密，实质价格安排。不是仅商保目录结果或保险参考身份，亦不等同基本医保或商保已经支付。'),
 'A-000558':(0,[3],'支付调整申请对象与目录申报归类','当前时间/批准/适应症变化限定后，主动申请支付调整是被申报药品身份；父句仅准许目录内申报（单选）。没有本项支付变更授权/限制或内容核验，兄弟续约后果不可倒借。'),
 'A-000563':(1,[],'实际药品价格磋商组织','当前明确专家负责与药企现场价格协商，实际设置价格磋商职责。价格内容自足，不只商保/医保人员身份，也不以协商成功才计。'),
 'A-000564':(1,[],'通过谈判竞价确定药品支付标准','当前根据评估意见实际谈判/竞价以确定全国统一支付标准及管理政策，经济机制明确。不是仅谈判阶段或签约结果；不需具体金额。'),
 'A-000566':(1,[],'申报药品费用信息的内容范围','当前申报内容明确包括药品费用信息，并指明具体要求来源。实质信息内容要求超过费用栏目标题、非空检查或递交步骤；这里只编码明确费用内容，不无限展开申报系统其他字段。'),
 'A-000577':(1,[],'同版经济准入标准—评审范围','当前以第7/8条及完整2021五项范围决定可进入评审，价格合理及无法单独收费标准被实际使用。无需把拟评审解释成已医保支付；保留全部成员且不从其身份继承其他经济标准。'),
 'A-000588':(1,[3,4],'药品基金预算合理性条件','当前要求未来两年基金预算增幅合理，直接父范围核明为谈判药品简易续约条件。定性预算约束足以Ec，不要求数字；独家资格或前句200%不复制给当前。'),
 'A-000598':(1,[3],'完整基金支出/预算/价格条件的应用','当前完整条件决定两年简易续约，明确药品实际基金支出、预算增幅和市场价格变化。属于实质条件—机会，总领不是纯列表引导；完整成员不漏独家及常规目录排除，但各成员仍分别判断。'),
 'A-000634':(1,[],'药品费用计算对象与规格范围','当前定义费用为基金及参保人共同支付并纳入全部规格计算，同段明确医保范围药品费用和销售预算。直接规定经济信息口径，不是查询模块操作或付款名称。'),
 'A-000638':(1,[],'双渠道实际药品医保支付机制定义','当前完整定义双通道同时通过医疗机构/药店并同步纳入医保支付，有自足的具体支付安排。虽然是概念定义，超过名称或供应身份；不借全文宗旨推更多费用关系。'),
 'A-000640':(0,[3],'支付范围对象标题与后文规则分开','当前仅标题“调整支付范围的药品”，沒有在本句授予调整、规定价格/责任或核验范围。前段支付标准降幅和后文调整公式为独立命题，不能倒借；目录/续约对象身份不足Ec。'),
 'A-000657':(0,[3],'目录调整范围的申请对象描述','当前描述主动申报支付范围调整的常规目录品种，父只是公布药品目录调整范围。未实际授权、限制支付变更或核验内容；适应症变化及申请身份不等于本项支付后果，另兄弟条件不可补入。'),
 'A-000677':(1,[],'药品企业报价与支付意愿比较','当前实际比较企业报价和医保支付意愿决定准入，明示价格评价内容和后果。不能只按目录结果排除，也不把比较结论当已成交价格。'),
 'A-000680':(1,[],'同版确指经济准入条件','当前要求符合2021方案第二部分（一）完整范围，确指第7/8条价格合理及不能单独收费排除。实际经济标准使用可Ec，非仅目录外身份或从后续支付常识推定；完整2021成员均已核。'),
 'A-000683':(1,[],'企业报价上限的价格比较','当前以两年省最低中标价及申报市场零售价限制报价，属于明确药品价格约束。既有价格作为基准仍有实质内容，非仅资料提交或字段填写。'),
 'A-000695':(1,[3],'经济数据争议的核算证据口径','当前无法一致时采用医保方数据，同段明确争议是药品基金实际支出。有限补所指数据后是费用核算证据采用规则，不是笼统协商成败；未将采用数据误称价格协商达成。'),
 'A-000711':(1,[],'报价与支付意愿条件—目录准入','当前至少一家报价不超过医保支付意愿才能纳入，否则不纳入。真实价格条件及双向后果自足，不凭“乙类”分类常识或仅成功失败词汇赋Ec。'),
 'A-000724':(1,[],'现场药品价格磋商安排','当前实际组织现场价格协商，并分别写成功目录及承诺后果。Ec依据是价格磋商而非目录推荐等同医保/商保承保；没有具体金额、协商可能失败均不排除。'),
 'A-000726':(1,[],'药品基金影响和经济学评估要求','当前两组对谈判/竞价药品分别评价基金影响及经济学，实质经济评价明确。不是专家组织身份或费用栏目。'),
 'A-000733':(1,[],'同版价格/经济条件实质应用','当前要求目录内范围符合第9/10条，完整同版包括药物经济性、价格费用过高及不符合经济性条件。Ec来自操作性标准使用，不凭目录调整结果或其他撤证分支。'),
 'A-000734':(1,[3],'基金实际支出数据的最终采用','当前协商无一致时以医保数据为准，明确同段所指为药品基金实际支出分歧。是经济证据口径，非一般协商结果；不同原文记录仍各计一次不合并删去。'),
 'A-000746':(1,[3],'药品基金支出分歧的实质补证','当前费用分歧允许补充数据及协商，明确核验药品基金实际支出内容。不是只递交数据步骤；保留较大分歧条件，不推定协商已一致。'),
 'A-000754':(0,[],'原件完整申报范围与支付申请身份分开','当前在2021附件“申报药品的范围”目录内第二项描述主动申请支付范围调整品种。原件页8完整两项已核，当前没有授予支付范围变更、规定须申报方可变更或核验支付信息；第一项需重定支付标准的兄弟后果不能借。普通申报资格不是实际支付授权。'),
 'A-000757':(1,[3],'药品基金支出分歧的经济补证','当前2022续约下，对基金实际支出争议允许补充数据及协商，要求核经济信息。只是引用同版范围解释药品对象，不复制其他年份支付规则或后句数据优先结论。'),
 'A-000760':(1,[],'药品价格协商的实质决定权','当前商保专家被赋药品价格协商重要决定权，是价格磋商安排的实际治理权限。与药品进目录的并列决定分开，Ec只记价格关系，不推成实际保险支付。'),
 'A-000762':(1,[1],'实质药品价格测算和经济评估','当前同段明确开展价格测算评估，并实施基金测算/经济学评估和提出意见。具有药品价格评估内容，不是仅一般专家流程或方法名称；标题只补目录谈判对象。'),
 'A-000788':(1,[],'完整经济准入标准与2021申报范围','当前第7/8条及完整四种目录外情形限定申报机会，价格合理、无法单独收费排除为实质经济准入标准。同版完整来源已核；不声称资格药品已获支付，不把成员名单单独经济化。'),
 'A-000789':(1,[],'通用名药品支付意愿测算门槛','当前2022竞价规则实际测算医保支付意愿并设准入门槛，药品经济内容自足。按程序语气及未写金额不抹除实质价格安排。'),
 'A-000791':(1,[],'支付标准最终降幅的比较选择','当前最终下调比例取两方法较高值，同段完整说明药费3亿元区间10%与简易续约计算两法。是明确支付标准调整算法，非一般方法比较或纯常规乙类结果；两法和市场重谈例外不擅自互换。'),
}
assert set(C)=={r['A盲号'] for r in DIS}

Q={
 'A-000079':'目录申报义务导致既有谈判协议不能续约，是否已经构成支付待遇延续的实质限制，还是仍按普通申报/续约手续排除？应以哪一当前锚点和同版直接机制区分？',
 'A-000149':'提前确定参照药并说明它给药物经济学研究提供基础，是否已经表达经济评价比较内容，还是仅通用研究方法/时间用途？不得用后句实际预沟通或其他价格条款替代当前。',
 'A-000337':'要求另交删除经济/价格费用信息的PPT版本，属于材料呈现操作，还是对指定经济内容的实质披露限制？保留当前初判0，需统一与字段非空、价格保密两类的界线。',
}

def ctx(d,bid,i,use='只解释当前明确对象、指代、条件或边界；不继承相邻独立命题'):
 c=d['source_record']['contexts'][i];assert c.get('text')
 return {'quote':c['text'],'file':str(MAT/(bid+'.json')),'json_pointer':f'/source_record/contexts/{i}/text','kind':c.get('kind'),'resource_id':c.get('context_id'),'original_source_ref':c.get('source_ref'),'use':use}

def kind_quotes(d,bid,wanted,use):
 out=[];seen=set()
 for i,c in enumerate(d['source_record']['contexts']):
  if c.get('kind') in wanted and c.get('text') and c['text'] not in seen:
   seen.add(c['text']);out.append(ctx(d,bid,i,use))
 return out

def doc_title(d,bid,ix):
 return {'quote':d['source_documents'][0]['source_title_lines_verbatim_extraction_candidates'][ix],
         'file':str(MAT/(bid+'.json')),'json_pointer':f'/source_documents/0/source_title_lines_verbatim_extraction_candidates/{ix}',
         'source_sha256':d['source_documents'][0]['source_sha256'],
         'use':'只核经济测算的药品对象；文件题名本身不成为Ec依据'}

def text_lines(sha,lo,hi,use):
 p=SRC/(sha+'.txt');ls=p.read_text().splitlines()
 return {'quote':'\n'.join(ls[lo-1:hi]),'file':str(p),'line_range_1based_inclusive':[lo,hi],'source_sha256':sha,'use':use}

def pdf_pages(sha,pages,use):
 # 原PDF只读；衍生文字仅写本目录，保留每页布局文本和可重现提取命令。
 out=[];(OUT/'pdf-excerpts').mkdir(exist_ok=True)
 for page in pages:
  p=SRC/(sha+'.pdf');cmd=['pdftotext','-f',str(page),'-l',str(page),'-layout',str(p),'-']
  txt=subprocess.check_output(cmd,text=True)
  q=OUT/'pdf-excerpts'/(sha+'-p'+str(page)+'.txt');q.write_text(txt)
  out.append({'quote':txt,'file':str(p),'physical_pages_1based':[page],'source_sha256':sha,'extraction_file':str(q),
              'extraction_method':'pdftotext -f PAGE -l PAGE -layout SOURCE -; UTF8','use':use})
 return out

REF78={'A-000289','A-000307','A-000415','A-000577','A-000680','A-000788'}
REF910={'A-000152','A-000733'}
MEMBERS=REF78|{'A-000280','A-000293','A-000450','A-000598'}

def ext(d,bid):
 if bid in REF78:return [text_lines(NHSA20,17,19,'核第7/8条完整同版价格/收费条件及排除，不漏任何成员')]
 if bid in REF910:return [text_lines(NHSA20,21,23,'核第9/10条完整同版经济性/价格费用条件及并列范围')]
 if bid=='A-000058':return [text_lines(NHSA20,35,35,'核当前组织同一药品谈判竞价条款完整直接机制和并列后果')]
 if bid=='A-000233':return [text_lines(PLAN19,85,91,'仅补当前2019同一药品经济评估对象及其支付标准测算机制')]
 if bid=='A-000534':return [text_lines(PLAN19,43,49,'同版同一谈判专家/谈判组与医保支付标准的直接机制')]
 if bid=='A-000452':return pdf_pages(BID22,[1,2],'已读并看图；同一竞价支付结果定义、供药价格承诺及有效期，保留全部限定')
 if bid=='A-000536':return pdf_pages(RENEW22,[1,3],'已读并看图；当前不符合常规目录标准须完整读两项常规资格，保留简易续约成员位置')
 if bid=='A-000754':return pdf_pages(SCOPE21,[8],'已读并看图；完整附件两项申报范围，界定当前为申报对象，不倒借兄弟支付后果')
 return []

def manual_ev(path):
 ls=MAN.read_text().splitlines();lo=next(i for i,l in enumerate(ls) if l.startswith('## 五、经济性 Ec'));hi=next(i for i,l in enumerate(ls) if l.startswith('## 六、创新性 I'))
 out=[{'file':str(MAN),'line_range_1based_inclusive':[lo+1,hi],'quote':'\n'.join(ls[lo:hi])}]
 if any(w in path for w in ['标准','条件','成员','同版','资格','申报']):targets=['- 当前有“应包括下列”','- “详见工作方案”']
 elif any(w in path for w in ['信息','数据','证据','方法','版本']):targets=['**概括性评价要求与具体机制分开。**','**资料与证据也用同一门槛。**']
 else:targets=['**五维使用同一实质门槛：**','4. **限定必要语境。**']
 for t in targets:
  ix=next(i for i,l in enumerate(ls) if l.startswith(t));out.append({'file':str(MAN),'line_range_1based_inclusive':[ix+1,ix+1],'quote':ls[ix]})
 return out

input_paths={Path(p) for p in EXPECTED};sources={};data={}
# 不读正式LLM全量或部分输出；只读取授权的800原AI及原规则首答。
for row in DIS:
 bid=row['A盲号'];p=MAT/(bid+'.json');input_paths.add(p);d=json.loads(p.read_text());data[bid]=d
 for doc in d['source_documents']:
  sha=doc['source_sha256'];matches=[p for p in SRC.glob(sha+'.*') if digest(p)==sha];assert matches,(bid,sha)
  input_paths.add(matches[0]);sources[str(matches[0])]=sha
for sha in [NHSA20,PLAN19]:
 p=SRC/(sha+'.txt');assert digest(p)==sha;input_paths.add(p);sources[str(p)]=sha
before={str(p):digest(p) for p in sorted(input_paths)}
reviews=[]
for n,row in enumerate(DIS,1):
 bid=row['A盲号'];d=data[bid];s=d['source_record'];sid=s['id'];a=AI[sid];ru=RULES[sid]
 val,ixes,path,reason=C[bid]
 assert sid==row['原记录号'] and s['text']==row['当前完整命题']
 assert a['judgments']['Ec']['value']==int(row['本轮AI值']) and ru['labels']['Ec']==int(row['规则法值'])
 ev=[]
 if s['contexts'][0].get('text')!=s['text']:ev.append(ctx(d,bid,0))
 ev.extend(ctx(d,bid,i) for i in ixes)
 if bid=='A-000762':ev.extend(doc_title(d,bid,i) for i in [1,2])
 if bid in MEMBERS:ev.extend(kind_quotes(d,bid,{'ordered_members'},'完整核被指向条件/成员及否定例外；不用兄弟内容替代当前'))
 if bid in REF78|REF910:ev.extend(kind_quotes(d,bid,{'cited_article'},'完整核当前确指条文；只补实质价格/费用标准链'))
 ev.extend(ext(d,bid))
 unique=[];seen=set()
 for e in ev:
  key=(e['file'],e.get('json_pointer'),tuple(e.get('line_range_1based_inclusive',[])),tuple(e.get('physical_pages_1based',[])))
  if key not in seen:seen.add(key);unique.append(e)
 human=bid in Q
 if human:assessment='手册边界待核';etype='待统一操作边界'
 elif val==1 and ru['labels']['Ec']==0:assessment='规则遗漏依据';etype='规则漏判'
 elif val==0 and ru['labels']['Ec']==1:assessment='规则过度纳入';etype='规则过度纳入'
 elif val==0:assessment='AI不符合现手册';etype='AI过度纳入'
 else:assessment='AI遗漏依据';etype='AI遗漏'
 reviews.append({
  'blind_id':bid,'source_id':sid,'dimension':'Ec','ai':a['judgments']['Ec']['value'],'rule':ru['labels']['Ec'],
  'review_value':val,'suggested_value':val,'initial_review_value':val,'review_status':'未定' if val is None else '初判待边界核定' if human else '已核定AI复审建议',
  'assessment':assessment,'error_type':etype,'check_group':'经济性全部87项分歧','selection_order':n,
  'reviewer':'AI-Codex-economic87-sol','reviewer_model_requested':'gpt-6.1-sol','reviewer_reasoning_effort_requested':'ultra','is_human_review':False,
  'review_identity_note':'与I22及S89同一非真人AI语义复审者；已见双方首答，非真人、非正式金标准、非新盲法结果。',
  'current_original':s['text'],'current_location':{'file':str(MAT/(bid+'.json')),'json_pointer':'/source_record/text','source_ref':s['source_ref']},
  'actual_context_evidence':unique,'manual_clauses':['§一五维同一实质门槛','§二当前完整命题、有限同版语境与成员规则','§五经济性Ec定义/纳入/排除/边界',path],
  'manual_evidence':manual_ev(path),'manual_file':str(MAN),'manual_sha256':EXPECTED[str(MAN)],
  'reason':reason,'needs_human_review':human,'human_review_question':Q.get(bid),'material_missing':False,
  'ai_original_judgment':a['judgments']['Ec'],'rule_original_decision':ru['decisions']['Ec'],'read_material_sha256':digest(MAT/(bid+'.json')),
  'evidence_consumption_difference':{
   'review_current_consumed_in_full':True,'review_context_locations':[{'file':e['file'],'json_pointer':e.get('json_pointer'),'line_range_1based_inclusive':e.get('line_range_1based_inclusive'),'physical_pages_1based':e.get('physical_pages_1based')} for e in unique],
   'original_ai_reported_locator':a['judgments']['Ec'].get('locator'),'original_rule_reported_basis_path':ru['decisions']['Ec'].get('basis_path'),'original_rule_reported_context_evidence':ru['decisions']['Ec'].get('context_evidence'),
   'interpretation_note':'只比较首答已报告依据与本复审实际引文范围，不推断原模型未引用即未阅读；语义消费差异及禁止倒借的关系逐条写在reason。',
  },
 })
assert len(reviews)==87 and len({r['source_id'] for r in reviews})==87
assert Counter((r['ai'],r['rule']) for r in reviews)=={(1,0):75,(0,1):12}

def pointer(d,p):
 v=d
 for k in p.strip('/').split('/'):
  k=k.replace('~1','/').replace('~0','~');v=v[int(k)] if isinstance(v,list) else v[k]
 return v

validation=[];nquotes=0;nctx=0
for r in reviews:
 d=json.loads(Path(r['current_location']['file']).read_text());assert pointer(d,r['current_location']['json_pointer'])==r['current_original']
 assert r['current_original']==DIS[r['selection_order']-1]['当前完整命题']
 checks=[]
 for e in r['actual_context_evidence']+r['manual_evidence']:
  p=Path(e['file'])
  if 'physical_pages_1based' in e:
   assert digest(p)==e['source_sha256'];page=e['physical_pages_1based'][0]
   actual=subprocess.check_output(['pdftotext','-f',str(page),'-l',str(page),'-layout',str(p),'-'],text=True)
   assert Path(e['extraction_file']).read_text()==actual
  elif 'json_pointer' in e:actual=pointer(json.loads(p.read_text()),e['json_pointer'])
  else:
   lo,hi=e['line_range_1based_inclusive'];actual='\n'.join(p.read_text().splitlines()[lo-1:hi])
  assert actual==e['quote'],(r['blind_id'],e);nquotes+=1
  checks.append({'file':e['file'],'json_pointer':e.get('json_pointer'),'line_range_1based_inclusive':e.get('line_range_1based_inclusive'),'physical_pages_1based':e.get('physical_pages_1based'),'exact_match':True})
 nctx+=len(r['actual_context_evidence'])
 validation.append({'selection_order':r['selection_order'],'blind_id':r['blind_id'],'source_id':r['source_id'],'dimension':'Ec','actual_current_read':True,
  'current_csv_material_exact_match':True,'original_values_join_verified':True,'material_sha256':r['read_material_sha256'],'evidence_location_checks':checks})
after={str(p):digest(p) for p in sorted(input_paths)};assert before==after
for p,sha in EXPECTED.items():assert after[p]==sha
counts=Counter('null' if r['review_value'] is None else str(r['review_value']) for r in reviews)
assess=Counter(r['assessment'] for r in reviews)
manifest={
 'reviewer':'AI-Codex-economic87-sol','is_human_review':False,'scope':'原CSV筛Ec的全部87项，保持原顺序；75 AI1/规则0、12 AI0/规则1',
 'expected_frozen_input_sha256':EXPECTED,'source_input_hashes_before_output':before,'source_input_hashes_after_output':after,'input_hashes_unchanged':True,
 'source_original_bytes_sha256_verified':sources,'review_count':87,'original_pair_counts':{'AI1_rule0':75,'AI0_rule1':12},'review_value_counts':dict(counts),'assessment_counts':dict(assess),
 'undetermined_blind_ids':[r['blind_id'] for r in reviews if r['review_value'] is None],'needs_human_review_blind_ids':[r['blind_id'] for r in reviews if r['needs_human_review']],
 'provisional_zero_blind_ids':['A-000337'],'current_texts_exact_verified':87,'actual_context_quote_count':nctx,'context_and_manual_quote_locations_exact_verified':nquotes,
 'actual_read_statement':'本复审按原清单順序实际逐条读完87项当前完整命题、原AI Ec依据以及必要同版段落/父谓词/完整成员；独立读取2022竞价规则物理页1—3、2022续约规则页1—3、2021申报范围页7—8、2019方案同一谈判机制及2020办法7—10/16条。实际看过2022竞价页1/2、续约页1/3、2021申报范围页8共5张原件渲染图。不是以加载全包推称语义读完，亦未读取正式LLM全量部分输出。',
 'pdf_pages_actually_viewed':[{'source_sha256':BID22,'physical_pages_1based':[1,2]},{'source_sha256':RENEW22,'physical_pages_1based':[1,3]},{'source_sha256':SCOPE21,'physical_pages_1based':[8]}],
 'limits':'74项1、10项确定0另1项初判0、2项null；结果仅非真人AI复审建议，非正式金标准。已见双方值，不是盲判。未按期待分数/部门占比修改定义，未回写生产标签。未声称800每条或所有全文均语义审读。',
 'source_or_production_files_modified':False,'previous_I_and_S_outputs_modified':False,'new_Codex_CLI_started':False,'formal_LLM_partial_outputs_read':False,'writes_restricted_to':str(OUT),
}
(OUT/'reviews.json').write_text(json.dumps(reviews,ensure_ascii=False,indent=2)+'\n')
(OUT/'reviews.jsonl').write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in reviews))
(OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(OUT/'validation.json').write_text(json.dumps({'scope_record_count':87,'quote_location_checks':nquotes,'passed':True,'records':validation},ensure_ascii=False,indent=2)+'\n')
(OUT/'human_review_questions.json').write_text(json.dumps([{'blind_id':r['blind_id'],'source_id':r['source_id'],'dimension':'Ec','review_value':r['review_value'],'human_review_question':r['human_review_question'],'is_human_review':False} for r in reviews if r['needs_human_review']],ensure_ascii=False,indent=2)+'\n')
md=['# 经济性87项分歧：非真人AI逐条核源复审','',
 '身份：与I22、S89相同的AI复审者，非真人，已见双方原首答，非盲法首判或正式金标准。保留I/S文件；未读正式LLM全量部分输出、未新开CLI、未改原始或生产表。','',
 f'原CSV顺序全部87项实际阅读完成（75 AI1/规则0，12 AI0/规则1）。本次74项建议1，11项建议0（其中A-000337保留初判0并需复核），2项null未定。74项1均有规则遗漏依据；10项确定0为规则过度纳入。','',
 '规则遗漏集中于支付意愿/报价及价格门槛、药物经济学和基金影响评价、费用/销售及支出信息形成或准确性核验、实际支付限制及变更、同版完整经济标准的操作性援引。资格条件决定实质经济机会时不要求具体金额或最终获批；当前明确价格磋商也不因处在谈判阶段或有失败分支被清空。','',
 '确定0主要为到期转常规乙类、仅“不调整/调整支付范围”的对象标题、主动调整作为目录申报分类身份、纯权责列表引导。没有借甲乙支付常识、兄弟支付公式或文件后文给当前加标签。','',
 '待统一3项：A-000079（通用目录申报与既有支付协议续约的限制，null）、A-000149（提前参照药选择与经济评价内容界线，null）、A-000337（另交删除经济信息PPT版本的呈现/披露边界，初判0）。具体问题单列human_review_questions.json，未知未硬填0。','',
 f'87项完整当前/原CSV/ID及双方值全核；{nctx}条实际上下文与手册共{nquotes}处引文逐项验证精确JSON指针、1基行或PDF物理页，原PDF逐页重提取比对。冻结输入和本轮读取材料/原件SHA在输出前后保持一致，原件另核记录SHA。范围与检验逐项见validation.json/manifest.json。','',
 '|序号|盲号|原记录号|AI|规则|本次建议|分类|需复核|','|---:|---|---|---:|---:|---|---|---|']
for r in reviews:md.append(f'|{r["selection_order"]}|{r["blind_id"]}|{r["source_id"]}|{r["ai"]}|{r["rule"]}|{"null（未定）" if r["review_value"] is None else r["review_value"]}|{r["assessment"]}|{"是" if r["needs_human_review"] else "否"}|')
(OUT/'report.md').write_text('\n'.join(md)+'\n')
print(json.dumps({'review_count':87,'review_value_counts':counts,'assessment_counts':assess,'context_quotes':nctx,'quote_checks':nquotes,'input_hashes_unchanged':True,'output':str(OUT)},ensure_ascii=False,indent=2))
