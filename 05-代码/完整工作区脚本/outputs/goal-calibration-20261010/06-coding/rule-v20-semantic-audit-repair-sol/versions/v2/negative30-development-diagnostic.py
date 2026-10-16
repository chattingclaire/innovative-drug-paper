"""Already exposed negative-source diagnostics; unresolved cases are unscored."""
import sys,json,datetime
from pathlib import Path
sys.dont_write_bytecode=True
import regression_tests as helpers
HERE=Path(__file__).resolve().parent
AUDIT=HERE.parents[3]/'08-audits/ai800-disagreement-semantic-root/common-negative30-root/reviews.json'
def run(dest):
 out=Path(dest);out.mkdir(exist_ok=False);modules=helpers.modules();reviews=json.loads(AUDIT.read_text());records={};items=[]
 for audit in reviews:
  sid=audit['source_id'];dim=audit['dimension']
  if sid not in records:
   path=Path(audit['material_path']);bundle=json.loads(path.read_text());unit=modules['source_packet'].semantic_unit(bundle)
   view=modules['relations'].RelationView(unit);decisions=modules['dimensions'].judge(view);modules['evidence'].validate_decisions(unit,decisions)
   records[sid]=(unit,view,decisions,helpers.bind(path))
  unit,view,decisions,binding=records[sid]
  items.append({'source_id':sid,'blind_id':audit['blind_id'],'dimension':dim,'current_text':unit['text'],'source_input':binding,
   'audit_review_value':audit['review_value'],'candidate_value':decisions[dim]['value'],
   'candidate_decision':decisions[dim],'audit_unresolved_not_scored':audit['review_value'] is None,
   'agreement_descriptive_only':None if audit['review_value'] is None else audit['review_value']==decisions[dim]['value'],
   'audit_question':audit.get('human_review_question',''),'source_relation_traces':view.traces()})
 summary={'identity':'nonhuman AI exposed-development diagnostic','no_independent_gold_or_formal_accuracy':True,
          'record_N':len(records),'dimension_N':len(items),'audit_resolved_N':sum(i['audit_review_value']is not None for i in items),
          'audit_unresolved_unscored_N':sum(i['audit_unresolved_not_scored']for i in items),
          'resolved_directional_disagreement_N':sum(i['agreement_descriptive_only']is False for i in items),
          'audit_input_binding':helpers.bind(AUDIT),'code_bindings':[helpers.bind(HERE/(n+'.py'))for n in helpers.NAMES],
          'created_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'whole77_or800_run':False}
 (out/'results.json').write_text(json.dumps(items,ensure_ascii=False,indent=2)+'\n');(out/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in summary.items()if k not in ['code_bindings','audit_input_binding']},ensure_ascii=False))
if __name__=='__main__':run(sys.argv[1])
