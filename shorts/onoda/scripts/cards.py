from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random, math, sys
W, H = 1080, 1920
OUT = sys.argv[1]
FB = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"
FM = "/usr/share/fonts/truetype/nanum/NanumMyeongjoBold.ttf"
RED, WHITE, GREY, BG1, BG2 = (255,59,59), (245,245,245), (150,160,185), (13,17,26), (30,36,52)
def f(sz, p=FB): return ImageFont.truetype(p, sz)

def base(seed=0):
    random.seed(seed)
    im = Image.new("RGB", (W, H), BG1); d = ImageDraw.Draw(im)
    for y in range(H):
        t = y / H; c = tuple(int(BG1[i] + (BG2[i]-BG1[i]) * math.sin(t*math.pi)) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    # grain
    g = Image.effect_noise((W, H), 18).convert("RGB")
    im = Image.blend(im, g, 0.05)
    # vignette
    v = Image.new("L", (W, H), 0); vd = ImageDraw.Draw(v)
    vd.ellipse([-300, -200, W+300, H+200], fill=255); v = v.filter(ImageFilter.GaussianBlur(220))
    im = Image.composite(im, Image.new("RGB", (W, H), (0,0,0)), v)
    return im

def ctext(d, y, s, font, fill=WHITE, stroke=0, sf=(0,0,0)):
    w = d.textlength(s, font=font); d.text(((W-w)/2, y), s, font=font, fill=fill, stroke_width=stroke, stroke_fill=sf)

def tag(d, s):  # small "재구성" label so diagrams are not mistaken for archival records
    ft = f(30); w = d.textlength(s, font=ft)
    d.rounded_rectangle([W-w-80, 1290, W-40, 1344], 10, outline=GREY, width=2); d.text((W-w-60, 1298), s, font=ft, fill=GREY)

def save(im, name): im.save(f"{OUT}/{name}.png"); print(name)


TOP = 400  # everything below the fixed title band (0-380)

# S02: Lubang real photo + inset map (built only if the photo is present)
import os
if os.path.exists("photos/X_lubang_2013.jpg") and os.path.getsize("photos/X_lubang_2013.jpg") > 50000:
    ph = Image.open("photos/X_lubang_2013.jpg").convert("RGB")
    bg = ph.copy(); sc = max(W/bg.width, H/bg.height); bg = bg.resize((int(bg.width*sc)+2, int(bg.height*sc)+2))
    bg = bg.crop(((bg.width-W)//2, 0, (bg.width-W)//2+W, H)).filter(ImageFilter.GaussianBlur(40))
    im = Image.blend(bg, Image.new("RGB", (W, H), (0,0,0)), 0.45)
    sc = 1080/ph.width; fg = ph.resize((1080, int(ph.height*sc)), Image.LANCZOS)
    im.paste(fg, (0, 860 - fg.height//2))
    mp = Image.open(f"{OUT}/map_lubang.png").resize((400, 407)).crop((40, 60, 400, 380))
    mk = Image.new("L", mp.size, 0); ImageDraw.Draw(mk).rounded_rectangle([0,0,mp.width-1,mp.height-1], 24, fill=255)
    d = ImageDraw.Draw(im); x0, y0 = W-mp.width-40, 860 + fg.height//2 - mp.height + 120
    d.rounded_rectangle([x0-6, y0-6, x0+mp.width+5, y0+mp.height+5], 28, fill=(255,255,255))
    im.paste(mp, (x0, y0), mk)
    save(im, "S02_lubang")
else:
    im = base(2); im.paste(Image.open(f"{OUT}/map_lubang.png"), (0, TOP)); save(im, "S02_lubang")

def paper(seed, lines, stamp=None):
    im = base(seed); d = ImageDraw.Draw(im)
    px0, py0, px1, py1 = 190, TOP+40, 890, 1260
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rectangle([px0+20, py0+30, px1+20, py1+30], fill=160)
    im.paste((0,0,0), (0,0), sh.filter(ImageFilter.GaussianBlur(25)))
    d.rectangle([px0, py0, px1, py1], fill=(226,214,186))
    for _ in range(4000):
        d.point((random.randint(px0, px1), random.randint(py0, py1)), fill=(205,192,160))
    ctext(d, py0+60, "명  령", f(100, FM), (60,40,30))
    d.line([px0+80, py0+200, px1-80, py0+200], fill=(90,70,50), width=3)
    y = py0+250
    for ln in lines:
        if ln is None:
            d.rectangle([px0+90, y+10, px1-90-random.randint(0,180), y+40], fill=(70,60,50)); y += 75
        else:
            ctext(d, y, ln, f(80, FM), (40,30,25)); y += 150
    if stamp:
        st = Image.new("RGBA", (380, 380), (0,0,0,0)); sd = ImageDraw.Draw(st)
        sd.ellipse([10,10,370,370], outline=(200,30,30,230), width=16)
        fs = f(96, FM); w = sd.textlength(stamp, font=fs); sd.text(((380-w)/2, 130), stamp, font=fs, fill=(200,30,30,230))
        st = st.rotate(-14, expand=True); im.paste(st, (560, 880), st)
    return im, d

im, d = paper(4, [None]*8, stamp="극비"); tag(d, "재구성"); save(im, "S04_order")
im, d = paper(5, ["항복 금지", "자결 금지"])
for yy in (TOP+290-20, TOP+290+150-20): d.rounded_rectangle([250, yy-15, 830, yy+115], 12, outline=RED, width=8)
tag(d, "재구성"); save(im, "S05_order_detail")

def jungle(im, seed):
    random.seed(seed); d = ImageDraw.Draw(im)
    for col, base_y, n in [((22,46,34), 1150, 22), ((14,32,24), 1250, 26), ((8,20,15), 1350, 30)]:
        for i in range(n):
            x = random.randint(-80, W+80); r = random.randint(90, 170); y = base_y + random.randint(-60, 60)
            d.ellipse([x-r, y-r, x+r, y+r], fill=col)
        d.rectangle([0, base_y, W, H], fill=col)

def leaflet(text, rot, scale=1.0):
    lw, lh = int(420*scale), int(300*scale)
    L = Image.new("RGBA", (lw, lh), (236,230,210,255)); ld = ImageDraw.Draw(L)
    ld.rectangle([8,8,lw-9,lh-9], outline=(80,70,60,255), width=4)
    fs = f(int(58*scale), FM); w = ld.textlength(text, font=fs); ld.text(((lw-w)/2, lh*0.36), text, font=fs, fill=(30,25,20,255))
    for k in range(3): ld.rectangle([lw*0.18, lh*0.68+k*18*scale, lw*0.82 - k*40*scale, lh*0.68+k*18*scale+7*scale], fill=(120,110,95,255))
    return L.rotate(rot, expand=True, resample=Image.BICUBIC)

im = base(7).convert("RGBA"); jungle(im, 7)
for (x, y, r, s_) in [(80,420,18,0.6),(640,400,-22,0.55),(360,620,8,0.95),(110,900,-30,0.5),(700,860,25,0.6),(320,1080,-12,0.45)]:
    L = leaflet("전쟁은 끝났다", r, s_); im.alpha_composite(L, (x, y))
d = ImageDraw.Draw(im); tag(d, "재구성"); save(im.convert("RGB"), "S07_leaflets")

im = base(8).convert("RGBA"); L = leaflet("전쟁은 끝났다", -6, 1.6); im.alpha_composite(L, ((W-L.width)//2, 560))
d = ImageDraw.Draw(im)
d.line([230, 520, 850, 1160], fill=RED, width=36); d.line([850, 520, 230, 1160], fill=RED, width=36)
tag(d, "재구성"); save(im.convert("RGB"), "S08_trap")

im = base(10); d = ImageDraw.Draw(im)
ctext(d, 560, "섬 주민", f(100), GREY)
ctext(d, 700, "약 30명", f(240), RED, 4)
save(im, "S10_victims")

im = base(11); d = ImageDraw.Draw(im)
d.chord([290, 520, 790, 1020], 180, 360, fill=(70,90,60)); d.rectangle([250, 765, 830, 815], fill=(70,90,60))
ctext(d, 860, "군대", f(110), GREY)
d.line([230, 480, 850, 1080], fill=RED, width=44); d.line([850, 480, 230, 1080], fill=RED, width=44)
save(im, "S11_not_army")

# S12: Suzuki's famous "search list"
im = base(12); d = ImageDraw.Draw(im)
d.rounded_rectangle([170, TOP+60, 910, 1240], 24, fill=(240,236,222))
for yy in range(TOP+230, 1240, 110): d.line([210, yy, 870, yy], fill=(190,200,225), width=3)
d.line([270, TOP+60, 270, 1240], fill=(230,150,150), width=4)
d.text((300, TOP+110), "찾을 것", font=f(84), fill=(40,40,50))
for i, item in enumerate(["오노다 소위", "판다", "설인"]):
    y = TOP+300 + i*200
    d.rectangle([300, y, 370, y+70], outline=(40,40,50), width=6)
    d.text((410, y-6), item, font=f(80), fill=(40,40,50))
d.line([310, TOP+335, 335, TOP+365], fill=RED, width=14); d.line([335, TOP+365, 390, TOP+280], fill=RED, width=14)
tag(d, "재구성"); save(im, "S12_suzuki_list")

im = base(13); d = ImageDraw.Draw(im)
d.text((140, TOP+20), "“", font=f(300, FM), fill=RED)
for i, ln in enumerate(["상관의 명령", "없이는", "나갈 수 없다"]):
    ctext(d, 650 + i*170, ln, f(120), WHITE)
save(im, "S13_quote")

im = base(14); mp = Image.open(f"{OUT}/map_route.png"); im.paste(mp, (0, TOP))
save(im, "S14_route")

im = base(15); d = ImageDraw.Draw(im)
cols = [(120,70,60),(60,90,120),(140,120,70),(70,110,80),(110,70,110),(150,90,60),(90,100,130),(130,80,70)]
for i in range(8):
    d.rectangle([230 + (i%2)*30, 1150-(i+1)*85, 850 - (i%3)*50, 1150-i*85-8], fill=cols[i])
tag(d, "일러스트"); save(im, "S15_books")

im = base(16); d = ImageDraw.Draw(im)
d.rounded_rectangle([220, 480, 860, 1220], 30, fill=(240,240,240)); d.rounded_rectangle([220, 480, 860, 660], 30, fill=RED)
d.rectangle([220, 610, 860, 660], fill=RED)
ctext(d, 520, "1974년 3월", f(88), WHITE)
ctext(d, 700, "9", f(400), (25,25,30))
save(im, "S16_date")

im = base(18); d = ImageDraw.Draw(im)
d.rounded_rectangle([140, 640, 940, 700], 30, fill=RED)
d.text((140, 730), "1945", font=f(64), fill=GREY); d.text((800, 730), "1974", font=f(64), fill=GREY)
ctext(d, 880, "29년", f(280), RED, 6)
save(im, "S18_loop")
