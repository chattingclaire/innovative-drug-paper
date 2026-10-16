"""Remaining-dependency examples fixed before first execution; not labels/gold."""
import json,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
from source_packet import semantic_unit
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions
from semantic_selfcheck import unit
P=Path(__file__).resolve().parent;ROOT=P.parents[5]
ACTUAL=[(173,{'S':1}),(611,{'S':1}),(415,{'S':1,'E':1,'Ec':1}),(384,{'S':1,'E':1}),(772,{'S':1}),(12,{'Ec':1}),(64,{'Ec':1}),(100,{'Ec':1}),(377,{'Ec':1}),(310,{'Ec':1}),(419,{'S':1})]
SYNTHETIC=[
 ('quotation_submission','参加竞价的药品企业按要求报价并提交承诺书。',{'Ec':1}),
 ('fund_ability_constraint','以医保基金支付能力为约束确定药品目录调整范围。',{'Ec':1}),
 ('fund_ability_header_only','药品申报表中的基金支付能力栏目名称应采用规定字体。',{'Ec':0}),
 ('fund_statistics','医保部门负责统计该药品基金实际支出，不包括企业行政费。',{'Ec':1}),
 ('price_reduction_content','应合理控制本药降价幅度。',{'Ec':1}),
 ('cost_metric_exclusion','该药不计入医保自费率指标。',{'Ec':1}),
 ('dose_safety_improvement','通过药物剂量模拟向老年患者提供更安全、有效的药物治疗方案。',{'S':1,'E':1}),
 ('risk_detection_medication','提供清晰用药指导，及时记录患者服药后不适，以提升风险发现和干预的及时性。',{'S':1}),
 ('non_drug_operational_risk','提供清晰数据上传指导，记录工作人员操作不适，以提升办公风险发现的及时性。',{'S':0}),
 ('measurement_no_content','该药品项目的测算评估会议应安排会议室。',{'Ec':0}),
]

def run():
 out=[]
 for n,expected in ACTUAL:
  path=ROOT/'outputs/ai-audit800-20261010/source-A/coder-A/materials'/f'A-{n:06}.json';raw=path.read_bytes();bundle=json.loads(raw);u=semantic_unit(bundle);v=RelationView(u);d=judge(v);validate_decisions(u,d);a={k:d[k]['value'] for k in expected}
  out.append({'name':f'actual_dependency_{n}','expected_fixed_before_execution':expected,'actual':a,'passed':a==expected,'source_current':bundle['source_record']['text'],'source_contexts':bundle['source_record']['contexts'],'material_sha256':hashlib.sha256(raw).hexdigest(),'material_path':str(path),'decisions':d,'relations':v.traces()})
 for name,text,expected in SYNTHETIC:
  u=unit(text);v=RelationView(u);d=judge(v);validate_decisions(u,d);a={k:d[k]['value'] for k in expected};out.append({'name':name,'synthetic_input':u,'expected_fixed_before_execution':expected,'actual':a,'passed':a==expected,'decisions':d,'relations':v.traces()})
 with (P/sys.argv[1]).open('x') as f:json.dump({'test_N':len(out),'failed_N':sum(not x['passed'] for x in out),'tests':out,'non_human_not_gold':True,'not_full800_replay':True},f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({'test_N':len(out),'failed':[(x['name'],x['actual']) for x in out if not x['passed']]},ensure_ascii=False))
if __name__=='__main__':run()
