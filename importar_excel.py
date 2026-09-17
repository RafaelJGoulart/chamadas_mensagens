# -*- coding: utf-8 -*-
"""Importa os export do Microcamp (Export_F10.xlsx e "Export_F10 - Chamadas.xlsx")
para o banco do Sistema de Chamadas, substituindo todos os dados atuais.

Uso:
    python importar_excel.py

O script apaga TODAS as tabelas e importa os dados reais:
- Um curso "Informatica" e as 7 turmas dos export (nome = codigo da coluna Turma);
- Todos os alunos (unicos por nome), com responsavel e ate 3 telefones;
- Uma matricula por aluno/turma (ativa so quando o Status Contrato e 'Ativo');
- As chamadas e presencas do mes (datas unicas, 1 = frequente, 0 = ausente).
"""
import re
import sys
from datetime import datetime
from pathlib import Path

import openpyxl

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "app"))

from extensions import db  # noqa: E402
from app import create_app  # noqa: E402
from models import (  # noqa: E402
    AUSENTE,
    Aluno,
    Chamada,
    Contato,
    Curso,
    FREQUENTE,
    Matricula,
    Presenca,
    Turma,
)

CADASTRO = RAIZ / "Export_F10.xlsx"
CHAMADAS = RAIZ / "Export_F10 - Chamadas.xlsx"

NOME_CURSO = "Informatica"
CONTRATO_ATIVO = "Ativo"

DIAS = ["segunda", "terca", "quarta", "quinta", "sexta", "sabado", "domingo"]


def limpar_telefone(valor):
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    if not texto or texto.lower().startswith("n"):
        return None
    texto = re.split(r"[;|]", texto)[0].strip()
    return texto or None


def limpar_fio_nome(valor):
    if not isinstance(valor, str):
        return None
    texto = valor.strip()
    return texto or None


def ler_cadastro(caminho):
    """Retorna: nome_da_turma -> lista de dicts (linha por aluno/turma)."""
    wb = openpyxl.load_workbook(caminho, data_only=True)
    saida = {}
    for nome in wb.sheetnames:
        ws = wb[nome]
        linhas = []
        for r in ws.iter_rows(min_row=2, values_only=True):
            if not r[0]:
                continue
            linhas.append(
                {
                    "aluno": r[0].strip(),
                    "titular": limpar_fio_nome(r[1]),
                    "codigo_turma": (r[4] or "").strip() if isinstance(r[4], str) else r[4],
                    "entrada": r[9],
                    "tel_aluno": r[10],
                    "cel_aluno": r[11],
                    "tel_titular": r[13],
                    "cel_titular": r[14],
                    "com_titular": r[15],
                    "com_aluno": r[16],
                    "status_contrato": (r[3] or "").strip() if isinstance(r[3], str) else r[3],
                }
            )
        saida[nome] = linhas
    wb.close()
    return saida


def ler_chamadas(caminho):
    """Retorna: nome_da_turma -> {'datas': [date...], 'notas': {aluno: {date: 0|1}}}."""
    wb = openpyxl.load_workbook(caminho, data_only=True)
    saida = {}
    for nome in wb.sheetnames:
        ws = wb[nome]
        linhas = list(ws.iter_rows(values_only=True))
        hdr = linhas[0]
        datas = []
        for h in hdr[1:]:
            if not isinstance(h, datetime):
                continue
            d = h.date()
            if d not in datas:
                datas.append(d)
        notas = {}
        for r in linhas[1:]:
            if not r or not r[0]:
                continue
            cel = {datas[j]: r[1 + j] for j in range(len(datas))}
            notas[r[0].strip()] = cel
        saida[nome] = {"datas": datas, "notas": notas}
    wb.close()
    return saida


def telefones_do_aluno(linha):
    if linha["titular"]:
        return (
            limpar_telefone(linha["tel_titular"]),
            limpar_telefone(linha["cel_titular"]),
            limpar_telefone(linha["com_titular"]),
        )
    return (
        limpar_telefone(linha["tel_aluno"]),
        limpar_telefone(linha["cel_aluno"]),
        limpar_telefone(linha["com_aluno"]),
    )


def principal():
    cad = ler_cadastro(CADASTRO)
    cha = ler_chamadas(CHAMADAS)

    app = create_app()
    with app.app_context():
        db.session.query(Presenca).delete()
        db.session.query(Matricula).delete()
        db.session.query(Chamada).delete()
        db.session.query(Contato).delete()
        db.session.query(Aluno).delete()
        db.session.query(Turma).delete()
        db.session.query(Curso).delete()
        db.session.commit()

        curso = Curso(nome=NOME_CURSO)
        db.session.add(curso)
        db.session.commit()

        turmas_por_sheet = {}
        for nome_sheet in cad:
            datas = cha.get(nome_sheet, {}).get("datas", [])
            dia_semana = DIAS[datas[0].weekday()] if datas else "segunda"
            codigo = None
            for linha in cad[nome_sheet]:
                if linha["codigo_turma"]:
                    codigo = linha["codigo_turma"]
                    break
            nome_turma = codigo or nome_sheet
            turma = Turma(
                curso_id=curso.id,
                nome=nome_turma,
                dia_semana=dia_semana,
                ativa=True,
            )
            db.session.add(turma)
            db.session.flush()
            turmas_por_sheet[nome_sheet] = turma

        alunos_por_nome = {}
        for nome_sheet, linhas in cad.items():
            for linha in linhas:
                nome = linha["aluno"]
                aluno = alunos_por_nome.get(nome)
                tel, cel, com = telefones_do_aluno(linha)
                entrada = linha["entrada"]
                if aluno is None:
                    aluno = Aluno(
                        nome=nome,
                        responsavel=linha["titular"],
                        telefone=tel,
                        celular=cel,
                        comercial=com,
                        data_matricula=entrada if isinstance(entrada, datetime) else datetime.today().date(),
                        status="inativo",
                    )
                    db.session.add(aluno)
                    db.session.flush()
                    alunos_por_nome[nome] = aluno
                else:
                    if aluno.responsavel is None and linha["titular"]:
                        aluno.responsavel = linha["titular"]
                    if aluno.telefone is None and tel:
                        aluno.telefone = tel
                    if aluno.celular is None and cel:
                        aluno.celular = cel
                    if aluno.comercial is None and com:
                        aluno.comercial = com
                    data_inicio = (
                        entrada if isinstance(entrada, datetime) else None
                    )
                    if data_inicio and (
                        aluno.data_matricula is None or data_inicio < aluno.data_matricula
                    ):
                        aluno.data_matricula = data_inicio
                if linha["status_contrato"] == CONTRATO_ATIVO:
                    aluno.status = "ativo"

        db.session.commit()

        matriculas_ativas = {}
        for nome_sheet, linhas in cad.items():
            turma = turmas_por_sheet[nome_sheet]
            for linha in linhas:
                aluno = alunos_por_nome[linha["aluno"]]
                matricula = Matricula(
                    aluno_id=aluno.id,
                    turma_id=turma.id,
                    data_inicio=(
                        linha["entrada"] if isinstance(linha["entrada"], datetime) else None
                    ),
                    ativa=linha["status_contrato"] == CONTRATO_ATIVO,
                )
                db.session.add(matricula)
                db.session.flush()
                if matricula.ativa:
                    matriculas_ativas[(turma.id, aluno.id)] = matricula

        chamadas_por_sheet = {}
        for nome_sheet, dados in cha.items():
            turma = turmas_por_sheet[nome_sheet]
            for data in dados["datas"]:
                chamada = Chamada(turma_id=turma.id, data=data)
                db.session.add(chamada)
                db.session.flush()
                chamadas_por_sheet.setdefault(nome_sheet, []).append(chamada)

        for nome_sheet, dados in cha.items():
            turma = turmas_por_sheet[nome_sheet]
            for chamada in chamadas_por_sheet.get(nome_sheet, []):
                for nome_aluno, cel in dados["notas"].items():
                    aluno = alunos_por_nome.get(nome_aluno)
                    if aluno is None:
                        continue
                    valor = cel.get(chamada.data)
                    if (turma.id, aluno.id) in matriculas_ativas:
                        estado = FREQUENTE if valor == 1 else AUSENTE
                        db.session.add(
                            Presenca(
                                chamada_id=chamada.id,
                                aluno_id=aluno.id,
                                estado=estado,
                            )
                        )
                    elif valor == 1:
                        db.session.add(
                            Presenca(
                                chamada_id=chamada.id,
                                aluno_id=aluno.id,
                                estado=AUSENTE,
                            )
                        )

        db.session.commit()

        total_alunos = len(alunos_por_nome)
        total_ativos = sum(1 for a in alunos_por_nome.values() if a.status == "ativo")
        total_matriculas = Matricula.query.count()
        total_chamadas = Chamada.query.count()
        total_presencas = Presenca.query.count()
        print(f"cursos: 1")
        print(f"turmas: {len(turmas_por_sheet)}")
        print(f"alunos unicos: {total_alunos} (ativos: {total_ativos})")
        print(f"matriculas: {total_matriculas}")
        print(f"chamadas: {total_chamadas}")
        print(f"presencas: {total_presencas}")
        print("Importacao concluida.")


if __name__ == "__main__":
    principal()