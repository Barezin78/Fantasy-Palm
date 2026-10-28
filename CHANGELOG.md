# Changelog

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
