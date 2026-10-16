"""Fixed-200 descriptive comparison of AI-initial/human-reviewed labels.

Reads preserved originals and frozen production outputs; never admits formal
human validation, changes classifications, draws samples, or claims a CI.
"""
from collections import Counter
from datetime import datetime
from fractions import Fraction
import argparse
import ast
import hashlib
import json
from pathlib import Path
import posixpath
import xml.etree.ElementTree as ET
import zipfile
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DIMS = ('S', 'E', 'Ec', 'I', 'F')
HUMAN = HERE.parent / 'human200-readiness/incoming/20261012-145316-65d70fedff5c/真人标注汇总-200条.xlsx'
AI_ROOT = ROOT.parent / 'ai-blind200-20261012'
CORE = ROOT / '07-statistics/prospective-dynamic-domain-engine-sol/frozen_year_core.py'
EXPECTED_HUMAN = '65d70fedff5ce03226f59aad163c99b0e4d7a500102e0e257305c3be03fa3de1'
EXPECTED_CORE = 'f6b33491bb27d7325cdc18c25fb7d54fef45909e1ef38c3f27606edcb61c2262'
EXPECTED_DRAW = '5690672e10612371def277f7d98ed332e22cb281cfb5b636a9cbc93eaba1bd55'
EXPECTED_FREEZE = 'f6e2e2d08a4f4c448ea1bd8b1b07c51cc95b5f7d2eb35dd0c371fd6d1a961b80'
EXPECTED_FRAME = '5100cd0c0cee7cee629e1b95a89abd43a4e561a196f6b9e25f7023684c242612'
EXPECTED_TEMPLATE = '7b2c49a910f1f9e4fad1e83dff45c5a9890d2cf5fb20fa3b7a493456662ff3c9'
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
REL = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'


def binding(path):
    raw = Path(path).read_bytes()
    return {'path': str(Path(path).resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def check(path, sha):
    result = binding(path)
    assert result['sha256'] == sha, f'Changed input: {path}'
    return result


def workbook_cells(path):
    with zipfile.ZipFile(path) as z:
        strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            strings = [''.join(x.itertext()) for x in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS)]
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        sheets = wb.find('m:sheets', NS)
        assert len(sheets) == 1
        rels = {r.attrib['Id']: r.attrib['Target'] for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))}
        target = rels[sheets[0].attrib[REL + 'id']]
        part = target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/' + target)
        assert part.startswith('xl/') and '..' not in part.split('/')
        root = ET.fromstring(z.read(part))
        cells = {}
        for cell in root.findall('m:sheetData/m:row/m:c', NS):
            assert cell.find('m:f', NS) is None, 'Unexpected formula in original input'
            address = cell.attrib['r']
            assert address not in cells
            v = cell.find('m:v', NS)
            if cell.attrib.get('t') == 'inlineStr':
                value = ''.join(cell.find('m:is', NS).itertext())
            elif v is None:
                value = None
            elif cell.attrib.get('t') == 's':
                value = strings[int(v.text)]
            else:
                assert cell.attrib.get('t') != 'b', 'Boolean is not a binary human judgment'
                value = v.text
            cells[address] = value
        return cells


def main(output_dir=None):
    out = Path(output_dir).resolve() if output_dir else HERE / 'results'
    assert not out.exists(), 'Do not overwrite a completed comparison'
    inputs = {'human_original': check(HUMAN, EXPECTED_HUMAN), 'math_core': check(CORE, EXPECTED_CORE)}
    draw_path = ROOT / '09-delivery/human200-independent-preparation-root/coordinator-private/draw-and-mapping.json'
    inputs['draw'] = check(draw_path, EXPECTED_DRAW)
    draw = json.loads(draw_path.read_text())
    old = {r['A_blind_id']: r for r in draw['records']}
    assert len(old) == 200
    template = ROOT / '05-validation/human200-reception-root/templates/original-blank-A.xlsx'
    inputs['issued_template'] = check(template, EXPECTED_TEMPLATE)
    blank, actual = workbook_cells(template), workbook_cells(HUMAN)
    frame_path = HERE.parent / 'current-validation/exposure/candidate-frame.jsonl'
    inputs['exposure_frame'] = check(frame_path, EXPECTED_FRAME)
    frame = {r['source_id']: r for r in map(json.loads, frame_path.read_text().splitlines())}
    freeze_path = HERE.parent / 'current-validation/machine-freeze.json'
    inputs['machine_freeze'] = check(freeze_path, EXPECTED_FREEZE)
    freeze = json.loads(freeze_path.read_text())
    machines = {}
    for method, key in [('rule', 'rule_predictions'), ('LLM', 'LLM_records')]:
        spec = freeze['inputs'][key]
        assert binding(spec['path']) == spec
        inputs[method] = spec
        rows = [json.loads(line) for line in Path(spec['path']).read_text().splitlines()]
        machines[method] = {r['id']: r for r in rows}
        assert len(rows) == len(machines[method]) == 4481
    alignment_spec = freeze['inputs']['source_alignment']
    assert binding(alignment_spec['path']) == alignment_spec
    inputs['material_alignment'] = alignment_spec
    assert set(json.loads(Path(alignment_spec['path']).read_text())['material_changed_record_ids']).isdisjoint(r['source_id'] for r in old.values())
    # Execute only the unchanged two pure Fraction functions. The full engine's
    # scipy-dependent interval pipeline is not used for this descriptive task.
    tree = ast.parse(CORE.read_text())
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in ('_ratio', 'exact_metrics')]
    assert [node.name for node in functions] == ['_ratio', 'exact_metrics']
    math_namespace = {'Fraction': Fraction}
    exec(compile(ast.Module(body=functions, type_ignores=[]), str(CORE), 'exec'), math_namespace)
    records, seen = [], set()
    provenance = Counter()
    for row_number in range(2, 1002):
        for col in 'ABC':
            assert actual.get(f'{col}{row_number}') == blank.get(f'{col}{row_number}'), 'Original source columns changed'
        blind, dim = actual[f'A{row_number}'], actual[f'C{row_number}']
        assert blind in old and dim in DIMS and (blind, dim) not in seen
        seen.add((blind, dim))
        assignment = old[blind]
        source_id = assignment['source_id']
        raw_value = actual.get(f'D{row_number}')
        human_value = None if raw_value in (None, '') else int(raw_value)
        assert raw_value in (None, '', '0', '1')
        reason = actual.get(f'E{row_number}')
        assert f'记录：{source_id}；维度：{dim}。' in reason
        if reason.startswith('用户统一确认：'):
            recording_source = 'user_bulk_confirmation_of_AI_consensus'
            assert f'标注值为{human_value}。' in reason
        elif reason.startswith('用户逐项意见确认录入：'):
            recording_source = 'user_item_specific_confirmation'
            assert f'录入值为{human_value}。' in reason
        else:
            assert reason.startswith('待定：')
            recording_source = 'user_pending_discussion'
        if human_value is None:
            assert recording_source == 'user_pending_discussion'
        else:
            assert recording_source != 'user_pending_discussion'
        provenance[recording_source] += 1
        values = {}
        for method in ('rule', 'LLM'):
            machine = machines[method][source_id]
            value = machine['labels'][dim]
            assert value is None or type(value) is int and value in (0, 1)
            assert value == machine['decisions' if method == 'rule' else 'dimensions'][dim]['value']
            values[method] = value
        records.append({'source_id': source_id, 'A_blind_id': blind, 'dimension': dim,
                        'historical_domain': assignment['domain'], 'current_domain': frame[source_id]['candidate_domain'],
                        'original_stratum': assignment['stratum'], 'original_pi_exact': assignment['pi_exact'],
                        'original_weight_exact': assignment['weight_exact'], 'human_reviewed_value': human_value,
                        'human_state': 'pending_discussion' if human_value is None else 'reviewed_binary',
                        'recording_source': recording_source, 'recorded_reason': reason, **values})
    assert len(seen) == 1000
    assert provenance == {'user_bulk_confirmation_of_AI_consensus': 987, 'user_item_specific_confirmation': 9, 'user_pending_discussion': 4}
    summaries = []
    scopes = [('all200', None), ('historical_remaining120', 'remaining'), ('historical_exposed80', 'exposed')]
    for group, historical in scopes:
        group_rows = [r for r in records if historical is None or r['historical_domain'] == historical]
        for method in ('rule', 'LLM'):
            for dim in DIMS:
                rows = [r for r in group_rows if r['dimension'] == dim]
                states, raw_cells = Counter(), [0, 0, 0, 0]
                weighted = [Fraction(0) for _ in range(4)]
                for r in rows:
                    h, m = r['human_reviewed_value'], r[method]
                    states[f'{"pending" if h is None else h}|{"null" if m is None else m}'] += 1
                    if h is None or m is None:
                        continue
                    index = {(1, 1): 0, (1, 0): 1, (0, 1): 2, (0, 0): 3}[(m, h)]
                    raw_cells[index] += 1
                    weighted[index] += Fraction(r['original_weight_exact'])
                def metrics(cells):
                    result = math_namespace['exact_metrics'](cells)
                    return {k: None if v is None else float(v) for k, v in result.items()}
                common = sum(raw_cells)
                summaries.append({'group': group, 'method': method, 'dimension': dim, 'planned_N': len(rows),
                                  'common_binary_N': common, 'excluded_N': len(rows)-common,
                                  'human_pending_N': sum(r['human_reviewed_value'] is None for r in rows),
                                  'machine_lawful_null_N': sum(r[method] is None for r in rows),
                                  'machine_technical_failure_N': 0, 'joint_states_human_machine': dict(states),
                                  'cell_order': ['TP', 'FP', 'FN', 'TN'], 'raw_cells': raw_cells,
                                  'original_weighted_cells_exact': [str(v) for v in weighted],
                                  'raw_metrics': metrics(raw_cells), 'original_weighted_metrics': metrics(weighted),
                                  'formal_acceptance': False, 'independent_accuracy_CI': None})
    unique = {r['source_id']: r for r in records}
    crosswalk = Counter((r['historical_domain'], r['current_domain']) for r in unique.values())
    result = {'analysis_type': 'fixed200_AI_initial_human_reviewed_descriptive_comparison',
              'actual_user_confirmation': ['这个ai独立盲评就是真人标注的内容', '已经真人复核过了'],
              'created_at_shanghai': datetime.now(ZoneInfo('Asia/Shanghai')).isoformat(),
              'records_N': 200, 'dimension_slots_N': 1000, 'recording_source_counts': dict(provenance),
              'domain_crosswalk': [{'historical': a, 'current': b, 'N': n} for (a,b),n in sorted(crosswalk.items())],
              'pending': [{'source_id': r['source_id'], 'dimension': r['dimension'], 'reason': r['recorded_reason']} for r in records if r['human_reviewed_value'] is None],
              'numeric_comparisons': summaries, 'source_bindings': inputs,
              'scope': {'two_independent_human_firsts': False, 'machine_blind_reference_verified': False,
                        'formal_independent_validation_executed': False, 'formal_acceptance': False,
                        'new_draw_or_model_changes': False,
                        'historical_weights_role': 'descriptive_reweighting_only_not_current_population_accuracy',
                        'CI_reason': 'Fixed200 descriptive comparison with AI-linked human reference and adaptive historical sample; no supported current-population independent accuracy interval. Formal future validation CI requirement remains.'}}
    out.mkdir()
    (out/'comparison.json').write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    (out/'joined-dimension-records.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in records))
    def n(v): return 'NA' if v is None else f'{v:.3f}'
    lines = ['# AI初评与真人复核对照结果', '',
             '已按用户确认，将这份200条记录接纳为AI初评后经真人复核确认的结果。本报告比较它与当前4481条生产规则、LLM中同一批200条的编码。', '',
             '共有1000项维度判断：987项由AI一致值经统一确认后录入，9项来自逐项人工意见，4项仍待讨论。使用原件逐项核对来源，未修改标签或把待定补为0。', '',
             '表中Precision、Recall和F1以本复核结果为比较参照，表示本固定样本的相符程度。它们受参照与AI答案的来源关联影响，不作为独立准确性验收；本报告不计算双人真人一致性。', '',
             '原120/80为历史抽样分组，当前分别对应91条剩余＋29条曝光、80条曝光。原权重仅作诊断性重加权，不能据此估计当前全4481或剩余1261条的独立准确性。本次不附缺乏适用依据的总体95%区间；正式独立验证所要求的区间仍待实际独立样本与可信参照形成后计算。', '']
    for group, title in [('all200','全部200条'),('historical_remaining120','历史未曝光组120条'),('historical_exposed80','历史曝光组80条')]:
        lines += [f'## {title}', '', 'TP/FP/FN/TN以机器为预测、复核值为参照。人工待定与机器NULL可能重叠，排除数按并集计算；技术失败为0。', '',
                  '| 方法 | 维度 | 共同可比/计划 | 人工待定 | 机器NULL | TP/FP/FN/TN | κ | Precision | Recall | F1 |',
                  '|---|---|---:|---:|---:|---|---:|---:|---:|---:|']
        subset = [x for x in summaries if x['group']==group]
        for x in subset:
            m=x['raw_metrics']
            lines.append(f"| {'规则' if x['method']=='rule' else 'LLM'} | {x['dimension']} | {x['common_binary_N']}/{x['planned_N']} | {x['human_pending_N']} | {x['machine_lawful_null_N']} | {'/'.join(map(str,x['raw_cells']))} | {n(m['kappa'])} | {n(m['Precision'])} | {n(m['Recall'])} | {n(m['F1'])} |")
        lines += ['', '按原设计权重重加权的诊断性指标：', '', '| 方法 | 维度 | κ | Precision | Recall | F1 |', '|---|---|---:|---:|---:|---:|']
        for x in subset:
            m=x['original_weighted_metrics']
            lines.append(f"| {'规则' if x['method']=='rule' else 'LLM'} | {x['dimension']} | {n(m['kappa'])} | {n(m['Precision'])} | {n(m['Recall'])} | {n(m['F1'])} |")
        lines.append('')
    lines += ['## 待讨论记录', '']
    lines += [f"- {p['source_id']} / {p['dimension']}：{p['reason']}" for p in result['pending']]
    lines += ['', '原120/80分组、抽样概率和权重均未改写；全部200条、1000项均保留在逐项记录中。数学指标直接复用原冻结核心的四格纯函数，未开启正式验证入口，未修改模型、重新抽样或重试机器任务。', '',
              '[原件保存记录](../../human200-readiness/incoming/20261012-145316-65d70fedff5c/receipt.json) · [完整指标与输入绑定](comparison.json) · [逐项对应记录](joined-dimension-records.jsonl)', '']
    (out/'AI初评与真人复核对照结果.md').write_text('\n'.join(lines))
    print(json.dumps({'records':200, 'slots':1000, 'pending':len(result['pending']), 'raw_all200':[{k:x[k] for k in ('method','dimension','common_binary_N','raw_cells','raw_metrics')} for x in summaries if x['group']=='all200'], 'formal_acceptance':False}, ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir')
    main(parser.parse_args().output_dir)
