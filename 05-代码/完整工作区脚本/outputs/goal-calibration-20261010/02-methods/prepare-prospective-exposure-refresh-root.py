"""Prospective development exposure accounting; preserves historical draws and weights."""
import datetime
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '02-methods/prospective-exposure-refresh-root'
FRAME = ROOT / '00-baseline/source-only-frame.jsonl'
OLD = ROOT / '01-review/exposure-ids.json'
DRAW = ROOT / '09-delivery/human200-independent-preparation-root/coordinator-private/draw-and-mapping.json'
COMPLETE = ROOT / '08-audits/ai800-disagreement-semantic-root/complete-review-reception-root/future-development-exposure-overlay.json'
NEGATIVE = ROOT / '08-audits/ai800-disagreement-semantic-root/common-negative30-root/future-development-exposure-overlay.json'
COMMON = ROOT / '08-audits/common-material-candidate-reception-sol/report.json'
SE_READING = ROOT / '06-coding/rule-v20-SEEconomic-repair-sol/versions/v2/actual-read-and-quote-validation.json'

def load(path):
    return json.loads(Path(path).read_text())

def bind(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())

def save(path, obj):
    with path.open('x', encoding='utf8') as handle:
        json.dump(obj, handle, ensure_ascii=False, indent=2)
        handle.write('\n')

assert not OUT.exists(), 'A prospective exposure snapshot already exists; use a new version'
frozen_paths = [FRAME, OLD, DRAW, COMPLETE, NEGATIVE, COMMON, SE_READING,
    ROOT/'05-validation/full800-common-v15-prerelease-sol/coordinator-private/draw-contract.json',
    ROOT/'05-validation/full800-common-v15-prerelease-sol/coordinator-private/mapping.json',
    ROOT/'03-manual/full4481-common-release-20261010-root/manual.txt',
    ROOT/'07-statistics/prospective-engine-domain-sol/metrics_engine.py']
before = [bind(p) for p in frozen_paths]
old = load(OLD)
assert bind(FRAME)['sha256'] == old['frame_sha256']
assert bind(DRAW)['sha256'] == '5690672e10612371def277f7d98ed332e22cb281cfb5b636a9cbc93eaba1bd55'
frame = [json.loads(line) for line in FRAME.read_text().splitlines()]
assert len(frame) == 4481
meta = {r['id']: dict(id=r['id'], department=r['analysis_group'], family=r['normalized_text_family']['family_id']) for r in frame}
assert len(meta) == 4481
old_excluded = set(old['excluded_ids'])
assert len(old_excluded) == 3037 and old_excluded <= set(meta)
old_remaining = set(meta) - old_excluded
assert len(old_remaining) == 1444
assert {r['id'] for r in old['records']} == old_excluded
assert all(meta[r['id']]['family'] == r['family_id'] for r in old['records'])
draw = load(DRAW)
assert len(draw['records']) == len({r['source_id'] for r in draw['records']}) == 200
assert Counter(r['domain'] for r in draw['records']) == {'remaining': 120, 'exposed': 80}
assert all((r['source_id'] in old_remaining) == (r['domain'] == 'remaining') for r in draw['records'])

complete = set(load(COMPLETE)['reviewed_current_source_ids'])
negative = set(load(NEGATIVE)['source_ids'])
common = set(load(COMMON)['finite_interface_result']['actual_source_packets'])
assert len(complete) == 328 and len(negative) == 30 and len(common) == 5
SE = set()
se_material_bindings = []
for material in load(SE_READING)['materials']:
    actual = bind(material['path'])
    assert actual == {k: material[k] for k in ('path', 'bytes', 'sha256')}
    se_material_bindings.append(actual)
    SE.add(load(material['path'])['source_record']['id'])
assert len(SE) == 34
groups = [('complete_semantic_review_328', complete, bind(COMPLETE)),
    ('common_negative_semantic_review_30', negative, bind(NEGATIVE)),
    ('common_material_finite_source_read_5', common, bind(COMMON)),
    ('SE_Ec_v2_actual_material_read_34', SE, bind(SE_READING))]
direct = set().union(*(g[1] for g in groups))
assert direct <= set(meta)
reasons = defaultdict(list)
for name, ids, provenance in groups:
    for rid in ids:
        reasons[rid].append(dict(category=name, binding=provenance))
families = defaultdict(set)
for rid, row in meta.items():
    families[row['family']].add(rid)
new_families = {meta[rid]['family'] for rid in direct}
prospective_excluded = old_excluded | set().union(*(families[family] for family in new_families))
new_exclusions = prospective_excluded - old_excluded
new_direct = direct & old_remaining
family_only = new_exclusions - new_direct
prospective_remaining = set(meta) - prospective_excluded

original_complete_hits = [r for r in draw['records'] if r['source_id'] in complete]
assert len(original_complete_hits) == 63
assert sum(r['domain'] == 'remaining' for r in original_complete_hits) == 29
impact = []
for row in draw['records']:
    rid = row['source_id']
    impact.append(dict(source_id=rid, A_blind_id=row['A_blind_id'], B_blind_id=row['B_blind_id'],
        historical_domain=row['domain'], historical_stratum=row['stratum'], historical_weight_exact=row['weight_exact'],
        candidate_exposed=rid in prospective_excluded, direct_new_semantic_review=rid in direct,
        changed_from_historical_remaining=rid in new_exclusions,
        exposure_reasons=reasons.get(rid, []),
        new_same_family_direct_ids=sorted(direct & families[meta[rid]['family']]) if rid in family_only else [],
        historical_assignment_or_weights_modified=False))
candidate_rows = []
for row in frame:
    rid = row['id']
    candidate_rows.append(dict(source_id=rid, department=meta[rid]['department'], family_id=meta[rid]['family'],
        historical_domain='exposed' if rid in old_excluded else 'remaining',
        candidate_domain='exposed' if rid in prospective_excluded else 'remaining',
        current_direct_development_read=rid in direct,
        new_exclusion_reason='direct_semantic_review' if rid in new_direct else 'same_normalized_text_family_of_new_direct_review' if rid in family_only else None))
counts = dict(historical_domains={'remaining':1444, 'exposed':3037},
    direct_current_source_ids=len(direct), new_direct_exclusions=len(new_direct),
    new_same_family_only_exclusions=len(family_only), new_exclusions=len(new_exclusions),
    candidate_domains={'remaining':len(prospective_remaining),'exposed':len(prospective_excluded)},
    historical200_complete328_overlap=63, historical200_remaining_complete328_overlap=29,
    historical200_remaining_now_candidate_exposed=sum(r['changed_from_historical_remaining'] for r in impact),
    historical200_remaining_still_candidate_remaining=sum(r['historical_domain']=='remaining' and not r['candidate_exposed'] for r in impact),
    candidate_domain_by_department={d:dict(Counter(r['candidate_domain'] for r in candidate_rows if r['department']==d)) for d in ['NHC','NHSA','NMPA']})
assert [bind(p) for p in frozen_paths] == before, 'Historical inputs changed during read-only accounting'
OUT.mkdir(mode=0o700)
private = OUT/'coordinator-private'
private.mkdir(mode=0o700)
save(OUT/'input-bindings.json',dict(inputs=before, real_material_bindings=se_material_bindings))
save(OUT/'future-development-exposure-overlay.json',dict(status='prospective_candidate_exposure_accounting_not_new_validation_release',
    at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), source_groups=[dict(name=name,N=len(ids),binding=provenance) for name,ids,provenance in groups],
    counts=counts, direct_source_ids=sorted(direct), new_direct_excluded_ids=sorted(new_direct), new_family_only_excluded_ids=sorted(family_only),
    candidate_remaining_ids=sorted(prospective_remaining),candidate_excluded_ids=sorted(prospective_excluded),
    historical_domains_unchanged=True, original200_draw_weights_answers_unchanged=True,
    not_certificate_of_no_other_case_exposure=True,
    policy='Actual semantic development reviews plus baseline exact normalized-text families; full-corpus inference, pure byte/source preparation, unfilled packets and synthetic controls do not count as case development. Only current propositions actually read are added, not every clause in a visible source document.',
    validity='Future rule candidates may not describe the changed historical remaining rows as unseen test records. Do not relabel the historical200 and reuse its old domain weights as a newly designed population. Freeze the final joint rule/material version and updated exposure registry before any prospective independent draw. Historical800/200 and primary machine outputs remain tied to their historical versions.',
    pending=['account for any later actual development reads before final freeze','freeze final joint5dim classifier and common material release','prepare separately bound sampling/statistics contract for updated domains; existing1444/3037 engine is not reused by bypassing checks','new human initial and blinded adjudicated reference results remain unreceived'],
    human_or_machine_labels_read=False, human_results_created=0, new_draws=0, rules_or_material_release_adopted=False))
save(private/'historical200-new-candidate-eligibility-impact.json',dict(counts=counts, draw_binding=bind(DRAW), historical_records=impact, new_weights_or_domain_estimates_computed=False))
with (private/'future-frame-candidate.jsonl').open('x',encoding='utf8') as handle:
    for row in candidate_rows:
        handle.write(json.dumps(row,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n')
note = ('本目录是后续候选规则的开发曝光台账，不是正式检验结果或新抽样。\n'
    f'冻结旧域保留 remaining=1444、exposed=3037。已确认新增直接复审 {len(new_direct)} 条，按旧完全相同规范化文本家族另新增 {len(family_only)} 条；候选剩余池 {len(prospective_remaining)} 条。\n'
    f'原200抽样中，328条语义复审集合直接覆盖63条，其中29条原属 remaining；累计台账及同家族后，原120条 remaining 有 {counts["historical200_remaining_now_candidate_exposed"]} 条进入候选开发曝光域。\n'
    '不能只改这些条目的域标签后沿用旧总体与权重。旧表、盲号、初判、抽样、权重、统计契约和正在接收的机器原输出均不改。\n'
    '待共同材料和五维规则最终冻结，依据更新台账另准备独立检验设计。已用来修复规则的材料可以保留作开发核查，其指标不能冒充新规则未见材料的验证。\n'
    '这里只核对当前明确登记的读取和完全相同文本家族；不证明剩余材料从未在其他流程出现。无真人结果、无新抽样、无机器标签、无正式验收。\n')
with (OUT/'说明.txt').open('x',encoding='utf8') as handle:
    handle.write(note)
members = [bind(p) for p in sorted(OUT.rglob('*')) if p.is_file()]
save(OUT/'output-seal.json',dict(output_members=members, builder=bind(__file__), self_excluded=True))
print(json.dumps(dict(destination=str(OUT),counts=counts,historical_inputs_unchanged=True,new_draws=0),ensure_ascii=False))
