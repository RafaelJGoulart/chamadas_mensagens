# Sistema de Chamadas

Sistema local para controle de chamadas e frequência de turmas de Informática.

Sem login, sem nuvem, sem internet: tudo roda no computador em
`http://127.0.0.1:5000`.

---

## Funcionalidades

- Cadastro de cursos, turmas, alunos e matrículas;
- O cadastro do aluno já pode matriculá-lo numa turma (com ausência
  automática nas chamadas anteriores daquela turma);
- Cada aluno tem **3 telefones**: telefone, celular e comercial (+ nome do responsável);
- **Matriz de chamadas por turma**: nomes na 1ª coluna (fixa) e dias nas colunas
  seguintes, em ordem cronológica;
- Três estados de frequência por aula:
  - **ausente** — checkbox desmarcada com borda vermelha (falta);
  - **frequente** — checkbox marcada verde (presença);
  - **reposicao** — checkbox marcada amarela (presença, identificada);
- O estado **só muda com o botão direito** sobre a checkbox (menu com as 3 opções);
  clique esquerdo não altera nada;
- Últimas colunas da matriz: sinalização de coordenação e frequência total do aluno;
- **Lançamento dentro da matriz**: botão "Nova chamada" abre painel inline
  (data, conteúdo, observação) + coluna "Nova" binária (presente/falta, sem amarelo);
- Cálculo de frequência reutilizável:
  `frequência = (frequente + reposicao) / total de chamadas`;
- Dashboard mensal com gráficos (geral e por turma), seleção de mês/ano e
  indicadores — todos calculados dos dados reais do banco;
- Aba **Contato**: alunos ativos, sem flag de coordenação e com frequência
  **abaixo de 50% no mês**; botão Mensagem abre modal com um link **wa.me**
  por número válido (telefone → celular → comercial), com mensagem pronta;
- Barras de pesquisa aproximada (ignora acento/maiúsculas) em Alunos e Matrículas,
  com filtro instantâneo na tela;
- **Relatório em PDF** (botão "Relatório PDF" no Dashboard): mostra total de
  alunos, casos de coordenação, alunos frequentes/ausentes/sem dados no mês,
  a meta de presença (todos exceto coordenação) e o detalhamento por turma;
  fontes Lato (SIL OFL, uso comercial livre) embutidas em `static/fonts`;
- **Importação do Microcamp pela tela** (`/importacao`): envia os dois exports
  (`Export_F10.xlsx` e `Export_F10 - Chamadas.xlsx`) e substitui os dados do
  banco — com backup automático do banco atual em `backups/` antes de apagar;
- Aluno com sinalização para acompanhamento da coordenação (borda âmbar + badge).

### Regras principais

- Presenças válidas: **frequente** e **reposicao**; **ausente** não conta;
- Um aluno é **frequente no mês** com **50% ou mais** (50% exato = frequente);
- Unicidade: uma chamada por turma/data e uma presença por chamada/aluno;
- Reposição só existe depois da chamada lançada (nunca no lançamento);
- Sem regras de aprovação, reprovação ou limite de faltas (decisão de projeto);
- Percentuais sempre exibidos com no máximo 1 casa decimal.

---

## Como executar — no computador

### Pré-requisitos

- Python 3 instalado e acessível pelo comando `python`.

### Instalar dependências

Execute uma vez:

```bat
python -m pip install -r requirements.txt
```

### Iniciar

Dê dois cliques em:

```text
iniciar_debug.bat
```

ou execute no terminal:

```bat
python app\app.py
```

Depois abra `http://127.0.0.1:5000`. A janela fica aberta com os logs
enquanto o sistema roda (feche com `CTRL+C`).

---

## Como executar — no pendrive

No pendrive, o Python fica **fora** da pasta do sistema, em `Python\python.exe`.

### Estrutura esperada

```text
E:\
├── Python\
│   └── python.exe
│
└── SistemaChamadas\
    ├── app\
    ├── data\
    ├── backups\
    ├── logs\
    ├── iniciar.bat
    ├── iniciar_debug.bat
    ├── backup.bat
    ├── requirements.txt
    └── README.md
```

> A letra da unidade não importa (`E:`, `F:`, etc.). O `iniciar.bat` localiza o
> Python portátil subindo um nível a partir da própria pasta, sem usar letra
> fixa. Ele roda o servidor em primeiro plano (a janela fica aberta) e abre
> o navegador após 3 segundos.

### Iniciar

Insira o pendrive e dê dois cliques em `iniciar.bat`.

> `iniciar.bat` NÃO funciona no PC sem Python portátil ao lado — nele, use
> `iniciar_debug.bat`. Se o Python portátil não for encontrado, mensagem clara
> é exibida.

---

## Banco de dados

O banco SQLite é único e fica em:

```text
data\sistema.db
```

Todos os módulos usam o mesmo arquivo. O banco é criado automaticamente na
primeira execução, já com as colunas `telefone`, `celular` e `comercial` em
alunos. Bancos antigos são **migrados sozinhos** ao iniciar (cria as colunas e
copia o antigo `telefone_responsavel` para `celular`).

### Backup

```bat
backup.bat
```

Os arquivos ficam em `backups\sistema_AAAA-MM-DD_HHMMSS.db`.

### Restauração

Pare o sistema e copie um arquivo de `backups\` por cima de `data\sistema.db`:

```bat
copy /y "backups\sistema_2026-09-14_123000.db" "data\sistema.db"
```

### Cópia de segurança em .sql (exportar/restaurar)

```bat
python seed_banco.py exportar              :: gera seed\projeto_AAAA-MM-DD_HHMMSS.sql + atualiza seed\projeto_atual.sql
python seed_banco.py restaurar seed\projeto_atual.sql   :: recria o banco (pede RESTAURAR; preserva o atual em backups\)
python seed_banco.py resumo                :: contagem de registros por tabela
```

Os `.sql` ficam **só no computador** (fora do Git pelo `.gitignore`) — servem
para levar o banco pronto a outra máquina: copie o `.sql`, rode `restaurar` lá.

---

## Estrutura do projeto

```text
SistemaChamadas/
├── app/
│   ├── app.py            → criação da aplicação, registro dos módulos, migração de telefones
│   ├── config.py         → caminhos relativos (Path), banco, backups, logs
│   ├── extensions.py     → instância do SQLAlchemy
│   ├── models/           → modelos do banco (Curso, Turma, Aluno, ...)
│   ├── routes/           → rotas por módulo (blueprints: cursos, turmas, alunos,
│   │                       matrículas, chamadas, dashboard, contato, relatório, importação)
│   ├── services/         → frequência, estatísticas (+ WhatsApp), relatório (dados + PDF),
│   │                       importação do Microcamp
│   ├── templates/        → páginas Jinja2 (+ _icones, _sprite, _pesquisa)
│   └── static/
│       ├── css/style.css → design system (modo escuro, 14/14 contraste WCAG)
│       ├── js/app.js     → confirm, menu de presença, filtro de tabelas
│       ├── icons/        → 23 SVGs (Feather) + sprite embutido + favicon
│       └── fonts/        → Lato TTF (Regular/Bold/Black) usadas no relatório PDF
├── data/                 → banco SQLite
├── backups/              → cópias do banco
├── logs/                 → reservado para logs
├── iniciar.bat           → pendrive (1º plano, abre navegador)
├── iniciar_debug.bat     → desenvolvimento no PC
├── backup.bat            → cópia do banco
├── gerenciar_dados_teste.py → popular/resetar/resumo do banco
├── importar_excel.py        → importa os exports do Microcamp (CLI; mesmo código da tela /importacao)
├── seed_banco.py            → exportar/restaurar/resumo do banco (.sql em seed/)
├── seed/                    → cópias .sql do banco (somente local, fora do Git)
├── Export_F10*.xlsx         → exports originais (fonte da importação, fora do Git)
├── feather/                 → coleção original de ícones (fonte dos 21 em static/icons)
├── requirements.txt
├── .gitignore               → data/, backups/, seed/*.sql, *.xlsx e logs/ fora do Git
└── README.md
```

---

## Tecnologias

- Python, Flask, Flask-SQLAlchemy, SQLite, Jinja2
- HTML / CSS / JavaScript puros (sem frameworks externos)
- Ícones Feather copiados para `static/icons` e embutidos via sprite inline
  (mesma identidade no header e no favicon)

---

## Testes rápidos sugeridos

1. Iniciar com `iniciar_debug.bat` (ou `python app\app.py`);
2. Criar curso, turma e alunos (com os 3 telefones);
3. Matricular alunos (testar a busca em `/matriculas?q=`);
4. Na turma, clicar **Chamadas** → **Nova chamada**: preencher o painel e marcar
   a coluna Nova → Lançar;
5. Na matriz, testar o **botão direito** nas checkboxes (3 estados) e a lixeira
   da coluna;
6. Conferir dashboard do mês e a aba **Contato** (botão Mensagem → modal wa.me);
7. Testar `backup.bat`.

---

## Dados de teste

```bat
python gerenciar_dados_teste.py
```

Menu interativo: popular (20 alunos com 3 perfis de telefone), resetar (pede
`RESETAR`, com backup automático), resetar+popular, resumo.

---

## Importação de dados reais (Microcamp)

`openpyxl` está no `requirements.txt`.

Pela **tela do sistema** (`/importacao`): envie os dois arquivos e confirme —
o banco atual é copiado para `backups/` antes e depois os dados são
substituídos.

Pelo **terminal** (mesma lógica):

```bat
python importar_excel.py
```

Limpa o banco e importa os exports `Export_F10.xlsx` (cadastro) e
`Export_F10 - Chamadas.xlsx` (presenças do mês) que ficam na raiz (ou pela
tela, sem precisar deles na raiz).
Regras: turmas nomeadas pelo código oficial da coluna "Turma"; matrícula ativa
só com Status Contrato = "Ativo"; alunos não-ativos que o F10 marcou presentes
entram como **ausentes**; telefones limpos e priorizando o responsável.
Re-executável (sempre parte de um banco vazio).

> O banco atual já contém os dados reais de set/2026 (109 alunos, 7 turmas;
> 12 chamadas na importação, mais as lançadas desde então — 13 em 17/09).
> Não rode `gerenciar_dados_teste.py` se quiser manter esses dados.

---

## Manutenção / pendrive

- Não coloque o Python dentro de `SistemaChamadas` (fique fora, em `Python\`);
- Não use caminhos absolutos com letra fixa;
- Para atualizar o sistema, substitua apenas o conteúdo da pasta do projeto,
  preservando `data\` (banco) e `backups\`.
- O que vai para o GitHub: só o código. `data\`, `backups\`, `seed\*.sql`,
  `*.xlsx` e `logs\` ficam fora (ver `.gitignore`) — contêm dados dos alunos.
