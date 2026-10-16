"""Separate current rule–LLM agreement from A/C reference agreement."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
OLD=ROOT.parent/'autocode-v25-20260927'
PREV=ROOT.parent/'coding-v26-20260930'
sys.path.insert(0,str(OLD))
from comparison_statistics import agreement
from analyze_current_reruns import normalize_rule_record

DIMS=('S','E','Ec','I','F')


def read(path,field=None):
    rows=[json.loads(s) for s in path.read_text().splitlines()]
    output={r['id']:r[field] if field else r for r in rows}
    assert len(output)==len(rows)==4924
    return output


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def report(rule,llm,ids):
    values={}
    for d in (*DIMS,'pooled'):
        ds=DIMS if d=='pooled' else (d,)
        pairs=[(rule[i]['labels'][dim],llm[i]['labels'][dim],1) for i in ids for dim in ds]
        metric=agreement(pairs)
        values[d]={'common_n':int(metric['joint_determinate_n_or_weight']),
                   'rule_pending':int(metric['prediction_pending_n_or_weight']),
                   'llm_pending':int(metric['reference_pending_n_or_weight']),
                   'kappa':metric['binary_agreement']['kappa'],
                   'confusion':metric['confusion_on_joint_determinate'],
                   'rule_positive_rate':metric['binary_agreement']['first_positive_rate_joint_determinate'],
                   'llm_positive_rate':metric['binary_agreement']['second_positive_rate_joint_determinate']}
    return values


def main():
    manifest=json.loads((ROOT/'release_manifest.json').read_text())
    for path,digest in manifest['output_bindings'].items():assert sha(ROOT/path)==digest
    previous=PREV/'title_scope_verification/all_predictions.jsonl'
    check=json.loads((PREV/'title_scope_verification/verification.json').read_text())
    assert sha(previous)==check['output_sha256']
    llmpath=OLD/'llm_runs/gpt56-sol-v13-native-1/all_predictions.jsonl'
    seal=json.loads((llmpath.parent/'prediction_seal.json').read_text())
    assert sha(llmpath)==seal['predictions_sha256']
    old={i:normalize_rule_record(v) for i,v in read(previous,'prediction').items()}
    new=read(ROOT/'all_predictions.jsonl','prediction')
    llm=read(llmpath)
    allids=sorted(new)
    result={'provenance':{'v26_rule_sha256':sha(previous),'v27_rule_sha256':sha(ROOT/'all_predictions.jsonl'),
                          'llm_sha256':sha(llmpath)},
            'paired_4924':{'v26_rule_vs_current_llm':report(old,llm,allids),
                           'v27_rule_vs_current_llm':report(new,llm,allids)},
            'interpretation':'Method-to-method agreement, not validity or agreement with AI A/C references. LLM was not rerun.'}
    (ROOT/'current_method_agreement.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    for name,data in result['paired_4924'].items():
        print(name,{d:(round(v['kappa'],3) if v['kappa'] is not None else None,v['common_n']) for d,v in data.items()})


if __name__=='__main__':main()
