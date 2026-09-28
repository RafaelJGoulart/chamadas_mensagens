# Contexto do Projeto — Sistema de Chamadas

Este arquivo resume o estado atual do projeto para que outro chat/agente
continue trabalhando sem precisar explorar o código do zero.

---

## 1. O que é

Sistema **local** de chamadas e frequência para turmas de Informática.
Usuário único (um professor), sem login, sem nuvem, sem APIs externas.
Roda em `http://127.0.0.1:5000`.

Tecnologias: Python 3.12, Flask 3.1.3, Flask-SQLAlchemy 3.1.1, SQLAlchemy 2.0.52,
SQLite, Jinja2, HTML/CSS/JS puros + ícones Feather (coleção original em
`feather/`; 26 copiados p/ `static/icons`, sprite embutido inline, sem CDNs).
Importação usa `openpyxl` (instalado à parte — **fora** do `requirements.txt`).

---

## 2. Status: EM EVOLUÇÃO (base concluída + matriz + contato + 3 fones + importação + seed + tema claro)

Módulos originais concluídos (15/15 OK na época). Depois, nesta sequência:
1. `iniciar.bat` refeito (1º plano, navegador com delay, `pause` no fim)
2. Dashboard horizontalizado (1320px, 4 cartões, grade 2 colunas)
3. Busca aproximada em Alunos → componentizada (`_pesquisa.html` + filtro no `app.js`)
4. Fluxo de chamadas: `/chamadas` redireciona p/ `/turmas`; botão Chamadas na turma
5. Percentuais com 1 casa (`round(1)` nos templates)
6. Aba Avisos (baixa frequência + wa.me) → **renomeada p/ Contato** (ícone `phone`)
7. Ícones Feather em `static/icons` + sprite inline + favicon `check-square`
8. **Matriz alunos × dias** substituiu o detalhe por chamada (removido)
9. **Lançamento inline** na matriz (painel + coluna Nova, sem tela nova)
10. **3 telefones** (telefone/celular/comercial) + migração automática
11. Modal de confirmação corrigido (faltava classe `aberto` — nada excluía)
12. Clique esquerdo travado na matriz (só botão direito altera estado)
13. Redesign UI (contraste 14/14 WCAG, tokens, componentes refinados)
14. **Importação real do sistema de vendas** (`importar_excel.py`): banco limpo dos
    dados de teste e populado com os alunos/turmas/chamadas dos exports
    `Export_F10.xlsx` + `Export_F10 - Chamadas.xlsx` (set/2026). Não-ativos
    que o F10 de chamadas marcou presentes (Rebecca/QA19 e Gustavo/SB1330)
    entram como **ausentes**, conforme decidido.
15. **Cópia/restauração do banco** (`seed_banco.py` + pasta `seed/`):
    `exportar` gera `.sql` (schema+dados) + `projeto_atual.sql`, `restaurar`
    recria o banco (com backup prévio), `resumo` conta registros. `.sql`
    **fora do Git** (`.gitignore`) — só local. Desde então o professor lançou
    novas chamadas pelo sistema (13 chamadas / 184 presenças em 17/09).
16. **Relatório em PDF** (`reportlab` + fontes Lato): botão **Relatório PDF**
    no Dashboard gera `GET /relatorio?mes=&ano=` com total de alunos, casos de
    coordenação, alunos frequentes/ausentes/sem dados, a **meta de presença**
    (todos exceto coordenação — percentuais sobre o total geral) e o
    detalhamento por turma. `reportlab==5.0.1` entrou no `requirements.txt`;
    fontes Lato (SIL OFL, uso comercial livre) baixadas em
    `app/static/fonts/` e embutidas no próprio PDF. Ícone `download`
    adicionado ao sprite (agora 22 ícones).
17. **Tela de Importação do sistema de vendas** (`/importacao`, ícone `upload`):
    a lógica do antigo `importar_excel.py` virou `app/services/importacao_excel.py`
    (chamável de qualquer lugar, com app context) e a tela faz o upload dos dois
    exports e **substitui todos os dados** — já gerando backup automático do
    banco em `backups/` (arquivo `sistema_pre_importacao_<data>.db`) antes de
    apagar. `openpyxl==3.1.5` entrou no `requirements.txt`. O CLI virou wrapper
    fino (`importar_excel.py`) que chama o mesmo serviço. Modal de confirmação
    agora aceita `data-confirma-titulo` (usado na importação). Dashboard: painéis
    de gráfico com altura adaptada ao conteúdo (`align-items: start`).

18. **Tema claro (`data-tema="claro"` no `<html>`)**: tokens novos em `style.css`
    (`:root[data-tema="claro"]`) — fundo quase branco `#f2f4f8`, superfícies
    brancas, textos escuros e versões **mais escuras** das semânticas
    (verde `#15803d`, azul `#2563eb`, amarelo `#b45309`, vermelho `#dc2626`,
    violeta `#7c3aed`, primária `#0b9e6e`) para contraste confortável. Também
    sobrescritas no claro as cores fixas que só valiam no escuro (topo
    translúcido, thead da tabela, anel de badges, brilhos/sombras, barras de
    gráfico, modal). `color-scheme: dark/light` conforme o tema. **Switch
    minimalista no rodapé** (`#alternar-tema`): pista com ícones **lua/sol**
    e bolinha deslizante; estado ativo fica destacado. `sun.svg` + `moon.svg`
    copiados de `feather/` p/ `static/icons` e adicionados ao sprite inline
    (agora **26 SVGs** + favicon). JS em `app.js` persiste em `localStorage`
    (`sistema_tema`), sincroniza `aria-pressed`/`aria-label` e o
    `meta theme-color`; script inline no `<head>` do `base.html` aplica o tema
    antes da pintura (sem flash). Padrão permanece **escuro**.

19. **Módulo "Matérias" dentro de cada curso** (ícone `layers`):
    - Modelo `Materia` (curso → matérias, `UniqueConstraint(curso_id, nome)`),
      `Chamada.materia_id` (nullable FK) + `ix_chamadas_data` no banco.
    - **Migração automática** (`_migrar_materias`, idempotente): cria a coluna
      `materia_id`, o índice por data e a matéria **"Neutra"** por curso,
      associa as chamadas antigas sem matéria a ela (todo curso ganha a "Neutra"
      para o sistema funcionar mesmo sem matérias cadastradas). O **seed das 12
      matérias padrão é feito SÓ no curso "Informatica"** (ordem canônica em
      `services/materias.py`) — cursos criados pelo usuário nascem apenas com a
      "Neutra" e as matérias de cada um são administradas pelo professor.
    - **Ordem de exibição**: as matérias aparecem sempre na ordem canônica
      (Windows, Illustrator, Photoshop, Word, Lógica de Programação, Scratch,
      HTML, Powerpoint, Express, XD, Dreamweaver, Excel), matérias extras em
      ordem alfabética e a **"Neutra" por último** (`ordenar_materias` —
      centralizado em `services/materias.py`, usado nas pills da matriz, nos
      selects de mover/novo e na tela de matérias).
    - Rotas `/cursos/<id>/materias` (lista/nova) e `/materias/<id>/editar|excluir`
      (excluir bloqueia se houver chamadas). CRUD segue o padrão das outras telas.
      O acesso fica em **Cursos** (botão "Matérias" por linha) e na tela de
      **Editar curso** (botão "Matérias" no cabeçalho).
    - **Matriz por matéria**: `/chamadas/turma/<id>?materia=<id>` mostra as
      colunas de **uma** matéria; o padrão é a matéria da última chamada (ou
      "Neutra"). Seletor de matérias em pills no topo da tela.
    - **Mover chamada entre matérias**: select "Mover…" no topo de cada coluna
      faz `POST /chamadas/<id>/materia/<mid>` (mesmo curso exigido; bloqueia
      duplicata turma/data/matéria) e recarrega a janela.
    - Lançamento (painel inline e tela `/nova`) agora pede a **matéria**;
      chamada lançada redireciona para a janela da própria matéria.
    - **Correções de desempenho aplicadas**: estatísticas mensais/relatório/
      baixa frequência usam **agregação SQL única** (`resumo_mensal_por_turma_aluno`,
      GROUP BY turma/aluno) — fim do N+1 por presença; a matriz carrega chamadas
      com `selectinload(presencas)` + mapa aluno→presença (≈4 consultas, antes
      eram 12+); regra de leitura sem efeito colateral (o backfill de ausentes
      saiu do GET e virou migração `_garantir_backfill_presencas` no startup).
    - **Proteção CSRF + chave secreta**: SECRET_KEY persistida em `data/secret_key`
      (ou env `SISTEMA_SECRET_KEY`); todo POST exige `csrf_token` (form) ou
      `X-CSRF-Token` (fetch) — 400 caso contrário. Todos os templates enviam o
      token (`{{ csrf_token() }}`) e o `base.html` injeta `window.CSRF_TOKEN`.
    - **Atenção (constraint)**: bancos que já existiam mantêm a unicidade física
      antiga `(turma_id, data)` — no banco atual não é possível criar duas
      chamadas na mesma data em matérias diferentes para a mesma turma (a nova
      única `(turma_id, data, materia_id)` só vale em bancos criados do zero).

> Tarefas adiadas de propósito (não implementar sem autorização): regras de
> aprovação/reprovação/limite de faltas.

---

## 3. Estrutura do projeto

```
SistemaChamadas/
├── app/
│   ├── app.py               → create_app(), 10 blueprints, db.create_all(), migrações no startup
│   │                          (_garantir_colunas_telefone, _migrar_materias, _garantir_backfill_presencas),
│   │                          CSRF em todo POST + SECRET_KEY em data/secret_key
│   ├── config.py            → caminhos relativos (Path), cria data/, backups/, logs/
│   ├── extensions.py        → db = SQLAlchemy()
│   ├── models/              → Curso, Turma, Aluno (3 fones), Matricula, Chamada, Presenca, Contato, Materia
│   ├── routes/              → cursos, turmas, alunos, matriculas, chamadas, dashboard, contato,
│   │                          relatorio, importacao, materias
│   ├── services/            → frequencia, estatisticas (+WhatsApp), validacao (+normalizar_busca),
│   │                          relatorio (dados) + pdf_relatorio (geração PDF),
│   │                          materias (ordem canônica), importacao_excel (upload do sistema de vendas)
│   ├── templates/           → base + _icones + _sprite + _pesquisa + pastas por módulo (incl. materias/)
│   └── static/
│       ├── css/style.css, js/app.js
│       ├── icons/ (26 SVGs + favicon)
│       └── fonts/ → Lato-Regular/Bold/Black.ttf (usadas no relatório PDF)
├── data/                    → sistema.db (migra sozinho: celular/comercial + matérias + backfill)
├── backups/                 → .db (backup.bat + pré-importação 2026-09-16; pre_migracao_telefones.db pode apagar após conferir)
├── logs/                    → reservado para logs
├── seed/                    → .sql locais (exportar/restaurar; fora do Git)
├── feather/                 → coleção original Feather (287 SVGs; fonte dos ícones usados em static/icons)
├── Export_F10*.xlsx         → exports do sistema de vendas (fonte da importação; fora do Git)
├── importar_excel.py        → LIMPA o banco e importa os exports do sistema de vendas (ver seção 4)
├── seed_banco.py            → exportar (.sql) / restaurar / resumo do banco
├── gerenciar_dados_teste.py → popular (3 fones) / resetar / resumo
├── iniciar.bat              → pendrive: 1º plano + abre navegador após 3s + pause
├── iniciar_debug.bat        → PC: python do PATH, 1º plano + pause
├── backup.bat               → copia data\sistema.db p/ backups\ (com timestamp)
└── requirements.txt / .gitignore / README.md / CONTEXT.md
```

---

## 4. Banco de dados (`data/sistema.db`)

> **Dados reais importados** (set/2026): um curso "Informatica", 7 turmas com o
> código oficial da coluna Turma (QAMC170002, QAMC190003, SBMC080005,
> SBMC100005, SBMC133005, SGMC170003, SGMC190004), 109 alunos únicos
> (99 ativos), 110 matrículas (99 ativas). Na importação: 12 chamadas e
> 170 presenças (166 do F10 + 4 AUSENTE para Rebecca/Gustavo-SB1330);
> em 17/09 o banco já tinha **13 chamadas / 184 presenças** (novas lançadas
> no sistema — os totais crescem com o uso). Matrícula `ativa`
> somente para Status Contrato = "Ativo". Prof. Rafael Jonathan Goulart.
> Backup pré-importação: `backups/sistema_pre_importacao_2026-09-16_184905.db`.
> Dias confirmados nos dados: QA=quarta, SB=**sábado**, SG=segunda.

### Aluno — 3 telefones
`telefone`, `celular`, `comercial` (String 30, anuláveis) + `responsavel` (nome).
`telefone_responsavel` **saiu do modelo** (coluna física antiga permanece ignorada
em bancos existentes — inofensiva; bancos novos nascem sem ela).
Migração idempotente no startup: `ADD COLUMN celular/comercial` + backfill
`celular = telefone_responsavel` (só onde vazio).

### Demais modelos
- **Curso**: nome único; cascade p/ turmas; `materias` (relação).
- **Turma**: dia_semana (check), horários Time, ativa.
- **Matricula**: aluno+turma, datas, ativa.
- **Materia**: curso→matérias; `UniqueConstraint(curso_id, nome)`; `chamadas`
  (relação; **sem cascade** — matéria com chamadas não pode ser apagada).
- **Chamada**: `materia_id` (nullable FK) + `Index(ix_chamadas_data)`; em bancos
  criados do zero vale `UniqueConstraint(turma_id, data, materia_id)`.
- **Presenca**: UniqueConstraint(chamada_id, aluno_id), estado IN
  ausente/frequente/reposicao. Cascade delete-orphan via Chamada.
- **Contato**: existe, **sem UI** (decisão da spec).

---

## 5. Rotas (10 blueprints)

| Módulo | Endpoints principais |
|---|---|
| Cursos | `/cursos`, `/cursos/novo`, `/cursos/<id>/editar`, `/cursos/<id>/excluir` |
| Turmas | `/turmas`, ... (Ações tem botão **Chamadas** primário) |
| Alunos | `/alunos` (aceita `?q=` aproximado), `/novo` (pode matricular na turma com ausências retroativas), `/editar`, `/excluir` |
| Matrículas | `/matriculas` (aceita `?q=` em aluno/turma/curso), `/novo`, ... |
| Chamadas | `/chamadas` → redirect `/turmas`; `/chamadas/turma/<id>` (**matriz**, aceita `?materia=`); `/nova` (pede matéria; erro volta p/ matriz); `/<id>/presenca/<aluno>` (POST JSON, usado pela matriz); `/<id>/materia/<mid>` (POST mover entre matérias); `/<id>/excluir` → matriz |
| Dashboard | `/` (`?mes=&ano=`, valida e volta ao atual se inválido) |
| Contato | `/contato` (`?mes=&ano=`; <50% no mês, sem flag) |
| Relatório | `/relatorio` (`?mes=&ano=`) → baixa PDF (reportlab, fontes Lato) com resumo geral, meta de presença e por turma |
| Importação | `/importacao` (GET form + POST upload dos 2 exports do sistema de vendas; substitui dados, com backup prévio) |
| Matérias | `/cursos/<id>/materias` (lista), `/cursos/<id>/materias/nova`, `/materias/<id>/editar`, `/materias/<id>/excluir` (bloqueia com chamadas) |

**REMOVIDO**: `/chamadas/<id>` (detalhe por chamada) + template + JS/CSS órfãos
(`seletor-estado`, `botao-menu`, `badge-presenca`, `chamada-tabela`, `resumo-badges`).
Grep de verificação: zero refs a `detalhe|seletor-estado|botao-menu`.

---

## 6. Serviços

### `frequencia.py`
`presencas_validas`, `percentual_frequencia` (round 1, None se 0),
`percentual_frequencia_totais(total, presentes)`, `aluno_frequente` (>= 50.0),
`contar_estados`.

### `estatisticas.py`
- `resumo_mensal_por_turma_aluno(ano, mes)` → **agregação SQL única**
  (GROUP BY turma/aluno): `{turma_id: {aluno_id: {total, presentes}}}` — base de
  dashboard, contato e relatório (fim do N+1 por presença).
- `estatisticas_mensais`, `indicadores_gerais`, `chamadas_recentes`
  (com `selectinload(presencas)`), `presencas_do_mes`, `alunos_com_flag_coordenacao`,
  `MESES`.
- WhatsApp: `_somente_digitos`, `telefone_para_whatsapp(tel, cel, com)` →
  `(numero, exibido, rotulo)` na ordem telefone→celular→comercial (+55);
  `numeros_whatsapp(...)` → 1 link wa.me por número válido;
  `mensagem_whatsapp`, `link_whatsapp`.
- `alunos_baixa_frequencia(ano, mes, 50.0)` → ativos, sem flag, pct<50,
  ordenado do pior; cada item tem `telefones[]` (rotulo/exibido/numero_wa/wa_link).

### `relatorio.py` + `pdf_relatorio.py`
- `dados_relatorio(ano, mes)` → alunos ativos (total), casos de coordenação,
  frequentes/ausentes/sem dados no mês, meta = total − coordenação (com % sobre
  o total geral), real = frequentes (com %), faltam = meta − real, e por turma
  (alunos ativos matriculados, mesmos indicadores a partir das chamadas da turma).
- `gerar_pdf(dados)` → PDF A4 paisagem no reportlab com resumo (5 cartões),
  tabela da meta e tabela por turma; fontes Lato embutidas de `app/static/fonts`.

### `validacao.py`
Validadores por entidade + `normalizar_texto` + `normalizar_busca`
(minúsculas sem acento — usada nas buscas de alunos e matrículas).

### `importacao_excel.py`
- Lê os dois exports (`Export_F10.xlsx` cadastro + `Export_F10 - Chamadas.xlsx`)
  com openpyxl e **substitui todos os dados** — num único commit (rollback em
  erro), com backup automático do banco atual em `backups/`.
- `importar(caminho_cadastro, caminho_chamadas)` → dict resumo
  (turmas/alunos/ativos/matriculas/chamadas/presencas/backup). Requer app
  context (rotas já têm; o CLI cria). Usada pela tela `/importacao` e pelo
  `importar_excel.py`.

---

## 7. Regras de frequência e matriz

```
frequência = (frequente + reposicao) / total   ·   >= 50% = frequente
```
- **Matriz** (`turma.html`): linhas = alunos ativos; colunas = chamadas em ordem
  cronológica; checkbox verde/amarela/vermelha; 1ª coluna sticky; últimas colunas
  Coordenação + Freq. total (recalculada ao vivo).
- **Estado só muda com botão direito** (menu 3 opções via
  `window.SistemaChamadas.abrirMenuEstado`); clique esquerdo/space é bloqueado
  (`preventDefault` + reversão). Exceção: coluna Nova e tela de lançamento.
- **Lançamento inline**: botão Nova chamada → `body.modo-lancar` (antigas
  esmaecidas) + painel (`form-lancar`: data de hoje, conteúdo, observação,
  Lançar/Todos/Nenhum/Cancelar) + coluna Nova binária (`form=` attr, sem forms
  aninhados). Sem amarelo no lançamento. POST erro → flash + redirect matriz.
- Lixeira no topo de cada coluna exclui (com confirmação).

---

## 8. Contato (`/contato`, ícone `phone`)

Tabela sem coluna de telefone: Aluno | Turmas | Frequência | Faltas | Ações.
Botão **Mensagem** abre modal com 1 link wa.me por número válido
(rotulado Telefone/Celular/Comercial) + prévia da mensagem; fecha com
Fechar/clique fora/Escape. Sem número → badge "Sem telefone".

---

## 9. Busca componentizada

`templates/_pesquisa.html`: macros `barra_pesquisa` + `contagem_pesquisa`.
Filtro instantâneo genérico no `app.js` via `data-filtro-tabela` (+ opcional
`data-filtro-contagem`); linha usa `data-filtro` ou texto próprio; linha
`.linha-sem-resultado` quando nada bate. Em uso: Alunos (por nome) e
Matrículas (aluno+turma+curso). Servidor filtra igual via `?q=`.

---

## 10. Interface / design system

- Escuro `#111418` e claro quase branco `#f2f4f8` (via `data-tema` no `<html>`),
  esmeralda `#10b981` (escuro) / `#0b9e6e` (claro), gradiente + brilho no primário.
- **Contraste WCAG medido por script (`contraste.py` no temp): 14/14 OK.**
- Tokens: superficies, `--borda`, `--entrada` (inputs), semânticas claras no
  escuro e versões mais escuras no claro, raios 14 (cards) / 9 (botões-inputs).
- Números tabulares globais (`tabular-nums` — cara de pauta); foco visível
  esmeralda; `::selection` esmeralda; scrollbars finas nas tabelas.
- Ícones: 26 Feather em `static/icons` + `_sprite.html` inline + macro
  `{{ icone("nome") }}` (currentColor, tamanhos 14/16/18/22); logo e favicon =
  `check-square` esmeralda. (Sprite externo foi removido — `<use>` externo não
  renderizava; inline é confiável.)
- Badges com anel interno + `gap:4px` p/ ícone; flashs com fundo tingido;
  barras 16px com trilho; tabelas com thead sutil e linhas respiradas.
- Acessibilidade: skip-link, aria-current, labels, `role=dialog`, Escape,
  `prefers-reduced-motion`. Responsivo (1000px e 640px).

---

## 11. Arquivos `.bat`

- **`iniciar_debug.bat`**: PC — `where python` → `python "app\app.py"` (1º plano) → `pause`.
- **`iniciar.bat`**: pendrive — acha `..\Python\python.exe` (sem letra fixa);
  erro claro se ausente; roda em 1º plano + abre navegador via PowerShell após
  3s + `pause`. **Não funciona no PC sem Python portátil** (use o debug).
- **`backup.bat`**: `data\sistema.db` → `backups\sistema_AAAA-MM-DD_HHMMSS.db`.

---

## 12. Como executar para testar

```bat
python app\app.py        :: ou iniciar_debug.bat
:: http://127.0.0.1:5000
```

Fluxo: Turmas → Chamadas (matriz) → Nova chamada (painel+coluna Nova) →
botão direito p/ editar → dashboard → Contato (modal wa.me).
`gerenciar_dados_teste.py`: popular (3 fones) / resetar (`RESETAR`) / resumo.

---

## 13. Próximos passos possíveis (só com autorização)

UI de Contato (tabela `contatos`); aprovação/reprovação/limite de faltas;
histórico individual; upload em massa; relatórios; `runtime/` proibido.

---

## 14. Importação do sistema de vendas (tela `/importacao` + CLI)

- A lógica vive em `app/services/importacao_excel.py`; a tela `/importacao`
  recebe os uploads dos dois exports e chama `importar()`. O CLI
  `importar_excel.py` é um wrapper fino que usa os arquivos da raiz — mesma
  função, outro front-end.
- **LIMPA o banco** antes de popular (substitui tudo, com backup automático
  em `backups/sistema_pre_importacao_<data>.db`) — re-executável, rollback em erro.
- Regras:
  - Turma é nomeada pelo código oficial da coluna "Turma" (ex.: QAMC170002);
    `dia_semana` é derivado das datas de chamada (QA=quarta, SB=**sábado**, SG=segunda).
  - Matrícula `ativa` só quando Status Contrato = "Ativo"; aluno `status=ativo`
    se tiver alguma matrícula ativa. Não-ativos listados nas chamadas do F10
    entram como **ausentes** (decisão do professor — não herdam o "1" do F10).
  - Colunas de dados duplicadas/None nas chamadas são ignoradas (mantém a 1ª);
    uniqueness `(turma, data)` e `(chamada, aluno)` é respeitada.
  - Telefones são limpos (corta sufixo após `;`/`|`, ignora "Não Cadastrado")
    e priorizam o responsável: `telefone`/`celular`/`comercial` do titular com
    fallback p/ números do próprio aluno; `responsavel` = nome do titular.
- Pós-importação recomendada: conferir backups/ (arquivo gerado), dashboard,
  relatório e contato.

## 15. Observações para o próximo agente

- Não instalar libs novas sem justificativa; não reescrever o que funciona.
- Dependências: `reportlab` (relatório PDF) e `openpyxl` (importação) estão no
  `requirements.txt`; as fontes Lato ficam em `app/static/fonts/` (SIL OFL) — o
  relatório PDF não depende de internet.
- `.sql` da pasta `seed/` e `*.xlsx` nunca vão ao Git (dados dos alunos).
- `.bat` sem letra fixa; janelas ficam abertas (1º plano + `pause`).
- Templates usam macros (`_icones`, `_pesquisa`); JS compartilhado no `app.js`.
- Scripts `teste_*.py` ficam em `C:\Users\ALUNO2\AppData\Local\Temp\opencode`
  (alguns antigos referenciam rotas removidas — conferir antes de reusar).
- Trabalhar em etapas pequenas e testáveis; informar arquivos, como testar e
  próximos passos.
