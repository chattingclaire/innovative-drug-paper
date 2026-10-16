"""Source-bounded I3 tests; synthetic mutations are never written as real inputs."""
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE / 'code'))
from relations import RelationView
from dimensions import judge
from evidence import validate_decisions

PATHS = {
    '02210': 'I3_same_route_historical_rnd_support',
    '03452': 'I3_regulatory_research_design_discussion',
    '04169': 'I3_professional_participation_in_research_feedback',
    '04189': 'I3_priority_expert_consultation_in_review',
}
units = {}
for row in map(json.loads, (ROOT / '06-coding/rule-full4481-v2-root/run4481-first/effective-semantic-units.jsonl').open()):
    short = row['id'].rsplit('-', 1)[-1]
    if short in PATHS:
        units[short] = row['semantic_unit']


def replace_strings(value, old, new):
    if isinstance(value, str):
        return value.replace(old, new)
    if isinstance(value, list):
        return [replace_strings(v, old, new) for v in value]
    if isinstance(value, dict):
        return {k: replace_strings(v, old, new) for k, v in value.items()}
    return value


def current(unit, new):
    return replace_strings(unit, unit['text'], new)


results = []


def check(name, key, unit, expected_path, expected_value='unspecified'):
    view = RelationView(unit)
    ds = judge(view)
    validate_decisions(view.unit, ds)
    decision = ds['I']
    paths = [decision['basis_path']] + [e['basis_path'] for e in decision.get('details', {}).get('additional_evidence', [])]
    found = PATHS[key] in paths
    passed = found == expected_path and (expected_value == 'unspecified' or decision['value'] == expected_value)
    results.append({'name': name, 'target': key, 'expected_path': expected_path, 'has_path': found,
                    'expected_value': expected_value, 'value': decision['value'], 'passed': passed,
                    'current': unit['text'], 'decision': decision})


for key, source in units.items():
    check('original_' + key, key, copy.deepcopy(source), True, 1)
    base = source['text'].rstrip('。')
    check('quoted_upload_' + key, key, current(source, '上传写有“' + base + '”的文件。'), False)
    check('column_name_' + key, key, current(source, '栏目名称：“' + base + '”。'), False)
    check('unquoted_form_' + key, key, current(source, '在表格中填写：' + base + '。'), False)
    check('mixed_form_then_actual_' + key, key, current(source, '上传写有“' + base + '”的文件；' + source['text']), True, 1)
    check('mixed_actual_then_form_' + key, key, current(source, source['text'].rstrip('。') + '，并在申请表签字盖章。'), True, 1)
    changed = copy.deepcopy(source)
    for ctx in changed['contexts']:
        if ctx['kind'] in ('preceding_paragraph', 'source_fragment', 'source_paragraph', 'following_heading'):
            ctx['source_ref']['sha256'] = 'b' * 64
    check('cross_source_' + key, key, changed, False)
    changed = copy.deepcopy(source)
    changed['structure'] = {'component_id': 'CURRENT'}
    for ctx in changed['contexts']:
        ctx.setdefault('structure', {})['component_id'] = 'OTHER'
    check('cross_component_' + key, key, changed, False)

source = units['02210']
check('historical_different_route', '02210', current(source, source['text'].replace('60日', '90日')), False)
changed = copy.deepcopy(source)
for ctx in changed['contexts']:
    if ctx['kind'] == 'preceding_paragraph':
        ctx['text'] = ctx['text'].replace('有力推动了创新药研发提速', '并未推动创新药研发提速')
check('historical_denied_support_link', '02210', changed, False)
changed = copy.deepcopy(source)
for ctx in changed['contexts']:
    if ctx['kind'] == 'preceding_paragraph':
        ctx['text'] = '30日通道为创新药研发提供优先资源。60日制度仅是一般登记管理。'
check('historical_later_route_not_borrowed', '02210', changed, False)
check('historical_name_only', '02210', current(source, '目录列有60日默示许可制度及其实施年份。'), False)

source = units['03452']
check('design_guidance_without_actual_service', '03452', current(source, '申请人应优化试验设计和实施，合理安排采样时间并采用可行的新技术。'), False)
check('design_only_meeting_format', '03452', current(source, '监管机构与申办方沟通可采用电话、视频或书面形式。'), False)
check('design_denied_actual_service', '03452', current(source, source['text'].replace('也是监管机构', '并非监管机构')), False)
changed = copy.deepcopy(source)
for ctx in changed['contexts']:
    if ctx.get('structure', {}).get('source_role') == 'self_declared_scope':
        ctx['text'] = ctx['text'].replace('提出创新药研发中的', '提出仿制药研发中的')
check('design_no_innovation_object', '03452', changed, False)
changed = copy.deepcopy(source)
for ctx in changed['contexts']:
    if ctx['kind'] == 'preceding_paragraph':
        ctx['text'] = '上市后常规诊疗服务应保持一般沟通。'
check('design_postmarketing_stage_mismatch', '03452', changed, False)

for key in ('04169', '04189'):
    source = units[key]
    changed = copy.deepcopy(source)
    marker = next(c for c in changed['contexts'] if c['kind'] == 'following_heading')
    omitted = marker['structure']['scope_context_ids'][3]
    changed['contexts'] = [c for c in changed['contexts'] if c['context_id'] != omitted]
    check('incomplete_scope_' + key, key, changed, False, None)
    changed = copy.deepcopy(source)
    for ctx in changed['contexts']:
        if ctx['kind'] == 'source_paragraph' and '适用范围:' in ctx.get('text', ''):
            ctx['text'] = '(一)适用范围:非创新药。'
    check('noninnovation_scope_' + key, key, changed, False)
    changed = copy.deepcopy(source)
    for ctx in changed['contexts']:
        if ctx['kind'] == 'heading':
            ctx['text'] = '(五)上市后常规监测'
    check('wrong_service_stage_' + key, key, changed, False)

source = units['04169']
check('invite_only_attendance', '04169', current(source, source['text'].rstrip('。') + '，这些机构仅负责签到。'), False)
check('invite_only_attendance_suffix', '04169', current(source, source['text'] + '上述机构仅负责签到，不涉及研究方案。'), False)
check('invite_denied', '04169', current(source, source['text'].replace('应邀请', '不邀请')), False)
changed = copy.deepcopy(source)
for ctx in changed['contexts']:
    if ctx['kind'] == 'preceding_paragraph':
        ctx['text'] = '药审中心与申请人仅沟通材料签章与报销手续。'
check('invite_missing_technical_feedback', '04169', changed, False)

source = units['04189']
changed = copy.deepcopy(source)
for ctx in changed['contexts']:
    if ctx['kind'] == 'paragraph':
        ctx['text'] = ctx['text'].replace('药审中心优先组织专家咨询会', '药审中心不组织专家咨询会')
check('consultation_denied_priority_service', '04189', changed, False)
changed = copy.deepcopy(source)
for ctx in changed['contexts']:
    if ctx['kind'] == 'paragraph':
        ctx['text'] = ctx['text'].replace('药审中心优先组织专家咨询会', '以上仅为一般会议，另一个项目由药审中心优先组织专家咨询会')
check('consultation_other_meeting_not_borrowed', '04189', changed, False)
check('consultation_meeting_name_only', '04189', current(source, '专业部门应填写需要召开专家咨询会的日期。'), False)

report = {'purpose': 'development boundary tests, not new independent validation',
          'dimensions_sha256': hashlib.sha256((HERE / 'code/dimensions.py').read_bytes()).hexdigest(),
          'passed': sum(r['passed'] for r in results), 'total': len(results), 'cases': results}
(HERE / 'round5-local-support-tests.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
print(json.dumps({k: report[k] for k in ('dimensions_sha256', 'passed', 'total')} | {
    'failed': [{'name': r['name'], 'value': r['value'], 'has_path': r['has_path']} for r in results if not r['passed']]}, ensure_ascii=False))
if any(not r['passed'] for r in results):
    raise SystemExit(1)
