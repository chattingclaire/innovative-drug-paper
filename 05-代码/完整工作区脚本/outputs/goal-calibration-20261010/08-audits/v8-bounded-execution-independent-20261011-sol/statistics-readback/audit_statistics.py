"""Independent arithmetic readback only. No classifier is imported or called."""
from pathlib import Path
from collections import Counter
from fractions import Fraction
from datetime import datetime, timezone
import csv, hashlib, json, math, posixpath, re, traceback, zipfile
import xml.etree.ElementTree as ET

OUT = Path(__file__).resolve().parent
G = OUT.parents[2]
STATS = G / '07-statistics/current-v8-composite-machine-diagnostics-20261011-root'
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
    assert not (OUT/'report.json').exists(), 'Never overwrite a completed independent audit'
    pre = load(OUT/'pre-execution-audit-freeze.json')
    register(__file__,pre['auditor'])
    verify_seal(STATS/'seal.json')
    actual = load(STATS/'metrics.json')
    for key in ('rule_execution','rule_seal','native_snapshot_seal','old_v5_predictions','calculator'):
        register(actual[key]['path'],actual[key])
    for b in actual['reference_bindings']:
        register(b['path'],b)
    composite = Path(actual['rule_execution']['path']).parent
    status = load(actual['rule_execution']['path'])
    merged_seal = verify_seal(actual['rule_seal']['path'])
    assert status['status']==merged_seal['status']=='complete_v8_compatible_composite_with_explicit_execution_origins'
    assert status['actual_record_N']==4481 and status['actual_dimension_N']==22405
    assert status['actual_v8_delta_inference_record_N']==7 and status['inherited_v7_record_N']==4474
    assert status['all4481_actually_inferred_under_v8'] is False
    assert merged_seal['all4481_actually_inferred_under_v8'] is False and merged_seal['no_new_inference_executed_by_merge']
    for b in merged_seal['ancestor_seals']:
        register(b['path'],b)
        verify_seal(b['path'],('output_files','implementation_files','material_bindings','control_inputs'))
    for key in ('impact_closure_plan','adoption','original_input_lineage','merger'):
        register(status[key]['path'],status[key])
    native_dir = Path(actual['native_snapshot_seal']['path']).parent
    assert native_dir.name=='original-whole-batch-native-snapshot-20261011T1537-root'
    verify_seal(native_dir/'seal.json')
    coverage = load(native_dir/'coverage.json')
    assert coverage['thin35_included'] is False and coverage['full_corpus_complete'] is False
    for key in ('original_manifest','recovery_manifest','collector'):
        register(coverage[key]['path'],coverage[key])
    old_dir = Path(actual['old_v5_predictions']['path']).parent
    verify_seal(old_dir/'seal.json',('output_files',))
    adapter = load(G/'08-audits/v8-composite-statistical-adapter-preparation-root.json')
    register(adapter['new_calculator']['path'],adapter['new_calculator'])
    register(adapter['verified_parent_calculator']['path'],adapter['verified_parent_calculator'])
    assert adapter['new_calculator']==actual['calculator'] and adapter['actual_classification_calls']==0
    rule = read_records(composite/'predictions.jsonl','decisions')
    old = read_records(actual['old_v5_predictions']['path'],'decisions')
    native = read_records(native_dir/'selected-records.jsonl','dimensions')
    assert len(rule)==len(old)==4481 and set(rule)==set(old) and set(native)<=set(rule)
    assert len(native)==coverage['selected_record_N']==2276
    ra,la = xlsx(actual['reference_bindings'][0]['path'])
    rb,lb = xlsx(actual['reference_bindings'][1]['path'])
    assert ra==rb
    selftests = {'false_positive_and_false_negative_F1':arithmetic([(0,1),(1,0)])['F1'],
                 'all_negative_kappa':arithmetic([(0,0)])['kappa'],
                 'all_negative_F1':arithmetic([(0,0)])['F1'],
                 'empty_Po':arithmetic([])['Po'],
                 'false_negative_no_prediction_Precision':arithmetic([(1,0)])['Precision'],
                 'false_negative_no_prediction_F1':arithmetic([(1,0)])['F1']}
    assert selftests=={'false_positive_and_false_negative_F1':0.,'all_negative_kappa':None,'all_negative_F1':None,
                       'empty_Po':None,'false_negative_no_prediction_Precision':None,'false_negative_no_prediction_F1':0.}
    refs = {'A':ra,'B':rb}
    ref_results = {side:{'rule':directed(rule,ref),'native':directed(native,ref)} for side,ref in refs.items()}
    for side,res in ref_results.items():
        compare(res['rule'],actual['development77_rule_metrics'],f'{side}/development77_rule_metrics')
        compare(res['native'],actual['development77_native_metrics'],f'{side}/development77_native_metrics')
    matched, matched_ids = {}, {}
    for d in DIMS:
        keys = [key for key in ra if key[1]==d and key[0] in native and
                rule[key[0]]['labels'][d] is not None and native[key[0]]['labels'][d] is not None]
        matched_ids[d] = [k[0] for k in keys]
        matched[d] = {'matched_binary_N':len(keys),
                      'rules':arithmetic([(ra[k],rule[k[0]]['labels'][d]) for k in keys]),
                      'native':arithmetic([(ra[k],native[k[0]]['labels'][d]) for k in keys])}
    compare(matched,actual['development77_same_binary_slots'],'development77_same_binary_slots')
    transitions = {d:Counter() for d in DIMS}; changes=[]
    for sid,row in rule.items():
        for d in DIMS:
            ov,nv = old[sid]['labels'][d], row['labels'][d]
            transitions[d][f'{ov}_to_{nv}']+=1
            if ov != nv:
                changes.append({'id':sid,'dimension':d,'old':ov,'new':nv,'new_decision':row['decisions'][d],
                                'old_decision':old[sid]['decisions'][d]})
    root_changes = [json.loads(line) for line in register(STATS/'old-v5-to-v8-composite-label-changes.jsonl').open(encoding='utf8')]
    compare(changes,root_changes,'old-v5-to-v8-composite-label-changes.jsonl')
    compare(len(changes),actual['old_v5_to_v8_composite_changed_label_N'],'old_v5_to_v8_composite_changed_label_N')
    compare({d:dict(c) for d,c in transitions.items()},actual['old_v5_to_v8_composite_transitions'],'old_v5_to_v8_composite_transitions')
    counts = {d:{'positive_N':sum(r['labels'][d]==1 for r in rule.values()),
                 'negative_N':sum(r['labels'][d]==0 for r in rule.values()),
                 'lawful_null_N':sum(r['labels'][d] is None for r in rule.values())} for d in DIMS}
    compare(counts,actual['rules_counts'],'rules_counts'); compare(counts,status['counts'],'composite/counts')
    null_N = sum(c['lawful_null_N'] for c in counts.values())
    compare(null_N,actual['rules_lawful_null_label_N'],'rules_lawful_null_label_N')
    assert all(sum(c.values())==4481 for c in counts.values()) and null_N==status['lawful_null_N']==238
    native_counts = {d:{'positive_N':sum(r['labels'][d]==1 for r in native.values()),
                        'negative_N':sum(r['labels'][d]==0 for r in native.values()),
                        'lawful_null_N':sum(r['labels'][d] is None for r in native.values()),
                        'missing_N':4481-len(native)} for d in DIMS}
    compare(native_counts,coverage['per_dimension'],'native_coverage/per_dimension')
    native_null_N = sum(c['lawful_null_N'] for c in native_counts.values())
    native_binary_N = len(native)*5-native_null_N
    coverage_expected = {'allocated_record_N':4481,'selected_record_N':len(native),'missing_record_N':4481-len(native),
                         'binary_label_N':native_binary_N,'lawful_null_label_N':native_null_N,
                         'missing_label_N':(4481-len(native))*5,'record_output_coverage':div(len(native),4481),
                         'complete_binary_record_N':sum(all(binary(v) for v in row['labels'].values()) for row in native.values()),
                         'full_corpus_complete':False,'thin35_included':False,'formal_validation_complete':False}
    compare(coverage_expected,coverage,'native_coverage');compare(coverage,actual['native_coverage'],'reported_native_coverage')
    agreements, pair_exclusions, disagreements = {}, {}, []
    for d in DIMS:
        pairs = [(rule[sid]['labels'][d],native[sid]['labels'][d]) for sid in native
                 if rule[sid]['labels'][d] is not None and native[sid]['labels'][d] is not None]
        m = arithmetic(pairs)
        agreements[d] = {'binary_pair_N':m['N'],'native_output_N':len(native),'native_missing_N':4481-len(native),
                         'both_1':m['TP'],'rule0_native1':m['FP'],'rule1_native0':m['FN'],'both_0':m['TN'],
                         'Po':m['Po'],'Pe':m['Pe'],'kappa':m['kappa'],
                         'positive_agreement':m['positive_agreement'],'negative_agreement':m['negative_agreement'],
                         'is_accuracy':False}
        pair_exclusions[d] = {'allocated_N':4481,'native_missing_N':4481-len(native),'both_binary_N':len(pairs),
                              'rule_only_null_N':sum(rule[s]['labels'][d] is None and native[s]['labels'][d] is not None for s in native),
                              'native_only_null_N':sum(rule[s]['labels'][d] is not None and native[s]['labels'][d] is None for s in native),
                              'both_null_N':sum(rule[s]['labels'][d] is None and native[s]['labels'][d] is None for s in native),
                              'binary_coverage_of_allocated':div(len(pairs),4481),'binary_coverage_of_native_outputs':div(len(pairs),len(native)),
                              'metric_denominators':denominators(m)}
        assert sum(pair_exclusions[d][k] for k in ('native_missing_N','both_binary_N','rule_only_null_N','native_only_null_N','both_null_N'))==4481
        for sid in native:
            rv,nv = rule[sid]['labels'][d], native[sid]['labels'][d]
            if rv != nv:
                disagreements.append({'id':sid,'dimension':d,'rule':rv,'native':nv,'rule_decision':rule[sid]['decisions'][d],
                                      'native_decision':native[sid]['dimensions'][d],'native_first':native[sid]['first'],
                                      'packet':native[sid]['packet'],'not_adjudicated_truth':True})
    compare(agreements,actual['machine_pair_agreement_not_accuracy'],'machine_pair_agreement_not_accuracy')
    root_disagreements = [json.loads(line) for line in register(STATS/'machine-pair-disagreements.jsonl').open(encoding='utf8')]
    compare(disagreements,root_disagreements,'machine-pair-disagreements.jsonl')
    compare(len(disagreements),actual['machine_disagreement_including_null_N'],'machine_disagreement_including_null_N')
    with register(STATS/'development77-comparison.csv').open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f);csv_rows=list(reader)
    expected_csv=[]
    for sid,d in sorted(ra):
        nv = native[sid]['labels'][d] if sid in native else None
        expected_csv.append({'id':sid,'dimension':d,'reference_A':str(ra[sid,d]),'reference_B':str(rb[sid,d]),
                             'rules_v8_compatible_composite':'' if rule[sid]['labels'][d] is None else str(rule[sid]['labels'][d]),
                             'native_original_whole_batch':'' if nv is None else str(nv),
                             'native_state':'missing_record' if sid not in native else 'lawful_null' if nv is None else 'binary'})
    compare(expected_csv,csv_rows,'development77-comparison.csv')
    markdown=register(STATS/'结果说明.md').read_text()
    for label,ms in [('规则',ref_results['A']['rule']),('LLM完整整批快照',ref_results['A']['native'])]:
        for d,m in ms.items():
            fmt=lambda x:'NA' if x is None else f'{x:.3f}'
            expected_line=f"|{label}|{d}|{m['N']}/77|{m['lawful_null_N']}|{m['missing_N']}|{fmt(m['kappa'])}|{fmt(m['Precision'])}|{fmt(m['Recall'])}|{fmt(m['F1'])}|"
            equivalent(True,expected_line in markdown,f'markdown/{label}/{d}')
    for text in ('4474条原v7','7条实际v8','未声称全4481重新运行v8','2276/4481','不能作为正确率','77条曾用于规则开发','不能替代独立检验'):
        equivalent(True,text in markdown,'markdown/boundary/'+text)
    compare({'rules_full_corpus_completed':True,'native_full_corpus_completed':False,'rules_allocated_N':4481,
             'rules_technical_failure_N':0,'formal_validation_complete':False,'population_CI_computed_from_development':False,
             'paper_writing_gate_open':False},actual,'report_boundaries')
    readback_failures=[]
    for b in list(INPUTS.values()):
        if bind(b['path'])!=b:
            readback_failures.append(b['path'])
    assert not readback_failures,readback_failures
    report = {'status':'independent_statistics_readback_passed' if not MISMATCHES else 'independent_statistics_readback_found_mismatches',
              'at_utc':now(),'actual_statistics':str(STATS),'mismatch_N':len(MISMATCHES),'mismatches':MISMATCHES,
              'boundaries':{'complete_rule_composite_record_N':4481,'actual_v8_delta_record_N':7,'inherited_v7_record_N':4474,
                            'all4481_actually_inferred_under_v8':False,'reference77_is_disclosed_development':True,
                            'formal_validation_complete':False,'population_CI_computed_from_development':False,
                            'paper_writing_gate_open':False,'native_partial_snapshot':True,'native_selected_record_N':2276,
                            'native_missing_record_N':2205,'thin35_included':False,'two_machines_are_not_gold_standards':True,
                            'new_classification_calls_N':0,'native_later_snapshots_read_N':0},
              'dimension_names':NAMES,'arithmetic_boundary_checks':selftests,'sealed_binding_checks':CHECKS,
              'input_binding_N':len(INPUTS),'all_inputs_byte_hash_unchanged_on_readback':True,
              'separate_A_B_metrics':ref_results,'development77_metric_denominators':{side:{method:{d:denominators(m) for d,m in ms.items()} for method,ms in res.items()} for side,res in ref_results.items()},
              'development77_same_binary_slots':matched,'development77_same_binary_record_ids':matched_ids,
              'rules_counts':counts,'rule_lawful_null_label_N':null_N,'native_counts':native_counts,
              'native_coverage_recomputed':coverage_expected,'machine_pair_agreement_not_accuracy':agreements,
              'machine_pair_exclusion_decomposition':pair_exclusions,'old_v5_to_v8_composite_changed_label_N':len(changes),
              'old_v5_to_v8_composite_changed_record_N':len({x['id'] for x in changes}),
              'old_v5_to_v8_composite_transitions':{d:dict(c) for d,c in transitions.items()},
              'machine_disagreement_including_null_N':len(disagreements),'development77_csv_actual_rows_N':len(csv_rows),
              'classification_correctness_or_new_gold_labels_created':False,
              'execution_origin_and_source_byte_closure_audit':'separately handled by parent execution-readback; this report verifies bindings and statistics only'}
    save('report.json',report)
    lines=[f"独立统计复算{'通过' if not MISMATCHES else '发现差异'}：落地指标、四格、NA、覆盖分母、同一可判集合比较、变化及分歧记录均独立核对；差异 {len(MISMATCHES)} 项。",'',
           '规则结果完整覆盖4481条，但执行来源是4474条继承v7与7条实际v8局部运行。LLM只使用1537封存快照：2276/4481条，缺失2205条，原生待定39项；未读取后续快照。', '',
           '|方法|维度|可判N/77|待定|缺失|TP/FP/FN/TN|κ|精确率|召回率|F1|','|---|---|---:|---:|---:|---|---:|---:|---:|---:|']
    fmt=lambda x:'NA' if x is None else f'{x:.6f}'
    for label,ms in [('规则合并',ref_results['A']['rule']),('LLM部分原生快照',ref_results['A']['native'])]:
        for d,m in ms.items():
            lines.append(f"|{label}|{d} {NAMES[d]}|{m['N']}/77|{m['lawful_null_N']}|{m['missing_N']}|{m['TP']}/{m['FP']}/{m['FN']}/{m['TN']}|{fmt(m['kappa'])}|{fmt(m['Precision'])}|{fmt(m['Recall'])}|{fmt(m['F1'])}|")
    lines+=['',f"A/B分别解析与复算，数值相同。旧v5到当前合并结果共变化{len(changes)}个标签槽；规则待定{null_N}项。机器间包括null的分歧{len(disagreements)}槽。",'',
            '77条是已披露开发材料；两机器的相互一致不能作为正确率。未新增真人金标准，正式验证与论文写作门槛仍为false。此审计未重新分类，未改原件或progress；执行与源字节闭包由另份执行审计核查。', '',
            f"全部实际封印成员及统计输入绑定核验通过；{len(INPUTS)}个输入文件读后SHA256/字节数保持一致。",'']
    with (OUT/'report.md').open('x',encoding='utf8') as f:
        f.write('\n'.join(lines))
    save('input-bindings.json',{'at_utc':now(),'all_inputs_byte_hash_unchanged':True,'inputs':list(INPUTS.values())})
    save('seal.json',{'status':report['status'],'files':[bind(p) for p in sorted(OUT.iterdir()) if p.is_file() and p.name!='seal.json'],
                      'self_excluded':True,'formal_validation_complete':False,'new_classification_calls_N':0})
    print(json.dumps({'status':report['status'],'mismatch_N':len(MISMATCHES),'report':bind(OUT/'report.json'),
                      'markdown':bind(OUT/'report.md'),'seal':bind(OUT/'seal.json'),'input_binding_N':len(INPUTS)},ensure_ascii=False))
    return 0 if not MISMATCHES else 2

if __name__=='__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        failure={'status':'independent_statistics_audit_attempt_failed','at_utc':now(),'error_type':type(exc).__name__,
                 'error':str(exc),'traceback':traceback.format_exc(),'new_classification_calls_N':0,'formal_validation_complete':False}
        save('attempt-failure.json',failure)
        print(json.dumps(failure,ensure_ascii=False))
        raise SystemExit(2)
