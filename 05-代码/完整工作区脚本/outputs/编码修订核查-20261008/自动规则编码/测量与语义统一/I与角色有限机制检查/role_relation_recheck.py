"""One authorized narrow recheck after the preserved cross-sentence failure."""
import hashlib,json,sys
from pathlib import Path
p=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(p/'runtime'))
from current_unit_role import classify,permits_content_expansion
cases=[
 ('first_failed_mixed_unit','应评价药品安全性。这些特征包括以下几个方面:','ordinary_or_mixed_substantive_unit',False),
 ('same_sentence_substantive_lead','药品上市许可申请时，以下符合条件的药品；可以申请适用优先审评审批程序:','substantive_list_lead',True),
 ('cross_sentence_without_anaphoric_requirement','应提供创新性评价证据。上述特征包括以下几个方面:','ordinary_or_mixed_substantive_unit',False),
]
results=[]
for name,text,role,permission in cases:
 actual=classify(text)
 results.append(dict(name=name,text=text,actual=actual,expected_role=role,expected_expansion_gate=permission,
  mechanism_pass=(actual['role']==role and permits_content_expansion(text)==permission)))
result=dict(scope='three role-function grammar controls only, no source rerun or whole coding entrance; first failure retained',
 code_sha256=hashlib.sha256((p/'runtime/current_unit_role.py').read_bytes()).hexdigest(),results=results)
Path(__file__).with_name('role_relation_recheck.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
for r in results:print(json.dumps(r,ensure_ascii=False))
