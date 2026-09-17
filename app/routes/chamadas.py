from datetime import date, datetime

from flask import (
    Blueprint,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)

from extensions import db
from models import (
    Aluno,
    AUSENTE,
    Chamada,
    ESTADOS_PRESENCA,
    FREQUENTE,
    Matricula,
    Presenca,
    Turma,
)
from services.frequencia import percentual_frequencia

chamadas_bp = Blueprint("chamadas", __name__)


@chamadas_bp.route("/chamadas")
def listar():
    return redirect(url_for("turmas.listar"))


@chamadas_bp.route("/chamadas/turma/<int:turma_id>")
def por_turma(turma_id):
    turma = db.get_or_404(Turma, turma_id)
    chamadas = (
        Chamada.query.filter_by(turma_id=turma.id)
        .order_by(Chamada.data.asc(), Chamada.id.asc())
        .all()
    )
    for chamada in chamadas:
        _criar_presencas_faltantes(chamada)
    if chamadas:
        db.session.commit()

    alunos = _alunos_ativos_da_turma(turma.id)
    mapa = {}
    for chamada in chamadas:
        for presenca in chamada.presencas:
            mapa[(chamada.id, presenca.aluno_id)] = presenca

    linhas = []
    for aluno in alunos:
        presencas_aluno = [
            mapa.get((chamada.id, aluno.id)) for chamada in chamadas
        ]
        validas = [p for p in presencas_aluno if p is not None]
        linhas.append(
            {
                "aluno": aluno,
                "estados": [
                    p.estado if p is not None else AUSENTE
                    for p in presencas_aluno
                ],
                "total": len(validas),
                "percentual": percentual_frequencia(validas),
            }
        )

    return render_template(
        "chamadas/turma.html",
        turma=turma,
        chamadas=chamadas,
        linhas=linhas,
        hoje=date.today(),
    )


@chamadas_bp.route(
    "/chamadas/turma/<int:turma_id>/nova",
    methods=["GET", "POST"],
)
def nova(turma_id):
    turma = db.get_or_404(Turma, turma_id)
    alunos = _alunos_ativos_da_turma(turma.id)
    ids_validos = {aluno.id for aluno in alunos}
    dados = None

    if request.method == "POST":
        erro, dados = _ler_form_no_formato()
        if erro:
            flash(erro, "erro")
        else:
            existe = Chamada.query.filter_by(
                turma_id=turma.id,
                data=dados["data"],
            ).first()
            if existe:
                flash("Já existe uma chamada para essa turma nessa data.", "erro")
            else:
                chamada = Chamada(
                    turma_id=turma.id,
                    data=dados["data"],
                    conteudo=dados["conteudo"] or None,
                    observacao=dados["observacao"] or None,
                )
                db.session.add(chamada)
                db.session.commit()
                presentes = set()
                for valor in request.form.getlist("presente"):
                    try:
                        aluno_id = int(valor)
                    except (TypeError, ValueError):
                        continue
                    if aluno_id in ids_validos:
                        presentes.add(aluno_id)
                for aluno in alunos:
                    db.session.add(
                        Presenca(
                            chamada_id=chamada.id,
                            aluno_id=aluno.id,
                            estado=FREQUENTE
                            if aluno.id in presentes
                            else AUSENTE,
                        )
                    )
                db.session.commit()
                flash("Chamada lançada.", "sucesso")
                return redirect(
                    url_for("chamadas.por_turma", turma_id=turma.id)
                )

        return redirect(url_for("chamadas.por_turma", turma_id=turma.id))

    return render_template(
        "chamadas/nova.html",
        turma=turma,
        alunos=alunos,
        hoje=date.today(),
        dados=dados,
    )


@chamadas_bp.route(
    "/chamadas/<int:chamada_id>/presenca/<int:aluno_id>",
    methods=["POST"],
)
def registrar_presenca(chamada_id, aluno_id):
    chamada = db.get_or_404(Chamada, chamada_id)
    aluno = db.get_or_404(Aluno, aluno_id)

    estado = request.form.get("estado", "")
    if estado not in ESTADOS_PRESENCA:
        return jsonify({"ok": False, "erro": "Estado inválido."}), 400

    presenca = Presenca.query.filter_by(
        chamada_id=chamada.id,
        aluno_id=aluno.id,
    ).first()

    if presenca is None:
        presenca = Presenca(
            chamada_id=chamada.id,
            aluno_id=aluno.id,
            estado=estado,
        )
        db.session.add(presenca)
    else:
        presenca.estado = estado

    db.session.commit()

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(
            {
                "ok": True,
                "estado": estado,
                "frequencia": percentual_frequencia(list(chamada.presencas)),
            }
        )

    flash(f"{aluno.nome} marcado como {estado}.", "sucesso")
    return redirect(url_for("chamadas.por_turma", turma_id=chamada.turma_id))


@chamadas_bp.route("/chamadas/<int:chamada_id>/excluir", methods=["POST"])
def excluir(chamada_id):
    chamada = db.get_or_404(Chamada, chamada_id)
    turma_id = chamada.turma_id
    db.session.delete(chamada)
    db.session.commit()
    flash("Chamada removida.", "sucesso")
    return redirect(url_for("chamadas.por_turma", turma_id=turma_id))


def _alunos_ativos_da_turma(turma_id):
    return (
        Aluno.query.join(Matricula, Matricula.aluno_id == Aluno.id)
        .filter(
            Matricula.turma_id == turma_id,
            Matricula.ativa.is_(True),
            Aluno.status == "ativo",
        )
        .order_by(Aluno.nome)
        .all()
    )


def _criar_presencas_faltantes(chamada):
    existentes = {
        p.aluno_id for p in chamada.presencas
    }
    for aluno in _alunos_ativos_da_turma(chamada.turma_id):
        if aluno.id not in existentes:
            db.session.add(
                Presenca(
                    chamada_id=chamada.id,
                    aluno_id=aluno.id,
                    estado=AUSENTE,
                )
            )


def _ler_form_no_formato():
    texto_data = request.form.get("data", "").strip()
    if not texto_data:
        return "Informe a data da chamada.", None
    try:
        data = datetime.strptime(texto_data, "%Y-%m-%d").date()
    except ValueError:
        return "Data inválida.", None

    conteudo = request.form.get("conteudo", "").strip()
    observacao = request.form.get("observacao", "").strip()
    return None, {
        "data": data,
        "conteudo": conteudo,
        "observacao": observacao,
    }