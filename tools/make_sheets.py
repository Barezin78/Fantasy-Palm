#!/usr/bin/env python3
"""Monta preview/contact-sheet.png (telas do app na moldura do T3) e preview/comparativo-mockup-vs-app.png."""
import os, sys
from PIL import Image, ImageDraw
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "hostsim"))
import palmui as mm
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = lambda n: Image.open(f"{R}/preview/{n}.png").convert("RGB")
M = lambda n: Image.open(f"{R}/mockups/v2/{n}.png").convert("RGB")
F = mm.UIB
def sheet(items, title, out, cols):
    devs = [(mm.device(im), lb) for im, lb in items]; dw, dh = devs[0][0].size; gap = 40
    rows = (len(devs) + cols - 1) // cols
    sh = Image.new("RGB", (cols * dw + (cols + 1) * gap, 120 + rows * (dh + 110)), (24, 24, 28)); d = ImageDraw.Draw(sh)
    d.text((gap, 30), title, font=F(38), fill=(255, 255, 255))
    for i, (dv, lb) in enumerate(devs):
        x = gap + (i % cols) * (dw + gap); y = 110 + (i // cols) * (dh + 110)
        sh.paste(dv, (x, y), dv)
        d.text((x + dw // 2, y + dh + 45), lb, font=F(30), fill=(255, 110, 110) if "SIMUL" in lb or "mockup" in lb else (80, 220, 200), anchor="mm")
    sh.save(out); print(out, sh.size)
telas = [("1-inicio", "1 · Início"), ("2-escalacao-la", "2 · Escalação LA"), ("2c-escalacao-lb-adversario", "2 · LB adversário"),
         ("3-tabela-la", "3 · Tabela LA"), ("3c-tabela-lb-rolada", "3 · Tabela LB (rolada)"), ("4-jogos-nfl", "4 · Jogos NFL"),
         ("6b-sobre-os-dados", "5 · Sobre os dados"), ("7-inicio-encerrada-SIMULADA", "6 · Encerrada (SIMULADA)"),
         ("8-tabela-encerrada-SIMULADA", "6 · Tabela (SIMULADA)"), ("5-inicio-320x320", "Início 320×320"),
         ("9-escalacao-encerrada-SIMULADA", "Escalação (SIMULADA)"), ("6-sem-dados", "Sem dados")]
sheet([(P(n), l) for n, l in telas], "Fantasy v1.0.1 para Palm T3 — telas do app (simulador), dados fictícios (Liga Alfa / Liga Beta)",
      f"{R}/preview/contact-sheet.png", 6)
comp = [("1-inicio-andamento", "1-inicio", "Início"), ("2-escalacao", "2-escalacao-la", "Escalação"), ("3-tabela", "3-tabela-la", "Tabela"),
        ("4-jogos-nfl", "4-jogos-nfl", "NFL"), ("7-inicio-encerrada-SIMULADA", "7-inicio-encerrada-SIMULADA", "Encerrada")]
items = []
for m, a, l in comp: items += [(M(m), f"{l} · mockup"), (P(a), f"{l} · app")]
sheet(items, "Mockup v2 (vermelho) x app v1.0.1 (verde) — dados fictícios", f"{R}/preview/comparativo-mockup-vs-app.png", 10)
