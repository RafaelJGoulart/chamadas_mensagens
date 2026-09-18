"""Dados do relatório mensal de frequência (todas as turmas do professor)."""
from collections import defaultdict
from datetime import date

from extensions import db
from models import Aluno, Chamada, Presenca, Turma
from services.estatisticas import MESES
from services.frequencia import aluno_frequente, percentual_frequencia


def _intervalo_mes(ano, mes):
    inicio = date(ano, mes, 1)
    fim = date(ano + 1, 1, 1) if mes == 12 else date(ano, mes + 1, 1)
    return inicio, fim


def dados_relatorio(ano, mes):
    """Agrega os números do relatório do mês/ano em um dicionário.

    Conceitos:
    - Meta: se todos os alunos que NÃO são caso de coordenação viessem.
    - Real: alunos ativos que, no mês, ficaram com frequência >= 50%.
    - Os percentuais de meta e real usam o TOTAL (incluindo coordenação).
    """
    mes_nome = MESES[mes - 1] if 1 <= mes <= 12 else str(mes)

    inicio, fim = _intervalo_mes(ano, mes)
    chamadas = Chamada.query.filter(
        Chamada.data >= inicio,
        Chamada.data < fim,
    ).all()
    presencas = []
    if chamadas:
        presencas = Presenca.query.filter(
            Presenca.chamada_id.in_([c.id for c in chamadas])
        ).all()

    alunos_ativos = (
        Aluno.query.filter_by(status="ativo").order_by(Aluno.nome).all()
    )
    por_id = {aluno.id: aluno for aluno in alunos_ativos}
    total_alunos = len(alunos_ativos)

    por_aluno = defaultdict(list)
    por_turma_aluno = defaultdict(lambda: defaultdict(list))
    for p in presencas:
        if p.aluno_id not in por_id:
            continue
        por_aluno[p.aluno_id].append(p)
        por_turma_aluno[p.chamada.turma_id][p.aluno_id].append(p)

    casos_coordenacao = sum(
        1 for aluno in alunos_ativos if aluno.flag_coordenacao
    )

    alunos_frequentes = 0
    alunos_ausentes = 0
    for aluno_id, lista in por_aluno.items():
        if aluno_frequente(percentual_frequencia(lista)):
            alunos_frequentes += 1
        else:
            alunos_ausentes += 1
    alunos_sem_dados = total_alunos - len(por_aluno)

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
        matriculados = (
            turma.matriculas.filter_by(ativa=True).all()
        )
        aluno_ids = [
            m.aluno_id for m in matriculados if m.aluno_id in por_id
        ]
        qtd_alunos = len(aluno_ids)
        qtd_coord = sum(1 for a in aluno_ids if por_id[a].flag_coordenacao)
        qtd_meta = qtd_alunos - qtd_coord

        qtd_freq = 0
        qtd_aus = 0
        qtd_sem = 0
        for aluno_id in aluno_ids:
            lista = por_turma_aluno.get(turma.id, {}).get(aluno_id, [])
            if not lista:
                qtd_sem += 1
            elif aluno_frequente(percentual_frequencia(lista)):
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