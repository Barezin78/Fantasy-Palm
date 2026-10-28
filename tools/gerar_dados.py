#!/usr/bin/env python3
"""Gera FantasyDados.pdb (Palm OS) com o resumo da rodada do Sleeper + jogos da NFL (ESPN).

Uso:
  python3 tools/gerar_dados.py [saida.pdb] --usuario SEU_USUARIO [--ligas "Liga A,Liga B"] [--simular-fim]
  python3 tools/gerar_dados.py [saida.pdb] --config /caminho/config.json [--simular-fim]

Config (JSON): { "usuario": "...", "ligas": ["Liga A", "Liga B"], "siglas": {"Liga A": "LA"} }
Também lê FANTASY_CONFIG (caminho) ou config.local.json no diretório do projeto.
--usuario é obrigatório se não houver config. Sem default pessoal no código.

  --simular-fim: só p/ teste. Finge que a rodada acabou (cada titular faz o maior entre o parcial e a projeção),
                 marca o .pdb como SIMULADO e põe o sync na terça seguinte, 08h00.
Sem rede no Palm: o .pdb é uma "foto" do momento em que você roda isto (horário de Brasília).
Não baixa a lista inteira de jogadores (/players/nfl, ~15 MB): os nomes vêm das projeções da semana.
Só se algum titular não aparecer nas projeções ele baixa a lista uma vez e guarda aparada em
~/.cache/fantasy-palm/jogadores.json (vale 7 dias).

Formato (big-endian). Todos os textos em CP1252, terminados em zero.
  rec0 meta   (64): 'FNT1', u16 versão=1, u32 sync (seg. Palm, horário de Brasília), u8 semana, u8 estado (0 andamento, 1 encerrada),
                    u8 nLigas, u8 nJogos, u16 nJogadores, u16 nTabela, char temporada[6], char usuario[20], u8 simulado, pad
  rec1 ligas  (96 cada): char nome[20], char sigla[4], u8 times, u8 pos, u8 posAnterior (0 = sem), u8 vitoria% (255 = sem),
                    u8 V, u8 D, u8 E, u8 temAdversario, u16 meusPts*100, u16 ptsAdv*100, u16 minhaProj*10, u16 projAdv*10,
                    u8 titularesEncerrados, u8 nTitulares, u8 posAdv, u8 pad, char meuTime[26], char timeAdv[26]
  rec2 titulares (40 cada): u8 liga, u8 lado (0 eu, 1 adv), u8 estado (0 a jogar, 1 em andamento no sync, 2 final, 3 bye),
                    u8 lesão (letra ou 0), u16 pts*100, u16 proj*10, char slot[4], char nome[16], char time[4], char adv[8]
  rec3 tabela (36 cada): u8 liga, u8 pos, u8 posAnterior, u8 V, u8 D, u8 E, u8 souEu, u8 pad, u32 PF*100, char time[20], char seq[4]
  rec4 jogos  (24 cada): u32 início (seg. Palm, Brasília), u8 estado (0 pre, 1 andamento, 2 final), u8 pontosFora, u8 pontosCasa,
                    u8 máscara (bit i = liga i tem titular meu), char fora[4], char casa[4], char tv[8]
"""
import json, math, os, struct, sys, time, urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

API = "https://api.sleeper.app/v1"
BRT = ZoneInfo("America/Sao_Paulo")
EPOCH = datetime(1904, 1, 1)
CREATOR, TYPE, DBNAME = b"FNFL", b"DATA", "FantasyDados"
DESVIO_POR_PONTO = 0.55          # igual ao widget (Fantasy.js)
NORM = {"WSH": "WAS", "JAC": "JAX"}
CACHE = os.path.expanduser("~/.cache/fantasy-palm")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def load_cfg(path=None):
    """Lê config JSON: --config, FANTASY_CONFIG, config.local.json (nesta ordem de tentativa se path=None)."""
    cands = []
    if path: cands.append(path)
    else:
        env = os.environ.get("FANTASY_CONFIG")
        if env: cands.append(env)
        cands.append(os.path.join(ROOT, "config.local.json"))
    for p in cands:
        if p and os.path.isfile(p):
            with open(p, encoding="utf-8") as f:
                return json.load(f), p
    return {}, None

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 FantasyPalm/1.0"})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

def palm_secs(dt_utc):
    return int((dt_utc.astimezone(BRT).replace(tzinfo=None) - EPOCH).total_seconds())

def limpa(t):
    return (t or "").replace("“", '"').replace("”", '"').replace("’", "'").replace("‘", "'").strip()

def s(txt, n):
    b = limpa(txt).encode("cp1252", "replace")[: n - 1]
    return b + b"\0" * (n - len(b))

def phi(z):  # mesma aproximação do widget
    t = 1 / (1 + 0.3275911 * abs(z))
    y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * math.exp(-z * z / 2)
    return (1 + y) / 2 if z >= 0 else (1 - y) / 2

def jogadores_aparados():
    p = os.path.join(CACHE, "jogadores.json")
    if os.path.exists(p) and time.time() - os.path.getmtime(p) < 7 * 86400:
        return json.load(open(p))
    print("baixando /players/nfl (só desta vez, guarda aparado)...", file=sys.stderr)
    full = get(API + "/players/nfl"); o = {}
    for pid, x in full.items():
        if x and x.get("position") in ("QB", "RB", "WR", "TE", "K", "DEF"):
            o[pid] = [x.get("first_name") or "", x.get("last_name") or "", x.get("position"), x.get("team") or ""]
    os.makedirs(CACHE, exist_ok=True); json.dump(o, open(p, "w"))
    return o

def espn_semana(temp, sem, tipo):
    j = get(f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={temp}&seasontype={3 if tipo == 'post' else 2}&week={sem}")
    jogos, times = [], {}
    for e in j.get("events", []):
        c = e["competitions"][0]; st = (c.get("status") or {}).get("type", {}).get("state", "pre")
        dt = datetime.fromisoformat(e["date"].replace("Z", "+00:00"))
        comp = {x["homeAway"]: x for x in c["competitors"]}
        ab = lambda x: NORM.get(x["team"]["abbreviation"], x["team"]["abbreviation"])
        sc = lambda x: int(float(x.get("score") or 0))
        tv = ((c.get("broadcasts") or [{}])[0].get("names") or [""])[0]
        stt = c.get("status") or {}; frac = 0.0
        if st == "in":
            per = min(4, stt.get("period") or 1); rel = max(0, min(900, float(stt.get("clock") or 0)))
            frac = min(1, ((per - 1) * 900 + (900 - rel)) / 3600)
        g = dict(frac=frac, t=palm_secs(dt), st={"pre": 0, "in": 1, "post": 2}.get(st, 0), away=ab(comp["away"]), home=ab(comp["home"]),
                 sa=sc(comp["away"]), sh=sc(comp["home"]), tv=tv.replace("Prime Video", "Prime").replace("NFL Net", "NFL Net"), mask=0)
        jogos.append(g)
        times[g["away"]] = (g, "@ " + g["home"]); times[g["home"]] = (g, "vs " + g["away"])
    jogos.sort(key=lambda g: g["t"])
    return jogos, times

def main(path, usuario, simular=False, ordem=None, siglas=None):
    est = get(API + "/state/nfl")
    temp, tipo = str(est["season"]), est.get("season_type", "regular")
    sem = int(est.get("display_week") or est.get("week") or 1)
    usr = get(f"{API}/user/{usuario}")
    if not usr: sys.exit(f"usuário {usuario} não encontrado no Sleeper")
    uid = usr["user_id"]
    ligas = get(f"{API}/user/{uid}/leagues/nfl/{temp}") or []
    ordem = list(ordem or [])
    siglas = dict(siglas or {})
    if ordem:
        # mantém só as ligas pedidas (match por substring no nome), na ordem do config
        escolhidas = []
        for o in ordem:
            hit = next((l for l in ligas if o.lower() in (l.get("name") or "").lower()), None)
            if hit and hit not in escolhidas: escolhidas.append(hit)
        ligas = escolhidas
    else:
        ligas.sort(key=lambda l: l["name"])
    ligas = ligas[:4]
    tp = "post" if tipo == "post" else "regular"
    proj = {e["player_id"]: e for e in get(f"https://api.sleeper.app/projections/nfl/{temp}/{sem}?season_type={tp}" +
            "".join(f"&position%5B%5D={p}" for p in ("QB", "RB", "WR", "TE", "K", "DEF")))}
    jogos, times = espn_semana(temp, sem, tp)
    if simular:
        for g in jogos:
            if g["st"] != 2: g["sa"] = g["sh"] = 255   # sem placar inventado
            g["st"] = 2
    encerrada = bool(jogos) and all(g["st"] == 2 for g in jogos)
    nomes = None
    L_out, P_out, T_out = [], [], []

    for li, lg in enumerate(ligas):
        lid = lg["league_id"]; nome = limpa(lg["name"])
        rec = (lg.get("scoring_settings") or {}).get("rec", 0.5)
        chave = {1: "pts_ppr", 0.5: "pts_half_ppr", 0: "pts_std"}.get(rec, "pts_half_ppr")
        us = {u["user_id"]: u for u in get(f"{API}/league/{lid}/users")}
        rs = get(f"{API}/league/{lid}/rosters")
        ms = get(f"{API}/league/{lid}/matchups/{sem}") or []
        if simular:
            rec_ = (lg.get("scoring_settings") or {}).get("rec", 0.5); ch_ = {1: "pts_ppr", 0.5: "pts_half_ppr", 0: "pts_std"}.get(rec_, "pts_half_ppr")
            for m in ms:
                sp = [max(float(a or 0), float(((proj.get(pid) or {}).get("stats") or {}).get(ch_) or 0)) for pid, a in zip(m.get("starters") or [], m.get("starters_points") or [])]
                m["starters_points"] = sp; m["points"] = round(sum(sp), 2)
        slots = [p for p in lg.get("roster_positions", []) if p not in ("BN", "IR", "TAXI")]
        tname = lambda r: limpa((us.get(r["owner_id"], {}).get("metadata") or {}).get("team_name") or us.get(r["owner_id"], {}).get("display_name") or f"Time {r['roster_id']}")
        pf = lambda st: st.get("fpts", 0) + st.get("fpts_decimal", 0) / 100
        tab = {r["roster_id"]: dict(rid=r["roster_id"], team=tname(r), w=r["settings"].get("wins", 0), l=r["settings"].get("losses", 0),
                                    t=r["settings"].get("ties", 0), pf=pf(r["settings"]), seq=(r.get("metadata") or {}).get("streak") or "",
                                    me=r["owner_id"] == uid or uid in (r.get("co_owners") or [])) for r in rs}
        contadas = max((x["w"] + x["l"] + x["t"]) for x in tab.values()) if tab else 0
        mm = {m["roster_id"]: m for m in ms}

        def aplica(semana_ms, sinal):
            """soma (+1) ou desfaz (-1) o resultado de uma semana na tabela"""
            by = {}
            for m in semana_ms:
                if m.get("matchup_id") is not None: by.setdefault(m["matchup_id"], []).append(m)
            for par in by.values():
                if len(par) != 2: continue
                a, b = par
                for x, y in ((a, b), (b, a)):
                    T = tab.get(x["roster_id"])
                    if not T: continue
                    px, py = x.get("points") or 0, y.get("points") or 0
                    k = "w" if px > py else "l" if px < py else "t"
                    T[k] += sinal; T["pf"] += sinal * px
                    if sinal > 0:
                        c = {"w": "W", "l": "L", "t": "T"}[k]; sq = T["seq"]
                        T["seq"] = f"{int(sq[:-1]) + 1}{c}" if sq.endswith(c) and sq[:-1].isdigit() else f"1{c}"
        ordem = lambda: [x["rid"] for x in sorted(tab.values(), key=lambda x: (-x["w"], -x["pf"]))]
        if encerrada and contadas < sem and ms:      # rodada acabou mas o Sleeper ainda não somou: soma aqui
            ant = {rid: i + 1 for i, rid in enumerate(ordem())}
            aplica(ms, +1)
        elif contadas >= 1:                          # posição anterior = antes da última semana somada
            aplica(get(f"{API}/league/{lid}/matchups/{contadas}") or [], -1)
            ant = {rid: i + 1 for i, rid in enumerate(ordem())}
            aplica(get(f"{API}/league/{lid}/matchups/{contadas}") or [], +1)
            for x in tab.values():                   # aplica(+1) recalcula a sequência: volta a do Sleeper
                x["seq"] = next(((r.get("metadata") or {}).get("streak") or "" for r in rs if r["roster_id"] == x["rid"]), "")
        else:
            ant = {}
        pos = {rid: i + 1 for i, rid in enumerate(ordem())}
        for rid in ordem():
            x = tab[rid]
            T_out.append(struct.pack(">BBBBBBBBI", li, pos[rid], ant.get(rid, 0), x["w"], x["l"], x["t"], 1 if x["me"] else 0, 0, round(x["pf"] * 100)) + s(x["team"], 20) + s(x["seq"], 4))

        meu = next((r for r in rs if tab[r["roster_id"]]["me"]), None)
        if not meu: continue
        def lado(rid, ladoN):
            nonlocal nomes
            m = mm.get(rid) or {}; pts_l = m.get("starters_points") or []
            tot = 0; resta = 0; vr = 0; fin = 0; tit = []
            for i, pid in enumerate(m.get("starters") or []):
                pts = float(pts_l[i]) if i < len(pts_l) and pts_l[i] is not None else 0.0
                e = proj.get(pid); pl = (e or {}).get("player") or {}
                first, last, posi, team = pl.get("first_name", ""), pl.get("last_name", ""), pl.get("position", ""), (e or {}).get("team") or pl.get("team") or ""
                inj = pl.get("injury_status") or ""
                if pid != "0" and not last and not pid.isalpha():
                    nomes = nomes or jogadores_aparados()
                    n = nomes.get(pid) or ["", f"#{pid}", "", ""]; first, last, posi, team = n[0], n[1], posi or n[2], team or n[3]
                if pid.isalpha(): nm, team, posi = f"{pid} D/ST", team or pid, "DEF"
                elif pid == "0": nm = "(vazio)"
                else: nm = f"{first[:1]}. {last}" if first else last
                pr = float(((e or {}).get("stats") or {}).get(chave) or 0)
                g = times.get(NORM.get(team, team))
                if pid == "0": st, adv = 3, ""
                elif not g: st, adv = 3, "BYE"
                else: st, adv = {0: 0, 1: 1, 2: 2}[g[0]["st"]], g[1]
                if g and pid != "0": g[0]["mask"] |= (1 << li) if ladoN == 0 else 0
                frac = g[0]["frac"] if g and st == 1 else 0   # fração jogada: só p/ projeção/% (o app não mostra relógio)
                r_ = pr if st == 0 else pr * (1 - frac) if st == 1 else 0
                resta += r_; vr += (DESVIO_POR_PONTO * r_) ** 2; fin += st == 2; tot += pts
                sl = slots[i] if i < len(slots) else "FLEX"
                sl = {"FLEX": "W/R", "SUPER_FLEX": "SF", "REC_FLEX": "W/T", "WRRB_FLEX": "W/R", "IDP_FLEX": "IDP"}.get(sl, sl)
                tit.append(dict(slot=sl, nome=nm, team=team, adv=adv, st=st, pts=pts, proj=pr,
                                inj=(inj[:1].upper() if inj and inj.lower() not in ("active", "na") else "")))
            pts = float(m["points"]) if isinstance(m.get("points"), (int, float)) else tot
            return dict(rid=rid, team=tab[rid]["team"], pts=pts, proj=pts + resta, vr=vr, fin=fin, tit=tit, mid=m.get("matchup_id"))
        eu = lado(meu["roster_id"], 0)
        opp_m = next((m for m in ms if eu["mid"] is not None and m.get("matchup_id") == eu["mid"] and m["roster_id"] != meu["roster_id"]), None)
        ad = lado(opp_m["roster_id"], 1) if opp_m else None
        wp = 255
        if ad:
            sd = math.sqrt(eu["vr"] + ad["vr"]); d = eu["proj"] - ad["proj"]
            wp = round(100 * ((1 if d > 0 else 0 if d < 0 else 0.5) if sd < 0.5 else phi(d / sd)))
        me = tab[meu["roster_id"]]
        sig = siglas.get(nome) or "".join(w[0] for w in nome.split())[:3].upper()
        u16 = lambda v: max(0, min(65535, round(v)))
        L_out.append(s(nome, 20) + s(sig, 4) + struct.pack(">BBBBBBBB", lg.get("total_rosters") or len(rs), pos[meu["roster_id"]], ant.get(meu["roster_id"], 0), wp,
                     me["w"], me["l"], me["t"], 1 if ad else 0) +
                     struct.pack(">HHHHBBBB", u16(eu["pts"] * 100), u16((ad or eu)["pts"] * 100 if ad else 0), u16(eu["proj"] * 10), u16(ad["proj"] * 10 if ad else 0),
                                 eu["fin"], len(eu["tit"]), pos.get(ad["rid"], 0) if ad else 0, 0) + s(eu["team"], 26) + s(ad["team"] if ad else "", 26))
        for ladoN, T in ((0, eu), (1, ad)):
            if not T: continue
            for p in T["tit"]:
                P_out.append(struct.pack(">BBBBHH", li, ladoN, p["st"], ord(p["inj"]) if p["inj"] else 0, u16(p["pts"] * 100), u16(p["proj"] * 10)) +
                             s(p["slot"], 4) + s(p["nome"], 16) + s(p["team"], 4) + s(p["adv"], 8))
        print(f"  {nome}: {eu['team']} {eu['pts']:.2f} x {ad['pts'] if ad else 0:.2f}  proj {eu['proj']:.1f} x {ad['proj'] if ad else 0:.1f}  {wp}%  "
              f"{me['w']}-{me['l']} {pos[meu['roster_id']]}º (antes {ant.get(meu['roster_id'], '-')})", file=sys.stderr)

    G_out = [struct.pack(">IBBBB", g["t"], g["st"], min(g["sa"], 255), min(g["sh"], 255), g["mask"]) + s(g["away"], 4) + s(g["home"], 4) + s(g["tv"], 8) for g in jogos]
    now = palm_secs(datetime.now(timezone.utc))
    if simular:   # terça seguinte, 08h00 (Brasília)
        d = datetime.now(BRT); from datetime import timedelta
        d = (d + timedelta(days=(1 - d.weekday()) % 7 or 7)).replace(hour=8, minute=0, second=0, microsecond=0)
        now = int((d.replace(tzinfo=None) - EPOCH).total_seconds())
    rec0 = b"FNT1" + struct.pack(">HIBBBBHH", 1, now, sem, 1 if encerrada else 0, len(L_out), len(G_out), len(P_out), len(T_out)) + s(temp, 6) + s(usuario, 20) + bytes([1 if simular else 0])
    rec0 += b"\0" * (64 - len(rec0))
    recs = [rec0, b"".join(L_out) or b"\0", b"".join(P_out) or b"\0", b"".join(T_out) or b"\0", b"".join(G_out) or b"\0"]
    assert len(rec0) == 64 and all(len(x) == 96 for x in L_out) and all(len(x) == 40 for x in P_out) and all(len(x) == 36 for x in T_out) and all(len(x) == 24 for x in G_out)
    write_pdb(path, recs, now)
    print(f"{path}: semana {sem} ({'encerrada' if encerrada else 'em andamento'}), {len(L_out)} ligas, {len(P_out)} titulares, {len(T_out)} linhas de tabela, {len(G_out)} jogos", file=sys.stderr)

def write_pdb(path, recs, ts):
    n = len(recs); off = 78 + 8 * n + 2
    hdr = s(DBNAME, 32) + struct.pack(">HHIIIIII", 0x0008, 1, ts, ts, 0, 0, 0, 0) + TYPE + CREATOR + struct.pack(">IIH", 0, 0, n)
    ent = b""
    for i, r in enumerate(recs):
        ent += struct.pack(">IB", off, 0) + (0x6F0000 + i).to_bytes(3, "big"); off += len(r)
    with open(path, "wb") as f:
        f.write(hdr + ent + b"\0\0" + b"".join(recs))

if __name__ == "__main__":
    a = sys.argv[1:]
    sim = "--simular-fim" in a
    if sim: a.remove("--simular-fim")
    cfg_path = None
    if "--config" in a:
        i = a.index("--config"); cfg_path = a[i + 1]; del a[i:i + 2]
    cfg, used = load_cfg(cfg_path)
    u = (cfg.get("usuario") or "").strip()
    ordem = list(cfg.get("ligas") or [])
    siglas = dict(cfg.get("siglas") or {})
    if "--usuario" in a:
        i = a.index("--usuario"); u = a[i + 1]; del a[i:i + 2]
    if "--ligas" in a:
        i = a.index("--ligas"); ordem = [x.strip() for x in a[i + 1].split(",") if x.strip()]; del a[i:i + 2]
    if not u:
        sys.exit("Informe o usuário do Sleeper: --usuario SEU_USUARIO\nou um config JSON (--config / FANTASY_CONFIG / config.local.json).\nVeja config.example.json.")
    if used: print(f"config: {used}", file=sys.stderr)
    main(a[0] if a else "FantasyDados.pdb", u, sim, ordem=ordem, siglas=siglas)
