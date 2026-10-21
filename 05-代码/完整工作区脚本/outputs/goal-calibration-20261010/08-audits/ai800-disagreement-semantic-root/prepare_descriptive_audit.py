"""Read frozen originals; write descriptive comparison and source identity checks only."""
from pathlib import Path
from collections import Counter
import json, hashlib

BASE = Path('/PROJECT_ROOT')
OUT = Path(__file__).resolve().parent
AI = BASE / 'outputs/ai-audit800-20261010'
RULE = BASE / 'outputs/goal-calibration-20261010/06-coding/rule-full4481-v2-root'
DIMS = ('S', 'E', 'Ec', 'I', 'F')

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def canonical(x):
    return json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)

def save(name, x):
    with (OUT / name).open('x', encoding='utf-8') as f:
        f.write(json.dumps(x, ensure_ascii=False, indent=2, allow_nan=False) + '\n')

ai_path = AI / 'AI原始判读-800条.jsonl'
rule_path = RULE / 'run4481-first/predictions.jsonl'
ai = {r['source_id']: r for r in map(json.loads, ai_path.read_text().splitlines())}
rule = {r['id']: r for r in map(json.loads, rule_path.read_text().splitlines()) if r['id'] in ai}
assert len(ai) == len(rule) == 800 and ai.keys() == rule.keys()
release = json.loads((RULE / 'rule-production-release.json').read_text())
version_checks = {}
for key, filename in [('manual','manual.txt'), ('prompt','execution-prompt.txt'), ('protocol','common-execution-protocol.txt')]:
    actual = sha(AI / 'source-A/coder-A' / filename)
    expected = release[key]['sha256']
    assert actual == expected
    version_checks[key] = {'sha256': actual, 'matches_rule_release': True}

source_checks = []
for line in (RULE / 'run4481-first/delivered-complete-source-bundles.jsonl').open():
    production = json.loads(line)
    sid = production['source_record']['id']
    if sid not in ai:
        continue
    packet = AI / 'source-A/coder-A/materials' / (ai[sid]['blind_id'] + '.json')
    review = json.loads(packet.read_text())
    same = canonical(production) == canonical(review)
    source_checks.append({'source_id': sid, 'blind_id': ai[sid]['blind_id'],
                          'complete_bundle_canonical_equal': same,
                          'review_packet_file_sha256': sha(packet)})
assert len(source_checks) == 800

result = []
for d in DIMS:
    c = Counter((r['judgments'][d]['value'], rule[s]['labels'][d]) for s, r in ai.items())
    n00, n01, n10, n11 = [c[k] for k in [(0,0), (0,1), (1,0), (1,1)]]
    n = n00 + n01 + n10 + n11
    po = (n00 + n11) / n
    pe = ((n10+n11)*(n01+n11)+(n00+n01)*(n00+n10)) / n**2
    pos = 2*n11/(2*n11+n10+n01) if 2*n11+n10+n01 else None
    neg = 2*n00/(2*n00+n10+n01) if 2*n00+n10+n01 else None
    result.append({'dimension': d, 'joint_binary_N': n, 'excluded_N': 800-n,
                   'AI0_rule0': n00, 'AI0_rule1': n01, 'AI1_rule0': n10, 'AI1_rule1': n11,
                   'AI_positive_N_joint': n10+n11, 'rule_positive_N_joint': n01+n11,
                   'agreement': po, 'kappa': (po-pe)/(1-pe),
                   'positive_agreement': pos, 'negative_agreement': neg})

save('source-version-reception.json', {'identity':'ROOT mechanical input identity audit, not semantic adjudication',
     'AI_initial_sha256':sha(ai_path), 'rule_predictions_sha256':sha(rule_path),
     'version_checks':version_checks, 'complete_source_bundle_matches':sum(r['complete_bundle_canonical_equal'] for r in source_checks),
     'complete_source_bundle_comparisons':source_checks})
save('descriptive-metrics.json', {'identity':'AI辅助抽检与固定规则首答的未加权描述性对照；均不作为金标准',
     'reference_status':'none; no accuracy, precision, recall, F1 or formal validation claimed',
     'positive_agreement_formula':'2*n11 / (2*n11+n10+n01)',
     'AI_zero_fraction_all_4000':sum(r['judgments'][d]['value']==0 for r in ai.values() for d in DIMS)/4000,
     'overall_slot_agreement_pooled_descriptive_only':sum(r['AI0_rule0']+r['AI1_rule1'] for r in result)/sum(r['joint_binary_N'] for r in result),
     'by_dimension':result})
print(json.dumps({'source_matches':sum(r['complete_bundle_canonical_equal'] for r in source_checks),
                  'source_N':len(source_checks), 'dimension_metrics':result}, ensure_ascii=False))
