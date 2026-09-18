from extensions import db


class Chamada(db.Model):
    __tablename__ = "chamadas"
    __table_args__ = (
        db.UniqueConstraint(
            "turma_id",
            "data",
            "materia_id",
            name="uq_chamada_turma_data_materia",
        ),
        db.Index("ix_chamadas_data", "data"),
    )

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(
        db.Integer,
        db.ForeignKey("turmas.id"),
        nullable=False,
    )
    materia_id = db.Column(
        db.Integer,
        db.ForeignKey("materias.id"),
        nullable=True,
    )
    data = db.Column(db.Date, nullable=False)
    conteudo = db.Column(db.Text)
    observacao = db.Column(db.Text)

    presencas = db.relationship(
        "Presenca",
        backref="chamada",
        lazy="select",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Chamada turma={self.turma_id} data={self.data}>"