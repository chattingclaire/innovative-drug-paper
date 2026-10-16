"""Reference-relative metrics, explicit abstentions, and finite completion bounds.

No data are loaded on import. The remaining-frame census gets no fictitious
sampling confidence intervals. Completion bounds are logical, not statistical
confidence intervals and not adjudicated truth.
"""
import itertools

DIMS = ('S', 'E', 'Ec', 'I', 'F')
LEVELS = (0, 1, '待定')

def label(value):
    if type(value) is int and value in (0, 1):
        return value
    if value in ('待定', 'pending'):
        return '待定'
    raise ValueError('Missing/invalid label is not an abstention: ' + repr(value))

def safe_ratio(a, b):
    return a / b if b else None

def scores(c):
    a,b,c_,d = (c[k] for k in ('TP','FP','FN','TN'))
    return {'precision':safe_ratio(a,a+b), 'recall':safe_ratio(a,a+c_),
            'f1':safe_ratio(2*a,2*a+b+c_), 'specificity':safe_ratio(d,d+b),
            'accuracy':safe_ratio(a+d,a+b+c_+d), 'n_or_weight':a+b+c_+d}

def confusion_cell(pred, ref):
    return {(1,1):'TP',(1,0):'FP',(0,1):'FN',(0,0):'TN'}[(pred,ref)]

def matrix(pairs):
    """Each pair is (prediction, reference, positive finite weight)."""
    import math
    out = {(p,r):0.0 for p in LEVELS for r in LEVELS}
    for p,r,w in pairs:
        if not isinstance(w,(int,float)) or isinstance(w,bool) or not math.isfinite(w) or w<=0:
            raise ValueError('Weights must be positive and finite')
        out[label(p),label(r)] += w
    return out

def completion_bounds(m):
    """Exact extrema over all binary completions of pending cells.

    For a fixed metric every within-cell split is a convex mixture of vertices;
    its ratio lies within vertex ratios with positive denominator. Thus assigning
    each of the five unresolved cells wholly to each compatible confusion cell
    enumerates every possible extremum (64 vertices), including undefined cases.
    """
    known = {k:0.0 for k in ('TP','FP','FN','TN')}
    for p in (0,1):
        for r in (0,1):known[confusion_cell(p,r)] += m[p,r]
    unknown = [
        (m[1,'待定'],('TP','FP')), (m[0,'待定'],('FN','TN')),
        (m['待定',1],('TP','FN')), (m['待定',0],('FP','TN')),
        (m['待定','待定'],('TP','FP','FN','TN'))]
    keys=('precision','recall','f1','specificity','accuracy')
    values={k:[] for k in keys};undefined={k:False for k in keys}
    for assignments in itertools.product(*(options for _,options in unknown)):
        c=known.copy()
        for (weight,_),target in zip(unknown,assignments):c[target]+=weight
        result=scores(c)
        for k in keys:
            if result[k] is None:undefined[k]=True
            else:values[k].append(result[k])
    return {k:{'min':min(values[k]) if values[k] else None,
               'max':max(values[k]) if values[k] else None,
               'undefined_completion_possible':undefined[k]} for k in keys}

def summarize(pairs):
    m=matrix(pairs);total=sum(m.values())
    c={k:0.0 for k in ('TP','FP','FN','TN')}
    for p in (0,1):
        for r in (0,1):c[confusion_cell(p,r)]=m[p,r]
    n=sum(c.values());ref_pending=sum(m[p,'待定'] for p in LEVELS)
    pred_pending=sum(m['待定',r] for r in LEVELS)
    # Recall coverage treats machine abstention on a known positive as unresolved,
    # not negative. Report this denominator explicitly beside conditional recall.
    positive_reference=m[0,1]+m[1,1]+m['待定',1]
    return {'three_by_three':[{'prediction':p,'reference':r,'count_or_weight':m[p,r]}
                              for p in LEVELS for r in LEVELS],
        'total_n_or_weight':total,'joint_determinate_n_or_weight':n,
        'joint_determinate_coverage':safe_ratio(n,total),
        'prediction_pending_n_or_weight':pred_pending,
        'reference_pending_n_or_weight':ref_pending,
        'both_pending_n_or_weight':m['待定','待定'],
        'confusion_on_joint_determinate':c,'conditional_scores':scores(c),
        'known_reference_positive_n_or_weight':positive_reference,
        'prediction_coverage_on_known_reference_positive':safe_ratio(m[0,1]+m[1,1],positive_reference),
        'binary_completion_bounds_not_confidence_intervals':completion_bounds(m)}

def agreement(pairs):
    report=summarize(pairs);c=report['confusion_on_joint_determinate']
    a,b,c_,d=(c[k] for k in ('TP','FP','FN','TN'));n=a+b+c_+d
    observed=safe_ratio(a+d,n)
    expected=((a+b)*(a+c_)+(c_+d)*(b+d))/(n*n) if n else None
    report['binary_agreement']={
        'observed_agreement':observed,
        'kappa':(observed-expected)/(1-expected) if expected is not None and expected!=1 else None,
        'positive_agreement':safe_ratio(2*a,2*a+b+c_),
        'negative_agreement':safe_ratio(2*d,2*d+b+c_),
        'first_positive_rate_joint_determinate':safe_ratio(a+b,n),
        'second_positive_rate_joint_determinate':safe_ratio(a+c_,n)}
    return report

def evaluate_units(units, methods, references=('A','C')):
    """Units: {id, weight, predictions:{method:labels}, references:{coder:labels}}.

    Common-comparable scores use exactly the same per-reference subset for every
    method. They are conditional descriptive results, with excluded coverage shown.
    """
    ids=[u['id'] for u in units]
    if len(ids)!=len(set(ids)):raise ValueError('Duplicate units')
    result={'n':len(units),'methods':{},'reference_agreement':{},
            'weight_total':sum(u.get('weight',1) for u in units)}
    for ref in references:
        result['methods'][ref]={}
        for dim in DIMS:
            common=[u for u in units if label(u['references'][ref][dim]) in (0,1)
                    and all(label(u['predictions'][m][dim]) in (0,1) for m in methods)]
            result['methods'][ref][dim]={'common_unit_n':len(common),
                'common_weight':sum(u.get('weight',1) for u in common),'by_method':{}}
            for method in methods:
                pair=lambda selected,weighted:[(u['predictions'][method][dim],u['references'][ref][dim],
                    u.get('weight',1) if weighted else 1) for u in selected]
                result['methods'][ref][dim]['by_method'][method]={
                    'all_units_unweighted':summarize(pair(units,False)),
                    'all_units_weighted':summarize(pair(units,True)),
                    'common_units_unweighted':summarize(pair(common,False)),
                    'common_units_weighted':summarize(pair(common,True))}
    if len(references)==2:
        for dim in DIMS:
            result['reference_agreement'][dim]={
                'unweighted':agreement([(u['references'][references[0]][dim],u['references'][references[1]][dim],1) for u in units]),
                'weighted':agreement([(u['references'][references[0]][dim],u['references'][references[1]][dim],u.get('weight',1)) for u in units])}
    return result
