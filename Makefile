# Fantasy (Sleeper) para Palm OS 5 — build com prc-tools-remix + pilrc
SDK      ?= sdk/sdk-5r3/include
INCS     := $(shell find $(SDK) -type d -printf "-I%p ")
CC       := m68k-palmos-gcc
CFLAGS   := -O2 -Wall -Wno-multichar -Ibuild $(INCS)
CREATOR  := FNFL
# Um lugar só: a linha VERSION em src/fantasy.rcp (ex.: VERSION 1 "1.0.1")
VERSION  := $(shell sed -n 's/^VERSION 1 "\([^"]*\)".*/\1/p' src/fantasy.rcp)
ifeq ($(strip $(VERSION)),)
$(error Não achei a linha VERSION em src/fantasy.rcp)
endif
# Config do Sleeper (usuário/ligas). Padrão: config.local.json (gitignored) ou FANTASY_CONFIG.
FANTASY_CONFIG ?= $(CURDIR)/config.local.json

all: dist/Fantasy.prc dist/Fantasy-v$(VERSION).prc

build/%.c: src/%.c | build
	iconv -f UTF-8 -t CP1252 $< > $@
build/fantasy.rcp: src/fantasy.rcp | build
	iconv -f UTF-8 -t CP1252 $< > $@
build/resource.h: src/resource.h | build
	cp $< $@

build/main.o: build/main.c build/resource.h
	$(CC) $(CFLAGS) -c $< -o $@
build/fantasy: build/main.o
	$(CC) $(CFLAGS) $^ -o $@

build/icons.stamp: tools/make_icons.py | build
	python3 tools/make_icons.py build && touch $@
build/res.stamp: build/fantasy.rcp build/resource.h build/icons.stamp
	cd build && rm -f *.bin && pilrc -q -I . fantasy.rcp > /dev/null && touch res.stamp

dist/Fantasy.prc: build/fantasy build/res.stamp | dist
	build-prc -o $@ -n Fantasy -c $(CREATOR) build/fantasy build/*.bin

# Mesmo PRC, com a versão no nome do arquivo. O banco interno continua "Fantasy".
dist/Fantasy-v$(VERSION).prc: dist/Fantasy.prc
	cp -f $< $@

# Gera dados reais do Sleeper — precisa de config com usuário (veja config.example.json).
data: | dist
	FANTASY_CONFIG="$(FANTASY_CONFIG)" python3 tools/gerar_dados.py dist/FantasyDados.pdb
	cp -f dist/FantasyDados.pdb "dist/FantasyDados-$$(date +%Y-%m-%d).pdb"

# PDB de demonstração (nomes fictícios) — vai no repo / previews públicos.
demo-data: | dist build
	python3 tools/gerar_demo.py build/demo.pdb
	python3 tools/gerar_demo.py build/demo-simulado.pdb --simular-fim

# Prévias no computador com dados FICTÍCIOS (não usa Sleeper).
preview: build/main.c build/resource.h demo-data
	$(MAKE) -C tools/hostsim -B sim
	python3 tools/hostsim/render.py build/demo.pdb build/demo-simulado.pdb
	python3 tools/make_sheets.py

check: all
	python3 tools/validar.py dist/Fantasy-v$(VERSION).prc build/demo.pdb

build dist:
	mkdir -p $@
clean:
	rm -rf build dist/Fantasy.prc dist/Fantasy-v*.prc tools/hostsim/sim
.PHONY: all data demo-data preview check clean
