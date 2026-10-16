from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'attention_share_bounds.json').read_text())
idx={(r['coder'],r['group'],r['dimension']):r for r in data['rows']}
dims=('S','E','Ec','I','F')
labels=('安全性','有效性','经济性','创新性','公平性')
colors=('#2E5266','#408A8C','#D9B44A','#81759B','#B46D63')
names={'NMPA':'药监','NHSA':'医保','NHC':'卫生健康','GOV':'综合政策'}
font_path='/System/Library/Fonts/Supplemental/Songti.ttc'
font=lambda n:ImageFont.truetype(font_path,n)
im=Image.new('RGB',(2200,1450),'white');draw=ImageDraw.Draw(im)
left,right=390,2110;top,bottom=225,1270;width=right-left
for x in range(0,101,20):
    xx=left+width*x/100
    draw.line((xx,top-15,xx,bottom+10),fill='#DADADA',width=2)
    t=str(x);box=draw.textbbox((0,0),t,font=font(42))
    draw.text((xx-(box[2]-box[0])/2,bottom+28),t,fill='black',font=font(42))
for n,(label,color) in enumerate(zip(labels,colors)):
    x=420+n*340
    draw.rectangle((x,75,x+62,117),fill=color)
    draw.text((x+82,64),label,fill='black',font=font(45))
coordinates=[]
for g,group in enumerate(('NMPA','NHSA','NHC','GOV')):
    for c,coder in enumerate(('A','C')):
        y=250+g*260+c*95
        name=f'{names[group]}  {coder}'
        box=draw.textbbox((0,0),name,font=font(43))
        draw.text((left-40-(box[2]-box[0]),y+13),name,fill='black',font=font(43))
        current=0
        for dim,color in zip(dims,colors):
            share=idx[coder,group,dim]['attention_share']
            a,b=left+current*width,left+(current+share)*width
            draw.rectangle((round(a),y,round(b),y+72),fill=color,outline='white',width=2)
            if share>=0.05:
                text=f'{100*share:.1f}'
                box=draw.textbbox((0,0),text,font=font(36))
                text_color='black' if dim=='Ec' else 'white'
                draw.text(((a+b-(box[2]-box[0]))/2,y+15),text,fill=text_color,font=font(36))
            coordinates.append({'group':group,'coder':coder,'dimension':dim,'share':share,
                                'left_pixel':a,'right_pixel':b,'y_pixel':y})
            current+=share
        assert abs(current-1)<1e-12
draw.line((left,bottom+10,right,bottom+10),fill='black',width=3)
axis='注意力占比（%）';box=draw.textbbox((0,0),axis,font=font(47))
draw.text(((left+right-(box[2]-box[0]))/2,1368),axis,fill='black',font=font(47))
im.save(ROOT/'图2-五维注意力占比分布.png',dpi=(300,300))
(ROOT/'图2-数据与坐标.json').write_text(json.dumps({'source':'attention_share_bounds.json','data':coordinates},ensure_ascii=False,indent=2)+'\n')
print('Plotted 40 exact weighted shares in eight 100% stacked rows.')
