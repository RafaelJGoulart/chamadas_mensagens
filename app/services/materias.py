"""Ordem canônica das matérias.

Matérias padrão seguem a ordem definida pelo professor; a matéria "Neutra"
(a que abriga as chamadas antigas) aparece sempre no final da lista.
"""

# Ordem fixa das matérias padrão do curso de Informática.
MATERIAS_PADRAO_INFORMATICA = [
    "Windows",
    "Illustrator",
    "Photoshop",
    "Word",
    "Lógica de Programação",
    "Scratch",
    "HTML",
    "Powerpoint",
    "Express",
    "XD",
    "Dreamweaver",
    "Excel",
]

# Matéria usada para agrupar as chamadas antigas (sem matéria informada).
MATERIA_NEUTRA = "Neutra"


def ordenar_materias(materias):
    """Ordena matérias: padrão na ordem canônica, depois extras (alfabéticas),
    e a "Neutra" sempre por último."""
    pos = {nome: i for i, nome in enumerate(MATERIAS_PADRAO_INFORMATICA)}

    def chave(m):
        nome = (m.nome or "").strip()
        if nome.lower() == MATERIA_NEUTRA.lower():
            return (2, 0, "")
        p = pos.get(nome)
        if p is not None:
            return (0, p, "")
        return (1, 0, nome.lower())

    return sorted(materias, key=chave)