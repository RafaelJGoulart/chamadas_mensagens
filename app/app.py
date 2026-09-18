import logging
import sys
from pathlib import Path

# Garante que imports irmãos (config, extensions, models...) funcionem
# independente de como o Python foi invocado (instalado vs. portátil/embeddable,
# CWD diferente, PYTHONSAFEPATH, python._pth isolado etc.).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from flask import Flask

from config import Config
from extensions import db
import models  # noqa: F401  (registra os modelos no SQLAlchemy)
from routes.cursos import cursos_bp
from routes.turmas import turmas_bp
from routes.alunos import alunos_bp
from routes.matriculas import matriculas_bp
from routes.chamadas import chamadas_bp
from routes.dashboard import dashboard_bp
from routes.contato import contato_bp
from routes.relatorio import relatorio_bp
from routes.importacao import importacao_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(cursos_bp)
    app.register_blueprint(turmas_bp)
    app.register_blueprint(alunos_bp)
    app.register_blueprint(matriculas_bp)
    app.register_blueprint(chamadas_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(contato_bp)
    app.register_blueprint(relatorio_bp)
    app.register_blueprint(importacao_bp)

    with app.app_context():
        try:
            db.create_all()
        except Exception:
            logging.exception("Falha ao inicializar o banco de dados")
        _garantir_colunas_telefone()

    return app


def _garantir_colunas_telefone():
    """Migração idempotente: garante celular/comercial em bancos antigos.

    Bancos novos já nascem com as colunas via create_all().
    O número do antigo telefone_responsavel é copiado para celular
    (somente onde celular estiver vazio) para não perder contato.
    """
    try:
        with db.engine.begin() as conn:
            colunas = {
                linha[1]
                for linha in conn.exec_driver_sql("PRAGMA table_info(alunos)")
            }
            if "celular" not in colunas:
                conn.exec_driver_sql(
                    "ALTER TABLE alunos ADD COLUMN celular VARCHAR(30)"
                )
            if "comercial" not in colunas:
                conn.exec_driver_sql(
                    "ALTER TABLE alunos ADD COLUMN comercial VARCHAR(30)"
                )
            if "telefone_responsavel" in colunas:
                conn.exec_driver_sql(
                    "UPDATE alunos SET celular = telefone_responsavel "
                    "WHERE (celular IS NULL OR celular = '') "
                    "AND telefone_responsavel IS NOT NULL "
                    "AND telefone_responsavel != ''"
                )
    except Exception:
        logging.exception("Falha na migração das colunas de telefone")


app = create_app()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )