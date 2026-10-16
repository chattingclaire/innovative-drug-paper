"""Potential candidate14 implementation impact envelope, not classifications.

Only source text/neutral fields enter. This function shares runtime dispatch
triggers. It never reads previous predictions, labels, departments or metrics.
No full corpus coding is performed by this script.
"""
import argparse,hashlib,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H/'runtime'))
import common_innovation_relations14 as I
import common_medicine_access14 as F

def scope(record):
    reasons={'I':I.trigger_reasons(record),'F':F.trigger_reasons(record)}
    return dict(potential_new_relation_or_retired_relation=any(reasons.values()),
        reasons=reasons,current_text_sha256=hashlib.sha256(record.get('unit_text','').encode()).hexdigest(),
        classification_performed=False,source_authentication_performed=False,
        old_labels_metrics_identity_used=False,
        scope_kind='content-only trigger envelope; actual source and object binding may still reject or pend')

def main():
    p=argparse.ArgumentParser();p.add_argument('--input',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();out=[]
    for line in Path(args.input).open():
        row=json.loads(line);r=scope(row.get('input',row))
        if r['potential_new_relation_or_retired_relation']:
            r['id']=row.get('id') or row.get('unit_id');out.append(r)
    Path(args.output).write_text(json.dumps(dict(input_path=str(Path(args.input).resolve()),
        input_sha256=hashlib.sha256(Path(args.input).read_bytes()).hexdigest(),
        rows=out,classification_count=0,manual_sha256=I.MANUAL_SHA256),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
