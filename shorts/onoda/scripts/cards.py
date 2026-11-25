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
    d.rounded_rectangle([W-w-80, 230, W-40, 284], 10, outline=GREY, width=2); d.text((W-w-60, 238), s, font=ft, fill=GREY)

def save(im, name): im.save(f"{OUT}/{name}.png"); print(name)

# S01 fallback: 29 years
im = base(1); d = ImageDraw.Draw(im)
ctext(d, 420, "전쟁이 끝난 뒤", f(64), GREY)
ctext(d, 520, "29년", f(330), RED, 6)
ctext(d, 920, "1945  →  1974", f(78), WHITE)
save(im, "S01_fallback")

# S02 map
im = base(2); d = ImageDraw.Draw(im)
mp = Image.open(f"{OUT}/map_lubang.png"); im.paste(mp, (0, 330))
ctext(d, 200, "1974 · 필리핀 루방섬", f(62), WHITE)
save(im, "S02_map_lubang")

# S03 fallback: name card
im = base(3); d = ImageDraw.Draw(im)
d.ellipse([390, 330, 690, 630], fill=(55,62,82)); d.rounded_rectangle([300, 640, 780, 1000], 140, fill=(55,62,82))
ctext(d, 1060, "오노다 히로", f(110), WHITE)
ctext(d, 1200, "일본 육군 소위 · 정보장교", f(52), GREY)
save(im, "S03_fallback")

def paper(seed, lines, stamp=None, big=None):
    im = base(seed); d = ImageDraw.Draw(im)
    px0, py0, px1, py1 = 170, 260, 910, 1330
    sh = Image.new("L", (W, H), 0); ImageDraw.Draw(sh).rectangle([px0+20, py0+30, px1+20, py1+30], fill=160)
    im.paste((0,0,0), (0,0), sh.filter(ImageFilter.GaussianBlur(25)))
    d.rectangle([px0, py0, px1, py1], fill=(226,214,186))
    for _ in range(4000):
        x, y = random.randint(px0, px1), random.randint(py0, py1); d.point((x, y), fill=(205,192,160))
    ctext(d, py0+70, "명  령", f(110, FM), (60,40,30))
    d.line([px0+80, py0+230, px1-80, py0+230], fill=(90,70,50), width=3)
    y = py0+290
    for ln in lines:
        if ln is None:
            d.rectangle([px0+90, y+10, px1-90-random.randint(0,180), y+40], fill=(70,60,50)); y += 75
        else:
            ctext(d, y, ln, f(72, FM), (40,30,25)); y += 130
    if stamp:
        st = Image.new("RGBA", (420, 420), (0,0,0,0)); sd = ImageDraw.Draw(st)
        sd.ellipse([10,10,410,410], outline=(200,30,30,230), width=16)
        fs = f(96, FM); w = sd.textlength(stamp, font=fs); sd.text(((420-w)/2, 150), stamp, font=fs, fill=(200,30,30,230))
        st = st.rotate(-14, expand=True); im.paste(st, (560, 900), st)
    return im, d

im, d = paper(4, [None, None, None, "단 하나", None, None, None], stamp="극비")
d.text((200, 1350), "", font=f(10)); tag(d, "재구성")
save(im, "S04_order")
im, d = paper(5, ["항복 금지", "", "자결 금지"])
for yy in (545, 805):
    d.rounded_rectangle([230, yy-25, 850, yy+120], 12, outline=RED, width=8)
tag(d, "재구성"); save(im, "S05_order_detail")

# S06 fallback
im = base(6); d = ImageDraw.Draw(im)
ctext(d, 520, "1945", f(220), WHITE); ctext(d, 820, "일본 항복", f(140), RED); ctext(d, 1020, "제2차 세계대전 종전", f(56), GREY)
save(im, "S06_fallback")

def jungle(im, seed):
    random.seed(seed); d = ImageDraw.Draw(im)
    for layer, (col, base_y, n) in enumerate([((22,46,34), 1450, 22), ((14,32,24), 1560, 26), ((8,20,15), 1680, 30)]):
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

# S07 leaflets falling over jungle
im = base(7).convert("RGBA"); jungle(im, 7)
random.seed(77)
for i, (x, y, r, s) in enumerate([(80,300,18,0.6),(640,250,-22,0.55),(380,560,8,0.9),(120,900,-30,0.5),(700,820,25,0.6),(300,1150,-12,0.45)]):
    L = leaflet("전쟁은 끝났다", r, s); im.alpha_composite(L, (x, y))
d = ImageDraw.Draw(im); tag(d, "재구성"); save(im.convert("RGB"), "S07_leaflets")

# S08 trap
im = base(8).convert("RGBA"); L = leaflet("전쟁은 끝났다", -6, 1.5); im.alpha_composite(L, ((W-L.width)//2, 420))
d = ImageDraw.Draw(im)
d.line([250, 400, 830, 1000], fill=RED, width=34); d.line([830, 400, 250, 1000], fill=RED, width=34)
ctext(d, 1110, "“적의 속임수다”", f(100), WHITE, 4)
tag(d, "재구성"); save(im.convert("RGB"), "S08_trap")

# S09 comrades
im = base(9); d = ImageDraw.Draw(im)
ctext(d, 230, "함께 숨은 4명", f(70), WHITE)
rows = [("오노다", "", WHITE), ("아카쓰", "1950 투항", GREY), ("시마다", "1954 사망", RED), ("고즈카", "1972 사망", RED)]
for i, (n, ev, col) in enumerate(rows):
    y = 420 + i*230
    cx = 260
    d.ellipse([cx-70, y, cx+70, y+140], fill=(70,78,100) if i == 0 else (45,50,66))
    d.text((cx+120, y+30), n, font=f(72), fill=WHITE if i == 0 else (150,155,170))
    if ev: d.text((cx+430, y+42), ev, font=f(56), fill=col)
    if i > 0: d.line([cx-80, y+70, cx+80, y+70], fill=RED, width=10)
ctext(d, 1350, "결국 혼자 남았다", f(76), RED)
save(im, "S09_comrades")

# S10 victims
im = base(10); d = ImageDraw.Draw(im)
ctext(d, 420, "29년 동안", f(70), GREY)
ctext(d, 560, "섬 주민", f(110), WHITE)
ctext(d, 730, "약 30명", f(220), RED, 4)
ctext(d, 1010, "목숨을 잃었다", f(96), WHITE)
save(im, "S10_victims")

# S11 not the army
im = base(11); d = ImageDraw.Draw(im)
ctext(d, 300, "그를 찾아낸 건", f(84), WHITE)
d.chord([290, 560, 790, 1060], 180, 360, fill=(70,90,60)); d.rectangle([250, 805, 830, 850], fill=(70,90,60))
ctext(d, 900, "군대", f(110), GREY)
d.line([230, 520, 850, 1100], fill=RED, width=40); d.line([850, 520, 230, 1100], fill=RED, width=40)
ctext(d, 1200, "아니었다", f(120), RED, 4)
save(im, "S11_not_army")

# S12 Suzuki
im = base(12); d = ImageDraw.Draw(im)
d.ellipse([440, 330, 640, 530], fill=(70,78,100)); d.rounded_rectangle([360, 540, 720, 900], 100, fill=(70,78,100))
d.rounded_rectangle([660, 560, 800, 860], 30, fill=(150,95,60))
ctext(d, 960, "스즈키 노리오", f(100), WHITE)
ctext(d, 1090, "24세 · 일본인 탐험가", f(56), GREY)
ctext(d, 1200, "“오노다 소위, 판다, 설인", f(46), (200,205,220))
ctext(d, 1265, "순서로 찾겠다”", f(46), (200,205,220))
tag(d, "본인 아님 · 일러스트"); save(im, "S12_suzuki")

# S13 quote
im = base(13); d = ImageDraw.Draw(im)
d.text((140, 330), "“", font=f(300, FM), fill=RED)
for i, ln in enumerate(["상관의 명령", "없이는", "나갈 수 없다"]):
    ctext(d, 620 + i*170, ln, f(120), WHITE)
ctext(d, 1180, "— 오노다 히로, 1974.2", f(52), GREY)
save(im, "S13_quote")

# S14 route
im = base(14); d = ImageDraw.Draw(im)
mp = Image.open(f"{OUT}/map_route.png"); im.paste(mp, (0, 330))
ctext(d, 200, "옛 상관을 찾아서", f(66), WHITE)
save(im, "S14_route")

# S15 Taniguchi
im = base(15); d = ImageDraw.Draw(im)
cols = [(120,70,60),(60,90,120),(140,120,70),(70,110,80),(110,70,110),(150,90,60)]
for i in range(6):
    d.rectangle([250, 860-(i+1)*70, 830 - (i%3)*40, 860-i*70-6], fill=cols[i])
ctext(d, 940, "다니구치 요시미", f(100), WHITE)
ctext(d, 1075, "전 육군 소령 → 서점 주인", f(60), RED)
tag(d, "일러스트"); save(im, "S15_taniguchi")

# S16 date
im = base(16); d = ImageDraw.Draw(im)
d.rounded_rectangle([240, 300, 840, 1000], 30, fill=(240,240,240)); d.rounded_rectangle([240, 300, 840, 470], 30, fill=RED)
d.rectangle([240, 420, 840, 470], fill=RED)
ctext(d, 330, "1974년 3월", f(84), WHITE)
ctext(d, 520, "9", f(380), (25,25,30))
ctext(d, 1080, "임무 해제 명령", f(100), WHITE)
ctext(d, 1220, "루방섬 정글에서 직접 낭독", f(52), GREY)
save(im, "S16_date")

# S17 fallback
im = base(17); d = ImageDraw.Draw(im)
d.line([220, 760, 860, 600], fill=(110,80,55), width=40); d.line([520, 680, 860, 600], fill=(60,60,66), width=24)
ctext(d, 940, "29년 만에", f(90), GREY); ctext(d, 1070, "무기를 내려놓다", f(110), WHITE)
save(im, "S17_fallback")

# S18 loop counter
im = base(18); d = ImageDraw.Draw(im)
ctext(d, 380, "명령 한 줄을 기다린", f(72), WHITE)
d.rounded_rectangle([140, 640, 940, 700], 30, fill=(45,50,66)); d.rounded_rectangle([140, 640, 940, 700], 30, fill=RED)
d.text((140, 730), "1945", font=f(64), fill=GREY); d.text((800, 730), "1974", font=f(64), fill=GREY)
ctext(d, 900, "29년", f(260), RED, 6)
save(im, "S18_loop")
