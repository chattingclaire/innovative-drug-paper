from pathlib import Path
import json,hashlib
OUT=Path(__file__).parent.resolve()
BASE=Path('/Users/rainbow/Desktop/战略院/创新药论文-完整归档-20260914/12-投稿定稿工作区')
proof=BASE/'独立验证候选-v23-输入QA.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(proof)=='59aa1f94ca02549dd12ba4e52a7122c76af929d255aed41bf0e60ebc869c76f3'
qa=json.loads(proof.read_text());assert qa['status']=='candidate_ready_for_independent_validation_not_publication'
for f in qa['artifacts'].values():assert sha(Path(f['path']))==f['sha256']
mapping={'corpus':'corpus','adapter':'adapter_snapshot','dictionary':'code','dictionary_predictions':'predictions','protocol':'protocol','registered_development':'registered_development_units'}
paths={k:qa['artifacts'][v]['path'] for k,v in mapping.items()}
local={'exposure':'开发暴露映射-补充v4.json','exposure_audit_base':'开发暴露映射-当前语料-v4.json',
       'sampler':'sample_holdout.py','survey_metrics':'survey_metrics.py','holdout_results':'holdout_results.py',
       'llm_prompt':'统一口径-v1.3/LLM系统提示词-统一口径.txt','sampling_plan':'扩样验证执行方案-预先固定v1.md',
       'training_audit':'formal-preparation/共同培训核验.json','training_feedback':'formal-preparation/共同培训反馈-v1.3.md',
       'review_instructions':'H600-评审任务说明.md','R200_plan':'R200-预定挑战集规则.md',
       'freeze_builder':'freeze_holdout_inputs.py','candidate_preflight':'candidate_preflight.py',
       'exposure_auditor':'prepare_expansion.py','exposure_supplementer':'supplement_exposure.py'}
paths.update({k:str(OUT/v) for k,v in local.items()})
upstream={'classification':'部门归属与年度系列-冻结v1.json','source_metadata':'55条部门与系列映射-核验中.json',
          'supplementary_exposure_manifest':'开发暴露文件补充清单.json','source_context_manifest':'上下文补充候选-20260926/同类结构上下文补充-v2.json',
          'statistics_adapter_code':'policy_statistics_adapter.py','statistics_code':'policy_statistics.py',
          'regression_code':'test_policy_coding_v4_development.py','producer_readiness':'独立验证候选-v23-输入QA.json'}
paths.update({k:str(BASE/v) for k,v in upstream.items()})
config={'candidate_readiness_confirmed':True,'protocol_version':'CAL-5D-20260926-v1.3',
        'candidate_readiness_basis':{'path':str(proof),'sha256':sha(proof),'producer_confirmation':'另一任务明确同意封存v23并启动600，承诺不根据正式参考标签调参。'},'paths':paths}
with (OUT/'冻结配置-v23.json').open('x') as f:json.dump(config,f,ensure_ascii=False,indent=2)
print(json.dumps({'paths':len(paths),'code_version':'v4-development-23','candidate_confirmed':True},ensure_ascii=False))
