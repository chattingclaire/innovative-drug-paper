"""Independent arithmetic audit of the completed V600 statistical output.

Reads the completed result and three hash-bound frozen definition files only.
Never imports or executes a production metric function, resamples, recodes,
reconciles labels, reads separate predictions, or edits existing study files.
All sums of design weights use exact fractions; published floats are compared
with explicit tolerances. Output paths are fixed and exclusive.
"""
from collections import Counter
from datetime import datetime, timezone
from fractions import Fraction as F
from pathlib import Path
import hashlib
import json
import math

BASE = Path(__file__).resolve().parent
SOURCE = BASE / 'V600-正式成对统计.json'
JSON_OUT = BASE / 'V600-统计结果独立数值核对.json'
MD_OUT = BASE / 'V600-统计结果独立数值核对.md'
DIMS = ('S', 'E', 'Ec', 'I', 'F')
SPEC = [('A_vs_C', 'A', 'C')] + [(v+'_'+ 'vs_'+c, v, c)
        for v in ('baseline', 'candidate') for c in ('A', 'C')]
SCOPE = 'jointly definite baseline, candidate and specified reference only'
ABS_TOL, REL_TOL = 1e-10, 1e-12


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_json(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            if k in result:
                raise ValueError('Duplicate JSON key')
            result[k] = v
        return result
    def bad(_):
        raise ValueError('Nonfinite JSON number')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=bad)


def quotient(a, b):
    return a / b if b > 0 else None


def plain(x):
    if isinstance(x, F):
        return float(x)
    if isinstance(x, dict):
        return {k: plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [plain(v) for v in x]
    return x


class Audit:
    def __init__(self):
        self.checks = []

    def check(self, path, reported, recomputed, kind='independent_recalculation'):
        r, e = plain(reported), plain(recomputed)
        numeric = (type(r) in (int, float) and type(e) in (int, float))
        if numeric and (isinstance(recomputed, F) or type(r) is float or type(e) is float):
            passed = math.isfinite(r) and math.isfinite(e) and math.isclose(r, e, rel_tol=REL_TOL, abs_tol=ABS_TOL)
            error = abs(r-e) if math.isfinite(r) and math.isfinite(e) else None
        else:
            passed = type(r) is type(e) and r == e
            error = None
        item = {'path': path, 'kind': kind, 'reported': r, 'independently_expected': e,
                'passed': passed}
        if error is not None:
            item['absolute_error'] = error
        self.checks.append(item)

    def matrix(self, path, reported, expected):
        self.check(path+'/shape', [len(reported), *[len(r) for r in reported]],
                   [len(expected), *[len(r) for r in expected]])
        for i, row in enumerate(expected):
            for j, value in enumerate(row):
                self.check(f'{path}/{i}/{j}', reported[i][j], value)


def tables(rows, left, right, dim, size=3):
    raw = [[0 for _ in range(size)] for _ in range(size)]
    weighted = [[F(0) for _ in range(size)] for _ in range(size)]
    for row in rows:
        i = row[left][dim] if type(row[left][dim]) is int else 2
        j = row[right][dim] if type(row[right][dim]) is int else 2
        raw[i][j] += 1
        weighted[i][j] += F(row['N_h'], row['n_h'])
    return raw, weighted


def point_values(t, classification):
    tn, fn, fp, tp = t[0][0], t[0][1], t[1][0], t[1][1]
    definite = tn+fn+fp+tp
    n = sum((sum(row, F(0)) for row in t), F(0))
    left = sum(t[0], F(0))+sum(t[1], F(0))
    right = sum((row[0]+row[1] for row in t), F(0))
    agree = quotient(tn+tp, definite)
    pa, pb = quotient(fp+tp, definite), quotient(fn+tp, definite)
    chance = None if definite == 0 else pa*pb+(1-pa)*(1-pb)
    kappa = None if chance is None or 1-chance <= F(1, 10**14) else (agree-chance)/(1-chance)
    result = {'population_weight_total': n, 'binary_total_00': tn, 'binary_total_01': fn,
              'binary_total_10': fp, 'binary_total_11': tp, 'both_definite_total': definite,
              'left_definite_total': left, 'right_definite_total': right,
              'coverage_both_definite': quotient(definite,n), 'coverage_left': quotient(left,n),
              'coverage_right': quotient(right,n), 'agreement_definite': agree, 'kappa_definite': kappa,
              'positive_agreement_definite': quotient(2*tp,2*tp+fp+fn),
              'negative_agreement_definite': quotient(2*tn,2*tn+fp+fn),
              'positive_rate_left_on_both_definite': pa, 'positive_rate_right_on_both_definite': pb,
              'positive_rate_left_on_left_definite': quotient(sum(t[1],F(0)),left),
              'positive_rate_right_on_right_definite': quotient(sum((row[1] for row in t),F(0)),right)}
    if len(t) == 3:
        result.update(pending_left_total=sum(t[2],F(0)), pending_right_total=sum((r[2] for r in t),F(0)),
                      pending_both_total=t[2][2], pending_exactly_one_total=t[2][0]+t[2][1]+t[0][2]+t[1][2])
    if classification:
        result.update(TP=tp, FP=fp, FN=fn, TN=tn, precision_definite=quotient(tp,tp+fp),
                      recall_definite=quotient(tp,tp+fn), f1_definite=quotient(2*tp,2*tp+fp+fn),
                      specificity_definite=quotient(tn,tn+fp), accuracy_definite=agree)
    reason = 'no_both_definite' if definite == 0 else ('degenerate_expected_agreement' if kappa is None else None)
    return result, reason


def interval_check(audit, path, interval, point, census):
    kind = 'interval_internal_consistency_only_no_bootstrap'
    audit.check(path+'/estimate', interval['estimate'], point, kind)
    defined, missing = interval['defined_replicates'], interval['undefined_replicates']
    audit.check(path+'/replicate_counts_valid', type(defined) is int and type(missing) is int
                and defined >= 0 and missing >= 0 and defined+missing == 2000, True, kind)
    fraction = F(missing,2000)
    audit.check(path+'/undefined_fraction', interval['undefined_fraction'], fraction, kind)
    audit.check(path+'/confidence_level', interval['confidence_level'], 0.95, kind)
    audit.check(path+'/simultaneous', interval['simultaneous'], False, kind)
    status = ('unstable_more_than_10_percent_undefined' if fraction > F(1,10) else
              'point_undefined' if point is None else 'census_design_variance_zero' if census else
              'approximate_percentile_conditional_on_defined' if missing else 'approximate_percentile')
    audit.check(path+'/status', interval['status'], status, kind)
    if status in ('unstable_more_than_10_percent_undefined','point_undefined'):
        for key in ('lower','upper','replicate_se'):
            audit.check(path+'/'+key, interval[key], None, kind)
    else:
        lo, hi, se = interval['lower'], interval['upper'], interval['replicate_se']
        audit.check(path+'/ordered_finite_bounds', type(lo) in (int,float) and type(hi) in (int,float)
                    and math.isfinite(lo) and math.isfinite(hi) and lo <= hi, True, kind)
        audit.check(path+'/nonnegative_finite_se', type(se) in (int,float) and math.isfinite(se) and se >= 0, True, kind)
        if census:
            audit.check(path+'/lower', lo, point, kind)
            audit.check(path+'/upper', hi, point, kind)
            audit.check(path+'/replicate_se', se, 0.0, kind)


def intervals(audit, path, item, census):
    estimates, bands = item['estimates'], item['marginal_95_intervals']
    audit.check(path+'/interval_metric_inventory', sorted(bands), sorted(estimates), 'interval_internal_consistency_only_no_bootstrap')
    for key, value in estimates.items():
        interval_check(audit,path+'/marginal_95_intervals/'+key,bands[key],value,census)


def main():
    for path in (JSON_OUT,MD_OUT):
        if path.exists() or path.is_symlink():
            raise FileExistsError('Refusing existing audit output: '+str(path))
    raw = SOURCE.read_bytes(); document = read_json(raw)
    stats, archive = document['paired_statistics'], document['archive']
    rows = archive['normalized_rows_without_generated_reference']
    audit = Audit()
    bindings = {}
    for name in ('survey_metrics','paired_version_metrics','analysis_plan'):
        entry = archive['freeze_manifest_original']['files'][name]
        file = Path(entry['path']); content = file.read_bytes()
        digest = sha(content)
        audit.check('definition/'+name+'/sha256',digest,entry['sha256'],'input_binding')
        bindings[name] = {'path':str(file),'sha256':digest,'read_as_text_or_bytes_only':True}
    audit.check('status',document['status'],'completed_frozen_paired_ID_join_not_validation_pass','design')
    audit.check('phase',document['phase'],'V600','design')
    audit.check('statistics_status',stats['status'],'paired_statistical_output_not_validation_pass','design')
    audit.check('sample_n',stats['sample_n'],len(rows),'design')
    audit.check('unique_ID_count',len({r['id'] for r in rows}),len(rows),'design')
    census = all(r['N_h']==r['n_h'] for r in rows)
    audit.check('all_census',stats['all_census'],census,'design')
    for column in ('A','C','baseline','candidate'):
        valid = all(set(r[column])==set(DIMS) and all(
            (type(r[column][d]) is int and r[column][d] in (0,1)) or r[column][d]=='待定' for d in DIMS) for r in rows)
        audit.check('labels/'+column+'/valid',valid,True,'design')
    design = archive['sampling_manifest_original']['plan']
    strata = design['strata']; counts = Counter(r['stratum'] for r in rows)
    audit.check('strata/inventory',sorted(counts),sorted(strata),'design')
    audit.check('population_N',stats['population_N'],sum(x['N_h'] for x in strata.values()),'design')
    audit.check('sampling_plan_n',design['n'],len(rows),'design')
    audit.check('sampling_plan_N',design['N_star'],stats['population_N'],'design')
    weighted_n = sum((F(r['N_h'],r['n_h']) for r in rows),F(0))
    audit.check('design_weight_sum',stats['population_N'],weighted_n,'design')
    for h,spec in strata.items():
        audit.check('strata/'+h+'/observed_n',counts[h],spec['n_h'],'design')
        audit.check('strata/'+h+'/row_design_matches',all(r['N_h']==spec['N_h'] and r['n_h']==spec['n_h']
                    and type(r['N_h']) is int and type(r['n_h']) is int and 0<r['n_h']<=r['N_h']
                    for r in rows if r['stratum']==h),True,'design')
        audit.check('strata/'+h+'/weight',spec['weight'],F(spec['N_h'],spec['n_h']),'design')
        audit.check('strata/'+h+'/inclusion_probability',spec['pi'],F(spec['n_h'],spec['N_h']),'design')
    audit.check('reported_strata_inventory',sorted(x['stratum'] for x in stats['strata']),sorted(strata),'design')
    for spec in stats['strata']:
        h=spec['stratum']
        for key in ('N_h','n_h','weight'):
            audit.check('reported_strata/'+h+'/'+key,spec[key],strata[h][key],'design')
    declaration = {'reference_generated':False,'primary_differences':['recall_definite','f1_definite'],
                   'difference_sign':'candidate minus baseline','difference_scope':SCOPE}
    for key,value in declaration.items():
        audit.check('declaration/'+key,stats[key],value,'frozen_scope')
    for key,value in {'replicates':2000,'seed':2026092606,'generator':'numpy.random.PCG64',
            'shared_weights_across_all_versions_dimensions_and_references':True,
            'intervals':'approximate marginal 95% percentile, not simultaneous',
            'undefined_fraction_suppression_threshold':'>0.10'}.items():
        audit.check('bootstrap_declaration/'+key,stats['bootstrap'][key],value,'frozen_scope_not_reexecuted')
    audit.check('comparison_inventory',sorted(stats['comparisons']),sorted(x[0] for x in SPEC),'design')
    comparison_results = {}
    for name,left,right in SPEC:
        found = stats['comparisons'][name]; comparison_results[name] = {}
        audit.check(name+'/left',found['left'],left,'frozen_scope')
        audit.check(name+'/right',found['right'],right,'frozen_scope')
        audit.check(name+'/dimensions',sorted(found['dimensions']),sorted(DIMS),'design')
        for d in DIMS:
            p=name+'/'+d; item=found['dimensions'][d]
            raw_table, table = tables(rows,left,right,d)
            metrics,reason = point_values(table,name!='A_vs_C')
            audit.check(p+'/table_axis_order',item['table_axis_order'],[0,1,'待定'])
            audit.matrix(p+'/raw_3x3_counts',item['raw_3x3_counts'],raw_table)
            audit.matrix(p+'/weighted_3x3_estimated_totals',item['weighted_3x3_estimated_totals'],table)
            for key,value in metrics.items():
                audit.check(p+'/estimates/'+key,item['estimates'][key],value)
            audit.check(p+'/kappa_undefined_reason',item['completion_and_undefined_flags']['kappa_undefined_reason'],reason)
            intervals(audit,p,item,census)
            comparison_results[name][d] = {'raw_3x3_counts':raw_table,'weighted_3x3_estimated_totals':plain(table),
                                           'independently_recomputed_estimates':plain(metrics),'kappa_undefined_reason':reason}
    paired_results = {}
    common_keys = ('TP','FP','FN','TN','precision_definite','recall_definite','f1_definite','specificity_definite','accuracy_definite')
    for ref in ('A','C'):
        found=stats['paired_differences'][ref];paired_results[ref]={}
        audit.check(ref+'/reference',found['reference'],ref,'frozen_scope')
        audit.check(ref+'/dimensions',sorted(found['dimensions']),sorted(DIMS),'design')
        for d in DIMS:
            p='paired/'+ref+'/'+d;item=found['dimensions'][d]
            joint=[r for r in rows if all(type(r[c][d]) is int for c in ('baseline','candidate',ref))]
            weight=sum((F(r['N_h'],r['n_h']) for r in joint),F(0))
            positive=[r for r in joint if r[ref][d]==1]
            positive_weight=sum((F(r['N_h'],r['n_h']) for r in positive),F(0))
            audit.check(p+'/raw_jointly_definite_n',item['raw_jointly_definite_n'],len(joint))
            audit.check(p+'/weighted_joint_coverage',item['weighted_joint_coverage'],weight/weighted_n)
            for v,other in (('baseline','candidate'),('candidate','baseline')):
                only=sum(type(r[v][d]) is int and type(r[ref][d]) is int and r[other][d]=='待定' for r in rows)
                audit.check(p+'/raw_'+v+'_only_assessable_n',item['raw_'+v+'_only_assessable_n'],only)
            saved={}
            for v in ('baseline','candidate'):
                one=item[v+'_common_subset'];q=p+'/'+v+'_common_subset'
                raw_table,table=tables(joint,v,ref,d,size=2);metrics,_=point_values(table,True)
                metrics={k:metrics[k] for k in common_keys}
                audit.check(q+'/scope',one['scope'],SCOPE,'frozen_scope')
                audit.check(q+'/table_axis_order',one['table_axis_order'],[0,1])
                audit.matrix(q+'/raw_2x2_counts',one['raw_2x2_counts'],raw_table)
                audit.matrix(q+'/weighted_2x2_estimated_totals',one['weighted_2x2_estimated_totals'],table)
                for key,value in metrics.items():
                    audit.check(q+'/estimates/'+key,one['estimates'][key],value)
                audit.check(q+'/derived_raw_reference_positive_denominator',sum(r[1] for r in one['raw_2x2_counts']),len(positive))
                audit.check(q+'/derived_weighted_reference_positive_denominator',one['estimates']['TP']+one['estimates']['FN'],positive_weight)
                intervals(audit,q,one,census)
                saved[v]={'raw_2x2_counts':raw_table,'weighted_2x2_estimated_totals':plain(table),'estimates':metrics}
            deltas={}
            for key in ('recall_definite','f1_definite'):
                b,c=saved['baseline']['estimates'][key],saved['candidate']['estimates'][key]
                delta=None if b is None or c is None else c-b;deltas[key]=delta
                band=item['candidate_minus_baseline'][key]
                audit.check(p+'/candidate_minus_baseline/'+key+'/estimate',band['estimate'],delta)
                interval_check(audit,p+'/candidate_minus_baseline/'+key,band,delta,census)
            paired_results[ref][d]=plain({'raw_jointly_definite_n':len(joint),'weighted_joint_total':weight,
                'weighted_joint_coverage':weight/weighted_n,'raw_reference_positive_denominator':len(positive),
                'weighted_reference_positive_denominator':positive_weight,'common_subsets':saved,
                'candidate_minus_baseline':deltas})
    # Input immutability is checked before any new audit artifact is published.
    audit.check('primary_unchanged',sha(SOURCE.read_bytes()),sha(raw),'input_binding')
    for key,entry in bindings.items():
        audit.check('definition/'+key+'/unchanged',sha(Path(entry['path']).read_bytes()),entry['sha256'],'input_binding')
    failed=[c for c in audit.checks if not c['passed']]
    errors=[c['absolute_error'] for c in audit.checks if 'absolute_error' in c]
    kinds=Counter(c['kind'] for c in audit.checks)
    result={'status':'independent_numerical_audit_no_discrepancies' if not failed else 'independent_numerical_audit_discrepancies_found',
            'review_identity':'AI independent statistical output check; not a blind label review or human adjudication',
            'created_at':datetime.now(timezone.utc).isoformat(),'primary_result':{'path':str(SOURCE),'sha256':sha(raw)},
            'checker_sha256':sha(Path(__file__).read_bytes()),'frozen_definitions':bindings,
            'design':{'sample_n':len(rows),'population_N':stats['population_N'],'strata_n':len(strata),'exact_weight_sum':str(weighted_n)},
            'method':{'weight':'exact Fraction(N_h,n_h); no production metric function called',
                      'table_orientation':'rows=left/model, columns=right/reference; axis 0,1,pending',
                      'agreement':'(TN+TP)/jointly_definite_weight','kappa':'(observed-chance)/(1-chance), threshold 1-chance<=1e-14 undefined',
                      'precision':'TP/(TP+FP)','recall':'TP/(TP+FN)','F1':'2TP/(2TP+FP+FN)',
                      'paired_subset':SCOPE,'difference_sign':'candidate minus baseline',
                      'zero_denominators':'None, not zero or imputed',
                      'numeric_tolerance':{'absolute':ABS_TOL,'relative':REL_TOL},'raw_counts':'exact integer comparison'},
            'coverage':{'full_comparison_dimension_tables':25,'machine_reference_PRF_blocks':20,
                        'paired_reference_dimension_blocks':10,'bootstrap_rerun':False,
                        'A_C_directional_PRF_generated':False,'completion_bound_formulas_recomputed':False},
            'summary':{'checks':len(audit.checks),'passed':len(audit.checks)-len(failed),'failed':len(failed),
                       'check_kinds':dict(kinds),'maximum_absolute_numeric_difference':max(errors,default=0)},
            'recomputed_comparisons':comparison_results,'recomputed_paired_subsets':paired_results,
            'checks':audit.checks,'discrepancies':failed,
            'limitations':['Conditional on archived normalized labels and design metadata; no correctness adjudication or re-verification against original submissions/prediction files.',
                'No bootstrap replication, quantile/SE reproduction or confidence interval coverage validation; intervals checked only for point consistency, declared status, counts, bounds order and scope.',
                'Completion bound formulas and their completion-undefined flags were not independently recomputed; their interval point fields were checked internally only.',
                'Finite frame only. No new research indicator, pass threshold, consensus reference, missing-label imputation, sensitivity analysis or full-corpus inference.']}
    lines=['# V600 统计输出独立数值核对','',
           '本次是 AI 对已完成统计输出的独立算术核对，不是盲评、标签裁决或真人领域审查。', '',
           ('未发现超出声明浮点容差的数值差异。' if not failed else f'发现 {len(failed)} 项差异，详见 JSON 的 discrepancies。'),
           f'样本 n={len(rows)}，有限候选框 N={stats["population_N"]}，{len(strata)} 个层；精确设计权重总和为 {weighted_n}。',
           f'共核对 {len(audit.checks)} 项，最大浮点绝对差 {max(errors,default=0):.3g}；绝对容差 {ABS_TOL:g}、相对容差 {REL_TOL:g}。', '',
           '覆盖 25 个原始 3×3 表、加权总量/覆盖/一致性/κ，20 个机器对参考 PRF，以及 10 个两版共同可判子集的计数、阳性分母和 ΔRecall/ΔF1。A/C 不新增方向性 PRF。按 Fraction(N_h,n_h) 独立累加，未调用原统计函数。','',
           '|参考|维度|共同可判 n|参考阳性 n|加权阳性分母|ΔRecall|ΔF1|',
           '|---|---|---:|---:|---:|---:|---:|']
    def fmt(x):return 'NA' if x is None else f'{x:.6f}'
    for ref in ('A','C'):
        for d,item in paired_results[ref].items():
            delta=item['candidate_minus_baseline']
            lines.append(f'|{ref}|{d}|{item["raw_jointly_definite_n"]}|{item["raw_reference_positive_denominator"]}|{fmt(item["weighted_reference_positive_denominator"])}|{fmt(delta["recall_definite"])}|{fmt(delta["f1_definite"])}|')
    lines.extend(['','区间仅核对点估计、复制计数/未定义比例、抑制状态、边界顺序与边际 95% 声明；未重跑 bootstrap、验证区间分位数/标准误或覆盖率。未复算待定补全界公式。未重新对照原始提交或预测文件，亦不判断标签正确性。', '',
                  '主结果 SHA256：`'+sha(raw)+'`。完整逐项核对、报告值、独立值与差异列表见同名 JSON。'])
    with JSON_OUT.open('x') as stream:
        json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    with MD_OUT.open('x') as stream:
        stream.write('\n'.join(lines)+'\n')
    print(json.dumps({'status':result['status'],'primary_sha256':sha(raw),'checker_sha256':result['checker_sha256'],
                      **result['summary'],'json':str(JSON_OUT),'markdown':str(MD_OUT)},ensure_ascii=False))


if __name__ == '__main__':
    main()
