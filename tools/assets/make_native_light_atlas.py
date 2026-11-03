"""Assemble unretouched real captures; no brightness/color edits or invented pixels."""

# Preserve stable tools imports when this script is invoked by its new path.
import sys as _tidy_sys
from pathlib import Path as _TidyPath
_tidy_tools = _TidyPath(__file__).resolve().parents[1]
if str(_tidy_tools) not in _tidy_sys.path:
    _tidy_sys.path.insert(0, str(_tidy_tools))

import argparse,json,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from calibrate_hero_roster import ROOT,ROSTER

LABELS=['源氏','麦克雷（卡西迪）','法老之鹰','死神','士兵：76','猎空','堡垒','半藏','狂鼠','美','托比昂','黑百合','D.Va','莱因哈特','路霸','温斯顿','查莉娅','卢西奥','天使','秩序之光','禅雅塔']
FONT='C:/Windows/Fonts/msyh.ttc'
def font(n):return ImageFont.truetype(FONT,n)

def render(folder,heroes,cols,width,path,title):
    gap=20;pair=width*2+10;image_h=round(width*9/16);card_h=image_h+76
    rows=math.ceil(len(heroes)/cols);out=Image.new('RGB',(cols*pair+(cols+1)*gap,150+rows*card_h+gap),(22,25,31));d=ImageDraw.Draw(out)
    d.text((gap,16),title,font=font(36),fill='#f2f5fa')
    d.text((gap,72),'每组左：花村登录场景  ｜  右：好莱坞  ·  真实游戏截图，未调色',font=font(22),fill='#c0cad6')
    d.text((gap,108),'离线 Beta 全部 21 位英雄 · 固定朝向 0° / 俯仰 0° · 原生武器光照对比（非完整技能验收）',font=font(18),fill='#a4aebb')
    for index,(name,_,_) in enumerate(heroes):
        col=index//rows;row=index%rows;x=gap+col*(pair+gap);y=150+row*card_h
        label=LABELS[next(i for i,r in enumerate(ROSTER) if r[0]==name)]
        d.text((x,y),label+'  '+name,font=font(22),fill='#ffffff')
        for scene,dx,caption in [('kyoto',0,'花村'),('hollywood',width+10,'好莱坞')]:
            with Image.open(folder/scene/(name+'.png')) as im:
                if im.size!=(2560,1440):raise ValueError('Unexpected native window size '+str(im.size))
                out.paste(im.convert('RGB').resize((width,image_h),Image.Resampling.LANCZOS),(x+dx,y+33))
            d.rectangle((x+dx+7,y+40,x+dx+100,y+68),fill=(22,25,31))
            d.text((x+dx+14,y+41),caption,font=font(18),fill='#ffffff')
    out.save(path)

def main(folder):
    manifests=[json.loads((folder/s/'manifest.json').read_text()) for s in ['kyoto','hollywood']]
    for m in manifests:
        if not m['passed'] or [v['name'] for v in m['rows']]!=[v[0] for v in ROSTER]:raise ValueError('Need successful actual captures of every beta hero')
    for key in ('x','z','feetY'):
        if abs(manifests[0]['origin'][key]-manifests[1]['origin'][key])>.1:raise ValueError('A/B position differs')
    if manifests[0]['dimension']!=manifests[1]['dimension']:raise ValueError('A/B dimension differs')
    render(folder,ROSTER,3,440,folder/'all-21-heroes.jpg','守望先锋 × Minecraft · 全英雄光照对比')
    for page in range(3):render(folder,ROSTER[page*7:(page+1)*7],1,800,folder/f'detail-{page+1}.png',f'全英雄光照对比 · 细节 {page+1}/3')
    print(json.dumps({'overview':str(folder/'all-21-heroes.jpg'),'actualCaptures':42,'allHeroes':21,'colors':'unmodified'},ensure_ascii=False))

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--folder',type=Path,required=True);v=a.parse_args();main(v.folder.resolve())
