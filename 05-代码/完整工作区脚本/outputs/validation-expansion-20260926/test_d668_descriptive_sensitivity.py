"""Synthetic-only checks for the separately predeclared descriptive scenarios."""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import unittest

HERE = Path(__file__).resolve().parent
def module(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
s = module('d668_descriptive_sensitivity')
stats = module('d668_statistics')


def fixture():
    design = stats.frozen_design(); units = []; links = []; docs = {'R': {}, 'D': {}}; raw = {}; seq = {'R': 0, 'D': 0}
    for phase, batches in [('R', 24), ('D', 27)]:
        for c in s.CODERS:
            for b in range(1, batches+1): docs[phase][f'agent-{c}/结果-{b:02d}.json'] = {'coder': c, 'rows': []}
    for h in design['strata']:
        phase = h['phase']
        for _ in range(h['n']):
            seq[phase] += 1; idx = seq[phase]; uid = f'SYNTHETIC-{phase}-{idx:04d}'; blind = f'SYNTHETIC-BLIND-{phase}-{idx:04d}'
            units.append({'unit_id': uid, 'stratum_id': h['stratum_id'], 'labels': {}})
            links.append({'review_id': uid, 'stratum_id': h['stratum_id'], 'phase': phase, 'blind_id': blind})
            for c in s.CODERS:
                row = {'id': blind, 'labels': {d: 0 for d in s.DIMS}, 'safety_quality_basis': 'no_quality_basis',
                       'innovation_subtypes': [], 'fairness_subtypes': []}
                docs[phase][f'agent-{c}/结果-{(idx-1)//25+1:02d}.json']['rows'].append(row); raw[uid, c] = row
    def change(idx, dim, **fields):
        row = raw[f'SYNTHETIC-R-{idx:04d}', 'A']; row['labels'][dim] = 1; row.update(fields)
    change(1, 'S', safety_quality_basis='quality_only')
    change(2, 'S', safety_quality_basis='quality_and_other')
    change(3, 'I', innovation_subtypes=['qualification_advantage'])
    change(4, 'I', innovation_subtypes=['qualification_advantage', 'attribute'])
    change(5, 'F', fairness_subtypes=['clinical_management'])
    change(6, 'F', fairness_subtypes=['clinical_management', 'access'])
    change(7, 'F', fairness_subtypes=['dimension_information'])
    change(8, 'F', fairness_subtypes=['dimension_information', 'affordability'])
    row = raw['SYNTHETIC-R-0009', 'A']; row['labels']['F'] = '待定'
    for unit in units:
        unit['labels'] = {c: s.normalized(raw[unit['unit_id'], c]['labels']) for c in s.CODERS}
    primary = {'status': 'completed_supplementary_AI_content_analysis_not_human_validation',
               'archive': {'normalized_analysis_payload': {'data_kind': 'observed_coding', 'design': design, 'units': units},
                           'raw_coder_submissions': docs, 'ID_join_provenance': links}}
    return primary, raw


class Tests(unittest.TestCase):
    def test_all_five_scenarios_separate_and_other_basis_preserved(self):
        p, _ = fixture(); result = s.analyze(p)
        self.assertEqual(len(result['scenarios']), 5)
        for scenario, expected in zip(result['scenarios'], [1, 1, 1, 1, 2]):
            self.assertEqual(scenario['status'], 'computed_descriptive_only')
            overall = next(x for x in scenario['estimates'] if x['coder'] == 'A' and x['department'] == 'overall')
            self.assertEqual(overall['changed_sample_count'], expected)
            self.assertEqual(len(scenario['estimates']), 10)
    def test_AI_C_unchanged_not_pooled(self):
        p, _ = fixture()
        for sc in s.analyze(p)['scenarios']:
            for row in sc['estimates']:
                if row['coder'] == 'C': self.assertEqual(row['changed_sample_count'], 0)
    def test_pending_and_fixed_denominators_preserved(self):
        p, _ = fixture()
        for sc in s.analyze(p)['scenarios']:
            for row in sc['estimates']:
                self.assertEqual(row['main_weighted_totals_exact']['pending'], row['scenario_weighted_totals_exact']['pending'])
                self.assertEqual(row['fixed_denominator'], 4924 if row['department'] == 'overall' else stats.FROZEN_DEPARTMENT_SIZES[row['department']])
    def test_input_never_mutated(self):
        p, _ = fixture(); before = copy.deepcopy(p); s.analyze(p); self.assertEqual(p, before)
    def test_missing_subtype_disables_whole_affected_scenarios(self):
        p, raw = fixture(); del raw['SYNTHETIC-R-0005', 'A']['fairness_subtypes']
        result = s.analyze(p)['scenarios']
        self.assertTrue(all(x['status'] == 'computed_descriptive_only' for x in result[:2]))
        self.assertTrue(all(x['status'] == 'not_computable_missing_or_invalid_own_metadata' and x['unrecodable_records'] == 1 for x in result[2:]))
    def test_inconsistent_raw_normalized_rejected(self):
        p, raw = fixture(); raw['SYNTHETIC-R-0001', 'A']['labels']['S'] = 0
        with self.assertRaises(ValueError): s.analyze(p)
    def test_missing_file_and_invalid_label_rejected(self):
        p, _ = fixture(); p['archive']['raw_coder_submissions']['D'].pop('agent-C/结果-27.json')
        with self.assertRaises(ValueError): s.analyze(p)
        p, raw = fixture(); raw['SYNTHETIC-R-0001', 'A']['labels']['S'] = True
        with self.assertRaises(ValueError): s.analyze(p)
    def test_no_new_inference_in_output(self):
        p, _ = fixture(); result = s.analyze(p)
        self.assertTrue(result['no_original_changes_imputation_CI_pvalues_or_inferential_rank'])
        for sc in result['scenarios']:
            self.assertTrue(sc['no_CI_pvalues_or_inferential_rank'])
            self.assertTrue(all('confidence_interval' not in x and 'p_value' not in x for x in sc['estimates']))


if __name__ == '__main__': unittest.main(verbosity=2)
