# Mockups "Fantasy" (Sleeper) para Palm Tungsten T3 — 320x480, 16-bit, Palm OS 5.2. Só visual, dados FICTÍCIOS de demonstração.
import sys, os, json, datetime as dt
sys.path.insert(0, "/workspace/palm-mengao/mockups")
import make_mockups as M
from make_mockups import S, UI, UIB, BEB, BARK, BARB, W, H, APP_H, BLK, WHT, LGRY, MGRY, DGRY, GRY, statusbar, button, scrollbar, device, to565
from PIL import Image, ImageDraw
OUT = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(f"{OUT}/demo-snapshot.json"))
MODEL, GAMES, STAND = D["model"], D["games"], D["standings"]
NAVY, TEAL, LIVE, PALE, GOLD = (14, 30, 70), (0, 160, 140), (220, 0, 20), (222, 244, 240), (255, 196, 0)
POSC = {"QB": (226, 60, 120), "RB": (0, 160, 140), "WR": (40, 110, 220), "TE": (240, 130, 0), "K": (130, 80, 200), "DEF": (130, 90, 50), "FLEX": (90, 90, 90)}
CLOCK = "15:20"; SYNC = "sync 15h20"
LIGAS = {l["nome"]: l for l in MODEL["ligas"]}
SIG = {"Liga Alfa": "LA", "Liga Beta": "LB"}
ESPN_AB = {"WSH": "WAS"}
GAME = {}
for g in GAMES:
    for side in ("away", "home"): GAME[ESPN_AB.get(g[side][0], g[side][0])] = g

def save(s, name):
    im = to565(s.im); im.save(f"{OUT}/{name}.png"); im.resize((W*2, H*2), Image.NEAREST).save(f"{OUT}/{name}@2x.png"); return im

def title(s, txt, right=None):
    f = UIB(17); w = s.tw(txt, f) + 16
    s.d.rounded_rectangle([0, 0, w, 25], 5, fill=NAVY); s.d.rectangle([0, 0, w, 6], fill=NAVY); s.d.rectangle([0, 0, 6, 25], fill=NAVY)
    s.t((8, 3), txt, f, WHT); s.d.line([0, 25, W, 25], fill=NAVY, width=2)
    if right: s.t((W-6, 5), right, UIB(14), NAVY, "ra")

def popup(s, xr, y, txt):
    f = UIB(14); w = s.tw(txt, f); x = xr - w - 14
    s.d.polygon([(x, y+6), (x+10, y+6), (x+5, y+12)], fill=NAVY); s.t((x+14, y), txt, f, NAVY)

def pushbtns(s, items, sel, y, x0=6, x1=W-6, h=22):
    w = (x1-x0)//len(items)
    for i, it in enumerate(items):
        b = [x0+i*w, y, x0+(i+1)*w-1, y+h]
        s.d.rectangle(b, fill=NAVY if i == sel else WHT, outline=NAVY, width=1)
        s.t(((b[0]+b[2])//2, y+h//2+1), it, UIB(14), WHT if i == sel else NAVY, "mm")

def fmt(x): return f"{x:.2f}"
def status_txt(team):
    g = GAME.get(team)
    if not g: return "BYE", MGRY
    if g["state"] == "post": return "Final", DGRY
    if g["state"] == "in":
        d = g["detail"].replace("Halftime", "Interv.").replace(" - 2nd", " 2ºQ").replace(" - 1st", " 1ºQ").replace(" - 3rd", " 3ºQ").replace(" - 4th", " 4ºQ")
        return d, LIVE
    return None, NAVY

# ---------------- 1. Início ----------------
def inicio(menu=False):
    s = S(WHT); title(s, "Fantasy", "Dom 25/10 · Sem 7")
    y = 31
    for nome in ("Liga Alfa", "Liga Beta"):
        L = LIGAS[nome]; eu, ad = L["eu"], L["adv"]; wp = L["wp"]
        s.d.rounded_rectangle([4, y, W-5, y+150], 8, fill=WHT, outline=NAVY, width=2)
        s.d.rounded_rectangle([4, y, W-5, y+24], 8, fill=NAVY); s.d.rectangle([4, y+14, W-5, y+24], fill=NAVY)
        s.t((12, y+4), nome, UIB(15), WHT); s.t((W-12, y+5), f"{eu['rec']} · {eu['rank']}º de {L['times']}", UIB(13), (190, 230, 222), "ra")
        if eu["aoVivo"]:
            s.d.ellipse([W-128, y+8, W-120, y+16], fill=(255, 70, 70))
        s.t((12, y+30), eu["time"], UIB(14), NAVY); s.t((W-12, y+30), ad["time"].replace("“", '"').replace("”", '"'), UIB(14), DGRY, "ra")
        win = eu["pts"] >= ad["pts"]
        s.t((12, y+44), fmt(eu["pts"]), BARK(44), TEAL if win else NAVY, aa=True)
        s.t((W//2, y+70), "x", UIB(16), MGRY, "mm")
        s.t((W-12, y+44), fmt(ad["pts"]), BARK(44), TEAL if not win else DGRY, "ra", aa=True)
        s.t((12, y+98), f"proj {eu['proj']:.1f}", UI(13), DGRY); s.t((W-12, y+98), f"proj {ad['proj']:.1f}", UI(13), DGRY, "ra")
        # barra de vitória
        bx0, bx1, by = 12, W-13, y+118
        s.t((bx0, by), "Vitória", UIB(12), NAVY)
        s.d.rectangle([bx0+50, by+2, bx1-40, by+12], outline=NAVY, fill=WHT)
        fx = bx0+50 + max(2, int((bx1-40-bx0-50)*wp)); s.d.rectangle([bx0+51, by+3, fx, by+11], fill=TEAL)
        s.t((bx1, by), f"{round(wp*100)}%", UIB(13), NAVY, "ra")
        s.t((12, by+16), f"{eu['aJogar']} a jogar  ·  adv {ad['aJogar']} a jogar", UI(12), MGRY)
        y += 158
    # faixa jogos agora
    nlive = sum(1 for g in GAMES if g["state"] == "in")
    s.d.rectangle([4, y, W-5, y+40], fill=PALE, outline=TEAL)
    s.d.ellipse([12, y+8, 22, y+18], fill=LIVE)
    s.t((28, y+5), f"{nlive} jogos rolando no sync", UIB(13), NAVY)
    s.t((12, y+22), "Próx: DEN@ARI 17h05 · GB@DET 17h25", UI(12), DGRY)
    s.t((W-6, 394), SYNC + " · HotSync", UI(11), MGRY, "ra")
    button(s, [6, 412, 104, 440], "Escalação"); button(s, [111, 412, 209, 440], "Tabela"); button(s, [216, 412, 314, 440], "NFL")
    if menu:
        s.d.rectangle([0, 0, W, 26], fill=WHT); s.d.line([0, 26, W, 26], fill=BLK, width=2)
        s.d.rectangle([4, 1, 70, 24], fill=BLK); s.t((12, 4), "Dados", UIB(16), WHT); s.t((84, 4), "Opções", UIB(16))
        mx0, my0, mx1 = 4, 26, 236
        items = [("Sincronizar (HotSync)", "/S"), ("Liga padrão...", "/L"), ("Trocar usuário...", "/U"), None, ("Preferências...", "/R"), ("Sobre o Fantasy", "")]
        my1 = my0 + 8 + sum(10 if it is None else 24 for it in items)
        s.d.rectangle([mx0+3, my0+3, mx1+3, my1+3], fill=DGRY); s.d.rectangle([mx0, my0, mx1, my1], fill=WHT, outline=BLK, width=2)
        yy = my0 + 4
        for i, it in enumerate(items):
            if it is None:
                for xx in range(mx0+6, mx1-6, 4): s.d.point((xx, yy+4), fill=BLK)
                yy += 10; continue
            if i == 0: s.d.rectangle([mx0+3, yy, mx1-3, yy+22], fill=BLK)
            fg = WHT if i == 0 else BLK
            s.t((mx0+10, yy+3), it[0], UI(15), fg); s.t((mx1-10, yy+3), it[1], UI(15), fg, "ra"); yy += 24
    statusbar(s, CLOCK)
    return save(s, "5-menu-dados" if menu else "1-inicio")

# ---------------- 2. Escalação ----------------
def escalacao(nome="Liga Alfa", lado="eu", fname="2-escalacao"):
    L = LIGAS[nome]; eu, ad = L["eu"], L["adv"]; T = L[lado]
    s = S(WHT); title(s, "Escalação"); popup(s, W-6, 5, nome)
    pushbtns(s, ["Meu time", "Adversário"], 0 if lado == "eu" else 1, 31)
    y = 58
    s.d.rectangle([4, y, W-5, y+32], fill=NAVY)
    an = ad["time"].replace("“", '"').replace("”", '"')
    s.t((10, y+2), "Blue Comets", UIB(12), (190, 230, 222)); s.t((W-10, y+2), an, UIB(12), (190, 230, 222), "ra")
    s.t((10, y+15), fmt(eu["pts"]), UIB(15), WHT); s.t((10 + s.tw(fmt(eu["pts"]), UIB(15)) + 6, y+18), f"proj {eu['proj']:.1f}", UI(11), (150, 170, 200))
    s.t((W-10, y+15), fmt(ad["pts"]), UIB(15), WHT, "ra"); s.t((W-16 - s.tw(fmt(ad["pts"]), UIB(15)), y+18), f"proj {ad['proj']:.1f}", UI(11), (150, 170, 200), "ra")
    s.t((W//2, y+22), f"{round(L['wp']*100)}%", UIB(12), GOLD, "mm"); s.t((W//2, y+9), "vitória", UI(10), (150, 170, 200), "mm")
    y = 94
    s.t((8, y), "Pos", UIB(12), DGRY); s.t((50, y), "Jogador / jogo", UIB(12), DGRY); s.t((W-8, y), "Pts", UIB(12), DGRY, "ra")
    s.d.line([4, y+16, W-5, y+16], fill=BLK)
    y = 112; rh = 33
    for i, p in enumerate(T["tit"]):
        yy = y + i*rh
        live = p["estado"] == "in"
        if live: s.d.rectangle([4, yy, W-5, yy+rh-1], fill=(255, 238, 238))
        slot = {"FLEX": "W/R"}.get(p["slot"], p["slot"])
        c = POSC.get(p["slot"], DGRY) if p["slot"] != "FLEX" else POSC["FLEX"]
        s.d.rounded_rectangle([7, yy+7, 43, yy+25], 4, fill=c); s.t((25, yy+16), slot, UIB(12), WHT, "mm")
        s.t((50, yy+2), p["nome"], UIB(15), BLK)
        if p.get("lesao"): s.t((50 + s.tw(p["nome"], UIB(15)) + 6, yy+4), p["lesao"][0], UIB(12), LIVE)
        st, sc = status_txt(p["time"])
        g = GAME.get(p["time"])
        if p["estado"] == "pre": st = p["kick"]
        elif g and p["estado"] in ("in", "post"):
            a, h = g["away"], g["home"]; st = f"{a[0]} {a[1]}-{h[1]} {h[0]} · {st}"
        sub = f"{p['adv']}  {st}" if p["estado"] == "pre" else st
        s.t((50, yy+18), sub, UIB(11) if live else UI(11), sc if p["estado"] != "pre" else DGRY)
        pf = UIB(16)
        s.t((W-8, yy+2), fmt(p["pts"]) if p["estado"] != "pre" else "–", pf, BLK if p["estado"] != "pre" else MGRY, "ra")
        s.t((W-8, yy+19), f"p {p['proj']:.1f}", UI(10), MGRY, "ra")
        if i: s.d.line([4, yy, W-5, yy], fill=LGRY)
    s.t((8, 414+0), "", UI(10))
    button(s, [6, 412, 96, 440], "Início"); button(s, [103, 412, 193, 440], "Banco")
    s.t((W-6, 420), SYNC, UI(11), MGRY, "ra")
    statusbar(s, CLOCK); return save(s, fname)

# ---------------- 3. Classificação ----------------
def tabela(nome="Liga Alfa", fname="3-tabela"):
    L = LIGAS[nome]; rows = STAND[L["id"]]
    s = S(WHT); title(s, "Tabela"); popup(s, W-6, 5, nome)
    y = 32
    s.d.rectangle([0, y, W, y+22], fill=NAVY)
    hf = UIB(13); s.t((8, y+4), "#", hf, WHT); s.t((30, y+4), "Time", hf, WHT)
    s.t((210, y+4), "V-D", hf, WHT, "ma"); s.t((262, y+4), "PF", hf, WHT, "ma"); s.t((W-8, y+4), "Seq", hf, WHT, "ra")
    y += 24; rh = 28 if len(rows) <= 12 else 19
    f, fb = (UI(15), UIB(15)) if rh > 20 else (UI(13), UIB(13))
    for i, r in enumerate(rows):
        yy = y + i*rh; me = r["owner"] == "demo"
        if me: s.d.rectangle([0, yy, W, yy+rh-1], fill=PALE)
        c = TEAL if me else BLK; ff = fb if me else f
        s.t((20, yy+rh//2), str(i+1), ff, c, "rm")
        team = r["team"].strip().replace("“", '"').replace("”", '"').replace("’", "'")
        while s.tw(team, ff) > 150: team = team[:-2] + "…"
        s.t((30, yy+rh//2), team, ff, c, "lm")
        s.t((210, yy+rh//2), f"{r['w']}-{r['l']}", fb, c, "mm")
        s.t((262, yy+rh//2), f"{r['pf']:.0f}", ff, c, "mm")
        sk = r["streak"] or ""; s.t((W-8, yy+rh//2), sk, UI(12) if rh > 20 else UI(11), (0, 140, 60) if sk.endswith("W") else LIVE, "rm")
        if i: s.d.line([4, yy, W-4, yy], fill=LGRY)
    yb = y + len(rows)*rh + 6
    if yb < 398: s.t((8, yb), "Ordem: vitórias, depois pontos · Sem 7 não conta", UI(11), MGRY)
    button(s, [6, 412, 96, 440], "Início"); s.t((W-6, 420), SYNC, UI(11), MGRY, "ra")
    statusbar(s, CLOCK); return save(s, fname)

# ---------------- 4. Jogos da NFL ----------------
def nfl():
    s = S(WHT); title(s, "NFL", "Semana 7")
    mine = {}
    for nome, L in LIGAS.items():
        for p in L["eu"]["tit"]: mine.setdefault(p["time"], set()).add(SIG[nome])
    gs = sorted(GAMES, key=lambda g: g["t"])
    DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    y = 30; last = None; rh = 20
    for g in gs:
        t = dt.datetime.fromisoformat(g["t"][:19])
        day = f"{DIAS[t.weekday()]} {t.day:02d}/{t.month:02d}"
        if day != last:
            s.d.rectangle([0, y, W, y+17], fill=NAVY if day.startswith("Dom") else DGRY)
            s.t((8, y+2), day, UIB(13), WHT); last = day; y += 19
        a, h = g["away"], g["home"]
        live = g["state"] == "in"
        if live: s.d.rectangle([0, y, W, y+rh-1], fill=(255, 238, 238))
        hr = f"{t.hour}h{t.minute:02d}"
        s.t((8, y+rh//2), hr, UI(12), DGRY, "lm")
        ff = UIB(14)
        s.t((50, y+rh//2), a[0], ff, BLK, "lm"); s.t((152, y+rh//2), h[0], ff, BLK, "lm")
        if g["state"] != "pre":
            s.t((110, y+rh//2), a[1], UIB(14), BLK, "rm"); s.t((120, y+rh//2), "x", UI(12), MGRY, "mm"); s.t((130, y+rh//2), h[1], UIB(14), BLK, "lm")
            st, c = status_txt(a[0])
            s.t((192, y+rh//2), st, UIB(12) if live else UI(12), c, "lm")
        else:
            s.t((120, y+rh//2), "@", UI(12), MGRY, "mm")
            s.t((192, y+rh//2), "TV " + (g["tv"] or [""])[0], UI(12), MGRY, "lm")
        tags = sorted(set().union(*(mine.get(ESPN_AB.get(x, x), set()) for x in (a[0], h[0]))))
        xx = W-8
        for tg in reversed(tags):
            w = s.tw(tg, UIB(11)) + 8
            s.d.rounded_rectangle([xx-w, y+3, xx, y+rh-4], 3, fill=TEAL if tg == "LA" else (40, 110, 220))
            s.t((xx-w//2, y+rh//2), tg, UIB(11), WHT, "mm"); xx -= w + 3
        y += rh
    s.d.line([0, y+2, W, y+2], fill=LGRY)
    s.t((8, y+8), "LA / LB = tem titular seu nesse jogo · horário de Brasília", UI(11), DGRY)
    button(s, [6, 412, 96, 440], "Início"); s.t((W-6, 420), SYNC, UI(11), MGRY, "ra")
    statusbar(s, CLOCK); return save(s, "4-jogos-nfl")

def overview(screens, labels):
    devs = [device(x) for x in screens]; gap = 50; dw, dh = devs[0].size
    sheet = Image.new("RGB", (len(devs)*dw + (len(devs)+1)*gap, dh + 230), (24, 24, 28)); d = ImageDraw.Draw(sheet)
    d.text((gap, 26), "Fantasy (Sleeper) para Palm Tungsten T3 — mockups 320×480 · dados fictícios de demonstração", font=UIB(40), fill=WHT)
    for i, (dv, lb) in enumerate(zip(devs, labels)):
        x = gap + i*(dw+gap); sheet.paste(dv, (x, 110), dv)
        d.text((x+dw//2, 110+dh+55), lb, font=UIB(34), fill=(80, 220, 200), anchor="mm")
    sheet.save(f"{OUT}/overview.png")
    # versão leve só das telas (2x, sem moldura)
    sc = [x.resize((W*2, H*2), Image.NEAREST) for x in screens]
    g2 = 30; sh = Image.new("RGB", (len(sc)*(W*2+g2)+g2, H*2+2*g2), (24, 24, 28))
    for i, x in enumerate(sc): sh.paste(x, (g2 + i*(W*2+g2), g2))
    sh.save(f"{OUT}/telas-2x.png")
    for i, (x, lb) in enumerate(zip(screens, labels)):
        device(x).save(f"{OUT}/moldura-{i+1}.png")

if __name__ == "__main__":
    a = inicio(); b = escalacao(); b2 = escalacao("Liga Beta", "adv", "2b-escalacao-lb-adversario")
    c = tabela(); c2 = tabela("Liga Beta", "3b-tabela-lb"); e = nfl(); m = inicio(True)
    overview([a, b, c, e, m], ["1 · Início (2 ligas)", "2 · Escalação LA", "3 · Tabela LA", "4 · Jogos NFL", "5 · Menu Dados"])
    print("ok")
