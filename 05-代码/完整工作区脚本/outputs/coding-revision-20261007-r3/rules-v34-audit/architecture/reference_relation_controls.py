"""Independent current/source-anchor controls, not held-out validation."""
import copy
import json
from pathlib import Path
import sys
from reproduce_architecture import fixture,sha,payload

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'))
import policy_coding_v27 as core


CASES=[
 ('generic_evaluation','应按照第二条评价药品价值。','第二条 药品须安全有效、价格合理。',{'S','E','Ec'}),
 ('specific_effect','应按照第二条评价该药物疗效。','第二条 药品须安全有效、价格合理。',{'E'}),
 ('administrative','符合第二条申报条件的药品，应通过平台提交申请。','第二条 药品须安全有效、价格合理。',set()),
 ('navigation','药品相关说明请参见第二条。','第二条 药品须安全有效、价格合理。',set()),
 ('assessment_scope','符合第二条的药品可以纳入目录评审范围。','第二条 疗效不确切的药品应调出药品目录。',set()),
 ('actual_exit_standard','符合第二条退出条件的药品应予以调出药品目录。','第二条 药品发生严重不良反应、疗效不确切或药品价格不合理的，应调出药品目录。',{'S','E','Ec','F'}),
 ('negated_evidence','应按照第二条评价药物价值。','第二条 该药物尚未证明有效性，未发现不良反应。',{'S','E'}),
 ('non_drug_content','应按照第二条评价药物价值。','第二条 验证数据有效性和基金安全性。',set()),
 ('carrier_only','应按照第二条评价药物价值。','第二条 仅公开药物疗效报告和安全性资料。',set()),
 ('independent_effect_survives','应按照第二条评价药物价值。','第二条 验证数据有效性并评价药物疗效。',{'E'}),
 ('data_right_only','按照第二条执行，对该药物试验数据给予数据保护期。','第二条 专有试验数据保护的期限为六年，资料应证明药品安全有效。',{'I'}),
 ('payment_after_application','该药品可申请重新谈判并提交资料，按第二条确定新的支付标准。','第二条 药品支付标准应按照治疗费用与预算影响确定。',{'Ec'}),
]


def main():
 rows=[]
 for name,current,cited,expected in CASES:
  r,c=fixture('dual_anchor_'+name,current,[cited])
  refs=[{'reference_address':'第二条','selection':'complete_exact_cited_interval_only','contexts':[c['contexts'][1]],
         'structure_boundary':{'first_paragraph_id':'p1','last_paragraph_id':'p1',
                               'all_paragraphs_in_interval_included':True,
                               'next_candidate_paragraph_id':'p2','next_candidate_paragraph_text':'下一节：其他事务'}}]
  value={'repair_version':'v12-source-explicit-qualification-reference','current_unit_sha256':sha(current),
         'current_unit_id':r['unit_id'],'current_unit_source_path':r['unit_source'],
         'current_unit_source_sha256':r['unit_source_sha256'],'current_unit_candidate_path':r['candidate_file'],
         'current_unit_candidate_sha256':r['candidate_sha256'],'references':refs,'references_sha256':payload(refs)}
  r['llm_v29_shared_context']['explicitly_cited_qualifications_v12']=value
  result=core.code_unit(r)
  evidence=[e for e in result['evidence'] if e['rule'].startswith('V34_')]
  found={e['dimension'] for e in evidence}
  assert found==expected,(name,found,expected,result)
  for e in evidence:
   assert current[e['start']:e['end']]==e['text']
   assert e['current_relation_anchor']['text']==e['text']
   for anchor in e['cited_substantive_anchors']:
    assert cited[anchor['start']:anchor['end']]==anchor['text']
    assert anchor['source_sha256']==r['source_sha256']
  rows.append({'control':name,'current_unit':current,'cited_text':cited,
               'expected_cited_dimensions':sorted(expected),'actual_cited_dimensions':sorted(found),
               'evidence':evidence,'labels':result['labels']})
 report={'scope':'constructed dual-anchor development controls only','n':len(rows),'all_passed':True,'controls':rows}
 (HERE/'reference_relation_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'controls':len(rows),'all_passed':True}))


if __name__=='__main__':main()
