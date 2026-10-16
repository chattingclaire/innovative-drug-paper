#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成论文图1（分析框架图）与图2（三部门注意力雷达图）。需 matplotlib；中文字体用 Songti SC（Mac）。
图2数据 = 论文表4（词典编码口径）。"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np

cand=['Songti SC','STSong','SimSun','PingFang SC']
avail={f.name for f in fm.fontManager.ttflist}
plt.rcParams['font.family']=next((c for c in cand if c in avail),None)
plt.rcParams['axes.unicode_minus']=False

dims=['安全性','有效性','经济性','创新性','公平性']
data={'药监局':[28.5,44.9,0.7,21.5,4.3],'医保局':[4.8,5.0,65.7,15.8,8.6],'卫健委':[35.0,11.1,7.2,3.3,43.3]}
angles=np.linspace(0,2*np.pi,len(dims),endpoint=False).tolist(); angles+=angles[:1]
fig,ax=plt.subplots(figsize=(5.2,4.6),subplot_kw=dict(polar=True))
styles={'药监局':('-','o','#333333'),'医保局':('--','s','#666666'),'卫健委':(':','^','#000000')}
for k,v in data.items():
    vals=v+v[:1]; ls,mk,c=styles[k]
    ax.plot(angles,vals,linestyle=ls,marker=mk,markersize=4.5,linewidth=1.4,color=c,label=k)
    ax.fill(angles,vals,alpha=0.06,color=c)
ax.set_xticks(angles[:-1]); ax.set_xticklabels(dims,fontsize=11)
ax.set_ylim(0,70); ax.set_yticks([20,40,60]); ax.set_yticklabels(['20%','40%','60%'],fontsize=8,color='#555')
ax.set_theta_offset(np.pi/2); ax.set_theta_direction(-1)
ax.spines['polar'].set_color('#999'); ax.grid(color='#cccccc',linewidth=0.6)
ax.legend(loc='lower center',bbox_to_anchor=(0.5,-0.18),ncol=3,frameon=False,fontsize=10)
plt.tight_layout(); plt.savefig('fig2_radar.png',dpi=300,bbox_inches='tight'); plt.close()

from matplotlib.patches import FancyBboxPatch,FancyArrowPatch
fig,ax=plt.subplots(figsize=(8.6,5.6)); ax.axis('off'); ax.set_xlim(0,10); ax.set_ylim(0,10)
def box(x,y,w,h,text,fs=10.5):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.06",fc='white',ec='black',lw=1.1))
    ax.text(x+w/2,y+h/2,text,ha='center',va='center',fontsize=fs,linespacing=1.5)
def arrow(x1,y1,x2,y2):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle='-|>',mutation_scale=13,lw=1.1,color='black'))
ax.text(0.35,9.35,'宏观：制度逻辑',fontsize=11,fontweight='bold')
box(0.4,7.9,2.8,1.0,'科学-安全逻辑\n（药监局）'); box(3.6,7.9,2.8,1.0,'经济-效率逻辑\n（医保局）'); box(6.8,7.9,2.8,1.0,'公共服务逻辑\n（卫健委）')
ax.text(0.35,7.0,'中观：组织注意力配置',fontsize=11,fontweight='bold')
box(0.4,5.6,2.8,1.0,'安全信号\n技术创新指标'); box(3.6,5.6,2.8,1.0,'成本效果\n预算影响'); box(6.8,5.6,2.8,1.0,'临床需求\n公平可及')
for x in (1.8,5.0,8.2): arrow(x,7.85,x,6.75)
box(1.4,3.75,7.2,0.95,'政策文本中的评价维度配置（安全性·有效性·经济性·创新性·公平性）\n——认知分歧的可观测测量',fs=10)
for x in (1.8,5.0,8.2): arrow(x,5.55,x,4.85)
box(1.4,2.15,7.2,0.9,'三类制度性分歧：“创新”定义 ｜ 证据要求 ｜ 价值衡量',fs=10.5)
arrow(5.0,3.7,5.0,3.2)
box(1.4,0.5,7.2,0.95,'协调路径：对话与分级机制 ｜ 动态评价与审批-使用衔接 ｜ 信息共享与透明',fs=10.5)
arrow(5.0,2.1,5.0,1.6)
plt.tight_layout(); plt.savefig('fig1_framework.png',dpi=300,bbox_inches='tight')
print('done')
