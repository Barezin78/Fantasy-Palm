/* prévia no computador: compila o código real do app (src/main.c, já em CP1252) contra um shim e grava as operações de desenho */
#include "main.c"
int main(int argc, char **argv) {
    /* uso: sim pdb|- altura tela [liga|semanaHist lado topo] > ops */
    gPdbPath = strcmp(argv[1], "-") ? argv[1] : NULL;
    gH = atoi(argv[2]); gScreen = atoi(argv[3]);
    shimNow = (UInt32)(time(NULL) - 3 * 3600) + P1904;
    gOps = stdout;
    LoadData();
    if (gScreen == scrHist) {
        if (argc > 4 && atoi(argv[4]) > 0) gHistWeek = (UInt8)atoi(argv[4]);
    } else {
        if (argc > 4) gLg = atoi(argv[4]);
        if (gLg >= gNL) gLg = 0;
    }
    if (argc > 5) gSide = atoi(argv[5]);
    Draw();
    if (argc > 6 && atoi(argv[6])) { gOps = fopen("/dev/null", "w"); Scroll(atoi(argv[6])); gOps = stdout; DrawListOnly(); }
    if (argc > 7 && !strcmp(argv[7], "sobre")) ShowAboutData();
    FreeData();
    return 0;
}
