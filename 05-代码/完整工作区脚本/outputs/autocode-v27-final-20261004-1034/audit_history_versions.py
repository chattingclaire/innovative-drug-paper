"""Disentangle the reproducible 0.867 and 0.654 figures on identical old IDs.

This reads frozen historical outputs; it does not change labels or rules.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parent
ARCHIVE=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/03-编码数据与脚本')
sys.path.insert(0,str(ROOT.parent/'autocode-v25-20260927'))
from comparison_statistics import agreement

DIMS=('安全性','有效性','经济性','创新性','公平性')


def read(name):
    return {r['id']:r for r in json.loads((ARCHIVE/name).read_text())}


def metric(left,right,ids):
    result={}
    for dim in (*DIMS,'pooled'):
        choices=DIMS if dim=='pooled' else (dim,)
        result[dim]=agreement([(int(d in left[i]),int(d in right[i]),1)
                               for i in ids for d in choices])
    return result


def k(report):
    return {d:round(report[d]['binary_agreement']['kappa'],6) for d in report}


def main():
    source=ARCHIVE/'词典编码脚本-policy_coding_v2.py'
    script=source.read_text()
    namespace={}
    exec(script[script.index('DIMENSIONS = {'):script.index('DIM_PATTERNS = {}')],namespace)
    pattern={d:[re.compile(x) for x in namespace['DIMENSIONS'][d]] for d in DIMS}
    texts=read('all_sentences.json')
    v2dict={i:{d for d in DIMS if any(p.search(r['sent']) for p in pattern[d])} for i,r in texts.items()}
    v2llm={i:set(r['dims']) for i,r in read('llm_all_results.json').items()}
    v3dictrows=read('coding_v3_dict.json')
    v3dict={i:set(r['dims_v3']) for i,r in v3dictrows.items()}
    v3llm={i:set(r['dims']) for i,r in read('coding_v3_llm.json').items()}
    assert len(texts)==len(v2dict)==len(v2llm)==len(v3dict)==3387
    assert len(v3llm)==2965 and set(v3llm)<=set(texts)
    assert all(texts[i]['sent']==v3dictrows[i]['sent'] for i in texts)
    ids=sorted(v3llm)
    reports={
        'v2_dictionary_vs_v2_llm_all3387':metric(v2dict,v2llm,sorted(texts)),
        'v2_dictionary_vs_v2_llm_matched2965':metric(v2dict,v2llm,ids),
        'v3_dictionary_vs_v2_llm_matched2965':metric(v3dict,v2llm,ids),
        'v2_dictionary_vs_v3_llm_matched2965':metric(v2dict,v3llm,ids),
        'v3_dictionary_vs_v3_llm_matched2965':metric(v3dict,v3llm,ids),
    }
    output={'inputs':{name:hashlib.sha256((ARCHIVE/name).read_bytes()).hexdigest()
                      for name in ('all_sentences.json','llm_all_results.json',
                                   'coding_v3_dict.json','coding_v3_llm.json',
                                   '词典编码脚本-policy_coding_v2.py')},
            'same_text_for_all_3387':True,
            'matched_ids_2965':len(ids),'v3_llm_missing_from_full_frame':len(texts)-len(ids),
            'within_matched_ids_changed_label_sets':{
                'dictionary_v2_to_v3':sum(v2dict[i]!=v3dict[i] for i in ids),
                'llm_v2_to_v3':sum(v2llm[i]!=v3llm[i] for i in ids)},
            'kappa':{name:k(report) for name,report in reports.items()},
            'confusion':{name:{d:report[d]['confusion_on_joint_determinate'] for d in DIMS}
                         for name,report in reports.items()},
            'interpretation':'Matched-ID counterfactuals isolate version changes descriptively; no method is a truth label.'}
    (ROOT/'history_version_audit.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in output.items() if k in ('matched_ids_2965','v3_llm_missing_from_full_frame','within_matched_ids_changed_label_sets','kappa')},ensure_ascii=False,indent=2))


if __name__=='__main__':main()
