"""Dados do relatório mensal de frequência (todas as turmas do professor).

Usa a mesma agregação em SQL do serviço de estatísticas (sem duplicação).
"""
from collections import defaultdict

from models import Aluno, Turma
from services.estatisticas import MESES, resumo_mensal_por_turma_aluno
from services.frequencia import aluno_frequente, percentual_frequencia_totais


def dados_relatorio(ano, mes):
    """Agrega os números do relatório do mês/ano em um dicionário.

    Conceitos:
    - Meta: se todos os alunos que NÃO são caso de coordenação viessem.
    - Real: alunos ativos que, no mês, ficaram com frequência >= 50%.
    - Os percentuais de meta e real usam o TOTAL (incluindo coordenação).
    """
    mes_nome = MESES[mes - 1] if 1 <= mes <= 12 else str(mes)

    resumo = resumo_mensal_por_turma_aluno(ano, mes)

    alunos_ativos = (
        Aluno.query.filter_by(status="ativo").order_by(Aluno.nome).all()
    )
    por_id = {aluno.id: aluno for aluno in alunos_ativos}
    total_alunos = len(alunos_ativos)

    por_aluno = defaultdict(lambda: {"total": 0, "presentes": 0})
    for mapa in resumo.values():
        for aluno_id, dados in mapa.items():
            ag = por_aluno[aluno_id]
            ag["total"] += dados["total"]
            ag["presentes"] += dados["presentes"]

    casos_coordenacao = sum(
        1 for aluno in alunos_ativos if aluno.flag_coordenacao
    )

    # Só alunos ATIVOS contam: o resumo SQL pode incluir presenças de alunos
    # inativos (ex.: não-ativos importados do F10 marcados como ausentes).
    alunos_com_dados = {
        aluno_id for aluno_id in por_aluno if aluno_id in por_id
    }

    alunos_frequentes = 0
    alunos_ausentes = 0
    for aluno_id in alunos_com_dados:
        dados = por_aluno[aluno_id]
        if aluno_frequente(
            percentual_frequencia_totais(dados["total"], dados["presentes"])
        ):
            alunos_frequentes += 1
        else:
            alunos_ausentes += 1
    alunos_sem_dados = total_alunos - len(alunos_com_dados)

    meta_alunos = total_alunos - casos_coordenacao
    meta_percentual = (
        round(meta_alunos / total_alunos * 100, 1) if total_alunos else None
    )
    real_percentual = (
        round(alunos_frequentes / total_alunos * 100, 1)
        if total_alunos
        else None
    )
    faltam_meta = max(meta_alunos - alunos_frequentes, 0)

    turmas = Turma.query.filter_by(ativa=True).order_by(Turma.nome).all()
    por_turma = []
    for turma in turmas:
        matriculados = turma.matriculas.filter_by(ativa=True).all()
        aluno_ids = [
            m.aluno_id for m in matriculados if m.aluno_id in por_id
        ]
        qtd_alunos = len(aluno_ids)
        qtd_coord = sum(1 for a in aluno_ids if por_id[a].flag_coordenacao)
        qtd_meta = qtd_alunos - qtd_coord

        mapa = resumo.get(turma.id, {})
        qtd_freq = 0
        qtd_aus = 0
        qtd_sem = 0
        for aluno_id in aluno_ids:
            dados = mapa.get(aluno_id)
            if not dados:
                qtd_sem += 1
            elif aluno_frequente(
                percentual_frequencia_totais(dados["total"], dados["presentes"])
            ):
                qtd_freq += 1
            else:
                qtd_aus += 1

        por_turma.append(
            {
                "nome": turma.nome,
                "alunos": qtd_alunos,
                "coordenacao": qtd_coord,
                "frequentes": qtd_freq,
                "ausentes": qtd_aus,
                "sem_dados": qtd_sem,
                "meta": qtd_meta,
                "meta_percentual": (
                    round(qtd_meta / qtd_alunos * 100, 1)
                    if qtd_alunos
                    else None
                ),
                "real": qtd_freq,
                "real_percentual": (
                    round(qtd_freq / qtd_alunos * 100, 1)
                    if qtd_alunos
                    else None
                ),
                "faltam": max(qtd_meta - qtd_freq, 0),
            }
        )

    return {
        "ano": ano,
        "mes": mes,
        "mes_nome": mes_nome,
        "total_alunos": total_alunos,
        "casos_coordenacao": casos_coordenacao,
        "alunos_frequentes": alunos_frequentes,
        "alunos_ausentes": alunos_ausentes,
        "alunos_sem_dados": alunos_sem_dados,
        "meta_alunos": meta_alunos,
        "meta_percentual": meta_percentual,
        "real_alunos": alunos_frequentes,
        "real_percentual": real_percentual,
        "faltam_meta": faltam_meta,
        "por_turma": por_turma,
    }