from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.ticker import PercentFormatter
OUT=Path(__file__).resolve().parent
font='/System/Library/Fonts/Supplemental/Songti.ttc';fm.fontManager.addfont(font);name=fm.FontProperties(fname=font).get_name()
plt.rcParams.update({'font.family':name,'font.size':12,'axes.unicode_minus':False,'pdf.fonttype':42,'ps.fonttype':42})
data=json.loads((OUT/'统计及稳健性完整结果.json').read_text())['results']['LLM']['scenarios']['条款等权']
deps=['NMPA','NHSA','NHC'];names=['药监局','医保局','卫健委'];dims=['S','E','Ec','I','F'];labels=['安全性','有效性','经济性','创新性','公平性'];colors=['#336B8E','#71A4BE','#C18338','#8170A5','#70A38C']
fig,(ax,bx)=plt.subplots(2,1,figsize=(10.8,8.8),gridspec_kw={'height_ratios':[1.25,1]},layout=None)
fig.subplots_adjust(left=.15,right=.97,top=.88,bottom=.19,hspace=.58)
x=np.arange(3);width=.15
for i,(d,label,c) in enumerate(zip(dims,labels,colors)):
 vals=[data[dep]['dimensions'][d]['p_conditional_lower']*100 for dep in deps]
 bars=ax.bar(x+(i-2)*width,vals,width*.9,color=c,label=label,zorder=3)
 ax.bar_label(bars,labels=[f'{v:.1f}' for v in vals],padding=3,fontsize=10)
ax.set_xticks(x,[f'{n}\n条款数={data[dep]["clause_N"]}' for dep,n in zip(deps,names)])
ax.set_ylim(0,48);ax.set_yticks(range(0,50,10));ax.yaxis.set_major_formatter(PercentFormatter(100,decimals=0));ax.set_ylabel('占本部门全部条款的比例')
ax.set_title('A  各评价维度的条款占比',loc='left',pad=13,fontsize=14)
ax.grid(axis='y',color='#DDDDDD',linewidth=.6,zorder=0)
fig.legend(*ax.get_legend_handles_labels(),ncol=5,frameon=False,bbox_to_anchor=(.56,.975),loc='upper center',columnspacing=1.5)
left=np.zeros(3)
for d,label,c in zip(dims,labels,colors):
 vals=np.array([data[dep]['dimensions'][d]['q_observed']*100 for dep in deps]);bx.barh(x,vals,left=left,height=.52,color=c,edgecolor='white',linewidth=.5)
 for j,v in enumerate(vals):
  if v>=3:
   bx.text(left[j]+v/2,j,f'{v:.1f}%',ha='center',va='center',fontsize=10,color='white' if d in ['S','Ec','I'] else '#14252F')
  else:
   bx.annotate(f'{v:.2f}%',xy=(left[j]+v/2,j-.24),xytext=(left[j]+v/2,j-.50),ha='center',va='bottom',fontsize=10,arrowprops={'arrowstyle':'-','lw':.7,'color':'#555555'})
 left+=vals
bx.set_yticks(x,[f'{n}\n正标签数={int(data[dep]["positive_assignment_weight"])}' for dep,n in zip(deps,names)])
bx.set_ylim(2.6,-.75);bx.set_xlim(0,100);bx.set_xticks(range(0,101,20));bx.xaxis.set_major_formatter(PercentFormatter(100,decimals=0));bx.set_xlabel('占本部门五维正标签累计数的比例');bx.set_title('B  五个评价维度的内部构成',loc='left',pad=14,fontsize=14)
for a in [ax,bx]:
 for side in ['top','right']:a.spines[side].set_visible(False)
 a.spines['left'].set_color('#777777');a.spines['bottom'].set_color('#777777');a.tick_params(length=3,color='#777777')
fig.text(.15,.115,'注：同一条款可涉及多个维度。A图五维比例不要求合计100%；B图各部门合计100%。',fontsize=10.5)
fig.text(.15,.085,'待定判断另列：'+'、'.join(f'{n}{int(data[dep]["unresolved_assignment_weight"])}项' for dep,n in zip(deps,names))+'；不计入正标签，也不作为负标签。',fontsize=10.5)
fig.text(.15,.055,'资料来源：77条校准对应版本的4481条LLM保存结果。图中比例按已识别正标签计算。',fontsize=10.5)
fig.savefig(OUT/'三部门评价维度-双口径组合图.png',dpi=300)
fig.savefig(OUT/'三部门评价维度-双口径组合图.pdf')
fig.savefig(OUT/'三部门评价维度-双口径组合图-预览.png',dpi=130)
print('saved',name)
