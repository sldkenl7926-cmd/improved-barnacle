"""Render 1080x1920 shorts. usage: render.py scenes.json out.mp4 [narration.wav]"""
import json, sys, subprocess, math, re, os, numpy as np, wave
from PIL import Image, ImageDraw, ImageFont, ImageFilter
W, H, FPS, SR = 1080, 1920, 30, 44100
FB = "/usr/share/fonts/truetype/nanum/NanumSquareB.ttf"
scenes = json.load(open(sys.argv[1])); OUT = sys.argv[2]; NAR = sys.argv[3] if len(sys.argv) > 3 else None
BUILD = "build"

def syl(s): return len(re.findall(r"[가-힣]", s))

def read_wav(p):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", p, "-ac", "1", "-ar", str(SR), f"{BUILD}/nar.wav"], check=True)
    with wave.open(f"{BUILD}/nar.wav") as w: return np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768

# ---- timing ----
if NAR:
    a = read_wav(NAR)
    log = subprocess.run(["ffmpeg", "-i", f"{BUILD}/nar.wav", "-af", "silencedetect=noise=-38dB:d=0.18", "-f", "null", "-"], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    gaps = [((s + e) / 2, e - s) for s, e in zip(starts, ends) if s > 0.3 and e < len(a) / SR - 0.1]
    # pick the N-1 longest pauses as scene boundaries, weighted toward expected positions
    total = len(a) / SR; n = len(scenes)
    w = np.array([syl(s["say"]) for s in scenes], float); exp = np.cumsum(w)[:-1] / w.sum() * total
    cuts = []
    for t in exp:
        cand = [g for g in gaps if g[0] not in cuts]
        best = min(cand, key=lambda g: abs(g[0] - t) - 1.5 * g[1])
        cuts.append(best[0])
    cuts = sorted(cuts); bounds = [0.0] + cuts + [total + 0.25]
    nar_audio = a
else:
    dur = [max(1.3, syl(s["say"]) / 6.3 + 0.2) for s in scenes]
    bounds = [0.0] + list(np.cumsum(dur)); nar_audio = None
total = bounds[-1]; print("total %.2fs" % total, ["%.2f" % (bounds[i+1]-bounds[i]) for i in range(len(scenes))])

# ---- visuals ----
def fg_bg(path, kind, crop=None):
    im = Image.open(path).convert("RGB")
    if crop and kind == "photo":
        x0, y0, x1, y1 = crop; im = im.crop((int(x0*im.width), int(y0*im.height), int(x1*im.width), int(y1*im.height)))
    if kind == "card": return im.resize((W, H)), None
    bg = im.copy(); s = max(W / bg.width, H / bg.height); bg = bg.resize((int(bg.width*s)+2, int(bg.height*s)+2))
    bg = bg.crop(((bg.width-W)//2, (bg.height-H)//2, (bg.width-W)//2+W, (bg.height-H)//2+H)).filter(ImageFilter.GaussianBlur(40))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)
    if kind == "fill":   # crop (fractions) and fill the whole picture zone: hook close-ups
        x0, y0, x1, y1 = crop
        im = im.crop((int(x0*im.width), int(y0*im.height), int(x1*im.width), int(y1*im.height)))
        tw, th = 1080, 950; s = max(tw / im.width, th / im.height)
        im = im.resize((int(im.width*s)+1, int(im.height*s)+1), Image.LANCZOS)
        fg = im.crop(((im.width-tw)//2, (im.height-th)//2, (im.width-tw)//2+tw, (im.height-th)//2+th)).filter(ImageFilter.UnsharpMask(2, 80, 2))
        return fg, bg
    s = min(1040 / im.width, 940 / im.height); fg = im.resize((int(im.width*s), int(im.height*s)), Image.LANCZOS)
    return fg, bg

FONT = ImageFont.truetype(FB, 84)
def subtitle_layer(text, hl):
    lay = Image.new("RGBA", (W, 360), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    words = text.split(" "); lines, cur = [], ""
    for wd in words:
        t = (cur + " " + wd).strip()
        if d.textlength(t, font=FONT) > 940 and cur: lines.append(cur); cur = wd
        else: cur = t
    lines.append(cur)
    y = 180 - len(lines) * 55
    for ln in lines:
        x = (W - d.textlength(ln, font=FONT)) / 2
        i = ln.find(hl) if hl else -1
        parts = [(ln, (255, 255, 255))] if i < 0 else [(ln[:i], (255,255,255)), (hl, (255, 214, 0)), (ln[i+len(hl):], (255,255,255))]
        for p, c in parts:
            d.text((x, y), p, font=FONT, fill=c, stroke_width=8, stroke_fill=(0, 0, 0)); x += d.textlength(p, font=FONT)
        y += 110
    return lay

TITLE = json.load(open("title.json")) if os.path.exists("title.json") else None
band = Image.new("RGBA", (W, H), (0, 0, 0, 0))
if TITLE:
    bd = ImageDraw.Draw(band); bd.rectangle([0, 0, W, 375], fill=(0, 0, 0, 235)); TF = ImageFont.truetype(FB, 96)
    for i, (ln, col) in enumerate(TITLE):
        bd.text(((W - bd.textlength(ln, font=TF)) / 2, 90 + i * 118), ln, font=TF, fill=tuple(col), stroke_width=3, stroke_fill=(0,0,0))
pre = []
for i, s in enumerate(scenes):
    fg, bg = fg_bg(s["img"], s["type"], s.get("crop")); pre.append((fg, bg, subtitle_layer(s["sub"], s.get("hl"))))

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
                       "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", f"{BUILD}/video.mp4"], stdin=subprocess.PIPE)
nframes = int(math.ceil(total * FPS))
for fi in range(nframes):
    t = fi / FPS; k = max(0, min(len(scenes)-1, int(np.searchsorted(bounds, t, side="right")) - 1))
    p = (t - bounds[k]) / (bounds[k+1] - bounds[k]); fg, bg, sub = pre[k]; s_kind = scenes[k]['type']
    z = 1.0 + 0.07 * p if k % 2 == 0 else 1.07 - 0.07 * p          # alternate zoom in / out
    dt = t - bounds[k]; z += 0.10 * max(0.0, 1 - dt / 0.18) ** 2    # punch-in on each cut
    if bg is None:
        cw, ch = W / z, H / z; dx = (W - cw) / 2 + (18 * (p - .5) if k % 3 == 1 else 0)
        frame = fg.crop((dx, (H-ch)/2, dx+cw, (H-ch)/2+ch)).resize((W, H), Image.BILINEAR)
    else:
        frame = bg.copy(); f2 = fg.resize((int(fg.width*z), int(fg.height*z)), Image.BILINEAR)
        frame.paste(f2, ((W - f2.width)//2, 860 - f2.height//2)) if s_kind != 'fill' else frame.paste(f2.crop(((f2.width-1080)//2, (f2.height-950)//2, (f2.width-1080)//2+1080, (f2.height-950)//2+950)), (0, 385))
    if scenes[k].get("sfx") and dt < 0.35:   # shake on impact
        amp = 18 * (1 - dt / 0.35); ox, oy = int(amp * math.sin(dt * 90)), int(amp * math.cos(dt * 70))
        frame = frame.transform((W, H), Image.AFFINE, (1, 0, ox, 0, 1, oy))
    # pop-in subtitle
    a = min(1, (t - bounds[k]) / 0.12); sc = 0.9 + 0.1 * a
    sl = sub if sc >= 0.999 else sub.resize((int(W*sc), int(360*sc)))
    frame = frame.convert("RGBA"); frame.alpha_composite(band); frame.alpha_composite(sl, ((W - sl.width)//2, 1345 + (360 - sl.height)//2)); frame = frame.convert("RGB")
    if t < 0.08: frame = Image.blend(frame, Image.new("RGB", (W, H), (255, 255, 255)), 0.6 * (1 - t / 0.08))  # hook flash
    ff.stdin.write(frame.tobytes())
ff.stdin.close(); ff.wait()

# ---- audio: tension bed (clock tick + drone) + SFX + narration ----
N = int(total * SR); tt = np.arange(N) / SR; rng = np.random.default_rng(1)
drone = (0.5*np.sin(2*np.pi*55*tt) + 0.3*np.sin(2*np.pi*82.4*tt) + 0.2*np.sin(2*np.pi*110*tt*1.002)) * (0.6 + 0.4*np.sin(2*np.pi*0.15*tt))
tick = np.zeros(N); tk = (np.exp(-np.arange(int(0.03*SR)) / (0.004*SR)) * np.sin(2*np.pi*2400*np.arange(int(0.03*SR))/SR))
for j, tm in enumerate(np.arange(0.2, total, 0.5)):
    i = int(tm*SR); seg = tk * (1.0 if j % 2 == 0 else 0.6); tick[i:i+len(seg)] += seg[:N-i]
bed = 0.05 * drone + 0.10 * tick
rev = next((bounds[i] for i, s in enumerate(scenes) if s.get("sfx") == "reversal"), None)
if rev:  # cut the bed at the reversal, bring it back 0.8s later
    g = np.ones(N); i0, i1 = int((rev-0.05)*SR), int((rev+0.8)*SR); g[i0:i1] = 0
    ramp = int(0.4*SR); g[i1:i1+ramp] = np.linspace(0, 1, len(g[i1:i1+ramp])); bed *= g
def impact(n):
    x = np.arange(n) / SR; return (np.sin(2*np.pi*(60*np.exp(-x*3))*x*6) * np.exp(-x*4) + 0.4*rng.standard_normal(n)*np.exp(-x*25))
sfx = np.zeros(N)
for i, s in enumerate(scenes):
    if s.get("sfx"):
        st = int(bounds[i]*SR); L = min(int(1.4*SR), N-st); sfx[st:st+L] += 0.55 * impact(L)
        if s["sfx"] == "reversal":  # short riser into the hit
            rl = int(0.6*SR); r0 = max(0, st-rl); x = np.arange(st-r0)/SR
            sfx[r0:st] += 0.12 * rng.standard_normal(st-r0) * np.linspace(0, 1, st-r0)
mix = bed + sfx
if nar_audio is not None: mix[:min(N, len(nar_audio))] += 1.0 * nar_audio[:N]
fade = int(0.3*SR); mix[-fade:] *= np.linspace(1, 0.35, fade)   # soften loop seam
mix = mix / max(1e-6, np.abs(mix).max()) * 0.89
with wave.open(f"{BUILD}/mix.wav", "w") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype(np.int16).tobytes())
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", f"{BUILD}/video.mp4", "-i", f"{BUILD}/mix.wav", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", OUT], check=True)
json.dump({"bounds": bounds}, open(f"{BUILD}/timing.json", "w"))
print("done", OUT)
