"""Original SVG question schematics derived from explicit problem models. No publisher images."""
from pathlib import Path
from html import escape as E
from math import sqrt
import hashlib
FONT='Arial, sans-serif'
def create(row,out):
    m=row['independent_model'];k=m['kind'];parts=[]
    def text(x,y,s,size=16,color='#14213d'):parts.append(f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" fill="{color}">{E(str(s))}</text>')
    def line(a,b,color='#14213d',width=3,dash=''):
        parts.append(f'<line x1="{a[0]}" y1="{a[1]}" x2="{b[0]}" y2="{b[1]}" stroke="{color}" stroke-width="{width}"'+(f' stroke-dasharray="{dash}"' if dash else '')+'/>')
    def poly(v,fill='none',color='#14213d'):
        parts.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in v)+f'" fill="{fill}" stroke="{color}" stroke-width="2"/>')
    def grid(cs,ox,oy,label,fixed=None):
        fixed=set(map(tuple,fixed or []));cs=set(map(tuple,cs))
        text(ox,oy-16,label)
        for yy in range(3):
            for xx in range(3):
                fill='#b8d8ff' if (xx,yy) in fixed else '#ffd59c' if (xx,yy) in cs else '#ffffff'
                x,y=ox+xx*36,oy+(2-yy)*36
                parts.append(f'<rect x="{x}" y="{y}" width="36" height="36" fill="{fill}" stroke="#5c677d"/>')
                text(x+11,y+24,chr(65+(2-yy)*3+xx),15)
    text(25,28,'MathVisionKid — mô hình gốc của đề, không phải ảnh SGK',16)
    text(25,53,row['topic'],14)
    if k=='boundary':
        grid([],35,115,'P cố định',m['fixed'])
        for i,(name,c) in enumerate(m['options'].items()):grid(c,210+i*165,115,'Miếng '+name)
        text(35,260,'Xanh: phần cố định. Cam: miếng thử ở hướng ban đầu.',14)
        text(35,285,'Chỉ dùng các phép biến đổi được nêu trong đề.',14)
    elif k in ('squares','triangle_remove','rhombus_move','quads'):
        points=m['points'];edges=m['edges']
        def xy(v):
            x,y=v
            if k in ('quads','triangle_remove','rhombus_move'):x,y=x+y/2,y*sqrt(3)/2
            return x,y
        xs=[xy(v)[0] for v in points.values()];ys=[xy(v)[1] for v in points.values()]
        scale=min(70,540/max(max(xs)-min(xs),1),255/max(max(ys)-min(ys),1))
        p={n:(70+(xy(v)[0]-min(xs))*scale,360-(xy(v)[1]-min(ys))*scale) for n,v in points.items()}
        for edge in edges:line(p[edge[0]],p[edge[1]])
        if k=='rhombus_move':
            for edge in m['new_slots']:line(p[edge[0]],p[edge[1]],'#aeb8c4',2,'5 5')
        if k=='triangle_remove':
            for edge in m['remove']:line(p[edge[0]],p[edge[1]],'#c33f3f',4)
        for n,(x,y) in p.items():text(x+5,y-8,n,15)
        text(35,410,'Chỉ những đoạn liệt kê trong đề mới được dùng.',14)
    elif k=='pair_assembly':
        # Source inventory and separate target, no solution placement.
        xoff=35
        for name,p in m['pieces'].items():
            minx=min(a[0] for a in p);miny=min(a[1] for a in p)
            q=[(xoff+(x-minx)*35,215-(y-miny)*35) for x,y in p]
            poly(q,'#e6f0ff');text(xoff,245,'Miếng '+name,15);xoff+=180
        w,h=m['target_size'];poly([(40,300),(40+35*w,300),(40+35*w,300+35*h),(40,300+35*h)])
        text(40+35*w+15,330,f'Bảng đích {w} × {h}',15)
        text(35,430,'Các miếng và bảng đích cùng tỉ lệ; không tự cắt hoặc đổi luật xoay.',14)
    elif k=='partition':
        target=m['target'];maxx=max(x for t in target for x,y in t);maxy=max(y for t in target for x,y in t)
        scale=min(42,160/max(maxx,1),190/max(maxy,1))
        if 'house' in row['topic']:
            outer=[[0,0],[2,0],[2,2],[1,3],[0,2]]
            poly([(35+x*scale,300-y*scale) for x,y in outer])
        else:
            for t in target:poly([(35+x*scale,300-y*scale) for x,y in t])
        text(35,335,'Bóng/bảng đích',15)
        # Display normalized individual pieces separately, without their target locations.
        names=['P','Q','R'] if 'house' in row['topic'] else ['A','B','C','D'] if 'four_triangles' in row['topic'] else ['L1','L2','M','S','T1','T2','P'] if 'tangram' in row['topic'] else [str(i+1) for i in range(len(m['pieces']))]
        for i,p in enumerate(m['pieces']):
            col=i%4;r=i//4;ox=270+col*105;oy=185+r*145
            minx=min(x for x,y in p);miny=min(y for x,y in p)
            size=max(max(x for x,y in p)-minx,max(y for x,y in p)-miny,1)
            s=min(30,75/size)
            poly([(ox+(x-minx)*s,oy-(y-miny)*s) for x,y in p],['#d8e9ff','#ffe5b7','#d7efdb','#eddbff'][i%4])
            text(ox,oy+25,'Miếng '+names[i],13)
        text(35,420,'Kho miếng tách rời không cùng tỉ lệ; kích thước chính xác theo đề.',14)
        text(35,443,'Đường cắt/vị trí cần kiểm chỉ lấy từ mô tả, không tự suy nét mới.',14)
    elif k=='unit_cells':
        if row['topic']=='irregular_staircase_full_unit_cells':
            for y in range(3):
                for x in range(3):
                    fill='#84b8ef' if x<3-y else '#ffffff'
                    parts.append(f'<rect x="{60+x*58}" y="{280-y*58}" width="58" height="58" fill="{fill}" stroke="#28344b" stroke-width="2"/>')
            text(60,380,'Chỉ ô màu thuộc vùng được hỏi.',15)
        else:
            for i,label in enumerate('ABCDEF'):
                x=40+i*100;y=180
                if label in m['full']:poly([(x,y),(x+65,y),(x+65,y+65),(x,y+65)],'#84b8ef')
                else:
                    poly([(x,y),(x+65,y),(x+65,y+65),(x,y+65)])
                    if label in ('C','E'):poly([(x,y),(x+65,y+65),(x,y+65)],'#84b8ef')
                    else:poly([(x,y),(x+65,y),(x+65,y+65)],'#84b8ef')
                text(x+23,y+95,label)
            text(40,325,'Ô vuông bằng nhau; màu chỉ phủ phần được ghi trong đề.',15)
    elif k in ('seven_build','seven'):
        initial=m.get('initial','_');loc={'a':((0,0),(50,0)),'b':((50,0),(50,50)),'c':((50,50),(50,100)),'d':((0,100),(50,100)),'e':((0,50),(0,100)),'f':((0,0),(0,50)),'g':((0,50),(50,50))}
        codes=['abcdef','bc','abdeg','abcdg','bcfg','acdfg','acdefg','abc','abcdefg','abcdfg']
        for i,d in enumerate(initial):
            ox,oy=65+i*195,155;active=set() if d=='_' else set(codes[int(d)])
            for s,(a,b) in loc.items():
                line((ox+a[0],oy+a[1]),(ox+b[0],oy+b[1]),'#1e5794' if s in active else '#d5dbe2',5 if s in active else 2)
                text(ox+(a[0]+b[0])/2+7,oy+(a[1]+b[1])/2-6,s,13,'#3c4b61')
            text(ox,300,'Ô '+str(i+1),16)
        if m.get('equation'):text(165,215,'+',26);text(360,215,'=',26)
        text(35,360,'Que xanh: đang có. Nét xám: vị trí trống, không phải que.',15)
        text(35,388,'Các dấu in sẵn và số lượt chuyển theo đúng đề.',15)
    elif k=='faces':
        text(35,110,'Hướng',17);text(195,110,'Nhãn',17);text(385,110,'Chấm',17);text(485,110,'Nhìn thấy?',17)
        for i,f in enumerate(m['faces']):
            y=150+i*40;text(35,y,f['direction']);text(195,y,f['label']);text(385,y,f['dots']);text(485,y,'có' if f['visible'] else 'bị che')
        text(35,440,'Bảng là dữ kiện chữ của đề; không suy các mặt chưa được cho.',14)
    parts.append('</svg>')
    data=('<svg xmlns="http://www.w3.org/2000/svg" width="760" height="480" viewBox="0 0 760 480"><rect width="760" height="480" fill="white"/>'+''.join(parts)).encode()
    folder=out/'assets';folder.mkdir(exist_ok=True)
    name=row['topic']+'.svg';p=folder/name;p.write_bytes(data)
    return dict(path='assets/'+name,sha256=hashlib.sha256(data).hexdigest(),bytes=len(data),origin='ORIGINAL_PROGRAMMATIC_QUESTION_SCHEMATIC',publisher_image=False,role='Optional original question illustration; explicit problem text remains authoritative.',answer_or_oracle_annotation=False)

