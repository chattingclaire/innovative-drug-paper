"""New scientific figures drawn from the exact final descriptive data."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from fractions import Fraction
import json,hashlib
OUT=Path(__file__).resolve().parent
font_path='/System/Library/Fonts/Supplemental/Songti.ttc'
font=lambda n:ImageFont.truetype(font_path,n)
def center(draw,xy,text,size=44,color='black'):
    b=draw.textbbox((0,0),text,font=font(size));draw.text((xy[0]-(b[2]-b[0])/2,xy[1]),text,font=font(size),fill=color)

# A new analytical schematic, preserving the manuscript's three logical axes.
im=Image.new('RGB',(2200,1280),'white');d=ImageDraw.Draw(im)
def box(x,y,w,h,lines):
    d.rectangle((x,y,x+w,y+h),outline='black',width=3)
    for i,t in enumerate(lines):center(d,(x+w/2,y+24+i*65),t,44)
def arrow(x,y,xx,yy):
    d.line((x,y,xx,yy),fill='black',width=4)
    if xx==x:d.polygon([(xx,yy),(xx-12,yy-23),(xx+12,yy-23)],fill='black')
    else:d.polygon([(xx,yy),(xx-23,yy-12),(xx-23,yy+12)],fill='black')
for x,lines in [(70,['科学—安全逻辑','药品注册与风险控制']),(805,['经济—效率逻辑','医保准入与资源约束']),(1540,['公共服务逻辑','临床使用与用药保障'])]:box(x,30,590,170,lines);arrow(x+295,200,x+295,260)
box(70,260,2060,170,['统一五维观察框架','安全性　有效性　经济性　创新性　公平性'])
arrow(555,430,555,490);arrow(1645,430,1645,490)
box(70,490,970,240,['关注结构','各维编码句次／五维句次合计','注意力占比与部门间百分点差'])
box(1160,490,970,240,['维度内的政策内容','目标人群与比较方案','证据要求与结论用途'])
arrow(555,730,555,790);arrow(1645,730,1645,790)
box(70,790,2060,170,['结合政策原文与访谈解释','比较共同关注和判断条件的差别'])
arrow(1100,960,1100,1020)
box(70,1020,2060,170,['协调路径','评价结论对照　补充证据衔接　评审理由与使用反馈共享'])
im.save(OUT/'图1-制度逻辑与注意力分析框架.png',dpi=(300,300))

source=OUT/'三部门注意力分布与敏感性.json';a=json.loads(source.read_text());method=a['method_bindings']['rule']['method']
assert method=='rules_v30'
dims=['S','E','Ec','I','F'];cn=['安全性','有效性','经济性','创新性','公平性']
colors=['#2E5266','#408A8C','#D9B44A','#81759B','#B46D63'];names={'NMPA':'药监','NHSA':'医保','NHC':'卫健'}
im=Image.new('RGB',(2200,1070),'white');d=ImageDraw.Draw(im);left,right=300,2120;top,bottom=210,880;w=right-left
for x in range(0,101,20):
    xx=left+w*x/100;d.line((xx,top,xx,bottom),fill='#DADADA',width=2);center(d,(xx,bottom+20),str(x),40)
for i,(label,color) in enumerate(zip(cn,colors)):
    xx=360+i*340;d.rectangle((xx,65,xx+60,107),fill=color);d.text((xx+80,53),label,font=font(46),fill='black')
coordinates=[]
for gi,g in enumerate(names):
    y=255+gi*225;center(d,(155,y+24),names[g],48);current=Fraction(0)
    for dim,color in zip(dims,colors):
        share=Fraction(a['primary'][method][g]['dimensions'][dim]['attention_share']['exact_fraction'])
        xx=left+float(current)*w;end=left+float(current+share)*w
        d.rectangle((round(xx),y,round(end),y+105),fill=color,outline='white',width=2)
        if share>=Fraction(3,100):center(d,((xx+end)/2,y+29),f'{float(share)*100:.1f}',40,'black' if dim=='Ec' else 'white')
        coordinates.append({'group':g,'dimension':dim,'share':float(share),'exact_fraction':str(share),'x_start':xx,'x_end':end,'y':y})
        current+=share
    assert current==1
d.line((left,bottom,right,bottom),fill='black',width=3);center(d,((left+right)/2,980),'注意力占比（%）',47)
im.save(OUT/'图2-三部门五维注意力占比.png',dpi=(300,300))
(OUT/'图表数据与来源.json').write_text(json.dumps({'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':method,'figure2_data':coordinates,'small_segment_note':'药监经济性0.31%列于表3，避免在极窄色块中挤压数字。'},ensure_ascii=False,indent=2))
print('Created analytical framework and 15 exact shares in three 100% rows.')
