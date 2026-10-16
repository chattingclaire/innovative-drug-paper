"""Drop only validator-identified nonliteral evidence; never change labels/reasons."""
import argparse,json,subprocess,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];VAL=ROOT/'outputs/llm-v29-method-audit-20261005/validate_binary_output.py'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--batch',type=int,required=True);ap.add_argument('--targets',nargs='+',required=True,help='ID:index');ap.add_argument('--dedupe-issues',action='store_true');a=ap.parse_args();batch=HERE/'production-25-v29/batches'/f'batch-{a.batch:04d}';source=batch/'raw_output.json';data=json.loads(source.read_text());before={r['id']:r['labels'] for r in data['rows']};removed=[]
 for spec in a.targets:
  rid,index=spec.rsplit(':',1);row=next(r for r in data['rows'] if r['id']==rid);item=row['evidence'].pop(int(index));removed.append({'id':rid,'index':int(index),'removed':item})
 assert before=={r['id']:r['labels'] for r in data['rows']}
 if a.dedupe_issues:
  seen=set();kept=[]
  for issue in data['issue_records']:
   if issue['id'] in seen:removed.append({'duplicate_issue_removed':issue});continue
   seen.add(issue['id']);kept.append(issue)
  data['issue_records']=kept
 out=batch/'repaired_output.json';out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');check=subprocess.run(['python3',str(VAL),str(batch/'input.json'),str(out)],capture_output=True,text=True);(batch/'repaired_validation.json').write_text(check.stdout)
 if check.returncode:raise SystemExit(check.stdout)
 (batch/'repair_manifest.json').write_text(json.dumps({'status':'accepted_after_mechanical_nonliteral_evidence_removal','original_raw_preserved':True,'labels_and_reasons_unchanged':True,'removed':removed,'repaired_output_sha256':sha(out)},ensure_ascii=False,indent=2)+'\n');print(check.stdout.strip())
if __name__=='__main__':main()
