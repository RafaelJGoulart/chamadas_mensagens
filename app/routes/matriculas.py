from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Aluno, Matricula, Turma
from services.validacao import normalizar_busca, validar_matricula

matriculas_bp = Blueprint("matriculas", __name__)


def _texto_matricula(matricula):
    aluno = matricula.aluno.nome if matricula.aluno else ""
    turma = matricula.turma.nome if matricula.turma else ""
    curso = (
        matricula.turma.curso.nome
        if matricula.turma and matricula.turma.curso
        else ""
    )
    return normalizar_busca(f"{aluno} {turma} {curso}")


@matriculas_bp.route("/matriculas")
def listar():
    q = request.args.get("q", "").strip()
    matriculas = (
        Matricula.query.join(Aluno)
        .order_by(Aluno.nome)
        .all()
    )
    if q:
        q_norm = normalizar_busca(q)
        matriculas = [m for m in matriculas if q_norm in _texto_matricula(m)]
    return render_template("matriculas/listar.html", matriculas=matriculas, q=q)


@matriculas_bp.route("/matriculas/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST" and _salvar_matricula(None):
        return redirect(url_for("matriculas.listar"))
    return render_template(
        "matriculas/form.html",
        matricula=None,
        alunos=_alunos_ativos(),
        turmas=_turmas_ativas(),
    )


@matriculas_bp.route(
    "/matriculas/<int:matricula_id>/editar",
    methods=["GET", "POST"],
)
def editar(matricula_id):
    matricula = db.get_or_404(Matricula, matricula_id)
    if request.method == "POST":
        salvo, _ = _salvar_matricula(matricula)
        if salvo:
            return redirect(url_for("matriculas.listar"))
        return render_template(
            "matriculas/form.html",
            matricula=_preencher_com_form(matricula),
            alunos=_alunos_ativos(),
            turmas=_turmas_ativas(),
        )
    return render_template(
        "matriculas/form.html",
        matricula=matricula,
        alunos=_alunos_ativos(),
        turmas=_turmas_ativas(),
    )


@matriculas_bp.route(
    "/matriculas/<int:matricula_id>/excluir",
    methods=["POST"],
)
def excluir(matricula_id):
    matricula = db.get_or_404(Matricula, matricula_id)
    db.session.delete(matricula)
    db.session.commit()
    flash("Matrícula removida.", "sucesso")
    return redirect(url_for("matriculas.listar"))


def _salvar_matricula(matricula):
    aluno_id, turma_id, erros = validar_matricula(request.form)

    if erros:
        for erro in erros:
            flash(erro, "erro")
        return False, None

    aluno = db.session.get(Aluno, aluno_id)
    turma = db.session.get(Turma, turma_id)

    if aluno is None or turma is None:
        flash("Aluno ou turma inexistente.", "erro")
        return False, None

    if matricula is None:
        matricula = Matricula()
        db.session.add(matricula)

    matricula.aluno_id = aluno_id
    matricula.turma_id = turma_id
    matricula.ativa = request.form.get("ativa", "on") == "on"

    db.session.commit()
    flash("Matrícula salva.", "sucesso")
    return True, matricula


def _preencher_com_form(matricula):
    matricula.aluno_id = int(request.form.get("aluno_id") or 0)
    matricula.turma_id = int(request.form.get("turma_id") or 0)
    matricula.ativa = request.form.get("ativa") == "on"
    return matricula


def _alunos_ativos():
    return (
        Aluno.query.filter_by(status="ativo").order_by(Aluno.nome).all()
    )


def _turmas_ativas():
    return Turma.query.filter_by(ativa=True).order_by(Turma.nome).all()