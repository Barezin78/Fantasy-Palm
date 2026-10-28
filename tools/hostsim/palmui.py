# Partes visuais do Palm T3 (barra de status, moldura) — copiadas do projeto Mengão (mockups/make_mockups.py)
from PIL import Image, ImageDraw, ImageFont
import os
W, H = 320, 480
SB = 32                      # T3 status bar height (bottom)
APP_H = H - SB               # 448 usable with slider open + DIA collapsed
G = "/usr/share/fonts/truetype/sand-box/google/"
L = "/usr/share/fonts/truetype/liberation/"
def F(p, s): return ImageFont.truetype(p, s)
UI   = lambda s: F(L+"LiberationSans-Regular.ttf", s)   # Palm system font feel
UIB  = lambda s: F(L+"LiberationSans-Bold.ttf", s)      # Palm bold font feel
ANTON= lambda s: F(G+"Anton/Anton-Regular.ttf", s)
BEB  = lambda s: F(G+"Bebas Neue/BebasNeue-Regular.ttf", s)
BARK = lambda s: F(G+"Barlow Condensed/BarlowCondensed-Black.ttf", s)
BARB = lambda s: F(G+"Barlow Condensed/BarlowCondensed-Bold.ttf", s)

RED, DRED, BLK, WHT = (232,0,16), (150,0,8), (0,0,0), (255,255,255)
GRY, LGRY, MGRY, DGRY = (200,200,200), (232,232,232), (150,150,150), (64,64,64)
GRN, YEL, PALE = (0,150,40), (255,200,0), (255,236,236)
SBBG = (40,40,48)

class S:
    def __init__(s, bg=WHT):
        s.im = Image.new("RGB", (W, H), bg); s.d = ImageDraw.Draw(s.im)
    def px(s, on=True): s.d.fontmode = "1" if on else "L"   # "1" = crisp bitmap, like Palm fonts
    def t(s, xy, txt, f, fill=BLK, anchor="la", aa=False):
        if aa:
            s.px(False); s.d.text(xy, txt, font=f, fill=fill, anchor=anchor); s.px(True); return
        # crisp 1-bit text (Palm bitmap-font feel) without mono-hinting spacing glitches
        m = Image.new("L", s.im.size, 0); md = ImageDraw.Draw(m)
        md.text(xy, txt, font=f, fill=255, anchor=anchor)
        m = m.point(lambda v: 255 if v > 100 else 0)
        s.im.paste(Image.new("RGB", s.im.size, fill), (0, 0), m)
    def tw(s, txt, f): b = s.d.textbbox((0,0), txt, font=f); return b[2]-b[0]

def title(s, txt, right=None, rfill=BLK, tab=BLK, bar=None):
    """Palm OS 5 form title: filled black tab + rule across the screen."""
    f = UIB(17); w = s.tw(txt, f) + 16
    if bar: s.d.rectangle([0, 0, W, 25], fill=bar)
    s.d.rounded_rectangle([0, 0, w, 25], 5, fill=tab); s.d.rectangle([0, 0, w, 6], fill=tab)
    s.d.rectangle([0, 0, 6, 25], fill=tab)
    s.t((8, 3), txt, f, WHT)
    s.d.line([0, 25, W, 25], fill=tab if bar else BLK, width=2)
    if right: s.t((W-6, 4), right, UIB(15), rfill, "ra")

def button(s, box, txt, sel=False, f=None):
    f = f or UIB(15)
    s.d.rounded_rectangle(box, 7, fill=BLK if sel else WHT, outline=BLK, width=2)
    cx, cy = (box[0]+box[2])//2, (box[1]+box[3])//2
    s.t((cx, cy), txt, f, WHT if sel else BLK, "mm")

def popup_trigger(s, x, y, txt):
    f = UIB(15); s.d.polygon([(x, y+6), (x+10, y+6), (x+5, y+12)], fill=BLK)
    s.t((x+14, y), txt, f)

def exemplo(s, x, y, color=RED):
    f = UIB(11); w = s.tw("EXEMPLO", f) + 8
    s.d.rectangle([x-w, y, x, y+15], fill=WHT, outline=color, width=1)
    s.t((x-w//2-0, y+8), "EXEMPLO", f, color, "mm")

def shield(s, x, y, w, h, outline=WHT, text=True):
    """Escudo genérico estilizado (NÃO é o escudo oficial): listras rubro-negras + CRF."""
    pts = [(x, y), (x+w, y), (x+w, y+h*0.58), (x+w/2, y+h), (x, y+h*0.58)]
    m = Image.new("L", (W, H), 0); ImageDraw.Draw(m).polygon(pts, fill=255)
    st = Image.new("RGB", (W, H), BLK); sd = ImageDraw.Draw(st)
    band = h/7
    for i in range(7):
        if i % 2 == 1: sd.rectangle([x, y+i*band, x+w, y+(i+1)*band], fill=RED)
    s.im.paste(st, (0, 0), m)
    s.d.line(pts+[pts[0]], fill=outline, width=2, joint="curve")
    if text:
        f = BARK(int(h*0.36)); cy = y + h*0.40
        s.d.rectangle([x+3, cy-h*0.17, x+w-3, cy+h*0.17], fill=BLK)
        s.t((x+w/2, cy), "CRF", f, WHT, "mm", aa=True)

def statusbar(s, clock="14:37"):
    """Tungsten T3 status bar (slider open): Home, Menu, Find | clock | alert, BT, battery, input toggle."""
    y = APP_H; d = s.d
    d.rectangle([0, y, W, H], fill=SBBG); d.line([0, y, W, y], fill=MGRY)
    c = (225,225,225); cy = y + SB//2
    # home
    d.polygon([(10, cy-1), (19, cy-9), (28, cy-1)], fill=c); d.rectangle([13, cy-1, 25, cy+8], fill=c)
    d.rectangle([17, cy+2, 21, cy+8], fill=SBBG)
    # menu (drop-down)
    d.rectangle([38, cy-8, 56, cy+8], outline=c, width=2); d.rectangle([38, cy-8, 56, cy-4], fill=c)
    for k in (0, 5): d.line([42, cy+k, 52, cy+k], fill=c, width=2)
    # find
    d.ellipse([66, cy-9, 80, cy+5], outline=c, width=2); d.line([78, cy+3, 84, cy+9], fill=c, width=3)
    s.t((W//2, cy), clock, UIB(16), c, "mm")
    # alert star, bluetooth
    d.polygon([(214, cy+7), (220, cy-9), (226, cy+7)], outline=c, width=2)
    d.line([(236, cy-4), (246, cy+5), (241, cy+9), (241, cy-9), (246, cy-5), (236, cy+4)], fill=c, width=2)
    # battery
    d.rectangle([256, cy-6, 278, cy+6], outline=c, width=2); d.rectangle([279, cy-3, 281, cy+3], fill=c)
    d.rectangle([259, cy-3, 272, cy+3], fill=(90,210,90))
    # input area toggle (show Graffiti)
    d.rectangle([290, cy-9, 312, cy+9], outline=c, width=2)
    d.polygon([(295, cy+4), (301, cy-4), (307, cy+4)], fill=c)

def stripes_bg(s, y0, y1, n=8, c1=RED, c2=BLK):
    h = (y1-y0)/n
    for i in range(n): s.d.rectangle([0, round(y0+i*h), W, round(y0+(i+1)*h)], fill=c1 if i % 2 == 0 else c2)

def to565(im):
    return im.point(lambda v: v & 0xF8 if True else v)  # approx RGB565 (G gets 6 bits; close enough for preview)

def save(s, name):
    im = to565(s.im)
    im.save(f"{OUT}/{name}.png"); im.resize((W*2, H*2), Image.NEAREST).save(f"{OUT}/{name}@2x.png"); return im

# ---------------- contact sheet with T3-ish frame ----------------
def device(screen):
    sc = screen.resize((W*2, H*2), Image.NEAREST)
    bw, bh = W*2 + 80, H*2 + 250
    im = Image.new("RGBA", (bw, bh), (0,0,0,0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw-1, bh-1], 60, fill=(118,122,130))
    d.rounded_rectangle([6, 6, bw-7, bh-7], 56, fill=(78,82,90))
    d.rounded_rectangle([24, 50, bw-25, 50+H*2+32], 14, fill=(10,10,12))
    d.text((bw//2, 28), "palmOne", font=UIB(22), fill=(200,200,205), anchor="mm")
    im.paste(sc, (40, 66))
    cy = 66 + H*2 + 100
    for cx in (110, 220, bw-220, bw-110):
        d.ellipse([cx-30, cy-30, cx+30, cy+30], fill=(55,58,64), outline=(150,154,160), width=3)
    d.ellipse([bw//2-48, cy-48, bw//2+48, cy+48], fill=(55,58,64), outline=(170,174,180), width=4)
    d.ellipse([bw//2-18, cy-18, bw//2+18, cy+18], fill=(95,98,105))
    return im
