"""Independent synthetic ID-join QA. No policy labels or real inputs are read."""
import copy
import random
import unittest

import numpy
import scipy
import d668_analysis_bridge as bridge
import d668_statistics as stats


def fixture():
    design = stats.frozen_design()
    mappings = {'R': {'rows': []}, 'D': {'rows': []}}
    documents = {'R': {}, 'D': {}}
    counter = {'R': 0, 'D': 0}
    for h in design['strata']:
        phase = h['phase']
        for j in range(h['n']):
            counter[phase] += 1
            index = counter[phase]
            blind_id = f'SYNTHETIC-{phase}-{index:04d}'
            row = {'id': blind_id, 'review_id': f'SYNTHETIC-GLOBAL-{phase}-{index:04d}',
                   'group': h['department'], 'stratum': h['stratum_id'].removeprefix('R|'),
                   'N_h': h['N'], 'n_h': h['n'], 'pi': h['n'] / h['N'],
                   'weight': h['N'] / h['n'],
                   'unit_text_sha256': bridge.sha(f'SYNTHETIC TEXT {phase} {index}'.encode())}
            mappings[phase]['rows'].append(row)
            batch = (index - 1) // 25 + 1
            for coder in bridge.CODERS:
                relative = f'agent-{coder}/结果-{batch:02d}.json'
                document = documents[phase].setdefault(relative, {'coder': coder, 'rows': []})
                labels = {dim: (0, 1, '待定')[(index + k + (coder == 'C')) % 3]
                          for k, dim in enumerate(bridge.DIMS)}
                document['rows'].append({'id': blind_id, 'labels': labels})
    return mappings['R'], mappings['D'], documents, design


def assemble(args):
    return bridge.assemble_rows(*args)


class PureJoinTests(unittest.TestCase):
    def test_complete_join_has_1268_unique_units_and_two_distinct_coders(self):
        payload, provenance = assemble(fixture())
        self.assertEqual(len(payload['units']), 1268)
        self.assertEqual(len({row['unit_id'] for row in payload['units']}), 1268)
        self.assertEqual(len(provenance), 1268)
        self.assertEqual(sum(row['phase'] == 'R' for row in provenance), 600)
        self.assertEqual(sum(row['phase'] == 'D' for row in provenance), 668)
        self.assertTrue(all(row['labels']['A'] != row['labels']['C'] for row in payload['units']))
        self.assertTrue(any(row['labels']['A']['S'] == 'pending' for row in payload['units']))
        # Validation only: no observed-labeled synthetic statistics are emitted.
        stats._validate(payload, synthetic=False)

    def test_shuffled_files_and_rows_join_by_ID_not_position(self):
        args = fixture()
        expected, _ = assemble(args)
        altered = copy.deepcopy(args)
        rng = random.Random(90210)
        for phase, documents in altered[2].items():
            names = list(documents)
            rng.shuffle(names)
            altered[2][phase] = {name: documents[name] for name in names}
            for document in altered[2][phase].values():
                rng.shuffle(document['rows'])
        rng.shuffle(altered[0]['rows'])
        rng.shuffle(altered[1]['rows'])
        rng.shuffle(altered[3]['strata'])
        got, _ = assemble(altered)
        self.assertEqual({u['unit_id']: u for u in expected['units']}, {u['unit_id']: u for u in got['units']})

    def test_machine_and_consensus_fields_are_never_consumed(self):
        args = fixture()
        expected, _ = assemble(args)
        args[0]['machine_predictions'] = object()
        args[1]['consensus'] = object()
        for mapping in args[:2]:
            for row in mapping['rows']:
                row['machine_label'] = object()
                row['consensus_labels'] = object()
        got, _ = assemble(args)
        self.assertEqual(got, expected)
        self.assertNotIn('machine_predictions', got)
        self.assertNotIn('consensus', got)

    def test_missing_or_extra_batch_document_rejected_even_if_rows_elsewhere(self):
        args = fixture()
        args[2]['R']['agent-A/结果-01.json']['rows'] += args[2]['R'].pop('agent-A/结果-02.json')['rows']
        with self.assertRaisesRegex(ValueError, '48 R or 54 D'):
            assemble(args)
        args = fixture()
        args[2]['D']['agent-A/结果-28.json'] = {'coder': 'A', 'rows': []}
        with self.assertRaises(ValueError):
            assemble(args)

    def test_missing_duplicate_extra_submission_row_rejected(self):
        for mode in ('missing', 'duplicate', 'unknown'):
            args = fixture()
            rows = args[2]['D']['agent-C/结果-01.json']['rows']
            if mode == 'missing':
                rows.pop()
            elif mode == 'duplicate':
                rows.append(copy.deepcopy(rows[0]))
            else:
                rows[0]['id'] = 'SYNTHETIC-UNKNOWN'
            with self.assertRaises(ValueError):
                assemble(args)

    def test_duplicate_global_ID_across_R_D_and_duplicate_blind_ID_rejected(self):
        args = fixture()
        args[1]['rows'][0]['review_id'] = args[0]['rows'][0]['review_id']
        with self.assertRaisesRegex(ValueError, 'global ID'):
            assemble(args)
        args = fixture()
        args[0]['rows'][1]['id'] = args[0]['rows'][0]['id']
        with self.assertRaisesRegex(ValueError, 'blind mapping ID'):
            assemble(args)

    def test_wrong_probability_weight_type_and_hash_rejected(self):
        for key, value in [('pi', .999), ('weight', 1), ('weight', True), ('pi', float('nan')),
                           ('weight', float('inf')), ('weight', '2.5'), ('unit_text_sha256', 'bad')]:
            args = fixture()
            args[0]['rows'][0][key] = value
            with self.assertRaises(ValueError):
                assemble(args)

    def test_illegal_labels_and_missing_or_extra_dimension_rejected(self):
        for value in (True, False, 2, -1, 0.0, '1', 'pending', None, ''):
            args = fixture()
            args[2]['R']['agent-A/结果-01.json']['rows'][0]['labels']['S'] = value
            with self.assertRaises(ValueError):
                assemble(args)
        for change in ('missing', 'extra'):
            args = fixture()
            labels = args[2]['D']['agent-C/结果-01.json']['rows'][0]['labels']
            if change == 'missing': labels.pop('F')
            else: labels['extra'] = 0
            with self.assertRaises(ValueError):
                assemble(args)

    def test_wrong_coder_identity_rejected(self):
        args = fixture()
        args[2]['R']['agent-A/结果-01.json']['coder'] = 'C'
        with self.assertRaisesRegex(ValueError, 'Coder identity'):
            assemble(args)

    def test_per_stratum_n_checked_independently_of_total_n(self):
        args = fixture()
        row = args[0]['rows'][0]
        target = next(h for h in args[3]['strata'] if h['stratum_id'] == 'R|NMPA|2021')
        row.update(stratum='NMPA|2021', N_h=target['N'], n_h=target['n'],
                   pi=target['n'] / target['N'], weight=target['N'] / target['n'])
        with self.assertRaisesRegex(ValueError, 'Per-stratum sample count'):
            assemble(args)

    def test_every_frozen_stratum_value_checked_not_only_total(self):
        args = fixture()
        args[3]['strata'][0]['N'] += 1
        args[3]['strata'][1]['N'] -= 1
        with self.assertRaisesRegex(ValueError, '29-stratum metadata'):
            assemble(args)

    def test_pure_join_does_not_mutate_inputs(self):
        args = fixture()
        saved = copy.deepcopy(args)
        assemble(args)
        self.assertEqual(args, saved)


class RuntimeAndJsonTests(unittest.TestCase):
    def test_frozen_runtime_exact_match_and_version_mismatch(self):
        import platform
        runtime = {'python_version': platform.python_version(), 'numpy': numpy.__version__, 'scipy': scipy.__version__}
        actual = bridge.validate_runtime(runtime)
        self.assertEqual(actual['scipy'], scipy.__version__)
        for key in ('python_version', 'numpy', 'scipy'):
            altered = {**runtime, key: 'WRONG'}
            with self.assertRaisesRegex(ValueError, 'runtime differs'):
                bridge.validate_runtime(altered)
        with self.assertRaises(ValueError):
            bridge.validate_runtime(None)

    def test_duplicate_JSON_keys_rejected(self):
        with self.assertRaises(ValueError):
            bridge.read_json(b'{"rows": [], "rows": []}')


if __name__ == '__main__':
    unittest.main(verbosity=2)
