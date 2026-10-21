"""No-model, no-classifier v3 single-control supplement; preserve v2 reports."""
from pathlib import Path
import datetime
import hashlib
import importlib.util
import json
import sys
sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
BASE = OUT.parent
ROOT = Path('/PROJECT_ROOT')
def read(p): return json.loads(Path(p).read_text())
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def normalize_new_paths(x):
    if isinstance(x, str): return x.replace(str(BASE / 'design-v3'), str(BASE / 'design-v2'))
    if isinstance(x, list): return [normalize_new_paths(y) for y in x]
    if isinstance(x, dict): return {k: normalize_new_paths(v) for k, v in x.items()}
    return x
def main():
    newdir = BASE / 'design-v3'
    assert sha(newdir / 'controls_FULL5_FROZEN.json') == 'b39327e4af68075d0679a95e415cf99c17f031a8d0c1cd777ae59c20b83a8422'
    assert sha(newdir / 'freeze_manifest.json') == '72f7de5c0d7361d282b17be7695078acc71c5d8d746d521d75c467acd622ab9c'
    manifest = read(newdir / 'freeze_manifest.json')
    assert manifest['before_adverb_fix_output'] is True and len(manifest['files']) == 66
    bindings = []
    for relative, value in manifest['files'].items():
        path = BASE / relative
        assert sha(path) == value
        bindings.append({'path': str(path), 'sha256': value})
    old = {c['id']: c for c in read(BASE / 'design-v2/controls_FULL5_FROZEN.json')['controls']}
    new = {c['id']: c for c in read(newdir / 'controls_FULL5_FROZEN.json')['controls']}
    assert len(old) == 31 and set(new) - set(old) == {'CHAN-P03'}
    for ident, before in old.items():
        assert normalize_new_paths(new[ident]) == before
        for key in ['unit_source', 'candidate_file']:
            assert Path(before['input'][key]).read_bytes() == Path(new[ident]['input'][key]).read_bytes()
    c = new['CHAN-P03']
    assert c['input_text'] == c['paragraph'] == '医保平台应连通医疗机构与定点零售药店，确保电子处方顺利流转。'
    independent = {'S': 0, 'E': 0, 'Ec': 0, 'I': 0, 'F': 1}
    assert c['expected_labels'] == independent
    assert c['expected_subtype_requirements'] == {'F': ['access'], 'I': []}
    inp = c['input']
    assert inp['unit_text'] == c['input_text'] and inp['unit_id'] == c['id']
    assert inp['source'] == inp['unit_source'] and sha(inp['source']) == inp['source_sha256'] == inp['unit_source_sha256']
    assert sha(inp['candidate_file']) == inp['candidate_sha256']
    candidate = read(inp['candidate_file'])
    assert candidate['paragraphs'][0]['text'] == candidate['unit_candidates'][0]['text'] == c['input_text']
    assert Path(inp['unit_source']).read_text().splitlines()[0] == c['input_text']
    path = ROOT / 'outputs/coding-revision-20261008-r4/validation-state-audit/reserved_context_redactor.py'
    spec = importlib.util.spec_from_file_location('v3_supplement_mechanical_redactor', path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.ReservedContextRedactor().audit_object_no_full_match(read(newdir / 'controls_FULL5_FROZEN.json'))['no_remaining_full_normalized_reserved_unit_match']
    assert all(sha(b['path']) == b['sha256'] for b in bindings)
    report = {'status': 'PASS_INDEPENDENT_V3_CONTROL_SUPPLEMENT_NOT_IMPLEMENTATION_CERTIFICATION',
        'reviewed_at_UTC': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'prior_v2_report': {'path': str(OUT / 'rules39_design_v2_independent_semantic_preflight.json'),
            'sha256': sha(OUT / 'rules39_design_v2_independent_semantic_preflight.json'),
            'precision_addendum': str(OUT / 'metadata_status_precision_addendum.json'), 'retained_unchanged': True},
        'design_manifest': {'path': str(newdir / 'freeze_manifest.json'), 'sha256': sha(newdir / 'freeze_manifest.json'), 'files_verified': 66,
                            'before_adverb_fix_output': True, 'v2_prior_development_output_not_hidden': True},
        'source_bindings': bindings, 'blocking_findings': [],
        'old31': {'exact_control_objects_unchanged_except_design_directory_paths': True,
                  'all31_raw_source_and_candidate_fixture_bytes_identical': True, 'no_expected_label_or_metadata_change': True},
        'new_control': {'id': c['id'], 'complete_current_input_read': c['input_text'], 'full_paragraph_read': c['paragraph'], 'articles': [],
            'independent_labels': independent,
            'per_dimension_reason': {'S': '无用药风险或质量安全内容，不能由医疗机构/处方平台补S。',
                'E': '无防治效果、疗效证据或治疗推荐。', 'Ec': '医保平台身份本身不说明药价/药费/支付责任。',
                'I': '信息平台和处方流转不属药物属性创新/创新研发支持。',
                'F': '医疗机构与定点零售药店连通并确保电子处方顺利流转，完整谓词表达常规处方获取渠道；顺利修饰流转不改变政策关系。'},
            'F_subtypes': ['access'], 'I_subtypes': [], 'S_quality_basis': 'no_quality_basis',
            'no_affordability_or_management_difficulty_inferred': True, 'continuous_unit_evidence_required': True,
            'source_and_candidate_SHA_and_line_binding_verified': True},
        'scope_after_supplement': {'controls': 32, 'semantic_controls': 31, 'semantic_dimension_cells': 155, 'technical_missing_material_controls': 1},
        'limits': ['Current positive supports the same actual channel relationship, not general adverbs or generic platforms.',
            'Actual classifier behavior, exact evidence offsets and inherited controls still require testing.',
            'v3 follows exposed old180 development findings; it is not a new independent validation sample.',
            'No full4924/production/manuscript authorization or metric-target guarantee.'],
        'source_files_modified': False, 'real180_raw_or_A_B_T_read': False, 'classifier_runs': 0, 'model_calls': 0}
    out = OUT / 'rules39_design_v3_independent_supplement.json'
    assert not out.exists()
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'path': str(out), 'sha256': sha(out), 'status': report['status'], 'model_calls': 0, 'classifier_runs': 0}, ensure_ascii=False))
if __name__ == '__main__': main()
