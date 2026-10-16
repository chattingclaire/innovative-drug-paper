"""Build identical-version inputs for both current coding methods.

Current A/C means the 1268 first AI submissions under v1.3, never the old
author labels. Future residual-frame text is processed but not printed.
"""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'validation-expansion-20260926'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def safe_context(value):
    if isinstance(value,list):return [safe_context(v) for v in value]
    if isinstance(value,dict):
        return {k:safe_context(v) for k,v in value.items()
                if not (isinstance(v,str) and v.startswith('/Users/'))}
    return value

def main():
    freeze=json.loads((OLD/'V600-最终冻结清单.json').read_text())
    corpus_path=Path(freeze['files']['corpus']['path'])
    assert digest(corpus_path)==freeze['files']['corpus']['sha256']
    archive_path=OLD/'D668-原4924范围主统计.json'
    assert digest(archive_path)=='9646246c2ed5b3d15e529797a144c3c7c972f3c683f8dc87873328a41222857b'
    archive=json.loads(archive_path.read_text())['archive']
    corpus=[json.loads(s) for s in corpus_path.read_text().splitlines()]
    units=[r for r in corpus if r['count_as_analysis_unit'] is True]
    assert len(units)==4924
    assert len({r['review_id'] for r in units})==4924
    units.sort(key=lambda r:r['review_id'])
    metadata={r['review_id']:r for stage in ['R','D']
              for r in archive[stage+'_mapping_original']['rows']}
    reference_map={}
    for stage, submissions in archive['raw_coder_submissions'].items():
        by_blind={r['id']:r['review_id'] for r in archive[stage+'_mapping_original']['rows']}
        for packet in submissions.values():
            for row in packet['rows']:
                key=by_blind[row['id']]
                reference_map.setdefault(key,{})[packet['coder']]=row
    assert len(reference_map)==1268
    assert all(set(v)=={'A','C'} for v in reference_map.values())
    normalized={r['unit_id']:r['labels'] for r in archive['normalized_analysis_payload']['units']}
    for key,refs in reference_map.items():
        for c,r in refs.items():
            assert {d:str(v) if type(v)is int else 'pending' for d,v in r['labels'].items()}==normalized[key][c]
    records=[];llm=[];refs=[]
    for index,unit in enumerate(units,1):
        rid=f'RECODE25-{index:05d}'
        key=unit['review_id']
        payload={'id':rid,'text':unit['unit_text'],'source_title':unit['original_file_stem'],
                 'pages':unit.get('pages',[]),
                 'input_assessment':unit.get('input_assessment',{'status':'not_assessed'}),
                 'contexts':safe_context({k:unit[k] for k in freeze['context_fields'] if k in unit}),
                 'context_usage':'只判定text的实质内容；用语境消解对象/指代/条件，不能复制段落所有标签。'}
        records.append({'id':rid,'original_id':key,'input':unit})
        llm.append(payload)
        if key in reference_map:
            ref=reference_map[key];meta=metadata[key]
            assert hashlib.sha256(unit['unit_text'].encode()).hexdigest()==meta['unit_text_sha256']
            refs.append({'id':rid,'original_id':key,'current_reference_id':meta['id'],
                         'original_references':ref,'historical_sampling':{
                             'stratum':('R|' if meta['id'].startswith('V600') else 'D|')+meta['stratum'],
                             'N_h':meta['N_h'],'n_h':meta['n_h']}})
    outputs={}
    for name,data in [('current_rule_inputs.jsonl',records),('current_llm_inputs.jsonl',llm),('current_1268_references.jsonl',refs)]:
        p=HERE/name;p.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in data));outputs[name]=digest(p)
    manifest={'purpose':'rerun_both_methods_under_current_protocol_not_old_author_comparison',
        'analysis_units':len(records),'current_first_AI_reference_units':len(refs),
        'context_only_excluded':len(corpus)-len(units),'protocol_version':'CAL-5D-20260926-v1.3',
        'full_text_and_context_not_truncated':True,'current_reference_labels_modified':False,
        'old_author_labels_used':False,'source_hashes':{str(corpus_path):digest(corpus_path),str(archive_path):digest(archive_path)},
        'output_hashes':outputs,'comparison_limit':'Existing current A/C are developmental reference for tuned v25; new residual-frame validation reported separately.'}
    (HERE/'current_input_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:manifest[k] for k in ['analysis_units','current_first_AI_reference_units','context_only_excluded','old_author_labels_used']},ensure_ascii=False))

if __name__=='__main__':main()
