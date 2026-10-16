"""Compare completed final v31/v30 statistics with the frozen delivered baseline."""
from pathlib import Path
from itertools import combinations
from fractions import Fraction
import csv
import hashlib
import json

OUT=Path(__file__).resolve().parent
BASE=OUT.parent/'final-three-department-20261007'
DIMS=('S','E','Ec','I','F')
GROUPS=('NMPA','NHSA','NHC')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def fraction(value):
    return Fraction(value['exact_fraction']) if isinstance(value,dict) else Fraction(value)


def main():
    paths={key:root/name for key,root,name in (
        ('old_coding',BASE,'三部门编码指标.json'),('new_coding',OUT,'三部门编码指标.json'),
        ('old_attention',BASE,'三部门注意力分布与敏感性.json'),('new_attention',OUT,'三部门注意力分布与敏感性.json'),
        ('point_qa',OUT,'三部门编码指标核验.json'),('ci_qa',OUT,'聚类区间独立重算核验.json'),
        ('attention_qa',OUT,'三部门数据独立QA.json'))}
    sources={str(p):sha(p) for p in paths.values()}
    data={key:json.loads(path.read_text()) for key,path in paths.items()}
    old,new=data['old_coding'],data['new_coding']
    old_attention,new_attention=data['old_attention'],data['new_attention']
    assert new['latest_llm']['status']=='actual_completed_v30_loaded'
    assert new['method_bindings']['rule']['method']=='rules_v31'
    assert new['method_bindings']['llm']['method']=='llm_gpt56_sol_v30'
    assert len(new['records'])==len(old['records'])==200
    assert sum(len(r['metrics']) for r in new['records'])==1280
    for key in ('point_qa','ci_qa'):
        assert data[key]['status']=='passed' and data[key]['target_sha256']==sha(paths['new_coding'])
    assert data['ci_qa']['intervals_independently_recomputed']==1280
    assert data['attention_qa']['status']=='passed' and data['attention_qa']['target_sha256']==sha(paths['new_attention'])
    methods={'rules_v31':'rules_v30','llm_gpt56_sol_v30':'llm_gpt56_sol_v29','A_C':'A_C'}
    index={(r['frame'],r['group'],r['dimension'],r['method'],r['reference']):r for r in old['records']}
    rows=[];a_c_unchanged=0
    for r in new['records']:
        a=index[r['frame'],r['group'],r['dimension'],methods[r['method']],r['reference']]
        for k in ('n','frame_n','excluded_n','exclusions','right_positive_n','eligible_ids_sha256'):
            assert a[k]==r[k], ('Changed reference subset',k,r)
        if r['method']=='A_C':
            assert a['cross_tab']==r['cross_tab'] and a['metrics']==r['metrics']
            a_c_unchanged+=1;continue
        row={k:r[k] for k in ('frame','group','dimension','method','reference','n','frame_n','excluded_n','right_positive_n','source_clusters')}
        row['old_confusion'],row['new_confusion']=a['confusion'],r['confusion']
        for m in ('precision','recall','f1','kappa','agreement'):
            x,y=a['metrics'][m]['estimate'],r['metrics'][m]['estimate']
            row['old_'+m],row['new_'+m]=x,y
            row['delta_'+m]=y-x if x is not None and y is not None else None
        row['new_recall_ci95']=r['metrics']['recall']['ci95']
        row['new_kappa_ci95']=r['metrics']['kappa']['ci95']
        rows.append(row)
    assert a_c_unchanged==40 and len(rows)==160
    attention_rows=[];direction_checks=[]
    attention_methods={'rules_v31':'rules_v30','llm_gpt56_sol_v30':'llm_gpt56_sol_v29',
                       'A_AI_reference':'A_AI_reference','C_AI_reference':'C_AI_reference'}
    for method,old_method in attention_methods.items():
        for group in GROUPS:
            for dim in DIMS:
                a=old_attention['primary'][old_method][group]['dimensions'][dim]
                r=new_attention['primary'][method][group]['dimensions'][dim]
                x,y=fraction(a['attention_share']),fraction(r['attention_share'])
                if method.endswith('_AI_reference'):
                    assert a==r
                attention_rows.append({'method':method,'group':group,'dimension':dim,
                    'old_share':float(x),'new_share':float(y),'change_percentage_points':float((y-x)*100),
                    'old_share_exact_fraction':str(x),'new_share_exact_fraction':str(y),
                    'old_known_hit_count':a['raw_known_hit_count'],'new_known_hit_count':r['raw_known_hit_count']})
    sign=lambda v:(v>0)-(v<0)
    for g1,g2 in combinations(GROUPS,2):
        for dim in DIMS:
            row={'pair':[g1,g2],'dimension':dim}
            for name,stats,rule,llm in (('old',old_attention,'rules_v30','llm_gpt56_sol_v29'),
                                        ('new',new_attention,'rules_v31','llm_gpt56_sol_v30')):
                values={method:sign(fraction(stats['primary'][method][g1]['dimensions'][dim]['attention_share'])-
                                    fraction(stats['primary'][method][g2]['dimensions'][dim]['attention_share'])) for method in (rule,llm)}
                row[name+'_rule_direction']=values[rule]
                row[name+'_llm_direction']=values[llm]
                row[name+'_methods_direction_agree']=values[rule]==values[llm]
            direction_checks.append(row)
    result={'status':'COMPLETED_STATISTICAL_COMPARISON_WITH_INDEPENDENT_QA',
            'reference_identity':new['reference_identity'],'validation_status':new['validation_status'],
            'A_C_records_and_original_intervals_unchanged':a_c_unchanged,
            'main_overall_machine_comparisons':20,'main_department_machine_comparisons':60,
            'classification_comparisons':rows,'attention_comparisons':attention_rows,
            'three_department_fifteen_direction_checks':direction_checks,
            'interpretation':'Metrics measure agreement and class recovery against unchanged exposed AI A/C references. Improvements and losses are both retained; they do not replace substantive source checks or actual independent human validation.',
            'source_sha256':sources}
    assert sources=={p:sha(Path(p)) for p in sources}
    (OUT/'召回修订前后指标与注意力比较.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    def export(name,table):
        with (OUT/name).open('w',encoding='utf-8-sig',newline='') as f:
            writer=csv.DictWriter(f,fieldnames=list(table[0]));writer.writeheader();writer.writerows(table)
    flat=[]
    for row in rows:
        if row['frame']!='main1057':continue
        item={k:v for k,v in row.items() if not isinstance(v,dict)}
        for phase in ('old','new'):item.update({phase+'_'+k:v for k,v in row[phase+'_confusion'].items()})
        flat.append(item)
    export('召回修订前后主样本20与60项.csv',flat)
    export('召回修订前后注意力占比.csv',attention_rows)
    fmt=lambda v:'NA' if v is None else f'{v:.6f}'
    lines=['# 召回修订前后统计比较','',
        '以下比较使用实际完成的规则 v31 和 gpt-5.6-sol LLM v30 全量结果。A/C 原始首次 AI 参照、待定状态和共同可判集合保持不变。200 条比较与 1280 个来源文件聚类区间已完成独立核验。','',
        '|方法|维度|参照|n / 参照正类数|精确率 旧→新|召回率 旧→新|F1 旧→新|κ 旧→新|',
        '|---|---|---|---|---|---|---|---|']
    for row in rows:
        if row['frame']=='main1057' and row['group']=='ALL':
            lines.append('|'+ '|'.join([row['method'],row['dimension'],row['reference'],f"{row['n']} / {row['right_positive_n']}",
                *[fmt(row['old_'+m])+'→'+fmt(row['new_'+m]) for m in ('precision','recall','f1','kappa')]])+'|')
    lines+=['','完整分部门变化和四格见 CSV。注意力占比以同部门五维编码句次为分母，跨维共现分别计次，同维每条至多一次。A/C 注意力先按原设计权重估计句次后求比。','',
            '这些结果报告实际修订的改进和损失，不将召回率单独作为方法优劣或可发表性的判据。','']
    (OUT/'召回修订前后指标比较.md').write_text('\n'.join(lines))
    print(json.dumps({'status':result['status'],'A_C_unchanged':a_c_unchanged,'comparisons':len(rows),
                      'new_rule_LLM_direction_agreement_count':sum(r['new_methods_direction_agree'] for r in direction_checks)},ensure_ascii=False))


if __name__=='__main__':main()
