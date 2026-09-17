from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import AUSENTE, Aluno, Chamada, Matricula, Presenca, Turma
from services.validacao import normalizar_busca, validar_aluno

alunos_bp = Blueprint("alunos", __name__)


@alunos_bp.route("/alunos")
def listar():
    q = request.args.get("q", "").strip()
    alunos = Aluno.query.order_by(Aluno.nome).all()
    if q:
        q_norm = normalizar_busca(q)
        alunos = [a for a in alunos if q_norm in normalizar_busca(a.nome)]
    return render_template("alunos/listar.html", alunos=alunos, q=q)


@alunos_bp.route("/alunos/novo", methods=["GET", "POST"])
def novo():
    turmas = _turmas_ativas()
    if request.method == "POST":
        salvo, aluno_novo = _salvar_aluno(None)
        if salvo:
            _matricular_em_turma(aluno_novo, request.form.get("turma_id"))
            return redirect(url_for("alunos.listar"))
        return render_template(
            "alunos/form.html",
            aluno=None,
            turmas=turmas,
            turma_selecionada=request.form.get("turma_id", ""),
        )
    return render_template(
        "alunos/form.html", aluno=None, turmas=turmas, turma_selecionada=""
    )


@alunos_bp.route("/alunos/<int:aluno_id>/editar", methods=["GET", "POST"])
def editar(aluno_id):
    aluno = db.get_or_404(Aluno, aluno_id)
    if request.method == "POST":
        salvo, _ = _salvar_aluno(aluno)
        if salvo:
            return redirect(url_for("alunos.listar"))
        return render_template(
            "alunos/form.html",
            aluno=_preencher_com_form(aluno),
            turmas=_turmas_ativas(),
            turma_selecionada="",
        )
    return render_template(
        "alunos/form.html",
        aluno=aluno,
        turmas=_turmas_ativas(),
        turma_selecionada="",
    )


@alunos_bp.route("/alunos/<int:aluno_id>/excluir", methods=["POST"])
def excluir(aluno_id):
    aluno = db.get_or_404(Aluno, aluno_id)
    db.session.delete(aluno)
    db.session.commit()
    flash(f"Aluno '{aluno.nome}' removido.", "sucesso")
    return redirect(url_for("alunos.listar"))


def _salvar_aluno(aluno):
    (
        nome,
        telefone,
        celular,
        comercial,
        responsavel,
        flag_coordenacao,
        erros,
    ) = validar_aluno(request.form)

    if erros:
        for erro in erros:
            flash(erro, "erro")
        return False, None

    if aluno is None:
        aluno = Aluno(data_matricula=datetime.now().date())
        db.session.add(aluno)

    aluno.nome = nome
    aluno.telefone = telefone
    aluno.celular = celular
    aluno.comercial = comercial
    aluno.responsavel = responsavel
    aluno.flag_coordenacao = flag_coordenacao

    db.session.commit()
    flash("Aluno salvo.", "sucesso")
    return True, aluno


def _preencher_com_form(aluno):
    aluno.nome = request.form.get("nome", "")
    aluno.telefone = request.form.get("telefone", "") or None
    aluno.celular = request.form.get("celular", "") or None
    aluno.comercial = request.form.get("comercial", "") or None
    aluno.responsavel = request.form.get("responsavel", "") or None
    aluno.flag_coordenacao = request.form.get("flag_coordenacao") == "on"
    return aluno


def _turmas_ativas():
    return Turma.query.filter_by(ativa=True).order_by(Turma.nome).all()


def _matricular_em_turma(aluno, turma_id):
    """Matricula o aluno recém-criado e lança ausência nas chamadas passadas."""
    try:
        turma_id = int(turma_id or 0)
    except (TypeError, ValueError):
        return
    turma = db.session.get(Turma, turma_id)
    if turma is None or not turma.ativa:
        return
    matricula = Matricula(
        aluno_id=aluno.id,
        turma_id=turma.id,
        data_inicio=datetime.now().date(),
        ativa=True,
    )
    db.session.add(matricula)
    chamadas = Chamada.query.filter_by(turma_id=turma.id).all()
    for chamada in chamadas:
        db.session.add(
            Presenca(
                chamada_id=chamada.id,
                aluno_id=aluno.id,
                estado=AUSENTE,
            )
        )
    db.session.commit()
    if chamadas:
        flash(
            f"Aluno matriculado em '{turma.nome}' com ausência nas "
            f"{len(chamadas)} chamada(s) anteriores.",
            "info",
        )
    else:
        flash(f"Aluno matriculado em '{turma.nome}'.", "sucesso")