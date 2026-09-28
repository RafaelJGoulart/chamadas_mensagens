from datetime import date

from flask import Blueprint, render_template, request

from services.estatisticas import MESES, alunos_baixa_frequencia
from services.validacao import normalizar_busca

contato_bp = Blueprint("contato", __name__)

LIMITE_BAIXA_FREQUENCIA = 50.0


@contato_bp.route("/contato")
def listar():
    hoje = date.today()

    try:
        ano = int(request.args.get("ano", hoje.year))
        mes = int(request.args.get("mes", hoje.month))
    except (TypeError, ValueError):
        ano, mes = hoje.year, hoje.month

    if not (1 <= mes <= 12):
        mes = hoje.month
    if not (2000 <= ano <= 2100):
        ano = hoje.year

    itens = alunos_baixa_frequencia(ano, mes, LIMITE_BAIXA_FREQUENCIA)

    q = request.args.get("q", "").strip()
    if q:
        q_norm = normalizar_busca(q)
        itens = [i for i in itens if q_norm in _texto_contato(i)]

    return render_template(
        "contato/listar.html",
        ano=ano,
        mes=mes,
        meses=MESES,
        ultimo_ano=hoje.year,
        itens=itens,
        limite=LIMITE_BAIXA_FREQUENCIA,
        q=q,
    )


def _texto_contato(item):
    return normalizar_busca(
        f"{item['aluno'].nome} {' '.join(item['turmas'])} "
        f"{item['nivel_rotulo']} {item['aluno'].responsavel or ''}"
    )
