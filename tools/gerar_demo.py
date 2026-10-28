#!/usr/bin/env python3
"""Gera um FantasyDados.pdb de DEMONSTRAÇÃO com nomes fictícios (sem rede, sem Sleeper).
Uso: python3 tools/gerar_demo.py [saida.pdb] [--simular-fim]
"""
import os, struct, sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

BRT = ZoneInfo("America/Sao_Paulo")
EPOCH = datetime(1904, 1, 1)
CREATOR, TYPE, DBNAME = b"FNFL", b"DATA", "FantasyDados"

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

# --- dados fictícios ---
LIGAS = [
    dict(nome="Liga Alfa", sig="LA", times=12, pos=3, posA=4, wp=62, V=4, D=2, E=0,
         meu="Blue Comets", adv="Pixel Foxes", meus=88.44, advp=81.20, mproj=95.5, aproj=90.1, fin=6, ntit=9, posAdv=7),
    dict(nome="Liga Beta", sig="LB", times=10, pos=5, posA=5, wp=41, V=3, D=3, E=0,
         meu="Blue Comets", adv="Neon Owls", meus=72.10, advp=79.80, mproj=85.0, aproj=88.2, fin=5, ntit=9, posAdv=2),
]
# titulares (liga, lado 0/1, st, pts, proj, slot, nome, team, adv)
TITS = []
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
    for lado, team_key in ((0, "meu"), (1, "adv")):
        for slot, nome, team, adv, pts, proj in starters:
            # lado adv: mirror with slight score change
            p = pts if lado == 0 else max(0, pts - 2.5)
            TITS.append(dict(li=li, lado=lado, st=2, pts=p, proj=proj, slot=slot, nome=nome, team=team, adv=adv))

STAND = [
    # liga, pos, posA, V, D, E, me, pf, team, seq
    (0,1,1,5,1,0,0,920.5,"Pixel Foxes","5W"),(0,2,3,5,1,0,0,880.1,"Neon Owls","3W"),
    (0,3,4,4,2,0,1,850.0,"Blue Comets","2W"),(0,4,2,4,2,0,0,840.2,"Solar Sharks","1L"),
    (0,5,5,3,3,0,0,800.0,"Jade Dragons","1W"),(0,6,6,3,3,0,0,790.4,"Iron Wolves","2L"),
    (0,7,8,3,3,0,0,770.0,"Copper Hawks","1W"),(0,8,7,2,4,0,0,740.1,"Silver Lynx","3L"),
    (0,9,9,2,4,0,0,720.0,"Amber Bears","2L"),(0,10,10,2,4,0,0,700.5,"Coral Crabs","1L"),
    (0,11,11,1,5,0,0,680.0,"Maple Moose","4L"),(0,12,12,1,5,0,0,650.2,"Quartz Quokkas","5L"),
    (1,1,1,5,1,0,0,900.0,"Neon Owls","4W"),(1,2,2,4,2,0,0,870.0,"Pixel Foxes","2W"),
    (1,3,4,4,2,0,0,860.0,"Solar Sharks","1W"),(1,4,3,3,3,0,0,830.0,"Jade Dragons","1L"),
    (1,5,5,3,3,0,1,810.0,"Blue Comets","1L"),(1,6,6,3,3,0,0,800.0,"Iron Wolves","2L"),
    (1,7,7,2,4,0,0,780.0,"Copper Hawks","2L"),(1,8,8,2,4,0,0,760.0,"Silver Lynx","3L"),
    (1,9,9,2,4,0,0,740.0,"Amber Bears","1L"),(1,10,10,1,5,0,0,700.0,"Coral Crabs","4L"),
]

GAMES = [
    # t will be filled; st 2=final, sa, sh, mask, away, home, tv
    dict(st=2, sa=24, sh=17, mask=3, away="NE", home="CHI", tv="CBS"),
    dict(st=2, sa=20, sh=27, mask=1, away="BAL", home="CIN", tv="FOX"),
    dict(st=2, sa=14, sh=31, mask=1, away="GB", home="DET", tv="FOX"),
    dict(st=2, sa=17, sh=21, mask=3, away="DAL", home="PHI", tv="NBC"),
    dict(st=2, sa=10, sh=24, mask=0, away="SF", home="ATL", tv="FOX"),
    dict(st=0, sa=0, sh=0, mask=2, away="LV", home="LAR", tv="Prime"),
]

def main(path, simular=False):
    now_dt = datetime.now(BRT)
    if simular:
        d = now_dt + timedelta(days=(1 - now_dt.weekday()) % 7 or 7)
        d = d.replace(hour=8, minute=0, second=0, microsecond=0)
        now = palm_secs(d)
        estado = 1
        for L in LIGAS:
            L["wp"] = 0 if L["meus"] < L["advp"] else 100
            L["fin"] = L["ntit"]
    else:
        now = palm_secs(now_dt)
        estado = 0
    semana = 7
    L_out, P_out, T_out, G_out = [], [], [], []
    u16 = lambda v: max(0, min(65535, round(v)))
    for li, L in enumerate(LIGAS):
        L_out.append(
            s(L["nome"], 20) + s(L["sig"], 4) +
            struct.pack(">BBBBBBBB", L["times"], L["pos"], L["posA"], L["wp"], L["V"], L["D"], L["E"], 1) +
            struct.pack(">HHHHBBBB", u16(L["meus"]*100), u16(L["advp"]*100), u16(L["mproj"]*10), u16(L["aproj"]*10),
                        L["fin"], L["ntit"], L["posAdv"], 0) +
            s(L["meu"], 26) + s(L["adv"], 26)
        )
    for t in TITS:
        st = 2 if (simular or t["st"] == 2) else t["st"]
        P_out.append(
            struct.pack(">BBBBHH", t["li"], t["lado"], st, 0, u16(t["pts"]*100), u16(t["proj"]*10)) +
            s(t["slot"], 4) + s(t["nome"], 16) + s(t["team"], 4) + s(t["adv"], 8)
        )
    for row in STAND:
        liga, pos, posA, V, D, E, me, pf, team, seq = row
        T_out.append(struct.pack(">BBBBBBBBI", liga, pos, posA, V, D, E, me, 0, round(pf*100)) + s(team, 20) + s(seq, 4))
    base = datetime(2026, 10, 25, 14, 0, tzinfo=BRT)
    for i, g in enumerate(GAMES):
        st = 2 if simular else g["st"]
        t = palm_secs(base + timedelta(hours=i*3))
        G_out.append(struct.pack(">IBBBB", t, st, g["sa"], g["sh"], g["mask"]) + s(g["away"], 4) + s(g["home"], 4) + s(g["tv"], 8))

    rec0 = b"FNT1" + struct.pack(">HIBBBBHH", 1, now, semana, estado, len(L_out), len(G_out), len(P_out), len(T_out))
    rec0 += s("2026", 6) + s("demo", 20) + bytes([1 if simular else 0])
    rec0 += b"\0" * (64 - len(rec0))
    assert len(rec0) == 64
    recs = [rec0, b"".join(L_out), b"".join(P_out), b"".join(T_out), b"".join(G_out)]
    write_pdb(path, recs, now)
    print(f"{path}: demo semana {semana} ({'encerrada' if estado else 'andamento'}), {len(L_out)} ligas, usuario=demo", file=sys.stderr)

if __name__ == "__main__":
    a = sys.argv[1:]; sim = "--simular-fim" in a
    if sim: a.remove("--simular-fim")
    main(a[0] if a else "FantasyDados-demo.pdb", sim)
