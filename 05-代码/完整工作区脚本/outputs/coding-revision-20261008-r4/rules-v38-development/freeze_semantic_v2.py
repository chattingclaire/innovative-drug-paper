"""Record root's construct correction and freeze revised controls before code."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,shutil
R=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(n,x):
 p=R/n;p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n');return p
snapshot=R/'iteration-v1-preserved'
snapshot.mkdir(exist_ok=False)
shutil.copytree(R/'runtime',snapshot/'runtime',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
for n in ['test_predeclared_v38.py','test_inherited_stability_v38.py','new36_constructed_controls_results_v38.json','new38_constructed_controls_results_v38.json','inherited_stability_results_v38.json']:
 shutil.copy2(R/n,snapshot/n)
review={
 'review_utc':datetime.now(timezone.utc).isoformat(),
 'trigger':'root独立语义复核指出两条F=0预期与既定关注构念冲突；尚未生成candidate38最终冻结/实际全量。',
 'basis':'v1.3每维1表示实质讨论而非已实现政策效果；v1.4条件、否定等可计维度，F1包括实际药物配备/供应范围及其纳入退出和具体条件。',
 'conclusion':'具有明确药品对象、供应范围和实质纳入/退出内容的拟议、建议本身可涉及F；不能以未实施或建议语气一律排除。纯申请办理/安排后续研究讨论职责且无实质标准或归属安排，仍不计本支F。',
 'v1_expectation_errors':[
  {'name':'effect-condition-versus-proposal-negative','original_expected_F':0,'corrected_F':1,'reason':'药物疗效证据条件与实际退出机构用药范围的命题明确。'},
  {'name':'conditional-permission-versus-advice-negative','original_expected_F':0,'corrected_F':1,'reason':'评估合格条件与实际纳入机构药品配备目录的命题明确。'}],
 'v1_status':'先前38合成控制的通过仅复现了含两项语义错误的v1预期，不能作为构念符合证明；原件与结果保留，v2另行冻结并替代采纳依据。',
 'v1_snapshot':str(snapshot.resolve()),'real_corpus_run':False,'no_new_reserved_text_read':True}
rp=write('semantic_reassessment_v2.json',review)
design=copy.deepcopy(json.loads((R/'preimplementation_design_v38.json').read_text()))
design.update(design_revision='v2-root-semantic-correction',frozen_utc=datetime.now(timezone.utc).isoformat())
design['ordinary_language_relation']=[
 '当前条款以实际药品为对象，实质讨论该药品纳入、调入、列入、退出、移出、调出或清退机构常规用药配备/供应目录或范围，计F的access子类型；1表示关注该范围安排，不表示其已实施或范围已扩大。',
 '必须约束实际药品对象、纳入/退出实质内容及机构常规用药供应范围；支持安全性、疗效或其他实质条件，否定、限制、拟议或建议均按本句实质内容判断。拟/建议本身不构成排除。',
 '只识别同一逗号分句中的明确主谓宾，或明确从该供应范围中退出某药品的倒装关系；不从另一分句、标题、文件名、部门身份或样本ID借药品对象。',
 '《》中的明确机构用药供应目录名仅可作为当前实质纳入/退出命题的宾语；整句文件标题不能成为谓词或药品对象。',
 '药品资料/企业/价格等不是实际药品对象；行政、资料、监测档案目录不是药品配备/供应范围。一般申请资格/办理路线，或仅组织研究讨论是否纳入退出而未陈述实质标准/归属安排，不按词面提到目录赋F。',
 '仅以现有目录身份限定价格上限、资料保存或其他事务时，不新增F；保留其他模块凭独立证据判定的S/E/Ec/I/F，不删除整个单元其他维度。']
design['minimal_implementation']='新增只增F证据模块，保留37.2所有生产代码；仅入口导入/调用/版本改变。v2去掉拟/建议一律排除，保留明确程序/申请门禁。'
dp=write('preimplementation_design_v38_v2.json',design)
old=json.loads((R/'preimplementation_controls_v38.json').read_text())
rows=copy.deepcopy(old['rows'])
replaced=[]
for row in rows:
 if row['name']=='effect-condition-versus-proposal-negative':
  replaced.append({**copy.deepcopy(row),'name':'substantive-proposed-exit-positive','pair':None,'expected_F':1,'expected_new_branch_F':True,'reason':'root复核：具体疗效条件下拟退出实际供应范围，属于关注F，不要求已实施。','origin':'v1错误负类转正类，保留原句'})
  row['constructed_text']='拟组织专家讨论是否将药物调出本机构临床用药范围。'
  row['reason']='仅安排后续讨论职责，无当前实际覆盖标准或归属安排；拟字不作为独立排除依据。'
 elif row['name']=='conditional-permission-versus-advice-negative':
  replaced.append({**copy.deepcopy(row),'name':'substantive-recommended-admission-positive','pair':None,'expected_F':1,'expected_new_branch_F':True,'reason':'root复核：评估合格条件下建议纳入真实配备目录，属于实质F。','origin':'v1错误负类转正类，保留原句'})
  row['constructed_text']='建议开展研究，讨论是否将药品纳入本院药品配备目录。'
  row['reason']='仅提出开展研究/讨论是否纳入的工作，无实质标准或具体归属安排；建议字不作为独立排除依据。'
rows+=copy.deepcopy(json.loads((R/'static_review_supplement_controls_v38.json').read_text())['rows'])
rows+=replaced
rows+=[{'name':'direct-proposal-mode-positive','pair':None,'constructed_text':'评估合格的药品拟纳入本院药品配备目录。','expected_F':1,'expected_new_branch_F':True,'reason':'拟为语气，实际药品范围及条件明确。'},
       {'name':'direct-recommendation-mode-positive','pair':None,'constructed_text':'出现严重安全风险的药品建议调出本院用药供应目录。','expected_F':1,'expected_new_branch_F':True,'reason':'建议为语气，实际药品退出范围及条件明确。'}]
cp=write('preimplementation_controls_v38_v2.json',{'constructed_only':True,'not_independent_validation':True,'expectations_frozen_before_v2_code_revision':True,'n_complete_pairs':19,'n_unpaired_supplemental_positives':4,'rows':rows})
fp=write('preimplementation_freeze_v38_v2.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),'design':{'path':str(dp.resolve()),'sha256':sha(dp)},'controls':{'path':str(cp.resolve()),'sha256':sha(cp)},'semantic_reassessment':{'path':str(rp.resolve()),'sha256':sha(rp)},'v1_freeze_sha256':sha(R/'preimplementation_freeze_v38.json'),'v1_static_supplement_freeze_sha256':sha(R/'static_review_supplement_freeze_v38.json'),'module_sha256_before_v2_revision':sha(R/'runtime/rules_supply_membership_v38.py'),'builder_sha256':sha(__file__),'n_constructed':len(rows),'no_v2_code_or_control_run_at_freeze':True,'actual_corpus_units_run':0})
print(json.dumps({'freeze_path':str(fp),'freeze_sha256':sha(fp),'design_sha256':sha(dp),'controls_sha256':sha(cp),'n':len(rows)},ensure_ascii=False))
