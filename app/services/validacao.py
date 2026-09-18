from models import DIAS_SEMANA


def normalizar_texto(valor):
    if valor is None:
        return ""
    texto = str(valor).strip()
    return " ".join(texto.split())


def normalizar_busca(texto):
    """Minúsculas sem acento, para pesquisa aproximada."""
    import unicodedata

    return "".join(
        c
        for c in unicodedata.normalize("NFD", (texto or "").lower())
        if unicodedata.category(c) != "Mn"
    )


def validar_nome_curso(form):
    nome = normalizar_texto(form.get("nome", ""))
    descricao = normalizar_texto(form.get("descricao", ""))
    erros = []
    if not nome:
        erros.append("Informe o nome do curso.")
    return nome, descricao, erros


def validar_turma(form):
    nome = normalizar_texto(form.get("nome", ""))
    dia_semana = normalizar_texto(form.get("dia_semana", ""))
    horario_inicio = normalizar_texto(form.get("horario_inicio", "")) or None
    horario_fim = normalizar_texto(form.get("horario_fim", "")) or None
    ativa = form.get("ativa") == "on"

    erros = []
    try:
        curso_id = int(form.get("curso_id", ""))
    except (TypeError, ValueError):
        curso_id = None

    if not curso_id:
        erros.append("Selecione um curso.")
    if not nome:
        erros.append("Informe o nome da turma.")
    if dia_semana not in DIAS_SEMANA:
        erros.append("Selecione um dia da semana válido.")

    return (
        curso_id,
        nome,
        dia_semana,
        horario_inicio,
        horario_fim,
        ativa,
        erros,
    )


def validar_aluno(form):
    nome = normalizar_texto(form.get("nome", ""))
    telefone = normalizar_texto(form.get("telefone", "")) or None
    celular = normalizar_texto(form.get("celular", "")) or None
    comercial = normalizar_texto(form.get("comercial", "")) or None
    responsavel = normalizar_texto(form.get("responsavel", "")) or None
    flag_coordenacao = form.get("flag_coordenacao") == "on"

    erros = []
    if not nome:
        erros.append("Informe o nome do aluno.")

    return (
        nome,
        telefone,
        celular,
        comercial,
        responsavel,
        flag_coordenacao,
        erros,
    )


def validar_matricula(form):
    erros = []
    try:
        aluno_id = int(form.get("aluno_id", ""))
    except (TypeError, ValueError):
        aluno_id = None
    try:
        turma_id = int(form.get("turma_id", ""))
    except (TypeError, ValueError):
        turma_id = None

    if not aluno_id:
        erros.append("Selecione um aluno.")
    if not turma_id:
        erros.append("Selecione uma turma.")

    return aluno_id, turma_id, erros


def validar_materia(form):
    nome = normalizar_texto(form.get("nome", ""))
    erros = []
    if not nome:
        erros.append("Informe o nome da matéria.")
    return nome, erros