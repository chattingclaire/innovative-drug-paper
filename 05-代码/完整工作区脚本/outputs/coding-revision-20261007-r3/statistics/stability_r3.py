"""Three actual identical-request runs; selected IDs supplied explicitly.

The production run remains the original run. This computes repeatability,
never chooses an output, and never reads reference/coder files.
"""
from collections import Counter
from itertools import combinations
import numpy as np
import statistical_core_r3 as core
from statistical_extensions_r3 import attention_share


def summarize_stability(runs, ids, groups):
    if len(runs) != 3:
        raise ValueError('Require production plus two additional actual runs')
    if len(ids) != len(set(ids)) or any(set(run) != set(ids) for run in runs.values()):
        raise ValueError('All three runs must have exactly the frozen 75 IDs')
    names = list(runs)
    scopes = [('THREE_DEPARTMENTS', [rid for rid in ids if groups[rid] in core.GROUPS])]
    scopes += [(g, [rid for rid in ids if groups[rid] == g]) for g in core.GROUPS]
    scopes += [('ALL_ACTUAL_RUN_IDS_TECHNICAL', list(ids))]
    records = []
    for group, chosen in scopes:
        pairs = []
        for one, two in combinations(names, 2):
            per_dim = {}
            for d in core.DIMS:
                mat, valid = core.cells(runs[one], runs[two], d, chosen)
                counts = mat.sum(axis=0)
                point = core.metrics(counts)[0]
                per_dim[d] = {
                    'paired_n': int(valid.sum()), 'excluded_pending_n': int((~valid).sum()),
                    'raw_cells': dict(zip(('both_1', 'first_1_second_0',
                                          'first_0_second_1', 'both_0'), map(int, counts))),
                    'kappa': core.safe(point[0]), 'agreement': core.safe(point[1]),
                    'first_positive_n': int(counts[0]+counts[1]),
                    'second_positive_n': int(counts[0]+counts[2]),
                    'disagreement_ids': [rid for rid, row in zip(chosen, mat)
                                         if row[1] or row[2]],
                    'excluded_ids': [rid for rid, ok in zip(chosen, valid) if not ok],
                }
            complete = [rid for rid in chosen if all(core.binary(core.label(runs[n][rid],d))
                        for n in (one,two) for d in core.DIMS)]
            identical = [rid for rid in complete if all(core.label(runs[one][rid],d)
                         == core.label(runs[two][rid],d) for d in core.DIMS)]
            pairs.append({'first_run': one, 'second_run': two, 'dimensions': per_dim,
                          'fully_paired_row_n': len(complete),
                          'identical_five_dimension_row_n': len(identical),
                          'identical_five_dimension_row_rate': len(identical)/len(complete)
                              if complete else None})
        dimensions = {}
        for d in core.DIMS:
            complete = [rid for rid in chosen if all(core.binary(core.label(runs[n][rid],d))
                        for n in names)]
            votes = Counter(sum(core.label(runs[n][rid],d) for n in names) for rid in complete)
            positives = {n: sum(core.label(runs[n][rid],d)==1 for rid in chosen
                               if core.binary(core.label(runs[n][rid],d))) for n in names}
            pendings = {n: sum(not core.binary(core.label(runs[n][rid],d)) for rid in chosen)
                        for n in names}
            dimensions[d] = {
                'three_run_complete_n': len(complete),
                'three_run_excluded_pending_n': len(chosen)-len(complete),
                'positive_votes_across_three_runs': {str(k): votes[k] for k in range(4)},
                'stable_label_n': votes[0]+votes[3], 'label_varies_n': votes[1]+votes[2],
                'positive_count_by_run': positives, 'pending_count_by_run': pendings,
                'positive_count_range': [min(positives.values()),max(positives.values())],
            }
        common_rows = [rid for rid in chosen if all(core.binary(core.label(runs[n][rid],d))
                       for n in names for d in core.DIMS)]
        q = {}
        for n in names:
            total = np.asarray([sum(core.label(runs[n][rid],d) for rid in common_rows)
                                for d in core.DIMS], float)
            q[n] = attention_share(total)
        q_ranges = {}
        for j,d in enumerate(core.DIMS):
            finite = [float(q[n][j]) for n in names if np.isfinite(q[n][j])]
            q_ranges[d] = {'attention_share_by_run': {n:core.safe(q[n][j]) for n in names},
                           'observed_run_range': [min(finite),max(finite)] if finite else [None,None],
                           'undefined_run_n': len(names)-len(finite)}
        records.append({'group': group, 'actual_id_n': len(chosen),
                        'department_counts': dict(Counter(groups[rid] for rid in chosen)),
                        'pairwise': pairs, 'three_run_dimensions': dimensions,
                        'attention_share_common_complete_n': len(common_rows),
                        'attention_share_ranges': q_ranges})
    return {'run_order': names, 'production_run': names[0],
            'production_output_replaced': False,
            'scope_note': 'Main scope is 72 three-department units; all75 includes GOV3 only in technical record.',
            'selection_note': 'Three complete production batches selected before outputs; not SRS of policy units.',
            'interpretation': 'Stability is repeatability on fixed requests, not semantic validity. Three-run ranges are descriptive, not confidence intervals.',
            'records': records}


def summarize_order_perturbation(production, perturbed, ids, groups):
    """One preregistered order perturbation versus production, no rerun choice."""
    assert set(production)==set(perturbed)==set(ids)
    scopes=[('THREE_DEPARTMENTS',[rid for rid in ids if groups[rid] in core.GROUPS])]
    scopes += [(g,[rid for rid in ids if groups[rid]==g]) for g in core.GROUPS]
    scopes += [('ALL_ACTUAL_RUN_IDS_TECHNICAL',list(ids))]
    records=[]
    for group,chosen in scopes:
        per_dim={}
        for d in core.DIMS:
            cells,valid=core.cells(production,perturbed,d,chosen)
            counts=cells.sum(axis=0);point=core.metrics(counts)[0]
            per_dim[d]={'paired_n':int(valid.sum()),'excluded_pending_n':int((~valid).sum()),
                'kappa':core.safe(point[0]),'agreement':core.safe(point[1]),
                'raw_cells':dict(zip(('both_1','production_1_perturbed_0','production_0_perturbed_1','both_0'),map(int,counts))),
                'disagreement_ids':[rid for rid,row in zip(chosen,cells) if row[1] or row[2]]}
        complete=[rid for rid in chosen if all(core.binary(core.label(rows[rid],d))
                  for rows in (production,perturbed) for d in core.DIMS)]
        exact=sum(all(core.label(production[rid],d)==core.label(perturbed[rid],d) for d in core.DIMS)
                  for rid in complete)
        q={name:attention_share(np.asarray([sum(core.label(rows[rid],d) for rid in complete)
                                           for d in core.DIMS],float))
           for name,rows in [('production',production),('order_perturbed',perturbed)]}
        records.append({'group':group,'actual_id_n':len(chosen),'dimensions':per_dim,
            'fully_paired_row_n':len(complete),'identical_five_dimension_row_n':exact,
            'identical_five_dimension_row_rate':exact/len(complete) if complete else None,
            'attention_share':{d:{'production':core.safe(q['production'][j]),
                'order_perturbed':core.safe(q['order_perturbed'][j]),
                'perturbed_minus_production_percentage_points':core.safe(100*(q['order_perturbed'][j]-q['production'][j]))}
                for j,d in enumerate(core.DIMS)}})
    return {'interpretation':'One frozen order perturbation on identical packets; prompt sensitivity, not semantic validity or a confidence interval.',
            'production_output_replaced':False,'records':records}
