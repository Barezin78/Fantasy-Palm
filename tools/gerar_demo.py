#!/usr/bin/env python3
"""Gera um FantasyDados.pdb de DEMONSTRAÇÃO com nomes fictícios (sem rede, sem Sleeper).
Uso: python3 tools/gerar_demo.py [saida.pdb] [--simular-fim]

Sem flags: semana 8 "próxima" (ainda não começou) + histórico Sem 1–7.
--simular-fim: semana 7 em andamento (parcial), histórico Sem 1–6 (marcado SIMULADO).
"""
import struct, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BRT = ZoneInfo("America/Sao_Paulo")
EPOCH = datetime(1904, 1, 1)
CREATOR, TYPE, DBNAME = b"FNFL", b"DATA", "FantasyDados"
EST_ANDAMENTO, EST_PROXIMA = 0, 2

def palm_secs(dt):
    if dt.tzinfo is None: dt = dt.replace(tzinfo=BRT)
    return int((dt.astimezone(BRT).replace(tzinfo=None) - EPOCH).total_seconds())

def s(txt, n):
    b = (txt or "").encode("cp1252", "replace")[: n - 1]
    return b + b"\0" * (n - len(b))

def write_pdb(path, recs, ts):
    n = len(recs); off = 78 + 8 * n + 2
    hdr = s(DBNAME, 32) + struct.pack(">HHIIIIII", 0x0008, 1, ts, ts, 0, 0, 0, 0) + TYPE + CREATOR + struct.pack(">IIH", 0, 0, n)
    ent = b""
    for i, r in enumerate(recs):
        ent += struct.pack(">IB", off, 0) + (0x6F0000 + i).to_bytes(3, "big"); off += len(r)
    with open(path, "wb") as f:
        f.write(hdr + ent + b"\0\0" + b"".join(recs))

LIGAS = [
    dict(nome="Liga Alfa", sig="LA", times=12, pos=3, posA=4, wp=55, V=4, D=3, E=0,
         meu="Blue Comets", adv="Pixel Foxes", meus=0.0, advp=0.0, mproj=94.5, aproj=91.2, fin=0, ntit=9, posAdv=7),
    dict(nome="Liga Beta", sig="LB", times=10, pos=5, posA=5, wp=42, V=3, D=4, E=0,
         meu="Blue Comets", adv="Neon Owls", meus=0.0, advp=0.0, mproj=88.0, aproj=92.5, fin=0, ntit=9, posAdv=2),
]
# Histórico fictício: (liga, semana, res 0V/1D/2E, rank, V,D,E, meus, advp, adv)
HIST = [
    (0,1,0,4,1,0,0,102.4,88.1,"Pixel Foxes"), (0,2,1,5,1,1,0,79.2,91.0,"Neon Owls"),
    (0,3,0,3,2,1,0,110.5,95.2,"Solar Sharks"), (0,4,0,3,3,1,0,98.0,90.1,"Jade Dragons"),
    (0,5,1,4,3,2,0,85.4,99.0,"Iron Wolves"), (0,6,0,3,4,2,0,101.2,87.5,"Copper Hawks"),
    (0,7,1,4,4,3,0,88.44,91.26,"Silver Lynx"),
    (1,1,1,6,0,1,0,70.0,95.0,"Neon Owls"), (1,2,0,5,1,1,0,105.0,80.0,"Pixel Foxes"),
    (1,3,1,6,1,2,0,82.0,100.0,"Solar Sharks"), (1,4,0,5,2,2,0,99.5,88.0,"Jade Dragons"),
    (1,5,1,6,2,3,0,75.0,110.0,"Iron Wolves"), (1,6,0,5,3,3,0,108.0,92.0,"Copper Hawks"),
    (1,7,1,5,3,4,0,72.10,79.80,"Amber Bears"),
]

TITS_PROX = []
for li, starters in enumerate([
    [("QB","A. Nova","NE","@ MIA",0,21.5),("RB","B. River","BAL","vs BUF",0,12.0),
     ("RB","C. Stone","GB","vs CAR",0,9.5),("WR","D. Sky","DAL","vs ARI",0,14.0),
     ("WR","E. Lake","DET","vs MIN",0,16.0),("TE","F. Hill","SF","@ HOU",0,8.5),
     ("W/R","G. Park","PIT","vs NYJ",0,10.0),("K","H. Moon","SF","@ HOU",0,8.0),
     ("DEF","CAR D/ST","CAR","@ GB",0,5.0)],
    [("QB","I. Spark","WAS","@ PHI",0,18.0),("RB","J. Dash","IND","vs JAX",0,15.0),
     ("RB","K. Bolt","CIN","vs TEN",0,7.0),("WR","L. Beam","DAL","vs ARI",0,14.0),
     ("WR","M. Wave","ARI","@ DAL",0,11.0),("TE","N. Grove","PIT","vs NYJ",0,6.0),
     ("W/R","O. Field","LV","@ NYJ",0,8.0),("K","P. Kick","IND","vs JAX",0,8.0),
     ("DEF","CLE D/ST","CLE","@ NE",0,6.0)],
]):
    for lado in (0, 1):
        for slot, nome, team, adv, pts, proj in starters:
            p = pts if lado == 0 else 0
            pr = proj if lado == 0 else max(0, proj - 1.5)
            TITS_PROX.append(dict(li=li, lado=lado, st=0, pts=p, proj=pr, slot=slot, nome=nome, team=team, adv=adv))

TITS_AND = []
for li, starters in enumerate([
    [("QB","A. Nova","NE","@ CHI",28.4,24.0),("RB","B. River","BAL","vs CIN",4.8,10.5),
     ("RB","C. Stone","GB","@ DET",4.5,8.2),("WR","D. Sky","DAL","@ PHI",13.7,14.0),
     ("WR","E. Lake","DET","vs GB",23.6,18.0),("TE","F. Hill","SF","@ ATL",9.8,9.0),
     ("W/R","G. Park","PIT","@ NO",6.6,11.0),("K","H. Moon","SF","@ ATL",8.0,7.5),
     ("DEF","CAR D/ST","CAR","vs TB",-3.0,5.0)],
    [("QB","I. Spark","LV","vs LAR",20.4,18.0),("RB","J. Dash","IND","@ MIN",18.0,16.0),
     ("RB","K. Bolt","HOU","vs NYG",8.6,9.0),("WR","L. Beam","DAL","@ PHI",13.7,14.0),
     ("WR","M. Wave","ARI","vs DEN",8.6,10.0),("TE","N. Grove","PIT","@ NO",3.0,6.0),
     ("W/R","O. Field","PIT","@ NO",4.2,7.0),("K","P. Kick","IND","@ MIN",4.0,8.0),
     ("DEF","CLE D/ST","CLE","@ TEN",6.0,6.0)],
]):
    for lado in (0, 1):
        for slot, nome, team, adv, pts, proj in starters:
            p = pts if lado == 0 else max(0, pts - 2.5)
            TITS_AND.append(dict(li=li, lado=lado, st=2 if pts else 0, pts=p, proj=proj, slot=slot, nome=nome, team=team, adv=adv))

STAND = [
    (0,1,1,5,2,0,0,920.5,"Pixel Foxes","2W"),(0,2,3,5,2,0,0,880.1,"Neon Owls","1W"),
    (0,3,4,4,3,0,1,850.0,"Blue Comets","1L"),(0,4,2,4,3,0,0,840.2,"Solar Sharks","1L"),
    (0,5,5,3,4,0,0,800.0,"Jade Dragons","2L"),(0,6,6,3,4,0,0,790.4,"Iron Wolves","1W"),
    (0,7,8,3,4,0,0,770.0,"Copper Hawks","1W"),(0,8,7,2,5,0,0,740.1,"Silver Lynx","3L"),
    (0,9,9,2,5,0,0,720.0,"Amber Bears","2L"),(0,10,10,2,5,0,0,700.5,"Coral Crabs","1L"),
    (0,11,11,1,6,0,0,680.0,"Maple Moose","4L"),(0,12,12,1,6,0,0,650.2,"Quartz Quokkas","5L"),
    (1,1,1,5,2,0,0,900.0,"Neon Owls","2W"),(1,2,2,4,3,0,0,870.0,"Pixel Foxes","1W"),
    (1,3,4,4,3,0,0,860.0,"Solar Sharks","1W"),(1,4,3,3,4,0,0,830.0,"Jade Dragons","1L"),
    (1,5,5,3,4,0,1,810.0,"Blue Comets","1L"),(1,6,6,3,4,0,0,800.0,"Iron Wolves","2L"),
    (1,7,7,2,5,0,0,780.0,"Copper Hawks","2L"),(1,8,8,2,5,0,0,760.0,"Silver Lynx","3L"),
    (1,9,9,2,5,0,0,740.0,"Amber Bears","1L"),(1,10,10,1,6,0,0,700.0,"Coral Crabs","4L"),
]

GAMES_PROX = [
    dict(st=0, sa=0, sh=0, mask=3, away="CAR", home="GB", tv="Prime"),
    dict(st=0, sa=0, sh=0, mask=1, away="BAL", home="BUF", tv="CBS"),
    dict(st=0, sa=0, sh=0, mask=2, away="WAS", home="PHI", tv="FOX"),
    dict(st=0, sa=0, sh=0, mask=3, away="DAL", home="ARI", tv="FOX"),
    dict(st=0, sa=0, sh=0, mask=0, away="SF", home="HOU", tv="FOX"),
    dict(st=0, sa=0, sh=0, mask=2, away="LV", home="NYJ", tv="CBS"),
]
GAMES_AND = [
    dict(st=2, sa=24, sh=17, mask=3, away="NE", home="CHI", tv="CBS"),
    dict(st=2, sa=20, sh=27, mask=1, away="BAL", home="CIN", tv="FOX"),
    dict(st=2, sa=14, sh=31, mask=1, away="GB", home="DET", tv="FOX"),
    dict(st=2, sa=17, sh=21, mask=3, away="DAL", home="PHI", tv="NBC"),
    dict(st=2, sa=10, sh=24, mask=0, away="SF", home="ATL", tv="FOX"),
    dict(st=0, sa=0, sh=0, mask=2, away="LV", home="LAR", tv="Prime"),
]

def main(path, simular=False):
    u16 = lambda v: max(0, min(65535, round(v)))
    now_dt = datetime.now(BRT)
    if simular:
        # "andamento" mid-week 7 (legado de teste)
        d = now_dt.replace(hour=15, minute=20, second=0, microsecond=0)
        now = palm_secs(d); estado = EST_ANDAMENTO; semana = 7; sim_flag = 1
        ligas = [
            dict(nome="Liga Alfa", sig="LA", times=12, pos=3, posA=4, wp=62, V=4, D=2, E=0,
                 meu="Blue Comets", adv="Pixel Foxes", meus=88.44, advp=81.20, mproj=95.5, aproj=90.1, fin=6, ntit=9, posAdv=7),
            dict(nome="Liga Beta", sig="LB", times=10, pos=5, posA=5, wp=41, V=3, D=3, E=0,
                 meu="Blue Comets", adv="Neon Owls", meus=72.10, advp=79.80, mproj=85.0, aproj=88.2, fin=5, ntit=9, posAdv=2),
        ]
        tits, games = TITS_AND, GAMES_AND
        hist = [h for h in HIST if h[1] <= 6]
        base = datetime(2026, 10, 25, 14, 0, tzinfo=BRT)
    else:
        d = (now_dt + timedelta(days=(1 - now_dt.weekday()) % 7 or 7)).replace(hour=8, minute=0, second=0, microsecond=0)
        # terça 08h — próxima rodada
        now = palm_secs(datetime(2026, 10, 28, 8, 8, tzinfo=BRT))
        estado = EST_PROXIMA; semana = 8; sim_flag = 0
        ligas = LIGAS; tits, games = TITS_PROX, GAMES_PROX
        hist = HIST
        base = datetime(2026, 10, 29, 21, 15, tzinfo=BRT)

    L_out, P_out, T_out, G_out, H_out = [], [], [], [], []
    for li, L in enumerate(ligas):
        L_out.append(
            s(L["nome"], 20) + s(L["sig"], 4) +
            struct.pack(">BBBBBBBB", L["times"], L["pos"], L["posA"], L["wp"], L["V"], L["D"], L["E"], 1) +
            struct.pack(">HHHHBBBB", u16(L["meus"]*100), u16(L["advp"]*100), u16(L["mproj"]*10), u16(L["aproj"]*10),
                        L["fin"], L["ntit"], L["posAdv"], 0) +
            s(L["meu"], 26) + s(L["adv"], 26)
        )
    for t in tits:
        P_out.append(
            struct.pack(">BBBBHH", t["li"], t["lado"], t["st"], 0, u16(t["pts"]*100), u16(t["proj"]*10)) +
            s(t["slot"], 4) + s(t["nome"], 16) + s(t["team"], 4) + s(t["adv"], 8)
        )
    for row in STAND:
        liga, pos, posA, V, D, E, me, pf, team, seq = row
        T_out.append(struct.pack(">BBBBBBBBI", liga, pos, posA, V, D, E, me, 0, round(pf*100)) + s(team, 20) + s(seq, 4))
    for i, g in enumerate(games):
        t = palm_secs(base + timedelta(hours=i * 3))
        G_out.append(struct.pack(">IBBBB", t, g["st"], g["sa"], g["sh"], g["mask"]) + s(g["away"], 4) + s(g["home"], 4) + s(g["tv"], 8))
    for liga, semana_h, res, rank, V, D, E, meus, advp, adv in hist:
        H_out.append(struct.pack(">BBBBBBBBHH", liga, semana_h, res, rank, V, D, E, 0, u16(meus*100), u16(advp*100)) + s(adv, 26) + b"\0\0")

    n_hist = len(H_out)
    rec0 = b"FNT2" + struct.pack(">HIBBBBHH", 2, now, semana, estado, len(L_out), len(G_out), len(P_out), len(T_out))
    rec0 += s("2026", 6) + s("demo", 20) + bytes([sim_flag, n_hist])
    rec0 += b"\0" * (64 - len(rec0))
    assert len(rec0) == 64 and all(len(x) == 40 for x in H_out)
    recs = [rec0, b"".join(L_out), b"".join(P_out), b"".join(T_out), b"".join(G_out), b"".join(H_out) or b"\0"]
    write_pdb(path, recs, now)
    est_txt = "próxima" if estado == EST_PROXIMA else "andamento"
    print(f"{path}: demo FNT2 semana {semana} ({est_txt}), {len(L_out)} ligas, hist={n_hist}, usuario=demo", file=sys.stderr)

if __name__ == "__main__":
    a = sys.argv[1:]; sim = "--simular-fim" in a
    if sim: a.remove("--simular-fim")
    main(a[0] if a else "FantasyDados-demo.pdb", sim)
