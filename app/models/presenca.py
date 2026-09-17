from extensions import db


ESTADOS_PRESENCA = (
    "ausente",
    "frequente",
    "reposicao",
)

AUSENTE = "ausente"
FREQUENTE = "frequente"
REPOSICAO = "reposicao"


class Presenca(db.Model):
    __tablename__ = "presencas"
    __table_args__ = (
        db.UniqueConstraint(
            "chamada_id",
            "aluno_id",
            name="uq_presenca_chamada_aluno",
        ),
        db.CheckConstraint(
            f"estado IN {ESTADOS_PRESENCA}",
            name="ck_presenca_estado",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    chamada_id = db.Column(
        db.Integer,
        db.ForeignKey("chamadas.id"),
        nullable=False,
    )
    aluno_id = db.Column(
        db.Integer,
        db.ForeignKey("alunos.id"),
        nullable=False,
    )
    estado = db.Column(db.String(10), nullable=False)
    observacao = db.Column(db.Text)

    def __repr__(self):
        return (
            f"<Presenca chamada={self.chamada_id} "
            f"aluno={self.aluno_id} {self.estado}>"
        )