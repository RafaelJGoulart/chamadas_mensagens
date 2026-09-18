from datetime import date

from flask import Blueprint, Response, request

from services.pdf_relatorio import gerar_pdf
from services.relatorio import dados_relatorio

relatorio_bp = Blueprint("relatorio", __name__)


@relatorio_bp.route("/relatorio")
def gerar():
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

    dados = dados_relatorio(ano, mes)
    pdf = gerar_pdf(dados)

    nome_arquivo = f"relatorio_frequencia_{ano}_{mes:02d}.pdf"
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{nome_arquivo}"'
        },
    )