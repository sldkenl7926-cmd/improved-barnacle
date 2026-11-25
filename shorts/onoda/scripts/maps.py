import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from mpl_toolkits.basemap import Basemap
import sys
out = sys.argv[1]
F = fm.FontProperties(fname="/usr/share/fonts/truetype/nanum/NanumSquareB.ttf")
LAND, SEA, RED = "#2a3245", "#0f1420", "#ff3b3b"
LUB = (120.10, 13.82)  # Lubang Island

def fig():
    f = plt.figure(figsize=(10.8, 11.0), dpi=100); f.patch.set_facecolor(SEA)
    ax = f.add_axes([0,0,1,1]); ax.set_facecolor(SEA); return f, ax

# Map A: Philippines with Lubang
f, ax = fig()
m = Basemap(projection="merc", llcrnrlon=114.5, llcrnrlat=4.5, urcrnrlon=127.5, urcrnrlat=19.8, resolution="h", ax=ax)
m.fillcontinents(color=LAND, lake_color=SEA); m.drawcoastlines(color="#5a6785", linewidth=0.6)
x, y = m(*LUB)
for r, a in [(900, .15), (420, .3)]:
    ax.scatter(x, y, s=r*6, color=RED, alpha=a, zorder=5)
ax.scatter(x, y, s=180, color=RED, zorder=6, edgecolor="white", linewidth=2)
ax.annotate("루방섬", (x, y), xytext=(x-520000, y+260000), fontproperties=F, fontsize=46, color="white",
            arrowprops=dict(arrowstyle="-", color="white", lw=2), zorder=7)
mx, my = m(121.0, 14.6)
ax.text(mx+40000, my+40000, "마닐라", fontproperties=F, fontsize=28, color="#9aa6c4")
ax.scatter(mx, my, s=40, color="#9aa6c4")
tx, ty = m(122.2, 8.0)
ax.text(tx, ty, "필리핀", fontproperties=F, fontsize=60, color="#6f7da0")
f.savefig(f"{out}/map_lubang.png", facecolor=SEA); plt.close(f)

# Map B: Lubang -> Japan (Kyushu)
f, ax = fig()
m = Basemap(projection="merc", llcrnrlon=112, llcrnrlat=8, urcrnrlon=142, urcrnrlat=38, resolution="i", ax=ax)
m.fillcontinents(color=LAND, lake_color=SEA); m.drawcoastlines(color="#5a6785", linewidth=0.6)
x1, y1 = m(*LUB); x2, y2 = m(131.0, 32.5)
ax.annotate("", xy=(x1, y1), xytext=(x2, y2),
            arrowprops=dict(arrowstyle="-|>,head_width=0.8,head_length=1.4", color=RED, lw=6,
                            connectionstyle="arc3,rad=0.25", linestyle="--"), zorder=6)
ax.text(x2-1500000, y2-260000, "(서점 주인)", fontproperties=F, fontsize=36, color="#ff8a8a", zorder=8)
for (xx, yy), lab, dx, dy in [((x1, y1), "루방섬", 120000, -330000), ((x2, y2), "다니구치 전 소령", -1500000, 150000)]:
    ax.scatter(xx, yy, s=260, color=RED, edgecolor="white", linewidth=2, zorder=7)
    ax.text(xx+dx, yy+dy, lab, fontproperties=F, fontsize=44, color="white", zorder=8)
f.savefig(f"{out}/map_route.png", facecolor=SEA); plt.close(f)
print("maps ok")
