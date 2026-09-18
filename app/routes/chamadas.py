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
    Materia,
    Matricula,
    Presenca,
    Turma,
)
from services.frequencia import percentual_frequencia_totais
from services.materias import MATERIA_NEUTRA, ordenar_materias

chamadas_bp = Blueprint("chamadas", __name__)

ESTADO_PESO = {
    "ausente": 0,
    "frequente": 1,
    "reposicao": 1,
}


@chamadas_bp.route("/chamadas")
def listar():
    return redirect(url_for("turmas.listar"))


@chamadas_bp.route("/chamadas/turma/<int:turma_id>")
def por_turma(turma_id):
    turma = db.get_or_404(Turma, turma_id)
    materias = ordenar_materias(
        Materia.query.filter_by(curso_id=turma.curso_id).all()
    )

    materia_id = request.args.get("materia", type=int)
    material_atual = None
    if materias:
        if materia_id is None:
            material_atual = _materia_mais_recente(turma, materias)
        else:
            material_atual = next(
                (m for m in materias if m.id == materia_id), None
            )
            if material_atual is None:
                material_atual = _materia_mais_recente(turma, materias)
    mf = material_atual.id if material_atual else None

    # 1 query: chamadas da turma (e da matéria) já com as presenças.
    filtro = Chamada.query.filter_by(turma_id=turma.id)
    if mf is not None:
        filtro = filtro.filter_by(materia_id=mf)
    chamadas = (
        filtro.order_by(Chamada.data.asc(), Chamada.id.asc())
        .options(db.selectinload(Chamada.presencas))
        .all()
    )

    # 2 queries: alunos ativos da turma.
    alunos = _alunos_ativos_da_turma(turma.id)

    # Índice aluno->presença por chamada para montar a grade sem N+1.
    presencas_por_chamada = {
        c.id: {p.aluno_id: p for p in c.presencas}
        for c in chamadas
    }

    linhas = []
    for aluno in alunos:
        estados = []
        presentes = 0
        total = 0
        for chamada in chamadas:
            presenca = presencas_por_chamada[chamada.id].get(aluno.id)
            if presenca is None:
                estados.append(AUSENTE)
            else:
                estados.append(presenca.estado)
                total += 1
                presentes += ESTADO_PESO.get(presenca.estado, 0)
        linhas.append(
            {
                "aluno": aluno,
                "estados": estados,
                "total": total,
                "percentual": percentual_frequencia_totais(total, presentes),
            }
        )

    return render_template(
        "chamadas/turma.html",
        turma=turma,
        chamadas=chamadas,
        linhas=linhas,
        materias=materias,
        material_atual=material_atual,
        hoje=date.today(),
    )


def _materia_mais_recente(turma, materias):
    """Escolhe a matéria padrão: a da última chamada da turma ou a primeira."""
    ultima = (
        Chamada.query.filter_by(turma_id=turma.id)
        .order_by(Chamada.data.desc(), Chamada.id.desc())
        .first()
    )
    if ultima is not None and ultima.materia_id is not None:
        for m in materias:
            if m.id == ultima.materia_id:
                return m
    for m in materias:
        if m.nome.lower() == MATERIA_NEUTRA.lower():
            return m
    return materias[0]


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


@chamadas_bp.route(
    "/chamadas/turma/<int:turma_id>/nova",
    methods=["GET", "POST"],
)
def nova(turma_id):
    turma = db.get_or_404(Turma, turma_id)
    alunos = _alunos_ativos_da_turma(turma.id)
    ids_validos = {aluno.id for aluno in alunos}
    materias = ordenar_materias(
        Materia.query.filter_by(curso_id=turma.curso_id).all()
    )
    dados = None
    material_atual = (
        _materia_mais_recente(turma, materias) if materias else None
    )

    if request.method == "POST":
        erro, dados = _ler_form_no_formato(materias)
        if erro:
            flash(erro, "erro")
        else:
            existe = Chamada.query.filter_by(
                turma_id=turma.id,
                data=dados["data"],
                materia_id=dados["materia_id"],
            ).first()
            if existe:
                flash(
                    "Já existe uma chamada para essa turma/matéria nessa data.",
                    "erro",
                )
            else:
                chamada = Chamada(
                    turma_id=turma.id,
                    materia_id=dados["materia_id"],
                    data=dados["data"],
                    conteudo=dados["conteudo"] or None,
                    observacao=dados["observacao"] or None,
                )
                db.session.add(chamada)
                db.session.flush()
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
                    url_for(
                        "chamadas.por_turma",
                        turma_id=turma.id,
                        materia=dados["materia_id"],
                    )
                )

        return redirect(
            url_for(
                "chamadas.por_turma",
                turma_id=turma.id,
                materia=dados["materia_id"] if dados else None,
            )
        )

    return render_template(
        "chamadas/nova.html",
        turma=turma,
        alunos=alunos,
        materias=materias,
        material_atual=material_atual,
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
        percentual = _percentual_da_chamada(chamada.id)
        return jsonify(
            {
                "ok": True,
                "estado": estado,
                "frequencia": percentual,
            }
        )

    flash(f"{aluno.nome} marcado como {estado}.", "sucesso")
    return redirect(url_for("chamadas.por_turma", turma_id=chamada.turma_id))


def _percentual_da_chamada(chamada_id):
    """Percentual de frequência de uma chamada via SQL (sem listas em memória)."""
    totais = (
        db.session.query(
            db.func.count(Presenca.id),
            db.func.sum(Presenca.estado.in_(("frequente", "reposicao"))),
        )
        .filter(Presenca.chamada_id == chamada_id)
        .one()
    )
    return percentual_frequencia_totais(totais[0], totais[1] or 0)


@chamadas_bp.route("/chamadas/<int:chamada_id>/materia/<int:materia_id>",
                   methods=["POST"])
def mover_materia(chamada_id, materia_id):
    chamada = db.get_or_404(Chamada, chamada_id)
    materia = db.get_or_404(Materia, materia_id)
    turma = db.session.get(Turma, chamada.turma_id)
    if materia.curso_id != turma.curso_id:
        return jsonify({"ok": False, "erro": "Matéria inválida."}), 400

    existe = Chamada.query.filter_by(
        turma_id=chamada.turma_id,
        data=chamada.data,
        materia_id=materia.id,
    ).first()
    if existe is not None and existe.id != chamada.id:
        return jsonify(
            {"ok": False, "erro": "Já existe uma chamada nessa matéria/data."}
        ), 400

    chamada.materia_id = materia.id
    db.session.commit()
    return jsonify({"ok": True, "materia": materia.nome})


@chamadas_bp.route("/chamadas/<int:chamada_id>/excluir", methods=["POST"])
def excluir(chamada_id):
    chamada = db.get_or_404(Chamada, chamada_id)
    turma_id = chamada.turma_id
    materia_id = chamada.materia_id
    Presenca.query.filter_by(chamada_id=chamada.id).delete()
    db.session.delete(chamada)
    db.session.commit()
    flash("Chamada removida.", "sucesso")
    return redirect(
        url_for(
            "chamadas.por_turma",
            turma_id=turma_id,
            materia=materia_id,
        )
    )


def _ler_form_no_formato(materias):
    texto_data = request.form.get("data", "").strip()
    if not texto_data:
        return "Informe a data da chamada.", None
    try:
        data = datetime.strptime(texto_data, "%Y-%m-%d").date()
    except ValueError:
        return "Data inválida.", None

    materia_id = None
    try:
        materia_id = int(request.form.get("materia_id", "") or 0)
    except (TypeError, ValueError):
        materia_id = 0
    materias_validas = {m.id for m in materias}
    if not materias or materia_id not in materias_validas:
        return "Selecione a matéria da chamada.", None

    conteudo = request.form.get("conteudo", "").strip()
    observacao = request.form.get("observacao", "").strip()
    return None, {
        "data": data,
        "materia_id": materia_id,
        "conteudo": conteudo,
        "observacao": observacao,
    }