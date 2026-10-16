"""Synthetic-only presentation QA; never open D668 materials or study labels."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

import d668_analysis_bridge as bridge
import d668_statistics as stats
from test_d668_analysis_bridge_synthetic import fixture as join_fixture
import render_d668_report as render


def fixture():
    rmap, dmap, documents, design = join_fixture()
    payload, provenance = bridge.assemble_rows(rmap, dmap, documents, design)
    payload['data_kind'] = 'synthetic_test'
    statistics = stats._analyze_synthetic(payload)
    tracked = {}
    root = Path('/SYNTHETIC_ONLY_NEVER_READ')

    def entry(name, value):
        raw = render.original_encoding(value)
        p = str(root / name)
        h = render.sha(raw)
        tracked[p] = h
        return {'path': p, 'sha256': h, 'byte_count': len(raw)}

    manifests = {'R': {}, 'D': {}}
    rsource = {'n': 600, 'N_R': 1531, 'protocol_version': 'SYNTHETIC_ONLY', 'raw_submissions': {}}
    for phase in ('R', 'D'):
        for relative, doc in documents[phase].items():
            raw = render.original_encoding(doc)
            manifests[phase][relative] = {'sha256': render.sha(raw), 'byte_count': len(raw)}
            if phase == 'R':
                rsource['raw_submissions'][relative] = {
                    'original': entry('R-original/' + relative, doc),
                    'first_receipt': entry('R-first-receipt/' + relative, doc)}
            else:
                entry('D-release/' + relative, doc)
    rsource['source_original_freeze'] = entry('R-freeze.json', {'synthetic_only': True})
    rsource['source_release_seal'] = entry('R-seal.json', {'synthetic_only': True})
    rsource['source_mapping'] = entry('R-mapping.json', rmap)
    files = {key: entry('code/' + key, {'synthetic_code_placeholder': key}) for key in
             ('analysis_bridge', 'statistics', 'admin_receiver', 'protocol', 'protocol_clarifications')}
    files['r600_source_manifest'] = entry('R-source-manifest.json', rsource)
    files['v600_sampling_manifest'] = rsource['source_mapping']
    for j in range(13):
        files[f'synthetic_frozen_item_{j}'] = entry(f'extra-{j}.json', {'synthetic_only': j})
    runtime = {'python_version': 'SYNTHETIC_PYTHON', 'numpy': 'SYNTHETIC_NUMPY', 'scipy': 'SYNTHETIC_SCIPY'}
    freeze = {'status': 'frozen_for_D668_supplementary_AI_content_analysis', 'phase': 'D668',
              'release_directory': str(root / 'D-release'), 'protocol_version': 'SYNTHETIC_ONLY',
              'runtime': runtime, 'files': files}
    freeze_hash = entry('D-freeze.json', freeze)['sha256']
    dmap_entry = entry('D-release/抽样清单-研究者.json', dmap)
    seal = {'freeze_manifest_sha256': freeze_hash, 'phase': 'D668', 'n': 668, 'N_star': 3393,
            'release_status': 'ready_for_blind_review', 'input_hashes': {k: v['sha256'] for k, v in files.items()},
            'output_files': {'抽样清单-研究者.json': dmap_entry['sha256']}}
    result = {'status': 'completed_supplementary_AI_content_analysis_not_human_validation', 'phase': 'R600_plus_D668',
              'synthetic_test': True, 'statistics': statistics,
              'archive': {'freeze_original': freeze, 'release_seal_original': seal,
                          'R_source_manifest_original': rsource, 'R_mapping_original': rmap, 'D_mapping_original': dmap,
                          'raw_coder_submissions': documents, 'original_submission_manifest': manifests,
                          'normalized_analysis_payload': payload, 'ID_join_provenance': provenance,
                          'input_snapshot_hashes': tracked, 'verified_runtime': runtime,
                          'no_machine_predictions_or_consensus_used': True}}
    return result, freeze_hash


class ReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.freeze_hash = fixture()

    def draw(self, obj=None, expected_hash=None):
        obj = self.original if obj is None else obj
        return render.render_result(obj, render.sha(render.original_encoding(obj)), '/SYNTHETIC_ONLY/result.json',
                                    expected_hash or self.freeze_hash, synthetic_test=True)

    def test_all_290_source_rows_preserved_exactly_and_all_table_counts(self):
        markdown = self.draw()
        audit = render.build_source_audit(self.original, render.sha(render.original_encoding(self.original)))
        exact = audit['source_rows']
        self.assertEqual(len(exact), 290)
        self.assertNotIn('```json', markdown)
        self.assertIn('并不代表更高统计精度', markdown)
        for name, count in render.COUNTS.items():
            if name == 'stratum_coder_dimension_counts':
                continue
            for i, row in enumerate(self.original['statistics'][name]):
                pointer = f'/statistics/{name}/{i}'
                self.assertEqual(exact[pointer], row)
                self.assertIn(f'`{pointer}`', markdown)
                if 'proportion' in row:
                    self.assertIn(render.percentage(row['proportion']), markdown)
                    self.assertIn(render.interval(row['confidence_interval']), markdown)
            self.assertEqual(sum(k.startswith(f'/statistics/{name}/') for k in exact), count)
        self.assertIn('合成软件测试', markdown)
        self.assertIn('1268', markdown)
        self.assertIn('不是新的未见样本验证', markdown)

    def test_summary_uses_both_AI_complete_rows_and_original_support_fields(self):
        markdown = self.draw()
        self.assertIn('4924 个分析单元', markdown)
        self.assertIn('1268 个唯一分析单元', markdown)
        self.assertNotIn('4924 篇', markdown)
        self.assertNotIn('1268 篇', markdown)
        self.assertIn('制度系统单次归属', markdown)
        self.assertIn('不能全部归因于某一个机关的偏好', markdown)
        supported = sum(r['robust_to_design_error_and_pending'] for r in self.original['statistics']['common_robust_directions'])
        self.assertIn(f'标记 {supported} 个共同稳健方向', markdown)
        for coder in ('A', 'C'):
            values = [r['proportion'] for r in self.original['statistics']['department_status_estimates']
                      if r['coder'] == coder and r['measure'] == 'pending']
            self.assertIn(f'AI {coder} 的 20 个部门×维度待定点估计范围为 {render.percentage(min(values))}—{render.percentage(max(values))}', markdown)

    def test_tiny_nonzero_endpoint_never_prints_zero(self):
        for value in (1e-8, -1e-8, 1e-12, -1e-12):
            text = render.percentage(value)
            self.assertNotIn('0.000%', text)
            self.assertNotEqual(float(text.removesuffix('%')), 0)

    def test_missing_state_difference_common_source_or_wrong_hash_rejected(self):
        changes = [
            lambda r: r.__setitem__('status', 'unfinished'),
            lambda r: r['statistics']['department_status_estimates'].pop(),
            lambda r: r['statistics']['department_potential_positive_estimates'].pop(),
            lambda r: r['statistics']['coder_pairwise_differences'].pop(),
            lambda r: r['statistics']['common_robust_directions'].pop(),
            lambda r: r['archive']['original_submission_manifest']['R'].pop('agent-A/结果-01.json'),
            lambda r: r['archive']['raw_coder_submissions']['D']['agent-C/结果-01.json']['rows'].pop(),
            lambda r: r['archive']['freeze_original'].__setitem__('phase', 'WRONG'),
            lambda r: r['archive']['release_seal_original'].__setitem__('freeze_manifest_sha256', '0' * 64),
            lambda r: r['statistics']['metadata'].__setitem__('unique_sample_units', 2536),
        ]
        for change in changes:
            altered = copy.deepcopy(self.original)
            change(altered)
            with self.assertRaises(ValueError):
                self.draw(altered)
        with self.assertRaises(ValueError):
            self.draw(expected_hash='1' * 64)

    def test_synthetic_cannot_render_in_observed_mode(self):
        with self.assertRaises(ValueError):
            render.render_result(self.original, 'a' * 64, '/synthetic.json', self.freeze_hash)

    def test_presentation_does_not_mutate_object_or_input_bytes_and_refuses_overwrite(self):
        saved = copy.deepcopy(self.original)
        self.draw()
        self.assertEqual(self.original, saved)
        with tempfile.TemporaryDirectory(prefix='d668-SYNTHETIC-presentation-') as directory:
            source = Path(directory) / 'SYNTHETIC-result.json'
            output = Path(directory) / 'SYNTHETIC-report.md'
            raw = render.original_encoding(self.original)
            source.write_bytes(raw)
            outcome = render.write_report(source, output, self.freeze_hash, synthetic_test=True)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(outcome['source_sha256'], render.sha(raw))
            self.assertFalse(outcome['statistics_recomputed'])
            with self.assertRaises(ValueError):
                render.write_report(source, output, self.freeze_hash, synthetic_test=True)

    def test_renderer_has_no_statistical_import_or_external_file_reader(self):
        import ast
        tree = ast.parse(Path(render.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                self.assertFalse(any('d668_statistics' in item.name or 'scipy' in item.name for item in node.names))
            if isinstance(node, ast.ImportFrom):
                self.assertNotIn(node.module, ('d668_statistics', 'scipy'))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                self.assertNotIn(node.func.id, ('analyze', '_analyze_synthetic'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
