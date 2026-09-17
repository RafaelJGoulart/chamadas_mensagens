from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Curso
from services.validacao import validar_nome_curso

cursos_bp = Blueprint("cursos", __name__)


@cursos_bp.route("/cursos")
def listar():
    cursos = Curso.query.order_by(Curso.nome).all()
    return render_template("cursos/listar.html", cursos=cursos)


@cursos_bp.route("/cursos/novo", methods=["GET", "POST"])
def novo():
    if request.method == "POST" and _salvar_curso(None):
        return redirect(url_for("cursos.listar"))
    return render_template("cursos/form.html")


@cursos_bp.route("/cursos/<int:curso_id>/editar", methods=["GET", "POST"])
def editar(curso_id):
    curso = db.get_or_404(Curso, curso_id)
    if request.method == "POST" and _salvar_curso(curso):
        return redirect(url_for("cursos.listar"))
    return render_template("cursos/form.html", curso=curso)


@cursos_bp.route("/cursos/<int:curso_id>/excluir", methods=["POST"])
def excluir(curso_id):
    curso = db.get_or_404(Curso, curso_id)
    db.session.delete(curso)
    db.session.commit()
    flash(f"Curso '{curso.nome}' removido.", "sucesso")
    return redirect(url_for("cursos.listar"))


def _salvar_curso(curso):
    nome, descricao, erros = validar_nome_curso(request.form)

    if erros:
        for erro in erros:
            flash(erro, "erro")
        return False

    if curso is None:
        curso = Curso()
        db.session.add(curso)

    curso.nome = nome
    curso.descricao = descricao or None

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        flash("Já existe um curso com esse nome.", "erro")
        return False

    flash("Curso salvo.", "sucesso")
    return True