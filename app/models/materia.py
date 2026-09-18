from extensions import db


class Materia(db.Model):
    __tablename__ = "materias"
    __table_args__ = (
        db.UniqueConstraint(
            "curso_id",
            "nome",
            name="uq_materia_curso_nome",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(
        db.Integer,
        db.ForeignKey("cursos.id"),
        nullable=False,
    )
    nome = db.Column(db.String(120), nullable=False)

    chamadas = db.relationship(
        "Chamada",
        backref="materia",
        lazy="dynamic",
    )

    def __repr__(self):
        return f"<Materia {self.nome}>"