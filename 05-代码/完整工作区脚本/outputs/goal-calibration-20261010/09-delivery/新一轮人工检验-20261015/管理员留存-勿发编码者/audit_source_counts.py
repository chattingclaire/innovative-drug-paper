import json
import hashlib
from pathlib import Path
from collections import Counter

ROOT = Path('/Users/rainbow/Desktop/战略院/药企项目-创新药')
HERE = Path(__file__).resolve().parent
BASE = ROOT / 'outputs/goal-calibration-20261010'
mapping_path = ROOT / 'outputs/validation-expansion-20260926/frozen-inputs/classification--部门归属与年度系列-冻结v1.json'
frame_path = BASE / '00-baseline/source-only-frame.jsonl'
mapping = json.loads(mapping_path.read_text())['rows']
frame = [json.loads(line) for line in frame_path.read_text().splitlines()]
counts = Counter(r['source_document_stem'] for r in frame)
class_stems = {Path(r['original_file']).stem for r in mapping}
snapshot_manifest = json.loads((BASE / '00-baseline/source_files_manifest.json').read_text())
file_checks = []
for r in snapshot_manifest['files']:
    p = Path(r['snapshot'])
    actual = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    file_checks.append({'original':r['original'], 'snapshot':str(p), 'expected':r['sha256'], 'actual':actual, 'ok':actual == r['sha256']})
groups = Counter(r['analysis_group'] for r in mapping)
frame_groups = Counter(r['analysis_group'] for r in frame)
result = {
    'date':'2026-10-15', 'classification_rows':len(mapping),
    'classification_counts':dict(groups), 'frame_units':len(frame),
    'frame_groups':dict(frame_groups), 'frame_source_count':len(counts),
    'classification_without_frame':[r['original_file'] for r in mapping if Path(r['original_file']).stem not in counts],
    'frame_without_classification':sorted(set(counts)-class_stems),
    'source_snapshot_file_checks':file_checks,
    'all_saved_source_snapshots_match_manifest':all(x['ok'] for x in file_checks),
    'limits':'源条目数不等于物理文件数；此核对确认映射和已保存快照完整性，不认证全部原文真实性、收集完备性或每项来源纳入理由。',
}
(HERE / '55项来源与全量样本对应核对.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
names = {'NMPA':'药监局系统','NHSA':'医保局系统','NHC':'卫健委系统','GOV':'中央综合政策'}
lines = ['# 55项原始来源与4481条分析材料的关系', '', '核对日期：2026-10-15。依据既有来源映射及全量材料清单重新计数；没有更改来源范围或重跑编码。', '',
         '**原清单共有55项来源：三部门51项，加中央综合政策4项。不是把55项删成51项。**', '',
         '| 类别 | 来源条目 | 三部门全量分析单元 |', '|---|---:|---:|']
for group in ['NMPA','NHSA','NHC','GOV']:
    lines.append(f'| {names[group]} | {groups[group]} | {frame_groups[group] if group != "GOV" else "另列背景材料，不进入4481条"} |')
lines += ['| 合计 | 55 | 4481 |', '',
          '“来源条目”是原项目采用的登记口径。一项可能关联通知正文、附件、官方解读以及不同格式的保存件，不能直接将55项说成55个彼此独立的物理文件。中央综合政策在既有框架中另有443条材料；这里的4481条只用于三部门比较。', '',
          '下面列出全部55项。中央综合政策保留在清单中；不把它们混入三部门比较，也不因为它们未进入4481条而称其“遗漏”。', '',
          '| 序号 | 原清单来源名称 | 归属 | 4481条中数量 |', '|---:|---|---|---:|']
for i, r in enumerate(mapping, 1):
    group = r['analysis_group']
    n = counts.get(Path(r['original_file']).stem, 0)
    lines.append(f'| {i} | {r["original_file"]} | {names[group]} | {n if group != "GOV" else "背景材料"} |')
lines += ['', '核对边界：', '',
          f'- 4481条材料对应{len(counts)}个来源名称；未匹配到原55项清单的来源数为{len(result["frame_without_classification"])}。',
          f'- 已保存的{len(file_checks)}份来源快照逐一核对文件指纹：' + ('均与原清单记录一致。' if result['all_saved_source_snapshots_match_manifest'] else '存在不一致，详见管理员核对记录。'),
          '- 文件指纹一致只说明保存件没有发生变化，不代表每份材料的目录题名和正文身份已经全部人工复核。',
          '- 此前发现的药监局“公告/解读”登记差异另见《来源范围交叉核对》。这项收藏记录并不在这55项分析来源中，不能据此推断4481条编码错用了该文件。',
          '- 两份时间范围内的卫健委候选材料未查到原纳入记录或逐项排除理由，仍为收集范围待核问题；没有因此增删原55项。', '']
(HERE.parent / '55项来源与4481条对应清单.md').write_text('\n'.join(lines))
print(json.dumps({k:v for k,v in result.items() if k!='source_snapshot_file_checks'}, ensure_ascii=False, indent=2))
