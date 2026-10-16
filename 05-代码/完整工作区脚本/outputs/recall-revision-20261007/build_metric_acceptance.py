"""Report the clarified diagnostic point markers to actual, independently checked metrics.

No threshold is represented as a universal publication standard, and no label
is changed. H411 is a separate supplementary review; no mechanical authoring gate is set.
"""
from pathlib import Path
from collections import Counter
import csv
import datetime
import hashlib
import json

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[1]
THRESHOLD=.80
NAMES={'S':'安全性','E':'有效性','Ec':'经济性','I':'创新性','F':'公平性'}
GROUPS={'ALL':'总体','NMPA':'药监','NHSA':'医保','NHC':'卫健'}
TARGET_SOURCE='用户先前提出0.80逐项目标，随后澄清核心目标为三种方法共同支持同一实质结论；0.80仅保留逐项诊断标记，不作为全340项必须过线的门禁。'
TARGET_SCOPE='主1057机器总体20项和分部门60项比较的κ/P/R/F1点估计，以及A—C总体5项和分部门15项比较的κ点估计；340个点指标；0.80为诊断标记，区间同步报告。'


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text())
def jsonl(path):return {r['id']:r for r in map(json.loads,Path(path).read_text().splitlines())}
def binary(value):return type(value) is int and value in (0,1)
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')


def write_csv(path,records):
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=list(records[0]));writer.writeheader();writer.writerows(records)


def summarize(records):
    summary={}
    for segment in ('machine_overall','machine_department','A_C_overall','A_C_department'):
        chosen=[r for r in records if r['acceptance_segment']==segment]
        values=[m for r in chosen for m in r['evaluated_metrics'].values()]
        summary[segment]={'comparison_count':len(chosen),'point_indicator_count':len(values),
            'defined_ge_0_80':sum(m['point_target_met'] is True for m in values),
            'defined_lt_0_80':sum(m['point_lt_0_80'] is True for m in values),
            'undefined_not_passed':sum(m['estimate'] is None for m in values),
            'metrics':{name:dict(Counter('undefined_not_passed' if r['evaluated_metrics'][name]['estimate'] is None
                          else 'defined_ge_0_80' if r['evaluated_metrics'][name]['point_target_met'] else 'defined_lt_0_80'
                          for r in chosen if name in r['evaluated_metrics']))
                       for name in ('kappa','precision','recall','f1')}}
    return summary


def main():
    metric_path=OUT/'三部门编码指标.json';metrics=read(metric_path)
    point_qa=read(OUT/'三部门编码指标核验.json');interval_qa=read(OUT/'聚类区间独立重算核验.json')
    assert point_qa['status']==interval_qa['status']=='passed'
    assert point_qa['target_sha256']==interval_qa['target_sha256']==sha(metric_path)
    assert interval_qa['intervals_independently_recomputed']==1280
    assert metrics['method_bindings']['llm']['source_material_version']=='v3'
    assert metrics['method_bindings']['llm']['status']=='complete_validated_full_corpus'
    assert len(metrics['records'])==200 and metrics['bootstrap']['repetitions']==5000
    sources=[metric_path,OUT/'三部门编码指标核验.json',OUT/'聚类区间独立重算核验.json',Path(__file__)]
    source_hashes={str(p):sha(p) for p in sources}
    structured={};flat={}
    for frame in ('main1057','supplement_H411'):
        selected=[r for r in metrics['records'] if r['frame']==frame]
        assert len(selected)==100
        records=[];csv_rows=[]
        for row in selected:
            ac=row['method']=='A_C';names=('kappa',) if ac else ('kappa','precision','recall','f1')
            segment=('A_C' if ac else 'machine')+('_overall' if row['group']=='ALL' else '_department')
            key='/'.join(row[k] for k in ('frame','group','dimension','method','reference'))
            evaluated={}
            for name in names:
                value=row['metrics'][name];point=value['estimate'];ci=value['ci95']
                evaluated[name]={'estimate':point,'ci95':ci,'defined':point is not None,
                    'point_lt_0_80':None if point is None else point<THRESHOLD,
                    'point_target_met':point is not None and point>=THRESHOLD,
                    'ci95_low_lt_0_80':None if ci['low'] is None else ci['low']<THRESHOLD,
                    'interval_is_acceptance_criterion':False}
            record={'record_key':key,'frame':frame,'group':row['group'],'group_name':GROUPS[row['group']],
                'dimension':row['dimension'],'dimension_name':NAMES[row['dimension']],
                'method':row['method'],'reference':row['reference'],'acceptance_segment':segment,
                'paired_n':row['n'],'frame_n':row['frame_n'],'excluded_n':row['excluded_n'],
                'left_positive_n':row['left_positive_n'],'reference_positive_n':row['right_positive_n'],
                'reference_positive_rate':row['right_positive_rate'],'source_clusters':row['source_clusters'],
                'confusion':row['confusion'],'cross_tab':row['cross_tab'],'exclusions':row['exclusions'],
                'evaluated_metrics':evaluated,'all_evaluated_points_meet_target':all(v['point_target_met'] for v in evaluated.values()),
                'A_C_precision_recall_f1':'not_applicable_symmetric_agreement' if ac else None}
            records.append(record)
            target_note='0.80仅作逐项诊断复核标记；非通用发表线，也不是论文唯一门禁' if frame=='main1057' else '补充H411单列描述性复核；不混入主样本验收门禁'
            csv_row={'record_key':key,'样本框':frame,'诊断分组':segment,'部门':GROUPS[row['group']],
                '维度':NAMES[row['dimension']],'方法':row['method'],'参照':row['reference'],
                '实际配对n':row['n'],'整框n':row['frame_n'],'排除待定n':row['excluded_n'],
                '方法编码1数':row['left_positive_n'],'参照编码1数':row['right_positive_n'],
                '来源文件簇数':row['source_clusters'],'点值复核标记':THRESHOLD,
                '复核标记来源':TARGET_SOURCE if frame=='main1057' else '仅沿用0.80作补充复核标记',
                '复核标记含义':target_note,'本比较所有适用点值不低于复核标记':record['all_evaluated_points_meet_target']}
            for name,label in [('kappa','κ'),('precision','精确率P'),('recall','召回率R'),('f1','F1')]:
                value=evaluated.get(name)
                csv_row.update({label+'点值':value['estimate'] if value else None,
                    label+'95%CI下界':value['ci95']['low'] if value else None,
                    label+'95%CI上界':value['ci95']['high'] if value else None,
                    label+'点值小于0.80':value['point_lt_0_80'] if value else None,
                    label+'点值不低于复核标记':value['point_target_met'] if value else None,
                    label+'状态':'A—C不适用' if value is None else '未定义，不能据此判为达到数值标记' if value['estimate'] is None else '点值低于0.80复核标记' if value['point_lt_0_80'] else '点值不低于0.80复核标记',
                    label+'区间有效重复':value['ci95']['defined_repetitions'] if value else None,
                    label+'区间未定义重复':value['ci95']['undefined_repetitions'] if value else None})
            csv_rows.append(csv_row)
        assert sum(len(r['evaluated_metrics']) for r in records)==340
        summary=summarize(records)
        assert [summary[k]['point_indicator_count'] for k in summary]==[80,240,5,15]
        all_pass=all(r['all_evaluated_points_meet_target'] for r in records)
        report={'status':'diagnostic_point_markers_all_ge_0_80' if all_pass else 'diagnostic_point_markers_include_low_or_undefined_values',
            'checked_at':datetime.datetime.now().astimezone().isoformat(),'frame':frame,
            'target':{'threshold':THRESHOLD,'confirmation_source':TARGET_SOURCE,
                'current_use':'diagnostic_only_after_user_substantive_goal_clarification','not_a_current_all_indicators_must_pass_requirement':True,'scope':TARGET_SCOPE,'not_a_universal_journal_publication_line':True,
                'point_estimates_only':True,'undefined_counts_as_pass':False,'CI_lower_bound_target':None,
                'H411_not_part_of_main_acceptance_gate':True},
            'main_authoring_gate_applies':False,
            'authoring_gate':'no_mechanical_threshold_gate; substantive_common_conclusion_confirmation_pending',
            'comparison_count':100,'point_indicator_count':340,'summary':summary,'records':records,
            'weak_comparison_record_keys':[r['record_key'] for r in records if not r['all_evaluated_points_meet_target']],
            'reference_identity':metrics['reference_identity'],'validation_status':metrics['validation_status'],
            'human_validation_completed':False,'labels_modified':False,'publication_acceptance_claim':False,
            'source_sha256':source_hashes}
        stem='指标诊断表' if frame=='main1057' else 'H411指标复核表-补充样本'
        dump(OUT/(stem+'.json'),report);write_csv(OUT/(stem+'.csv'),csv_rows)
        structured[frame]=report;flat[frame]=csv_rows
    # Independently enumerate original paired disagreements for every weak main
    # comparison, including weak P/R/F1 cells whose kappa may be high.
    binding=metrics['method_bindings'];inputs=jsonl(binding['rule']['inputs'])
    rules=jsonl(binding['rule']['rules']);llm=jsonl(binding['llm']['path'])
    refs=jsonl(binding['references']);metadata=read(binding['metadata'])['rows']
    groups={Path(r['original_file']).stem:r['analysis_group'] for r in metadata}
    weak_records=[r for r in structured['main1057']['records'] if not r['all_evaluated_points_meet_target']]
    disagreements=[];weak_support=[]
    for record in weak_records:
        d=record['dimension'];ac=record['method']=='A_C';n=0;left_ones=0;right_ones=0;cells=Counter();ids=[]
        for rid,ref in refs.items():
            inp=inputs[rid]['input'];group=groups[inp['original_file_stem']]
            if group not in ('NMPA','NHSA','NHC') or (record['group']!='ALL' and group!=record['group']):continue
            left_record=ref['original_references']['A'] if ac else (rules[rid]['prediction'] if record['method']=='rules_v31' else llm[rid].get('prediction',llm[rid]))
            right_record=ref['original_references'][record['reference']]
            left,right=left_record['labels'][d],right_record['labels'][d]
            if not binary(left) or not binary(right):continue
            n+=1;left_ones+=left;right_ones+=right
            cells[{(1,1):'TP',(1,0):'FP',(0,1):'FN',(0,0):'TN'}[left,right]]+=1
            if left==right:continue
            ids.append(rid)
            disagreements.append({'record_key':record['record_key'],'id':rid,'group':group,
                'dimension':d,'dimension_name':NAMES[d],'method':record['method'],'reference':record['reference'],
                'relative_reference_contribution':('A1_C0' if left==1 else 'A0_C1') if ac else ('FP' if left==1 else 'FN'),
                'classification_scope':'Disagreement relative to exposed original AI reference; not adjudicated human error or semantic truth.',
                'original_id':inputs[rid]['original_id'],'unit_text':inp['unit_text'],
                'source_file':inp.get('unit_source') or inp['source'],'pages':inp.get('pages',[]),
                'paragraph_context':inp.get('paragraph_context',[]),
                'nearest_preceding_heading':inp.get('nearest_preceding_heading'),
                'verified_parent_context_texts':[p['text'] for p in inp.get('verified_parent_context',[])],
                'actual_shared_contexts':inp['llm_v29_shared_context'],
                'left_label':left,'reference_label':right,
                'left_reason':left_record.get('dimension_reasons',{}).get(d),
                'reference_reason':right_record.get('dimension_reasons',{}).get(d),
                'left_evidence':[e for e in left_record.get('evidence',[]) if isinstance(e,dict) and e.get('dimension')==d],
                'left_raw_evidence_if_not_dimension_structured':left_record.get('evidence') if not isinstance(left_record.get('evidence'),list) else None,
                'left_suppressions':[e for e in (left_record.get('suppressions') or []) if isinstance(e,dict) and (e.get('dimension')==d or d in e.get('dimensions',[]))]})
        assert n==record['paired_n'] and left_ones==record['left_positive_n'] and right_ones==record['reference_positive_n']
        if not ac:assert {k:cells[k] for k in ('TP','FP','FN','TN')}==record['confusion']
        weak_support.append({'record_key':record['record_key'],'weak_metrics':{k:v for k,v in record['evaluated_metrics'].items() if not v['point_target_met']},
            'paired_n':n,'left_positive_n':left_ones,'reference_positive_n':right_ones,
            'confusion_as_left_relative_to_right':{k:cells[k] for k in ('TP','FP','FN','TN')},
            'disagreement_n':len(ids),'disagreement_ids':ids,
            'no_paired_disagreement_but_undefined_metric':not ids and any(v['estimate'] is None for v in record['evaluated_metrics'].values())})
    audit={'status':'actual_main_diagnostic_flags_and_raw_disagreement_ids_enumerated',
        'target_source':TARGET_SOURCE,'target_threshold':THRESHOLD,'main_frame_only':True,
        'weak_comparison_count':len(weak_support),'weak_comparisons':weak_support,'disagreements':disagreements,
        'unique_disagreement_id_dimension_count':len({(r['id'],r['dimension']) for r in disagreements}),
        'relative_to_AI_reference_only':True,'human_adjudication_claim':False,'labels_changed':False,
        'zero_support_note':'A zero class denominator can leave P/R/F1 or kappa undefined even when paired labels agree. Undefined is not a passing value and is not repaired by inventing positive labels.',
        'source_sha256':{str(p):sha(p) for p in [*sources,Path(binding['rule']['inputs']),Path(binding['rule']['rules']),Path(binding['llm']['path']),Path(binding['references']),Path(binding['metadata']),OUT/'指标诊断表.json']}}
    dump(OUT/'指标诊断弱项与逐例原文.json',audit)
    assert source_hashes=={str(p):sha(p) for p in sources}
    print(json.dumps({'main_status':structured['main1057']['status'],'main_summary':structured['main1057']['summary'],
        'main_weak_comparisons':len(weak_support),'raw_disagreement_rows':len(disagreements),
        'main_authoring_gate':structured['main1057']['authoring_gate']},ensure_ascii=False))


if __name__=='__main__':main()
