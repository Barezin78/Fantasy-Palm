#!/usr/bin/env python3
"""Confere a estrutura do Fantasy.prc e do FantasyDados.pdb (cabeçalho Palm, recursos, tamanhos dos registros)."""
import struct, sys, datetime as d
def hdr(b):
    name = b[:32].split(b"\0")[0].decode("cp1252"); attr, ver = struct.unpack(">HH", b[32:36])
    typ, cre = b[60:64].decode(), b[64:68].decode(); n = struct.unpack(">H", b[76:78])[0]
    return name, attr, typ, cre, n
def prc(path):
    b = open(path, "rb").read(); name, attr, typ, cre, n = hdr(b)
    assert attr & 1, "PRC sem atributo de recurso"
    res = []
    for i in range(n):
        e = b[78 + 10 * i: 88 + 10 * i]; res.append((e[:4].decode(), struct.unpack(">H", e[4:6])[0], struct.unpack(">I", e[6:10])[0]))
    ver = next((b[o:o + 16].split(b"\0")[0].decode() for t, i, o in res if t == "tver"), "?")
    print(f"{path}: '{name}' tipo {typ} criador {cre}, versão {ver}, {n} recursos: " + " ".join(sorted({f'{t}' for t, _, _ in res})))
    assert typ == "appl" and cre == "FNFL"
    for need in ("code", "data", "tFRM", "MBAR", "Talt", "tAIB", "tAIN", "tver"): assert any(t == need for t, _, _ in res), need
def pdb(path):
    b = open(path, "rb").read(); name, attr, typ, cre, n = hdr(b)
    offs = [struct.unpack(">I", b[78 + 8 * i: 82 + 8 * i])[0] for i in range(n)] + [len(b)]
    recs = [b[offs[i]:offs[i + 1]] for i in range(n)]
    assert typ == "DATA" and cre == "FNFL" and name == "FantasyDados", (name, typ, cre)
    m = recs[0]
    assert m[:4] in (b"FNT1", b"FNT2") and len(m) == 64
    if m[:4] == b"FNT1":
        assert n == 5
        ver, sync, sem, est, nl, ng, npl, nr = struct.unpack(">HIBBBBHH", m[4:18])
        assert len(recs[1]) == 96 * nl
        print(f"{path}: FNT1 (legado) semana {sem}")
        return
    assert n == 6, n
    ver, sync, sem, est, nl, ng, npl, nr = struct.unpack(">HIBBBBHH", m[4:18])
    nh = m[45]
    assert len(recs[1]) in (96 * nl, 1) and len(recs[2]) in (40 * npl, 1)
    assert len(recs[3]) in (36 * nr, 1) and len(recs[4]) in (24 * ng, 1)
    assert len(recs[5]) in (40 * nh, 1), (len(recs[5]), nh)
    t = d.datetime(1904, 1, 1) + d.timedelta(seconds=sync)
    est_txt = {0: "em andamento", 1: "encerrada", 2: "próxima"}.get(est, str(est))
    ligas = [recs[1][i * 96:i * 96 + 20].split(b"\0")[0].decode("cp1252") for i in range(nl)] if nl else []
    print(f"{path}: OK FNT2 — sync {t:%d/%m/%Y %H:%M} (Brasília), semana {sem} {est_txt}{' SIMULADO' if m[44] else ''}, "
          f"ligas {ligas}, {npl} titulares, {nr} tabela, {ng} jogos, {nh} histórico")
for p in sys.argv[1:]: (prc if p.endswith(".prc") else pdb)(p)
