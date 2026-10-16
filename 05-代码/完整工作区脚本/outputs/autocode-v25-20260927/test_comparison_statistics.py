"""Synthetic mathematical checks; never read study labels."""
import itertools
import random
import unittest
from comparison_statistics import *

class MetricsTest(unittest.TestCase):
    def test_hand_calculated(self):
        pairs=[(1,1,3),(1,0,1),(0,1,2),(0,0,4)]
        r=summarize(pairs)
        self.assertEqual(r['conditional_scores']['precision'],.75)
        self.assertEqual(r['conditional_scores']['recall'],.6)
        self.assertEqual(r['conditional_scores']['f1'],2/3)
        self.assertAlmostEqual(agreement(pairs)['binary_agreement']['kappa'],.4)

    def test_no_positives_are_undefined(self):
        r=summarize([(0,0,10)])
        self.assertIsNone(r['conditional_scores']['precision'])
        self.assertIsNone(r['conditional_scores']['recall'])
        self.assertIsNone(r['conditional_scores']['f1'])

    def test_exhaustive_completions_match_bounds(self):
        rng=random.Random(7123)
        examples=[[(p,r,1)] for p in LEVELS for r in LEVELS]
        examples += [[(rng.choice(LEVELS),rng.choice(LEVELS),rng.choice([1,2,.5]))
                      for _ in range(rng.randrange(1,6))] for _ in range(120)]
        for pairs in examples:
            actual=completion_bounds(matrix(pairs));all_scores=[]
            choices=[[(pp,rr,w) for pp in ((0,1) if p=='待定' else (p,))
                      for rr in ((0,1) if r=='待定' else (r,))] for p,r,w in pairs]
            for completed in itertools.product(*choices):
                conf={k:0. for k in ('TP','FP','FN','TN')}
                for p,r,w in completed:conf[confusion_cell(p,r)]+=w
                all_scores.append(scores(conf))
            for k,bounds in actual.items():
                values=[v[k] for v in all_scores if v[k] is not None]
                self.assertEqual(bounds['undefined_completion_possible'],any(v[k] is None for v in all_scores))
                for name,fn in [('min',min),('max',max)]:
                    if values:self.assertAlmostEqual(bounds[name],fn(values))
                    else:self.assertIsNone(bounds[name])

    def test_pending_not_deleted_or_counted_negative(self):
        r=summarize([(1,1,1),('待定',1,9)])
        self.assertEqual(r['conditional_scores']['recall'],1)
        self.assertEqual(r['joint_determinate_coverage'],.1)
        self.assertEqual(r['binary_completion_bounds_not_confidence_intervals']['recall']['min'],.1)
        self.assertEqual(r['binary_completion_bounds_not_confidence_intervals']['recall']['max'],1)

    def test_invalid_missing_bool_and_weight_rejected(self):
        for value in [None,'',True,False,2]:
            with self.assertRaises(ValueError):summarize([(value,0,1)])
        for w in [0,-1,float('nan'),True]:
            with self.assertRaises(ValueError):summarize([(0,0,w)])

    def test_shared_denominator(self):
        def unit(i,x,y):
            return {'id':i,'predictions':{'x':dict.fromkeys(DIMS,x),'y':dict.fromkeys(DIMS,y)},
                    'references':{c:dict.fromkeys(DIMS,1) for c in ('A','C')}}
        r=evaluate_units([unit('one',1,1),unit('two',0,'待定')],['x','y'])
        d=r['methods']['A']['S']
        self.assertEqual(d['common_unit_n'],1)
        for m in ('x','y'):
            self.assertEqual(d['by_method'][m]['common_units_unweighted']['conditional_scores']['recall'],1)
        self.assertEqual(d['by_method']['x']['all_units_unweighted']['conditional_scores']['recall'],.5)

if __name__=='__main__':unittest.main()
