"""One finite source-authenticated I module check; no full coding entrance."""
import copy,hashlib,json,sys,traceback
from pathlib import Path
OUT=Path(__file__).resolve().parent;RT=OUT.parent/'runtime';sys.path.insert(0,str(RT))
import common_innovation_relations14 as rule
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda s:hashlib.sha256(s.encode()).hexdigest()
CURRENT='(三)对于已终止专门研发咨询程序的品种，自终止之日起，技术审评机构不再优先安排相关沟通交流。'
SCOPE='药物临床试验期间，创新药或者改良型新药等，申请人可以申请适用专门研发咨询程序。'
def fixture(name, *,scope=SCOPE,current=CURRENT,separate=False,hash_bad=False):
 directory=OUT/'fixtures'/name;directory.mkdir(parents=True,exist_ok=True)
 lines=['附件1','专门研发咨询程序（试行）','一、适用范围',scope]
 if separate:lines += ['附件2','专门研发咨询程序（试行）','二、工作要求']
 else:lines += ['二、工作要求']
 lines += [current,'附件3','另一工作程序（试行）','一、适用范围','其余正文。']
 source=directory/'literal_source.txt';source.write_text('\n'.join(lines)+'\n')
 srcsha=sha(source);paragraphs=[];units=[];bound_lines=[]
 for n,line in enumerate(lines,1):
  if line.startswith('附件') or line.endswith('（试行）'):continue
  pid='p'+str(n);lid='L'+str(n)
  paragraphs.append(dict(id=pid,text=line,line_ids=[lid],source_lines=[n],pages=[]))
  bound_lines.append(dict(id=lid,text=line,line=n))
  if line==current:units.append(dict(id='current',text=current,paragraph_id=pid,pages=[]))
 candidate=directory/'candidate.json';candidate.write_text(json.dumps(dict(source=str(source),source_sha256=srcsha,
  paragraphs=paragraphs,lines=bound_lines,unit_candidates=units),ensure_ascii=False,indent=2)+'\n')
 record=dict(unit_id='current',unit_text=current,unit_source=str(source),unit_source_sha256=srcsha,
  source=str(source),source_sha256=srcsha,candidate_file=str(candidate),candidate_sha256=sha(candidate))
 record['verified_innovation_scope_v27']=dict(text=scope,text_sha256=digest(scope),source_sha256=srcsha,
  original_unit_sha256=digest(current),locator=dict(paragraph_id='p4',source_lines=[4]),
  component_binding=dict(unit_id='current',candidate_sha256=record['candidate_sha256']),
  # This deliberately false metadata must not authorize or deny the relation.
  component='untrusted_metadata_not_a_rule_feature',verified=False)
 if hash_bad:record['verified_innovation_scope_v27']['source_sha256']='0'*64
 return record
inputs=[
 ('correct_same_programme_same_component',fixture('correct'),True,False),
 ('different_programme',fixture('different_programme',scope=SCOPE.replace('专门研发咨询程序','其他研发咨询程序')),False,False),
 ('different_attachment_same_named_programme',fixture('different_attachment',separate=True),False,False),
 ('programme_status_only',fixture('status_only',current='(三)该品种已终止专门研发咨询程序。'),False,False),
 ('invalid_scope_source_hash',fixture('invalid_scope_hash',hash_bad=True),False,True),
]
w=OUT.parents[2]
source_inputs=w/'LLM编码/统一判据编码准备/共用纯来源材料04/rule_inputs_material04.jsonl'
actual=next(json.loads(l) for l in source_inputs.open() if json.loads(l)['id']=='RECODE25-00046')
inputs.append(('actual_source_00046',actual['input'],True,False))
(OUT/'module_inputs6.jsonl').write_text(''.join(json.dumps(dict(name=name,input=r,expected_contract_support_mention=expected,
 expected_source_pending=pending),ensure_ascii=False)+'\n' for name,r,expected,pending in inputs))
results=[]
for name,record,expected,pending in inputs:
 item=dict(name=name,current_text=record['unit_text'],input_sha256=digest(json.dumps(record,ensure_ascii=False,sort_keys=True)))
 try:
  result=rule.revise(copy.deepcopy(record),dict(evidence=[],judgement_status='determined'))
  has=any(e['dimension']=='I' for e in result['evidence']);actual_pending=bool(result.get('common14_pending_dimensions',{}).get('I'))
  complete=(all(e['text']==record['unit_text'] for e in result['evidence']) if expected else True)
  item.update(execution_status='completed',module_result=result,has_I_module_evidence=has,source_pending=actual_pending,
   complete_current_proposition_preserved=complete,mechanism_pass=(has==expected and actual_pending==pending and complete))
 except Exception as error:
  item.update(execution_status='failed',error_type=type(error).__name__,error=str(error),traceback=traceback.format_exc(),mechanism_pass=False)
 results.append(item)
(OUT/'module_results.json').write_text(json.dumps(dict(scope='five authenticated synthetic contract fixtures plus one actual source; innovation module only, no whole code_unit, no model or reference labels; not validity validation',
 actual_source_input_path=str(source_inputs),actual_source_input_sha256=sha(source_inputs),module_sha256=sha(RT/'common_innovation_relations14.py'),manual_sha256=rule.MANUAL_SHA256,
 results=results),ensure_ascii=False,indent=2)+'\n')
for r in results:print(json.dumps({k:r[k] for k in ('name','execution_status','mechanism_pass','has_I_module_evidence','source_pending','complete_current_proposition_preserved','error') if k in r},ensure_ascii=False))
