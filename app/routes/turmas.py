from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Curso, DIAS_SEMANA, Turma
from services.validacao import validar_turma

turmas_bp = Blueprint("turmas", __name__)


@turmas_bp.route("/turmas")
def listar():
    turmas = Turma.query.order_by(Turma.nome).all()
    return render_template("turmas/listar.html", turmas=turmas)


@turmas_bp.route("/turmas/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST" and _salvar_turma(None):
        return redirect(url_for("turmas.listar"))
    return render_template(
        "turmas/form.html",
        turma=None,
        cursos=_cursos_ativos(),
        dias_semana=DIAS_SEMANA,
    )


@turmas_bp.route("/turmas/<int:turma_id>/editar", methods=["GET", "POST"])
def editar(turma_id):
    turma = db.get_or_404(Turma, turma_id)
    if request.method == "POST":
        salvo, _ = _salvar_turma(turma)
        if salvo:
            return redirect(url_for("turmas.listar"))
        return render_template(
            "turmas/form.html",
            turma=_preencher_com_form(turma),
            cursos=_cursos_ativos(),
            dias_semana=DIAS_SEMANA,
        )
    return render_template(
        "turmas/form.html",
        turma=turma,
        cursos=_cursos_ativos(),
        dias_semana=DIAS_SEMANA,
    )


@turmas_bp.route("/turmas/<int:turma_id>/excluir", methods=["POST"])
def excluir(turma_id):
    turma = db.get_or_404(Turma, turma_id)
    db.session.delete(turma)
    db.session.commit()
    flash(f"Turma '{turma.nome}' removida.", "sucesso")
    return redirect(url_for("turmas.listar"))


def _salvar_turma(turma):
    (
        curso_id,
        nome,
        dia_semana,
        inicio,
        fim,
        ativa,
        erros,
    ) = validar_turma(request.form)

    if erros:
        for erro in erros:
            flash(erro, "erro")
        return False, None

    if turma is None:
        turma = Turma()
        db.session.add(turma)

    turma.curso_id = curso_id
    turma.nome = nome
    turma.dia_semana = dia_semana
    turma.horario_inicio = _parse_hora(inicio)
    turma.horario_fim = _parse_hora(fim)
    turma.ativa = ativa

    db.session.commit()
    flash("Turma salva.", "sucesso")
    return True, turma


def _preencher_com_form(turma):
    turma.curso_id = int(request.form.get("curso_id") or 0)
    turma.nome = request.form.get("nome", "")
    turma.dia_semana = request.form.get("dia_semana", "")
    turma.ativa = request.form.get("ativa") == "on"
    turma.horario_inicio = _parse_hora(
        request.form.get("horario_inicio", "")
    )
    turma.horario_fim = _parse_hora(request.form.get("horario_fim", ""))
    return turma


def _cursos_ativos():
    return Curso.query.order_by(Curso.nome).all()


def _parse_hora(valor):
    if not valor:
        return None
    try:
        return datetime.strptime(valor, "%H:%M").time()
    except ValueError:
        return None