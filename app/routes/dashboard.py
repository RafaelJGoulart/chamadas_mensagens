from datetime import date

from flask import Blueprint, render_template, request

from services.estatisticas import (
    MESES,
    alunos_com_flag_coordenacao,
    chamadas_recentes,
    estatisticas_mensais,
    indicadores_gerais,
)
from services.frequencia import contar_estados

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def inicio():
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

    estatisticas = estatisticas_mensais(ano, mes)
    indicadores = indicadores_gerais()
    recentes = chamadas_recentes()

    chamadas_recentes_resumo = []
    for chamada in recentes:
        chamadas_recentes_resumo.append(
            {
                "chamada": chamada,
                "contagem": contar_estados(list(chamada.presencas)),
            }
        )

    return render_template(
        "dashboard.html",
        ano=ano,
        mes=mes,
        meses=MESES,
        ultimo_ano=hoje.year,
        estatisticas=estatisticas,
        indicadores=indicadores,
        chamadas_recentes=chamadas_recentes_resumo,
        alunos_atencao=alunos_com_flag_coordenacao(),
    )