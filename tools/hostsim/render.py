#!/usr/bin/env python3
"""Renderiza as operações de desenho do app (via ./sim, que compila o src/main.c de verdade) em PNG.
Prévia aproximada: fontes Liberation no lugar das fontes do Palm (larguras de fontw.h)."""
import subprocess, sys, os
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
L = "/usr/share/fonts/truetype/liberation/"
FONTS = {0: ImageFont.truetype(L+"LiberationSans-Regular.ttf", 18), 1: ImageFont.truetype(L+"LiberationSans-Bold.ttf", 18),
         2: ImageFont.truetype(L+"LiberationSans-Regular.ttf", 23), 7: ImageFont.truetype(L+"LiberationSans-Bold.ttf", 24)}
LH = {0: 22, 1: 22, 2: 28, 7: 28}
def col(h): return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def render(pdb, height, screen, out, lg=0, side=0, scroll=0, clock=None, sobre=False):
    import datetime as _d; clock = clock or _d.datetime.now().strftime("%H:%M")
    args = [os.path.join(HERE, "sim"), pdb, str(height), str(screen), str(lg), str(side), str(scroll)] + (["sobre"] if sobre else [])
    res = subprocess.run(args, capture_output=True, text=True, encoding="cp1252")
    if res.returncode: raise SystemExit(f"sim falhou ({' '.join(args)}):\n{res.stderr}")
    ops = res.stdout.splitlines()
    im = Image.new("RGB", (320, height), (255, 255, 255)); d = ImageDraw.Draw(im)
    for op in ops:
        p = op.split()
        if p[0] == "R":
            x, y, w, h, r = map(int, p[1:6])
            if w <= 0 or h <= 0: continue
            box = [x, y, x+w-1, y+h-1]
            if r: d.rounded_rectangle(box, min(r, w//2, h//2), fill=col(p[6]))
            else: d.rectangle(box, fill=col(p[6]))
        elif p[0] == "L":
            d.line(list(map(int, p[1:5])), fill=col(p[5]))
        elif p[0] == "T":
            x, y, f = map(int, p[1:4]); fg, bg, w = col(p[4]), col(p[5]), int(p[6])
            s = bytes.fromhex(p[7]).decode("cp1252") if len(p) > 7 else ""
            d.rectangle([x, y, x+w-1, y+LH[f]-1], fill=bg)
            m = Image.new("L", im.size, 0); ImageDraw.Draw(m).text((x, y+1), s, font=FONTS[f], fill=255)
            m = m.point(lambda v: 255 if v > 100 else 0)
            im.paste(Image.new("RGB", im.size, fg), (0, 0), m)
    for ln in res.stderr.splitlines():
        if ln.startswith("ALERT"): alerta(im, ln)
    full = Image.new("RGB", (320, 480), (40, 40, 48)); full.paste(im, (0, 0))
    fd = ImageDraw.Draw(full)
    if height < 448:
        fd.rectangle([0, height, 320, 447], fill=(70, 70, 80))
        fd.text((160, (height+448)//2), "área de Graffiti (aberta)", font=FONTS[0], fill=(200, 200, 200), anchor="mm")
    import palmui as mm
    s = mm.S(); s.im = full; s.d = ImageDraw.Draw(full); mm.statusbar(s, clock)
    full.save(out); full.resize((640, 960), Image.NEAREST).save(out.replace(".png", "@2x.png"))
    return full

def alerta(im, ln):
    """desenha o alerta do Palm (texto do .rcp com ^1 ^2 ^3 trocados), como o FrmCustomAlert mostraria"""
    import re
    rcp = open(os.path.join(HERE, "../../src/fantasy.rcp"), encoding="utf-8").read()
    m = re.search(r'ALERT ID AboutDataAlert.*?TITLE "([^"]*)".*?MESSAGE "([^"]*)"', rcp, re.S)
    title, msg = m.group(1), m.group(2).replace("\\n", "\n")
    a = ln.split(": ", 1)[1].split(" | ")
    for i, v in enumerate(a): msg = msg.replace(f"^{i+1}", v)
    d = ImageDraw.Draw(im); x0, x1 = 6, 314
    lines = []
    for par in msg.split("\n"):
        cur = ""
        for w in par.split(" "):
            t = (cur + " " + w).strip()
            if d.textlength(t, font=FONTS[0]) > x1 - x0 - 24 and cur: lines.append(cur); cur = w
            else: cur = t
        lines.append(cur)
    h = 26 + len(lines) * 22 + 56; y0 = im.height - h - 4
    d.rectangle([x0, y0, x1, y0 + h], fill=(255, 255, 255), outline=(0, 0, 0), width=2)
    d.rectangle([x0, y0, x1, y0 + 24], fill=(14, 30, 70)); d.text(((x0 + x1) // 2, y0 + 12), title, font=FONTS[1], fill=(255, 255, 255), anchor="mm")
    y = y0 + 30
    for l in lines: d.text((x0 + 12, y), l, font=FONTS[0], fill=(0, 0, 0)); y += 22
    d.rounded_rectangle([x0 + 10, y + 10, x0 + 90, y + 40], 7, outline=(0, 0, 0), width=2, fill=(255, 255, 255))
    d.text((x0 + 50, y + 25), "OK", font=FONTS[1], fill=(0, 0, 0), anchor="mm")

if __name__ == "__main__":
    root = os.path.join(HERE, "../..")
    pdb = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "dist/FantasyDados.pdb")
    sim = sys.argv[2] if len(sys.argv) > 2 else None
    outd = os.path.join(root, "preview"); os.makedirs(outd, exist_ok=True)
    R = lambda n, *a, **k: render(pdb, *a[:2], f"{outd}/{n}.png", **k)
    R("1-inicio", 448, 0)
    R("2-escalacao-la", 448, 1, lg=0, side=0)
    R("2b-escalacao-la-rolada", 448, 1, lg=0, side=0, scroll=6)
    R("2c-escalacao-lb-adversario", 448, 1, lg=1, side=1)
    R("3-tabela-la", 448, 2, lg=0)
    R("3b-tabela-lb", 448, 2, lg=1)
    R("3c-tabela-lb-rolada", 448, 2, lg=1, scroll=12)
    R("4-jogos-nfl", 448, 3)
    R("4b-jogos-nfl-rolada", 448, 3, scroll=14)
    R("5-inicio-320x320", 320, 0)
    R("5b-escalacao-320x320", 320, 1)
    render("-", 448, 0, f"{outd}/6-sem-dados.png")
    R("6b-sobre-os-dados", 448, 0, sobre=True)
    if sim:
        render(sim, 448, 0, f"{outd}/7-inicio-encerrada-SIMULADA.png", clock="08:00")
        render(sim, 448, 2, f"{outd}/8-tabela-encerrada-SIMULADA.png", clock="08:00")
        render(sim, 448, 2, f"{outd}/8b-tabela-lb-encerrada-SIMULADA.png", lg=1, clock="08:00")
        render(sim, 448, 1, f"{outd}/9-escalacao-encerrada-SIMULADA.png", clock="08:00")
        render(sim, 320, 0, f"{outd}/9b-inicio-encerrada-320x320-SIMULADA.png", clock="08:00")
    print("ok")
