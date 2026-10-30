# Changelog

## v1.1.2 — 30/10/2026
- Barra de chance no Início: rótulo **Favorito** (≥50%, barra verde) ou **Azarão** (<50%, barra vermelha). Exatamente 50% = Favorito.
- Escalação (andamento): `% fav` / `% azar` no lugar de `% vitória`.
- Botões da barra inferior com largura pelo texto (margem ≥3px) — **Anterior** e **Início** não estouram mais a borda; NFL fica mais estreito.

## v1.1.1 — 29/10/2026
- Botões da barra inferior: **Escal.** / Tabela / NFL / Anterior (ou Início), com larguras iguais — cabem em 320×480 e 320×320.

## v1.1.0 — 29/10/2026
- Depois que a rodada fecha, o **Início** mostra a **próxima** semana (projeções, % vitória, adversário, 1º jogo).
- 4º botão **Anterior**: histórico de **todas** as rodadas já jogadas na temporada (as duas ligas).
- Navegação `‹ Sem N ›`, botões físicos cima/baixo e faixa compacta V/D.
- PDB **FNT2** com registro de histórico. PDB FNT1 antigo → mensagem "Atualize os dados".
- `gerar_dados.py` busca matchups de todas as semanas concluídas; posição no histórico recalculada pelos placares (o Sleeper não expõe rank por semana).
- `make data` continua igual (mesmo comando / `FANTASY_CONFIG` / `config.local.json`).

## v1.0.2 — 29/10/2026
- `Cat` / `CatN` / `Cat2` / `CatC` / `CatD` agora respeitam o tamanho do buffer.
- `gHasData` fica falso se o PDB não tiver ligas.


## v1.0.1 — 28/10/2026
- Remove dados pessoais do repositório e das prévias (usuário, ligas e times de demonstração são fictícios).
- Usuário do Sleeper configurável: `--usuario`, `--config`, `FANTASY_CONFIG` ou `config.local.json` (veja `config.example.json`). Sem default pessoal no código.
- Ligas e siglas vêm do config (opcional); se omitidas, o gerador lista as ligas do usuário em ordem alfabética.
- `make preview` usa `tools/gerar_demo.py` (PDB fictício), sem chamar a API do Sleeper.
- `make data` continua gerando o seu `FantasyDados.pdb` a partir do config local (ignorado pelo git).

## v1.0.0 — 25/10/2026
Primeira versão, no formato "resumo da rodada", sem ao vivo. Segue os mockups v2 aprovados.
- **Telas:** Início (até duas ligas), Escalação (meu time/adversário, troca de liga), Tabela (com ▲▼ desde a rodada anterior) e Jogos da NFL da semana (horário de Brasília).
- **Faixa "Dados de …"** com o selo *andamento* ou *encerrada* em todas as telas. Com a rodada encerrada: VITÓRIA/DERROTA, recorde e posição novos.
- **Menus:** Dados (*Sobre os dados*, *Como atualizar*) e Opções.
- **Gerador `tools/gerar_dados.py`:** busca os dados no Sleeper e na ESPN, sem baixar a lista inteira de jogadores.
  - `make data` grava também `FantasyDados-AAAA-MM-DD.pdb`.
  - `--simular-fim` gera um arquivo de teste marcado como SIMULADO.
- **Sem piscar:** buffer fora da tela e nenhum redesenho em evento ocioso.
- 320×480 (T3 com o slider aberto) e 320×320.
- Creator ID `FNFL`.
