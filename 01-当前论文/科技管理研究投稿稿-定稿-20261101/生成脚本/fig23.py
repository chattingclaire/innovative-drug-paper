import csv, sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
S = sys.argv[1]
for f in ('SourceHanSerifSC-Regular.otf', 'SourceHanSerifSC-Bold.otf'):
    fm.fontManager.addfont(S + '/fonts/' + f)
plt.rcParams.update({'font.family': 'Source Han Serif SC', 'axes.unicode_minus': False})
rows = list(csv.DictReader(open(S + '/supp_data/复核数据/4481条全量编码.csv', encoding='utf-8-sig')))
deps = [('NMPA', '药监局'), ('NHSA', '医保局'), ('NHC', '卫健委')]
dims = [('S', '安全性'), ('E', '有效性'), ('Ec', '经济性'), ('I', '创新性'), ('F', '公平性')]
att, cov = {}, {}
for d, _ in deps:
    rs = [r for r in rows if r['部门'] == d]
    pos = {k: sum(1 for r in rs if r['LLM_' + k] == '1') for k, _ in dims}
    tot = sum(pos.values())
    att[d] = [100 * pos[k] / tot for k, _ in dims]
    cov[d] = [100 * pos[k] / len(rs) for k, _ in dims]
def draw(vals, xmax, xstep, xlabel, out):
    fig, axes = plt.subplots(1, 3, figsize=(11.1, 3.86), dpi=300, sharey=True)
    for ax, (d, name) in zip(axes, deps):
        v = vals[d]
        bars = ax.barh(range(5), v, height=0.45, color='#333333')
        ax.bar_label(bars, labels=[f'{x:.1f}' for x in v], padding=2, fontsize=8)
        ax.set_xlim(0, xmax); ax.set_xticks(range(0, xmax + 1, xstep))
        ax.set_ylim(4.5, -0.5)
        ax.set_yticks(range(5)); ax.set_yticklabels([n for _, n in dims], fontsize=11, fontweight='bold')
        ax.set_title(name, fontsize=11, fontweight='bold')
        ax.set_xlabel(xlabel, fontsize=10, fontweight='bold')
        ax.grid(axis='x', color='#dddddd', lw=0.6); ax.set_axisbelow(True)
        for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
        ax.tick_params(axis='y', length=0)
    fig.tight_layout(w_pad=3)
    fig.savefig(out, dpi=300)
    print(out, {d: [round(x, 1) for x in vals[d]] for d, _ in deps})
draw(att, 90, 20, '注意力占比/%', S + '/figs/fig2.png')
draw(cov, 50, 10, '内容覆盖比例/%', S + '/figs/fig3.png')
