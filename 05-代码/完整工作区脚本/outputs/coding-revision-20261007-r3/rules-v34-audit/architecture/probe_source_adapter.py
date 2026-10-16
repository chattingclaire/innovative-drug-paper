"""Source authentication only: never invokes the five-dimension classifier."""
from collections import Counter
import hashlib
import json
import logging
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
BASE=HERE.parents[1]
sys.path.insert(0,str(HERE/'runtime'))
import source_context_adapter_v34 as adapter


def main():
    logging.getLogger('pypdf').setLevel(logging.ERROR)
    path=BASE/'rule_inputs_shared_v12.jsonl'
    rows=[json.loads(x)['input'] for x in path.read_text().splitlines()]
    fields=('complete_following_list_v11','explicitly_cited_articles_v10','explicitly_cited_qualifications_v12')
    counts=Counter();methods=Counter();failures=[];selected=0
    for r in rows:
        shared=r.get('llm_v29_shared_context',{})
        if not any(k in r or k in shared for k in fields) and not shared.get('structured_following_units'):
            continue
        selected+=1
        try:
            result=adapter.prepare(r)
            counts.update(x['field'] for x in result.get('source_field_consumption_v34',[]))
            for group in result.get('typed_contexts_v34',[]):
                methods.update(c.get('authentication_v34',{}).get('method','preview_not_authenticated')
                               for c in group.get('contexts',[]))
        except Exception as e:
            failures.append({'current_unit_text':r['unit_text'],'error':str(e)})
    freeze=json.loads((BASE/'rules-v33/candidate_freeze.json').read_text())
    unchanged=all(hashlib.sha256(Path(p).read_bytes()).hexdigest()==h
                  for p,h in freeze['production_code_sha256'].items())
    report={'scope':'source-only field authentication; no labels/reference/predictions accessed',
            'input_path':str(path),'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'selected_n':selected,'authenticated_or_preview_counts':dict(counts),
            'context_authentication_method_counts':dict(methods),'rejected_n':len(failures),
            'rejection_error_counts':dict(Counter(x['error'] for x in failures)),
            'rejections':failures,'frozen_v33_production_sha256_unchanged':unchanged,
            'candidate_not_released':True,'strict_new_confirmation_claim_allowed':False}
    (HERE/'source_adapter_authentication_probe.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('rejections','input_path')},ensure_ascii=False))


if __name__=='__main__':main()
