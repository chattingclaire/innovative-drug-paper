"""Independent constructed controls through unseeded code_unit; no corpus read."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
PYTHON = '/LOCAL_HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3'
RUNTIMES = {
    'v36.2': PROJECT / 'outputs/coding-revision-20261007-r3/rules-v36.2-development/runtime',
    'v37.1': PROJECT / 'outputs/coding-revision-20261008-r4/rules-v37.1-development/runtime',
}
SCOPE = '药物临床试验期间，用于防治严重疾病的创新药或者改良型新药，申请人可以申请适用突破性治疗药物程序。'
CASES = [
    ('old-B01-right-term', '为促进药品创新发展，完善药品试验数据保护制度，给予新药6年数据保护期，现予发布。', 'I', 1, False, 'v1.4 I3专有数据期限；发布不删除独立权利。'),
    ('old-B02-right-scope', '为促进药品创新发展，扩大药品试验数据保护制度的适用范围至改良型新药，现予发布。', 'I', 1, False, '当前扩大明确药物权利适用范围。'),
    ('old-B03-catering-price', '药品按程序申报，会议餐饮采用采购最低价。', 'Ec', 0, False, '非药品采购价格不得借用前句药品对象。'),
    ('old-B03-consumables-price', '药品按程序申报，检验耗材采用采购最低价。', 'Ec', 0, False, '检验耗材与药价对象区分。'),
    ('old-B04-money-object', '在药品调配时，应防止误用科研经费。', 'S', 0, False, '误用宾语明确非药品。'),
    ('old-B05-subject-switch', '药审中心安排审评人员核对文件清单，申请人基于已有研究资料，对下一步研究方案提出意见或者建议。', 'I', 0, True, '申请人自提意见不能成为机构研发指导。'),
    ('positive-drug-price', '本药采用集采中选最高价计算。', 'Ec', 1, False, '当前明确药品取价。'),
    ('positive-medication-prevention', '在药品发放过程中，药师核对用药清单，应防止误选。', 'S', 1, False, '同一用药流程内连续控制动作和误选预防。'),
    ('negative-purpose-only', '为促进药品创新发展，完善药品试验数据保护制度，现予发布。', 'I', 0, False, '纯发布宗旨而无实体权利。'),
    ('positive-same-reviewer-advice', '药审中心安排审评人员沟通，审评人员基于已有研究资料，对下一步研究方案提出建议。', 'I', 1, True, '同一审评人员给出实质研究方案指导。'),
    ('negative-research-document-layout', '药审中心安排审评人员沟通，基于已有研究资料，对下一步研究方案的排版格式提出建议。', 'I', 0, True, '仅研究文档排版格式的建议仍属资料事务，不是实质研发指导。'),
    ('negative-research-filing-deadline', '药审中心安排审评人员沟通，基于已有研究资料，对下一步研究方案的报送截止时间提出建议。', 'I', 0, True, '仅资料报送截止时间建议不成为实体创新研发支持。'),
    ('positive-research-endpoint-guidance', '药审中心安排审评人员沟通，基于已有研究资料，对下一步研究方案的主要终点设置提出建议。', 'I', 1, True, '研究方案主要终点设置是实质研发内容。'),
    ('negative-price-clause-order', '药品按采购最低价条款的编排顺序登记。', 'Ec', 0, False, '当前仅按条款顺序登记，无实质价格取值。'),
    ('positive-independent-safety-preserved', '为促进药品创新发展，完善药品试验数据保护制度，评估药物安全性，现予发布。', 'S', 1, False, '纯创新宗旨排除不应删除独立安全评价。'),
]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save_new(path, content):
    if path.exists():
        assert path.read_text() == content
    else:
        path.write_text(content)


def snapshot(runtime):
    return {str(p.resolve()): sha(p) for p in sorted(runtime.glob('*.py'))}


def child(runtime, cases_file, output_file, version):
    sys.path.insert(0, str(runtime))
    from policy_coding_v27 import code_unit
    cases = json.loads(Path(cases_file).read_text())['cases']
    dest = HERE / 'constructed-source-fixtures' / version
    dest.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cases:
        text = c['text']
        record = {'unit_text': text}
        if c['scope_fixture']:
            source, candidate = dest / (c['name'] + '.txt'), dest / (c['name'] + '.json')
            source.write_text(SCOPE + '\n' + text + '\n')
            candidate.write_text(json.dumps({'paragraphs': [{'id': 'scope', 'text': SCOPE, 'pages': []}],
                                              'unit_candidates': [{'id': 'unit', 'text': text}]}, ensure_ascii=False))
            record.update(unit_source=str(source.resolve()), unit_source_sha256=sha(source),
                          candidate_file=str(candidate.resolve()), candidate_sha256=sha(candidate), unit_id='unit',
                          verified_innovation_scope_v27={'text': SCOPE, 'text_sha256': hashlib.sha256(SCOPE.encode()).hexdigest(),
                          'source_sha256': sha(source), 'original_unit_sha256': hashlib.sha256(text.encode()).hexdigest(),
                          'component': '突破性治疗程序', 'verified': True, 'locator': {'source_lines': [1], 'paragraph_id': 'scope'},
                          'component_binding': {'unit_id': 'unit', 'candidate_sha256': sha(candidate)}})
        result = code_unit(record)
        for evidence in result['evidence'] + result['suppressions']:
            if 'start' in evidence:
                assert text[evidence['start']:evidence['end']] == evidence['text']
        rows.append({**c, 'full_result': result, 'matches_predeclared_dimension': result['labels'][c['dimension']] == c['expected'],
                     'seed_evidence_used': False})
    Path(output_file).write_text(json.dumps({'version': version, 'rows': rows}, ensure_ascii=False, indent=2) + '\n')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--child', nargs=4)
    args = parser.parse_args()
    if args.child:
        child(*args.child)
        return
    declared = {'status': 'FROZEN_BEFORE_INDEPENDENT_CONSTRUCTED_EXECUTION', 'constructed_only': True,
                'cases': [{'name': n, 'text': t, 'dimension': d, 'expected': e, 'scope_fixture': scope, 'basis': basis}
                          for n, t, d, e, scope, basis in CASES]}
    case_path = HERE / 'independent_controls_predeclared.json'
    save_new(case_path, json.dumps(declared, ensure_ascii=False, indent=2) + '\n')
    before = {v: snapshot(p) for v, p in RUNTIMES.items()}
    for version, runtime in RUNTIMES.items():
        subprocess.run([PYTHON, '-B', str(Path(__file__).resolve()), '--child', str(runtime), str(case_path),
                        str(HERE / (version + '_constructed_results.json')), version], check=True)
    after = {v: snapshot(p) for v, p in RUNTIMES.items()}
    assert before == after, 'Author runtime changed while reviewing; repeat against a final freeze.'
    report = {'status': 'INDEPENDENT_CONSTRUCTED_EXECUTION_COMPLETE', 'author_code_unchanged_during_execution': True,
              'runtime_bindings': before, 'controls_sha256': sha(case_path), 'script_sha256': sha(__file__),
              'full_corpus_run': False, 'model_calls': 0, 'human_or_reserved_corpus_text_read': False}
    for version in RUNTIMES:
        rows = json.loads((HERE / (version + '_constructed_results.json')).read_text())['rows']
        report[version] = [{'name': r['name'], 'expected_dimension': r['dimension'], 'expected': r['expected'],
                            'observed': r['full_result']['labels'][r['dimension']], 'pass': r['matches_predeclared_dimension'],
                            'new_v37_evidence': [e for e in r['full_result']['evidence'] if e['rule'].startswith(('V37_', 'V371_'))]}
                           for r in rows]
    (HERE / 'independent_constructed_summary.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({v: [{'name': r['name'], 'observed': r['observed'], 'expected': r['expected']} for r in report[v]] for v in RUNTIMES}, ensure_ascii=False))


if __name__ == '__main__':
    main()
