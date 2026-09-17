#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Copia de seguranca / restauracao do banco (SQLite) — Sistema de Chamadas

Exporta todo o banco (schema + dados) para um arquivo .sql na pasta seed/
e permite recriar o banco a partir desse arquivo.

O arquivo .sql gerado fica APENAS local e NAO vai para o GitHub (esta
excluido no .gitignore). Somente este script e versionado.

Uso:
    python seed_banco.py exportar                     raiz/seed/projeto_AAAA-MM-DD_HHMMSS.sql
    python seed_banco.py exportar --sem-copia         nao grava projeto_atual.sql
    python seed_banco.py restaurar seed/dados.sql     recria o banco (pede confirmacao)
    python seed_banco.py restaurar seed/dados.sql --sim
    python seed_banco.py resumo                       contagem de registros por tabela
"""

import sys
import sqlite3
import shutil
from datetime import datetime
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
DB_PATH = ROOT_DIR / "data" / "sistema.db"
SEED_DIR = ROOT_DIR / "seed"
BACKUPS_DIR = ROOT_DIR / "backups"


def _conectar(path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(path))


def _resumo(con: sqlite3.Connection) -> dict:
    tabelas = [
        r[0]
        for r in con.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    ]
    contagem = {}
    for tabela in tabelas:
        contagem[tabela] = con.execute(f"SELECT COUNT(*) FROM {tabela}").fetchone()[0]
    return contagem


def _imprimir_resumo(contagem: dict) -> None:
    if not contagem:
        print("  (sem tabelas)")
        return
    largura = max(len(t) for t in contagem)
    total = 0
    for tabela, qtd in contagem.items():
        print(f"  {tabela:<{largura}} : {qtd}")
        total += qtd
    print(f"  {'total':<{largura}} : {total}")


def exportar(sem_copia: bool = False) -> int:
    if not DB_PATH.exists():
        print("ERRO: banco nao encontrado em:")
        print(DB_PATH)
        print("Inicie o sistema pelo menos uma vez antes de exportar.")
        return 1

    SEED_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    destino = SEED_DIR / f"projeto_{timestamp}.sql"

    try:
        con = _conectar(DB_PATH)
        linhas = list(con.iterdump())
        con.close()
    except Exception as erro:
        print(f"ERRO ao ler o banco: {erro}")
        return 1

    with open(destino, "w", encoding="utf-8", newline="\n") as f:
        for linha in linhas:
            f.write(linha + "\n")

    print("[OK] Copia de seguranca gerada:")
    print(f"     {destino}")

    if not sem_copia:
        atual = SEED_DIR / "projeto_atual.sql"
        shutil.copy2(destino, atual)
        print(f"[OK] Copia 'mais recente' atualizada: {atual}")

    con = _conectar(DB_PATH)
    print("\nRegistros exportados:")
    _imprimir_resumo(_resumo(con))
    con.close()
    return 0


def restaurar(nome_arquivo: str, sem_confirmacao: bool = False) -> int:
    origem = ROOT_DIR / nome_arquivo
    if not Path(origem).exists():
        print(f"ERRO: arquivo nao encontrado: {origem}")
        return 1

    if DB_PATH.exists() and not sem_confirmacao:
        print("[!]  ATENCAO: esta operacao SUBSTITUI o banco atual.")
        print(f"   Banco atual : {DB_PATH}")
        print(f"   Fonte       : {origem}")
        resposta = input("\nDigite 'RESTAURAR' para confirmar: ").strip()
        if resposta != "RESTAURAR":
            print("\nOperacao cancelada.")
            return 1

    if DB_PATH.exists():
        BACKUPS_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        backup_atual = BACKUPS_DIR / f"sistema_pre_restauro_{timestamp}.db"
        shutil.copy2(DB_PATH, backup_atual)
        print(f"[OK] Banco atual preservado em: {backup_atual}")
        DB_PATH.unlink()

    try:
        sql = Path(origem).read_text(encoding="utf-8")
        con = _conectar(DB_PATH)
        con.executescript(sql)
        con.commit()
        resumo = _resumo(con)
        con.close()
    except Exception as erro:
        print(f"ERRO ao restaurar: {erro}")
        return 1

    print("[OK] Banco restaurado a partir de:")
    print(f"     {origem}")
    print("\nRegistros restaurados:")
    _imprimir_resumo(resumo)
    return 0


def resumo() -> int:
    if not DB_PATH.exists():
        print("ERRO: banco nao encontrado em:")
        print(DB_PATH)
        return 1
    con = _conectar(DB_PATH)
    _imprimir_resumo(_resumo(con))
    con.close()
    return 0


def _ajuda() -> None:
    print(__doc__)


def main() -> int:
    args = sys.argv[1:]
    if not args:
        _ajuda()
        return 0

    comando = args[0].lower()

    if comando == "exportar":
        return exportar(sem_copia="--sem-copia" in args)
    if comando == "restaurar":
        nomes = [a for a in args[1:] if not a.startswith("--")]
        if not nomes:
            print("ERRO: informe o arquivo .sql a restaurar.")
            print("  Ex.: python seed_banco.py restaurar seed/projeto_2026-09-17_HHMMSS.sql")
            return 1
        return restaurar(nomes[0], sem_confirmacao="--sim" in args)
    if comando == "resumo":
        return resumo()

    print(f"Comando desconhecido: {comando}")
    _ajuda()
    return 2


if __name__ == "__main__":
    sys.exit(main())