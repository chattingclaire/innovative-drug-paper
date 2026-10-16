"""Final three-department attention ratios; never changes labels or design weights."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import sys, json, hashlib, argparse

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'outputs/attention-share-audit-20261007'))
import recalculate_attention_share as a
a.GROUPS=('NMPA','NHSA','NHC')
DIMS=a.DIMS
INPUT=ROOT/'outputs/autocode-v28-review-20261004-111306/rule_inputs_v27.jsonl'
RULE=INPUT.parent/'all_predictions.jsonl'
AC=ROOT/'outputs/autocode-v25-20260927/current_1268_references.jsonl'
META=ROOT/'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--rules',type=Path,default=RULE)
    parser.add_argument('--inputs',type=Path,default=INPUT)
    parser.add_argument('--rule-method',help='Required for a non-default rule prediction file')
    parser.add_argument('--rule-version',help='Exact actual prediction version')
    parser.add_argument('--llm',type=Path,help='Explicit actual completed full 4924-row LLM JSONL only')
    parser.add_argument('--llm-method',default='llm_gpt56_sol_v29')
    args=parser.parse_args()
    if args.rules.resolve()!=RULE.resolve() and (not args.rule_method or not args.rule_version):
        parser.error('Non-default --rules requires --rule-method and --rule-version')
    args.rule_method=args.rule_method or 'rules_v28_2'
    args.rule_version=args.rule_version or 'v28.2-five-dimension-discrepancy-audit-20261004'
    if args.rule_method=='rules_v28_2' and args.rule_version!='v28.2-five-dimension-discrepancy-audit-20261004':
        parser.error('A new rule version cannot be labelled rules_v28_2')
    if args.rule_method in ('A_AI_reference','C_AI_reference') or args.rule_method==args.llm_method:
        parser.error('Method keys must remain distinct')
    inp=a.jsonl(args.inputs);pred=a.jsonl(args.rules);refs=a.jsonl(AC)
    assert len(inp)==4924 and set(inp)==set(pred),'Rules require full ID closure'
    meta=json.loads(META.read_text())['rows']
    cls={Path(x['original_file']).stem:x for x in meta}
    llm_path=args.llm
    methods=[args.rule_method,'A_AI_reference','C_AI_reference']
    llm=None
    if llm_path is not None:
        llm=a.jsonl(llm_path)
        assert len(llm)==4924 and set(llm)==set(inp),'Final LLM requires full ID closure, never a partial merged result'
        methods.insert(1,args.llm_method)
    sources=[args.inputs,args.rules,AC,META,Path(__file__)] + ([llm_path] if llm is not None else [])
    source_hashes={str(p):a.sha(p) for p in sources}
    rows=[];background=[];strata=Counter()
    for rid,item in inp.items():
        prediction=pred[rid]['prediction']
        assert prediction['version']==args.rule_version,f'Rule version mismatch: {rid}'
        assert prediction['unit_text_sha256']==hashlib.sha256(item['input']['unit_text'].encode()).hexdigest()
        for record in ([prediction,llm[rid].get('prediction',llm[rid])] if llm is not None else [prediction]):
            assert set(record['labels'])==set(DIMS)
            assert all((type(v)is int and v in (0,1)) or v=='待定' for v in record['labels'].values())
        stem=item['input']['original_file_stem'];m=cls[stem]
        if m['analysis_group'] not in a.GROUPS:
            background.append(rid);continue
        rec={args.rule_method:prediction};weights={args.rule_method:Fraction(1)}
        if llm is not None:
            rec[args.llm_method]=llm[rid].get('prediction',llm[rid]);weights[args.llm_method]=Fraction(1)
        if rid in refs:
            sm=refs[rid]['historical_sampling'];strata[sm['stratum']]+=1
            for coder in ('A','C'):
                key=f'{coder}_AI_reference';rec[key]=refs[rid]['original_references'][coder]
                weights[key]=Fraction(sm['N_h'],sm['n_h'])
        rows.append({'id':rid,'metadata':{**m,'policy_file_stem':stem},'records':rec,'weights':weights})
    assert len(rows)==4481 and len(background)==443
    assert sum('A_AI_reference' in r['records'] for r in rows)==1057
    a.METHODS=tuple(methods)
    primary={m:a.summary(rows,m) for m in methods}
    latest={}
    for m in meta:
        if m['annual_series']:
            latest[m['policy_series']]=max(latest.get(m['policy_series'],-1),m['year_in_filename'])
    latest_rows=[r for r in rows if not r['metadata']['annual_series'] or r['metadata']['year_in_filename']==latest[r['metadata']['policy_series']]]
    nojoint=[r for r in rows if not r['metadata']['joint_publication']]
    files=sorted({r['metadata']['policy_file_stem'] for r in rows})
    sensitivities={}
    for method in methods:
        scenarios={
            'policy_file_equal_weight':a.equalized(rows,method,'policy_file_stem'),
            'policy_series_equal_weight':a.equalized(rows,method,'policy_series'),
            'latest_member_of_annual_series_only':a.summary(latest_rows,method),
            'exclude_all_joint_publications':a.summary(nojoint,method),
            **{s:a.summary(rows,method,s) for s in a.SCENARIOS if s!='primary'}}
        loo=[]
        for file in files:
            result=a.summary([r for r in rows if r['metadata']['policy_file_stem']!=file],method)
            loo.append({'discarded_file':file,'distribution':result,'dominant_dimensions':a.dominant(result),
                        'direction_changes':a.direction_changes(primary[method],result)})
        sensitivities[method]={'scenarios':scenarios,'leave_one_policy_file_out':loo,
            'primary_dominant_dimensions':a.dominant(primary[method]),
            'scenario_dominant_dimensions':{s:a.dominant(v) for s,v in scenarios.items()},
            'scenario_direction_changes':{s:a.direction_changes(primary[method],v) for s,v in scenarios.items()}}
    result={'scope':'药监、医保、卫健三个专业部门；中央文件仅作背景',
        'population_n':4481,'background_n':443,'source_entries':51,'reference_sample_n':1057,
        'attention_share_definition':'每维编码句次/同部门五维编码句次合计；A/C先按原设计权重估计句次再求比',
        'provenance':{'A_C':'AI agent首次独立判读，按双编码员指标计算','rules':args.rule_version+'实际全量运行',
                      'LLM':'gpt-5.6-sol v29实际全量结果' if llm else '真实重跑进行中；未接入旧结果'},
        'method_bindings':{'rule':{'inputs':str(args.inputs.resolve()),'rules':str(args.rules.resolve()),
                                  'method':args.rule_method,'version':args.rule_version},
                           'references':str(AC),'metadata':str(META),
                           'llm':{'path':str(llm_path.resolve()) if llm is not None else None,'method':args.llm_method,
                                  'expected_final_path':str(OUT/'llm-v29/production-25-v29/all_predictions.jsonl')}},
        'primary':primary,'sensitivities':sensitivities,
        'comparisons':{m:a.comparisons(primary[m]) for m in methods},
        'source_sha256':source_hashes,
        'original_strata_observed_counts':dict(strata),
        'A_C_weighting':'保留原29层设计的权重作三部门域估计；不重新声明1057为另抽独立样本。'}
    assert source_hashes=={str(p):a.sha(p) for p in sources},'Source changed during computation'
    (OUT/'三部门注意力分布与敏感性.json').write_text(json.dumps(a.as_json(result),ensure_ascii=False,indent=2))
    lines=['# 三部门五维注意力占比','',result['attention_share_definition'],'',
        '|方法|部门|观测单元|加权单元|五维句次|安全性%|有效性%|经济性%|创新性%|公平性%|',
        '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|']
    for method in methods:
        for g in (*a.GROUPS,'ALL'):
            r=primary[method][g]
            lines.append('|'+ '|'.join([method,g,str(r['observed_unit_count']),f"{float(r['weighted_unit_count']):.3f}",f"{float(r['weighted_five_dimension_known_hit_sum']):.3f}"]+[f"{float(r['dimensions'][d]['attention_share'])*100:.2f}" for d in DIMS])+'|')
    (OUT/'三部门注意力分布.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'methods':methods,'population_n':len(rows),'reference_n':1057,
        'weight_totals':{m:float(primary[m]['ALL']['weighted_unit_count']) for m in methods},
        'primary':{m:{g:[round(float(primary[m][g]['dimensions'][d]['attention_share'])*100,2) for d in DIMS] for g in a.GROUPS} for m in methods}},ensure_ascii=False))

if __name__=='__main__':main()
