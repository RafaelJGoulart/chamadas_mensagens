# -*- coding: utf-8 -*-
"""Importa os export do Microcamp (Export_F10.xlsx e "Export_F10 - Chamadas.xlsx")
para o banco do Sistema de Chamadas, substituindo todos os dados atuais.

Uso:
    python importar_excel.py

A lógica agora vive em app/services/importacao_excel.py e também está
disponível pela tela Importação do sistema (rota /importacao).
O script apaga TODAS as tabelas (com backup prévio em backups/) e importa:
- Um curso "Informatica" e as turmas dos export (nome = codigo da coluna Turma);
- Todos os alunos (unicos por nome), com responsavel e ate 3 telefones;
- Uma matricula por aluno/turma (ativa so quando o Status Contrato e 'Ativo');
- As chamadas e presencas do mes (datas unicas, 1 = frequente, 0 = ausente).
"""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "app"))

from app import create_app  # noqa: E402
from services.importacao_excel import importar  # noqa: E402

CADASTRO = RAIZ / "Export_F10.xlsx"
CHAMADAS = RAIZ / "Export_F10 - Chamadas.xlsx"


def principal():
    if not CADASTRO.exists():
        sys.exit(f"Arquivo não encontrado: {CADASTRO}")
    if not CHAMADAS.exists():
        sys.exit(f"Arquivo não encontrado: {CHAMADAS}")

    app = create_app()
    with app.app_context():
        resumo = importar(CADASTRO, CHAMADAS)

    print(f"turmas: {resumo['turmas']}")
    print(
        f"alunos unicos: {resumo['alunos']} "
        f"(ativos: {resumo['alunos_ativos']})"
    )
    print(f"matriculas: {resumo['matriculas']}")
    print(f"chamadas: {resumo['chamadas']}")
    print(f"presencas: {resumo['presencas']}")
    if resumo["backup"]:
        print(f"backup do banco anterior: backups/{resumo['backup']}")
    print("Importacao concluida.")


if __name__ == "__main__":
    principal()