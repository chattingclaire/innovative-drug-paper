#!/usr/bin/env python3
"""
政策文本编码分析 v2 —— 筛选后版本
排除：抗肿瘤临床应用指导原则、药品目录清单、DRG/DIP、CDE年度审评报告、征求意见稿（已有正式版时）
保留：含评价标准/维度的政策框架文件
"""
import os
import re
import json
import csv
from collections import defaultdict

POLICY_DIR = '/Users/rainbow/Desktop/战略院/药企项目-创新药/政策文件'
TXT_DIR = os.path.join(POLICY_DIR, 'txt_extracted')
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# === 排除规则 ===
EXCLUDE_PATTERNS = [
    '国家基本医保药品目录-20',       # 药品清单
    '商业健康保险创新药品目录-2025',   # 药品清单
    '新型抗肿瘤药物临床应用指导原则',   # 临床用药手册，非评价框架
    'DRG-DIP',                       # 支付分组技术规范
    '年度药品审评报告',               # 统计年鉴
    'README',
    'PKULaw-搜索结果',
    '医保药品目录及商保目录',
    '医保药品目录调整公告',            # 公告（仅公布结果，无评价标准）
    '征求意见稿',                     # 统一排除所有征求意见稿（保留正式版）
]

# 征求意见稿：如果同目录下有对应正式版，则排除征求意见稿
# 处理逻辑：先收集所有文件，再去重

def should_exclude(fname):
    for pat in EXCLUDE_PATTERNS:
        if pat in fname:
            return True
    return False

def classify_dept(fname):
    fname_upper = fname.upper()
    if fname_upper.startswith('NMPA') or fname_upper.startswith('CDE'):
        return 'NMPA'
    elif fname_upper.startswith('NHSA'):
        return 'NHSA'
    elif fname_upper.startswith('NHC'):
        return 'NHC'
    elif fname_upper.startswith('GOV'):
        return 'GOV'
    return 'OTHER'

# === 关键词词典 ===
DIMENSIONS = {
    '安全性': [
        '安全', '不良反应', '毒性', '风险管理', '药物警戒',
        '安全性评价', '安全信号', '风险控制', '风险评估',
        '获益.*风险', '风险.*获益', '安全监测', '风险分担',
        '副作用', '禁忌', '质量可控', '质量控制',
    ],
    '有效性': [
        '有效性', '疗效', '临床价值', '临床获益', '治疗效果',
        '临床必需', '临床需求', '生存率', '生存期',
        '临床试验', '临床研究', '临床证据', '循证',
        '治疗价值', '临床优势', 'QALY', '生命质量',
        '真实世界', '临床综合评价',
    ],
    '经济性': [
        '经济性', '成本效果', '成本效用', '成本效益',
        '药物经济', '价格合理', '费用', '预算影响',
        '支付标准', '医保基金', '基金承受', '基金可持续',
        '谈判', '定价', '价格', '报销', '支付',
        '成本', '经济学', '药品费用', '医疗费用',
    ],
    '创新性': [
        '创新', '新药', '突破性', '首创',
        '新化合物', '新靶点', '新机制', '新适应症',
        '加快上市', '优先审评', '附条件批准', '特别审批',
        '临床急需', '未满足需求', '填补.*空白',
        '自主研发', '原始创新', '仿制药',
    ],
    '公平性': [
        '公平', '可及', '可获得', '可负担',
        '基层', '保基本', '基本用药', '基本药物',
        '罕见病', '儿童用药', '短缺', '供应保障',
        '分级诊疗', '公共卫生', '健康权益',
        '城乡', '区域差异', '贫困', '适宜性',
        '合理用药', '处方',
    ],
}

DIM_PATTERNS = {}
for dim, keywords in DIMENSIONS.items():
    DIM_PATTERNS[dim] = [re.compile(kw) for kw in keywords]

ALL_DIMS = ['安全性', '有效性', '经济性', '创新性', '公平性']


def split_sentences(text):
    text = re.sub(r'\s+', ' ', text)
    sents = re.split(r'[。；！？\n]', text)
    return [s.strip() for s in sents if len(s.strip()) >= 4]


def code_sentence(sent):
    dims_hit = set()
    for dim, patterns in DIM_PATTERNS.items():
        for pat in patterns:
            if pat.search(sent):
                dims_hit.add(dim)
                break
    return dims_hit


def remove_draft_duplicates(file_list):
    """如果有正式版，去掉对应的征求意见稿"""
    final_set = set()
    drafts = set()
    for fname in file_list:
        if '征求意见稿' in fname:
            drafts.add(fname)
        else:
            final_set.add(fname)

    for draft in drafts:
        # 看有没有对应正式版
        # e.g. "NHSA-目录调整工作方案征求意见稿-2026.txt" -> "NHSA-目录调整工作方案-2026-正式版.txt"
        base = draft.replace('征求意见稿', '').replace('--', '-')
        has_final = False
        for final in final_set:
            if '正式版' in final:
                # 简单匹配：部门前缀和年份相同
                draft_dept = draft.split('-')[0]
                final_dept = final.split('-')[0]
                draft_year = re.search(r'20\d{2}', draft)
                final_year = re.search(r'20\d{2}', final)
                if (draft_dept == final_dept and draft_year and final_year
                    and draft_year.group() == final_year.group()):
                    # 检查是否同类文件
                    draft_type = re.sub(r'[-\d.a-zA-Z征求意见稿]', '', draft)
                    final_type = re.sub(r'[-\d.a-zA-Z正式版]', '', final)
                    if draft_type == final_type:
                        has_final = True
                        break
        if not has_final:
            final_set.add(draft)
        else:
            pass  # 排除此征求意见稿

    return final_set


def load_texts():
    all_files = {}  # fname -> (dept, text, source)

    # md files
    for fname in sorted(os.listdir(POLICY_DIR)):
        if not fname.endswith('.md'):
            continue
        if should_exclude(fname):
            continue
        dept = classify_dept(fname)
        if dept == 'OTHER':
            continue
        with open(os.path.join(POLICY_DIR, fname), 'r', encoding='utf-8') as f:
            text = f.read()
        all_files[fname] = (dept, text, 'md')

    # txt files from PDF
    if os.path.isdir(TXT_DIR):
        for fname in sorted(os.listdir(TXT_DIR)):
            if not fname.endswith('.txt'):
                continue
            orig = fname.replace('.txt', '.pdf')
            if should_exclude(orig) or should_exclude(fname):
                continue
            dept = classify_dept(fname)
            if dept == 'OTHER':
                continue
            # 避免md和txt重复（同一文件两种格式）
            md_equiv = fname.replace('.txt', '.md')
            if md_equiv in all_files:
                continue
            with open(os.path.join(TXT_DIR, fname), 'r', encoding='utf-8') as f:
                text = f.read()
            if len(text.strip()) < 100:
                continue
            all_files[fname] = (dept, text, 'txt')

    # 去掉征求意见稿（已有正式版时）
    kept = remove_draft_duplicates(set(all_files.keys()))
    removed = set(all_files.keys()) - kept
    if removed:
        print(f"去掉征求意见稿（已有正式版）: {len(removed)} 份")
        for r in sorted(removed):
            print(f"  - {r}")
        print()

    return [(fname, all_files[fname][0], all_files[fname][1])
            for fname in sorted(kept)]


def main():
    docs = load_texts()
    print(f"筛选后文件总数: {len(docs)}")

    dept_counts = defaultdict(int)
    for _, dept, _ in docs:
        dept_counts[dept] += 1
    print(f"部门分布: NMPA={dept_counts['NMPA']}, NHSA={dept_counts['NHSA']}, NHC={dept_counts['NHC']}, GOV={dept_counts.get('GOV',0)}")
    print()

    # 列出所有文件
    print("纳入分析的文件清单：")
    for fname, dept, _ in docs:
        print(f"  [{dept}] {fname}")
    print()

    # === 编码 ===
    dept_dim_freq = defaultdict(lambda: defaultdict(int))
    file_dim_freq = {}
    dept_total_sents = defaultdict(int)
    dept_coded_sents = defaultdict(int)  # 至少命中一个维度的句子数

    for fname, dept, text in docs:
        sents = split_sentences(text)
        file_counts = defaultdict(int)
        file_coded = 0

        for sent in sents:
            dims = code_sentence(sent)
            if dims:
                file_coded += 1
            for dim in dims:
                dept_dim_freq[dept][dim] += 1
                file_counts[dim] += 1

        dept_total_sents[dept] += len(sents)
        dept_coded_sents[dept] += file_coded
        file_dim_freq[(fname, dept)] = dict(file_counts)

    # === 输出 ===
    target_depts = ['NMPA', 'NHSA', 'NHC', 'GOV']

    print("=" * 90)
    print("表A：部门×维度 关键词命中频次（编码单元：句子）")
    print("=" * 90)
    header = f"{'部门':<8}{'文件数':>6}" + "".join(f"{d:>8}" for d in ALL_DIMS) + f"{'编码句':>8}{'总句数':>8}"
    print(header)
    print("-" * 90)
    for dept in target_depts:
        row = f"{dept:<8}{dept_counts[dept]:>6}"
        for dim in ALL_DIMS:
            row += f"{dept_dim_freq[dept][dim]:>8}"
        row += f"{dept_coded_sents[dept]:>8}{dept_total_sents[dept]:>8}"
        print(row)

    # 合计
    row = f"{'合计':<8}{sum(dept_counts[d] for d in target_depts):>6}"
    for dim in ALL_DIMS:
        row += f"{sum(dept_dim_freq[d][dim] for d in target_depts):>8}"
    row += f"{sum(dept_coded_sents[d] for d in target_depts):>8}{sum(dept_total_sents[d] for d in target_depts):>8}"
    print(row)

    print()
    print("=" * 90)
    print("表B：部门×维度 注意力占比（%）= 维度频次 / 五维度频次之和 × 100")
    print("=" * 90)
    header = f"{'部门':<8}" + "".join(f"{d:>10}" for d in ALL_DIMS) + f"{'五维度合计':>10}"
    print(header)
    print("-" * 90)
    for dept in target_depts:
        total = sum(dept_dim_freq[dept][d] for d in ALL_DIMS)
        if total == 0:
            continue
        row = f"{dept:<8}"
        for dim in ALL_DIMS:
            pct = dept_dim_freq[dept][dim] / total * 100
            row += f"{pct:>9.1f}%"
        row += f"{total:>10}"
        print(row)

    print()
    print("=" * 90)
    print("表C：文件级编码明细（按部门分组）")
    print("=" * 90)

    for dept in target_depts:
        items = [(fname, counts) for (fname, d), counts in file_dim_freq.items()
                 if d == dept and sum(counts.values()) > 0]
        items.sort(key=lambda x: -sum(x[1].values()))

        print(f"\n--- {dept}（{len(items)}份有效文件）---")
        print(f"  {'文件名':<60} {'安全':>4} {'有效':>4} {'经济':>4} {'创新':>4} {'公平':>4} {'合计':>4}")
        for fname, counts in items:
            short = fname[:57] + '...' if len(fname) > 60 else fname
            total = sum(counts.values())
            row = f"  {short:<60}"
            for dim in ALL_DIMS:
                row += f" {counts.get(dim, 0):>4}"
            row += f" {total:>4}"
            print(row)

    # === 保存结果 ===
    output = {
        'file_count': {d: dept_counts[d] for d in target_depts},
        'dept_dim_freq': {d: {dim: dept_dim_freq[d][dim] for dim in ALL_DIMS} for d in target_depts},
        'dept_dim_pct': {},
        'dept_total_sents': {d: dept_total_sents[d] for d in target_depts},
        'files': [],
    }
    for dept in target_depts:
        total = sum(dept_dim_freq[dept][d] for d in ALL_DIMS)
        if total > 0:
            output['dept_dim_pct'][dept] = {
                dim: round(dept_dim_freq[dept][dim] / total * 100, 1) for dim in ALL_DIMS
            }

    for (fname, dept), counts in sorted(file_dim_freq.items()):
        if dept in target_depts:
            output['files'].append({
                'file': fname, 'dept': dept,
                **{dim: counts.get(dim, 0) for dim in ALL_DIMS}
            })

    out_path = os.path.join(SCRIPT_DIR, 'coding_results_v2.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 也输出CSV方便Excel查看
    csv_path = os.path.join(SCRIPT_DIR, 'coding_results_v2.csv')
    with open(csv_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['文件名', '部门', '安全性', '有效性', '经济性', '创新性', '公平性', '合计'])
        for item in output['files']:
            total = sum(item[d] for d in ALL_DIMS)
            writer.writerow([item['file'], item['dept']] + [item[d] for d in ALL_DIMS] + [total])

    print(f"\n结果已保存:")
    print(f"  JSON: {out_path}")
    print(f"  CSV:  {csv_path}")


if __name__ == '__main__':
    main()
