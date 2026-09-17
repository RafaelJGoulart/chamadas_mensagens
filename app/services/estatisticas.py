from collections import defaultdict
from datetime import date
from urllib.parse import quote

from extensions import db
from models import (
    Aluno,
    Chamada,
    Presenca,
    Turma,
)
from services.frequencia import aluno_frequente, percentual_frequencia


MESES = [
    "Janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro",
]


def _intervalo_mes(ano, mes):
    proximo_ano = ano + 1 if mes == 12 else ano
    proximo_mes = 1 if mes == 12 else mes + 1
    return date(ano, mes, 1), date(proximo_ano, proximo_mes, 1)


def chamadas_do_mes(ano, mes):
    inicio, fim = _intervalo_mes(ano, mes)
    return Chamada.query.filter(
        Chamada.data >= inicio,
        Chamada.data < fim,
    ).order_by(Chamada.data).all()


def presencas_do_mes(ano, mes):
    chamadas = chamadas_do_mes(ano, mes)
    ids = [c.id for c in chamadas]
    if not ids:
        return []
    return Presenca.query.filter(Presenca.chamada_id.in_(ids)).all()


def estatisticas_mensais(ano, mes):
    """Monta os dados usados pelos gráficos e pelo resumo do mês.

    Retorna um dicionário com:
    - total_alunos_com_dados: alunos ativos com presença no mês
    - alunos_frequentes: quantos atingiram 50% ou mais
    - alunos_abaixo: quantos ficaram abaixo de 50%
    - percentual_frequentes: % sobre o total com dados
    - por_turma: lista de dicts por turma com % de frequentes
    """
    presencas = presencas_do_mes(ano, mes)

    por_aluno = defaultdict(list)
    por_turma_aluno = defaultdict(lambda: defaultdict(list))

    for p in presencas:
        por_aluno[p.aluno_id].append(p)
        por_turma_aluno[p.chamada.turma_id][p.aluno_id].append(p)

    alunos_com_dados = set()
    frequentes_por_aluno = {}
    for aluno_id, lista in por_aluno.items():
        aluno = db.session.get(Aluno, aluno_id)
        if aluno is None or aluno.status != "ativo":
            continue
        alunos_com_dados.add(aluno_id)
        frequentes_por_aluno[aluno_id] = aluno_frequente(
            percentual_frequencia(lista)
        )

    total_com_dados = len(alunos_com_dados)
    alunos_frequentes = sum(
        1 for a in frequentes_por_aluno.values() if a
    )
    alunos_abaixo = total_com_dados - alunos_frequentes
    percentual_frequentes = None
    if total_com_dados:
        percentual_frequentes = round(
            (alunos_frequentes / total_com_dados) * 100, 1
        )

    por_turma = []
    for turma_id, mapa in por_turma_aluno.items():
        turma = db.session.get(Turma, turma_id)
        if turma is None:
            continue
        presentes_turma = 0
        frequentes_turma = 0
        for aluno_id, lista in mapa.items():
            aluno = db.session.get(Aluno, aluno_id)
            if aluno is None or aluno.status != "ativo":
                continue
            presentes_turma += 1
            if aluno_frequente(percentual_frequencia(lista)):
                frequentes_turma += 1
        pct_frequentes = None
        if presentes_turma:
            pct_frequentes = round(
                (frequentes_turma / presentes_turma) * 100, 1
            )
        por_turma.append(
            {
                "turma": turma,
                "total": presentes_turma,
                "frequentes": frequentes_turma,
                "abaixo": presentes_turma - frequentes_turma,
                "percentual": pct_frequentes,
            }
        )

    por_turma.sort(key=lambda item: item["turma"].nome)

    return {
        "total_alunos_com_dados": total_com_dados,
        "alunos_frequentes": alunos_frequentes,
        "alunos_abaixo": alunos_abaixo,
        "percentual_frequentes": percentual_frequentes,
        "por_turma": por_turma,
    }


def indicadores_gerais():
    """Indicadores usados no topo do dashboard."""
    return {
        "alunos_ativos": Aluno.query.filter_by(status="ativo").count(),
        "turmas_ativas": Turma.query.filter_by(ativa=True).count(),
        "alunos_atencao": Aluno.query.filter_by(
            status="ativo", flag_coordenacao=True
        ).count(),
    }


def chamadas_recentes(limite=5):
    return (
        Chamada.query.order_by(Chamada.data.desc(), Chamada.id.desc())
        .limit(limite)
        .all()
    )


def alunos_com_flag_coordenacao():
    return (
        Aluno.query.filter_by(status="ativo", flag_coordenacao=True)
        .order_by(Aluno.nome)
        .all()
    )


def _somente_digitos(texto):
    if not texto:
        return ""
    return "".join(c for c in str(texto) if c.isdigit())


def numeros_whatsapp(telefone, celular, comercial, mensagem):
    """Monta um link wa.me para cada número válido (telefone, celular, comercial)."""
    saidas = []
    for rotulo, candidato in (
        ("Telefone", telefone),
        ("Celular", celular),
        ("Comercial", comercial),
    ):
        digitos = _somente_digitos(candidato).lstrip("0")
        numero = None
        if len(digitos) in (10, 11) and not digitos.startswith("55"):
            numero = "55" + digitos
        elif len(digitos) in (12, 13) and digitos.startswith("55"):
            numero = digitos
        if numero:
            saidas.append(
                {
                    "rotulo": rotulo,
                    "exibido": str(candidato).strip(),
                    "numero_wa": numero,
                    "wa_link": link_whatsapp(numero, mensagem),
                }
            )
    return saidas


def telefone_para_whatsapp(telefone, celular=None, comercial=None):
    """Escolhe o melhor telefone e normaliza para o padrão wa.me.

    Ordem: telefone, celular, comercial.
    Retorna (numero_wa, telefone_exibido, rotulo) ou (None, None, None).
    """
    for rotulo, candidato in (
        ("Telefone", telefone),
        ("Celular", celular),
        ("Comercial", comercial),
    ):
        digitos = _somente_digitos(candidato)
        # Remove zero inicial de DDD antigo tipo "011..."
        digitos = digitos.lstrip("0")
        if len(digitos) in (10, 11) and not digitos.startswith("55"):
            return "55" + digitos, str(candidato).strip(), rotulo
        if len(digitos) in (12, 13) and digitos.startswith("55"):
            return digitos, str(candidato).strip(), rotulo
    return None, None, None


def mensagem_whatsapp(nome, percentual, total, presentes, mes_nome, ano):
    primeiro = (nome or "").strip().split(" ")[0] or nome
    faltas = total - presentes
    return (
        f"Olá {primeiro}, aqui é do curso de Informática. "
        f"Sua frequência em {mes_nome}/{ano} está em {percentual}% "
        f"({presentes}/{total} presenças, {faltas} falta(s)). "
        f"Sentimos sua falta nas aulas. Podemos contar com você?"
    )


def link_whatsapp(numero_wa, mensagem):
    return f"https://wa.me/{numero_wa}?text={quote(mensagem)}"


def alunos_baixa_frequencia(ano, mes, limite=50.0):
    """Alunos ativos, SEM flag de coordenação e com frequência < limite no mês.

    Retorna lista de dicts ordenada por percentual (pior primeiro):
    aluno, percentual, total, presentes, faltas, turmas, telefone,
    telefone_rotulo, telefones, numero_wa, wa_link, mensagem.
    """
    presencas = presencas_do_mes(ano, mes)
    mes_nome = MESES[mes - 1] if 1 <= mes <= 12 else str(mes)

    por_aluno = defaultdict(list)
    turmas_por_aluno = defaultdict(set)
    for p in presencas:
        por_aluno[p.aluno_id].append(p)
        try:
            turmas_por_aluno[p.aluno_id].add(p.chamada.turma.nome)
        except Exception:
            pass

    itens = []
    for aluno_id, lista in por_aluno.items():
        aluno = db.session.get(Aluno, aluno_id)
        if aluno is None:
            continue
        if aluno.status != "ativo":
            continue
        if aluno.flag_coordenacao:
            continue
        percentual = percentual_frequencia(lista)
        if percentual is None or percentual >= limite:
            continue
        total = len(lista)
        presentes = sum(
            1 for p in lista if p.estado in ("frequente", "reposicao")
        )
        numero_wa, exibido, rotulo = telefone_para_whatsapp(
            aluno.telefone, aluno.celular, aluno.comercial
        )
        mensagem = mensagem_whatsapp(
            aluno.nome, percentual, total, presentes, mes_nome, ano
        )
        telefones = numeros_whatsapp(
            aluno.telefone, aluno.celular, aluno.comercial, mensagem
        )
        itens.append(
            {
                "aluno": aluno,
                "percentual": percentual,
                "total": total,
                "presentes": presentes,
                "faltas": total - presentes,
                "turmas": sorted(turmas_por_aluno.get(aluno_id, set())),
                "telefone": exibido,
                "telefone_rotulo": rotulo,
                "telefones": telefones,
                "numero_wa": numero_wa,
                "wa_link": link_whatsapp(numero_wa, mensagem)
                if numero_wa
                else None,
                "mensagem": mensagem,
            }
        )

    itens.sort(key=lambda i: (i["percentual"], i["aluno"].nome))
    return itens