"""Prepare the original Figure 2 with the verified current Table 3 values."""
from pathlib import Path
import hashlib
import json

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.patches import Patch

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'table3-preparation.json'
EXPECTED_SOURCE_SHA = '1cb22b0c38dd5fed5e755d44bebb15527dd1290abe75d5c4224071e401bdbcf5'
data_bytes = SOURCE.read_bytes()
assert hashlib.sha256(data_bytes).hexdigest() == EXPECTED_SOURCE_SHA
data = json.loads(data_bytes)
DIMS = ['S', 'E', 'Ec', 'I', 'F']
NAMES = ['安全性', '有效性', '经济性', '创新性', '公平性']
COLORS = ['#2e5266', '#408a8c', '#d9b44a', '#81759b', '#b46d63']
DEPTS = ['NMPA', 'NHSA', 'NHC']
LABELS = ['药监局', '医保局', '卫健委']

available = {x.name: x.fname for x in font_manager.fontManager.ttflist}
chinese = next(x for x in ['Songti SC', 'STSong', 'SimSun', 'Arial Unicode MS'] if x in available)
cn = font_manager.FontProperties(fname=available[chinese])
legend_font = cn.copy()
legend_font.set_size(15)
plt.rcParams.update({'font.family': 'DejaVu Sans', 'axes.unicode_minus': False,
                     'svg.fonttype': 'path'})

fig, axes = plt.subplots(2, 1, figsize=(12.6, 5.7), dpi=200, sharex=True)
fig.subplots_adjust(left=.13, right=.965, bottom=.13, top=.82, hspace=.35)
fig.legend([Patch(facecolor=c) for c in COLORS], NAMES, ncol=5, loc='upper center',
           bbox_to_anchor=(.55, .997), frameon=False, prop=legend_font,
           handlelength=1.25, columnspacing=1.4, handletextpad=.5)

values = []
for ax, method, title in zip(axes, ['rule', 'native'], ['自动规则编码', 'LLM编码']):
    ax.set_title(title, loc='left', fontproperties=cn, fontsize=16, pad=7)
    for y, dept in enumerate(DEPTS):
        row = next(r for r in data['rows'] if r['method'] == method and r['department'] == dept)
        assert sum(row['T'].values()) == row['B']
        widths = [100 * row['T'][d] / row['B'] for d in DIMS]
        assert abs(sum(widths) - 100) < 1e-10
        left = 0.0
        for d, w, color in zip(DIMS, widths, COLORS):
            assert abs(w / 100 - row['q'][d]) < 1e-12
            ax.barh(y, w, left=left, height=.55, color=color, edgecolor='white', linewidth=.8, zorder=3)
            label = row['figure_percentages_1dp'][d]
            if w >= 3:
                ax.text(left+w/2, y, label, ha='center', va='center', fontsize=12.5,
                        color='black' if d == 'Ec' else 'white', zorder=4)
                position = 'inside'
            else:
                ax.annotate(label, xy=(left+w/2, y-.27), xytext=(left+w/2, y-.56),
                            ha='center', va='center', fontsize=11,
                            arrowprops={'arrowstyle': '-', 'lw': .65, 'color': '#555555'}, zorder=5)
                position = 'above_with_leader'
            values.append({'method': method, 'department': dept, 'dimension': d,
                           'T': row['T'][d], 'B': row['B'], 'percent': w,
                           'label': label, 'label_position': position})
            left += w
    ax.set_yticks(range(3), LABELS, fontproperties=cn, fontsize=15)
    ax.set_ylim(2.45, -.72)
    ax.set_xlim(0, 100)
    ax.set_xticks(range(0, 101, 20))
    ax.tick_params(axis='x', labelsize=15, length=4)
    ax.tick_params(axis='y', length=0, pad=7)
    ax.grid(axis='x', color='#d5d5d5', linewidth=.65, zorder=0)
    for name in ['top', 'right', 'left']:
        ax.spines[name].set_visible(False)
    ax.spines['bottom'].set_linewidth(.8)
axes[-1].set_xlabel('注意力占比（%）', fontproperties=cn, fontsize=15.5, labelpad=9)

paths = [ROOT/'figure2-current.png', ROOT/'figure2-current.svg']
fig.savefig(paths[0], dpi=200, facecolor='white')
fig.savefig(paths[1], facecolor='white', metadata={'Date': None})
plt.close(fig)

metadata = {
    'scope': 'Current paired full-corpus descriptive result; prepared for local original-manuscript merge.',
    'source': {'path': str(SOURCE), 'sha256': EXPECTED_SOURCE_SHA},
    'dimensions_px': [2520, 1140], 'dpi': 200,
    'dimensions': dict(zip(DIMS, NAMES)), 'colors': dict(zip(DIMS, COLORS)),
    'font': {'name': chinese, 'path': available[chinese]},
    'values': values, 'plotted_value_N': len(values), 'displayed_label_N': len(values),
    'plot_uses_exact_T_over_B': True, 'rounded_values_renormalized': False,
    'lawful_null_handling': 'Observed positive counts only; unknown dimensions remain unknown. See Table 3 note.',
    'DOCX_modified': False, 'formal_validation_complete': False,
    'outputs': [{'path': str(p), 'bytes': p.stat().st_size,
                 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths],
}
(ROOT/'figure2-current.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
print(json.dumps({'files': [p.name for p in paths], 'value_N': len(values)}, ensure_ascii=False))
