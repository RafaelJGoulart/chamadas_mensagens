"""Ordem canônica das matérias.

Matérias padrão seguem a ordem definida pelo professor; a matéria "Neutra"
(a que abriga as chamadas antigas) aparece sempre no final da lista.
"""

from extensions import db
from models import Materia

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


def garantir_materia_neutra(curso_id):
    """Busca ou cria a matéria "Neutra" do curso (sem commit).

    Usada ao criar um curso e ao trocar uma turma de curso (as pautas da
    turma passam para a Neutra do curso de destino). Quem chama commita.
    """
    neutra = Materia.query.filter_by(
        curso_id=curso_id, nome=MATERIA_NEUTRA
    ).first()
    if neutra is None:
        neutra = Materia(curso_id=curso_id, nome=MATERIA_NEUTRA)
        db.session.add(neutra)
        db.session.flush()
    return neutra