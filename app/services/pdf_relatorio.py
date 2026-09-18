"""Geração do relatório mensal de frequência em PDF (reportlab).

Fontes: Lato (SIL Open Font License 1.1 — uso comercial livre), baixadas em
app/static/fonts/ (Lato-Regular.ttf, Lato-Bold.ttf, Lato-Black.ttf) e
embutidas no próprio PDF.
"""
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PASTA_FONTES = Path(__file__).resolve().parent.parent / "static" / "fonts"

EMERALD = colors.HexColor("#10b981")
EMERALD_ESCURA = colors.HexColor("#059669")
INK = colors.HexColor("#1a2233")
MUTED = colors.HexColor("#6b7686")
LINHA = colors.HexColor("#dde3eb")
FUNDO_SUAVE = colors.HexColor("#f3f5f8")
AMARELO = colors.HexColor("#F5B94F")
VERDE = colors.HexColor("#4CCB7A")
VERMELHO = colors.HexColor("#ED6B6B")
NEUTRO = colors.HexColor("#8f9bb0")


def _registrar_fontes():
    pdfmetrics.registerFont(
        TTFont("Lato", str(PASTA_FONTES / "Lato-Regular.ttf"))
    )
    pdfmetrics.registerFont(
        TTFont("Lato-Bold", str(PASTA_FONTES / "Lato-Bold.ttf"))
    )
    pdfmetrics.registerFont(
        TTFont("Lato-Black", str(PASTA_FONTES / "Lato-Black.ttf"))
    )
    pdfmetrics.registerFontFamily(
        "Lato",
        normal="Lato",
        bold="Lato-Bold",
        italic="Lato",
        boldItalic="Lato-Bold",
    )


if "Lato" not in pdfmetrics.getRegisteredFontNames():
    _registrar_fontes()


def _fmt(valor):
    """Formata número para padrão pt-BR (vírgula decimal)."""
    if valor is None:
        return "0"
    return str(valor).replace(".", ",")


def _pct(valor):
    return "0" if valor is None else _fmt(valor)


def _estilos():
    st = {
        "titulo": ParagraphStyle(
            "titulo",
            fontName="Lato-Black",
            fontSize=20,
            leading=24,
            textColor=INK,
        ),
        "subtitulo": ParagraphStyle(
            "subtitulo",
            fontName="Lato",
            fontSize=9.5,
            leading=13,
            textColor=MUTED,
        ),
        "h2": ParagraphStyle(
            "h2",
            fontName="Lato-Bold",
            fontSize=12,
            leading=16,
            textColor=EMERALD_ESCURA,
            spaceBefore=8,
            spaceAfter=2,
        ),
        "corpo": ParagraphStyle(
            "corpo",
            fontName="Lato",
            fontSize=10,
            leading=14,
            textColor=INK,
        ),
        "nota": ParagraphStyle(
            "nota",
            fontName="Lato",
            fontSize=8,
            leading=11,
            textColor=MUTED,
        ),
        "valor_cartao": ParagraphStyle(
            "valor_cartao",
            fontName="Lato-Black",
            fontSize=20,
            leading=22,
        ),
        "rotulo_cartao": ParagraphStyle(
            "rotulo_cartao",
            fontName="Lato-Bold",
            fontSize=8,
            leading=11,
        ),
        "cab_tabela": ParagraphStyle(
            "cab_tabela",
            fontName="Lato-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white,
        ),
        "celula": ParagraphStyle(
            "celula",
            fontName="Lato",
            fontSize=8.5,
            leading=11,
            textColor=INK,
        ),
        "celula_c": ParagraphStyle(
            "celula_c",
            fontName="Lato",
            fontSize=8.5,
            leading=11,
            textColor=INK,
        ),
        "celula_destaque": ParagraphStyle(
            "celula_destaque",
            fontName="Lato-Bold",
            fontSize=8.5,
            leading=11,
            textColor=INK,
        ),
    }
    return st


def _cartao(estilos, valor, rotulo, cor, texto_cor):
    interno = Table(
        [
            [Paragraph(str(valor), estilos["valor_cartao"])],
            [Paragraph(rotulo, estilos["rotulo_cartao"])],
        ],
        colWidths=[50 * mm],
    )
    interno.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), cor),
                ("TEXTCOLOR", (0, 0), (-1, -1), texto_cor),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return interno


def _bloco_cartoes(estilos, dados):
    cards = [
        _cartao(estilos, dados["total_alunos"], "TOTAL DE ALUNOS",
                EMERALD_ESCURA, colors.white),
        _cartao(estilos, dados["casos_coordenacao"], "CASOS DE COORDENAÇÃO",
                AMARELO, INK),
        _cartao(estilos, dados["alunos_frequentes"], "ALUNOS FREQUENTES",
                EMERALD, colors.white),
        _cartao(estilos, dados["alunos_ausentes"], "ALUNOS AUSENTES",
                VERMELHO, INK),
        _cartao(estilos, dados["alunos_sem_dados"], "SEM DADOS NO MÊS",
                NEUTRO, colors.white),
    ]
    tabela = Table([cards], colWidths=[50 * mm] * 5)
    tabela.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 1),
                ("RIGHTPADDING", (0, 0), (-1, -1), 1),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return tabela


def _tabela_meta(estilos, dados):
    linhas = [
        [
            Paragraph("Meta — todos os alunos, exceto coordenação, presentes",
                      estilos["corpo"]),
            Paragraph(
                f"<b>{dados['meta_alunos']}</b> de {dados['total_alunos']}"
                f" ({_pct(dados['meta_percentual'])}%)",
                estilos["celula_destaque"],
            ),
        ],
        [
            Paragraph("Comparecimento real — alunos frequentes no mês",
                      estilos["corpo"]),
            Paragraph(
                f"<b>{dados['real_alunos']}</b> de {dados['total_alunos']}"
                f" ({_pct(dados['real_percentual'])}%)",
                estilos["celula_destaque"],
            ),
        ],
        [
            Paragraph("Alunos que faltam para atingir a meta", estilos["corpo"]),
            Paragraph(f"<b>{dados['faltam_meta']}</b>",
                      estilos["celula_destaque"]),
        ],
    ]
    tabela = Table(linhas, colWidths=[150 * mm, 70 * mm])
    tabela.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), FUNDO_SUAVE),
                ("BOX", (0, 0), (-1, -1), 0.5, LINHA),
                ("LINEBELOW", (0, 0), (-1, -2), 0.5, LINHA),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    return tabela


def _tabela_turmas(estilos, dados):
    cab = [
        Paragraph("<b>Turma</b>", estilos["cab_tabela"]),
        Paragraph("<b>Alunos</b>", estilos["cab_tabela"]),
        Paragraph("<b>Coord.</b>", estilos["cab_tabela"]),
        Paragraph("<b>Frequentes</b>", estilos["cab_tabela"]),
        Paragraph("<b>Ausentes</b>", estilos["cab_tabela"]),
        Paragraph("<b>Sem dados</b>", estilos["cab_tabela"]),
        Paragraph("<b>Meta</b>", estilos["cab_tabela"]),
        Paragraph("<b>Real</b>", estilos["cab_tabela"]),
        Paragraph("<b>Faltam</b>", estilos["cab_tabela"]),
    ]
    linhas = [cab]
    for t in dados["por_turma"]:
        meta = f"{t['meta']} ({_pct(t['meta_percentual'])}%)"
        real = f"{t['real']} ({_pct(t['real_percentual'])}%)"
        linhas.append(
            [
                Paragraph(t["nome"], estilos["celula_destaque"]),
                Paragraph(str(t["alunos"]), estilos["celula_c"]),
                Paragraph(str(t["coordenacao"]), estilos["celula_c"]),
                Paragraph(str(t["frequentes"]), estilos["celula_c"]),
                Paragraph(str(t["ausentes"]), estilos["celula_c"]),
                Paragraph(str(t["sem_dados"]), estilos["celula_c"]),
                Paragraph(meta, estilos["celula_c"]),
                Paragraph(real, estilos["celula_c"]),
                Paragraph(str(t["faltam"]), estilos["celula_c"]),
            ]
        )

    larguras = [
        66 * mm,
        22 * mm,
        24 * mm,
        24 * mm,
        24 * mm,
        24 * mm,
        30 * mm,
        30 * mm,
        29 * mm,
    ]
    tabela = Table(linhas, colWidths=larguras, repeatRows=1)
    estilo = [
        ("BACKGROUND", (0, 0), (-1, 0), EMERALD_ESCURA),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOX", (0, 0), (-1, -1), 0.5, LINHA),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, LINHA),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]
    for i in range(1, len(linhas)):
        if i % 2 == 0:
            estilo.append(("BACKGROUND", (0, i), (-1, i), FUNDO_SUAVE))
    tabela.setStyle(TableStyle(estilo))
    return tabela


def _rodape(canvas, documento):
    canvas.saveState()
    canvas.setFont("Lato", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        12 * mm,
        9 * mm,
        "Sistema de Chamadas · Relatório de Frequência",
    )
    canvas.setFont("Lato-Bold", 8)
    canvas.drawRightString(
        297 * mm - 12 * mm,
        9 * mm,
        f"Página {documento.page}",
    )
    canvas.restoreState()


def gerar_pdf(dados):
    """Monta o PDF do relatório e devolve os bytes."""
    estilos = _estilos()
    saida = BytesIO()
    documento = SimpleDocTemplate(
        saida,
        pagesize=landscape(A4),
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=14 * mm,
        bottomMargin=16 * mm,
        title=f"Relatório de Frequência — {dados['mes_nome']}/{dados['ano']}",
        author="Sistema de Chamadas",
    )

    agora = datetime.now()
    historia = []
    historia.append(
        Paragraph("Relatório de Frequência", estilos["titulo"])
    )
    historia.append(
        Paragraph(
            f"{dados['mes_nome']} de {dados['ano']}  ·  gerado em "
            f"{agora.strftime('%d/%m/%Y %H:%M')}",
            estilos["subtitulo"],
        )
    )
    historia.append(Spacer(1, 3 * mm))
    historia.append(HRFlowable(width="100%", thickness=2, color=EMERALD))
    historia.append(Spacer(1, 5 * mm))

    historia.append(Paragraph("Resumo geral", estilos["h2"]))
    historia.append(_bloco_cartoes(estilos, dados))
    historia.append(Spacer(1, 6 * mm))

    historia.append(Paragraph("Meta de presença", estilos["h2"]))
    historia.append(
        Paragraph(
            "A meta considera todos os alunos, exceto os casos de coordenação, "
            "presentes nas chamadas. O percentual usa o total geral (incluindo "
            "a coordenação).",
            estilos["nota"],
        )
    )
    historia.append(_tabela_meta(estilos, dados))
    historia.append(Spacer(1, 6 * mm))

    historia.append(Paragraph("Detalhamento por turma", estilos["h2"]))
    historia.append(_tabela_turmas(estilos, dados))
    historia.append(Spacer(1, 3 * mm))
    historia.append(
        Paragraph(
            "Frequentes: frequência igual ou acima de 50% no mês · "
            "Ausentes: abaixo de 50% · Sem dados: alunos sem chamada "
            "lançada no mês.",
            estilos["nota"],
        )
    )

    documento.build(
        historia,
        onFirstPage=_rodape,
        onLaterPages=_rodape,
    )
    return saida.getvalue()