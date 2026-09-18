from models import AUSENTE, FREQUENTE, REPOSICAO


def presencas_validas(presencas):
    """Presenças que contam como presença (frequente + reposição)."""
    return [
        p for p in presencas
        if p.estado in (FREQUENTE, REPOSICAO)
    ]


def percentual_frequencia(presencas):
    """Percentual de frequência (0 a 100.0) ou None sem chamadas."""
    total = len(presencas)
    if total == 0:
        return None
    validas = len(presencas_validas(presencas))
    return round((validas / total) * 100, 1)


def percentual_frequencia_totais(total, presentes):
    """Percentual de frequência conhecendo só as contagens (sem listas)."""
    if not total:
        return None
    return round((presentes / total) * 100, 1)


def aluno_frequente(percentual):
    """Aluno é frequente quando atinge 50% ou mais."""
    return percentual is not None and percentual >= 50.0


def contar_estados(presencas):
    """Conta quantas ocorrências de cada estado."""
    return {
        AUSENTE: sum(1 for p in presencas if p.estado == AUSENTE),
        FREQUENTE: sum(1 for p in presencas if p.estado == FREQUENTE),
        REPOSICAO: sum(1 for p in presencas if p.estado == REPOSICAO),
    }