"""Preserve ROOT's source-based review separately from an agent's first view."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PACKETS = ROOT / '06-coding/full4481-common-v15-production-preparation-sol/packets'
MANUAL = ROOT / '03-manual/full4481-common-release-20261010-root/manual.txt'


def binding(p):
    b = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(b).hexdigest()}


def main():
    manual = MANUAL.read_text()
    temporal = next(s for s in manual.splitlines()
                    if s.startswith('“当前”指固定记录的命题'))
    assert '过去、完成或未来时态及背景位置均不能单独决定标签' in temporal
    source_quotes = [
        '试点项目范围为1类创新药（细胞和基因治疗产品、疫苗产品等除外）临床试验申请。',
        '经确认的试点项目，药审中心在受理临床试验申请后30个工作日内完成审评审批，并通过药审中心网站通知申请人审批结果。']
    rows = []
    for sid, anchor in [('RECODE25-01729', '决定开展'),
                        ('RECODE25-02233', '2024年组织开展了')]:
        packet_path = PACKETS / (sid + '.json')
        packet = json.loads(packet_path.read_text())
        bundle = packet['source_bundle']
        current = bundle['source_record']['text']
        assert anchor in current and '支持创新药研发' in current
        resource = next(r for r in bundle['explicit_or_primary_source_resources']
                        if r['source_resource_id'] == 'SOURCE-NMPA-2024-PILOT-21')
        assert resource['document_year'] == 2024
        leaf = next(s for s in resource['source_texts']
                    if all(q in s['text'] for q in source_quotes))
        evidence = []
        for quote in source_quotes:
            start = leaf['text'].index(quote)
            assert leaf['text'][start:start + len(quote)] == quote
            evidence.append({'source_resource_id': resource['source_resource_id'],
                             'source_locator': leaf['source_locator'],
                             'leaf_text_range_0based_halfopen': [start, start + len(quote)],
                             'quote': quote})
        rows.append({'source_id': sid, 'dimension': 'I', 'review_value': 1,
                     'current_text_actually_read': current,
                     'current_action_anchor': anchor,
                     'frozen_manual_temporal_rule': temporal,
                     'necessary_same_period_resource_evidence': evidence,
                     'reason': '当前直接陈述设立/实施具名创新研发试点；同包2024原方案限定1类创新药并实质设置30日审评通道，满足I3对象、可用安排及直接关系。制定目的或背景位置不消除本句已表达的实施行动。',
                     'temporal_limit': '02233表达2024年曾实施的支持议题，不证明目前仍可申请；不倒灌2025年新机制。',
                     'packet': binding(packet_path),
                     'agent_independent_first_review_overwritten': False})
    result = {'identity': 'ROOT non-blind AI source-based discussion review; not human adjudication',
              'manual': binding(MANUAL), 'rows': rows,
              'frozen_manual_changed': False, 'original_labels_changed': False,
              'semantic_model_execution_authenticated': False}
    out = HERE / 'root-pilot-boundary-review.json'
    with out.open('x') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(json.dumps({'records_reviewed': 2,
                      'proposed_I_values': [1, 1], 'output': str(out)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
