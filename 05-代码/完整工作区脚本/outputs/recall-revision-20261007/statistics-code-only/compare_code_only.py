"""Independent count check and paired before/after code-effect diagnostic.

No label changes, source edits, bootstrap, or independent-validation claims.
"""
from pathlib import Path
from collections import Counter
from fractions import Fraction
import csv
import hashlib
import json

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
OUT = Path(__file__).resolve().parent
BASE = ROOT / 'outputs/final-three-department-20261007'
DIMS = ('S', 'E', 'Ec', 'I', 'F')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def jsonl(path):
    rows = [json.loads(s) for s in path.read_text().splitlines() if s.strip()]
    result = {r['id']: r for r in rows}
    assert len(result) == len(rows)
    return result


def estimates(cells):
    tp, fp, fn, tn = cells
    n = sum(cells)
    assert n > 0
    po = Fraction(tp + tn, n)
    pe = Fraction((tp+fp)*(tp+fn)+(fn+tn)*(fp+tn), n*n)
    ratio = lambda a, b: float(Fraction(a, b)) if b else None
    return {
        'kappa': float((po-pe)/(1-pe)) if pe != 1 else None,
        'agreement': float(po),
        'precision': ratio(tp, tp+fp), 'recall': ratio(tp, tp+fn),
        'f1': ratio(2*tp, 2*tp+fp+fn),
        'left_positive_rate': ratio(tp+fp, n),
        'right_positive_rate': ratio(tp+fn, n),
    }


def main():
    paths = {
        'baseline_statistics': BASE / '三部门编码指标.json',
        'candidate_statistics': OUT / '三部门编码指标.json',
        'candidate_rules': OUT / 'rules-v31-code-only-frozen.jsonl',
        'baseline_rules': BASE / 'rules-v30/all_predictions.jsonl',
        'llm_unchanged_v29': BASE / 'llm-v29/production-25-v29/all_predictions.jsonl',
        'inputs': BASE / 'rules-v30/rule_inputs_v30_shared.jsonl',
        'main_references': ROOT / 'outputs/autocode-v25-20260927/current_1268_references.jsonl',
        'metadata': ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json',
        'supplement_mapping': ROOT / 'outputs/autocode-v25-20260927/H427/admin_mapping.json',
    }
    before = {str(p): sha(p) for p in paths.values()}
    old, new = [json.loads(paths[x].read_text()) for x in ('baseline_statistics', 'candidate_statistics')]
    inputs = jsonl(paths['inputs'])
    meta = {Path(r['original_file']).stem:r['analysis_group'] for r in json.loads(paths['metadata'].read_text())['rows']}
    group = {rid:meta[r['input']['original_file_stem']] for rid,r in inputs.items()}
    preds = {key:jsonl(paths[name]) for key,name in (
        ('rules_v30','baseline_rules'),('rules_v31_code_only','candidate_rules'),('llm_gpt56_sol_v29','llm_unchanged_v29'))}
    labels = {key:{rid:r.get('prediction', r)['labels'] for rid,r in rows.items()} for key,rows in preds.items()}
    assert len(inputs) == 4924 and all(set(rows) == set(inputs) for rows in preds.values())
    assert sha(paths['candidate_rules']) == 'be8da51fe8b3dfb887dc13664543cf13ef6e02d75a7086e10c7ccf59948a7b1a'
    for key in ('rules_v30', 'rules_v31_code_only'):
        for rid, r in preds[key].items():
            assert r['prediction']['unit_text_sha256'] == hashlib.sha256(inputs[rid]['input']['unit_text'].encode()).hexdigest()
    frames = {'main1057':{}, 'supplement_H411':{}}
    refs = jsonl(paths['main_references'])
    assert len(refs) == 1268
    for rid,r in refs.items():
        if group[rid] in ('NMPA', 'NHSA', 'NHC'):
            frames['main1057'][rid] = {c:r['original_references'][c]['labels'] for c in ('A', 'C')}
    mapping = {r['id']:r for r in json.loads(paths['supplement_mapping'].read_text())}
    h = {}
    hdir = paths['supplement_mapping'].parent
    for coder in ('A', 'C'):
        h[coder] = {}
        for n in range(1,44):
            path = hdir / f'agent-{coder}/结果-{n:02d}.json'
            packet = hdir / f'agent-{coder}/材料-{n:02d}.json'
            content = json.loads(path.read_text())
            assert content['input_packet_sha256'] == sha(packet)
            before[str(path)], before[str(packet)] = sha(path), sha(packet)
            for r in content['rows']:
                assert r['id'] not in h[coder]
                h[coder][r['id']] = r['labels']
        assert len(h[coder]) == 427
    for bid, mapping_row in mapping.items():
        rid = mapping_row['rerun_id']
        assert mapping_row['text_sha256'] == hashlib.sha256(inputs[rid]['input']['unit_text'].encode()).hexdigest()
        if group[rid] in ('NMPA','NHSA','NHC'):
            frames['supplement_H411'][rid] = {c:h[c][bid] for c in ('A','C')}
    assert len(frames['main1057']) == 1057 and len(frames['supplement_H411']) == 411
    assert not set(frames['main1057']) & set(frames['supplement_H411'])
    verified_records = 0
    for result in (old,new):
        for r in result['records']:
            counts = Counter()
            pending = 0
            eligible = []
            for rid, reference in frames[r['frame']].items():
                if r['group'] != 'ALL' and group[rid] != r['group']:
                    continue
                a = reference['A'][r['dimension']] if r['method'] == 'A_C' else labels[r['method']][rid][r['dimension']]
                b = reference[r['reference']][r['dimension']]
                if type(a) is int and a in (0,1) and type(b) is int and b in (0,1):
                    counts[(a,b)] += 1
                    eligible.append(rid)
                else:
                    pending += 1
            cells = [counts[(1,1)],counts[(1,0)],counts[(0,1)],counts[(0,0)]]
            assert sum(cells) == r['n'] and pending == r['excluded_n']
            assert r['eligible_ids_sha256'] == hashlib.sha256('\n'.join(sorted(eligible)).encode()).hexdigest()
            assert list((r['cross_tab'] if r['method'] == 'A_C' else r['confusion']).values()) == cells
            direct = estimates(cells)
            for name, entry in r['metrics'].items():
                reported = entry['estimate']
                assert (direct[name] is None and reported is None) or (reported is not None and abs(direct[name]-reported) < 1e-12), (r,name,direct)
            verified_records += 1
    old_index = {(r['frame'],r['group'],r['dimension'],r['method'],r['reference']):r for r in old['records']}
    comparisons = []
    invariant_records = []
    for r in new['records']:
        old_method = 'rules_v30' if r['method'] == 'rules_v31_code_only' else r['method']
        a = old_index[r['frame'],r['group'],r['dimension'],old_method,r['reference']]
        for name in ('n','frame_n','excluded_n','right_positive_n','exclusions','eligible_ids_sha256'):
            assert a[name] == r[name]
        if r['method'] == 'A_C':
            assert a['cross_tab'] == r['cross_tab']
            invariant_records.append({'frame':r['frame'],'group':r['group'],'dimension':r['dimension'],'type':'A_C','unchanged':True})
            continue
        row = {k:r[k] for k in ('frame','group','dimension','reference','n','frame_n','excluded_n','right_positive_n','source_clusters')}
        row['method'] = 'rules' if r['method'] == 'rules_v31_code_only' else 'llm_unchanged_v29'
        row['reference_positive_support_n'] = r['right_positive_n']
        row['old_confusion'], row['new_confusion'] = a['confusion'], r['confusion']
        for name in ('precision','recall','f1','kappa','agreement'):
            x,y = a['metrics'][name]['estimate'],r['metrics'][name]['estimate']
            row[f'old_{name}'], row[f'new_{name}'] = x,y
            row[f'delta_{name}'] = None if x is None or y is None else y-x
        row['changed_confusion'] = a['confusion'] != r['confusion']
        if row['method'] == 'llm_unchanged_v29':
            assert not row['changed_confusion']
        comparisons.append(row)
    changed_ids = []
    for rid in inputs:
        for d in DIMS:
            a,b = labels['rules_v30'][rid][d], labels['rules_v31_code_only'][rid][d]
            if a != b:
                membership = next((f for f,rows in frames.items() if rid in rows),'not_in_reference_frames')
                changed_ids.append({'id':rid,'group':group[rid],'dimension':d,'old':a,'new':b,'frame':membership,
                                    'unit_text':inputs[rid]['input']['unit_text'],
                                    'A':frames[membership][rid]['A'][d] if membership in frames else None,
                                    'C':frames[membership][rid]['C'][d] if membership in frames else None})
    assert len(changed_ids) == 22
    def diagnostic_counts(rows):
        return {m: {'defined':sum(r[f'new_{m}'] is not None for r in rows),
                    'old_below_0_8':sum(r[f'old_{m}'] is not None and r[f'old_{m}'] < .8 for r in rows),
                    'new_below_0_8':sum(r[f'new_{m}'] is not None and r[f'new_{m}'] < .8 for r in rows)}
                for m in ('precision','recall','f1','kappa')}
    counts = {f:{g:diagnostic_counts([r for r in comparisons if r['frame']==f and (r['group']=='ALL' if g=='overall20' else r['group']!='ALL')]) for g in ('overall20','department60')} for f in frames}
    data = {'status':'DEVELOPMENT_CODE_ONLY_DIAGNOSTIC_NOT_FINAL_VALIDATION',
            'reference_identity':'Unchanged first AI A/C submissions; not actual independent human labels',
            'effect_isolation':'Frozen old inputs, frozen old v29 LLM, same A/C labels and exact common binary subsets. Only rule code changed.',
            'intervals':'Not recomputed in this diagnostic. All ci95 fields in candidate statistics are null; bootstrap repetitions=0.',
            'threshold_note':'0.8 counts are descriptive project diagnostics; not a universal publication threshold and do not authorize label changes.',
            'independent_verification':{'old_and_new_records':verified_records,'method':'Raw first A/C JSON submissions and actual prediction rows reconstructed independently; exact Fraction Cohen kappa and confusion formulas; all point estimates agree within 1e-12.', 'A_C_invariant_checks':invariant_records},
            'main_overall_comparisons_n':sum(r['frame']=='main1057' and r['group']=='ALL' for r in comparisons),
            'main_department_comparisons_n':sum(r['frame']=='main1057' and r['group']!='ALL' for r in comparisons),
            'metric_diagnostic_counts':counts,'changed_rule_id_dimensions':changed_ids,
            'comparisons':comparisons,'source_sha256':before}
    assert data['main_overall_comparisons_n'] == 20 and data['main_department_comparisons_n'] == 60
    assert before == {p:sha(Path(p)) for p in before}, 'Read-only sources changed during calculation'
    (OUT/'规则代码效应-逐项对比与独立核验.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    for frame,filename in (('main1057','主样本20与60项-代码效应对比.csv'),('supplement_H411','H411-20与60项-代码效应对比.csv')):
        flat=[]
        for r in comparisons:
            if r['frame'] != frame:
                continue
            row = {k:v for k,v in r.items() if k not in ('old_confusion','new_confusion')}
            for phase in ('old','new'):
                row.update({f'{phase}_{k}':v for k,v in r[f'{phase}_confusion'].items()})
            flat.append(row)
        with (OUT/filename).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(flat[0]));writer.writeheader();writer.writerows(flat)
    def fmt(v):
        return '未定义' if v is None else f'{v:.6f}'
    lines=['# 冻结旧输入的规则代码效应诊断','',
        '这份结果只比较规则代码修改的效果。全部原文、上下文、A/C 首次 AI 参照及 LLM v29 均保持不变。它不是最终验证，也不是新增真人独立验证。候选输出冻结哈希为 `be8da51fe8b3dfb887dc13664543cf13ef6e02d75a7086e10c7ccf59948a7b1a`。', '',
        '共独立重建并核对旧、新 400 条比较记录。主样本完整列出总体 20 项和分部门 60 项；H411 分列对应 80 项。分母为每一维度、方法与参照真实共同可判定条目；未将“待定”改成 0。支持数是参照中 1 的数量。此阶段不重算置信区间。', '',
        '代码导致 22 个 ID×维度改变（I 0→1 共 5；F 0→1 共 1；F 1→0 共 16）。实际指标变化只集中于 I 和 F，S、E、Ec 与旧版一致，LLM 全部保持一致。','',
        '|范围|维度|参照|有效 n / 参照阳性数|精确率 旧→新|召回率 旧→新|F1 旧→新|κ 旧→新|',
        '|---|---|---|---|---|---|---|---|']
    for r in comparisons:
        if r['frame']=='main1057' and r['method']=='rules' and r['changed_confusion']:
            lines.append('|'+ '|'.join([r['group'],r['dimension'],r['reference'],f"{r['n']} / {r['reference_positive_support_n']}", *[f"{fmt(r['old_'+m])}→{fmt(r['new_'+m])}" for m in ('precision','recall','f1','kappa')]])+'|')
    lines += ['',
        '创新性：NMPA 新增的具体研发和支持机制使总体召回提高约 9.7–10.0 个百分点，同时精确率下降约 2.3–2.8 个百分点。A、C 比较各新增 3 个 TP 和 1 个 FP；F1、κ均提高。', '',
        '公平性：这次修订同时移除了已覆盖药品的甲乙类、协议与常规管理身份等扩大解释，因此不能称作纯粹提升召回。NMPA 公平性漏识别减少，但 NHSA 公平性的参照召回下降，精确率提高。总体 F1、κ略有提高；NHSA 对 C 的 F1、κ略降。是否采用应依据统一定义和实际原文，不宜依据哪版指标更高决定。', '',
        '低于 0.8 的数量仅作开发诊断，不能代表“可发表/不可发表”的判定。', '',
        '完整表和支持数见同目录 CSV；正式补全上下文和新 LLM 全量运行完成后需另算最终指标，不可将本诊断冒充最终结果。','']
    (OUT/'规则代码效应诊断.md').write_text('\n'.join(lines))
    print(json.dumps({'verified_records':verified_records,'main_overall':20,'main_department':60,'changed_id_dimensions':len(changed_ids),'metric_diagnostic_counts':counts,'changed_main_comparisons':[r for r in comparisons if r['frame']=='main1057' and r['changed_confusion']]},ensure_ascii=False))


if __name__ == '__main__':
    main()
