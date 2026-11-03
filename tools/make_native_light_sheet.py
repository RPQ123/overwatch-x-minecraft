"""Private QA contact sheet of actual captured native foregrounds; no game input."""
import argparse,re
from pathlib import Path
from PIL import Image,ImageDraw
from observe_overwatch import ROOT

def main(folder):
    folder=folder.resolve()
    if ROOT/'research' not in folder.parents:raise ValueError('Private evidence folder required')
    entries=[]
    for path in folder.glob('baseline-*-pitch*.png'):
        m=re.fullmatch(r'baseline-(-?[\d.]+)-pitch(-?[\d.]+)\.png',path.name)
        if m:entries.append((float(m[2]),float(m[1]),path))
    entries.sort(key=lambda v:(v[0],v[1]));cols=8;w,h=360,245
    sheet=Image.new('RGB',(w*cols,h*((len(entries)+cols-1)//cols)),(26,26,26));draw=ImageDraw.Draw(sheet)
    for i,(pitch,yaw,path) in enumerate(entries):
        with Image.open(path) as im:
            # Fixed screen crop retains weapon/hands; HUD corners and much of
            # the changing MC background are excluded. This is not a hand mask.
            box=(int(im.width*.20),int(im.height*.43),int(im.width*.86),int(im.height*.96))
            crop=im.crop(box);crop.thumbnail((w,h-25));x=(i%cols)*w;y=(i//cols)*h;sheet.paste(crop,(x,y+25))
            draw.text((x+8,y+5),f'yaw {yaw:g} / pitch {pitch:g}',fill='white')
    out=folder/'foreground-sheet.jpg';sheet.save(out,quality=93);print(out)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);args=p.parse_args();main(args.folder)
