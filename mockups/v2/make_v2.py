# Mockups v2 "Fantasy" p/ Palm T3 — RESUMO DA RODADA (sem ao vivo). Dados FICTÍCIOS de demonstração + variante SIMULADA.
import os, json, importlib.util, datetime as dt
spec = importlib.util.spec_from_file_location("v1", "/workspace/palm-fantasy/mockups/make_mockups.py"); V1 = importlib.util.module_from_spec(spec); spec.loader.exec_module(V1)
from make_mockups import S, UI, UIB, BARK, W, H, BLK, WHT, LGRY, MGRY, DGRY, statusbar, button, device, to565
from PIL import Image, ImageDraw
NAVY, TEAL, PALE, GOLD, POSC, LIGAS, GAMES, STAND, SIG, fmt, title, popup, pushbtns = (V1.NAVY, V1.TEAL, V1.PALE, V1.GOLD, V1.POSC, V1.LIGAS, V1.GAMES, V1.STAND, V1.SIG, V1.fmt, V1.title, V1.popup, V1.pushbtns)
OUT = os.path.dirname(os.path.abspath(__file__))
SIM = json.load(open(f"{OUT}/demo-simulado.json"))
GREEN, RED, AMBER = (0, 135, 60), (200, 20, 30), (200, 120, 0)
GAME = V1.GAME
def q(x): return x.replace("“", '"').replace("”", '"').replace("’", "'").strip()

def save(s, name):
    im = to565(s.im); im.save(f"{OUT}/{name}.png"); im.resize((W*2, H*2), Image.NEAREST).save(f"{OUT}/{name}@2x.png"); return im

def syncbar(s, y, txt, estado, cor):
    sim = txt.startswith("SIMULADO")
    """faixa fixa com data/hora do sync + estado da rodada"""
    s.d.rectangle([0, y, W, y+20], fill=(236, 240, 248)); s.d.line([0, y+20, W, y+20], fill=NAVY)
    s.t((6, y+10), txt, UIB(12), RED if sim else NAVY, "lm")
    f = UIB(11); w = s.tw(estado, f) + 10
    s.d.rounded_rectangle([W-6-w, y+3, W-6, y+17], 3, fill=cor); s.t((W-6-w//2, y+10), estado, f, WHT, "mm")

def simulado(s, x, y):
    f = UIB(11); txt = "SIMULADO"; w = s.tw(txt, f) + 10
    s.d.rectangle([x-w, y, x, y+15], fill=WHT, outline=RED, width=2); s.t((x-w//2, y+8), txt, f, RED, "mm")

ANDAMENTO = ("Dados de dom 25/10 15h20", "Rodada em andamento", AMBER)
ENCERRADA = ("SIMULADO · ter 27/10 08h00", "Rodada encerrada", GREEN)

def kickoff(team):
    g = GAME.get(team)
    if not g: return "BYE"
    if g["state"] == "post": return "Final"
    t = dt.datetime.fromisoformat(g["t"][:19]); D = ["seg", "ter", "qua", "qui", "sex", "sáb", "dom"][t.weekday()]
    return f"{D} {t.hour}h" + (f"{t.minute:02d}" if t.minute else "")

# ---------------- 1. Início — rodada em andamento ----------------
def inicio(menu=None):
    s = S(WHT); title(s, "Fantasy", "Semana 7"); syncbar(s, 27, *ANDAMENTO)
    y = 52
    for nome in ("Liga Alfa", "Liga Beta"):
        L = LIGAS[nome]; eu, ad = L["eu"], L["adv"]; wp = L["wp"]
        s.d.rounded_rectangle([4, y, W-5, y+148], 8, fill=WHT, outline=NAVY, width=2)
        s.d.rounded_rectangle([4, y, W-5, y+24], 8, fill=NAVY); s.d.rectangle([4, y+14, W-5, y+24], fill=NAVY)
        s.t((12, y+4), nome, UIB(15), WHT); s.t((W-12, y+5), f"{eu['rec']} · {eu['rank']}º de {L['times']}", UIB(13), (190, 230, 222), "ra")
        s.t((12, y+29), eu["time"], UIB(14), NAVY); s.t((W-12, y+29), q(ad["time"]), UIB(14), DGRY, "ra")
        s.t((12, y+43), fmt(eu["pts"]), BARK(42), NAVY, aa=True); s.t((W//2, y+67), "x", UIB(16), MGRY, "mm")
        s.t((W-12, y+43), fmt(ad["pts"]), BARK(42), DGRY, "ra", aa=True)
        s.t((W//2, y+88), "parcial", UI(11), MGRY, "mm")
        s.t((12, y+94), f"proj {eu['proj']:.1f}", UI(13), DGRY); s.t((W-12, y+94), f"proj {ad['proj']:.1f}", UI(13), DGRY, "ra")
        bx0, bx1, by = 12, W-13, y+114
        s.t((bx0, by), "Vitória", UIB(12), NAVY)
        s.d.rectangle([bx0+50, by+2, bx1-40, by+12], outline=NAVY, fill=WHT)
        fx = bx0+50 + max(2, int((bx1-40-bx0-50)*wp)); s.d.rectangle([bx0+51, by+3, fx, by+11], fill=TEAL)
        s.t((bx1, by), f"{round(wp*100)}%", UIB(13), NAVY, "ra")
        fin = sum(1 for p in eu["tit"] if p["estado"] == "post")
        s.t((12, by+16), f"{fin} de {len(eu['tit'])} titulares com jogo encerrado", UI(12), MGRY)
        y += 154
    # resumo do que falta
    s.d.rectangle([4, y, W-5, y+44], fill=(246, 246, 246), outline=LGRY)
    s.t((12, y+5), "Falta na rodada", UIB(13), NAVY)
    s.t((12, y+23), "Último jogo: seg 26/10 21h15 · DAL @ PHI", UI(12), DGRY)
    button(s, [6, 412, 104, 440], "Escalação"); button(s, [111, 412, 209, 440], "Tabela"); button(s, [216, 412, 314, 440], "NFL")
    if menu: menu_dados(s, menu)
    statusbar(s, "15:20")
    return save(s, {None: "1-inicio-andamento", "menu": "5-menu-dados", "sobre": "6-sobre-os-dados"}[menu])

def menu_dados(s, modo):
    if modo == "menu":
        s.d.rectangle([0, 0, W, 26], fill=WHT); s.d.line([0, 26, W, 26], fill=BLK, width=2)
        s.d.rectangle([4, 1, 70, 24], fill=BLK); s.t((12, 4), "Dados", UIB(16), WHT); s.t((84, 4), "Opções", UIB(16))
        mx0, my0, mx1 = 4, 26, 250
        items = [("Sobre os dados...", "/D"), ("Sincronizar (HotSync)", "/S"), None, ("Liga padrão...", "/L"), ("Trocar usuário...", "/U"), None, ("Preferências...", "/R"), ("Sobre o Fantasy", "")]
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
        s.t((mx0+10, my1+6), "", UI(10)); return
    # diálogo modal Palm "Sobre os dados"
    x0, y0, x1, y1 = 8, 96, W-8, 404
    s.d.rectangle([x0+3, y0+3, x1+3, y1+3], fill=DGRY)
    s.d.rectangle([x0, y0, x1, y1], fill=WHT, outline=BLK, width=2)
    s.d.rectangle([x0, y0, x1, y0+22], fill=NAVY); s.t((W//2, y0+11), "Sobre os dados", UIB(15), WHT, "mm")
    rows = [("Sync:", "dom 25/10/2026 15h20"), ("", "(horário de Brasília)"), ("Semana:", "7 · em andamento"), ("Fonte:", "Sleeper + ESPN"),
            ("Usuário:", "demo"), ("Ligas:", "Liga Alfa, Liga Beta"), ("Arquivo:", "FantasyDados-demo.pdb")]
    yy = y0 + 32
    for k, v in rows:
        s.t((x0+10, yy), k, UIB(13), BLK); s.t((x0+80, yy), v, UI(13), BLK); yy += 19
    yy += 6; s.d.line([x0+8, yy, x1-8, yy], fill=LGRY); yy += 8
    for ln in ["Pontos e placares são os do momento", "do sync. O Palm não atualiza sozinho:", "rode o HotSync de novo para ver", "o resultado final da rodada."]:
        s.t((x0+10, yy), ln, UI(13), DGRY); yy += 17
    button(s, [W//2-90, y1-34, W//2-8, y1-8], "OK"); button(s, [W//2+8, y1-34, W//2+90, y1-8], "HotSync")

# ---------------- 2. Escalação (resumo) ----------------
def escalacao(nome="Liga Alfa", lado="eu", fname="2-escalacao"):
    L = LIGAS[nome]; eu, ad = L["eu"], L["adv"]; T = L[lado]
    s = S(WHT); title(s, "Escalação"); popup(s, W-6, 5, nome)
    syncbar(s, 27, *ANDAMENTO)
    pushbtns(s, ["Meu time", "Adversário"], 0 if lado == "eu" else 1, 51, h=20)
    y = 75
    s.d.rectangle([4, y, W-5, y+32], fill=NAVY); c2 = (150, 170, 200)
    s.t((10, y+2), "Blue Comets", UIB(12), (190, 230, 222)); s.t((W-10, y+2), q(ad["time"]), UIB(12), (190, 230, 222), "ra")
    s.t((10, y+15), fmt(eu["pts"]), UIB(15), WHT); s.t((16 + s.tw(fmt(eu["pts"]), UIB(15)), y+18), f"proj {eu['proj']:.1f}", UI(11), c2)
    s.t((W-10, y+15), fmt(ad["pts"]), UIB(15), WHT, "ra"); s.t((W-16 - s.tw(fmt(ad["pts"]), UIB(15)), y+18), f"proj {ad['proj']:.1f}", UI(11), c2, "ra")
    s.t((W//2, y+9), "vitória", UI(10), c2, "mm"); s.t((W//2, y+22), f"{round(L['wp']*100)}%", UIB(12), GOLD, "mm")
    y = 110
    s.t((8, y), "Pos", UIB(12), DGRY); s.t((50, y), "Jogador / jogo", UIB(12), DGRY); s.t((W-8, y), "Pts", UIB(12), DGRY, "ra")
    s.d.line([4, y+15, W-5, y+15], fill=BLK)
    y = 127; rh = 30
    for i, p in enumerate(T["tit"]):
        yy = y + i*rh
        slot = {"FLEX": "W/R"}.get(p["slot"], p["slot"]); c = POSC.get(p["slot"], DGRY)
        s.d.rounded_rectangle([7, yy+6, 43, yy+24], 4, fill=c); s.t((25, yy+15), slot, UIB(12), WHT, "mm")
        s.t((50, yy+1), p["nome"], UIB(15), BLK)
        if p.get("lesao"): s.t((50 + s.tw(p["nome"], UIB(15)) + 6, yy+3), p["lesao"][0], UIB(12), RED)
        g = GAME.get(p["time"]); ko = kickoff(p["time"])
        if ko == "Final":
            a, h = g["away"], g["home"]; s.t((50, yy+17), f"{a[0]} {a[1]} x {h[1]} {h[0]} · Final", UIB(11), GREEN)
        else:
            s.t((50, yy+17), f"{p['adv']} · {ko}", UI(11), DGRY)
        done = p["estado"] == "post"
        s.t((W-8, yy+1), fmt(p["pts"]), UIB(16), BLK if done else DGRY, "ra")
        s.t((W-8, yy+18), f"p {p['proj']:.1f}", UI(10), MGRY, "ra")
        if i: s.d.line([4, yy, W-5, yy], fill=LGRY)
    s.t((8, y+9*rh+2), "pontos de quem ainda não terminou = parcial do sync", UI(10), MGRY)
    button(s, [6, 412, 96, 440], "Início"); button(s, [103, 412, 193, 440], "Banco")
    statusbar(s, "15:20"); return save(s, fname)

# ---------------- 3. Tabela ----------------
def tabela(nome="Liga Alfa", fname="3-tabela", sim=False):
    L = LIGAS[nome]; rows = SIM[L["id"]] if sim else STAND[L["id"]]
    s = S(WHT); title(s, "Tabela"); popup(s, W-6, 5, nome)
    syncbar(s, 27, *(ENCERRADA if sim else ANDAMENTO))
    y = 50
    s.d.rectangle([0, y, W, y+20], fill=NAVY); hf = UIB(13)
    s.t((8, y+3), "#", hf, WHT); s.t((30, y+3), "Time", hf, WHT); s.t((210, y+3), "V-D", hf, WHT, "ma"); s.t((262, y+3), "PF", hf, WHT, "ma"); s.t((W-8, y+3), "Seq", hf, WHT, "ra")
    y += 22; rh = 27 if len(rows) <= 12 else 18
    f, fb = (UI(15), UIB(15)) if rh > 20 else (UI(13), UIB(13))
    for i, r in enumerate(rows):
        yy = y + i*rh; me = r["owner"] == "demo"
        if me: s.d.rectangle([0, yy, W, yy+rh-1], fill=PALE)
        c = TEAL if me else BLK; ff = fb if me else f
        s.t((20, yy+rh//2), str(i+1), ff, c, "rm")
        team = q(r["team"])
        lim = 140 if sim else 150
        while s.tw(team, ff) > lim: team = team[:-2] + "…"
        s.t((30, yy+rh//2), team, ff, c, "lm")
        if sim and r.get("old_rank"):
            dlt = r["old_rank"] - (i+1)
            if dlt: s.t((178, yy+rh//2), ("▲" if dlt > 0 else "▼"), UI(10), GREEN if dlt > 0 else RED, "mm")
        s.t((210, yy+rh//2), f"{r['w']}-{r['l']}", fb, c, "mm"); s.t((262, yy+rh//2), f"{r['pf']:.0f}", ff, c, "mm")
        sk = r["streak"] or ""; s.t((W-8, yy+rh//2), sk, UI(12) if rh > 20 else UI(11), GREEN if sk.endswith("W") else RED, "rm")
        if i: s.d.line([4, yy, W-4, yy], fill=LGRY)
    yb = y + len(rows)*rh + 5
    if yb < 398: s.t((8, yb), "Ordem: vitórias, depois pontos" + (" · inclui sem 7" if sim else " · sem 7 ainda não conta"), UI(11), MGRY)
    if sim: simulado(s, W-6, 392 if yb >= 398 else yb)
    button(s, [6, 412, 96, 440], "Início")
    statusbar(s, "08:00" if sim else "15:20"); return save(s, fname)

# ---------------- 4. Jogos da NFL (resultados + horários) ----------------
def nfl():
    s = S(WHT); title(s, "NFL", "Semana 7"); syncbar(s, 27, *ANDAMENTO)
    mine = {}
    for nome, L in LIGAS.items():
        for p in L["eu"]["tit"]: mine.setdefault(p["time"], set()).add(SIG[nome])
    gs = sorted(GAMES, key=lambda g: g["t"]); DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
    y = 50; last = None; rh = 19
    for g in gs:
        t = dt.datetime.fromisoformat(g["t"][:19]); day = f"{DIAS[t.weekday()]} {t.day:02d}/{t.month:02d}"
        if day != last:
            s.d.rectangle([0, y, W, y+16], fill=NAVY if day.startswith("Dom") else DGRY); s.t((8, y+1), day, UIB(13), WHT); last = day; y += 18
        a, h = g["away"], g["home"]; m = y + rh//2; ff = UIB(14)
        s.t((8, m), f"{t.hour}h{t.minute:02d}", UI(12), DGRY, "lm")
        s.t((50, m), a[0], ff, BLK, "lm"); s.t((152, m), h[0], ff, BLK, "lm")
        if g["state"] == "post":
            aw = int(a[1]) > int(h[1])
            s.t((110, m), a[1], UIB(14) if aw else UI(14), BLK, "rm"); s.t((120, m), "x", UI(12), MGRY, "mm"); s.t((130, m), h[1], UIB(14) if not aw else UI(14), BLK, "lm")
            s.t((192, m), "Final", UIB(12), GREEN, "lm")
        else:
            s.t((120, m), "@", UI(12), MGRY, "mm"); s.t((192, m), (g["tv"] or [""])[0], UI(12), MGRY, "lm")
        tags = sorted(set().union(*(mine.get(x, set()) for x in (a[0], h[0])))); xx = W-8
        for tg in reversed(tags):
            w = s.tw(tg, UIB(11)) + 8
            s.d.rounded_rectangle([xx-w, y+3, xx, y+rh-4], 3, fill=TEAL if tg == "LA" else (40, 110, 220)); s.t((xx-w//2, m), tg, UIB(11), WHT, "mm"); xx -= w + 3
        if gs.index(g) and last == day: s.d.line([4, y, W-4, y], fill=(240, 240, 240))
        y += rh
    s.d.line([0, y+2, W, y+2], fill=LGRY)
    s.t((8, y+6), "Final = resultado · demais: horário de início", UI(11), DGRY)
    s.t((8, y+20), "LA / LB = tem titular seu · horário de Brasília", UI(11), DGRY)
    button(s, [6, 412, 96, 440], "Início")
    statusbar(s, "15:20"); return save(s, "4-jogos-nfl")

# ---------------- 7. Início — rodada encerrada (SIMULADA ter 27/10) ----------------
def inicio_encerrada():
    s = S(WHT); title(s, "Fantasy", "Semana 7"); syncbar(s, 27, *ENCERRADA)
    y = 52
    for nome in ("Liga Alfa", "Liga Beta"):
        L = LIGAS[nome]; rows = SIM[L["id"]]
        rank, me = next((i+1, r) for i, r in enumerate(rows) if r["owner"] == "demo")
        opp = next(r for r in rows if r["rid"] == me["opp"]); win = me["week_pts"] > me["opp_pts"]
        s.d.rounded_rectangle([4, y, W-5, y+148], 8, fill=WHT, outline=NAVY, width=2)
        s.d.rounded_rectangle([4, y, W-5, y+24], 8, fill=NAVY); s.d.rectangle([4, y+14, W-5, y+24], fill=NAVY)
        s.t((12, y+4), nome, UIB(15), WHT); s.t((W-12, y+5), "Final · Sem 7", UIB(13), (190, 230, 222), "ra")
        s.t((12, y+29), "Blue Comets", UIB(14), NAVY); s.t((W-12, y+29), q(opp["team"]), UIB(14), DGRY, "ra")
        s.t((12, y+43), fmt(me["week_pts"]), BARK(42), GREEN if win else DGRY, aa=True); s.t((W//2, y+67), "x", UIB(16), MGRY, "mm")
        s.t((W-12, y+43), fmt(me["opp_pts"]), BARK(42), DGRY if win else RED, "ra", aa=True)
        # selo VITÓRIA/DERROTA
        lab = "VITÓRIA" if win else "DERROTA"; col = GREEN if win else RED; f = UIB(16); w = s.tw(lab, f) + 20
        s.d.rounded_rectangle([12, y+94, 12+w, y+116], 5, fill=col); s.t((12+w//2, y+105), lab, f, WHT, "mm")
        s.t((W-12, y+97), f"por {abs(me['week_pts']-me['opp_pts']):.2f}", UI(13), DGRY, "ra")
        old = me["old_rank"]; dlt = old - rank
        arrow = "▲" if dlt > 0 else "▼" if dlt < 0 else "="
        s.t((12, y+124), f"Agora {me['w']}-{me['l']} · {rank}º de {L['times']}", UIB(13), NAVY)
        s.t((W-12, y+124), f"{arrow} era {old}º" if dlt else "= mesma posição", UIB(12), GREEN if dlt > 0 else RED if dlt < 0 else MGRY, "ra")
        y += 154
    s.d.rectangle([4, y, W-5, y+44], fill=(246, 246, 246), outline=LGRY)
    s.t((12, y+5), "Próxima rodada: Semana 8", UIB(13), NAVY)
    s.t((12, y+23), "Escalações da sem 8 no próximo sync", UI(12), DGRY)
    simulado(s, W-10, y+5)
    button(s, [6, 412, 104, 440], "Escalação"); button(s, [111, 412, 209, 440], "Tabela"); button(s, [216, 412, 314, 440], "NFL")
    statusbar(s, "08:00"); return save(s, "7-inicio-encerrada-SIMULADA")

def overview(screens, labels):
    devs = [device(x) for x in screens]; gap = 50; dw, dh = devs[0].size
    sheet = Image.new("RGB", (len(devs)*dw + (len(devs)+1)*gap, dh + 230), (24, 24, 28)); d = ImageDraw.Draw(sheet)
    d.text((gap, 26), "Fantasy (Sleeper) para Palm T3 — v2 “resumo da rodada” (sem ao vivo) · dados fictícios de demonstração · tela 7 e 8 SIMULADAS (ter 27/10)", font=UIB(40), fill=WHT)
    for i, (dv, lb) in enumerate(zip(devs, labels)):
        x = gap + i*(dw+gap); sheet.paste(dv, (x, 110), dv)
        d.text((x+dw//2, 110+dh+55), lb, font=UIB(34), fill=(255, 110, 110) if "SIMUL" in lb else (80, 220, 200), anchor="mm")
    sheet.save(f"{OUT}/overview.png")
    sc = [x.resize((W*2, H*2), Image.NEAREST) for x in screens]; g2 = 30
    sh = Image.new("RGB", (len(sc)*(W*2+g2)+g2, H*2+2*g2), (24, 24, 28))
    for i, x in enumerate(sc): sh.paste(x, (g2 + i*(W*2+g2), g2))
    sh.save(f"{OUT}/telas-2x.png")

if __name__ == "__main__":
    a = inicio(); b = escalacao(); escalacao("Liga Beta", "adv", "2b-escalacao-lb-adversario")
    c = tabela(); tabela("Liga Beta", "3b-tabela-lb"); e = nfl(); m = inicio("menu"); so = inicio("sobre")
    f = inicio_encerrada(); g = tabela("Liga Alfa", "8-tabela-encerrada-SIMULADA", sim=True); tabela("Liga Beta", "8b-tabela-lb-encerrada-SIMULADA", sim=True)
    overview([a, b, c, e, m, so, f, g], ["1 · Início (em andamento)", "2 · Escalação LA", "3 · Tabela LA", "4 · Jogos NFL", "5 · Menu Dados", "6 · Sobre os dados", "7 · Encerrada (SIMULADA)", "8 · Tabela (SIMULADA)"])
    print("ok")
