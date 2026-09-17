from datetime import date

from extensions import db


class Matricula(db.Model):
    __tablename__ = "matriculas"

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(
        db.Integer,
        db.ForeignKey("alunos.id"),
        nullable=False,
    )
    turma_id = db.Column(
        db.Integer,
        db.ForeignKey("turmas.id"),
        nullable=False,
    )
    data_inicio = db.Column(db.Date, default=date.today, nullable=False)
    data_fim = db.Column(db.Date)
    ativa = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return (
            f"<Matricula aluno={self.aluno_id} "
            f"turma={self.turma_id}>"
        )