"""Render basic original SVG primitives for local visual QA; not a browser renderer."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from xml.etree import ElementTree as ET
import json,hashlib
OUT=Path(__file__).resolve().parent
def main():
    folder=OUT/'visual_qa';folder.mkdir(exist_ok=True);images=[];records=[]
    for p in sorted((OUT/'assets').glob('*.svg')):
        im=Image.new('RGB',(760,480),'white');d=ImageDraw.Draw(im)
        for e in ET.parse(p).getroot():
            tag=e.tag.rsplit('}',1)[-1];a=e.attrib
            if tag=='rect':
                x=float(a.get('x',0));y=float(a.get('y',0));w=float(a['width']);h=float(a['height']);d.rectangle((x,y,x+w,y+h),fill=a.get('fill','white'),outline=a.get('stroke'))
            elif tag=='line':d.line((float(a['x1']),float(a['y1']),float(a['x2']),float(a['y2'])),fill=a['stroke'],width=int(a.get('stroke-width',1)))
            elif tag=='polygon':
                vs=[tuple(map(float,v.split(','))) for v in a['points'].split()];d.polygon(vs,fill=None if a.get('fill')=='none' else a.get('fill'),outline=a['stroke'],width=2)
            elif tag=='text':
                font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',int(a['font-size']));d.text((float(a['x']),float(a['y'])-int(a['font-size'])),e.text or '',font=font,fill=a['fill'])
        dest=folder/(p.stem+'.png');im.save(dest);images.append(im)
        records.append(dict(svg=str(p.relative_to(OUT)).replace('\\','/'),svg_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),png=str(dest.relative_to(OUT)).replace('\\','/'),png_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),renderer='Reference rendering of SVG basic shapes/text with Pillow; not a browser screenshot',xml_valid=True,size=[760,480]))
    for start in range(0,len(images),6):
        sheet=Image.new('RGB',(1520,1440),'#c0c0c0')
        for i,im in enumerate(images[start:start+6]):sheet.paste(im,((i%2)*760,(i//2)*480))
        sheet.save(folder/('sheet_'+str(start//6+1)+'.png'))
    (folder/'render_receipt.json').write_text(json.dumps(dict(assets=records,publisher_images_used=False,all_images_model_derived=True),ensure_ascii=False,indent=2),encoding='utf-8')
    print('Rendered',len(images),'original assets')
if __name__=='__main__':main()

