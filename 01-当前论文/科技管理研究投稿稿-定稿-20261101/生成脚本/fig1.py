import sys
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.patches import Rectangle, FancyArrowPatch
S = sys.argv[1]
fm.fontManager.addfont(S + '/fonts/SourceHanSerifSC-Bold.otf')
plt.rcParams['font.family'] = 'Source Han Serif SC'
W, H = 22.0, 12.8
fig = plt.figure(figsize=(W / 2, H / 2), dpi=200)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(H, 0); ax.axis('off')
def box(x, y, w, h, lines, size=12.5):
    ax.add_patch(Rectangle((x, y), w, h, fill=False, lw=1.4, ec='black'))
    n = len(lines)
    for k, s in enumerate(lines):
        ax.text(x + w / 2, y + h * (k + 1) / (n + 1), s, ha='center', va='center', fontsize=size, fontweight='bold')
def arrow(x, y0, y1):
    ax.add_patch(FancyArrowPatch((x, y0), (x, y1), arrowstyle='-|>', mutation_scale=13, lw=1.4, color='black'))
m, g, h = 0.6, 0.45, 1.5
full = W - 2 * m
bw = (full - 2 * 0.9) / 3
xs = [m + i * (bw + 0.9) for i in range(3)]
y = 0.3
for x, (a, b) in zip(xs, [('科学—安全逻辑', '药品注册与风险控制'), ('经济—效率逻辑', '医保准入与资源约束'), ('公共服务逻辑', '临床使用与用药保障')]):
    box(x, y, bw, h, [a, b]); arrow(x + bw / 2, y + h, y + h + g)
y += h + g
box(m, y, full, h, ['统一的五维评价框架', '安全性　有效性　经济性　创新性　公平性'])
hw = (full - 1.2) / 2; c1 = m + hw / 2; c2 = m + hw + 1.2 + hw / 2
arrow(c1, y + h, y + h + g); arrow(c2, y + h, y + h + g)
y += h + g; h3 = 2.1
box(m, y, hw, h3, ['注意力配置差异', '注意力占比与内容覆盖比例', '维度共现与部门差异检验'])
box(m + hw + 1.2, y, hw, h3, ['同一维度的评价任务差异', '评价对象与比较药品', '结论用途'])
arrow(c1, y + h3, y + h3 + g); arrow(c2, y + h3, y + h3 + g)
y += h3 + g
box(m, y, full, h, ['结合政策条文与访谈资料的理论解释', '部门评价差异与决策任务的对应关系'])
arrow(W / 2, y + h, y + h + g); y += h + g
box(m, y, full, h, ['跨部门协同的判断依据', '协调对象：评价结论的适用条件　　目标：评价规则可预期性与质效协同'])
arrow(W / 2, y + h, y + h + g); y += h + g
box(m, y, full, h, ['跨部门协同路径', '上市审评与医保准入的前置沟通　　上市后补充研究统筹　　临床应用反馈与证据更新'])
fig.savefig(S + '/figs/fig1.png', dpi=200)
print('ok')
