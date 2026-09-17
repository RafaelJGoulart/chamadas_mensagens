from extensions import db


DIAS_SEMANA = (
    "segunda",
    "terca",
    "quarta",
    "quinta",
    "sexta",
    "sabado",
    "domingo",
)


class Turma(db.Model):
    __tablename__ = "turmas"
    __table_args__ = (
        db.CheckConstraint(
            f"dia_semana IN {DIAS_SEMANA}",
            name="ck_turma_dia_semana",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    curso_id = db.Column(
        db.Integer,
        db.ForeignKey("cursos.id"),
        nullable=False,
    )
    nome = db.Column(db.String(120), nullable=False)
    dia_semana = db.Column(db.String(10), nullable=False)
    horario_inicio = db.Column(db.Time)
    horario_fim = db.Column(db.Time)
    ativa = db.Column(db.Boolean, nullable=False, default=True)

    matriculas = db.relationship(
        "Matricula",
        backref="turma",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    chamadas = db.relationship(
        "Chamada",
        backref="turma",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Turma {self.nome}>"