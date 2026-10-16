"""Audit the recorded development review, never turn it into a reference standard."""
from collections import Counter
from pathlib import Path
import csv
import hashlib
import json

ROOT=Path(__file__).resolve().parent
BASE=ROOT.parent/'autocode-v27-final-20261004-1034'
DIMS=('S','E','Ec','I','F')
NAMES=dict(zip(DIMS,('安全性','有效性','经济性','创新性','公平性')))

def read(path):
    return json.loads(Path(path).read_text())

def rows(path):
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]

def save(name,value):
    (ROOT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def review_checks():
    old={r['id']:r for r in read(BASE/'workbook_data.json')['rows']}
    original_discrepancies=read(ROOT/'parent_discrepancies.json')
    needed={(r['id'],d['dimension']) for r in original_discrepancies for d in r['differences']}
    checked=set();records=[];by_group={};bindings={}
    for group,dims in [('se',('S','E')),('ec',('Ec',)),('if',('I','F'))]:
        updated=ROOT/f'semantic_review_{group}_context_updated.jsonl'
        review_path=updated if updated.exists() else ROOT/f'semantic_review_{group}.jsonl'
        packet_path=ROOT/f'audit_packet_{group}_context_updated.jsonl' if updated.exists() else ROOT/f'audit_packet_{group}.jsonl'
        packet={r['id']:r for r in rows(packet_path)}
        initial={r['id']:r for r in rows(ROOT/f'semantic_review_{group}.jsonl')}
        submitted=rows(review_path)
        assert len(submitted)==len(packet)
        assert {r['id'] for r in submitted}==set(packet)
        assert len({r['id'] for r in submitted})==len(submitted)
        selection=read(ROOT/f'parent_selection_{group}.json')
        selected=set(selection['targeted_ids'])
        count=Counter()
        for review in submitted:
            rid=review['id'];record=packet[rid]['input'];text=record['unit_text']
            assert set(review['labels'])==set(dims),(rid,review['labels'])
            for d in dims:
                value=review['labels'][d]
                assert type(value) is int and value in (0,1),(rid,d,value)
                evidence=review.get('evidence',{}).get(d,[])
                assert isinstance(evidence,list),(rid,d,evidence)
                assert all(isinstance(e,str) and e and e in text for e in evidence),(rid,d,evidence)
                reason=review['reason'][d]
                assert isinstance(reason,str) and reason.strip(),(rid,d,'missing reason')
                assert value==0 or evidence or review.get('context_evidence'),(rid,d,'positive without evidence')
                checked.add((rid,d))
                count['dimension_reviews']+=1
                if value!=old[rid]['after'][d]:count['different_from_v27']+=1
                refs={ref:old[rid]['references'][ref][d] for ref in ('A','C')}
                records.append({'id':rid,'group':group,'dimension':d,'scope':old[rid]['scope'],
                    'packet_role':'分歧专项材料' if rid in selected else '随机对照材料',
                    'original_id':packet[rid]['original_id'],'text':text,
                    'old_rule':old[rid]['after'][d],'semantic_review':value,
                    'initial_semantic_review':initial[rid]['labels'][d],
                    'semantic_review_version':'context_updated' if updated.exists() else 'initial',
                    'A':refs['A'],'C':refs['C'],'evidence':evidence,'reason':reason,
                    'context_evidence':review.get('context_evidence'),
                    'source':record.get('unit_source') or record.get('source'),
                    'original_discrepancy':(rid,d) in needed})
        by_group[group]={'units':len(packet),**dict(count)}
        bindings[str(ROOT/f'semantic_review_{group}.jsonl')]=sha(ROOT/f'semantic_review_{group}.jsonl')
        bindings[str(review_path)]=sha(review_path)
        bindings[str(packet_path)]=sha(packet_path)
    assert needed<=checked,needed-checked
    result={'scope':'Development semantic audit, not a gold standard or independent validation',
            'original_discrepant_units':len(original_discrepancies),
            'original_discrepant_unit_dimensions':len(needed),
            'unique_reviewed_units':len({r['id'] for r in records}),
            'unit_dimension_reviews':len(records),'all_targeted_unit_dimensions_covered':True,
            'by_group':by_group,'review_bindings':bindings}
    save('semantic_review_verification.json',result)
    save('semantic_review_flat.json',records)
    print(json.dumps(result,ensure_ascii=False))
    return records,result

def report():
    reviews,verification=review_checks()
    data=read(ROOT/'workbook_data.json');metrics=read(ROOT/'metrics.json')
    byid={r['id']:r for r in data['rows']}
    masks={k:set(v) for k,v in read(ROOT/'comparison_masks.json').items()}
    matrices=[];counts=Counter();details=[];residual_units=set();initial_units=set()
    for scope in ('H427','current1268'):
        for d in DIMS:
            row={'scope':scope,'dimension':d}
            for a in ('A','C'):
                entry=metrics['comparisons'][scope]['references'][a][d]
                for method in ('rules_v27','rules_v28','llm_unchanged'):
                    metric=entry['methods'][method]['common_unweighted']
                    k=metric['binary_agreement']['kappa']
                    row[f'{method}_{a}']=k
                    counts[f'{method}_at_target']+=int(k is not None and k>=0.8)
                row[f'n_{a}']=entry['common_n']
                row[f'new_recall_{a}']=entry['methods']['rules_v28']['common_unweighted']['conditional_scores']['recall']
            matrices.append(row)
    for r in data['rows']:
        for d in DIMS:
            for a in ('A','C'):
                if r['id'] not in masks.get(f"{r['scope']}/{a}/{d}",set()):continue
                ref=r['references'][a][d]
                if r['before'][d]!=ref:initial_units.add(r['id'])
                if r['after'][d]!=ref:
                    residual_units.add(r['id'])
                    details.append({'id':r['id'],'scope':r['scope'],'dimension':d,'reference':a,
                                    'prediction':r['after'][d],'reference_label':ref})
    for r in reviews:
        r['new_rule']=byid[r['id']]['after'][r['dimension']]
        r['changed']=r['old_rule']!=r['new_rule']
        r['new_matches_review']=r['new_rule']==r['semantic_review']
        r['old_matches_review']=r['old_rule']==r['semantic_review']
        if r['original_discrepancy']:
            r['review_assessment']='专项复核支持旧规则' if r['old_matches_review'] else '专项复核与旧规则不同'
        else:r['review_assessment']='对照及同句其他维度'
    new_changes=[r for r in data['rows'] if r['changed_dimensions']]
    old_input_predictions={r['id']:r['prediction']['labels'] for r in rows(ROOT/'v27_input_predictions.jsonl')}
    code_changed={r['id'] for r in data['rows'] if r['before']!=old_input_predictions[r['id']]}
    context_changed={r['id'] for r in data['rows'] if r['after']!=old_input_predictions[r['id']]}
    decomposition={'new_code_on_fixed_v27_inputs_changed_units':len(code_changed),
                   'added_context_on_fixed_new_code_changed_units':len(context_changed),
                   'overlap_units':len(code_changed & context_changed),
                   'note':'Sequential descriptive ablation; overlaps and reversals mean counts need not add to final changes.'}
    source_totals={}
    for r in data['rows']:
        key=r.get('source') or 'unknown'
        count=source_totals.setdefault(key,{'n':0,'before':Counter(),'after':Counter()})
        count['n']+=1
        for d in DIMS:
            count['before'][d]+=int(r['before'][d]==1);count['after'][d]+=int(r['after'][d]==1)
    source_changes=[{'source':s,'n':c['n'],'before':dict(c['before']),'after':dict(c['after']),
                     'changes':{d:c['after'][d]-c['before'][d] for d in DIMS}}
                    for s,c in source_totals.items() if c['before']!=c['after']]
    amendments={g:read(ROOT/f'amendment_log_{g}.json') for g in ('se','ec','if')}
    if (ROOT/'amendment_log_ec_context_fix.json').exists():
        amendments['ec_context_fix']=read(ROOT/'amendment_log_ec_context_fix.json')
    if (ROOT/'amendment_log_se_name_only_fix.json').exists():
        amendments['se_name_only_fix']=read(ROOT/'amendment_log_se_name_only_fix.json')
    supplemental=[]
    if (ROOT/'new_discrepancy_semantic_review_se.json').exists():
        extra=read(ROOT/'new_discrepancy_semantic_review_se.json')
        assert extra['input_provenance']['unit_text']==byid[extra['id']]['text']
        supplemental.append({'id':extra['id'],'dimension':'S','semantic_review':extra['labels']['S'],
                             'rule':byid[extra['id']]['after']['S'],
                             'reason':extra['reason']['S'],
                             'review_file':'new_discrepancy_semantic_review_se.json'})
    stats={'total':metrics['n'],'pending':metrics['pending_n'],'changed_units':len(new_changes),
        'target':0.8,'comparisons_per_method':20,**dict(counts),
        'initial_discrepant_units':len(initial_units),'residual_discrepant_units':len(residual_units),
        'resolved_units':len(initial_units-residual_units),'new_discrepant_units':len(residual_units-initial_units),
        'residual_unit_dimensions':len({(r['id'],r['dimension']) for r in details}),
        'reviewed_unique_units':verification['unique_reviewed_units'],
        'reviewed_unit_dimensions':verification['unit_dimension_reviews'],
        'independent_validation':'not_performed',
        'all_rule_pairs_at_working_target':counts['rules_v28_at_target']==20,
        'LLM_rerun':False,'reference_labels_unchanged':True,
        'source_groups_with_any_count_change':len(source_changes),
        'supplemental_review_count':len(supplemental),
        'code_context_decomposition':decomposition,
        'semantic_review_matches':{'before':sum(r['old_matches_review'] for r in reviews),
                                   'after':sum(r['new_matches_review'] for r in reviews)}}
    save('audit_report_data.json',{'summary':stats,'matrix':matrices,'metrics':data['metrics'],
                                 'reviews':reviews,'all_rows':data['rows'],'amendments':amendments,
                                 'supplemental_reviews':supplemental})
    save('residual_discrepancies.json',details);save('source_distribution_changes.json',source_changes)
    save('audit_summary.json',stats)
    fields=['id','original_id','scope','source','text']+[f'{v}_{d}' for v in ('before','after') for d in DIMS]
    with (ROOT/'全量编码-v28.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader()
        for r in data['rows']:
            writer.writerow({**{k:r[k] for k in fields[:5]},**{f'{v}_{d}':r[v][d] for v in ('before','after') for d in DIMS}})
    lines=['自动规则 κ 复核与修订记录','',
           '工作目标为 κ≥0.80。这是看到 v27 结果后设定的保守复核目标，不是原先预注册标准或通用投稿门槛。',
           '两组均为已接触的开发材料。达到工作目标不等于独立验证通过。A/C 为 AI 首次编码参照，不是真人金标准。',
           f"完成 {stats['reviewed_unique_units']} 条不同原文、{stats['reviewed_unit_dimensions']} 个维度判断的专项复核，覆盖全部257条原始分歧。", 
           f"本轮全量 {stats['total']} 条，待定 {stats['pending']} 条；相对 v27 改变 {stats['changed_units']} 条原文的至少一个维度。", 
           f"自动规则达到工作目标：{stats['rules_v27_at_target']}/20 → {stats['rules_v28_at_target']}/20。原LLM为 {stats['llm_unchanged_at_target']}/20，本轮没有重跑。", 
           f"与任一A/C存在分歧的原文：{stats['initial_discrepant_units']} → {stats['residual_discrepant_units']}。其中原分歧消失 {stats['resolved_units']} 条，新出现分歧 {stats['new_discrepant_units']} 条。",'',
           '各组每个维度均沿用v27相同配对口径，保留原A/C和原LLM标签。语义复核结果另外保存，不能替换首次参照。',
           '原文未改变；v28对104条输入补充核验后的上下文。原LLM及首次A/C未回改；另报新规则在v27旧输入上的对照，区分代码与上下文效果。',
           f"固定v27输入仅更换规则改变 {len(code_changed)} 条；固定新规则再补充上下文改变 {len(context_changed)} 条；两步受影响集合重叠 {len(code_changed & context_changed)} 条。最终变化数按唯一条目与v27逐条比较得到。",
           '调整记录与正负回归案例见各专项 amendment_log 和 test 文件。全量重跑完成后统一计算，未按结果选择样本。','',
           '另对v28.1新增的一条分歧进行隐藏标签的补充语义复核，并据手册修正仅凭药品类别名称触发S的通用边界。v28.1产物已另行封存，本版为v28.2。',
           '自动规则 κ（原v27 → 本轮v28）']
    for row in matrices:
        lines.append(f"{row['scope']} {NAMES[row['dimension']]}：A {row['rules_v27_A']:.3f} → {row['rules_v28_A']:.3f}；C {row['rules_v27_C']:.3f} → {row['rules_v28_C']:.3f}")
    lines.extend(['','论文使用边界：',
        '当前 κ 描述方法与AI参照的一致性，不能单独证明部门关注排序或制度解释。正文需另核对各部门分布、测量偏差与敏感性。',
        'H427 对本轮修订规则已不再是未见检验材料；历史冻结结果的验证地位必须按当时版本分别叙述。',
        '本轮没有完成新的独立样本验证、真人专家效度复核或LLM修订重跑，不能标注全部信效度验证通过。',
        '如仍有 κ 低于工作目标，应报告实际数值和限制，不通过改参照、选择性排除或改变维度定义追求通过。','',
        '方法依据：Artstein & Poesio (2008), https://aclanthology.org/J08-4004/；Grimmer & Stewart (2013), https://doi.org/10.1093/pan/mps028。'])
    (ROOT/'本轮复核结果说明.txt').write_text('\n'.join(lines)+'\n')
    print(json.dumps(stats,ensure_ascii=False,indent=2))

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--reviews-only',action='store_true')
    args=parser.parse_args()
    if args.reviews_only:review_checks()
    else:report()
