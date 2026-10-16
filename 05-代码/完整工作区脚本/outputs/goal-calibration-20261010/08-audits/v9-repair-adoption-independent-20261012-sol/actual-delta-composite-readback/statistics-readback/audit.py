"""Independent arithmetic readback only. No classifier is imported or called."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
from datetime import datetime, timezone
import csv, hashlib, json, math, posixpath, re, traceback, zipfile
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
G = OUT.parents[3]
STATS = G / '07-statistics/current-v9-compatible-native2624-diagnostics-root'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
NAMES = {'S':'安全性', 'E':'有效性', 'Ec':'经济性', 'I':'创新性', 'F':'公平性'}
INPUTS = {}
CHECKS = []
MISMATCHES = []

def now():
    return datetime.now(timezone.utc).isoformat()

def bind(path):
    p = Path(path).resolve()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024 * 1024), b''):
            h.update(b)
    return {'path':str(p), 'bytes':p.stat().st_size, 'sha256':h.hexdigest()}

def register(path, expected=None):
    key = str(Path(path).resolve())
    current = INPUTS.get(key)
    if current is None:
        current = bind(key)
        INPUTS[key] = current
    if expected is not None:
        assert all(current[k] == expected[k] for k in ('path', 'bytes', 'sha256')), (current, expected)
    return Path(key)

def load(path):
    return json.loads(register(path).read_bytes())

def verify_seal(path, groups=('files',)):
    seal = load(path)
    counts = {}
    for group in groups:
        members = seal[group]
        assert isinstance(members, list) and members
        for item in members:
            register(item['path'], item)
        counts[group] = len(members)
    CHECKS.append({'check':'sealed member hashes', 'seal':str(Path(path).resolve()), 'member_groups':counts})
    return seal

def save(name, obj):
    with (OUT / name).open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')

def binary(v):
    return type(v) is int and v in (0, 1)

def read_records(path, decision_field):
    rows = {}
    for line in register(path).open(encoding='utf8'):
        row = json.loads(line)
        sid = row['id']
        assert sid not in rows and set(row['labels']) == set(DIMS)
        assert set(row[decision_field]) == set(DIMS)
        assert all((v is None or binary(v)) and row[decision_field][d]['value'] == v
                   for d, v in row['labels'].items())
        if 'implementation_errors' in row:
            assert not row['implementation_errors']
        rows[sid] = row
    return rows

def div(n, d):
    return None if d == 0 else float(Fraction(n, d))

def arithmetic(pairs):
    assert all(binary(a) and binary(b) for a, b in pairs)
    c = Counter(pairs)
    tp, fp, fn, tn = c[(1,1)], c[(0,1)], c[(1,0)], c[(0,0)]
    n = tp + fp + fn + tn
    rp, rn, pp, pn = tp + fn, tn + fp, tp + fp, tn + fn
    # Algebraic count formula avoids reproducing the production floating-point kappa expression.
    kd = pp * rn + rp * pn
    return {'N':n, 'TP':tp, 'FP':fp, 'FN':fn, 'TN':tn,
            'reference_positive_N':rp, 'reference_negative_N':rn,
            'prediction_positive_N':pp, 'prediction_negative_N':pn,
            'Po':div(tp+tn,n), 'Pe':div(rp*pp+rn*pn,n*n),
            'kappa':div(2*(tp*tn-fp*fn),kd), 'Precision':div(tp,pp),
            'Recall':div(tp,rp), 'F1':div(2*tp,2*tp+fp+fn),
            'positive_agreement':div(2*tp,2*tp+fp+fn),
            'negative_agreement':div(2*tn,2*tn+fp+fn),
            'specificity':div(tn,rn), 'NPV':div(tn,pn)}

def denominators(m):
    tp, fp, fn, tn = (m[x] for x in ('TP','FP','FN','TN'))
    return {'kappa':(tp+fp)*(tn+fp)+(tp+fn)*(tn+fn),
            'Precision':tp+fp, 'Recall':tp+fn, 'F1':2*tp+fp+fn,
            'Po':m['N'], 'Pe':m['N']**2, 'positive_agreement':2*tp+fp+fn,
            'negative_agreement':2*tn+fp+fn, 'specificity':tn+fp, 'NPV':tn+fn}

def xlsx(path):
    ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    rns = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'
    with zipfile.ZipFile(register(path)) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(si.itertext()) for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',ns)]
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rel_id = next(s.attrib['{'+rns+'}id'] for s in wb.findall('s:sheets/s:sheet',ns) if s.attrib['name']=='编码表')
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
        target = next(r.attrib['Target'] for r in rels if r.attrib['Id']==rel_id)
        target = target.lstrip('/') if target.startswith('/') else posixpath.normpath(posixpath.join('xl',target))
        grid, formulas = {}, set()
        for row in ET.fromstring(z.read(target)).findall('s:sheetData/s:row',ns):
            cells = {}
            for cell in row.findall('s:c',ns):
                addr = cell.attrib['r']; col = re.match(r'[A-Z]+',addr).group()
                kind = cell.attrib.get('t','n'); value = cell.find('s:v',ns)
                raw = None if value is None else value.text
                if kind == 'inlineStr':
                    val = ''.join(cell.find('s:is',ns).itertext())
                elif kind == 's':
                    val = strings[int(raw)]
                elif kind == 'n' and raw is not None:
                    val = int(raw) if re.fullmatch(r'-?\d+',raw) else float(raw)
                else:
                    val = raw
                if cell.find('s:f',ns) is not None:
                    formulas.add(addr)
                cells[col] = val
            grid[int(row.attrib['r'])] = cells
        cols = {value:col for col,value in grid[6].items()}
        result, locations = {}, {}
        for index, cells in sorted(grid.items()):
            if index < 7 or cells.get(cols['条款编号']) is None:
                continue
            val = cells[cols['条款编号']]
            sid = f'RECODE25-{val:05d}' if type(val) is int else str(val).strip()
            if not sid.startswith('RECODE25-'):
                sid = 'RECODE25-'+sid.zfill(5)
            d = str(cells[cols['维度']]).split()[0]
            v = cells[cols['编码值']]
            assert d in DIMS and binary(v)
            key = sid, d
            assert key not in result and cols['编码值']+str(index) not in formulas
            result[key] = v
            locations[key] = {'row':index,'cell':cols['编码值']+str(index)}
        assert len(result)==385 and len({sid for sid,d in result})==77
        assert Counter(d for sid,d in result)==Counter({d:77 for d in DIMS})
        return result, locations

def equivalent(expected, actual, path):
    if type(expected) is float:
        ok = type(actual) in (int,float) and math.isclose(expected,actual,rel_tol=1e-12,abs_tol=1e-12)
    else:
        ok = expected == actual
    if not ok:
        MISMATCHES.append({'path':path,'independent_expected':expected,'actual':actual})
    return ok

def compare(expected, actual, path):
    if isinstance(expected, dict):
        if not isinstance(actual, dict):
            equivalent(expected,actual,path); return
        for key,val in expected.items():
            if key not in actual:
                MISMATCHES.append({'path':path+'/'+str(key),'missing_actual_field':True})
            else:
                compare(val,actual[key],path+'/'+str(key))
    elif isinstance(expected,list):
        equivalent(expected,actual,path)
    else:
        equivalent(expected,actual,path)

def directed(pred, ref):
    result = {}
    for d in DIMS:
        slots = [(sid,val) for (sid,dim),val in ref.items() if dim==d]
        missing = [{'id':sid,'reference':v} for sid,v in slots if sid not in pred]
        null = [{'id':sid,'reference':v} for sid,v in slots if sid in pred and pred[sid]['labels'][d] is None]
        pairs = [(v,pred[sid]['labels'][d]) for sid,v in slots if sid in pred and pred[sid]['labels'][d] is not None]
        m = arithmetic(pairs)
        m.update(allocated_N=len(slots),allocated_reference_positive_N=sum(v for sid,v in slots),
                 allocated_reference_negative_N=sum(v==0 for sid,v in slots),
                 missing_N=len(missing),lawful_null_N=len(null),binary_coverage=div(len(pairs),len(slots)),
                 excluded_positive_N=sum(r['reference'] for r in missing+null),
                 excluded_negative_N=sum(r['reference']==0 for r in missing+null),missing=missing,lawful_null=null,
                 conditional_core_targets_passed=all(m[k] is not None and m[k]>=.8 for k in ('kappa','Precision','Recall','F1')),
                 formal_validation_complete=False)
        result[d] = m
    return result

def main():
    assert not (OUT/'report.json').exists()
    pre=load(OUT/'pre-execution-audit-freeze.json');register(__file__,pre['auditor'])
    verify_seal(STATS/'seal.json');actual=load(STATS/'metrics.json')
    for k in ('rule_execution','rule_seal','native_snapshot_seal','old_v5_predictions','calculator'):register(actual[k]['path'],actual[k])
    for s in actual['reference_bindings']:register(s['path'],s)
    prior_metrics=load(G/'07-statistics/current-v8-composite-machine-diagnostics-20261011-root/metrics.json')
    assert actual['reference_bindings']==prior_metrics['reference_bindings']
    status=load(actual['rule_execution']['path']);composite=Path(actual['rule_execution']['path']).parent;verify_seal(actual['rule_seal']['path'])
    assert status['actual_record_N']==4481 and status['actual_dimension_N']==22405 and status['actual_v9_affected_inference_record_N']==3904 and status['inherited_compatible_parent_record_N']==577 and status['all4481_actually_inferred_under_v9']is False
    for k in ('impact_closure_plan','adoption','original_input_lineage','merger'):register(status[k]['path'],status[k])
    native_dir=Path(actual['native_snapshot_seal']['path']).parent;assert native_dir.name=='original-whole-batch-native-snapshot-20261012T0120-root';verify_seal(native_dir/'seal.json');coverage=load(native_dir/'coverage.json')
    assert coverage['selected_record_N']==2624 and coverage['selected_batch_N']==338 and coverage['pointer_quote_issue_N']==0 and coverage['thin35_included']is False
    assert coverage['actual_selected_modes']['original_record_N']==2132 and coverage['actual_selected_modes']['transport_recovery_record_N']==492
    for k in ('original_manifest','recovery_manifest','collector'):register(coverage[k]['path'],coverage[k])
    rule=read_records(composite/'predictions.jsonl','decisions');old=read_records(actual['old_v5_predictions']['path'],'decisions');native=read_records(native_dir/'selected-records.jsonl','dimensions');prior_rule=read_records(G/'06-coding/rule-full4481-v8-delta-merged-root/predictions.jsonl','decisions')
    assert len(rule)==len(old)==len(prior_rule)==4481 and set(rule)==set(old)==set(prior_rule)and len(native)==2624 and set(native)<=set(rule)
    ra,la=xlsx(actual['reference_bindings'][0]['path']);rb,lb=xlsx(actual['reference_bindings'][1]['path']);assert ra==rb and len(ra)==len(rb)==385
    assert all(rule[s]['labels'][d]==prior_rule[s]['labels'][d]for s,d in ra),'77 original machine values must stay unchanged'
    ref_results={side:{'rule':directed(rule,ref),'native':directed(native,ref)}for side,ref in {'A':ra,'B':rb}.items()}
    for side,res in ref_results.items():compare(res['rule'],actual['development77_rule_metrics'],side+'/rule');compare(res['native'],actual['development77_native_metrics'],side+'/native')
    matched={};matched_ids={}
    for d in DIMS:
        keys=[k for k in ra if k[1]==d and k[0]in native and rule[k[0]]['labels'][d]is not None and native[k[0]]['labels'][d]is not None];matched_ids[d]=[k[0]for k in keys]
        matched[d]={'matched_binary_N':len(keys),'rules':arithmetic([(ra[k],rule[k[0]]['labels'][d])for k in keys]),'native':arithmetic([(ra[k],native[k[0]]['labels'][d])for k in keys])}
    compare(matched,actual['development77_same_binary_slots'],'same_binary_slots')
    transitions={d:Counter()for d in DIMS};changes=[]
    for sid,row in rule.items():
        for d in DIMS:
            a,b=old[sid]['labels'][d],row['labels'][d];transitions[d][f'{a}_to_{b}']+=1
            if a!=b:changes.append({'id':sid,'dimension':d,'old':a,'new':b,'new_decision':row['decisions'][d],'old_decision':old[sid]['decisions'][d]})
    root_changes=[json.loads(x)for x in register(STATS/'old-v5-to-current-composite-label-changes.jsonl').open()];compare(changes,root_changes,'v5_changes');compare(len(changes),actual['old_v5_to_current_composite_changed_label_N'],'v5_changed_N');compare({d:dict(c)for d,c in transitions.items()},actual['old_v5_to_current_composite_transitions'],'v5_transitions');assert len(changes)==260
    counts={d:{'positive_N':sum(r['labels'][d]==1for r in rule.values()),'negative_N':sum(r['labels'][d]==0for r in rule.values()),'lawful_null_N':sum(r['labels'][d]is None for r in rule.values())}for d in DIMS};compare(counts,actual['rules_counts'],'rule_counts');compare(counts,status['counts'],'composite_counts');null_N=sum(c['lawful_null_N']for c in counts.values());assert null_N==241
    compare(null_N,actual['rules_lawful_null_label_N'],'rule_null_N')
    native_counts={d:{'positive_N':sum(r['labels'][d]==1for r in native.values()),'negative_N':sum(r['labels'][d]==0for r in native.values()),'lawful_null_N':sum(r['labels'][d]is None for r in native.values()),'missing_N':4481-len(native)}for d in DIMS};compare(native_counts,coverage['per_dimension'],'native_counts')
    native_null=sum(c['lawful_null_N']for c in native_counts.values());assert native_null==39
    expected_cov={'allocated_record_N':4481,'selected_record_N':2624,'missing_record_N':1857,'binary_label_N':13120-native_null,'lawful_null_label_N':native_null,'missing_label_N':9285,'record_output_coverage':div(2624,4481),'complete_binary_record_N':sum(all(binary(v)for v in r['labels'].values())for r in native.values()),'full_corpus_complete':False,'thin35_included':False,'formal_validation_complete':False}
    compare(expected_cov,coverage,'coverage');compare(coverage,actual['native_coverage'],'actual_native_coverage')
    agreements={};pair_exclusions={};disagreements=[];pair_directional_diagnostic={}
    for d in DIMS:
        pairs=[(rule[s]['labels'][d],native[s]['labels'][d])for s in native if rule[s]['labels'][d]is not None and native[s]['labels'][d]is not None];m=arithmetic(pairs);pair_directional_diagnostic[d]=m
        agreements[d]={'binary_pair_N':m['N'],'native_output_N':2624,'native_missing_N':1857,'both_1':m['TP'],'rule0_native1':m['FP'],'rule1_native0':m['FN'],'both_0':m['TN'],'Po':m['Po'],'Pe':m['Pe'],'kappa':m['kappa'],'positive_agreement':m['positive_agreement'],'negative_agreement':m['negative_agreement'],'is_accuracy':False}
        pair_exclusions[d]={'allocated_N':4481,'native_missing_N':1857,'both_binary_N':len(pairs),'rule_only_null_N':sum(rule[s]['labels'][d]is None and native[s]['labels'][d]is not None for s in native),'native_only_null_N':sum(rule[s]['labels'][d]is not None and native[s]['labels'][d]is None for s in native),'both_null_N':sum(rule[s]['labels'][d]is None and native[s]['labels'][d]is None for s in native),'binary_coverage_of_allocated':div(len(pairs),4481),'binary_coverage_of_native_outputs':div(len(pairs),2624),'metric_denominators':denominators(m)}
        assert sum(pair_exclusions[d][k]for k in ('native_missing_N','both_binary_N','rule_only_null_N','native_only_null_N','both_null_N'))==4481
        for sid in native:
            rv,nv=rule[sid]['labels'][d],native[sid]['labels'][d]
            if rv!=nv:disagreements.append({'id':sid,'dimension':d,'rule':rv,'native':nv,'rule_decision':rule[sid]['decisions'][d],'native_decision':native[sid]['dimensions'][d],'native_first':native[sid]['first'],'packet':native[sid]['packet'],'not_adjudicated_truth':True})
    compare(agreements,actual['machine_pair_agreement_not_accuracy'],'machine_pair');compare(disagreements,[json.loads(x)for x in register(STATS/'machine-pair-disagreements.jsonl').open()],'disagreements');compare(len(disagreements),actual['machine_disagreement_including_null_N'],'disagreement_N');assert len(disagreements)==696
    with register(STATS/'development77-comparison.csv').open(encoding='utf-8-sig',newline='')as f:csv_rows=list(csv.DictReader(f))
    expected_csv=[]
    for sid,d in sorted(ra):
        nv=native[sid]['labels'][d]if sid in native else None;expected_csv.append({'id':sid,'dimension':d,'reference_A':str(ra[sid,d]),'reference_B':str(rb[sid,d]),'rules_current_compatible_composite':''if rule[sid]['labels'][d]is None else str(rule[sid]['labels'][d]),'native_original_whole_batch':''if nv is None else str(nv),'native_state':'missing_record'if sid not in native else'lawful_null'if nv is None else'binary'})
    compare(expected_csv,csv_rows,'csv');assert len(csv_rows)==385
    text=register(STATS/'结果说明.md').read_text()
    for label,ms in [('规则',ref_results['A']['rule']),('LLM完整整批快照',ref_results['A']['native'])]:
        for d,m in ms.items():
            fmt=lambda v:'NA'if v is None else f'{v:.3f}';line=f"|{label}|{d}|{m['N']}/77|{m['lawful_null_N']}|{m['missing_N']}|{fmt(m['kappa'])}|{fmt(m['Precision'])}|{fmt(m['Recall'])}|{fmt(m['F1'])}|";equivalent(True,line in text,'markdown/'+label+'/'+d)
    for phrase in ('2624/4481','复用结果不声称为新版本下重新运行','不能作为正确率','77条曾用于规则开发','不能替代独立检验'):equivalent(True,phrase in text,'boundary/'+phrase)
    compare({'rules_full_corpus_completed':True,'native_full_corpus_completed':False,'rules_allocated_N':4481,'rules_technical_failure_N':0,'formal_validation_complete':False,'population_CI_computed_from_development':False,'paper_writing_gate_open':False},actual,'formal_boundaries')
    for s in INPUTS.values():assert bind(s['path'])==s
    report={'status':'independent_v9_statistics_readback_passed'if not MISMATCHES else'independent_v9_statistics_readback_found_mismatches','at_utc':now(),'mismatch_N':len(MISMATCHES),'mismatches':MISMATCHES,'dimension_names':NAMES,'A_B_original_385_reference_values_unchanged':True,'rule_development77_original_385_values_unchanged_v8_to_v9':True,'separate_A_B_metrics':ref_results,'development77_metric_denominators':{s:{method:{d:denominators(m)for d,m in dims.items()}for method,dims in res.items()}for s,res in ref_results.items()},'same_binary_slots':matched,'same_binary_ids':matched_ids,'rules_counts':counts,'native_counts':native_counts,'native_coverage':expected_cov,'original2132_recovery492_modes':coverage['actual_selected_modes'],'machine_pair_agreement_not_accuracy':agreements,'pair_denominator_and_null_decomposition':pair_exclusions,'machine_directional_diagnostic_rule_as_reference_not_gold':pair_directional_diagnostic,'v5_to_current_change_N':len(changes),'v5_to_current_changed_record_N':len({c['id']for c in changes}),'v5_transitions':{d:dict(c)for d,c in transitions.items()},'disagreement_including_null_N':len(disagreements),'sealed_inputs_N':len(INPUTS),'all_inputs_unchanged':True,'classifier_runs':0,'new_human200_answers_or_semantic_originals_read':False,'two_machines_are_not_gold':True,'77_is_disclosed_development_not_formal_independent_validation':True,'full_native_complete':False,'formal_validation_complete':False,'paper_writing_gate_open':False}
    save('report.json',report)
    with(OUT/'report.md').open('x',encoding='utf8')as f:f.write(f'独立统计读回差异{len(MISMATCHES)}项。规则4481条/22405槽，待定241；LLM封印快照2624/4481条、338批，其中原整批2132与运输恢复492，缺失1857条、待定39。\n\nA/B原385值和规则开发77原385值均未改变；规则77逐维核心辅助指标均1，LLM每维53个可比值，缺失24，未补待定或缺失。全四格、κ/P/R/F1/Po及辅助指标、同一可判集合、覆盖分母、v5变化260槽与两机器696项含null分歧均与ROOT落地统计相同。F1直接按2TP/(2TP+FP+FN)，零分母为NA；机器对比只表示相似，方向性以规则为参照也不成为准确率。\n\n这些仅为已暴露开发和机器间诊断；LLM仍partial，正式独立验收、总体CI和论文gate均false。没有新human200答案或正文语义审查，没有重新分类或标签修订。\n')
    save('input-bindings.json',{'inputs':list(INPUTS.values()),'exact_before_after':True});save('seal.json',{'files':[bind(p)for p in sorted(OUT.iterdir())if p.is_file()and p.name!='seal.json'],'self_excluded':True,'classifier_runs':0,'formal_validation_complete':False})
    print(json.dumps({'mismatch_N':len(MISMATCHES),'seal':bind(OUT/'seal.json'),'report':bind(OUT/'report.json'),'native_development':ref_results['A']['native']},ensure_ascii=False));return 0 if not MISMATCHES else 2
if __name__=='__main__':
    try:raise SystemExit(main())
    except Exception as exc:
        save('attempt-failure.json',{'error_type':type(exc).__name__,'error':str(exc),'traceback':traceback.format_exc(),'classifier_runs':0});raise
