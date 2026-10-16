"""Freeze ordinary-language design/constructed expectations before candidate38 code."""
from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
DEST = BASE / 'rules-v38-development'
DEST.mkdir(exist_ok=False)
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(name, obj):
    p=DEST/name
    p.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
    return p

manual13=BASE.parent/'coding-revision-20261007-r3/protocol/完整五维手册-v1.3.md'
manual14=BASE.parent/'coding-revision-20261007-r3/future-human-validation-v5/手册/共用操作说明-v1.4.md'
parent=BASE/'rules-v37.2-development/candidate_freeze.json'
design={
 'candidate':'v38-institution-routine-drug-supply-membership-development',
 'frozen_utc':datetime.now(timezone.utc).isoformat(),
 'basis':{'v1.3':{'path':str(manual13),'sha256':sha(manual13),'section':'公平性F及保障/经济内容与实现'},
          'v1.4':{'path':str(manual14),'sha256':sha(manual14),'section':'公平性F第1及第4项'}},
 'ordinary_language_relation':[
   '当前条款明确以实际药品为纳入、调入、列入、退出、移出、调出或清退对象，并把机构常规用药配备/供应目录或范围作为该决定的对象，计F的access子类型。',
   '必须同时约束药品对象、具有实际效力的规定/决定及机构常规用药供应范围；支持安全性、疗效或其他实质条件，且退出/不予纳入/不得退出均不因方向而排除。',
   '只识别同一逗号分句中的明确主谓宾，或明确从该供应范围中退出某药品的倒装关系；不从另一分句、标题、文件名、部门身份或样本ID借药品对象。',
   '《》中的已明确机构用药供应目录名仅可作为当前实际纳入/退出谓词的宾语；整句文件标题不能成为谓词或药品对象。',
   '药品资料/企业/价格等不是实际药品对象；行政、资料、监测档案目录不是药品配备/供应范围。申请、拟议、建议、研究是否或目录工作路线不等于实际范围决定。',
   '仅以现有目录身份限定价格上限、资料保存或其他事务时，不新增F；保留其他模块凭独立证据判定的S/E/Ec/I/F，绝不删除整个单元的其他维度。'],
 'minimal_implementation':'新增一个在37.2末尾执行的只增F证据模块；仅改入口导入/调用/版本。37.2字节、旧冻结和手册不变。',
 'coverage_limits':['这是明确局部语法的有界实现，不是F构念的必要条件；未识别的语法/上下文关系不得据此宣称人工F=0。',
                    '不扩展至一般行政目录、试验分组供药、一般价格上限或医保申请路线。',
                    '本轮只运行继承合成控制和新合成控制；不自行全量，不运行实际01361，不读其他267保留成员正文/预测/标签。'],
 'exposed_development_case':{'id':'RECODE25-01361','already_exposed':True,
   'original_text_sha256':'3dbdeb3949965cc6fa16bfe53b84ba644d7ae2aa20d430590536e00b309cc251',
   'input_file_sha256':'fbee2777afe7e437ef1d2e0773e12a41ec3682914510f05f2dad2f31db7b6a6a',
   'read_scope':'仅root已明确披露原句与该ID原输入机械确认；不删除旧保留成员或暴露标记，不称独立验证。'},
 'parent_candidate_freeze':{'path':str(parent),'sha256':sha(parent)},
 'forbidden_features':['样本ID','部门','文件名含义','A/C或其他人工参照标签','模型标签','一致性或性能指标'],
 'control_interpretation':'每对正例表示实际药物范围安排，反例只改变实质关系；按手册先定语义预期，不按目标分数定预期。F预期不规定其他四维。'
}
pairs=[
 ('safety-exit','将出现严重风险的药品清退出本院用药供应目录。','将药品监测资料清退出本院资料目录。','退出实际药品供应范围与退出监测资料目录区分'),
 ('admission-versus-application','符合临床配备条件的药品应纳入本医疗机构常规用药目录。','符合申报条件的药品可申请纳入本医疗机构常规用药目录。','配备决定与申请机会区分'),
 ('drug-versus-dossier-object','本院应将不符合配备条件的药物从本院药品供应范围中移出。','本院应将不符合归档条件的药物资料从本院药品供应范围中移出。','明确药物对象与明确资料对象区分'),
 ('inverse-drug-versus-document','本院应从本院药品配备目录中剔除不符合条件的药品。','本院应从本院药品配备目录中剔除药品申报材料。','倒装退出药品与退出材料区分'),
 ('negative-admission-condition','未经必要评估的药品不得纳入本院常规用药目录。','未经形式审核的药品不得申请纳入本院常规用药目录。','实际负向纳入条件与申请资格区分'),
 ('retention-versus-opportunity','符合继续配备条件的药品不得退出本机构用药供应范围。','药品退出申请可以重新提出。','保障范围维持要求与重提申请机会区分'),
 ('quoted-scope-versus-title','该药品应列入《本院用药供应目录》。','文件名为《该药品应列入本院用药供应目录》。','目录名作真实宾语与整句文件名区分'),
 ('independent-decision-and-records','药品资料按期归档；该药品应调入本院药物供应范围。','药品资料按期归档；本院应调整申报资料目录。','独立实质供应决定不因另有档案要求被删除'),
 ('effect-condition-versus-proposal','疗效证据不足的药物应调出本机构临床用药范围。','拟将疗效证据不足的药物调出本机构临床用药范围。','实质范围规定与拟议区分，条件不局限安全关键词'),
 ('membership-versus-price-cap','本机构用药供应目录内的药品应调出本机构用药供应目录。','本机构用药供应目录内药品的供应价格不得高于最高限价。','目录实际退出与目录身份限定药价区分'),
 ('no-object-borrowing','药品监测出现风险，应将该药品退出本医疗机构常规配备范围。','药品监测出现风险，应将有关报告退出资料备查目录。','第二分句必须自身有药品对象及实际供应范围'),
 ('conditional-permission-versus-advice','评估合格的药品可以纳入本院药品配备目录。','建议将评估合格的药品纳入本院药品配备目录。','条件性实质规定与单纯建议区分'),
 ('decision-versus-administrative-premise','药品应纳入本院用药供应范围；应按编号归档申请材料。','药品纳入本院用药供应范围后应按编号归档申请材料。','当前实际决定与仅作事务前提的目录身份区分'),
 ('scope-versus-file-head','该药应移出本机构用药供应目录。','该药应移出本机构用药供应目录的备查文件。','范围为宾语与完整宾语中心词为文件区分'),
 ('drug-versus-enterprise','将药品列入本机构药品供应目录。','将药品企业列入本机构药品供应目录。','药品实体与企业对象区分'),
 ('from-formulary-versus-materials','不符合持续使用条件的药品必须从本医疗机构用药目录中退出。','药品应从本医疗机构资料目录中退出。','从实际用药范围退出与资料目录区分'),
 ('negative-condition-versus-research','该药品不得再纳入本院药品供应范围。','研究是否将该药品纳入本院药品供应范围。','负向实际范围条件与研究是否纳入区分'),
 ('drug-versus-office-supply','本机构将药物调入本机构常规配备范围。','本机构将办公用品调入本机构常规配备范围。','实际药物与办公用品区分')]
controls={'constructed_only':True,'not_independent_validation':True,'expectations_frozen_before_code':True,
 'rows':[{'name':n+'-'+kind,'pair':n,'constructed_text':t,'expected_F':value,'expected_new_branch_F':bool(value),'reason':why}
         for n,pos,neg,why in pairs for kind,t,value in [('positive',pos,1),('negative',neg,0)]]}
dp=write('preimplementation_design_v38.json',design)
cp=write('preimplementation_controls_v38.json',controls)
freeze=write('preimplementation_freeze_v38.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),
 'design':{'path':str(dp),'sha256':sha(dp)},'controls':{'path':str(cp),'sha256':sha(cp)},
 'builder':{'path':str(Path(__file__).resolve()),'sha256':sha(__file__)},
 'production_runtime_present_at_freeze':(DEST/'runtime').exists(),
 'n_constructed':len(controls['rows']),'n_pairs':len(pairs),'reference_or_metric_read':False})
assert not (DEST/'runtime').exists()
print(json.dumps({'freeze_path':str(freeze),'freeze_sha256':sha(freeze),'design_sha256':sha(dp),'controls_sha256':sha(cp),'n':len(controls['rows'])},ensure_ascii=False))
