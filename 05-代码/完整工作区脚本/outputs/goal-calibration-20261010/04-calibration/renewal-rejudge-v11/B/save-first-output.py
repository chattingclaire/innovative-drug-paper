"""Save the first complete native AI development judgment once, without reruns."""
import datetime
import hashlib
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parents[2]
DESIGN_PATH = OUT.parent / 'admin/design.json'
SHA = lambda raw: hashlib.sha256(raw).hexdigest()
CANONICAL = lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')

design = json.loads(DESIGN_PATH.read_text())
id_map = json.loads((OUT / 'id-map.json').read_text())
source_raw = Path(design['source']['path']).read_bytes()
assert SHA(source_raw) == design['source']['sha256']
rows = {row['id']: row for row in map(json.loads, source_raw.splitlines())}
resource_raw = Path(design['resource']['path']).read_bytes()
assert SHA(resource_raw) == design['resource']['sha256']
resource = json.loads(resource_raw)
resources = resource['source_texts']

# These ten judgments are authored by the native AI after the full authorized
# reading. This script only copies fixed decisions and exact source spans.
DECISIONS = {
    'RECODE25-00902': {
        'S': (0, ['excluded'], '本条规定法定1类药品在符合简易续约条件时，仍可主动申请谈判确定支付标准。完整核明的简易续约条件涉及独家属性、费用与预算、市场价格成本和目录管理资格，没有药物损害、用药风险、安全证据或风险控制要求；注册类别本身不能证明安全议题。故S为0。'),
        'E': (0, ['excluded'], '本条的条件—待遇关系是满足简易续约条件的法定1类品种可选择谈判定价。同版简易续约五项条件及第3项两个子项没有治疗效果、健康收益或相应证据要求；续约有效期、治疗成本和注册类别均不等于药物效果评价。故E为0。'),
        'Ec': (1, ['Ec_treatment_payment_resource'], '当前完整命题明确允许这些品种主动通过谈判确定医保支付标准，共同父谓词补明其纳入重新谈判范围；这是对药品治疗支付的实质定价安排。简易续约条件原文补全“虽符合”的有限条件，保留费用与预算约束，未将全篇程序或其他支付规则复制入本条。故Ec为1。'),
        'I': (1, ['I4'], '当前明确采用现行注册办法与分类标准批准的1类化学药品、1类治疗用生物制品、1类中药作为差别化资格条件；即便符合简易续约条件，也可主动申请谈判确定支付标准，父谓词补明重新谈判机会。按共同手册的法定类别口径，这是创新类别与实际续约选择权的直接联系，属于I4；不据此推断临床优越性，也不将其改作研发支持I3。故I为1。'),
        'F': (0, ['excluded'], '本条开放的是企业就特定注册类别药品选择谈判确定支付标准的机会。完整条件中的药品费用预算、价格与治疗成本属于支付和资源约束，没有患者支付能力、按需保障、可及差距或机会不公平的直接关系。不能把医保支付安排或创新类别的差别化资格自动等同患者公平。故F为0。'),
    },
    'RECODE25-00900': {
        'S': (0, ['excluded'], '当前是“满足条件之一→纳入重新谈判范围”的实质资格总领，须读取两个完整成员。成员1的常规目录管理和简易续约条件已用同版资格原文核明，成员2为法定1类品种的自愿谈判定价选择；这些条件均不表达药物损害、用药风险或安全证据要求。保留“不符合”和“之一”，不推成某药不安全或全部条件失败。故S为0。'),
        'E': (0, ['excluded'], '本总领规定符合任一成员的协议期内独家药品取得重新谈判资格。完整成员及其同版常规管理、简易续约资格条件涉及独家属性、纳入年限、费用预算、市场价格成本和法定类别，没有药物疗效、健康收益或效果证据要求；不能从续约或治疗成本推导疗效。故E为0。'),
        'Ec': (1, ['Ec_treatment_payment_resource'], '当前实质规定两类品种纳入重新谈判范围，而非仅组织清单。成员1以不符合常规管理及简易续约条件决定这一待遇，同版被援引条件包含药品费用/预算、未来预算增幅和市场价格/治疗成本约束；成员2明确允许主动谈判确定支付标准。完整有限条件与当前资格后果构成药品支付、预算和价格安排的直接关系。只编码一般规范，不断言任何具体药品已超预算或所有条件失败。故Ec为1。'),
        'I': (1, ['I4'], '当前“条件之一→纳入重新谈判范围”提供实质机会，完整第二成员将现行标准批准的1类化学药品、1类治疗用生物制品、1类中药与自愿谈判定价资格直接连接。按共同手册的法定创新类别口径，这一成员补足本总领的创新类别差别化待遇，属于I4；第一成员的不符合常规管理及简易续约条件不因此变成创新属性，不证明所有独家药品创新，也不新增I3。故I为1。'),
        'F': (0, ['excluded'], '当前及两个完整成员规定企业药品的重新谈判资格；已核明的资格标准中的费用预算、价格和治疗成本指向支付资源约束。没有把该资格安排直接连接患者负担、需要缺口、可及差距或机会不公平，也没有药物评价中的公平比较。差别化创新类别机会与医保支付目标本身不足以构成F。故F为0。'),
    },
}

def restored(row, index):
    source_id = resources[index]['source_resource_id']
    matches = [c for c in row['contexts'] if c.get('kind') == 'same_snapshot_referenced_source_paragraph' and c['structure']['source_paragraph_id'] == source_id]
    assert len(matches) == 1 and matches[0]['text'] == resources[index]['text']
    return matches[0]

def exact_quote(context, purpose):
    text = context['text']
    return {'context_id': context['context_id'], 'field_path': 'text', 'quote': text,
            'span': {'start': 0, 'end': len(text)}, 'purpose': purpose}

def selected_indices(uid, dimension):
    if uid == 'RECODE25-00902':
        if dimension == 'I':
            return [30]
        return [30, *range(9, 17)]
    return [31, 32, 3, 4, 5, *range(9, 17)]

outputs = []
sidecars = []
for binding in id_map['mapping']:
    uid = binding['source_id']
    row = rows[uid]
    evidence = {}
    sidecar_dimensions = {}
    for dim in ['S', 'E', 'Ec', 'I', 'F']:
        label, paths, reason = DECISIONS[uid][dim]
        indices = selected_indices(uid, dim)
        quoted_contexts = []
        references = []
        for index in indices:
            context = restored(row, index)
            if index == 30:
                purpose = '补全本成员的重新谈判共同谓词与资格后果，保留“条件之一”。'
            elif index in [31, 32]:
                purpose = '读取总领确指的完整成员；保留两个分支、否定与例外，补全当前实质条件—机会关系。'
            else:
                purpose = '核明当前或完整成员确指的同版资格条件；仅补全标准及限定范围，不承接全文其他规则。'
            quote = exact_quote(context, purpose)
            quoted_contexts.append(quote)
            references.append({'resource_index': index, 'resource_id': resources[index]['source_resource_id'],
                               'resource_text_sha256': resources[index]['text_sha256'],
                               'source_ref': resources[index]['source_ref'],
                               'source_char_interval_footerless_whitespace_normalized': resources[index]['source_char_interval_footerless_whitespace_normalized'],
                               **quote})
        geometry = next(c['context_id'] for c in row['contexts'] if c.get('kind') == 'same_snapshot_source_numbered_group_geometry')
        structure_ids = [geometry]
        if uid == 'RECODE25-00900':
            structure_ids += ['CTX-9fa123c79ebfacdfa85d', 'CTX-7b830e5ff4c239a3d9e5']
        pages = sorted({8, *[p for index in indices for p in resources[index]['source_ref']['locator']['physical_pages']]})
        images = [a['attachment_id'] for a in row['source_attachments'] if a['physical_page'] in pages]
        evidence[dim] = {'paths': paths, 'current_quote': row['text'],
                         'current_span': {'start': 0, 'end': len(row['text'])},
                         'contexts_used': quoted_contexts, 'structural_context_ids_used': structure_ids,
                         'image_sources_used': images, 'reason': reason,
                         'innovation_support': None, 'fairness_specific': None}
        sidecar_dimensions[dim] = {'current_source_ref': row['source_ref'], 'resources_actually_used': references,
                                   'structural_context_ids_used': structure_ids, 'image_sources_used': images}
    outputs.append({'blind_id': binding['output_blind_id'], 'content_sha256': binding['content_sha256'],
                    'manual_sha256': design['manual']['sha256'],
                    'labels': {dim: DECISIONS[uid][dim][0] for dim in ['S', 'E', 'Ec', 'I', 'F']},
                    'evidence': evidence, 'material_requests': []})
    sidecars.append({'source_id': uid, 'output_blind_id': binding['output_blind_id'],
                     'raw_jsonl_row_sha256_excluding_line_ending': binding['raw_jsonl_row_sha256_excluding_line_ending'],
                     'canonical_complete_row_sha256': binding['canonical_complete_row_sha256'],
                     'content_sha256': binding['content_sha256'],
                     'source_file_sha256': design['source']['sha256'],
                     'resource_file_sha256': design['resource']['sha256'],
                     'dimensions': sidecar_dimensions})

assert [x['source_id'] for x in sidecars] == ['RECODE25-00902', 'RECODE25-00900']
for filename, objects in [('labels.jsonl', outputs), ('source-evidence.jsonl', sidecars)]:
    with (OUT / filename).open('x', encoding='utf-8') as handle:
        for obj in objects:
            handle.write(json.dumps(obj, ensure_ascii=False, allow_nan=False) + '\n')

recorded = datetime.datetime.now(datetime.timezone.utc).isoformat()
first = {'first_complete_output_saved_at_utc': recorded,
         'judgment_order': ['RECODE25-00902', 'RECODE25-00900'],
         'record_count': 2, 'dimension_count': 10, 'attempt': 1,
         'generation': 'Native Codex AI judgment; fixed authored decisions copied once by this script.',
         'retries_or_favorable_selection': False, 'prior_output_overwrite': False,
         'labels_sha256': SHA((OUT / 'labels.jsonl').read_bytes()),
         'source_evidence_sha256': SHA((OUT / 'source-evidence.jsonl').read_bytes()),
         'id_map_sha256': SHA((OUT / 'id-map.json').read_bytes())}
with (OUT / 'first-complete-output.json').open('x', encoding='utf-8') as handle:
    json.dump(first, handle, ensure_ascii=False, indent=2)
    handle.write('\n')
print(json.dumps({'saved': ['labels.jsonl', 'source-evidence.jsonl', 'first-complete-output.json'],
                  'first_output_preserved': True}, ensure_ascii=False))
