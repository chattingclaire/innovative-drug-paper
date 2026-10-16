"""Minimal missing evaluation-content gate; does not classify dimensions."""
import copy
import re
from source_context_adapter_v34 import authenticate_target, authenticate_context, candidate, norm
from context_validation import verified_following_list

PATTERNS = (
    r'(?:药品|药物|该药|本药)[^。；;]{0,20}(?:评价|评估)(?:的)?(?:内容|资料|证据|结果|要求)?(?:应当|应|须)?(?:包括|包含|如下|为)(?:以下|下列)?(?:内容|资料|证据|结果|要求)?[:：]$',
    r'(?:提交|提供|补充|评价|评估|审查|比较)(?:以下|下列|如下)[^。；;]{0,24}(?:药品|药物|疗效|安全性|有效性|经济性|创新性|公平性)[^。；;]{0,12}(?:资料|证据|数据|信息|内容)?[:：]$',
)


def same_verified_paragraph_has_following(record):
    if not record.get('candidate_file'):
        return False
    authenticate_target(record)
    paragraphs = candidate(record['candidate_file']).get('paragraphs', [])
    for p in record.get('paragraph_context', []):
        value = norm(p.get('text',''));target=norm(record['unit_text'])
        if value.count(target) != 1 or not value.split(target,1)[1]:
            continue
        matches = [q for q in paragraphs if q.get('id') == p.get('paragraph_id') and q.get('text') == p.get('text')]
        if not matches:
            continue
        authenticate_context({**p,'source_path':record.get('unit_source') or record.get('source'),
                              'source_sha256':record.get('unit_source_sha256') or record.get('source_sha256'),
                              'candidate_path':record['candidate_file'],'candidate_sha256':record['candidate_sha256'],
                              'source_lines':p.get('source_lines') or matches[0].get('source_lines') or matches[0].get('line_ids')})
        return True
    return False


def prepare(record):
    text = record.get('unit_text','').strip()
    if (re.search(r'委员会|工作组|秘书处|办公室|机构',text) and
            re.search(r'职责|负责|任务|分工',text) and
            not re.search(r'(?:须|应当|应|需要)(?:评价|评估|提交|补充)',text)):
        return record
    if re.search(r'参见|详见|下载地址|网址|链接|导航',text) or not any(re.search(p,text) for p in PATTERNS):
        return record
    if (record.get('verified_complete_following_list_v34') or verified_following_list(record)
            or same_verified_paragraph_has_following(record)):
        return record
    out = copy.deepcopy(record)
    out['input_assessment'] = {'status':'context_insufficient',
        'reason':'explicit_required_evaluation_content_not_available_as_complete_following_material'}
    out['completeness_gate_v34'] = {'current_unit_text':record['unit_text'],
                                   'reason':out['input_assessment']['reason'],
                                   'source_material_review_required':True}
    return out
