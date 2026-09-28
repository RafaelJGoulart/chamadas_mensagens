from collections import defaultdict
from datetime import date
from urllib.parse import quote

from sqlalchemy import case, func

from extensions import db
from models import (
    Aluno,
    Chamada,
    FREQUENTE,
    Presenca,
    REPOSICAO,
    Turma,
)
from services.frequencia import aluno_frequente, percentual_frequencia_totais


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
    """Presenças do mês já com chamada e turma carregadas (sem N+1)."""
    inicio, fim = _intervalo_mes(ano, mes)
    return (
        Presenca.query.join(Chamada, Chamada.id == Presenca.chamada_id)
        .options(
            db.joinedload(Presenca.chamada).joinedload(Chamada.turma)
        )
        .filter(Chamada.data >= inicio, Chamada.data < fim)
        .all()
    )


def resumo_mensal_por_turma_aluno(ano, mes):
    """Agrega o mês no banco: {turma_id: {aluno_id: {total, presentes}}}.

    Uma única consulta com GROUP BY; nada é carregado linha a linha.
    O resultado serve para dashboard, contato e relatório (sem duplicação).
    """
    inicio, fim = _intervalo_mes(ano, mes)
    linhas = (
        db.session.query(
            Chamada.turma_id,
            Presenca.aluno_id,
            func.count(Presenca.id).label("total"),
            func.sum(
                case(
                    (Presenca.estado.in_((FREQUENTE, REPOSICAO)), 1),
                    else_=0,
                )
            ).label("presentes"),
        )
        .join(Chamada, Chamada.id == Presenca.chamada_id)
        .filter(Chamada.data >= inicio, Chamada.data < fim)
        .group_by(Chamada.turma_id, Presenca.aluno_id)
        .all()
    )
    saida = defaultdict(dict)
    for turma_id, aluno_id, total, presentes in linhas:
        saida[turma_id][aluno_id] = {
            "total": total or 0,
            "presentes": presentes or 0,
        }
    return saida


def _alunos_ativos_por_id():
    return {
        a.id: a
        for a in Aluno.query.filter_by(status="ativo").order_by(Aluno.nome).all()
    }


def _resumo_global(por_turma_aluno):
    """Soma todos os totais por aluno, ignorando turma."""
    por_aluno = {}
    for mapa in por_turma_aluno.values():
        for aluno_id, dados in mapa.items():
            ag = por_aluno.setdefault(aluno_id, {"total": 0, "presentes": 0})
            ag["total"] += dados["total"]
            ag["presentes"] += dados["presentes"]
    return por_aluno


def estatisticas_mensais(ano, mes):
    """Monta os dados usados pelos gráficos e pelo resumo do mês.

    Retorna um dicionário com:
    - total_alunos_com_dados: alunos ativos com presença no mês
    - alunos_frequentes: quantos atingiram 50% ou mais
    - alunos_abaixo: quantos ficaram abaixo de 50%
    - percentual_frequentes: % sobre o total com dados
    - por_turma: lista de dicts por turma com % de frequentes
    """
    por_turma_aluno = resumo_mensal_por_turma_aluno(ano, mes)
    ativos = _alunos_ativos_por_id()
    por_aluno = _resumo_global(por_turma_aluno)

    alunos_com_dados = {
        aluno_id
        for aluno_id in por_aluno
        if aluno_id in ativos
    }

    def _frequente(aluno_id):
        dados = por_aluno[aluno_id]
        return aluno_frequente(
            percentual_frequencia_totais(dados["total"], dados["presentes"])
        )

    total_com_dados = len(alunos_com_dados)
    alunos_frequentes = sum(1 for aid in alunos_com_dados if _frequente(aid))
    alunos_abaixo = total_com_dados - alunos_frequentes
    percentual_frequentes = None
    if total_com_dados:
        percentual_frequentes = round(
            (alunos_frequentes / total_com_dados) * 100, 1
        )

    turmas_ids = list(por_turma_aluno.keys())
    turmas = {}
    if turmas_ids:
        turmas = {
            t.id: t
            for t in Turma.query.filter(Turma.id.in_(turmas_ids)).all()
        }

    por_turma = []
    for turma_id, mapa in por_turma_aluno.items():
        turma = turmas.get(turma_id)
        if turma is None:
            continue
        presentes_turma = 0
        frequentes_turma = 0
        for aluno_id, dados in mapa.items():
            if aluno_id not in ativos:
                continue
            presentes_turma += 1
            if aluno_frequente(
                percentual_frequencia_totais(dados["total"], dados["presentes"])
            ):
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
        Chamada.query.options(db.selectinload(Chamada.presencas))
        .order_by(Chamada.data.desc(), Chamada.id.desc())
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


def nivel_faltas(faltas):
    """Faixa da situação no mês pelo nº de faltas: (chave, rótulo, badge)."""
    if faltas <= 1:
        return ("leve", "Toque leve", "badge-neutro")
    if faltas <= 3:
        return ("atencao", "Atenção", "badge-aviso")
    return ("urgente", "Urgente", "badge-erro")


def mensagem_whatsapp(nome, percentual, total, presentes, mes_nome, ano,
                       responsavel=None, faltas=None):
    """Mensagem pronta por faixa de faltas (humanizada, com reposição).

    Com responsável, fala com ele sobre o aluno; sem, fala com o aluno.
    Mantém todos os dados (mês/ano, %, presenças/total, faltas).
    """
    if faltas is None:
        faltas = total - presentes
    pct = "%g" % percentual
    base = f"em {mes_nome}/{ano}: {presentes}/{total} presenças ({pct}%)"
    falta_txt = "1 falta" if faltas == 1 else f"{faltas} faltas"
    chave = nivel_faltas(faltas)[0]

    if responsavel:
        if chave == "leve":
            return (
                f"Olá! Aqui é do curso de Informática. Sentimos falta "
                f"de {nome} na aula — {base}, {falta_txt}. Está tudo bem "
                f"por aí? Se precisar, combinamos uma reposição: é só "
                f"responder a esta mensagem. Contamos com vocês!"
            )
        if chave == "atencao":
            return (
                f"Olá! Aqui é do curso de Informática. Estou preocupado "
                f"com a frequência de {nome} — {base}, {falta_txt}. Para "
                f"não ficar para trás no conteúdo, o ideal é retomar já: "
                f"a gente agenda a reposição das aulas perdidas. Pode me "
                f"responder aqui para combinarmos? Conto com vocês!"
            )
        return (
            f"Olá! Aqui é do curso de Informática e preciso falar sobre "
            f"a frequência de {nome} — {base}, {falta_txt}. Nesse ritmo "
            f"fica difícil acompanhar a turma, mas dá tempo de reverter: "
            f"vamos agendar as reposições? Me responda ainda hoje para "
            f"combinarmos o melhor dia. Conto com vocês!"
        )

    primeiro = (nome or "").strip().split(" ")[0] or nome
    if chave == "leve":
        return (
            f"Olá {primeiro}! Aqui é do curso de Informática. Sentimos "
            f"sua falta na aula — {base}, {falta_txt}. Está tudo bem? "
            f"Se precisar, combinamos uma reposição: é só responder "
            f"aqui. Conto com você!"
        )
    if chave == "atencao":
        return (
            f"Olá {primeiro}! Aqui é do curso de Informática. Sua "
            f"frequência {base}, {falta_txt} — e isso pode "
            f"te deixar para trás no conteúdo. Vamos retomar já? A gente "
            f"agenda a reposição das aulas perdidas: me responde aqui "
            f"para combinarmos. Conto com você!"
        )
    return (
        f"Olá {primeiro}! Aqui é do curso de Informática e preciso "
        f"falar sério com você sobre sua frequência: {pct}% {base}, "
        f"{falta_txt}. Nesse ritmo fica difícil acompanhar a turma, mas "
        f"dá tempo de reverter — vamos agendar as reposições? Me "
        f"responde ainda hoje para combinarmos o melhor dia. Conto com "
        f"você!"
    )


def link_whatsapp(numero_wa, mensagem):
    return f"https://wa.me/{numero_wa}?text={quote(mensagem)}"


def alunos_baixa_frequencia(ano, mes, limite=50.0):
    """Alunos ativos, SEM flag de coordenação e com frequência < limite no mês.

    Retorna lista de dicts ordenada por percentual (pior primeiro):
    aluno, percentual, total, presentes, faltas, nivel, nivel_rotulo,
    nivel_badge, responsavel, telefones_aluno, telefones_responsavel,
    turmas, telefone, telefone_rotulo, telefones, numero_wa,
    wa_link, mensagem.
    """
    por_turma_aluno = resumo_mensal_por_turma_aluno(ano, mes)
    por_aluno = _resumo_global(por_turma_aluno)

    ativos = _alunos_ativos_por_id()

    turmas_ids = list(por_turma_aluno.keys())
    turmas = {}
    if turmas_ids:
        turmas = {
            t.id: t
            for t in Turma.query.filter(Turma.id.in_(turmas_ids)).all()
        }

    turmas_por_aluno = defaultdict(set)
    for turma_id, mapa in por_turma_aluno.items():
        turma = turmas.get(turma_id)
        if turma is None:
            continue
        for aluno_id in mapa:
            turmas_por_aluno[aluno_id].add(turma.nome)

    mes_nome = MESES[mes - 1] if 1 <= mes <= 12 else str(mes)

    itens = []
    for aluno_id, dados in por_aluno.items():
        aluno = ativos.get(aluno_id)
        if aluno is None or aluno.flag_coordenacao:
            continue
        percentual = percentual_frequencia_totais(
            dados["total"], dados["presentes"]
        )
        if percentual is None or percentual >= limite:
            continue
        total = dados["total"]
        presentes = dados["presentes"]
        numero_wa, exibido, rotulo = telefone_para_whatsapp(
            aluno.telefone, aluno.celular, aluno.comercial
        )
        mensagem = mensagem_whatsapp(
            aluno.nome,
            percentual,
            total,
            presentes,
            mes_nome,
            ano,
            responsavel=aluno.responsavel,
        )
        telefones = numeros_whatsapp(
            aluno.telefone, aluno.celular, aluno.comercial, mensagem
        )
        nivel_chave, nivel_rotulo, nivel_badge = nivel_faltas(
            total - presentes
        )
        # Os números gravados são do responsável quando há um cadastrado
        # (regra da importação); sem responsável, são do próprio aluno.
        if aluno.responsavel:
            telefones_aluno = []
            telefones_responsavel = telefones
        else:
            telefones_aluno = telefones
            telefones_responsavel = []
        itens.append(
            {
                "aluno": aluno,
                "percentual": percentual,
                "total": total,
                "presentes": presentes,
                "faltas": total - presentes,
                "nivel": nivel_chave,
                "nivel_rotulo": nivel_rotulo,
                "nivel_badge": nivel_badge,
                "responsavel": aluno.responsavel,
                "telefones_aluno": telefones_aluno,
                "telefones_responsavel": telefones_responsavel,
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