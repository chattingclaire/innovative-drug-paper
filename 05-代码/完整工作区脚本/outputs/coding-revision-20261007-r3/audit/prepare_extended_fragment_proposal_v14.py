"""Propose source-only fragment-parent repairs; never modify frozen inputs."""
from pathlib import Path
from collections import defaultdict
import copy
import hashlib
import json
import subprocess
import unicodedata

B = Path(__file__).resolve().parents[1]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest = lambda s: hashlib.sha256(s.encode()).hexdigest()
norm = lambda s: ''.join(c for c in unicodedata.normalize('NFKC', s) if c.isalnum())
ll = [json.loads(s) for s in (B / 'effective_blind_inputs_v13.jsonl').read_text().splitlines()]
rr = {x['id']: x['input'] for x in map(json.loads, (B / 'rule_inputs_shared_v13.jsonl').read_text().splitlines())}
lb = {x['id']: x for x in ll}
lists = {x['id']: x for x in json.loads((B / 'audit/necessary_list_completion_proposal_v11.json').read_text())['proposals']}
inventory = json.loads((B / 'audit/extended_numbered_list_parent_inventory_v13.json').read_text())['items']
byhead = defaultdict(list)
for x in inventory:
    byhead[x['source_list_head_id']].append(x)


def texts(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k == 'text' and isinstance(v, str):
                yield v
            else:
                yield from texts(v)
    elif isinstance(o, list):
        for v in o:
            yield from texts(v)


# Reviewed actual source relationships, not an automatic rank/marker decision.
reasons = {
    'RECODE25-01530': '资料模板的研究描述子项缺少申请人应阐述以下内容的控制谓词；不是对研究内容本身新增独立要求。',
    'RECODE25-02986': '问题式子项属于评估真实世界数据与临床问题相关性的重要因素；当前只有数据适用性章题，缺实际评估对象与关系。',
    'RECODE25-03947': '特殊情形列举受伦理委员会重点审查权益与安全保护的谓词控制；子项本身不是一般入组许可。',
    'RECODE25-04338': '具有资格/培训经历的半句主语是从事处方审核的药师，且属于其须满足的条件。',
    'RECODE25-04367': '疑问式审核子项缺实际西药及中成药处方的应审核范围与谓词；同章另有中药饮片并列分支。',
    'RECODE25-04377': '疑问式审核子项缺实际中药饮片处方的应审核范围与谓词；不得借西药分支解释。',
    'RECODE25-04386': '场所、人员、工具、制度是开展处方审核的必备条件，不是药品本身的条件。',
    'RECODE25-04418': '名词式管理工作子项缺省级药监部门负责本行政区域的实际主体及职责谓词。',
    'RECODE25-04514': '药品类型/情形子项缺可以直接提出非处方药上市申请的控制谓词。',
    'RECODE25-04566': '药品类别半句缺中检院或指定机构承担注册检验的主体和实际谓词。',
    'RECODE25-04589': '申请人所获程序支持受对纳入突破性治疗程序的药物临床试验限定；只补实际源资格，不推断维度。',
    'RECODE25-04594': '药品情形子项缺药物临床试验期间可以申请附条件批准的资格关系。',
    'RECODE25-04613': '优先安排/补交等支持受对纳入优先审评审批程序的上市申请限定；只补实际源资格。',
    'RECODE25-04631': '变更事项名词子项缺持有人以补充申请申报、经批准实施的控制谓词。',
    'RECODE25-04636': '变更事项名词子项缺变更实施前向所在地省级监管部门备案的控制谓词。',
    'RECODE25-04643': '变更事项子项缺持有人在年度报告中报告的控制谓词。',
    'RECODE25-04687': '情形子项缺注册申请不予批准的否定性控制谓词，不能单凭药品/资料内容推测。',
    'RECODE25-04720': '时间类半句缺不计入相关工作时限的控制谓词。',
    'RECODE25-04738': '情形子项缺国家药监局注销注册证书并公布的控制谓词。',
}
families = []
proposals = []
for headid, reason in reasons.items():
    src = lists[headid]
    interval = copy.deepcopy(src['complete_contiguous_interval'])
    parent = interval[0]
    assert all(c['verification']['verified'] for c in interval)
    assert sha(src['source_path']) == src['source_sha256']
    assert sha(src['candidate_path']) == src['candidate_sha256']
    cp = json.loads(Path(src['candidate_path']).read_text())
    ps = cp['paragraphs']
    ix = {p['id']: i for i, p in enumerate(ps)}
    assert [c['paragraph_id'] for c in interval] == [p['id'] for p in ps[ix[src['first_paragraph_id']]:ix[src['last_paragraph_id']] + 1]]
    for c in interval:
        p = ps[ix[c['paragraph_id']]]
        assert c['text'] == p['text'] and c['pages'] == p.get('pages', [])
    # Attached independent, self-contained notes of article 79 retain v13.
    rows = [x for x in byhead[headid] if not (headid == 'RECODE25-04636' and x['id'] in {'RECODE25-04641', 'RECODE25-04642'})]
    assert rows
    already = []
    pids = {c['paragraph_id'] for c in interval[1:]}
    for row in ll:
        if rr[row['id']]['candidate_file'] == src['candidate_path'] and pids & {c['paragraph_id'] for c in row['contexts']['paragraph_context']}:
            if any(norm(src['head']) in norm(t) for t in texts(row['contexts'])):
                already.append(row['id'])
    families.append({'source_list_head_unit': headid, 'actual_parent_paragraph_id': parent['paragraph_id'], 'actual_parent_text': parent['text'], 'source_path': src['source_path'], 'source_sha256': src['source_sha256'], 'candidate_path': src['candidate_path'], 'candidate_sha256': src['candidate_sha256'], 'complete_contiguous_interval': interval, 'next_boundary': copy.deepcopy(src['next_boundary']), 'affected_ids': [x['id'] for x in rows], 'existing_first_or_other_items_with_actual_head_available_no_change_needed': already, 'reason': reason, 'verification': 'Existing v11 actual-source-reviewed contiguous interval reused with current source/candidate SHA and paragraph membership rechecked; image-only source p17 visually reread.'})
    for row in rows:
        rid = row['id']
        proposals.append({'id': rid, 'current_unit': lb[rid]['text'], 'current_unit_sha256': digest(lb[rid]['text']), 'repair_type': 'actual_local_list_parent_predicate', 'family_head_unit': headid, 'actual_parent_context': copy.deepcopy(parent), 'complete_local_family_contexts': interval, 'next_boundary': copy.deepcopy(src['next_boundary']), 'why_this_local_parent_is_needed': reason, 'nearest_heading_change_needed': False, 'old_context_sha256': digest(json.dumps(lb[rid]['contexts'], ensure_ascii=False, sort_keys=True)), 'no_original_text_id_or_label_change': True})

# The independent original Word attachment has a genuine component heading.
# Do not manufacture a candidate paragraph for a title absent from that parser.
ar = rr['RECODE25-02010']
ap = Path(ar.get('unit_source') or ar['source'])
attachment = subprocess.run(['textutil', '-convert', 'txt', '-stdout', str(ap)], check=True, capture_output=True, text=True).stdout
title = '《优化药品补充申请审评审批程序改革试点工作方案》试点工作申报资料要求'
assert norm(title) in norm(attachment)
acp = Path(ar['candidate_file'])
acd = json.loads(acp.read_text())
aps = [p for p in acd['paragraphs'] if p.get('origin') == 'verified_local_attachment' and p.get('attachment_title') == '试点工作申报资料要求']
assert len(aps) == 9
attachment_rows = [row for row in ll if Path(rr[row['id']].get('unit_source') or rr[row['id']]['source']).resolve() == ap.resolve()]
assert len(attachment_rows) == 9
for i, row in enumerate(attachment_rows):
    assert row['text'] == aps[i]['text'] and norm(row['text']) in norm(attachment)
    assert row['contexts']['nearest_preceding_heading']['text'] == '五、保障措施'
    proposals.append({'id': row['id'], 'current_unit': row['text'], 'current_unit_sha256': digest(row['text']), 'repair_type': 'actual_source_component_heading_and_boundary', 'old_nearest_heading': row['contexts']['nearest_preceding_heading'], 'actual_component_heading': {'text': title, 'pages': [], 'source_key': 'original_word_attachment_title_paragraphs', 'source_path': str(ap), 'source_sha256': sha(ap), 'candidate_path': str(acp), 'candidate_sha256': sha(acp), 'candidate_attachment_title': '试点工作申报资料要求', 'verification': {'verified': True, 'method': 'actual_original_word_textutil_extraction_title_and_all_9_items'}}, 'complete_actual_attachment_items': [{'paragraph_id': p['id'], 'text': p['text'], 'pages': [], 'source_lines': p.get('line_ids', []), 'source_path': str(ap), 'source_sha256': sha(ap), 'candidate_path': str(acp), 'candidate_sha256': sha(acp)} for p in aps], 'first_item_wrong_cross_component_immediate_previous_requires_replacement': i == 0, 'actual_next_boundary': 'end_of_original_word_attachment', 'old_context_sha256': digest(json.dumps(row['contexts'], ensure_ascii=False, sort_keys=True)), 'no_fake_candidate_heading_paragraph': True, 'no_original_text_id_or_label_change': True})
families.append({'family': 'independent_original_word_attachment_material_requirements', 'actual_component_heading': title, 'source_path': str(ap), 'source_sha256': sha(ap), 'candidate_path': str(acp), 'candidate_sha256': sha(acp), 'source_paragraph_ids': [p['id'] for p in aps], 'affected_ids': [row['id'] for row in attachment_rows], 'all_actual_9_items_included': True, 'boundary': 'end_of_actual_attachment', 'first_item_cross_component_immediate_previous_replaced': attachment_rows[0]['id']})
proposals.sort(key=lambda x: x['id'])
assert len({x['id'] for x in proposals}) == len(proposals)
out = {'proposal_version': 'v14-source-only-fragment-parent-and-component-boundary-pending-root-approval', 'source_only': True, 'base_material_version': 'v13', 'v13_llm_sha256': sha(B / 'effective_blind_inputs_v13.jsonl'), 'v13_rule_sha256': sha(B / 'rule_inputs_shared_v13.jsonl'), 'affected_unit_n': len(proposals), 'affected_ids': [x['id'] for x in proposals], 'source_family_n': len(families), 'families': families, 'proposals': proposals, 'new_analysis_units': 0, 'unit_text_changes': 0, 'no_labels_transferred_or_predictions_read': True, 'original_sources_candidates_v13_and_manual_unchanged': True, 'first_item_policy': 'A first sibling already carrying its genuine local head is not changed merely to repeat existing evidence. Source-family completeness is recorded in each proposed certificate; genuine component-boundary errors affect all nine attachment items.', 'mechanical_inventory_is_not_a_repair_decision': {'reviewed_list_missing_head_inventory_n': len(inventory), 'inventory_path': str(B / 'audit/extended_numbered_list_parent_inventory_v13.json'), 'self_contained_statements_not_automatically_padded': True, 'title_or_heading_already_contains_the_needed_predicate_not_treated_as_missing': True}, 'v13_remains_immutable': True}
dest = B / 'audit/extended_fragment_source_proposal_v14.json'
assert not dest.exists()
dest.write_text(json.dumps(out, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'affected_unit_n': out['affected_unit_n'], 'source_family_n': out['source_family_n'], 'affected_ids': out['affected_ids']}, ensure_ascii=False))
