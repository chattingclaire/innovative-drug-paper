"""Attention shares and paired differences; only explicitly supplied labels are read.

This module never searches for prediction files and never constructs a reference.
The full original 60-per-department ID set is retained for bootstrap resampling,
even if a supplied common analysis mask excludes unresolved observations.
"""
import numpy as np
import statistical_core_r3 as core


def divide(a, b):
    a, b = np.broadcast_arrays(np.asarray(a, float), np.asarray(b, float))
    return np.divide(a, b, out=np.full(a.shape, np.nan), where=b > 1e-12)


def attention_share(totals):
    totals = np.asarray(totals, float)
    return divide(totals, totals.sum(axis=-1, keepdims=True))


def common_complete_mask(method_rows, ids):
    """Use the same five-dimension-complete rows for all compared methods."""
    return np.asarray([
        all(core.binary(core.label(rows[rid], dim))
            for rows in method_rows for dim in core.DIMS)
        for rid in ids
    ], dtype=bool)


def _attention_arrays(rows, ids):
    values = np.asarray([[core.label(rows[rid], d) for d in core.DIMS]
                         for rid in ids], dtype=object)
    known = np.asarray([[core.binary(v) for v in row] for row in values], bool)
    hits = np.asarray([[float(v == 1) if k else 0.0
                        for v, k in zip(row, mask)]
                       for row, mask in zip(values, known)], float)
    return known, hits


def missing_share_bounds(known_hits, pending_weights):
    """Sharp marginal q bounds for binary pending labels; not joint intervals."""
    t = np.asarray(known_hits, float)
    m = np.asarray(pending_weights, float)
    total = t.sum()
    possible = total + m.sum()
    if possible <= 1e-12:
        return [{'low': None, 'high': None} for _ in core.DIMS]
    result = []
    for j in range(len(core.DIMS)):
        lower_den = total + m.sum() - m[j]
        upper_den = total + m[j]
        lower = t[j] / lower_den if lower_den > 1e-12 else 1.0
        upper = (t[j] + m[j]) / upper_den if upper_den > 1e-12 else 0.0
        result.append({'low': float(lower), 'high': float(upper)})
    return result


def attention_profile(ctx, rows, ids, component, group, kind, method,
                      factor_cache, analysis_mask=None):
    """q_d=T_d/sum_d(T_d); hit rates are separately named diagnostics.

    With unresolved labels, q for the full frame is NA. A same-row complete-case
    diagnostic and sharp binary missing-label bounds are supplied explicitly.
    An external common mask means the comparison is conditional on that support.
    """
    if not ids:
        raise ValueError('No sampled IDs for this group/component')
    known, hits = _attention_arrays(rows, ids)
    weights = core.weighting(ctx, ids, kind)
    complete = known.all(axis=1)
    mask = complete if analysis_mask is None else np.asarray(analysis_mask, bool)
    if mask.shape != (len(ids),) or np.any(mask & ~complete):
        raise ValueError('Analysis mask includes unresolved five-dimension row')
    total_hits = weights @ hits
    pending_weights = weights @ (~known).astype(float)
    selected_hits = hits * mask[:, None]
    point_totals = weights @ selected_hits
    point_q = attention_share(point_totals)
    full_q_defined = bool(known.all()) and analysis_mask is None
    bounds = missing_share_bounds(total_hits, pending_weights)
    primary = ('department_unit_rescaled_SRSWOR'
               if component == 'probability_canonical'
               else 'department_unit_conditional_WR')
    intervals = {}
    for mechanism in (primary, 'department_source_file_conditional_WR'):
        key = (component, group, mechanism, tuple(ids))
        if key not in factor_cache:
            factor_cache[key] = core.replicate_factors(ctx, ids, component, mechanism)
        boot_totals = (factor_cache[key] * weights) @ selected_hits
        boot_q = attention_share(boot_totals)
        intervals[mechanism] = {d: core.interval(boot_q[:, j])
                                for j, d in enumerate(core.DIMS)}
    per_dim = {}
    for j, dim in enumerate(core.DIMS):
        per_dim[dim] = {
            'weighted_known_coding_count': float(total_hits[j]),
            'raw_known_coding_count': int(hits[:, j].sum()),
            'pending_n': int((~known[:, j]).sum()),
            'weighted_pending_count': float(pending_weights[j]),
            'attention_share': core.safe(point_q[j]) if full_q_defined else None,
            'attention_share_missing_label_bounds': bounds[j],
            'attention_share_on_common_complete_support': {
                'estimate': core.safe(point_q[j]),
                'ci95_primary': intervals[primary][dim],
                'ci95_source_file_conditional_sensitivity':
                    intervals['department_source_file_conditional_WR'][dim],
            },
            'known_label_hit_rate_diagnostic': core.safe(
                divide(total_hits[j], weights @ known[:, j].astype(float))),
        }
    return {
        'component': component, 'group': group, 'weighting': kind, 'method': method,
        'definition': '注意力占比 q_d=T_d/Σ_dT_d；T为加权编码句次，五维合计100%。',
        'inference_scope': ('remaining canonical representative frame only'
                            if component == 'probability_canonical'
                            else 'selected challenge cases only; conditional diagnostic'),
        'unit_frame_n': len(ids), 'complete_support_n': int(mask.sum()),
        'excluded_pending_or_common_support_n': int((~mask).sum()),
        'complete_support_ids': [rid for rid, include in zip(ids, mask) if include],
        'full_frame_attention_share_defined': full_q_defined,
        'support_conditioning': ('own fully observed five-dimension rows'
                                if analysis_mask is None
                                else 'explicit identical complete support across methods'),
        'weighted_five_dimension_coding_count_on_support': float(point_totals.sum()),
        'primary_bootstrap_mechanism': primary, 'dimensions': per_dim,
    }


def paired_metric_difference(ctx, left_one, left_two, reference, dim, ids,
                             component, group, kind, names, factor_cache):
    """Same reference, same paired support and replicate factors for method1−2."""
    a, va = core.cells(left_one, reference, dim, ids)
    b, vb = core.cells(left_two, reference, dim, ids)
    valid = va & vb
    a *= valid[:, None]
    b *= valid[:, None]
    w = core.weighting(ctx, ids, kind)
    point = core.metrics(w @ a)[0] - core.metrics(w @ b)[0]
    mechanism = ('department_unit_rescaled_SRSWOR'
                 if component == 'probability_canonical'
                 else 'department_unit_conditional_WR')
    key = (component, group, mechanism, tuple(ids))
    if key not in factor_cache:
        factor_cache[key] = core.replicate_factors(ctx, ids, component, mechanism)
    fw = factor_cache[key] * w
    reps = core.metrics(fw @ a) - core.metrics(fw @ b)
    return {
        'difference_direction': 'method_one_minus_method_two',
        'paired_n': int(valid.sum()), 'excluded_pending_n': int((~valid).sum()),
        'metrics': {name: {'estimate': core.safe(point[core.METRIC_NAMES.index(name)]),
                           'ci95_primary': core.interval(reps[:, core.METRIC_NAMES.index(name)])}
                    for name in names},
        'primary_bootstrap_mechanism': mechanism,
    }


def paired_attention_difference(ctx, one, two, ids, component, group, kind,
                                factor_cache, analysis_mask=None):
    """Compute q differences on a common complete support, retaining design n."""
    mask = (common_complete_mask([one, two], ids) if analysis_mask is None
            else np.asarray(analysis_mask, bool))
    k1, h1 = _attention_arrays(one, ids)
    k2, h2 = _attention_arrays(two, ids)
    if mask.shape != (len(ids),) or np.any(mask & ~(k1 & k2).all(axis=1)):
        raise ValueError('Invalid common complete support')
    h1, h2 = h1 * mask[:, None], h2 * mask[:, None]
    w = core.weighting(ctx, ids, kind)
    point = attention_share(w @ h1) - attention_share(w @ h2)
    mechanism = ('department_unit_rescaled_SRSWOR'
                 if component == 'probability_canonical'
                 else 'department_unit_conditional_WR')
    key = (component, group, mechanism, tuple(ids))
    if key not in factor_cache:
        factor_cache[key] = core.replicate_factors(ctx, ids, component, mechanism)
    fw = factor_cache[key] * w
    reps = attention_share(fw @ h1) - attention_share(fw @ h2)
    return {'difference_direction': 'method_one_minus_method_two',
            'complete_support_n': int(mask.sum()),
            'excluded_pending_or_common_support_n': int((~mask).sum()),
            'primary_bootstrap_mechanism': mechanism,
            'dimensions': {d: {'estimate': core.safe(point[j]),
                                'ci95_primary': core.interval(reps[:, j])}
                           for j, d in enumerate(core.DIMS)}}
