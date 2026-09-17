from datetime import date

from extensions import db


class Contato(db.Model):
    __tablename__ = "contatos"

    id = db.Column(db.Integer, primary_key=True)
    aluno_id = db.Column(
        db.Integer,
        db.ForeignKey("alunos.id"),
        nullable=False,
    )
    data = db.Column(db.Date, default=date.today, nullable=False)
    tipo = db.Column(db.String(50))
    descricao = db.Column(db.Text)

    def __repr__(self):
        return f"<Contato aluno={self.aluno_id} data={self.data}>"