from flask import Blueprint, flash, redirect, render_template, request, url_for

from extensions import db
from models import Curso, Materia
from services.materias import MATERIA_NEUTRA, ordenar_materias
from services.validacao import validar_materia

materias_bp = Blueprint("materias", __name__)


@materias_bp.route("/cursos/<int:curso_id>/materias")
def listar(curso_id):
    curso = db.get_or_404(Curso, curso_id)
    materias = ordenar_materias(
        Materia.query.filter_by(curso_id=curso.id).all()
    )
    return render_template("materias/listar.html", curso=curso, materias=materias)


@materias_bp.route(
    "/cursos/<int:curso_id>/materias/nova",
    methods=["GET", "POST"],
)
def novo(curso_id):
    curso = db.get_or_404(Curso, curso_id)
    if request.method == "POST":
        if _salvar_materia(None, curso):
            return redirect(url_for("materias.listar", curso_id=curso.id))
        return render_template(
            "materias/form.html",
            curso=curso,
            materia=None,
        )
    return render_template("materias/form.html", curso=curso, materia=None)


@materias_bp.route(
    "/materias/<int:materia_id>/editar",
    methods=["GET", "POST"],
)
def editar(materia_id):
    materia = db.get_or_404(Materia, materia_id)
    if request.method == "POST":
        if _salvar_materia(materia, materia.curso):
            return redirect(url_for("materias.listar", curso_id=materia.curso_id))
        return render_template(
            "materias/form.html",
            curso=materia.curso,
            materia=materia,
        )
    return render_template(
        "materias/form.html",
        curso=materia.curso,
        materia=materia,
    )


@materias_bp.route("/materias/<int:materia_id>/excluir", methods=["POST"])
def excluir(materia_id):
    materia = db.get_or_404(Materia, materia_id)
    curso_id = materia.curso_id
    if materia.chamadas.count():
        flash(
            f"Não é possível excluir '{materia.nome}': há chamadas lançadas "
            "nessa matéria. Mova as aulas para outra matéria antes.",
            "erro",
        )
        return redirect(url_for("materias.listar", curso_id=curso_id))
    db.session.delete(materia)
    db.session.commit()
    flash(f"Matéria '{materia.nome}' removida.", "sucesso")
    return redirect(url_for("materias.listar", curso_id=curso_id))


def _salvar_materia(materia, curso):
    nome, erros = validar_materia(request.form)

    if erros:
        for erro in erros:
            flash(erro, "erro")
        return False

    existe = Materia.query.filter_by(curso_id=curso.id, nome=nome).first()
    if existe is not None and (materia is None or existe.id != materia.id):
        flash("Já existe uma matéria com esse nome neste curso.", "erro")
        return False

    if materia is None:
        materia = Materia(curso_id=curso.id, nome=nome)
        db.session.add(materia)
    else:
        materia.nome = nome

    db.session.commit()
    flash("Matéria salva.", "sucesso")
    return True