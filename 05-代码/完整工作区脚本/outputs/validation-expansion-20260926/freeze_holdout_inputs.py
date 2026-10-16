"""Create immutable study snapshots after an explicit candidate-readiness record."""
import argparse, hashlib, json, shutil
from pathlib import Path
from datetime import datetime
from sample_holdout import DEFAULT_CONTEXT_FIELDS, frame, allocate
from candidate_preflight import inspect

OUT=Path(__file__).parent
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);args=parser.parse_args()
    conf=load(args.config)
    assert conf['candidate_readiness_confirmed'] is True
    assert conf['protocol_version']=='CAL-5D-20260926-v1.3'
    paths={k:Path(v).resolve() for k,v in conf['paths'].items()}
    required={'corpus','adapter','classification','exposure','protocol','dictionary','dictionary_predictions','sampler','survey_metrics','llm_prompt','holdout_results','registered_development','supplementary_exposure_manifest','exposure_audit_base','sampling_plan','training_audit','producer_readiness'}
    assert required<=set(paths)
    before={k:sha(p) for k,p in paths.items()}
    qa=inspect({k:paths[k] for k in ('corpus','adapter','classification','dictionary','dictionary_predictions','protocol')})
    exposure=load(paths['exposure']);base=load(paths['exposure_audit_base'])
    assert exposure['inputs']['corpus_sha256']==before['corpus']
    assert exposure['inputs']['adapter_sha256']==before['adapter']
    assert exposure['inputs']['prior_audit_sha256']==before['exposure_audit_base']
    assert exposure['inputs']['supplement_manifest_sha256']==before['supplementary_exposure_manifest']
    assert base['inputs'][str(paths['registered_development'])]==before['registered_development']
    assert all(x['manifest_hash_matches'] and sha(Path(x['path']))==x['sha256'] for x in exposure['inputs']['files'])
    corpus=[json.loads(s) for s in paths['corpus'].read_text().splitlines()]
    units,pools,meta=frame(corpus,load(paths['adapter']),load(paths['classification']),exposure)
    assert exposure['analysis_units']==len(units)
    assert set(exposure['provisional_eligible_ids'])|set(exposure['exclusions'])==set(units)
    assert not set(exposure['provisional_eligible_ids'])&set(exposure['exclusions'])
    d60=load(OUT/'开发60-研究者映射.json')['rows']
    assert all(r['review_id'] in exposure['exclusions'] for r in d60)
    counts={h:len(v) for h,v in pools.items()};allocation=allocate(counts,600)
    assert sum(allocation.values())==min(600,len(meta))
    training=load(paths['training_audit'])
    assert training['same_five_dimension_judgements']==15 and len(training['independent_post_training_acknowledgements'])==2
    dest=OUT/'frozen-inputs';manifest=OUT/'最终冻结清单.json';partial=OUT/'.frozen-inputs.partial'
    if any(p.exists() for p in (dest,manifest,partial)):raise RuntimeError('Preserve existing freeze or quarantine attempt')
    partial.mkdir()
    entries={}
    for name,p in paths.items():
        target=partial/f'{name}--{p.name}'
        shutil.copyfile(p,target)
        assert sha(target)==before[name]
        entries[name]={'path':str(dest/target.name),'sha256':before[name],'original_path':str(p)}
    assert before=={k:sha(p) for k,p in paths.items()}
    result={'status':'frozen_for_reference_label_holdout','created_at':datetime.now().astimezone().isoformat(),
            'protocol_version':conf['protocol_version'],'files':entries,'context_fields':DEFAULT_CONTEXT_FIELDS,
            'candidate_readiness_basis':conf['candidate_readiness_basis'],'preflight':qa,
            'N_star':len(meta),'analysis_units':len(units),'excluded_known_development':len(exposure['exclusions']),
            'n':sum(allocation.values()),'sampling_seed':2026092602,'bootstrap_seed':2026092603,
            'human_coders':False,'external_llm_rerun':False,
            'AI_context_history':training['roles'],
            'comparison':'A_vs_C and dictionary_vs_each_AI separately; no automatic human gold standard',
            'scope':'Frozen finite U*; reference-label holdout, not certified unseen text',
            'label_blindness':'Neither coder receives the other coder or dictionary answers; source identity may be evident from policy text',
            'postfreeze_policy':'Do not use H600 labels to alter this frozen implementation or select a more favorable version'}
    partial.rename(dest)
    # Exclusive creation prevents replacing an issued freeze manifest.
    with manifest.open('x') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps({k:result[k] for k in ('status','protocol_version','N_star','excluded_known_development','n')},ensure_ascii=False))
if __name__=='__main__':main()
