#!/usr/bin/env python3
"""Build a source plan only; never edit the manuscript or earlier deliveries."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.parse import quote
import json
import re
import hashlib

BASE = Path(__file__).resolve().parent
PARENT = BASE.parent


def read(name):
    return json.loads((BASE / name).read_text())


def save(name, value):
    (BASE / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def link(label, target):
    return f"[{label}](<{target}>)"


def compact(value):
    if isinstance(value, list):
        return "；".join(map(str, value))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value or "")


def cell(value):
    return compact(value).replace("|", "／").replace("\n", " ")


spec = read("plan_spec.json")
steps = read("step_coverage_spec.json")
manifest = read("planning_input_manifest.json")
old = read("snapshots/old-66-plan__参考文献精简候选清单.json")
matrix = read("snapshots/matrix-21__完整方法指标矩阵.json")
methods = read("methods-review.json")
theory = read("theory-review.json")
policy = read("policy-review.json")
root = read("root-source-review.json")
steering = read("later-steering-input.json")
for c in spec['conditional_new']:
    if c['id'] == 'N-L2013':
        c['trigger'] = '最终主线实际采用患者获取过程、五个服务维度与五项患者能力的配对框架'
        c['decision'] = '不把过程位置、服务维度和患者能力混写成同一组；未采用该过程框架则只留开发档案。'
now = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat()
old_by_id = {f"R{x['number']:03d}": x for x in old['items']}
catalog = {}

# Preserve each specialist's actual reading scope; a full PDF being available
# never becomes a claim that all its pages were read.
method_ids = {
    'HS2005': 'N-HS2005', 'CO1960': 'R046', 'HT1952': 'R049',
    'RWY1992': 'R048', 'BE2022': 'N-BE2022', 'HK2026': 'R043',
    'GS2013': 'R045', 'W2014': 'R028', 'C2018': 'R029',
    'T2024': 'R066', 'BY1993': 'N-BY1993', 'CF1990': 'N-CF1990',
    'GW2008': 'N-GW2008', 'AP2008': 'N-AP2008',
}
for s in methods['sources']:
    rid = method_ids[s['id']]
    unavailable = s['read_level_this_subtask'] in ['未全文', '摘要', '既有审计']
    access = '本轮未取得原刊全文；读取书目/摘要或承接既有审计'
    if not unavailable:
        access = '原刊全文载体可得，实际只定点阅读相关页'
        if s['id'] == 'GS2013':
            access = '本地作者稿可得；实际定点阅读，未把作者稿页码冒作原刊页码'
        if s['id'] == 'HK2026':
            access = '本轮成功取得出版社PDF字节并定点阅读；未另存下载盖章的PDF'
        if s['id'] == 'T2024':
            access = '本地出版社全文HTML可得；实际只读书目和第9节等相关段'
    year = re.search(r',\s*(19\d\d|20\d\d)\s*[,，]', s['bibliography'])
    catalog[rid] = {
        'id': rid, 'bibliography': s['bibliography'], 'doi': s['doi'],
        'publication_year': int(year.group(1)) if year else None,
        'primary_urls': [s['primary_url']] + ([s['official_record_url']] if s.get('official_record_url') else []),
        'actual_reading_level': s['read_level_this_subtask'],
        'actual_locator': s['actual_locator'], 'full_text_access': access,
        'whole_text_read_this_round': False,
        'supports': s['supports'], 'does_not_support': s['does_not_support'],
        'metadata_check': s['bibliographic_check'], 'evidence': s['evidence'],
        'review_record': {'path': str(BASE / 'methods-review.json'), 'record_id': s['id']},
    }

for s in theory['records']:
    rid = f"R{s['current_number_66']:03d}"
    access = '原刊全文本轮未取得；书目/摘要/原刊检索索引或既有审计层级'
    if s['id'] in ['Wen2014', 'LiEtAl2024', 'CasilliEtAl2023']:
        access = '本地发表版PDF可得，实际只核相关页；不声称通读全文'
    elif s['id'] == 'HeBaliRamesh2022':
        access = '本轮成功取得作者机构保存的发表版PDF字节并定点阅读；未保存新PDF'
    elif s['id'] == 'ThorntonOcasio2008':
        access = '作者上传原章的既有网页转写相关页可读；未新取得出版社排版全文'
    elif s['id'] == 'ChenBiWu2018':
        access = '本轮原刊检索索引相关段可读；直开/下载超时或502，结合此前原刊定点审计'
    catalog[rid] = {
        'id': rid, 'bibliography': s['bibliography'], 'doi': s['metadata'].get('doi'),
        'publication_year': s['metadata']['year'], 'metadata': s['metadata'],
        'primary_urls': [e['url'] for e in s['sources'] if e.get('url')],
        'actual_reading_level': s['evidence_tier_this_round'],
        'actual_locator': compact([e.get('locator', e.get('read_scope_this_round', '')) for e in s['sources']]),
        'full_text_access': access, 'whole_text_read_this_round': s['full_text_read_this_round'],
        'supports': s['direct_support'], 'does_not_support': s['does_not_support'],
        'evidence': s['sources'],
        'review_record': {'path': str(BASE / 'theory-review.json'), 'record_id': s['id']},
    }

for s in policy['reference_reviews']:
    rid = f"R{s['reference_number']:03d}"
    meta = s['bibliographic_metadata']
    # Keep a valid Z citation style as a blueprint. Verified dates and URLs are
    # supplied separately; no arbitrary journal style is imposed.
    issuer = meta.get('issuer')
    citation = old_by_id[rid]['text'].strip()
    if issuer:
        citation = ','.join(issuer) + '.' + meta['title']
        if meta.get('number'):
            citation += '（' + meta['number'] + '）'
        citation += '[Z].' + str(meta['year']) + '.' if meta.get('year') else '[EB/OL].'
    catalog[rid] = {
        'id': rid, 'bibliography': citation, 'doi': None,
        'publication_year': meta.get('year'), 'metadata': meta,
        'primary_urls': list(dict.fromkeys([meta[k] for k in ['official_url', 'official_notice_url', 'attachment_url'] if meta.get(k)])),
        'actual_reading_level': compact([e.get('read_level') for e in s['sources'] if e.get('read_level')]),
        'actual_locator': compact([e.get('locator') for e in s['sources'] if e.get('locator')]),
        'full_text_access': '详见实际载体与读取层级：官方原件/归档正文、官方转载或仅检索定位分开记录',
        'whole_text_read_this_round': False,
        'supports': s['condition'], 'does_not_support': '仅支持定位条款或解释；不由规范推断实际执行效果。适用范围及日期须另守各项边界。',
        'evidence': s['sources'],
        'review_record': {'path': str(BASE / 'policy-review.json'), 'record_number': s['reference_number']},
    }

for s in root['sources']:
    rid = s['reference_id']
    evidence = []
    for k in ['local_pdf', 'local_text']:
        if s.get(k):
            evidence.append({'path': s[k], 'sha256': s[k + '_sha256'], 'kind': 'author_final_manuscript' if k == 'local_pdf' else 'author_manuscript_text'})
    urls = [s[k] for k in ['primary_url', 'primary_metadata_url', 'primary_author_version_url'] if s.get(k)]
    urls += s.get('primary_metadata_urls', [])
    catalog[rid] = {
        'id': rid, 'bibliography': s.get('citation', s.get('current_entry')),
        'doi': s.get('doi'), 'publication_year': s.get('publication_year', s.get('issue_year')),
        'online_date': s.get('online_publication_date'), 'primary_urls': urls,
        'actual_reading_level': s['actual_read_scope_this_turn'],
        'actual_locator': s['actual_read_scope_this_turn'],
        'full_text_access': '本地LSE作者最终稿可得；未取得原刊排版全文' if rid == 'N-OM2004' else ('官方概念网页可读' if rid == 'N-WHO' else '本轮未取得原刊全文，原刊/官方数据库索引元数据核读'),
        'whole_text_read_this_round': False,
        'supports': s.get('supports', '中国HTA发展背景；本轮仅核年份和出版日期，不重新证明全部内容'),
        'does_not_support': s.get('does_not_supply', '不提供本研究药品五维逐句编码规则'),
        'metadata_check': s.get('correction_decision', s.get('online_repository_date_not_publication_year')),
        'evidence': evidence,
        'review_record': {'path': str(BASE / 'root-source-review.json'), 'record_id': rid},
    }

# Levesque is a conditional concept source, never a compulsory addition.
for s in theory.get('optional_fairness_concepts', []):
    if 'Levesque' not in s.get('id', ''):
        continue
    catalog['N-L2013'] = {
        'id': 'N-L2013', 'bibliography': s['bibliography'],
        'doi': s['metadata'].get('doi'), 'publication_year': s['metadata']['year'],
        'metadata': s['metadata'], 'primary_urls': [e['url'] for e in s['sources'] if e.get('url')],
        'actual_reading_level': s['evidence_tier_this_round'],
        'actual_locator': compact([compact(e.get('locators', e.get('locator', ''))) for e in s['sources']]),
        'full_text_access': s.get('full_text_access_note', '原刊开放全文可得；实际阅读范围按本轮台账，未宣称通读'),
        'whole_text_read_this_round': s.get('full_text_read_this_round', False),
        'actual_reading_scope': s.get('actual_reading_scope'),
        'supports': s['direct_support'], 'does_not_support': s['does_not_support'],
        'evidence': s['sources'],
        'review_record': {'path': str(BASE / 'theory-review.json'), 'record_id': s['id']},
    }

debt_ids = {'RX': 'N-RX2018', 'DUAL': 'N-DUAL2021'}
policy_matrix = read('snapshots/policy-matrix__policy_evidence_matrix.json')
matrix_sources = {s['id']: s for s in policy_matrix['sources']}
for debt in policy['table4_additional_source_debts']:
    rid = debt_ids[debt['source_id']]
    source = matrix_sources[debt['source_id']]
    dual = debt['source_id'] == 'DUAL'
    meta = {
        'title': source['title'], 'issuer': source['issuer'], 'year': 2021 if dual else 2018,
        'number': '医保发〔2021〕28号' if dual else '国卫办医发〔2018〕14号',
        'issue_date': '2021-04-22' if dual else '2018-06-29',
        'publication_date': '2021-05-10' if dual else None,
        'date_verification': '本轮官方网页日期栏和落款直接核定' if dual else '2018-06-29印发及文号承接既核矩阵，本轮官方网页412未取得；不猜公开日',
    }
    catalog[rid] = {
        'id': rid, 'bibliography': f"{source['issuer']}.{source['title']}（{meta['number']}）[Z].{meta['year']}.",
        'doi': None, 'publication_year': meta['year'], 'metadata': meta,
        'primary_urls': [source['official_url']],
        'actual_reading_level': '本轮根代理定点读归档官方正文；双通道另读官方网页' if dual else '本轮根代理定点读归档官方正文第15条；官网412，日期承接既核矩阵',
        'actual_locator': '本地TXT L1–17、L22；官方网页日期及第三、四部分' if dual else '本地TXT L75–95，第15条（一）5–7',
        'full_text_access': '归档官方完整正文可得，实际定点阅读；不声称原网页全篇核读',
        'whole_text_read_this_round': False, 'supports': debt['current_claim'],
        'does_not_support': '正文具体安全责任可据对应条款；不是当前五维定义、实际执行效果或新验证完成的证据。',
        'evidence': [{'path': source['local_path'], 'sha256': source['sha256'], 'kind': 'archived_official_body'}],
        'review_record': {'path': str(BASE / 'policy-review.json'), 'section': 'table4_additional_source_debts', 'source_id': debt['source_id'], 'additional_root_read': True},
    }
    spec['conditional_new'].append({'id': rid, 'trigger': '最终表4或解释保留“' + debt['current_claim'] + '”的具体责任', 'decision': debt['decision']})

# Bind mutable project inputs to their read-time snapshots. A later correction
# in the main task must not invalidate or silently replace the cited version.
frozen_by_path = {f['original_path']: f for f in manifest['files']}
for source in catalog.values():
    normalized = []
    for evidence in source.get('evidence', []):
        e = dict(evidence)
        key = 'path' if e.get('path') else 'source_path'
        path = e.get(key)
        if path and path.startswith(('https://', 'http://')):
            e['url'] = path
            e.pop(key, None)
        elif path in frozen_by_path:
            frozen = frozen_by_path[path]
            expected = e.get('sha256', e.get('source_sha256'))
            if expected == frozen['sha256']:
                e['original_path_at_read_time'] = path
                e[key] = frozen['snapshot_path']
                e['delivery_binding'] = 'read_time_snapshot; live project file may advance'
        normalized.append(e)
    source['evidence'] = normalized

core = []
for item in spec['core']:
    record = dict(item)
    if item['id'] == 'N-HS2005':
        record['claims'] = ['由先有理论确定起始类别、操作定义和未覆盖内容的检查；正反例由本文手册具体组织']
    record['source'] = catalog[item['id']]
    record['legacy_number'] = int(item['id'][1:]) if item['id'].startswith('R') else None
    record['current_citation_locations'] = old_by_id.get(item['id'], {}).get('citation_locations', [])
    core.append(record)
conditionals = []
for item in spec['conditional_old'] + spec['conditional_new']:
    record = dict(item)
    record['source'] = catalog.get(item['id'], {
        'id': item['id'], 'bibliography': old_by_id.get(item['id'], {}).get('text', '').strip(),
        'actual_reading_level': '本轮仅角色/引用位置复核；既有书目审计保留，未逐篇重读或取得全文',
        'full_text_access': '本轮未重新核定；不可据本清单声称全文验证通过',
        'whole_text_read_this_round': False,
        'review_record': {'path': str(BASE / 'snapshots/previous-biblio__参考文献核验.json'), 'numbering_warning': '旧审计编号不同，匹配完整书目；不按旧编号强行对应'},
    })
    record['legacy_number'] = int(item['id'][1:]) if item['id'].startswith('R') else None
    record['current_citation_locations'] = old_by_id.get(item['id'], {}).get('citation_locations', [])
    conditionals.append(record)

core_ids = {x['id'] for x in core}
conditional_ids = {x['id'] for x in conditionals}
legacy_dispositions = []
for rid, item in old_by_id.items():
    status = 'core' if rid in core_ids else ('conditional' if rid in conditional_ids else 'development_or_redundant_after_claim_removal')
    legacy_dispositions.append({
        'id': rid, 'original_number': item['number'], 'original_entry_unchanged': item['text'],
        'current_locations': item['citation_locations'], 'planned_disposition': status,
        'reason': next((x['role'] for x in core if x['id'] == rid), None) or next((x['decision'] for x in conditionals if x['id'] == rid), None) or item['reason'],
        'reading_this_round': catalog.get(rid, {}).get('actual_reading_level', '角色与实际引用位置复核；本轮未逐篇复读原文'),
        'action': '仅规划，未删除、重编号、替换书目或正文。非核心来源的原句/具体事实保留时须重新决定，不可直接删引文。',
    })

matrix_by_id = {s['id']: s for s in matrix['matrix']}
step_coverage = []
for s in steps:
    row = dict(s)
    original = matrix_by_id[s['id']]
    row.update({'step_name': original['步骤'], 'historical_implementation': original['当前实际实施'], 'matrix_snapshot_status': original['本轮状态'],
                'execution_scope': '历史实施与当前开发状态分开；本清单不完成抽样、真人首判、裁定或最终统计',
                'standalone_citation_required': False})
    step_coverage.append(row)

boundaries = [
    '本文五维共同框架由2026医保申报要求、2021卫健原六维及药监具体用途映射形成；政策栏目不是逐句命中充分条件。',
    '陈星平§2.3参考点内部构成、§3/Table3报告总句数强度与文宏总句数分母分别记录；本文五维编码句次合计分母为明示研究定义，不冒称相同原法。',
    'Hsieh仅支持由先有类别形成操作定义、检查未覆盖内容的流程，不提供本文五维、上游F或0.80阈值。',
    'Oliver/WHO支持按需要的获取机会和公平概念；当前上游F需“具体治疗需要或缺口—有条件优先/申请/资源机会”关系，是本研究的扩展操作化。临床管理难度本身不判F。',
    '0.80是用户设定的项目逐维κ/P/R/F1验收要求，不是统一文献发表阈值。不新增置信下限≥0.80条件，不用均值/AC1/稳定性代替未通过维度。',
    'P/R/F1由逐维混淆表和明示公式定义；Grimmer/Keith支持任务内验证，不另增一般LLM应用性能论文。加权F1须说明设计权重，而非误用Halterman的类别支持数加权F1。',
    '访谈纪要承担机制解释或现实问题来源；已封存接收记录不等于完成系统定性编码、多来源三角验证或编码信度。',
    'R040覆盖现用R056口径需未来同步调整年度表述，并限定谈判药品支付标准；竞价药品另有基金支付基准口径。',
    '政策发布、成文、施行和语料截止时间分开；GCP2026在7月语料截止时已发布、尚未施行。不得以2026规范倒灌历史年度条款。',
    '理论和来源服务真实最终发现，不预设最终三部门结构、I/F主轴或固定论文组织；本包只给最少引文覆盖预案。',
]
bootstrap = {
    'status': '事前契约v2拟选为主要区间；新独立参照、实际抽样与整体冻结仍未完成',
    'later_contract_v2': steering,
    'declared_primary': '同记录、全部方法和五维共用重复权重；5000次、seed20261010、逐指标百分位95%',
    'declared_secondary': '同设计FPC四格协方差和解析梯度线性化，用作复核/诊断，不能结果出来后择优',
    'current_engine_snapshot': str(BASE / 'snapshots/engine__metrics_engine.py'),
    'design_if_used': '固定分层简单随机不放回（SRSWOR），已知N_h和n_h；重抽样m_h=n_h−1',
    'factor': 'a_hi = 1 + sqrt(1 − n_h/N_h) * (n_h*k_hi/(n_h−1) − 1)',
    'direct_source': 'N-BE2022，§3.3式(20)，原刊p344–345；非线性近似讨论§8',
    'historical_source': 'R048，RWY1992§3.3式(3.4)给重缩放溯源，但不包含当前完整有限总体修正因子',
    'decisions': ['实际使用上述设计则增补N-BE2022，R048可省；已知概率的非全取总体加权再条件保留R049。',
                  '全取层因子固定1；非全取单例层无该有效重缩放式，需修改设计，不能任意补一个因子。',
                  '引用总量无偏文献不证明κ、P/R/F1或注意力比率无偏；先算加权总量/混淆表，再构成统计量。',
                  '原文权重方差方法及光滑非线性近似不保证稀有类百分位95%区间的有限样本覆盖率；NA、退化和空正类须报告。',
                  '5000次和seed20261010是本项目事前契约参数；不得称论文强制该次数。全取有限语料描述不默认制造抽样区间。',
                  '若最终采用其他设计（含分阶段筛选、两相或不等概率），重新核设计与因子，不能因文献标题写有多阶段就声称本项目执行了多阶段抽样。'],
}

plan = {
    'schema': 'minimum-reference-claim-coverage-v1', 'created_at': now, 'status': 'writing_preparation_complete_no_manuscript_edit',
    'requested_model': 'gpt-6.1-sol', 'requested_reasoning_effort': 'ultra',
    'scope': {'write_directory': str(BASE), 'current_references_preserved': 66,
              'manuscript_modified': False, 'citations_replaced': False, 'earlier_deliverables_modified': False,
              'full_manuscript_written': False, 'final_empirical_acceptance_asserted': False},
    'baseline': {'manuscript': old['baseline_path'], 'sha256': old['baseline_sha256'], 'current_all_66_are_cited': True,
                 'frozen_inputs': str(BASE / 'planning_input_manifest.json'),
                 'execution_state_read_time': root['new_execution_state_read']['observed_last_integration_at'],
                 'execution_state': root['new_execution_state_read']['state']},
    'selection_summary': {'core_total': len(core), 'legacy_core': sum(x['legacy_number'] is not None for x in core),
                          'new_core': sum(x['legacy_number'] is None for x in core), 'policy_core': 12, 'academic_core': 11,
                          'legacy_conditional': len(spec['conditional_old']), 'new_conditional': len(spec['conditional_new']),
                          'legacy_development_or_redundant': sum(x['planned_disposition'].startswith('development') for x in legacy_dispositions),
                          'basis': '由拟保留中心主张的最直接来源决定；23不是期刊上限、最终数量或保留全部现稿细节的保证。',
                          'previous_38_42_range': '旧交付保持；原编辑预算不作本次任意数量目标。',
                          'minimal_addition_examples': '若执行非全取概率样本及上述含FPC重抽样，在核心基础上通常加R049与N-BE2022；若同请求重复/等义微扰正式报告，再加R066。每条仍由实际主张触发。',
                          'publication_text_vs_corpus_archive': '正文参考书目可精简，原始51条政策语料清单/136份源文件及开发原文档案保留，不随正文减引文删除。'},
    'core_references': core, 'conditional_references': conditionals,
    'legacy_66_dispositions': legacy_dispositions, 'same_function_consolidation': spec['redundancy_groups'],
    'steps_21_coverage': step_coverage,
    'no_standalone_citation_steps': ['标识符完整性、冻结与SHA校核', '待定/执行失败台账', '未知值情景边界', '文档/系列/归属敏感性', '布尔共现和条件比例', '交付核验'],
    'minimum_method_groups': ['操作定义与计数：N-HS2005/R029', '文本测量开发与任务内验证：R045/R043', '逐维κ：R046',
                              '机会/公平概念：N-OM2004，另连具体政策', '抽样、区间和稳定性按实际执行条件增加'],
    'critical_claim_boundaries': boundaries, 'bootstrap_citation_implementation_match': bootstrap,
    'later_steering_separately_recorded': steering,
    'not_default_additions': [{'id': 'N-GW2008', 'reason': '当前引擎没有AC1；只有真正实施并报告时再核全文和公式，不自动添加或替换κ。'},
                             {'id': 'R042/R047', 'reason': '他域ChatGPT/聊天机器人性能不证明本项目；一般宣传或开发比较留档。'},
                             {'id': 'SK18/SVREP', 'reason': '软件公式和实现可在技术附录/复现说明引官方文档；不自动额外计入正文书目。'}],
    'reading_level_policy': {'full_text_available_is_not_full_text_read': True, 'prior_audit_is_not_new_fulltext_check': True,
                            'all_66_new_fulltext_read_claimed': False, 'unavailable_or_partial_records_kept_explicit': True,
                            'specialist_reviews': [str(BASE / f) for f in ['methods-review.json','theory-review.json','policy-review.json','root-source-review.json']]},
    'next_application_rule': '待真实最终发现与方法执行确定后逐主张采用、合并或删除；重新编首引顺序编号并保存crosswalk。当前R编号仅定位既有66条，N编号为规划候选。',
}

fixes = []
for rid, source in catalog.items():
    if rid not in old_by_id:
        continue
    original = old_by_id[rid]['text']
    if source.get('doi') and source['doi'].casefold() not in original.casefold():
        fixes.append({'id': rid, 'type': 'bibliographic_completion', 'current_entry': original,
                      'verified_doi': source['doi'],
                      'suggested_entry': source['bibliography'] + ('' if source['doi'].casefold() in source['bibliography'].casefold() else ' DOI:' + source['doi'] + '.'),
                      'action': '如最终保留，按期刊规范补DOI；不是凭缺DOI判为不存在或不合格。',
                      'metadata_evidence': source['review_record'], 'actual_reading_level': source['actual_reading_level'], 'applied': False})
for s in policy['reference_reviews']:
    rid = f"R{s['reference_number']:03d}"
    fixes.append({'id': rid, 'type': 'policy_metadata_completion_or_preservation',
                  'current_entry': old_by_id[rid]['text'], 'verified_metadata': s['bibliographic_metadata'],
                  'action': s['bibliographic_completion_needed'], 'style_rule': 'Z有效时不强制改EB/OL；如采用网络载体格式，补经核日期/URL，未核字段留空。',
                  'applied': False})
fixes += [
    {'id': 'R026', 'type': 'year_guard_no_change', 'issue_year': 2023, 'online_date': '2024-05-08',
     'doi': '10.1080/23288604.2024.2327099', 'action': '按原刊指定引用保留2023卷9(3):2327099；不据DOI字符串改为2024。原刊全文本轮未取得。', 'applied': False},
    {'id': 'R043', 'type': 'year_guard_no_change', 'issue_year': 2026, 'online_date': '2025-09-19',
     'action': '保留正式2026，34(2):188–204；期2来自既有书目核定，本轮首页直接核卷年页码和DOI。', 'applied': False},
    {'id': 'R033', 'type': 'year_guard_no_change', 'issue_year': 1997, 'web_first_published': '1998-12-04',
     'action': '保留1997正式卷年；1998网页上线不改出版年。', 'applied': False},
    {'id': 'R049', 'type': 'year_guard_no_change', 'issue_year': 1952, 'digital_online_date': '2012-04-11',
     'action': '保留1952，不用后期数字化上线日期改年。', 'applied': False},
    {'id': 'R051', 'type': 'year_guard_no_change', 'issue_date': '2025-09-09', 'publication_date': '2025-09-12',
     'action': '原件核定保持2025；不能机械改2024或2026。', 'applied': False},
    {'id': 'R040/R056', 'type': 'conditional_claim_and_source_consolidation',
     'action': '未来若改为2026口径/年度中性且明确谈判药品，R040覆盖现P82两个解释，R056可退出正文；旧语料来源仍保留。', 'applied': False},
    {'id': 'R048/N-BE2022', 'type': 'execution_matched_source_change',
     'action': '实际采用含FPC固定分层SRSWOR重缩放式时用2022式20作直接依据；RWY1992仅溯源，可省。不是立即替换现稿引文。', 'applied': False},
    {'id': 'R066', 'type': 'conditional_disposition_revised',
     'action': '从旧删除候选改为条件保留：第9节直接支持同请求重复和等义微扰；仅在最终真实执行并报告时进入书目。', 'applied': False},
    {'id': 'N-OM2004', 'type': 'year_guard_for_new_source', 'publication_year': 2004,
     'action': '作者稿Oct2003文件名及2005仓储上线均不是正式出版年。', 'applied': False},
]
fixes_doc = {'schema': 'bibliographic-fixes-plan-v1', 'created_at': now,
             'scope': '书目补全、保年保护、具体主张/来源匹配；不作正文或66条书目的实际修改',
             'applied_changes': 0, 'reference_numbering': 'R001–R066为当前底稿原编号；旧51条审计编号不同，不能直接按编号移植。',
             'fixes': fixes,
             'new_sources': [catalog[x['id']] for x in core + conditionals if x['legacy_number'] is None],
             'not_new_core': ['Gwet/AC1未执行不添加', 'WHO与Oliver不堆叠', 'Levesque获取过程未采用不添加', '一般LLM宣传综述不添加'],
             'unresolved_bibliographic_fields': ['R001封面没有唯一机构责任者，已核国务院提出/全国人大批准；不以国家发展改革委托管网站猜作者。',
                                                'R037本轮核2021-07-21成文，网页精确公开日未重新取得。',
                                                'R057本轮恢复正文未见成文落款，只核2019-04-09公开日。',
                                                'R064主题页没有固定发布日期；不猜出版年，访问日沿既核记录或将来实际核读更新。',
                                                'N-RX2018官方网页本轮412；成文日/文号承接既核矩阵，不冒称本轮重核。'],
             'verification_references': [str(BASE / f) for f in ['methods-review.json','theory-review.json','policy-review.json','root-source-review.json']]}

save('core-reference-coverage.json', plan)
save('bibliographic-fixes.json', fixes_doc)

lines = [
    '# 最少必要引文与主张覆盖预案', '',
    f'生成时间：{now}。任务为写作前来源规划，未写完整正文、未改原DOCX、未替换引文。', '',
    '**精简核心为23条：既有21条＋新增Hsieh（2005）和Oliver–Mossialos（2004），其中制度原文12条、学术来源11条。** 数量由拟保留主张的直接覆盖决定，不设期刊上限。此前38–42条是旧编辑预算，已封存保留，不约束本次清单。', '',
    '23条适用于压缩重复综述、旁支及具体细节后的主线。现稿66条均有正文引用，保持原状；不能不改原句就直接删除“非核心”引文。最终发现、具体制度表述和实际执行的方法决定是否增减。', '',
    '## 一、核心清单及每条承担的主张', '',
    '| 定位ID | 来源 | 必要作用 | 支持边界 |', '|---|---|---|---|',
]
for x in core:
    src = x['source']
    lines.append(f"| {x['id']} | {cell(src['bibliography'])} | {cell(x['role'])}：{cell(x['claims'])} | {cell(x['no_expansion'])} |")
lines += ['', 'R编号沿当前66条，不是未来首引编号；N编号仅为规划新增候选。完整DOI、原刊/官方URL和载体哈希见JSON。', '',
          '## 二、实际读取层级和定位', '',
          '“全文载体可得”与“全文通读”分开。相关页能支持主张即可明确定位；本次不声称重新读完66篇。', '',
          '| ID | 实际读取层级 | 本轮定位／全文取得情况 |', '|---|---|---|']
for x in core:
    src = x['source']
    urls = src.get('primary_urls', [])
    doi = src.get('doi')
    source_link = link('DOI', 'https://doi.org/' + quote(doi, safe='/():;')) if doi else (link('官方来源', urls[0]) if urls else '')
    lines.append(f"| {x['id']} {source_link} | {cell(src['actual_reading_level'])} | {cell(src['actual_locator'])}；{cell(src['full_text_access'])} |")
lines += ['', 'Cohen本轮为出版社书目与官方软件公式核对，未取得原刊全文；Ocasio为出版社摘要/元数据；陈星平为原刊检索索引相关段加此前原刊定点审计。Thornton为作者原章转写；Grimmer与Oliver为作者稿。以上层级不提升为原刊全文核验。', '',
          '## 三、条件性保留与执行触发', '',
          '| ID | 条件来源 | 真正触发条件 | 处理 |', '|---|---|---|---|']
for x in conditionals:
    src = x['source']
    lines.append(f"| {x['id']} | {cell(src['bibliography'])} | {cell(x['trigger'])} | {cell(x['decision'])} |")
lines += ['',
          '若最终执行非全取概率样本及当前含有限总体修正的重缩放bootstrap，在23条基础上通常加入R049和N-BE2022；同请求复测/等义微扰正式报告时再加入R066。全取有限语料的描述性结果不因此自动需要抽样引用。条件清单是逐主张选择，不是一组全部加回的参考文献。', '',
          'Gwet暂不添加：当前引擎未实施AC1。P/R/F1直接给逐维混淆表和公式，已有任务内验证来源，不再添加通用LLM性能文献。WHO、Oliver和Levesque各承担不同概念作用，未使用的模型留开发档案。', '',
          '## 四、21步覆盖：合并到方法组，不逐步配一篇', '',
          '| 步骤 | 核心／条件引文 | 本研究自己须明示的设计或证据 |', '|---|---|---|']
for s in step_coverage:
    refs = '、'.join(s['core_refs']) or '不需要独立引文'
    if s['conditional_refs']:
        refs += '；条件：' + '、'.join(s['conditional_refs'])
    lines.append(f"| {s['id']} {cell(s['step_name'])} | {refs} | {cell(s['own_basis'])} |")
lines += ['',
          'SHA、ID完整性、待定台账、未知值边界、文件/系列/归属敏感性、布尔共现及交付验收主要是本文设计与复现记录，不凭文献数量证明。不同方法组可以共用同一来源。', '',
          '## 五、相同功能如何合并，哪些留开发档案', '',
          '| 相同作用 | 既有编号 | 默认保留 | 合并条件 |', '|---|---|---|---|']
for g in spec['redundancy_groups']:
    lines.append(f"| {cell(g['function'])} | {cell(g['old'])} | {cell(g['default_keep']) or '无'} | {cell(g['condition'])} |")
dev = [x for x in legacy_dispositions if x['planned_disposition'].startswith('development')]
lines += ['', '**默认退出正文、保留开发/来源档案的既有22条：** ' + '、'.join(x['id'] for x in dev) + '。', '',
          '它们承担重复综述、理论铺陈、利益相关者/博弈旁支、通用LLM性能或不再保留的具体事实。若最终结果需要其中某项独立主张，应恢复对应原文，不能只据“精简”结论删除来源。全部66条逐项去向及现稿引用位置在JSON保留。', '',
          '## 六、必须保留的概念与方法边界', '']
for b in boundaries:
    lines.append('- ' + b)
lines += ['', '### bootstrap来源与当前代码的匹配', '',
          '固定分层SRSWOR下，当前引擎重抽样数为m_h=n_h−1，权重因子为：', '',
          '`a_hi = 1 + sqrt(1 − n_h/N_h) × (n_h k_hi/(n_h−1) − 1)`', '',
          '直接依据为Beaumont–Émond（2022）§3.3式20，p344–345。RWY（1992）式3.4提供历史重缩放形式，单独不能支持本式的完整有限总体修正。2022标题提到多阶段/两相不代表本项目执行了该设计。', '',
          '后续事前契约v2拟选共同重缩放bootstrap为主要区间（5000次、seed20261010、逐指标百分位95%），全部方法和五维共用记录权重；解析线性化作复核/诊断。实际抽样、独立参照和整体冻结尚未完成，方法引用仍以执行触发。后续输入单独保存于 ' + link('later-steering-input.json', str(BASE / 'later-steering-input.json')) + '，原输入清单和快照未改。', '']
for b in bootstrap['decisions'][1:]:
    lines.append('- ' + b)
lines += ['', '## 七、书目修正与未取得全文事项', '',
          '按核定书目补缺失DOI、机构全称、正式文件/附件标题和经核日期。2025/2026医保问答合并与重抽样来源调整属于未来的主张/引文同步修改，不是本次执行。具体修正逐项见 ' + link('bibliographic-fixes.json', str(BASE / 'bibliographic-fixes.json')) + '。', '',
          'R043保留正式卷年2026；R033保留1997；R049保留1952；R051原件核定保持2025。R026按原刊卷期指定引用保留2023，另记2024-05-08在线日，不能依据DOI中的2024改年。Oliver正式出版2004，作者稿名2003和仓储上线2005均不替换出版年。', '',
          'R001未核唯一机构责任者；R037精确网页公开日、R057成文落款未重新取得；AIFA无固定发布日期。BY1993、CF1990、Gwet本轮仅官方摘要/书目；Kesselheim仅摘要；Guo原刊403未取得全文。条件来源若未来承担超出已读内容的主张，先取得对应原文。', '',
          '## 八、状态与应用方式', '',
          root['new_execution_state_read']['state'] + '读取状态为 ' + root['new_execution_state_read']['observed_last_integration_at'] + '，更晚主对话进展须另接收，不能冒写为本次来源规划的执行成果。', '',
          '后续契约v2另核：600/1444为剩余池方案，3037开发项纳入概率为0，不能靠加权变成4481全框验证。Specificity=TN/(FP+TN)，NPV=TN/(FN+TN)；初始文字写反已勘误，新引擎正确，κ/P/R/F1不受影响。这里只记录来源与契约边界，不重做统计或宣称完成验证。', '',
          '最终写作按真实发现确定结构，逐主张采用本清单。保留原语料/开发来源档案；正文书目精简后保存旧号—新首引编号crosswalk。', '',
          '- ' + link('机器可读主张覆盖与66条去向', str(BASE / 'core-reference-coverage.json')),
          '- ' + link('书目修正预案', str(BASE / 'bibliographic-fixes.json')),
          '- ' + link('冻结输入清单', str(BASE / 'planning_input_manifest.json')),
          '- ' + link('方法核查', str(BASE / 'methods-review.json')) + '；' + link('理论核查', str(BASE / 'theory-review.json')) + '；' + link('制度核查', str(BASE / 'policy-review.json')),
          '']
(BASE / 'core-reference-coverage.md').write_text('\n'.join(lines))
print(json.dumps({'core': len(core), 'conditional_old': len(spec['conditional_old']), 'conditional_new': len(spec['conditional_new']), 'development_old': len(dev), 'steps': len(steps), 'outputs': ['core-reference-coverage.json','core-reference-coverage.md','bibliographic-fixes.json']}, ensure_ascii=False))
