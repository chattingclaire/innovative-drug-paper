"""Actual source-only v13 authentication and bounded list-source controls."""
import copy
import json
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'runtime'))
import policy_coding_v27 as core
import source_context_adapter_v34 as adapter
from context_validation import validate_added_parents


def rejected(record):
 try:adapter.prepare(record)
 except ValueError:return True
 return False


def main():
 path=HERE.parents[1]/'rule_inputs_shared_v13.jsonl'
 records=[json.loads(x)['input'] for x in path.read_text().splitlines()
          if json.loads(x)['input'].get('source_local_list_family_v13')]
 assert len(records)==3
 outputs=[]
 for r in records:
  adapted=adapter.prepare(r);group=next(g for g in adapted['typed_contexts_v34'] if g['field']=='source_local_list_family_v13')
  result=core.code_unit(r)
  late=[e for e in result['evidence'] if e['rule']=='V34_S_authenticated_local_evidence_source_list']
  assert bool(late)==group['target_is_list_child']
  assert result['labels']=={'S':1,'E':0,'Ec':0,'I':0,'F':0}
  for e in late:
   assert r['unit_text'][e['start']:e['end']]==e['text']
   for anchor in e['cited_substantive_anchors']:
    assert group['parent_predicate']['text'][anchor['start']:anchor['end']]==anchor['text']
  outputs.append({'text':r['unit_text'],'target_is_list_child':group['target_is_list_child'],
                  'labels':result['labels'],'new_evidence':late})
 bad=copy.deepcopy(records[-1]);bad.pop('source_local_list_family_v13');bad['llm_v29_shared_context'].pop('source_local_list_family_v13')
 assert rejected(bad),'a new version must not bypass validation when its family is absent'
 bad=copy.deepcopy(records[-1]);p=next(p for p in bad['verified_parent_context'] if p.get('repair_version','').startswith('v13'))
 p['text']='当前研究涉及创新属性。';p['text_sha256']=adapter.digest(p['text'])
 bad['llm_v29_shared_context']['verified_parent_context']=copy.deepcopy(bad['verified_parent_context'])
 assert rejected(bad),'target-bound but wrong actual parent must be rejected'
 generic=copy.deepcopy(records[-1]);generic.pop('source_local_list_family_v13');generic['llm_v29_shared_context'].pop('source_local_list_family_v13')
 for p in generic['verified_parent_context']:
  if p.get('repair_version','').startswith('v13'):p['repair_version']='future-source-bound-parent-format'
 generic['llm_v29_shared_context']['verified_parent_context']=copy.deepcopy(generic['verified_parent_context'])
 validate_added_parents(generic)
 bad=copy.deepcopy(generic);p=next(p for p in bad['verified_parent_context'] if p.get('repair_version')=='future-source-bound-parent-format');p['text']='伪造父谓词';p['text_sha256']=adapter.digest(p['text'])
 try:validate_added_parents(bad)
 except ValueError:pass
 else:raise AssertionError('an unknown version must not bypass source authentication')
 report={'scope':'actual source-only v13 plus certificate mutation controls; no new reference labels',
         'controls':7,'all_passed':True,'source_rows':outputs}
 (HERE/'v13_local_family_controls_results.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'controls':7,'all_passed':True}))


if __name__=='__main__':main()
