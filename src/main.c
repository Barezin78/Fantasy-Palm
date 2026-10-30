/* Fantasy 1.1.2 — resumo da rodada do Sleeper para Palm OS 5 (Tungsten T3, 320x480 / 320x320)
 * Sem rede e sem "ao vivo": mostra a foto do último sync (FantasyDados.pdb).
 * Fonte em UTF-8; o Makefile converte para CP1252 (codificação do Palm OS) antes de compilar. */
#include <PalmOS.h>
#include <PenInputMgr.h>
#include "resource.h"

#define CRID      'FNFL'
#define DATA_TYPE 'DATA'

/* ---------- dados (ver tools/gerar_dados.py) ---------- */
typedef struct { Char name[20], sig[4]; UInt8 nt, rank, prev, wp, w, l, t, hasOpp; UInt16 pts, opts, proj, oproj;
                 UInt8 fin, ntit, orank; Char me[26], opp[26]; } League;
typedef struct { UInt8 lg, side, st, inj; UInt16 pts, proj; Char slot[4], name[16], team[4], adv[8]; } Player;
typedef struct { UInt8 lg, rank, prev, w, l, t, me; UInt32 pf; Char team[20], seq[4]; } Row;
typedef struct { UInt32 when; UInt8 st, sa, sh, mask; Char away[4], home[4], tv[8]; } Game;
typedef struct { UInt8 lg, week, res, rank, w, l, t; UInt16 pts, opts; Char opp[26]; } Hist;

#define MAXLG 4
#define EST_AND 0
#define EST_DONE 1
#define EST_NEXT 2
static League  gLgs[MAXLG]; static UInt16 gNL;
static Player *gPl;  static UInt16 gNPl;
static Row    *gRows; static UInt16 gNR;
static Game   *gGames; static UInt16 gNG;
static Hist   *gHist; static UInt16 gNH;
static UInt32  gSync; static UInt8 gWeek, gEstado, gSim; static Char gUser[20], gSeason[6];
static Boolean gHasData, gNeedUpdate;
#define gDone (gEstado == EST_DONE)

/* ---------- estado de tela ---------- */
enum { scrHome = 0, scrEsc, scrTab, scrNfl, scrHist };
static UInt16  gScreen = scrHome;
static Coord   gW = 320, gH = 320;
static Boolean gPINS;
static Int16   gTop[5];
static UInt16  gLg = 0, gSide = 0, gHistWeek = 0;

typedef struct { Coord x, y, w, h; UInt16 action, arg; } Hot;
#define MAXHOT 24
static Hot     gHot[MAXHOT]; static UInt16 gNHot;
enum { actHome = 1, actEsc, actTab, actNfl, actSide, actNextLg, actHist, actHistPrev, actHistNext };

static WinHandle gOff;static WinHandle gOff;  static Coord gOffW, gOffH;     /* buffer fora da tela (sem piscar) */

/* lista da tela atual (coordenadas nativas) */
static Coord gListY0, gListY1, gRowH; static UInt16 gVis;
#define MAXITEMS 64
static UInt16 gItem[MAXITEMS]; static UInt16 gNItem;  /* índices da lista atual */
#define HDR 0x8000                                    /* NFL: cabeçalho de dia (índice do 1º jogo do dia) */

/* ---------- utilidades ---------- */
static UInt16 rd16(const UInt8 *p) { return ((UInt16)p[0] << 8) | p[1]; }
static UInt32 rd32(const UInt8 *p) { return ((UInt32)p[0] << 24) | ((UInt32)p[1] << 16) | ((UInt32)p[2] << 8) | p[3]; }
static void cpy(Char *dst, const UInt8 *src, UInt16 n) { MemMove(dst, src, n); dst[n - 1] = 0; }
/* Append without overflowing d[0..cap-1] (cap includes the NUL). */
static void Cat(Char *d, UInt16 cap, const Char *s) {
    UInt16 n, i, room;
    if (!d || cap < 2) return;
    n = StrLen(d);
    if (n >= cap - 1) { d[cap - 1] = 0; return; }
    if (!s) return;
    room = (UInt16)(cap - 1 - n);
    for (i = 0; s[i] && i < room; i++) d[n + i] = s[i];
    d[n + i] = 0;
}
static void CatN(Char *d, UInt16 cap, Int32 n) { Char b[12]; StrIToA(b, n); Cat(d, cap, b); }
static void Cat2(Char *d, UInt16 cap, Int16 n) {
    Char b[3]; b[0] = '0' + (n / 10) % 10; b[1] = '0' + n % 10; b[2] = 0; Cat(d, cap, b);
}
/* centésimos -> "47.84"; décimos -> "85.9" */
static void CatC(Char *d, UInt16 cap, UInt32 c) { CatN(d, cap, c / 100); Cat(d, cap, "."); Cat2(d, cap, (Int16)(c % 100)); }
static void CatD(Char *d, UInt16 cap, UInt32 c) { Char b[2]; CatN(d, cap, c / 10); Cat(d, cap, "."); b[0] = '0' + (Char)(c % 10); b[1] = 0; Cat(d, cap, b); }

static const Char *kWd[7] = { "dom", "seg", "ter", "qua", "qui", "sex", "sáb" };
static const Char *kWD[7] = { "Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb" };

/* ---------- carga do PDB ---------- */
static void *Arr(DmOpenRef db, UInt16 rec, UInt16 *n, UInt16 rs, UInt16 ms, UInt8 **pp, MemHandle *hh) {
    MemHandle h = DmQueryRecord(db, rec); UInt32 sz; void *mem;
    *pp = NULL; *hh = NULL;
    if (!h) { *n = 0; return NULL; }
    sz = MemHandleSize(h);
    if ((UInt32)*n * rs > sz) *n = (UInt16)(sz / rs);
    if (*n == 0) return NULL;
    mem = MemPtrNew((UInt32)*n * ms);
    if (!mem) { *n = 0; return NULL; }
    MemSet(mem, (UInt32)*n * ms, 0);
    *hh = h; *pp = (UInt8 *)MemHandleLock(h);
    return mem;
}

static void LoadData(void) {
    DmOpenRef db = DmOpenDatabaseByTypeCreator(DATA_TYPE, CRID, dmModeReadOnly);
    MemHandle h; UInt8 *p, *r; UInt16 i;
    gHasData = false; gNeedUpdate = false; gNH = 0; gHist = NULL;
    if (!db) return;
    if (DmNumRecords(db) >= 1 && (h = DmQueryRecord(db, 0)) != NULL && MemHandleSize(h) >= 64) {
        p = (UInt8 *)MemHandleLock(h);
        if (p[0] == 'F' && p[1] == 'N' && p[2] == 'T' && p[3] == '1') {
            gNeedUpdate = true;
        } else if (p[0] == 'F' && p[1] == 'N' && p[2] == 'T' && p[3] == '2' && DmNumRecords(db) >= 6) {
            gSync = rd32(p + 6); gWeek = p[10]; gEstado = p[11]; gNL = p[12]; gNG = p[13];
            gNPl = rd16(p + 14); gNR = rd16(p + 16); cpy(gSeason, p + 18, 6); cpy(gUser, p + 24, 20);
            gSim = p[44]; gNH = p[45];
            gHasData = true;
        }
        MemHandleUnlock(h);
    }
    if (gHasData) {
        if (gNL > MAXLG) gNL = MAXLG;
        h = DmQueryRecord(db, 1);
        if (h && MemHandleSize(h) >= (UInt32)gNL * 96) {
            p = (UInt8 *)MemHandleLock(h);
            for (i = 0; i < gNL; i++) {
                League *L = &gLgs[i]; r = p + i * 96;
                cpy(L->name, r, 20); cpy(L->sig, r + 20, 4);
                L->nt = r[24]; L->rank = r[25]; L->prev = r[26]; L->wp = r[27]; L->w = r[28]; L->l = r[29]; L->t = r[30]; L->hasOpp = r[31];
                L->pts = rd16(r + 32); L->opts = rd16(r + 34); L->proj = rd16(r + 36); L->oproj = rd16(r + 38);
                L->fin = r[40]; L->ntit = r[41]; L->orank = r[42]; cpy(L->me, r + 44, 26); cpy(L->opp, r + 70, 26);
            }
            MemHandleUnlock(h);
        } else gNL = 0;
        gPl = (Player *)Arr(db, 2, &gNPl, 40, sizeof(Player), &p, &h);
        for (i = 0; i < gNPl; i++) {
            Player *q = &gPl[i]; r = p + i * 40;
            q->lg = r[0]; q->side = r[1]; q->st = r[2]; q->inj = r[3]; q->pts = rd16(r + 4); q->proj = rd16(r + 6);
            cpy(q->slot, r + 8, 4); cpy(q->name, r + 12, 16); cpy(q->team, r + 28, 4); cpy(q->adv, r + 32, 8);
        }
        if (h) MemHandleUnlock(h);
        gRows = (Row *)Arr(db, 3, &gNR, 36, sizeof(Row), &p, &h);
        for (i = 0; i < gNR; i++) {
            Row *q = &gRows[i]; r = p + i * 36;
            q->lg = r[0]; q->rank = r[1]; q->prev = r[2]; q->w = r[3]; q->l = r[4]; q->t = r[5]; q->me = r[6];
            q->pf = rd32(r + 8); cpy(q->team, r + 12, 20); cpy(q->seq, r + 32, 4);
        }
        if (h) MemHandleUnlock(h);
        gGames = (Game *)Arr(db, 4, &gNG, 24, sizeof(Game), &p, &h);
        for (i = 0; i < gNG; i++) {
            Game *g = &gGames[i]; r = p + i * 24;
            g->when = rd32(r); g->st = r[4]; g->sa = r[5]; g->sh = r[6]; g->mask = r[7];
            cpy(g->away, r + 8, 4); cpy(g->home, r + 12, 4); cpy(g->tv, r + 16, 8);
        }
        if (h) MemHandleUnlock(h);
        {   UInt16 nh = gNH;
            gHist = (Hist *)Arr(db, 5, &nh, 40, sizeof(Hist), &p, &h);
            gNH = nh;
            for (i = 0; i < gNH; i++) {
                Hist *q = &gHist[i]; r = p + i * 40;
                q->lg = r[0]; q->week = r[1]; q->res = r[2]; q->rank = r[3];
                q->w = r[4]; q->l = r[5]; q->t = r[6];
                q->pts = rd16(r + 8); q->opts = rd16(r + 10); cpy(q->opp, r + 12, 26);
            }
            if (h) MemHandleUnlock(h);
        }
        if (gNL == 0) gHasData = false;
        gHistWeek = 0;
        for (i = 0; i < gNH; i++) if (gHist[i].week > gHistWeek) gHistWeek = gHist[i].week;
    }
    DmCloseDatabase(db);
}

static void FreeData(void) {
    if (gPl) MemPtrFree(gPl);
    if (gRows) MemPtrFree(gRows);
    if (gGames) MemPtrFree(gGames);
    if (gHist) MemPtrFree(gHist);
    gPl = NULL; gRows = NULL; gGames = NULL; gHist = NULL;
}

static Game *GameOf(const Char *team) {
    UInt16 i;
    for (i = 0; i < gNG; i++)
        if (!StrCompare(gGames[i].away, team) || !StrCompare(gGames[i].home, team)) return &gGames[i];
    return NULL;
}

/* ---------- desenho (coordenadas nativas) ---------- */
#define RGB(r, g, b) (((UInt32)(r) << 16) | ((UInt32)(g) << 8) | (b))
#define cNAVY  RGB(14, 30, 70)
#define cTEAL  RGB(0, 150, 130)
#define cMINT  RGB(190, 230, 222)
#define cPALE  RGB(222, 244, 240)
#define cBAR   RGB(232, 236, 246)
#define cBLK   RGB(0, 0, 0)
#define cWHT   RGB(255, 255, 255)
#define cGRY   RGB(96, 96, 96)
#define cMGRY  RGB(150, 150, 150)
#define cLGRY  RGB(220, 220, 220)
#define cBOX   RGB(244, 244, 244)
#define cGRN   RGB(0, 130, 60)
#define cRED   RGB(200, 20, 30)
#define cAMB   RGB(200, 120, 0)
#define cGOLD  RGB(255, 196, 0)

static void ToRGB(UInt32 c, RGBColorType *r) { r->index = 0; r->r = (UInt8)(c >> 16); r->g = (UInt8)(c >> 8); r->b = (UInt8)c; }
static void Fg(UInt32 c) { RGBColorType r; ToRGB(c, &r); WinSetForeColorRGB(&r, NULL); }
static void Box(Coord x, Coord y, Coord w, Coord h, UInt32 c, UInt16 corner) {
    RectangleType r; r.topLeft.x = x; r.topLeft.y = y; r.extent.x = w; r.extent.y = h;
    Fg(c); WinDrawRectangle(&r, corner);
}
static void Line(Coord x1, Coord y1, Coord x2, Coord y2, UInt32 c) { Fg(c); WinDrawLine(x1, y1, x2, y2); }

enum { aL = 0, aC, aR };
static Coord TW(const Char *s, FontID f) { FntSetFont(f); return FntCharsWidth(s, StrLen(s)); }
static Coord Txt(const Char *s, Coord x, Coord y, FontID f, UInt32 fg, UInt32 bg, UInt16 align) {
    RGBColorType r; Int16 len = StrLen(s); Coord w;
    FntSetFont(f); w = FntCharsWidth(s, len);
    if (align == aC) x -= w / 2; else if (align == aR) x -= w;
    ToRGB(fg, &r); WinSetTextColorRGB(&r, NULL);
    ToRGB(bg, &r); WinSetBackColorRGB(&r, NULL);
    WinDrawChars(s, len, x, y);
    return w;
}
static Coord FH(FontID f) { FntSetFont(f); return FntLineHeight(); }
/* corta com "…" até caber em maxw */
static void Fit(Char *s, FontID f, Coord maxw) {
    Int16 n = StrLen(s);
    if (TW(s, f) <= maxw) return;
    while (n > 1) { s[--n] = 0; while (n > 0 && s[n - 1] == ' ') s[--n] = 0; s[n] = (Char)0x85; s[n + 1] = 0;
                    if (TW(s, f) <= maxw) return;
                    s[n] = 0; }
}

static void AddHot(Coord x, Coord y, Coord w, Coord h, UInt16 a, UInt16 arg) {
    if (gNHot < MAXHOT) { Hot *t = &gHot[gNHot++]; t->x = x; t->y = y; t->w = w; t->h = h; t->action = a; t->arg = arg; }
}

static void Button(Coord x, Coord y, Coord w, Coord h, const Char *label, UInt16 action) {
    Box(x, y, w, h, cBLK, 7);
    Box(x + 2, y + 2, w - 4, h - 4, cWHT, 5);
    Txt(label, x + w / 2, y + (h - FH(boldFont)) / 2, boldFont, cBLK, cWHT, aC);
    AddHot(x, y, w, h, action, 0);
}

/* barra inferior: larguras pelo texto (margem >=3px cada lado no branco) */
static void NavBar(UInt16 fourthAct) {
    Coord by = gH - 38, i, x, w, need[4], total, avail, extra, add;
    Char fourth[12];
    const Char *labs[4];
    UInt16 acts[4];
    if (fourthAct == actHist) StrCopy(fourth, "Anterior");
    else StrCopy(fourth, "Início");
    labs[0] = "Escal."; labs[1] = "Tabela"; labs[2] = "NFL"; labs[3] = fourth;
    acts[0] = actEsc; acts[1] = actTab; acts[2] = actNfl; acts[3] = fourthAct;
    /* branco = w-4; precisa texto+6 -> w >= texto+10; vão de 2px entre botões */
    total = 0;
    for (i = 0; i < 4; i++) {
        need[i] = TW(labs[i], boldFont) + 10;
        if (need[i] < 44) need[i] = 44;
        total += need[i];
    }
    avail = gW - 8 - 6; /* 3 vãos de 2px */
    if (avail < total) avail = total;
    extra = avail - total;
    x = 4;
    for (i = 0; i < 4; i++) {
        add = total ? (Coord)(((Int32)extra * need[i]) / total) : 0;
        w = need[i] + add;
        if (i == 3) w = gW - 4 - x;
        Button(x, by, w, 34, labs[i], acts[i]);
        x += w + 2;
    }
}


/* triângulo cheio: para cima (up) ou para baixo */
static void Tri(Coord cx, Coord y, Coord h, Boolean up, UInt32 c) {
    Coord k; Fg(c);
    for (k = 0; k < h; k++) { Coord half = up ? k : (h - 1 - k); WinDrawLine(cx - half, y + k, cx + half, y + k); }
}

/* título Palm OS (aba) */
static void Title(const Char *t) {
    Coord w = TW(t, boldFont) + 18;
    Box(0, 0, w, 25, cNAVY, 6); Box(0, 0, 8, 25, cNAVY, 0); Box(0, 0, w, 8, cNAVY, 0);
    Txt(t, 9, (25 - FH(boldFont)) / 2, boldFont, cWHT, cNAVY, aL);
    Box(0, 23, gW, 2, cNAVY, 0);
}
/* gatilho de lista à direita do título: "(seta) nome da liga" — toque troca de liga */
static void LeaguePopup(void) {
    Char b[24]; Coord w, x;
    if (!gNL) return;
    StrCopy(b, gLgs[gLg].name); Fit(b, boldFont, 170);
    w = TW(b, boldFont); x = gW - 6 - w;
    Tri(x - 10, 8, 7, false, cNAVY);
    Txt(b, x, (24 - FH(boldFont)) / 2, boldFont, cNAVY, cWHT, aL);
    AddHot(x - 20, 0, gW - (x - 20), 26, actNextLg, 0);
}

/* faixa "Dados de dom 25/10 15h20" + selo andamento/encerrada (todas as telas) */
static void SyncBar(Coord y) {
    Char b[40]; DateTimeType dt; const Char *badge; UInt32 bc; Coord bw, fh;
    if (gScreen == scrHist) { badge = "histórico"; bc = cNAVY; }
    else if (gEstado == EST_DONE) { badge = "encerrada"; bc = cGRN; }
    else if (gEstado == EST_NEXT) { badge = "próxima"; bc = cTEAL; }
    else { badge = "andamento"; bc = cAMB; }
    bw = TW(badge, boldFont) + 12; fh = FH(stdFont);
    Box(0, y, gW, 24, cBAR, 0); Line(0, y + 24, gW, y + 24, cNAVY);
    if (gNeedUpdate) { Txt("PDB antigo — atualize", 6, y + (24 - fh) / 2, boldFont, cRED, cBAR, aL); return; }
    if (!gHasData) { Txt("Sem dados", 6, y + (24 - fh) / 2, boldFont, cRED, cBAR, aL); return; }
    TimSecondsToDateTime(gSync, &dt);
    StrCopy(b, "Dados de "); Cat(b, sizeof(b), kWd[dt.weekDay % 7]); Cat(b, sizeof(b), " "); Cat2(b, sizeof(b), dt.day); Cat(b, sizeof(b), "/"); Cat2(b, sizeof(b), dt.month);
    Cat(b, sizeof(b), " "); Cat2(b, sizeof(b), dt.hour); Cat(b, sizeof(b), "h"); Cat2(b, sizeof(b), dt.minute);
    if (!gSim && 6 + TW(b, stdFont) + 8 + bw > gW - 4) {           /* não coube: tira o dia da semana */
        StrCopy(b, "Dados de "); Cat2(b, sizeof(b), dt.day); Cat(b, sizeof(b), "/"); Cat2(b, sizeof(b), dt.month); Cat(b, sizeof(b), " "); Cat2(b, sizeof(b), dt.hour); Cat(b, sizeof(b), "h"); Cat2(b, sizeof(b), dt.minute);
    }
    if (gSim) {                                                  /* .pdb de teste (--simular-fim) */
        Coord sw = TW("SIMULADO", boldFont) + 10;
        Box(4, y + 2, sw, 20, cRED, 0); Box(5, y + 3, sw - 2, 18, cWHT, 0);
        Txt("SIMULADO", 4 + sw / 2, y + (24 - FH(boldFont)) / 2, boldFont, cRED, cWHT, aC);
        b[0] = 0; Cat2(b, sizeof(b), dt.day); Cat(b, sizeof(b), "/"); Cat2(b, sizeof(b), dt.month); Cat(b, sizeof(b), " "); Cat2(b, sizeof(b), dt.hour); Cat(b, sizeof(b), "h"); Cat2(b, sizeof(b), dt.minute); Fit(b, stdFont, gW - 4 - bw - 8 - sw - 10);
        Txt(b, 4 + sw + 6, y + (24 - fh) / 2, stdFont, cRED, cBAR, aL);
    } else Txt(b, 6, y + (24 - fh) / 2, stdFont, cNAVY, cBAR, aL);
    Box(gW - 4 - bw, y + 2, bw, 20, bc, 4);
    Txt(badge, gW - 4 - bw / 2, y + (24 - FH(boldFont)) / 2, boldFont, cWHT, bc, aC);
}

/* dígitos de 7 segmentos (placar grande) */
static const UInt8 kSeg[10] = { 0x3F, 0x06, 0x5B, 0x4F, 0x66, 0x6D, 0x7D, 0x07, 0x7F, 0x6F };
static void Digit(Coord x, Coord y, Coord w, Coord h, Coord t, UInt8 d, UInt32 c) {
    UInt8 m = kSeg[d % 10]; Coord h2 = h / 2;
    if (m & 0x01) Box(x, y, w, t, c, 0);
    if (m & 0x02) Box(x + w - t, y, t, h2 + t / 2, c, 0);
    if (m & 0x04) Box(x + w - t, y + h2 - t / 2, t, h - h2 + t / 2, c, 0);
    if (m & 0x08) Box(x, y + h - t, w, t, c, 0);
    if (m & 0x10) Box(x, y + h2 - t / 2, t, h - h2 + t / 2, c, 0);
    if (m & 0x20) Box(x, y, t, h2 + t / 2, c, 0);
    if (m & 0x40) Box(x, y + h2 - t / 2, w, t, c, 0);
}
static Coord Seg(const Char *s, Coord x, Coord y, Coord w, Coord h, Coord t, UInt32 c, UInt16 align) {
    Coord g = t / 2 + 2, tot = 0, i; Int16 n = StrLen(s);
    for (i = 0; i < n; i++) tot += (s[i] == '.' ? t : w) + g;
    tot -= g;
    if (align == aR) x -= tot; else if (align == aC) x -= tot / 2;
    for (i = 0; i < n; i++) {
        if (s[i] == '.') { Box(x, y + h - t, t, t, c, 0); x += t + g; }
        else { Digit(x, y, w, h, t, (UInt8)(s[i] - '0'), c); x += w + g; }
    }
    return tot;
}

/* barra de chance: Favorito (>=50%, verde) / Azarão (<50%, vermelho) */
static void WinBar(Coord x, Coord y, Coord w, UInt8 wp, UInt32 bg) {
    Boolean fav; const Char *lab; UInt32 fill;
    Char b[8]; Coord lw, pw, bx, bw, f;
    if (wp == 255) { Txt("sem confronto", x, y, stdFont, cMGRY, bg, aL); return; }
    fav = (wp >= 50); /* exatamente 50% conta como Favorito */
    lab = fav ? "Favorito" : "Azarão";
    fill = fav ? cGRN : cRED;
    lw = Txt(lab, x, y, boldFont, cNAVY, bg, aL) + 8;
    b[0] = 0; CatN(b, sizeof(b), wp); Cat(b, sizeof(b), "%");
    pw = Txt(b, x + w, y, boldFont, cNAVY, bg, aR) + 8;
    bx = x + lw; bw = w - lw - pw;
    if (bw < 12) bw = 12;
    Box(bx, y + 5, bw, 12, cNAVY, 0); Box(bx + 1, y + 6, bw - 2, 10, cWHT, 0);
    f = (Coord)(((Int32)(bw - 4) * wp) / 100); if (f < 2) f = 2; if (f > bw - 4) f = bw - 4;
    Box(bx + 2, y + 7, f, 8, fill, 0);
}

/* ---------- Início ---------- */
static void Card(UInt16 li, Coord y, Coord h, Boolean tall) {
    League *L = &gLgs[li]; Char b[40], sa[12], sb[12];
    Coord dh = tall ? 34 : 26, dw = tall ? 17 : 14, dt = tall ? 5 : 4, sy;
    Boolean win = L->pts > L->opts, lose = L->pts < L->opts;
    Box(4, y, gW - 8, h, cNAVY, 8); Box(6, y + 2, gW - 12, h - 4, cWHT, 7);
    Box(4, y, gW - 8, 24, cNAVY, 8); Box(4, y + 12, gW - 8, 12, cNAVY, 0);
    StrCopy(b, L->name); Fit(b, boldFont, 150);
    Txt(b, 12, y + (24 - FH(boldFont)) / 2, boldFont, cWHT, cNAVY, aL);
    if (gDone) { StrCopy(b, "Final · Sem "); CatN(b, sizeof(b), gWeek); }
    else { b[0] = 0; CatN(b, sizeof(b), L->w); Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), L->l); if (L->t) { Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), L->t); }
           Cat(b, sizeof(b), " · "); CatN(b, sizeof(b), L->rank); Cat(b, sizeof(b), "º de "); CatN(b, sizeof(b), L->nt); }
    Txt(b, gW - 12, y + (24 - FH(stdFont)) / 2, stdFont, cMINT, cNAVY, aR);
    StrCopy(b, L->me); Fit(b, boldFont, 138); Txt(b, 12, y + 26, boldFont, cNAVY, cWHT, aL);
    if (L->hasOpp) { StrCopy(b, L->opp); Fit(b, boldFont, 150); Txt(b, gW - 12, y + 26, boldFont, cGRY, cWHT, aR); }
    sy = y + 26 + FH(boldFont) + 2;
    if (gEstado == EST_NEXT) {
        sa[0] = 0; CatD(sa, sizeof(sa), L->proj); sb[0] = 0; CatD(sb, sizeof(sb), L->oproj);
        Seg(sa, 12, sy, dw, dh, dt, cTEAL, aL);
        if (L->hasOpp) { Seg(sb, gW - 12, sy, dw, dh, dt, cGRY, aR); Txt("x", gW / 2, sy + (dh - FH(boldFont)) / 2, boldFont, cMGRY, cWHT, aC); }
        sy += dh + 4;
        if (tall) { Txt("projeção", gW / 2, sy, stdFont, cMGRY, cWHT, aC); sy += FH(stdFont) + 1; }
        WinBar(12, sy, gW - 24, L->wp, cWHT);
    } else {
        sa[0] = 0; CatC(sa, sizeof(sa), L->pts); sb[0] = 0; CatC(sb, sizeof(sb), L->opts);
        {   UInt32 ca = cNAVY, cb = cGRY;
            if (gDone) { ca = win ? cGRN : cGRY; cb = lose ? cRED : cGRY; }
            else if (win) ca = cTEAL; else if (lose) cb = cTEAL;
            Seg(sa, 12, sy, dw, dh, dt, ca, aL);
            if (L->hasOpp) { Seg(sb, gW - 12, sy, dw, dh, dt, cb, aR); Txt("x", gW / 2, sy + (dh - FH(boldFont)) / 2, boldFont, cMGRY, cWHT, aC); }
        }
        sy += dh + 4;
        if (!gDone) {
            if (tall) {
                StrCopy(b, "proj "); CatD(b, sizeof(b), L->proj); Txt(b, 12, sy, stdFont, cGRY, cWHT, aL);
                Txt("parcial", gW / 2, sy, stdFont, cMGRY, cWHT, aC);
                if (L->hasOpp) { StrCopy(b, "proj "); CatD(b, sizeof(b), L->oproj); Txt(b, gW - 12, sy, stdFont, cGRY, cWHT, aR); }
                sy += FH(stdFont) + 1;
            }
            WinBar(12, sy, gW - 24, L->wp, cWHT);
        } else {
            const Char *lab = win ? "VITÓRIA" : lose ? "DERROTA" : "EMPATE";
            UInt32 c = win ? cGRN : lose ? cRED : cAMB; Coord bw = TW(lab, boldFont) + 20, fh = FH(boldFont);
            if (L->hasOpp) {
                Box(12, sy, bw, fh + 2, c, 5); Txt(lab, 12 + bw / 2, sy + 1, boldFont, cWHT, c, aC);
                StrCopy(b, "por "); CatC(b, sizeof(b), (UInt32)(win ? L->pts - L->opts : L->opts - L->pts)); Txt(b, gW - 12, sy + 1, stdFont, cGRY, cWHT, aR);
                sy += fh + (tall ? 4 : 2);
            }
            if (tall || !L->hasOpp) {
                Coord x;
                StrCopy(b, "Agora "); CatN(b, sizeof(b), L->w); Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), L->l); if (L->t) { Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), L->t); }
                Cat(b, sizeof(b), " · "); CatN(b, sizeof(b), L->rank); Cat(b, sizeof(b), "º de "); CatN(b, sizeof(b), L->nt);
                {   Coord need = (L->prev && L->prev != L->rank) ? TW("era 00º", boldFont) + 22 : (L->prev ? TW("= mesma posição", stdFont) + 10 : 0);
                    if (12 + TW(b, boldFont) + need > gW - 12) { StrCopy(b, ""); CatN(b, sizeof(b), L->w); Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), L->l); if (L->t) { Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), L->t); }
                                                                Cat(b, sizeof(b), " · "); CatN(b, sizeof(b), L->rank); Cat(b, sizeof(b), "º de "); CatN(b, sizeof(b), L->nt); }
                }
                Txt(b, 12, sy, boldFont, cNAVY, cWHT, aL);
                if (L->prev && L->prev != L->rank) {
                    Boolean up = L->rank < L->prev; UInt32 ac = up ? cGRN : cRED;
                    StrCopy(b, "era "); CatN(b, sizeof(b), L->prev); Cat(b, sizeof(b), "º");
                    x = gW - 12 - Txt(b, gW - 12, sy, boldFont, ac, cWHT, aR);
                    Tri(x - 9, sy + 6, 7, up, ac);
                } else if (L->prev) Txt(12 + TW(b, boldFont) + TW("= mesma posição", stdFont) + 10 > gW - 12 ? "=" : "= mesma posição", gW - 12, sy, stdFont, cMGRY, cWHT, aR);
            }
        }
    }
    AddHot(4, y, gW - 8, h, actEsc, li);
}

static void DrawHome(void) {
    Boolean tall = gH >= 440;
    Coord y = 54, ch = tall ? 140 : 100, by = gH - 38, i;
    Char b[48];
    Box(0, 0, gW, gH, cWHT, 0);
    Title("Fantasy");
    { StrCopy(b, "Semana "); CatN(b, sizeof(b), gWeek); if (gHasData) Txt(b, gW - 6, (24 - FH(boldFont)) / 2, boldFont, cNAVY, cWHT, aR); }
    SyncBar(26);
    gNHot = 0;
    if (gNeedUpdate) {
        Txt("Atualize os dados", gW / 2, 100, boldFont, cBLK, cWHT, aC);
        Txt("Este FantasyDados.pdb é antigo", gW / 2, 130, stdFont, cGRY, cWHT, aC);
        Txt("(FNT1). Gere de novo com", gW / 2, 152, stdFont, cGRY, cWHT, aC);
        Txt("make data e reinstale o .pdb.", gW / 2, 174, stdFont, cGRY, cWHT, aC);
        return;
    }
    if (!gHasData || !gNL) {
        Txt("Sem dados :(", gW / 2, 90, boldFont, cBLK, cWHT, aC);
        Txt("Instale o FantasyDados.pdb", gW / 2, 118, stdFont, cGRY, cWHT, aC);
        Txt("(veja o README)", gW / 2, 142, stdFont, cGRY, cWHT, aC);
        return;
    }
    for (i = 0; i < (Coord)gNL && i < 2; i++) { Card(i, y, ch, tall); y += ch + 6; }
    if (tall && by - y >= 2 * FH(stdFont) + 6) {
        Box(4, y, gW - 8, by - y - 6, cLGRY, 0); Box(5, y + 1, gW - 10, by - y - 8, cBOX, 0);
        if (gEstado == EST_NEXT) {
            Txt("Próxima rodada", 12, y + 2, boldFont, cTEAL, cBOX, aL);
            if (gNG) {
                Game *first = &gGames[0]; DateTimeType dt; TimSecondsToDateTime(first->when, &dt);
                StrCopy(b, "Abre "); Cat(b, sizeof(b), kWd[dt.weekDay % 7]); Cat(b, sizeof(b), " ");
                Cat2(b, sizeof(b), dt.day); Cat(b, sizeof(b), "/"); Cat2(b, sizeof(b), dt.month); Cat(b, sizeof(b), " ");
                CatN(b, sizeof(b), dt.hour); Cat(b, sizeof(b), "h"); Cat2(b, sizeof(b), dt.minute);
                Cat(b, sizeof(b), " · "); Cat(b, sizeof(b), first->away); Cat(b, sizeof(b), "@"); Cat(b, sizeof(b), first->home);
                Fit(b, stdFont, gW - 24); Txt(b, 12, y + 2 + FH(boldFont), stdFont, cGRY, cBOX, aL);
            }
        } else if (gDone) {
            StrCopy(b, "Rodada encerrada · Sem "); CatN(b, sizeof(b), gWeek);
            Txt(b, 12, y + 2, boldFont, cGRN, cBOX, aL);
            Txt("Veja o histórico em Anterior", 12, y + 2 + FH(boldFont), stdFont, cGRY, cBOX, aL);
        } else {
            Game *last = NULL; UInt16 k;
            Txt("Rodada em andamento", 12, y + 2, boldFont, cAMB, cBOX, aL);
            for (k = 0; k < gNG; k++) if (!last || gGames[k].when >= last->when) last = &gGames[k];
            if (last) {
                DateTimeType dt; TimSecondsToDateTime(last->when, &dt);
                StrCopy(b, "Último jogo: "); Cat(b, sizeof(b), kWd[dt.weekDay % 7]); Cat(b, sizeof(b), " "); CatN(b, sizeof(b), dt.hour); Cat(b, sizeof(b), "h"); Cat2(b, sizeof(b), dt.minute);
                Cat(b, sizeof(b), " "); Cat(b, sizeof(b), last->away); Cat(b, sizeof(b), "@"); Cat(b, sizeof(b), last->home);
                Fit(b, stdFont, gW - 24); Txt(b, 12, y + 2 + FH(boldFont), stdFont, cGRY, cBOX, aL);
            }
        }
    }
    NavBar(actHist);
    gHot[gNHot - 4].arg = gLg;
}

static void HistWeekBounds(UInt8 *minW, UInt8 *maxW) {
    UInt16 i; *minW = 255; *maxW = 0;
    for (i = 0; i < gNH; i++) {
        if (gHist[i].week < *minW) *minW = gHist[i].week;
        if (gHist[i].week > *maxW) *maxW = gHist[i].week;
    }
    if (*minW == 255) { *minW = 0; *maxW = 0; }
}

static Hist *HistOf(UInt16 li, UInt8 week) {
    UInt16 i;
    for (i = 0; i < gNH; i++) if (gHist[i].lg == li && gHist[i].week == week) return &gHist[i];
    return NULL;
}

static void HistCard(Hist *H, UInt16 li, Coord y, Coord h, Boolean tall) {
    League *L = &gLgs[li]; Char b[40], sa[12], sb[12];
    Coord dh = tall ? 34 : 26, dw = tall ? 17 : 14, dt = tall ? 5 : 4, sy;
    Boolean win = H->res == 0, lose = H->res == 1;
    Box(4, y, gW - 8, h, cNAVY, 8); Box(6, y + 2, gW - 12, h - 4, cWHT, 7);
    Box(4, y, gW - 8, 24, cNAVY, 8); Box(4, y + 12, gW - 8, 12, cNAVY, 0);
    StrCopy(b, L->name); Fit(b, boldFont, 150);
    Txt(b, 12, y + (24 - FH(boldFont)) / 2, boldFont, cWHT, cNAVY, aL);
    StrCopy(b, "Final · Sem "); CatN(b, sizeof(b), H->week);
    Txt(b, gW - 12, y + (24 - FH(stdFont)) / 2, stdFont, cMINT, cNAVY, aR);
    StrCopy(b, L->me); Fit(b, boldFont, 138); Txt(b, 12, y + 26, boldFont, cNAVY, cWHT, aL);
    StrCopy(b, H->opp); Fit(b, boldFont, 150); Txt(b, gW - 12, y + 26, boldFont, cGRY, cWHT, aR);
    sy = y + 26 + FH(boldFont) + 2;
    sa[0] = 0; CatC(sa, sizeof(sa), H->pts); sb[0] = 0; CatC(sb, sizeof(sb), H->opts);
    Seg(sa, 12, sy, dw, dh, dt, win ? cGRN : cGRY, aL);
    Seg(sb, gW - 12, sy, dw, dh, dt, lose ? cRED : cGRY, aR);
    Txt("x", gW / 2, sy + (dh - FH(boldFont)) / 2, boldFont, cMGRY, cWHT, aC);
    sy += dh + 4;
    {   const Char *lab = win ? "VITÓRIA" : lose ? "DERROTA" : "EMPATE";
        UInt32 c = win ? cGRN : lose ? cRED : cAMB; Coord bw2 = TW(lab, boldFont) + 20, fh = FH(boldFont);
        Box(12, sy, bw2, fh + 2, c, 5); Txt(lab, 12 + bw2 / 2, sy + 1, boldFont, cWHT, c, aC);
        { UInt32 diff = win ? (UInt32)(H->pts - H->opts) : (UInt32)(H->opts - H->pts);
          StrCopy(b, "por "); CatC(b, sizeof(b), diff); Txt(b, gW - 12, sy + 1, stdFont, cGRY, cWHT, aR); }
        sy += fh + (tall ? 4 : 2);
    }
    if (tall) {
        StrCopy(b, "Agora "); CatN(b, sizeof(b), H->w); Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), H->l);
        if (H->t) { Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), H->t); }
        if (H->rank) { Cat(b, sizeof(b), " · "); CatN(b, sizeof(b), H->rank); Cat(b, sizeof(b), "º"); }
        Txt(b, 12, sy, boldFont, cNAVY, cWHT, aL);
    }
}

static void DrawHist(void) {
    Boolean tall = gH >= 440;
    Coord y, ch, by = gH - 38, i;
    Char b[48]; UInt8 minW, maxW;
    Box(0, 0, gW, gH, cWHT, 0);
    Title("Anterior");
    if (!tall && gNL) LeaguePopup();
    SyncBar(26);
    gNHot = 0;
    if (!gHasData || !gNH) {
        Txt("Sem histórico", gW / 2, 120, boldFont, cBLK, cWHT, aC);
        Txt("Gere o FantasyDados.pdb de novo", gW / 2, 148, stdFont, cGRY, cWHT, aC);
        NavBar(actHome);
        return;
    }
    HistWeekBounds(&minW, &maxW);
    if (gHistWeek < minW || gHistWeek > maxW) gHistWeek = maxW;
    y = 54;
    Box(4, y, gW - 8, 28, cNAVY, 0);
    Txt("<", 24, y + (28 - FH(boldFont)) / 2, boldFont, cWHT, cNAVY, aC);
    AddHot(4, y, 60, 28, actHistPrev, 0);
    StrCopy(b, "Semana "); CatN(b, sizeof(b), gHistWeek);
    Txt(b, gW / 2, y + (28 - FH(boldFont)) / 2, boldFont, cWHT, cNAVY, aC);
    Txt(">", gW - 24, y + (28 - FH(boldFont)) / 2, boldFont, cWHT, cNAVY, aC);
    AddHot(gW - 64, y, 60, 28, actHistNext, 0);
    y += 34;
    ch = tall ? 140 : 100;
    if (tall) {
        for (i = 0; i < gNL && i < 2; i++) {
            Hist *H = HistOf(i, gHistWeek);
            if (H) HistCard(H, i, y, ch, true);
            else { Box(4, y, gW - 8, ch, cLGRY, 8); Txt("sem jogo", gW / 2, y + ch / 2, stdFont, cMGRY, cLGRY, aC); }
            y += ch + 6;
        }
        if (by - y >= 22) {
            Coord x; UInt8 w; Char mark[2];
            Box(4, y, gW - 8, by - y - 4, cBOX, 0);
            Txt("Hist:", 8, y + 4, boldFont, cNAVY, cBOX, aL);
            x = 8 + TW("Hist:", boldFont) + 6;
            for (w = minW; w <= maxW && x < gW - 24; w++) {
                Hist *H = HistOf(0, w);
                if (!H) continue;
                mark[0] = H->res == 0 ? 'V' : (H->res == 1 ? 'D' : 'E'); mark[1] = 0;
                {   UInt32 c = H->res == 0 ? cGRN : (H->res == 1 ? cRED : cAMB);
                    Coord mw = TW(mark, boldFont) + 10;
                    if (w == gHistWeek) { Box(x - 2, y + 2, mw, 18, c, 3); Txt(mark, x + 3, y + 4, boldFont, cWHT, c, aL); }
                    else Txt(mark, x, y + 4, boldFont, c, cBOX, aL);
                    AddHot(x - 2, y, mw, 20, actHist, w);
                    x += mw + 4;
                }
            }
        }
    } else {
        Hist *H = HistOf(gLg, gHistWeek);
        if (H) HistCard(H, gLg, y, ch, false);
        else { Box(4, y, gW - 8, ch, cLGRY, 8); Txt("sem jogo nesta semana", gW / 2, y + ch / 2, stdFont, cMGRY, cLGRY, aC); }
    }
    NavBar(actHome);
}

/* ---------- listas (Escalação / Tabela / NFL) ---------- */
static void BuildItems(void) {
    UInt16 i; gNItem = 0;
    if (gScreen == scrEsc) {
        for (i = 0; i < gNPl && gNItem < MAXITEMS; i++) if (gPl[i].lg == gLg && gPl[i].side == gSide) gItem[gNItem++] = i;
    } else if (gScreen == scrTab) {
        for (i = 0; i < gNR && gNItem < MAXITEMS; i++) if (gRows[i].lg == gLg) gItem[gNItem++] = i;
    } else if (gScreen == scrNfl) {
        Int16 lastDay = -1;
        for (i = 0; i < gNG && gNItem < MAXITEMS - 1; i++) {
            DateTimeType dt; TimSecondsToDateTime(gGames[i].when, &dt);
            if (dt.day != lastDay) { gItem[gNItem++] = HDR | i; lastDay = dt.day; }
            gItem[gNItem++] = i;
        }
    }
}

static UInt32 SlotColor(const Char *s) {
    if (!StrCompare(s, "QB")) return RGB(214, 50, 110);
    if (!StrCompare(s, "RB")) return RGB(0, 150, 130);
    if (!StrCompare(s, "WR")) return RGB(40, 105, 210);
    if (!StrCompare(s, "TE")) return RGB(225, 120, 0);
    if (!StrCompare(s, "K"))  return RGB(125, 75, 195);
    if (!StrCompare(s, "DEF")) return RGB(125, 85, 45);
    return RGB(90, 90, 90);
}

static void DrawEscRow(Player *p, Coord y, Coord right) {
    Char b[40], slot[5]; Coord fh = FH(stdFont), pw, nx = 52, room; Game *g = GameOf(p->team);
    Boolean fin = p->st == 2;
    StrCopy(slot, p->slot);
    if (!StrCompare(slot, "FLEX")) StrCopy(slot, "W/R"); else if (!StrCompare(slot, "SUPER_FLEX")) StrCopy(slot, "SF");
    Box(5, y + 10, 42, 22, SlotColor(p->slot), 4);
    Txt(slot, 26, y + 10 + (22 - FH(boldFont)) / 2, boldFont, cWHT, SlotColor(p->slot), aC);
    /* pontos e projeção à direita */
    b[0] = 0; CatC(b, sizeof(b), p->pts);
    pw = Txt(b, right, y + 1, boldFont, fin ? cBLK : cGRY, cWHT, aR);
    StrCopy(b, "p "); CatD(b, sizeof(b), p->proj);
    { Coord w2 = Txt(b, right, y + 1 + fh - 2, stdFont, cMGRY, cWHT, aR); if (w2 > pw) pw = w2; }
    room = right - pw - 6 - nx;
    StrCopy(b, p->name); Fit(b, boldFont, room - (p->inj ? 16 : 0));
    { Coord w = Txt(b, nx, y + 1, boldFont, cBLK, cWHT, aL);
      if (p->inj) { Char c[2]; c[0] = (Char)p->inj; c[1] = 0; Txt(c, nx + w + 5, y + 1, boldFont, cRED, cWHT, aL); } }
    /* jogo: só "Final" com resultado, ou dia/horário de início (sem relógio de jogo) */
    if (p->st == 3 || !g) StrCopy(b, p->adv[0] ? p->adv : "sem jogo");
    else if (fin && (g->sa == 255 || g->sh == 255)) { StrCopy(b, p->adv); Cat(b, sizeof(b), " · Final"); }
    else if (fin) {
        UInt16 k;
        for (k = 0; k < 3; k++) {
            b[0] = 0;
            if (k < 2) { Cat(b, sizeof(b), g->away); Cat(b, sizeof(b), " "); }
            CatN(b, sizeof(b), g->sa); Cat(b, sizeof(b), k == 0 ? " x " : "x"); CatN(b, sizeof(b), g->sh);
            if (k < 2) { Cat(b, sizeof(b), " "); Cat(b, sizeof(b), g->home); }
            Cat(b, sizeof(b), k == 0 ? " · Final" : " Final");
            if (TW(b, stdFont) <= room) break;
        }
    } else {
        DateTimeType dt; TimSecondsToDateTime(g->when, &dt);
        StrCopy(b, p->adv); Cat(b, sizeof(b), " · "); Cat(b, sizeof(b), kWd[dt.weekDay % 7]); Cat(b, sizeof(b), " "); CatN(b, sizeof(b), dt.hour); Cat(b, sizeof(b), "h");
        if (dt.minute) Cat2(b, sizeof(b), dt.minute);
    }
    Fit(b, stdFont, room);
    Txt(b, nx, y + 1 + fh - 2, stdFont, fin ? cGRN : cGRY, cWHT, aL);
    Line(0, y + gRowH - 1, right + 3, y + gRowH - 1, cLGRY);
}

static void DrawTabRow(Row *r, Coord y, Coord right) {
    Char b[24]; UInt32 bg = r->me ? cPALE : cWHT, fg = r->me ? cTEAL : cBLK;
    FontID f = r->me ? boldFont : stdFont; Coord ty = y + (gRowH - FH(f)) / 2;
    Box(0, y, right + 4, gRowH, bg, 0);
    b[0] = 0; CatN(b, sizeof(b), r->rank); Txt(b, 24, ty, f, fg, bg, aR);
    if (r->prev && r->prev != r->rank) Tri(32, y + gRowH / 2 - 3, 6, r->rank < r->prev, r->rank < r->prev ? cGRN : cRED);
    StrCopy(b, r->team); Fit(b, f, 136); Txt(b, 42, ty, f, fg, bg, aL);
    b[0] = 0; CatN(b, sizeof(b), r->w); Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), r->l); if (r->t) { Cat(b, sizeof(b), "-"); CatN(b, sizeof(b), r->t); }
    Txt(b, 200, ty, boldFont, fg, bg, aC);
    b[0] = 0; CatN(b, sizeof(b), (r->pf + 50) / 100); Txt(b, 262, ty, f, fg, bg, aR);
    Txt(r->seq, right, ty, stdFont, r->seq[StrLen(r->seq) - 1] == 'W' ? cGRN : cRED, bg, aR);
    Line(0, y + gRowH - 1, right + 3, y + gRowH - 1, cLGRY);
}

static void DrawNflRow(UInt16 it, Coord y, Coord right) {
    Char b[24]; Coord ty = y + (gRowH - FH(stdFont)) / 2, tb = y + (gRowH - FH(boldFont)) / 2, x;
    if (it & HDR) {
        Game *g = &gGames[it & ~HDR]; DateTimeType dt; UInt32 c;
        TimSecondsToDateTime(g->when, &dt); c = (dt.weekDay == 0) ? cNAVY : cGRY;
        Box(0, y, right + 4, gRowH, c, 0);
        StrCopy(b, kWD[dt.weekDay % 7]); Cat(b, sizeof(b), " "); Cat2(b, sizeof(b), dt.day); Cat(b, sizeof(b), "/"); Cat2(b, sizeof(b), dt.month);
        Txt(b, 6, tb, boldFont, cWHT, c, aL);
        return;
    } else {
        Game *g = &gGames[it]; DateTimeType dt; UInt16 k; Coord tagx = right;
        Box(0, y, right + 4, gRowH, cWHT, 0);
        TimSecondsToDateTime(g->when, &dt);
        b[0] = 0; CatN(b, sizeof(b), dt.hour); Cat(b, sizeof(b), "h"); Cat2(b, sizeof(b), dt.minute); Txt(b, 4, ty, stdFont, cGRY, cWHT, aL);
        Txt(g->away, 60, tb, boldFont, cBLK, cWHT, aL);
        Txt(g->home, 170, tb, boldFont, cBLK, cWHT, aL);
        for (k = 0; k < gNL; k++) if (g->mask & (1 << (gNL - 1 - k))) {        /* selos à direita, na ordem das ligas */
            League *L = &gLgs[gNL - 1 - k]; Coord w = TW(L->sig, boldFont) + 6; UInt32 c = (gNL - 1 - k) == 0 ? cTEAL : RGB(40, 105, 210);
            tagx -= w; Box(tagx, y + 2, w, gRowH - 4, c, 3); Txt(L->sig, tagx + w / 2, tb, boldFont, cWHT, c, aC); tagx -= 2;
        }
        if (g->st == 2) {
            Boolean aw = g->sa > g->sh;
            if (g->sa == 255 || g->sh == 255) Txt("@", 139, ty, stdFont, cMGRY, cWHT, aC);   /* sem placar (pdb simulado) */
            else {
                b[0] = 0; CatN(b, sizeof(b), g->sa); Txt(b, 132, tb, aw ? boldFont : stdFont, cBLK, cWHT, aR);
                Txt("x", 139, ty, stdFont, cMGRY, cWHT, aC);
                b[0] = 0; CatN(b, sizeof(b), g->sh); Txt(b, 146, tb, aw ? stdFont : boldFont, cBLK, cWHT, aL);
            }
            x = 214; if (x + TW("Final", stdFont) <= tagx - 2) Txt("Final", x, ty, stdFont, cGRN, cWHT, aL);
        } else {
            Txt("@", 139, ty, stdFont, cMGRY, cWHT, aC);
            if (214 + TW(g->tv, stdFont) <= tagx - 2) Txt(g->tv, 214, ty, stdFont, cMGRY, cWHT, aL);   /* sem espaço: sem TV */
        }
        Line(0, y + gRowH - 1, right + 3, y + gRowH - 1, RGB(236, 236, 236));
    }
}

static void DrawScrollbar(void) {
    Coord x = gW - 14, y0 = gListY0, y1 = gListY1, track = y1 - y0 - 24;
    Box(x, y0, 14, y1 - y0, cWHT, 0);
    if (gNItem <= gVis) return;
    Tri(x + 7, y0 + 2, 8, true, cBLK); Tri(x + 7, y1 - 10, 8, false, cBLK);
    Line(x + 7, y0 + 12, x + 7, y1 - 12, cGRY);
    {   Coord th = (Coord)(((Int32)track * gVis) / gNItem), ty;
        if (th < 12) th = 12;
        ty = y0 + 12 + (Coord)(((Int32)(track - th) * gTop[gScreen]) / (gNItem - gVis));
        Box(x + 3, ty, 8, th, cBLK, 0); }
}

static void DrawList(void) {
    UInt16 i; Coord y, right = gW - 18;
    Int16 maxTop = (Int16)gNItem - (Int16)gVis;
    if (maxTop < 0) maxTop = 0;
    if (gTop[gScreen] > maxTop) gTop[gScreen] = maxTop;
    if (gTop[gScreen] < 0) gTop[gScreen] = 0;
    Box(0, gListY0, gW, gListY1 - gListY0, cWHT, 0);
    for (i = 0, y = gListY0; i < gVis && gTop[gScreen] + i < gNItem; i++, y += gRowH) {
        UInt16 it = gItem[gTop[gScreen] + i];
        if (gScreen == scrEsc) DrawEscRow(&gPl[it], y, right);
        else if (gScreen == scrTab) DrawTabRow(&gRows[it], y, right);
        else DrawNflRow(it, y, right);
    }
    DrawScrollbar();
}

static void PushButtons(Coord y) {
    static const Char *lab[2] = { "Meu time", "Adversário" };
    Coord x0 = 4, w = (gW - 8) / 2, i;
    for (i = 0; i < 2; i++) {
        Boolean sel = gSide == (UInt16)i;
        Box(x0 + i * w, y, w, 24, cNAVY, 0);
        if (!sel) Box(x0 + i * w + 1, y + 1, w - 2, 22, cWHT, 0);
        Txt(lab[i], x0 + i * w + w / 2, y + (24 - FH(boldFont)) / 2, boldFont, sel ? cWHT : cNAVY, sel ? cNAVY : cWHT, aC);
        AddHot(x0 + i * w, y, w, 24, actSide, i);
    }
}

static void DrawListScreen(void) {
    Char b[40]; Coord hy;
    Box(0, 0, gW, gH, cWHT, 0);
    gNHot = 0;
    if (gScreen == scrEsc) Title("Escalação");
    else if (gScreen == scrTab) Title("Tabela");
    else { Title("NFL"); StrCopy(b, "Semana "); CatN(b, sizeof(b), gWeek); if (gHasData) Txt(b, gW - 6, (24 - FH(boldFont)) / 2, boldFont, cNAVY, cWHT, aR); }
    if (gScreen != scrNfl) LeaguePopup();
    SyncBar(26);
    hy = 54;
    if (gScreen == scrEsc && gNL) {
        League *L = &gLgs[gLg]; Coord fh = FH(boldFont);
        PushButtons(hy); hy += 28;
        Box(4, hy, gW - 8, fh + 4, cNAVY, 0);
        b[0] = 0; CatC(b, sizeof(b), L->pts); Txt(b, 10, hy + 2, boldFont, gSide == 0 ? cWHT : cMINT, cNAVY, aL);
        if (L->hasOpp) {
            b[0] = 0; CatC(b, sizeof(b), L->opts); Txt(b, gW - 10, hy + 2, boldFont, gSide == 1 ? cWHT : cMINT, cNAVY, aR);
            if (!gDone && L->wp != 255) {
                Boolean fav = (L->wp >= 50);
                b[0] = 0; CatN(b, sizeof(b), L->wp); Cat(b, sizeof(b), fav ? "% fav" : "% azar");
                Txt(b, gW / 2, hy + 2, boldFont, fav ? cGOLD : RGB(255, 140, 140), cNAVY, aC);
            }
            else if (gDone) Txt(L->pts > L->opts ? "VITÓRIA" : L->pts < L->opts ? "DERROTA" : "EMPATE", gW / 2, hy + 2, boldFont,
                                L->pts > L->opts ? RGB(120, 230, 150) : RGB(255, 120, 120), cNAVY, aC);
        }
        hy += fh + 6;
        gRowH = 2 * FH(stdFont) - 4;
    } else if (gScreen == scrTab) {
        Coord fh = FH(boldFont);
        Box(0, hy, gW, fh + 2, cNAVY, 0);
        Txt("#", 24, hy + 1, boldFont, cWHT, cNAVY, aR); Txt("Time", 42, hy + 1, boldFont, cWHT, cNAVY, aL);
        Txt("V-D", 200, hy + 1, boldFont, cWHT, cNAVY, aC); Txt("PF", 262, hy + 1, boldFont, cWHT, cNAVY, aR);
        Txt("Seq", gW - 18, hy + 1, boldFont, cWHT, cNAVY, aR);
        hy += fh + 4;
        gRowH = FH(stdFont) + 2;
    } else gRowH = FH(stdFont) + 2;
    gListY0 = hy; gListY1 = gH - 44;
    gVis = (UInt16)((gListY1 - gListY0) / gRowH);
    gListY1 = gListY0 + gVis * gRowH;
    BuildItems();
    if (!gHasData) {
        Txt("Sem dados.", gW / 2, gListY0 + 40, boldFont, cBLK, cWHT, aC);
        Txt("Instale o FantasyDados.pdb", gW / 2, gListY0 + 66, stdFont, cGRY, cWHT, aC);
    } else if (!gNItem) Txt("Nada por aqui.", gW / 2, gListY0 + 40, boldFont, cGRY, cWHT, aC);
    else DrawList();
    Line(0, gH - 42, gW, gH - 42, cLGRY);
    Button(4, gH - 38, 92, 34, "Início", actHome);
    if (gScreen == scrEsc && gNL > 1) Button(102, gH - 38, 110, 34, "Outra liga", actNextLg);
    if (gScreen == scrTab && gNL > 1) Button(102, gH - 38, 110, 34, "Outra liga", actNextLg);
}

/* ---------- buffer fora da tela (igual ao Mengão 1.0.1+) ---------- */
static void FreeOff(void) { if (gOff) { WinDeleteWindow(gOff, false); gOff = NULL; } }
static WinHandle GetOff(void) {
    Err err = errNone; UInt16 old;
    if (gOff && gOffW == gW && gOffH == gH) return gOff;
    FreeOff();
    old = WinSetCoordinateSystem(kCoordinatesStandard);
    gOff = WinCreateOffscreenWindow(gW / 2, gH / 2, nativeFormat, &err);
    WinSetCoordinateSystem(old);
    if (err != errNone) gOff = NULL;
    if (gOff) { gOffW = gW; gOffH = gH; }
    return gOff;
}
static void Render(void (*fn)(void), Coord x, Coord y, Coord w, Coord h) {
    FormPtr frm = FrmGetActiveForm();
    WinHandle scr = frm ? FrmGetWindowHandle(frm) : WinGetDrawWindow(), off = GetOff();
    UInt16 old;
    WinSetDrawWindow(off ? off : scr);
    WinPushDrawState();
    old = WinSetCoordinateSystem(kCoordinatesNative);
    fn();
    WinSetCoordinateSystem(old);
    WinPopDrawState();
    if (off) {
        RectangleType r; r.topLeft.x = x; r.topLeft.y = y; r.extent.x = w; r.extent.y = h;
        WinSetDrawWindow(scr);
        WinPushDrawState();
        old = WinSetCoordinateSystem(kCoordinatesNative);
        WinCopyRectangle(off, scr, &r, x, y, winPaint);
        WinSetCoordinateSystem(old);
        WinPopDrawState();
    }
}
static void DrawScreen(void) { if (gScreen == scrHome) DrawHome(); else if (gScreen == scrHist) DrawHist(); else DrawListScreen(); }
static void Draw(void) { Render(DrawScreen, 0, 0, gW, gH); }
static void DrawListOnly(void) { Render(DrawList, 0, gListY0, gW, gListY1 - gListY0); }

/* ---------- ações ---------- */
static void Goto(UInt16 scr) {
    if (scr != gScreen) gTop[scr] = 0;
    gScreen = scr;
    Draw();
}
static void Scroll(Int16 delta) {
    if (gScreen == scrHome || gScreen == scrHist || gNItem <= gVis) return;
    gTop[gScreen] += delta;
    DrawListOnly();
}
static void NextLeague(void) {
    if (gNL < 2) return;
    gLg = (gLg + 1) % gNL; gTop[scrEsc] = gTop[scrTab] = 0;
    Draw();
}

static void ShowAboutData(void) {
    Char a[40], b[24]; DateTimeType dt;
    if (!gHasData) { FrmCustomAlert(AboutDataAlert, "sem dados", "-", "-"); return; }
    TimSecondsToDateTime(gSync, &dt);
    StrCopy(a, kWd[dt.weekDay % 7]); Cat(a, sizeof(a), " "); Cat2(a, sizeof(a), dt.day); Cat(a, sizeof(a), "/"); Cat2(a, sizeof(a), dt.month); Cat(a, sizeof(a), "/"); CatN(a, sizeof(a), dt.year);
    Cat(a, sizeof(a), " "); Cat2(a, sizeof(a), dt.hour); Cat(a, sizeof(a), "h"); Cat2(a, sizeof(a), dt.minute);
    StrCopy(b, "");  CatN(b, sizeof(b), gWeek);
    Cat(b, sizeof(b), gEstado == EST_DONE ? " · encerrada" : (gEstado == EST_NEXT ? " · próxima" : " · em andamento"));
    if (gSim) Cat(b, sizeof(b), " (SIMULADO)");
    FrmCustomAlert(AboutDataAlert, a, b, gUser);
}

static Boolean HandlePen(Coord x, Coord y) {
    UInt16 i;
    for (i = 0; i < gNHot; i++) {
        Hot *h = &gHot[i];
        if (x >= h->x && x < h->x + h->w && y >= h->y && y < h->y + h->h) {
            switch (h->action) {
                case actHome: Goto(scrHome); break;
                case actEsc:  gLg = h->arg < gNL ? h->arg : 0; gSide = 0; gTop[scrEsc] = 0; gScreen = scrEsc; Draw(); break;
                case actTab:  Goto(scrTab); break;
                case actNfl:  Goto(scrNfl); break;
                case actHist:
                    if (h->arg > 0 && gScreen == scrHist) { gHistWeek = (UInt8)h->arg; Draw(); }
                    else {
                        { UInt8 mn, mx; HistWeekBounds(&mn, &mx); if (mx) gHistWeek = mx; }
                        Goto(scrHist);
                    }
                    break;
                case actHistPrev: {
                    UInt8 mn, mx; HistWeekBounds(&mn, &mx);
                    if (gHistWeek > mn) { gHistWeek--; Draw(); }
                    break; }
                case actHistNext: {
                    UInt8 mn, mx; HistWeekBounds(&mn, &mx);
                    if (gHistWeek < mx) { gHistWeek++; Draw(); }
                    break; }
                case actSide: if (gSide != h->arg) { gSide = h->arg; gTop[scrEsc] = 0; Draw(); } break;
                case actNextLg: NextLeague(); break;
            }
            return true;
        }
    }
    if (gScreen != scrHome && gScreen != scrHist && y >= gListY0 && y < gListY1 && gVis && x >= gW - 16) {
        Scroll((y < (gListY0 + gListY1) / 2) ? -(Int16)(gVis - 1) : (Int16)(gVis - 1));
        return true;
    }
    return false;
}

/* ---------- PINS (área de Graffiti virtual / 320x480) ---------- */
static void ResizeForm(FormPtr frm) {
    Coord w, h; RectangleType r;
    WinGetDisplayExtent(&w, &h);
    r.topLeft.x = 0; r.topLeft.y = 0; r.extent.x = w; r.extent.y = h;
    WinSetBounds(FrmGetWindowHandle(frm), &r);
    gW = w * 2; gH = h * 2;
}

static Boolean MainHandleEvent(EventPtr e) {
    FormPtr frm = FrmGetActiveForm();
    switch (e->eType) {
        case frmOpenEvent:
            if (gPINS) {
                WinSetConstraintsSize(FrmGetWindowHandle(frm), 160, 240, 240, 160, 160, 160);
                FrmSetDIAPolicyAttr(frm, frmDIAPolicyCustom);
                PINSetInputTriggerState(pinInputTriggerEnabled);
                PINSetInputAreaState(pinInputAreaClosed);
            }
            ResizeForm(frm);
            FrmDrawForm(frm);
            Draw();
            return true;
        case frmUpdateEvent:
            Draw();
            return true;
        case winDisplayChangedEvent: {
            Coord ow = gW, oh = gH;
            ResizeForm(frm);
            if (gW != ow || gH != oh || !gOff) Draw();
            return true;
        }
        case frmCloseEvent:
            FreeOff();
            return false;
        case penDownEvent:
            return HandlePen(e->screenX * 2, e->screenY * 2);
        case keyDownEvent:
            if (e->data.keyDown.chr == vchrPageUp) {
                if (gScreen == scrHist) {
                    UInt8 mn, mx; HistWeekBounds(&mn, &mx);
                    if (gHistWeek > mn) { gHistWeek--; Draw(); }
                } else if (gScreen == scrHome) { gScreen = scrEsc; Draw(); }
                else Scroll(-(Int16)(gVis - 1));
                return true;
            }
            if (e->data.keyDown.chr == vchrPageDown) {
                if (gScreen == scrHist) {
                    UInt8 mn, mx; HistWeekBounds(&mn, &mx);
                    if (gHistWeek < mx) { gHistWeek++; Draw(); }
                } else if (gScreen == scrHome) { gScreen = scrEsc; Draw(); }
                else Scroll((Int16)(gVis - 1));
                return true;
            }
            return false;
        case menuEvent:
            switch (e->data.menu.itemID) {
                case MenuHome:    Goto(scrHome); return true;
                case MenuEsc:     Goto(scrEsc);  return true;
                case MenuTab:     Goto(scrTab);  return true;
                case MenuNfl:     Goto(scrNfl);  return true;
                case MenuHist: {
                    UInt8 mn, mx; HistWeekBounds(&mn, &mx); if (mx) gHistWeek = mx;
                    Goto(scrHist); return true; }
                case MenuLiga:    NextLeague();  return true;
                case MenuAboutData: ShowAboutData(); return true;
                case MenuUpdate:  FrmAlert(UpdateAlert); return true;
                case MenuAbout:   FrmAlert(AboutAlert); return true;
            }
            return false;
        default:
            return false;
    }
}

static Boolean AppHandleEvent(EventPtr e) {
    if (e->eType == frmLoadEvent) {
        FormPtr frm = FrmInitForm(e->data.frmLoad.formID);
        FrmSetActiveForm(frm);
        FrmSetEventHandler(frm, MainHandleEvent);
        return true;
    }
    return false;
}

static void EventLoop(void) {
    EventType e; Err err;
    do {
        EvtGetEvent(&e, evtWaitForever);            /* nada anima: sem nilEvent, sem redesenho à toa */
        if (SysHandleEvent(&e)) continue;
        if (MenuHandleEvent(0, &e, &err)) continue;
        if (AppHandleEvent(&e)) continue;
        FrmDispatchEvent(&e);
    } while (e.eType != appStopEvent);
}

static Boolean CheckHiRes(void) {
    UInt32 v = 0, dens = 0;
    if (FtrGet(sysFtrCreator, sysFtrNumWinVersion, &v) != errNone || v < 4) return false;
    if (WinScreenGetAttribute(winScreenDensity, &dens) != errNone) return false;
    return dens >= kDensityDouble;
}

UInt32 PilotMain(UInt16 cmd, MemPtr pbp, UInt16 flags) {
    UInt32 v;
    if (cmd != sysAppLaunchCmdNormalLaunch) return 0;
    if (!CheckHiRes()) { FrmAlert(NoHiResAlert); return 0; }
    gPINS = (FtrGet(pinCreator, pinFtrAPIVersion, &v) == errNone);
    LoadData();
    FrmGotoForm(MainForm);
    EventLoop();
    FrmCloseAllForms();
    FreeOff();
    FreeData();
    return 0;
}
