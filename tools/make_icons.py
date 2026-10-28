# Gera os ícones BMP (bola de futebol americano em fundo azul-marinho) para o pilrc
from PIL import Image, ImageDraw
import os, sys
OUT = sys.argv[1] if len(sys.argv) > 1 else "."
MAG, NAVY, BALL, WHT = (255, 0, 255), (14, 30, 70), (150, 80, 30), (255, 255, 255)
def icon(w, h, color=True):
    S = 8; W, H = w * S, h * S
    im = Image.new("RGB", (W, H), MAG if color else WHT); d = ImageDraw.Draw(im)
    if color: d.rounded_rectangle([0, 0, W - 1, H - 1], int(min(W, H) * 0.22), fill=NAVY)
    m = min(W, H); cx, cy = W // 2, H // 2; bw, bh = m * 0.86, m * 0.52
    d.ellipse([cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2], fill=BALL if color else (0, 0, 0))
    lc = WHT; lw = max(S, int(m * 0.06))
    d.line([cx - bw * 0.22, cy, cx + bw * 0.22, cy], fill=lc, width=lw)
    for k in (-2, -1, 0, 1, 2):
        x = cx + k * bw * 0.09; d.line([x, cy - bh * 0.17, x, cy + bh * 0.17], fill=lc, width=max(S, lw // 2 + S // 2))
    return im.resize((w, h), Image.NEAREST)
def save(im, name): im.save(os.path.join(OUT, name))
save(icon(22, 22), "icon-8.bmp"); save(icon(44, 44), "icon-8-hd.bmp")
save(icon(22, 22, False).convert("1"), "icon-1.bmp")
save(icon(15, 9), "sicon-8.bmp"); save(icon(30, 18), "sicon-8-hd.bmp")
save(icon(15, 9, False).convert("1"), "sicon-1.bmp")
