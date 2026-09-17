from extensions import db


class Chamada(db.Model):
    __tablename__ = "chamadas"
    __table_args__ = (
        db.UniqueConstraint(
            "turma_id",
            "data",
            name="uq_chamada_turma_data",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    turma_id = db.Column(
        db.Integer,
        db.ForeignKey("turmas.id"),
        nullable=False,
    )
    data = db.Column(db.Date, nullable=False)
    conteudo = db.Column(db.Text)
    observacao = db.Column(db.Text)

    presencas = db.relationship(
        "Presenca",
        backref="chamada",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Chamada turma={self.turma_id} data={self.data}>"