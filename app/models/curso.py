from datetime import date

from extensions import db


class Curso(db.Model):
    __tablename__ = "cursos"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(120), nullable=False, unique=True)
    descricao = db.Column(db.Text)

    turmas = db.relationship(
        "Turma",
        backref="curso",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"<Curso {self.nome}>"