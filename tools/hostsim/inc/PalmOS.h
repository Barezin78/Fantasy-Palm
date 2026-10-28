/* Minimal host shim of the Palm OS APIs used by Fantasy — records draw ops for the preview renderer */
#ifndef SHIM_H
#define SHIM_H
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
typedef unsigned char UInt8; typedef signed char Int8; typedef unsigned short UInt16; typedef short Int16;
typedef unsigned int UInt32; typedef int Int32; typedef char Char; typedef unsigned char Boolean;
typedef Int16 Coord; typedef UInt16 Err; typedef void *MemPtr; typedef void *MemHandle; typedef void *DmOpenRef;
typedef UInt8 FontID; typedef void *FormPtr; typedef void *WinHandle;
#define true 1
#define false 0
#define NULL ((void*)0)
#define errNone 0
enum { stdFont = 0, boldFont = 1, largeFont = 2, largeBoldFont = 7 };
typedef struct { UInt8 index, r, g, b; } RGBColorType;
typedef struct { Coord x, y; } PointType;
typedef struct { PointType topLeft, extent; } RectangleType;
typedef struct { Int16 second, minute, hour, day, month, year, weekDay; } DateTimeType;
typedef struct { int eType; Coord screenX, screenY; union { struct { UInt16 chr; } keyDown; struct { UInt16 itemID; } menu; struct { UInt16 formID; } frmLoad; } data; } EventType;
typedef EventType *EventPtr;
#define kCoordinatesNative 0
#define kCoordinatesStandard 72
#define dmModeReadOnly 1
FILE *gOps;
static UInt32 shimFg, shimTx, shimBg; static FontID shimFont;
#include "fontw.h"
static const unsigned char *fw(void) { return shimFont == 1 ? kW1 : shimFont == 2 ? kW2 : shimFont == 7 ? kW7 : kW0; }
static UInt32 pack(const RGBColorType *c) { return ((UInt32)c->r << 16) | (c->g << 8) | c->b; }
static void WinSetForeColorRGB(const RGBColorType *c, RGBColorType *p) { shimFg = pack(c); }
static void WinSetTextColorRGB(const RGBColorType *c, RGBColorType *p) { shimTx = pack(c); }
static void WinSetBackColorRGB(const RGBColorType *c, RGBColorType *p) { shimBg = pack(c); }
static void WinDrawRectangle(const RectangleType *r, UInt16 cd) { fprintf(gOps, "R %d %d %d %d %d %06x\n", r->topLeft.x, r->topLeft.y, r->extent.x, r->extent.y, cd, shimFg); }
static void WinDrawLine(Coord a, Coord b, Coord c, Coord d) { fprintf(gOps, "L %d %d %d %d %06x\n", a, b, c, d, shimFg); }
static void FntSetFont(FontID f) { shimFont = f; }
static Int16 FntCharsWidth(const Char *s, Int16 n) { int w = 0, i; for (i = 0; i < n; i++) w += fw()[(UInt8)s[i]]; return w; }
static Int16 FntLineHeight(void) { return (shimFont == 2 || shimFont == 7) ? 28 : 22; }
static void WinDrawChars(const Char *s, Int16 n, Coord x, Coord y) {
    int i; fprintf(gOps, "T %d %d %d %06x %06x %d ", x, y, shimFont, shimTx, shimBg, FntCharsWidth(s, n));
    for (i = 0; i < n; i++) fprintf(gOps, "%02x", (UInt8)s[i]); fprintf(gOps, "\n"); }
static void WinEraseWindow(void) {}
static void WinPushDrawState(void) {} static void WinPopDrawState(void) {}
static UInt16 WinSetCoordinateSystem(UInt16 c) { return kCoordinatesStandard; }
static void MemMove(void *d, const void *s, Int32 n) { memmove(d, s, n); }
static void MemSet(void *d, Int32 n, UInt8 v) { memset(d, v, n); }
static void *MemPtrNew(UInt32 n) { return malloc(n); } static void MemPtrFree(void *p) { free(p); }
static Char *StrCat(Char *d, const Char *s) { return strcat(d, s); }
static Char *StrCopy(Char *d, const Char *s) { return strcpy(d, s); }
static Int16 StrLen(const Char *s) { return strlen(s); }
static Int16 StrCompare(const Char *a, const Char *b) { return strcmp(a, b); }
static Char *StrIToA(Char *d, Int32 n) { sprintf(d, "%d", n); return d; }
/* time: Palm seconds since 1904 local (Brasília, UTC-3) */
#define P1904 2082844800u
UInt32 shimNow;
static UInt32 TimGetSeconds(void) { return shimNow; }
static void TimSecondsToDateTime(UInt32 s, DateTimeType *d) { time_t t = (time_t)(s - P1904); struct tm tm; gmtime_r(&t, &tm);
    d->second = tm.tm_sec; d->minute = tm.tm_min; d->hour = tm.tm_hour; d->day = tm.tm_mday; d->month = tm.tm_mon + 1; d->year = tm.tm_year + 1900; d->weekDay = tm.tm_wday; }
/* Data Manager reading a .pdb file */
typedef struct { unsigned char *buf; long len; int n; } ShimDB; typedef struct { unsigned char *p; UInt32 sz; } ShimRec;
const char *gPdbPath; static ShimRec shimRecs[8];
static DmOpenRef DmOpenDatabaseByTypeCreator(UInt32 t, UInt32 c, UInt16 m) {
    static ShimDB db; FILE *f = gPdbPath ? fopen(gPdbPath, "rb") : NULL; int i; if (!f) return NULL;
    fseek(f, 0, SEEK_END); db.len = ftell(f); rewind(f); db.buf = malloc(db.len); fread(db.buf, 1, db.len, f); fclose(f);
    if (memcmp(db.buf + 60, "DATAFNFL", 8)) return NULL;
    db.n = (db.buf[76] << 8) | db.buf[77];
    for (i = 0; i < db.n && i < 8; i++) { unsigned char *e = db.buf + 78 + 8 * i; UInt32 o = (e[0] << 24) | (e[1] << 16) | (e[2] << 8) | e[3];
        UInt32 o2 = (i + 1 < db.n) ? (UInt32)((e[8] << 24) | (e[9] << 16) | (e[10] << 8) | e[11]) : (UInt32)db.len;
        shimRecs[i].p = db.buf + o; shimRecs[i].sz = o2 - o; }
    return &db; }
static UInt16 DmNumRecords(DmOpenRef d) { return ((ShimDB *)d)->n; }
static MemHandle DmQueryRecord(DmOpenRef d, UInt16 i) { return i < 8 ? &shimRecs[i] : NULL; }
static UInt32 MemHandleSize(MemHandle h) { return ((ShimRec *)h)->sz; }
static void *MemHandleLock(MemHandle h) { return ((ShimRec *)h)->p; }
static void MemHandleUnlock(MemHandle h) {}
static Err DmCloseDatabase(DmOpenRef d) { return 0; }
/* UI bits not exercised by the preview */
#define FrmCustomAlert(a, b, c, d) fprintf(stderr, "ALERT %d: %s | %s | %s\n", a, b, c, d)
#define FrmAlert(a) 0
#define FrmGetActiveForm() NULL
#define FrmGetWindowHandle(f) NULL
#define FrmDrawForm(f)
#define FrmInitForm(i) NULL
#define FrmSetActiveForm(f)
#define FrmSetEventHandler(f, h)
#define FrmGotoForm(f)
#define FrmCloseAllForms()
#define FrmDispatchEvent(e) 0
#define FrmGetActiveFormID() 1000
#define SysHandleEvent(e) 0
#define MenuHandleEvent(a, e, r) 0
#define EvtGetEvent(e, t) ((e)->eType = 0)
#define SysTicksPerSecond() 100
#define WinGetDisplayExtent(w, h) (*(w) = 160, *(h) = 240)
#define WinSetBounds(w, r)
#define WinSetConstraintsSize(a, b, c, d, e, f, g) 0
#define FrmSetDIAPolicyAttr(f, p) 0
#define PINSetInputTriggerState(s) 0
#define PINSetInputAreaState(s) 0
#define FtrGet(a, b, v) (*(v) = 4, 0)
#define WinScreenGetAttribute(a, v) (*(v) = 144, 0)
#define evtWaitForever (-1)
#define nilEvent 0
#define appStopEvent 0
enum { frmLoadEvent = 100, frmOpenEvent, frmUpdateEvent, penDownEvent, keyDownEvent, menuEvent };
#define winDisplayChangedEvent 0x4101
#define vchrPageUp 0x0B
#define vchrPageDown 0x0C
#define sysAppLaunchCmdNormalLaunch 0
#define sysFtrCreator 0
#define sysFtrNumWinVersion 0
#define winScreenDensity 0
#define kDensityDouble 144
#define frmDIAPolicyCustom 1
#define pinInputTriggerEnabled 0
#define pinInputAreaClosed 0
#define pinCreator 0
#define pinFtrAPIVersion 0
/* offscreen (v1.0.1): no preview, o "buffer" grava as mesmas operações de desenho */
enum { screenFormat = 0, genericFormat, nativeFormat };
enum { winPaint = 0 };
static int shimOffWin; static WinHandle shimDraw;
static WinHandle WinCreateOffscreenWindow(Coord w, Coord h, int fmt, UInt16 *err) { *err = 0; return &shimOffWin; }
static void WinDeleteWindow(WinHandle w, Boolean e) {}
static WinHandle WinGetDrawWindow(void) { return shimDraw; }
static WinHandle WinSetDrawWindow(WinHandle w) { WinHandle o = shimDraw; shimDraw = w; return o; }
static void WinCopyRectangle(WinHandle s, WinHandle d, const RectangleType *r, Coord x, Coord y, int m) {}
#define frmCloseEvent 200
#define PilotMain PilotMain_unused
#endif
