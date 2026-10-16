"""Compute before-adjudication A/C reliability, separately for probability/challenge."""
from collections import Counter
import csv
import datetime
from statistical_core import *
from current_material_context import load_current_context

def main():
    OUT.mkdir(exist_ok=True)
    ctx=load_current_context();paths=ctx['source_paths']+[RUN/f'reference/agent_{c}_{v}.jsonl' for c in ('A','C') for v in ('first','final_v6','final_v8')]+[Path(__file__)]
    before={str(p):sha(p) for p in paths};records=[];versions={};factors={}
    for version in ('first','final_v6','final_v8'):
        refs={coder:jsonl(RUN/f'reference/agent_{coder}_{version}.jsonl') for coder in ('A','C')}
        assert set(refs['A'])==set(refs['C'])==set(ctx['sample'])
        versions[version]=refs
        for component in ('probability_base','enriched_challenge'):
            for group,kind in groups_and_weights(component):
                ids=[rid for rid,r in ctx['sample'].items() if r['component']==component and(group=='ALL' or r['group']==group)]
                for dim in DIMS:
                    row=comparison(ctx,refs['A'],refs['C'],dim,ids,component,group,kind,'A_C','C',factors)
                    row['reference_version']=version;records.append(row)
    changes=[]
    for coder in ('A','C'):
        for rid in versions['final_v6'][coder]:
            for dim in DIMS:
                old=label(versions['final_v6'][coder][rid],dim);new=label(versions['final_v8'][coder][rid],dim)
                if old!=new:
                    assert rid in ctx['final_source_reread_sample_ids']
                    changes.append({'coder':coder,'id':rid,'dimension':dim,'final_v6':old,'final_v8':new})
    final=versions['final_v8'];disagreements=[{'id':rid,'component':ctx['sample'][rid]['component'],'group':ctx['sample'][rid]['group'],
        'dimensions':[d for d in DIMS if label(final['A'][rid],d)!=label(final['C'][rid],d)]} for rid in final['A'] if final['A'][rid]['labels']!=final['C'][rid]['labels']]
    assert len(disagreements)==19 and len(changes)==2
    report={'status':'completed_before_adjudication_AI_agent_reference_reliability','created_at':datetime.datetime.now().astimezone().isoformat(),
        'human_validation_completed':False,'adjudication_used_for_A_C_reliability':False,'analysis_notes':analysis_notes(),
        'v6_to_v8_source_reread_changes':changes,'other_v6_binary_labels_preserved':True,'final_material_version':'v8',
        'final_disagreement_units':len(disagreements),'final_disagreements':disagreements,'records':records,'source_sha256':before}
    write_json(OUT/'A_C协商前信度-v8.json',report)
    fields=['reference_version','component','group','weighting','dimension','unit_frame_n','paired_n','excluded_pending_n','left_positive_n','reference_positive_n','TP','FP','FN','TN','kappa','kappa_low','kappa_high','agreement','agreement_low','agreement_high','source_file_kappa_low','source_file_kappa_high']
    with (OUT/'A_C协商前信度-v8.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fields);writer.writeheader()
        for r in records:
            row={k:r[k] for k in fields if k in r};row.update(r['raw_confusion'])
            for name in ('kappa','agreement'):
                metric=r['metrics'][name];row[name]=metric['estimate'];row[name+'_low']=metric['ci95_primary']['low'];row[name+'_high']=metric['ci95_primary']['high']
            row.update({'source_file_kappa_'+key:r['metrics']['kappa']['ci95_source_file_conditional_sensitivity'][key] for key in ('low','high')})
            writer.writerow(row)
    lines=['# 新专家agent A/C协商前信度','',
        'A/C为两位独立专家agent，未冒称真人。首次、v6和新增四条补料后的独立v8提交分别留存；本表未使用第三方裁决改写协商前信度。概率240条与挑战60条分开。','',
        '|样本|部门|加权|维度|配对n|A1/C1、A1/C0、A0/C1、A0/C0|κ|95%主区间|一致率|','|---|---|---|---|---:|---|---:|---|---:|']
    fmt=lambda x:'NA' if x is None else f'{x:.6f}'
    for r in records:
        if r['reference_version']!='final_v8':continue
        k=r['metrics']['kappa'];ci=k['ci95_primary']
        lines.append('|'+ '|'.join([r['component'],r['group'],r['weighting'],r['dimension'],str(r['paired_n']),'/'.join(str(v) for v in r['raw_confusion'].values()),fmt(k['estimate']),f'[{fmt(ci["low"])}, {fmt(ci["high"])}]',fmt(r['metrics']['agreement']['estimate'])])+'|')
    lines+=['','概率部门内按单位简单随机不放回抽样。主区间采用部门内n−1重抽及有限总体重标度的5000次百分位近似；非线性κ的有限样本覆盖不作精确保证。另列按部门文件聚类重抽样的条件敏感性区间，不能冒充原单位抽样设计区间。两套机制都不覆盖agent共同语义错误。',
        '', '全概率样本未加权总体表示等额部门样本混合；eligible_design_weighted总体按1147/80、1575/80、240/80加权，仅对应开发排除后的2962单元可用框。挑战不进入该总体估计。',
        '', '无正类导致的零分母记NA。完美样本一致的退化区间仅说明该已见样本的重抽结果，不能保证未见材料或真人判定一致。',
        '', '[重标度机制文档](https://bschneidr.github.io/svrep/reference/make_rwyb_bootstrap_weights.html)与[官方实现](https://github.com/bschneidr/svrep/blob/main/R/make_bootstrap_weights.R)；确切公式、权重、种子和区间范围见JSON analysis_notes。']
    (OUT/'A_C协商前信度-v8.md').write_text('\n'.join(lines)+'\n')
    assert before=={str(p):sha(p) for p in paths}
    print(json.dumps({'status':report['status'],'records':len(records),'disagreement_units':len(disagreements),'final_probability_overall_kappa':{r['dimension']:r['metrics']['kappa']['estimate'] for r in records if r['reference_version']=='final_v8' and r['component']=='probability_base' and r['group']=='ALL' and r['weighting']=='unweighted'}},ensure_ascii=False))

if __name__=='__main__':main()
