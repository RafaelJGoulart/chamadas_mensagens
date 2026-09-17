from datetime import date

from extensions import db


STATUS_ALUNO = (
    "ativo",
    "inativo",
)


class Aluno(db.Model):
    __tablename__ = "alunos"
    __table_args__ = (
        db.CheckConstraint(
            f"status IN {STATUS_ALUNO}",
            name="ck_aluno_status",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(160), nullable=False)
    telefone = db.Column(db.String(30))
    celular = db.Column(db.String(30))
    comercial = db.Column(db.String(30))
    responsavel = db.Column(db.String(160))
    data_matricula = db.Column(db.Date, default=date.today, nullable=False)
    status = db.Column(db.String(10), nullable=False, default="ativo")
    flag_coordenacao = db.Column(db.Boolean, nullable=False, default=False)

    matriculas = db.relationship(
        "Matricula",
        backref="aluno",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    presencas = db.relationship(
        "Presenca",
        backref="aluno",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )
    contatos = db.relationship(
        "Contato",
        backref="aluno",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Aluno {self.nome}>"