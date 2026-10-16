"""Full source-only candidate execution; no confirmation/reference answers."""
from collections import Counter
import argparse
import hashlib
import json
import logging
from pathlib import Path
import sys
import datetime

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
sys.path.insert(0,str(HERE/'runtime'))
import policy_coding_v27 as core


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
 parser=argparse.ArgumentParser();parser.add_argument('--material-version',choices=['v12','v13','v14'],default='v12');parser.add_argument('--output-name');args=parser.parse_args()
 logging.getLogger('pypdf').setLevel(logging.ERROR)
 inp=BASE/f'rule_inputs_shared_{args.material_version}.jsonl';dest=HERE/(args.output_name or f'candidate_predictions_{args.material_version}.jsonl')
 assert not dest.exists(),'candidate execution does not overwrite a prior run'
 before=sha(inp);runtime={str(p.resolve()):sha(p) for p in (HERE/'runtime').glob('*.py')}
 rows=[json.loads(x) for x in inp.read_text().splitlines()]
 assert len(rows)==4924 and len({r['id'] for r in rows})==4924
 started=datetime.datetime.now().astimezone().isoformat()
 outputs=[];status=Counter();new_rules=Counter();pending=[]
 for r in rows:
  result=core.code_unit(r['input']);original=r['input']['unit_text']
  assert result['unit_text_sha256']==hashlib.sha256(original.encode()).hexdigest()
  for e in result['evidence']:
   assert original[e['start']:e['end']]==e['text']
   if e['rule'].startswith('V34_'):new_rules[e['dimension']]+=1
  status[result['judgement_status']]+=1
  if result['judgement_status']=='undetermined':pending.append({'id':r['id'],'text':original,'reason':result.get('issue_reason')})
  outputs.append({'id':r['id'],'original_id':r['original_id'],'prediction':result})
 assert sha(inp)==before and all(sha(p)==h for p,h in runtime.items())
 dest.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in outputs))
 report={'version':core.VERSION,'status':'exposed_r3_development_diagnostic_only_not_new_independent_confirmation',
         'n':len(rows),'material_version':args.material_version,'input_path':str(inp.resolve()),'input_sha256':before,
         'runner_sha256':sha(__file__),
         'prediction_path':str(dest.resolve()),'prediction_sha256':sha(dest),
         'runtime_code_sha256':runtime,'reference_labels_loaded':False,
         'judgement_status_counts':dict(status),'new_cited_evidence_counts':dict(new_rules),
         'pending':pending,'started_at':started,'completed_at':datetime.datetime.now().astimezone().isoformat()}
 dest.with_suffix('.run.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({k:v for k,v in report.items() if k in ('version','status','n','judgement_status_counts','new_cited_evidence_counts')},ensure_ascii=False))


if __name__=='__main__':main()
